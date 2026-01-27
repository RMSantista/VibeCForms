"""Relationships Controller for VibeCForms

This module provides API endpoints for managing relationships between entities.
Routes are organized as a Flask Blueprint for modular architecture.
"""

import logging
import sqlite3
from typing import Dict, Any, List
from flask import (
    Blueprint,
    jsonify,
    request,
)

from persistence.factory import RepositoryFactory
from persistence.relationship_repository import RelationshipRepository
from utils.spec_loader import load_spec

logger = logging.getLogger(__name__)

# Create Blueprint
relationships_bp = Blueprint("relationships", __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_relationship_repository(form_path: str) -> RelationshipRepository:
    """
    Get RelationshipRepository instance for a given form.

    Args:
        form_path: Path to the form (e.g., 'amostra', 'orcamento')

    Returns:
        RelationshipRepository instance

    Raises:
        RuntimeError: If backend is not SQLite
    """
    repo = RepositoryFactory.get_repository(form_path)

    # Check if backend is SQLite (relationships only work with SQLite)
    if not hasattr(repo, "conn") or not isinstance(repo.conn, sqlite3.Connection):
        raise RuntimeError(
            f"Relationships are only supported for SQLite backend. "
            f"Form '{form_path}' uses a different backend."
        )

    return RelationshipRepository(repo.conn)


def get_display_value(form_path: str, record_id: str) -> str:
    """
    Get the display value for a record.

    Uses the same logic as RelationshipRepository._get_display_field()
    to find the primary display field (first required text field).

    Args:
        form_path: Form path (e.g., 'clientes')
        record_id: Record UUID

    Returns:
        Display value or record_id if not found
    """
    try:
        spec = load_spec(form_path)
        repo = RepositoryFactory.get_repository(form_path)

        # Read the record
        record = repo.read_by_id(form_path, spec, record_id)
        if not record:
            return record_id

        # Find display field (first required text field)
        display_field = None
        for field in spec.get("fields", []):
            field_type = field.get("type", "text")
            if field.get("required", False) and field_type in [
                "text",
                "email",
                "tel",
                "url",
                "search",
            ]:
                display_field = field.get("name")
                break

        # Fallback: use first text field
        if not display_field:
            for field in spec.get("fields", []):
                field_type = field.get("type", "text")
                if field_type in ["text", "email", "tel", "url", "search"]:
                    display_field = field.get("name")
                    break

        if display_field and display_field in record:
            return record[display_field]

        return record_id
    except Exception as e:
        logger.warning(
            f"Error getting display value for {form_path}/{record_id}: {str(e)}"
        )
        return record_id


# =============================================================================
# API ROUTES
# =============================================================================


@relationships_bp.route(
    "/api/relationships/<path:form_path>/<record_id>", methods=["GET"]
)
def get_relationships(form_path: str, record_id: str):
    """
    Get all relationships for a given record (forward and reverse).

    Returns:
        JSON response with:
        {
            "success": true,
            "forward": [
                {
                    "rel_id": "...",
                    "relationship_name": "cliente",
                    "target_type": "clientes",
                    "target_id": "...",
                    "target_display": "Cliente ABC",
                    "created_at": "2026-01-08T..."
                }
            ],
            "reverse": [
                {
                    "rel_id": "...",
                    "source_type": "pedidos",
                    "source_id": "...",
                    "source_display": "Pedido #123",
                    "relationship_name": "amostra",
                    "created_at": "2026-01-08T..."
                }
            ],
            "count": {
                "forward": 3,
                "reverse": 5
            }
        }
    """
    try:
        # Get relationship repository
        rel_repo = get_relationship_repository(form_path)

        # Get forward relationships (this entity points to others)
        forward_rels = rel_repo.get_relationships(
            source_type=form_path, source_id=record_id, active_only=True
        )

        # Get reverse relationships (other entities point to this)
        reverse_rels = rel_repo.get_reverse_relationships(
            target_type=form_path, target_id=record_id, active_only=True
        )

        # Format forward relationships
        forward_data = []
        for rel in forward_rels:
            forward_data.append(
                {
                    "rel_id": rel.rel_id,
                    "relationship_name": rel.relationship_name,
                    "target_type": rel.target_type,
                    "target_id": rel.target_id,
                    "target_display": get_display_value(rel.target_type, rel.target_id),
                    "created_at": rel.created_at,
                }
            )

        # Format reverse relationships
        reverse_data = []
        for rel in reverse_rels:
            reverse_data.append(
                {
                    "rel_id": rel.rel_id,
                    "source_type": rel.source_type,
                    "source_id": rel.source_id,
                    "source_display": get_display_value(rel.source_type, rel.source_id),
                    "relationship_name": rel.relationship_name,
                    "created_at": rel.created_at,
                }
            )

        return jsonify(
            {
                "success": True,
                "forward": forward_data,
                "reverse": reverse_data,
                "count": {
                    "forward": len(forward_data),
                    "reverse": len(reverse_data),
                },
                # Backward compatibility with FASE 3.4 tests
                "relationships": forward_data,
                "reverse_relationships": reverse_data,
            }
        )

    except RuntimeError as e:
        # Backend not supported
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "forward": [],
                    "reverse": [],
                    "count": {"forward": 0, "reverse": 0},
                    # Backward compatibility
                    "relationships": [],
                    "reverse_relationships": [],
                }
            ),
            400,
        )

    except Exception as e:
        logger.error(
            f"Error getting relationships for {form_path}/{record_id}: {str(e)}"
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error",
                    "forward": [],
                    "reverse": [],
                    "count": {"forward": 0, "reverse": 0},
                    # Backward compatibility
                    "relationships": [],
                    "reverse_relationships": [],
                }
            ),
            500,
        )


@relationships_bp.route("/api/relationships/<rel_id>", methods=["DELETE"])
def delete_relationship(rel_id: str):
    """
    Soft-delete a relationship by ID.

    Args:
        rel_id: Relationship UUID

    Query params:
        removed_by: User/actor performing the removal (optional, defaults to 'user')

    Returns:
        JSON response:
        {
            "success": true,
            "message": "Relationship removed successfully"
        }
    """
    try:
        removed_by = request.args.get("removed_by", "user")

        # We need to get a repository instance to access the connection
        # Since we don't know the form_path, we'll use any SQLite-backed form
        # This is a limitation of the current architecture

        # Try to get first SQLite-backed form
        from persistence.config import get_config

        config = get_config()

        # Find a form that uses SQLite
        sqlite_form = None
        for form_path, backend_config in config.config.get("form_mappings", {}).items():
            if form_path != "*":
                backend_type = config.get_backend_config(form_path).get("type")
                if backend_type == "sqlite":
                    sqlite_form = form_path
                    break

        if not sqlite_form:
            # Fallback: use default backend if it's SQLite
            default_backend = config.config.get("default_backend", "txt")
            if default_backend == "sqlite":
                # Use any form (we just need the connection)
                sqlite_form = "clientes"  # Assuming clientes exists

        if not sqlite_form:
            return (
                jsonify({"success": False, "error": "No SQLite backend configured"}),
                400,
            )

        # Get relationship repository
        rel_repo = get_relationship_repository(sqlite_form)

        # Verify relationship exists
        rel = rel_repo.get_relationship(rel_id)
        if not rel:
            return jsonify({"success": False, "error": "Relationship not found"}), 404

        # Remove relationship (soft delete)
        success = rel_repo.remove_relationship(rel_id, removed_by)

        if success:
            logger.info(f"Relationship {rel_id} removed by {removed_by}")
            return jsonify(
                {"success": True, "message": "Relationship removed successfully"}
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to remove relationship"}),
                500,
            )

    except Exception as e:
        logger.error(f"Error removing relationship {rel_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
