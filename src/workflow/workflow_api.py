"""
WorkflowAPI - REST API endpoints for workflow management

Provides Flask routes for:
- Kanban CRUD operations
- Process management
- AI suggestions
- Analytics and dashboards
- Anomaly detection
"""

from flask import Blueprint, request, jsonify
from typing import Callable


class WorkflowAPI:
    """
    Flask Blueprint for workflow REST API

    All endpoints return JSON and follow REST conventions:
    - GET: Retrieve resources
    - POST: Create resources
    - PUT: Update resources
    - DELETE: Remove resources
    """

    def __init__(
        self,
        kanban_registry,
        workflow_repo,
        kanban_editor,
        workflow_dashboard,
        agent_orchestrator,
        anomaly_detector,
        pattern_analyzer,
    ):
        """
        Initialize WorkflowAPI

        Args:
            kanban_registry: KanbanRegistry instance
            workflow_repo: WorkflowRepository instance
            kanban_editor: KanbanEditor instance
            workflow_dashboard: WorkflowDashboard instance
            agent_orchestrator: AgentOrchestrator instance
            anomaly_detector: AnomalyDetector instance
            pattern_analyzer: PatternAnalyzer instance
        """
        self.registry = kanban_registry
        self.repo = workflow_repo
        self.editor = kanban_editor
        self.dashboard = workflow_dashboard
        self.orchestrator = agent_orchestrator
        self.anomaly_detector = anomaly_detector
        self.pattern_analyzer = pattern_analyzer

        # Create Blueprint
        self.bp = Blueprint("workflow_api", __name__, url_prefix="/api/workflow")

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""

        # ========== Kanban Management ==========

        @self.bp.route("/kanbans", methods=["GET"])
        def list_kanbans():
            """List all registered kanbans"""
            kanbans = []
            for kanban_id in self.registry.list_kanbans():
                kanban = self.registry.get_kanban(kanban_id)
                if kanban:
                    kanbans.append(
                        {
                            "id": kanban_id,
                            "name": kanban.get("name", kanban_id),
                            "description": kanban.get("description", ""),
                            "state_count": len(kanban.get("states", {})),
                            "form_mappings": kanban.get("form_mappings", []),
                        }
                    )
            return jsonify(kanbans)

        @self.bp.route("/kanbans/<kanban_id>", methods=["GET"])
        def get_kanban(kanban_id):
            """Get kanban details"""
            kanban = self.registry.get_kanban(kanban_id)
            if not kanban:
                return jsonify({"error": "Kanban not found"}), 404
            return jsonify(kanban)

        @self.bp.route("/kanbans", methods=["POST"])
        def create_kanban():
            """Create or update a kanban"""
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            kanban_id = data.get("id")
            if not kanban_id:
                return jsonify({"error": "Kanban ID is required"}), 400

            try:
                # Use kanban editor to create/update kanban
                self.editor.load_kanban(kanban_id)

                # Update kanban properties
                if "name" in data:
                    self.editor.kanban["name"] = data["name"]
                if "description" in data:
                    self.editor.kanban["description"] = data["description"]
                if "linked_forms" in data:
                    self.editor.kanban["linked_forms"] = data["linked_forms"]

                # Update states
                if "states" in data:
                    self.editor.kanban["states"] = data["states"]

                # Update transitions
                if "transitions" in data:
                    self.editor.kanban["transitions"] = data["transitions"]

                # Save kanban
                success = self.editor.save()

                if success:
                    return jsonify({"success": True, "kanban_id": kanban_id})
                else:
                    return (
                        jsonify({"success": False, "error": "Failed to save kanban"}),
                        500,
                    )

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.bp.route("/kanbans/<kanban_id>/validate", methods=["POST"])
        def validate_kanban(kanban_id):
            """Validate kanban structure"""
            try:
                self.editor.load_kanban(kanban_id)
                is_valid = self.editor.validate()
                errors = self.editor.get_validation_errors()

                return jsonify({"valid": is_valid, "errors": errors})
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # ========== Process Management ==========

        @self.bp.route("/processes", methods=["GET"])
        def list_processes():
            """List processes, optionally filtered by kanban_id"""
            kanban_id = request.args.get("kanban_id")

            if kanban_id:
                processes = self.repo.get_processes_by_kanban(kanban_id)
            else:
                processes = self.repo.get_all_processes()

            return jsonify(processes)

        @self.bp.route("/processes/<process_id>", methods=["GET"])
        def get_process(process_id):
            """Get process details"""
            process = self.repo.get_process_by_id(process_id)
            if not process:
                return jsonify({"error": "Process not found"}), 404
            return jsonify(process)

        @self.bp.route("/process/<process_id>/transition", methods=["POST"])
        def transition_process(process_id):
            """Execute a workflow transition"""
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            to_state = data.get("to_state")
            transition_type = data.get("type", "manual")
            user = data.get("user", "system")
            justification = data.get("justification", "")

            if not to_state:
                return jsonify({"error": "to_state is required"}), 400

            try:
                success = self.repo.update_process_state(
                    process_id,
                    to_state,
                    transition_type=transition_type,
                    user=user,
                    justification=justification,
                )

                if success:
                    # Get updated process
                    process = self.repo.get_process_by_id(process_id)
                    return jsonify({"success": True, "process": process})
                else:
                    return (
                        jsonify(
                            {"success": False, "error": "Failed to update process"}
                        ),
                        500,
                    )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.bp.route("/processes/<process_id>/suggest", methods=["GET"])
        def suggest_transition(process_id):
            """Get AI suggestion for next transition"""
            agent = request.args.get("agent", "auto")

            try:
                result = self.orchestrator.analyze_with_agent(process_id, agent)
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/processes/<process_id>/suggest/all", methods=["GET"])
        def suggest_transition_all_agents(process_id):
            """Get multi-agent consensus suggestion"""
            try:
                result = self.orchestrator.analyze_with_all_agents(process_id)
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route(
            "/processes/<process_id>/validate/<target_state>", methods=["GET"]
        )
        def validate_transition(process_id, target_state):
            """Validate proposed transition"""
            try:
                result = self.orchestrator.validate_transition_with_all_agents(
                    process_id, target_state
                )
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # ========== Dashboard & Analytics ==========

        @self.bp.route("/dashboard/<kanban_id>", methods=["GET"])
        def get_dashboard(kanban_id):
            """Get comprehensive dashboard data"""
            try:
                dashboard = self.dashboard.get_dashboard_summary(kanban_id)
                return jsonify(dashboard)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/health/<kanban_id>", methods=["GET"])
        def get_kanban_health(kanban_id):
            """Get kanban health metrics"""
            try:
                health = self.dashboard.get_kanban_health(kanban_id)
                return jsonify(health)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/stats/<kanban_id>", methods=["GET"])
        def get_process_stats(kanban_id):
            """Get process statistics"""
            days = request.args.get("days", 30, type=int)

            try:
                stats = self.dashboard.get_process_stats(kanban_id, days)
                return jsonify(stats)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/bottlenecks/<kanban_id>", methods=["GET"])
        def get_bottlenecks(kanban_id):
            """Get bottleneck analysis"""
            try:
                bottlenecks = self.dashboard.identify_bottlenecks(kanban_id)
                return jsonify(bottlenecks)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # ========== Anomaly Detection ==========

        @self.bp.route("/anomalies/<kanban_id>", methods=["GET"])
        def get_anomalies(kanban_id):
            """Get anomaly report"""
            try:
                report = self.anomaly_detector.generate_anomaly_report(kanban_id)
                return jsonify(report)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/anomalies/<kanban_id>/stuck", methods=["GET"])
        def get_stuck_processes(kanban_id):
            """Get stuck processes"""
            threshold = request.args.get("threshold", 48, type=int)

            try:
                stuck = self.anomaly_detector.detect_stuck_processes(
                    kanban_id, threshold_hours=threshold
                )
                return jsonify(stuck)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/anomalies/<kanban_id>/loops", methods=["GET"])
        def get_loops(kanban_id):
            """Get processes with loops"""
            try:
                loops = self.anomaly_detector.detect_loops(kanban_id)
                return jsonify(loops)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        # ========== Pattern Analysis ==========

        @self.bp.route("/patterns/<kanban_id>", methods=["GET"])
        def get_patterns(kanban_id):
            """Get transition patterns"""
            min_support = request.args.get("min_support", 0.3, type=float)

            try:
                patterns = self.pattern_analyzer.analyze_transition_patterns(
                    kanban_id, min_support=min_support
                )
                return jsonify(patterns)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/patterns/<kanban_id>/classified", methods=["GET"])
        def get_classified_patterns(kanban_id):
            """Get classified patterns"""
            min_support = request.args.get("min_support", 0.3, type=float)

            try:
                patterns = self.pattern_analyzer.analyze_transition_patterns(
                    kanban_id, min_support=min_support
                )
                classified = self.pattern_analyzer.classify_patterns(patterns)
                return jsonify(classified)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/patterns/<kanban_id>/matrix", methods=["GET"])
        def get_transition_matrix(kanban_id):
            """Get transition probability matrix"""
            try:
                matrix = self.pattern_analyzer.build_transition_matrix(kanban_id)
                return jsonify(matrix)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/patterns/<kanban_id>/durations", methods=["GET"])
        def get_state_durations(kanban_id):
            """Get state duration statistics"""
            try:
                durations = self.pattern_analyzer.analyze_state_durations(kanban_id)
                return jsonify(durations)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.bp.route("/patterns/<kanban_id>/similar/<process_id>", methods=["GET"])
        def get_similar_processes(kanban_id, process_id):
            """Find similar processes"""
            limit = request.args.get("limit", 5, type=int)

            try:
                similar = self.pattern_analyzer.find_similar_processes(
                    process_id, kanban_id, limit=limit
                )
                return jsonify(similar)
            except Exception as e:
                return jsonify({"error": str(e)}), 400

    def get_blueprint(self):
        """Get Flask Blueprint for registration"""
        return self.bp


def register_workflow_api(
    app,
    kanban_registry,
    workflow_repo,
    kanban_editor,
    workflow_dashboard,
    agent_orchestrator,
    anomaly_detector,
    pattern_analyzer,
    csv_exporter=None,
    excel_exporter=None,
    pdf_exporter=None,
    audit_trail=None,
):
    """
    Convenience function to register workflow API with Flask app

    Args:
        app: Flask application instance
        kanban_registry: KanbanRegistry instance
        workflow_repo: WorkflowRepository instance
        kanban_editor: KanbanEditor instance
        workflow_dashboard: WorkflowDashboard instance
        agent_orchestrator: AgentOrchestrator instance
        anomaly_detector: AnomalyDetector instance
        pattern_analyzer: PatternAnalyzer instance
        csv_exporter: (Optional) CSVExporter instance for Phase 5
        excel_exporter: (Optional) ExcelExporter instance for Phase 5
        pdf_exporter: (Optional) PDFExporter instance for Phase 5
        audit_trail: (Optional) AuditTrail instance for Phase 5

    Example:
        from workflow.workflow_api import register_workflow_api

        register_workflow_api(
            app,
            kanban_registry,
            workflow_repo,
            kanban_editor,
            workflow_dashboard,
            agent_orchestrator,
            anomaly_detector,
            pattern_analyzer,
            csv_exporter=csv_exporter,
            excel_exporter=excel_exporter,
            pdf_exporter=pdf_exporter,
            audit_trail=audit_trail
        )
    """
    api = WorkflowAPI(
        kanban_registry,
        workflow_repo,
        kanban_editor,
        workflow_dashboard,
        agent_orchestrator,
        anomaly_detector,
        pattern_analyzer,
    )

    # Get the blueprint before registration
    blueprint = api.get_blueprint()

    # Register Phase 5 routes if components are provided
    if csv_exporter and excel_exporter and pdf_exporter:
        from workflow.exporters import register_export_routes

        register_export_routes(blueprint, csv_exporter, excel_exporter, pdf_exporter)

    if audit_trail:
        from workflow.audit_trail import register_audit_routes

        register_audit_routes(blueprint, audit_trail)

    # Now register the blueprint with all routes
    app.register_blueprint(blueprint)
