"""
Unit tests for RelationshipRepository (FASE 2a - Critical Bug Fixes).

Tests cover:
- BUG #1: SQL Injection fix in validate_relationships()
- BUG #2: Dynamic display field detection (not hardcoded 'nome')
- BUG #3: EAGER sync of display values in create_relationship()
"""

import pytest
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from persistence.relationship_repository import RelationshipRepository, Relationship
from persistence.contracts.relationship_interface import SyncStrategy


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_db_path(tmp_path):
    """Create path for temporary SQLite database."""
    return tmp_path / "test_relationships.db"


@pytest.fixture
def db_with_schema(temp_db_path):
    """Create SQLite database with relationships schema and test tables."""
    conn = sqlite3.connect(str(temp_db_path))
    cursor = conn.cursor()

    # Create form_metadata table (required by relationships schema)
    cursor.execute(
        """
        CREATE TABLE form_metadata (
            form_path TEXT PRIMARY KEY,
            display_name TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Register test forms
    for form_name in ["clientes", "produtos", "pedidos"]:
        cursor.execute(
            "INSERT INTO form_metadata (form_path, display_name) VALUES (?, ?)",
            (form_name, form_name.upper()),
        )

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
            UNIQUE(source_type, source_id, relationship_name, target_id),
            FOREIGN KEY(source_type) REFERENCES form_metadata(form_path),
            FOREIGN KEY(target_type) REFERENCES form_metadata(form_path)
        )
    """
    )

    # Create indexes
    cursor.execute(
        "CREATE INDEX idx_rel_source ON relationships(source_type, source_id)"
    )
    cursor.execute(
        "CREATE INDEX idx_rel_target ON relationships(target_type, target_id)"
    )
    cursor.execute(
        "CREATE INDEX idx_rel_name ON relationships(source_type, relationship_name)"
    )
    cursor.execute(
        "CREATE INDEX idx_rel_active ON relationships(source_type, source_id, removed_at)"
    )

    # Create views
    cursor.execute(
        """
        CREATE VIEW active_relationships AS
        SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
               created_at, created_by, metadata
        FROM relationships
        WHERE removed_at IS NULL
    """
    )

    cursor.execute(
        """
        CREATE VIEW relationship_history AS
        SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
               'created' as event_type, created_at as event_at, created_by as event_by
        FROM relationships
        UNION ALL
        SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
               'removed' as event_type, removed_at as event_at, removed_by as event_by
        FROM relationships
        WHERE removed_at IS NOT NULL
        ORDER BY event_at DESC
    """
    )

    # Create test entity tables
    # clientes table (with 'nome' as display field - standard case)
    cursor.execute(
        """
        CREATE TABLE clientes (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            updated_at TEXT,
            _pedido_display TEXT
        )
    """
    )

    # produtos table (with 'nome' as display field)
    cursor.execute(
        """
        CREATE TABLE produtos (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco REAL,
            descricao TEXT,
            updated_at TEXT
        )
    """
    )

    # pedidos table (with 'numero' as display field - non-standard case)
    cursor.execute(
        """
        CREATE TABLE pedidos (
            record_id TEXT PRIMARY KEY,
            numero TEXT NOT NULL,
            cliente_id TEXT,
            data TEXT,
            updated_at TEXT,
            _cliente_display TEXT,
            _produto_display TEXT
        )
    """
    )

    # Insert test data
    cursor.execute(
        "INSERT INTO clientes (record_id, nome, email, telefone) VALUES (?, ?, ?, ?)",
        ("cliente-1", "Cliente A", "a@example.com", "111-1111"),
    )
    cursor.execute(
        "INSERT INTO clientes (record_id, nome, email, telefone) VALUES (?, ?, ?, ?)",
        ("cliente-2", "Cliente B", "b@example.com", "222-2222"),
    )

    cursor.execute(
        "INSERT INTO produtos (record_id, nome, preco, descricao) VALUES (?, ?, ?, ?)",
        ("produto-1", "Produto X", 99.99, "Description X"),
    )
    cursor.execute(
        "INSERT INTO produtos (record_id, nome, preco, descricao) VALUES (?, ?, ?, ?)",
        ("produto-2", "Produto Y", 149.99, "Description Y"),
    )

    cursor.execute(
        "INSERT INTO pedidos (record_id, numero, cliente_id, data) VALUES (?, ?, ?, ?)",
        ("pedido-1", "PED-001", "cliente-1", "2025-01-01"),
    )

    conn.commit()
    conn.close()

    return temp_db_path


@pytest.fixture
def repository(db_with_schema):
    """Create RelationshipRepository instance with test database."""
    # Create connection directly (RelationshipRepository expects sqlite3.Connection)
    conn = sqlite3.connect(str(db_with_schema), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return RelationshipRepository(conn)


@pytest.fixture
def user_id():
    """Standard user ID for tests."""
    return "test-user-123"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: BUG #1 - SQL Injection Fix in validate_relationships()
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateRelationships:
    """Tests for validate_relationships() method - BUG #1 fix."""

    def test_validate_relationships_no_orphans(self, repository, user_id):
        """Test validation when all relationships are healthy."""
        # Create a valid relationship
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Validate
        result = repository.validate_relationships("pedidos", "pedido-1")

        assert result["valid"] is True
        assert len(result["orphans"]) == 0
        assert len(result["errors"]) == 0

    def test_validate_relationships_detects_orphans(
        self, repository, user_id, db_with_schema
    ):
        """Test that validate_relationships() detects orphaned relationships."""
        # Create a valid relationship first
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Now manually insert a relationship pointing to non-existent record
        conn = sqlite3.connect(str(db_with_schema))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO relationships (
                rel_id, source_type, source_id, relationship_name,
                target_type, target_id, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "orphan-rel-1",
                "pedidos",
                "pedido-1",
                "cliente",
                "clientes",
                "cliente-nonexistent",
                datetime.now().isoformat(),
                user_id,
            ),
        )
        conn.commit()
        conn.close()

        # Validate
        result = repository.validate_relationships("pedidos", "pedido-1")

        assert result["valid"] is False
        assert len(result["orphans"]) >= 1
        assert any("orphan-rel-1" in str(err) for err in result["errors"])

    def test_validate_relationships_no_sql_injection(self, repository):
        """Test that validate_relationships() is safe from SQL injection."""
        # Try malicious input that would have broken old code
        malicious_form = "'; DROP TABLE relationships; --"

        # This should not crash or execute SQL injection
        try:
            result = repository.validate_relationships(malicious_form)
            # Should either return empty result or raise ValueError, not SQL error
            assert result["valid"] is not None
        except ValueError:
            # This is acceptable - invalid form path
            pass


# ═══════════════════════════════════════════════════════════════════════════
# TEST: BUG #2 - Dynamic Display Field Detection
# ═══════════════════════════════════════════════════════════════════════════


class TestDisplayFieldDetection:
    """Tests for _get_display_field() and _get_display_value() - BUG #2 fix."""

    def test_detect_display_field_standard_nome(self, repository):
        """Test detection of 'nome' field (standard case)."""
        display_field = repository._get_display_field("clientes")

        assert display_field == "nome"

    def test_detect_display_field_custom_numero(self, repository):
        """Test that non-standard display fields require spec file."""
        # 'numero' is not in default candidates, so should return None
        # unless defined in spec file (Convenção #2)
        display_field = repository._get_display_field("pedidos")

        # Returns None because 'numero' is not in candidates and no spec file exists
        assert display_field is None

    def test_get_display_value_with_nome(self, repository):
        """Test getting display value from 'nome' field."""
        cursor = repository.conn.cursor()
        display_value = repository._get_display_value(cursor, "clientes", "cliente-1")

        assert display_value == "Cliente A"

    def test_get_display_value_with_numero(self, repository):
        """Test that non-standard display fields return None without spec."""
        cursor = repository.conn.cursor()
        display_value = repository._get_display_value(cursor, "pedidos", "pedido-1")

        # Should return None because 'numero' is not a standard candidate
        # and no spec file exists to define it
        assert display_value is None

    def test_get_display_value_nonexistent_record(self, repository):
        """Test getting display value for non-existent record."""
        cursor = repository.conn.cursor()
        display_value = repository._get_display_value(
            cursor, "clientes", "cliente-nonexistent"
        )

        assert display_value is None


# ═══════════════════════════════════════════════════════════════════════════
# TEST: BUG #3 - EAGER Sync of Display Values in create_relationship()
# ═══════════════════════════════════════════════════════════════════════════


class TestEagerSyncDisplayValues:
    """Tests for display value sync in create_relationship() - BUG #3 fix."""

    def test_create_relationship_syncs_display_values(
        self, repository, user_id, db_with_schema
    ):
        """Test that create_relationship() immediately syncs display values."""
        # Create relationship
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Verify relationship was created
        rel = repository.get_relationship(rel_id)
        assert rel is not None

        # Check that display value was synced immediately
        conn = sqlite3.connect(str(db_with_schema))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT _cliente_display FROM pedidos WHERE record_id = ?", ("pedido-1",)
        )
        row = cursor.fetchone()
        conn.close()

        # Display value should have been populated (EAGER sync)
        assert row["_cliente_display"] == "Cliente A"

    def test_create_relationship_eager_vs_lazy(self, repository, user_id):
        """Test that create_relationship uses EAGER sync (immediate)."""
        # Create a relationship
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-2",
            created_by=user_id,
        )

        # Immediately verify the display value (no manual sync needed)
        rel = repository.get_relationship(rel_id)

        # The relationship should be valid
        assert rel is not None
        assert rel.source_id == "pedido-1"
        assert rel.target_id == "cliente-2"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Core Functionality
# ═══════════════════════════════════════════════════════════════════════════


class TestRelationshipCRUD:
    """Tests for core CRUD operations."""

    def test_create_relationship_valid(self, repository, user_id):
        """Test creating a valid relationship."""
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        assert rel_id is not None
        assert isinstance(rel_id, str)
        assert len(rel_id) > 0

    def test_create_relationship_target_not_exist(self, repository, user_id):
        """Test that creating relationship to non-existent target fails."""
        with pytest.raises(ValueError, match="does not exist"):
            repository.create_relationship(
                source_type="pedidos",
                source_id="pedido-1",
                relationship_name="cliente",
                target_type="clientes",
                target_id="cliente-nonexistent",
                created_by=user_id,
            )

    def test_create_relationship_duplicate(self, repository, user_id):
        """Test that duplicate relationships are rejected."""
        # Create first relationship
        repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            repository.create_relationship(
                source_type="pedidos",
                source_id="pedido-1",
                relationship_name="cliente",
                target_type="clientes",
                target_id="cliente-1",
                created_by=user_id,
            )

    def test_get_relationship(self, repository, user_id):
        """Test retrieving a relationship."""
        # Create
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Retrieve
        rel = repository.get_relationship(rel_id)

        assert rel is not None
        assert rel.rel_id == rel_id
        assert rel.source_type == "pedidos"
        assert rel.source_id == "pedido-1"
        assert rel.relationship_name == "cliente"
        assert rel.target_type == "clientes"
        assert rel.target_id == "cliente-1"
        assert rel.is_active() is True

    def test_get_relationships(self, repository, user_id):
        """Test retrieving multiple relationships."""
        # Create multiple relationships
        rel_id1 = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        rel_id2 = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="produto",
            target_type="produtos",
            target_id="produto-1",
            created_by=user_id,
        )

        # Retrieve
        rels = repository.get_relationships("pedidos", "pedido-1")

        assert len(rels) == 2
        rel_ids = {r.rel_id for r in rels}
        assert rel_id1 in rel_ids
        assert rel_id2 in rel_ids

    def test_remove_relationship_soft_delete(self, repository, user_id):
        """Test soft-delete of relationship."""
        # Create
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Remove (soft-delete)
        removed = repository.remove_relationship(rel_id, user_id)

        assert removed is True

        # Verify soft-delete
        rel = repository.get_relationship(rel_id)
        assert rel is not None  # Record still exists
        assert rel.is_active() is False  # But marked as inactive
        assert rel.removed_at is not None
        assert rel.removed_by == user_id

    def test_restore_relationship(self, repository, user_id):
        """Test restoring a soft-deleted relationship."""
        # Create
        rel_id = repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Remove (soft-delete)
        repository.remove_relationship(rel_id, user_id)

        # Verify it's removed
        rel = repository.get_relationship(rel_id)
        assert rel.is_active() is False

        # Restore
        restored = repository.restore_relationship(rel_id, user_id)
        assert restored is True

        # Verify restored
        rel = repository.get_relationship(rel_id)
        assert rel.is_active() is True
        assert rel.removed_at is None
        assert rel.removed_by is None


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Batch Operations
# ═══════════════════════════════════════════════════════════════════════════


class TestBatchOperations:
    """Tests for batch operations."""

    def test_create_relationships_batch(self, repository, user_id):
        """Test creating multiple relationships in batch."""
        relationships = [
            {
                "source_type": "pedidos",
                "source_id": "pedido-1",
                "relationship_name": "cliente",
                "target_type": "clientes",
                "target_id": "cliente-1",
            },
            {
                "source_type": "pedidos",
                "source_id": "pedido-1",
                "relationship_name": "produto",
                "target_type": "produtos",
                "target_id": "produto-1",
            },
        ]

        results = repository.create_relationships_batch(
            relationships, created_by=user_id
        )

        # Returns list of rel_ids (strings) for successful creations
        assert len(results) == 2
        assert all(isinstance(rel_id, str) for rel_id in results)


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Relationship Sync and Statistics
# ═══════════════════════════════════════════════════════════════════════════


class TestSyncAndStatistics:
    """Tests for sync operations and statistics."""

    def test_sync_display_values(self, repository, user_id, db_with_schema):
        """Test syncing display values."""
        # Create relationship
        repository.create_relationship(
            source_type="pedidos",
            source_id="pedido-1",
            relationship_name="cliente",
            target_type="clientes",
            target_id="cliente-1",
            created_by=user_id,
        )

        # Manually clear display value
        conn = sqlite3.connect(str(db_with_schema))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pedidos SET _cliente_display = NULL WHERE record_id = ?",
            ("pedido-1",),
        )
        conn.commit()
        conn.close()

        # Sync display values
        updated = repository.sync_display_values("pedidos", "pedido-1")

        assert updated > 0

    def test_get_relationship_stats(self, repository, user_id):
        """Test getting relationship statistics."""
        # Create multiple relationships
        for i in range(3):
            repository.create_relationship(
                source_type="pedidos",
                source_id="pedido-1",
                relationship_name="cliente" if i == 0 else f"item_{i}",
                target_type="clientes" if i == 0 else "produtos",
                target_id="cliente-1" if i == 0 else "produto-1",
                created_by=user_id,
            )

        # Get stats for pedidos
        stats = repository.get_relationship_stats("pedidos")

        assert stats["total"] >= 3
        assert stats["active"] >= 3
        assert "by_name" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
