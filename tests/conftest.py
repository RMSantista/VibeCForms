"""
Pytest configuration and fixtures for VibeCForms tests.
"""

import os
import sys
import json
import shutil
import pytest
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_business_case(tmp_path_factory):
    """
    Create a temporary business case structure for testing.

    This fixture creates a complete business case directory with:
    - specs/ folder with test form specifications
    - config/ folder with persistence.json and schema_history.json
    - templates/ folder (copied from src/templates)
    - data/ folder for test data
    - backups/ folder for test backups
    """
    # Create temporary business case directory
    business_case = tmp_path_factory.mktemp("test_business_case")

    # Create directory structure
    (business_case / "specs").mkdir()
    (business_case / "specs" / "financeiro").mkdir()
    (business_case / "specs" / "rh").mkdir()
    (business_case / "specs" / "rh" / "departamentos").mkdir()
    (business_case / "config").mkdir()
    (business_case / "data").mkdir()
    (business_case / "backups" / "migrations").mkdir(parents=True)

    # Copy templates from src/templates
    src_templates = Path(__file__).parent.parent / "src" / "templates"
    if src_templates.exists():
        shutil.copytree(src_templates, business_case / "templates")

    # Copy test specs from src/specs
    src_specs = Path(__file__).parent.parent / "src" / "specs"
    if src_specs.exists():
        # Copy individual spec files (including form specs)
        for spec_file in src_specs.glob("*.json"):
            shutil.copy(spec_file, business_case / "specs")

        # Copy folder specs including _folder.json files
        if (src_specs / "financeiro").exists():
            for spec_file in (src_specs / "financeiro").glob("*.json"):
                shutil.copy(spec_file, business_case / "specs" / "financeiro")

        if (src_specs / "rh").exists():
            for spec_file in (src_specs / "rh").glob("*.json"):
                shutil.copy(spec_file, business_case / "specs" / "rh")

            if (src_specs / "rh" / "departamentos").exists():
                for spec_file in (src_specs / "rh" / "departamentos").glob("*.json"):
                    shutil.copy(
                        spec_file, business_case / "specs" / "rh" / "departamentos"
                    )

    # Create persistence.json
    persistence_config = {
        "version": "1.0",
        "default_backend": "txt",
        "backends": {
            "txt": {
                "type": "txt",
                "path": "data/",
                "delimiter": ";",
                "encoding": "utf-8",
                "extension": ".txt",
            },
            "sqlite": {
                "type": "sqlite",
                "database": "data/test.db",
                "timeout": 10,
                "check_same_thread": False,
            },
        },
        "form_mappings": {"*": "default_backend"},
        "auto_create_storage": True,
        "auto_migrate_schema": True,
        "backup_before_migrate": True,
        "backup_path": "backups/migrations/",
    }

    with open(business_case / "config" / "persistence.json", "w") as f:
        json.dump(persistence_config, f, indent=2)

    # Create empty schema_history.json
    with open(business_case / "config" / "schema_history.json", "w") as f:
        json.dump({}, f)

    return business_case


@pytest.fixture(scope="function", autouse=True)
def initialize_test_app(test_business_case, request):
    """
    Automatically initialize the VibeCForms app with test business case.

    This fixture runs before each test and initializes the app with the
    test business case directory.

    Tests can opt-out by using the marker: @pytest.mark.no_autoinit
    """
    # Check if test has no_autoinit marker
    if "no_autoinit" in request.keywords:
        yield
        return

    # Import using the same path as tests
    from src import VibeCForms

    # Reset any existing state
    from persistence.config import reset_config
    from persistence.schema_history import reset_history

    reset_config()
    reset_history()

    # Initialize app with test business case
    VibeCForms.initialize_app(str(test_business_case))

    # Verify initialization
    assert VibeCForms.SPECS_DIR is not None, "SPECS_DIR was not initialized"
    assert (
        VibeCForms.BUSINESS_CASE_ROOT is not None
    ), "BUSINESS_CASE_ROOT was not initialized"

    yield

    # Cleanup: reset config and history after each test
    reset_config()
    reset_history()
    # Reset global variables
    VibeCForms.BUSINESS_CASE_ROOT = None
    VibeCForms.SPECS_DIR = None
    VibeCForms.TEMPLATE_DIR = None
