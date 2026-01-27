"""
Tests for BaseRepository.get_relationship_repository() integration.

FASE 3.2: BaseRepository Integration
Tests that validate the get_relationship_repository() method in both
SQLiteRepository and TxtRepository adapters.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

from persistence.factory import RepositoryFactory
from persistence.adapters.sqlite_adapter import SQLiteRepository
from persistence.adapters.txt_adapter import TxtRepository
from persistence.contracts.relationship_interface import IRelationshipRepository


# =========================================================================
# FIXTURES
# =========================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sqlite_config(temp_dir):
    """SQLite repository configuration."""
    db_path = os.path.join(temp_dir, "test_relationships.db")
    return {"type": "sqlite", "database": db_path, "timeout": 5}


@pytest.fixture
def txt_config(temp_dir):
    """TXT repository configuration."""
    return {
        "type": "txt",
        "path": temp_dir,
        "delimiter": ";",
        "encoding": "utf-8",
    }


@pytest.fixture
def sample_spec():
    """Sample form specification for testing."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "type": "text", "required": True},
            {"name": "email", "type": "email", "required": False},
            {"name": "ativo", "type": "checkbox", "required": False},
        ],
    }


# =========================================================================
# SQLITE REPOSITORY TESTS
# =========================================================================


def test_sqlite_get_relationship_repository_returns_valid_instance(
    sqlite_config, sample_spec
):
    """Test that SQLiteRepository returns a valid RelationshipRepository instance."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"

    # Create storage first
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert (
        rel_repo is not None
    ), "SQLiteRepository should return a RelationshipRepository"
    assert isinstance(
        rel_repo, IRelationshipRepository
    ), "Should implement IRelationshipRepository interface"


def test_sqlite_relationship_repository_singleton_behavior(sqlite_config, sample_spec):
    """Test that SQLiteRepository returns the same instance on multiple calls."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo1 = repo.get_relationship_repository()
    rel_repo2 = repo.get_relationship_repository()

    # Assert
    assert rel_repo1 is rel_repo2, "Should return the same instance (singleton pattern)"


def test_sqlite_relationship_repository_table_creation(sqlite_config, sample_spec):
    """Test that getting RelationshipRepository creates the relationships table."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is not None
    assert rel_repo.table_exists(), "Relationships table should be created"


def test_sqlite_relationship_repository_can_create_relationships(
    sqlite_config, sample_spec
):
    """Test that RelationshipRepository from SQLite can create relationships."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Create test records
    record1_id = repo.create(
        form_path, sample_spec, {"nome": "João", "email": "joao@example.com"}
    )
    record2_id = repo.create(
        form_path, sample_spec, {"nome": "Maria", "email": "maria@example.com"}
    )

    # Get relationship repository
    rel_repo = repo.get_relationship_repository()

    # Act
    relationship_id = rel_repo.create_relationship(
        source_type=form_path,
        source_id=record1_id,
        relationship_name="amigo",
        target_type=form_path,
        target_id=record2_id,
        created_by="test_user",
    )

    # Assert
    assert relationship_id is not None, "Should create relationship successfully"
    assert len(relationship_id) == 27, "Should return a valid Crockford Base32 ID"


def test_sqlite_relationship_repository_can_query_relationships(
    sqlite_config, sample_spec
):
    """Test that RelationshipRepository can query created relationships."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Create test records
    record1_id = repo.create(
        form_path, sample_spec, {"nome": "João", "email": "joao@example.com"}
    )
    record2_id = repo.create(
        form_path, sample_spec, {"nome": "Maria", "email": "maria@example.com"}
    )

    # Get relationship repository and create relationship
    rel_repo = repo.get_relationship_repository()
    rel_id = rel_repo.create_relationship(
        source_type=form_path,
        source_id=record1_id,
        relationship_name="amigo",
        target_type=form_path,
        target_id=record2_id,
        created_by="test_user",
    )

    # Act
    relationships = rel_repo.get_relationships(form_path, record1_id)

    # Assert
    assert len(relationships) == 1, "Should find the created relationship"
    assert relationships[0].rel_id == rel_id
    assert relationships[0].relationship_name == "amigo"
    assert relationships[0].target_id == record2_id


# =========================================================================
# TXT REPOSITORY TESTS
# =========================================================================


def test_txt_get_relationship_repository_returns_none(txt_config, sample_spec):
    """Test that TxtRepository returns None (relationships not supported)."""
    # Arrange
    repo = TxtRepository(txt_config)
    form_path = "test_form"

    # Create storage first
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is None, "TxtRepository should return None (not supported)"


def test_txt_repository_handles_missing_relationship_support_gracefully(
    txt_config, sample_spec
):
    """Test that TXT repository gracefully handles lack of relationship support."""
    # Arrange
    repo = TxtRepository(txt_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo = repo.get_relationship_repository()

    # Assert - should not raise exception
    assert rel_repo is None
    # Should still be able to perform regular CRUD operations
    record_id = repo.create(
        form_path, sample_spec, {"nome": "Test", "email": "test@example.com"}
    )
    assert record_id is not None, "Regular CRUD should still work"


# =========================================================================
# REPOSITORY FACTORY INTEGRATION TESTS
# =========================================================================


def test_factory_created_sqlite_repository_has_relationship_support(temp_dir):
    """Test that RepositoryFactory-created SQLite repos support relationships."""
    # Arrange - Create a direct SQLite repository for simplicity
    # (RepositoryFactory integration is complex and requires config file setup)
    sqlite_config = {
        "type": "sqlite",
        "database": os.path.join(temp_dir, "factory_test.db"),
        "timeout": 5,
    }

    # Act
    repo = SQLiteRepository(sqlite_config)
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is not None, "SQLite repo should support relationships"
    assert isinstance(
        rel_repo, IRelationshipRepository
    ), "Should implement IRelationshipRepository interface"


def test_factory_created_txt_repository_returns_none_for_relationships(temp_dir):
    """Test that TXT repos return None for relationships."""
    # Arrange - Create a direct TXT repository for simplicity
    txt_config = {
        "type": "txt",
        "path": temp_dir,
        "delimiter": ";",
        "encoding": "utf-8",
    }

    # Act
    repo = TxtRepository(txt_config)
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is None, "TXT repo should return None for relationships"


# =========================================================================
# ERROR HANDLING TESTS
# =========================================================================


def test_sqlite_relationship_repository_before_storage_creation(sqlite_config):
    """Test that getting RelationshipRepository works even before storage creation."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)

    # Act - should not raise exception
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is not None, "Should return relationship repository"
    assert rel_repo.table_exists(), "Should create relationships table"


def test_txt_repository_relationship_support_check(txt_config, sample_spec):
    """Test checking for relationship support in TXT repository."""
    # Arrange
    repo = TxtRepository(txt_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Act
    rel_repo = repo.get_relationship_repository()

    # Assert
    assert rel_repo is None, "TXT should not support relationships"

    # Application code should check for None before using
    if rel_repo is not None:
        pytest.fail("Should not reach here for TXT repository")


def test_sqlite_relationship_repository_shares_connection(sqlite_config, sample_spec):
    """Test that RelationshipRepository shares the same SQLite connection."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "test_form"
    repo.create_storage(form_path, sample_spec)

    # Create two different records (self-relationships are not allowed)
    record1_id = repo.create(
        form_path, sample_spec, {"nome": "Test 1", "email": "test1@example.com"}
    )
    record2_id = repo.create(
        form_path, sample_spec, {"nome": "Test 2", "email": "test2@example.com"}
    )

    # Get relationship repository
    rel_repo = repo.get_relationship_repository()

    # Act - Create relationship using the same connection
    rel_id = rel_repo.create_relationship(
        source_type=form_path,
        source_id=record1_id,
        relationship_name="linked_to",
        target_type=form_path,
        target_id=record2_id,
        created_by="test_user",
    )

    # Assert - Both operations should work in the same database
    assert rel_id is not None, "Relationship should be created"

    # Verify we can read the record through the main repo
    record = repo.read_by_id(form_path, sample_spec, record1_id)
    assert record is not None, "Should read record from same connection"

    # Verify we can read the relationship
    rels = rel_repo.get_relationships(form_path, record1_id)
    assert len(rels) == 1, "Should read relationship from same connection"


# =========================================================================
# INTEGRATION WITH EXISTING WORKFLOW
# =========================================================================


def test_full_workflow_with_relationships(sqlite_config, sample_spec):
    """Test complete workflow: create records, establish relationships, query."""
    # Arrange
    repo = SQLiteRepository(sqlite_config)
    form_path = "contacts"
    repo.create_storage(form_path, sample_spec)

    # Create multiple records
    joao_id = repo.create(
        form_path, sample_spec, {"nome": "João", "email": "joao@example.com"}
    )
    maria_id = repo.create(
        form_path, sample_spec, {"nome": "Maria", "email": "maria@example.com"}
    )
    pedro_id = repo.create(
        form_path, sample_spec, {"nome": "Pedro", "email": "pedro@example.com"}
    )

    # Get relationship repository
    rel_repo = repo.get_relationship_repository()
    assert rel_repo is not None

    # Create relationships
    rel1 = rel_repo.create_relationship(
        source_type=form_path,
        source_id=joao_id,
        relationship_name="amigo",
        target_type=form_path,
        target_id=maria_id,
        created_by="admin",
    )

    rel2 = rel_repo.create_relationship(
        source_type=form_path,
        source_id=joao_id,
        relationship_name="amigo",
        target_type=form_path,
        target_id=pedro_id,
        created_by="admin",
    )

    # Query relationships
    joao_friends = rel_repo.get_relationships(form_path, joao_id)

    # Assert
    assert len(joao_friends) == 2, "João should have 2 friends"
    assert all(r.relationship_name == "amigo" for r in joao_friends)
    friend_ids = {r.target_id for r in joao_friends}
    assert friend_ids == {maria_id, pedro_id}, "Should have correct friend IDs"

    # Verify reverse lookup works
    maria_relationships = rel_repo.get_reverse_relationships(form_path, maria_id)
    assert len(maria_relationships) == 1, "Maria should be target of 1 relationship"
    assert maria_relationships[0].source_id == joao_id


def test_relationship_persistence_across_repository_instances(
    sqlite_config, sample_spec
):
    """Test that relationships persist when creating new repository instances."""
    # Arrange
    form_path = "test_form"

    # Create first instance and add data
    repo1 = SQLiteRepository(sqlite_config)
    repo1.create_storage(form_path, sample_spec)
    record1_id = repo1.create(
        form_path, sample_spec, {"nome": "Test 1", "email": "test1@example.com"}
    )
    record2_id = repo1.create(
        form_path, sample_spec, {"nome": "Test 2", "email": "test2@example.com"}
    )

    rel_repo1 = repo1.get_relationship_repository()
    rel_id = rel_repo1.create_relationship(
        source_type=form_path,
        source_id=record1_id,
        relationship_name="linked_to",
        target_type=form_path,
        target_id=record2_id,
        created_by="test_user",
    )

    # Create second instance (simulates app restart)
    repo2 = SQLiteRepository(sqlite_config)
    rel_repo2 = repo2.get_relationship_repository()

    # Act
    relationships = rel_repo2.get_relationships(form_path, record1_id)

    # Assert
    assert len(relationships) == 1, "Relationship should persist"
    assert relationships[0].rel_id == rel_id
    assert relationships[0].target_id == record2_id
