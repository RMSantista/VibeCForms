"""
Tests for PatternAnalyzer - Phase 3 Workflow Component

Tests pattern analysis including:
- Transition pattern mining
- Pattern classification
- Transition matrix building
- State duration analysis
- Similar process identification
"""

import pytest
from datetime import datetime, timedelta
from src.workflow.pattern_analyzer import PatternAnalyzer


class MockWorkflowRepository:
    """Mock repository for testing"""

    def __init__(self):
        self.processes = []

    def add_process(self, process):
        """Add a process to the mock repository"""
        self.processes.append(process)

    def get_all_processes(self, kanban_id=None):
        """Get all processes, optionally filtered by kanban_id"""
        if kanban_id:
            return [p for p in self.processes if p.get("kanban_id") == kanban_id]
        return self.processes

    def get_processes_by_kanban(self, kanban_id):
        """Get processes by kanban_id"""
        return [p for p in self.processes if p.get("kanban_id") == kanban_id]

    def get_process_by_id(self, process_id):
        """Get process by ID"""
        for p in self.processes:
            if p.get("process_id") == process_id:
                return p
        return None


@pytest.fixture
def mock_repo():
    """Create a mock repository with sample data"""
    repo = MockWorkflowRepository()

    # Create sample processes with common pattern: novo -> em_analise -> aprovado
    base_time = datetime.now() - timedelta(days=30)

    for i in range(10):
        process = {
            "process_id": f"proc_{i}",
            "kanban_id": "kanban_pedidos",
            "current_state": "aprovado",
            "history": [
                {
                    "from_state": "novo",
                    "to_state": "em_analise",
                    "timestamp": (base_time + timedelta(days=i)).isoformat(),
                    "duration_hours": 24.0,
                },
                {
                    "from_state": "em_analise",
                    "to_state": "aprovado",
                    "timestamp": (base_time + timedelta(days=i + 1)).isoformat(),
                    "duration_hours": 48.0,
                },
            ],
        }
        repo.add_process(process)

    # Add a few processes with different pattern: novo -> em_analise -> rejeitado
    for i in range(10, 13):
        process = {
            "process_id": f"proc_{i}",
            "kanban_id": "kanban_pedidos",
            "current_state": "rejeitado",
            "history": [
                {
                    "from_state": "novo",
                    "to_state": "em_analise",
                    "timestamp": (base_time + timedelta(days=i)).isoformat(),
                    "duration_hours": 24.0,
                },
                {
                    "from_state": "em_analise",
                    "to_state": "rejeitado",
                    "timestamp": (base_time + timedelta(days=i + 1)).isoformat(),
                    "duration_hours": 12.0,
                },
            ],
        }
        repo.add_process(process)

    # Add one anomaly with loop: novo -> em_analise -> novo -> em_analise -> aprovado
    process = {
        "process_id": "proc_loop",
        "kanban_id": "kanban_pedidos",
        "current_state": "aprovado",
        "history": [
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time + timedelta(days=20)).isoformat(),
                "duration_hours": 12.0,
            },
            {
                "from_state": "em_analise",
                "to_state": "novo",
                "timestamp": (base_time + timedelta(days=20, hours=12)).isoformat(),
                "duration_hours": 6.0,
            },
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time + timedelta(days=20, hours=18)).isoformat(),
                "duration_hours": 24.0,
            },
            {
                "from_state": "em_analise",
                "to_state": "aprovado",
                "timestamp": (base_time + timedelta(days=21, hours=18)).isoformat(),
                "duration_hours": 48.0,
            },
        ],
    }
    repo.add_process(process)

    return repo


@pytest.fixture
def analyzer(mock_repo):
    """Create PatternAnalyzer with mock repository"""
    return PatternAnalyzer(mock_repo)


# ========== Pattern Mining Tests ==========


def test_analyze_transition_patterns_basic(analyzer):
    """Test basic pattern analysis"""
    patterns = analyzer.analyze_transition_patterns("kanban_pedidos", min_support=0.5)

    # Should find the common pattern: novo -> em_analise -> aprovado (10/14 = 71%)
    assert len(patterns) > 0
    assert patterns[0]["support"] >= 0.5

    # Pattern should contain at least 2 transitions
    assert len(patterns[0]["pattern"]) >= 2


def test_analyze_transition_patterns_min_support(analyzer):
    """Test min_support threshold filtering"""
    # High threshold should return fewer patterns
    high_threshold = analyzer.analyze_transition_patterns(
        "kanban_pedidos", min_support=0.8
    )
    low_threshold = analyzer.analyze_transition_patterns(
        "kanban_pedidos", min_support=0.2
    )

    assert len(high_threshold) <= len(low_threshold)


def test_analyze_transition_patterns_empty_kanban(analyzer):
    """Test pattern analysis with no processes"""
    patterns = analyzer.analyze_transition_patterns(
        "nonexistent_kanban", min_support=0.3
    )

    assert patterns == []


def test_pattern_contains_confidence(analyzer):
    """Test that patterns include confidence scores"""
    patterns = analyzer.analyze_transition_patterns("kanban_pedidos", min_support=0.3)

    for pattern in patterns:
        assert "confidence" in pattern
        assert 0.0 <= pattern["confidence"] <= 1.0


def test_pattern_contains_avg_duration(analyzer):
    """Test that patterns include average duration"""
    patterns = analyzer.analyze_transition_patterns("kanban_pedidos", min_support=0.3)

    for pattern in patterns:
        assert "avg_duration_hours" in pattern
        assert pattern["avg_duration_hours"] >= 0


# ========== Pattern Classification Tests ==========


def test_classify_patterns_basic(analyzer):
    """Test pattern classification"""
    patterns = analyzer.analyze_transition_patterns("kanban_pedidos", min_support=0.3)
    classified = analyzer.classify_patterns(patterns)

    assert "common" in classified
    assert "problematic" in classified
    assert "exceptional" in classified


def test_classify_patterns_common_threshold(analyzer):
    """Test that common patterns have high support"""
    patterns = analyzer.analyze_transition_patterns("kanban_pedidos", min_support=0.3)
    classified = analyzer.classify_patterns(patterns)

    for pattern in classified["common"]:
        assert pattern["support"] >= 0.5


def test_classify_patterns_empty(analyzer):
    """Test classification with no patterns"""
    classified = analyzer.classify_patterns([])

    assert classified["common"] == []
    assert classified["problematic"] == []
    assert classified["exceptional"] == []


# ========== Transition Matrix Tests ==========


def test_build_transition_matrix_basic(analyzer):
    """Test transition matrix building"""
    matrix = analyzer.build_transition_matrix("kanban_pedidos")

    assert isinstance(matrix, dict)
    assert len(matrix) > 0

    # Check matrix structure - values are probabilities (floats)
    for from_state, transitions in matrix.items():
        assert isinstance(transitions, dict)
        for to_state, probability in transitions.items():
            assert isinstance(probability, float)
            assert 0.0 <= probability <= 1.0


def test_transition_matrix_probabilities_sum_to_one(analyzer):
    """Test that probabilities from each state sum to ~1.0"""
    matrix = analyzer.build_transition_matrix("kanban_pedidos")

    for from_state, transitions in matrix.items():
        total_prob = sum(transitions.values())  # Values are floats (probabilities)
        assert abs(total_prob - 1.0) < 0.01  # Allow small floating point errors


def test_transition_matrix_empty_kanban(analyzer):
    """Test matrix with no processes"""
    matrix = analyzer.build_transition_matrix("nonexistent_kanban")

    assert matrix == {}


# ========== State Duration Analysis Tests ==========


def test_analyze_state_durations_basic(analyzer):
    """Test state duration analysis"""
    durations = analyzer.analyze_state_durations("kanban_pedidos")

    assert isinstance(durations, dict)
    assert len(durations) > 0

    for state, stats in durations.items():
        assert "sample_count" in stats
        assert "avg_hours" in stats
        assert "min_hours" in stats
        assert "max_hours" in stats
        assert "std_dev" in stats


def test_state_durations_statistics_validity(analyzer):
    """Test that duration statistics are valid"""
    durations = analyzer.analyze_state_durations("kanban_pedidos")

    for state, stats in durations.items():
        # Min <= Avg <= Max
        assert stats["min_hours"] <= stats["avg_hours"]
        assert stats["avg_hours"] <= stats["max_hours"]

        # Std deviation >= 0
        assert stats["std_dev"] >= 0


def test_state_durations_empty_kanban(analyzer):
    """Test duration analysis with no processes"""
    durations = analyzer.analyze_state_durations("nonexistent_kanban")

    assert durations == {}


# ========== Similar Process Tests ==========


def test_find_similar_processes_basic(analyzer):
    """Test finding similar processes"""
    similar = analyzer.find_similar_processes("proc_0", "kanban_pedidos", limit=3)

    assert isinstance(similar, list)
    assert len(similar) <= 3


def test_find_similar_processes_excludes_self(analyzer):
    """Test that process doesn't match itself"""
    similar = analyzer.find_similar_processes("proc_0", "kanban_pedidos", limit=10)

    # Should not include the source process
    for match in similar:
        assert match["process_id"] != "proc_0"


def test_find_similar_processes_similarity_scores(analyzer):
    """Test that similarity scores are valid and sorted"""
    similar = analyzer.find_similar_processes("proc_0", "kanban_pedidos", limit=5)

    # All scores should be between 0 and 1
    for match in similar:
        assert "similarity" in match
        assert 0.0 <= match["similarity"] <= 1.0

    # Should be sorted by similarity (descending)
    if len(similar) > 1:
        for i in range(len(similar) - 1):
            assert similar[i]["similarity"] >= similar[i + 1]["similarity"]


def test_find_similar_processes_nonexistent(analyzer):
    """Test with nonexistent process"""
    similar = analyzer.find_similar_processes("nonexistent", "kanban_pedidos", limit=3)

    assert similar == []


def test_find_similar_processes_includes_common_transitions(analyzer):
    """Test that results include common transitions"""
    similar = analyzer.find_similar_processes("proc_0", "kanban_pedidos", limit=3)

    for match in similar:
        assert "common_transitions" in match
        assert isinstance(match["common_transitions"], list)
