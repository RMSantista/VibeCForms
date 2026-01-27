"""
Tests for relationship field cardinality (one/many) support.

This module tests the implementation of cardinality in relationship fields,
allowing single or multiple selections of related records.
"""

import pytest
import os
import json
from flask import Flask
from utils.spec_renderer import _render_field, _render_table_row
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


class TestRelationshipCardinalityOne:
    """Test relationship field with cardinality=one (single selection)."""

    def test_render_cardinality_one_explicit(self, app):
        """Test rendering relationship field with explicit cardinality='one'."""
        field = {
            "name": "customer",
            "label": "Customer",
            "type": "relationship",
            "target": "customers",
            "cardinality": "one",
            "display_field": "nome",
            "required": True,
        }

        with app.app_context():
            html = _render_field(field)

        # Should render standard autocomplete
        assert 'id="customer_display"' in html
        assert 'id="customer"' in html
        assert 'type="hidden"' in html
        assert "/api/search/customers" in html
        assert "required" in html
        # Should have cardinality='one' in JavaScript
        assert "const cardinality = 'one';" in html

    def test_render_cardinality_one_default(self, app):
        """Test that cardinality defaults to 'one' when not specified."""
        field = {
            "name": "supplier",
            "label": "Supplier",
            "type": "relationship",
            "target": "suppliers",
            "required": False,
        }

        with app.app_context():
            html = _render_field(field)

        # Should behave as cardinality='one' by default
        assert "const cardinality = 'one';" in html
        assert 'type="hidden"' in html

    def test_cardinality_one_with_value(self, app):
        """Test cardinality=one with existing UUID value."""
        field = {
            "name": "category",
            "label": "Category",
            "type": "relationship",
            "target": "categories",
            "cardinality": "one",
            "required": True,
        }

        form_data = {"category": "CAT-UUID-123"}

        with app.app_context():
            html = _render_field(field, form_data)

        # Hidden field should contain the UUID
        assert 'value="CAT-UUID-123"' in html


class TestRelationshipCardinalityMany:
    """Test relationship field with cardinality=many (multiple selection)."""

    def test_render_cardinality_many(self, app):
        """Test rendering relationship field with cardinality='many'."""
        field = {
            "name": "products",
            "label": "Products",
            "type": "relationship",
            "target": "products",
            "cardinality": "many",
            "display_field": "nome",
            "required": True,
        }

        with app.app_context():
            html = _render_field(field)

        # Should have chips container for multiple selections
        assert 'id="products_chips"' in html
        assert "relationship-chips" in html
        assert 'id="products_display"' in html
        assert 'id="products"' in html
        assert "/api/search/products" in html

        # Required should NOT be on input (handled by chips validation)
        # The input is for searching, not for the actual value
        assert (
            "required" not in html
            or 'id="products_display"' not in html.split("required")[0]
        )

    def test_cardinality_many_with_values(self, app):
        """Test cardinality=many with existing values (JSON array)."""
        field = {
            "name": "tags",
            "label": "Tags",
            "type": "relationship",
            "target": "tags",
            "cardinality": "many",
            "required": False,
        }

        # Simulate stored JSON array with labels
        selected_items = [
            {"record_id": "TAG-001", "label": "Important"},
            {"record_id": "TAG-002", "label": "Urgent"},
        ]
        form_data = {"tags": json.dumps(selected_items)}

        with app.app_context():
            html = _render_field(field, form_data)

        # Hidden field should contain JSON array (escaped for HTML)
        # The JSON will be HTML-escaped in the value attribute
        assert "TAG-001" in html
        assert "TAG-002" in html

    def test_cardinality_many_javascript_rendering(self, app):
        """Test that JavaScript for many cardinality is present."""
        field = {
            "name": "participants",
            "label": "Participants",
            "type": "relationship",
            "target": "users",
            "cardinality": "many",
            "required": True,
        }

        with app.app_context():
            html = _render_field(field)

        # Should have JavaScript for chip rendering
        assert "renderChips" in html
        assert "selectedItems" in html
        assert "relationship-chip" in html


class TestRelationshipCardinalityValidation:
    """Test cardinality validation."""

    def test_invalid_cardinality_defaults_to_one(self, app):
        """Test that invalid cardinality values default to 'one'."""
        field = {
            "name": "test_field",
            "label": "Test",
            "type": "relationship",
            "target": "items",
            "cardinality": "invalid_value",  # Invalid
            "required": False,
        }

        with app.app_context():
            # Should not raise error, but log warning and default to 'one'
            html = _render_field(field)

        # Should render as cardinality='one' in JavaScript
        assert "const cardinality = 'one';" in html


class TestRelationshipTableDisplay:
    """Test relationship field display in table views with cardinality."""

    def test_table_display_cardinality_one(self):
        """Test table display for cardinality=one shows single UUID."""
        spec = {
            "fields": [
                {
                    "name": "customer",
                    "label": "Customer",
                    "type": "relationship",
                    "target": "customers",
                    "cardinality": "one",
                }
            ]
        }

        form_data = {"_record_id": "REC001", "customer": "CUST-UUID-123"}

        row_html = _render_table_row(form_data, spec, "orders")

        # Should display the UUID value
        assert "CUST-UUID-123" in row_html

    def test_table_display_cardinality_many(self):
        """Test table display for cardinality=many shows comma-separated labels."""
        spec = {
            "fields": [
                {
                    "name": "products",
                    "label": "Products",
                    "type": "relationship",
                    "target": "products",
                    "cardinality": "many",
                }
            ]
        }

        # JSON array with labels
        selected_items = [
            {"record_id": "PROD-001", "label": "Product A"},
            {"record_id": "PROD-002", "label": "Product B"},
            {"record_id": "PROD-003", "label": "Product C"},
        ]
        form_data = {"_record_id": "REC002", "products": json.dumps(selected_items)}

        row_html = _render_table_row(form_data, spec, "orders")

        # Should display comma-separated labels
        assert "Product A" in row_html
        assert "Product B" in row_html
        assert "Product C" in row_html

    def test_table_display_cardinality_many_empty(self):
        """Test table display for empty cardinality=many field."""
        spec = {
            "fields": [
                {
                    "name": "tags",
                    "label": "Tags",
                    "type": "relationship",
                    "target": "tags",
                    "cardinality": "many",
                }
            ]
        }

        form_data = {"_record_id": "REC003", "tags": ""}

        row_html = _render_table_row(form_data, spec, "items")

        # Should render without errors (empty cell)
        assert "<td></td>" in row_html or '<td class="tags-cell"' in row_html


class TestRelationshipPersistenceCardinality:
    """Test persistence of relationship fields with different cardinalities."""

    def test_persist_cardinality_one(self, tmp_path):
        """Test persisting relationship with cardinality=one."""
        db_path = tmp_path / "test.db"
        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "customer",
                    "type": "relationship",
                    "target": "customers",
                    "cardinality": "one",
                    "required": True,
                },
                {"name": "amount", "type": "number", "required": True},
            ]
        }

        repo.create_storage("invoices", spec)

        # Create record with single UUID
        data = {"customer": "CUST-UUID-456", "amount": 1500}
        record_id = repo.create("invoices", spec, data)
        assert record_id is not None

        # Verify data
        records = repo.read_all("invoices", spec)
        assert len(records) == 1
        assert records[0]["customer"] == "CUST-UUID-456"

    def test_persist_cardinality_many(self, tmp_path):
        """Test persisting relationship with cardinality=many."""
        db_path = tmp_path / "test.db"
        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "products",
                    "type": "relationship",
                    "target": "products",
                    "cardinality": "many",
                    "required": True,
                },
                {"name": "order_date", "type": "date", "required": True},
            ]
        }

        repo.create_storage("orders", spec)

        # Create record with JSON array of UUIDs
        selected_products = [
            {"record_id": "PROD-001", "label": "Product A"},
            {"record_id": "PROD-002", "label": "Product B"},
        ]
        data = {"products": json.dumps(selected_products), "order_date": "2025-01-17"}

        record_id = repo.create("orders", spec, data)
        assert record_id is not None

        # Verify data
        records = repo.read_all("orders", spec)
        assert len(records) == 1

        # Parse stored JSON
        stored_products = json.loads(records[0]["products"])
        assert len(stored_products) == 2
        assert stored_products[0]["record_id"] == "PROD-001"
        assert stored_products[1]["label"] == "Product B"

    def test_update_cardinality_many(self, tmp_path):
        """Test updating relationship with cardinality=many."""
        db_path = tmp_path / "test.db"
        repo = SQLiteRepository({"database": str(db_path)})

        spec = {
            "fields": [
                {
                    "name": "tags",
                    "type": "relationship",
                    "target": "tags",
                    "cardinality": "many",
                    "required": False,
                },
                {"name": "title", "type": "text", "required": True},
            ]
        }

        repo.create_storage("articles", spec)

        # Create initial record
        initial_tags = [{"record_id": "TAG-001", "label": "News"}]
        data = {"tags": json.dumps(initial_tags), "title": "Article 1"}
        repo.create("articles", spec, data)

        # Update with more tags
        updated_tags = [
            {"record_id": "TAG-001", "label": "News"},
            {"record_id": "TAG-002", "label": "Featured"},
            {"record_id": "TAG-003", "label": "Breaking"},
        ]
        updated_data = {"tags": json.dumps(updated_tags), "title": "Article 1 Updated"}
        result = repo.update("articles", spec, 0, updated_data)
        assert result is True

        # Verify update
        records = repo.read_all("articles", spec)
        stored_tags = json.loads(records[0]["tags"])
        assert len(stored_tags) == 3
        assert stored_tags[2]["label"] == "Breaking"
