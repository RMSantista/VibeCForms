"""
Tests for KanbanRegistry - Kanban-Form mapping and validation

Test Coverage:
- Loading kanban definitions from JSON files
- Validating kanban structure
- Form-to-kanban mapping queries
- State and transition queries
- Registry management operations
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from workflow.kanban_registry import KanbanRegistry, get_registry


@pytest.fixture
def temp_kanbans_dir():
    """Create a temporary directory for kanban configs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_kanban():
    """Sample kanban definition for testing"""
    return {
        "id": "test_kanban",
        "name": "Test Kanban",
        "states": [
            {"id": "state1", "name": "State 1", "is_initial": True},
            {"id": "state2", "name": "State 2"},
        ],
        "transitions": [{"from": "state1", "to": "state2"}],
        "linked_forms": ["test_form"],
    }


@pytest.fixture
def registry_with_sample(temp_kanbans_dir, sample_kanban):
    """Create a registry with a sample kanban"""
    # Write sample kanban to file
    kanban_file = os.path.join(temp_kanbans_dir, "test_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(sample_kanban, f)

    # Force new instance by clearing singleton
    KanbanRegistry._instance = None

    # Create registry
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)
    yield registry

    # Cleanup singleton
    KanbanRegistry._instance = None


# ========== Loading Tests ==========


def test_load_valid_kanban(temp_kanbans_dir, sample_kanban):
    """Test loading a valid kanban from JSON file"""
    # Create kanban file
    kanban_file = os.path.join(temp_kanbans_dir, "test_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(sample_kanban, f)

    # Clear singleton
    KanbanRegistry._instance = None

    # Load registry
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    # Verify kanban was loaded
    kanban = registry.get_kanban("test_kanban")
    assert kanban is not None
    assert kanban["id"] == "test_kanban"
    assert kanban["name"] == "Test Kanban"

    # Cleanup
    KanbanRegistry._instance = None


def test_load_multiple_kanbans(temp_kanbans_dir):
    """Test loading multiple kanbans"""
    # Create two kanban files
    kanban1 = {
        "id": "kanban1",
        "name": "Kanban 1",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [],
    }
    kanban2 = {
        "id": "kanban2",
        "name": "Kanban 2",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [],
    }

    with open(os.path.join(temp_kanbans_dir, "kanban1.json"), "w") as f:
        json.dump(kanban1, f)

    with open(os.path.join(temp_kanbans_dir, "kanban2.json"), "w") as f:
        json.dump(kanban2, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    # Verify both loaded
    all_kanbans = registry.get_all_kanbans()
    assert len(all_kanbans) == 2
    assert "kanban1" in all_kanbans
    assert "kanban2" in all_kanbans

    KanbanRegistry._instance = None


def test_load_empty_directory(temp_kanbans_dir):
    """Test loading from empty directory"""
    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    all_kanbans = registry.get_all_kanbans()
    assert len(all_kanbans) == 0

    KanbanRegistry._instance = None


# ========== Validation Tests ==========


def test_validate_missing_required_fields(temp_kanbans_dir):
    """Test validation fails when required fields are missing"""
    invalid_kanban = {
        "id": "invalid",
        # Missing: name, states, transitions
    }

    kanban_file = os.path.join(temp_kanbans_dir, "invalid.json")
    with open(kanban_file, "w") as f:
        json.dump(invalid_kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    # Should not load invalid kanban
    kanban = registry.get_kanban("invalid")
    assert kanban is None

    KanbanRegistry._instance = None


def test_validate_invalid_state_structure(temp_kanbans_dir):
    """Test validation fails when state is missing id or name"""
    invalid_kanban = {
        "id": "invalid",
        "name": "Invalid",
        "states": [{"id": "s1"}],  # Missing name
        "transitions": [],
    }

    kanban_file = os.path.join(temp_kanbans_dir, "invalid.json")
    with open(kanban_file, "w") as f:
        json.dump(invalid_kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    # Should not load
    assert registry.get_kanban("invalid") is None

    KanbanRegistry._instance = None


def test_validate_invalid_transition_references(temp_kanbans_dir):
    """Test validation fails when transition references non-existent state"""
    invalid_kanban = {
        "id": "invalid",
        "name": "Invalid",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [{"from": "s1", "to": "nonexistent"}],  # nonexistent state
    }

    kanban_file = os.path.join(temp_kanbans_dir, "invalid.json")
    with open(kanban_file, "w") as f:
        json.dump(invalid_kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    assert registry.get_kanban("invalid") is None

    KanbanRegistry._instance = None


# ========== Query Tests ==========


def test_get_kanban_by_id(registry_with_sample):
    """Test retrieving kanban by ID"""
    kanban = registry_with_sample.get_kanban("test_kanban")
    assert kanban is not None
    assert kanban["id"] == "test_kanban"


def test_get_nonexistent_kanban(registry_with_sample):
    """Test retrieving non-existent kanban returns None"""
    kanban = registry_with_sample.get_kanban("nonexistent")
    assert kanban is None


def test_get_kanban_by_form(registry_with_sample):
    """Test retrieving kanban by linked form"""
    kanban = registry_with_sample.get_kanban_by_form("test_form")
    assert kanban is not None
    assert kanban["id"] == "test_kanban"


def test_is_form_linked(registry_with_sample):
    """Test checking if form is linked to kanban"""
    assert registry_with_sample.is_form_linked("test_form") is True
    assert registry_with_sample.is_form_linked("unlinked_form") is False


def test_get_kanban_id_for_form(registry_with_sample):
    """Test getting kanban ID for a form"""
    kanban_id = registry_with_sample.get_kanban_id_for_form("test_form")
    assert kanban_id == "test_kanban"

    nonexistent = registry_with_sample.get_kanban_id_for_form("nonexistent")
    assert nonexistent is None


def test_get_linked_forms(registry_with_sample):
    """Test getting all forms linked to a kanban"""
    forms = registry_with_sample.get_linked_forms("test_kanban")
    assert len(forms) == 1
    assert "test_form" in forms


# ========== State Query Tests ==========


def test_get_states(registry_with_sample):
    """Test getting all states for a kanban"""
    states = registry_with_sample.get_states("test_kanban")
    assert len(states) == 2
    assert states[0]["id"] == "state1"
    assert states[1]["id"] == "state2"


def test_get_initial_state(registry_with_sample):
    """Test getting initial state"""
    initial = registry_with_sample.get_initial_state("test_kanban")
    assert initial is not None
    assert initial["id"] == "state1"
    assert initial.get("is_initial") is True


def test_get_state_by_id(registry_with_sample):
    """Test getting specific state by ID"""
    state = registry_with_sample.get_state("test_kanban", "state2")
    assert state is not None
    assert state["id"] == "state2"
    assert state["name"] == "State 2"


# ========== Transition Query Tests ==========


def test_get_transitions(registry_with_sample):
    """Test getting all transitions"""
    transitions = registry_with_sample.get_transitions("test_kanban")
    assert len(transitions) == 1
    assert transitions[0]["from"] == "state1"
    assert transitions[0]["to"] == "state2"


def test_can_transition(registry_with_sample):
    """Test checking if transition is allowed - NEW PHILOSOPHY: All transitions allowed by default"""
    # Recommended transition (explicitly defined)
    assert (
        registry_with_sample.can_transition("test_kanban", "state1", "state2") is True
    )

    # Non-recommended transition (not defined, but STILL ALLOWED by default)
    # NEW PHILOSOPHY: Only explicitly blocked transitions are forbidden
    assert (
        registry_with_sample.can_transition("test_kanban", "state2", "state1") is True
    )


def test_blocked_transitions(tmp_path):
    """Test explicitly blocked transitions"""
    # Create kanban with blocked transitions
    kanban_def = {
        "id": "test_blocked",
        "name": "Test Blocked",
        "states": [
            {"id": "state1", "name": "State 1"},
            {"id": "state2", "name": "State 2"},
        ],
        "recommended_transitions": [{"from": "state1", "to": "state2"}],
        "blocked_transitions": [
            {"from": "state2", "to": "state1", "reason": "Cannot go back"}
        ],
    }

    kanban_file = tmp_path / "test_blocked.json"
    with open(kanban_file, "w", encoding="utf-8") as f:
        json.dump(kanban_def, f)

    # Clear singleton instance to ensure fresh load
    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=str(tmp_path))

    # Recommended transition should be allowed
    assert registry.can_transition("test_blocked", "state1", "state2") is True

    # Blocked transition should be forbidden
    assert registry.can_transition("test_blocked", "state2", "state1") is False

    # Check blocked transition details
    blocked = registry.get_blocked_transition("test_blocked", "state2", "state1")
    assert blocked is not None
    assert blocked["reason"] == "Cannot go back"


def test_warned_transitions(tmp_path):
    """Test transitions with warnings"""
    # Create kanban with warned transitions
    kanban_def = {
        "id": "test_warned",
        "name": "Test Warned",
        "states": [
            {"id": "state1", "name": "State 1"},
            {"id": "state2", "name": "State 2"},
        ],
        "recommended_transitions": [{"from": "state1", "to": "state2"}],
        "warned_transitions": [
            {
                "from": "state2",
                "to": "state1",
                "warning": "Unusual flow",
                "warning_message": "Are you sure?",
                "require_justification": True,
                "severity": "high",
            }
        ],
    }

    kanban_file = tmp_path / "test_warned.json"
    with open(kanban_file, "w", encoding="utf-8") as f:
        json.dump(kanban_def, f)

    # Clear singleton instance to ensure fresh load
    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=str(tmp_path))

    # Warned transition should still be ALLOWED (just warned)
    assert registry.can_transition("test_warned", "state2", "state1") is True

    # Check if it's marked as warned
    assert registry.is_transition_warned("test_warned", "state2", "state1") is True

    # Check warning details
    warned = registry.get_warned_transition("test_warned", "state2", "state1")
    assert warned is not None
    assert warned["warning_message"] == "Are you sure?"
    assert warned["require_justification"] is True
    assert warned["severity"] == "high"


def test_get_transition(registry_with_sample):
    """Test getting specific transition"""
    transition = registry_with_sample.get_transition("test_kanban", "state1", "state2")
    assert transition is not None
    assert transition["from"] == "state1"
    assert transition["to"] == "state2"

    # Non-existent transition
    no_transition = registry_with_sample.get_transition(
        "test_kanban", "state2", "state1"
    )
    assert no_transition is None


def test_get_available_transitions(registry_with_sample):
    """Test getting available transitions from a state"""
    available = registry_with_sample.get_available_transitions("test_kanban", "state1")
    assert len(available) == 1
    assert available[0]["to"] == "state2"

    # State with no outgoing transitions
    none_available = registry_with_sample.get_available_transitions(
        "test_kanban", "state2"
    )
    assert len(none_available) == 0


# ========== Registry Management Tests ==========


def test_register_kanban_programmatically(registry_with_sample, tmp_path):
    """Test programmatically registering a kanban"""
    new_kanban = {
        "id": "new_kanban",
        "name": "New Kanban",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [],
    }

    # Register without saving
    success = registry_with_sample.register_kanban(new_kanban, save_to_disk=False)
    assert success is True

    # Verify it's in registry
    kanban = registry_with_sample.get_kanban("new_kanban")
    assert kanban is not None


def test_unregister_kanban(registry_with_sample):
    """Test unregistering a kanban"""
    # Verify it exists
    assert registry_with_sample.get_kanban("test_kanban") is not None

    # Unregister
    success = registry_with_sample.unregister_kanban(
        "test_kanban", delete_from_disk=False
    )
    assert success is True

    # Verify it's gone
    assert registry_with_sample.get_kanban("test_kanban") is None


def test_reload_registry(temp_kanbans_dir, sample_kanban):
    """Test reloading registry from disk"""
    # Create initial kanban
    kanban_file = os.path.join(temp_kanbans_dir, "test_kanban.json")
    with open(kanban_file, "w") as f:
        json.dump(sample_kanban, f)

    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    # Verify loaded
    assert registry.get_kanban("test_kanban") is not None

    # Add new kanban to disk
    new_kanban = {
        "id": "new_kanban",
        "name": "New",
        "states": [{"id": "s1", "name": "S1"}],
        "transitions": [],
    }
    new_file = os.path.join(temp_kanbans_dir, "new_kanban.json")
    with open(new_file, "w") as f:
        json.dump(new_kanban, f)

    # Reload
    registry.reload()

    # Verify both are loaded
    assert registry.get_kanban("test_kanban") is not None
    assert registry.get_kanban("new_kanban") is not None

    KanbanRegistry._instance = None


# ========== Singleton Tests ==========


def test_singleton_pattern(temp_kanbans_dir):
    """Test that KanbanRegistry follows singleton pattern"""
    KanbanRegistry._instance = None

    registry1 = KanbanRegistry(kanbans_dir=temp_kanbans_dir)
    registry2 = KanbanRegistry(kanbans_dir=temp_kanbans_dir)

    assert registry1 is registry2

    KanbanRegistry._instance = None


def test_get_registry_helper(temp_kanbans_dir):
    """Test get_registry() helper function"""
    KanbanRegistry._instance = None

    registry = get_registry(kanbans_dir=temp_kanbans_dir)
    assert isinstance(registry, KanbanRegistry)

    KanbanRegistry._instance = None
