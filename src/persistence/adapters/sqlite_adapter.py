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
        'text': 'TEXT',
        'tel': 'TEXT',
        'email': 'TEXT',
        'password': 'TEXT',
        'url': 'TEXT',
        'search': 'TEXT',
        'textarea': 'TEXT',
        'number': 'INTEGER',
        'checkbox': 'BOOLEAN',
        'date': 'DATE',
        'time': 'TEXT',
        'datetime-local': 'TEXT',
        'month': 'TEXT',
        'week': 'TEXT',
        'select': 'TEXT',
        'radio': 'TEXT',
        'color': 'TEXT',
        'range': 'INTEGER',
        'hidden': 'TEXT',
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
        self.database = config.get('database', 'src/vibecforms.db')
        self.timeout = config.get('timeout', 10)
        self.check_same_thread = config.get('check_same_thread', False)

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
            check_same_thread=self.check_same_thread
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

    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """Create storage (table) for the form."""
        table_name = self._get_table_name(form_path)

        if self.exists(form_path):
            logger.debug(f"Table already exists: {table_name}")
            return False

        # Build CREATE TABLE statement
        columns = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            sql_type = self.TYPE_MAPPING.get(field_type, 'TEXT')

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
            cursor.execute(f"SELECT * FROM {table_name}")
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
                        form_data[field_name] = bool(value) if value is not None else False
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

    def read_one(self, form_path: str, spec: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
        """Read a single record by index."""
        # For SQLite, we read all and return by index
        # (since we're using index-based addressing, not ID-based)
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.debug(f"Index {idx} out of bounds for {form_path}")
            return None

        return forms[idx]

    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Insert a new record into the table."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            self.create_storage(form_path, spec)

        # Build INSERT statement
        field_names = [field["name"] for field in spec["fields"]]
        placeholders = ", ".join(["?" for _ in field_names])
        columns = ", ".join(field_names)

        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Extract values in correct order
        values = []
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

            logger.debug(f"Inserted record into {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to insert into {table_name}: {e}")
            return False

    def update(self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]) -> bool:
        """Update an existing record."""
        table_name = self._get_table_name(form_path)

        # Get all records to find the ID of the record at index idx
        forms = self.read_all(form_path, spec)

        if idx < 0 or idx >= len(forms):
            logger.error(f"Cannot update: index {idx} out of bounds for {form_path}")
            return False

        # Get the row ID (we need to get it from the database)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {table_name} LIMIT 1 OFFSET {idx}")
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                conn.close()
                return False

            record_id = row['id']

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

            update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"

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

        # Get the row ID at the given index
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM {table_name} LIMIT 1 OFFSET {idx}")
            row = cursor.fetchone()

            if not row:
                logger.error(f"No record found at index {idx}")
                conn.close()
                return False

            record_id = row['id']

            # Delete the record
            delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
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
            logger.warning(
                f"Cannot drop {table_name}: table has data and force=False"
            )
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
                (table_name,)
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

            return row['count'] > 0

        except Exception as e:
            logger.error(f"Failed to check if table has data: {e}")
            return False

    def migrate_schema(
        self,
        form_path: str,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any]
    ) -> bool:
        """
        Migrate schema when form specification changes.

        For SQLite, this handles:
        - Add new fields: ALTER TABLE ADD COLUMN
        - Existing fields are preserved
        - Cannot remove fields easily in SQLite (requires table recreation)

        A backup is created before migration.
        """
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            logger.info(f"No table to migrate: {table_name}")
            return True

        # Create backup
        backup_path = self._create_backup()
        if not backup_path:
            logger.error("Failed to create backup, aborting migration")
            return False

        try:
            # Determine which fields are new
            old_field_names = {f["name"] for f in old_spec["fields"]}
            new_fields = [
                f for f in new_spec["fields"]
                if f["name"] not in old_field_names
            ]

            if not new_fields:
                logger.info(f"No new fields to add in {table_name}")
                return True

            # Add each new field
            conn = self._get_connection()
            cursor = conn.cursor()

            for field in new_fields:
                field_name = field["name"]
                field_type = field["type"]
                sql_type = self.TYPE_MAPPING.get(field_type, 'TEXT')

                # Get default value for the field type
                default_value = self._get_default_value_sql(field_type)

                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {sql_type} DEFAULT {default_value}"

                cursor.execute(alter_sql)
                logger.info(f"Added column {field_name} to {table_name}")

            conn.commit()
            conn.close()

            logger.info(f"Successfully migrated {table_name}: added {len(new_fields)} fields")
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
        create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({field_name})"

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
