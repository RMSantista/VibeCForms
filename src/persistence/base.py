"""
Base repository interface for VibeCForms persistence layer.

This module defines the abstract base class that all persistence adapters
must implement. This allows VibeCForms to support multiple storage backends
(TXT, SQLite, MySQL, PostgreSQL, CSV, JSON, XML, NoSQL, etc.) without
changing the application code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseRepository(ABC):
    """
    Abstract base class for all persistence adapters.

    Each backend (txt, SQLite, MySQL, etc.) must implement this interface
    to provide storage capabilities for VibeCForms dynamic forms.

    All methods work with form specifications (specs) which are JSON objects
    defining the structure of a form, and form data which are dictionaries
    containing the actual field values.
    """

    @abstractmethod
    def create_storage(self, form_path: str, spec: Dict[str, Any]) -> bool:
        """
        Create storage structure (table/file/collection) for a form.

        This method is called when a form is first accessed and its storage
        doesn't exist yet. It should create the necessary structure based
        on the form specification.

        Args:
            form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')
            spec: Form specification containing fields definition

        Returns:
            True if storage was created successfully
            False if storage already exists

        Example:
            For SQLite: Creates a table with columns based on spec fields
            For TXT: Creates an empty .txt file
            For MongoDB: Creates a collection with schema validation
        """
        pass

    @abstractmethod
    def read_all(self, form_path: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Read all records from the form storage.

        Args:
            form_path: Path to the form
            spec: Form specification for field type conversion

        Returns:
            List of dictionaries, each representing a record
            Empty list if no records exist

        Example:
            [
                {'nome': 'João', 'telefone': '11999999999', 'ativo': True},
                {'nome': 'Maria', 'telefone': '11988888888', 'ativo': False}
            ]
        """
        pass

    @abstractmethod
    def read_one(self, form_path: str, spec: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
        """
        Read a single record by its index.

        Args:
            form_path: Path to the form
            spec: Form specification for field type conversion
            idx: Zero-based index of the record

        Returns:
            Dictionary with record data if found
            None if index is out of bounds

        Example:
            {'nome': 'João', 'telefone': '11999999999', 'ativo': True}
        """
        pass

    @abstractmethod
    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Insert a new record into the form storage.

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            data: Dictionary containing field values to insert

        Returns:
            True if record was inserted successfully
            False if insertion failed

        Example:
            data = {'nome': 'João', 'telefone': '11999999999', 'ativo': True}
        """
        pass

    @abstractmethod
    def update(self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing record.

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            idx: Zero-based index of the record to update
            data: Dictionary containing new field values

        Returns:
            True if record was updated successfully
            False if index doesn't exist or update failed
        """
        pass

    @abstractmethod
    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """
        Delete a record by its index.

        Args:
            form_path: Path to the form
            spec: Form specification
            idx: Zero-based index of the record to delete

        Returns:
            True if record was deleted successfully
            False if index doesn't exist or deletion failed
        """
        pass

    @abstractmethod
    def drop_storage(self, form_path: str, force: bool = False) -> bool:
        """
        Remove the entire storage structure (table/file/collection).

        This is a destructive operation. If data exists and force=False,
        the method should return False to prevent accidental data loss.

        Args:
            form_path: Path to the form
            force: If True, drops even if data exists

        Returns:
            True if storage was dropped successfully
            False if cancelled (has data and force=False)

        Warning:
            This permanently deletes all data! Use with caution.
        """
        pass

    @abstractmethod
    def exists(self, form_path: str) -> bool:
        """
        Check if storage exists for this form.

        Args:
            form_path: Path to the form

        Returns:
            True if storage structure exists (table/file/collection)
            False otherwise

        Example:
            For SQLite: Checks if table exists
            For TXT: Checks if .txt file exists
        """
        pass

    @abstractmethod
    def has_data(self, form_path: str) -> bool:
        """
        Check if storage contains any records.

        Args:
            form_path: Path to the form

        Returns:
            True if at least one record exists
            False if storage is empty or doesn't exist
        """
        pass

    @abstractmethod
    def migrate_schema(self, form_path: str, old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> bool:
        """
        Migrate storage schema when form specification changes.

        This method is called when fields are added, removed, or modified
        in the form specification. It should preserve existing data whenever
        possible.

        Args:
            form_path: Path to the form
            old_spec: Previous form specification
            new_spec: New form specification

        Returns:
            True if migration was successful
            False if migration failed

        Migration scenarios:
            - Add field: Add column/field with default value
            - Remove field: Drop column/field (may require confirmation)
            - Change type: Convert existing data if possible
            - Rename field: Detect and rename (may require heuristics)

        Note:
            A backup should be created before migration if configured.
        """
        pass

    @abstractmethod
    def create_index(self, form_path: str, field_name: str) -> bool:
        """
        Create an index on a specific field to improve query performance.

        Not all backends support indexes (e.g., TXT files don't).
        Implementation can return True immediately if indexes are not applicable.

        Args:
            form_path: Path to the form
            field_name: Name of the field to index

        Returns:
            True if index was created or already exists
            False if creation failed

        Example:
            For SQLite: CREATE INDEX IF NOT EXISTS idx_formpath_fieldname ON table(field)
            For TXT: Returns True (no-op, indexes not applicable)
        """
        pass

    @abstractmethod
    def rename_field(self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str) -> bool:
        """
        Rename a field in the storage, preserving all data.

        This is a schema migration operation that changes the name of a field
        without losing the existing data in that field.

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field name)
            old_name: Current name of the field
            new_name: New name for the field

        Returns:
            True if field was renamed successfully
            False if field doesn't exist or rename failed

        Implementation notes:
            - For TXT: Rewrite file with new field order
            - For SQLite: Recreate table (SQLite doesn't support RENAME COLUMN in old versions)
            - For other DBs: Use ALTER TABLE RENAME COLUMN
            - Should preserve all data values
            - Should create backup before operation if configured

        Example:
            rename_field('contatos', spec, 'telefone', 'celular')
        """
        pass

    @abstractmethod
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

        This is a schema migration operation that changes a field's type
        and tries to convert existing data to the new type.

        Args:
            form_path: Path to the form
            spec: Updated form specification (with new field type)
            field_name: Name of the field to change
            old_type: Current type of the field (e.g., 'text')
            new_type: New type for the field (e.g., 'number')

        Returns:
            True if type was changed and data converted successfully
            False if conversion is not possible or failed

        Implementation notes:
            - Should validate if conversion is possible before attempting
            - Compatible conversions: text→number, number→text, etc.
            - Should create backup before operation if configured
            - If any record fails conversion, should rollback

        Example:
            change_field_type('produtos', spec, 'preco', 'text', 'number')
        """
        pass

    @abstractmethod
    def remove_field(self, form_path: str, spec: Dict[str, Any], field_name: str) -> bool:
        """
        Remove a field from the storage structure.

        This is a destructive schema migration operation that permanently
        deletes a field and all its data.

        Args:
            form_path: Path to the form
            spec: Updated form specification (without the removed field)
            field_name: Name of the field to remove

        Returns:
            True if field was removed successfully
            False if field doesn't exist or removal failed

        Implementation notes:
            - For TXT: Rewrite file without the field column
            - For SQLite: ALTER TABLE DROP COLUMN (or recreate table)
            - For other DBs: Use ALTER TABLE DROP COLUMN
            - Should create backup before operation if configured
            - This operation is irreversible - data is lost!

        Warning:
            This permanently deletes all data in this field!
            User confirmation should be required before calling this method.

        Example:
            remove_field('contatos', spec, 'fax')  # Remove obsolete fax field
        """
        pass
