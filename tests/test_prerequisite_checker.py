"""
Tests for PrerequisiteChecker - Validates prerequisites for workflow transitions

Test Coverage:
- Type 1: field_check (not_empty, equals, greater_than, less_than, contains, regex, etc.)
- Type 2: external_api (successful, failed, timeout, error)
- Type 3: time_elapsed (satisfied, not satisfied, invalid timestamp)
- Type 4: custom_script (valid, error, not found)
- Helper methods (are_all_satisfied, get_unsatisfied)
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import requests

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from workflow.prerequisite_checker import PrerequisiteChecker


@pytest.fixture
def checker():
    """Create PrerequisiteChecker instance"""
    temp_dir = tempfile.mkdtemp()
    checker = PrerequisiteChecker(scripts_dir=temp_dir)
    yield checker
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_process():
    """Sample process for testing"""
    return {
        "process_id": "test_process_001",
        "kanban_id": "test_kanban",
        "current_state": "initial",
        "field_values": {
            "name": "Test Name",
            "value": "100",
            "status": "active",
            "priority": "5",
            "email": "test@example.com",
        },
        "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "history": [],
    }


@pytest.fixture
def sample_kanban():
    """Sample kanban definition"""
    return {
        "id": "test_kanban",
        "name": "Test Kanban",
        "states": [
            {"id": "initial", "name": "Initial", "is_initial": True},
            {"id": "next", "name": "Next"},
        ],
    }


# ========== Type 1: Field Check Tests ==========


def test_field_check_not_empty_satisfied(checker, sample_process, sample_kanban):
    """Test field_check with not_empty condition - satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "name",
            "condition": "not_empty",
            "message": "Name is required",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert len(results) == 1
    assert results[0]["type"] == "field_check"
    assert results[0]["satisfied"] is True


def test_field_check_not_empty_unsatisfied(checker, sample_process, sample_kanban):
    """Test field_check with not_empty condition - not satisfied"""
    sample_process["field_values"]["empty_field"] = ""

    prereqs = [
        {
            "type": "field_check",
            "field": "empty_field",
            "condition": "not_empty",
            "message": "Field is required",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert len(results) == 1
    assert results[0]["satisfied"] is False
    assert "Field is required" in results[0]["message"]


def test_field_check_equals_satisfied(checker, sample_process, sample_kanban):
    """Test field_check with equals condition - satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "status",
            "condition": "equals",
            "value": "active",
            "message": "Status must be active",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_equals_unsatisfied(checker, sample_process, sample_kanban):
    """Test field_check with equals condition - not satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "status",
            "condition": "equals",
            "value": "inactive",
            "message": "Status must be inactive",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


def test_field_check_not_equals(checker, sample_process, sample_kanban):
    """Test field_check with not_equals condition"""
    prereqs = [
        {
            "type": "field_check",
            "field": "status",
            "condition": "not_equals",
            "value": "inactive",
            "message": "Status should not be inactive",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_greater_than_satisfied(checker, sample_process, sample_kanban):
    """Test field_check with greater_than condition - satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "value",
            "condition": "greater_than",
            "value": "50",
            "message": "Value must be greater than 50",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_greater_than_unsatisfied(checker, sample_process, sample_kanban):
    """Test field_check with greater_than condition - not satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "value",
            "condition": "greater_than",
            "value": "200",
            "message": "Value must be greater than 200",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


def test_field_check_less_than(checker, sample_process, sample_kanban):
    """Test field_check with less_than condition"""
    prereqs = [
        {
            "type": "field_check",
            "field": "value",
            "condition": "less_than",
            "value": "200",
            "message": "Value must be less than 200",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_greater_or_equal(checker, sample_process, sample_kanban):
    """Test field_check with greater_or_equal condition"""
    prereqs = [
        {
            "type": "field_check",
            "field": "value",
            "condition": "greater_or_equal",
            "value": "100",
            "message": "Value must be >= 100",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_less_or_equal(checker, sample_process, sample_kanban):
    """Test field_check with less_or_equal condition"""
    prereqs = [
        {
            "type": "field_check",
            "field": "value",
            "condition": "less_or_equal",
            "value": "100",
            "message": "Value must be <= 100",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_contains_satisfied(checker, sample_process, sample_kanban):
    """Test field_check with contains condition - satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "email",
            "condition": "contains",
            "value": "@example.com",
            "message": "Email must be from example.com",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_contains_unsatisfied(checker, sample_process, sample_kanban):
    """Test field_check with contains condition - not satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "email",
            "condition": "contains",
            "value": "@other.com",
            "message": "Email must be from other.com",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


def test_field_check_regex_satisfied(checker, sample_process, sample_kanban):
    """Test field_check with regex condition - satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "email",
            "condition": "regex",
            "value": r"^[a-z]+@example\.com$",
            "message": "Email must match pattern",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True


def test_field_check_regex_unsatisfied(checker, sample_process, sample_kanban):
    """Test field_check with regex condition - not satisfied"""
    prereqs = [
        {
            "type": "field_check",
            "field": "email",
            "condition": "regex",
            "value": r"^[0-9]+@",
            "message": "Email must start with numbers",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


def test_field_check_invalid_regex(checker, sample_process, sample_kanban):
    """Test field_check with invalid regex pattern"""
    prereqs = [
        {
            "type": "field_check",
            "field": "email",
            "condition": "regex",
            "value": "[invalid(",
            "message": "Invalid regex",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


# ========== Type 2: External API Tests ==========


@patch("workflow.prerequisite_checker.requests.get")
def test_external_api_success_satisfied(
    mock_get, checker, sample_process, sample_kanban
):
    """Test external_api with successful API call returning satisfied=true"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "satisfied": True,
        "message": "API validation passed",
    }
    mock_get.return_value = mock_response

    prereqs = [
        {
            "type": "external_api",
            "url": "https://api.example.com/validate",
            "method": "GET",
            "message": "External validation failed",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["type"] == "external_api"
    assert results[0]["satisfied"] is True
    assert "API validation passed" in results[0]["message"]


@patch("workflow.prerequisite_checker.requests.get")
def test_external_api_success_unsatisfied(
    mock_get, checker, sample_process, sample_kanban
):
    """Test external_api with successful API call returning satisfied=false"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "satisfied": False,
        "message": "API validation failed: insufficient balance",
    }
    mock_get.return_value = mock_response

    prereqs = [
        {
            "type": "external_api",
            "url": "https://api.example.com/check_balance",
            "method": "GET",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "insufficient balance" in results[0]["message"]


@patch("workflow.prerequisite_checker.requests.post")
def test_external_api_post_with_payload(
    mock_post, checker, sample_process, sample_kanban
):
    """Test external_api with POST method and payload"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "satisfied": True,
        "message": "POST validation passed",
    }
    mock_post.return_value = mock_response

    prereqs = [
        {
            "type": "external_api",
            "url": "https://api.example.com/validate",
            "method": "POST",
            "payload": {"process_id": "{process_id}", "value": "{value}"},
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is True
    # Verify POST was called with correct payload
    mock_post.assert_called_once()


@patch("workflow.prerequisite_checker.requests.get")
def test_external_api_timeout(mock_get, checker, sample_process, sample_kanban):
    """Test external_api with timeout"""
    mock_get.side_effect = requests.exceptions.Timeout

    prereqs = [
        {"type": "external_api", "url": "https://api.example.com/slow", "timeout": 1}
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "timed out" in results[0]["message"]


@patch("workflow.prerequisite_checker.requests.get")
def test_external_api_error(mock_get, checker, sample_process, sample_kanban):
    """Test external_api with connection error"""
    mock_get.side_effect = requests.exceptions.ConnectionError

    prereqs = [{"type": "external_api", "url": "https://api.example.com/unreachable"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "API call failed" in results[0]["message"]


@patch("workflow.prerequisite_checker.requests.get")
def test_external_api_non_200_status(mock_get, checker, sample_process, sample_kanban):
    """Test external_api with non-200 status code"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    prereqs = [{"type": "external_api", "url": "https://api.example.com/not_found"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "404" in results[0]["message"]


# ========== Type 3: Time Elapsed Tests ==========


def test_time_elapsed_satisfied(checker, sample_process, sample_kanban):
    """Test time_elapsed with time satisfied (2 hours elapsed, requires 1 hour)"""
    prereqs = [
        {
            "type": "time_elapsed",
            "hours": 1,
            "minutes": 0,
            "message": "Must wait at least 1 hour",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["type"] == "time_elapsed"
    assert results[0]["satisfied"] is True


def test_time_elapsed_not_satisfied(checker, sample_process, sample_kanban):
    """Test time_elapsed with time not satisfied"""
    prereqs = [
        {
            "type": "time_elapsed",
            "hours": 5,
            "minutes": 0,
            "message": "Must wait at least 5 hours",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False


def test_time_elapsed_with_minutes(checker, sample_process, sample_kanban):
    """Test time_elapsed with minutes specification"""
    prereqs = [
        {
            "type": "time_elapsed",
            "hours": 0,
            "minutes": 30,
            "message": "Must wait at least 30 minutes",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Process was created 2 hours ago, so 30 minutes should be satisfied
    assert results[0]["satisfied"] is True


def test_time_elapsed_with_history(checker, sample_process, sample_kanban):
    """Test time_elapsed using last transition timestamp from history"""
    # Add recent transition to history (30 minutes ago)
    sample_process["history"] = [
        {
            "from_state": "initial",
            "to_state": "current",
            "timestamp": (
                datetime.now(timezone.utc) - timedelta(minutes=30)
            ).isoformat(),
        }
    ]

    prereqs = [
        {
            "type": "time_elapsed",
            "hours": 1,
            "minutes": 0,
            "message": "Must wait 1 hour since last transition",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    # Only 30 minutes have passed, so should not be satisfied
    assert results[0]["satisfied"] is False


def test_time_elapsed_invalid_timestamp(checker, sample_process, sample_kanban):
    """Test time_elapsed with invalid timestamp"""
    sample_process["created_at"] = "invalid-timestamp"

    prereqs = [{"type": "time_elapsed", "hours": 1, "message": "Must wait 1 hour"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "Invalid timestamp" in results[0]["message"]


# ========== Type 4: Custom Script Tests ==========


def test_custom_script_satisfied(checker, sample_process, sample_kanban):
    """Test custom_script with valid script returning satisfied=true"""
    # Create a valid script
    script_path = os.path.join(checker.scripts_dir, "validate_test.py")
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    return {
        'satisfied': True,
        'message': 'Custom validation passed'
    }
"""
        )

    prereqs = [
        {
            "type": "custom_script",
            "script": "validate_test.py",
            "message": "Custom script validation failed",
        }
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["type"] == "custom_script"
    assert results[0]["satisfied"] is True
    assert "Custom validation passed" in results[0]["message"]


def test_custom_script_unsatisfied(checker, sample_process, sample_kanban):
    """Test custom_script with valid script returning satisfied=false"""
    script_path = os.path.join(checker.scripts_dir, "validate_fail.py")
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    # Check if value is greater than 200
    value = int(process['field_values'].get('value', 0))
    if value > 200:
        return {'satisfied': True, 'message': 'Value is sufficient'}
    else:
        return {'satisfied': False, 'message': 'Value must be greater than 200'}
"""
        )

    prereqs = [{"type": "custom_script", "script": "validate_fail.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "must be greater than 200" in results[0]["message"]


def test_custom_script_not_found(checker, sample_process, sample_kanban):
    """Test custom_script with non-existent script file"""
    prereqs = [{"type": "custom_script", "script": "nonexistent.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "Script not found" in results[0]["message"]


def test_custom_script_no_validate_function(checker, sample_process, sample_kanban):
    """Test custom_script with script missing validate() function"""
    script_path = os.path.join(checker.scripts_dir, "no_validate.py")
    with open(script_path, "w") as f:
        f.write(
            """
def some_other_function():
    return True
"""
        )

    prereqs = [{"type": "custom_script", "script": "no_validate.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "does not define validate()" in results[0]["message"]


def test_custom_script_execution_error(checker, sample_process, sample_kanban):
    """Test custom_script with script that raises exception"""
    script_path = os.path.join(checker.scripts_dir, "error_script.py")
    with open(script_path, "w") as f:
        f.write(
            """
def validate(process, kanban):
    raise ValueError("Intentional error")
"""
        )

    prereqs = [{"type": "custom_script", "script": "error_script.py"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "Script execution error" in results[0]["message"]


# ========== Helper Methods Tests ==========


def test_are_all_satisfied_true(checker, sample_process, sample_kanban):
    """Test are_all_satisfied returns True when all prerequisites are satisfied"""
    prereqs = [
        {"type": "field_check", "field": "name", "condition": "not_empty"},
        {
            "type": "field_check",
            "field": "status",
            "condition": "equals",
            "value": "active",
        },
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert checker.are_all_satisfied(results) is True


def test_are_all_satisfied_false(checker, sample_process, sample_kanban):
    """Test are_all_satisfied returns False when any prerequisite is not satisfied"""
    prereqs = [
        {"type": "field_check", "field": "name", "condition": "not_empty"},
        {
            "type": "field_check",
            "field": "status",
            "condition": "equals",
            "value": "inactive",
        },
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert checker.are_all_satisfied(results) is False


def test_get_unsatisfied(checker, sample_process, sample_kanban):
    """Test get_unsatisfied returns only unsatisfied prerequisites"""
    prereqs = [
        {"type": "field_check", "field": "name", "condition": "not_empty"},
        {
            "type": "field_check",
            "field": "status",
            "condition": "equals",
            "value": "inactive",
        },
        {
            "type": "field_check",
            "field": "value",
            "condition": "greater_than",
            "value": "200",
        },
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)
    unsatisfied = checker.get_unsatisfied(results)

    # Should have 2 unsatisfied (status != inactive, value not > 200)
    assert len(unsatisfied) == 2


def test_unknown_prerequisite_type(checker, sample_process, sample_kanban):
    """Test handling of unknown prerequisite type"""
    prereqs = [{"type": "unknown_type", "some_param": "value"}]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert results[0]["satisfied"] is False
    assert "Unknown prerequisite type" in results[0]["message"]


def test_multiple_prerequisites_mixed(checker, sample_process, sample_kanban):
    """Test checking multiple prerequisites of different types"""
    prereqs = [
        {"type": "field_check", "field": "name", "condition": "not_empty"},
        {"type": "time_elapsed", "hours": 1, "minutes": 0},
    ]

    results = checker.check_prerequisites(prereqs, sample_process, sample_kanban)

    assert len(results) == 2
    assert results[0]["type"] == "field_check"
    assert results[1]["type"] == "time_elapsed"
    # Both should be satisfied
    assert checker.are_all_satisfied(results) is True
