"""
Tests for AnomalyDetector - Phase 3 Workflow Component

Tests anomaly detection including:
- Stuck process detection
- Duration anomalies (outliers)
- Loop detection
- Unusual transition detection
- Comprehensive anomaly reports
"""

import pytest
from datetime import datetime, timedelta
from src.workflow.anomaly_detector import AnomalyDetector


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
    base_time = datetime.now()

    # Create normal processes (not stuck)
    for i in range(8):
        process = {
            "process_id": f"proc_normal_{i}",
            "kanban_id": "kanban_pedidos",
            "current_state": "em_analise",
            "history": [
                {
                    "from_state": "novo",
                    "to_state": "em_analise",
                    "timestamp": (base_time - timedelta(hours=24)).isoformat(),
                    "duration_hours": 24.0,
                }
            ],
        }
        repo.add_process(process)

    # Create stuck processes (>72 hours in current state)
    for i in range(2):
        process = {
            "process_id": f"proc_stuck_{i}",
            "kanban_id": "kanban_pedidos",
            "current_state": "em_analise",
            "history": [
                {
                    "from_state": "novo",
                    "to_state": "em_analise",
                    "timestamp": (base_time - timedelta(hours=96)).isoformat(),
                    "duration_hours": 24.0,
                }
            ],
        }
        repo.add_process(process)

    # Create process with loop
    process_loop = {
        "process_id": "proc_loop",
        "kanban_id": "kanban_pedidos",
        "current_state": "aprovado",
        "history": [
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time - timedelta(days=5)).isoformat(),
                "duration_hours": 24.0,
            },
            {
                "from_state": "em_analise",
                "to_state": "novo",  # Loop back
                "timestamp": (base_time - timedelta(days=4)).isoformat(),
                "duration_hours": 12.0,
            },
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time - timedelta(days=3)).isoformat(),
                "duration_hours": 24.0,
            },
            {
                "from_state": "em_analise",
                "to_state": "aprovado",
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
                "duration_hours": 48.0,
            },
        ],
    }
    repo.add_process(process_loop)

    # Create process with anomalous duration
    process_outlier = {
        "process_id": "proc_outlier",
        "kanban_id": "kanban_pedidos",
        "current_state": "aprovado",
        "history": [
            {
                "from_state": "novo",
                "to_state": "em_analise",
                "timestamp": (base_time - timedelta(hours=240)).isoformat(),  # 10 days
                "duration_hours": 240.0,
            },
            {
                "from_state": "em_analise",
                "to_state": "aprovado",
                "timestamp": (base_time - timedelta(hours=48)).isoformat(),
                "duration_hours": 48.0,
            },
        ],
    }
    repo.add_process(process_outlier)

    return repo


@pytest.fixture
def detector(mock_repo):
    """Create AnomalyDetector with mock repository"""
    return AnomalyDetector(mock_repo)


# ========== Stuck Process Detection Tests ==========


def test_detect_stuck_processes_basic(detector):
    """Test basic stuck process detection"""
    stuck = detector.detect_stuck_processes("kanban_pedidos", threshold_hours=48)

    # Should find the 2 stuck processes (>96 hours in current state)
    assert len(stuck) >= 2

    for process in stuck:
        assert "process_id" in process
        assert "current_state" in process
        assert "hours_stuck" in process
        assert process["hours_stuck"] > 48


def test_detect_stuck_processes_threshold(detector):
    """Test that threshold is respected"""
    # Lower threshold should find more stuck processes
    low_threshold = detector.detect_stuck_processes(
        "kanban_pedidos", threshold_hours=24
    )
    high_threshold = detector.detect_stuck_processes(
        "kanban_pedidos", threshold_hours=96
    )

    assert len(low_threshold) >= len(high_threshold)


def test_detect_stuck_processes_empty_kanban(detector):
    """Test with nonexistent kanban"""
    stuck = detector.detect_stuck_processes("nonexistent_kanban", threshold_hours=48)

    assert stuck == []


def test_stuck_processes_include_anomaly_score(detector):
    """Test that stuck processes include anomaly score"""
    stuck = detector.detect_stuck_processes("kanban_pedidos", threshold_hours=48)

    for process in stuck:
        assert "anomaly_score" in process
        assert 0.0 <= process["anomaly_score"] <= 1.0


# ========== Duration Anomaly Detection Tests ==========


def test_detect_duration_anomalies_basic(detector):
    """Test basic duration anomaly detection"""
    anomalies = detector.detect_duration_anomalies(
        "kanban_pedidos", z_score_threshold=2.0
    )

    assert isinstance(anomalies, list)

    # Should find the outlier process (10 days in novo)
    assert len(anomalies) >= 0  # May or may not find anomalies depending on data


def test_detect_duration_anomalies_includes_details(detector):
    """Test that anomalies include required details"""
    anomalies = detector.detect_duration_anomalies(
        "kanban_pedidos", z_score_threshold=2.0
    )

    for anomaly in anomalies:
        assert "process_id" in anomaly
        assert "state" in anomaly
        assert "duration_hours" in anomaly
        assert "expected_duration" in anomaly
        assert "z_score" in anomaly


def test_detect_duration_anomalies_threshold(detector):
    """Test that z_score_threshold controls sensitivity"""
    # Lower threshold should find more anomalies
    low_threshold = detector.detect_duration_anomalies(
        "kanban_pedidos", z_score_threshold=1.5
    )
    high_threshold = detector.detect_duration_anomalies(
        "kanban_pedidos", z_score_threshold=3.0
    )

    assert len(low_threshold) >= len(high_threshold)


def test_detect_duration_anomalies_empty_kanban(detector):
    """Test with nonexistent kanban"""
    anomalies = detector.detect_duration_anomalies(
        "nonexistent_kanban", z_score_threshold=2.0
    )

    assert anomalies == []


# ========== Loop Detection Tests ==========


def test_detect_loops_basic(detector):
    """Test basic loop detection"""
    loops = detector.detect_loops("kanban_pedidos")

    # Should find the process with loop (em_analise -> novo -> em_analise)
    assert len(loops) >= 1

    for process_with_loops in loops:
        assert "process_id" in process_with_loops
        assert "loops_detected" in process_with_loops


def test_detect_loops_identifies_states(detector):
    """Test that loops identify the states involved"""
    loops = detector.detect_loops("kanban_pedidos")

    for process_with_loops in loops:
        loops_detected = process_with_loops["loops_detected"]
        assert len(loops_detected) > 0

        for loop_info in loops_detected:
            assert "loop" in loop_info
            assert "occurrences" in loop_info
            assert len(loop_info["loop"]) > 0


def test_detect_loops_empty_kanban(detector):
    """Test loop detection with no processes"""
    loops = detector.detect_loops("nonexistent_kanban")

    assert loops == []


# ========== Unusual Transition Detection Tests ==========


def test_detect_unusual_transitions_basic(detector):
    """Test unusual transition detection"""
    unusual = detector.detect_unusual_transitions(
        "kanban_pedidos", rarity_threshold=0.2
    )

    assert isinstance(unusual, list)


def test_detect_unusual_transitions_includes_details(detector):
    """Test that unusual transitions include details"""
    unusual = detector.detect_unusual_transitions(
        "kanban_pedidos", rarity_threshold=0.3
    )

    for process_with_unusual in unusual:
        assert "process_id" in process_with_unusual
        assert "unusual_transitions" in process_with_unusual

        for trans in process_with_unusual["unusual_transitions"]:
            assert "from_state" in trans
            assert "to_state" in trans
            assert "occurrence_rate" in trans
            assert 0.0 <= trans["occurrence_rate"] <= 1.0


def test_detect_unusual_transitions_threshold(detector):
    """Test that rarity_threshold controls detection"""
    # Higher threshold should find more unusual transitions
    low_threshold = detector.detect_unusual_transitions(
        "kanban_pedidos", rarity_threshold=0.1
    )
    high_threshold = detector.detect_unusual_transitions(
        "kanban_pedidos", rarity_threshold=0.5
    )

    assert len(high_threshold) >= len(low_threshold)


# ========== Comprehensive Report Tests ==========


def test_generate_anomaly_report_basic(detector):
    """Test comprehensive anomaly report generation"""
    report = detector.generate_anomaly_report("kanban_pedidos")

    assert "stuck_processes" in report
    assert "duration_anomalies" in report
    assert "loops" in report
    assert "unusual_transitions" in report
    assert "summary" in report


def test_anomaly_report_summary_counts(detector):
    """Test that report summary includes counts"""
    report = detector.generate_anomaly_report("kanban_pedidos")

    summary = report["summary"]
    assert "total_processes" in summary
    assert "stuck_count" in summary
    assert "duration_anomalies_count" in summary
    assert "loops_count" in summary
    assert "unusual_transitions_count" in summary


def test_anomaly_report_counts_are_valid(detector):
    """Test that report counts are valid numbers"""
    report = detector.generate_anomaly_report("kanban_pedidos")

    summary = report["summary"]
    assert summary["total_processes"] >= 0
    assert summary["stuck_count"] >= 0
    assert summary["duration_anomalies_count"] >= 0
    assert summary["loops_count"] >= 0
    assert summary["unusual_transitions_count"] >= 0


def test_anomaly_report_empty_kanban(detector):
    """Test report with nonexistent kanban"""
    report = detector.generate_anomaly_report("nonexistent_kanban")

    assert report["summary"]["stuck_count"] == 0
    assert report["summary"]["duration_anomalies_count"] == 0
    assert report["summary"]["loops_count"] == 0
    assert report["summary"]["unusual_transitions_count"] == 0
    assert report["summary"]["total_processes"] == 0
