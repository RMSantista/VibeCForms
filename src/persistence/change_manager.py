"""
Change detection and coordination for VibeCForms persistence layer.

This module coordinates schema change detection, backend change detection,
and migration execution (to be implemented in migration_manager.py).
"""

import logging
from typing import Dict, Any, Optional, Tuple
from .schema_detector import SchemaChangeDetector, SchemaChange, BackendChange
from .schema_history import get_history
from .config import get_config

# Configure logging
logger = logging.getLogger(__name__)


class ChangeManager:
    """
    Manages change detection and coordination for forms.

    This class acts as a coordinator between:
    - SchemaChangeDetector (detects changes)
    - SchemaHistory (tracks historical state)
    - MigrationManager (executes migrations - to be implemented)
    """

    @staticmethod
    def check_for_changes(
        form_path: str,
        spec: Dict[str, Any],
        backend: str,
        has_data: bool = False,
        record_count: int = 0
    ) -> Tuple[Optional[SchemaChange], Optional[BackendChange]]:
        """
        Check if a form has schema or backend changes.

        Args:
            form_path: Path to the form
            spec: Current form specification
            backend: Current backend type
            has_data: Whether the form has existing data
            record_count: Number of existing records

        Returns:
            Tuple of (SchemaChange, BackendChange) - either can be None if no change
        """
        history = get_history()
        schema_change = None
        backend_change = None

        # Compute current spec hash
        current_hash = SchemaChangeDetector.compute_spec_hash(spec)

        # Check if spec changed
        if history.has_spec_changed(form_path, current_hash):
            # Get old spec from history (if exists)
            form_history = history.get_form_history(form_path)

            if form_history:
                # We have history - need to load old spec to compare
                # For now, we'll skip detailed comparison and just flag it
                # TODO: Store full spec in history or load from backup
                logger.info(f"Spec changed for '{form_path}' (hash changed)")

                # Create a simple schema change notification
                # Detailed detection will be done when we have old spec available
                schema_change = SchemaChange(
                    form_path=form_path,
                    has_data=has_data,
                    requires_confirmation=False  # Will be updated when we detect details
                )
            else:
                # First time seeing this form - no change to detect
                logger.info(f"First time tracking '{form_path}'")

        # Check if backend changed
        last_backend = history.get_last_backend(form_path)
        if last_backend and last_backend != backend:
            backend_change = SchemaChangeDetector.detect_backend_change(
                form_path=form_path,
                old_backend=last_backend,
                new_backend=backend,
                record_count=record_count
            )

        return schema_change, backend_change

    @staticmethod
    def update_tracking(
        form_path: str,
        spec: Dict[str, Any],
        backend: str,
        record_count: int = 0
    ) -> bool:
        """
        Update tracking information after successful operations.

        Args:
            form_path: Path to the form
            spec: Current specification
            backend: Current backend
            record_count: Current record count

        Returns:
            True if successful
        """
        history = get_history()
        spec_hash = SchemaChangeDetector.compute_spec_hash(spec)

        return history.update_form_history(
            form_path=form_path,
            spec_hash=spec_hash,
            backend=backend,
            record_count=record_count
        )

    @staticmethod
    def requires_confirmation(
        schema_change: Optional[SchemaChange],
        backend_change: Optional[BackendChange]
    ) -> bool:
        """
        Check if any detected changes require user confirmation.

        Args:
            schema_change: Detected schema change (or None)
            backend_change: Detected backend change (or None)

        Returns:
            True if confirmation is needed
        """
        if schema_change and schema_change.requires_confirmation:
            return True

        if backend_change and backend_change.requires_confirmation:
            return True

        return False

    @staticmethod
    def get_change_summary(
        schema_change: Optional[SchemaChange],
        backend_change: Optional[BackendChange]
    ) -> str:
        """
        Get a human-readable summary of detected changes.

        Args:
            schema_change: Detected schema change (or None)
            backend_change: Detected backend change (or None)

        Returns:
            Summary string
        """
        parts = []

        if schema_change and schema_change.has_changes():
            parts.append(SchemaChangeDetector.get_confirmation_message(schema_change))

        if backend_change:
            parts.append(SchemaChangeDetector.get_backend_confirmation_message(backend_change))

        if not parts:
            return "Nenhuma alteração detectada."

        return "\n\n".join(parts)


def check_form_changes(
    form_path: str,
    spec: Dict[str, Any],
    has_data: bool = False,
    record_count: int = 0
) -> Tuple[Optional[SchemaChange], Optional[BackendChange]]:
    """
    Convenience function to check for form changes.

    This function automatically gets the current backend from config.

    Args:
        form_path: Path to the form
        spec: Current form specification
        has_data: Whether the form has existing data
        record_count: Number of existing records

    Returns:
        Tuple of (SchemaChange, BackendChange)
    """
    config = get_config()
    backend_config = config.get_backend_config(form_path)
    backend = backend_config.get("type")

    return ChangeManager.check_for_changes(
        form_path=form_path,
        spec=spec,
        backend=backend,
        has_data=has_data,
        record_count=record_count
    )


def update_form_tracking(
    form_path: str,
    spec: Dict[str, Any],
    record_count: int = 0
) -> bool:
    """
    Convenience function to update form tracking.

    Args:
        form_path: Path to the form
        spec: Current specification
        record_count: Current record count

    Returns:
        True if successful
    """
    config = get_config()
    backend_config = config.get_backend_config(form_path)
    backend = backend_config.get("type")

    return ChangeManager.update_tracking(
        form_path=form_path,
        spec=spec,
        backend=backend,
        record_count=record_count
    )
