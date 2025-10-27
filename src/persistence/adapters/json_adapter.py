"""
JSON file adapter for VibeCForms persistence.

This adapter stores data in JSON format, one file per form.
Ideal for workflows and structured data that benefits from
native JSON representation.
"""

import os
import json
import shutil
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from persistence.base import BaseRepository

logger = logging.getLogger(__name__)


class JSONRepository(BaseRepository):
    """
    Repository adapter for JSON files.

    This adapter provides JSON-based persistence, storing each form
    as a separate .json file containing an array of records.

    File format:
        [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"}
        ]

    Advantages:
    - Native support for complex objects (no serialization needed)
    - Human-readable and editable
    - Better for debugging
    - No delimiter issues
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize JSON repository adapter.

        Args:
            config: Configuration dictionary with:
                - path: Directory for data files (default: 'data/')
                - encoding: File encoding (default: 'utf-8')
                - indent: JSON indentation (default: 2)
                - ensure_ascii: Ensure ASCII encoding (default: False)
        """
        self.path = config.get('path', 'data/')
        self.encoding = config.get('encoding', 'utf-8')
        self.indent = config.get('indent', 2)
        self.ensure_ascii = config.get('ensure_ascii', False)

        # Ensure path exists
        Path(self.path).mkdir(parents=True, exist_ok=True)

        logger.info(f"JSONRepository initialized: path={self.path}")

    def _get_file_path(self, form_path: str) -> str:
        """
        Get the file path for a form.

        Args:
            form_path: Form path (e.g., 'contatos', 'workflows_pedidos_processes')

        Returns:
            Full file path

        Example:
            'contatos' -> 'data/contatos.json'
            'workflows_pedidos_processes' -> 'data/workflows_pedidos_processes.json'
        """
        # Replace slashes with underscores for flat file storage
        safe_name = form_path.replace("/", "_")
        return os.path.join(self.path, f"{safe_name}.json")

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (empty JSON array file) for the form."""
        file_path = self._get_file_path(form_path)

        if os.path.exists(file_path):
            logger.debug(f"Storage already exists: {file_path}")
            return False

        # Create empty JSON array
        with open(file_path, 'w', encoding=self.encoding) as f:
            json.dump([], f)

        logger.info(f"Created storage: {file_path}")
        return True

    def read_all(self, form_path: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read all records from the JSON file."""
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.debug(f"File doesn't exist: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.error(f"Invalid JSON format in {file_path}: expected array, got {type(data)}")
                return []

            logger.debug(f"Read {len(data)} records from {file_path}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []

    def read_one(self, form_path: str, spec: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
        """Read a single record by index."""
        records = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(records):
            logger.debug(f"Index {idx} out of bounds for {form_path}")
            return None

        return records[idx]

    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Insert a new record."""
        # Read existing records
        records = self.read_all(form_path, spec)

        # Append new record
        records.append(data)

        # Write all records back
        return self._write_all(form_path, records)

    def update(self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]) -> bool:
        """Update an existing record."""
        records = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(records):
            logger.error(f"Cannot update: index {idx} out of bounds for {form_path}")
            return False

        # Update the record
        records[idx] = data

        # Write all records back
        return self._write_all(form_path, records)

    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """Delete a record by index."""
        records = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(records):
            logger.error(f"Cannot delete: index {idx} out of bounds for {form_path}")
            return False

        # Remove the record
        records.pop(idx)

        # Write remaining records back
        return self._write_all(form_path, records)

    def drop_storage(self, form_path: str, force: bool = False) -> bool:
        """Remove the JSON file."""
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.debug(f"Storage doesn't exist: {file_path}")
            return False

        # Check if file has data
        if not force:
            records = self.read_all(form_path, {})
            if len(records) > 0:
                logger.warning(
                    f"Cannot drop storage {file_path}: contains {len(records)} records. "
                    f"Use force=True to delete anyway."
                )
                return False

        # Create backup before deleting
        backup_dir = os.path.join(self.path, "backups")
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            backup_dir,
            f"{os.path.basename(file_path)}.{timestamp}.bak"
        )

        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        # Delete the file
        os.remove(file_path)
        logger.info(f"Dropped storage: {file_path}")

        return True

    def exists(self, form_path: str) -> bool:
        """Check if storage exists for the form."""
        file_path = self._get_file_path(form_path)
        return os.path.exists(file_path)

    def has_data(self, form_path: str) -> bool:
        """Check if storage has any records."""
        if not self.exists(form_path):
            return False

        records = self.read_all(form_path, {})
        return len(records) > 0

    def count(self, form_path: str, spec: Dict[str, Any]) -> int:
        """Count total number of records."""
        records = self.read_all(form_path, spec)
        return len(records)

    def _write_all(self, form_path: str, records: List[Dict[str, Any]]) -> bool:
        """
        Write all records to the JSON file.

        This is a helper method used by create, update, and delete.

        Args:
            form_path: Form path
            records: List of record dictionaries

        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(form_path)

        try:
            # Create backup before writing
            if os.path.exists(file_path):
                backup_path = f"{file_path}.bak"
                shutil.copy2(file_path, backup_path)

            # Write to file
            with open(file_path, 'w', encoding=self.encoding) as f:
                json.dump(
                    records,
                    f,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii
                )

            # Remove backup after successful write
            if os.path.exists(f"{file_path}.bak"):
                os.remove(f"{file_path}.bak")

            logger.debug(f"Wrote {len(records)} records to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")

            # Restore backup if write failed
            backup_path = f"{file_path}.bak"
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                os.remove(backup_path)
                logger.info(f"Restored backup after write failure")

            return False

    # ========== SCHEMA MIGRATION METHODS ==========

    def migrate_schema(self, form_path: str, old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> bool:
        """
        Migrate storage schema when form specification changes.

        For JSON, this is relatively straightforward since JSON is schema-less.
        We just add missing fields with default values and keep all existing data.

        Args:
            form_path: Path to the form
            old_spec: Previous form specification
            new_spec: New form specification

        Returns:
            True if migration was successful
        """
        records = self.read_all(form_path, old_spec)

        # Get old and new field names
        old_fields = {f["name"] for f in old_spec.get("fields", [])}
        new_fields = {f["name"] for f in new_spec.get("fields", [])}

        # Fields that were added
        added_fields = new_fields - old_fields

        # Add new fields with default values
        for record in records:
            for field_name in added_fields:
                if field_name not in record:
                    record[field_name] = ""

        # Write updated records
        return self._write_all(form_path, records)

    def create_index(self, form_path: str, field_name: str) -> bool:
        """
        Create an index on a specific field.

        For JSON files, indexes are not applicable (data is loaded into memory).
        This method returns True as a no-op.

        Args:
            form_path: Path to the form
            field_name: Name of the field to index

        Returns:
            True (no-op for JSON)
        """
        logger.debug(f"Index creation not applicable for JSON backend: {form_path}.{field_name}")
        return True

    def rename_field(self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str) -> bool:
        """
        Rename a field in all records.

        Args:
            form_path: Path to the form
            spec: Updated form specification
            old_name: Current name of the field
            new_name: New name for the field

        Returns:
            True if field was renamed successfully
        """
        records = self.read_all(form_path, spec)

        for record in records:
            if old_name in record:
                record[new_name] = record.pop(old_name)

        return self._write_all(form_path, records)

    def change_field_type(
        self,
        form_path: str,
        spec: Dict[str, Any],
        field_name: str,
        old_type: str,
        new_type: str
    ) -> bool:
        """
        Change the type of a field, attempting to convert existing data.

        For JSON, types are flexible. We just attempt conversion where possible.

        Args:
            form_path: Path to the form
            spec: Updated form specification
            field_name: Name of the field to change
            old_type: Current type of the field
            new_type: New type for the field

        Returns:
            True if type was changed successfully
        """
        records = self.read_all(form_path, spec)

        for record in records:
            if field_name in record:
                try:
                    # Attempt conversion based on new type
                    if new_type == "number":
                        record[field_name] = int(record[field_name])
                    elif new_type == "checkbox":
                        record[field_name] = bool(record[field_name])
                    elif new_type == "text":
                        record[field_name] = str(record[field_name])
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    logger.warning(
                        f"Could not convert field '{field_name}' from {old_type} to {new_type}, "
                        f"keeping original value"
                    )

        return self._write_all(form_path, records)

    def remove_field(self, form_path: str, spec: Dict[str, Any], field_name: str) -> bool:
        """
        Remove a field from all records.

        This is a destructive operation that permanently deletes field data.

        Args:
            form_path: Path to the form
            spec: Updated form specification
            field_name: Name of the field to remove

        Returns:
            True if field was removed successfully
        """
        records = self.read_all(form_path, spec)

        for record in records:
            if field_name in record:
                del record[field_name]

        return self._write_all(form_path, records)
