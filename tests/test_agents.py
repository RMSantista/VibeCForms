"""
Tests for AI Agents and AgentOrchestrator - Phase 3 Workflow Component

Tests AI agents including:
- GenericAgent (heuristics-based)
- PatternAgent (pattern-based)
- RuleAgent (rule-based)
- AgentOrchestrator (multi-agent coordination)
"""

import pytest
from datetime import datetime, timedelta
from src.workflow.agents import GenericAgent, PatternAgent, RuleAgent, BaseAgent
from src.workflow.agent_orchestrator import AgentOrchestrator


class MockWorkflowRepository:
    """Mock repository for testing"""

    def __init__(self):
        self.processes = {}

    def add_process(self, process):
        """Add a process to the mock repository"""
        process_id = process["process_id"]
        self.processes[process_id] = process

    def get_process_by_id(self, process_id):
        """Get process by ID"""
        return self.processes.get(process_id)

    def get_all_processes(self, kanban_id=None):
        """Get all processes, optionally filtered by kanban_id"""
        if kanban_id:
            return [
                p for p in self.processes.values() if p.get("kanban_id") == kanban_id
            ]
        return list(self.processes.values())

    def get_processes_by_kanban(self, kanban_id):
        """Get processes by kanban_id"""
        return [p for p in self.processes.values() if p.get("kanban_id") == kanban_id]


class MockKanbanRegistry:
    """Mock kanban registry for testing"""

    def __init__(self):
        self.kanbans = {}
        self.transitions = {}

    def add_kanban(self, kanban_id, kanban_def):
        """Add a kanban definition"""
        self.kanbans[kanban_id] = kanban_def
        self.transitions[kanban_id] = {}

        # Build transitions map
        for state_id, state_def in kanban_def.get("states", {}).items():
            self.transitions[kanban_id][state_id] = state_def.get("transitions", [])

    def get_kanban(self, kanban_id):
        """Get kanban definition"""
        return self.kanbans.get(kanban_id)

    def get_available_transitions(self, kanban_id, from_state):
        """Get available transitions from a state"""
        if kanban_id not in self.transitions:
            return []
        if from_state not in self.transitions[kanban_id]:
            return []

        return [{"to": t} for t in self.transitions[kanban_id][from_state]]

    def can_transition(self, kanban_id, from_state, to_state):
        """Check if transition is allowed"""
        available = self.get_available_transitions(kanban_id, from_state)
        return any(t["to"] == to_state for t in available)

    def get_state(self, kanban_id, state_id):
        """Get state definition"""
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return None
        return kanban.get("states", {}).get(state_id)

    def get_transition(self, kanban_id, from_state, to_state):
        """Get transition definition"""
        state_def = self.get_state(kanban_id, from_state)
        if not state_def:
            return None

        transitions = state_def.get("transitions", [])
        if to_state in transitions:
            return {"prerequisites": []}  # Simplified for testing
        return None


class MockPatternAnalyzer:
    """Mock pattern analyzer for testing"""

    def analyze_transition_patterns(self, kanban_id, min_support=0.3):
        """Return mock patterns"""
        return [
            {
                "pattern": ["novo", "em_analise", "aprovado"],
                "support": 0.85,
                "confidence": 0.92,
                "count": 10,
            }
        ]

    def find_similar_processes(self, process_id, kanban_id, limit=3):
        """Return mock similar processes"""
        return [
            {
                "process_id": "similar_1",
                "similarity": 0.95,
                "sequence": ["novo", "em_analise", "aprovado"],
            }
        ]


class MockPrerequisiteChecker:
    """Mock prerequisite checker for testing"""

    def check_prerequisites(self, prerequisites, process, kanban):
        """Return mock prerequisite results"""
        return [{"satisfied": True, "type": "field_check", "message": "OK"}]

    def are_all_satisfied(self, results):
        """Check if all prerequisites are satisfied"""
        return all(r.get("satisfied", False) for r in results)

    def get_unsatisfied(self, results):
        """Get unsatisfied prerequisites"""
        return [r for r in results if not r.get("satisfied", False)]


@pytest.fixture
def mock_repo():
    """Create a mock repository with sample data"""
    repo = MockWorkflowRepository()
    base_time = datetime.now()

    # Process with high field completeness
    process_complete = {
        "process_id": "proc_complete",
        "kanban_id": "kanban_pedidos",
        "current_state": "novo",
        "field_values": {
            "cliente": "João Silva",
            "valor": 1000.0,
            "descricao": "Pedido teste",
            "data": "2025-01-01",
        },
        "history": [],
        "created_at": (base_time - timedelta(hours=2)).isoformat(),
    }
    repo.add_process(process_complete)

    # Process with low field completeness
    process_incomplete = {
        "process_id": "proc_incomplete",
        "kanban_id": "kanban_pedidos",
        "current_state": "novo",
        "field_values": {
            "cliente": "Maria Santos",
            "valor": None,
            "descricao": "",
            "data": None,
        },
        "history": [],
        "created_at": (base_time - timedelta(hours=1)).isoformat(),
    }
    repo.add_process(process_incomplete)

    # Process with history
    process_with_history = {
        "process_id": "proc_history",
        "kanban_id": "kanban_pedidos",
        "current_state": "em_analise",
        "field_values": {"cliente": "Pedro Lima", "valor": 500.0},
        "history": [
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time - timedelta(days=1)).isoformat(),
                "duration_hours": 24.0,
            }
        ],
        "created_at": (base_time - timedelta(days=2)).isoformat(),
    }
    repo.add_process(process_with_history)

    return repo


@pytest.fixture
def mock_registry():
    """Create a mock kanban registry"""
    registry = MockKanbanRegistry()

    kanban_def = {
        "id": "kanban_pedidos",
        "name": "Kanban de Pedidos",
        "states": {
            "novo": {
                "name": "Novo",
                "transitions": ["em_analise"],
                "auto_transition_to": None,
            },
            "em_analise": {
                "name": "Em Análise",
                "transitions": ["aprovado", "rejeitado"],
                "auto_transition_to": None,
            },
            "aprovado": {
                "name": "Aprovado",
                "transitions": [],
                "auto_transition_to": None,
            },
            "rejeitado": {
                "name": "Rejeitado",
                "transitions": [],
                "auto_transition_to": None,
            },
        },
    }
    registry.add_kanban("kanban_pedidos", kanban_def)

    return registry


@pytest.fixture
def mock_pattern_analyzer():
    """Create mock pattern analyzer"""
    return MockPatternAnalyzer()


@pytest.fixture
def mock_prerequisite_checker():
    """Create mock prerequisite checker"""
    return MockPrerequisiteChecker()


# ========== GenericAgent Tests ==========


def test_generic_agent_analyze_context(mock_repo, mock_registry):
    """Test GenericAgent context analysis"""
    agent = GenericAgent(mock_repo, mock_registry)
    context = agent.analyze_context("proc_complete")

    assert "field_completeness" in context
    assert "time_in_current_state" in context
    assert "transition_count" in context
    assert "available_transitions" in context


def test_generic_agent_suggest_low_completeness(mock_repo, mock_registry):
    """Test GenericAgent suggestion for low field completeness"""
    agent = GenericAgent(mock_repo, mock_registry)
    suggestion = agent.suggest_transition("proc_incomplete")

    # Should suggest staying due to low completeness (<50%)
    assert suggestion["suggested_state"] is None
    assert suggestion["confidence"] < 0.5


def test_generic_agent_suggest_single_transition(mock_repo, mock_registry):
    """Test GenericAgent suggestion with single available transition"""
    agent = GenericAgent(mock_repo, mock_registry)
    suggestion = agent.suggest_transition("proc_complete")

    # Should suggest the only available transition
    assert suggestion["suggested_state"] == "em_analise"
    assert suggestion["confidence"] > 0.5


def test_generic_agent_validate_transition(mock_repo, mock_registry):
    """Test GenericAgent transition validation"""
    agent = GenericAgent(mock_repo, mock_registry)
    validation = agent.validate_transition("proc_complete", "em_analise")

    assert "valid" in validation
    assert "warnings" in validation
    assert "risk_level" in validation


# ========== PatternAgent Tests ==========


def test_pattern_agent_analyze_context(mock_repo, mock_registry, mock_pattern_analyzer):
    """Test PatternAgent context analysis"""
    agent = PatternAgent(mock_repo, mock_registry, mock_pattern_analyzer)
    context = agent.analyze_context("proc_history")

    assert "current_sequence" in context
    assert "matching_patterns" in context
    assert "similar_processes" in context
    assert "common_next_states" in context


def test_pattern_agent_suggest_transition(
    mock_repo, mock_registry, mock_pattern_analyzer
):
    """Test PatternAgent suggestion based on patterns"""
    agent = PatternAgent(mock_repo, mock_registry, mock_pattern_analyzer)
    suggestion = agent.suggest_transition("proc_history")

    assert "suggested_state" in suggestion
    assert "confidence" in suggestion
    assert "justification" in suggestion


def test_pattern_agent_validate_transition(
    mock_repo, mock_registry, mock_pattern_analyzer
):
    """Test PatternAgent transition validation"""
    agent = PatternAgent(mock_repo, mock_registry, mock_pattern_analyzer)
    validation = agent.validate_transition("proc_history", "aprovado")

    assert "valid" in validation
    assert "warnings" in validation
    assert "risk_level" in validation


# ========== RuleAgent Tests ==========


def test_rule_agent_analyze_context(
    mock_repo, mock_registry, mock_prerequisite_checker
):
    """Test RuleAgent context analysis"""
    agent = RuleAgent(mock_repo, mock_registry, mock_prerequisite_checker)
    context = agent.analyze_context("proc_complete")

    assert "available_transitions" in context
    assert "transition_readiness" in context
    assert "auto_transition_available" in context


def test_rule_agent_suggest_transition(
    mock_repo, mock_registry, mock_prerequisite_checker
):
    """Test RuleAgent suggestion based on rules"""
    agent = RuleAgent(mock_repo, mock_registry, mock_prerequisite_checker)
    suggestion = agent.suggest_transition("proc_complete")

    assert "suggested_state" in suggestion
    assert "confidence" in suggestion
    assert "justification" in suggestion


def test_rule_agent_validate_transition(
    mock_repo, mock_registry, mock_prerequisite_checker
):
    """Test RuleAgent transition validation"""
    agent = RuleAgent(mock_repo, mock_registry, mock_prerequisite_checker)
    validation = agent.validate_transition("proc_complete", "em_analise")

    assert "valid" in validation
    assert "warnings" in validation
    assert "risk_level" in validation


# ========== AgentOrchestrator Tests ==========


def test_orchestrator_get_best_agent(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator agent selection"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    best_agent = orchestrator.get_best_agent_for_process("proc_complete")
    assert best_agent in ["generic", "pattern", "rule"]


def test_orchestrator_analyze_with_agent(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator single agent analysis"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    result = orchestrator.analyze_with_agent("proc_complete", "generic")

    assert "agent_used" in result
    assert result["agent_used"] == "generic"
    assert "context" in result
    assert "suggestion" in result


def test_orchestrator_analyze_with_all_agents(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator multi-agent analysis"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    result = orchestrator.analyze_with_all_agents("proc_complete")

    assert "process_id" in result
    assert "agents" in result
    assert "consensus" in result
    assert "best_suggestion" in result

    # Should have results from all 3 agents
    assert "generic" in result["agents"]
    assert "pattern" in result["agents"]
    assert "rule" in result["agents"]


def test_orchestrator_consensus_calculation(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator consensus calculation"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    result = orchestrator.analyze_with_all_agents("proc_complete")
    consensus = result["consensus"]

    assert "suggested_states" in consensus
    assert "consensus_state" in consensus
    assert "agreement_level" in consensus
    assert consensus["agreement_level"] in ["none", "low", "medium", "high"]


def test_orchestrator_validate_with_all_agents(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator multi-agent validation"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    result = orchestrator.validate_transition_with_all_agents(
        "proc_complete", "em_analise"
    )

    assert "process_id" in result
    assert "target_state" in result
    assert "validations" in result
    assert "overall_valid" in result
    assert "max_risk_level" in result
    assert "all_warnings" in result


def test_orchestrator_auto_agent_selection(
    mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
):
    """Test orchestrator auto agent selection"""
    orchestrator = AgentOrchestrator(
        mock_repo, mock_registry, mock_pattern_analyzer, mock_prerequisite_checker
    )

    # Using 'auto' should select best agent automatically
    result = orchestrator.analyze_with_agent("proc_complete", "auto")

    assert result["agent_used"] in ["generic", "pattern", "rule"]
    assert "context" in result
    assert "suggestion" in result


# ========== BaseAgent Tests ==========


def test_base_agent_is_abstract():
    """Test that BaseAgent cannot be instantiated directly"""
    with pytest.raises(TypeError):
        BaseAgent(None, None)


def test_agent_suggestion_format(mock_repo, mock_registry):
    """Test that all agents return properly formatted suggestions"""
    agent = GenericAgent(mock_repo, mock_registry)
    suggestion = agent.suggest_transition("proc_complete")

    # Required fields
    assert "suggested_state" in suggestion
    assert "confidence" in suggestion
    assert "justification" in suggestion
    assert "risk_factors" in suggestion

    # Confidence should be between 0 and 1
    assert 0.0 <= suggestion["confidence"] <= 1.0


def test_agent_validation_format(mock_repo, mock_registry):
    """Test that all agents return properly formatted validations"""
    agent = GenericAgent(mock_repo, mock_registry)
    validation = agent.validate_transition("proc_complete", "em_analise")

    # Required fields
    assert "valid" in validation
    assert "warnings" in validation
    assert "errors" in validation
    assert "risk_level" in validation

    # Risk level should be valid
    assert validation["risk_level"] in ["low", "medium", "high"]
