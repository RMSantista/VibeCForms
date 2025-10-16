"""
Text file adapter for VibeCForms persistence.

This adapter maintains compatibility with the original semicolon-delimited
text file format used by VibeCForms. It implements the BaseRepository
interface while preserving the existing data format and behavior.
"""

import os
import shutil
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from persistence.base import BaseRepository

logger = logging.getLogger(__name__)


class TxtRepository(BaseRepository):
    """
    Repository adapter for semicolon-delimited text files.

    This adapter provides the original VibeCForms persistence behavior,
    storing data in .txt files with semicolon-separated values.

    File format:
        value1;value2;value3
        value4;value5;value6

    Booleans are stored as "True" or "False" strings.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TXT repository adapter.

        Args:
            config: Configuration dictionary with:
                - path: Directory for data files (default: 'src/')
                - delimiter: Field delimiter (default: ';')
                - encoding: File encoding (default: 'utf-8')
                - extension: File extension (default: '.txt')
        """
        self.path = config.get('path', 'src/')
        self.delimiter = config.get('delimiter', ';')
        self.encoding = config.get('encoding', 'utf-8')
        self.extension = config.get('extension', '.txt')

        # Ensure path exists
        Path(self.path).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"TxtRepository initialized: path={self.path}, delimiter={self.delimiter}"
        )

    def _get_file_path(self, form_path: str) -> str:
        """
        Get the file path for a form.

        Args:
            form_path: Form path (e.g., 'contatos', 'financeiro/contas')

        Returns:
            Full file path

        Example:
            'contatos' -> 'src/contatos.txt'
            'financeiro/contas' -> 'src/financeiro_contas.txt'
        """
        # Replace slashes with underscores for flat file storage
        safe_name = form_path.replace("/", "_")
        return os.path.join(self.path, f"{safe_name}{self.extension}")

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (empty text file) for the form."""
        file_path = self._get_file_path(form_path)

        if os.path.exists(file_path):
            logger.debug(f"Storage already exists: {file_path}")
            return False

        # Create empty file
        with open(file_path, 'w', encoding=self.encoding) as f:
            pass

        logger.info(f"Created storage: {file_path}")
        return True

    def read_all(self, form_path: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read all records from the text file."""
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.debug(f"File doesn't exist: {file_path}")
            return []

        with open(file_path, "r", encoding=self.encoding) as f:
            lines = f.readlines()

        forms = []
        field_names = [field["name"] for field in spec["fields"]]

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            values = line.strip().split(self.delimiter)
            if len(values) != len(field_names):
                logger.warning(
                    f"Skipping malformed line {line_num} in {file_path}: "
                    f"expected {len(field_names)} fields, got {len(values)}"
                )
                continue

            form_data = {}
            for i, field in enumerate(spec["fields"]):
                field_name = field["name"]
                field_type = field["type"]
                value = values[i]

                # Convert value based on field type
                if field_type == "checkbox":
                    form_data[field_name] = value == "True"
                elif field_type == "number":
                    try:
                        form_data[field_name] = int(value) if value else 0
                    except ValueError:
                        logger.warning(
                            f"Invalid number value '{value}' for field '{field_name}', "
                            f"using 0"
                        )
                        form_data[field_name] = 0
                else:
                    form_data[field_name] = value

            forms.append(form_data)

        logger.debug(f"Read {len(forms)} records from {file_path}")
        return forms

    def read_one(self, form_path: str, spec: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
        """Read a single record by index."""
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.debug(f"Index {idx} out of bounds for {form_path}")
            return None

        return forms[idx]

    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Insert a new record."""
        # Read existing records
        forms = self.read_all(form_path, spec)

        # Append new record
        forms.append(data)

        # Write all records back
        return self._write_all(form_path, spec, forms)

    def update(self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]) -> bool:
        """Update an existing record."""
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.error(f"Cannot update: index {idx} out of bounds for {form_path}")
            return False

        # Update the record
        forms[idx] = data

        # Write all records back
        return self._write_all(form_path, spec, forms)

    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """Delete a record by index."""
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.error(f"Cannot delete: index {idx} out of bounds for {form_path}")
            return False

        # Remove the record
        forms.pop(idx)

        # Write remaining records back
        return self._write_all(form_path, spec, forms)

    def _write_all(self, form_path: str, spec: Dict[str, Any], forms: List[Dict[str, Any]]) -> bool:
        """
        Write all records to the text file.

        This is a helper method used by create, update, and delete.

        Args:
            form_path: Form path
            spec: Form specification
            forms: List of records to write

        Returns:
            True if successful
        """
        file_path = self._get_file_path(form_path)

        try:
            with open(file_path, "w", encoding=self.encoding) as f:
                for form_data in forms:
                    values = []
                    for field in spec["fields"]:
                        field_name = field["name"]
                        value = form_data.get(field_name, "")

                        # Convert value to string for storage
                        if isinstance(value, bool):
                            values.append(str(value))
                        else:
                            values.append(str(value))

                    f.write(self.delimiter.join(values) + "\n")

            logger.debug(f"Wrote {len(forms)} records to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write to {file_path}: {e}")
            return False

    def drop_storage(self, form_path: str, force: bool = False) -> bool:
        """Remove the text file completely."""
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.debug(f"File doesn't exist: {file_path}")
            return True

        # Check if file has data and force is False
        if not force and self.has_data(form_path):
            logger.warning(
                f"Cannot drop {file_path}: file has data and force=False"
            )
            return False

        try:
            os.remove(file_path)
            logger.info(f"Dropped storage: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop {file_path}: {e}")
            return False

    def exists(self, form_path: str) -> bool:
        """Check if the text file exists."""
        file_path = self._get_file_path(form_path)
        return os.path.exists(file_path)

    def has_data(self, form_path: str) -> bool:
        """Check if the text file has any records."""
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            return False

        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                for line in f:
                    if line.strip():
                        return True
            return False
        except Exception:
            return False

    def migrate_schema(
        self,
        form_path: str,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any]
    ) -> bool:
        """
        Migrate schema when form specification changes.

        For text files, this means:
        - Add new fields: Append empty values to each line
        - Remove fields: Remove corresponding values from each line
        - Reorder fields: Reorder values in each line

        A backup is created before migration.
        """
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.info(f"No file to migrate: {file_path}")
            return True

        # Create backup
        backup_path = self._create_backup(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting migration")
            return False

        try:
            # Read data with old spec
            old_forms = self.read_all(form_path, old_spec)

            # Build mapping of old fields to new fields
            old_field_names = [f["name"] for f in old_spec["fields"]]
            new_field_names = [f["name"] for f in new_spec["fields"]]

            # Migrate each record
            migrated_forms = []
            for old_form in old_forms:
                new_form = {}
                for new_field in new_spec["fields"]:
                    field_name = new_field["name"]
                    field_type = new_field["type"]

                    if field_name in old_form:
                        # Field exists in old data
                        new_form[field_name] = old_form[field_name]
                    else:
                        # New field, use default value
                        new_form[field_name] = self._get_default_value(field_type)

                migrated_forms.append(new_form)

            # Write migrated data with new spec
            success = self._write_all(form_path, new_spec, migrated_forms)

            if success:
                logger.info(
                    f"Successfully migrated {form_path}: "
                    f"{len(old_field_names)} -> {len(new_field_names)} fields, "
                    f"{len(migrated_forms)} records"
                )
            else:
                # Restore from backup on failure
                shutil.copy2(backup_path, file_path)
                logger.error(f"Migration failed, restored from backup")

            return success

        except Exception as e:
            # Restore from backup on error
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            logger.error(f"Migration error: {e}, restored from backup")
            return False

    def create_index(self, form_path: str, field_name: str) -> bool:
        """
        Create index (no-op for text files).

        Text files don't support indexes, so this always returns True.
        """
        logger.debug(f"create_index is no-op for TxtRepository")
        return True

    def _get_default_value(self, field_type: str) -> Any:
        """
        Get default value for a field type.

        Args:
            field_type: Type of field

        Returns:
            Default value appropriate for the type
        """
        if field_type == "checkbox":
            return False
        elif field_type == "number":
            return 0
        else:
            return ""

    def _create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of the file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file, or None on failure
        """
        if not os.path.exists(file_path):
            return None

        # Create backups directory
        backup_dir = os.path.join(self.path, "backups")
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
