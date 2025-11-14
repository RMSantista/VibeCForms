"""
Tests for Kanban Service (FASE 8 - Sistema de Kanban Visual).

This module tests the KanbanService functionality including:
- Board configuration loading
- Card retrieval by column
- Card movement between columns
- Move validation
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.kanban_service import KanbanService, get_kanban_service
from services.tag_service import TagService, get_tag_service
from persistence.factory import RepositoryFactory
from utils.spec_loader import load_spec


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory with test board configuration."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create test board configuration
    board_config = {
        "boards": {
            "test_pipeline": {
                "title": "Test Pipeline",
                "form": "contatos",
                "columns": [
                    {"tag": "new", "label": "New", "color": "#e3f2fd"},
                    {"tag": "active", "label": "Active", "color": "#fff3e0"},
                    {"tag": "done", "label": "Done", "color": "#c8e6c9"},
                ],
            },
            "sales_pipeline": {
                "title": "Pipeline de Vendas",
                "form": "contatos",
                "columns": [
                    {"tag": "lead", "label": "Leads", "color": "#e3f2fd"},
                    {"tag": "qualified", "label": "Qualificados", "color": "#fff3e0"},
                    {"tag": "proposal", "label": "Proposta", "color": "#f3e5f5"},
                    {"tag": "negotiation", "label": "Negociação", "color": "#e8f5e9"},
                    {"tag": "closed_won", "label": "Ganhos", "color": "#c8e6c9"},
                    {"tag": "closed_lost", "label": "Perdidos", "color": "#ffcdd2"},
                ],
            },
        }
    }

    config_file = config_dir / "kanban_boards.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(board_config, f, indent=2)

    return str(config_file)


@pytest.fixture
def kanban_service(temp_config_dir):
    """Create KanbanService instance with test configuration."""
    return KanbanService(config_path=temp_config_dir)


@pytest.fixture
def tag_service():
    """Get TagService instance."""
    return get_tag_service()


class TestKanbanServiceInit:
    """Test KanbanService initialization and configuration loading."""

    def test_init_with_custom_config(self, temp_config_dir):
        """Test initialization with custom config path."""
        service = KanbanService(config_path=temp_config_dir)
        assert service is not None
        assert service.config_path == temp_config_dir
        assert "boards" in service.boards_config

    def test_init_default_config(self):
        """Test initialization with default config path."""
        service = KanbanService()
        assert service is not None
        assert service.config_path is not None

    def test_singleton_pattern(self):
        """Test that get_kanban_service returns singleton instance."""
        service1 = get_kanban_service()
        service2 = get_kanban_service()
        assert service1 is service2

    def test_load_boards_config(self, kanban_service):
        """Test loading board configurations."""
        config = kanban_service.boards_config
        assert "boards" in config
        assert "test_pipeline" in config["boards"]
        assert "sales_pipeline" in config["boards"]


class TestBoardConfiguration:
    """Test board configuration management."""

    def test_load_board_config(self, kanban_service):
        """Test loading a specific board configuration."""
        config = kanban_service.load_board_config("test_pipeline")

        assert config is not None
        assert config["title"] == "Test Pipeline"
        assert config["form"] == "contatos"
        assert len(config["columns"]) == 3

    def test_load_nonexistent_board(self, kanban_service):
        """Test loading configuration for non-existent board."""
        config = kanban_service.load_board_config("nonexistent")
        assert config is None

    def test_get_available_boards(self, kanban_service):
        """Test getting list of available boards."""
        boards = kanban_service.get_available_boards()

        assert len(boards) == 2
        assert any(b["name"] == "test_pipeline" for b in boards)
        assert any(b["name"] == "sales_pipeline" for b in boards)

        # Check board info structure
        for board in boards:
            assert "name" in board
            assert "title" in board

    def test_board_columns_structure(self, kanban_service):
        """Test board column structure."""
        config = kanban_service.load_board_config("test_pipeline")
        columns = config["columns"]

        for column in columns:
            assert "tag" in column
            assert "label" in column
            assert "color" in column


class TestCardRetrieval:
    """Test card retrieval functionality."""

    def test_get_cards_for_empty_column(self, kanban_service):
        """Test getting cards for column with no cards."""
        cards = kanban_service.get_cards_for_column("contatos", "new")
        assert isinstance(cards, list)
        # Will be empty unless there are test records with 'new' tag

    def test_get_cards_for_column_with_spec(self, kanban_service):
        """Test getting cards with explicit spec."""
        try:
            spec = load_spec("contatos")
            cards = kanban_service.get_cards_for_column("contatos", "new", spec)
            assert isinstance(cards, list)
        except FileNotFoundError:
            pytest.skip("contatos spec not found")

    def test_get_all_board_cards(self, kanban_service):
        """Test getting all cards for a board."""
        cards = kanban_service.get_all_board_cards("test_pipeline")

        assert isinstance(cards, dict)
        # Should have all columns even if empty
        assert "new" in cards
        assert "active" in cards
        assert "done" in cards

        # Each column should have a list of cards
        for column_tag, column_cards in cards.items():
            assert isinstance(column_cards, list)

    def test_get_all_board_cards_invalid_board(self, kanban_service):
        """Test getting cards for invalid board."""
        cards = kanban_service.get_all_board_cards("invalid_board")
        assert cards == {}


class TestCardMovement:
    """Test card movement between columns."""

    def test_validate_move_valid(self, kanban_service):
        """Test validation of valid move."""
        # Move between valid columns on the board
        valid = kanban_service.validate_move("test_pipeline", "new", "active")
        assert valid is True

        valid = kanban_service.validate_move("test_pipeline", "active", "done")
        assert valid is True

    def test_validate_move_invalid_from_tag(self, kanban_service):
        """Test validation of move with invalid source tag."""
        valid = kanban_service.validate_move("test_pipeline", "invalid", "active")
        assert valid is False

    def test_validate_move_invalid_to_tag(self, kanban_service):
        """Test validation of move with invalid target tag."""
        valid = kanban_service.validate_move("test_pipeline", "new", "invalid")
        assert valid is False

    def test_validate_move_invalid_board(self, kanban_service):
        """Test validation of move on invalid board."""
        valid = kanban_service.validate_move("invalid_board", "new", "active")
        assert valid is False

    def test_validate_move_across_boards(self, kanban_service):
        """Test that tags from different boards are validated correctly."""
        # 'lead' is valid on sales_pipeline but not on test_pipeline
        valid = kanban_service.validate_move("test_pipeline", "lead", "new")
        assert valid is False


class TestMoveCardIntegration:
    """Integration tests for moving cards (requires tag service)."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, tmp_path):
        """Setup test environment with temporary data directory."""
        # This would require setting up temporary persistence
        # For now, we test the method signature and error handling
        pass

    def test_move_card_signature(self, kanban_service):
        """Test move_card method signature and parameters."""
        # Test with fake data - will fail but validates the interface
        result = kanban_service.move_card(
            form_path="contatos",
            object_id="INVALID_ID_FOR_TEST_000000",
            from_tag="new",
            to_tag="active",
            actor="test_user",
            metadata={"test": True},
        )
        # Should return False for invalid ID, but method works
        assert isinstance(result, bool)

    def test_move_card_metadata(self, kanban_service):
        """Test that metadata is passed through to tag service."""
        # This tests the interface - actual functionality requires database
        metadata = {"reason": "test", "timestamp": "2025-01-01T00:00:00"}

        result = kanban_service.move_card(
            form_path="contatos",
            object_id="INVALID_ID_FOR_TEST_000000",
            from_tag="new",
            to_tag="active",
            actor="test_user",
            metadata=metadata,
        )
        assert isinstance(result, bool)


class TestSalesPipelineBoard:
    """Test the sales_pipeline board configuration."""

    def test_sales_pipeline_structure(self, kanban_service):
        """Test that sales_pipeline has correct structure."""
        config = kanban_service.load_board_config("sales_pipeline")

        assert config is not None
        assert config["title"] == "Pipeline de Vendas"
        assert config["form"] == "contatos"
        assert len(config["columns"]) == 6

    def test_sales_pipeline_columns(self, kanban_service):
        """Test sales_pipeline column configuration."""
        config = kanban_service.load_board_config("sales_pipeline")
        columns = config["columns"]

        # Check expected columns in order
        expected_tags = [
            "lead",
            "qualified",
            "proposal",
            "negotiation",
            "closed_won",
            "closed_lost",
        ]
        actual_tags = [col["tag"] for col in columns]

        assert actual_tags == expected_tags

    def test_sales_pipeline_moves(self, kanban_service):
        """Test valid moves in sales pipeline."""
        board = "sales_pipeline"

        # Test progressive moves
        assert kanban_service.validate_move(board, "lead", "qualified") is True
        assert kanban_service.validate_move(board, "qualified", "proposal") is True
        assert kanban_service.validate_move(board, "proposal", "negotiation") is True
        assert kanban_service.validate_move(board, "negotiation", "closed_won") is True

        # Test backward moves (should also be valid)
        assert kanban_service.validate_move(board, "proposal", "qualified") is True

        # Test direct to closed_lost (should be valid)
        assert kanban_service.validate_move(board, "lead", "closed_lost") is True


class TestErrorHandling:
    """Test error handling in KanbanService."""

    def test_missing_config_file(self, tmp_path):
        """Test handling of missing configuration file."""
        nonexistent_path = str(tmp_path / "nonexistent.json")
        service = KanbanService(config_path=nonexistent_path)

        # Should initialize with empty boards
        assert service.boards_config == {"boards": {}}

    def test_invalid_json_config(self, tmp_path):
        """Test handling of invalid JSON configuration."""
        invalid_config = tmp_path / "invalid.json"
        invalid_config.write_text("{ invalid json }")

        service = KanbanService(config_path=str(invalid_config))

        # Should handle error gracefully
        assert service.boards_config == {"boards": {}}

    def test_get_cards_invalid_form(self, kanban_service):
        """Test getting cards for invalid form."""
        cards = kanban_service.get_cards_for_column("nonexistent_form", "tag")
        # Should return empty list, not crash
        assert cards == []


# Run tests with: uv run pytest tests/test_kanban.py -v
