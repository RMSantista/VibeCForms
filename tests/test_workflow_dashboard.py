"""
Tests for WorkflowDashboard - Phase 4 Workflow Component

Tests analytics and monitoring dashboard including:
- Kanban health metrics
- Process statistics
- Bottleneck identification
- Agent performance tracking
- Dashboard summary generation
"""

import pytest
from datetime import datetime, timedelta
from src.workflow.workflow_dashboard import WorkflowDashboard


class MockWorkflowRepository:
    """Mock workflow repository for testing"""

    def __init__(self):
        self.processes = []

    def add_process(self, process):
        """Add a process to the repository"""
        self.processes.append(process)

    def get_processes_by_kanban(self, kanban_id):
        """Get processes by kanban_id"""
        return [p for p in self.processes if p.get("kanban_id") == kanban_id]


class MockKanbanRegistry:
    """Mock kanban registry for testing"""

    def __init__(self):
        self.kanbans = {}

    def add_kanban(self, kanban_id, kanban_def):
        """Add a kanban definition"""
        self.kanbans[kanban_id] = kanban_def

    def get_kanban(self, kanban_id):
        """Get kanban definition"""
        return self.kanbans.get(kanban_id)

    def get_state(self, kanban_id, state_id):
        """Get state definition"""
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return None
        return kanban.get("states", {}).get(state_id)


class MockPatternAnalyzer:
    """Mock pattern analyzer for testing"""

    def analyze_state_durations(self, kanban_id):
        """Return mock state durations"""
        return {
            "novo": {
                "avg_hours": 10.0,
                "min_hours": 5.0,
                "max_hours": 15.0,
                "std_dev": 3.0,
                "sample_count": 10,
            },
            "em_analise": {
                "avg_hours": 48.0,
                "min_hours": 12.0,
                "max_hours": 96.0,
                "std_dev": 20.0,
                "sample_count": 8,
            },
        }


class MockAnomalyDetector:
    """Mock anomaly detector for testing"""

    def __init__(self):
        self.stuck_count = 0
        self.loops_count = 0
        self.duration_anomalies_count = 0
        self.unusual_transitions_count = 0

    def generate_anomaly_report(self, kanban_id):
        """Return mock anomaly report"""
        return {
            "kanban_id": kanban_id,
            "summary": {
                "stuck_count": self.stuck_count,
                "loops_count": self.loops_count,
                "duration_anomalies_count": self.duration_anomalies_count,
                "unusual_transitions_count": self.unusual_transitions_count,
            },
        }


class MockAgentOrchestrator:
    """Mock agent orchestrator for testing"""

    def analyze_with_all_agents(self, process_id):
        """Return mock multi-agent analysis"""
        return {
            "process_id": process_id,
            "agents": {
                "generic": {
                    "suggestion": {"suggested_state": "aprovado", "confidence": 0.85}
                },
                "pattern": {
                    "suggestion": {"suggested_state": "aprovado", "confidence": 0.90}
                },
                "rule": {
                    "suggestion": {"suggested_state": "aprovado", "confidence": 0.75}
                },
            },
            "consensus": {"suggested_state": "aprovado", "agreement_level": "high"},
        }


@pytest.fixture
def mock_repo():
    """Create mock repository with sample processes"""
    repo = MockWorkflowRepository()
    base_time = datetime.now()

    # Completed processes
    for i in range(10):
        repo.add_process(
            {
                "process_id": f"proc_completed_{i}",
                "kanban_id": "kanban_test",
                "current_state": "aprovado",
                "created_at": (base_time - timedelta(days=i + 1)).isoformat(),
                "history": [
                    {
                        "from_state": "novo",
                        "to_state": "aprovado",
                        "timestamp": (base_time - timedelta(days=i)).isoformat(),
                        "duration_hours": 24.0,
                    }
                ],
            }
        )

    # Active processes
    for i in range(5):
        repo.add_process(
            {
                "process_id": f"proc_active_{i}",
                "kanban_id": "kanban_test",
                "current_state": "em_analise",
                "created_at": (base_time - timedelta(hours=i + 1)).isoformat(),
                "history": [],
            }
        )

    return repo


@pytest.fixture
def mock_registry():
    """Create mock kanban registry"""
    registry = MockKanbanRegistry()
    registry.add_kanban(
        "kanban_test",
        {
            "id": "kanban_test",
            "name": "Test Kanban",
            "states": {
                "novo": {"name": "Novo", "type": "initial"},
                "em_analise": {"name": "Em Análise", "type": "intermediate"},
                "aprovado": {"name": "Aprovado", "type": "final"},
                "rejeitado": {"name": "Rejeitado", "type": "final"},
            },
        },
    )
    return registry


@pytest.fixture
def mock_pattern_analyzer():
    """Create mock pattern analyzer"""
    return MockPatternAnalyzer()


@pytest.fixture
def mock_anomaly_detector():
    """Create mock anomaly detector"""
    return MockAnomalyDetector()


@pytest.fixture
def mock_orchestrator():
    """Create mock agent orchestrator"""
    return MockAgentOrchestrator()


@pytest.fixture
def dashboard(
    mock_repo,
    mock_registry,
    mock_pattern_analyzer,
    mock_anomaly_detector,
    mock_orchestrator,
):
    """Create WorkflowDashboard instance"""
    return WorkflowDashboard(
        mock_repo,
        mock_registry,
        mock_pattern_analyzer,
        mock_anomaly_detector,
        mock_orchestrator,
    )


# ========== Kanban Health Tests ==========


def test_get_kanban_health(dashboard):
    """Test getting kanban health metrics"""
    health = dashboard.get_kanban_health("kanban_test")

    assert "kanban_id" in health
    assert health["kanban_id"] == "kanban_test"
    assert "health_score" in health
    assert "status" in health
    assert "metrics" in health
    assert "issues" in health
    assert "recommendations" in health


def test_health_metrics_structure(dashboard):
    """Test health metrics structure"""
    health = dashboard.get_kanban_health("kanban_test")
    metrics = health["metrics"]

    assert "total_processes" in metrics
    assert "active_processes" in metrics
    assert "completed_processes" in metrics
    assert "stuck_processes" in metrics
    assert "avg_completion_time_hours" in metrics
    assert "throughput_per_day" in metrics


def test_health_score_calculation(dashboard):
    """Test health score is between 0 and 1"""
    health = dashboard.get_kanban_health("kanban_test")

    assert 0.0 <= health["health_score"] <= 1.0


def test_health_status_mapping(dashboard):
    """Test health status is valid"""
    health = dashboard.get_kanban_health("kanban_test")

    assert health["status"] in ["healthy", "warning", "critical"]


def test_health_with_stuck_processes(dashboard, mock_anomaly_detector):
    """Test health score decreases with stuck processes"""
    mock_anomaly_detector.stuck_count = 5

    health = dashboard.get_kanban_health("kanban_test")

    # Should have issue for stuck processes
    stuck_issues = [i for i in health["issues"] if i["type"] == "stuck_processes"]
    assert len(stuck_issues) > 0
    assert stuck_issues[0]["count"] == 5


def test_health_with_loops(dashboard, mock_anomaly_detector):
    """Test health detects loops"""
    mock_anomaly_detector.loops_count = 3

    health = dashboard.get_kanban_health("kanban_test")

    loop_issues = [i for i in health["issues"] if i["type"] == "loops"]
    assert len(loop_issues) > 0
    assert loop_issues[0]["count"] == 3


def test_health_recommendations(dashboard, mock_anomaly_detector):
    """Test health generates recommendations"""
    mock_anomaly_detector.stuck_count = 2

    health = dashboard.get_kanban_health("kanban_test")

    assert len(health["recommendations"]) > 0
    assert any("stuck" in rec.lower() for rec in health["recommendations"])


# ========== Process Statistics Tests ==========


def test_get_process_stats(dashboard):
    """Test getting process statistics"""
    stats = dashboard.get_process_stats("kanban_test", days=30)

    assert "period_days" in stats
    assert stats["period_days"] == 30
    assert "created" in stats
    assert "completed" in stats
    assert "active" in stats
    assert "completion_rate" in stats
    assert "avg_cycle_time_hours" in stats
    assert "states_distribution" in stats
    assert "daily_throughput" in stats


def test_process_stats_counts(dashboard):
    """Test process statistics counts"""
    stats = dashboard.get_process_stats("kanban_test", days=30)

    # Should have 15 total processes (10 completed + 5 active)
    assert stats["created"] == 15
    assert stats["completed"] == 10
    assert stats["active"] == 5


def test_completion_rate_calculation(dashboard):
    """Test completion rate calculation"""
    stats = dashboard.get_process_stats("kanban_test", days=30)

    # 10 completed out of 15 total = 0.667
    assert 0.6 <= stats["completion_rate"] <= 0.7


def test_states_distribution(dashboard):
    """Test states distribution"""
    stats = dashboard.get_process_stats("kanban_test", days=30)
    dist = stats["states_distribution"]

    assert "aprovado" in dist
    assert "em_analise" in dist


def test_daily_throughput_structure(dashboard):
    """Test daily throughput structure"""
    stats = dashboard.get_process_stats("kanban_test", days=30)
    throughput = stats["daily_throughput"]

    assert isinstance(throughput, dict)


# ========== Bottleneck Identification Tests ==========


def test_identify_bottlenecks(dashboard):
    """Test bottleneck identification"""
    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    assert "bottleneck_states" in bottlenecks
    assert "recommendations" in bottlenecks


def test_bottleneck_states_structure(dashboard):
    """Test bottleneck states structure"""
    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    if bottlenecks["bottleneck_states"]:
        bottleneck = bottlenecks["bottleneck_states"][0]
        assert "state_id" in bottleneck
        assert "avg_duration_hours" in bottleneck
        assert "min_duration_hours" in bottleneck
        assert "slowdown_factor" in bottleneck
        assert "process_count" in bottleneck


def test_bottleneck_detection_threshold(dashboard):
    """Test bottleneck detection uses 2x threshold"""
    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    # em_analise has avg=48h, min=12h -> slowdown=4.0 > 2.0
    # Should be detected as bottleneck
    bottleneck_ids = [b["state_id"] for b in bottlenecks["bottleneck_states"]]
    assert "em_analise" in bottleneck_ids


def test_bottleneck_sorting(dashboard):
    """Test bottlenecks are sorted by slowdown factor"""
    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    if len(bottlenecks["bottleneck_states"]) > 1:
        factors = [b["slowdown_factor"] for b in bottlenecks["bottleneck_states"]]
        # Should be sorted descending
        assert factors == sorted(factors, reverse=True)


def test_bottleneck_recommendations(dashboard):
    """Test bottleneck generates recommendations"""
    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    if bottlenecks["bottleneck_states"]:
        assert len(bottlenecks["recommendations"]) > 0


# ========== Agent Performance Tests ==========


def test_get_agent_performance(dashboard):
    """Test getting agent performance metrics"""
    # Note: This test will skip processes without valid data
    performance = dashboard.get_agent_performance("kanban_test", sample_size=5)

    assert "sample_size" in performance
    assert "agents" in performance
    assert "consensus" in performance


def test_agent_performance_structure(dashboard):
    """Test agent performance structure"""
    performance = dashboard.get_agent_performance("kanban_test", sample_size=3)

    agents = performance["agents"]
    assert "generic" in agents
    assert "pattern" in agents
    assert "rule" in agents


def test_agent_metrics(dashboard):
    """Test individual agent metrics"""
    performance = dashboard.get_agent_performance("kanban_test", sample_size=3)

    for agent_name in ["generic", "pattern", "rule"]:
        agent = performance["agents"][agent_name]
        assert "avg_confidence" in agent
        assert "suggestion_count" in agent
        assert "high_confidence_count" in agent


def test_consensus_metrics(dashboard):
    """Test consensus metrics"""
    performance = dashboard.get_agent_performance("kanban_test", sample_size=3)

    consensus = performance["consensus"]
    assert "high_agreement_count" in consensus
    assert "high_agreement_rate" in consensus


# ========== Dashboard Summary Tests ==========


def test_get_dashboard_summary(dashboard):
    """Test getting complete dashboard summary"""
    summary = dashboard.get_dashboard_summary("kanban_test")

    assert "kanban_id" in summary
    assert summary["kanban_id"] == "kanban_test"
    assert "generated_at" in summary
    assert "health" in summary
    assert "statistics" in summary
    assert "bottlenecks" in summary


def test_dashboard_summary_completeness(dashboard):
    """Test dashboard summary includes all components"""
    summary = dashboard.get_dashboard_summary("kanban_test")

    # Should include health metrics
    assert "health_score" in summary["health"]
    assert "status" in summary["health"]

    # Should include statistics
    assert "created" in summary["statistics"]
    assert "completed" in summary["statistics"]

    # Should include bottlenecks
    assert "bottleneck_states" in summary["bottlenecks"]


def test_dashboard_summary_timestamp(dashboard):
    """Test dashboard summary includes valid timestamp"""
    summary = dashboard.get_dashboard_summary("kanban_test")

    # Should have ISO format timestamp
    timestamp = summary["generated_at"]
    # Should be parseable as datetime
    datetime.fromisoformat(timestamp)


# ========== Edge Cases Tests ==========


def test_health_with_no_processes(
    mock_registry, mock_pattern_analyzer, mock_anomaly_detector, mock_orchestrator
):
    """Test health calculation with no processes"""
    empty_repo = MockWorkflowRepository()
    dashboard = WorkflowDashboard(
        empty_repo,
        mock_registry,
        mock_pattern_analyzer,
        mock_anomaly_detector,
        mock_orchestrator,
    )

    health = dashboard.get_kanban_health("kanban_test")

    assert health["metrics"]["total_processes"] == 0
    # Health score should be 1.0 (perfect) when no processes
    assert health["health_score"] == 1.0


def test_stats_with_short_period(dashboard):
    """Test statistics with 7-day period"""
    stats = dashboard.get_process_stats("kanban_test", days=7)

    assert stats["period_days"] == 7
    # Should have fewer processes than 30-day period
    assert stats["created"] <= 15


def test_bottlenecks_with_insufficient_samples(
    mock_repo, mock_registry, mock_orchestrator, mock_anomaly_detector
):
    """Test bottleneck detection with insufficient samples"""
    # Create analyzer with low sample counts
    analyzer = MockPatternAnalyzer()
    # Override with low sample count
    analyzer.analyze_state_durations = lambda k: {
        "novo": {
            "avg_hours": 10.0,
            "min_hours": 5.0,
            "max_hours": 15.0,
            "std_dev": 3.0,
            "sample_count": 2,
        }  # Below threshold of 3
    }

    dashboard = WorkflowDashboard(
        mock_repo, mock_registry, analyzer, mock_anomaly_detector, mock_orchestrator
    )

    bottlenecks = dashboard.identify_bottlenecks("kanban_test")

    # Should not include states with sample_count < 3
    bottleneck_ids = [b["state_id"] for b in bottlenecks["bottleneck_states"]]
    assert "novo" not in bottleneck_ids


def test_agent_performance_with_errors(dashboard):
    """Test agent performance handles errors gracefully"""
    # Even if some processes fail to analyze, should return valid structure
    performance = dashboard.get_agent_performance("kanban_test", sample_size=20)

    assert "agents" in performance
    assert "consensus" in performance
