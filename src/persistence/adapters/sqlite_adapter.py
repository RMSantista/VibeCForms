"""
SQLite adapter for VibeCForms persistence.

This adapter provides SQLite database storage for VibeCForms, offering
better performance, ACID transactions, and support for indexes compared
to text files.
"""

import os
import sqlite3
import shutil
import logging
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from persistence.base import BaseRepository
from persistence.schema_detector import SchemaChangeDetector, ChangeType
from utils.crockford import generate_id

logger = logging.getLogger(__name__)


class SQLiteRepository(BaseRepository):
    """
    Repository adapter for SQLite database.

    Provides local, zero-configuration database storage with:
    - ACID transactions
    - Support for indexes
    - Better performance for large datasets
    - Schema migrations

    Each form gets its own table in the database.
    """

    # Type mapping: VibeCForms field type -> SQLite type
    TYPE_MAPPING = {
        "text": "TEXT",
        "tel": "TEXT",
        "email": "TEXT",
        "password": "TEXT",
        "url": "TEXT",
        "search": "TEXT",
        "textarea": "TEXT",
        "number": "INTEGER",
        "checkbox": "BOOLEAN",
        "date": "DATE",
        "time": "TEXT",
        "datetime-local": "TEXT",
        "month": "TEXT",
        "week": "TEXT",
        "select": "TEXT",
        "radio": "TEXT",
        "color": "TEXT",
        "range": "INTEGER",
        "hidden": "TEXT",
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite repository adapter.

        Args:
            config: Configuration dictionary with:
                - database: Path to SQLite database file
                - timeout: Connection timeout in seconds (default: 10)
                - check_same_thread: SQLite check_same_thread parameter
        """
        self.database = config.get("database", "data/sqlite/vibecforms.db")
        self.timeout = config.get("timeout", 10)
        self.check_same_thread = config.get("check_same_thread", False)

        # Ensure database directory exists
        db_dir = os.path.dirname(self.database)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"SQLiteRepository initialized: database={self.database}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.

        Returns:
            sqlite3.Connection object
        """
        conn = sqlite3.connect(
            self.database,
            timeout=self.timeout,
            check_same_thread=self.check_same_thread,
        )
        # Return rows as dictionaries
        conn.row_factory = sqlite3.Row
        return conn

    def _get_table_name(self, form_path: str) -> str:
        """
        Get the table name for a form.

        Args:
            form_path: Form path (e.g., 'contatos', 'financeiro/contas')

        Returns:
            Table name (e.g., 'contatos', 'financeiro_contas')
        """
        # Replace slashes with underscores for SQL table names
        return form_path.replace("/", "_")

    def _validate_field_name(self, field_name: str) -> bool:
        """Validate that field name contains only safe characters."""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field_name))

    def _ensure_tags_table(self) -> None:
        """Ensure the tags table exists in the database."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            applied_by TEXT NOT NULL,
            removed_at TEXT,
            removed_by TEXT,
            metadata TEXT
        )
        """

        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_tags_object ON tags(object_type, object_id);
        CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(object_type, tag);
        CREATE INDEX IF NOT EXISTS idx_tags_active ON tags(object_type, object_id, removed_at);
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_sql)
            cursor.executescript(index_sql)
            conn.commit()
            conn.close()
            logger.debug("Tags table ensured")
        except Exception as e:
            logger.error(f"Failed to ensure tags table: {e}")
            raise

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (table) for the form."""
        table_name = self._get_table_name(form_path)

        if self.exists(form_path):
            logger.debug(f"Table already exists: {table_name}")
            return False

        # Validate field names before creating table
        for field in spec["fields"]:
            field_name = field["name"]
            if not self._validate_field_name(field_name):
                logger.error(f"Invalid field name: {field_name}")
                raise ValueError(
                    f"Invalid field name '{field_name}'. Use only letters, numbers, and underscore."
                )

        # Build CREATE TABLE statement
        columns = [
            "record_id TEXT PRIMARY KEY",  # UUID Crockford Base32 as PRIMARY KEY
        ]

        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            sql_type = self.TYPE_MAPPING.get(field_type, "TEXT")

            # Add NOT NULL constraint for required fields (except checkbox)
            required = field.get("required", False)
            constraint = " NOT NULL" if required and field_type != "checkbox" else ""

            columns.append(f"{field_name} {sql_type}{constraint}")

        columns_sql = ",\n    ".join(columns)
        create_sql = f"CREATE TABLE {table_name} (\n    {columns_sql}\n)"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_sql)

            # Create index on record_id for fast lookups
            cursor.execute(
                f"CREATE INDEX idx_{table_name}_record_id ON {table_name}(record_id)"
            )

            conn.commit()
            conn.close()

            logger.info(f"Created table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False

    def read_all(self, form_path: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read all records from the table."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.debug(f"Table doesn't exist: {table_name}")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY record_id")
            rows = cursor.fetchall()
            conn.close()

            # Convert rows to dictionaries and apply type conversions
            forms = []
            for row in rows:
                form_data = {}
                for field in spec["fields"]:
                    field_name = field["name"]
                    field_type = field["type"]
                    value = row[field_name]

                    # Convert based on field type
                    if field_type == "checkbox":
                        form_data[field_name] = (
                            bool(value) if value is not None else False
                        )
                    elif field_type == "number" or field_type == "range":
                        form_data[field_name] = int(value) if value is not None else 0
                    else:
                        form_data[field_name] = value if value is not None else ""

                # Add record_id to form_data (not in spec but needed for migrations/references)
                if "record_id" in row.keys():
                    form_data["_record_id"] = row["record_id"]

                forms.append(form_data)

            logger.debug(f"Read {len(forms)} records from {table_name}")
            return forms

        except Exception as e:
            logger.error(f"Failed to read from {table_name}: {e}")
            return []

    def read_one(
        self, form_path: str, spec: Dict[str, Any], idx: int
    ) -> Optional[Dict[str, Any]]:
        """Read a single record by index."""
        # For SQLite, we read all and return by index
        # (since we're using index-based addressing, not ID-based)
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.debug(f"Index {idx} out of bounds for {form_path}")
            return None

        return forms[idx]

    def create(
        self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]
    ) -> Optional[str]:
        """Insert a new record into the table and return its UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            self.create_storage(form_path, spec)

        # Use existing UUID if provided (for migrations), otherwise generate new one
        record_id = data.get("_record_id") or generate_id()

        # Build INSERT statement (include record_id)
        field_names = ["record_id"] + [field["name"] for field in spec["fields"]]
        placeholders = ", ".join(["?" for _ in field_names])
        columns = ", ".join(field_names)

        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Extract values (record_id first, then field values)
        values = [record_id]
        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            value = data.get(field_name, "")

            # Convert based on field type
            if field_type == "checkbox":
                values.append(1 if value else 0)
            elif field_type == "number" or field_type == "range":
                try:
                    values.append(int(value) if value else 0)
                except ValueError:
                    values.append(0)
            else:
                values.append(str(value) if value else "")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            conn.commit()
            conn.close()

            logger.debug(f"Inserted record {record_id} into {table_name}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to insert into {table_name}: {e}")
            return None

    def update(
        self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]
    ) -> bool:
        """Update an existing record."""
        table_name = self._get_table_name(form_path)

        # Get all records to find the ID of the record at index idx
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.error(f"Cannot update: index {idx} out of bounds for {form_path}")
            return False

        # Get the record_id from the record at the given index
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT record_id FROM {table_name} ORDER BY record_id LIMIT 1 OFFSET {idx}"
            )
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                conn.close()
                return False

            record_id = row["record_id"]

            # Build UPDATE statement
            set_clauses = []
            values = []

            for field in spec["fields"]:
                field_name = field["name"]
                field_type = field["type"]
                value = data.get(field_name, "")

                set_clauses.append(f"{field_name} = ?")

                # Convert based on field type
                if field_type == "checkbox":
                    values.append(1 if value else 0)
                elif field_type == "number" or field_type == "range":
                    try:
                        values.append(int(value) if value else 0)
                    except ValueError:
                        values.append(0)
                else:
                    values.append(str(value) if value else "")

            values.append(record_id)  # For WHERE clause

            update_sql = (
                f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE record_id = ?"
            )

            cursor.execute(update_sql, values)
            conn.commit()
            conn.close()

            logger.debug(f"Updated record {idx} in {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update {table_name}: {e}")
            return False

    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """Delete a record by index."""
        table_name = self._get_table_name(form_path)

        # Get the record_id at the given index
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT record_id FROM {table_name} ORDER BY record_id LIMIT 1 OFFSET {idx}"
            )
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                conn.close()
                return False

            record_id = row["record_id"]

            # Delete the record
            delete_sql = f"DELETE FROM {table_name} WHERE record_id = ?"
            cursor.execute(delete_sql, (record_id,))
            conn.commit()
            conn.close()

            logger.debug(f"Deleted record {idx} from {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from {table_name}: {e}")
            return False

    def drop_storage(self, form_path: str, force: bool = False) -> bool:
        """Remove the table completely."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.debug(f"Table doesn't exist: {table_name}")
            return True

        # Check if table has data and force is False
        if not force and self.has_data(form_path):
            logger.warning(f"Cannot drop {table_name}: table has data and force=False")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {table_name}")
            conn.commit()
            conn.close()

            logger.info(f"Dropped table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to drop table {table_name}: {e}")
            return False

    def exists(self, form_path: str) -> bool:
        """Check if the table exists."""
        table_name = self._get_table_name(form_path)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            result = cursor.fetchone()
            conn.close()

            return result is not None

        except Exception as e:
            logger.error(f"Failed to check if table exists: {e}")
            return False

    def has_data(self, form_path: str) -> bool:
        """Check if the table has any records."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row = cursor.fetchone()
            conn.close()

            return row["count"] > 0

        except Exception as e:
            logger.error(f"Failed to check if table has data: {e}")
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
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.info(f"No table to migrate: {table_name}")
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
        backup_path = self._create_backup()
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
            conn = self._get_connection()
            cursor = conn.cursor()

            for change in schema_change.changes:
                if change.change_type == ChangeType.ADD_FIELD:
                    logger.info(
                        f"Adding new field '{change.field_name}' with type {change.field_type}"
                    )

                    field_name = change.field_name
                    field_type = change.field_type
                    sql_type = self.TYPE_MAPPING.get(field_type, "TEXT")

                    # Get default value for the field type
                    default_value = self._get_default_value_sql(field_type)

                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {sql_type} DEFAULT {default_value}"
                    cursor.execute(alter_sql)

                    # Update current_spec
                    current_spec["fields"].append(
                        {"name": field_name, "type": field_type}
                    )

            conn.commit()
            conn.close()

            logger.info(f"Successfully migrated schema for {form_path}")
            return True

        except Exception as e:
            # Restore from backup on error
            if backup_path:
                self._restore_backup(backup_path)
            logger.error(f"Migration error: {e}, restored from backup")
            return False

    def create_index(self, form_path: str, field_name: str) -> bool:
        """Create an index on a specific field."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.warning(f"Cannot create index: table {table_name} doesn't exist")
            return False

        index_name = f"idx_{table_name}_{field_name}"
        create_index_sql = (
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({field_name})"
        )

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_index_sql)
            conn.commit()
            conn.close()

            logger.info(f"Created index {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False

    def _get_default_value_sql(self, field_type: str) -> str:
        """
        Get SQL default value for a field type.

        Args:
            field_type: Type of field

        Returns:
            SQL default value
        """
        if field_type == "checkbox":
            return "0"
        elif field_type == "number" or field_type == "range":
            return "0"
        else:
            return "''"

    def rename_field(
        self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str
    ) -> bool:
        """
        Rename a field in the table, preserving all data.

        For SQLite, we recreate the table since ALTER TABLE RENAME COLUMN
        is not supported in older versions.

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field name)
            old_name: Current name of the field
            new_name: New name for the field

        Returns:
            True if field was renamed successfully
        """
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot rename field: table {table_name} doesn't exist")
            return False

        # Create backup
        backup_path = self._create_backup()
        if not backup_path:
            logger.error("Failed to create backup, aborting rename")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create new table with renamed field
            temp_table = f"{table_name}_temp"

            # Build CREATE TABLE for new structure
            columns = ["record_id TEXT PRIMARY KEY"]
            for field in spec["fields"]:
                field_name = field["name"]
                field_type = field["type"]
                sql_type = self.TYPE_MAPPING.get(field_type, "TEXT")

                required = field.get("required", False)
                constraint = (
                    " NOT NULL" if required and field_type != "checkbox" else ""
                )

                columns.append(f"{field_name} {sql_type}{constraint}")

            columns_sql = ",\n    ".join(columns)
            create_sql = f"CREATE TABLE {temp_table} (\n    {columns_sql}\n)"

            cursor.execute(create_sql)

            # Copy data from old table to new table
            # Build field list with old_name -> new_name mapping
            old_fields = ["record_id"] + [
                old_name if f["name"] == new_name else f["name"] for f in spec["fields"]
            ]
            new_fields = ["record_id"] + [f["name"] for f in spec["fields"]]

            old_fields_sql = ", ".join(old_fields)
            new_fields_sql = ", ".join(new_fields)

            copy_sql = f"""
                INSERT INTO {temp_table} ({new_fields_sql})
                SELECT {old_fields_sql}
                FROM {table_name}
            """
            cursor.execute(copy_sql)

            # Drop old table and rename new table
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

            conn.commit()
            conn.close()

            logger.info(f"Renamed field '{old_name}' to '{new_name}' in {table_name}")
            return True

        except Exception as e:
            # Restore from backup on error
            if backup_path:
                self._restore_backup(backup_path)
            logger.error(f"Failed to rename field: {e}, restored from backup")
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

        For SQLite, we recreate the table with the new type and copy/convert data.

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field type)
            field_name: Name of the field to change
            old_type: Current type of the field
            new_type: New type for the field

        Returns:
            True if type was changed successfully
        """
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot change field type: table {table_name} doesn't exist")
            return False

        # Create backup
        backup_path = self._create_backup()
        if not backup_path:
            logger.error("Failed to create backup, aborting type change")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Read all existing data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Create new table with updated type
            temp_table = f"{table_name}_temp"

            # Build CREATE TABLE with new field type
            columns = ["record_id TEXT PRIMARY KEY"]
            for field in spec["fields"]:
                fname = field["name"]
                ftype = field["type"]
                sql_type = self.TYPE_MAPPING.get(ftype, "TEXT")

                required = field.get("required", False)
                constraint = " NOT NULL" if required and ftype != "checkbox" else ""

                columns.append(f"{fname} {sql_type}{constraint}")

            columns_sql = ",\n    ".join(columns)
            create_sql = f"CREATE TABLE {temp_table} (\n    {columns_sql}\n)"

            cursor.execute(create_sql)

            # Convert and insert data (include record_id)
            field_names = ["record_id"] + [f["name"] for f in spec["fields"]]
            placeholders = ", ".join(["?" for _ in field_names])
            columns_insert = ", ".join(field_names)

            insert_sql = (
                f"INSERT INTO {temp_table} ({columns_insert}) VALUES ({placeholders})"
            )

            conversion_errors = 0
            for row in rows:
                # Start with record_id
                values = [row["record_id"]]

                for field in spec["fields"]:
                    fname = field["name"]
                    ftype = field["type"]
                    value = row[fname]

                    # Convert the changed field
                    if fname == field_name:
                        try:
                            value = self._convert_value(value, old_type, new_type)
                        except Exception as e:
                            logger.warning(f"Conversion error for {fname}: {e}")
                            conversion_errors += 1
                            value = self._get_default_value(new_type)

                    # Apply type conversion
                    if ftype == "checkbox":
                        values.append(1 if value else 0)
                    elif ftype == "number" or ftype == "range":
                        try:
                            values.append(int(value) if value else 0)
                        except ValueError:
                            values.append(0)
                    else:
                        values.append(str(value) if value else "")

                cursor.execute(insert_sql, values)

            # Check if too many conversions failed
            total_rows = len(rows)
            if total_rows > 0 and conversion_errors / total_rows > 0.5:
                raise Exception(
                    f"Too many conversion errors: {conversion_errors}/{total_rows}"
                )

            # Drop old table and rename new table
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

            conn.commit()
            conn.close()

            logger.info(
                f"Changed field '{field_name}' from {old_type} to {new_type} "
                f"in {table_name} ({conversion_errors} conversion errors)"
            )
            return True

        except Exception as e:
            # Restore from backup on error
            if backup_path:
                self._restore_backup(backup_path)
            logger.error(f"Failed to change field type: {e}, restored from backup")
            return False

    def remove_field(
        self, form_path: str, spec: Dict[str, Any], field_name: str
    ) -> bool:
        """
        Remove a field from the table (destructive operation).

        For SQLite, we recreate the table without the removed field.

        Args:
            form_path: Path to the form
            spec: Updated form specification (without the removed field)
            field_name: Name of the field to remove

        Returns:
            True if field was removed successfully
        """
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot remove field: table {table_name} doesn't exist")
            return False

        # Create backup (critical for destructive operations!)
        backup_path = self._create_backup()
        if not backup_path:
            logger.error("Failed to create backup, aborting field removal")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create new table without the removed field
            temp_table = f"{table_name}_temp"

            # Build CREATE TABLE without removed field
            columns = ["record_id TEXT PRIMARY KEY"]
            for field in spec["fields"]:
                fname = field["name"]
                ftype = field["type"]
                sql_type = self.TYPE_MAPPING.get(ftype, "TEXT")

                required = field.get("required", False)
                constraint = " NOT NULL" if required and ftype != "checkbox" else ""

                columns.append(f"{fname} {sql_type}{constraint}")

            columns_sql = ",\n    ".join(columns)
            create_sql = f"CREATE TABLE {temp_table} (\n    {columns_sql}\n)"

            cursor.execute(create_sql)

            # Copy data excluding the removed field (include record_id)
            field_names = ["record_id"] + [f["name"] for f in spec["fields"]]
            fields_sql = ", ".join(field_names)

            copy_sql = f"""
                INSERT INTO {temp_table} ({fields_sql})
                SELECT {fields_sql}
                FROM {table_name}
            """
            cursor.execute(copy_sql)

            # Drop old table and rename new table
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

            conn.commit()
            conn.close()

            logger.info(f"Removed field '{field_name}' from {table_name}")
            return True

        except Exception as e:
            # Restore from backup on error
            if backup_path:
                self._restore_backup(backup_path)
            logger.error(f"Failed to remove field: {e}, restored from backup")
            return False

    def _convert_value(self, value: Any, old_type: str, new_type: str) -> Any:
        """
        Convert a value from one type to another.

        Args:
            value: Original value
            old_type: Original field type
            new_type: Target field type

        Returns:
            Converted value

        Raises:
            ValueError: If conversion is not possible
        """
        # None/empty values
        if value is None or value == "":
            return self._get_default_value(new_type)

        # text -> number
        if old_type in ["text", "email", "tel", "url", "search"] and new_type in [
            "number",
            "range",
        ]:
            return int(value)

        # number -> text
        if old_type in ["number", "range"] and new_type in [
            "text",
            "email",
            "tel",
            "url",
            "search",
        ]:
            return str(value)

        # text -> checkbox
        if (
            old_type in ["text", "email", "tel", "url", "search"]
            and new_type == "checkbox"
        ):
            return value.lower() in ["true", "1", "yes", "sim"]

        # checkbox -> text
        if old_type == "checkbox" and new_type in [
            "text",
            "email",
            "tel",
            "url",
            "search",
        ]:
            return "true" if value else "false"

        # Any type -> text (always safe)
        if new_type in ["text", "textarea", "email", "tel", "url", "search"]:
            return str(value)

        # Same type or compatible types
        return value

    def _get_default_value(self, field_type: str) -> Any:
        """
        Get default value for a field type.

        Args:
            field_type: Type of field

        Returns:
            Default value for that type
        """
        if field_type == "checkbox":
            return False
        elif field_type in ["number", "range"]:
            return 0
        else:
            return ""

    def _create_backup(self) -> Optional[str]:
        """
        Create a backup of the database.

        Returns:
            Path to backup file, or None on failure
        """
        if not os.path.exists(self.database):
            return None

        # Create backups directory
        db_dir = os.path.dirname(self.database)
        backup_dir = os.path.join(db_dir, "backups")
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_filename = os.path.basename(self.database)
        name, ext = os.path.splitext(db_filename)
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            shutil.copy2(self.database, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restored successfully
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file doesn't exist: {backup_path}")
            return False

        try:
            shutil.copy2(backup_path, self.database)
            logger.info(f"Restored from backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    # =========================================================================
    # NEW ID-BASED CRUD METHODS (Stub implementations for FASE 3)
    # =========================================================================

    def read_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Read a single record by its unique ID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.debug(f"Table does not exist: {table_name}")
            return None

        # Build SELECT statement
        field_names = [field["name"] for field in spec["fields"]]
        columns = ", ".join(["record_id"] + field_names)

        select_sql = f"SELECT {columns} FROM {table_name} WHERE record_id = ?"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(select_sql, (record_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.debug(f"No record found with ID {record_id} in {table_name}")
                return None

            # Convert row to dictionary
            data = {"_record_id": row["record_id"]}
            for field in spec["fields"]:
                field_name = field["name"]
                field_type = field["type"]
                value = row[field_name]

                # Convert based on field type
                if field_type == "checkbox":
                    data[field_name] = bool(value) if value else False
                elif field_type == "number" or field_type == "range":
                    data[field_name] = int(value) if value else 0
                else:
                    data[field_name] = str(value) if value else ""

            return data

        except Exception as e:
            logger.error(f"Failed to read record {record_id} from {table_name}: {e}")
            return None

    def update_by_id(
        self,
        form_path: str,
        spec: Dict[str, Any],
        record_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """Update an existing record by its ID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot update: table does not exist: {table_name}")
            return False

        # Build UPDATE statement
        set_clauses = []
        values = []

        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            value = data.get(field_name, "")

            set_clauses.append(f"{field_name} = ?")

            # Convert based on field type
            if field_type == "checkbox":
                values.append(1 if value else 0)
            elif field_type == "number" or field_type == "range":
                try:
                    values.append(int(value) if value else 0)
                except ValueError:
                    values.append(0)
            else:
                values.append(str(value) if value else "")

        # Add record_id to WHERE clause
        values.append(record_id)

        set_sql = ", ".join(set_clauses)
        update_sql = f"UPDATE {table_name} SET {set_sql} WHERE record_id = ?"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(update_sql, values)
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            if rows_affected == 0:
                logger.warning(f"No record found with ID {record_id} in {table_name}")
                return False

            logger.debug(f"Updated record {record_id} in {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update record {record_id} in {table_name}: {e}")
            return False

    def delete_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> bool:
        """Delete a record by its unique ID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot delete: table does not exist: {table_name}")
            return False

        delete_sql = f"DELETE FROM {table_name} WHERE record_id = ?"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(delete_sql, (record_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            if rows_affected == 0:
                logger.warning(f"No record found with ID {record_id} in {table_name}")
                return False

            logger.debug(f"Deleted record {record_id} from {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete record {record_id} from {table_name}: {e}")
            return False

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
        self._ensure_tags_table()

        # Check if tag is already active
        if self.has_tag(object_type, object_id, tag):
            logger.debug(f"Tag '{tag}' already exists for {object_type}:{object_id}")
            return False

        applied_at = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        insert_sql = """
        INSERT INTO tags (object_type, object_id, tag, applied_at, applied_by, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                insert_sql,
                (object_type, object_id, tag, applied_at, applied_by, metadata_json),
            )
            conn.commit()
            conn.close()

            logger.debug(f"Added tag '{tag}' to {object_type}:{object_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add tag '{tag}' to {object_type}:{object_id}: {e}")
            return False

    def remove_tag(
        self, object_type: str, object_id: str, tag: str, removed_by: str
    ) -> bool:
        """Remove a tag from an object."""
        self._ensure_tags_table()

        # Check if tag exists and is active
        if not self.has_tag(object_type, object_id, tag):
            logger.debug(f"Tag '{tag}' not found for {object_type}:{object_id}")
            return False

        removed_at = datetime.now().isoformat()

        update_sql = """
        UPDATE tags
        SET removed_at = ?, removed_by = ?
        WHERE object_type = ? AND object_id = ? AND tag = ? AND removed_at IS NULL
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                update_sql, (removed_at, removed_by, object_type, object_id, tag)
            )
            conn.commit()
            conn.close()

            logger.debug(f"Removed tag '{tag}' from {object_type}:{object_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to remove tag '{tag}' from {object_type}:{object_id}: {e}"
            )
            return False

    def get_tags(
        self, object_type: str, object_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all tags for an object."""
        self._ensure_tags_table()

        if active_only:
            query_sql = """
            SELECT tag, applied_at, applied_by, metadata
            FROM tags
            WHERE object_type = ? AND object_id = ? AND removed_at IS NULL
            ORDER BY applied_at DESC
            """
            params = (object_type, object_id)
        else:
            query_sql = """
            SELECT tag, applied_at, applied_by, removed_at, removed_by, metadata
            FROM tags
            WHERE object_type = ? AND object_id = ?
            ORDER BY applied_at DESC
            """
            params = (object_type, object_id)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            conn.close()

            tags = []
            for row in rows:
                tag_data = {
                    "tag": row["tag"],
                    "applied_at": row["applied_at"],
                    "applied_by": row["applied_by"],
                    "metadata": (
                        json.loads(row["metadata"]) if row["metadata"] else None
                    ),
                }

                if not active_only:
                    tag_data["removed_at"] = row.get("removed_at")
                    tag_data["removed_by"] = row.get("removed_by")

                tags.append(tag_data)

            return tags

        except Exception as e:
            logger.error(f"Failed to get tags for {object_type}:{object_id}: {e}")
            return []

    def has_tag(self, object_type: str, object_id: str, tag: str) -> bool:
        """Check if an object has a specific tag."""
        self._ensure_tags_table()

        query_sql = """
        SELECT COUNT(*) FROM tags
        WHERE object_type = ? AND object_id = ? AND tag = ? AND removed_at IS NULL
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_sql, (object_type, object_id, tag))
            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            logger.error(
                f"Failed to check tag '{tag}' for {object_type}:{object_id}: {e}"
            )
            return False

    def get_objects_by_tag(
        self, object_type: str, tag: str, active_only: bool = True
    ) -> List[str]:
        """Get all object IDs with a specific tag."""
        self._ensure_tags_table()

        if active_only:
            query_sql = """
            SELECT DISTINCT object_id
            FROM tags
            WHERE object_type = ? AND tag = ? AND removed_at IS NULL
            ORDER BY applied_at DESC
            """
        else:
            query_sql = """
            SELECT DISTINCT object_id
            FROM tags
            WHERE object_type = ? AND tag = ?
            ORDER BY applied_at DESC
            """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_sql, (object_type, tag))
            rows = cursor.fetchall()
            conn.close()

            return [row["object_id"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get objects by tag '{tag}' for {object_type}: {e}")
            return []

    def get_tag_history(
        self, object_type: str, object_id: str, tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get complete tag history for an object."""
        self._ensure_tags_table()

        if tag:
            query_sql = """
            SELECT tag, applied_at, applied_by, removed_at, removed_by, metadata
            FROM tags
            WHERE object_type = ? AND object_id = ? AND tag = ?
            ORDER BY applied_at DESC
            """
            params = (object_type, object_id, tag)
        else:
            query_sql = """
            SELECT tag, applied_at, applied_by, removed_at, removed_by, metadata
            FROM tags
            WHERE object_type = ? AND object_id = ?
            ORDER BY applied_at DESC
            """
            params = (object_type, object_id)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                history.append(
                    {
                        "tag": row["tag"],
                        "applied_at": row["applied_at"],
                        "applied_by": row["applied_by"],
                        "removed_at": row["removed_at"],
                        "removed_by": row["removed_by"],
                        "metadata": (
                            json.loads(row["metadata"]) if row["metadata"] else None
                        ),
                        "is_active": row["removed_at"] is None,
                    }
                )

            return history

        except Exception as e:
            logger.error(
                f"Failed to get tag history for {object_type}:{object_id}: {e}"
            )
            return []

    def get_tag_statistics(self, object_type: str) -> Dict[str, int]:
        """Get statistics about tag usage."""
        self._ensure_tags_table()

        query_sql = """
        SELECT tag, COUNT(DISTINCT object_id) as count
        FROM tags
        WHERE object_type = ? AND removed_at IS NULL
        GROUP BY tag
        ORDER BY count DESC, tag ASC
        """

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_sql, (object_type,))
            rows = cursor.fetchall()
            conn.close()

            statistics = {}
            for row in rows:
                statistics[row["tag"]] = row["count"]

            return statistics

        except Exception as e:
            logger.error(f"Failed to get tag statistics for {object_type}: {e}")
            return {}

    # =========================================================================
    # BULK OPERATIONS (Performance Optimization)
    # =========================================================================

    def bulk_create(
        self, form_path: str, spec: Dict[str, Any], records: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Optimized bulk insert for multiple records using a single transaction.

        Performance improvement:
        - Single transaction instead of N commits
        - Single connection instead of N connections
        - Reduces I/O from O(n) commits to O(1) commit

        For 19 records: ~200-950ms → ~10-20ms (10-50x faster)

        Args:
            form_path: Path to the form
            spec: Form specification
            records: List of dictionaries containing field values

        Returns:
            List of UUIDs for created records
        """
        if not records:
            return []

        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            self.create_storage(form_path, spec)

        # Prepare all records with UUIDs
        record_ids = []
        all_values = []

        for record in records:
            # Use existing UUID if provided (for migrations), otherwise generate new one
            record_id = record.get("_record_id") or generate_id()
            record_ids.append(record_id)

            # Extract values (record_id first, then field values)
            values = [record_id]
            for field in spec["fields"]:
                field_name = field["name"]
                field_type = field["type"]
                value = record.get(field_name, "")

                # Convert based on field type
                if field_type == "checkbox":
                    values.append(1 if value else 0)
                elif field_type == "number" or field_type == "range":
                    try:
                        values.append(int(value) if value else 0)
                    except ValueError:
                        values.append(0)
                else:
                    values.append(str(value) if value else "")

            all_values.append(values)

        # Build INSERT statement
        field_names = ["record_id"] + [field["name"] for field in spec["fields"]]
        placeholders = ", ".join(["?" for _ in field_names])
        columns = ", ".join(field_names)
        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        try:
            import time

            start_time = time.time()

            conn = self._get_connection()
            cursor = conn.cursor()

            # Use executemany() for optimal performance (C-level optimization)
            cursor.executemany(insert_sql, all_values)

            # Single commit for all records
            conn.commit()
            conn.close()

            elapsed = time.time() - start_time
            logger.info(
                f"✅ Bulk inserted {len(records)} records into {table_name} "
                f"in {elapsed:.2f}s ({len(records)/elapsed:.0f} rec/s)"
            )
            return record_ids

        except Exception as e:
            logger.error(f"❌ Failed to bulk insert into {table_name}: {e}")
            # Return None for all records on failure
            return [None] * len(records)
