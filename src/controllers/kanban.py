"""
Kanban Controller for VibeCForms Visual Kanban System.

This controller handles all Kanban board routes:
- GET /kanban/<board_name> - Display a Kanban board
- GET /api/kanban/boards - List all available Kanban boards
- GET /api/kanban/<board_name>/cards - Get cards for a board
- POST /api/kanban/<board_name>/move - Move a card between columns

Routes are registered with Flask Blueprint pattern for modular organization.
"""

import logging
from flask import Blueprint, render_template, request, jsonify

from services.kanban_service import get_kanban_service
from utils.crockford import validate_id

# Configure logging
logger = logging.getLogger(__name__)

# Create Flask Blueprint for Kanban routes
kanban_bp = Blueprint("kanban", __name__)

# Initialize Kanban service at module level
kanban_service = get_kanban_service()


@kanban_bp.route("/kanban/<board_name>")
def kanban_board(board_name):
    """
    Display a Kanban board.

    GET /kanban/sales_pipeline

    Returns:
        Rendered Kanban board HTML page
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return f"Board '{board_name}' not found", 404

        # Render kanban template
        return render_template(
            "kanban.html",
            board_name=board_name,
            board_title=board_config.get("title", board_name.replace("_", " ").title()),
            board_config=board_config,
        )

    except Exception as e:
        logger.error(f"Error displaying Kanban board '{board_name}': {e}")
        return f"Error loading board: {str(e)}", 500


@kanban_bp.route("/api/kanban/boards")
def api_kanban_boards():
    """
    List all available Kanban boards.

    GET /api/kanban/boards

    Returns:
        JSON response with list of boards
    """
    try:
        boards = kanban_service.get_available_boards()

        return jsonify({"success": True, "boards": boards})

    except Exception as e:
        logger.error(f"Error listing Kanban boards: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@kanban_bp.route("/api/kanban/<board_name>/cards")
def api_kanban_cards(board_name):
    """
    Get all cards for a Kanban board organized by columns.

    GET /api/kanban/sales_pipeline/cards

    Returns:
        JSON response with cards organized by column tags
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return (
                jsonify({"success": False, "error": f"Board '{board_name}' not found"}),
                404,
            )

        # Get all cards organized by column
        cards = kanban_service.get_all_board_cards(board_name)

        return jsonify({"success": True, "board": board_name, "cards": cards})

    except Exception as e:
        logger.error(f"Error getting cards for board '{board_name}': {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@kanban_bp.route("/api/kanban/<board_name>/move", methods=["POST"])
def api_kanban_move(board_name):
    """
    Move a card between columns (tag transition).

    POST /api/kanban/sales_pipeline/move
    Body: {
        "record_id": "5FQR8V9JMF8SKT2EGTC90X7G1WW",
        "from_tag": "qualified",
        "to_tag": "proposal",
        "actor": "user123"
    }

    Returns:
        JSON response with success status
    """
    try:
        # Load board configuration
        board_config = kanban_service.load_board_config(board_name)

        if not board_config:
            return (
                jsonify({"success": False, "error": f"Board '{board_name}' not found"}),
                404,
            )

        # Get request data
        data = request.get_json()
        record_id = data.get("record_id")
        from_tag = data.get("from_tag")
        to_tag = data.get("to_tag")
        actor = data.get("actor", "unknown")

        # Validate required fields
        if not record_id or not from_tag or not to_tag:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required fields: record_id, from_tag, to_tag",
                    }
                ),
                400,
            )

        # Validate ID format
        if not validate_id(record_id):
            return jsonify({"success": False, "error": "Invalid ID format"}), 400

        # Validate move is allowed on this board
        if not kanban_service.validate_move(board_name, from_tag, to_tag):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Invalid move: {from_tag} -> {to_tag} not allowed on this board",
                    }
                ),
                400,
            )

        # Get form path from board config
        form_path = board_config.get("form")
        if not form_path:
            return (
                jsonify({"success": False, "error": "Board has no form configured"}),
                500,
            )

        # Move the card
        success = kanban_service.move_card(
            form_path,
            record_id,
            from_tag,
            to_tag,
            actor,
            metadata={"board": board_name},
        )

        if success:
            logger.info(
                f"Card moved on board '{board_name}': {record_id} from {from_tag} to {to_tag} by {actor}"
            )
            return jsonify(
                {
                    "success": True,
                    "record_id": record_id,
                    "from_tag": from_tag,
                    "to_tag": to_tag,
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to move card"}), 500

    except Exception as e:
        logger.error(f"Error moving card on board '{board_name}': {e}")
        return jsonify({"success": False, "error": str(e)}), 500
