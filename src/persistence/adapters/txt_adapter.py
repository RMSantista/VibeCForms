"""
Text file adapter for VibeCForms persistence.

This adapter maintains compatibility with the original semicolon-delimited
text file format used by VibeCForms. It implements the BaseRepository
interface while preserving the existing data format and behavior.
"""

import os
import shutil
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from persistence.base import BaseRepository
from persistence.schema_detector import SchemaChangeDetector, ChangeType
from persistence.contracts.relationship_interface import IRelationshipRepository
from utils.crockford import generate_id

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
                - path: Directory for data files (default: 'data/txt/')
                - delimiter: Field delimiter (default: ';')
                - encoding: File encoding (default: 'utf-8')
                - extension: File extension (default: '.txt')
        """
        self.path = config.get("path", "data/txt/")
        self.delimiter = config.get("delimiter", ";")
        self.encoding = config.get("encoding", "utf-8")
        self.extension = config.get("extension", ".txt")

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

    def _get_tags_file_path(self) -> str:
        """Get the path to the global tags file."""
        return os.path.join(self.path, "tags.txt")

    def _read_all_tags(self) -> List[Dict[str, Any]]:
        """Read all tags from the tags file."""
        tags_file = self._get_tags_file_path()

        if not os.path.exists(tags_file):
            return []

        tags = []
        try:
            with open(tags_file, "r", encoding=self.encoding) as f:
                for line in f:
                    if not line.strip():
                        continue

                    parts = line.strip().split(self.delimiter)
                    if len(parts) < 7:
                        continue

                    tags.append(
                        {
                            "object_type": parts[0],
                            "object_id": parts[1],
                            "tag": parts[2],
                            "applied_at": parts[3],
                            "applied_by": parts[4],
                            "removed_at": parts[5] if parts[5] else None,
                            "removed_by": parts[6] if parts[6] else None,
                            "metadata": (
                                json.loads(parts[7])
                                if len(parts) > 7 and parts[7]
                                else None
                            ),
                        }
                    )
        except FileNotFoundError:
            logger.debug(f"Tags file not found: {tags_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in tags file {tags_file}: {e}")
            return []
        except PermissionError as e:
            logger.error(f"Permission denied reading tags: {e}")
            return []

        return tags

    def _write_all_tags(self, tags: List[Dict[str, Any]]) -> bool:
        """Write all tags to the tags file."""
        tags_file = self._get_tags_file_path()

        try:
            os.makedirs(os.path.dirname(tags_file), exist_ok=True)

            with open(tags_file, "w", encoding=self.encoding) as f:
                for tag in tags:
                    parts = [
                        tag["object_type"],
                        tag["object_id"],
                        tag["tag"],
                        tag["applied_at"],
                        tag["applied_by"],
                        tag.get("removed_at") or "",
                        tag.get("removed_by") or "",
                        json.dumps(tag.get("metadata")) if tag.get("metadata") else "",
                    ]
                    f.write(self.delimiter.join(parts) + "\n")

            return True

        except Exception as e:
            logger.error(f"Failed to write tags file: {e}")
            return False

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (empty text file) for the form."""
        file_path = self._get_file_path(form_path)

        if os.path.exists(file_path):
            logger.debug(f"Storage already exists: {file_path}")
            return False

        # Create empty file
        with open(file_path, "w", encoding=self.encoding) as f:
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

            # Check if we have the expected number of fields
            # New format: record_id + field values (len = 1 + len(field_names))
            # Old format: just field values (len = len(field_names))
            expected_with_id = len(field_names) + 1
            expected_without_id = len(field_names)

            if len(values) == expected_with_id:
                # New format with record_id
                record_id = values[0]
                field_values = values[1:]
            elif len(values) == expected_without_id:
                # Old format without record_id (backwards compatibility)
                record_id = ""
                field_values = values
            else:
                logger.warning(
                    f"Skipping malformed line {line_num} in {file_path}: "
                    f"expected {expected_with_id} or {expected_without_id} fields, got {len(values)}"
                )
                continue

            form_data = {}

            for i, field in enumerate(spec["fields"]):
                field_name = field["name"]
                field_type = field["type"]
                value = field_values[i]

                # Convert value based on field type
                if field_type == "checkbox":
                    form_data[field_name] = value == "True"
                elif field_type == "number":
                    if value:
                        try:
                            # Check if field should use decimal (float) instead of integer
                            # Convention: fields named valor, preco, custo, price, cost, amount use decimals
                            # Configuration: explicit "decimal": true in field spec
                            is_decimal = field.get(
                                "decimal", False
                            ) or field_name.lower() in [
                                "valor",
                                "preco",
                                "custo",
                                "price",
                                "cost",
                                "amount",
                                "total",
                                "subtotal",
                                "desconto",
                                "discount",
                                "taxa",
                                "fee",
                                "valor_total",
                                "valor_unitario",
                                "preco_unitario",
                                "valor_desconto",
                            ]
                            if is_decimal:
                                form_data[field_name] = float(value)
                            else:
                                form_data[field_name] = int(value)
                        except ValueError as e:
                            raise ValueError(
                                f"Invalid number value '{value}' for field '{field_name}' "
                                f"(line {line_num}): {e}"
                            )
                    else:
                        form_data[field_name] = 0
                else:
                    form_data[field_name] = value

            # Store record_id internally for ID-based operations (not exposed in read_all)
            # Generate UUID for old records without one (migration scenario)
            if not record_id:
                record_id = generate_id()
                logger.info(
                    f"Generated UUID {record_id} for legacy record without UUID in {form_path}"
                )
            form_data["_record_id"] = record_id

            forms.append(form_data)

        logger.debug(f"Read {len(forms)} records from {file_path}")
        return forms

    def read_one(
        self, form_path: str, spec: Dict[str, Any], idx: int
    ) -> Optional[Dict[str, Any]]:
        """Read a single record by index."""
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.debug(f"Index {idx} out of bounds for {form_path}")
            return None

        return forms[idx]

    def create(
        self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]
    ) -> Optional[str]:
        """Insert a new record and return its UUID."""
        # Use existing UUID if provided (for migrations), otherwise generate new one
        record_id = data.get("_record_id") or generate_id()

        # Read existing records
        forms = self.read_all(form_path, spec)

        # Add record_id to data
        data_with_id = {**data, "_record_id": record_id}

        # Append new record
        forms.append(data_with_id)

        # Write all records back
        if self._write_all(form_path, spec, forms):
            return record_id
        return None

    def update(
        self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]
    ) -> bool:
        """Update an existing record."""
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.error(f"Cannot update: index {idx} out of bounds for {form_path}")
            return False

        # Preserve the record_id when updating, generate if missing (migration scenario)
        record_id = forms[idx].get("_record_id") or generate_id()
        updated_data = {**data, "_record_id": record_id}

        # Update the record
        forms[idx] = updated_data

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

    def _write_all(
        self, form_path: str, spec: Dict[str, Any], forms: List[Dict[str, Any]]
    ) -> bool:
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

                    # First, write record_id (generate if missing - all records MUST have UUID)
                    record_id = form_data.get("_record_id")
                    if not record_id:
                        record_id = generate_id()
                        form_data["_record_id"] = record_id
                        logger.warning(
                            f"Generated UUID {record_id} for record without UUID during write to {form_path}"
                        )
                    values.append(record_id)

                    # Then write field values
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
            logger.warning(f"Cannot drop {file_path}: file has data and force=False")
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
        self, form_path: str, old_spec: Dict[str, Any], new_spec: Dict[str, Any]
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
            form_path=form_path, old_spec=old_spec, new_spec=new_spec, has_data=has_data
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
                    logger.info(
                        f"Renaming field '{change.old_name}' to '{change.new_name}'"
                    )

                    # Update current_spec to reflect the rename
                    for field in current_spec["fields"]:
                        if field["name"] == change.old_name:
                            field["name"] = change.new_name
                            break

                    # Execute rename
                    if not self.rename_field(
                        form_path, current_spec, change.old_name, change.new_name
                    ):
                        raise Exception(f"Failed to rename field '{change.old_name}'")

            # 2. Process type changes
            for change in schema_change.changes:
                if change.change_type == ChangeType.CHANGE_TYPE:
                    logger.info(
                        f"Changing type of '{change.field_name}' from {change.old_type} to {change.new_type}"
                    )

                    # Update current_spec to reflect the type change
                    for field in current_spec["fields"]:
                        if field["name"] == change.field_name:
                            field["type"] = change.new_type
                            break

                    # Execute type change
                    if not self.change_field_type(
                        form_path,
                        current_spec,
                        change.field_name,
                        change.old_type,
                        change.new_type,
                    ):
                        raise Exception(
                            f"Failed to change type of field '{change.field_name}'"
                        )

            # 3. Process field removals (destructive)
            for change in schema_change.changes:
                if change.change_type == ChangeType.REMOVE_FIELD:
                    logger.warning(
                        f"Removing field '{change.field_name}' (data will be lost)"
                    )

                    # Remove from current_spec
                    current_spec["fields"] = [
                        f
                        for f in current_spec["fields"]
                        if f["name"] != change.field_name
                    ]

                    # Execute removal
                    if not self.remove_field(
                        form_path, current_spec, change.field_name
                    ):
                        raise Exception(f"Failed to remove field '{change.field_name}'")

            # 4. Process field additions (safe)
            added_fields = []
            for change in schema_change.changes:
                if change.change_type == ChangeType.ADD_FIELD:
                    logger.info(
                        f"Adding new field '{change.field_name}' with type {change.field_type}"
                    )
                    added_fields.append(change)

            # Add new fields by reading all data and writing with new spec
            if added_fields:
                forms = self.read_all(form_path, current_spec)

                # Add new fields to current_spec
                for change in added_fields:
                    current_spec["fields"].append(
                        {"name": change.field_name, "type": change.field_type}
                    )

                # Add default values for new fields in each record
                for form in forms:
                    for change in added_fields:
                        form[change.field_name] = self._get_default_value(
                            change.field_type
                        )

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

    def rename_field(
        self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str
    ) -> bool:
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
                logger.info(
                    f"Successfully renamed field '{old_name}' to '{new_name}' in {form_path}"
                )
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
        new_type: str,
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
                                new_value = old_value.lower() in (
                                    "true",
                                    "1",
                                    "yes",
                                    "sim",
                                )
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

    def remove_field(
        self, form_path: str, spec: Dict[str, Any], field_name: str
    ) -> bool:
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

    # =========================================================================
    # NEW ID-BASED CRUD METHODS (Stub implementations for FASE 3)
    # =========================================================================

    def read_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Read a single record by its unique ID."""
        forms = self.read_all(form_path, spec)

        for form in forms:
            if form.get("_record_id") == record_id:
                return form

        logger.debug(f"No record found with ID {record_id} in {form_path}")
        return None

    def update_by_id(
        self,
        form_path: str,
        spec: Dict[str, Any],
        record_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """Update an existing record by its ID."""
        forms = self.read_all(form_path, spec)

        # Find and update the record
        found = False
        for i, form in enumerate(forms):
            if form.get("_record_id") == record_id:
                # Preserve record_id when updating
                updated_data = {**data, "_record_id": record_id}
                forms[i] = updated_data
                found = True
                break

        if not found:
            logger.warning(f"No record found with ID {record_id} in {form_path}")
            return False

        # Write all records back
        return self._write_all(form_path, spec, forms)

    def delete_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> bool:
        """Delete a record by its unique ID."""
        forms = self.read_all(form_path, spec)

        # Filter out the record to delete
        original_count = len(forms)
        forms = [f for f in forms if f.get("_record_id") != record_id]

        if len(forms) == original_count:
            logger.warning(f"No record found with ID {record_id} in {form_path}")
            return False

        return self._write_all(form_path, spec, forms)

    # =========================================================================
    # SEARCH METHOD (for search autocomplete fields)
    # =========================================================================

    def search(
        self,
        form_path: str,
        spec: Dict[str, Any],
        field_name: str,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Search for records matching a query string in a specific field.

        Uses file scanning with early termination after reaching limit.
        Case-insensitive search optimized for TXT files.
        """
        if not self.exists(form_path):
            logger.warning(f"Cannot search: file does not exist for {form_path}")
            return []

        if not query or not query.strip():
            return []

        file_path = self._get_file_path(form_path)
        query_lower = query.lower()

        # Find field index in spec
        field_index = None
        for i, field in enumerate(spec.get("fields", [])):
            if field["name"] == field_name:
                field_index = i + 1  # +1 because record_id is first column
                break

        if field_index is None:
            logger.error(f"Field '{field_name}' not found in spec for {form_path}")
            return []

        results = []
        seen = set()  # Track unique values

        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                for line in f:
                    # Early termination if we have enough results
                    if len(results) >= limit:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(self.delimiter)

                    # Check if field index is valid for this line
                    if field_index >= len(parts):
                        continue

                    field_value = parts[field_index].strip()

                    # Skip empty values
                    if not field_value:
                        continue

                    # Case-insensitive substring match
                    if query_lower in field_value.lower():
                        # Only add if not seen before (DISTINCT)
                        if field_value not in seen:
                            seen.add(field_value)
                            results.append(field_value)

            # Sort results alphabetically
            results.sort()

            logger.debug(
                f"Search '{query}' in {form_path}.{field_name}: {len(results)} results"
            )
            return results

        except Exception as e:
            logger.error(f"Search failed in {form_path}.{field_name}: {e}")
            return []

    # =========================================================================
    # TAG MANAGEMENT METHODS (Stub implementations for FASE 3)
    # =========================================================================

    def add_tag(
        self,
        object_type: str,
        object_id: str,
        tag: str,
        applied_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a tag to an object."""
        # Check if tag already exists and is active
        if self.has_tag(object_type, object_id, tag):
            logger.debug(f"Tag '{tag}' already exists for {object_type}:{object_id}")
            return False

        tags = self._read_all_tags()

        new_tag = {
            "object_type": object_type,
            "object_id": object_id,
            "tag": tag,
            "applied_at": datetime.now().isoformat(),
            "applied_by": applied_by,
            "removed_at": None,
            "removed_by": None,
            "metadata": metadata,
        }

        tags.append(new_tag)

        if self._write_all_tags(tags):
            logger.debug(f"Added tag '{tag}' to {object_type}:{object_id}")
            return True

        return False

    def remove_tag(
        self, object_type: str, object_id: str, tag: str, removed_by: str
    ) -> bool:
        """Remove a tag from an object."""
        # Check if tag exists and is active
        if not self.has_tag(object_type, object_id, tag):
            logger.debug(f"Tag '{tag}' not found for {object_type}:{object_id}")
            return False

        tags = self._read_all_tags()

        # Find and mark tag as removed
        found = False
        for t in tags:
            if (
                t["object_type"] == object_type
                and t["object_id"] == object_id
                and t["tag"] == tag
                and t["removed_at"] is None
            ):
                t["removed_at"] = datetime.now().isoformat()
                t["removed_by"] = removed_by
                found = True
                break

        if found and self._write_all_tags(tags):
            logger.debug(f"Removed tag '{tag}' from {object_type}:{object_id}")
            return True

        return False

    def get_tags(
        self, object_type: str, object_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all tags for an object."""
        all_tags = self._read_all_tags()

        result = []
        for t in all_tags:
            if t["object_type"] == object_type and t["object_id"] == object_id:
                if active_only and t["removed_at"] is not None:
                    continue

                tag_data = {
                    "tag": t["tag"],
                    "applied_at": t["applied_at"],
                    "applied_by": t["applied_by"],
                    "metadata": t.get("metadata"),
                }

                if not active_only:
                    tag_data["removed_at"] = t.get("removed_at")
                    tag_data["removed_by"] = t.get("removed_by")

                result.append(tag_data)

        return result

    def has_tag(self, object_type: str, object_id: str, tag: str) -> bool:
        """Check if an object has a specific tag."""
        tags = self._read_all_tags()

        for t in tags:
            if (
                t["object_type"] == object_type
                and t["object_id"] == object_id
                and t["tag"] == tag
                and t["removed_at"] is None
            ):
                return True

        return False

    def get_objects_by_tag(
        self, object_type: str, tag: str, active_only: bool = True
    ) -> List[str]:
        """Get all object IDs with a specific tag."""
        all_tags = self._read_all_tags()

        object_ids = set()
        for t in all_tags:
            if t["object_type"] == object_type and t["tag"] == tag:
                if active_only and t["removed_at"] is not None:
                    continue

                object_ids.add(t["object_id"])

        return list(object_ids)

    def get_tag_history(
        self, object_type: str, object_id: str, tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get complete tag history for an object."""
        all_tags = self._read_all_tags()

        history = []
        for t in all_tags:
            if t["object_type"] == object_type and t["object_id"] == object_id:
                if tag and t["tag"] != tag:
                    continue

                history.append(
                    {
                        "tag": t["tag"],
                        "applied_at": t["applied_at"],
                        "applied_by": t["applied_by"],
                        "removed_at": t.get("removed_at"),
                        "removed_by": t.get("removed_by"),
                        "metadata": t.get("metadata"),
                        "is_active": t.get("removed_at") is None,
                    }
                )

        return history

    def get_tag_statistics(self, object_type: str) -> Dict[str, int]:
        """Get statistics about tag usage."""
        all_tags = self._read_all_tags()

        stats = {}
        for t in all_tags:
            if t["object_type"] == object_type and t["removed_at"] is None:
                tag_name = t["tag"]
                if tag_name not in stats:
                    stats[tag_name] = 0
                stats[tag_name] += 1

        # Sort by count descending, then by tag name
        return dict(sorted(stats.items(), key=lambda x: (-x[1], x[0])))

    # =========================================================================
    # BULK OPERATIONS (Performance Optimization)
    # =========================================================================

    def bulk_create(
        self, form_path: str, spec: Dict[str, Any], records: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Optimized bulk insert for multiple records using a single file write.

        Performance improvement:
        - Single read + single write instead of N reads + N writes
        - Reduces I/O from O(n²) to O(n)
        - File grows linearly instead of being rewritten N times

        For 19 records with 10 existing: O(n²) = 19 * (10+N) ops → O(n) = 1 + 1 ops
        Estimated speedup: ~100x faster for moderate datasets

        Args:
            form_path: Path to the form
            spec: Form specification
            records: List of dictionaries containing field values

        Returns:
            List of UUIDs for created records
        """
        if not records:
            return []

        # Read existing records once
        existing_forms = self.read_all(form_path, spec)

        # Prepare all new records with UUIDs
        record_ids = []
        new_forms = []

        for record in records:
            # Use existing UUID if provided (for migrations), otherwise generate new one
            record_id = record.get("_record_id") or generate_id()
            record_ids.append(record_id)

            # Add record_id to data
            data_with_id = {**record, "_record_id": record_id}
            new_forms.append(data_with_id)

        # Combine existing and new records
        all_forms = existing_forms + new_forms

        # Write all records in a single operation
        if self._write_all(form_path, spec, all_forms):
            logger.info(f"Bulk inserted {len(records)} records into {form_path}")
            return record_ids
        else:
            logger.error(f"Failed to bulk insert into {form_path}")
            # Return None for all records on failure
            return [None] * len(records)

    # =========================================================================
    # RELATIONSHIP REPOSITORY ACCESS
    # =========================================================================

    def get_relationship_repository(self) -> Optional[IRelationshipRepository]:
        """TXT backend does not support relationships."""
        logger.warning("Relationships are not supported in TXT backend")
        return None
