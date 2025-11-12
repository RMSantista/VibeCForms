"""
ProcessFactory - Factory para criar workflow processes a partir de form data

Responsabilidades:
- Criar workflow process quando form é salvo
- Mapear campos do form para campos do processo (field_mapping)
- Gerar process_id único
- Determinar estado inicial baseado no kanban
- Inicializar histórico vazio
"""

import uuid
from datetime import datetime
from typing import Dict, Optional
from .kanban_registry import KanbanRegistry


class ProcessFactory:
    """
    Factory for creating workflow processes from form submissions
    """

    def __init__(self, kanban_registry: KanbanRegistry):
        """
        Initialize ProcessFactory

        Args:
            kanban_registry: KanbanRegistry instance for accessing kanban definitions
        """
        self.registry = kanban_registry

    def create_from_form(
        self, form_path: str, form_data: dict, record_idx: int
    ) -> Optional[dict]:
        """
        Create workflow process from form submission

        Args:
            form_path: Path of the form (e.g., "pedidos")
            form_data: Form field values (dict)
            record_idx: Index of the record in form storage

        Returns:
            Process dict ready for WorkflowRepository.create_process()
            None if form is not linked to any kanban

        Process structure:
            {
                'process_id': str (UUID),
                'kanban_id': str,
                'source_form': str,
                'source_record_idx': int,
                'current_state': str (initial state ID),
                'field_values': dict (mapped from form_data),
                'created_at': str (ISO datetime),
                'updated_at': str (ISO datetime),
                'history': [] (empty initially)
            }
        """
        # Check if form is linked to a kanban
        kanban = self.registry.get_kanban_by_form(form_path)
        if not kanban:
            return None

        kanban_id = kanban["id"]

        # Get initial state
        initial_state = self.registry.get_initial_state(kanban_id)
        if not initial_state:
            raise ValueError(f"No initial state found for kanban '{kanban_id}'")

        # Generate process ID
        process_id = self.generate_process_id(kanban_id)

        # Map form fields to process fields
        field_values = self.apply_field_mapping(kanban, form_data)

        # Create process
        now = datetime.now().isoformat()

        # Calculate SLA if defined in kanban
        sla = self._calculate_sla(kanban, initial_state)

        process = {
            "process_id": process_id,
            "kanban_id": kanban_id,
            "source_form": form_path,
            "source_record_idx": record_idx,
            "current_state": initial_state["id"],
            "field_values": field_values,
            "created_at": now,
            "updated_at": now,
            "history": [],
            # New fields (Etapa 2.1)
            "tags": [],
            "assigned_to": None,
            "sla": sla,
            "metadata": {},
        }

        return process

    def generate_process_id(self, kanban_id: str) -> str:
        """
        Generate unique process ID

        Format: {kanban_id}_{timestamp}_{uuid4}
        Example: pedidos_20251102_a7b3c4d5

        Args:
            kanban_id: Kanban ID

        Returns:
            Unique process ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{kanban_id}_{timestamp}_{short_uuid}"

    def apply_field_mapping(self, kanban: dict, form_data: dict) -> dict:
        """
        Map form fields to process fields

        Uses field_mapping from kanban definition if present.
        If no mapping, copies all form fields directly.

        Field mapping format in kanban JSON:
        {
            "field_mapping": {
                "form_field_name": "process_field_name"
            }
        }

        Example:
        {
            "field_mapping": {
                "nome_cliente": "cliente",
                "valor_total": "valor",
                "data_pedido": "data"
            }
        }

        Args:
            kanban: Kanban definition dict
            form_data: Form field values

        Returns:
            Mapped field values dict
        """
        field_mapping = kanban.get("field_mapping", {})

        if not field_mapping:
            # No mapping defined - copy all fields directly
            return form_data.copy()

        # Apply mapping
        mapped_values = {}

        for form_field, process_field in field_mapping.items():
            if form_field in form_data:
                mapped_values[process_field] = form_data[form_field]

        return mapped_values

    def update_process_from_form(
        self, process: dict, form_data: dict, kanban: Optional[dict] = None
    ) -> dict:
        """
        Update existing process with new form data

        Useful when source form is updated and we want to sync the process.

        Args:
            process: Existing process dict
            form_data: Updated form field values
            kanban: Kanban definition (optional, will fetch if not provided)

        Returns:
            Updated process dict
        """
        if kanban is None:
            kanban = self.registry.get_kanban(process["kanban_id"])

        if not kanban:
            raise ValueError(f"Kanban '{process['kanban_id']}' not found")

        # Re-apply field mapping
        updated_field_values = self.apply_field_mapping(kanban, form_data)

        # Update process
        process["field_values"] = updated_field_values
        process["updated_at"] = datetime.now().isoformat()

        return process

    def validate_process_data(self, process: dict) -> bool:
        """
        Validate process data structure

        Checks:
        - Required fields present
        - Current state exists in kanban
        - Kanban exists in registry

        Args:
            process: Process dict to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails with specific error
        """
        # Check required fields
        required_fields = [
            "process_id",
            "kanban_id",
            "current_state",
            "field_values",
            "created_at",
            "updated_at",
            "history",
        ]

        for field in required_fields:
            if field not in process:
                raise ValueError(f"Missing required field: {field}")

        # Check kanban exists
        kanban = self.registry.get_kanban(process["kanban_id"])
        if not kanban:
            raise ValueError(f"Kanban '{process['kanban_id']}' not found in registry")

        # Check current_state exists in kanban
        state = self.registry.get_state(process["kanban_id"], process["current_state"])
        if not state:
            raise ValueError(
                f"State '{process['current_state']}' not found in kanban '{process['kanban_id']}'"
            )

        return True

    def clone_process(
        self,
        original_process: dict,
        new_source_form: Optional[str] = None,
        new_source_idx: Optional[int] = None,
    ) -> dict:
        """
        Clone a process (create a copy with new process_id)

        Useful for:
        - Creating similar processes
        - Testing
        - Process templates

        Args:
            original_process: Process to clone
            new_source_form: Optional new source form (keeps original if None)
            new_source_idx: Optional new source index (keeps original if None)

        Returns:
            New process dict with new process_id
        """
        cloned = original_process.copy()

        # Generate new process_id
        cloned["process_id"] = self.generate_process_id(original_process["kanban_id"])

        # Update timestamps
        now = datetime.now().isoformat()
        cloned["created_at"] = now
        cloned["updated_at"] = now

        # Reset history
        cloned["history"] = []

        # Reset to initial state
        initial_state = self.registry.get_initial_state(original_process["kanban_id"])
        if initial_state:
            cloned["current_state"] = initial_state["id"]

        # Update source if provided
        if new_source_form is not None:
            cloned["source_form"] = new_source_form

        if new_source_idx is not None:
            cloned["source_record_idx"] = new_source_idx

        # Copy field_values (deep copy to avoid references)
        cloned["field_values"] = original_process["field_values"].copy()

        return cloned

    def create_process_summary(self, process: dict) -> dict:
        """
        Create a summary view of a process (for UI display)

        Args:
            process: Full process dict

        Returns:
            Summary dict with key information
        """
        kanban = self.registry.get_kanban(process["kanban_id"])
        state = self.registry.get_state(process["kanban_id"], process["current_state"])

        summary = {
            "process_id": process["process_id"],
            "kanban_name": kanban["name"] if kanban else "Unknown",
            "current_state_name": state["name"] if state else "Unknown",
            "current_state_color": (
                state.get("color", "#cccccc") if state else "#cccccc"
            ),
            "created_at": process["created_at"],
            "updated_at": process["updated_at"],
            "transition_count": len(process.get("history", [])),
            "source_form": process.get("source_form", "N/A"),
        }

        # Add key field values (first 3 non-empty values)
        field_values = process.get("field_values", {})
        key_values = {}
        count = 0

        for key, value in field_values.items():
            if value and count < 3:
                key_values[key] = value
                count += 1

        summary["key_values"] = key_values

        return summary

    def bulk_create_processes(
        self, form_path: str, form_records: list, start_idx: int = 0
    ) -> list:
        """
        Create multiple processes from multiple form records

        Useful for:
        - Initial migration of existing forms to workflow
        - Batch imports

        Args:
            form_path: Form path
            form_records: List of form data dicts
            start_idx: Starting index for record_idx (default 0)

        Returns:
            List of created processes
        """
        processes = []

        for idx, form_data in enumerate(form_records):
            record_idx = start_idx + idx
            process = self.create_from_form(form_path, form_data, record_idx)

            if process:
                processes.append(process)

        return processes

    def get_process_metrics(self, process: dict) -> dict:
        """
        Calculate metrics for a process

        Args:
            process: Process dict

        Returns:
            Metrics dict:
                - age_hours: Hours since creation
                - transitions_count: Number of transitions
                - last_transition_hours: Hours since last transition (None if no transitions)
                - current_state_duration_hours: Hours in current state
        """
        from datetime import datetime, timezone

        created = datetime.fromisoformat(process["created_at"])
        now = datetime.now(timezone.utc)

        # Handle timezone-naive datetimes
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        age_hours = (now - created).total_seconds() / 3600

        history = process.get("history", [])
        transitions_count = len(history)

        last_transition_hours = None
        if history:
            last_transition = datetime.fromisoformat(history[-1]["timestamp"])
            if last_transition.tzinfo is None:
                last_transition = last_transition.replace(tzinfo=timezone.utc)
            last_transition_hours = (now - last_transition).total_seconds() / 3600

        # Current state duration
        if history:
            # Duration since last transition
            current_state_duration_hours = last_transition_hours
        else:
            # Duration since creation (never transitioned)
            current_state_duration_hours = age_hours

        return {
            "age_hours": round(age_hours, 2),
            "transitions_count": transitions_count,
            "last_transition_hours": (
                round(last_transition_hours, 2) if last_transition_hours else None
            ),
            "current_state_duration_hours": round(current_state_duration_hours, 2),
        }

    def _calculate_sla(self, kanban: dict, initial_state: dict) -> Optional[dict]:
        """
        Calculate SLA for a new process

        SLA can be defined at kanban level or per-state level.

        Args:
            kanban: Kanban definition
            initial_state: Initial state definition

        Returns:
            SLA dict with deadline, or None if no SLA defined
            {
                'deadline': str (ISO datetime),
                'warn_threshold_hours': int,
                'state_slas': {state_id: hours}
            }
        """
        from datetime import timedelta

        # Check for kanban-level SLA (total process duration)
        kanban_sla_hours = kanban.get("sla_hours")

        # Check for per-state SLA
        state_slas = {}
        for column in kanban.get("columns", []):
            if "sla_hours" in column:
                state_slas[column["id"]] = column["sla_hours"]

        if not kanban_sla_hours and not state_slas:
            return None

        sla = {}

        # Calculate deadline based on kanban-level SLA
        if kanban_sla_hours:
            now = datetime.now()
            deadline = now + timedelta(hours=kanban_sla_hours)
            sla["deadline"] = deadline.isoformat()
            sla["warn_threshold_hours"] = (
                kanban_sla_hours // 4
            )  # Warn at 75% (25% remaining)

        # Add per-state SLAs
        if state_slas:
            sla["state_slas"] = state_slas

        return sla if sla else None
