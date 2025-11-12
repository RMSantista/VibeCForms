"""
FormTriggerManager - Hook system para detectar form saves e criar processos

Responsabilidades:
- Hook no form save (após form.create() ou form.update())
- Detectar se form está linked a kanban
- Criar processo automaticamente via ProcessFactory
- Persistir processo via WorkflowRepository
- Logging de processo criado
"""

from typing import Optional, Callable
from .kanban_registry import KanbanRegistry
from .process_factory import ProcessFactory

# Import WorkflowRepository - check if src is in path first
try:
    from persistence.workflow_repository import WorkflowRepository
except ModuleNotFoundError:
    # If running from tests, use relative import
    import sys
    import os
    from pathlib import Path

    # Add src to path if not already there (use absolute path)
    src_path = str(Path(__file__).parent.parent.resolve())
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from persistence.workflow_repository import WorkflowRepository


class FormTriggerManager:
    """
    Manager for form save hooks and automatic process creation

    Integrates with VibeCForms form save operations to automatically
    create workflow processes when forms linked to kanbans are saved.
    """

    def __init__(
        self,
        kanban_registry: KanbanRegistry,
        process_factory: ProcessFactory,
        workflow_repository: WorkflowRepository,
    ):
        """
        Initialize FormTriggerManager

        Args:
            kanban_registry: KanbanRegistry instance
            process_factory: ProcessFactory instance
            workflow_repository: WorkflowRepository instance
        """
        self.registry = kanban_registry
        self.factory = process_factory
        self.repo = workflow_repository

        # Hooks registry
        self._on_process_created_hooks = []
        self._on_process_updated_hooks = []

    # ========== Main Trigger Methods ==========

    def on_form_created(
        self, form_path: str, form_data: dict, record_idx: int
    ) -> Optional[str]:
        """
        Triggered when a new form record is created

        Checks if form is linked to kanban and creates process if so.

        Args:
            form_path: Path of the form (e.g., "pedidos")
            form_data: Form field values
            record_idx: Index of the created record

        Returns:
            process_id if process was created, None otherwise
        """
        # Check if form is linked to any kanban
        if not self.registry.is_form_linked(form_path):
            return None

        # Create process
        process = self.factory.create_from_form(form_path, form_data, record_idx)

        if not process:
            return None

        # Persist process
        success = self.repo.create_process(process)

        if success:
            process_id = process["process_id"]
            print(
                f"✅ Created workflow process: {process_id} (from form '{form_path}')"
            )

            # Trigger hooks
            self._trigger_on_process_created_hooks(process)

            return process_id
        else:
            print(f"❌ Failed to create workflow process from form '{form_path}'")
            return None

    def on_form_updated(self, form_path: str, form_data: dict, record_idx: int) -> bool:
        """
        Triggered when an existing form record is updated

        Updates the linked workflow process if it exists.

        Args:
            form_path: Path of the form
            form_data: Updated form field values
            record_idx: Index of the updated record

        Returns:
            True if process was updated, False otherwise
        """
        # Check if form is linked to any kanban
        if not self.registry.is_form_linked(form_path):
            return False

        # Find existing process
        processes = self.repo.get_processes_by_source_form(form_path)

        # Find process matching this record_idx
        matching_process = None
        for process in processes:
            if process.get("source_record_idx") == record_idx:
                matching_process = process
                break

        if not matching_process:
            # No existing process for this record - could be legacy data
            # Create new process
            return self.on_form_created(form_path, form_data, record_idx) is not None

        # Get kanban
        kanban = self.registry.get_kanban(matching_process["kanban_id"])

        # Update process with new form data
        updated_process = self.factory.update_process_from_form(
            matching_process, form_data, kanban
        )

        # Persist update
        success = self.repo.update_process(
            matching_process["process_id"],
            {
                "field_values": updated_process["field_values"],
                "updated_at": updated_process["updated_at"],
            },
        )

        if success:
            print(f"✅ Updated workflow process: {matching_process['process_id']}")

            # Trigger hooks
            self._trigger_on_process_updated_hooks(updated_process)

            return True
        else:
            print(
                f"❌ Failed to update workflow process {matching_process['process_id']}"
            )
            return False

    def on_form_deleted(
        self, form_path: str, record_idx: int, delete_process: bool = False
    ) -> bool:
        """
        Triggered when a form record is deleted

        By default, does NOT delete the workflow process (preserves history).
        Set delete_process=True to also delete the process.

        Args:
            form_path: Path of the form
            record_idx: Index of the deleted record
            delete_process: If True, also delete the workflow process

        Returns:
            True if action was successful
        """
        # Check if form is linked to any kanban
        if not self.registry.is_form_linked(form_path):
            return False

        # Find existing process
        processes = self.repo.get_processes_by_source_form(form_path)

        matching_process = None
        for process in processes:
            if process.get("source_record_idx") == record_idx:
                matching_process = process
                break

        if not matching_process:
            return False

        if delete_process:
            # Delete the process
            success = self.repo.delete_process(matching_process["process_id"])
            if success:
                print(f"🗑️  Deleted workflow process: {matching_process['process_id']}")
            return success
        else:
            # Mark as orphaned (source deleted) but keep process
            success = self.repo.update_process(
                matching_process["process_id"],
                {"source_form": f"[DELETED] {form_path}", "source_record_idx": -1},
            )
            if success:
                print(
                    f"⚠️  Marked process as orphaned: {matching_process['process_id']}"
                )
            return success

    # ========== Bulk Operations ==========

    def sync_existing_forms(
        self, form_path: str, form_records: list, recreate: bool = False
    ) -> dict:
        """
        Sync existing form records with workflow processes

        Useful for:
        - Initial migration when adding workflow to existing forms
        - Fixing inconsistencies between forms and processes

        Args:
            form_path: Form path to sync
            form_records: List of all form records
            recreate: If True, delete existing processes and recreate all

        Returns:
            Dict with sync stats:
                - created: Number of processes created
                - updated: Number of processes updated
                - skipped: Number of records skipped (not linked to kanban)
                - errors: Number of errors
        """
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        # Check if form is linked to kanban
        if not self.registry.is_form_linked(form_path):
            print(f"⚠️  Form '{form_path}' is not linked to any kanban")
            stats["skipped"] = len(form_records)
            return stats

        # Get existing processes
        existing_processes = self.repo.get_processes_by_source_form(form_path)

        # Create index of existing processes by record_idx
        existing_by_idx = {}
        for process in existing_processes:
            idx = process.get("source_record_idx")
            if idx is not None and idx >= 0:
                existing_by_idx[idx] = process

        # If recreate, delete all existing processes
        if recreate:
            for process in existing_processes:
                self.repo.delete_process(process["process_id"])
            existing_by_idx = {}
            print(
                f"🗑️  Deleted {len(existing_processes)} existing processes for recreation"
            )

        # Process each form record
        for idx, form_data in enumerate(form_records):
            try:
                if idx in existing_by_idx:
                    # Update existing process
                    process = existing_by_idx[idx]
                    kanban = self.registry.get_kanban(process["kanban_id"])

                    updated_process = self.factory.update_process_from_form(
                        process, form_data, kanban
                    )

                    success = self.repo.update_process(
                        process["process_id"],
                        {
                            "field_values": updated_process["field_values"],
                            "updated_at": updated_process["updated_at"],
                        },
                    )

                    if success:
                        stats["updated"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    # Create new process
                    process = self.factory.create_from_form(form_path, form_data, idx)

                    if process:
                        success = self.repo.create_process(process)
                        if success:
                            stats["created"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        stats["errors"] += 1

            except Exception as e:
                print(f"❌ Error processing record {idx}: {e}")
                stats["errors"] += 1

        print(f"\n✅ Sync completed for '{form_path}':")
        print(f"   Created: {stats['created']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Errors: {stats['errors']}")

        return stats

    # ========== Hook System ==========

    def register_on_process_created_hook(
        self, callback: Callable[[dict], None]
    ) -> None:
        """
        Register a callback to be called when a process is created

        Args:
            callback: Function that takes process dict as argument

        Example:
            def log_process(process):
                print(f"Process created: {process['process_id']}")

            manager.register_on_process_created_hook(log_process)
        """
        self._on_process_created_hooks.append(callback)

    def register_on_process_updated_hook(
        self, callback: Callable[[dict], None]
    ) -> None:
        """
        Register a callback to be called when a process is updated

        Args:
            callback: Function that takes process dict as argument
        """
        self._on_process_updated_hooks.append(callback)

    def _trigger_on_process_created_hooks(self, process: dict) -> None:
        """Call all registered on_process_created hooks"""
        for hook in self._on_process_created_hooks:
            try:
                hook(process)
            except Exception as e:
                print(f"❌ Error in on_process_created hook: {e}")

    def _trigger_on_process_updated_hooks(self, process: dict) -> None:
        """Call all registered on_process_updated hooks"""
        for hook in self._on_process_updated_hooks:
            try:
                hook(process)
            except Exception as e:
                print(f"❌ Error in on_process_updated hook: {e}")

    # ========== Diagnostics ==========

    def get_sync_status(self, form_path: str) -> dict:
        """
        Get synchronization status between form and workflow processes

        Args:
            form_path: Form path to check

        Returns:
            Status dict:
                - is_linked: Boolean
                - kanban_id: Kanban ID or None
                - process_count: Number of processes
                - orphaned_count: Number of orphaned processes
        """
        status = {
            "is_linked": False,
            "kanban_id": None,
            "process_count": 0,
            "orphaned_count": 0,
        }

        # Check if linked
        if not self.registry.is_form_linked(form_path):
            return status

        status["is_linked"] = True
        status["kanban_id"] = self.registry.get_kanban_id_for_form(form_path)

        # Get processes
        processes = self.repo.get_processes_by_source_form(form_path)
        status["process_count"] = len(processes)

        # Count orphaned
        orphaned = [p for p in processes if p.get("source_record_idx", -1) < 0]
        status["orphaned_count"] = len(orphaned)

        return status

    def cleanup_orphaned_processes(self, form_path: str) -> int:
        """
        Delete orphaned processes (where source_record_idx = -1)

        Args:
            form_path: Form path to clean

        Returns:
            Number of processes deleted
        """
        # Get all processes and filter for this form (including [DELETED] prefix)
        all_processes = self.repo.get_all_processes()

        # Find processes for this form (including orphaned ones with [DELETED] prefix)
        form_processes = []
        for process in all_processes:
            source_form = process.get("source_form", "")
            if source_form == form_path or source_form == f"[DELETED] {form_path}":
                form_processes.append(process)

        # Filter for orphaned (source_record_idx < 0)
        orphaned = [p for p in form_processes if p.get("source_record_idx", -1) < 0]

        deleted_count = 0
        for process in orphaned:
            success = self.repo.delete_process(process["process_id"])
            if success:
                deleted_count += 1

        if deleted_count > 0:
            print(f"🗑️  Deleted {deleted_count} orphaned processes from '{form_path}'")

        return deleted_count
