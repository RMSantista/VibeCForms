import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    redirect,
    abort,
    jsonify,
)
from dotenv import load_dotenv

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from persistence.factory import RepositoryFactory
from persistence.change_manager import (
    check_form_changes,
    update_form_tracking,
    ChangeManager,
)
from persistence.migration_manager import MigrationManager
from utils.spec_loader import load_spec, set_specs_dir
from services.tag_service import TagService
from services.kanban_service import get_kanban_service

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default fallback directories (src-relative)
DATA_FILE = os.path.join(os.path.dirname(__file__), "registros.txt")
FALLBACK_SPECS_DIR = os.path.join(os.path.dirname(__file__), "specs")
FALLBACK_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Active directories (will be set by initialize_app or default to fallback)
SPECS_DIR = FALLBACK_SPECS_DIR
TEMPLATE_DIR = FALLBACK_TEMPLATE_DIR
BUSINESS_CASE_ROOT = None

# Table column widths (percentage)
TABLE_FIELDS_TOTAL_WIDTH = 60
TABLE_TAGS_WIDTH = 15
TABLE_ACTIONS_WIDTH = 25

# Create app with fallback template directory (will be updated during initialization)
app = Flask(__name__, template_folder=FALLBACK_TEMPLATE_DIR)


def parse_arguments():
    """Parse command-line arguments for business case path."""
    parser = argparse.ArgumentParser(
        description="VibeCForms - AI-first framework for process tracking systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/VibeCForms.py examples/ponto-de-vendas
  python src/VibeCForms.py examples/processo-seletivo
  uv run app examples/demo
        """,
    )
    parser.add_argument(
        "business_case_path",
        help="Path to the business case directory (e.g., examples/ponto-de-vendas)",
    )
    return parser.parse_args()


def initialize_app(business_case_path):
    """Initialize the Flask app with the given business case path.

    Args:
        business_case_path: Path to the business case directory
    """
    global BUSINESS_CASE_ROOT, SPECS_DIR, TEMPLATE_DIR

    # Convert to absolute path
    BUSINESS_CASE_ROOT = os.path.abspath(business_case_path)

    # Validate business case directory exists
    if not os.path.isdir(BUSINESS_CASE_ROOT):
        print(f"Error: Business case directory not found: {BUSINESS_CASE_ROOT}")
        print("\nAvailable examples:")
        examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
        if os.path.isdir(examples_dir):
            for item in os.listdir(examples_dir):
                item_path = os.path.join(examples_dir, item)
                if os.path.isdir(item_path):
                    print(f"  - examples/{item}")
        sys.exit(1)

    # Set up directory paths
    SPECS_DIR = os.path.join(BUSINESS_CASE_ROOT, "specs")
    TEMPLATE_DIR = os.path.join(BUSINESS_CASE_ROOT, "templates")

    # Validate required directories exist
    if not os.path.isdir(SPECS_DIR):
        print(f"Error: specs/ directory not found in {BUSINESS_CASE_ROOT}")
        sys.exit(1)

    # Configure spec loader to use business case specs directory
    set_specs_dir(SPECS_DIR)

    # Template directory is optional (will fallback to src/templates)
    if not os.path.isdir(TEMPLATE_DIR):
        logger.info(f"templates/ not found in business case, using fallback templates")
        TEMPLATE_DIR = FALLBACK_TEMPLATE_DIR

    # Update Flask app template folder
    app.template_folder = TEMPLATE_DIR

    # Initialize persistence configuration with business case config path
    from persistence.config import get_config, reset_config
    from persistence.schema_history import get_history, reset_history

    reset_config()  # Reset any existing config
    reset_history()  # Reset any existing history
    config_path = os.path.join(BUSINESS_CASE_ROOT, "config", "persistence.json")
    history_path = os.path.join(BUSINESS_CASE_ROOT, "config", "schema_history.json")
    get_config(config_path)  # Initialize with business case config
    get_history(history_path)  # Initialize with business case history

    logger.info(f"Initialized VibeCForms with business case: {BUSINESS_CASE_ROOT}")
    logger.info(f"  - Specs: {SPECS_DIR}")
    logger.info(f"  - Templates: {TEMPLATE_DIR}")
    logger.info(f"  - Config: {config_path}")
    logger.info(f"  - History: {history_path}")


def get_template_path(template_name):
    """Get template path with fallback support.

    First tries business case templates, then falls back to src/templates.

    Args:
        template_name: Name of the template file (can include subdirectory, e.g., "fields/input.html")

    Returns:
        Full path to the template file
    """
    # Check business case templates first
    business_template = os.path.join(TEMPLATE_DIR, template_name)
    if os.path.exists(business_template):
        return business_template

    # Fallback to src/templates
    fallback_template = os.path.join(FALLBACK_TEMPLATE_DIR, template_name)
    if os.path.exists(fallback_template):
        return fallback_template

    # Neither exists, return business case path (will fail appropriately)
    return business_template


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
    # Use current SPECS_DIR if base_path not provided
    if base_path is None:
        base_path = SPECS_DIR

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


@app.route("/api/search/contatos")
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


@app.route("/")
def main_page():
    """Display the main landing page."""
    forms = get_all_forms_flat()
    return render_template("index.html", forms=forms)


@app.route("/tags/manager")
def tags_manager():
    """Display the tags management page."""
    forms = get_all_forms_flat()
    menu_items = scan_specs_directory()
    menu_html = generate_menu_html(menu_items, "")
    return render_template("tags_manager.html", forms=forms, menu_html=menu_html)


@app.route("/<path:form_name>", methods=["GET", "POST"])
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


@app.route("/migrate/confirm/<path:form_path>")
def migrate_confirm(form_path):
    """Display migration confirmation page."""
    spec = load_spec(form_path)

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
            f"Migration confirmation: Backend changed for '{form_path}', using historical record count: {record_count}"
        )
    else:
        # No backend change: check current backend for data
        has_data = repo.exists(form_path) and repo.has_data(form_path)

        if has_data:
            try:
                existing_data = repo.read_all(form_path, spec)
                record_count = len(existing_data)
            except Exception as e:
                logger.warning(f"Error reading existing data: {e}")
                has_data = False

    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path, spec=spec, has_data=has_data, record_count=record_count
    )

    # Check if there are any changes requiring confirmation
    if not schema_change and not backend_change:
        # No changes, redirect back to form
        return redirect(f"/{form_path}")

    # Check if confirmation is required
    requires_confirmation = ChangeManager.requires_confirmation(
        schema_change, backend_change
    )

    if not requires_confirmation:
        # No confirmation needed, redirect back to form
        return redirect(f"/{form_path}")

    # Determine if there are destructive changes
    has_destructive_changes = False
    has_warnings = False

    if schema_change:
        from persistence.schema_detector import ChangeType

        for change in schema_change.changes:
            if change.change_type == ChangeType.REMOVE_FIELD:
                has_destructive_changes = True
            if change.change_type == ChangeType.CHANGE_TYPE:
                has_warnings = True

    if backend_change:
        has_warnings = True

    # Render confirmation page
    return render_template(
        "migration_confirm.html",
        form_path=form_path,
        form_title=spec.get("title", form_path),
        record_count=record_count,
        schema_change=schema_change,
        backend_change=backend_change,
        has_destructive_changes=has_destructive_changes,
        has_warnings=has_warnings,
    )


@app.route("/migrate/execute/<path:form_path>", methods=["POST"])
def migrate_execute(form_path):
    """Execute the migration after user confirmation."""
    spec = load_spec(form_path)

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
            f"Backend changed for '{form_path}', using historical record count for migration: {record_count}"
        )
    else:
        # No backend change: check current backend for data
        has_data = repo.exists(form_path) and repo.has_data(form_path)

        if has_data:
            try:
                existing_data = repo.read_all(form_path, spec)
                record_count = len(existing_data)
            except Exception as e:
                logger.warning(f"Error reading existing data: {e}")
                has_data = False

    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path, spec=spec, has_data=has_data, record_count=record_count
    )

    success = True
    error_message = None

    try:
        # Execute backend migration if needed
        if backend_change:
            logger.info(f"Executing backend migration for '{form_path}'...")
            success = MigrationManager.migrate_backend(
                form_path=form_path,
                spec=spec,
                old_backend=backend_change.old_backend,
                new_backend=backend_change.new_backend,
                record_count=record_count,
            )

            if not success:
                error_message = f"Falha na migração de backend: {backend_change.old_backend} → {backend_change.new_backend}"

        # Execute schema migration if needed
        if success and schema_change and schema_change.has_changes():
            logger.info(f"Executing schema migration for '{form_path}'...")

            # Get old spec from history to perform migration
            from persistence.schema_history import get_history

            history = get_history()
            form_history = history.get_form_history(form_path)

            if form_history:
                # We need the old spec, but we don't have it stored
                # For now, we'll let migrate_schema handle it without old spec
                # The individual operations (rename, change_type, remove) will work
                logger.info(
                    f"Schema changes will be applied: {schema_change.get_summary()}"
                )

                # Note: The actual migration will happen automatically on next read_forms call
                # because the spec has changed and change_manager will detect it

        # Update tracking
        if success:
            logger.info(f"Updating form tracking for '{form_path}'...")
            tracking_updated = update_form_tracking(form_path, spec, record_count)
            if tracking_updated:
                logger.info(f"✅ Form tracking updated successfully for '{form_path}'")
            else:
                logger.warning(f"⚠️  Failed to update form tracking for '{form_path}'")
            logger.info(f"✅ Migration completed successfully for '{form_path}'")

    except Exception as e:
        success = False
        error_message = f"Erro durante migração: {str(e)}"
        logger.error(f"❌ Migration error: {error_message}")

    # Redirect back to form with success/error message
    if success:
        logger.info(f"Redirecting to /{form_path}...")
        return redirect(f"/{form_path}")
    else:
        logger.error(f"Migration failed: {error_message}")
        return redirect(f"/{form_path}")


@app.route("/<path:form_name>/edit/<record_id>", methods=["GET", "POST"])
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


@app.route("/<path:form_name>/delete/<record_id>")
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


# Old index-based routes removed - all forms now use UUID-based routes
# Use /<form_name>/edit/<record_id> and /<form_name>/delete/<record_id>


# =============================================================================
# TAG MANAGEMENT API ENDPOINTS (FASE 6 - Phase 3: Tag API & Service Layer)
# =============================================================================

# Initialize TagService
tag_service = TagService()

# Initialize KanbanService
kanban_service = get_kanban_service()


@app.route("/api/<path:form_name>/tags/<record_id>", methods=["POST"])
def api_add_tag(form_name, record_id):
    """
    Add a tag to a record.

    POST /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW
    Body: {"tag": "importante", "applied_by": "user123", "metadata": {"reason": "vip"}}

    Returns:
        JSON response with success status
    """
    try:
        data = request.get_json()
        tag = data.get("tag")
        applied_by = data.get("applied_by", "unknown")
        metadata = data.get("metadata", None)

        if not tag:
            return jsonify({"success": False, "error": "Tag is required"}), 400

        # Validate ID format
        from utils.crockford import validate_id

        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        success = tag_service.add_tag(form_name, record_id, tag, applied_by, metadata)

        if success:
            logger.info(f"Tag '{tag}' added to {form_name}:{record_id} by {applied_by}")
            return jsonify({"success": True, "tag": tag, "record_id": record_id})
        else:
            return (
                jsonify(
                    {"success": False, "error": "Tag already exists or failed to add"}
                ),
                409,
            )

    except Exception as e:
        logger.error(f"Error adding tag: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/<path:form_name>/tags/<record_id>/<tag>", methods=["DELETE"])
def api_remove_tag(form_name, record_id, tag):
    """
    Remove a tag from a record.

    DELETE /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW/importante

    Returns:
        JSON response with success status
    """
    try:
        # Validate ID format
        from utils.crockford import validate_id

        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        # Get removed_by from query param or default to 'unknown'
        removed_by = request.args.get("removed_by", "unknown")

        success = tag_service.remove_tag(form_name, record_id, tag, removed_by)

        if success:
            logger.info(
                f"Tag '{tag}' removed from {form_name}:{record_id} by {removed_by}"
            )
            return jsonify({"success": True, "tag": tag, "record_id": record_id})
        else:
            return jsonify({"success": False, "error": "Tag not found"}), 404

    except Exception as e:
        logger.error(f"Error removing tag: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/<path:form_name>/tags/<record_id>", methods=["GET"])
def api_get_tags(form_name, record_id):
    """
    Get all tags for a record.

    GET /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW

    Returns:
        JSON response with list of tags
    """
    try:
        # Validate ID format
        from utils.crockford import validate_id

        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        tags = tag_service.get_tags(form_name, record_id)

        return jsonify({"success": True, "record_id": record_id, "tags": tags})

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/<path:form_name>/tags/<record_id>/history", methods=["GET"])
def api_get_tag_history(form_name, record_id):
    """
    Get tag history for a record (including removed tags).

    GET /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW/history

    Returns:
        JSON response with full tag history
    """
    try:
        # Validate ID format
        from utils.crockford import validate_id

        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        # Get all tags including removed ones
        tags = tag_service.get_tags(form_name, record_id, active_only=False)

        return jsonify({"success": True, "record_id": record_id, "history": tags})

    except Exception as e:
        logger.error(f"Error getting tag history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/<path:form_name>/search/tags", methods=["GET"])
def api_search_by_tag(form_name):
    """
    Search for objects by tag.

    GET /api/contatos/search/tags?tag=importante

    Returns:
        JSON response with list of object IDs that have the tag
    """
    try:
        tag = request.args.get("tag", "").strip()

        if not tag:
            return (
                jsonify({"success": False, "error": "Tag parameter is required"}),
                400,
            )

        # Get all objects with this tag
        object_ids = tag_service.get_objects_with_tag(form_name, tag)

        # If we need full object data, fetch it from repository
        include_data = request.args.get("include_data", "false").lower() == "true"

        if include_data:
            spec = load_spec(form_name)
            repo = RepositoryFactory.get_repository(form_name)
            objects = []

            for obj_id in object_ids:
                obj_data = repo.read_by_id(form_name, spec, obj_id)
                if obj_data:
                    objects.append(obj_data)

            return jsonify(
                {"success": True, "tag": tag, "count": len(objects), "objects": objects}
            )
        else:
            return jsonify(
                {
                    "success": True,
                    "tag": tag,
                    "count": len(object_ids),
                    "object_ids": object_ids,
                }
            )

    except Exception as e:
        logger.error(f"Error searching by tag: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# KANBAN BOARD ENDPOINTS (FASE 8 - Sistema de Kanban Visual)
# =============================================================================


@app.route("/kanban/<board_name>")
def kanban_board(board_name):
    """
    Display a Kanban board.

    GET /kanban/sales_pipeline

    Returns:
        Rendered Kanban board HTML page
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return f"Board '{board_name}' not found", 404

        # Render kanban template
        return render_template(
            "kanban.html",
            board_name=board_name,
            board_title=board_config.get("title", board_name.replace("_", " ").title()),
            board_config=board_config,
        )

    except Exception as e:
        logger.error(f"Error displaying Kanban board '{board_name}': {e}")
        return f"Error loading board: {str(e)}", 500


@app.route("/api/kanban/boards")
def api_kanban_boards():
    """
    List all available Kanban boards.

    GET /api/kanban/boards

    Returns:
        JSON response with list of boards
    """
    try:
        boards = kanban_service.get_available_boards()

        return jsonify({"success": True, "boards": boards})

    except Exception as e:
        logger.error(f"Error listing Kanban boards: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/kanban/<board_name>/cards")
def api_kanban_cards(board_name):
    """
    Get all cards for a Kanban board organized by columns.

    GET /api/kanban/sales_pipeline/cards

    Returns:
        JSON response with cards organized by column tags
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return (
                jsonify({"success": False, "error": f"Board '{board_name}' not found"}),
                404,
            )

        # Get all cards organized by column
        cards = kanban_service.get_all_board_cards(board_name)

        return jsonify({"success": True, "board": board_name, "cards": cards})

    except Exception as e:
        logger.error(f"Error getting cards for board '{board_name}': {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/kanban/<board_name>/move", methods=["POST"])
def api_kanban_move(board_name):
    """
    Move a card between columns (tag transition).

    POST /api/kanban/sales_pipeline/move
    Body: {
        "record_id": "5FQR8V9JMF8SKT2EGTC90X7G1WW",
        "from_tag": "qualified",
        "to_tag": "proposal",
        "actor": "user123"
    }

    Returns:
        JSON response with success status
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return (
                jsonify({"success": False, "error": f"Board '{board_name}' not found"}),
                404,
            )

        # Get request data
        data = request.get_json()
        record_id = data.get("record_id")
        from_tag = data.get("from_tag")
        to_tag = data.get("to_tag")
        actor = data.get("actor", "unknown")

        # Validate required fields
        if not record_id or not from_tag or not to_tag:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required fields: record_id, from_tag, to_tag",
                    }
                ),
                400,
            )

        # Validate ID format
        from utils.crockford import validate_id

        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        # Validate move is allowed on this board
        if not kanban_service.validate_move(board_name, from_tag, to_tag):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Invalid move: {from_tag} -> {to_tag} not allowed on this board",
                    }
                ),
                400,
            )

        # Get form path from board config
        form_path = board_config.get("form")
        if not form_path:
            return (
                jsonify({"success": False, "error": "Board has no form configured"}),
                500,
            )

        # Move the card
        success = kanban_service.move_card(
            form_path,
            record_id,
            from_tag,
            to_tag,
            actor,
            metadata={"board": board_name},
        )

        if success:
            logger.info(
                f"Card moved on board '{board_name}': {record_id} from {from_tag} to {to_tag} by {actor}"
            )
            return jsonify(
                {
                    "success": True,
                    "record_id": record_id,
                    "from_tag": from_tag,
                    "to_tag": to_tag,
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to move card"}), 500

    except Exception as e:
        logger.error(f"Error moving card on board '{board_name}': {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Initialize app with business case path
    initialize_app(args.business_case_path)

    print(f"Iniciando VibeCForms com business case: {BUSINESS_CASE_ROOT}")
    print("Servidor Flask em http://0.0.0.0:5000 ...")
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        print("Verifique se a porta 5000 está livre ou se há outro serviço rodando.")
