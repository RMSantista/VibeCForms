"""
Schema history tracking for VibeCForms persistence layer.

This module maintains a history of form specifications and backend configurations
to detect changes and trigger migrations when needed.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class SchemaHistory:
    """
    Manages historical tracking of form schemas and backend configurations.

    Stores the last known state of each form to enable change detection:
    - Last spec hash
    - Last backend type
    - Last update timestamp
    - Record count at last check
    """

    def __init__(self, history_file: Optional[str] = None):
        """
        Initialize schema history manager.

        Args:
            history_file: Path to history JSON file.
                         If None, uses default: src/config/schema_history.json
        """
        if history_file is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            history_file = project_root / "src" / "config" / "schema_history.json"

        self.history_file = Path(history_file)
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """
        Load history from JSON file.

        Returns:
            Dictionary with form history data
        """
        if not self.history_file.exists():
            logger.info(f"History file not found, creating new: {self.history_file}")
            return {}

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            logger.info(f"Loaded schema history from {self.history_file}")
            return history
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in history file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return {}

    def _save_history(self) -> bool:
        """
        Save history to JSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved schema history to {self.history_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving history: {e}")
            return False

    def get_form_history(self, form_path: str) -> Optional[Dict[str, Any]]:
        """
        Get historical data for a specific form.

        Args:
            form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')

        Returns:
            Dictionary with form history or None if no history exists
        """
        return self.history.get(form_path)

    def update_form_history(
        self, form_path: str, spec_hash: str, backend: str, record_count: int = 0
    ) -> bool:
        """
        Update history for a form.

        Args:
            form_path: Path to the form
            spec_hash: MD5 hash of the current spec
            backend: Current backend type (e.g., 'txt', 'sqlite')
            record_count: Number of records in the form

        Returns:
            True if successful
        """
        self.history[form_path] = {
            "last_spec_hash": spec_hash,
            "last_backend": backend,
            "last_updated": datetime.now().isoformat(),
            "record_count": record_count,
        }

        return self._save_history()

    def has_spec_changed(self, form_path: str, current_spec_hash: str) -> bool:
        """
        Check if a form's spec has changed since last check.

        Args:
            form_path: Path to the form
            current_spec_hash: Current spec hash

        Returns:
            True if spec has changed or no history exists
        """
        history = self.get_form_history(form_path)
        if not history:
            return True  # No history = consider it changed (first time)

        last_hash = history.get("last_spec_hash", "")
        return last_hash != current_spec_hash

    def has_backend_changed(self, form_path: str, current_backend: str) -> bool:
        """
        Check if a form's backend has changed since last check.

        Args:
            form_path: Path to the form
            current_backend: Current backend type

        Returns:
            True if backend has changed or no history exists
        """
        history = self.get_form_history(form_path)
        if not history:
            return False  # No history = first time, not a "change"

        last_backend = history.get("last_backend", "")
        return last_backend != current_backend and last_backend != ""

    def get_last_backend(self, form_path: str) -> Optional[str]:
        """
        Get the last known backend for a form.

        Args:
            form_path: Path to the form

        Returns:
            Last backend type or None if no history
        """
        history = self.get_form_history(form_path)
        if not history:
            return None

        return history.get("last_backend")

    def get_last_record_count(self, form_path: str) -> int:
        """
        Get the last known record count for a form.

        Args:
            form_path: Path to the form

        Returns:
            Last record count or 0 if no history
        """
        history = self.get_form_history(form_path)
        if not history:
            return 0

        return history.get("record_count", 0)

    def delete_form_history(self, form_path: str) -> bool:
        """
        Delete history for a form.

        Args:
            form_path: Path to the form

        Returns:
            True if successful
        """
        if form_path in self.history:
            del self.history[form_path]
            return self._save_history()

        return True  # Already doesn't exist

    def get_all_forms(self) -> list:
        """
        Get list of all forms with history.

        Returns:
            List of form paths
        """
        return list(self.history.keys())

    def clear_history(self) -> bool:
        """
        Clear all history data.

        Returns:
            True if successful
        """
        self.history = {}
        return self._save_history()

    def __repr__(self) -> str:
        """String representation of schema history."""
        return f"SchemaHistory(file={self.history_file}, " f"forms={len(self.history)})"


# Global history instance (singleton)
_history_instance: Optional[SchemaHistory] = None


def get_history(history_file: Optional[str] = None) -> SchemaHistory:
    """
    Get the global schema history instance.

    This implements a singleton pattern to ensure only one history
    instance exists throughout the application lifecycle.

    Args:
        history_file: Path to history file (only used on first call)

    Returns:
        SchemaHistory instance
    """
    global _history_instance

    if _history_instance is None:
        _history_instance = SchemaHistory(history_file)

    return _history_instance


def reset_history() -> None:
    """
    Reset the global history instance.

    Useful for testing to force history reload.
    """
    global _history_instance
    _history_instance = None
