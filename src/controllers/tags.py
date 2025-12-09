"""Tags Controller for VibeCForms.

Handles all tag-related operations including:
- Tag management interface
- Tag CRUD operations via API
- Tag history tracking
- Tag-based search and filtering
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from typing import Dict, Any, Optional, List

from services.tag_service import TagService
from persistence.factory import RepositoryFactory
from utils.spec_loader import load_spec
from utils.crockford import validate_id

logger = logging.getLogger(__name__)

# Create Blueprint
tags_bp = Blueprint("tags", __name__)

# Initialize service
tag_service = TagService()


# Helper functions (imported from VibeCForms.py)
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
    from VibeCForms import SPECS_DIR

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


# =============================================================================
# TAGS ENDPOINTS
# =============================================================================


@tags_bp.route("/tags/manager")
def tags_manager():
    """Display the tags management page."""
    forms = get_all_forms_flat()
    menu_items = scan_specs_directory()
    menu_html = generate_menu_html(menu_items, "")
    return render_template("tags_manager.html", forms=forms, menu_html=menu_html)


@tags_bp.route("/api/<path:form_name>/tags/<record_id>", methods=["POST"])
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


@tags_bp.route("/api/<path:form_name>/tags/<record_id>/<tag>", methods=["DELETE"])
def api_remove_tag(form_name, record_id, tag):
    """
    Remove a tag from a record.

    DELETE /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW/importante

    Returns:
        JSON response with success status
    """
    try:
        # Validate ID format
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


@tags_bp.route("/api/<path:form_name>/tags/<record_id>", methods=["GET"])
def api_get_tags(form_name, record_id):
    """
    Get all tags for a record.

    GET /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW

    Returns:
        JSON response with list of tags
    """
    try:
        # Validate ID format
        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        tags = tag_service.get_tags(form_name, record_id)

        return jsonify({"success": True, "record_id": record_id, "tags": tags})

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@tags_bp.route("/api/<path:form_name>/tags/<record_id>/history", methods=["GET"])
def api_get_tag_history(form_name, record_id):
    """
    Get tag history for a record (including removed tags).

    GET /api/contatos/tags/5FQR8V9JMF8SKT2EGTC90X7G1WW/history

    Returns:
        JSON response with full tag history
    """
    try:
        # Validate ID format
        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        # Get all tags including removed ones
        tags = tag_service.get_tags(form_name, record_id, active_only=False)

        return jsonify({"success": True, "record_id": record_id, "history": tags})

    except Exception as e:
        logger.error(f"Error getting tag history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@tags_bp.route("/api/<path:form_name>/search/tags", methods=["GET"])
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
