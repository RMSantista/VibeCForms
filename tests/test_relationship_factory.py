"""
Tests for RelationshipRepository Factory Pattern Integration (FASE 3.1)

Tests the RepositoryFactory methods for creating and configuring
RelationshipRepository instances.
"""

import pytest
import os
import sys
import sqlite3
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from persistence.factory import RepositoryFactory
from persistence.contracts.relationship_interface import SyncStrategy, CardinalityType
from persistence.config import get_config


@pytest.fixture
def temp_db_with_relationships(tmp_path):
    """Create a temporary database with relationships table."""
    db_path = tmp_path / "test_relationships.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create relationships table
    cursor.execute(
        """
        CREATE TABLE relationships (
            rel_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relationship_name TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            removed_at TEXT,
            removed_by TEXT,
            metadata TEXT,
            UNIQUE(source_type, source_id, relationship_name, target_id)
        )
    """
    )

    # Create test tables
    cursor.execute(
        """
        CREATE TABLE pedidos (
            record_id TEXT PRIMARY KEY,
            quantidade INTEGER,
            _cliente_display TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE clientes (
            record_id TEXT PRIMARY KEY,
            nome TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def mock_sqlite_config(temp_db_with_relationships, monkeypatch):
    """Mock persistence config to use temp database."""
    import json

    config_data = {
        "version": "1.0",
        "default_backend": "sqlite",
        "backends": {
            "sqlite": {
                "type": "sqlite",
                "database": str(temp_db_with_relationships),
                "timeout": 10,
                "check_same_thread": False,
            }
        },
        "form_mappings": {"*": "default_backend"},
        "relationships": {
            "default_sync_strategy": "eager",
            "sync_strategy_mappings": {
                "pedidos.cliente": "eager",
                "pedidos.produtos": "lazy",
                "*": "default_sync_strategy",
            },
            "cardinality_rules": {
                "pedidos.cliente": "one_to_one",
                "pedidos.produtos": "one_to_many",
            },
        },
    }

    # Write temporary config
    temp_config_path = temp_db_with_relationships.parent / "persistence.json"
    with open(temp_config_path, "w") as f:
        json.dump(config_data, f)

    # Mock config path
    def mock_get_config():
        from persistence.config import PersistenceConfig

        return PersistenceConfig(str(temp_config_path))

    monkeypatch.setattr("persistence.factory.get_config", mock_get_config)
    monkeypatch.setattr("persistence.config.get_config", mock_get_config)

    # Clear factory cache
    RepositoryFactory.clear_cache()

    return temp_config_path


class TestRepositoryFactoryRelationships:
    """Test suite for RelationshipRepository factory methods"""

    def test_create_relationship_repository(self, mock_sqlite_config):
        """Test creating a RelationshipRepository via factory"""
        # Create relationship repository
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        assert rel_repo is not None
        assert hasattr(rel_repo, "conn")
        assert hasattr(rel_repo, "sync_strategy")
        assert hasattr(rel_repo, "cardinality_rules")

    def test_relationship_repository_has_correct_sync_strategy(
        self, mock_sqlite_config
    ):
        """Test that repository gets correct sync strategy from config"""
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        # Default is EAGER
        assert rel_repo.sync_strategy == SyncStrategy.EAGER

    def test_relationship_repository_has_cardinality_rules(self, mock_sqlite_config):
        """Test that repository loads cardinality rules from config"""
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        # Should have cardinality rules loaded
        assert len(rel_repo.cardinality_rules) > 0
        assert "pedidos.cliente" in rel_repo.cardinality_rules
        assert (
            rel_repo.cardinality_rules["pedidos.cliente"] == CardinalityType.ONE_TO_ONE
        )

    def test_get_sync_strategy_default(self, mock_sqlite_config):
        """Test get_sync_strategy returns default EAGER"""
        strategy = RepositoryFactory.get_sync_strategy("unknown_form")

        assert strategy == SyncStrategy.EAGER

    def test_get_sync_strategy_from_config(self, mock_sqlite_config):
        """Test get_sync_strategy reads from config"""
        # Config has default_sync_strategy: "eager"
        strategy = RepositoryFactory.get_sync_strategy("pedidos")

        assert strategy == SyncStrategy.EAGER

    def test_get_cardinality_rules_loads_all_rules(self, mock_sqlite_config):
        """Test get_cardinality_rules loads all rules from config"""
        rules = RepositoryFactory.get_cardinality_rules()

        assert len(rules) == 2  # Two rules in config
        assert rules["pedidos.cliente"] == CardinalityType.ONE_TO_ONE
        assert rules["pedidos.produtos"] == CardinalityType.ONE_TO_MANY

    def test_get_cardinality_rules_maps_strings_to_enums(self, mock_sqlite_config):
        """Test that string values are correctly mapped to CardinalityType enums"""
        rules = RepositoryFactory.get_cardinality_rules()

        # Verify enum types
        assert isinstance(rules["pedidos.cliente"], CardinalityType)
        assert isinstance(rules["pedidos.produtos"], CardinalityType)

    def test_relationship_repository_shares_connection_with_main_repo(
        self, mock_sqlite_config
    ):
        """Test that RelationshipRepository uses same connection as main repository"""
        # Get main repository
        main_repo = RepositoryFactory.get_repository("pedidos")

        # Create relationship repository
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        # Should share same connection
        assert rel_repo.conn is main_repo.conn

    def test_create_relationship_repository_for_txt_backend_returns_none(
        self, monkeypatch
    ):
        """Test that factory returns None for backends without database connection"""

        # Mock config for TXT backend
        def mock_get_config_txt():
            from persistence.config import PersistenceConfig
            import json
            import tempfile

            temp_dir = tempfile.mkdtemp()
            config_data = {
                "version": "1.0",
                "default_backend": "txt",
                "backends": {
                    "txt": {
                        "type": "txt",
                        "path": temp_dir,
                        "delimiter": ";",
                        "encoding": "utf-8",
                        "extension": ".txt",
                    }
                },
                "form_mappings": {"*": "default_backend"},
            }

            config_path = Path(temp_dir) / "persistence.json"
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            return PersistenceConfig(str(config_path))

        monkeypatch.setattr("persistence.factory.get_config", mock_get_config_txt)
        RepositoryFactory.clear_cache()

        # Try to create relationship repository for TXT backend
        rel_repo = RepositoryFactory.create_relationship_repository("test_form")

        # Should return None (TXT doesn't support relationships)
        assert rel_repo is None

    def test_factory_methods_handle_missing_relationships_config(
        self, temp_db_with_relationships, monkeypatch
    ):
        """Test that factory methods handle missing relationships config gracefully"""
        import json

        # Create config without relationships section
        config_data = {
            "version": "1.0",
            "default_backend": "sqlite",
            "backends": {
                "sqlite": {
                    "type": "sqlite",
                    "database": str(temp_db_with_relationships),
                    "timeout": 10,
                    "check_same_thread": False,
                }
            },
            "form_mappings": {"*": "default_backend"},
            # No "relationships" section!
        }

        temp_config_path = temp_db_with_relationships.parent / "persistence_no_rel.json"
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        def mock_get_config():
            from persistence.config import PersistenceConfig

            return PersistenceConfig(str(temp_config_path))

        monkeypatch.setattr("persistence.factory.get_config", mock_get_config)
        RepositoryFactory.clear_cache()

        # Should not crash, should use defaults
        strategy = RepositoryFactory.get_sync_strategy("pedidos")
        assert strategy == SyncStrategy.EAGER

        rules = RepositoryFactory.get_cardinality_rules()
        assert rules == {}  # Empty dict when no config


class TestFactoryIntegrationWithRelationshipRepository:
    """Integration tests between Factory and RelationshipRepository"""

    def test_end_to_end_relationship_creation_via_factory(
        self, mock_sqlite_config, temp_db_with_relationships
    ):
        """Test complete workflow: factory → create relationship → verify"""
        # Get relationship repository from factory
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        # Insert test data
        conn = sqlite3.connect(str(temp_db_with_relationships))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (record_id, nome, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("CLI001", "João Silva", "2026-01-10T10:00:00", "2026-01-10T10:00:00"),
        )
        cursor.execute(
            "INSERT INTO pedidos (record_id, quantidade, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("PED001", 10, "2026-01-10T10:01:00", "2026-01-10T10:01:00"),
        )
        conn.commit()
        conn.close()

        # Create relationship using factory-created repository
        rel_id = rel_repo.create_relationship(
            source_type="pedidos",
            source_id="PED001",
            relationship_name="cliente",
            target_type="clientes",
            target_id="CLI001",
            created_by="test_user",
        )

        assert rel_id is not None
        assert len(rel_id) > 0

        # Verify relationship was created
        rels = rel_repo.get_relationships("pedidos", "PED001")
        assert len(rels) == 1
        assert rels[0].target_id == "CLI001"

    def test_factory_respects_cardinality_rules(
        self, mock_sqlite_config, temp_db_with_relationships
    ):
        """Test that factory-created repository enforces cardinality rules"""
        rel_repo = RepositoryFactory.create_relationship_repository("pedidos")

        # Insert test data
        conn = sqlite3.connect(str(temp_db_with_relationships))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (record_id, nome, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("CLI001", "João Silva", "2026-01-10T10:00:00", "2026-01-10T10:00:00"),
        )
        cursor.execute(
            "INSERT INTO clientes (record_id, nome, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("CLI002", "Maria Santos", "2026-01-10T10:00:00", "2026-01-10T10:00:00"),
        )
        cursor.execute(
            "INSERT INTO pedidos (record_id, quantidade, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("PED001", 10, "2026-01-10T10:01:00", "2026-01-10T10:01:00"),
        )
        conn.commit()
        conn.close()

        # Create first relationship (should work - 1:1 allows one)
        rel_id1 = rel_repo.create_relationship(
            source_type="pedidos",
            source_id="PED001",
            relationship_name="cliente",
            target_type="clientes",
            target_id="CLI001",
            created_by="test_user",
        )
        assert rel_id1 is not None

        # Try to create second relationship (should fail - cardinality is ONE_TO_ONE)
        with pytest.raises(
            ValueError, match="Cannot add more targets to 1:1 relationship"
        ):
            rel_repo.create_relationship(
                source_type="pedidos",
                source_id="PED001",
                relationship_name="cliente",
                target_type="clientes",
                target_id="CLI002",
                created_by="test_user",
            )
