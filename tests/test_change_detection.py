"""
Tests for schema and backend change detection.
"""
import pytest
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistence.schema_detector import SchemaChangeDetector, SchemaChange, BackendChange, ChangeType


@pytest.fixture
def sample_spec_v1():
    """Original form specification."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": False}
        ]
    }


@pytest.fixture
def sample_spec_v2_add_field():
    """Specification with added field."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": False},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": False}
        ]
    }


@pytest.fixture
def sample_spec_v2_remove_field():
    """Specification with removed field."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True}
        ]
    }


@pytest.fixture
def sample_spec_v2_change_type():
    """Specification with changed field type."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "text", "required": False}  # Changed from email to text
        ]
    }


def test_compute_spec_hash(sample_spec_v1):
    """Test computing MD5 hash of spec."""
    hash1 = SchemaChangeDetector.compute_spec_hash(sample_spec_v1)
    hash2 = SchemaChangeDetector.compute_spec_hash(sample_spec_v1)

    assert hash1 == hash2
    assert len(hash1) == 32  # MD5 hash is 32 characters


def test_different_specs_different_hashes(sample_spec_v1, sample_spec_v2_add_field):
    """Test that different specs have different hashes."""
    hash1 = SchemaChangeDetector.compute_spec_hash(sample_spec_v1)
    hash2 = SchemaChangeDetector.compute_spec_hash(sample_spec_v2_add_field)

    assert hash1 != hash2


def test_detect_added_field(sample_spec_v1, sample_spec_v2_add_field):
    """Test detecting added field."""
    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=sample_spec_v1,
        new_spec=sample_spec_v2_add_field,
        has_data=False
    )

    assert change.has_changes()
    assert len(change.changes) == 1
    assert change.changes[0].change_type == ChangeType.ADD_FIELD
    assert change.changes[0].field_name == "telefone"
    assert not change.changes[0].requires_confirmation


def test_detect_removed_field_no_data(sample_spec_v1, sample_spec_v2_remove_field):
    """Test detecting removed field when there's no data."""
    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=sample_spec_v1,
        new_spec=sample_spec_v2_remove_field,
        has_data=False
    )

    assert change.has_changes()
    assert len(change.changes) == 1
    assert change.changes[0].change_type == ChangeType.REMOVE_FIELD
    assert change.changes[0].field_name == "email"
    assert not change.changes[0].requires_confirmation  # No data = no confirmation


def test_detect_removed_field_with_data(sample_spec_v1, sample_spec_v2_remove_field):
    """Test detecting removed field when there's data (requires confirmation)."""
    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=sample_spec_v1,
        new_spec=sample_spec_v2_remove_field,
        has_data=True
    )

    assert change.has_changes()
    assert len(change.changes) == 1
    assert change.changes[0].change_type == ChangeType.REMOVE_FIELD
    assert change.changes[0].requires_confirmation  # Has data = requires confirmation
    assert change.changes[0].data_loss_risk


def test_detect_type_change(sample_spec_v1, sample_spec_v2_change_type):
    """Test detecting field type change."""
    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=sample_spec_v1,
        new_spec=sample_spec_v2_change_type,
        has_data=True
    )

    assert change.has_changes()
    assert len(change.changes) == 1
    assert change.changes[0].change_type == ChangeType.CHANGE_TYPE
    assert change.changes[0].field_name == "email"
    assert change.changes[0].old_value == "email"
    assert change.changes[0].new_value == "text"


def test_detect_required_change():
    """Test detecting required flag change."""
    old_spec = {
        "fields": [{"name": "nome", "type": "text", "required": False}]
    }
    new_spec = {
        "fields": [{"name": "nome", "type": "text", "required": True}]
    }

    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=old_spec,
        new_spec=new_spec,
        has_data=True
    )

    assert change.has_changes()
    assert any(c.change_type == ChangeType.CHANGE_REQUIRED for c in change.changes)


def test_detect_backend_change():
    """Test detecting backend change."""
    change = SchemaChangeDetector.detect_backend_change(
        form_path="contatos",
        old_backend="txt",
        new_backend="sqlite",
        record_count=23
    )

    assert change is not None
    assert change.form_path == "contatos"
    assert change.old_backend == "txt"
    assert change.new_backend == "sqlite"
    assert change.has_data
    assert change.record_count == 23
    assert change.requires_confirmation


def test_detect_backend_change_no_data():
    """Test detecting backend change with no data."""
    change = SchemaChangeDetector.detect_backend_change(
        form_path="contatos",
        old_backend="txt",
        new_backend="sqlite",
        record_count=0
    )

    assert change is not None
    assert not change.has_data
    assert not change.requires_confirmation


def test_no_backend_change():
    """Test when backend hasn't changed."""
    change = SchemaChangeDetector.detect_backend_change(
        form_path="contatos",
        old_backend="txt",
        new_backend="txt",
        record_count=10
    )

    assert change is None


def test_schema_change_summary(sample_spec_v1, sample_spec_v2_add_field):
    """Test getting summary of schema changes."""
    change = SchemaChangeDetector.detect_changes(
        form_path="test_form",
        old_spec=sample_spec_v1,
        new_spec=sample_spec_v2_add_field,
        has_data=False
    )

    summary = change.get_summary()
    assert "add_field" in summary
    assert summary["add_field"] == 1


def test_requires_confirmation_logic():
    """Test requires_confirmation logic for schema changes."""
    # No data = no confirmation
    change1 = SchemaChange(form_path="test", has_data=False)
    assert not SchemaChangeDetector.requires_confirmation(change1)

    # Has data but no changes = no confirmation
    change2 = SchemaChange(form_path="test", has_data=True)
    assert not SchemaChangeDetector.requires_confirmation(change2)

    # Has data and requires_confirmation = confirmation needed
    change3 = SchemaChange(form_path="test", has_data=True, requires_confirmation=True)
    assert SchemaChangeDetector.requires_confirmation(change3)


def test_type_compatibility_check():
    """Test type compatibility checking."""
    # Text types are compatible
    assert SchemaChangeDetector._is_type_compatible("text", "email")
    assert SchemaChangeDetector._is_type_compatible("text", "tel")

    # Number types are compatible
    assert SchemaChangeDetector._is_type_compatible("number", "range")

    # Date types are compatible
    assert SchemaChangeDetector._is_type_compatible("date", "datetime-local")

    # Text to anything is safe
    assert SchemaChangeDetector._is_type_compatible("text", "number")

    # Number to text is NOT safe (data loss)
    assert not SchemaChangeDetector._is_type_compatible("number", "text")
