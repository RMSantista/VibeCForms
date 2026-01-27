"""
VibeCForms v3.0: Relationship Repository Interface

This module defines the contract for relationship management in the new persistence paradigm.
All implementations must follow this interface for consistency across backends.

Date: 2026-01-08
Version: 1.0
Status: Design Phase
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass


class SyncStrategy(Enum):
    """
    Strategies for keeping display values synchronized with source data
    """

    EAGER = "eager"
    """
    Immediate synchronization (strong consistency)
    - When: Critical relationships (customer, supplier)
    - How: Trigger after UPDATE on target table
    - Cost: High (additional I/O immediately)
    - Guarantee: Always consistent
    """

    LAZY = "lazy"
    """
    On-read synchronization (eventual consistency)
    - When: Non-critical relationships (categories, tags)
    - How: Check + update in read_by_id() method
    - Cost: Medium (only if outdated)
    - Guarantee: Eventually consistent (seconds to minutes)
    """

    SCHEDULED = "scheduled"
    """
    Periodic background job (batch update)
    - When: Analysis relationships (statistics)
    - How: Cron job every N minutes
    - Cost: Low (optimized batch)
    - Guarantee: Eventually consistent (minutes to hours)
    """


class CardinalityType(Enum):
    """
    Relationship cardinality types
    """

    ONE_TO_ONE = "one_to_one"  # 1:1
    ONE_TO_MANY = "one_to_many"  # 1:N
    MANY_TO_MANY = "many_to_many"  # N:N


@dataclass
class Relationship:
    """Data class representing a relationship"""

    rel_id: str
    source_type: str
    source_id: str
    relationship_name: str
    target_type: str
    target_id: str
    created_at: str
    created_by: str
    removed_at: Optional[str] = None
    removed_by: Optional[str] = None
    metadata: Optional[Dict] = None

    def is_active(self) -> bool:
        """Check if relationship is not soft-deleted"""
        return self.removed_at is None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "rel_id": self.rel_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "relationship_name": self.relationship_name,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "removed_at": self.removed_at,
            "removed_by": self.removed_by,
            "metadata": self.metadata,
        }


class IRelationshipRepository(ABC):
    """
    Interface for relationship management in the new persistence paradigm.

    This repository handles all CRUD operations for relationships between entities,
    supporting all cardinality types (1:1, 1:N, N:N) through a uniform interface.

    Key Principles:
    - UUID-based identification (Crockford Base32)
    - Soft-delete semantics (removed_at field)
    - Metadata preservation (audit trail)
    - Sync strategy support (eager, lazy, scheduled)
    - Transaction safety
    """

    # ═══════════════════════════════════════════════════════════════════════
    # CREATION
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def create_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str,
        target_type: str,
        target_id: str,
        created_by: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a relationship between two entities.

        This method establishes a new relationship and updates display values
        if the sync strategy requires it.

        Args:
            source_type: Form path of source entity (e.g., "pedidos")
            source_id: UUID of source record
            relationship_name: Field name (e.g., "cliente", "produtos")
            target_type: Form path of target entity (e.g., "clientes")
            target_id: UUID of target record
            created_by: UUID of actor creating this relationship
            metadata: Optional JSON metadata for additional context

        Returns:
            rel_id: UUID of the created relationship

        Raises:
            ValidationError: If data is invalid
            TargetNotFoundError: If target record doesn't exist
            DuplicateRelationshipError: If relationship already exists
            TransactionError: If database transaction fails

        Example:
            rel_id = repo.create_relationship(
                source_type='pedidos',
                source_id='PEDIDO_001',
                relationship_name='cliente',
                target_type='clientes',
                target_id='CLIENTE_001',
                created_by='user@example.com'
            )
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """
        Get a single relationship by ID.

        Args:
            rel_id: UUID of the relationship

        Returns:
            Relationship object if found, None otherwise

        Raises:
            ValidationError: If rel_id is invalid
        """
        pass

    @abstractmethod
    def get_relationships(
        self,
        source_type: str,
        source_id: str,
        relationship_name: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Relationship]:
        """
        Get all relationships for an entity.

        Forward navigation: find all entities that THIS entity points to.

        Args:
            source_type: Form path of source entity
            source_id: UUID of source record
            relationship_name: Optional filter by field name
            active_only: If True, exclude soft-deleted relationships

        Returns:
            List of Relationship objects (empty if none found)

        Example:
            # Get all related entities for a pedido
            relationships = repo.get_relationships('pedidos', 'PEDIDO_001')

            # Get only customer (for 1:1)
            client_rel = repo.get_relationships(
                'pedidos', 'PEDIDO_001',
                relationship_name='cliente'
            )
        """
        pass

    @abstractmethod
    def get_reverse_relationships(
        self,
        target_type: str,
        target_id: str,
        relationship_name: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Relationship]:
        """
        Get all entities that point TO this entity (reverse navigation).

        Args:
            target_type: Form path of target entity
            target_id: UUID of target record
            relationship_name: Optional filter by field name
            active_only: If True, exclude soft-deleted relationships

        Returns:
            List of Relationship objects pointing to this entity

        Example:
            # Find all pedidos that reference a cliente
            pedidos = repo.get_reverse_relationships(
                'clientes', 'CLIENTE_001',
                relationship_name='cliente'
            )
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # DELETION
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def remove_relationship(self, rel_id: str, removed_by: str) -> bool:
        """
        Soft-delete a relationship (mark as removed, don't actually delete).

        This preserves audit trail and allows recovery if needed.

        Args:
            rel_id: UUID of the relationship to remove
            removed_by: UUID of actor performing the removal

        Returns:
            True if successful, False if relationship not found

        Raises:
            ValidationError: If rel_id is invalid
            TransactionError: If database transaction fails

        Note:
            This is a soft delete - the record remains in the database
            with removed_at and removed_by fields set.
        """
        pass

    @abstractmethod
    def restore_relationship(self, rel_id: str, restored_by: str) -> bool:
        """
        Restore a soft-deleted relationship.

        Args:
            rel_id: UUID of the relationship to restore
            restored_by: UUID of actor performing the restoration

        Returns:
            True if successful, False if relationship not found

        Raises:
            ValidationError: If rel_id is invalid
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # SYNCHRONIZATION
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def sync_display_values(
        self, source_type: str, source_id: str, relationship_name: Optional[str] = None
    ) -> int:
        """
        Synchronize display values in source records with target data.

        This method is typically called:
        - After a target entity's display field is updated (eager sync)
        - When reading a source entity (lazy sync)
        - By a background job (scheduled sync)

        Args:
            source_type: Form path of source entity
            source_id: UUID of source record to sync
            relationship_name: Optional filter to sync specific field only

        Returns:
            Number of records updated

        Raises:
            ValidationError: If parameters are invalid
            TransactionError: If database transaction fails

        Example:
            # Sync all display values for a pedido
            updated_count = repo.sync_display_values('pedidos', 'PEDIDO_001')

            # Sync only the cliente field
            updated_count = repo.sync_display_values(
                'pedidos', 'PEDIDO_001',
                relationship_name='cliente'
            )
        """
        pass

    @abstractmethod
    def validate_relationships(
        self, source_type: str, source_id: Optional[str] = None
    ) -> Dict:
        """
        Validate integrity of relationships.

        Checks for:
        - Orphaned relationships (targets that don't exist)
        - Inconsistent display values
        - Missing relationships for required fields

        Args:
            source_type: Form path to validate
            source_id: Optional specific record to validate

        Returns:
            {
                'valid': bool,
                'errors': [list of error descriptions],
                'orphans': [orphaned relationship IDs],
                'inconsistencies': [display value mismatches]
            }
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def count_relationships(
        self,
        source_type: str,
        source_id: Optional[str] = None,
        relationship_name: Optional[str] = None,
        active_only: bool = True,
    ) -> int:
        """
        Count relationships matching criteria.

        Args:
            source_type: Form path of source
            source_id: Optional UUID of specific source
            relationship_name: Optional field name to filter
            active_only: If True, count only non-deleted

        Returns:
            Number of matching relationships
        """
        pass

    @abstractmethod
    def get_relationship_stats(self, source_type: str) -> Dict:
        """
        Get statistics about relationships for a form.

        Returns:
            {
                'total': total relationships,
                'active': non-deleted count,
                'orphaned': count of orphaned relationships,
                'by_name': {relationship_name: count, ...},
                'by_cardinality': {type: count, ...}
            }
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # BATCH OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def create_relationships_batch(
        self, relationships: List[Dict], created_by: str
    ) -> List[str]:
        """
        Create multiple relationships in a single transaction.

        Args:
            relationships: List of relationship dicts with required fields
            created_by: UUID of actor creating these relationships

        Returns:
            List of created rel_ids

        Raises:
            ValidationError: If any relationship data is invalid
            TransactionError: If transaction fails (all-or-nothing)
        """
        pass

    @abstractmethod
    def remove_relationships_batch(self, rel_ids: List[str], removed_by: str) -> int:
        """
        Remove multiple relationships in a single transaction.

        Args:
            rel_ids: List of relationship IDs to remove
            removed_by: UUID of actor performing removal

        Returns:
            Number of relationships removed

        Raises:
            TransactionError: If transaction fails (all-or-nothing)
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # SCHEMA MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    @abstractmethod
    def create_relationship_table(self) -> bool:
        """
        Create the relationships table and indexes (idempotent).

        Returns:
            True if table created/already exists, False on error
        """
        pass

    @abstractmethod
    def drop_relationship_table(self) -> bool:
        """
        Drop the relationships table (destructive!).

        Returns:
            True if table dropped/didn't exist, False on error
        """
        pass

    @abstractmethod
    def table_exists(self) -> bool:
        """Check if relationships table exists."""
        pass
