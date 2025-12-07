#!/usr/bin/env python3
"""
Validate data structure before XSLT transformation.
Usage: python3 scripts/validate_xslt_data.py data.json
"""

import json
import sys
from pathlib import Path


def validate_xslt_data(data):
    """Validate data structure for XSLT transformation."""
    errors = []

    # Check top-level structure
    if "spec" not in data:
        errors.append("Missing 'spec' key")
    if "records" not in data:
        errors.append("Missing 'records' key")

    if errors:
        return False, errors

    spec = data["spec"]

    # Validate spec
    if "title" not in spec:
        errors.append("Missing spec.title")
    if "fields" not in spec:
        errors.append("Missing spec.fields")
    elif not isinstance(spec["fields"], list):
        errors.append("spec.fields must be an array")

    # Validate fields
    for i, field in enumerate(spec.get("fields", [])):
        if "name" not in field:
            errors.append(f"Field {i}: missing 'name'")
        if "type" not in field:
            errors.append(f"Field {i}: missing 'type'")
        if "label" not in field:
            errors.append(f"Field {i}: missing 'label'")

        # Check select fields have options
        if field.get("type") in ("select", "radio"):
            if "options" not in field:
                errors.append(
                    f"Field {field.get('name', i)}: select/radio requires 'options'"
                )
            elif field["options"] and isinstance(field["options"][0], dict):
                if (
                    "value" not in field["options"][0]
                    or "label" not in field["options"][0]
                ):
                    errors.append(
                        f"Field {field.get('name', i)}: options need 'value' and 'label'"
                    )

    # Validate records
    if not isinstance(data["records"], list):
        errors.append("'records' must be an array")

    return len(errors) == 0, errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_xslt_data.py <data.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    valid, errors = validate_xslt_data(data)

    if valid:
        print(f"✅ {filepath} is valid for XSLT transformation")
        sys.exit(0)
    else:
        print(f"❌ {filepath} has validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
