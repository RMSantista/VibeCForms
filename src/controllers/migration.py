"""
Migration Controller for VibeCForms

Handles backend and schema migration operations including:
- Migration confirmation UI
- Migration execution
- Data migration between backends
"""

import logging
from flask import Blueprint, render_template, request, redirect

from persistence.factory import RepositoryFactory
from persistence.change_manager import (
    check_form_changes,
    update_form_tracking,
    ChangeManager,
)
from persistence.migration_manager import MigrationManager
from persistence.schema_history import get_history
from persistence.config import get_config
from utils.spec_loader import load_spec

logger = logging.getLogger(__name__)

migration_bp = Blueprint("migration", __name__)


@migration_bp.route("/migrate/confirm/<path:form_path>")
def migrate_confirm(form_path):
    """Display migration confirmation page."""
    spec = load_spec(form_path)

    # Check if backend has changed by comparing history with current config
    history = get_history()
    form_history = history.get_form_history(form_path)

    config = get_config()
    current_backend_config = config.get_backend_config(form_path)
    current_backend = current_backend_config.get("type")

    last_backend = history.get_last_backend(form_path)
    backend_changed = last_backend and last_backend != current_backend

    # Get repository for current (new) backend
    repo = RepositoryFactory.get_repository(form_path)

    # Check if storage exists and has data
    has_data = False
    record_count = 0

    if backend_changed and form_history:
        # Backend changed: use record count from history (reflects data in old backend)
        record_count = form_history.get("record_count", 0)
        has_data = record_count > 0
        logger.info(
            f"Migration confirmation: Backend changed for '{form_path}', using historical record count: {record_count}"
        )
    else:
        # No backend change: check current backend for data
        has_data = repo.exists(form_path) and repo.has_data(form_path)

        if has_data:
            try:
                existing_data = repo.read_all(form_path, spec)
                record_count = len(existing_data)
            except Exception as e:
                logger.warning(f"Error reading existing data: {e}")
                has_data = False

    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path, spec=spec, has_data=has_data, record_count=record_count
    )

    # Check if there are any changes requiring confirmation
    if not schema_change and not backend_change:
        # No changes, redirect back to form
        return redirect(f"/{form_path}")

    # Check if confirmation is required
    requires_confirmation = ChangeManager.requires_confirmation(
        schema_change, backend_change
    )

    if not requires_confirmation:
        # No confirmation needed, redirect back to form
        return redirect(f"/{form_path}")

    # Determine if there are destructive changes
    has_destructive_changes = False
    has_warnings = False

    if schema_change:
        from persistence.schema_detector import ChangeType

        for change in schema_change.changes:
            if change.change_type == ChangeType.REMOVE_FIELD:
                has_destructive_changes = True
            if change.change_type == ChangeType.CHANGE_TYPE:
                has_warnings = True

    if backend_change:
        has_warnings = True

    # Render confirmation page
    return render_template(
        "migration_confirm.html",
        form_path=form_path,
        form_title=spec.get("title", form_path),
        record_count=record_count,
        schema_change=schema_change,
        backend_change=backend_change,
        has_destructive_changes=has_destructive_changes,
        has_warnings=has_warnings,
    )


@migration_bp.route("/migrate/execute/<path:form_path>", methods=["POST"])
def migrate_execute(form_path):
    """Execute the migration after user confirmation."""
    spec = load_spec(form_path)

    # Check if backend has changed by comparing history with current config
    history = get_history()
    form_history = history.get_form_history(form_path)

    config = get_config()
    current_backend_config = config.get_backend_config(form_path)
    current_backend = current_backend_config.get("type")

    last_backend = history.get_last_backend(form_path)
    backend_changed = last_backend and last_backend != current_backend

    # Get repository for current (new) backend
    repo = RepositoryFactory.get_repository(form_path)

    # Check if storage exists and has data
    has_data = False
    record_count = 0

    if backend_changed and form_history:
        # Backend changed: use record count from history (reflects data in old backend)
        record_count = form_history.get("record_count", 0)
        has_data = record_count > 0
        logger.info(
            f"Backend changed for '{form_path}', using historical record count for migration: {record_count}"
        )
    else:
        # No backend change: check current backend for data
        has_data = repo.exists(form_path) and repo.has_data(form_path)

        if has_data:
            try:
                existing_data = repo.read_all(form_path, spec)
                record_count = len(existing_data)
            except Exception as e:
                logger.warning(f"Error reading existing data: {e}")
                has_data = False

    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path, spec=spec, has_data=has_data, record_count=record_count
    )

    success = True
    error_message = None

    try:
        # Execute backend migration if needed
        if backend_change:
            logger.info(f"Executing backend migration for '{form_path}'...")
            success = MigrationManager.migrate_backend(
                form_path=form_path,
                spec=spec,
                old_backend=backend_change.old_backend,
                new_backend=backend_change.new_backend,
                record_count=record_count,
            )

            if not success:
                error_message = f"Falha na migração de backend: {backend_change.old_backend} → {backend_change.new_backend}"

        # Execute schema migration if needed
        if success and schema_change and schema_change.has_changes():
            logger.info(f"Executing schema migration for '{form_path}'...")

            # Get old spec from history to perform migration
            history = get_history()
            form_history = history.get_form_history(form_path)

            if form_history:
                # We need the old spec, but we don't have it stored
                # For now, we'll let migrate_schema handle it without old spec
                # The individual operations (rename, change_type, remove) will work
                logger.info(
                    f"Schema changes will be applied: {schema_change.get_summary()}"
                )

                # Note: The actual migration will happen automatically on next read_forms call
                # because the spec has changed and change_manager will detect it

        # Update tracking
        if success:
            logger.info(f"Updating form tracking for '{form_path}'...")
            tracking_updated = update_form_tracking(form_path, spec, record_count)
            if tracking_updated:
                logger.info(f"✅ Form tracking updated successfully for '{form_path}'")
            else:
                logger.warning(f"⚠️  Failed to update form tracking for '{form_path}'")
            logger.info(f"✅ Migration completed successfully for '{form_path}'")

    except Exception as e:
        success = False
        error_message = f"Erro durante migração: {str(e)}"
        logger.error(f"❌ Migration error: {error_message}")

    # Redirect back to form with success/error message
    if success:
        logger.info(f"Redirecting to /{form_path}...")
        return redirect(f"/{form_path}")
    else:
        logger.error(f"Migration failed: {error_message}")
        return redirect(f"/{form_path}")
