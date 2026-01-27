"""
Tests for relationship field type support.

This module tests the implementation of the 'relationship' field type,
which allows forms to reference records from other entities using UUIDs.
"""

import pytest
import os
import tempfile
from flask import Flask
from utils.spec_renderer import _render_field
from persistence.adapters.sqlite_adapter import SQLiteRepository


@pytest.fixture
def app():
    """Create a Flask app context for testing."""
    app = Flask(__name__)
    app.config["BUSINESS_CASE_ROOT"] = None
    app.config["FALLBACK_TEMPLATE_DIR"] = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "src", "templates"
    )
    return app


class TestRelationshipFieldRendering:
    """Test relationship field rendering in forms."""

    def test_render_relationship_field_basic(self, app):
        """Test basic relationship field rendering."""
        field = {
            "name": "customer_id",
            "label": "Customer",
            "type": "relationship",
            "target": "customers",
            "required": True,
        }

        with app.app_context():
            html = _render_field(field)

        # Check for essential HTML elements
        assert 'id="customer_id_display"' in html
        assert 'id="customer_id"' in html
        assert 'type="hidden"' in html
        assert 'name="customer_id"' in html
        assert "Customer:" in html
        assert "required" in html

        # Check for autocomplete functionality
        assert "/api/search/customers" in html
        assert "autocomplete-suggestions" in html

    def test_render_relationship_field_optional(self, app):
        """Test optional relationship field rendering."""
        field = {
            "name": "manager_id",
            "label": "Manager",
            "type": "relationship",
            "target": "employees",
            "required": False,
        }

        with app.app_context():
            html = _render_field(field)

        # Field should render without 'required' attribute
        assert "required" not in html
        assert "/api/search/employees" in html

    def test_render_relationship_field_with_value(self, app):
        """Test relationship field rendering with existing value (edit mode)."""
        field = {
            "name": "product_id",
            "label": "Product",
            "type": "relationship",
            "target": "products",
            "required": True,
        }

        form_data = {"product_id": "ABC123XYZ"}

        with app.app_context():
            html = _render_field(field, form_data)

        # Hidden field should have the UUID value
        assert 'value="ABC123XYZ"' in html

    def test_render_relationship_field_missing_target(self):
        """Test that relationship field raises error when 'target' is missing."""
        field = {
            "name": "invalid_rel",
            "label": "Invalid Relationship",
            "type": "relationship",
            "required": True,
        }

        # Should raise ValueError due to missing 'target' attribute
        with pytest.raises(ValueError, match="must specify 'target' attribute"):
            _render_field(field)

    def test_render_relationship_field_javascript_injection_safe(self, app):
        """Test that relationship field is safe from JavaScript injection."""
        field = {
            "name": "test_field",
            "label": "Test <script>alert('XSS')</script>",
            "type": "relationship",
            "target": "users",
            "required": False,
        }

        with app.app_context():
            html = _render_field(field)

        # Jinja2 should escape HTML/JS by default
        assert "<script>" not in html or "&lt;script&gt;" in html


class TestRelationshipFieldTypeMapping:
    """Test SQLite type mapping for relationship fields."""

    def test_relationship_type_mapped_to_text(self):
        """Test that 'relationship' field type maps to TEXT in SQLite."""
        assert SQLiteRepository.TYPE_MAPPING.get("relationship") == "TEXT"

    def test_relationship_type_mapping_comment(self):
        """Test that relationship type mapping has documentation."""
        # Check that the mapping exists and is documented in code
        import inspect

        source = inspect.getsource(SQLiteRepository)
        assert "relationship" in source
        assert "UUID" in source or "uuid" in source


class TestRelationshipFieldTableDisplay:
    """Test relationship field display in table views."""

    def test_table_display_shows_uuid(self):
        """Test that relationship values display as UUIDs in tables."""
        from utils.spec_renderer import _render_table_row

        spec = {
            "fields": [
                {
                    "name": "customer_id",
                    "label": "Customer",
                    "type": "relationship",
                    "target": "customers",
                }
            ]
        }

        form_data = {"_record_id": "REC001", "customer_id": "CUST-UUID-123"}

        row_html = _render_table_row(form_data, spec, "orders")

        # Should display the UUID value
        assert "CUST-UUID-123" in row_html

    def test_table_display_empty_relationship(self):
        """Test that empty relationship fields display correctly in tables."""
        from utils.spec_renderer import _render_table_row

        spec = {
            "fields": [
                {
                    "name": "optional_field",
                    "label": "Optional",
                    "type": "relationship",
                    "target": "users",
                }
            ]
        }

        form_data = {"_record_id": "REC002", "optional_field": ""}

        row_html = _render_table_row(form_data, spec, "documents")

        # Should render without errors
        assert "<td></td>" in row_html or '<td class="tags-cell"' in row_html


class TestRelationshipFieldPersistence:
    """Test relationship field persistence in SQLite."""

    def test_create_table_with_relationship_field(self, tmp_path):
        """Test creating a SQLite table with relationship field."""
        db_path = tmp_path / "test.db"

        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "customer_id",
                    "type": "relationship",
                    "target": "customers",
                    "required": True,
                },
                {"name": "notes", "type": "text", "required": False},
            ]
        }

        # Should create table without errors
        result = repo.create_storage("orders", spec)
        assert result is True

        # Verify table exists
        assert repo.exists("orders")

    def test_insert_record_with_relationship(self, tmp_path):
        """Test inserting a record with relationship field."""
        db_path = tmp_path / "test.db"

        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "customer_id",
                    "type": "relationship",
                    "target": "customers",
                    "required": True,
                },
                {"name": "amount", "type": "number", "required": True},
            ]
        }

        repo.create_storage("invoices", spec)

        data = {"customer_id": "CUST-UUID-456", "amount": 1500}

        # Should insert without errors
        record_id = repo.create("invoices", spec, data)
        assert record_id is not None

        # Verify data was stored
        records = repo.read_all("invoices", spec)
        assert len(records) == 1
        assert records[0]["customer_id"] == "CUST-UUID-456"
        assert records[0]["amount"] == 1500

    def test_update_record_with_relationship(self, tmp_path):
        """Test updating a record with relationship field."""
        db_path = tmp_path / "test.db"

        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "supplier_id",
                    "type": "relationship",
                    "target": "suppliers",
                    "required": True,
                },
                {"name": "status", "type": "text", "required": True},
            ]
        }

        repo.create_storage("purchase_orders", spec)

        # Create initial record
        data = {"supplier_id": "SUPP-UUID-789", "status": "pending"}
        repo.create("purchase_orders", spec, data)

        # Update the relationship
        updated_data = {"supplier_id": "SUPP-UUID-999", "status": "approved"}
        result = repo.update("purchase_orders", spec, 0, updated_data)
        assert result is True

        # Verify update
        records = repo.read_all("purchase_orders", spec)
        assert records[0]["supplier_id"] == "SUPP-UUID-999"
        assert records[0]["status"] == "approved"


class TestRelationshipFieldValidation:
    """Test validation behavior for relationship fields."""

    def test_required_relationship_field_validation(self):
        """Test that required relationship fields are validated."""
        from utils.spec_renderer import validate_form

        spec = {
            "fields": [
                {
                    "name": "user_id",
                    "label": "User",
                    "type": "relationship",
                    "target": "users",
                    "required": True,
                }
            ],
            "validation_messages": {
                "all_empty": "Preencha os campos obrigatórios.",
                "user_id": "User is required",
            },
        }

        # Empty form data should fail validation
        form_data = {"user_id": ""}
        error = validate_form(spec, form_data)
        # Should show the all_empty message or field-specific message
        assert error in ["Preencha os campos obrigatórios.", "User is required"]

        # Valid UUID should pass validation
        form_data = {"user_id": "USER-UUID-001"}
        error = validate_form(spec, form_data)
        assert error == ""

    def test_optional_relationship_field_validation(self):
        """Test that optional relationship fields pass validation when empty."""
        from utils.spec_renderer import validate_form

        spec = {
            "fields": [
                {
                    "name": "manager_id",
                    "label": "Manager",
                    "type": "relationship",
                    "target": "employees",
                    "required": False,
                },
                {"name": "name", "label": "Name", "type": "text", "required": True},
            ],
            "validation_messages": {},
        }

        # Empty optional relationship should pass
        form_data = {"manager_id": "", "name": "John Doe"}
        error = validate_form(spec, form_data)
        assert error == ""


class TestRelationshipFieldIntegration:
    """Integration tests for relationship field type."""

    def test_full_workflow_with_relationship(self, tmp_path):
        """Test complete workflow: create, read, update, delete with relationship."""
        db_path = tmp_path / "test.db"

        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "category_id",
                    "type": "relationship",
                    "target": "categories",
                    "required": True,
                },
                {"name": "title", "type": "text", "required": True},
                {"name": "active", "type": "checkbox", "required": False},
            ]
        }

        # Create storage
        repo.create_storage("articles", spec)

        # Create record
        data = {"category_id": "CAT-UUID-001", "title": "Test Article", "active": True}
        record_id = repo.create("articles", spec, data)
        assert record_id is not None

        # Read all
        records = repo.read_all("articles", spec)
        assert len(records) == 1
        assert records[0]["category_id"] == "CAT-UUID-001"

        # Update
        updated_data = {
            "category_id": "CAT-UUID-002",
            "title": "Updated Article",
            "active": False,
        }
        result = repo.update("articles", spec, 0, updated_data)
        assert result is True

        # Verify update
        records = repo.read_all("articles", spec)
        assert records[0]["category_id"] == "CAT-UUID-002"
        assert records[0]["title"] == "Updated Article"

        # Delete
        result = repo.delete("articles", spec, 0)
        assert result is True

        # Verify deletion
        records = repo.read_all("articles", spec)
        assert len(records) == 0
