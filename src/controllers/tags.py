"""Tags Controller for VibeCForms.

Handles all tag-related operations including:
- Tag management interface
- Tag CRUD operations via API
- Tag history tracking
- Tag-based search and filtering
"""

import logging
from flask import Blueprint, render_template, request, jsonify
from typing import Dict, Any

from services.tag_service import TagService
from persistence.factory import RepositoryFactory
from utils.spec_loader import load_spec
from utils.menu_builder import get_forms_for_landing_page, get_menu_html
from utils.crockford import validate_id

logger = logging.getLogger(__name__)

# Create Blueprint
tags_bp = Blueprint("tags", __name__)

# Initialize service
tag_service = TagService()


# =============================================================================
# TAGS ENDPOINTS
# =============================================================================


@tags_bp.route("/tags/manager")
def tags_manager():
    """Display the tags management page."""
    forms = get_forms_for_landing_page()
    menu_html = get_menu_html("")
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
