import os
import json
from flask import Flask, render_template_string, request, redirect, abort
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "registros.txt")
SPECS_DIR = os.path.join(os.path.dirname(__file__), "specs")

app = Flask(__name__)


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


def scan_specs_directory(base_path=SPECS_DIR, relative_path=""):
    """Recursively scan the specs directory and build menu structure.

    Returns a list of menu items, where each item is either:
    - {"type": "form", "name": str, "path": str, "title": str, "icon": str}
    - {"type": "folder", "name": str, "path": str, "icon": str, "children": list}
    """
    items = []
    full_path = os.path.join(base_path, relative_path) if relative_path else base_path

    if not os.path.exists(full_path):
        return items

    # Get all items in directory
    entries = sorted(os.listdir(full_path))

    for entry in entries:
        entry_path = os.path.join(full_path, entry)
        relative_entry_path = os.path.join(relative_path, entry) if relative_path else entry

        if os.path.isdir(entry_path):
            # It's a folder - recursively scan it
            children = scan_specs_directory(base_path, relative_entry_path)
            if children:  # Only add folder if it has content
                items.append({
                    "type": "folder",
                    "name": entry.capitalize(),
                    "path": relative_entry_path,
                    "icon": get_folder_icon(entry),
                    "children": children
                })
        elif entry.endswith(".json"):
            # It's a form spec file
            form_name = entry[:-5]  # Remove .json extension
            form_path = os.path.join(relative_path, form_name) if relative_path else form_name

            try:
                spec = load_spec(form_path)
                # Root level forms get icons, nested forms don't
                icon = ""
                if not relative_path:  # Root level
                    if form_name == "contatos":
                        icon = "fa-address-book"
                    elif form_name == "produtos":
                        icon = "fa-box"
                    else:
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

            # Try to get a better icon for nested forms
            icon = item.get("icon", "")
            if not icon:
                # Assign default icon based on category
                if "financeiro" in item["path"].lower():
                    icon = "fa-dollar-sign"
                elif "rh" in item["path"].lower():
                    icon = "fa-users"
                else:
                    icon = "fa-file-alt"

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


def get_main_template():
    """Return the main page template with dynamic form generation."""
    return """
    <html>
    <head>
        <title>{{ title }}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .layout { display: flex; min-height: 100vh; }
            .sidebar { width: 250px; background: #2c3e50; color: #fff; padding: 20px 0; position: fixed; height: 100vh; z-index: 1000; display: flex; flex-direction: column; }
            .sidebar-header { padding: 0 20px 20px; border-bottom: 1px solid #34495e; margin-bottom: 20px; flex-shrink: 0; }
            .sidebar-header h1 { font-size: 24px; font-style: italic; margin: 0; color: #3498db; }
            .sidebar-header p { font-size: 12px; margin: 5px 0 0; color: #95a5a6; }
            .menu-container { flex: 1; overflow-y: auto; position: relative; }
            .menu { list-style: none; padding: 0; margin: 0; }
            .menu li { margin: 0; position: static; }
            .menu a { display: flex; align-items: center; gap: 12px; padding: 15px 20px; color: #ecf0f1; text-decoration: none; transition: all 0.2s; white-space: nowrap; }
            .menu a:hover { background: #34495e; color: #3498db; }
            .menu a.active { background: #3498db; color: #fff; }
            .menu a.active-path { background: #34495e; }
            .menu a i { font-size: 18px; width: 20px; text-align: center; }
            .submenu-arrow { font-size: 12px !important; margin-left: auto; }
            .has-submenu { position: relative; }
            .submenu { list-style: none; padding: 0; margin: 0; position: fixed; left: 250px; background: #34495e; min-width: 220px; width: auto; box-shadow: 4px 4px 12px rgba(0,0,0,0.4); display: none; z-index: 2000; border-radius: 4px; }
            .has-submenu:hover > .submenu { display: block; }
            .submenu li { position: static; }
            .submenu li a { padding: 12px 20px; font-size: 14px; white-space: nowrap; }
            .level-2 { background: #2c3e50; }
            .level-3 { background: #1a252f; }
            .main-content { margin-left: 250px; flex: 1; padding: 40px; position: relative; z-index: 1; }
            .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; position: relative; z-index: 1; }
            h2 { text-align: center; margin-bottom: 25px; color: #2c3e50; }
            form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; }
            label { font-weight: bold; color: #2c3e50; }
            input[type="text"], input[type="tel"], input[type="email"], input[type="number"], textarea { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            textarea { min-height: 80px; resize: vertical; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-start; gap: 10px; margin-left: 0; }
            button, .icon-btn { background: #3498db; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #2980b9; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            th { background: #3498db; color: #fff; }
            tr:last-child td { border-bottom: none; }
            .icon-btn { padding: 6px 10px; font-size: 16px; margin: 0 2px; }
            .edit { background: #f39c12; }
            .edit:hover { background: #e67e22; }
            .delete { background: #e74c3c; }
            .delete:hover { background: #c0392b; }
            .home-link { display: flex; align-items: center; gap: 12px; padding: 15px 20px; color: #ecf0f1; text-decoration: none; transition: all 0.2s; border-top: 1px solid #34495e; margin-top: 10px; }
            .home-link:hover { background: #34495e; color: #3498db; }
            .home-link i { font-size: 18px; width: 20px; text-align: center; }
        </style>
        <script>
            window.onload = function() {
                var form = document.getElementById('cadastroForm');
                if (form) {
                    form.onkeydown = function(e) {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            return false;
                        }
                    };
                }

                // Position submenus dynamically
                var menuItems = document.querySelectorAll('.has-submenu');
                menuItems.forEach(function(item) {
                    item.addEventListener('mouseenter', function() {
                        var submenu = this.querySelector(':scope > .submenu');
                        if (submenu) {
                            var rect = this.getBoundingClientRect();
                            submenu.style.top = rect.top + 'px';

                            // For nested submenus, calculate left position
                            if (this.closest('.submenu')) {
                                submenu.style.left = (rect.right) + 'px';
                            }
                        }
                    });
                });
            };
        </script>
    </head>
    <body>
    <div class="layout">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h1>VibeCForms</h1>
                <p>Formulários Dinâmicos</p>
            </div>
            <div class="menu-container">
                <ul class="menu">
                    {{ menu_html|safe }}
                </ul>
                <a href="/" class="home-link"><i class="fa fa-home"></i> Página Inicial</a>
            </div>
        </nav>
        <div class="main-content">
            <div class="container">
                <h2>{{ title }}</h2>
                {% if error %}
                <div style="color:#e74c3c; background:#ffeaea; border:1px solid #e74c3c; padding:10px; margin-bottom:15px; border-radius:5px;">
                    <i class="fa fa-exclamation-triangle"></i> {{error}}
                </div>
                {% endif %}
                <form method="post" id="cadastroForm">
                    {{ form_fields|safe }}
                    <div class="form-actions">
                        <button type="submit"><i class="fa fa-plus"></i> Cadastrar</button>
                    </div>
                </form>
                <h3 style="margin-top:0;">Registros cadastrados:</h3>
                <table>
                    <tr>
                        {{ table_headers|safe }}
                    </tr>
                    {{ table_rows|safe }}
                </table>
            </div>
        </div>
    </div>
    </body>
    </html>
    """


def get_edit_template():
    """Return the edit page template with dynamic form generation."""
    return """
    <html>
    <head>
        <title>Editar - {{ title }}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .layout { display: flex; min-height: 100vh; }
            .sidebar { width: 250px; background: #2c3e50; color: #fff; padding: 20px 0; position: fixed; height: 100vh; z-index: 1000; display: flex; flex-direction: column; }
            .sidebar-header { padding: 0 20px 20px; border-bottom: 1px solid #34495e; margin-bottom: 20px; flex-shrink: 0; }
            .sidebar-header h1 { font-size: 24px; font-style: italic; margin: 0; color: #3498db; }
            .sidebar-header p { font-size: 12px; margin: 5px 0 0; color: #95a5a6; }
            .menu-container { flex: 1; overflow-y: auto; position: relative; }
            .menu { list-style: none; padding: 0; margin: 0; }
            .menu li { margin: 0; position: static; }
            .menu a { display: flex; align-items: center; gap: 12px; padding: 15px 20px; color: #ecf0f1; text-decoration: none; transition: all 0.2s; white-space: nowrap; }
            .menu a:hover { background: #34495e; color: #3498db; }
            .menu a.active { background: #3498db; color: #fff; }
            .menu a.active-path { background: #34495e; }
            .menu a i { font-size: 18px; width: 20px; text-align: center; }
            .submenu-arrow { font-size: 12px !important; margin-left: auto; }
            .has-submenu { position: relative; }
            .submenu { list-style: none; padding: 0; margin: 0; position: fixed; left: 250px; background: #34495e; min-width: 220px; width: auto; box-shadow: 4px 4px 12px rgba(0,0,0,0.4); display: none; z-index: 2000; border-radius: 4px; }
            .has-submenu:hover > .submenu { display: block; }
            .submenu li { position: static; }
            .submenu li a { padding: 12px 20px; font-size: 14px; white-space: nowrap; }
            .level-2 { background: #2c3e50; }
            .level-3 { background: #1a252f; }
            .home-link { display: flex; align-items: center; gap: 12px; padding: 15px 20px; color: #ecf0f1; text-decoration: none; transition: all 0.2s; border-top: 1px solid #34495e; margin-top: 10px; }
            .home-link:hover { background: #34495e; color: #3498db; }
            .home-link i { font-size: 18px; width: 20px; text-align: center; }
            .main-content { margin-left: 250px; flex: 1; padding: 40px; position: relative; z-index: 1; }
            .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; position: relative; z-index: 1; }
            h2 { text-align: center; margin-bottom: 25px; color: #2c3e50; }
            form { display: flex; flex-direction: column; gap: 12px; }
            label { font-weight: bold; color: #2c3e50; }
            input[type="text"], input[type="tel"], input[type="email"], input[type="number"], textarea { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            textarea { min-height: 80px; resize: vertical; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-end; gap: 10px; }
            button, .icon-btn { background: #3498db; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #2980b9; }
            .cancel { background: #95a5a6; color: #fff; }
            .cancel:hover { background: #7f8c8d; }
        </style>
        <script>
            window.onload = function() {
                // Position submenus dynamically
                var menuItems = document.querySelectorAll('.has-submenu');
                menuItems.forEach(function(item) {
                    item.addEventListener('mouseenter', function() {
                        var submenu = this.querySelector(':scope > .submenu');
                        if (submenu) {
                            var rect = this.getBoundingClientRect();
                            submenu.style.top = rect.top + 'px';

                            // For nested submenus, calculate left position
                            if (this.closest('.submenu')) {
                                submenu.style.left = (rect.right) + 'px';
                            }
                        }
                    });
                });
            };
        </script>
    </head>
    <body>
    <div class="layout">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h1>VibeCForms</h1>
                <p>Formulários Dinâmicos</p>
            </div>
            <div class="menu-container">
                <ul class="menu">
                    {{ menu_html|safe }}
                </ul>
                <a href="/" class="home-link"><i class="fa fa-home"></i> Página Inicial</a>
            </div>
        </nav>
        <div class="main-content">
            <div class="container">
                <h2>Editar - {{ title }}</h2>
                {% if error %}
                <div style="color:#e74c3c; background:#ffeaea; border:1px solid #e74c3c; padding:10px; margin-bottom:15px; border-radius:5px;">
                    <i class="fa fa-exclamation-triangle"></i> {{error}}
                </div>
                {% endif %}
                <form method="post">
                    {{ form_fields|safe }}
                    <div class="form-actions">
                        <button type="submit"><i class="fa fa-save"></i> Salvar</button>
                        <a href="/{{ form_name }}" class="icon-btn cancel" style="text-decoration:none;"><i class="fa fa-times"></i> Cancelar</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
    </body>
    </html>
    """


def get_main_page_template():
    """Return the main landing page template."""
    return """
    <html>
    <head>
        <title>VibeCForms</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                width: 90%;
                background: #fff;
                padding: 60px 80px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                text-align: center;
            }
            h1 {
                font-size: 72px;
                font-style: italic;
                color: #667eea;
                margin: 0 0 20px 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            p {
                font-size: 18px;
                color: #666;
                margin: 20px 0 40px 0;
                line-height: 1.6;
            }
            .forms-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .form-card {
                background: #667eea;
                color: #fff;
                text-decoration: none;
                padding: 30px 20px;
                border-radius: 12px;
                font-size: 18px;
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 15px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .form-card:hover {
                background: #5568d3;
                transform: translateY(-5px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.5);
            }
            .form-card i {
                font-size: 48px;
                opacity: 0.9;
            }
            .form-title {
                font-weight: bold;
                font-size: 20px;
            }
            .form-category {
                font-size: 14px;
                opacity: 0.8;
                background: rgba(255,255,255,0.2);
                padding: 4px 12px;
                border-radius: 12px;
            }
        </style>
    </head>
    <body>
    <div class="container">
        <h1>VibeCForms</h1>
        <p>
            Bem-vindo ao VibeCForms - Uma aplicação web de gerenciamento de formulários dinâmicos<br>
            construída com o conceito de <strong>Vibe Coding</strong>, programação assistida por IA.
        </p>
        <div class="forms-grid">
            {% for form in forms %}
            <a href="/{{ form.path }}" class="form-card">
                <i class="fa {{ form.icon }}"></i>
                <div class="form-title">{{ form.title }}</div>
                <div class="form-category">{{ form.category }}</div>
            </a>
            {% endfor %}
        </div>
    </div>
    </body>
    </html>
    """


@app.route("/")
def main_page():
    """Display the main landing page."""
    forms = get_all_forms_flat()
    return render_template_string(get_main_page_template(), forms=forms)


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

            return render_template_string(
                get_main_template(),
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

    return render_template_string(
        get_main_template(),
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
            return render_template_string(
                get_edit_template(),
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

    return render_template_string(
        get_edit_template(),
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
