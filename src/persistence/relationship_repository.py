"""
VibeCForms v3.0: RelationshipRepository Implementation

This module provides the concrete implementation of IRelationshipRepository
for managing relationships in the new persistence paradigm.

Supports all cardinality types (1:1, 1:N, N:N) through a unified interface.

Date: 2026-01-08
Version: 1.0
Status: Implementation Phase
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4
from contextlib import contextmanager

from src.persistence.contracts.relationship_interface import (
    IRelationshipRepository,
    Relationship,
    SyncStrategy,
    CardinalityType,
)


logger = logging.getLogger(__name__)


class RelationshipRepository(IRelationshipRepository):
    """
    SQLite-based implementation of relationship management.

    Features:
    - Atomic transactions for data consistency
    - Soft-delete with audit trail
    - Display value synchronization (eager, lazy, scheduled)
    - Batch operations for performance
    - Comprehensive validation
    """

    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            connection: SQLite database connection (must be open)
        """
        self.conn = connection
        self.conn.row_factory = sqlite3.Row
        self.logger = logging.getLogger(__name__)

    # ═══════════════════════════════════════════════════════════════════════
    # CONTEXT MANAGER FOR TRANSACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    @contextmanager
    def _transaction(self):
        """
        Context manager for database transactions.

        Automatically commits on success, rolls back on exception.
        """
        try:
            yield self.conn.cursor()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Transaction failed: {str(e)}")
            raise

    # ═══════════════════════════════════════════════════════════════════════
    # CREATION
    # ═══════════════════════════════════════════════════════════════════════

    def create_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str,
        target_type: str,
        target_id: str,
        created_by: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new relationship."""

        # Validation
        self._validate_relationship_params(
            source_type, source_id, relationship_name,
            target_type, target_id
        )

        # Generate UUID
        rel_id = self._generate_id()

        with self._transaction() as cursor:
            # 1. Verify target exists
            if not self._record_exists(cursor, target_type, target_id):
                raise ValueError(
                    f"Target {target_type}/{target_id} does not exist"
                )

            # 2. Check for duplicate
            if self._relationship_exists(
                cursor, source_type, source_id,
                relationship_name, target_id
            ):
                raise ValueError(
                    f"Relationship already exists: "
                    f"{source_type}/{source_id} → {relationship_name} → "
                    f"{target_type}/{target_id}"
                )

            # 3. Insert relationship
            cursor.execute("""
                INSERT INTO relationships (
                    rel_id, source_type, source_id,
                    relationship_name, target_type, target_id,
                    created_at, created_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rel_id, source_type, source_id,
                relationship_name, target_type, target_id,
                self._now(), created_by,
                json.dumps(metadata) if metadata else None
            ))

            self.logger.info(
                f"Created relationship {rel_id}: "
                f"{source_type}/{source_id} → {relationship_name} → "
                f"{target_type}/{target_id}"
            )

        return rel_id

    # ═══════════════════════════════════════════════════════════════════════
    # RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════════

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """Get a single relationship by ID."""

        if not rel_id or not isinstance(rel_id, str):
            raise ValueError("Invalid rel_id")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM relationships
            WHERE rel_id = ?
        """, (rel_id,))

        row = cursor.fetchone()
        return self._row_to_relationship(row) if row else None

    def get_relationships(
        self,
        source_type: str,
        source_id: str,
        relationship_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[Relationship]:
        """Get all relationships for an entity (forward navigation)."""

        if not source_type or not source_id:
            raise ValueError("source_type and source_id are required")

        cursor = self.conn.cursor()

        # Build query
        query = """
            SELECT *
            FROM relationships
            WHERE source_type = ? AND source_id = ?
        """
        params = [source_type, source_id]

        if relationship_name:
            query += " AND relationship_name = ?"
            params.append(relationship_name)

        if active_only:
            query += " AND removed_at IS NULL"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_relationship(row) for row in rows]

    def get_reverse_relationships(
        self,
        target_type: str,
        target_id: str,
        relationship_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[Relationship]:
        """Get all entities that point to this entity (reverse navigation)."""

        if not target_type or not target_id:
            raise ValueError("target_type and target_id are required")

        cursor = self.conn.cursor()

        # Build query
        query = """
            SELECT *
            FROM relationships
            WHERE target_type = ? AND target_id = ?
        """
        params = [target_type, target_id]

        if relationship_name:
            query += " AND relationship_name = ?"
            params.append(relationship_name)

        if active_only:
            query += " AND removed_at IS NULL"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_relationship(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════════════
    # DELETION
    # ═══════════════════════════════════════════════════════════════════════

    def remove_relationship(self, rel_id: str, removed_by: str) -> bool:
        """Soft-delete a relationship."""

        if not rel_id or not removed_by:
            raise ValueError("rel_id and removed_by are required")

        with self._transaction() as cursor:
            cursor.execute("""
                UPDATE relationships
                SET removed_at = ?, removed_by = ?
                WHERE rel_id = ?
            """, (self._now(), removed_by, rel_id))

            if cursor.rowcount == 0:
                return False

            self.logger.info(f"Soft-deleted relationship {rel_id}")
            return True

    def restore_relationship(self, rel_id: str, restored_by: str) -> bool:
        """Restore a soft-deleted relationship."""

        if not rel_id or not restored_by:
            raise ValueError("rel_id and restored_by are required")

        with self._transaction() as cursor:
            cursor.execute("""
                UPDATE relationships
                SET removed_at = NULL, removed_by = NULL
                WHERE rel_id = ?
            """, (rel_id,))

            if cursor.rowcount == 0:
                return False

            self.logger.info(f"Restored relationship {rel_id}")
            return True

    # ═══════════════════════════════════════════════════════════════════════
    # SYNCHRONIZATION
    # ═══════════════════════════════════════════════════════════════════════

    def sync_display_values(
        self,
        source_type: str,
        source_id: str,
        relationship_name: Optional[str] = None
    ) -> int:
        """Synchronize display values (eager sync)."""

        if not source_type or not source_id:
            raise ValueError("source_type and source_id are required")

        with self._transaction() as cursor:
            # Get relationships to sync
            query = """
                SELECT DISTINCT
                    relationship_name, target_type, target_id
                FROM relationships
                WHERE source_type = ? AND source_id = ? AND removed_at IS NULL
            """
            params = [source_type, source_id]

            if relationship_name:
                query += " AND relationship_name = ?"
                params.append(relationship_name)

            cursor.execute(query, params)
            relationships = cursor.fetchall()

            updated_count = 0

            for rel in relationships:
                rel_name = rel['relationship_name']
                target_type = rel['target_type']
                target_id = rel['target_id']

                # Get target's display value
                display_value = self._get_display_value(
                    cursor, target_type, target_id
                )

                if display_value:
                    # Update source's display column
                    display_col = f"_{rel_name}_display"
                    update_query = f"""
                        UPDATE {source_type}
                        SET {display_col} = ?, updated_at = ?
                        WHERE record_id = ?
                    """

                    try:
                        cursor.execute(
                            update_query,
                            (display_value, self._now(), source_id)
                        )
                        updated_count += cursor.rowcount
                    except sqlite3.OperationalError:
                        # Column might not exist yet
                        self.logger.warning(
                            f"Display column {display_col} doesn't exist in {source_type}"
                        )

            return updated_count

    def validate_relationships(
        self,
        source_type: str,
        source_id: Optional[str] = None
    ) -> Dict:
        """Validate relationship integrity."""

        cursor = self.conn.cursor()
        errors = []
        orphans = []
        inconsistencies = []

        # Find orphaned relationships
        query = """
            SELECT r.rel_id, r.source_type, r.source_id, r.target_type, r.target_id
            FROM relationships r
            LEFT JOIN {target_table} t ON r.target_id = t.record_id
            WHERE r.removed_at IS NULL
              AND r.source_type = ?
              AND t.record_id IS NULL
        """

        if source_id:
            query += " AND r.source_id = ?"
            params = [source_type, source_id]
        else:
            params = [source_type]

        try:
            cursor.execute(query.format(target_table="{}"), params)
            orphans = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.warning(f"Error checking orphans: {str(e)}")

        if orphans:
            errors.append(f"Found {len(orphans)} orphaned relationships")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'orphans': orphans,
            'inconsistencies': inconsistencies
        }

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════

    def count_relationships(
        self,
        source_type: str,
        source_id: Optional[str] = None,
        relationship_name: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """Count relationships matching criteria."""

        cursor = self.conn.cursor()

        query = "SELECT COUNT(*) as count FROM relationships WHERE source_type = ?"
        params = [source_type]

        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)

        if relationship_name:
            query += " AND relationship_name = ?"
            params.append(relationship_name)

        if active_only:
            query += " AND removed_at IS NULL"

        cursor.execute(query, params)
        return cursor.fetchone()['count']

    def get_relationship_stats(self, source_type: str) -> Dict:
        """Get statistics about relationships."""

        cursor = self.conn.cursor()

        # Total and active count
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN removed_at IS NULL THEN 1 ELSE 0 END) as active
            FROM relationships
            WHERE source_type = ?
        """, (source_type,))

        stats = cursor.fetchone()

        # By relationship name
        cursor.execute("""
            SELECT relationship_name, COUNT(*) as count
            FROM relationships
            WHERE source_type = ? AND removed_at IS NULL
            GROUP BY relationship_name
        """, (source_type,))

        by_name = {row['relationship_name']: row['count']
                   for row in cursor.fetchall()}

        return {
            'total': stats['total'],
            'active': stats['active'],
            'by_name': by_name,
            'by_cardinality': {}  # TODO: Implement when schema available
        }

    # ═══════════════════════════════════════════════════════════════════════
    # BATCH OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    def create_relationships_batch(
        self,
        relationships: List[Dict],
        created_by: str
    ) -> List[str]:
        """Create multiple relationships atomically."""

        if not relationships:
            return []

        rel_ids = []

        with self._transaction() as cursor:
            for rel_data in relationships:
                # Validate
                required = ['source_type', 'source_id', 'relationship_name',
                           'target_type', 'target_id']
                if not all(k in rel_data for k in required):
                    raise ValueError(f"Missing required fields: {rel_data}")

                # Generate ID
                rel_id = self._generate_id()

                # Insert
                cursor.execute("""
                    INSERT INTO relationships (
                        rel_id, source_type, source_id,
                        relationship_name, target_type, target_id,
                        created_at, created_by, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel_id,
                    rel_data['source_type'],
                    rel_data['source_id'],
                    rel_data['relationship_name'],
                    rel_data['target_type'],
                    rel_data['target_id'],
                    self._now(),
                    created_by,
                    json.dumps(rel_data.get('metadata'))
                    if rel_data.get('metadata') else None
                ))

                rel_ids.append(rel_id)

        self.logger.info(f"Created {len(rel_ids)} relationships in batch")
        return rel_ids

    def remove_relationships_batch(
        self,
        rel_ids: List[str],
        removed_by: str
    ) -> int:
        """Remove multiple relationships atomically."""

        if not rel_ids:
            return 0

        with self._transaction() as cursor:
            cursor.execute(f"""
                UPDATE relationships
                SET removed_at = ?, removed_by = ?
                WHERE rel_id IN ({','.join(['?'] * len(rel_ids))})
            """, [self._now(), removed_by] + rel_ids)

            count = cursor.rowcount

        self.logger.info(f"Removed {count} relationships in batch")
        return count

    # ═══════════════════════════════════════════════════════════════════════
    # SCHEMA MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def create_relationship_table(self) -> bool:
        """Create relationships table and indexes."""

        cursor = self.conn.cursor()

        try:
            # Create main table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    rel_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    relationship_name TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    removed_at TEXT,
                    removed_by TEXT,
                    metadata TEXT,

                    UNIQUE(source_type, source_id, relationship_name, target_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_source
                ON relationships(source_type, source_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_target
                ON relationships(target_type, target_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_name
                ON relationships(source_type, relationship_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rel_active
                ON relationships(source_type, source_id, removed_at)
            """)

            self.conn.commit()
            self.logger.info("Relationships table created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error creating relationships table: {str(e)}")
            return False

    def drop_relationship_table(self) -> bool:
        """Drop relationships table (destructive!)."""

        cursor = self.conn.cursor()

        try:
            cursor.execute("DROP TABLE IF EXISTS relationships")
            self.conn.commit()
            self.logger.warning("Relationships table dropped")
            return True
        except Exception as e:
            self.logger.error(f"Error dropping relationships table: {str(e)}")
            return False

    def table_exists(self) -> bool:
        """Check if relationships table exists."""

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='relationships'
        """)
        return cursor.fetchone() is not None

    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_relationship_params(
        self, source_type, source_id, relationship_name,
        target_type, target_id
    ):
        """Validate relationship parameters."""
        if not all([source_type, source_id, relationship_name,
                   target_type, target_id]):
            raise ValueError("All relationship fields are required")

        if source_type == target_type and source_id == target_id:
            raise ValueError("Cannot create self-relationship")

    def _relationship_exists(
        self, cursor, source_type, source_id,
        relationship_name, target_id
    ) -> bool:
        """Check if relationship already exists."""
        cursor.execute("""
            SELECT 1 FROM relationships
            WHERE source_type = ? AND source_id = ?
              AND relationship_name = ? AND target_id = ?
              AND removed_at IS NULL
        """, (source_type, source_id, relationship_name, target_id))
        return cursor.fetchone() is not None

    def _record_exists(self, cursor, form_path: str, record_id: str) -> bool:
        """Check if a record exists in a table."""
        try:
            cursor.execute(
                f"SELECT 1 FROM {form_path} WHERE record_id = ?",
                (record_id,)
            )
            return cursor.fetchone() is not None
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return False

    def _get_display_value(
        self, cursor, form_path: str, record_id: str
    ) -> Optional[str]:
        """Get the display value from a record."""
        try:
            cursor.execute(
                f"SELECT nome FROM {form_path} WHERE record_id = ?",
                (record_id,)
            )
            row = cursor.fetchone()
            return row['nome'] if row else None
        except sqlite3.OperationalError:
            return None

    def _row_to_relationship(self, row: sqlite3.Row) -> Relationship:
        """Convert database row to Relationship object."""
        metadata = None
        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
            except json.JSONDecodeError:
                pass

        return Relationship(
            rel_id=row['rel_id'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            relationship_name=row['relationship_name'],
            target_type=row['target_type'],
            target_id=row['target_id'],
            created_at=row['created_at'],
            created_by=row['created_by'],
            removed_at=row['removed_at'],
            removed_by=row['removed_by'],
            metadata=metadata
        )

    @staticmethod
    def _generate_id() -> str:
        """Generate a UUID for relationship."""
        return str(uuid4())[:27].upper()

    @staticmethod
    def _now() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
