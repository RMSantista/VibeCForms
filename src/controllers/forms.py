"""Forms Controller for VibeCForms

This module contains all form-related routes and support functions.
Routes are organized as a Flask Blueprint for modular architecture.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from flask import (
    Blueprint,
    render_template,
    render_template_string,
    request,
    redirect,
    jsonify,
    current_app,
)

from persistence.factory import RepositoryFactory
from persistence.change_manager import (
    check_form_changes,
    update_form_tracking,
    ChangeManager,
)
from utils.spec_loader import load_spec
from services.tag_service import TagService

logger = logging.getLogger(__name__)

# Create Blueprint
forms_bp = Blueprint("forms", __name__)

# Table column widths (percentage)
TABLE_FIELDS_TOTAL_WIDTH = 60
TABLE_TAGS_WIDTH = 15
TABLE_ACTIONS_WIDTH = 25

# Initialize TagService
tag_service = TagService()


# =============================================================================
# SUPPORT FUNCTIONS
# =============================================================================


def get_template_path(template_name):
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


def read_template(template_name):
    """Read template content with fallback support.

    Args:
        template_name: Name of the template file (can include subdirectory)

    Returns:
        Template content as string
    """
    template_path = get_template_path(template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def get_folder_icon(folder_name):
    """Get an intuitive icon for a folder based on its name."""
    icons = {
        "financeiro": "fa-dollar-sign",
        "rh": "fa-users",
        "departamentos": "fa-sitemap",
        "vendas": "fa-shopping-cart",
        "estoque": "fa-boxes",
        "clientes": "fa-user-tie",
        "relatorios": "fa-chart-bar",
        "configuracoes": "fa-cog",
    }
    return icons.get(folder_name.lower(), "fa-folder")


def load_folder_config(folder_path: str) -> Optional[Dict[str, Any]]:
    """Load folder configuration from _folder.json if it exists.

    Args:
        folder_path: Full path to the folder

    Returns:
        Dictionary with config or None if file doesn't exist
    """
    config_path = os.path.join(folder_path, "_folder.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config {config_path}: {e}")
            return None
        except PermissionError as e:
            logger.error(f"Permission denied reading {config_path}: {e}")
            return None
    return None


def scan_specs_directory(base_path=None, relative_path=""):
    """Recursively scan the specs directory and build menu structure.

    Returns a list of menu items, where each item is either:
    - {"type": "form", "name": str, "path": str, "title": str, "icon": str}
    - {"type": "folder", "name": str, "path": str, "icon": str, "children": list, "description": str (optional)}
    """
    # Use specs directory from app config if base_path not provided
    if base_path is None:
        try:
            # Try to get from Flask app context first
            specs_dir = current_app.config.get("SPECS_DIR")
        except RuntimeError:
            # If no app context, fall back to global variable (for tests)
            from src import VibeCForms

            specs_dir = VibeCForms.SPECS_DIR
        base_path = specs_dir

    items = []
    full_path = os.path.join(base_path, relative_path) if relative_path else base_path

    if not os.path.exists(full_path):
        return items

    # Get all items in directory
    entries = sorted(os.listdir(full_path))

    for entry in entries:
        # Skip folder config files
        if entry == "_folder.json":
            continue

        entry_path = os.path.join(full_path, entry)
        relative_entry_path = (
            os.path.join(relative_path, entry) if relative_path else entry
        )

        if os.path.isdir(entry_path):
            # It's a folder - recursively scan it
            children = scan_specs_directory(base_path, relative_entry_path)
            if children:  # Only add folder if it has content
                # Try to load folder configuration
                folder_config = load_folder_config(entry_path)

                if folder_config:
                    # Use config values
                    folder_item = {
                        "type": "folder",
                        "name": folder_config.get("name", entry.capitalize()),
                        "path": relative_entry_path,
                        "icon": folder_config.get("icon", get_folder_icon(entry)),
                        "children": children,
                    }
                    # Add description if present
                    if "description" in folder_config:
                        folder_item["description"] = folder_config["description"]
                    # Add order if present
                    if "order" in folder_config:
                        folder_item["order"] = folder_config["order"]
                else:
                    # Fallback to default behavior
                    folder_item = {
                        "type": "folder",
                        "name": entry.capitalize(),
                        "path": relative_entry_path,
                        "icon": get_folder_icon(entry),
                        "children": children,
                    }

                items.append(folder_item)

        elif entry.endswith(".json"):
            # It's a form spec file
            form_name = entry[:-5]  # Remove .json extension
            form_path = (
                os.path.join(relative_path, form_name) if relative_path else form_name
            )

            try:
                spec = load_spec(form_path)
                # Read icon from spec (optional field)
                icon = spec.get("icon", "")

                # Fallback: root level forms without icon get default
                if not icon and not relative_path:
                    icon = "fa-file-alt"

                items.append(
                    {
                        "type": "form",
                        "name": form_name,
                        "path": form_path,
                        "title": spec.get("title", form_name.capitalize()),
                        "icon": icon,
                    }
                )
            except Exception:
                # Skip invalid spec files
                continue

    # Sort items by order field if present, then by name
    items.sort(key=lambda x: (x.get("order", 999), x.get("name", "")))

    return items


def get_all_forms_flat(menu_items=None, prefix=""):
    """Flatten the hierarchical menu structure to get all forms.

    Returns a list of all form items with their full path and category.
    Each item: {"title": str, "path": str, "icon": str, "category": str}
    """
    if menu_items is None:
        menu_items = scan_specs_directory()

    forms = []

    for item in menu_items:
        if item["type"] == "form":
            category = prefix if prefix else "Geral"

            # Get icon from item (already resolved in scan_specs_directory)
            icon = item.get("icon", "fa-file-alt")

            forms.append(
                {
                    "title": item["title"],
                    "path": item["path"],
                    "icon": icon,
                    "category": category,
                }
            )
        elif item["type"] == "folder":
            # Recursively get forms from folder
            folder_name = item["name"]
            nested_forms = get_all_forms_flat(item["children"], folder_name)
            forms.extend(nested_forms)

    return forms


def read_forms(spec: Dict[str, Any], form_path: str) -> List[Dict[str, Any]]:
    """Read forms using configured persistence backend.

    Args:
        spec: Form specification
        form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')

    Returns:
        List of form data dictionaries
    """
    from persistence.schema_history import get_history
    from persistence.config import get_config

    # Check if backend has changed by comparing history with current config
    history = get_history()
    form_history = history.get_form_history(form_path)

    config = get_config()
    current_backend_config = config.get_backend_config(form_path)
    current_backend = current_backend_config.get("type")

    last_backend = history.get_last_backend(form_path)
    backend_changed = last_backend and last_backend != current_backend

    # Get repository for current (new) backend
    repo = RepositoryFactory.get_repository(form_path)

    # Check if storage exists and has data
    has_data = False
    record_count = 0

    if backend_changed and form_history:
        # Backend changed: use record count from history (reflects data in old backend)
        record_count = form_history.get("record_count", 0)
        has_data = record_count > 0
        logger.info(
            f"Backend changed for '{form_path}', using historical record count: {record_count}"
        )
    else:
        # No backend change: check current backend for data
        has_data = repo.exists(form_path) and repo.has_data(form_path)

        if has_data:
            try:
                existing_data = repo.read_all(form_path, spec)
                record_count = len(existing_data)
            except Exception as e:
                logger.warning(f"Error reading existing data for change detection: {e}")
                has_data = False

    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path, spec=spec, has_data=has_data, record_count=record_count
    )

    # Check if changes require user confirmation
    if schema_change or backend_change:
        if schema_change and schema_change.has_changes():
            logger.info(
                f"Schema changes detected for '{form_path}': "
                f"{schema_change.get_summary()}"
            )

        if backend_change:
            logger.info(
                f"Backend change detected for '{form_path}': "
                f"{backend_change.old_backend} -> {backend_change.new_backend}"
            )

        # Redirect to confirmation UI if changes require confirmation
        requires_confirmation = ChangeManager.requires_confirmation(
            schema_change, backend_change
        )
        if requires_confirmation:
            logger.info(f"Redirecting to migration confirmation for '{form_path}'")
            # Use Flask's redirect - this will be caught by the caller
            from flask import redirect as flask_redirect

            raise Exception(f"MIGRATION_REQUIRED:{form_path}")

    # Auto-create storage if it doesn't exist
    if not repo.exists(form_path):
        repo.create_storage(form_path, spec)

    # Read data
    data = repo.read_all(form_path, spec)

    # Update tracking after successful read
    update_form_tracking(form_path, spec, len(data))

    return data


def write_forms(forms, spec, form_path):
    """Write forms using configured persistence backend.

    Args:
        forms: List of form data dictionaries
        spec: Form specification
        form_path: Path to the form (e.g., 'contatos', 'financeiro/contas')
    """
    repo = RepositoryFactory.get_repository(form_path)

    # Auto-create storage if it doesn't exist
    if not repo.exists(form_path):
        repo.create_storage(form_path, spec)

    # Clear all existing records
    current = repo.read_all(form_path, spec)
    for i in range(len(current)):
        repo.delete(form_path, spec, 0)  # Always delete the first record

    # Insert new records
    for form_data in forms:
        repo.create(form_path, spec, form_data)


def generate_form_field(field, form_data=None):
    """Generate HTML for a single form field based on spec using templates."""
    field_name = field["name"]
    field_label = field["label"]
    field_type = field["type"]
    required = field.get("required", False)

    value = ""
    if form_data:
        value = form_data.get(field_name, "")

    if field_type == "checkbox":
        template_content = read_template("fields/checkbox.html")
        checked = form_data and form_data.get(field_name)
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            checked=checked,
        )

    elif field_type == "textarea":
        template_content = read_template("fields/textarea.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
        )

    elif field_type == "select":
        template_content = read_template("fields/select.html")
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
        template_content = read_template("fields/radio.html")
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
        template_content = read_template("fields/color.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
        )

    elif field_type == "range":
        template_content = read_template("fields/range.html")
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
        template_content = read_template("fields/search_autocomplete.html")
        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            required=required,
            value=value,
        )

    else:
        # Input types: text, tel, email, number, password, date, url, search, datetime-local, time, month, week, hidden
        template_content = read_template("fields/input.html")
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

        return render_template_string(
            template_content,
            field_name=field_name,
            field_label=field_label,
            input_type=input_type,
            required=required,
            value=value,
        )


def generate_table_headers(spec: Dict[str, Any]) -> str:
    """Generate table headers from spec."""
    headers = ""

    # Tags column first (TABLE_TAGS_WIDTH% width) - no title
    headers += f'<th style="width: {TABLE_TAGS_WIDTH}%;"></th>\n'

    # Calculate width for fields (TABLE_FIELDS_TOTAL_WIDTH% total, divided by number of fields)
    num_fields = len(spec["fields"])
    col_width = (
        int(TABLE_FIELDS_TOTAL_WIDTH / num_fields)
        if num_fields > 0
        else TABLE_FIELDS_TOTAL_WIDTH
    )

    for field in spec["fields"]:
        headers += f'<th style="width: {col_width}%;">{field["label"]}</th>\n'

    # Actions column (TABLE_ACTIONS_WIDTH% width)
    headers += f'<th style="width: {TABLE_ACTIONS_WIDTH}%;">Ações</th>'
    return headers


def generate_table_row(
    form_data: Dict[str, Any], spec: Dict[str, Any], form_name: str
) -> str:
    """
    Generate a table row from form data.

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


def validate_form_data(spec, form_data):
    """Validate form data based on spec. Returns error message or empty string."""
    validation_messages = spec.get("validation_messages", {})
    required_fields = [f for f in spec["fields"] if f.get("required", False)]

    # Check if all required fields are empty
    all_empty = all(
        not form_data.get(f["name"], "").strip()
        for f in required_fields
        if f["type"] != "checkbox"
    )

    if all_empty and required_fields:
        return validation_messages.get("all_empty", "Preencha os campos obrigatórios.")

    # Check individual required fields
    for field in required_fields:
        field_name = field["name"]
        field_type = field["type"]

        if field_type != "checkbox":
            value = form_data.get(field_name, "").strip()
            if not value:
                field_msg = validation_messages.get(
                    field_name, f"O campo {field['label']} é obrigatório."
                )
                return field_msg

    return ""


def generate_menu_html(menu_items, current_form_path="", level=0):
    """Generate HTML for menu items recursively with submenu support.

    Args:
        menu_items: List of menu items from scan_specs_directory()
        current_form_path: Current form path to highlight active items
        level: Nesting level (0 = root)
    """
    if not menu_items:
        return ""

    html = ""
    for item in menu_items:
        if item["type"] == "form":
            # Form item
            is_active = item["path"] == current_form_path
            active_class = "active" if is_active else ""
            icon_html = f'<i class="fa {item["icon"]}"></i> ' if item["icon"] else ""

            html += f'<li><a href="/{item["path"]}" class="{active_class}">{icon_html}{item["title"]}</a></li>\n'

        elif item["type"] == "folder":
            # Folder item with submenu
            # Check if any child is active
            is_path_active = current_form_path.startswith(item["path"])
            icon_html = f'<i class="fa {item["icon"]}"></i> '

            html += f"""<li class="has-submenu">
                <a href="javascript:void(0)" class="folder-item {'active-path' if is_path_active else ''}">
                    {icon_html}{item["name"]}
                    <i class="fa fa-chevron-right submenu-arrow"></i>
                </a>
                <ul class="submenu level-{level + 1}">
                    {generate_menu_html(item["children"], current_form_path, level + 1)}
                </ul>
            </li>\n"""

    return html


# =============================================================================
# ROUTES
# =============================================================================


@forms_bp.route("/")
def main_page():
    """Display the main landing page."""
    forms = get_all_forms_flat()
    return render_template("index.html", forms=forms)


@forms_bp.route("/api/search/contatos")
def api_search_contatos():
    """API endpoint to search contacts by name."""
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify([])

    try:
        contatos_spec = load_spec("contatos")
    except:
        return jsonify([])

    forms = read_forms(contatos_spec, "contatos")

    # Filter contacts by name (case-insensitive substring match)
    results = []
    for form in forms:
        nome = form.get("nome", "").lower()
        if query in nome:
            results.append(form.get("nome", ""))

    return jsonify(results)


@forms_bp.route("/<path:form_name>", methods=["GET", "POST"])
def index(form_name):
    spec = load_spec(form_name)
    error = ""

    # Generate dynamic menu
    menu_items = scan_specs_directory()
    menu_html = generate_menu_html(menu_items, form_name)

    if request.method == "POST":
        # Collect form data
        form_data = {}
        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]

            if field_type == "checkbox":
                form_data[field_name] = field_name in request.form
            else:
                form_data[field_name] = request.form.get(field_name, "").strip()

        # Include the pre-generated UUID from hidden field
        if "_record_id" in request.form:
            form_data["_record_id"] = request.form.get("_record_id")

        # Validate
        error = validate_form_data(spec, form_data)

        if error:
            # Re-render with error and preserve form data
            try:
                forms = read_forms(spec, form_name)
            except Exception as e:
                # Check if migration is required
                if str(e).startswith("MIGRATION_REQUIRED:"):
                    form_path = str(e).split(":", 1)[1]
                    return redirect(f"/migrate/confirm/{form_path}")
                raise

            form_fields = "".join(
                [generate_form_field(f, form_data) for f in spec["fields"]]
            )
            table_headers = generate_table_headers(spec)
            table_rows = "".join(
                [generate_table_row(form, spec, form_name) for form in forms]
            )

            return render_template(
                "form.html",
                title=spec["title"],
                form_name=form_name,
                menu_html=menu_html,
                error=error,
                form_fields=form_fields,
                table_headers=table_headers,
                table_rows=table_rows,
            )

        # Save the form
        try:
            # Use repository directly to create new record
            repo = RepositoryFactory.get_repository(form_name)

            # Auto-create storage if it doesn't exist
            if not repo.exists(form_name):
                repo.create_storage(form_name, spec)

            # Create the new record
            record_id = repo.create(form_name, spec, form_data)

            if record_id:
                logger.info(f"Created new record {record_id} in {form_name}")

                # Apply default tags if configured in spec
                default_tags = spec.get("default_tags", [])
                if default_tags:
                    for tag in default_tags:
                        success = tag_service.add_tag(
                            form_name,
                            record_id,
                            tag,
                            applied_by="system",
                            metadata={"auto_applied": True, "source": "default_tags"},
                        )
                        if success:
                            logger.info(
                                f"Auto-applied default tag '{tag}' to {record_id}"
                            )
                        else:
                            logger.warning(
                                f"Failed to auto-apply tag '{tag}' to {record_id}"
                            )
            else:
                logger.error(f"Failed to create record in {form_name}")

            # Update tracking
            update_form_tracking(form_name, spec, len(repo.read_all(form_name, spec)))

        except Exception as e:
            # Check if migration is required
            if str(e).startswith("MIGRATION_REQUIRED:"):
                form_path = str(e).split(":", 1)[1]
                return redirect(f"/migrate/confirm/{form_path}")
            raise

        return redirect(f"/{form_name}")

    # GET request - show the form
    try:
        forms = read_forms(spec, form_name)
    except Exception as e:
        # Check if migration is required
        if str(e).startswith("MIGRATION_REQUIRED:"):
            form_path = str(e).split(":", 1)[1]
            return redirect(f"/migrate/confirm/{form_path}")
        raise

    # Generate UUID for new record (will be submitted with form)
    from utils.crockford import generate_id

    new_record_id = generate_id()

    # Hidden field to submit the UUID
    hidden_uuid = f'<input type="hidden" name="_record_id" value="{new_record_id}">'

    # Visible UUID display (disabled, read-only)
    uuid_field_html = render_template_string(
        read_template("fields/uuid_display.html"),
        field_name="_display_record_id",
        field_label="ID do Registro",
        value=new_record_id,
    )

    form_fields = (
        hidden_uuid
        + uuid_field_html
        + "".join([generate_form_field(f) for f in spec["fields"]])
    )
    table_headers = generate_table_headers(spec)
    table_rows = "".join([generate_table_row(form, spec, form_name) for form in forms])

    return render_template(
        "form.html",
        title=spec["title"],
        form_name=form_name,
        menu_html=menu_html,
        error="",
        form_fields=form_fields,
        table_headers=table_headers,
        table_rows=table_rows,
        default_tags=spec.get("default_tags", []),
    )


@forms_bp.route("/<path:form_name>/edit/<record_id>", methods=["GET", "POST"])
def edit(form_name, record_id):
    """
    Edit a record by UUID.

    Args:
        form_name: Path to the form
        record_id: 27-character Crockford Base32 UUID of the record
    """
    # Validate ID format (27 characters, valid Crockford Base32)
    from utils.crockford import validate_id

    if not validate_id(record_id):
        return "ID inválido (formato ou checksum incorreto)", 400

    spec = load_spec(form_name)
    error = ""

    # Generate dynamic menu
    menu_items = scan_specs_directory()
    menu_html = generate_menu_html(menu_items, form_name)

    # Get repository
    repo = RepositoryFactory.get_repository(form_name)

    # Read the record by ID
    record = repo.read_by_id(form_name, spec, record_id)
    if not record:
        return "Registro não encontrado", 404

    # Load current tags for display
    record_tags = tag_service.get_tags(form_name, record_id, active_only=True)

    if request.method == "POST":
        # Collect form data
        form_data = {}
        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]

            if field_type == "checkbox":
                form_data[field_name] = field_name in request.form
            else:
                form_data[field_name] = request.form.get(field_name, "").strip()

        # Validate
        error = validate_form_data(spec, form_data)

        if error:
            # Re-render with error
            # Generate UUID field display
            uuid_field_html = render_template_string(
                read_template("fields/uuid_display.html"),
                field_name="_record_id",
                field_label="ID do Registro",
                value=record_id,
            )

            form_fields = uuid_field_html + "".join(
                [generate_form_field(f, form_data) for f in spec["fields"]]
            )
            return render_template(
                "edit.html",
                title=spec["title"],
                form_name=form_name,
                menu_html=menu_html,
                error=error,
                form_fields=form_fields,
                record_id=record_id,
                record_tags=record_tags,
            )

        # Update the record by ID
        success = repo.update_by_id(form_name, spec, record_id, form_data)

        if success:
            logger.info(f"Updated record {record_id} in {form_name}")
        else:
            logger.error(f"Failed to update record {record_id} in {form_name}")

        return redirect(f"/{form_name}")

    # GET request - show edit form
    # Generate UUID field display with actual ID
    uuid_field_html = render_template_string(
        read_template("fields/uuid_display.html"),
        field_name="_record_id",
        field_label="ID do Registro",
        value=record_id,
    )

    form_fields = uuid_field_html + "".join(
        [generate_form_field(f, record) for f in spec["fields"]]
    )

    return render_template(
        "edit.html",
        title=spec["title"],
        form_name=form_name,
        menu_html=menu_html,
        error="",
        form_fields=form_fields,
        record_id=record_id,
        record_tags=record_tags,
    )


@forms_bp.route("/<path:form_name>/delete/<record_id>")
def delete(form_name, record_id):
    """
    Delete a record by UUID.

    Args:
        form_name: Path to the form
        record_id: 27-character Crockford Base32 UUID of the record
    """
    # Validate ID format (27 characters, valid Crockford Base32)
    from utils.crockford import validate_id

    if not validate_id(record_id):
        return "ID inválido (formato ou checksum incorreto)", 400

    spec = load_spec(form_name)

    # Get repository
    repo = RepositoryFactory.get_repository(form_name)

    # Verify record exists by trying to read it
    record = repo.read_by_id(form_name, spec, record_id)
    if not record:
        return "Registro não encontrado", 404

    # Delete the record by ID
    success = repo.delete_by_id(form_name, spec, record_id)

    if success:
        logger.info(f"Deleted record {record_id} from {form_name}")
    else:
        logger.error(f"Failed to delete record {record_id} from {form_name}")

    return redirect(f"/{form_name}")
