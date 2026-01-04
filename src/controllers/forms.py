"""Forms Controller for VibeCForms

This module contains all form-related routes and support functions.
Routes are organized as a Flask Blueprint for modular architecture.
"""

import logging
from typing import Dict, Any, List
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    jsonify,
)

from persistence.factory import RepositoryFactory
from persistence.change_manager import (
    check_form_changes,
    update_form_tracking,
    ChangeManager,
)
from utils.spec_loader import load_spec
from utils.menu_builder import get_forms_for_landing_page, get_menu_html
from utils.spec_renderer import render_form_fields, render_table, validate_form
from services.tag_service import TagService

logger = logging.getLogger(__name__)

# Create Blueprint
forms_bp = Blueprint("forms", __name__)

# Initialize TagService
tag_service = TagService()


# =============================================================================
# SUPPORT FUNCTIONS
# =============================================================================


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


# =============================================================================
# ROUTES
# =============================================================================


@forms_bp.route("/")
def main_page():
    """Display the main landing page."""
    forms = get_forms_for_landing_page()
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


@forms_bp.route("/api/search/<datasource>")
def api_search_generic(datasource):
    """Generic API endpoint to search any entity with autocomplete.

    Automatically detects the primary display field from the spec (first required text field)
    and returns results as {record_id, label} pairs for UUID-based relationships.

    Args:
        datasource: The entity name (e.g., 'clientes', 'acreditadores')

    Query params:
        q: Search query string

    Returns:
        JSON array of objects: [{"record_id": "UUID", "label": "Display Name"}, ...]
        Limited to 5 results for performance.
    """
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify([])

    try:
        spec = load_spec(datasource)
    except:
        return jsonify([])

    # Detect the primary display field from spec (first required text field)
    display_field = None
    for field in spec.get("fields", []):
        field_type = field.get("type", "text")
        # Use first required text-like field
        if field.get("required", False) and field_type in [
            "text",
            "email",
            "tel",
            "url",
            "search",
        ]:
            display_field = field.get("name")
            break

    # Fallback: use first text field if no required text field found
    if not display_field:
        for field in spec.get("fields", []):
            field_type = field.get("type", "text")
            if field_type in ["text", "email", "tel", "url", "search"]:
                display_field = field.get("name")
                break

    if not display_field:
        return jsonify([])

    forms = read_forms(spec, datasource)

    # Filter forms by display field (case-insensitive substring match)
    results = []
    for form in forms:
        display_value = form.get(display_field, "")
        if isinstance(display_value, str) and query in display_value.lower():
            results.append(
                {
                    "record_id": form.get(
                        "_record_id", ""
                    ),  # Note: SQLite adapter uses "_record_id"
                    "label": display_value,
                }
            )

            # Limit to 5 results for performance
            if len(results) >= 5:
                break

    return jsonify(results)


@forms_bp.route("/<path:form_name>", methods=["GET", "POST"])
def index(form_name):
    spec = load_spec(form_name)
    error = ""

    # Generate dynamic menu
    menu_html = get_menu_html(form_name)

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
        error = validate_form(spec, form_data)

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

            form_fields = render_form_fields(spec, form_data)
            table = render_table(spec, forms, form_name)

            return render_template(
                "form.html",
                title=spec["title"],
                form_name=form_name,
                menu_html=menu_html,
                error=error,
                form_fields=form_fields,
                table_headers=table["headers"],
                table_rows=table["rows"],
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

    # Render form fields with UUID
    form_fields = render_form_fields(
        spec, form_data={"_record_id": new_record_id}, include_uuid=True
    )

    # Render table
    table = render_table(spec, forms, form_name)

    return render_template(
        "form.html",
        title=spec["title"],
        form_name=form_name,
        menu_html=menu_html,
        error="",
        form_fields=form_fields,
        table_headers=table["headers"],
        table_rows=table["rows"],
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
    menu_html = get_menu_html(form_name)

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
        error = validate_form(spec, form_data)

        if error:
            # Re-render with error
            form_data["_record_id"] = record_id
            form_fields = render_form_fields(spec, form_data)

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
    record["_record_id"] = record_id
    form_fields = render_form_fields(spec, record)

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
