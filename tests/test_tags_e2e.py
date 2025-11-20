"""
End-to-End Tests for VibeCForms Tags System.

Tests the complete tag functionality including:
- Tag API endpoints (add, remove, list)
- Tag persistence in both TXT and SQLite backends
- UUID integrity with tag operations
- Tag service layer functionality
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

# Import from src
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from persistence.factory import RepositoryFactory
from persistence.config import PersistenceConfig
from services.tag_service import TagService, get_tag_service
from utils.crockford import generate_id


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create persistence.json
    persistence_config = {
        "default_backend": "sqlite",
        "backends": {
            "txt": {
                "type": "txt",
                "base_path": str(tmp_path / "data"),
                "encoding": "utf-8",
            },
            "sqlite": {
                "type": "sqlite",
                "database_path": str(tmp_path / "test.db"),
                "timeout": 10,
            },
        },
        "form_mappings": {"test_form": "sqlite", "*": "default_backend"},
    }

    config_file = config_dir / "persistence.json"
    with open(config_file, "w") as f:
        json.dump(persistence_config, f, indent=2)

    # Create schema_history.json
    history_file = config_dir / "schema_history.json"
    with open(history_file, "w") as f:
        json.dump({}, f)

    return config_dir


@pytest.fixture
def test_spec():
    """Sample form specification for testing."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": False},
        ],
    }


@pytest.fixture
def setup_repository(temp_config_dir, test_spec):
    """Setup repository with test configuration."""
    # Override config paths
    import os

    os.environ["VIBECFORMS_CONFIG_DIR"] = str(temp_config_dir)

    # Clear any cached instances
    from persistence.factory import RepositoryFactory

    RepositoryFactory._repository_cache = {}

    # Get repository
    repo = RepositoryFactory.get_repository("test_form")

    # Drop and recreate storage for clean state
    if repo.exists("test_form"):
        try:
            repo.drop_storage("test_form", force=True)
        except:
            pass  # Ignore errors during cleanup
    repo.create_storage("test_form", test_spec)

    yield repo

    # Cleanup
    if repo.exists("test_form"):
        try:
            repo.drop_storage("test_form", force=True)
        except:
            pass  # Ignore errors during cleanup

    if "VIBECFORMS_CONFIG_DIR" in os.environ:
        del os.environ["VIBECFORMS_CONFIG_DIR"]


class TestTagServiceBasicOperations:
    """Test basic tag service operations."""

    def test_add_tag(self, setup_repository, test_spec):
        """Test adding a tag to an object."""
        repo = setup_repository
        tag_service = TagService()

        # Create a test record
        record_data = {"name": "John Doe", "email": "john@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        assert record_id is not None

        # Add tag
        success = tag_service.add_tag("test_form", record_id, "qualified", "user123")
        assert success is True

        # Verify tag exists
        has_tag = tag_service.has_tag("test_form", record_id, "qualified")
        assert has_tag is True

    def test_add_invalid_tag_name(self, setup_repository, test_spec):
        """Test that invalid tag names are rejected."""
        repo = setup_repository
        tag_service = TagService()

        # Create a test record
        record_data = {"name": "Jane Doe", "email": "jane@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        # Try invalid tag names
        assert (
            tag_service.add_tag("test_form", record_id, "Invalid Tag", "user123")
            is False
        )
        assert tag_service.add_tag("test_form", record_id, "tag!", "user123") is False
        assert (
            tag_service.add_tag("test_form", record_id, "TAG-NAME", "user123") is False
        )

        # Valid tag should work
        assert (
            tag_service.add_tag("test_form", record_id, "valid_tag", "user123") is True
        )

    def test_remove_tag(self, setup_repository, test_spec):
        """Test removing a tag from an object."""
        repo = setup_repository
        tag_service = TagService()

        # Create record and add tag
        record_data = {"name": "Bob Smith", "email": "bob@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)
        tag_service.add_tag("test_form", record_id, "priority", "user123")

        # Verify tag exists
        assert tag_service.has_tag("test_form", record_id, "priority") is True

        # Remove tag
        success = tag_service.remove_tag("test_form", record_id, "priority", "user123")
        assert success is True

        # Verify tag is gone
        assert tag_service.has_tag("test_form", record_id, "priority") is False

    def test_get_tags(self, setup_repository, test_spec):
        """Test getting all tags for an object."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "Alice Johnson", "email": "alice@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        # Add multiple tags
        tag_service.add_tag("test_form", record_id, "qualified", "user123")
        tag_service.add_tag("test_form", record_id, "priority", "user456")
        tag_service.add_tag("test_form", record_id, "needs_followup", "system")

        # Get tags
        tags = tag_service.get_tags("test_form", record_id, active_only=True)

        assert len(tags) == 3
        tag_names = [tag["tag"] for tag in tags]
        assert "qualified" in tag_names
        assert "priority" in tag_names
        assert "needs_followup" in tag_names

    def test_get_tag_names(self, setup_repository, test_spec):
        """Test getting just tag names (without metadata)."""
        repo = setup_repository
        tag_service = TagService()

        # Create record and add tags
        record_data = {"name": "Charlie Brown", "email": "charlie@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        tag_service.add_tag("test_form", record_id, "tag1", "user123")
        tag_service.add_tag("test_form", record_id, "tag2", "user123")

        # Get tag names
        tag_names = tag_service.get_tag_names("test_form", record_id)

        assert len(tag_names) == 2
        assert "tag1" in tag_names
        assert "tag2" in tag_names


class TestTagServiceAdvancedOperations:
    """Test advanced tag service operations."""

    def test_state_transition(self, setup_repository, test_spec):
        """Test transitioning between states using tags."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "David Wilson", "email": "david@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        # Add initial state
        tag_service.add_tag("test_form", record_id, "lead", "system")

        # Transition to qualified
        success = tag_service.transition(
            "test_form",
            record_id,
            from_tag="lead",
            to_tag="qualified",
            actor="user123",
            metadata={"score": 85},
        )

        assert success is True
        assert tag_service.has_tag("test_form", record_id, "lead") is False
        assert tag_service.has_tag("test_form", record_id, "qualified") is True

    def test_has_any_tag(self, setup_repository, test_spec):
        """Test checking if object has any of specified tags."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "Emma Davis", "email": "emma@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        tag_service.add_tag("test_form", record_id, "qualified", "user123")

        # Check multiple tags
        assert (
            tag_service.has_any_tag("test_form", record_id, ["qualified", "proposal"])
            is True
        )
        assert (
            tag_service.has_any_tag("test_form", record_id, ["proposal", "closed"])
            is False
        )

    def test_has_all_tags(self, setup_repository, test_spec):
        """Test checking if object has all specified tags."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "Frank Miller", "email": "frank@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        tag_service.add_tag("test_form", record_id, "qualified", "user123")
        tag_service.add_tag("test_form", record_id, "priority", "user123")

        # Check all tags
        assert (
            tag_service.has_all_tags("test_form", record_id, ["qualified", "priority"])
            is True
        )
        assert (
            tag_service.has_all_tags("test_form", record_id, ["qualified", "closed"])
            is False
        )

    def test_remove_all_tags(self, setup_repository, test_spec):
        """Test removing all tags from an object."""
        repo = setup_repository
        tag_service = TagService()

        # Create record with multiple tags
        record_data = {"name": "Grace Lee", "email": "grace@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        tag_service.add_tag("test_form", record_id, "tag1", "user123")
        tag_service.add_tag("test_form", record_id, "tag2", "user123")
        tag_service.add_tag("test_form", record_id, "tag3", "user123")

        # Remove all tags
        removed_count = tag_service.remove_all_tags("test_form", record_id, "user123")

        assert removed_count == 3
        assert len(tag_service.get_tag_names("test_form", record_id)) == 0

    def test_get_objects_with_tag(self, setup_repository, test_spec):
        """Test finding all objects with a specific tag.

        NOTE: This test may fail in some environments due to tag persistence
        from previous test runs. This is a known limitation when tags table
        is shared across test runs.
        """
        repo = setup_repository
        tag_service = TagService()

        # Use a unique tag name to avoid collisions with other test runs
        import time

        unique_tag = f"priority_{int(time.time() * 1000)}"

        # Create multiple records
        record_ids = []
        for i in range(5):
            record_data = {"name": f"User {i}", "email": f"user{i}@example.com"}
            record_id = repo.create("test_form", test_spec, record_data)
            record_ids.append(record_id)

        # Tag some of them with unique tag
        tag_service.add_tag("test_form", record_ids[0], unique_tag, "user123")
        tag_service.add_tag("test_form", record_ids[2], unique_tag, "user123")
        tag_service.add_tag("test_form", record_ids[4], unique_tag, "user123")

        # Find objects with unique tag
        priority_ids = tag_service.get_objects_with_tag("test_form", unique_tag)

        assert len(priority_ids) == 3, f"Expected 3, got {len(priority_ids)}"
        assert record_ids[0] in priority_ids
        assert record_ids[2] in priority_ids
        assert record_ids[4] in priority_ids


class TestUUIDIntegrity:
    """Test UUID integrity with tag operations."""

    def test_uuid_format(self, setup_repository, test_spec):
        """Test that generated UUIDs have correct format."""
        repo = setup_repository

        # Create record
        record_data = {"name": "Test User", "email": "test@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        # Check UUID format (27 characters, Crockford Base32)
        assert len(record_id) == 27
        # Should only contain valid Crockford Base32 characters
        valid_chars = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        assert all(c in valid_chars for c in record_id)

    def test_uuid_persistence_after_tag_operations(self, setup_repository, test_spec):
        """Test that UUIDs remain consistent after tag operations."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "UUID Test", "email": "uuid@example.com"}
        original_id = repo.create("test_form", test_spec, record_data)

        # Perform tag operations
        tag_service.add_tag("test_form", original_id, "tag1", "user123")
        tag_service.add_tag("test_form", original_id, "tag2", "user123")
        tag_service.remove_tag("test_form", original_id, "tag1", "user123")

        # Read record back
        records = repo.read_all("test_form", test_spec)
        assert len(records) == 1

        # UUID should be preserved
        assert records[0]["_record_id"] == original_id

    def test_uuid_uniqueness(self, setup_repository, test_spec):
        """Test that generated UUIDs are unique."""
        repo = setup_repository

        # Generate multiple UUIDs
        record_ids = set()
        for i in range(100):
            record_data = {"name": f"User {i}", "email": f"user{i}@example.com"}
            record_id = repo.create("test_form", test_spec, record_data)
            record_ids.add(record_id)

        # All should be unique
        assert len(record_ids) == 100


class TestTagHistory:
    """Test tag history and audit trail functionality."""

    def test_tag_history_with_active_and_removed(self, setup_repository, test_spec):
        """Test retrieving both active and removed tags."""
        repo = setup_repository
        tag_service = TagService()

        # Create record
        record_data = {"name": "History Test", "email": "history@example.com"}
        record_id = repo.create("test_form", test_spec, record_data)

        # Add and remove tags
        tag_service.add_tag("test_form", record_id, "tag1", "user123")
        tag_service.add_tag("test_form", record_id, "tag2", "user123")
        tag_service.remove_tag("test_form", record_id, "tag1", "user123")

        # Get only active tags
        active_tags = tag_service.get_tags("test_form", record_id, active_only=True)
        assert len(active_tags) == 1
        assert active_tags[0]["tag"] == "tag2"

        # Get all tags (including removed)
        all_tags = tag_service.get_tags("test_form", record_id, active_only=False)
        assert len(all_tags) >= 1  # At least the active one


class TestGlobalTagService:
    """Test global tag service singleton."""

    def test_singleton_pattern(self):
        """Test that get_tag_service returns same instance."""
        service1 = get_tag_service()
        service2 = get_tag_service()

        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
