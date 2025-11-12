"""
Workflow Module - Kanban-based workflow management for VibeCForms

This module provides complete workflow management capabilities including:
- Kanban registry and form-kanban mappings
- Automatic process creation from form submissions
- Process factory for creating and managing workflow processes
- Form trigger hooks for automatic workflow integration
- Automatic state transitions with prerequisite checking
- Timeout-based transitions and cascade progression
- Forced transitions with business justification

Main Components (Phase 1):
- KanbanRegistry: Singleton managing kanban definitions and form mappings
- ProcessFactory: Factory for creating workflow processes from form data
- FormTriggerManager: Hook system for form save events
- WorkflowRepository: Repository for workflow process persistence

Main Components (Phase 2):
- PrerequisiteChecker: Validates prerequisites (field_check, external_api, time_elapsed, custom_script)
- AutoTransitionEngine: Automatic transitions, timeouts, cascade progression, forced transitions

Main Components (Phase 3):
- PatternAnalyzer: Analyzes historical transition patterns and identifies common paths
- AnomalyDetector: Detects stuck processes, duration anomalies, loops, unusual transitions
- BaseAgent: Abstract base class for AI agents
- GenericAgent: Heuristics-based agent for general-purpose suggestions
- PatternAgent: Pattern-based agent using historical analysis
- RuleAgent: Rule-based agent using prerequisite evaluation
- AgentOrchestrator: Coordinates multiple AI agents for consensus-based suggestions

Main Components (Phase 4):
- KanbanEditor: Visual editor for creating and managing kanban definitions
- WorkflowDashboard: Analytics and monitoring dashboard for workflow health and performance
- WorkflowAPI: REST API endpoints for workflow management and analytics

Main Components (Phase 5):
- WorkflowMLModel: Machine learning model for process clustering and duration prediction
- CSVExporter: Export workflow data to CSV format
- ExcelExporter: Export workflow data to Excel workbooks
- PDFExporter: Generate PDF reports from workflow data
- AuditTrail: Complete audit logging system for compliance and tracking

Usage:
    from workflow import (
        get_registry, ProcessFactory, FormTriggerManager,
        PrerequisiteChecker, AutoTransitionEngine,
        PatternAnalyzer, AnomalyDetector, AgentOrchestrator,
        BaseAgent, GenericAgent, PatternAgent, RuleAgent,
        KanbanEditor, WorkflowDashboard, register_workflow_api,
        WorkflowMLModel, CSVExporter, ExcelExporter, PDFExporter, AuditTrail
    )
    from persistence.repository_factory import RepositoryFactory
    from persistence.workflow_repository import WorkflowRepository

    # Initialize Phase 1 components
    registry = get_registry()
    factory = ProcessFactory(registry)

    # Setup repository
    repo_factory = RepositoryFactory()
    base_repo = repo_factory.create_repository('txt')
    workflow_repo = WorkflowRepository(base_repo)

    # Create trigger manager
    trigger_manager = FormTriggerManager(registry, factory, workflow_repo)

    # Initialize Phase 2 components
    checker = PrerequisiteChecker()
    engine = AutoTransitionEngine(registry, checker)

    # Initialize Phase 3 components
    pattern_analyzer = PatternAnalyzer(workflow_repo)
    anomaly_detector = AnomalyDetector(workflow_repo)
    orchestrator = AgentOrchestrator(workflow_repo, registry, pattern_analyzer, checker)

    # Initialize Phase 4 components
    editor = KanbanEditor(registry)
    dashboard = WorkflowDashboard(workflow_repo, registry, pattern_analyzer, anomaly_detector, orchestrator)
    register_workflow_api(app, registry, workflow_repo, editor, dashboard, orchestrator, anomaly_detector, pattern_analyzer)

    # Hook into form saves
    process_id = trigger_manager.on_form_created('pedidos', form_data, record_idx)

    # Check for auto-transitions
    if engine.should_auto_transition(process):
        transitions = engine.execute_cascade_progression(process, workflow_repo)

    # AI-powered analysis
    analysis = orchestrator.analyze_with_all_agents(process_id)
    suggestion = analysis['best_suggestion']

    # Detect anomalies
    stuck = anomaly_detector.detect_stuck_processes('kanban_pedidos', threshold_hours=48)

    # Visual editor
    editor.create_kanban('kanban_vendas', 'Vendas')\
          .add_state('novo', 'Novo', type='initial')\
          .add_state('em_negociacao', 'Em Negociação')\
          .add_state('fechado', 'Fechado', type='final')\
          .add_transition('novo', 'em_negociacao')\
          .add_transition('em_negociacao', 'fechado')\
          .save()

    # Dashboard analytics
    health = dashboard.get_kanban_health('kanban_pedidos')
    bottlenecks = dashboard.identify_bottlenecks('kanban_pedidos')

    # Initialize Phase 5 components
    ml_model = WorkflowMLModel(workflow_repo, pattern_analyzer)
    csv_exporter = CSVExporter(workflow_repo, registry)
    excel_exporter = ExcelExporter(workflow_repo, registry)
    pdf_exporter = PDFExporter(workflow_repo, registry)
    audit_trail = AuditTrail(workflow_repo)

    # ML-based analysis
    clusters = ml_model.cluster_similar_processes('kanban_pedidos', n_clusters=3)
    prediction = ml_model.predict_process_duration('kanban_pedidos', process_data)
    report = ml_model.generate_weekly_report('kanban_pedidos')

    # Export data
    csv_data = csv_exporter.export_processes('kanban_pedidos')
    excel_workbook = excel_exporter.export_workbook('kanban_pedidos')
    pdf_report = pdf_exporter.export_executive_report('kanban_pedidos', dashboard_data)

    # Audit logging
    audit_trail.log_state_transition(process_id, 'novo', 'aprovado', user='admin')
    process_history = audit_trail.get_process_audit_trail(process_id)
    compliance = audit_trail.generate_compliance_report('kanban_pedidos', days=30)
"""

from .kanban_registry import KanbanRegistry, get_registry
from .process_factory import ProcessFactory
from .form_trigger_manager import FormTriggerManager
from .prerequisite_checker import PrerequisiteChecker
from .auto_transition_engine import AutoTransitionEngine
from .pattern_analyzer import PatternAnalyzer
from .anomaly_detector import AnomalyDetector
from .agent_orchestrator import AgentOrchestrator
from .agents import BaseAgent, GenericAgent, PatternAgent, RuleAgent
from .kanban_editor import KanbanEditor
from .workflow_dashboard import WorkflowDashboard
from .workflow_api import WorkflowAPI, register_workflow_api
from .workflow_ml_model import WorkflowMLModel
from .exporters import CSVExporter, ExcelExporter, PDFExporter
from .audit_trail import AuditTrail
from .notification_manager import NotificationManager
from .webhook_manager import WebhookManager
from .agent_feedback_loop import AgentFeedbackLoop
from .ml_feature_engineering import MLFeatureEngineering

__all__ = [
    "KanbanRegistry",
    "get_registry",
    "ProcessFactory",
    "FormTriggerManager",
    "PrerequisiteChecker",
    "AutoTransitionEngine",
    "PatternAnalyzer",
    "AnomalyDetector",
    "AgentOrchestrator",
    "BaseAgent",
    "GenericAgent",
    "PatternAgent",
    "RuleAgent",
    "KanbanEditor",
    "WorkflowDashboard",
    "WorkflowAPI",
    "register_workflow_api",
    "WorkflowMLModel",
    "CSVExporter",
    "ExcelExporter",
    "PDFExporter",
    "AuditTrail",
    "NotificationManager",
    "WebhookManager",
    "AgentFeedbackLoop",
    "MLFeatureEngineering",
]

__version__ = "5.0.0"  # Phase 5 complete
