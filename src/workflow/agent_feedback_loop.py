"""
AgentFeedbackLoop - Sistema de feedback para agentes AI

Responsabilidades:
- Rastrear sugestões de agentes e seus resultados
- Calcular métricas de acurácia por agente
- Ajustar pesos/confiança dos agentes baseado em performance histórica
- Armazenar feedback para análise
- Fornecer estatísticas para dashboard
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json


logger = logging.getLogger(__name__)


class AgentFeedbackLoop:
    """
    Feedback loop for AI agents to learn from outcomes

    Tracks suggestion outcomes (accepted, rejected, successful, failed)
    and adjusts agent weights based on historical performance.
    """

    def __init__(self, workflow_repo):
        """
        Initialize AgentFeedbackLoop

        Args:
            workflow_repo: WorkflowRepository instance for persistence
        """
        self.repo = workflow_repo
        self.feedback_history = []  # In-memory cache

        # Agent weights (start at 1.0, will be adjusted based on performance)
        self.agent_weights = {"generic": 1.0, "pattern": 1.0, "rule": 1.0}

        logger.info("AgentFeedbackLoop initialized")

    def record_suggestion(
        self,
        process_id: str,
        agent_type: str,
        suggested_state: str,
        confidence: float,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record an agent suggestion

        Args:
            process_id: Process ID
            agent_type: Type of agent (generic, pattern, rule)
            suggested_state: Suggested next state
            confidence: Agent's confidence in suggestion (0-1)
            reasoning: Agent's reasoning
            metadata: Additional metadata

        Returns:
            Suggestion ID (UUID)
        """
        from uuid import uuid4

        suggestion_id = str(uuid4())

        feedback_entry = {
            "suggestion_id": suggestion_id,
            "process_id": process_id,
            "agent_type": agent_type,
            "suggested_state": suggested_state,
            "confidence": confidence,
            "reasoning": reasoning,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat(),
            "outcome": None,  # To be updated later
            "actual_state": None,  # To be updated when transition occurs
            "was_accepted": None,  # To be updated
            "success": None,  # To be updated
        }

        self.feedback_history.append(feedback_entry)

        logger.debug(
            f"Recorded suggestion {suggestion_id} from {agent_type} for process {process_id}"
        )

        return suggestion_id

    def record_outcome(
        self,
        suggestion_id: str,
        was_accepted: bool,
        actual_state: str,
        success: bool,
        outcome_notes: Optional[str] = None,
    ) -> bool:
        """
        Record the outcome of a suggestion

        Args:
            suggestion_id: Suggestion ID to update
            was_accepted: Whether suggestion was accepted by user
            actual_state: State that was actually transitioned to
            success: Whether the transition was successful
            outcome_notes: Optional notes about outcome

        Returns:
            True if outcome recorded successfully
        """
        # Find suggestion in history
        for entry in self.feedback_history:
            if entry["suggestion_id"] == suggestion_id:
                entry["was_accepted"] = was_accepted
                entry["actual_state"] = actual_state
                entry["success"] = success
                entry["outcome_notes"] = outcome_notes
                entry["outcome_recorded_at"] = datetime.now().isoformat()

                # Determine outcome type
                if was_accepted and success:
                    entry["outcome"] = "accepted_successful"
                elif was_accepted and not success:
                    entry["outcome"] = "accepted_failed"
                elif not was_accepted and actual_state == entry["suggested_state"]:
                    entry["outcome"] = "rejected_but_matched"
                else:
                    entry["outcome"] = "rejected"

                logger.debug(
                    f"Recorded outcome for suggestion {suggestion_id}: {entry['outcome']}"
                )

                # Update agent weight based on outcome
                self._update_agent_weight(entry["agent_type"], entry["outcome"])

                return True

        logger.warning(f"Suggestion {suggestion_id} not found in feedback history")
        return False

    def record_transition_feedback(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        agent_suggestions: List[Dict[str, Any]],
        user_choice: str,
        success: bool,
    ) -> List[str]:
        """
        Record feedback for all agents involved in a transition decision

        Args:
            process_id: Process ID
            from_state: Previous state
            to_state: Target state
            agent_suggestions: List of suggestions from all agents
            user_choice: State chosen by user
            success: Whether transition succeeded

        Returns:
            List of suggestion IDs recorded
        """
        suggestion_ids = []

        for suggestion in agent_suggestions:
            suggestion_id = self.record_suggestion(
                process_id=process_id,
                agent_type=suggestion.get("agent_type", "unknown"),
                suggested_state=suggestion.get("next_state"),
                confidence=suggestion.get("confidence", 0.0),
                reasoning=suggestion.get("reasoning", ""),
                metadata={
                    "from_state": from_state,
                    "to_state": to_state,
                    "all_suggestions": [s.get("next_state") for s in agent_suggestions],
                },
            )

            # Record outcome immediately
            was_accepted = suggestion.get("next_state") == user_choice
            self.record_outcome(
                suggestion_id=suggestion_id,
                was_accepted=was_accepted,
                actual_state=to_state,
                success=success,
                outcome_notes=f"User chose {user_choice}",
            )

            suggestion_ids.append(suggestion_id)

        return suggestion_ids

    def _update_agent_weight(self, agent_type: str, outcome: str):
        """
        Update agent weight based on outcome

        Weights are adjusted to reflect agent accuracy:
        - accepted_successful: +0.05 (capped at 2.0)
        - accepted_failed: -0.10
        - rejected_but_matched: +0.02 (user rejected but was right)
        - rejected: -0.02

        Args:
            agent_type: Agent type
            outcome: Outcome type
        """
        if agent_type not in self.agent_weights:
            self.agent_weights[agent_type] = 1.0

        current_weight = self.agent_weights[agent_type]

        # Adjustment rules
        adjustments = {
            "accepted_successful": 0.05,
            "accepted_failed": -0.10,
            "rejected_but_matched": 0.02,
            "rejected": -0.02,
        }

        adjustment = adjustments.get(outcome, 0.0)
        new_weight = current_weight + adjustment

        # Clamp between 0.3 and 2.0
        new_weight = max(0.3, min(2.0, new_weight))

        self.agent_weights[agent_type] = new_weight

        logger.debug(
            f"Updated {agent_type} weight: {current_weight:.2f} -> {new_weight:.2f} (outcome: {outcome})"
        )

    def get_agent_statistics(
        self, agent_type: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get agent performance statistics

        Args:
            agent_type: Specific agent type (or None for all)
            days: Number of days to analyze

        Returns:
            Statistics dict with accuracy, acceptance rate, etc.
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter feedback by date and agent
        filtered = [
            entry
            for entry in self.feedback_history
            if (
                datetime.fromisoformat(entry["recorded_at"]) >= cutoff_date
                and entry["outcome"] is not None
                and (agent_type is None or entry["agent_type"] == agent_type)
            )
        ]

        if not filtered:
            return {
                "agent_type": agent_type or "all",
                "period_days": days,
                "total_suggestions": 0,
                "acceptance_rate": 0.0,
                "success_rate": 0.0,
                "accuracy": 0.0,
                "current_weight": (
                    self.agent_weights.get(agent_type, 1.0) if agent_type else None
                ),
            }

        total = len(filtered)
        accepted = sum(1 for e in filtered if e["was_accepted"])
        successful = sum(1 for e in filtered if e["success"])
        correct = sum(1 for e in filtered if e["suggested_state"] == e["actual_state"])

        stats = {
            "agent_type": agent_type or "all",
            "period_days": days,
            "total_suggestions": total,
            "acceptance_rate": accepted / total if total > 0 else 0.0,
            "success_rate": successful / total if total > 0 else 0.0,
            "accuracy": correct / total if total > 0 else 0.0,
            "current_weight": (
                self.agent_weights.get(agent_type, 1.0) if agent_type else None
            ),
            "outcome_breakdown": self._count_outcomes(filtered),
        }

        return stats

    def _count_outcomes(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of each outcome type"""
        counts = defaultdict(int)
        for entry in entries:
            outcome = entry.get("outcome", "unknown")
            counts[outcome] += 1
        return dict(counts)

    def get_all_agent_statistics(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all agents

        Args:
            days: Number of days to analyze

        Returns:
            Dict mapping agent_type to statistics
        """
        stats = {}

        for agent_type in ["generic", "pattern", "rule"]:
            stats[agent_type] = self.get_agent_statistics(agent_type, days)

        return stats

    def get_agent_weight(self, agent_type: str) -> float:
        """
        Get current weight for an agent

        Args:
            agent_type: Agent type

        Returns:
            Current weight (default 1.0)
        """
        return self.agent_weights.get(agent_type, 1.0)

    def get_weighted_confidence(self, agent_type: str, base_confidence: float) -> float:
        """
        Calculate weighted confidence based on agent performance

        Args:
            agent_type: Agent type
            base_confidence: Agent's base confidence (0-1)

        Returns:
            Weighted confidence (0-1)
        """
        weight = self.get_agent_weight(agent_type)
        weighted = base_confidence * weight

        # Clamp to [0, 1]
        return max(0.0, min(1.0, weighted))

    def get_best_agent_for_kanban(
        self, kanban_id: str, days: int = 30
    ) -> Tuple[str, float]:
        """
        Identify best-performing agent for a specific kanban

        Args:
            kanban_id: Kanban ID
            days: Number of days to analyze

        Returns:
            Tuple of (agent_type, accuracy_score)
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter by kanban and date
        kanban_feedback = []
        for entry in self.feedback_history:
            if entry["outcome"] is None:
                continue

            if datetime.fromisoformat(entry["recorded_at"]) < cutoff_date:
                continue

            # Get process to check kanban
            process = self.repo.get_process_by_id(entry["process_id"])
            if process and process.get("kanban_id") == kanban_id:
                kanban_feedback.append(entry)

        if not kanban_feedback:
            return "generic", 1.0

        # Calculate accuracy per agent
        agent_scores = defaultdict(lambda: {"correct": 0, "total": 0})

        for entry in kanban_feedback:
            agent_type = entry["agent_type"]
            agent_scores[agent_type]["total"] += 1

            if entry["suggested_state"] == entry["actual_state"]:
                agent_scores[agent_type]["correct"] += 1

        # Find best agent
        best_agent = "generic"
        best_accuracy = 0.0

        for agent_type, scores in agent_scores.items():
            if scores["total"] > 0:
                accuracy = scores["correct"] / scores["total"]
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_agent = agent_type

        logger.info(
            f"Best agent for {kanban_id}: {best_agent} (accuracy: {best_accuracy:.2%})"
        )

        return best_agent, best_accuracy

    def get_feedback_history(
        self,
        process_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get feedback history

        Args:
            process_id: Filter by process ID (optional)
            agent_type: Filter by agent type (optional)
            limit: Maximum number of entries

        Returns:
            List of feedback entries
        """
        filtered = self.feedback_history

        if process_id:
            filtered = [e for e in filtered if e["process_id"] == process_id]

        if agent_type:
            filtered = [e for e in filtered if e["agent_type"] == agent_type]

        # Return most recent first
        return sorted(filtered, key=lambda e: e["recorded_at"], reverse=True)[:limit]

    def export_feedback_data(self) -> List[Dict[str, Any]]:
        """
        Export all feedback data for analysis

        Returns:
            List of all feedback entries
        """
        return self.feedback_history.copy()

    def clear_old_feedback(self, days: int = 90):
        """
        Clear feedback older than specified days

        Args:
            days: Keep feedback from last N days
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        original_count = len(self.feedback_history)

        self.feedback_history = [
            entry
            for entry in self.feedback_history
            if datetime.fromisoformat(entry["recorded_at"]) >= cutoff_date
        ]

        removed = original_count - len(self.feedback_history)

        logger.info(f"Cleared {removed} old feedback entries (kept last {days} days)")

    def reset_agent_weights(self):
        """Reset all agent weights to 1.0"""
        for agent_type in self.agent_weights:
            self.agent_weights[agent_type] = 1.0

        logger.info("Reset all agent weights to 1.0")

    def get_learning_insights(
        self, kanban_id: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get insights about agent learning progress

        Args:
            kanban_id: Optional kanban filter
            days: Number of days to analyze

        Returns:
            Insights dict with trends and recommendations
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter feedback
        filtered = [
            entry
            for entry in self.feedback_history
            if (
                datetime.fromisoformat(entry["recorded_at"]) >= cutoff_date
                and entry["outcome"] is not None
            )
        ]

        # Filter by kanban if specified
        if kanban_id:
            kanban_filtered = []
            for entry in filtered:
                process = self.repo.get_process_by_id(entry["process_id"])
                if process and process.get("kanban_id") == kanban_id:
                    kanban_filtered.append(entry)
            filtered = kanban_filtered

        if not filtered:
            return {
                "kanban_id": kanban_id,
                "period_days": days,
                "insights": [],
                "recommendations": ["Insufficient data for learning insights"],
            }

        insights = []
        recommendations = []

        # Analyze agent performance trends
        for agent_type in ["generic", "pattern", "rule"]:
            agent_entries = [e for e in filtered if e["agent_type"] == agent_type]

            if not agent_entries:
                continue

            correct = sum(
                1 for e in agent_entries if e["suggested_state"] == e["actual_state"]
            )
            accuracy = correct / len(agent_entries)
            weight = self.agent_weights.get(agent_type, 1.0)

            insights.append(
                {
                    "agent_type": agent_type,
                    "accuracy": accuracy,
                    "weight": weight,
                    "total_suggestions": len(agent_entries),
                    "trend": (
                        "improving"
                        if weight > 1.0
                        else "declining" if weight < 1.0 else "stable"
                    ),
                }
            )

            # Generate recommendations
            if accuracy < 0.5 and len(agent_entries) > 10:
                recommendations.append(
                    f"{agent_type} agent has low accuracy ({accuracy:.1%}) - consider reviewing configuration"
                )
            elif weight > 1.5:
                recommendations.append(
                    f"{agent_type} agent is performing well ({accuracy:.1%}) - consider using it as default"
                )

        return {
            "kanban_id": kanban_id,
            "period_days": days,
            "total_feedback_entries": len(filtered),
            "insights": insights,
            "recommendations": recommendations,
            "best_agent": (
                max(insights, key=lambda x: x["accuracy"])["agent_type"]
                if insights
                else None
            ),
        }
