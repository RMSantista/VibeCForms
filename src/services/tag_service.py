"""
Tag Service for VibeCForms Tags as State Convention.

This service provides high-level API for managing tags in VibeCForms,
implementing Convention #4 (Tags as State) from CLAUDE.md.

Tags represent object states in workflows, enabling:
- State transitions (lead → qualified → proposal → closed)
- Multi-actor collaboration (humans, AI agents, subsystems)
- Event-driven workflows
- Audit trails and history tracking

The service layer sits above the repository layer, providing business logic
and convenience methods for common tag operations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from persistence.factory import RepositoryFactory
from utils.spec_loader import load_spec

# Configure logging
logger = logging.getLogger(__name__)


class TagService:
    """
    Service layer for tag management in VibeCForms.

    This service provides a unified interface for tag operations across
    all storage backends (TXT, SQLite, etc.), implementing the Tags as State
    convention.

    Example usage:
        # Initialize service
        tag_service = TagService()

        # Add tags (state transitions)
        tag_service.add_tag('deals', deal_id, 'qualified', user_id)

        # Check state
        if tag_service.has_tag('deals', deal_id, 'qualified'):
            # Process qualified deal
            pass

        # State transition
        tag_service.transition('deals', deal_id,
                              from_tag='qualified',
                              to_tag='proposal',
                              actor=user_id)

        # Query by state
        qualified_deals = tag_service.get_objects_with_tag('deals', 'qualified')
    """

    def __init__(self):
        """Initialize the TagService."""
        self.logger = logging.getLogger(__name__)

    def _get_repository(self, object_type: str):
        """
        Get the appropriate repository for an object type.

        Args:
            object_type: Form path (e.g., 'contatos', 'deals', 'financeiro/contas')

        Returns:
            Repository instance for the object type
        """
        return RepositoryFactory.get_repository(object_type)

    def add_tag(
        self,
        object_type: str,
        object_id: str,
        tag: str,
        applied_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a tag to an object.

        This represents adding a state to an object. Objects can have multiple
        tags simultaneously (e.g., a deal can be both "qualified" and "priority").

        Args:
            object_type: Form path (e.g., 'deals', 'contatos')
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name (should be lowercase, alphanumeric, underscores)
            applied_by: Who is adding the tag (user_id, 'ai_agent', 'system')
            metadata: Optional metadata about why/how tag was added

        Returns:
            True if tag was added successfully
            False if tag already exists or addition failed

        Example:
            # Human user qualifies a lead
            tag_service.add_tag('deals', deal_id, 'qualified', 'user123',
                              {'qualification_score': 85})

            # AI agent adds priority tag
            tag_service.add_tag('deals', deal_id, 'priority', 'ai_agent',
                              {'confidence': 0.92, 'reason': 'High value customer'})

            # System adds automated tag
            tag_service.add_tag('deals', deal_id, 'needs_followup', 'system',
                              {'days_since_contact': 7})
        """
        try:
            repo = self._get_repository(object_type)

            # Validate tag name format (lowercase, alphanumeric, underscores)
            if not self._validate_tag_name(tag):
                self.logger.warning(
                    f"Invalid tag name '{tag}'. Tags should be lowercase, "
                    f"alphanumeric with underscores only."
                )
                return False

            success = repo.add_tag(object_type, object_id, tag, applied_by, metadata)

            if success:
                self.logger.info(
                    f"Tag '{tag}' added to {object_type}/{object_id} by {applied_by}"
                )
            else:
                self.logger.warning(
                    f"Failed to add tag '{tag}' to {object_type}/{object_id}"
                )

            return success

        except Exception as e:
            self.logger.error(
                f"Error adding tag '{tag}' to {object_type}/{object_id}: {e}"
            )
            return False

    def remove_tag(
        self, object_type: str, object_id: str, tag: str, removed_by: str
    ) -> bool:
        """
        Remove a tag from an object.

        This represents removing a state from an object. The tag history is
        preserved for audit purposes.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name to remove
            removed_by: Who is removing the tag (user_id, 'ai_agent', 'system')

        Returns:
            True if tag was removed successfully
            False if tag doesn't exist or removal failed

        Example:
            # Move deal out of qualified state
            tag_service.remove_tag('deals', deal_id, 'qualified', 'user123')
        """
        try:
            repo = self._get_repository(object_type)
            success = repo.remove_tag(object_type, object_id, tag, removed_by)

            if success:
                self.logger.info(
                    f"Tag '{tag}' removed from {object_type}/{object_id} by {removed_by}"
                )
            else:
                self.logger.warning(
                    f"Failed to remove tag '{tag}' from {object_type}/{object_id}"
                )

            return success

        except Exception as e:
            self.logger.error(
                f"Error removing tag '{tag}' from {object_type}/{object_id}: {e}"
            )
            return False

    def has_tag(self, object_type: str, object_id: str, tag: str) -> bool:
        """
        Check if an object currently has a specific active tag.

        This is the primary method for checking object state.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tag: Tag name to check

        Returns:
            True if object has the tag (and it's active)
            False otherwise

        Example:
            # Check if deal is qualified
            if tag_service.has_tag('deals', deal_id, 'qualified'):
                # Send qualification email
                send_qualification_email(deal_id)
        """
        try:
            repo = self._get_repository(object_type)
            return repo.has_tag(object_type, object_id, tag)
        except Exception as e:
            self.logger.error(
                f"Error checking tag '{tag}' on {object_type}/{object_id}: {e}"
            )
            return False

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

        Example:
            # Get current states
            active_tags = tag_service.get_tags('deals', deal_id)

            # Get full history
            all_tags = tag_service.get_tags('deals', deal_id, active_only=False)
        """
        try:
            repo = self._get_repository(object_type)
            return repo.get_tags(object_type, object_id, active_only)
        except Exception as e:
            self.logger.error(f"Error getting tags for {object_type}/{object_id}: {e}")
            return []

    def get_objects_with_tag(
        self, object_type: str, tag: str, active_only: bool = True
    ) -> List[str]:
        """
        Get all object IDs that have a specific tag.

        This is the primary query method for finding objects in a specific state.

        Args:
            object_type: Form path
            tag: Tag name to search for
            active_only: If True, return only objects with active tag (default)

        Returns:
            List of object IDs (27-char Crockford Base32)
            Empty list if no objects have the tag

        Example:
            # Find all qualified deals
            qualified_deals = tag_service.get_objects_with_tag('deals', 'qualified')

            # Find all priority contacts
            priority_contacts = tag_service.get_objects_with_tag('contatos', 'priority')
        """
        try:
            repo = self._get_repository(object_type)
            return repo.get_objects_by_tag(object_type, tag, active_only)
        except Exception as e:
            self.logger.error(
                f"Error getting objects with tag '{tag}' for {object_type}: {e}"
            )
            return []

    def transition(
        self,
        object_type: str,
        object_id: str,
        from_tag: str,
        to_tag: str,
        actor: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Perform a state transition (remove old tag, add new tag).

        This is a convenience method for the common pattern of moving an object
        from one state to another.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            from_tag: Current tag to remove
            to_tag: New tag to add
            actor: Who is performing the transition (user_id, 'ai_agent', 'system')
            metadata: Optional metadata about the transition

        Returns:
            True if transition was successful (both operations completed)
            False if either operation failed

        Note:
            If from_tag doesn't exist, the method will still add to_tag.
            This allows flexible state transitions.

        Example:
            # Move deal from qualified to proposal
            tag_service.transition(
                'deals', deal_id,
                from_tag='qualified',
                to_tag='proposal',
                actor='user123',
                metadata={'proposal_sent_at': '2025-01-14T10:30:00Z'}
            )

            # AI agent moves deal to priority
            tag_service.transition(
                'deals', deal_id,
                from_tag='lead',
                to_tag='qualified',
                actor='ai_agent',
                metadata={'confidence': 0.95, 'score': 92}
            )
        """
        try:
            repo = self._get_repository(object_type)

            # Remove old tag if it exists
            # Don't fail the transition if the tag doesn't exist
            if self.has_tag(object_type, object_id, from_tag):
                remove_success = repo.remove_tag(
                    object_type, object_id, from_tag, actor
                )
                if not remove_success:
                    self.logger.warning(
                        f"Failed to remove '{from_tag}' during transition for "
                        f"{object_type}/{object_id}"
                    )

            # Add new tag
            add_success = repo.add_tag(object_type, object_id, to_tag, actor, metadata)

            if add_success:
                self.logger.info(
                    f"Transition {object_type}/{object_id}: {from_tag} → {to_tag} by {actor}"
                )
                return True
            else:
                self.logger.error(
                    f"Failed to add '{to_tag}' during transition for "
                    f"{object_type}/{object_id}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error during transition {from_tag}→{to_tag} for "
                f"{object_type}/{object_id}: {e}"
            )
            return False

    def has_any_tag(self, object_type: str, object_id: str, tags: List[str]) -> bool:
        """
        Check if an object has any of the specified tags.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tags: List of tag names to check

        Returns:
            True if object has at least one of the tags
            False otherwise

        Example:
            # Check if deal is in any active sales stage
            if tag_service.has_any_tag('deals', deal_id,
                                      ['qualified', 'proposal', 'negotiation']):
                # Deal is in active pipeline
                pass
        """
        for tag in tags:
            if self.has_tag(object_type, object_id, tag):
                return True
        return False

    def has_all_tags(self, object_type: str, object_id: str, tags: List[str]) -> bool:
        """
        Check if an object has all of the specified tags.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            tags: List of tag names to check

        Returns:
            True if object has all of the tags
            False otherwise

        Example:
            # Check if deal is both qualified and priority
            if tag_service.has_all_tags('deals', deal_id, ['qualified', 'priority']):
                # High-priority qualified deal
                notify_sales_manager(deal_id)
        """
        for tag in tags:
            if not self.has_tag(object_type, object_id, tag):
                return False
        return True

    def get_tag_names(
        self, object_type: str, object_id: str, active_only: bool = True
    ) -> List[str]:
        """
        Get just the tag names for an object (without metadata).

        This is a convenience method that extracts just the tag names
        from the full tag dictionaries.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            active_only: If True, return only active tags (default)

        Returns:
            List of tag names (strings)
            Empty list if object has no tags

        Example:
            # Get current state labels
            states = tag_service.get_tag_names('deals', deal_id)
            # ['qualified', 'priority', 'needs_followup']
        """
        tags = self.get_tags(object_type, object_id, active_only)
        return [tag["tag"] for tag in tags]

    def remove_all_tags(self, object_type: str, object_id: str, removed_by: str) -> int:
        """
        Remove all active tags from an object.

        This can be useful for "resetting" an object's state or cleaning up
        before deletion.

        Args:
            object_type: Form path
            object_id: 27-character Crockford Base32 ID of the object
            removed_by: Who is removing the tags (user_id, 'ai_agent', 'system')

        Returns:
            Number of tags that were removed

        Example:
            # Reset deal state
            removed_count = tag_service.remove_all_tags('deals', deal_id, 'user123')
        """
        tag_names = self.get_tag_names(object_type, object_id, active_only=True)
        removed_count = 0

        for tag in tag_names:
            if self.remove_tag(object_type, object_id, tag, removed_by):
                removed_count += 1

        return removed_count

    def _validate_tag_name(self, tag: str) -> bool:
        """
        Validate tag name format.

        Tags should be:
        - Lowercase
        - Alphanumeric characters
        - Underscores allowed
        - No spaces or special characters

        Args:
            tag: Tag name to validate

        Returns:
            True if valid, False otherwise

        Example:
            'qualified' → True
            'high_priority' → True
            'needs_followup' → True
            'High Priority' → False (uppercase, space)
            'qualified!' → False (special char)
        """
        import re

        # Pattern: lowercase letters, numbers, and underscores only
        pattern = r"^[a-z0-9_]+$"
        return bool(re.match(pattern, tag))


# Global instance (singleton pattern)
_tag_service_instance: Optional[TagService] = None


def get_tag_service() -> TagService:
    """
    Get the global TagService instance.

    This implements a singleton pattern to ensure only one TagService
    instance exists throughout the application lifecycle.

    Returns:
        TagService instance

    Example:
        tag_service = get_tag_service()
        tag_service.add_tag('deals', deal_id, 'qualified', user_id)
    """
    global _tag_service_instance

    if _tag_service_instance is None:
        _tag_service_instance = TagService()

    return _tag_service_instance
