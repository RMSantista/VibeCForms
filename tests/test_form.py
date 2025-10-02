import os
import json
from src.VibeCForms import read_forms, write_forms, load_spec, validate_form_data


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
    assert result == forms


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
