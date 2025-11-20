"""
Base repository interface for VibeCForms persistence layer.

This module defines the abstract base class that all persistence adapters
must implement. This allows VibeCForms to support multiple storage backends
(TXT, SQLite, MySQL, PostgreSQL, CSV, JSON, XML, NoSQL, etc.) without
changing the application code.

Version 2.0 - UUID-based IDs and Tags as State:
    - All records now have unique Crockford Base32 IDs (27 characters)
    - Tags as State convention (#4) for workflow tracking
    - Index-based methods (read_one, update, delete) marked as deprecated
    - New ID-based methods (read_by_id, update_by_id, delete_by_id)
    - Complete tag management system
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import warnings


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
    def read_one(
        self, form_path: str, spec: Dict[str, Any], idx: int
    ) -> Optional[Dict[str, Any]]:
        """
        [DEPRECATED] Read a single record by its index.

        .. deprecated:: 2.0
            Use :meth:`read_by_id` instead. Index-based access is being phased out
            in favor of UUID-based IDs for better data integrity and relationships.

        Args:
            form_path: Path to the form
            spec: Form specification for field type conversion
            idx: Zero-based index of the record

        Returns:
            Dictionary with record data (including 'id' field) if found
            None if index is out of bounds

        Warning:
            This method will be removed in v3.0. Migrate to read_by_id().

        Example:
            {'id': '3HNMQR8PJSG0C9VWBYTE12K', 'nome': 'João', ...}
        """
        warnings.warn(
            "read_one() is deprecated. Use read_by_id() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    def create(
        self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Insert a new record into the form storage.

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            data: Dictionary containing field values to insert

        Returns:
            The ID (27-char Crockford Base32) of the created record
            None if insertion failed

        Note:
            The ID is automatically generated using utils.crockford.generate_id()
            and added to the data before insertion.

        Example:
            data = {'nome': 'João', 'telefone': '11999999999', 'ativo': True}
            new_id = repo.create('contatos', spec, data)
            # new_id = '3HNMQR8PJSG0C9VWBYTE12K'
        """
        pass

    def bulk_create(
        self, form_path: str, spec: Dict[str, Any], records: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Insert multiple records in a single batch operation.

        This method provides optimized batch insertion, which is significantly
        faster than calling create() multiple times, especially for large datasets.

        Performance benefits:
        - SQLite: Single transaction instead of N commits
        - TXT: Single file write instead of N rewrites
        - Reduces I/O operations from O(n²) to O(n)

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            records: List of dictionaries containing field values

        Returns:
            List of IDs (27-char Crockford Base32) for created records
            None in list positions where insertion failed

        Example:
            records = [
                {'nome': 'João', 'telefone': '11999999999'},
                {'nome': 'Maria', 'telefone': '11988888888'}
            ]
            ids = repo.bulk_create('contatos', spec, records)
            # ids = ['3HNMQR8PJSG0C9VWBYTE12K', '2JK8VNQR3HMSG0C9PWBY']

        Note:
            Default implementation falls back to calling create() for each record.
            Subclasses should override this method for better performance.
        """
        # Default implementation: call create() for each record
        # Subclasses should override with optimized batch operations
        result_ids = []
        for record in records:
            record_id = self.create(form_path, spec, record)
            result_ids.append(record_id)
        return result_ids

    # =========================================================================
    # ID-BASED CRUD METHODS (NEW in v2.0)
    # =========================================================================

    @abstractmethod
    def read_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Read a single record by its unique ID.

        Args:
            form_path: Path to the form
            spec: Form specification for field type conversion
            record_id: 27-character Crockford Base32 ID

        Returns:
            Dictionary with record data (including 'id' field) if found
            None if ID doesn't exist

        Example:
            record = repo.read_by_id('contatos', spec, '3HNMQR8PJSG0C9VWBYTE12K')
            # {'id': '3HNMQR8PJSG0C9VWBYTE12K', 'nome': 'João', ...}
        """
        pass

    @abstractmethod
    def update_by_id(
        self,
        form_path: str,
        spec: Dict[str, Any],
        record_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update an existing record by its ID.

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            record_id: 27-character Crockford Base32 ID of the record
            data: Dictionary containing new field values (ID is immutable)

        Returns:
            True if record was updated successfully
            False if ID doesn't exist or update failed

        Note:
            The 'id' field cannot be changed. If present in data, it will be ignored.

        Example:
            success = repo.update_by_id(
                'contatos', spec,
                '3HNMQR8PJSG0C9VWBYTE12K',
                {'telefone': '11988888888'}
            )
        """
        pass

    @abstractmethod
    def delete_by_id(
        self, form_path: str, spec: Dict[str, Any], record_id: str
    ) -> bool:
        """
        Delete a record by its unique ID.

        Args:
            form_path: Path to the form
            spec: Form specification
            record_id: 27-character Crockford Base32 ID of the record

        Returns:
            True if record was deleted successfully
            False if ID doesn't exist or deletion failed

        Warning:
            Also deletes all tags associated with this record.

        Example:
            success = repo.delete_by_id('contatos', spec, '3HNMQR8PJSG0C9VWBYTE12K')
        """
        pass

    # =========================================================================
    # DEPRECATED INDEX-BASED METHODS (Backward compatibility)
    # =========================================================================

    @abstractmethod
    def update(
        self, form_path: str, spec: Dict[str, Any], idx: int, data: Dict[str, Any]
    ) -> bool:
        """
        [DEPRECATED] Update an existing record by index.

        .. deprecated:: 2.0
            Use :meth:`update_by_id` instead. Index-based access is being phased out
            in favor of UUID-based IDs for better data integrity and relationships.

        Args:
            form_path: Path to the form
            spec: Form specification for validation and type conversion
            idx: Zero-based index of the record to update
            data: Dictionary containing new field values

        Returns:
            True if record was updated successfully
            False if index doesn't exist or update failed

        Warning:
            This method will be removed in v3.0. Migrate to update_by_id().
        """
        warnings.warn(
            "update() is deprecated. Use update_by_id() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    def delete(self, form_path: str, spec: Dict[str, Any], idx: int) -> bool:
        """
        [DEPRECATED] Delete a record by its index.

        .. deprecated:: 2.0
            Use :meth:`delete_by_id` instead. Index-based access is being phased out
            in favor of UUID-based IDs for better data integrity and relationships.

        Args:
            form_path: Path to the form
            spec: Form specification
            idx: Zero-based index of the record to delete

        Returns:
            True if record was deleted successfully
            False if index doesn't exist or deletion failed

        Warning:
            This method will be removed in v3.0. Migrate to delete_by_id().
        """
        warnings.warn(
            "delete() is deprecated. Use delete_by_id() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

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
    def migrate_schema(
        self, form_path: str, old_spec: Dict[str, Any], new_spec: Dict[str, Any]
    ) -> bool:
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
    def rename_field(
        self, form_path: str, spec: Dict[str, Any], old_name: str, new_name: str
    ) -> bool:
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
        new_type: str,
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
    def remove_field(
        self, form_path: str, spec: Dict[str, Any], field_name: str
    ) -> bool:
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

    # =========================================================================
    # TAG MANAGEMENT METHODS (Tags as State - Convention #4)
    # =========================================================================

    @abstractmethod
    def add_tag(
        self,
        object_type: str,
        object_id: str,
        tag: str,
        applied_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a tag to an object (Tags as State convention).

        Tags represent object states in a workflow. This method adds a tag
        to an object, creating a state transition. All tag applications are
        timestamped and tracked for audit purposes.

        Args:
            object_type: Form path (e.g., 'contatos', 'deals', 'financeiro/contas')
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name (e.g., 'lead', 'qualified', 'proposal', 'won')
            applied_by: Who applied the tag (user_id, 'ai_agent', 'system')
            metadata: Optional metadata about the tag application
                     (e.g., {'reason': 'Customer requested', 'score': 85})

        Returns:
            True if tag was added successfully
            False if tag already exists or addition failed

        Implementation notes:
            - Tag names should be lowercase, alphanumeric, underscores allowed
            - Same tag can exist multiple times if removed and re-added (tracked in history)
            - Should validate that object_id exists before adding tag
            - Should store timestamp automatically (ISO 8601 format)
            - For SQLite: Insert into tags table
            - For TXT: Append to .tags.txt file

        Example:
            success = repo.add_tag(
                'deals', '3HNMQR8PJSG0C9VWBYTE12K',
                'qualified', 'user123',
                {'qualification_score': 85, 'product_interest': 'Enterprise'}
            )
        """
        pass

    @abstractmethod
    def remove_tag(
        self, object_type: str, object_id: str, tag: str, removed_by: str
    ) -> bool:
        """
        Remove a tag from an object.

        This method removes an active tag from an object. The tag history
        is preserved for audit purposes.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name to remove
            removed_by: Who removed the tag (user_id, 'ai_agent', 'system')

        Returns:
            True if tag was removed successfully
            False if tag doesn't exist or removal failed

        Implementation notes:
            - Should preserve tag history (mark as removed with timestamp)
            - Should not delete tag records, only mark as inactive
            - For SQLite: Update removed_at and removed_by columns
            - For TXT: Append removal record to .tags.txt

        Example:
            success = repo.remove_tag(
                'deals', '3HNMQR8PJSG0C9VWBYTE12K',
                'lead', 'user123'
            )
        """
        pass

    @abstractmethod
    def get_tags(
        self, object_type: str, object_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all tags for an object.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            active_only: If True, return only active tags (default)
                        If False, return all tags including removed ones

        Returns:
            List of tag dictionaries with metadata
            Empty list if object has no tags

        Each tag dictionary contains:
            - tag: Tag name (str)
            - applied_at: ISO 8601 timestamp (str)
            - applied_by: Who applied (str)
            - metadata: Optional metadata (dict or None)
            - removed_at: ISO 8601 timestamp or None (str or None)
            - removed_by: Who removed or None (str or None)

        Example:
            tags = repo.get_tags('deals', '3HNMQR8PJSG0C9VWBYTE12K')
            # [
            #     {
            #         'tag': 'qualified',
            #         'applied_at': '2025-01-14T10:30:00Z',
            #         'applied_by': 'user123',
            #         'metadata': {'score': 85},
            #         'removed_at': None,
            #         'removed_by': None
            #     }
            # ]
        """
        pass

    @abstractmethod
    def has_tag(self, object_type: str, object_id: str, tag: str) -> bool:
        """
        Check if an object currently has a specific active tag.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name to check

        Returns:
            True if object has the tag (and it's active)
            False otherwise

        Example:
            if repo.has_tag('deals', '3HNMQR8PJSG0C9VWBYTE12K', 'qualified'):
                # Process qualified deal
                pass
        """
        pass

    @abstractmethod
    def get_objects_by_tag(
        self, object_type: str, tag: str, active_only: bool = True
    ) -> List[str]:
        """
        Get all object IDs that have a specific tag.

        This is useful for queries like "find all qualified deals" or
        "find all active proposals".

        Args:
            object_type: Form path
            tag: Tag name to search for
            active_only: If True, only return objects with active tag (default)
                        If False, return objects that ever had the tag

        Returns:
            List of 27-character Crockford Base32 IDs
            Empty list if no objects have the tag

        Example:
            qualified_deals = repo.get_objects_by_tag('deals', 'qualified')
            # ['3HNMQR8PJSG0C9VWBYTE12K', '7KMPQR9PJSG0C9VWBYTE45L', ...]
        """
        pass

    @abstractmethod
    def get_tag_history(
        self, object_type: str, object_id: str, tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete tag history for an object.

        This returns the full audit trail of all tag applications and removals
        for an object, useful for workflow analysis and debugging.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tag: Optional tag name to filter history
                 If None, returns history for all tags

        Returns:
            List of tag event dictionaries, sorted by timestamp (oldest first)
            Empty list if no tag history exists

        Each event dictionary contains:
            - tag: Tag name (str)
            - event: 'applied' or 'removed' (str)
            - timestamp: ISO 8601 timestamp (str)
            - actor: Who performed the action (str)
            - metadata: Optional metadata (dict or None)

        Example:
            history = repo.get_tag_history('deals', '3HNMQR8PJSG0C9VWBYTE12K')
            # [
            #     {'tag': 'lead', 'event': 'applied', 'timestamp': '2025-01-10T09:00:00Z', ...},
            #     {'tag': 'lead', 'event': 'removed', 'timestamp': '2025-01-12T14:30:00Z', ...},
            #     {'tag': 'qualified', 'event': 'applied', 'timestamp': '2025-01-12T14:30:00Z', ...}
            # ]
        """
        pass

    @abstractmethod
    def get_tag_statistics(self, object_type: str) -> Dict[str, int]:
        """
        Get statistics about tag usage for a form type.

        This provides insights into workflow states and distribution.

        Args:
            object_type: Form path

        Returns:
            Dictionary mapping tag names to counts of objects with that tag
            Empty dict if no tags exist

        Example:
            stats = repo.get_tag_statistics('deals')
            # {
            #     'lead': 45,
            #     'qualified': 23,
            #     'proposal': 12,
            #     'won': 8,
            #     'lost': 15
            # }
        """
        pass
