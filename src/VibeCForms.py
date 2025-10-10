import os
import json
from flask import Flask, render_template, request, redirect, abort
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "registros.txt")
SPECS_DIR = os.path.join(os.path.dirname(__file__), "specs")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)


def load_spec(form_path):
    """Load and validate a form specification file.

    Args:
        form_path: Path to form (can include subdirectories, e.g., 'financeiro/contas')
    """
    spec_path = os.path.join(SPECS_DIR, f"{form_path}.json")
    if not os.path.exists(spec_path):
        abort(404, description=f"Form specification '{form_path}' not found")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Validate required spec fields
    if "title" not in spec or "fields" not in spec:
        abort(500, description=f"Invalid spec file for '{form_path}'")

    return spec


def get_data_file(form_path):
    """Get the data file path for a given form.

    Args:
        form_path: Path to form (can include subdirectories, e.g., 'financeiro/contas')
    """
    # Replace slashes with underscores for flat file storage
    safe_name = form_path.replace("/", "_")
    return os.path.join(os.path.dirname(__file__), f"{safe_name}.txt")


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


def load_folder_config(folder_path):
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
        except Exception:
            return None
    return None


def scan_specs_directory(base_path=SPECS_DIR, relative_path=""):
    """Recursively scan the specs directory and build menu structure.

    Returns a list of menu items, where each item is either:
    - {"type": "form", "name": str, "path": str, "title": str, "icon": str}
    - {"type": "folder", "name": str, "path": str, "icon": str, "children": list, "description": str (optional)}
    """
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
        relative_entry_path = os.path.join(relative_path, entry) if relative_path else entry

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
                        "children": children
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
                        "children": children
                    }

                items.append(folder_item)

        elif entry.endswith(".json"):
            # It's a form spec file
            form_name = entry[:-5]  # Remove .json extension
            form_path = os.path.join(relative_path, form_name) if relative_path else form_name

            try:
                spec = load_spec(form_path)
                # Read icon from spec (optional field)
                icon = spec.get("icon", "")

                # Fallback: root level forms without icon get default
                if not icon and not relative_path:
                    icon = "fa-file-alt"

                items.append({
                    "type": "form",
                    "name": form_name,
                    "path": form_path,
                    "title": spec.get("title", form_name.capitalize()),
                    "icon": icon
                })
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

            forms.append({
                "title": item["title"],
                "path": item["path"],
                "icon": icon,
                "category": category
            })
        elif item["type"] == "folder":
            # Recursively get forms from folder
            folder_name = item["name"]
            nested_forms = get_all_forms_flat(item["children"], folder_name)
            forms.extend(nested_forms)

    return forms


def read_forms(spec, data_file):
    """Read forms from data file based on spec definition."""
    if not os.path.exists(data_file):
        return []

    with open(data_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    forms = []
    field_names = [field["name"] for field in spec["fields"]]

    for line in lines:
        if not line.strip():
            continue
        values = line.strip().split(";")
        if len(values) != len(field_names):
            continue  # Skip malformed lines

        form_data = {}
        for i, field in enumerate(spec["fields"]):
            field_name = field["name"]
            field_type = field["type"]
            value = values[i]

            # Convert value based on field type
            if field_type == "checkbox":
                form_data[field_name] = value == "True"
            elif field_type == "number":
                try:
                    form_data[field_name] = int(value) if value else 0
                except ValueError:
                    form_data[field_name] = 0
            else:
                form_data[field_name] = value

        forms.append(form_data)

    return forms


def write_forms(forms, spec, data_file):
    """Write forms to data file based on spec definition."""
    with open(data_file, "w", encoding="utf-8") as f:
        for form_data in forms:
            values = []
            for field in spec["fields"]:
                field_name = field["name"]
                value = form_data.get(field_name, "")

                # Convert value to string for storage
                if isinstance(value, bool):
                    values.append(str(value))
                else:
                    values.append(str(value))

            f.write(";".join(values) + "\n")


def generate_form_field(field, form_data=None):
    """Generate HTML for a single form field based on spec."""
    field_name = field["name"]
    field_label = field["label"]
    field_type = field["type"]
    required = field.get("required", False)

    value = ""
    if form_data:
        value = form_data.get(field_name, "")

    if field_type == "checkbox":
        checked = "checked" if (form_data and form_data.get(field_name)) else ""
        return f"""
        <div class="form-row">
            <label for="{field_name}">{field_label}:</label>
            <input type="checkbox" name="{field_name}" id="{field_name}" {checked}>
        </div>"""
    elif field_type == "textarea":
        required_attr = "required" if required else ""
        return f"""
        <div class="form-row">
            <label for="{field_name}">{field_label}:</label>
            <textarea name="{field_name}" id="{field_name}" {required_attr}>{value}</textarea>
        </div>"""
    else:
        required_attr = "required" if required else ""
        input_type = (
            field_type if field_type in ["text", "tel", "email", "number"] else "text"
        )
        return f"""
        <div class="form-row">
            <label for="{field_name}">{field_label}:</label>
            <input type="{input_type}" name="{field_name}" id="{field_name}" {required_attr} value="{value}">
        </div>"""


def generate_table_headers(spec):
    """Generate table headers from spec."""
    headers = ""
    num_fields = len(spec["fields"])
    col_width = int(75 / num_fields)  # Reserve 25% for actions

    for field in spec["fields"]:
        headers += f'<th style="width: {col_width}%;">{field["label"]}</th>\n'

    headers += '<th style="width: 25%;">Ações</th>'
    return headers


def generate_table_row(form_data, spec, idx, form_name):
    """Generate a table row from form data."""
    cells = ""

    for field in spec["fields"]:
        field_name = field["name"]
        field_type = field["type"]
        value = form_data.get(field_name, "")

        if field_type == "checkbox":
            display_value = "Sim" if value else "Não"
        else:
            display_value = value

        cells += f"<td>{display_value}</td>\n"

    cells += f"""<td>
        <form action="/{form_name}/edit/{idx}" method="get" style="display:inline;">
            <button class="icon-btn edit" title="Editar"><i class="fa fa-pencil-alt"></i></button>
        </form>
        <form action="/{form_name}/delete/{idx}" method="get" style="display:inline;" onsubmit="return confirm('Confirma exclusão?');">
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
            is_active = (item["path"] == current_form_path)
            active_class = "active" if is_active else ""
            icon_html = f'<i class="fa {item["icon"]}"></i> ' if item["icon"] else ""

            html += f'<li><a href="/{item["path"]}" class="{active_class}">{icon_html}{item["title"]}</a></li>\n'

        elif item["type"] == "folder":
            # Folder item with submenu
            # Check if any child is active
            is_path_active = current_form_path.startswith(item["path"])
            icon_html = f'<i class="fa {item["icon"]}"></i> '

            html += f'''<li class="has-submenu">
                <a href="javascript:void(0)" class="folder-item {'active-path' if is_path_active else ''}">
                    {icon_html}{item["name"]}
                    <i class="fa fa-chevron-right submenu-arrow"></i>
                </a>
                <ul class="submenu level-{level + 1}">
                    {generate_menu_html(item["children"], current_form_path, level + 1)}
                </ul>
            </li>\n'''

    return html


@app.route("/")
def main_page():
    """Display the main landing page."""
    forms = get_all_forms_flat()
    return render_template('index.html', forms=forms)


@app.route("/<path:form_name>", methods=["GET", "POST"])
def index(form_name):
    spec = load_spec(form_name)
    data_file = get_data_file(form_name)
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

        # Validate
        error = validate_form_data(spec, form_data)

        if error:
            # Re-render with error and preserve form data
            forms = read_forms(spec, data_file)
            form_fields = "".join(
                [generate_form_field(f, form_data) for f in spec["fields"]]
            )
            table_headers = generate_table_headers(spec)
            table_rows = "".join(
                [
                    generate_table_row(forms[i], spec, i, form_name)
                    for i in range(len(forms))
                ]
            )

            return render_template(
                'form.html',
                title=spec["title"],
                form_name=form_name,
                menu_html=menu_html,
                error=error,
                form_fields=form_fields,
                table_headers=table_headers,
                table_rows=table_rows,
            )

        # Save the form
        forms = read_forms(spec, data_file)
        forms.append(form_data)
        write_forms(forms, spec, data_file)
        return redirect(f"/{form_name}")

    # GET request - show the form
    forms = read_forms(spec, data_file)
    form_fields = "".join([generate_form_field(f) for f in spec["fields"]])
    table_headers = generate_table_headers(spec)
    table_rows = "".join(
        [generate_table_row(forms[i], spec, i, form_name) for i in range(len(forms))]
    )

    return render_template(
        'form.html',
        title=spec["title"],
        form_name=form_name,
        menu_html=menu_html,
        error="",
        form_fields=form_fields,
        table_headers=table_headers,
        table_rows=table_rows,
    )




@app.route("/<path:form_name>/edit/<int:idx>", methods=["GET", "POST"])
def edit(form_name, idx):
    spec = load_spec(form_name)
    data_file = get_data_file(form_name)
    forms = read_forms(spec, data_file)
    error = ""

    # Generate dynamic menu
    menu_items = scan_specs_directory()
    menu_html = generate_menu_html(menu_items, form_name)

    if idx < 0 or idx >= len(forms):
        return "Formulário não encontrado", 404

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
            form_fields = "".join(
                [generate_form_field(f, form_data) for f in spec["fields"]]
            )
            return render_template(
                'edit.html',
                title=spec["title"],
                form_name=form_name,
                menu_html=menu_html,
                error=error,
                form_fields=form_fields,
            )

        # Update the form
        forms[idx] = form_data
        write_forms(forms, spec, data_file)
        return redirect(f"/{form_name}")

    # GET request - show edit form
    form_fields = "".join([generate_form_field(f, forms[idx]) for f in spec["fields"]])

    return render_template(
        'edit.html',
        title=spec["title"],
        form_name=form_name,
        menu_html=menu_html,
        error="",
        form_fields=form_fields,
    )


@app.route("/<path:form_name>/delete/<int:idx>")
def delete(form_name, idx):
    spec = load_spec(form_name)
    data_file = get_data_file(form_name)
    forms = read_forms(spec, data_file)

    if idx < 0 or idx >= len(forms):
        return "Formulário não encontrado", 404

    forms.pop(idx)
    write_forms(forms, spec, data_file)
    return redirect(f"/{form_name}")


# Keep old routes for backward compatibility
@app.route("/edit/<int:idx>", methods=["GET", "POST"])
def old_edit(idx):
    return redirect(f"/contatos/edit/{idx}")


@app.route("/delete/<int:idx>")
def old_delete(idx):
    return redirect(f"/contatos/delete/{idx}")


if __name__ == "__main__":
    print("Iniciando servidor Flask em http://0.0.0.0:5000 ...")
    print("Formulários disponíveis: http://0.0.0.0:5000/contatos")
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        print("Verifique se a porta 5000 está livre ou se há outro serviço rodando.")
