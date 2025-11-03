"""
Tests for ProcessFactory - Creating workflow processes from form data

Test Coverage:
- Process creation from form submissions
- Field mapping between forms and processes
- Process ID generation
- Process validation
- Process cloning
- Bulk process creation
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from workflow.process_factory import ProcessFactory
from workflow.kanban_registry import KanbanRegistry


@pytest.fixture
def temp_kanbans_dir():
    """Create temp directory for kanbans"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_kanban():
    """Sample kanban for testing"""
    return {
        "id": "test_kanban",
        "name": "Test Kanban",
        "states": [
            {"id": "initial", "name": "Initial", "is_initial": True},
            {"id": "next", "name": "Next"},
        ],
        "transitions": [{"from": "initial", "to": "next"}],
        "linked_forms": ["test_form"],
        "field_mapping": {
            "form_field1": "process_field1",
            "form_field2": "process_field2",
        },
    }


@pytest.fixture
def registry_with_kanban(temp_kanbans_dir, sample_kanban):
    """Create registry with sample kanban"""
    kanban_file = os.path.join(temp_kanbans_dir, "test_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(sample_kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)
    yield registry
    KanbanRegistry._instance = None


@pytest.fixture
def factory(registry_with_kanban):
    """Create ProcessFactory instance"""
    return ProcessFactory(registry_with_kanban)


# ========== Process Creation Tests ==========


def test_create_process_from_form(factory):
    """Test creating a process from form submission"""
    form_data = {"form_field1": "value1", "form_field2": "value2"}

    process = factory.create_from_form("test_form", form_data, record_idx=0)

    assert process is not None
    assert process["kanban_id"] == "test_kanban"
    assert process["source_form"] == "test_form"
    assert process["source_record_idx"] == 0
    assert process["current_state"] == "initial"
    assert "process_id" in process
    assert "created_at" in process
    assert "updated_at" in process
    assert process["history"] == []


def test_create_process_with_field_mapping(factory):
    """Test field mapping is applied correctly"""
    form_data = {
        "form_field1": "value1",
        "form_field2": "value2",
        "extra_field": "extra",
    }

    process = factory.create_from_form("test_form", form_data, record_idx=0)

    # Check mapped fields
    assert process["field_values"]["process_field1"] == "value1"
    assert process["field_values"]["process_field2"] == "value2"

    # Extra field not in mapping should not be included
    assert "extra_field" not in process["field_values"]


def test_create_process_without_field_mapping(temp_kanbans_dir):
    """Test creating process when kanban has no field mapping"""
    # Kanban without field_mapping
    kanban = {
        "id": "no_mapping_kanban",
        "name": "No Mapping",
        "states": [{"id": "s1", "name": "S1", "is_initial": True}],
        "transitions": [],
        "linked_forms": ["test_form"],
        # No field_mapping defined
    }

    kanban_file = os.path.join(temp_kanbans_dir, "no_mapping_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)
    factory = ProcessFactory(registry)

    form_data = {"field1": "value1", "field2": "value2"}

    process = factory.create_from_form("test_form", form_data, record_idx=0)

    # All fields should be copied directly
    assert process["field_values"]["field1"] == "value1"
    assert process["field_values"]["field2"] == "value2"

    KanbanRegistry._instance = None


def test_create_process_unlinked_form(factory):
    """Test creating process from unlinked form returns None"""
    form_data = {"field": "value"}

    process = factory.create_from_form("unlinked_form", form_data, record_idx=0)

    assert process is None


# ========== Process ID Generation Tests ==========


def test_generate_process_id_format(factory):
    """Test generated process ID has correct format"""
    process_id = factory.generate_process_id("test_kanban")

    # Should be: kanban_id_timestamp_uuid
    parts = process_id.split("_")
    assert parts[0] == "test"
    assert parts[1] == "kanban"
    # Rest should be timestamp and uuid


def test_generate_process_id_uniqueness(factory):
    """Test that generated IDs are unique"""
    id1 = factory.generate_process_id("test_kanban")
    id2 = factory.generate_process_id("test_kanban")

    assert id1 != id2


# ========== Field Mapping Tests ==========


def test_apply_field_mapping_with_mapping(factory, registry_with_kanban):
    """Test applying field mapping when mapping is defined"""
    kanban = registry_with_kanban.get_kanban("test_kanban")

    form_data = {
        "form_field1": "value1",
        "form_field2": "value2",
        "unmapped": "ignored",
    }

    mapped = factory.apply_field_mapping(kanban, form_data)

    assert mapped["process_field1"] == "value1"
    assert mapped["process_field2"] == "value2"
    assert "unmapped" not in mapped


def test_apply_field_mapping_without_mapping(factory, temp_kanbans_dir):
    """Test field mapping when no mapping defined (copies all)"""
    kanban = {
        "id": "no_map",
        "name": "No Map",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [],
    }

    form_data = {"field1": "value1", "field2": "value2"}

    mapped = factory.apply_field_mapping(kanban, form_data)

    assert mapped == form_data


# ========== Process Update Tests ==========


def test_update_process_from_form(factory, registry_with_kanban):
    """Test updating existing process with new form data"""
    # Create initial process
    form_data = {"form_field1": "old_value", "form_field2": "old_value2"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    # Update with new data
    new_form_data = {"form_field1": "new_value", "form_field2": "new_value2"}
    kanban = registry_with_kanban.get_kanban("test_kanban")

    updated = factory.update_process_from_form(process, new_form_data, kanban)

    assert updated["field_values"]["process_field1"] == "new_value"
    assert updated["field_values"]["process_field2"] == "new_value2"
    assert updated["updated_at"] != process["created_at"]


# ========== Process Validation Tests ==========


def test_validate_process_data_valid(factory):
    """Test validation passes for valid process"""
    form_data = {"form_field1": "value1", "form_field2": "value2"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    # Should not raise exception
    is_valid = factory.validate_process_data(process)
    assert is_valid is True


def test_validate_process_missing_required_field(factory):
    """Test validation fails when required field is missing"""
    process = {
        # Missing process_id, kanban_id, etc.
        "current_state": "initial"
    }

    with pytest.raises(ValueError, match="Missing required field"):
        factory.validate_process_data(process)


def test_validate_process_invalid_kanban(factory):
    """Test validation fails for non-existent kanban"""
    process = {
        "process_id": "test_id",
        "kanban_id": "nonexistent",
        "current_state": "initial",
        "field_values": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "history": [],
    }

    with pytest.raises(ValueError, match="not found in registry"):
        factory.validate_process_data(process)


def test_validate_process_invalid_state(factory):
    """Test validation fails when state doesn't exist in kanban"""
    process = {
        "process_id": "test_id",
        "kanban_id": "test_kanban",
        "current_state": "nonexistent_state",
        "field_values": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "history": [],
    }

    with pytest.raises(ValueError, match="not found in kanban"):
        factory.validate_process_data(process)


# ========== Process Cloning Tests ==========


def test_clone_process(factory):
    """Test cloning a process creates new process with new ID"""
    original_data = {"form_field1": "value1", "form_field2": "value2"}
    original = factory.create_from_form("test_form", original_data, record_idx=0)

    cloned = factory.clone_process(original)

    # Should have different process_id
    assert cloned["process_id"] != original["process_id"]

    # Should have same kanban and field values
    assert cloned["kanban_id"] == original["kanban_id"]
    assert cloned["field_values"] == original["field_values"]

    # Should have new timestamps
    assert cloned["created_at"] != original["created_at"]

    # Should have empty history
    assert cloned["history"] == []

    # Should be reset to initial state
    assert cloned["current_state"] == "initial"


def test_clone_process_with_new_source(factory):
    """Test cloning with new source form and index"""
    original_data = {"form_field1": "value1"}
    original = factory.create_from_form("test_form", original_data, record_idx=0)

    cloned = factory.clone_process(
        original, new_source_form="new_form", new_source_idx=5
    )

    assert cloned["source_form"] == "new_form"
    assert cloned["source_record_idx"] == 5


# ========== Process Summary Tests ==========


def test_create_process_summary(factory):
    """Test creating process summary for UI display"""
    form_data = {"form_field1": "value1", "form_field2": "value2"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    summary = factory.create_process_summary(process)

    assert "process_id" in summary
    assert summary["kanban_name"] == "Test Kanban"
    assert summary["current_state_name"] == "Initial"
    assert "current_state_color" in summary
    assert "created_at" in summary
    assert "updated_at" in summary
    assert summary["transition_count"] == 0
    assert summary["source_form"] == "test_form"


def test_process_summary_with_key_values(factory):
    """Test summary includes key field values"""
    form_data = {"form_field1": "important_value", "form_field2": "another_value"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    summary = factory.create_process_summary(process)

    # Should include up to 3 key values
    assert "key_values" in summary
    assert len(summary["key_values"]) <= 3


# ========== Bulk Operations Tests ==========


def test_bulk_create_processes(factory):
    """Test creating multiple processes from multiple records"""
    form_records = [
        {"form_field1": "value1a", "form_field2": "value2a"},
        {"form_field1": "value1b", "form_field2": "value2b"},
        {"form_field1": "value1c", "form_field2": "value2c"},
    ]

    processes = factory.bulk_create_processes("test_form", form_records, start_idx=0)

    assert len(processes) == 3
    assert processes[0]["source_record_idx"] == 0
    assert processes[1]["source_record_idx"] == 1
    assert processes[2]["source_record_idx"] == 2


def test_bulk_create_with_start_idx(factory):
    """Test bulk creation with custom start index"""
    form_records = [{"form_field1": "value1"}, {"form_field1": "value2"}]

    processes = factory.bulk_create_processes("test_form", form_records, start_idx=10)

    assert processes[0]["source_record_idx"] == 10
    assert processes[1]["source_record_idx"] == 11


# ========== Process Metrics Tests ==========


def test_get_process_metrics_new_process(factory):
    """Test getting metrics for a newly created process"""
    form_data = {"form_field1": "value1"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    metrics = factory.get_process_metrics(process)

    assert metrics["age_hours"] >= 0
    assert metrics["transitions_count"] == 0
    assert metrics["last_transition_hours"] is None
    assert metrics["current_state_duration_hours"] >= 0


def test_get_process_metrics_with_history(factory):
    """Test metrics for process with transition history"""
    form_data = {"form_field1": "value1"}
    process = factory.create_from_form("test_form", form_data, record_idx=0)

    # Add mock history entry
    process["history"] = [
        {
            "from_state": "initial",
            "to_state": "next",
            "timestamp": datetime.now().isoformat(),
            "type": "manual",
        }
    ]

    metrics = factory.get_process_metrics(process)

    assert metrics["transitions_count"] == 1
    assert metrics["last_transition_hours"] is not None
    assert metrics["current_state_duration_hours"] is not None
