"""
GenericAgent - General-purpose AI agent using heuristics

Uses simple heuristics to suggest transitions:
- Field completeness
- Time in current state
- Available transitions
- Basic pattern matching
"""

from typing import Dict
from .base_agent import BaseAgent


class GenericAgent(BaseAgent):
    """
    General-purpose workflow agent

    Uses heuristics-based approach for transition suggestions.
    Works for any kanban/state without specific training.
    """

    def analyze_context(self, process_id: str) -> Dict:
        """
        Analyze process context using general heuristics

        Returns:
            {
                'field_completeness': 0.85,
                'time_in_current_state': 24.5,
                'transition_count': 3,
                'available_transitions': ['state1', 'state2'],
                'state_info': {...}
            }
        """
        process = self.get_process(process_id)

        if not process:
            return {
                "error": "Process not found",
                "field_completeness": 0.0,
                "time_in_current_state": 0.0,
                "transition_count": 0,
                "available_transitions": [],
            }

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")
        field_values = process.get("field_values", {})

        # Get kanban and state info
        kanban = self.get_kanban(kanban_id)
        available_trans = (
            self.get_available_transitions(kanban_id, current_state) if kanban else []
        )

        # Calculate field completeness (all non-empty fields)
        total_fields = len(field_values)
        filled_fields = sum(
            1 for v in field_values.values() if v is not None and v != ""
        )
        field_completeness = filled_fields / total_fields if total_fields > 0 else 0.0

        # Get time in current state
        time_in_state = self.get_current_state_duration(process)

        # Get transition count
        transition_count = self.get_transition_history_count(process)

        return {
            "field_completeness": round(field_completeness, 3),
            "time_in_current_state": round(time_in_state, 2),
            "transition_count": transition_count,
            "available_transitions": [t["to"] for t in available_trans],
            "state_info": {
                "kanban_id": kanban_id,
                "current_state": current_state,
                "total_fields": total_fields,
                "filled_fields": filled_fields,
            },
        }

    def suggest_transition(self, process_id: str) -> Dict:
        """
        Suggest next transition using heuristics

        Decision logic:
        1. If field completeness < 50%, suggest staying (fill data)
        2. If only one available transition, suggest it with high confidence
        3. If multiple transitions, prefer the one with auto_transition_to configured
        4. Consider time in state (urgency factor)

        Returns:
            Formatted suggestion dict
        """
        context = self.analyze_context(process_id)

        if "error" in context:
            return self.format_suggestion(None, 0.0, context["error"])

        field_completeness = context["field_completeness"]
        time_in_state = context["time_in_current_state"]
        available_transitions = context["available_transitions"]
        current_state = context["state_info"]["current_state"]

        # Rule 1: Low field completeness - suggest staying
        if field_completeness < 0.5:
            return self.format_suggestion(
                None,
                0.2,
                f"Field completeness is only {int(field_completeness*100)}%. Recommend filling more data before transitioning.",
                risk_factors=["Incomplete data may cause issues in next state"],
            )

        # Rule 2: No available transitions
        if not available_transitions:
            return self.format_suggestion(
                None,
                0.0,
                f"No transitions available from '{current_state}'",
                risk_factors=["Process may be in final state or misconfigured"],
            )

        # Rule 3: Single available transition
        if len(available_transitions) == 1:
            suggested_state = available_transitions[0]

            # Higher confidence if data is complete and some time has passed
            confidence = 0.6
            if field_completeness > 0.8:
                confidence += 0.2
            if time_in_state > 1.0:  # More than 1 hour
                confidence += 0.1

            return self.format_suggestion(
                suggested_state,
                confidence,
                f"Only one path available from '{current_state}' → '{suggested_state}'. Field completeness is {int(field_completeness*100)}%.",
                risk_factors=[],
            )

        # Rule 4: Multiple transitions - check for auto_transition_to
        process = self.get_process(process_id)
        kanban_id = process.get("kanban_id")
        kanban = self.get_kanban(kanban_id)

        if kanban:
            state_info = self.registry.get_state(kanban_id, current_state)
            auto_transition_to = (
                state_info.get("auto_transition_to") if state_info else None
            )

            if auto_transition_to and auto_transition_to in available_transitions:
                # Prefer auto_transition_to if configured
                confidence = 0.7
                if field_completeness > 0.9:
                    confidence = 0.85

                return self.format_suggestion(
                    auto_transition_to,
                    confidence,
                    f"State '{current_state}' is configured to auto-transition to '{auto_transition_to}'. Field completeness: {int(field_completeness*100)}%.",
                    risk_factors=[],
                )

        # Rule 5: Multiple transitions without auto_transition - suggest first with moderate confidence
        suggested_state = available_transitions[0]
        return self.format_suggestion(
            suggested_state,
            0.5,
            f"Multiple transitions available. Suggesting '{suggested_state}' based on definition order. Consider context before proceeding.",
            risk_factors=["Multiple paths available - manual review recommended"],
        )

    def validate_transition(self, process_id: str, target_state: str) -> Dict:
        """
        Validate proposed transition

        Checks:
        1. Transition exists in kanban definition
        2. Field completeness for target state
        3. No obvious risks

        Returns:
            Formatted validation dict
        """
        process = self.get_process(process_id)

        if not process:
            return self.format_validation(False, errors=["Process not found"])

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")

        # NEW PHILOSOPHY: Check if transition is explicitly blocked
        if not self.registry.can_transition(kanban_id, current_state, target_state):
            blocked_transition = self.registry.get_blocked_transition(
                kanban_id, current_state, target_state
            )
            reason = (
                blocked_transition.get("reason", "This transition is blocked")
                if blocked_transition
                else "This transition is blocked"
            )
            return self.format_validation(
                False,
                errors=[reason],
            )

        # Check field completeness
        context = self.analyze_context(process_id)
        field_completeness = context.get("field_completeness", 0.0)

        warnings = []
        risk_level = "low"

        if field_completeness < 0.5:
            warnings.append(
                f"Field completeness is only {int(field_completeness*100)}%"
            )
            risk_level = "high"
        elif field_completeness < 0.8:
            warnings.append(
                f"Field completeness is {int(field_completeness*100)}% - consider filling more data"
            )
            risk_level = "medium"

        # Check time in state (warn if very quick transition)
        time_in_state = context.get("time_in_current_state", 0.0)
        if time_in_state < 0.1:  # Less than 6 minutes
            warnings.append("Very quick transition - ensure this is intentional")

        return self.format_validation(
            True,  # Always valid if transition exists (Warn, Not Block)
            warnings=warnings,
            errors=[],
            risk_level=risk_level,
        )
