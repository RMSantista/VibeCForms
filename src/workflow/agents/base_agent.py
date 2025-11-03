"""
BaseAgent - Abstract base class for all AI agents

Responsibilities:
- Define interface for all workflow AI agents
- Provide common utilities for context analysis
- Standardize suggestion format
- Enable pluggable agent system

All concrete agents must implement:
- analyze_context(): Analyze process and return insights
- suggest_transition(): Suggest next state with confidence score
- validate_transition(): Validate if proposed transition is safe
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class BaseAgent(ABC):
    """
    Abstract base class for workflow AI agents

    Agents analyze process context and provide intelligent
    suggestions for transitions.
    """

    def __init__(self, workflow_repo, kanban_registry):
        """
        Initialize BaseAgent

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
        """
        self.repo = workflow_repo
        self.registry = kanban_registry

    # ========== Abstract Methods (must implement) ==========

    @abstractmethod
    def analyze_context(self, process_id: str) -> Dict:
        """
        Analyze context for a process

        Args:
            process_id: Process ID to analyze

        Returns:
            Dict with context analysis (structure varies by agent):
            {
                'data_completeness': 0.85,
                'field_quality': {...},
                'historical_patterns': {...},
                ...
            }
        """
        pass

    @abstractmethod
    def suggest_transition(self, process_id: str) -> Dict:
        """
        Suggest next transition for a process

        Args:
            process_id: Process ID

        Returns:
            Dict with suggestion:
            {
                'suggested_state': 'next_state' or None,
                'confidence': 0.92 (0.0 to 1.0),
                'justification': 'Why this suggestion...',
                'risk_factors': ['risk1', ...],
                'estimated_duration': 24.5 (hours, optional)
            }
        """
        pass

    @abstractmethod
    def validate_transition(self, process_id: str, target_state: str) -> Dict:
        """
        Validate if proposed transition is safe

        Args:
            process_id: Process ID
            target_state: Target state ID

        Returns:
            Dict with validation result:
            {
                'valid': True/False,
                'warnings': ['warning1', ...],
                'errors': ['error1', ...],
                'risk_level': 'low'/'medium'/'high'
            }
        """
        pass

    # ========== Common Utility Methods ==========

    def get_process(self, process_id: str) -> Optional[Dict]:
        """Get process by ID"""
        return self.repo.get_process_by_id(process_id)

    def get_kanban(self, kanban_id: str) -> Optional[Dict]:
        """Get kanban definition"""
        return self.registry.get_kanban(kanban_id)

    def get_available_transitions(self, kanban_id: str, from_state: str) -> List[Dict]:
        """Get available transitions from current state"""
        return self.registry.get_available_transitions(kanban_id, from_state)

    def check_field_completeness(
        self, process: Dict, required_fields: List[str]
    ) -> float:
        """
        Check what % of required fields are filled

        Args:
            process: Process dict
            required_fields: List of field names

        Returns:
            Completeness score (0.0 to 1.0)
        """
        if not required_fields:
            return 1.0

        field_values = process.get("field_values", {})
        filled = 0

        for field in required_fields:
            value = field_values.get(field)
            if value is not None and value != "":
                filled += 1

        return filled / len(required_fields)

    def get_transition_history_count(self, process: Dict) -> int:
        """Get number of transitions made"""
        history = process.get("history", [])
        return len(history)

    def get_current_state_duration(self, process: Dict) -> float:
        """
        Get hours spent in current state

        Returns:
            Hours in current state
        """
        from datetime import datetime, timezone

        history = process.get("history", [])

        if history:
            last_transition = history[-1]
            timestamp_str = last_transition.get("timestamp")
        else:
            timestamp_str = process.get("created_at")

        if not timestamp_str:
            return 0.0

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            duration_hours = (now - timestamp).total_seconds() / 3600
            return duration_hours

        except (ValueError, TypeError):
            return 0.0

    def format_suggestion(
        self,
        suggested_state: Optional[str],
        confidence: float,
        justification: str,
        risk_factors: List[str] = None,
        estimated_duration: Optional[float] = None,
    ) -> Dict:
        """
        Format suggestion in standard format

        Args:
            suggested_state: Suggested next state (or None)
            confidence: Confidence score (0.0 to 1.0)
            justification: Text explanation
            risk_factors: List of risk descriptions
            estimated_duration: Estimated hours (optional)

        Returns:
            Formatted suggestion dict
        """
        suggestion = {
            "suggested_state": suggested_state,
            "confidence": round(min(1.0, max(0.0, confidence)), 3),
            "justification": justification,
            "risk_factors": risk_factors or [],
        }

        if estimated_duration is not None:
            suggestion["estimated_duration"] = round(estimated_duration, 2)

        return suggestion

    def format_validation(
        self,
        valid: bool,
        warnings: List[str] = None,
        errors: List[str] = None,
        risk_level: str = "low",
    ) -> Dict:
        """
        Format validation result in standard format

        Args:
            valid: Whether transition is valid
            warnings: List of warnings
            errors: List of errors
            risk_level: 'low', 'medium', or 'high'

        Returns:
            Formatted validation dict
        """
        return {
            "valid": valid,
            "warnings": warnings or [],
            "errors": errors or [],
            "risk_level": risk_level,
        }
