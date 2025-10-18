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
from persistence.schema_detector import SchemaChangeDetector, ChangeType

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

        This method now uses change detection to intelligently handle:
        - Rename fields: Preserves data while renaming
        - Change field types: Converts data to new type
        - Remove fields: Deletes field and data (with backup)
        - Add fields: Adds new fields with default values

        A backup is created before migration.
        """
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.info(f"No file to migrate: {file_path}")
            return True

        # Detect schema changes
        has_data = self.has_data(form_path)
        schema_change = SchemaChangeDetector.detect_changes(
            form_path=form_path,
            old_spec=old_spec,
            new_spec=new_spec,
            has_data=has_data
        )

        if not schema_change.has_changes():
            logger.info(f"No schema changes detected for {form_path}")
            return True

        logger.info(f"Detected changes for {form_path}: {schema_change.get_summary()}")

        # Create backup before any changes
        backup_path = self._create_backup(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting migration")
            return False

        try:
            # Process changes in order: renames, type changes, removes, adds
            current_spec = old_spec.copy()

            # 1. Process field renames first (preserves data)
            for change in schema_change.changes:
                if change.change_type == ChangeType.RENAME_FIELD:
                    logger.info(f"Renaming field '{change.old_name}' to '{change.new_name}'")

                    # Update current_spec to reflect the rename
                    for field in current_spec["fields"]:
                        if field["name"] == change.old_name:
                            field["name"] = change.new_name
                            break

                    # Execute rename
                    if not self.rename_field(form_path, current_spec, change.old_name, change.new_name):
                        raise Exception(f"Failed to rename field '{change.old_name}'")

            # 2. Process type changes
            for change in schema_change.changes:
                if change.change_type == ChangeType.CHANGE_TYPE:
                    logger.info(f"Changing type of '{change.field_name}' from {change.old_type} to {change.new_type}")

                    # Update current_spec to reflect the type change
                    for field in current_spec["fields"]:
                        if field["name"] == change.field_name:
                            field["type"] = change.new_type
                            break

                    # Execute type change
                    if not self.change_field_type(form_path, current_spec, change.field_name, change.old_type, change.new_type):
                        raise Exception(f"Failed to change type of field '{change.field_name}'")

            # 3. Process field removals (destructive)
            for change in schema_change.changes:
                if change.change_type == ChangeType.REMOVE_FIELD:
                    logger.warning(f"Removing field '{change.field_name}' (data will be lost)")

                    # Remove from current_spec
                    current_spec["fields"] = [f for f in current_spec["fields"] if f["name"] != change.field_name]

                    # Execute removal
                    if not self.remove_field(form_path, current_spec, change.field_name):
                        raise Exception(f"Failed to remove field '{change.field_name}'")

            # 4. Process field additions (safe)
            added_fields = []
            for change in schema_change.changes:
                if change.change_type == ChangeType.ADD_FIELD:
                    logger.info(f"Adding new field '{change.field_name}' with type {change.field_type}")
                    added_fields.append(change)

            # Add new fields by reading all data and writing with new spec
            if added_fields:
                forms = self.read_all(form_path, current_spec)

                # Add new fields to current_spec
                for change in added_fields:
                    current_spec["fields"].append({
                        "name": change.field_name,
                        "type": change.field_type
                    })

                # Add default values for new fields in each record
                for form in forms:
                    for change in added_fields:
                        form[change.field_name] = self._get_default_value(change.field_type)

                # Write with new spec
                if not self._write_all(form_path, current_spec, forms):
                    raise Exception("Failed to add new fields")

            logger.info(f"Successfully migrated schema for {form_path}")
            return True

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

    def rename_field(self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str) -> bool:
        """
        Rename a field in the text file, preserving all data.

        This reads all data, renames the field in each record, and writes back.
        The spec parameter should already have the new field name.

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field name)
            old_name: Current name of the field
            new_name: New name for the field

        Returns:
            True if field was renamed successfully
        """
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.warning(f"Cannot rename field: file doesn't exist: {file_path}")
            return False

        # Create backup
        backup_path = self._create_backup(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting rename")
            return False

        try:
            # Create a temporary old spec for reading current data
            old_spec = {"fields": []}
            for field in spec["fields"]:
                if field["name"] == new_name:
                    # This is the renamed field, use old name for reading
                    old_field = field.copy()
                    old_field["name"] = old_name
                    old_spec["fields"].append(old_field)
                else:
                    old_spec["fields"].append(field)

            # Read data with old field name
            forms = self.read_all(form_path, old_spec)

            # Rename field in each record
            for form in forms:
                if old_name in form:
                    form[new_name] = form.pop(old_name)

            # Write with new spec
            success = self._write_all(form_path, spec, forms)

            if success:
                logger.info(f"Successfully renamed field '{old_name}' to '{new_name}' in {form_path}")
            else:
                # Restore from backup
                shutil.copy2(backup_path, file_path)
                logger.error(f"Rename failed, restored from backup")

            return success

        except Exception as e:
            # Restore from backup on error
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            logger.error(f"Rename error: {e}, restored from backup")
            return False

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

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field type)
            field_name: Name of the field to change
            old_type: Current type of the field
            new_type: New type for the field

        Returns:
            True if type was changed and data converted successfully
        """
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.warning(f"Cannot change field type: file doesn't exist: {file_path}")
            return False

        # Create backup
        backup_path = self._create_backup(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting type change")
            return False

        try:
            # Read all data
            forms = self.read_all(form_path, spec)

            # Convert each record's field value
            conversion_errors = 0
            for i, form in enumerate(forms):
                if field_name in form:
                    old_value = form[field_name]

                    try:
                        # Attempt conversion based on new type
                        if new_type == "number" or new_type == "range":
                            # Convert to number
                            if isinstance(old_value, (int, float)):
                                new_value = int(old_value)
                            elif isinstance(old_value, str):
                                new_value = int(old_value) if old_value else 0
                            elif isinstance(old_value, bool):
                                new_value = 1 if old_value else 0
                            else:
                                new_value = 0

                        elif new_type == "checkbox":
                            # Convert to boolean
                            if isinstance(old_value, bool):
                                new_value = old_value
                            elif isinstance(old_value, (int, float)):
                                new_value = old_value != 0
                            elif isinstance(old_value, str):
                                new_value = old_value.lower() in ('true', '1', 'yes', 'sim')
                            else:
                                new_value = False

                        else:
                            # Convert to string (always safe)
                            new_value = str(old_value)

                        form[field_name] = new_value

                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Failed to convert record {i} field '{field_name}' "
                            f"from {old_type} to {new_type}: {e}"
                        )
                        conversion_errors += 1
                        # Use default value on conversion failure
                        form[field_name] = self._get_default_value(new_type)

            # If too many conversion errors, abort
            if conversion_errors > len(forms) * 0.5:  # More than 50% failed
                logger.error(
                    f"Too many conversion errors ({conversion_errors}/{len(forms)}), "
                    f"aborting type change"
                )
                shutil.copy2(backup_path, file_path)
                return False

            # Write converted data
            success = self._write_all(form_path, spec, forms)

            if success:
                logger.info(
                    f"Successfully changed field '{field_name}' type from {old_type} to {new_type} "
                    f"in {form_path} ({conversion_errors} conversion warnings)"
                )
            else:
                # Restore from backup
                shutil.copy2(backup_path, file_path)
                logger.error(f"Type change failed, restored from backup")

            return success

        except Exception as e:
            # Restore from backup on error
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            logger.error(f"Type change error: {e}, restored from backup")
            return False

    def remove_field(self, form_path: str, spec: Dict[str, Any], field_name: str) -> bool:
        """
        Remove a field from the text file (destructive operation).

        This permanently deletes all data in this field!
        The spec parameter should already NOT contain the removed field.

        Args:
            form_path: Path to the form
            spec: Updated form specification (without the removed field)
            field_name: Name of the field to remove

        Returns:
            True if field was removed successfully
        """
        file_path = self._get_file_path(form_path)

        if not os.path.exists(file_path):
            logger.warning(f"Cannot remove field: file doesn't exist: {file_path}")
            return False

        # Create backup (important for destructive operation!)
        backup_path = self._create_backup(file_path)
        if not backup_path:
            logger.error("Failed to create backup, aborting field removal")
            return False

        try:
            # Create a temporary old spec that includes the removed field
            old_spec = {"fields": list(spec["fields"])}
            # Find where the removed field should be inserted (maintain order if possible)
            # For simplicity, add it at the end
            old_spec["fields"].append({"name": field_name, "type": "text"})

            # Read all data with old spec
            forms = self.read_all(form_path, old_spec)

            # Remove field from each record
            for form in forms:
                if field_name in form:
                    del form[field_name]

            # Write with new spec (without the removed field)
            success = self._write_all(form_path, spec, forms)

            if success:
                logger.warning(
                    f"Field '{field_name}' permanently removed from {form_path} "
                    f"({len(forms)} records affected)"
                )
            else:
                # Restore from backup
                shutil.copy2(backup_path, file_path)
                logger.error(f"Field removal failed, restored from backup")

            return success

        except Exception as e:
            # Restore from backup on error
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            logger.error(f"Field removal error: {e}, restored from backup")
            return False

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
