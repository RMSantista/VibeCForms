"""
Form rendering utilities for VibeCForms.

This module provides high-level functions for rendering forms and tables from specs.
Internal implementation details are private (prefixed with _).
"""

import os
import json
import logging
from typing import Dict, Any, List
from flask import render_template_string, current_app

logger = logging.getLogger(__name__)

# Table column widths (percentage)
_TABLE_FIELDS_TOTAL_WIDTH = 60
_TABLE_TAGS_WIDTH = 15
_TABLE_ACTIONS_WIDTH = 25


def _get_template_path(template_name: str) -> str:
    """Get template path with fallback support.

    First tries business case templates, then falls back to src/templates.

    Args:
        template_name: Name of the template file (can include subdirectory, e.g., "fields/input.html")

    Returns:
        Full path to the template file
    """
    # Get directories from app config
    try:
        # Try to get from Flask app context first
        business_case_root = current_app.config.get("BUSINESS_CASE_ROOT")
        fallback_template_dir = current_app.config.get("FALLBACK_TEMPLATE_DIR")
    except RuntimeError:
        # If no app context, fall back to global variables (for tests)
        from src import VibeCForms

        business_case_root = VibeCForms.BUSINESS_CASE_ROOT
        fallback_template_dir = VibeCForms.FALLBACK_TEMPLATE_DIR

    # Check business case templates first
    if business_case_root:
        business_template = os.path.join(business_case_root, "templates", template_name)
        if os.path.exists(business_template):
            return business_template

    # Fallback to src/templates
    fallback_template = os.path.join(fallback_template_dir, template_name)
    if os.path.exists(fallback_template):
        return fallback_template

    # Neither exists, return business case path (will fail appropriately)
    if business_case_root:
        return os.path.join(business_case_root, "templates", template_name)
    return fallback_template


def _read_template(template_name: str) -> str:
    """Read template content with fallback support.

    Args:
        template_name: Name of the template file (can include subdirectory)

    Returns:
        Template content as string
    """
    template_path = _get_template_path(template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def _render_field(field: Dict[str, Any], form_data: Dict[str, Any] = None) -> str:
    """Generate HTML for a single form field based on spec using templates.

    Args:
        field: Field definition from spec
        form_data: Optional data to pre-fill the field

    Returns:
        HTML string for the field
    """
    field_name = field["name"]
    field_label = field["label"]
    field_type = field["type"]
    required = field.get("required", False)

    value = ""
    if form_data:
        value = form_data.get(field_name, "")

    if field_type == "checkbox":
        template_content = _read_template("fields/checkbox.html")
        checked = form_data and form_data.get(field_name)
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            checked=checked,
        )

    elif field_type == "textarea":
        template_content = _read_template("fields/textarea.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
        )

    elif field_type == "select":
        template_content = _read_template("fields/select.html")
        options = field.get("options", [])
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
            options=options,
        )

    elif field_type == "radio":
        template_content = _read_template("fields/radio.html")
        options = field.get("options", [])
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
            options=options,
        )

    elif field_type == "color":
        template_content = _read_template("fields/color.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
        )

    elif field_type == "range":
        template_content = _read_template("fields/range.html")
        min_value = field.get("min", 0)
        max_value = field.get("max", 100)
        step_value = field.get("step", 1)

        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
            min_value=min_value,
            max_value=max_value,
            step_value=step_value,
        )

    elif field_type == "search" and field.get("datasource"):
        # Search field with autocomplete from datasource
        template_content = _read_template("fields/search_autocomplete.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
            datasource=field.get("datasource"),
        )

    elif field_type == "relationship":
        # Relationship field with autocomplete to target entity
        # Stores UUID of related record in hidden field (cardinality=one)
        # or JSON array of UUIDs (cardinality=many)
        template_content = _read_template("fields/relationship.html")
        target_type = field.get("target")
        cardinality = field.get("cardinality", "one")  # Default: one
        display_field = field.get("display_field")  # Optional: campo a exibir no target

        if not target_type:
            logger.error(
                f"Field '{field_name}' type 'relationship' requires 'target' attribute"
            )
            raise ValueError(
                f"Relationship field '{field_name}' must specify 'target' attribute"
            )

        # Validar cardinality
        if cardinality not in ["one", "many"]:
            logger.warning(
                f"Field '{field_name}' has invalid cardinality '{cardinality}', using 'one'"
            )
            cardinality = "one"

        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            target_type=target_type,
            cardinality=cardinality,
            display_field=display_field,
            required=required,
            value=value,
        )

    else:
        # Input types: text, tel, email, number, password, date, url, search, datetime-local, time, month, week, hidden
        template_content = _read_template("fields/input.html")
        input_type = (
            field_type
            if field_type
            in [
                "text",
                "tel",
                "email",
                "number",
                "password",
                "date",
                "url",
                "search",
                "datetime-local",
                "time",
                "month",
                "week",
                "hidden",
            ]
            else "text"
        )

        # For number fields, add step attribute to allow decimals
        step = None
        if input_type == "number":
            step = field.get("step", "any")  # Default: "any" allows any decimal

        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            input_type=input_type,
            required=required,
            value=value,
            step=step,
        )


def _render_table_headers(spec: Dict[str, Any]) -> str:
    """Generate table headers from spec.

    Args:
        spec: Form specification

    Returns:
        HTML string for table headers
    """
    headers = ""

    # Tags column first (TABLE_TAGS_WIDTH% width) - no title
    headers += f'<th style="width: {_TABLE_TAGS_WIDTH}%;"></th>\n'

    # Calculate width for fields (TABLE_FIELDS_TOTAL_WIDTH% total, divided by number of fields)
    num_fields = len(spec["fields"])
    col_width = (
        int(_TABLE_FIELDS_TOTAL_WIDTH / num_fields)
        if num_fields > 0
        else _TABLE_FIELDS_TOTAL_WIDTH
    )

    for field in spec["fields"]:
        headers += f'<th style="width: {col_width}%;">{field["label"]}</th>\n'

    # Actions column (TABLE_ACTIONS_WIDTH% width)
    headers += f'<th style="width: {_TABLE_ACTIONS_WIDTH}%;">Ações</th>'
    return headers


def _render_table_row(
    form_data: Dict[str, Any], spec: Dict[str, Any], form_name: str
) -> str:
    """Generate a table row from form data.

    Args:
        form_data: Dictionary with form field values (must include '_record_id')
        spec: Form specification
        form_name: Path to the form

    Returns:
        HTML string for table row
    """
    cells = ""

    # Extract record_id from form data (used for edit/delete/tags links)
    record_id = form_data.get("_record_id", "")

    # Tags column first (read-only display)
    tags_html = f"""<td class="tags-cell" data-record-id="{record_id}" data-form-name="{form_name}">
        <div class="tags-container" id="tags-{record_id}">
            <!-- Tags will be loaded here -->
        </div>
    </td>"""
    cells += tags_html

    # Generate cells for each field
    for field in spec["fields"]:
        field_name = field["name"]
        field_type = field["type"]
        value = form_data.get(field_name, "")

        if field_type == "checkbox":
            display_value = "Sim" if value else "Não"
        elif field_type == "select" or field_type == "radio":
            # Find label for the selected value
            options = field.get("options", [])
            display_value = value
            for option in options:
                if option.get("value") == value:
                    display_value = option.get("label", value)
                    break
        elif field_type == "color":
            # Display color swatch alongside hex value
            display_value = f'<span style="display:inline-block;width:20px;height:20px;background-color:{value};border:1px solid #ccc;vertical-align:middle;margin-right:5px;"></span>{value}'
        elif field_type == "password":
            # Don't display password values
            display_value = "••••••••"
        elif field_type == "hidden":
            # Don't display hidden values
            display_value = ""
        elif field_type == "relationship":
            # Display human-readable value for relationship fields
            # Check for enriched display value first (added by _enrich_with_display_values)
            display_field_name = f"_{field_name}_display"

            if display_field_name in form_data:
                # Use enriched display value (e.g., "João Silva" instead of UUID)
                display_value = form_data[display_field_name]
            else:
                # Fallback: show UUID or parse many relationships
                cardinality = field.get("cardinality", "one")

                if cardinality == "many" and value:
                    # Parse JSON array de UUIDs
                    try:
                        items = json.loads(value) if isinstance(value, str) else value
                        if isinstance(items, list):
                            # Exibir labels se disponível, senão UUIDs
                            labels = [
                                (
                                    item.get("label", item.get("record_id", ""))
                                    if isinstance(item, dict)
                                    else str(item)
                                )
                                for item in items
                            ]
                            display_value = ", ".join(labels) if labels else ""
                        else:
                            display_value = value
                    except Exception as e:
                        logger.warning(f"Erro ao parsear relationship many: {e}")
                        display_value = value
                else:
                    display_value = value if value else ""
        else:
            display_value = value

        cells += f"<td>{display_value}</td>\n"

    # Use record_id instead of index for edit/delete links
    cells += f"""<td>
        <form action="/{form_name}/edit/{record_id}" method="get" style="display:inline;">
            <button class="icon-btn edit" title="Editar"><i class="fa fa-pencil-alt"></i></button>
        </form>
        <form action="/{form_name}/delete/{record_id}" method="get" style="display:inline;" onsubmit="return confirm('Confirma exclusão?');">
            <button class="icon-btn delete" title="Excluir"><i class="fa fa-trash"></i></button>
        </form>
    </td>"""

    return f"<tr>{cells}</tr>"


# =============================================================================
# PUBLIC API (only 3 functions)
# =============================================================================


def render_form_fields(
    spec: Dict[str, Any], form_data: Dict[str, Any] = None, include_uuid: bool = False
) -> str:
    """Render all form fields as HTML string.

    Args:
        spec: Form specification
        form_data: Optional data to pre-fill fields
        include_uuid: Whether to include UUID field display (for new records)

    Returns:
        Complete HTML for all form fields

    Example:
        >>> form_html = render_form_fields(spec)
        >>> # Returns HTML with all fields rendered
    """
    fields_html = ""

    # Add UUID display field if requested (for new records)
    if include_uuid and form_data and "_record_id" in form_data:
        uuid_field_html = render_template_string(
            _read_template("fields/uuid_display.html"),
            field_name="_display_record_id",
            field_label="ID do Registro",
            value=form_data["_record_id"],
        )
        # Hidden field to submit the UUID
        hidden_uuid = (
            f'<input type="hidden" name="_record_id" value="{form_data["_record_id"]}">'
        )
        fields_html = hidden_uuid + uuid_field_html
    elif form_data and "_record_id" in form_data:
        # Edit mode: show UUID as read-only
        uuid_field_html = render_template_string(
            _read_template("fields/uuid_display.html"),
            field_name="_record_id",
            field_label="ID do Registro",
            value=form_data["_record_id"],
        )
        fields_html = uuid_field_html

    # Render all spec fields
    for field in spec["fields"]:
        fields_html += _render_field(field, form_data)

    return fields_html


def render_table(
    spec: Dict[str, Any], records: List[Dict[str, Any]], form_name: str
) -> Dict[str, str]:
    """Render complete table (headers + rows).

    Args:
        spec: Form specification
        records: List of record dictionaries
        form_name: Form path for action URLs

    Returns:
        Dictionary with "headers" and "rows" keys containing HTML strings

    Example:
        >>> table = render_table(spec, records, "contatos")
        >>> # Returns {"headers": "<th>...</th>", "rows": "<tr>...</tr>..."}
    """
    headers = _render_table_headers(spec)
    rows = "".join([_render_table_row(record, spec, form_name) for record in records])

    return {"headers": headers, "rows": rows}


def validate_form(spec: Dict[str, Any], form_data: Dict[str, Any]) -> str:
    """Validate form data based on spec. Returns error message or empty string.

    Args:
        spec: Form specification
        form_data: Form data to validate

    Returns:
        Error message string, or empty string if validation passes

    Example:
        >>> error = validate_form(spec, {"name": ""})
        >>> if error:
        >>>     # Handle validation error
    """
    validation_messages = spec.get("validation_messages", {})
    required_fields = [f for f in spec["fields"] if f.get("required", False)]

    # Check if all required fields are empty (excluding relationship fields)
    all_empty = all(
        not form_data.get(f["name"], "").strip()
        for f in required_fields
        if f["type"] != "checkbox"
        and not (f["type"] == "search" and f.get("datasource"))  # Skip relationships
    )

    if all_empty and required_fields:
        return validation_messages.get("all_empty", "Preencha os campos obrigatórios.")

    # Check individual required fields
    for field in required_fields:
        field_name = field["name"]
        field_type = field["type"]

        # Skip validation for relationship fields (search with datasource)
        # Relationships are managed separately and are optional by nature
        if field_type == "search" and field.get("datasource"):
            continue

        if field_type != "checkbox":
            value = form_data.get(field_name, "").strip()
            if not value:
                field_msg = validation_messages.get(
                    field_name, f"O campo {field['label']} é obrigatório."
                )
                return field_msg

    return ""
