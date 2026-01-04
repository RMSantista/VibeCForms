import os
import json
from src.VibeCForms import (
    read_forms,
    write_forms,
    load_spec,
    validate_form_data,
    scan_specs_directory,
    get_all_forms_flat,
    generate_menu_html,
)


def test_write_and_read_forms(tmp_path):
    """Test writing and reading forms with spec."""
    test_file = tmp_path / "test.txt"

    # Create test spec
    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": True},
            {
                "name": "whatsapp",
                "label": "WhatsApp",
                "type": "checkbox",
                "required": False,
            },
        ],
    }

    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False},
    ]

    write_forms(forms, spec, str(test_file))
    result = read_forms(spec, str(test_file))

    # Filter out _record_id from results for comparison (UUID field added in FASE 3)
    result_clean = [{k: v for k, v in r.items() if k != "_record_id"} for r in result]
    assert result_clean == forms


def test_update_form(tmp_path):
    """Test updating a form entry."""
    test_file = tmp_path / "test.txt"

    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": True},
            {
                "name": "whatsapp",
                "label": "WhatsApp",
                "type": "checkbox",
                "required": False,
            },
        ],
    }

    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False},
    ]

    write_forms(forms, spec, str(test_file))

    # Altera o telefone de Ana
    forms[0]["telefone"] = "999"
    write_forms(forms, spec, str(test_file))

    result = read_forms(spec, str(test_file))
    assert result[0]["telefone"] == "999"


def test_delete_form(tmp_path):
    """Test deleting a form entry."""
    test_file = tmp_path / "test.txt"

    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": True},
            {
                "name": "whatsapp",
                "label": "WhatsApp",
                "type": "checkbox",
                "required": False,
            },
        ],
    }

    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False},
    ]

    write_forms(forms, spec, str(test_file))

    # Remove Bob
    forms = [c for c in forms if c.get("nome") != "Bob"]
    write_forms(forms, spec, str(test_file))

    result = read_forms(spec, str(test_file))
    assert len(result) == 1
    assert result[0]["nome"] == "Ana"


def test_validation():
    """Test form validation logic."""
    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": True},
        ],
        "validation_messages": {
            "all_empty": "Campos obrigatórios vazios",
            "nome": "Nome é obrigatório",
            "telefone": "Telefone é obrigatório",
        },
    }

    # Test all empty
    form_data = {"nome": "", "telefone": ""}
    error = validate_form_data(spec, form_data)
    assert error == "Campos obrigatórios vazios"

    # Test missing nome
    form_data = {"nome": "", "telefone": "123"}
    error = validate_form_data(spec, form_data)
    assert error == "Nome é obrigatório"

    # Test missing telefone
    form_data = {"nome": "Test", "telefone": ""}
    error = validate_form_data(spec, form_data)
    assert error == "Telefone é obrigatório"

    # Test valid data
    form_data = {"nome": "Test", "telefone": "123"}
    error = validate_form_data(spec, form_data)
    assert error == ""


def test_load_spec():
    """Test loading a spec file."""
    spec = load_spec("contatos")

    assert spec["title"] == "Agenda Pessoal"
    assert len(spec["fields"]) == 3
    assert spec["fields"][0]["name"] == "nome"
    assert spec["fields"][1]["name"] == "telefone"
    assert spec["fields"][2]["name"] == "whatsapp"


def test_scan_specs_directory():
    """Test scanning specs directory for menu structure."""
    menu_items = scan_specs_directory()

    # Should find multiple items
    assert len(menu_items) > 0

    # Check if we have both forms and folders
    has_forms = any(item["type"] == "form" for item in menu_items)
    has_folders = any(item["type"] == "folder" for item in menu_items)

    assert has_forms or has_folders

    # Check structure of a form item
    form_items = [item for item in menu_items if item["type"] == "form"]
    if form_items:
        form = form_items[0]
        assert "name" in form
        assert "path" in form
        assert "title" in form
        assert "icon" in form

    # Check structure of a folder item
    folder_items = [item for item in menu_items if item["type"] == "folder"]
    if folder_items:
        folder = folder_items[0]
        assert "name" in folder
        assert "path" in folder
        assert "icon" in folder
        assert "children" in folder
        assert isinstance(folder["children"], list)


def test_get_all_forms_flat():
    """Test flattening menu structure to get all forms."""
    menu_items = scan_specs_directory()
    forms = get_all_forms_flat(menu_items)

    # Should find multiple forms
    assert len(forms) > 0

    # Check structure of each form
    for form in forms:
        assert "title" in form
        assert "path" in form
        assert "icon" in form
        assert "category" in form

    # Check if nested forms have correct category
    nested_forms = [f for f in forms if "/" in f["path"]]
    if nested_forms:
        # Categories should be capitalized folder names
        for form in nested_forms:
            assert form["category"] != ""


def test_generate_menu_html():
    """Test menu HTML generation."""
    # Create sample menu structure
    menu_items = [
        {
            "type": "form",
            "name": "contatos",
            "path": "contatos",
            "title": "Agenda Pessoal",
            "icon": "fa-address-book",
        },
        {
            "type": "folder",
            "name": "financeiro",
            "path": "financeiro",
            "icon": "fa-dollar-sign",
            "children": [
                {
                    "type": "form",
                    "name": "contas",
                    "path": "financeiro/contas",
                    "title": "Contas",
                    "icon": "fa-dollar-sign",
                }
            ],
        },
    ]

    html = generate_menu_html(menu_items)

    # Check if HTML contains expected elements (note: outer <ul> is added in template)
    assert "fa-address-book" in html
    assert "Agenda Pessoal" in html
    assert "fa-dollar-sign" in html
    assert "financeiro" in html
    assert "has-submenu" in html
    assert "submenu" in html
    assert "Contas" in html


def test_load_spec_nested():
    """Test loading nested spec files."""
    spec = load_spec("financeiro/contas")

    assert spec["title"] == "Contas"
    assert len(spec["fields"]) == 4
    assert spec["fields"][0]["name"] == "descricao"
    assert spec["fields"][1]["name"] == "valor"


def test_generate_menu_html_with_active():
    """Test menu HTML generation with active item."""
    menu_items = [
        {
            "type": "form",
            "name": "contatos",
            "path": "contatos",
            "title": "Agenda Pessoal",
            "icon": "fa-address-book",
        }
    ]

    html = generate_menu_html(menu_items, current_form_path="contatos")

    # Check if active class is present
    assert "active" in html


def test_icon_from_spec():
    """Test that icons are loaded from spec files."""
    # Test root level form with icon
    spec = load_spec("contatos")
    assert "icon" in spec
    assert spec["icon"] == "fa-address-book"

    # Test another root level form
    spec = load_spec("produtos")
    assert "icon" in spec
    assert spec["icon"] == "fa-box"

    # Test nested form
    spec = load_spec("financeiro/contas")
    assert "icon" in spec
    assert spec["icon"] == "fa-file-invoice-dollar"


def test_icon_in_menu_items():
    """Test that icons appear correctly in menu items."""
    menu_items = scan_specs_directory()

    # Find contatos form
    contatos_forms = [
        item
        for item in menu_items
        if item["type"] == "form" and item["name"] == "contatos"
    ]
    assert len(contatos_forms) == 1
    assert contatos_forms[0]["icon"] == "fa-address-book"

    # Find produtos form
    produtos_forms = [
        item
        for item in menu_items
        if item["type"] == "form" and item["name"] == "produtos"
    ]
    assert len(produtos_forms) == 1
    assert produtos_forms[0]["icon"] == "fa-box"


def test_folder_config_loading():
    """Test loading folder configuration from _folder.json files."""
    from src.VibeCForms import load_folder_config
    import os

    # Test loading financeiro folder config
    financeiro_path = os.path.join("src", "specs", "financeiro")
    config = load_folder_config(financeiro_path)

    assert config is not None
    assert config["name"] == "Financeiro"
    assert config["icon"] == "fa-dollar-sign"
    assert config["description"] == "Gestão financeira e contábil"
    assert config["order"] == 1

    # Test loading rh folder config
    rh_path = os.path.join("src", "specs", "rh")
    config = load_folder_config(rh_path)

    assert config is not None
    assert config["name"] == "Recursos Humanos"
    assert config["icon"] == "fa-users"
    assert config["order"] == 2

    # Test loading nested folder config (rh/departamentos)
    departamentos_path = os.path.join("src", "specs", "rh", "departamentos")
    config = load_folder_config(departamentos_path)

    assert config is not None
    assert config["name"] == "Departamentos"
    assert config["icon"] == "fa-sitemap"
    assert config["order"] == 1


def test_folder_items_use_config():
    """Test that folder items in menu use configuration from _folder.json."""
    menu_items = scan_specs_directory()

    # Find financeiro folder
    financeiro_folders = [
        item
        for item in menu_items
        if item["type"] == "folder" and item["path"] == "financeiro"
    ]
    assert len(financeiro_folders) == 1
    financeiro = financeiro_folders[0]

    # Check it uses config values
    assert financeiro["name"] == "Financeiro"
    assert financeiro["icon"] == "fa-dollar-sign"
    assert "description" in financeiro
    assert financeiro["description"] == "Gestão financeira e contábil"
    assert "order" in financeiro
    assert financeiro["order"] == 1

    # Find rh folder
    rh_folders = [
        item for item in menu_items if item["type"] == "folder" and item["path"] == "rh"
    ]
    assert len(rh_folders) == 1
    rh = rh_folders[0]

    # Check it uses config values
    assert rh["name"] == "Recursos Humanos"
    assert rh["icon"] == "fa-users"
    assert "order" in rh
    assert rh["order"] == 2


def test_menu_items_sorted_by_order():
    """Test that menu items are sorted by order field."""
    menu_items = scan_specs_directory()

    # Get folder items
    folder_items = [item for item in menu_items if item["type"] == "folder"]

    # Should have at least financeiro and rh
    assert len(folder_items) >= 2

    # Items with order should be sorted
    items_with_order = [item for item in folder_items if "order" in item]
    if len(items_with_order) >= 2:
        orders = [item["order"] for item in items_with_order]
        # Check if sorted (ascending)
        assert orders == sorted(orders), "Items should be sorted by order field"
