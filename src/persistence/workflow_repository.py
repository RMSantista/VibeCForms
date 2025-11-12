"""
WorkflowRepository - Repository específico para workflow processes

Extends BaseRepository com métodos específicos para workflow:
- Queries por kanban_id
- Queries por source_form
- Updates de estado
- Histórico de transições
- Analytics data

ARQUIVO SEPARADO:
- workflow_processes.txt: Estado ATUAL de cada processo (1 linha por processo)
- workflow_audit.txt: Log COMPLETO de transições (append-only, histórico)
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from .base import BaseRepository


class WorkflowRepository:
    """
    Repository for workflow processes

    Wraps a BaseRepository instance with workflow-specific queries.
    Uses delegation pattern to reuse existing persistence backends.
    """

    def __init__(
        self, base_repository: BaseRepository, form_path: str = "workflow_processes"
    ):
        """
        Initialize WorkflowRepository

        Args:
            base_repository: Instância de BaseRepository (TXT/SQLite/MySQL)
            form_path: Path for workflow processes storage (default: "workflow_processes")
        """
        self.repo = base_repository
        self.form_path = form_path
        self.audit_form_path = "workflow_audit"  # Separate file for audit log

    # ========== CRUD Operations ==========

    def create_process(self, process_data: dict) -> bool:
        """
        Create a new workflow process

        Args:
            process_data: Process data including:
                - process_id (str)
                - kanban_id (str)
                - source_form (str)
                - source_record_idx (int)
                - current_state (str)
                - field_values (dict)
                - created_at (str, ISO format)
                - updated_at (str, ISO format)

        Returns:
            bool: True if created successfully
        """
        # Ensure required fields
        if not process_data.get("process_id"):
            raise ValueError("process_id is required")
        if not process_data.get("kanban_id"):
            raise ValueError("kanban_id is required")
        if not process_data.get("current_state"):
            raise ValueError("current_state is required")

        # Add timestamps if not present
        now = datetime.now().isoformat()
        process_data.setdefault("created_at", now)
        process_data.setdefault("updated_at", now)

        # Remove history field - it's not stored in workflow_processes.txt anymore
        process_data.pop("history", None)

        # Convert nested dicts/lists to JSON strings for TXT backend compatibility
        process_data_flat = self._flatten_for_storage(process_data)

        # Dummy spec for workflow processes (generic structure)
        spec = self._get_workflow_spec()

        success = self.repo.create(self.form_path, spec, process_data_flat)

        # Log process creation to audit trail
        if success:
            self._log_to_audit(
                process_id=process_data["process_id"],
                kanban_id=process_data["kanban_id"],
                action="process_created",
                from_state=None,
                to_state=process_data["current_state"],
                user="system",
                type="system",
                metadata={"source_form": process_data.get("source_form")},
            )

        return success

    def get_all_processes(self) -> List[dict]:
        """Get all workflow processes"""
        spec = self._get_workflow_spec()
        processes = self.repo.read_all(self.form_path, spec)
        return [self._unflatten_from_storage(p) for p in processes]

    def get_process_by_id(self, process_id: str) -> Optional[dict]:
        """
        Get a specific process by ID

        Args:
            process_id: Process ID to search

        Returns:
            Process dict or None if not found
        """
        processes = self.get_all_processes()
        for process in processes:
            if process.get("process_id") == process_id:
                return process
        return None

    def update_process(self, process_id: str, updates: dict) -> bool:
        """
        Update a workflow process

        Args:
            process_id: Process ID to update
            updates: Fields to update

        Returns:
            bool: True if updated successfully
        """
        processes = self.get_all_processes()

        for idx, process in enumerate(processes):
            if process.get("process_id") == process_id:
                # Merge updates
                process.update(updates)
                process["updated_at"] = datetime.now().isoformat()

                # Flatten and update
                process_flat = self._flatten_for_storage(process)
                spec = self._get_workflow_spec()

                return self.repo.update(self.form_path, spec, idx, process_flat)

        return False

    def delete_process(self, process_id: str) -> bool:
        """
        Delete a workflow process

        Args:
            process_id: Process ID to delete

        Returns:
            bool: True if deleted successfully
        """
        processes = self.get_all_processes()

        for idx, process in enumerate(processes):
            if process.get("process_id") == process_id:
                spec = self._get_workflow_spec()
                success = self.repo.delete(self.form_path, spec, idx)

                # Log process deletion to audit trail
                if success:
                    self._log_to_audit(
                        process_id=process_id,
                        kanban_id=process.get("kanban_id", "unknown"),
                        action="process_deleted",
                        from_state=process.get("current_state"),
                        to_state=None,
                        user="system",
                        type="system",
                    )

                return success

        return False

    # ========== Workflow-Specific Queries ==========

    def get_processes_by_kanban(self, kanban_id: str) -> List[dict]:
        """
        Get all processes for a specific kanban

        Args:
            kanban_id: Kanban ID to filter

        Returns:
            List of process dicts
        """
        processes = self.get_all_processes()
        return [p for p in processes if p.get("kanban_id") == kanban_id]

    def get_processes_by_source_form(self, source_form: str) -> List[dict]:
        """
        Get all processes originating from a specific form

        Args:
            source_form: Source form path

        Returns:
            List of process dicts
        """
        processes = self.get_all_processes()
        return [p for p in processes if p.get("source_form") == source_form]

    def get_processes_by_state(self, kanban_id: str, state: str) -> List[dict]:
        """
        Get all processes in a specific state

        Args:
            kanban_id: Kanban ID to filter
            state: State ID to filter

        Returns:
            List of process dicts
        """
        processes = self.get_processes_by_kanban(kanban_id)
        return [p for p in processes if p.get("current_state") == state]

    def update_process_state(
        self,
        process_id: str,
        new_state: str,
        transition_type: str = "manual",
        user: str = "system",
        justification: str = None,
        duration_in_previous_state: float = None,
        prerequisites_met: bool = True,
    ) -> bool:
        """
        Update process state and log transition in audit trail

        Args:
            process_id: Process ID
            new_state: New state ID
            transition_type: Type of transition (manual, system, agent)
            user: User performing transition
            justification: Optional justification for forced transitions
            duration_in_previous_state: Time spent in previous state (hours)
            prerequisites_met: Whether all prerequisites were met

        Returns:
            bool: True if updated successfully
        """
        process = self.get_process_by_id(process_id)
        if not process:
            return False

        old_state = process.get("current_state")

        # Update process current_state only (no history field)
        updates = {"current_state": new_state}
        success = self.update_process(process_id, updates)

        # Log transition to audit trail
        if success:
            metadata = {}
            if justification:
                metadata["justification"] = justification
            if prerequisites_met is not None:
                metadata["prerequisites_met"] = prerequisites_met
            if duration_in_previous_state is not None:
                metadata["duration_in_previous_state"] = duration_in_previous_state

            self._log_to_audit(
                process_id=process_id,
                kanban_id=process.get("kanban_id", "unknown"),
                action="state_changed",
                from_state=old_state,
                to_state=new_state,
                user=user,
                type=transition_type,
                metadata=metadata,
            )

        return success

    def get_process_history(self, process_id: str) -> List[dict]:
        """
        Get transition history for a process from audit trail

        Args:
            process_id: Process ID

        Returns:
            List of history entries (oldest first)
        """
        audit_entries = self._read_audit_log()

        # Filter entries for this process_id
        process_entries = [
            entry for entry in audit_entries if entry.get("process_id") == process_id
        ]

        return process_entries

    # ========== Analytics ==========

    def get_analytics_data(
        self,
        kanban_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """
        Get analytics data for a kanban

        Args:
            kanban_id: Kanban ID
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            Analytics dict with metrics:
                - total_processes
                - by_state (count per state)
                - by_transition_type (count per type)
                - avg_transitions_per_process
        """
        processes = self.get_processes_by_kanban(kanban_id)

        # Date filtering
        if start_date or end_date:
            filtered = []
            for p in processes:
                created = p.get("created_at", "")
                if start_date and created < start_date:
                    continue
                if end_date and created > end_date:
                    continue
                filtered.append(p)
            processes = filtered

        # Compute metrics
        by_state = {}
        by_transition_type = {}
        total_transitions = 0

        # Get all audit entries for this kanban
        all_audit_entries = self._read_audit_log()
        kanban_audit_entries = [
            entry
            for entry in all_audit_entries
            if entry.get("kanban_id") == kanban_id
            and entry.get("action") == "state_changed"
        ]

        # Apply date filters to audit entries
        if start_date or end_date:
            filtered_audit = []
            for entry in kanban_audit_entries:
                timestamp = entry.get("timestamp", "")
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                filtered_audit.append(entry)
            kanban_audit_entries = filtered_audit

        for process in processes:
            # Count by state
            state = process.get("current_state", "unknown")
            by_state[state] = by_state.get(state, 0) + 1

        # Count transitions by type from audit trail
        for entry in kanban_audit_entries:
            total_transitions += 1
            trans_type = entry.get("type", "unknown")
            by_transition_type[trans_type] = by_transition_type.get(trans_type, 0) + 1

        avg_transitions = total_transitions / len(processes) if processes else 0

        return {
            "total_processes": len(processes),
            "by_state": by_state,
            "by_transition_type": by_transition_type,
            "avg_transitions_per_process": round(avg_transitions, 2),
        }

    # ========== Helper Methods ==========

    def _get_workflow_spec(self) -> dict:
        """
        Get generic spec for workflow processes (estado atual apenas)

        Returns:
            Spec dict compatible with BaseRepository
        """
        return {
            "title": "Workflow Processes",
            "fields": [
                {"name": "process_id", "type": "text", "required": True},
                {"name": "kanban_id", "type": "text", "required": True},
                {"name": "source_form", "type": "text", "required": False},
                {"name": "source_record_idx", "type": "number", "required": False},
                {"name": "current_state", "type": "text", "required": True},
                {
                    "name": "field_values",
                    "type": "text",
                    "required": False,
                },  # JSON string
                {"name": "created_at", "type": "text", "required": True},
                {"name": "updated_at", "type": "text", "required": True},
                # New fields (Etapa 2.1)
                {"name": "tags", "type": "text", "required": False},  # JSON array
                {"name": "assigned_to", "type": "text", "required": False},
                {"name": "sla", "type": "text", "required": False},  # JSON object
                {"name": "metadata", "type": "text", "required": False},  # JSON object
                # Removed: history field (now stored in workflow_audit.txt)
            ],
        }

    def _flatten_for_storage(self, process_data: dict) -> dict:
        """
        Flatten nested structures for TXT backend compatibility

        Converts dicts/lists to JSON strings
        """
        flat = process_data.copy()

        # Convert nested structures to JSON strings
        if "field_values" in flat and isinstance(flat["field_values"], dict):
            flat["field_values"] = json.dumps(flat["field_values"])

        # Convert new fields (Etapa 2.1)
        if "tags" in flat and isinstance(flat["tags"], list):
            flat["tags"] = json.dumps(flat["tags"])

        if "sla" in flat and isinstance(flat["sla"], dict):
            flat["sla"] = json.dumps(flat["sla"])

        if "metadata" in flat and isinstance(flat["metadata"], dict):
            flat["metadata"] = json.dumps(flat["metadata"])

        # Remove history field if present (not stored in workflow_processes.txt)
        flat.pop("history", None)

        return flat

    def _unflatten_from_storage(self, process_data: dict) -> dict:
        """
        Unflatten structures from storage

        Converts JSON strings back to dicts/lists
        """
        unflat = process_data.copy()

        # Parse JSON strings back to structures
        if "field_values" in unflat and isinstance(unflat["field_values"], str):
            try:
                unflat["field_values"] = json.loads(unflat["field_values"])
            except json.JSONDecodeError:
                unflat["field_values"] = {}

        # Parse new fields (Etapa 2.1)
        if "tags" in unflat and isinstance(unflat["tags"], str):
            try:
                unflat["tags"] = json.loads(unflat["tags"])
            except json.JSONDecodeError:
                unflat["tags"] = []

        if "sla" in unflat and isinstance(unflat["sla"], str):
            try:
                unflat["sla"] = json.loads(unflat["sla"])
            except json.JSONDecodeError:
                unflat["sla"] = None

        if "metadata" in unflat and isinstance(unflat["metadata"], str):
            try:
                unflat["metadata"] = json.loads(unflat["metadata"])
            except json.JSONDecodeError:
                unflat["metadata"] = {}

        # Note: history is NOT loaded here - use get_process_history() to read from audit trail

        return unflat

    # ========== Audit Trail Methods ==========

    def _log_to_audit(
        self,
        process_id: str,
        kanban_id: str,
        action: str,
        from_state: Optional[str],
        to_state: Optional[str],
        user: str,
        type: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Log an entry to the audit trail (workflow_audit.txt)

        Args:
            process_id: Process ID
            kanban_id: Kanban ID
            action: Action type (process_created, state_changed, process_updated, process_deleted)
            from_state: Previous state (or None)
            to_state: New state (or None)
            user: User performing action
            type: Transition type (manual, system, agent)
            metadata: Optional metadata dict (justification, duration, prerequisites_met, etc.)

        Returns:
            bool: True if logged successfully
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "process_id": process_id,
            "kanban_id": kanban_id,
            "action": action,
            "from_state": from_state or "",
            "to_state": to_state or "",
            "user": user,
            "type": type,
            "justification": metadata.get("justification", "") if metadata else "",
            "duration_in_previous_state": (
                metadata.get("duration_in_previous_state", "") if metadata else ""
            ),
            "prerequisites_met": (
                metadata.get("prerequisites_met", "") if metadata else ""
            ),
            "metadata": json.dumps(metadata) if metadata else "",
        }

        # Flatten for storage
        audit_entry_flat = self._flatten_audit_entry(audit_entry)

        # Append to audit log
        spec = self._get_audit_spec()

        try:
            return self.repo.create(self.audit_form_path, spec, audit_entry_flat)
        except Exception as e:
            print(f"❌ Error logging to audit trail: {e}")
            return False

    def _read_audit_log(self) -> List[dict]:
        """
        Read all entries from audit trail

        Returns:
            List of audit entries (oldest first)
        """
        spec = self._get_audit_spec()

        try:
            entries = self.repo.read_all(self.audit_form_path, spec)
            return [self._unflatten_audit_entry(e) for e in entries]
        except FileNotFoundError:
            # Audit file doesn't exist yet
            return []
        except Exception as e:
            print(f"❌ Error reading audit trail: {e}")
            return []

    def _get_audit_spec(self) -> dict:
        """
        Get spec for audit trail (workflow_audit.txt)

        Format: timestamp;process_id;kanban_id;action;from_state;to_state;user;type;justification;duration_in_previous_state;prerequisites_met;metadata

        Returns:
            Spec dict compatible with BaseRepository
        """
        return {
            "title": "Workflow Audit Trail",
            "fields": [
                {"name": "timestamp", "type": "text", "required": True},
                {"name": "process_id", "type": "text", "required": True},
                {"name": "kanban_id", "type": "text", "required": True},
                {
                    "name": "action",
                    "type": "text",
                    "required": True,
                },  # process_created, state_changed, process_updated, process_deleted
                {"name": "from_state", "type": "text", "required": False},
                {"name": "to_state", "type": "text", "required": False},
                {"name": "user", "type": "text", "required": True},
                {
                    "name": "type",
                    "type": "text",
                    "required": True,
                },  # manual, system, agent
                {"name": "justification", "type": "text", "required": False},
                {
                    "name": "duration_in_previous_state",
                    "type": "text",
                    "required": False,
                },
                {"name": "prerequisites_met", "type": "text", "required": False},
                {
                    "name": "metadata",
                    "type": "text",
                    "required": False,
                },  # JSON string for additional data
            ],
        }

    def _flatten_audit_entry(self, audit_entry: dict) -> dict:
        """Flatten audit entry for storage"""
        flat = audit_entry.copy()

        # Convert metadata dict to JSON string
        if "metadata" in flat and isinstance(flat["metadata"], dict):
            flat["metadata"] = json.dumps(flat["metadata"])

        # Ensure all fields are strings
        for key in flat:
            if flat[key] is None:
                flat[key] = ""
            elif not isinstance(flat[key], str):
                flat[key] = str(flat[key])

        return flat

    def _unflatten_audit_entry(self, audit_entry: dict) -> dict:
        """Unflatten audit entry from storage"""
        unflat = audit_entry.copy()

        # Parse metadata JSON string
        if (
            "metadata" in unflat
            and isinstance(unflat["metadata"], str)
            and unflat["metadata"]
        ):
            try:
                unflat["metadata"] = json.loads(unflat["metadata"])
            except json.JSONDecodeError:
                unflat["metadata"] = {}

        return unflat

    # ========== Storage Management ==========

    def create_storage(self) -> bool:
        """Create storage for workflow processes"""
        spec = self._get_workflow_spec()
        return self.repo.create_storage(self.form_path, spec)

    def drop_storage(self) -> bool:
        """Drop storage for workflow processes"""
        return self.repo.drop_storage(self.form_path)

    def exists(self) -> bool:
        """Check if workflow storage exists"""
        return self.repo.exists(self.form_path)

    def has_data(self) -> bool:
        """Check if workflow storage has data"""
        return self.repo.has_data(self.form_path)

    def count(self) -> int:
        """Count total workflow processes"""
        return len(self.get_all_processes())
