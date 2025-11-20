"""
Migration manager for VibeCForms persistence layer.

This module handles data migration between different storage backends,
allowing seamless transitions from TXT to SQLite, SQLite to TXT, etc.
"""

import logging
import shutil
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from persistence.base import BaseRepository
from persistence.factory import RepositoryFactory
from persistence.config import get_config

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages data migration between different persistence backends.

    This class handles the complex process of migrating data from one
    storage backend to another while preserving all data integrity.

    Features:
    - Automatic data conversion between backends
    - Backup creation before migration
    - Automatic rollback on failure
    - Support for all backend types
    """

    @staticmethod
    def migrate_backend(
        form_path: str,
        spec: Dict[str, Any],
        old_backend: str,
        new_backend: str,
        record_count: int = 0,
    ) -> bool:
        """
        Migrate data from one backend to another.

        This method:
        1. Creates backup of old backend data
        2. Reads all data from old backend
        3. Creates storage in new backend
        4. Writes all data to new backend
        5. Verifies migration success
        6. Rollback on failure

        Args:
            form_path: Path to the form
            spec: Form specification
            old_backend: Source backend type (e.g., 'txt')
            new_backend: Target backend type (e.g., 'sqlite')
            record_count: Number of records to migrate (for logging)

        Returns:
            True if migration successful, False otherwise

        Example:
            success = MigrationManager.migrate_backend(
                'contatos',
                spec,
                'txt',
                'sqlite',
                record_count=150
            )
        """
        logger.info(
            f"Starting backend migration for '{form_path}': "
            f"{old_backend} -> {new_backend} ({record_count} records)"
        )

        # Get repositories for old and new backends
        old_repo = MigrationManager._get_repository(old_backend)
        new_repo = MigrationManager._get_repository(new_backend)

        if not old_repo or not new_repo:
            logger.error("Failed to create repositories for migration")
            return False

        # Check if old backend has storage
        if not old_repo.exists(form_path):
            logger.info(
                f"No existing data in {old_backend} backend, nothing to migrate"
            )
            return True

        # Create backup of old backend
        backup_info = MigrationManager._create_cross_backend_backup(
            form_path=form_path, old_backend=old_backend, old_repo=old_repo
        )

        if not backup_info:
            logger.error("Failed to create backup, aborting migration")
            return False

        try:
            import time

            migration_start = time.time()

            # Step 1: Read all data from old backend
            logger.info(f"⏱️  Reading data from {old_backend} backend...")
            step_start = time.time()
            old_data = old_repo.read_all(form_path, spec)
            read_time = time.time() - step_start

            if not old_data:
                logger.info("No data to migrate")
                # Still successful - just no data
                return True

            logger.info(
                f"✅ Read {len(old_data)} records from {old_backend} in {read_time:.2f}s"
            )

            # Step 2: Create storage in new backend if needed
            if not new_repo.exists(form_path):
                logger.info(f"⏱️  Creating storage in {new_backend} backend...")
                step_start = time.time()
                if not new_repo.create_storage(form_path, spec):
                    raise Exception(
                        f"Failed to create storage in {new_backend} backend"
                    )
                create_time = time.time() - step_start
                logger.info(f"✅ Created storage in {create_time:.2f}s")

            # Step 3: Migrate records to new backend using bulk operation
            logger.info(
                f"⏱️  Migrating {len(old_data)} records to {new_backend} backend..."
            )
            step_start = time.time()

            # Use bulk_create for significantly better performance
            migrated_ids = new_repo.bulk_create(form_path, spec, old_data)
            migrate_time = time.time() - step_start

            # Count errors (None values in result)
            migration_errors = sum(1 for id in migrated_ids if id is None)

            # Check if too many errors occurred
            total_records = len(old_data)
            if migration_errors > 0:
                error_rate = migration_errors / total_records
                if error_rate > 0.1:  # More than 10% failed
                    raise Exception(
                        f"Too many migration errors: {migration_errors}/{total_records} "
                        f"({error_rate*100:.1f}%)"
                    )
                logger.warning(f"⚠️  {migration_errors} records failed to migrate")

            logger.info(f"✅ Migrated in {migrate_time:.2f}s")

            # Step 4: Verify migration
            logger.info(f"⏱️  Verifying migration...")
            step_start = time.time()
            new_data = new_repo.read_all(form_path, spec)
            verify_time = time.time() - step_start

            if len(new_data) != len(old_data):
                raise Exception(
                    f"Verification failed: expected {len(old_data)} records, "
                    f"got {len(new_data)}"
                )

            total_time = time.time() - migration_start
            logger.info(f"✅ Verified in {verify_time:.2f}s")

            # Migration successful
            logger.info(
                f"✅ Successfully migrated {len(old_data)} records from {old_backend} to {new_backend} "
                f"in {total_time:.2f}s total ({migration_errors} warnings)"
            )

            # Optional: Drop old storage (commented out for safety)
            # old_repo.drop_storage(form_path, force=True)

            return True

        except Exception as e:
            # Rollback: restore old backend and clean up new backend
            logger.error(f"Migration failed: {e}")
            logger.info("Rolling back migration...")

            MigrationManager._rollback_migration(
                form_path=form_path,
                new_backend=new_backend,
                new_repo=new_repo,
                backup_info=backup_info,
            )

            return False

    @staticmethod
    def _get_repository(backend_type: str) -> Optional[BaseRepository]:
        """
        Get a repository instance for a specific backend type.

        Args:
            backend_type: Type of backend (e.g., 'txt', 'sqlite')

        Returns:
            Repository instance or None
        """
        config = get_config()

        # Get backend configuration
        backend_config = config.config.get("backends", {}).get(backend_type)
        if not backend_config:
            logger.error(f"No configuration found for backend type: {backend_type}")
            return None

        # Create repository using factory (simulate form_path)
        # We need to temporarily modify config to use specific backend
        try:
            if backend_type == "txt":
                from persistence.adapters.txt_adapter import TxtRepository

                return TxtRepository(backend_config)
            elif backend_type == "sqlite":
                from persistence.adapters.sqlite_adapter import SQLiteRepository

                return SQLiteRepository(backend_config)
            else:
                logger.error(f"Unsupported backend type: {backend_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to create repository for {backend_type}: {e}")
            return None

    @staticmethod
    def _create_cross_backend_backup(
        form_path: str, old_backend: str, old_repo: BaseRepository
    ) -> Optional[Dict[str, Any]]:
        """
        Create a backup before cross-backend migration.

        Args:
            form_path: Path to the form
            old_backend: Source backend type
            old_repo: Source repository instance

        Returns:
            Backup info dictionary with paths and metadata
        """
        # Get backup path from config
        config = get_config()
        backup_path = config.get_setting("backup_path", "backups/migrations")

        # Resolve relative paths against business case root
        if not os.path.isabs(backup_path):
            backup_path = str(config.business_case_root / backup_path)

        # Create migration backups directory
        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = (
            f"{form_path.replace('/', '_')}_{old_backend}_to_migration_{timestamp}"
        )

        backup_info = {
            "form_path": form_path,
            "old_backend": old_backend,
            "timestamp": timestamp,
            "backup_dir": str(backup_dir),
            "backup_name": backup_name,
        }

        try:
            # Backend-specific backup
            if old_backend == "txt":
                # Copy .txt file
                from persistence.adapters.txt_adapter import TxtRepository

                if isinstance(old_repo, TxtRepository):
                    source_file = old_repo._get_file_path(form_path)
                    if os.path.exists(source_file):
                        dest_file = backup_dir / f"{backup_name}.txt"
                        shutil.copy2(source_file, dest_file)
                        backup_info["backup_file"] = str(dest_file)
                        logger.info(f"Created backup: {dest_file}")

            elif old_backend == "sqlite":
                # Copy entire database
                from persistence.adapters.sqlite_adapter import SQLiteRepository

                if isinstance(old_repo, SQLiteRepository):
                    source_db = old_repo.database
                    if os.path.exists(source_db):
                        dest_db = backup_dir / f"{backup_name}.db"
                        shutil.copy2(source_db, dest_db)
                        backup_info["backup_file"] = str(dest_db)
                        logger.info(f"Created backup: {dest_db}")

            return backup_info

        except Exception as e:
            logger.error(f"Failed to create cross-backend backup: {e}")
            return None

    @staticmethod
    def _rollback_migration(
        form_path: str,
        new_backend: str,
        new_repo: BaseRepository,
        backup_info: Dict[str, Any],
    ) -> bool:
        """
        Rollback a failed migration.

        This removes any data created in the new backend and ensures
        the old backend data is still intact.

        Args:
            form_path: Path to the form
            new_backend: Target backend type
            new_repo: Target repository instance
            backup_info: Backup information

        Returns:
            True if rollback successful
        """
        try:
            # Drop new backend storage (it may be partially created)
            if new_repo.exists(form_path):
                logger.info(f"Dropping incomplete {new_backend} storage...")
                new_repo.drop_storage(form_path, force=True)

            # Old backend data should still exist (we didn't delete it)
            logger.info("Old backend data preserved, migration rolled back")
            return True

        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False


def migrate_form_backend(
    form_path: str,
    spec: Dict[str, Any],
    old_backend: str,
    new_backend: str,
    record_count: int = 0,
) -> bool:
    """
    Convenience function to migrate a form's backend.

    Args:
        form_path: Path to the form
        spec: Form specification
        old_backend: Source backend type
        new_backend: Target backend type
        record_count: Number of records (for logging)

    Returns:
        True if successful
    """
    return MigrationManager.migrate_backend(
        form_path=form_path,
        spec=spec,
        old_backend=old_backend,
        new_backend=new_backend,
        record_count=record_count,
    )
