"""
Specification loader utilities for VibeCForms.

This module provides utilities for loading and managing form specifications.
"""

import os
import json
from flask import abort

# Global variable for specs directory (set during app initialization)
_SPECS_DIR = None


def set_specs_dir(specs_dir):
    """Set the global specs directory path.

    Args:
        specs_dir: Path to the specs directory
    """
    global _SPECS_DIR
    _SPECS_DIR = specs_dir


def get_specs_dir():
    """Get the current specs directory path.

    Returns:
        Path to the specs directory
    """
    return _SPECS_DIR


def load_spec(form_path):
    """Load and validate a form specification file.

    Args:
        form_path: Path to form (can include subdirectories, e.g., 'financeiro/contas')

    Returns:
        Parsed specification dictionary
    """
    if _SPECS_DIR is None:
        raise RuntimeError("Specs directory not set. Call set_specs_dir() first.")

    spec_path = os.path.join(_SPECS_DIR, f"{form_path}.json")
    if not os.path.exists(spec_path):
        abort(404, description=f"Form specification '{form_path}' not found")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Validate required spec fields
    if "title" not in spec or "fields" not in spec:
        abort(500, description=f"Invalid spec file for '{form_path}'")

    # Validate default_tags if present
    if "default_tags" in spec:
        if not isinstance(spec["default_tags"], list):
            abort(500, description=f"Invalid spec: default_tags must be an array")

        import re

        tag_pattern = r"^[a-z0-9_]+$"
        for tag in spec["default_tags"]:
            if not isinstance(tag, str):
                abort(500, description=f"Invalid tag in default_tags: must be string")
            if not re.match(tag_pattern, tag):
                abort(
                    500,
                    description=f"Invalid tag name '{tag}': use lowercase, numbers, underscores only",
                )

    return spec
