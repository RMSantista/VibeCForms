"""
Kanban Service for VibeCForms Visual Kanban System.

This service provides high-level API for managing Kanban boards in VibeCForms,
implementing the visual interface for Tags as State convention.

Kanban boards allow:
- Visual representation of object states (tags as columns)
- Drag & drop state transitions
- Multi-column workflow visualization
- Board configuration via JSON
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from persistence.factory import RepositoryFactory
from services.tag_service import get_tag_service
from utils.spec_loader import load_spec

# Configure logging
logger = logging.getLogger(__name__)


class KanbanService:
    """
    Service layer for Kanban board management in VibeCForms.

    This service provides visual board management on top of the tag system,
    allowing users to manage state transitions through drag & drop interface.

    Example usage:
        # Initialize service
        kanban_service = KanbanService()

        # Load board configuration
        config = kanban_service.load_board_config('sales_pipeline')

        # Get cards for a column
        cards = kanban_service.get_cards_for_column('contatos', 'qualified')

        # Move card between columns
        success = kanban_service.move_card(
            'contatos',
            'record_id',
            'qualified',
            'proposal',
            'user123'
        )
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the KanbanService.

        Args:
            config_path: Path to kanban_boards.json (optional, uses default if not provided)
        """
        self.logger = logging.getLogger(__name__)
        self.tag_service = get_tag_service()

        # Default config path
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
                "kanban_boards.json",
            )

        self.config_path = config_path
        self.boards_config = self._load_boards_config()

    def _load_boards_config(self) -> Dict[str, Any]:
        """
        Load all board configurations from kanban_boards.json.

        Returns:
            Dictionary with board configurations
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(
                    f"Kanban boards config not found: {self.config_path}"
                )
                return {"boards": {}}

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.logger.info(
                f"Loaded {len(config.get('boards', {}))} Kanban board configurations"
            )
            return config

        except Exception as e:
            self.logger.error(f"Error loading Kanban boards config: {e}")
            return {"boards": {}}

    def load_board_config(self, board_name: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration for a specific board.

        Args:
            board_name: Name of the board (e.g., 'sales_pipeline')

        Returns:
            Board configuration dictionary or None if board doesn't exist

        Example:
            config = kanban_service.load_board_config('sales_pipeline')
            # {
            #   "title": "Pipeline de Vendas",
            #   "form": "contatos",
            #   "columns": [...]
            # }
        """
        board_config = self.boards_config.get("boards", {}).get(board_name)

        if not board_config:
            self.logger.warning(f"Board configuration not found: {board_name}")
            return None

        return board_config

    def get_available_boards(self) -> List[Dict[str, str]]:
        """
        Get list of all available Kanban boards.

        Returns:
            List of board info dictionaries with 'name' and 'title'

        Example:
            boards = kanban_service.get_available_boards()
            # [
            #   {"name": "sales_pipeline", "title": "Pipeline de Vendas"},
            #   ...
            # ]
        """
        boards = []
        for board_name, config in self.boards_config.get("boards", {}).items():
            boards.append(
                {
                    "name": board_name,
                    "title": config.get("title", board_name.replace("_", " ").title()),
                }
            )

        return boards

    def get_cards_for_column(
        self, form_path: str, tag: str, spec: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all cards (objects) for a specific column (tag).

        Args:
            form_path: Path to the form (e.g., 'contatos')
            tag: Tag name representing the column (e.g., 'qualified')
            spec: Optional form spec (will be loaded if not provided)

        Returns:
            List of object dictionaries with full data

        Example:
            cards = kanban_service.get_cards_for_column('contatos', 'qualified')
            # [
            #   {"_record_id": "ABC123...", "nome": "João", "email": "joao@..."},
            #   ...
            # ]
        """
        try:
            # Load spec if not provided
            if spec is None:
                spec = load_spec(form_path)

            # Get all object IDs with this tag
            object_ids = self.tag_service.get_objects_with_tag(form_path, tag)

            if not object_ids:
                return []

            # Get repository to read full object data
            repo = RepositoryFactory.get_repository(form_path)

            # Read all objects and filter by IDs
            all_objects = repo.read_all(form_path, spec)

            # Filter objects that have the tag
            cards = [obj for obj in all_objects if obj.get("_record_id") in object_ids]

            self.logger.info(f"Found {len(cards)} cards for {form_path}:{tag}")
            return cards

        except Exception as e:
            self.logger.error(f"Error getting cards for {form_path}:{tag}: {e}")
            return []

    def get_all_board_cards(self, board_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all cards organized by column for a board.

        Args:
            board_name: Name of the board

        Returns:
            Dictionary mapping column tags to card lists

        Example:
            cards = kanban_service.get_all_board_cards('sales_pipeline')
            # {
            #   "lead": [{...}, {...}],
            #   "qualified": [{...}],
            #   "proposal": [],
            #   ...
            # }
        """
        board_config = self.load_board_config(board_name)

        if not board_config:
            self.logger.error(f"Cannot get cards for unknown board: {board_name}")
            return {}

        form_path = board_config.get("form")
        if not form_path:
            self.logger.error(f"Board {board_name} has no 'form' configured")
            return {}

        try:
            spec = load_spec(form_path)
        except Exception as e:
            self.logger.error(f"Error loading spec for {form_path}: {e}")
            return {}

        # Get cards for each column
        all_cards = {}
        for column in board_config.get("columns", []):
            tag = column.get("tag")
            if tag:
                all_cards[tag] = self.get_cards_for_column(form_path, tag, spec)

        return all_cards

    def move_card(
        self,
        form_path: str,
        object_id: str,
        from_tag: str,
        to_tag: str,
        actor: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Move a card from one column to another (tag transition).

        This is the core operation for drag & drop functionality in Kanban boards.

        Args:
            form_path: Path to the form (e.g., 'contatos')
            object_id: 27-character Crockford Base32 ID of the object
            from_tag: Current column tag to remove
            to_tag: New column tag to add
            actor: Who is moving the card (user_id, 'ai_agent', 'system')
            metadata: Optional metadata about the move

        Returns:
            True if move was successful
            False otherwise

        Example:
            success = kanban_service.move_card(
                'contatos',
                'ABC123...',
                'qualified',
                'proposal',
                'user123',
                {'moved_at': '2025-01-14T10:30:00Z'}
            )
        """
        try:
            # Use tag service's transition method
            success = self.tag_service.transition(
                form_path, object_id, from_tag, to_tag, actor, metadata
            )

            if success:
                self.logger.info(
                    f"Card moved: {form_path}:{object_id} from {from_tag} to {to_tag} by {actor}"
                )
            else:
                self.logger.error(
                    f"Failed to move card: {form_path}:{object_id} from {from_tag} to {to_tag}"
                )

            return success

        except Exception as e:
            self.logger.error(
                f"Error moving card {form_path}:{object_id} from {from_tag} to {to_tag}: {e}"
            )
            return False

    def validate_move(self, board_name: str, from_tag: str, to_tag: str) -> bool:
        """
        Validate if a move between columns is allowed on a board.

        Currently allows all moves within configured columns.
        Can be extended to enforce workflow rules.

        Args:
            board_name: Name of the board
            from_tag: Source column tag
            to_tag: Target column tag

        Returns:
            True if move is allowed
            False otherwise
        """
        board_config = self.load_board_config(board_name)

        if not board_config:
            return False

        # Get all valid tags for this board
        valid_tags = [
            col.get("tag") for col in board_config.get("columns", []) if col.get("tag")
        ]

        # Check if both tags are valid columns
        if from_tag not in valid_tags or to_tag not in valid_tags:
            self.logger.warning(
                f"Invalid move on board {board_name}: {from_tag} -> {to_tag}"
            )
            return False

        # Can be extended with workflow rules:
        # - Only allow sequential moves
        # - Require approval for certain transitions
        # - Check user permissions

        return True


# Global instance (singleton pattern)
_kanban_service_instance: Optional[KanbanService] = None


def get_kanban_service() -> KanbanService:
    """
    Get the global KanbanService instance.

    This implements a singleton pattern to ensure only one KanbanService
    instance exists throughout the application lifecycle.

    Returns:
        KanbanService instance

    Example:
        kanban_service = get_kanban_service()
        config = kanban_service.load_board_config('sales_pipeline')
    """
    global _kanban_service_instance

    if _kanban_service_instance is None:
        _kanban_service_instance = KanbanService()

    return _kanban_service_instance
