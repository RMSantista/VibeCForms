"""
Tests for AutoTransitionEngine - Automatic workflow state transitions

Test Coverage:
- Auto-transition checking (prerequisites satisfied/not satisfied)
- Timeout-based transitions (expired/not expired)
- should_auto_transition (priority: timeout > auto)
- Cascade progression (single, chain, max_depth)
- Forced transitions (allowed with warnings, execution)
- Batch processing (all processes, specific kanban)
- Diagnostics (pending auto-transitions)
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timezone, timedelta

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from workflow.kanban_registry import KanbanRegistry
from workflow.prerequisite_checker import PrerequisiteChecker
from workflow.auto_transition_engine import AutoTransitionEngine
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
def kanban_with_auto_transition():
    """Kanban configuration with auto_transition_to"""
    return {
        "id": "test_kanban",
        "name": "Test Kanban",
        "states": [
            {
                "id": "initial",
                "name": "Initial",
                "is_initial": True,
                "auto_transition_to": "next",
            },
            {"id": "next", "name": "Next", "auto_transition_to": "final"},
            {"id": "final", "name": "Final", "is_final": True},
        ],
        "transitions": [
            {
                "from": "initial",
                "to": "next",
                "type": "system",
                "prerequisites": [
                    {
                        "type": "field_check",
                        "field": "ready",
                        "condition": "equals",
                        "value": "yes",
                    }
                ],
            },
            {"from": "next", "to": "final", "type": "system", "prerequisites": []},
        ],
        "blocked_transitions": [
            {
                "from": "final",
                "to": "initial",
                "reason": "Transition not defined in kanban",
            }
        ],
        "linked_forms": ["test_form"],
        "field_mapping": {},
    }


@pytest.fixture
def kanban_with_timeout():
    """Kanban configuration with timeout"""
    return {
        "id": "timeout_kanban",
        "name": "Timeout Kanban",
        "states": [
            {
                "id": "waiting",
                "name": "Waiting",
                "is_initial": True,
                "timeout_hours": 1,
                "auto_transition_to": "expired",
            },
            {"id": "expired", "name": "Expired", "is_final": True},
        ],
        "transitions": [{"from": "waiting", "to": "expired", "type": "system"}],
        "linked_forms": ["timeout_form"],
        "field_mapping": {},
    }


@pytest.fixture
def engine(temp_dirs, kanban_with_auto_transition, kanban_with_timeout):
    """Create AutoTransitionEngine with dependencies"""
    kanbans_dir, data_dir = temp_dirs

    # Create kanban files
    kanban1_file = os.path.join(kanbans_dir, "test_kanban.json")
    with open(kanban1_file, "w") as f:
        json.dump(kanban_with_auto_transition, f)

    kanban2_file = os.path.join(kanbans_dir, "timeout_kanban.json")
    with open(kanban2_file, "w") as f:
        json.dump(kanban_with_timeout, f)

    # Setup components
    KanbanRegistry._instance = None
    registry = KanbanRegistry(kanbans_dir=kanbans_dir)
    checker = PrerequisiteChecker()
    engine = AutoTransitionEngine(registry, checker)

    # Setup repository
    txt_config = {"base_path": data_dir}
    txt_repo = TxtRepository(config=txt_config)
    workflow_repo = WorkflowRepository(txt_repo)
    workflow_repo.create_storage()

    yield engine, workflow_repo, registry

    # Cleanup
    KanbanRegistry._instance = None


# ========== Auto-Transition Checking Tests ==========


def test_check_auto_transition_prerequisites_satisfied(engine):
    """Test check_auto_transition when prerequisites are satisfied"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "test_001",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.check_auto_transition(process)

    assert result is not None
    assert result["to_state"] == "next"
    assert result["reason"] == "auto_transition"
    assert result["prerequisites_satisfied"] is True


def test_check_auto_transition_prerequisites_not_satisfied(engine):
    """Test check_auto_transition when prerequisites are not satisfied"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "test_002",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "no"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.check_auto_transition(process)

    assert result is not None
    assert result["to_state"] == "next"
    assert result["prerequisites_satisfied"] is False


def test_check_auto_transition_no_auto_transition_configured(engine):
    """Test check_auto_transition when no auto_transition_to configured"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "test_003",
        "kanban_id": "test_kanban",
        "current_state": "final",  # Final state has no auto_transition_to
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.check_auto_transition(process)

    assert result is None


def test_check_auto_transition_invalid_kanban(engine):
    """Test check_auto_transition with invalid kanban_id"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "test_004",
        "kanban_id": "nonexistent_kanban",
        "current_state": "initial",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.check_auto_transition(process)

    assert result is None


# ========== Timeout Transition Tests ==========


def test_check_timeout_transition_expired(engine):
    """Test check_timeout_transition when timeout has expired"""
    engine_obj, workflow_repo, registry = engine

    # Process created 2 hours ago (timeout is 1 hour)
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    process = {
        "process_id": "timeout_001",
        "kanban_id": "timeout_kanban",
        "current_state": "waiting",
        "field_values": {},
        "created_at": old_timestamp,
        "history": [],
    }

    result = engine_obj.check_timeout_transition(process)

    assert result is not None
    assert result["to_state"] == "expired"
    assert result["reason"] == "timeout"
    assert result["elapsed_hours"] >= 1


def test_check_timeout_transition_not_expired(engine):
    """Test check_timeout_transition when timeout has not expired"""
    engine_obj, workflow_repo, registry = engine

    # Process created 30 minutes ago (timeout is 1 hour)
    recent_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

    process = {
        "process_id": "timeout_002",
        "kanban_id": "timeout_kanban",
        "current_state": "waiting",
        "field_values": {},
        "created_at": recent_timestamp,
        "history": [],
    }

    result = engine_obj.check_timeout_transition(process)

    assert result is None


def test_check_timeout_transition_no_timeout_configured(engine):
    """Test check_timeout_transition when no timeout configured"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "timeout_003",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.check_timeout_transition(process)

    assert result is None


def test_check_timeout_transition_uses_history(engine):
    """Test check_timeout_transition uses last transition from history"""
    engine_obj, workflow_repo, registry = engine

    # Process created 5 hours ago, but last transition was 30 minutes ago
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    recent_transition = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

    process = {
        "process_id": "timeout_004",
        "kanban_id": "timeout_kanban",
        "current_state": "waiting",
        "field_values": {},
        "created_at": old_timestamp,
        "history": [
            {
                "from_state": "initial",
                "to_state": "waiting",
                "timestamp": recent_transition,
            }
        ],
    }

    result = engine_obj.check_timeout_transition(process)

    # Should use history timestamp (30 min ago), not created_at (5h ago)
    # So timeout (1h) should not be expired
    assert result is None


# ========== should_auto_transition Tests ==========


def test_should_auto_transition_timeout_priority(engine):
    """Test should_auto_transition returns timeout result (higher priority)"""
    engine_obj, workflow_repo, registry = engine

    # Create kanban with both timeout and auto_transition
    kanban_both = {
        "id": "both_kanban",
        "name": "Both",
        "states": [
            {
                "id": "start",
                "name": "Start",
                "is_initial": True,
                "timeout_hours": 1,
                "auto_transition_to": "next",
            },
            {"id": "next", "name": "Next"},
        ],
        "transitions": [
            {"from": "start", "to": "next", "type": "system", "prerequisites": []}
        ],
        "linked_forms": [],
        "field_mapping": {},
    }

    # Register this kanban temporarily
    registry = engine[2]
    registry._kanbans["both_kanban"] = kanban_both

    # Process with expired timeout
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    process = {
        "process_id": "both_001",
        "kanban_id": "both_kanban",
        "current_state": "start",
        "field_values": {},
        "created_at": old_timestamp,
        "history": [],
    }

    result = engine_obj.should_auto_transition(process)

    # Should return timeout result (higher priority than auto-transition)
    assert result is not None
    assert result["reason"] == "timeout"


def test_should_auto_transition_auto_when_satisfied(engine):
    """Test should_auto_transition returns auto result when prerequisites satisfied"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "auto_001",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.should_auto_transition(process)

    assert result is not None
    assert result["reason"] == "auto_transition"
    assert result["to_state"] == "next"


def test_should_auto_transition_none(engine):
    """Test should_auto_transition returns None when neither applies"""
    engine_obj, workflow_repo, registry = engine

    # Process with prerequisites not satisfied and no timeout
    process = {
        "process_id": "none_001",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "no"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.should_auto_transition(process)

    assert result is None


# ========== Cascade Progression Tests ==========


def test_execute_cascade_progression_single_transition(engine):
    """Test execute_cascade_progression with single transition"""
    engine_obj, workflow_repo, registry = engine

    # Create process
    process = {
        "process_id": "cascade_001",
        "kanban_id": "test_kanban",
        "current_state": "next",  # Start at 'next' which has auto_transition to 'final'
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    # Create in repository
    workflow_repo.create_process(process)

    transitions = engine_obj.execute_cascade_progression(process, workflow_repo)

    # Should execute one transition: next -> final
    assert len(transitions) == 1
    assert transitions[0]["from_state"] == "next"
    assert transitions[0]["to_state"] == "final"
    assert transitions[0]["success"] is True


def test_execute_cascade_progression_chain(engine):
    """Test execute_cascade_progression with chain of transitions"""
    engine_obj, workflow_repo, registry = engine

    # Create process at initial state with ready='yes'
    process = {
        "process_id": "cascade_002",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    # Create in repository
    workflow_repo.create_process(process)

    transitions = engine_obj.execute_cascade_progression(process, workflow_repo)

    # Should execute two transitions: initial -> next -> final
    assert len(transitions) == 2
    assert transitions[0]["from_state"] == "initial"
    assert transitions[0]["to_state"] == "next"
    assert transitions[1]["from_state"] == "next"
    assert transitions[1]["to_state"] == "final"


def test_execute_cascade_progression_max_depth(engine):
    """Test execute_cascade_progression stops at max_depth"""
    engine_obj, workflow_repo, registry = engine

    # Create process
    process = {
        "process_id": "cascade_003",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    workflow_repo.create_process(process)

    # Execute with max_depth=1
    transitions = engine_obj.execute_cascade_progression(
        process, workflow_repo, max_depth=1
    )

    # Should only execute 1 transition even though 2 are available
    assert len(transitions) == 1


def test_execute_cascade_progression_stops_when_no_more_transitions(engine):
    """Test execute_cascade_progression stops when no more transitions available"""
    engine_obj, workflow_repo, registry = engine

    # Start at final state (no auto_transition_to)
    process = {
        "process_id": "cascade_004",
        "kanban_id": "test_kanban",
        "current_state": "final",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    workflow_repo.create_process(process)

    transitions = engine_obj.execute_cascade_progression(process, workflow_repo)

    # Should execute 0 transitions (already at final)
    assert len(transitions) == 0


# ========== Forced Transition Tests ==========


def test_can_force_transition_allowed_with_warnings(engine):
    """Test can_force_transition is allowed with warnings about unmet prerequisites"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "force_001",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "no"},  # Prerequisites not satisfied
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    result = engine_obj.can_force_transition(process, "next", "admin_user")

    assert result["allowed"] is True
    assert len(result["warnings"]) > 0  # Should have warnings about unmet prerequisites


def test_can_force_transition_not_allowed_invalid_transition(engine):
    """Test can_force_transition not allowed for invalid transition"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "force_002",
        "kanban_id": "test_kanban",
        "current_state": "final",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    # Try to transition from final to initial (not defined)
    result = engine_obj.can_force_transition(process, "initial", "admin_user")

    assert result["allowed"] is False
    assert "Transition not defined" in result["warnings"][0]


def test_execute_forced_transition_success(engine):
    """Test execute_forced_transition executes successfully"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "force_003",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    workflow_repo.create_process(process)

    success = engine_obj.execute_forced_transition(
        process,
        "next",
        "admin_user",
        "Business requirement to skip initial state",
        workflow_repo,
    )

    assert success is True

    # Verify process was updated
    updated_process = workflow_repo.get_process_by_id("force_003")
    assert updated_process["current_state"] == "next"

    # Verify justification in audit trail (not in process.history anymore)
    history = workflow_repo.get_process_history("force_003")
    assert len(history) > 0
    last_transition = history[-1]
    assert "FORCED" in last_transition.get("justification", "")


def test_execute_forced_transition_with_unsatisfied_prerequisites(engine):
    """Test execute_forced_transition works even with unsatisfied prerequisites"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "force_004",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "no"},  # Prerequisites NOT satisfied
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    workflow_repo.create_process(process)

    # Should still succeed (Warn, Not Block philosophy)
    success = engine_obj.execute_forced_transition(
        process, "next", "admin_user", "Emergency bypass", workflow_repo
    )

    assert success is True


def test_execute_forced_transition_invalid_transition(engine):
    """Test execute_forced_transition fails for invalid transition"""
    engine_obj, workflow_repo, registry = engine

    process = {
        "process_id": "force_005",
        "kanban_id": "test_kanban",
        "current_state": "final",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }

    workflow_repo.create_process(process)

    success = engine_obj.execute_forced_transition(
        process,
        "initial",  # Invalid transition
        "admin_user",
        "Trying to go backwards",
        workflow_repo,
    )

    assert success is False


# ========== Batch Processing Tests ==========


def test_process_all_auto_transitions_all_processes(engine):
    """Test process_all_auto_transitions processes all pending transitions"""
    engine_obj, workflow_repo, registry = engine

    # Create multiple processes with auto-transitions ready
    for i in range(3):
        process = {
            "process_id": f"batch_{i:03d}",
            "kanban_id": "test_kanban",
            "current_state": "next",  # Has auto_transition to 'final'
            "field_values": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "history": [],
        }
        workflow_repo.create_process(process)

    stats = engine_obj.process_all_auto_transitions(workflow_repo)

    assert stats["processes_checked"] >= 3
    assert stats["transitions_executed"] >= 3
    assert stats["cascades_executed"] >= 3
    assert stats["errors"] == 0


def test_process_all_auto_transitions_specific_kanban(engine):
    """Test process_all_auto_transitions for specific kanban only"""
    engine_obj, workflow_repo, registry = engine

    # Create processes in different kanbans
    process1 = {
        "process_id": "specific_001",
        "kanban_id": "test_kanban",
        "current_state": "next",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process1)

    process2 = {
        "process_id": "specific_002",
        "kanban_id": "timeout_kanban",
        "current_state": "waiting",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process2)

    # Process only test_kanban
    stats = engine_obj.process_all_auto_transitions(
        workflow_repo, kanban_id="test_kanban"
    )

    # Should only process processes from test_kanban
    assert stats["processes_checked"] >= 1


# ========== Diagnostics Tests ==========


def test_get_pending_auto_transitions(engine):
    """Test get_pending_auto_transitions returns list of pending transitions"""
    engine_obj, workflow_repo, registry = engine

    # Create processes with pending auto-transitions
    process1 = {
        "process_id": "pending_001",
        "kanban_id": "test_kanban",
        "current_state": "next",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process1)

    process2 = {
        "process_id": "pending_002",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {"ready": "yes"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process2)

    pending = engine_obj.get_pending_auto_transitions(workflow_repo)

    # Should have at least 2 pending transitions
    assert len(pending) >= 2

    # Check structure
    for item in pending:
        assert "process_id" in item
        assert "current_state" in item
        assert "to_state" in item
        assert "reason" in item


def test_get_pending_auto_transitions_filtered_by_kanban(engine):
    """Test get_pending_auto_transitions filters by kanban"""
    engine_obj, workflow_repo, registry = engine

    # Create process in test_kanban
    process1 = {
        "process_id": "filtered_001",
        "kanban_id": "test_kanban",
        "current_state": "next",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process1)

    # Create process in timeout_kanban
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    process2 = {
        "process_id": "filtered_002",
        "kanban_id": "timeout_kanban",
        "current_state": "waiting",
        "field_values": {},
        "created_at": old_timestamp,
        "history": [],
    }
    workflow_repo.create_process(process2)

    # Get pending for only test_kanban
    pending = engine_obj.get_pending_auto_transitions(
        workflow_repo, kanban_id="test_kanban"
    )

    # All should be from test_kanban
    for item in pending:
        process = workflow_repo.get_process_by_id(item["process_id"])
        assert process["kanban_id"] == "test_kanban"


def test_empty_pending_auto_transitions(engine):
    """Test get_pending_auto_transitions returns empty list when none pending"""
    engine_obj, workflow_repo, registry = engine

    # Create process at final state (no auto-transitions)
    process = {
        "process_id": "empty_001",
        "kanban_id": "test_kanban",
        "current_state": "final",
        "field_values": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    workflow_repo.create_process(process)

    pending = engine_obj.get_pending_auto_transitions(workflow_repo)

    # Should be empty or not include this process
    # (There might be other processes from other tests)
    final_state_pending = [p for p in pending if p["process_id"] == "empty_001"]
    assert len(final_state_pending) == 0
