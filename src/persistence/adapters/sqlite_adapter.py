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
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from persistence.base import BaseRepository
from persistence.schema_detector import SchemaChangeDetector, ChangeType
from src.utils import crockford

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
                - timeout: Connection timeout in seconds (default: 30)
                - check_same_thread: SQLite check_same_thread parameter
        """
        self.database = config.get("database", "src/vibecforms.db")
        self.timeout = config.get("timeout", 30)  # Increased from 10 to 30 seconds
        self.check_same_thread = config.get("check_same_thread", False)

        # Ensure database directory exists
        db_dir = os.path.dirname(self.database)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

        # Enable WAL mode for better concurrency
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
            conn.commit()
            logger.info("SQLite WAL mode enabled")
        except Exception as e:
            logger.warning(f"Failed to enable WAL mode: {e}")
        finally:
            if conn:
                conn.close()

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

    def _sanitize_table_name(self, form_path: str) -> str:
        """
        Sanitize and get the table name for a form (alias for _get_table_name).

        Args:
            form_path: Form path (e.g., 'contatos', 'financeiro/contas')

        Returns:
            Table name (e.g., 'contatos', 'financeiro_contas')
        """
        return self._get_table_name(form_path)

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (table) for the form."""
        table_name = self._get_table_name(form_path)

        if self.exists(form_path):
            logger.debug(f"Table already exists: {table_name}")
            return False

        # Build CREATE TABLE statement
        columns = ["id TEXT PRIMARY KEY"]

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

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()

            logger.info(f"Created table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def read_all(self, form_path: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read all records from the table including UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.debug(f"Table doesn't exist: {table_name}")
            return []

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Convert rows to dictionaries and apply type conversions
            forms = []
            for row in rows:
                # Start with the UUID
                form_data = {"id": row["id"]}

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

                forms.append(form_data)

            logger.debug(f"Read {len(forms)} records from {table_name}")
            return forms

        except Exception as e:
            logger.error(f"Failed to read from {table_name}: {e}")
            return []
        finally:
            if conn:
                conn.close()

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

    def read_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Read a single record by UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.debug(f"Table doesn't exist: {table_name}")
            return None

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
            row = cursor.fetchone()

            if not row:
                logger.debug(f"Record {record_id} not found in {table_name}")
                return None

            # Build record dictionary starting with UUID
            record = {"id": row["id"]}

            for field in spec["fields"]:
                field_name = field["name"]
                field_type = field["type"]
                value = row[field_name]

                # Convert based on field type
                if field_type == "checkbox":
                    record[field_name] = bool(value) if value is not None else False
                elif field_type == "number" or field_type == "range":
                    record[field_name] = int(value) if value is not None else 0
                else:
                    record[field_name] = value if value is not None else ""

            logger.debug(f"Read record {record_id} from {table_name}")
            return record

        except Exception as e:
            logger.error(f"Failed to read record {record_id} from {table_name}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Insert a new record into the table with generated UUID.

        Returns:
            str: The generated UUID for the new record
        """
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            self.create_storage(form_path, spec)

        # Generate UUID
        record_id = crockford.generate_id()

        # Build INSERT statement including id column
        columns = ["id"] + [field["name"] for field in spec["fields"]]
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)

        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Build values list starting with UUID
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

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            conn.commit()

            logger.debug(f"Inserted record {record_id} into {table_name}")
            return record_id

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to insert into {table_name}: {e}")
            raise
        finally:
            if conn:
                conn.close()

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

        # Get the row ID (we need to get it from the database)
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {table_name} LIMIT 1 OFFSET {idx}")
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                return False

            record_id = row["id"]

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
                f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
            )

            cursor.execute(update_sql, values)
            conn.commit()

            logger.debug(f"Updated record {idx} in {table_name}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to update {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str, data: Dict[str, Any]
    ) -> bool:
        """Update a record by UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot update: table {table_name} doesn't exist")
            return False

        # Build SET clause and values
        set_parts = []
        values = []

        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            value = data.get(field_name, "")

            set_parts.append(f"{field_name} = ?")

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

        if not set_parts:
            logger.warning(f"No fields to update for record {record_id}")
            return False

        # Add record_id to end of values for WHERE clause
        values.append(record_id)

        # Execute UPDATE
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            update_sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE id = ?"
            cursor.execute(update_sql, values)
            conn.commit()

            # Check if any rows were updated
            rows_updated = cursor.rowcount > 0

            if rows_updated:
                logger.debug(f"Updated record {record_id} in {table_name}")
            else:
                logger.warning(f"Record {record_id} not found in {table_name}")

            return rows_updated

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to update record {record_id} in {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """Delete a record by index."""
        table_name = self._get_table_name(form_path)

        # Get the row ID at the given index
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {table_name} LIMIT 1 OFFSET {idx}")
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                return False

            record_id = row["id"]

            # Delete the record
            delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
            cursor.execute(delete_sql, (record_id,))
            conn.commit()

            logger.debug(f"Deleted record {idx} from {table_name}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to delete from {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> bool:
        """Delete a record by UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.error(f"Cannot delete: table {table_name} doesn't exist")
            return False

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete the record
            delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
            cursor.execute(delete_sql, (record_id,))
            conn.commit()

            # Check if any rows were deleted
            rows_deleted = cursor.rowcount > 0

            if rows_deleted:
                logger.debug(f"Deleted record {record_id} from {table_name}")
            else:
                logger.warning(f"Record {record_id} not found in {table_name}")

            return rows_deleted

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to delete record {record_id} from {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def id_exists(self, form_path: str, record_id: str) -> bool:
        """Check if record with UUID exists."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT 1 FROM {table_name} WHERE id = ? LIMIT 1", (record_id,)
            )
            result = cursor.fetchone()
            conn.close()

            return result is not None

        except Exception as e:
            logger.error(f"Failed to check if record {record_id} exists: {e}")
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

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {table_name}")
            conn.commit()

            logger.info(f"Dropped table: {table_name}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to drop table {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def exists(self, form_path: str) -> bool:
        """Check if the table exists."""
        table_name = self._get_table_name(form_path)

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            result = cursor.fetchone()

            return result is not None

        except Exception as e:
            logger.error(f"Failed to check if table exists: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def has_data(self, form_path: str) -> bool:
        """Check if the table has any records."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            return False

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row = cursor.fetchone()

            return row["count"] > 0

        except Exception as e:
            logger.error(f"Failed to check if table has data: {e}")
            return False
        finally:
            if conn:
                conn.close()

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

            # Build CREATE TABLE for new structure (preserving UUID column)
            columns = ["id TEXT PRIMARY KEY"]
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

            # Copy data from old table to new table, preserving UUIDs
            # Build field list with old_name -> new_name mapping
            old_fields = ["id"] + [
                old_name if f["name"] == new_name else f["name"] for f in spec["fields"]
            ]
            new_fields = ["id"] + [f["name"] for f in spec["fields"]]

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

            # Build CREATE TABLE with new field type (preserving UUID column)
            columns = ["id TEXT PRIMARY KEY"]
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

            # Convert and insert data, preserving UUIDs
            field_names = ["id"] + [f["name"] for f in spec["fields"]]
            placeholders = ", ".join(["?" for _ in field_names])
            columns_insert = ", ".join(field_names)

            insert_sql = (
                f"INSERT INTO {temp_table} ({columns_insert}) VALUES ({placeholders})"
            )

            conversion_errors = 0
            for row in rows:
                # Start with UUID
                values = [row["id"]]

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

            # Build CREATE TABLE without removed field (preserving UUID column)
            columns = ["id TEXT PRIMARY KEY"]
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

            # Copy data excluding the removed field, preserving UUIDs
            field_names = ["id"] + [f["name"] for f in spec["fields"]]
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
