"""
Tests for Phase 5 Advanced Features - Workflow Components

Tests ML models, exporters, and audit trail including:
- WorkflowMLModel: Clustering, predictions, risk factors, reports
- Exporters: CSV, Excel, PDF generation
- AuditTrail: Logging, queries, compliance reporting
"""

import pytest
from datetime import datetime, timedelta
from src.workflow.workflow_ml_model import WorkflowMLModel
from src.workflow.exporters import CSVExporter, ExcelExporter, PDFExporter
from src.workflow.audit_trail import AuditTrail


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

    def get_process_by_id(self, process_id):
        """Get process by ID"""
        for proc in self.processes:
            if proc.get("process_id") == process_id:
                return proc
        return None


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
            "aprovado": {
                "avg_hours": 5.0,
                "min_hours": 2.0,
                "max_hours": 8.0,
                "std_dev": 2.0,
                "sample_count": 8,
            },
        }

    def find_similar_processes(self, process_id, kanban_id, limit=5):
        """Return mock similar processes"""
        return [
            {"process_id": "proc_0", "similarity": 0.9, "duration_hours": 24.0},
            {"process_id": "proc_1", "similarity": 0.85, "duration_hours": 34.0},
            {"process_id": "proc_2", "similarity": 0.8, "duration_hours": 44.0},
        ][:limit]


@pytest.fixture
def mock_repo():
    """Create mock repository with sample processes"""
    repo = MockWorkflowRepository()
    base_time = datetime.now()

    # Add processes with various patterns
    for i in range(15):
        repo.add_process(
            {
                "process_id": f"proc_{i}",
                "kanban_id": "kanban_test",
                "current_state": "aprovado" if i < 10 else "novo",
                "created_at": (base_time - timedelta(days=i + 1)).isoformat(),
                "field_values": {
                    "nome": f"Process {i}",
                    "valor": 1000 + i * 100,
                    "prioridade": i % 5,
                },
                "history": (
                    [
                        {
                            "from_state": "novo",
                            "to_state": "aprovado",
                            "timestamp": (base_time - timedelta(days=i)).isoformat(),
                            "duration_hours": 24.0 + (i % 3) * 10,
                        }
                    ]
                    if i < 10
                    else []
                ),
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
                "aprovado": {"name": "Aprovado", "type": "final"},
            },
        },
    )
    return registry


@pytest.fixture
def mock_pattern_analyzer():
    """Create mock pattern analyzer"""
    return MockPatternAnalyzer()


@pytest.fixture
def ml_model(mock_repo, mock_pattern_analyzer):
    """Create WorkflowMLModel instance"""
    return WorkflowMLModel(mock_repo, mock_pattern_analyzer)


@pytest.fixture
def csv_exporter(mock_repo, mock_registry):
    """Create CSVExporter instance"""
    return CSVExporter(mock_repo, mock_registry)


@pytest.fixture
def excel_exporter(mock_repo, mock_registry):
    """Create ExcelExporter instance"""
    return ExcelExporter(mock_repo, mock_registry)


@pytest.fixture
def pdf_exporter(mock_repo, mock_registry):
    """Create PDFExporter instance"""
    return PDFExporter(mock_repo, mock_registry)


@pytest.fixture
def audit_trail(mock_repo):
    """Create AuditTrail instance"""
    return AuditTrail(mock_repo)


# ========== ML Model Tests ==========


def test_ml_cluster_similar_processes(ml_model):
    """Test clustering of similar processes"""
    result = ml_model.cluster_similar_processes("kanban_test", n_clusters=3)

    assert "clusters" in result
    assert "summary" in result
    assert result["summary"]["total_processes"] == 15
    assert (
        result["summary"]["clusters_count"] <= 3
    )  # May have fewer if not enough processes


def test_ml_cluster_structure(ml_model):
    """Test cluster result structure"""
    result = ml_model.cluster_similar_processes("kanban_test", n_clusters=2)

    if result["clusters"]:
        cluster = result["clusters"][0]
        assert "cluster_id" in cluster
        assert "process_count" in cluster
        assert "characteristics" in cluster
        assert "avg_duration_hours" in cluster["characteristics"]
        assert "avg_transitions" in cluster["characteristics"]
        assert "process_ids" in cluster


def test_ml_predict_duration(ml_model):
    """Test duration prediction"""
    # Use an existing process from mock_repo
    result = ml_model.predict_process_duration("proc_5")

    assert "predicted_total_hours" in result
    assert "confidence" in result
    assert result["predicted_total_hours"] >= 0
    assert 0.0 <= result["confidence"] <= 1.0


def test_ml_identify_risk_factors(ml_model):
    """Test risk factor identification"""
    result = ml_model.identify_risk_factors("kanban_test")

    assert "risk_factors" in result
    assert isinstance(result["risk_factors"], list)


def test_ml_weekly_report(ml_model):
    """Test weekly report generation"""
    result = ml_model.generate_weekly_report("kanban_test")

    assert "report_date" in result
    assert "period" in result
    assert "summary" in result
    assert "clusters" in result
    assert "risk_factors" in result


# ========== CSV Exporter Tests ==========


def test_csv_export_processes(csv_exporter):
    """Test CSV process export"""
    csv_data = csv_exporter.export_processes("kanban_test")

    assert isinstance(csv_data, str)
    assert len(csv_data) > 0
    assert "process_id" in csv_data
    assert "current_state" in csv_data


def test_csv_export_transitions(csv_exporter):
    """Test CSV transition export"""
    csv_data = csv_exporter.export_transitions("kanban_test")

    assert isinstance(csv_data, str)
    assert "process_id" in csv_data
    assert "from_state" in csv_data
    assert "to_state" in csv_data


def test_csv_export_with_custom_fields(csv_exporter):
    """Test CSV export with custom field selection"""
    custom_fields = ["process_id", "current_state", "nome", "valor"]
    csv_data = csv_exporter.export_processes(
        "kanban_test", include_fields=custom_fields
    )

    assert "nome" in csv_data
    assert "valor" in csv_data


# ========== Excel Exporter Tests ==========


def test_excel_export_workbook(excel_exporter):
    """Test Excel workbook export"""
    workbook = excel_exporter.export_workbook("kanban_test")

    assert "workbook_name" in workbook
    assert "sheets" in workbook
    assert "Processes" in workbook["sheets"]
    assert "Transitions" in workbook["sheets"]
    assert "Summary" in workbook["sheets"]


def test_excel_processes_sheet(excel_exporter):
    """Test Excel processes sheet structure"""
    workbook = excel_exporter.export_workbook("kanban_test")
    processes_sheet = workbook["sheets"]["Processes"]

    assert len(processes_sheet) > 0
    # First row should be headers
    headers = processes_sheet[0]
    assert "Process ID" in headers
    assert "Current State" in headers


def test_excel_summary_sheet(excel_exporter):
    """Test Excel summary sheet content"""
    workbook = excel_exporter.export_workbook("kanban_test")
    summary_sheet = workbook["sheets"]["Summary"]

    # Should contain statistics
    summary_text = str(summary_sheet)
    assert "Total Processes" in summary_text or any(
        "Total Processes" in str(row) for row in summary_sheet
    )


# ========== PDF Exporter Tests ==========


def test_pdf_executive_report(pdf_exporter):
    """Test PDF executive report generation"""
    dashboard_data = {
        "health": {
            "health_score": 0.85,
            "status": "healthy",
            "metrics": {"total_processes": 15},
            "issues": [],
            "recommendations": [],
        },
        "statistics": {"period_days": 30, "created": 15, "completed": 10, "active": 5},
        "bottlenecks": {"bottleneck_states": [], "recommendations": []},
    }

    report = pdf_exporter.export_executive_report("kanban_test", dashboard_data)

    assert "report_title" in report
    assert "report_date" in report
    assert "sections" in report
    assert "filename" in report


def test_pdf_process_report(pdf_exporter):
    """Test PDF individual process report"""
    report = pdf_exporter.export_process_report("proc_0")

    assert "report_title" in report
    assert "process" in report
    assert "timeline" in report
    assert report["process"]["process_id"] == "proc_0"


# ========== Audit Trail Tests ==========


def test_audit_log_process_creation(audit_trail):
    """Test logging process creation"""
    audit_id = audit_trail.log_process_creation(
        "proc_new", "kanban_test", user="admin", metadata={"source": "form_submission"}
    )

    assert audit_id is not None
    assert audit_id.startswith("audit_")


def test_audit_log_state_transition(audit_trail):
    """Test logging state transition"""
    audit_id = audit_trail.log_state_transition(
        "proc_123", "novo", "aprovado", user="admin", reason="Approved by manager"
    )

    assert audit_id is not None

    # Verify in audit trail
    trail = audit_trail.get_process_audit_trail("proc_123")
    assert len(trail) == 1
    assert trail[0]["action"] == "state_transition"
    assert trail[0]["before"]["state"] == "novo"
    assert trail[0]["after"]["state"] == "aprovado"


def test_audit_log_forced_transition(audit_trail):
    """Test logging forced transition"""
    audit_id = audit_trail.log_forced_transition(
        "proc_456",
        "novo",
        "aprovado",
        justification="Emergency approval required",
        user="admin",
    )

    assert audit_id is not None

    # Verify forced flag
    trail = audit_trail.get_process_audit_trail("proc_456")
    assert len(trail) == 1
    assert trail[0]["is_forced"] is True
    assert trail[0]["justification"] == "Emergency approval required"


def test_audit_get_user_activity(audit_trail):
    """Test getting user activity"""
    # Log several actions
    audit_trail.log_process_creation("proc_1", "kanban_test", user="user1")
    audit_trail.log_process_creation("proc_2", "kanban_test", user="user1")
    audit_trail.log_process_creation("proc_3", "kanban_test", user="user2")

    # Get user1 activity
    activity = audit_trail.get_user_activity("user1")

    assert len(activity) == 2
    assert all(log["user"] == "user1" for log in activity)


def test_audit_compliance_report(audit_trail):
    """Test compliance report generation"""
    # Log some processes and transitions with kanban_id in metadata
    audit_trail.log_process_creation("proc_1", "kanban_test", user="admin")
    audit_trail.log_process_creation("proc_2", "kanban_test", user="admin")
    audit_trail.log_process_creation("proc_3", "kanban_test", user="admin")

    # Log transitions - note: they need to be linked to kanban via process creation logs
    audit_trail.log_state_transition("proc_1", "novo", "aprovado", user="admin")
    audit_trail.log_state_transition("proc_2", "novo", "aprovado", user="admin")
    audit_trail.log_forced_transition(
        "proc_3", "novo", "aprovado", justification="Emergency", user="admin"
    )

    report = audit_trail.generate_compliance_report("kanban_test", days=30)

    assert "kanban_id" in report
    assert report["kanban_id"] == "kanban_test"
    assert "compliance_score" in report
    assert 0.0 <= report["compliance_score"] <= 1.0
    assert "forced_transitions" in report
    # Compliance report filters by kanban, so forced transitions should be found
    assert "total_processes" in report


def test_audit_activity_statistics(audit_trail):
    """Test activity statistics"""
    # Log various activities
    audit_trail.log_process_creation("proc_1", "kanban_test", user="user1")
    audit_trail.log_state_transition("proc_1", "novo", "aprovado", user="user1")
    audit_trail.log_process_update(
        "proc_1", {"status": "old"}, {"status": "new"}, user="user2"
    )

    stats = audit_trail.get_activity_statistics(days=30)

    assert "total_events" in stats
    assert stats["total_events"] == 3
    assert "events_by_type" in stats
    assert "events_by_user" in stats
    assert "user1" in stats["events_by_user"]
    assert "user2" in stats["events_by_user"]
