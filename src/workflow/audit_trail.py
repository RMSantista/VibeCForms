"""
AuditTrail - Complete audit logging for workflow operations

Tracks all workflow changes including:
- Process creations and updates
- State transitions
- Kanban modifications
- User actions
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class AuditTrail:
    """
    Comprehensive audit trail system

    Logs all workflow operations with:
    - User attribution
    - Timestamps
    - Before/after states
    - Change reasons
    """

    def __init__(self, workflow_repo):
        """
        Initialize AuditTrail

        Args:
            workflow_repo: WorkflowRepository instance
        """
        self.repo = workflow_repo
        self.audit_logs = []  # In-memory storage (would be persisted in production)

    # ========== Audit Logging ==========

    def log_process_creation(
        self,
        process_id: str,
        kanban_id: str,
        user: str = "system",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Log process creation event

        Args:
            process_id: Process ID
            kanban_id: Kanban ID
            user: User who created the process
            metadata: Additional metadata

        Returns:
            Audit log ID
        """
        return self._create_audit_log(
            {
                "action": "process_created",
                "entity_type": "process",
                "entity_id": process_id,
                "kanban_id": kanban_id,
                "user": user,
                "metadata": metadata or {},
            }
        )

    def log_state_transition(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        user: str = "system",
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Log state transition event

        Args:
            process_id: Process ID
            from_state: Source state
            to_state: Target state
            user: User who performed transition
            reason: Reason for transition
            metadata: Additional metadata

        Returns:
            Audit log ID
        """
        return self._create_audit_log(
            {
                "action": "state_transition",
                "entity_type": "process",
                "entity_id": process_id,
                "user": user,
                "before": {"state": from_state},
                "after": {"state": to_state},
                "reason": reason,
                "metadata": metadata or {},
            }
        )

    def log_process_update(
        self,
        process_id: str,
        before_values: Dict,
        after_values: Dict,
        user: str = "system",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Log process field update

        Args:
            process_id: Process ID
            before_values: Field values before update
            after_values: Field values after update
            user: User who updated the process
            metadata: Additional metadata

        Returns:
            Audit log ID
        """
        # Identify changed fields
        changed_fields = {}
        for field, new_value in after_values.items():
            old_value = before_values.get(field)
            if old_value != new_value:
                changed_fields[field] = {"old": old_value, "new": new_value}

        return self._create_audit_log(
            {
                "action": "process_updated",
                "entity_type": "process",
                "entity_id": process_id,
                "user": user,
                "before": before_values,
                "after": after_values,
                "changed_fields": changed_fields,
                "metadata": metadata or {},
            }
        )

    def log_kanban_modification(
        self,
        kanban_id: str,
        modification_type: str,
        details: Dict,
        user: str = "system",
    ) -> str:
        """
        Log kanban modification

        Args:
            kanban_id: Kanban ID
            modification_type: Type of modification (state_added, transition_added, etc.)
            details: Modification details
            user: User who made the modification

        Returns:
            Audit log ID
        """
        return self._create_audit_log(
            {
                "action": "kanban_modified",
                "entity_type": "kanban",
                "entity_id": kanban_id,
                "modification_type": modification_type,
                "user": user,
                "details": details,
            }
        )

    def log_forced_transition(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        justification: str,
        user: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Log forced transition (bypass rules)

        Args:
            process_id: Process ID
            from_state: Source state
            to_state: Target state
            justification: Business justification
            user: User who forced the transition
            metadata: Additional metadata

        Returns:
            Audit log ID
        """
        return self._create_audit_log(
            {
                "action": "forced_transition",
                "entity_type": "process",
                "entity_id": process_id,
                "user": user,
                "before": {"state": from_state},
                "after": {"state": to_state},
                "justification": justification,
                "is_forced": True,
                "metadata": metadata or {},
            }
        )

    def _create_audit_log(self, log_data: Dict) -> str:
        """
        Create audit log entry

        Args:
            log_data: Log data

        Returns:
            Audit log ID
        """
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        log_entry = {
            "audit_id": audit_id,
            "timestamp": datetime.now().isoformat(),
            **log_data,
        }

        self.audit_logs.append(log_entry)

        return audit_id

    # ========== Audit Queries ==========

    def get_process_audit_trail(self, process_id: str) -> List[Dict]:
        """
        Get complete audit trail for a process

        Args:
            process_id: Process ID

        Returns:
            List of audit log entries sorted by timestamp
        """
        logs = [
            log
            for log in self.audit_logs
            if log.get("entity_type") == "process"
            and log.get("entity_id") == process_id
        ]

        return sorted(logs, key=lambda x: x["timestamp"])

    def get_kanban_audit_trail(self, kanban_id: str) -> List[Dict]:
        """
        Get audit trail for a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            List of audit log entries
        """
        logs = [
            log
            for log in self.audit_logs
            if (
                log.get("entity_type") == "kanban" and log.get("entity_id") == kanban_id
            )
            or (log.get("kanban_id") == kanban_id)
        ]

        return sorted(logs, key=lambda x: x["timestamp"])

    def get_user_activity(
        self,
        user: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Get all activity by a specific user

        Args:
            user: User identifier
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of audit log entries
        """
        logs = [log for log in self.audit_logs if log.get("user") == user]

        # Apply date filters
        if start_date:
            logs = [
                log
                for log in logs
                if datetime.fromisoformat(log["timestamp"]) >= start_date
            ]

        if end_date:
            logs = [
                log
                for log in logs
                if datetime.fromisoformat(log["timestamp"]) <= end_date
            ]

        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)

    def get_recent_activity(self, limit: int = 100) -> List[Dict]:
        """
        Get recent activity across all entities

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent audit log entries
        """
        sorted_logs = sorted(
            self.audit_logs, key=lambda x: x["timestamp"], reverse=True
        )
        return sorted_logs[:limit]

    def get_forced_transitions(self, days: int = 30) -> List[Dict]:
        """
        Get all forced transitions in the specified period

        Args:
            days: Number of days to look back

        Returns:
            List of forced transition audit entries
        """
        cutoff = datetime.now() - timedelta(days=days)

        forced = [
            log
            for log in self.audit_logs
            if log.get("action") == "forced_transition"
            and datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]

        return sorted(forced, key=lambda x: x["timestamp"], reverse=True)

    # ========== Analytics ==========

    def get_activity_statistics(self, days: int = 30) -> Dict:
        """
        Get activity statistics for the specified period

        Args:
            days: Number of days to analyze

        Returns:
            {
                'period_days': 30,
                'total_events': 150,
                'events_by_type': {
                    'process_created': 45,
                    'state_transition': 89,
                    'process_updated': 12,
                    'forced_transition': 4
                },
                'events_by_user': {
                    'system': 120,
                    'user1': 20,
                    'user2': 10
                },
                'forced_transitions_count': 4
            }
        """
        cutoff = datetime.now() - timedelta(days=days)

        period_logs = [
            log
            for log in self.audit_logs
            if datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]

        # Count by event type
        events_by_type = {}
        for log in period_logs:
            action = log.get("action", "unknown")
            events_by_type[action] = events_by_type.get(action, 0) + 1

        # Count by user
        events_by_user = {}
        for log in period_logs:
            user = log.get("user", "unknown")
            events_by_user[user] = events_by_user.get(user, 0) + 1

        # Count forced transitions
        forced_count = sum(1 for log in period_logs if log.get("is_forced"))

        return {
            "period_days": days,
            "total_events": len(period_logs),
            "events_by_type": events_by_type,
            "events_by_user": events_by_user,
            "forced_transitions_count": forced_count,
        }

    def generate_compliance_report(self, kanban_id: str, days: int = 30) -> Dict:
        """
        Generate compliance report for audit purposes

        Args:
            kanban_id: Kanban ID
            days: Number of days to analyze

        Returns:
            {
                'kanban_id': 'kanban_pedidos',
                'report_date': '2025-11-03',
                'period_days': 30,
                'total_processes': 45,
                'total_transitions': 156,
                'forced_transitions': [
                    {
                        'process_id': 'proc_123',
                        'from_state': 'novo',
                        'to_state': 'aprovado',
                        'user': 'admin',
                        'justification': 'Emergency approval',
                        'timestamp': '2025-10-15T10:30:00'
                    }
                ],
                'unusual_activity': [...],
                'compliance_score': 0.95  # 0.0-1.0
            }
        """
        cutoff = datetime.now() - timedelta(days=days)

        kanban_logs = [
            log
            for log in self.get_kanban_audit_trail(kanban_id)
            if datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]

        # Count process creations and transitions
        process_creations = [
            log for log in kanban_logs if log.get("action") == "process_created"
        ]

        state_transitions = [
            log
            for log in kanban_logs
            if log.get("action") in ["state_transition", "forced_transition"]
        ]

        forced_transitions = [log for log in kanban_logs if log.get("is_forced")]

        # Calculate compliance score
        # Penalize for high ratio of forced transitions
        forced_ratio = (
            len(forced_transitions) / len(state_transitions) if state_transitions else 0
        )
        compliance_score = max(0.0, 1.0 - (forced_ratio * 2))  # Cap at 0.0

        # Identify unusual activity (multiple forced transitions by same user)
        forced_by_user = {}
        for forced in forced_transitions:
            user = forced.get("user", "unknown")
            forced_by_user[user] = forced_by_user.get(user, 0) + 1

        unusual_activity = [
            {
                "type": "high_forced_transition_count",
                "user": user,
                "count": count,
                "severity": "high" if count > 5 else "medium",
            }
            for user, count in forced_by_user.items()
            if count > 2
        ]

        return {
            "kanban_id": kanban_id,
            "report_date": datetime.now().date().isoformat(),
            "period_days": days,
            "total_processes": len(process_creations),
            "total_transitions": len(state_transitions),
            "forced_transitions": [
                {
                    "process_id": log.get("entity_id"),
                    "from_state": log.get("before", {}).get("state"),
                    "to_state": log.get("after", {}).get("state"),
                    "user": log.get("user"),
                    "justification": log.get("justification"),
                    "timestamp": log.get("timestamp"),
                }
                for log in forced_transitions
            ],
            "unusual_activity": unusual_activity,
            "compliance_score": round(compliance_score, 2),
        }


def register_audit_routes(workflow_api_bp, audit_trail):
    """
    Register audit trail routes with WorkflowAPI blueprint

    Args:
        workflow_api_bp: Flask Blueprint instance
        audit_trail: AuditTrail instance
    """
    from flask import request, jsonify

    @workflow_api_bp.route("/audit/process/<process_id>", methods=["GET"])
    def get_process_audit(process_id):
        """Get complete audit trail for a process"""
        trail = audit_trail.get_process_audit_trail(process_id)
        return jsonify({"process_id": process_id, "audit_trail": trail})

    @workflow_api_bp.route("/audit/kanban/<kanban_id>", methods=["GET"])
    def get_kanban_audit(kanban_id):
        """Get audit trail for a kanban"""
        trail = audit_trail.get_kanban_audit_trail(kanban_id)
        return jsonify({"kanban_id": kanban_id, "audit_trail": trail})

    @workflow_api_bp.route("/audit/user/<user>", methods=["GET"])
    def get_user_audit(user):
        """Get activity for a specific user"""
        days = request.args.get("days", 30, type=int)
        start_date = datetime.now() - timedelta(days=days)

        activity = audit_trail.get_user_activity(user, start_date=start_date)
        return jsonify({"user": user, "activity": activity})

    @workflow_api_bp.route("/audit/recent", methods=["GET"])
    def get_recent_audit():
        """Get recent activity"""
        limit = request.args.get("limit", 100, type=int)
        activity = audit_trail.get_recent_activity(limit=limit)
        return jsonify({"recent_activity": activity})

    @workflow_api_bp.route("/audit/forced-transitions", methods=["GET"])
    def get_forced_transitions_audit():
        """Get all forced transitions"""
        days = request.args.get("days", 30, type=int)
        forced = audit_trail.get_forced_transitions(days=days)
        return jsonify({"forced_transitions": forced})

    @workflow_api_bp.route("/audit/statistics", methods=["GET"])
    def get_audit_statistics():
        """Get activity statistics"""
        days = request.args.get("days", 30, type=int)
        stats = audit_trail.get_activity_statistics(days=days)
        return jsonify(stats)

    @workflow_api_bp.route("/audit/compliance/<kanban_id>", methods=["GET"])
    def get_compliance_report(kanban_id):
        """Generate compliance report"""
        days = request.args.get("days", 30, type=int)
        report = audit_trail.generate_compliance_report(kanban_id, days=days)
        return jsonify(report)
