"""
Tests for Tag Management API Endpoints (FASE 9).

Tests the REST API endpoints for tag management:
- POST /api/<form>/tags/<id> - Add tag
- DELETE /api/<form>/tags/<id>/<tag> - Remove tag
- GET /api/<form>/tags/<id> - Get tags
- GET /api/<form>/tags/<id>/history - Get tag history
- GET /api/<form>/search/tags?tag=<tag> - Search by tag
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

# Import from src
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from VibeCForms import app
from persistence.factory import RepositoryFactory
from persistence.config import PersistenceConfig
from services.tag_service import TagService
from utils.crockford import generate_id, validate_id


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory for testing."""
    import os
    import uuid

    # Create a unique subdirectory for this test
    test_id = str(uuid.uuid4())[:8]
    test_dir = tmp_path / test_id
    test_dir.mkdir()

    config_dir = test_dir / "config"
    config_dir.mkdir()

    # Create persistence.json
    persistence_config = {
        "default_backend": "sqlite",
        "backends": {
            "sqlite": {
                "type": "sqlite",
                "database_path": str(test_dir / "test.db"),
                "timeout": 10,
            }
        },
        "form_mappings": {"test_form": "sqlite", "*": "default_backend"},
    }

    with open(config_dir / "persistence.json", "w") as f:
        json.dump(persistence_config, f)

    # Set config path
    old_config_dir = os.environ.get("VIBECFORMS_CONFIG_DIR")
    os.environ["VIBECFORMS_CONFIG_DIR"] = str(config_dir)

    # Reload config
    PersistenceConfig._instance = None

    yield config_dir

    # Restore
    if old_config_dir:
        os.environ["VIBECFORMS_CONFIG_DIR"] = old_config_dir
    else:
        if "VIBECFORMS_CONFIG_DIR" in os.environ:
            del os.environ["VIBECFORMS_CONFIG_DIR"]

    PersistenceConfig._instance = None
    RepositoryFactory._repositories = {}


@pytest.fixture
def temp_specs_dir(tmp_path, test_spec):
    """Create temporary specs directory for testing."""
    import os

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(exist_ok=True)

    # Write test_form.json spec
    with open(specs_dir / "test_form.json", "w") as f:
        json.dump(test_spec, f)

    # Set specs directory
    from utils.spec_loader import set_specs_dir

    set_specs_dir(str(specs_dir))

    yield specs_dir


@pytest.fixture
def client(temp_config_dir, temp_specs_dir):
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_spec():
    """Test form specification."""
    return {
        "title": "Test Form",
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {
                "name": "description",
                "label": "Description",
                "type": "textarea",
                "required": False,
            },
        ],
    }


@pytest.fixture
def test_record(temp_config_dir, test_spec):
    """Create a test record and return its ID."""
    repo = RepositoryFactory.get_repository("test_form")
    repo.create_storage("test_form", test_spec)

    record_data = {"name": "Test Record", "description": "This is a test record"}

    record_id = repo.create("test_form", test_spec, record_data)
    return record_id


def test_add_tag_success(client, test_record):
    """Test successfully adding a tag to a record."""
    response = client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["tag"] == "important"
    assert data["record_id"] == test_record


def test_add_tag_invalid_id(client):
    """Test adding a tag with invalid ID format."""
    invalid_id = "invalid_id_format"

    response = client.post(
        f"/api/test_form/tags/{invalid_id}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Invalid ID format" in data["error"]


def test_add_tag_missing_tag(client, test_record):
    """Test adding a tag without providing tag name."""
    response = client.post(
        f"/api/test_form/tags/{test_record}", json={"applied_by": "test_user"}
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Tag is required" in data["error"]


def test_add_tag_invalid_name(client, test_record):
    """Test adding a tag with invalid name (uppercase, spaces, special chars)."""
    # Tag service validates tag names - uppercase should be rejected
    response = client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "Invalid Tag!", "applied_by": "test_user"},
    )

    # This should fail validation
    data = json.loads(response.data)
    assert data["success"] is False


def test_add_duplicate_tag(client, test_record):
    """Test adding the same tag twice."""
    # Add tag first time
    response1 = client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )
    assert response1.status_code == 200

    # Try to add same tag again
    response2 = client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    # Should return 409 Conflict
    assert response2.status_code == 409
    data = json.loads(response2.data)
    assert data["success"] is False


def test_get_tags_success(client, test_record):
    """Test getting tags for a record."""
    # Add some tags first
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "urgent", "applied_by": "test_user"},
    )

    # Get tags
    response = client.get(f"/api/test_form/tags/{test_record}")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["record_id"] == test_record
    assert len(data["tags"]) == 2

    tag_names = [t["tag"] for t in data["tags"]]
    assert "important" in tag_names
    assert "urgent" in tag_names


def test_get_tags_invalid_id(client):
    """Test getting tags with invalid ID format."""
    invalid_id = "invalid_id"

    response = client.get(f"/api/test_form/tags/{invalid_id}")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Invalid ID format" in data["error"]


def test_get_tags_empty(client, test_record):
    """Test getting tags for a record with no tags."""
    response = client.get(f"/api/test_form/tags/{test_record}")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["record_id"] == test_record
    assert len(data["tags"]) == 0


def test_remove_tag_success(client, test_record):
    """Test successfully removing a tag."""
    # Add tag first
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    # Remove tag
    response = client.delete(
        f"/api/test_form/tags/{test_record}/important?removed_by=test_user"
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["tag"] == "important"
    assert data["record_id"] == test_record

    # Verify tag was removed
    get_response = client.get(f"/api/test_form/tags/{test_record}")
    get_data = json.loads(get_response.data)
    assert len(get_data["tags"]) == 0


def test_remove_tag_nonexistent(client, test_record):
    """Test removing a tag that doesn't exist."""
    response = client.delete(
        f"/api/test_form/tags/{test_record}/nonexistent?removed_by=test_user"
    )

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Tag not found" in data["error"]


def test_remove_tag_invalid_id(client):
    """Test removing a tag with invalid ID format."""
    invalid_id = "invalid_id"

    response = client.delete(
        f"/api/test_form/tags/{invalid_id}/important?removed_by=test_user"
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Invalid ID format" in data["error"]


def test_get_tag_history(client, test_record):
    """Test getting full tag history including removed tags."""
    # Add and remove some tags
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "draft", "applied_by": "test_user"},
    )
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "review", "applied_by": "test_user"},
    )
    client.delete(f"/api/test_form/tags/{test_record}/draft?removed_by=test_user")
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "approved", "applied_by": "test_user"},
    )

    # Get history
    response = client.get(f"/api/test_form/tags/{test_record}/history")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["record_id"] == test_record
    assert len(data["history"]) >= 3  # Should include removed tags

    # Verify all tags are in history
    tag_names = [t["tag"] for t in data["history"]]
    assert "draft" in tag_names
    assert "review" in tag_names
    assert "approved" in tag_names


def test_get_tag_history_invalid_id(client):
    """Test getting tag history with invalid ID."""
    invalid_id = "invalid_id"

    response = client.get(f"/api/test_form/tags/{invalid_id}/history")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Invalid ID format" in data["error"]


def test_search_by_tag_ids_only(client, test_record):
    """Test searching objects by tag (IDs only)."""
    # Add tag to record
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    # Search by tag
    response = client.get("/api/test_form/search/tags?tag=important")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["tag"] == "important"
    assert data["count"] >= 1  # Allow for multiple results due to test isolation
    assert test_record in data["object_ids"]


def test_search_by_tag_with_data(client, test_record):
    """Test searching objects by tag with full object data."""
    # Add tag to record
    client.post(
        f"/api/test_form/tags/{test_record}",
        json={"tag": "important", "applied_by": "test_user"},
    )

    # Search by tag with data
    response = client.get("/api/test_form/search/tags?tag=important&include_data=true")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["tag"] == "important"
    assert data["count"] >= 1  # Allow for multiple results due to test isolation
    assert len(data["objects"]) >= 1

    # Find our specific record in the results
    our_record = next(
        (obj for obj in data["objects"] if obj["_record_id"] == test_record), None
    )
    assert our_record is not None
    assert our_record["name"] == "Test Record"


def test_search_by_tag_missing_tag(client):
    """Test searching without providing tag parameter."""
    response = client.get("/api/test_form/search/tags")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "Tag parameter is required" in data["error"]


def test_search_by_tag_no_results(client, test_record):
    """Test searching for a tag that no objects have."""
    response = client.get("/api/test_form/search/tags?tag=nonexistent")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["tag"] == "nonexistent"
    assert data["count"] == 0
    assert len(data["object_ids"]) == 0


def test_tag_workflow(client, test_record):
    """Test a complete tag workflow: add multiple, remove some, query."""
    # Add multiple tags
    tags_to_add = ["draft", "important", "needs_review"]
    for tag in tags_to_add:
        response = client.post(
            f"/api/test_form/tags/{test_record}",
            json={"tag": tag, "applied_by": "test_user"},
        )
        assert response.status_code == 200

    # Verify all tags exist
    response = client.get(f"/api/test_form/tags/{test_record}")
    data = json.loads(response.data)
    assert len(data["tags"]) == 3

    # Remove one tag
    response = client.delete(
        f"/api/test_form/tags/{test_record}/draft?removed_by=test_user"
    )
    assert response.status_code == 200

    # Verify only 2 active tags remain
    response = client.get(f"/api/test_form/tags/{test_record}")
    data = json.loads(response.data)
    assert len(data["tags"]) == 2

    active_tags = [t["tag"] for t in data["tags"]]
    assert "draft" not in active_tags
    assert "important" in active_tags
    assert "needs_review" in active_tags

    # Verify history shows all 3 tags
    response = client.get(f"/api/test_form/tags/{test_record}/history")
    data = json.loads(response.data)
    assert len(data["history"]) == 3

    # Search by tag
    response = client.get("/api/test_form/search/tags?tag=important")
    data = json.loads(response.data)
    assert test_record in data["object_ids"]

    response = client.get("/api/test_form/search/tags?tag=draft")
    data = json.loads(response.data)
    assert test_record not in data["object_ids"]  # Removed tag shouldn't match
