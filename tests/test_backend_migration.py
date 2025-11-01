"""
Tests for backend migration (TXT → SQLite, etc).
"""

import pytest
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from persistence.migration_manager import MigrationManager
from persistence.adapters.txt_adapter import TxtRepository
from persistence.adapters.sqlite_adapter import SQLiteRepository


@pytest.fixture
def txt_config(tmp_path):
    """TXT backend configuration."""
    return {
        "type": "txt",
        "path": str(tmp_path),
        "delimiter": ";",
        "encoding": "utf-8",
        "extension": ".txt",
    }


@pytest.fixture
def sqlite_config(tmp_path):
    """SQLite backend configuration."""
    db_path = tmp_path / "test.db"
    return {
        "type": "sqlite",
        "database": str(db_path),
        "timeout": 10,
        "check_same_thread": False,
    }


@pytest.fixture
def sample_spec():
    """Sample form specification."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": False},
            {"name": "ativo", "label": "Ativo", "type": "checkbox", "required": False},
        ],
    }


def test_migrate_txt_to_sqlite_empty(tmp_path, txt_config, sqlite_config, sample_spec):
    """Test migrating empty TXT storage to SQLite."""
    # Create empty TXT storage
    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("test_form", sample_spec)

    # Migrate to SQLite
    success = MigrationManager.migrate_backend(
        form_path="test_form",
        spec=sample_spec,
        old_backend="txt",
        new_backend="sqlite",
        record_count=0,
    )

    assert success


@pytest.mark.skip(
    reason="MigrationManager uses global config, needs architecture refactor for isolated testing"
)
def test_migrate_txt_to_sqlite_with_data(
    tmp_path, txt_config, sqlite_config, sample_spec
):
    """Test migrating TXT storage with data to SQLite."""
    # Create TXT storage with data
    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("test_form", sample_spec)

    # Add sample data
    txt_repo.create(
        "test_form",
        sample_spec,
        {"nome": "João Silva", "telefone": "11-9999-8888", "ativo": True},
    )
    txt_repo.create(
        "test_form",
        sample_spec,
        {"nome": "Maria Santos", "telefone": "21-8888-7777", "ativo": False},
    )
    txt_repo.create(
        "test_form",
        sample_spec,
        {"nome": "Pedro Costa", "telefone": "31-7777-6666", "ativo": True},
    )

    # Verify data in TXT
    txt_data = txt_repo.read_all("test_form", sample_spec)
    assert len(txt_data) == 3

    # Migrate to SQLite
    success = MigrationManager.migrate_backend(
        form_path="test_form",
        spec=sample_spec,
        old_backend="txt",
        new_backend="sqlite",
        record_count=3,
    )

    assert success

    # Verify data in SQLite
    sqlite_repo = SQLiteRepository(sqlite_config)
    sqlite_data = sqlite_repo.read_all("test_form", sample_spec)

    assert len(sqlite_data) == 3
    assert sqlite_data[0]["nome"] == "João Silva"
    assert sqlite_data[1]["nome"] == "Maria Santos"
    assert sqlite_data[2]["nome"] == "Pedro Costa"


@pytest.mark.skip(
    reason="MigrationManager uses global config, needs architecture refactor for isolated testing"
)
def test_migration_creates_backup(tmp_path, txt_config, sqlite_config, sample_spec):
    """Test that migration creates a backup before migrating."""
    # Create TXT storage with data
    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("test_form", sample_spec)
    txt_repo.create(
        "test_form",
        sample_spec,
        {"nome": "João Silva", "telefone": "11-9999-8888", "ativo": True},
    )

    # Migrate
    MigrationManager.migrate_backend(
        form_path="test_form",
        spec=sample_spec,
        old_backend="txt",
        new_backend="sqlite",
        record_count=1,
    )

    # Check if backup was created
    backup_dir = Path("src/backups/migrations")
    assert backup_dir.exists()

    # Find backup file
    backup_files = list(backup_dir.glob("test_form_txt_to_migration_*.txt"))
    assert len(backup_files) > 0


@pytest.mark.skip(
    reason="MigrationManager uses global config, needs architecture refactor for isolated testing"
)
def test_migration_preserves_data_integrity(
    tmp_path, txt_config, sqlite_config, sample_spec
):
    """Test that migration preserves all data fields correctly."""
    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("test_form", sample_spec)

    # Create data with various field types
    original_data = [
        {"nome": "João Silva", "telefone": "11-9999-8888", "ativo": True},
        {"nome": "Maria", "telefone": "", "ativo": False},
        {"nome": "Pedro Costa", "telefone": "31-7777-6666", "ativo": True},
    ]

    for data in original_data:
        txt_repo.create("test_form", sample_spec, data)

    # Migrate
    success = MigrationManager.migrate_backend(
        form_path="test_form",
        spec=sample_spec,
        old_backend="txt",
        new_backend="sqlite",
        record_count=len(original_data),
    )

    assert success

    # Verify all data
    sqlite_repo = SQLiteRepository(sqlite_config)
    migrated_data = sqlite_repo.read_all("test_form", sample_spec)

    assert len(migrated_data) == len(original_data)

    for i, original in enumerate(original_data):
        assert migrated_data[i]["nome"] == original["nome"]
        assert migrated_data[i]["telefone"] == original["telefone"]
        assert migrated_data[i]["ativo"] == original["ativo"]


@pytest.mark.skip(
    reason="MigrationManager uses global config, needs architecture refactor for isolated testing"
)
def test_migration_with_nested_form_path(tmp_path, txt_config, sqlite_config):
    """Test migration with nested form paths (e.g., 'financeiro/contas')."""
    spec = {
        "title": "Contas",
        "fields": [
            {
                "name": "descricao",
                "label": "Descrição",
                "type": "text",
                "required": True,
            },
            {"name": "valor", "label": "Valor", "type": "number", "required": True},
        ],
    }

    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("financeiro_contas", spec)
    txt_repo.create(
        "financeiro_contas", spec, {"descricao": "Conta de Luz", "valor": 150}
    )

    success = MigrationManager.migrate_backend(
        form_path="financeiro_contas",
        spec=spec,
        old_backend="txt",
        new_backend="sqlite",
        record_count=1,
    )

    assert success

    sqlite_repo = SQLiteRepository(sqlite_config)
    data = sqlite_repo.read_all("financeiro_contas", spec)
    assert len(data) == 1
    assert data[0]["descricao"] == "Conta de Luz"


def test_migration_rollback_on_failure(tmp_path, txt_config, sample_spec):
    """Test that migration rolls back on failure."""
    txt_repo = TxtRepository(txt_config)
    txt_repo.create_storage("test_form", sample_spec)
    txt_repo.create(
        "test_form",
        sample_spec,
        {"nome": "João", "telefone": "11-9999-8888", "ativo": True},
    )

    # Try to migrate to an invalid backend (should fail)
    success = MigrationManager.migrate_backend(
        form_path="test_form",
        spec=sample_spec,
        old_backend="txt",
        new_backend="invalid_backend",
        record_count=1,
    )

    assert not success

    # Original TXT data should still be intact
    txt_data = txt_repo.read_all("test_form", sample_spec)
    assert len(txt_data) == 1
    assert txt_data[0]["nome"] == "João"
