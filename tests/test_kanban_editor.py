"""
Tests for KanbanEditor - Phase 4 Workflow Component

Tests visual kanban editor including:
- Kanban creation and loading
- State management (add/remove/update)
- Transition management
- Form mappings
- Validation logic
- Export functionality
"""

import pytest
import json
import tempfile
import os
from src.workflow.kanban_editor import KanbanEditor


class MockKanbanRegistry:
    """Mock kanban registry for testing"""

    def __init__(self):
        self.kanbans = {}
        self.form_mappings = {}

    def register_kanban(self, kanban_def):
        """Register a kanban definition"""
        kanban_id = kanban_def["id"]
        self.kanbans[kanban_id] = kanban_def

    def get_kanban(self, kanban_id):
        """Get kanban definition"""
        return self.kanbans.get(kanban_id)

    def map_form_to_kanban(self, form_path, kanban_id):
        """Map form to kanban"""
        self.form_mappings[form_path] = kanban_id


@pytest.fixture
def mock_registry():
    """Create mock kanban registry"""
    return MockKanbanRegistry()


@pytest.fixture
def editor(mock_registry):
    """Create KanbanEditor instance"""
    return KanbanEditor(mock_registry)


# ========== Kanban Creation Tests ==========


def test_create_kanban(editor):
    """Test creating a new kanban"""
    editor.create_kanban("kanban_test", "Test Kanban", "Test description")

    assert editor.current_kanban is not None
    assert editor.current_kanban["id"] == "kanban_test"
    assert editor.current_kanban["name"] == "Test Kanban"
    assert editor.current_kanban["description"] == "Test description"
    assert editor.current_kanban["states"] == {}
    assert editor.current_kanban["initial_state"] is None


def test_create_kanban_chaining(editor):
    """Test that create_kanban returns self for chaining"""
    result = editor.create_kanban("test", "Test")
    assert result is editor


# ========== State Management Tests ==========


def test_add_state_basic(editor):
    """Test adding a basic state"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo", type="initial")

    assert "novo" in editor.current_kanban["states"]
    state = editor.current_kanban["states"]["novo"]
    assert state["name"] == "Novo"
    assert state["type"] == "initial"
    assert state["transitions"] == []
    assert editor.current_kanban["initial_state"] == "novo"


def test_add_state_with_all_options(editor):
    """Test adding state with all options"""
    editor.create_kanban("test", "Test")
    editor.add_state(
        "em_analise",
        "Em Análise",
        type="intermediate",
        description="State description",
        color="#FF0000",
        auto_transition_to="aprovado",
        timeout_hours=24,
    )

    state = editor.current_kanban["states"]["em_analise"]
    assert state["name"] == "Em Análise"
    assert state["type"] == "intermediate"
    assert state["description"] == "State description"
    assert state["color"] == "#FF0000"
    assert state["auto_transition_to"] == "aprovado"
    assert state["timeout_hours"] == 24


def test_add_state_sets_initial(editor):
    """Test that first state becomes initial"""
    editor.create_kanban("test", "Test")
    editor.add_state("primeiro", "Primeiro")

    assert editor.current_kanban["initial_state"] == "primeiro"


def test_add_state_without_kanban_fails(editor):
    """Test adding state without kanban loaded fails"""
    with pytest.raises(ValueError, match="No kanban loaded"):
        editor.add_state("novo", "Novo")


def test_add_duplicate_state_fails(editor):
    """Test adding duplicate state fails"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    with pytest.raises(ValueError, match="already exists"):
        editor.add_state("novo", "Novo Duplicado")


def test_remove_state(editor):
    """Test removing a state"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("em_analise", "Em Análise")

    editor.remove_state("em_analise")

    assert "em_analise" not in editor.current_kanban["states"]
    assert "novo" in editor.current_kanban["states"]


def test_remove_state_with_transition_fails(editor):
    """Test removing state referenced by transition fails without force"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("em_analise", "Em Análise")
    editor.add_transition("novo", "em_analise")

    with pytest.raises(ValueError, match="referenced by transition"):
        editor.remove_state("em_analise")


def test_remove_state_with_force(editor):
    """Test removing state with force removes transitions"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("em_analise", "Em Análise")
    editor.add_transition("novo", "em_analise")

    editor.remove_state("em_analise", force=True)

    assert "em_analise" not in editor.current_kanban["states"]
    assert "em_analise" not in editor.current_kanban["states"]["novo"]["transitions"]


def test_update_state(editor):
    """Test updating state properties"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    editor.update_state(
        "novo", name="Novo Atualizado", color="#00FF00", timeout_hours=48
    )

    state = editor.current_kanban["states"]["novo"]
    assert state["name"] == "Novo Atualizado"
    assert state["color"] == "#00FF00"
    assert state["timeout_hours"] == 48


# ========== Transition Management Tests ==========


def test_add_transition(editor):
    """Test adding a transition"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("em_analise", "Em Análise")
    editor.add_transition("novo", "em_analise")

    transitions = editor.current_kanban["states"]["novo"]["transitions"]
    assert "em_analise" in transitions


def test_add_transition_invalid_from_state(editor):
    """Test adding transition from invalid state fails"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    with pytest.raises(ValueError, match="Source state .* not found"):
        editor.add_transition("invalido", "novo")


def test_add_transition_invalid_to_state(editor):
    """Test adding transition to invalid state fails"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    with pytest.raises(ValueError, match="Target state .* not found"):
        editor.add_transition("novo", "invalido")


def test_remove_transition(editor):
    """Test removing a transition"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("em_analise", "Em Análise")
    editor.add_transition("novo", "em_analise")

    editor.remove_transition("novo", "em_analise")

    transitions = editor.current_kanban["states"]["novo"]["transitions"]
    assert "em_analise" not in transitions


# ========== Form Mapping Tests ==========


def test_map_form(editor):
    """Test mapping a form to kanban"""
    editor.create_kanban("test", "Test")
    editor.map_form("pedidos")

    assert "pedidos" in editor.current_kanban["form_mappings"]


def test_map_multiple_forms(editor):
    """Test mapping multiple forms"""
    editor.create_kanban("test", "Test")
    editor.map_form("pedidos")
    editor.map_form("vendas")

    assert "pedidos" in editor.current_kanban["form_mappings"]
    assert "vendas" in editor.current_kanban["form_mappings"]


def test_unmap_form(editor):
    """Test unmapping a form"""
    editor.create_kanban("test", "Test")
    editor.map_form("pedidos")
    editor.unmap_form("pedidos")

    assert "pedidos" not in editor.current_kanban["form_mappings"]


# ========== Validation Tests ==========


def test_validate_empty_kanban(editor):
    """Test validation fails for empty kanban"""
    editor.create_kanban("test", "Test")

    is_valid = editor.validate()

    assert not is_valid
    assert "at least one state" in str(editor.get_validation_errors())


def test_validate_missing_initial_state(editor):
    """Test validation fails without initial state"""
    editor.create_kanban("test", "Test")
    # Manually create state without setting initial
    editor.current_kanban["states"] = {
        "novo": {"name": "Novo", "type": "intermediate", "transitions": []}
    }
    editor.current_kanban["initial_state"] = None

    is_valid = editor.validate()

    assert not is_valid
    errors = editor.get_validation_errors()
    assert any("initial state" in err.lower() for err in errors)


def test_validate_invalid_transition_reference(editor):
    """Test validation fails with invalid transition target"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    # Manually add invalid transition
    editor.current_kanban["states"]["novo"]["transitions"].append("estado_inexistente")

    is_valid = editor.validate()

    assert not is_valid
    errors = editor.get_validation_errors()
    assert any("unknown state" in err.lower() for err in errors)


def test_validate_unreachable_states(editor):
    """Test validation detects unreachable states"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo", type="initial")
    editor.add_state("aprovado", "Aprovado")
    editor.add_state("isolado", "Isolado")  # No transitions to/from this state
    editor.add_transition("novo", "aprovado")

    is_valid = editor.validate()

    assert not is_valid
    errors = editor.get_validation_errors()
    assert any("unreachable" in err.lower() for err in errors)


def test_validate_valid_kanban(editor):
    """Test validation passes for valid kanban"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo", type="initial")
    editor.add_state("em_analise", "Em Análise")
    editor.add_state("aprovado", "Aprovado", type="final")
    editor.add_transition("novo", "em_analise")
    editor.add_transition("em_analise", "aprovado")

    is_valid = editor.validate()

    assert is_valid
    assert len(editor.get_validation_errors()) == 0


# ========== Save/Export Tests ==========


def test_save_to_registry(editor, mock_registry):
    """Test saving kanban to registry"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo", type="initial")
    editor.add_state("aprovado", "Aprovado", type="final")
    editor.add_transition("novo", "aprovado")

    success = editor.save()

    assert success
    assert mock_registry.get_kanban("test") is not None


def test_save_invalid_kanban_fails(editor):
    """Test saving invalid kanban fails"""
    editor.create_kanban("test", "Test")
    # Empty kanban is invalid

    with pytest.raises(ValueError, match="validation failed"):
        editor.save(validate=True)


def test_save_without_validation(editor, mock_registry):
    """Test saving without validation allows invalid kanban"""
    editor.create_kanban("test", "Test")
    # Empty kanban is invalid but we skip validation

    success = editor.save(validate=False)

    assert success


def test_save_to_file(editor):
    """Test saving kanban to JSON file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test_kanban.json")

        editor.create_kanban("test", "Test")
        editor.add_state("novo", "Novo", type="initial")
        editor.save_to_file(file_path)

        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["id"] == "test"
        assert "novo" in saved_data["states"]


def test_to_dict(editor):
    """Test exporting kanban to dictionary"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    kanban_dict = editor.to_dict()

    assert kanban_dict["id"] == "test"
    assert "novo" in kanban_dict["states"]


def test_to_json(editor):
    """Test exporting kanban to JSON string"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")

    json_str = editor.to_json()
    parsed = json.loads(json_str)

    assert parsed["id"] == "test"
    assert "novo" in parsed["states"]


# ========== Load Kanban Tests ==========


def test_load_kanban(editor, mock_registry):
    """Test loading existing kanban"""
    # Pre-populate registry
    kanban_def = {
        "id": "existing",
        "name": "Existing Kanban",
        "states": {"novo": {"name": "Novo", "type": "initial", "transitions": []}},
        "initial_state": "novo",
        "form_mappings": [],
    }
    mock_registry.register_kanban(kanban_def)

    editor.load_kanban("existing")

    assert editor.current_kanban["id"] == "existing"
    assert "novo" in editor.current_kanban["states"]


def test_load_nonexistent_kanban_fails(editor):
    """Test loading nonexistent kanban fails"""
    with pytest.raises(ValueError, match="not found"):
        editor.load_kanban("nonexistent")


# ========== Utility Methods Tests ==========


def test_get_state_count(editor):
    """Test getting state count"""
    editor.create_kanban("test", "Test")
    assert editor.get_state_count() == 0

    editor.add_state("novo", "Novo")
    assert editor.get_state_count() == 1

    editor.add_state("aprovado", "Aprovado")
    assert editor.get_state_count() == 2


def test_get_transition_count(editor):
    """Test getting transition count"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("aprovado", "Aprovado")
    assert editor.get_transition_count() == 0

    editor.add_transition("novo", "aprovado")
    assert editor.get_transition_count() == 1


def test_list_states(editor):
    """Test listing all states"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo")
    editor.add_state("aprovado", "Aprovado")

    states = editor.list_states()

    assert "novo" in states
    assert "aprovado" in states
    assert len(states) == 2


def test_get_state_details(editor):
    """Test getting state details"""
    editor.create_kanban("test", "Test")
    editor.add_state("novo", "Novo", color="#FF0000")

    details = editor.get_state_details("novo")

    assert details["name"] == "Novo"
    assert details["color"] == "#FF0000"


# ========== Fluent API Tests ==========


def test_fluent_api_chaining(editor):
    """Test complete fluent API workflow"""
    editor.create_kanban("vendas", "Kanban de Vendas").add_state(
        "lead", "Lead", type="initial"
    ).add_state("contato", "Contato").add_state("proposta", "Proposta").add_state(
        "fechado", "Fechado", type="final"
    ).add_transition(
        "lead", "contato"
    ).add_transition(
        "contato", "proposta"
    ).add_transition(
        "proposta", "fechado"
    ).map_form(
        "vendas"
    )

    assert editor.current_kanban["id"] == "vendas"
    assert len(editor.current_kanban["states"]) == 4
    assert "vendas" in editor.current_kanban["form_mappings"]
    assert editor.validate()
