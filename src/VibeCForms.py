import os
import json
from flask import Flask, render_template_string, request, redirect, abort
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/registros.txt")

# Directory containing form specification JSON files
SPECS_DIR = os.path.join(os.path.dirname(__file__), "../specs")

app = Flask(__name__)


def load_spec(form_name):
    """Load and validate a form specification file."""
    spec_path = os.path.join(SPECS_DIR, f"{form_name}.json")
    if not os.path.exists(spec_path):
        abort(404, description=f"Form specification '{form_name}' not found")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Validate required spec fields
    if "title" not in spec or "fields" not in spec:
        abort(500, description=f"Invalid spec file for '{form_name}'")

    return spec


def get_data_file(form_name):
    """Get the data file path for a given form."""
    return os.path.join(os.path.dirname(__file__), f"{form_name}.txt")


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


def get_main_template():
    """Return the main page template with dynamic form generation."""
    return """
    <html>
    <head>
        <title>{{ title }}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .container { max-width: 900px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
            h2 { text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; }
            label { font-weight: bold; }
            input[type="text"], input[type="tel"], input[type="email"], input[type="number"], textarea { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            textarea { min-height: 80px; resize: vertical; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-start; gap: 10px; margin-left: 0; }
            button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #1565c0; }
            table { width: 100%; min-width: 800px; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
            th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            th { background: #1976d2; color: #fff; }
            tr:last-child td { border-bottom: none; }
            .icon-btn { padding: 6px 10px; font-size: 16px; margin: 0 2px; }
            .edit { background: #ffa726; }
            .edit:hover { background: #fb8c00; }
            .delete { background: #e53935; }
            .delete:hover { background: #b71c1c; }
        </style>
        <script>
            window.onload = function() {
                var form = document.getElementById('cadastroForm');
                form.onkeydown = function(e) {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        return false;
                    }
                };
            };
        </script>
    </head>
    <body>
    <div class="container">
        <h2>{{ title }}</h2>
        {% if error %}
        <div style="color:#e53935; background:#ffeaea; border:1px solid #e53935; padding:10px; margin-bottom:15px; border-radius:5px;">
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
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
            h2 { text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 12px; }
            label { font-weight: bold; }
            input[type="text"], input[type="tel"], input[type="email"], input[type="number"], textarea { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            textarea { min-height: 80px; resize: vertical; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-end; gap: 10px; }
            button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #1565c0; }
            .cancel { background: #e0e0e0; color: #333; }
            .cancel:hover { background: #bdbdbd; }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>Editar - {{ title }}</h2>
        {% if error %}
        <div style="color:#e53935; background:#ffeaea; border:1px solid #e53935; padding:10px; margin-bottom:15px; border-radius:5px;">
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
    </body>
    </html>
    """


@app.route("/<form_name>", methods=["GET", "POST"])
def index(form_name):
    spec = load_spec(form_name)
    data_file = get_data_file(form_name)
    error = ""

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
        error="",
        form_fields=form_fields,
        table_headers=table_headers,
        table_rows=table_rows,
    )


# Redirect root to default form (contatos)
@app.route("/", methods=["GET"])
def root():
    return redirect("/contatos")


@app.route("/<form_name>/edit/<int:idx>", methods=["GET", "POST"])
def edit(form_name, idx):
    spec = load_spec(form_name)
    data_file = get_data_file(form_name)
    forms = read_forms(spec, data_file)
    error = ""

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
        error="",
        form_fields=form_fields,
    )


@app.route("/<form_name>/delete/<int:idx>")
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
