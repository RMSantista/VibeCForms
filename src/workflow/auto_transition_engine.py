"""
AutoTransitionEngine - Automatic workflow state transitions

Responsabilidades:
- Execute automatic transitions when conditions are met
- Check prerequisites before transitions
- Handle timeout-based transitions
- Support cascade progression (chain of auto-transitions)
- Allow forced transitions with justification
- Track auto-transition history

Transition Types:
- manual: User-initiated via UI
- system: Automatic via engine (prerequisites met)
- agent: AI-suggested (Phase 3 feature)
"""

from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from .kanban_registry import KanbanRegistry
from .prerequisite_checker import PrerequisiteChecker


class AutoTransitionEngine:
    """
    Engine for automatic workflow transitions

    Checks prerequisites and executes transitions automatically
    when conditions are met.
    """

    def __init__(
        self, kanban_registry: KanbanRegistry, prerequisite_checker: PrerequisiteChecker
    ):
        """
        Initialize AutoTransitionEngine

        Args:
            kanban_registry: KanbanRegistry instance
            prerequisite_checker: PrerequisiteChecker instance
        """
        self.registry = kanban_registry
        self.checker = prerequisite_checker

    # ========== Auto-Transition Checking ==========

    def check_auto_transition(self, process: dict) -> Optional[Dict]:
        """
        Check if process should auto-transition to next state

        Looks at current state's auto_transition_to and evaluates prerequisites.

        Args:
            process: Process dict

        Returns:
            Dict with transition info if should transition, None otherwise:
            {
                'to_state': str,
                'reason': str,
                'prerequisites_satisfied': bool
            }
        """
        kanban_id = process.get("kanban_id")
        current_state_id = process.get("current_state")

        # Get kanban and current state
        kanban = self.registry.get_kanban(kanban_id)
        if not kanban:
            return None

        current_state = self.registry.get_state(kanban_id, current_state_id)
        if not current_state:
            return None

        # Check if state has auto_transition_to configured
        auto_transition_to = current_state.get("auto_transition_to")
        if not auto_transition_to:
            return None

        # Get transition definition
        transition = self.registry.get_transition(
            kanban_id, current_state_id, auto_transition_to
        )
        if not transition:
            return None

        # Check prerequisites
        prerequisites = transition.get("prerequisites", [])
        prereq_results = self.checker.check_prerequisites(
            prerequisites, process, kanban
        )

        all_satisfied = self.checker.are_all_satisfied(prereq_results)

        return {
            "to_state": auto_transition_to,
            "reason": "auto_transition",
            "prerequisites_satisfied": all_satisfied,
            "prerequisite_results": prereq_results,
            "transition": transition,
        }

    def check_timeout_transition(self, process: dict) -> Optional[Dict]:
        """
        Check if process should transition due to timeout

        Looks at current state's timeout_hours and checks if time elapsed.

        Args:
            process: Process dict

        Returns:
            Transition info if timeout expired, None otherwise
        """
        kanban_id = process.get("kanban_id")
        current_state_id = process.get("current_state")

        kanban = self.registry.get_kanban(kanban_id)
        if not kanban:
            return None

        current_state = self.registry.get_state(kanban_id, current_state_id)
        if not current_state:
            return None

        # Check if state has timeout configured
        timeout_hours = current_state.get("timeout_hours")
        auto_transition_to = current_state.get("auto_transition_to")

        if not timeout_hours or not auto_transition_to:
            return None

        # Calculate time in current state
        history = process.get("history", [])

        if history:
            # Time since last transition
            last_transition = history[-1]
            timestamp_str = last_transition.get("timestamp")
        else:
            # Time since creation
            timestamp_str = process.get("created_at")

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed_hours = (now - timestamp).total_seconds() / 3600

            if elapsed_hours >= timeout_hours:
                # Timeout expired
                return {
                    "to_state": auto_transition_to,
                    "reason": "timeout",
                    "elapsed_hours": elapsed_hours,
                    "timeout_hours": timeout_hours,
                }

        except (ValueError, TypeError):
            pass

        return None

    def should_auto_transition(self, process: dict) -> Optional[Dict]:
        """
        Check if process should auto-transition (any reason)

        Checks both auto_transition and timeout conditions.

        Args:
            process: Process dict

        Returns:
            Transition info if should transition, None otherwise
        """
        # First check timeout (higher priority)
        timeout_result = self.check_timeout_transition(process)
        if timeout_result:
            return timeout_result

        # Then check auto-transition
        auto_result = self.check_auto_transition(process)
        if auto_result and auto_result.get("prerequisites_satisfied"):
            return auto_result

        return None

    # ========== Cascade Progression ==========

    def execute_cascade_progression(
        self, process: dict, workflow_repo, max_depth: int = 10
    ) -> List[Dict]:
        """
        Execute chain of automatic transitions

        Follows auto_transition_to chain until no more transitions available.
        Prevents infinite loops with max_depth.

        Args:
            process: Process dict
            workflow_repo: WorkflowRepository instance for persistence
            max_depth: Maximum number of transitions in cascade

        Returns:
            List of executed transitions:
            [
                {
                    'from_state': str,
                    'to_state': str,
                    'reason': str,
                    'success': bool
                },
                ...
            ]
        """
        transitions_executed = []
        depth = 0

        while depth < max_depth:
            # Check if should transition
            transition_info = self.should_auto_transition(process)

            if not transition_info:
                break

            from_state = process["current_state"]
            to_state = transition_info["to_state"]
            reason = transition_info["reason"]

            # Execute transition
            success = workflow_repo.update_process_state(
                process["process_id"],
                to_state,
                transition_type="system",
                user="auto_transition_engine",
                justification=f"Auto-transition: {reason}",
            )

            transitions_executed.append(
                {
                    "from_state": from_state,
                    "to_state": to_state,
                    "reason": reason,
                    "success": success,
                }
            )

            if not success:
                break

            # Update process state for next iteration
            process["current_state"] = to_state

            # Update history
            if "history" not in process:
                process["history"] = []

            process["history"].append(
                {
                    "from_state": from_state,
                    "to_state": to_state,
                    "timestamp": datetime.now().isoformat(),
                    "type": "system",
                    "user": "auto_transition_engine",
                    "justification": f"Auto-transition: {reason}",
                }
            )

            depth += 1

        return transitions_executed

    # ========== Forced Transitions ==========

    def can_force_transition(self, process: dict, to_state: str, user: str) -> Dict:
        """
        Check if a forced transition is allowed

        Even if prerequisites are not met, forced transitions are allowed
        with proper justification (following "Warn, Not Block" philosophy).

        Args:
            process: Process dict
            to_state: Target state
            user: User requesting forced transition

        Returns:
            Dict with:
            {
                'allowed': bool,
                'warnings': List[str],
                'prerequisite_results': List[dict]
            }
        """
        kanban_id = process.get("kanban_id")
        from_state = process.get("current_state")

        kanban = self.registry.get_kanban(kanban_id)
        if not kanban:
            return {
                "allowed": False,
                "warnings": ["Kanban not found"],
                "prerequisite_results": [],
            }

        # NEW PHILOSOPHY: Check if transition is explicitly blocked
        if not self.registry.can_transition(kanban_id, from_state, to_state):
            blocked_transition = self.registry.get_blocked_transition(
                kanban_id, from_state, to_state
            )
            reason = (
                blocked_transition.get("reason", "This transition is blocked")
                if blocked_transition
                else "This transition is blocked"
            )
            return {
                "allowed": False,
                "warnings": [reason],
                "prerequisite_results": [],
            }

        # Get recommended transition and check prerequisites
        transition = self.registry.get_transition(kanban_id, from_state, to_state)
        prerequisites = transition.get("prerequisites", []) if transition else []

        prereq_results = self.checker.check_prerequisites(
            prerequisites, process, kanban
        )

        # Forced transitions are ALWAYS allowed (Warn, Not Block)
        # But we return warnings about unmet prerequisites
        warnings = []
        for result in prereq_results:
            if not result.get("satisfied"):
                warnings.append(result.get("message", "Prerequisite not satisfied"))

        return {
            "allowed": True,
            "warnings": warnings,
            "prerequisite_results": prereq_results,
        }

    def execute_forced_transition(
        self, process: dict, to_state: str, user: str, justification: str, workflow_repo
    ) -> bool:
        """
        Execute a forced transition with justification

        Args:
            process: Process dict
            to_state: Target state
            user: User forcing the transition
            justification: Business justification for overriding prerequisites
            workflow_repo: WorkflowRepository for persistence

        Returns:
            bool: True if successful
        """
        # Check if allowed
        check_result = self.can_force_transition(process, to_state, user)

        if not check_result["allowed"]:
            return False

        # Execute transition
        success = workflow_repo.update_process_state(
            process["process_id"],
            to_state,
            transition_type="manual",
            user=user,
            justification=f"FORCED: {justification}",
        )

        return success

    # ========== Batch Processing ==========

    def process_all_auto_transitions(
        self, workflow_repo, kanban_id: Optional[str] = None
    ) -> Dict:
        """
        Process all pending auto-transitions across all processes

        Should be called periodically (e.g., cron job, background task)

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_id: Optional kanban ID to filter (process all if None)

        Returns:
            Stats dict:
            {
                'processes_checked': int,
                'transitions_executed': int,
                'cascades_executed': int,
                'errors': int
            }
        """
        stats = {
            "processes_checked": 0,
            "transitions_executed": 0,
            "cascades_executed": 0,
            "errors": 0,
        }

        # Get all processes to check
        if kanban_id:
            processes = workflow_repo.get_processes_by_kanban(kanban_id)
        else:
            processes = workflow_repo.get_all_processes()

        for process in processes:
            stats["processes_checked"] += 1

            try:
                # Execute cascade progression
                transitions = self.execute_cascade_progression(process, workflow_repo)

                if transitions:
                    stats["transitions_executed"] += len(transitions)
                    stats["cascades_executed"] += 1

            except Exception as e:
                stats["errors"] += 1
                print(
                    f"❌ Error processing auto-transition for {process.get('process_id')}: {e}"
                )

        return stats

    # ========== Diagnostics ==========

    def get_pending_auto_transitions(
        self, workflow_repo, kanban_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get list of processes with pending auto-transitions

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_id: Optional kanban filter

        Returns:
            List of dicts:
            [
                {
                    'process_id': str,
                    'current_state': str,
                    'to_state': str,
                    'reason': str,
                    'prerequisites_satisfied': bool
                },
                ...
            ]
        """
        pending = []

        if kanban_id:
            processes = workflow_repo.get_processes_by_kanban(kanban_id)
        else:
            processes = workflow_repo.get_all_processes()

        for process in processes:
            transition_info = self.should_auto_transition(process)

            if transition_info:
                pending.append(
                    {
                        "process_id": process.get("process_id"),
                        "current_state": process.get("current_state"),
                        "to_state": transition_info.get("to_state"),
                        "reason": transition_info.get("reason"),
                        "prerequisites_satisfied": transition_info.get(
                            "prerequisites_satisfied", False
                        ),
                    }
                )

        return pending
