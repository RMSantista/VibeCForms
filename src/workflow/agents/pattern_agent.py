"""
PatternAgent - AI agent using historical patterns for suggestions

Uses PatternAnalyzer to identify common paths and suggest
transitions based on what similar processes have done.
"""

from typing import Dict
from .base_agent import BaseAgent


class PatternAgent(BaseAgent):
    """
    Pattern-based workflow agent

    Suggests transitions based on historical patterns
    identified by PatternAnalyzer.
    """

    def __init__(self, workflow_repo, kanban_registry, pattern_analyzer):
        """
        Initialize PatternAgent

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
            pattern_analyzer: PatternAnalyzer instance
        """
        super().__init__(workflow_repo, kanban_registry)
        self.pattern_analyzer = pattern_analyzer

    def analyze_context(self, process_id: str) -> Dict:
        """
        Analyze context using pattern analysis

        Returns:
            {
                'current_sequence': ['state1', 'state2'],
                'matching_patterns': [...],'
                'similar_processes': [...],
                'common_next_states': {'state3': 0.85, ...}
            }
        """
        process = self.get_process(process_id)

        if not process:
            return {"error": "Process not found"}

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")

        # Get current sequence
        current_sequence = self._extract_sequence(process)

        # Get patterns for this kanban
        patterns = self.pattern_analyzer.analyze_transition_patterns(
            kanban_id, min_support=0.2
        )

        # Find patterns matching current sequence
        matching_patterns = self._find_matching_patterns(current_sequence, patterns)

        # Find similar processes
        similar = self.pattern_analyzer.find_similar_processes(
            process_id, kanban_id, limit=3
        )

        # Calculate common next states from patterns
        common_next_states = self._calculate_next_states_from_patterns(
            current_sequence, patterns
        )

        return {
            "current_sequence": current_sequence,
            "matching_patterns": matching_patterns,
            "similar_processes": similar,
            "common_next_states": common_next_states,
        }

    def suggest_transition(self, process_id: str) -> Dict:
        """
        Suggest transition based on patterns

        Logic:
        1. Find patterns matching current sequence
        2. Identify most common next state
        3. Use pattern confidence and support for suggestion confidence

        Returns:
            Formatted suggestion dict
        """
        context = self.analyze_context(process_id)

        if "error" in context:
            return self.format_suggestion(None, 0.0, context["error"])

        common_next_states = context["common_next_states"]
        matching_patterns = context["matching_patterns"]

        # No patterns found
        if not common_next_states:
            return self.format_suggestion(
                None,
                0.3,
                "No historical patterns found for current sequence. Consider manual transition.",
                risk_factors=["No historical data to guide decision"],
            )

        # Get most common next state
        best_state = max(common_next_states, key=common_next_states.get)
        confidence = common_next_states[best_state]

        # Build justification
        pattern_count = len(matching_patterns)
        support = matching_patterns[0]["support"] if matching_patterns else 0.0

        justification = (
            f"Historical patterns suggest '{best_state}' as next state. "
            f"Found {pattern_count} matching pattern(s) with {int(support*100)}% support."
        )

        return self.format_suggestion(
            best_state, confidence, justification, risk_factors=[]
        )

    def validate_transition(self, process_id: str, target_state: str) -> Dict:
        """
        Validate transition against patterns

        Returns:
            Formatted validation dict
        """
        context = self.analyze_context(process_id)

        if "error" in context:
            return self.format_validation(False, errors=[context["error"]])

        common_next_states = context["common_next_states"]

        warnings = []
        risk_level = "low"

        # Check if target is in common next states
        if target_state not in common_next_states:
            warnings.append(
                f"Target state '{target_state}' is not a common next state based on historical patterns"
            )
            risk_level = "medium"
        elif common_next_states[target_state] < 0.3:
            warnings.append(
                f"Target state '{target_state}' occurs in only {int(common_next_states[target_state]*100)}% of similar cases"
            )
            risk_level = "medium"

        return self.format_validation(
            True,  # Always valid (Warn, Not Block)
            warnings=warnings,
            errors=[],
            risk_level=risk_level,
        )

    # ========== Helper Methods ==========

    def _extract_sequence(self, process: Dict) -> list:
        """Extract state sequence from process history"""
        sequence = []
        history = process.get("history", [])

        for transition in history:
            from_state = transition.get("from_state")
            to_state = transition.get("to_state")

            if not sequence and from_state:
                sequence.append(from_state)
            if to_state:
                sequence.append(to_state)

        # Add current state if not in sequence
        current_state = process.get("current_state")
        if current_state and (not sequence or sequence[-1] != current_state):
            sequence.append(current_state)

        return sequence

    def _find_matching_patterns(self, current_sequence: list, patterns: list) -> list:
        """Find patterns that match the current sequence"""
        matching = []

        for pattern_dict in patterns:
            pattern = pattern_dict["pattern"]

            # Check if current sequence ends with this pattern's beginning
            if len(current_sequence) >= len(pattern) - 1:
                # Check if pattern prefix matches sequence suffix
                match = True
                for i in range(len(pattern) - 1):
                    if current_sequence[-(len(pattern) - 1 - i)] != pattern[i]:
                        match = False
                        break

                if match:
                    matching.append(pattern_dict)

        return matching

    def _calculate_next_states_from_patterns(
        self, current_sequence: list, patterns: list
    ) -> Dict[str, float]:
        """Calculate probability of next states based on patterns"""
        next_states = {}

        for pattern_dict in patterns:
            pattern = pattern_dict["pattern"]
            confidence = pattern_dict.get("confidence", 0.5)

            # If pattern starts with current sequence, next state in pattern is relevant
            if len(current_sequence) < len(pattern):
                # Check if pattern starts with current sequence
                matches = True
                for i, state in enumerate(current_sequence):
                    if i >= len(pattern) or pattern[i] != state:
                        matches = False
                        break

                if matches:
                    # Next state in pattern
                    next_state_idx = len(current_sequence)
                    if next_state_idx < len(pattern):
                        next_state = pattern[next_state_idx]

                        # Accumulate confidence scores
                        if next_state in next_states:
                            next_states[next_state] = max(
                                next_states[next_state], confidence
                            )
                        else:
                            next_states[next_state] = confidence

        return next_states
