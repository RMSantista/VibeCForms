"""
Tests for SQLite adapter.
"""

import pytest
import os
import sys
import sqlite3
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from persistence.adapters.sqlite_adapter import SQLiteRepository


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    config = {
        "type": "sqlite",
        "database": str(db_path),
        "timeout": 10,
        "check_same_thread": False,
    }
    return config, db_path


@pytest.fixture
def sample_spec():
    """Sample form specification."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": False},
            {"name": "ativo", "label": "Ativo", "type": "checkbox", "required": False},
        ],
    }


def test_sqlite_repository_initialization(temp_db):
    """Test SQLite repository initialization."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    assert repo.database == str(db_path)
    assert repo.timeout == 10


def test_create_storage(temp_db, sample_spec):
    """Test creating storage (table) in SQLite."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    # Create storage
    assert repo.create_storage("test_form", sample_spec)

    # Verify table exists
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='test_form';"
    )
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "test_form"


def test_exists_storage(temp_db, sample_spec):
    """Test checking if storage exists."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    # Should not exist initially
    assert not repo.exists("test_form")

    # Create storage
    repo.create_storage("test_form", sample_spec)

    # Should exist now
    assert repo.exists("test_form")


def test_create_and_read_record(temp_db, sample_spec):
    """Test creating and reading a record."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    repo.create_storage("test_form", sample_spec)

    # Create record
    data = {"nome": "João Silva", "email": "joao@example.com", "ativo": True}
    record_id = repo.create("test_form", sample_spec, data)

    # Verify UUID returned
    assert isinstance(record_id, str)
    assert len(record_id) == 27  # Crockford Base32 UUID length

    # Read all records
    records = repo.read_all("test_form", sample_spec)
    assert len(records) == 1
    assert records[0]["id"] == record_id
    assert records[0]["nome"] == "João Silva"
    assert records[0]["email"] == "joao@example.com"
    assert records[0]["ativo"] is True


def test_update_record(temp_db, sample_spec):
    """Test updating a record by UUID."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    repo.create_storage("test_form", sample_spec)

    # Create record
    data = {"nome": "João Silva", "email": "joao@example.com", "ativo": True}
    record_id = repo.create("test_form", sample_spec, data)

    # Update record
    updated_data = {
        "nome": "João Santos",
        "email": "joao.santos@example.com",
        "ativo": False,
    }
    success = repo.update_by_id("test_form", sample_spec, record_id, updated_data)
    assert success is True

    # Verify update
    records = repo.read_all("test_form", sample_spec)
    assert len(records) == 1
    assert records[0]["id"] == record_id
    assert records[0]["nome"] == "João Santos"
    assert records[0]["email"] == "joao.santos@example.com"
    assert records[0]["ativo"] is False


def test_delete_record(temp_db, sample_spec):
    """Test deleting a record by UUID."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    repo.create_storage("test_form", sample_spec)

    # Create multiple records
    id1 = repo.create(
        "test_form",
        sample_spec,
        {"nome": "João", "email": "joao@example.com", "ativo": True},
    )
    id2 = repo.create(
        "test_form",
        sample_spec,
        {"nome": "Maria", "email": "maria@example.com", "ativo": True},
    )
    id3 = repo.create(
        "test_form",
        sample_spec,
        {"nome": "Pedro", "email": "pedro@example.com", "ativo": False},
    )

    # Delete Maria's record
    success = repo.delete_by_id("test_form", sample_spec, id2)
    assert success is True

    # Verify deletion
    records = repo.read_all("test_form", sample_spec)
    assert len(records) == 2
    assert records[0]["nome"] == "João"
    assert records[0]["id"] == id1
    assert records[1]["nome"] == "Pedro"
    assert records[1]["id"] == id3

    # Try to read deleted record
    deleted = repo.read_by_id("test_form", sample_spec, id2)
    assert deleted is None


def test_has_data(temp_db, sample_spec):
    """Test checking if storage has data."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    repo.create_storage("test_form", sample_spec)

    # Should not have data initially
    assert not repo.has_data("test_form")

    # Create record
    repo.create(
        "test_form",
        sample_spec,
        {"nome": "João", "email": "joao@example.com", "ativo": True},
    )

    # Should have data now
    assert repo.has_data("test_form")


def test_drop_storage(temp_db, sample_spec):
    """Test dropping storage (table)."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    repo.create_storage("test_form", sample_spec)
    assert repo.exists("test_form")

    # Drop storage
    assert repo.drop_storage("test_form")

    # Should not exist anymore
    assert not repo.exists("test_form")


def test_multiple_forms(temp_db):
    """Test multiple forms in same database."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    spec1 = {
        "title": "Contatos",
        "fields": [{"name": "nome", "label": "Nome", "type": "text", "required": True}],
    }

    spec2 = {
        "title": "Produtos",
        "fields": [{"name": "nome", "label": "Nome", "type": "text", "required": True}],
    }

    # Create two forms
    repo.create_storage("contatos", spec1)
    repo.create_storage("produtos", spec2)

    # Add data to each
    id1 = repo.create("contatos", spec1, {"nome": "João"})
    id2 = repo.create("produtos", spec2, {"nome": "Produto A"})

    # Verify UUIDs
    assert isinstance(id1, str) and len(id1) == 27
    assert isinstance(id2, str) and len(id2) == 27

    # Verify both exist independently
    contatos = repo.read_all("contatos", spec1)
    produtos = repo.read_all("produtos", spec2)

    assert len(contatos) == 1
    assert len(produtos) == 1
    assert contatos[0]["id"] == id1
    assert contatos[0]["nome"] == "João"
    assert produtos[0]["id"] == id2
    assert produtos[0]["nome"] == "Produto A"


def test_boolean_field_conversion(temp_db):
    """Test that boolean fields are properly converted."""
    config, db_path = temp_db
    repo = SQLiteRepository(config)

    spec = {
        "title": "Test",
        "fields": [
            {"name": "ativo", "label": "Ativo", "type": "checkbox", "required": False}
        ],
    }

    repo.create_storage("test", spec)

    # Test True
    id1 = repo.create("test", spec, {"ativo": True})
    records = repo.read_all("test", spec)
    assert records[0]["id"] == id1
    assert records[0]["ativo"] is True

    # Test False
    repo.delete_by_id("test", spec, id1)
    id2 = repo.create("test", spec, {"ativo": False})
    records = repo.read_all("test", spec)
    assert records[0]["id"] == id2
    assert records[0]["ativo"] is False
