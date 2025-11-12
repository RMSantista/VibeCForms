"""
Workflow Exporters - Export workflow data to various formats

Supports:
- CSV export for data analysis
- Excel export with multiple sheets
- PDF export for reports and presentations
"""

from typing import Dict, List, Optional
from datetime import datetime
import csv
import io
import json


class BaseExporter:
    """Base class for all exporters"""

    def __init__(self, workflow_repo, kanban_registry):
        """
        Initialize exporter

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
        """
        self.repo = workflow_repo
        self.registry = kanban_registry


class CSVExporter(BaseExporter):
    """
    Export workflow data to CSV format

    Provides flexible CSV export with customizable fields
    and filtering options.
    """

    def export_processes(
        self, kanban_id: str, include_fields: Optional[List[str]] = None
    ) -> str:
        """
        Export processes to CSV string

        Args:
            kanban_id: Kanban ID
            include_fields: Optional list of fields to include

        Returns:
            CSV string
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if not processes:
            return ""

        # Default fields
        default_fields = [
            "process_id",
            "current_state",
            "created_at",
            "updated_at",
            "transition_count",
        ]

        fields = include_fields if include_fields else default_fields

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")

        writer.writeheader()

        for proc in processes:
            row = {
                "process_id": proc.get("process_id", ""),
                "current_state": proc.get("current_state", ""),
                "created_at": proc.get("created_at", ""),
                "updated_at": proc.get("updated_at", ""),
                "transition_count": len(proc.get("history", [])),
            }

            # Add field values if requested
            field_values = proc.get("field_values", {})
            for field in fields:
                if field not in row and field in field_values:
                    row[field] = (
                        str(field_values[field])
                        if field_values[field] is not None
                        else ""
                    )

            writer.writerow(row)

        return output.getvalue()

    def export_transitions(self, kanban_id: str) -> str:
        """
        Export transition history to CSV

        Args:
            kanban_id: Kanban ID

        Returns:
            CSV string with transition data
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        output = io.StringIO()
        fields = ["process_id", "from_state", "to_state", "timestamp", "duration_hours"]
        writer = csv.DictWriter(output, fieldnames=fields)

        writer.writeheader()

        for proc in processes:
            process_id = proc.get("process_id", "")
            for transition in proc.get("history", []):
                writer.writerow(
                    {
                        "process_id": process_id,
                        "from_state": transition.get("from_state", ""),
                        "to_state": transition.get("to_state", ""),
                        "timestamp": transition.get("timestamp", ""),
                        "duration_hours": transition.get("duration_hours", 0),
                    }
                )

        return output.getvalue()


class ExcelExporter(BaseExporter):
    """
    Export workflow data to Excel format

    Creates multi-sheet Excel workbooks with:
    - Processes sheet
    - Transitions sheet
    - Summary sheet
    """

    def export_workbook(self, kanban_id: str) -> Dict:
        """
        Export complete workbook data

        Returns dict that can be used with openpyxl or similar libraries

        Args:
            kanban_id: Kanban ID

        Returns:
            {
                'workbook_name': 'kanban_pedidos_2025-11-03.xlsx',
                'sheets': {
                    'Processes': [...rows...],
                    'Transitions': [...rows...],
                    'Summary': [...rows...]
                }
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)
        kanban = self.registry.get_kanban(kanban_id)

        # Processes sheet
        processes_rows = [
            [
                "Process ID",
                "Current State",
                "Created At",
                "Updated At",
                "Transitions",
                "Duration (hours)",
            ]
        ]

        for proc in processes:
            duration = self._calculate_duration(proc)
            processes_rows.append(
                [
                    proc.get("process_id", ""),
                    proc.get("current_state", ""),
                    proc.get("created_at", ""),
                    proc.get("updated_at", ""),
                    len(proc.get("history", [])),
                    round(duration, 2),
                ]
            )

        # Transitions sheet
        transitions_rows = [
            ["Process ID", "From State", "To State", "Timestamp", "Duration (hours)"]
        ]

        for proc in processes:
            for trans in proc.get("history", []):
                transitions_rows.append(
                    [
                        proc.get("process_id", ""),
                        trans.get("from_state", ""),
                        trans.get("to_state", ""),
                        trans.get("timestamp", ""),
                        trans.get("duration_hours", 0),
                    ]
                )

        # Summary sheet
        completed = sum(1 for p in processes if self._is_completed(p))
        active = len(processes) - completed
        avg_duration = (
            sum(self._calculate_duration(p) for p in processes) / len(processes)
            if processes
            else 0
        )

        summary_rows = [
            ["Kanban Summary", ""],
            ["Kanban ID", kanban_id],
            ["Kanban Name", kanban.get("name", "") if kanban else ""],
            ["Export Date", datetime.now().isoformat()],
            ["", ""],
            ["Statistics", ""],
            ["Total Processes", len(processes)],
            ["Completed", completed],
            ["Active", active],
            [
                "Completion Rate",
                f"{completed/len(processes)*100:.1f}%" if processes else "0%",
            ],
            ["Avg Duration (hours)", round(avg_duration, 2)],
        ]

        # Add state distribution
        state_counts = {}
        for proc in processes:
            state = proc.get("current_state", "unknown")
            state_counts[state] = state_counts.get(state, 0) + 1

        summary_rows.append(["", ""])
        summary_rows.append(["State Distribution", ""])
        for state, count in sorted(
            state_counts.items(), key=lambda x: x[1], reverse=True
        ):
            summary_rows.append([state, count])

        return {
            "workbook_name": f"{kanban_id}_{datetime.now().date().isoformat()}.xlsx",
            "sheets": {
                "Processes": processes_rows,
                "Transitions": transitions_rows,
                "Summary": summary_rows,
            },
        }

    def _calculate_duration(self, process: Dict) -> float:
        """Calculate process duration in hours"""
        created_at = process.get("created_at")
        if not created_at:
            return 0.0

        history = process.get("history", [])
        if history:
            last_timestamp = history[-1].get("timestamp")
            if last_timestamp:
                try:
                    start = datetime.fromisoformat(created_at)
                    end = datetime.fromisoformat(last_timestamp)
                    return (end - start).total_seconds() / 3600
                except:
                    pass

        try:
            start = datetime.fromisoformat(created_at)
            now = datetime.now()
            return (now - start).total_seconds() / 3600
        except:
            return 0.0

    def _is_completed(self, process: Dict) -> bool:
        """Check if process is completed"""
        return len(process.get("history", [])) > 0


class PDFExporter(BaseExporter):
    """
    Export workflow reports to PDF format

    Generates formatted PDF reports with:
    - Executive summary
    - Statistics
    - Charts and visualizations
    """

    def export_executive_report(self, kanban_id: str, dashboard_data: Dict) -> Dict:
        """
        Generate executive report data for PDF rendering

        This returns structured data that can be rendered to PDF
        using templates and PDF generation libraries like WeasyPrint

        Args:
            kanban_id: Kanban ID
            dashboard_data: Dashboard summary data

        Returns:
            {
                'report_title': 'Executive Report - Kanban Pedidos',
                'report_date': '2025-11-03',
                'sections': [
                    {
                        'title': 'Health Summary',
                        'type': 'health',
                        'content': {...}
                    },
                    {
                        'title': 'Statistics',
                        'type': 'statistics',
                        'content': {...}
                    },
                    {
                        'title': 'Bottlenecks',
                        'type': 'bottlenecks',
                        'content': {...}
                    }
                ],
                'template': 'executive_report',
                'filename': 'kanban_pedidos_report_2025-11-03.pdf'
            }
        """
        kanban = self.registry.get_kanban(kanban_id)
        kanban_name = kanban.get("name", kanban_id) if kanban else kanban_id

        sections = []

        # Health Summary Section
        if "health" in dashboard_data:
            health = dashboard_data["health"]
            sections.append(
                {
                    "title": "Health Summary",
                    "type": "health",
                    "content": {
                        "score": health.get("health_score", 0),
                        "status": health.get("status", "unknown"),
                        "metrics": health.get("metrics", {}),
                        "issues": health.get("issues", []),
                        "recommendations": health.get("recommendations", []),
                    },
                }
            )

        # Statistics Section
        if "statistics" in dashboard_data:
            stats = dashboard_data["statistics"]
            sections.append(
                {
                    "title": "Process Statistics",
                    "type": "statistics",
                    "content": {
                        "period_days": stats.get("period_days", 30),
                        "created": stats.get("created", 0),
                        "completed": stats.get("completed", 0),
                        "active": stats.get("active", 0),
                        "completion_rate": stats.get("completion_rate", 0),
                        "avg_cycle_time_hours": stats.get("avg_cycle_time_hours", 0),
                        "states_distribution": stats.get("states_distribution", {}),
                    },
                }
            )

        # Bottlenecks Section
        if "bottlenecks" in dashboard_data:
            bottlenecks = dashboard_data["bottlenecks"]
            sections.append(
                {
                    "title": "Bottleneck Analysis",
                    "type": "bottlenecks",
                    "content": {
                        "bottleneck_states": bottlenecks.get("bottleneck_states", []),
                        "recommendations": bottlenecks.get("recommendations", []),
                    },
                }
            )

        return {
            "report_title": f"Executive Report - {kanban_name}",
            "report_date": datetime.now().date().isoformat(),
            "kanban_id": kanban_id,
            "kanban_name": kanban_name,
            "sections": sections,
            "template": "executive_report",
            "filename": f"{kanban_id}_report_{datetime.now().date().isoformat()}.pdf",
        }

    def export_process_report(self, process_id: str) -> Dict:
        """
        Generate individual process report data

        Args:
            process_id: Process ID

        Returns:
            Process report data structure for PDF rendering
        """
        process = self.repo.get_process_by_id(process_id)
        if not process:
            return {"error": "Process not found"}

        kanban_id = process.get("kanban_id", "")
        kanban = self.registry.get_kanban(kanban_id)

        # Calculate metrics
        created_at = process.get("created_at", "")
        history = process.get("history", [])
        duration = self._calculate_duration(process)

        # Build timeline
        timeline = []
        if created_at:
            timeline.append(
                {
                    "event": "Process Created",
                    "timestamp": created_at,
                    "state": process.get("current_state", ""),
                }
            )

        for trans in history:
            timeline.append(
                {
                    "event": f"Transition: {trans.get('from_state', '')} → {trans.get('to_state', '')}",
                    "timestamp": trans.get("timestamp", ""),
                    "duration_hours": trans.get("duration_hours", 0),
                }
            )

        return {
            "report_title": f"Process Report - {process_id}",
            "report_date": datetime.now().date().isoformat(),
            "process": {
                "process_id": process_id,
                "kanban_id": kanban_id,
                "kanban_name": kanban.get("name", "") if kanban else "",
                "current_state": process.get("current_state", ""),
                "created_at": created_at,
                "total_duration_hours": round(duration, 2),
                "transition_count": len(history),
                "field_values": process.get("field_values", {}),
            },
            "timeline": timeline,
            "template": "process_report",
            "filename": f"process_{process_id}_report_{datetime.now().date().isoformat()}.pdf",
        }

    def _calculate_duration(self, process: Dict) -> float:
        """Calculate process duration in hours"""
        created_at = process.get("created_at")
        if not created_at:
            return 0.0

        history = process.get("history", [])
        if history:
            last_timestamp = history[-1].get("timestamp")
            if last_timestamp:
                try:
                    start = datetime.fromisoformat(created_at)
                    end = datetime.fromisoformat(last_timestamp)
                    return (end - start).total_seconds() / 3600
                except:
                    pass

        try:
            start = datetime.fromisoformat(created_at)
            now = datetime.now()
            return (now - start).total_seconds() / 3600
        except:
            return 0.0


def register_export_routes(workflow_api_bp, csv_exporter, excel_exporter, pdf_exporter):
    """
    Register export routes with WorkflowAPI blueprint

    Args:
        workflow_api_bp: Flask Blueprint instance
        csv_exporter: CSVExporter instance
        excel_exporter: ExcelExporter instance
        pdf_exporter: PDFExporter instance
    """
    from flask import request, Response, jsonify

    @workflow_api_bp.route("/export/<kanban_id>/csv", methods=["GET"])
    def export_csv(kanban_id):
        """Export processes to CSV"""
        export_type = request.args.get("type", "processes")  # processes or transitions

        if export_type == "transitions":
            csv_data = csv_exporter.export_transitions(kanban_id)
            filename = f"{kanban_id}_transitions.csv"
        else:
            csv_data = csv_exporter.export_processes(kanban_id)
            filename = f"{kanban_id}_processes.csv"

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @workflow_api_bp.route("/export/<kanban_id>/excel", methods=["GET"])
    def export_excel(kanban_id):
        """Export processes to Excel format (returns data structure)"""
        workbook_data = excel_exporter.export_workbook(kanban_id)
        return jsonify(workbook_data)

    @workflow_api_bp.route("/export/<kanban_id>/pdf", methods=["GET"])
    def export_pdf(kanban_id):
        """Export executive report (returns data structure for PDF rendering)"""
        # This would need dashboard data - simplified for now
        report_data = pdf_exporter.export_executive_report(kanban_id, {})
        return jsonify(report_data)

    @workflow_api_bp.route("/export/process/<process_id>/pdf", methods=["GET"])
    def export_process_pdf(process_id):
        """Export individual process report"""
        report_data = pdf_exporter.export_process_report(process_id)
        return jsonify(report_data)
