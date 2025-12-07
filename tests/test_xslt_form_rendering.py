"""Test XSLT form page rendering with complete workflow."""

import pytest
from src.rendering.xml_builder import XMLBuilder
from src.rendering.xslt_renderer import XSLTRenderer


def test_form_page_rendering():
    """Test complete form page rendering with all field types."""

    # Sample spec with multiple field types
    spec = {
        "title": "Test Form",
        "icon": "fa-clipboard",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "telefone", "label": "Telefone", "type": "tel", "required": False},
            {
                "name": "estado",
                "label": "Estado",
                "type": "select",
                "required": False,
                "options": [
                    {"value": "SP", "label": "São Paulo"},
                    {"value": "RJ", "label": "Rio de Janeiro"},
                ],
            },
            {"name": "ativo", "label": "Ativo", "type": "checkbox", "required": False},
            {"name": "senha", "label": "Senha", "type": "password", "required": False},
        ],
        "default_tags": ["lead", "novo"],
    }

    # Sample records
    records = [
        {
            "_record_id": "test123",
            "nome": "João Silva",
            "email": "joao@example.com",
            "telefone": "11999887766",
            "estado": "SP",
            "ativo": True,
            "senha": "secret123",
        },
    ]

    # Sample menu
    menu_items = [
        {"type": "form", "path": "test", "title": "Test Form", "icon": "fa-clipboard"},
    ]

    # Build XML
    xml_root = XMLBuilder.build_form_page_xml(
        spec=spec,
        form_name="test",
        records=records,
        menu_items=menu_items,
        error="",
        new_record_id="",
    )

    # Verify XML structure
    assert xml_root.tag == "form-page"
    assert xml_root.get("form-name") == "test"

    # Render with XSLT
    renderer = XSLTRenderer(
        business_case_root="examples/ponto-de-vendas", src_root="src"
    )
    html = renderer.render_form_page(
        spec=spec,
        form_name="test",
        records=records,
        menu_items=menu_items,
        error="",
        new_record_id="",
    )

    # Verify HTML content
    assert "<!DOCTYPE HTML>" in html
    assert "<title>Test Form</title>" in html
    assert "VibeCForms" in html  # Sidebar header
    assert "Formulários Dinâmicos" in html  # Sidebar subtitle

    # Verify Tailwind CSS
    assert "https://cdn.tailwindcss.com" in html

    # Verify Font Awesome
    assert "font-awesome" in html

    # Verify form fields
    assert 'name="nome"' in html
    assert 'name="email"' in html
    assert 'name="telefone"' in html
    assert 'name="estado"' in html
    assert 'name="ativo"' in html
    assert 'name="senha"' in html

    # Verify select options
    assert "São Paulo" in html
    assert "Rio de Janeiro" in html

    # Verify table headers
    assert "<th" in html
    assert "Tags" in html
    assert "Nome" in html
    assert "Email" in html
    assert "Ações" in html

    # Verify table data
    assert "João Silva" in html
    assert "joao@example.com" in html
    assert "11999887766" in html

    # Verify select label displayed (not value)
    assert "São Paulo" in html

    # Verify checkbox displayed as Sim/Não
    assert "Sim" in html

    # Verify password masked
    assert "••••••••" in html
    assert "secret123" not in html

    # Verify tag badges
    assert "lead" in html
    assert "novo" in html

    # Verify JavaScript preserved
    assert "loadTags" in html
    assert "getTagColorClass" in html
    assert "async function" in html

    # Verify menu
    assert "Test Form" in html
    assert "fa-clipboard" in html


def test_form_page_with_error():
    """Test form page rendering with error message."""

    spec = {
        "title": "Error Test",
        "icon": "fa-exclamation",
        "fields": [{"name": "nome", "label": "Nome", "type": "text", "required": True}],
    }

    renderer = XSLTRenderer(
        business_case_root="examples/ponto-de-vendas", src_root="src"
    )
    html = renderer.render_form_page(
        spec=spec,
        form_name="error_test",
        records=[],
        menu_items=[],
        error="Campo obrigatório não preenchido",
        new_record_id="",
    )

    # Verify error message displayed
    assert "Campo obrigatório não preenchido" in html
    assert "fa-exclamation-triangle" in html


def test_form_page_empty_records():
    """Test form page rendering with no records."""

    spec = {
        "title": "Empty Test",
        "icon": "fa-inbox",
        "fields": [{"name": "nome", "label": "Nome", "type": "text", "required": True}],
    }

    renderer = XSLTRenderer(
        business_case_root="examples/ponto-de-vendas", src_root="src"
    )
    html = renderer.render_form_page(
        spec=spec,
        form_name="empty_test",
        records=[],
        menu_items=[],
        error="",
        new_record_id="",
    )

    # Verify page renders even with empty records
    assert "Empty Test" in html
    assert "<table" in html
    assert "<tbody>" in html


def test_xml_structure():
    """Test XML structure generation."""

    spec = {
        "title": "XML Test",
        "icon": "fa-code",
        "fields": [
            {"name": "field1", "label": "Field 1", "type": "text", "required": True},
            {
                "name": "field2",
                "label": "Field 2",
                "type": "select",
                "required": False,
                "options": [{"value": "a", "label": "Option A"}],
            },
        ],
        "default_tags": ["tag1"],
    }

    records = [{"_record_id": "rec1", "field1": "value1", "field2": "a"}]

    menu_items = [
        {
            "type": "folder",
            "path": "folder1",
            "name": "Folder 1",
            "icon": "fa-folder",
            "children": [
                {
                    "type": "form",
                    "path": "folder1/form1",
                    "title": "Form 1",
                    "icon": "fa-file",
                }
            ],
        }
    ]

    xml_root = XMLBuilder.build_form_page_xml(
        spec=spec,
        form_name="xml_test",
        records=records,
        menu_items=menu_items,
        error="Test error",
        new_record_id="new123",
    )

    # Verify root element
    assert xml_root.tag == "form-page"
    assert xml_root.get("form-name") == "xml_test"
    assert xml_root.get("error") == "Test error"
    assert xml_root.get("new-record-id") == "new123"

    # Verify spec
    spec_elem = xml_root.find("spec")
    assert spec_elem is not None
    assert spec_elem.get("title") == "XML Test"
    assert spec_elem.get("icon") == "fa-code"

    # Verify fields
    fields = spec_elem.find("fields")
    assert fields is not None
    assert len(fields.findall("field")) == 2

    # Verify default tags
    default_tags = spec_elem.find("default-tags")
    assert default_tags is not None
    assert len(default_tags.findall("tag")) == 1
    assert default_tags.find("tag").text == "tag1"

    # Verify records
    records_elem = xml_root.find("records")
    assert records_elem is not None
    assert len(records_elem.findall("record")) == 1

    record = records_elem.find("record")
    assert record.get("id") == "rec1"

    # Verify menu
    menu = xml_root.find("menu")
    assert menu is not None
    assert len(menu.findall("item")) == 1

    folder = menu.find("item")
    assert folder.get("type") == "folder"
    assert len(folder.findall("item")) == 1
