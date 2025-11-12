"""
Tests for FormTriggerManager - Hook system for form saves

Test Coverage:
- Form creation triggers
- Form update triggers
- Form deletion triggers
- Bulk sync operations
- Hook callbacks
"""

import pytest
import os
import json
import tempfile
import shutil

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from workflow.kanban_registry import KanbanRegistry
from workflow.process_factory import ProcessFactory
from workflow.form_trigger_manager import FormTriggerManager
from persistence.workflow_repository import WorkflowRepository
from persistence.adapters.txt_adapter import TxtRepository


@pytest.fixture
def temp_dirs():
    """Create temp directories for kanbans and data"""
    kanbans_dir = tempfile.mkdtemp()
    data_dir = tempfile.mkdtemp()
    yield kanbans_dir, data_dir
    shutil.rmtree(kanbans_dir)
    shutil.rmtree(data_dir)


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
        "field_mapping": {"name": "name", "value": "value"},
    }


@pytest.fixture
def trigger_manager(temp_dirs, sample_kanban):
    """Create FormTriggerManager with dependencies"""
    kanbans_dir, data_dir = temp_dirs

    # Create kanban file
    kanban_file = os.path.join(kanbans_dir, "test_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(sample_kanban, f)

    # Setup components
    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=kanbans_dir)
    factory = ProcessFactory(registry)

    # Setup repository
    txt_config = {"path": data_dir}  # Use 'path' not 'base_path'
    txt_repo = TxtRepository(config=txt_config)
    workflow_repo = WorkflowRepository(txt_repo)
    workflow_repo.create_storage()

    # Create trigger manager
    manager = FormTriggerManager(registry, factory, workflow_repo)

    yield manager

    # Cleanup
    KanbanRegistry._instance = None


# ========== Form Creation Tests ==========


def test_on_form_created_linked_form(trigger_manager):
    """Test creating workflow process when form is linked"""
    form_data = {"name": "Test", "value": "123"}

    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    assert process_id is not None
    assert isinstance(process_id, str)


def test_on_form_created_unlinked_form(trigger_manager):
    """Test no process created for unlinked form"""
    form_data = {"name": "Test"}

    process_id = trigger_manager.on_form_created(
        "unlinked_form", form_data, record_idx=0
    )

    assert process_id is None


def test_on_form_created_persists_process(trigger_manager):
    """Test that created process is persisted"""
    form_data = {"name": "Test", "value": "123"}

    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Verify process exists in repository
    process = trigger_manager.repo.get_process_by_id(process_id)
    assert process is not None
    assert process["process_id"] == process_id


# ========== Form Update Tests ==========


def test_on_form_updated_existing_process(trigger_manager):
    """Test updating existing workflow process"""
    # Create initial process
    form_data = {"name": "Original", "value": "100"}
    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Update form
    updated_data = {"name": "Updated", "value": "200"}
    success = trigger_manager.on_form_updated("test_form", updated_data, record_idx=0)

    assert success is True

    # Verify process was updated
    process = trigger_manager.repo.get_process_by_id(process_id)
    assert process["field_values"]["name"] == "Updated"
    assert process["field_values"]["value"] == "200"


def test_on_form_updated_no_existing_process_creates_new(trigger_manager):
    """Test updating form without existing process creates new one"""
    form_data = {"name": "Test", "value": "123"}

    # Call update on non-existent process (should create new)
    result = trigger_manager.on_form_updated("test_form", form_data, record_idx=5)

    # Should create process (returns process_id as string when created)
    assert result is not None


def test_on_form_updated_unlinked_form(trigger_manager):
    """Test updating unlinked form returns False"""
    form_data = {"name": "Test"}

    success = trigger_manager.on_form_updated("unlinked_form", form_data, record_idx=0)

    assert success is False


# ========== Form Deletion Tests ==========


def test_on_form_deleted_preserves_process_by_default(trigger_manager):
    """Test deleting form preserves process by default"""
    # Create process
    form_data = {"name": "Test", "value": "123"}
    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Delete form (default: preserve process)
    success = trigger_manager.on_form_deleted(
        "test_form", record_idx=0, delete_process=False
    )

    assert success is True

    # Process should still exist but marked as orphaned
    process = trigger_manager.repo.get_process_by_id(process_id)
    assert process is not None
    assert "[DELETED]" in process["source_form"]
    assert process["source_record_idx"] == -1


def test_on_form_deleted_deletes_process_when_requested(trigger_manager):
    """Test deleting form can also delete process"""
    # Create process
    form_data = {"name": "Test", "value": "123"}
    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Delete form and process
    success = trigger_manager.on_form_deleted(
        "test_form", record_idx=0, delete_process=True
    )

    assert success is True

    # Process should be gone
    process = trigger_manager.repo.get_process_by_id(process_id)
    assert process is None


def test_on_form_deleted_nonexistent_process(trigger_manager):
    """Test deleting form with no associated process"""
    success = trigger_manager.on_form_deleted(
        "test_form", record_idx=999, delete_process=False
    )

    assert success is False


# ========== Bulk Sync Tests ==========


def test_sync_existing_forms_creates_processes(trigger_manager):
    """Test syncing existing form records creates processes"""
    form_records = [
        {"name": "Record1", "value": "100"},
        {"name": "Record2", "value": "200"},
        {"name": "Record3", "value": "300"},
    ]

    stats = trigger_manager.sync_existing_forms(
        "test_form", form_records, recreate=False
    )

    assert stats["created"] == 3
    assert stats["updated"] == 0
    assert stats["errors"] == 0


def test_sync_existing_forms_updates_existing(trigger_manager):
    """Test syncing updates existing processes"""
    # Create initial processes
    form_records = [
        {"name": "Original1", "value": "100"},
        {"name": "Original2", "value": "200"},
    ]
    trigger_manager.sync_existing_forms("test_form", form_records, recreate=False)

    # Sync with updated data
    updated_records = [
        {"name": "Updated1", "value": "150"},
        {"name": "Updated2", "value": "250"},
    ]
    stats = trigger_manager.sync_existing_forms(
        "test_form", updated_records, recreate=False
    )

    assert stats["updated"] == 2
    assert stats["created"] == 0


def test_sync_existing_forms_recreate(trigger_manager):
    """Test sync with recreate flag deletes and recreates all"""
    # Create initial processes
    initial_records = [{"name": "Initial", "value": "100"}]
    trigger_manager.sync_existing_forms("test_form", initial_records, recreate=False)

    # Sync with recreate=True
    new_records = [{"name": "New1", "value": "200"}, {"name": "New2", "value": "300"}]
    stats = trigger_manager.sync_existing_forms("test_form", new_records, recreate=True)

    # All should be created (old ones deleted)
    assert stats["created"] == 2


def test_sync_existing_forms_unlinked_form(trigger_manager):
    """Test syncing unlinked form skips all records"""
    form_records = [{"name": "Test1"}, {"name": "Test2"}]

    stats = trigger_manager.sync_existing_forms(
        "unlinked_form", form_records, recreate=False
    )

    assert stats["skipped"] == 2
    assert stats["created"] == 0


# ========== Hook System Tests ==========


def test_register_on_process_created_hook(trigger_manager):
    """Test registering and triggering on_process_created hook"""
    called = []

    def hook_callback(process):
        called.append(process["process_id"])

    trigger_manager.register_on_process_created_hook(hook_callback)

    # Create process
    form_data = {"name": "Test", "value": "123"}
    process_id = trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Hook should have been called
    assert len(called) == 1
    assert called[0] == process_id


def test_register_on_process_updated_hook(trigger_manager):
    """Test registering and triggering on_process_updated hook"""
    called = []

    def hook_callback(process):
        called.append(process["process_id"])

    trigger_manager.register_on_process_updated_hook(hook_callback)

    # Create and update process
    form_data = {"name": "Test", "value": "123"}
    trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    updated_data = {"name": "Updated", "value": "456"}
    trigger_manager.on_form_updated("test_form", updated_data, record_idx=0)

    # Hook should have been called on update
    assert len(called) == 1


def test_multiple_hooks(trigger_manager):
    """Test multiple hooks can be registered"""
    called1 = []
    called2 = []

    def hook1(process):
        called1.append(process["process_id"])

    def hook2(process):
        called2.append(process["process_id"])

    trigger_manager.register_on_process_created_hook(hook1)
    trigger_manager.register_on_process_created_hook(hook2)

    # Create process
    form_data = {"name": "Test", "value": "123"}
    trigger_manager.on_form_created("test_form", form_data, record_idx=0)

    # Both hooks should be called
    assert len(called1) == 1
    assert len(called2) == 1


# ========== Diagnostics Tests ==========


def test_get_sync_status_linked_form(trigger_manager):
    """Test getting sync status for linked form"""
    # Create some processes
    form_records = [
        {"name": "Test1", "value": "100"},
        {"name": "Test2", "value": "200"},
    ]
    trigger_manager.sync_existing_forms("test_form", form_records, recreate=False)

    status = trigger_manager.get_sync_status("test_form")

    assert status["is_linked"] is True
    assert status["kanban_id"] == "test_kanban"
    assert status["process_count"] == 2
    assert status["orphaned_count"] == 0


def test_get_sync_status_unlinked_form(trigger_manager):
    """Test sync status for unlinked form"""
    status = trigger_manager.get_sync_status("unlinked_form")

    assert status["is_linked"] is False
    assert status["kanban_id"] is None
    assert status["process_count"] == 0


def test_cleanup_orphaned_processes(trigger_manager):
    """Test cleaning up orphaned processes"""
    # Create and then orphan a process
    form_data = {"name": "Test", "value": "123"}
    trigger_manager.on_form_created("test_form", form_data, record_idx=0)
    trigger_manager.on_form_deleted("test_form", record_idx=0, delete_process=False)

    # Cleanup orphaned
    deleted_count = trigger_manager.cleanup_orphaned_processes("test_form")

    assert deleted_count == 1

    # Verify no orphaned processes remain
    status = trigger_manager.get_sync_status("test_form")
    assert status["orphaned_count"] == 0
