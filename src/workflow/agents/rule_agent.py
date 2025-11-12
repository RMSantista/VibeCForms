"""
RuleAgent - AI agent using business rules for suggestions

Applies configurable business rules to suggest transitions.
Rules can be defined in kanban configuration or externally.
"""

from typing import Dict, List
from .base_agent import BaseAgent


class RuleAgent(BaseAgent):
    """
    Rule-based workflow agent

    Evaluates business rules and suggests transitions
    based on rule outcomes.
    """

    def __init__(self, workflow_repo, kanban_registry, prerequisite_checker):
        """
        Initialize RuleAgent

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
            prerequisite_checker: PrerequisiteChecker instance for rule evaluation
        """
        super().__init__(workflow_repo, kanban_registry)
        self.prerequisite_checker = prerequisite_checker

    def analyze_context(self, process_id: str) -> Dict:
        """
        Analyze context using business rules

        Returns:
            {
                'available_transitions': [...],
                'transition_readiness': {
                    'state1': {
                        'ready': True,
                        'prerequisites_met': True,
                        'unsatisfied_prerequisites': []
                    },
                    ...
                },
                'auto_transition_available': True/False
            }
        """
        process = self.get_process(process_id)

        if not process:
            return {"error": "Process not found"}

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")
        kanban = self.get_kanban(kanban_id)

        if not kanban:
            return {"error": "Kanban not found"}

        # Get available transitions
        available_trans = self.get_available_transitions(kanban_id, current_state)

        # Evaluate prerequisites for each transition
        transition_readiness = {}

        for trans in available_trans:
            to_state = trans["to"]
            transition = self.registry.get_transition(
                kanban_id, current_state, to_state
            )

            if transition:
                prerequisites = transition.get("prerequisites", [])
                prereq_results = self.prerequisite_checker.check_prerequisites(
                    prerequisites, process, kanban
                )

                all_satisfied = self.prerequisite_checker.are_all_satisfied(
                    prereq_results
                )
                unsatisfied = self.prerequisite_checker.get_unsatisfied(prereq_results)

                transition_readiness[to_state] = {
                    "ready": all_satisfied,
                    "prerequisites_met": all_satisfied,
                    "unsatisfied_prerequisites": [
                        {"type": r["type"], "message": r["message"]}
                        for r in unsatisfied
                    ],
                }

        # Check if auto_transition is configured
        state_info = self.registry.get_state(kanban_id, current_state)
        auto_transition_to = (
            state_info.get("auto_transition_to") if state_info else None
        )

        return {
            "available_transitions": [t["to"] for t in available_trans],
            "transition_readiness": transition_readiness,
            "auto_transition_available": auto_transition_to is not None,
            "auto_transition_to": auto_transition_to,
        }

    def suggest_transition(self, process_id: str) -> Dict:
        """
        Suggest transition based on rule evaluation

        Logic:
        1. Check for auto_transition_to with all prerequisites met
        2. Find transition with all prerequisites satisfied
        3. Return transition with highest prerequisite satisfaction

        Returns:
            Formatted suggestion dict
        """
        context = self.analyze_context(process_id)

        if "error" in context:
            return self.format_suggestion(None, 0.0, context["error"])

        transition_readiness = context["transition_readiness"]
        auto_transition_to = context.get("auto_transition_to")

        # No available transitions
        if not transition_readiness:
            return self.format_suggestion(
                None,
                0.0,
                "No transitions available from current state",
                risk_factors=["Process may be stuck"],
            )

        # Rule 1: Auto-transition configured and ready
        if auto_transition_to and auto_transition_to in transition_readiness:
            readiness = transition_readiness[auto_transition_to]

            if readiness["ready"]:
                return self.format_suggestion(
                    auto_transition_to,
                    0.9,
                    f"Auto-transition to '{auto_transition_to}' configured and all prerequisites satisfied.",
                    risk_factors=[],
                )
            else:
                # Auto-transition configured but not ready
                unsatisfied = readiness["unsatisfied_prerequisites"]
                return self.format_suggestion(
                    None,
                    0.4,
                    f"Auto-transition to '{auto_transition_to}' configured but {len(unsatisfied)} prerequisite(s) not satisfied.",
                    risk_factors=[p["message"] for p in unsatisfied],
                )

        # Rule 2: Find any transition with all prerequisites met
        ready_transitions = [
            state
            for state, readiness in transition_readiness.items()
            if readiness["ready"]
        ]

        if ready_transitions:
            suggested_state = ready_transitions[0]
            return self.format_suggestion(
                suggested_state,
                0.8,
                f"All prerequisites satisfied for transition to '{suggested_state}'.",
                risk_factors=[],
            )

        # Rule 3: Find transition with most prerequisites satisfied
        best_state = None
        best_score = -1

        for state, readiness in transition_readiness.items():
            unsatisfied_count = len(readiness["unsatisfied_prerequisites"])
            # Lower is better (fewer unsatisfied)
            score = -unsatisfied_count

            if score > best_score:
                best_score = score
                best_state = state

        if best_state:
            readiness = transition_readiness[best_state]
            unsatisfied = readiness["unsatisfied_prerequisites"]

            return self.format_suggestion(
                best_state,
                0.5,
                f"Transition to '{best_state}' has {len(unsatisfied)} unsatisfied prerequisite(s). Consider forced transition with justification.",
                risk_factors=[p["message"] for p in unsatisfied],
            )

        # Fallback
        return self.format_suggestion(
            None,
            0.3,
            "No clear transition path. Manual review recommended.",
            risk_factors=["Multiple prerequisites not satisfied"],
        )

    def validate_transition(self, process_id: str, target_state: str) -> Dict:
        """
        Validate transition using prerequisite rules

        Returns:
            Formatted validation dict
        """
        context = self.analyze_context(process_id)

        if "error" in context:
            return self.format_validation(False, errors=[context["error"]])

        transition_readiness = context.get("transition_readiness", {})

        # Check if target state is available
        if target_state not in transition_readiness:
            return self.format_validation(
                False,
                errors=[f"Transition to '{target_state}' is not defined in kanban"],
            )

        readiness = transition_readiness[target_state]
        unsatisfied = readiness["unsatisfied_prerequisites"]

        warnings = []
        risk_level = "low"

        if not readiness["ready"]:
            # Prerequisites not satisfied
            warnings = [p["message"] for p in unsatisfied]
            risk_level = "high" if len(unsatisfied) > 2 else "medium"

        return self.format_validation(
            True,  # Always valid (Warn, Not Block)
            warnings=warnings,
            errors=[],
            risk_level=risk_level,
        )
