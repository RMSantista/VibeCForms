"""
AgentOrchestrator - Coordinates multiple AI agents for workflow analysis

Responsibilities:
- Manage collection of AI agents
- Route analysis requests to appropriate agents
- Aggregate results from multiple agents
- Provide consensus recommendations
- Select best suggestion from competing agents
"""

from typing import Dict, List, Optional
from .agents import GenericAgent, PatternAgent, RuleAgent


class AgentOrchestrator:
    """
    Orchestrator for workflow AI agents

    Coordinates multiple agents to provide comprehensive
    analysis and intelligent suggestions.
    """

    def __init__(
        self,
        workflow_repo,
        kanban_registry,
        pattern_analyzer,
        prerequisite_checker,
        feedback_loop=None,
    ):
        """
        Initialize AgentOrchestrator

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
            pattern_analyzer: PatternAnalyzer instance
            prerequisite_checker: PrerequisiteChecker instance
            feedback_loop: Optional AgentFeedbackLoop instance for learning
        """
        self.repo = workflow_repo
        self.registry = kanban_registry
        self.feedback_loop = feedback_loop

        # Initialize agents
        self.agents = {
            "generic": GenericAgent(workflow_repo, kanban_registry),
            "pattern": PatternAgent(workflow_repo, kanban_registry, pattern_analyzer),
            "rule": RuleAgent(workflow_repo, kanban_registry, prerequisite_checker),
        }

        # Default agent priority (can be configured)
        self.agent_priority = ["rule", "pattern", "generic"]

    # ========== Agent Selection ==========

    def get_agent(self, agent_name: str):
        """
        Get specific agent by name

        Args:
            agent_name: 'generic', 'pattern', or 'rule'

        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_name)

    def get_best_agent_for_process(self, process_id: str) -> str:
        """
        Determine best agent for analyzing a process

        Logic:
        - If process has long history, prefer PatternAgent
        - If prerequisites configured, prefer RuleAgent
        - Otherwise, use GenericAgent

        Args:
            process_id: Process ID

        Returns:
            Agent name: 'generic', 'pattern', or 'rule'
        """
        process = self.repo.get_process_by_id(process_id)

        if not process:
            return "generic"

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")
        history = process.get("history", [])

        # Check if prerequisites are configured for current state
        available_trans = self.registry.get_available_transitions(
            kanban_id, current_state
        )
        has_prerequisites = False

        for trans in available_trans:
            to_state = trans["to"]
            transition = self.registry.get_transition(
                kanban_id, current_state, to_state
            )

            if transition and transition.get("prerequisites"):
                has_prerequisites = True
                break

        # Decision logic
        if has_prerequisites:
            return "rule"  # Prefer RuleAgent when prerequisites exist
        elif len(history) >= 3:
            return "pattern"  # Prefer PatternAgent for processes with history
        else:
            return "generic"  # Default to GenericAgent

    # ========== Single Agent Analysis ==========

    def analyze_with_agent(self, process_id: str, agent_name: str = "auto") -> Dict:
        """
        Analyze process with specific agent

        Args:
            process_id: Process ID
            agent_name: 'generic', 'pattern', 'rule', or 'auto'

        Returns:
            {
                'agent_used': 'rule',
                'context': {...},
                'suggestion': {...}
            }
        """
        # Auto-select best agent
        if agent_name == "auto":
            agent_name = self.get_best_agent_for_process(process_id)

        agent = self.get_agent(agent_name)

        if not agent:
            return {
                "agent_used": None,
                "error": f"Agent '{agent_name}' not found",
                "context": {},
                "suggestion": {},
            }

        # Run analysis
        context = agent.analyze_context(process_id)
        suggestion = agent.suggest_transition(process_id)

        return {"agent_used": agent_name, "context": context, "suggestion": suggestion}

    # ========== Multi-Agent Analysis ==========

    def analyze_with_all_agents(self, process_id: str) -> Dict:
        """
        Analyze process with all agents and aggregate results

        Args:
            process_id: Process ID

        Returns:
            {
                'process_id': 'proc_123',
                'agents': {
                    'generic': {'context': {...}, 'suggestion': {...}},
                    'pattern': {'context': {...}, 'suggestion': {...}},
                    'rule': {'context': {...}, 'suggestion': {...}}
                },
                'consensus': {...},
                'best_suggestion': {...}
            }
        """
        results = {"process_id": process_id, "agents": {}}

        # Run analysis with each agent
        for agent_name in ["generic", "pattern", "rule"]:
            agent = self.get_agent(agent_name)

            if agent:
                try:
                    context = agent.analyze_context(process_id)
                    suggestion = agent.suggest_transition(process_id)

                    # Apply weighted confidence if feedback loop is available
                    if self.feedback_loop and "confidence" in suggestion:
                        base_confidence = suggestion["confidence"]
                        weighted_confidence = (
                            self.feedback_loop.get_weighted_confidence(
                                agent_name, base_confidence
                            )
                        )
                        suggestion["base_confidence"] = base_confidence
                        suggestion["confidence"] = weighted_confidence
                        suggestion["agent_weight"] = (
                            self.feedback_loop.get_agent_weight(agent_name)
                        )

                    # Record suggestion in feedback loop
                    if self.feedback_loop and suggestion.get("suggested_state"):
                        suggestion["feedback_id"] = (
                            self.feedback_loop.record_suggestion(
                                process_id=process_id,
                                agent_type=agent_name,
                                suggested_state=suggestion["suggested_state"],
                                confidence=suggestion.get("confidence", 0.0),
                                reasoning=suggestion.get("justification", ""),
                                metadata={"context": context},
                            )
                        )

                    results["agents"][agent_name] = {
                        "context": context,
                        "suggestion": suggestion,
                    }
                except Exception as e:
                    results["agents"][agent_name] = {"error": str(e)}

        # Calculate consensus
        consensus = self._calculate_consensus(results["agents"])
        results["consensus"] = consensus

        # Select best suggestion
        best_suggestion = self._select_best_suggestion(results["agents"], consensus)
        results["best_suggestion"] = best_suggestion

        return results

    def _calculate_consensus(self, agent_results: Dict) -> Dict:
        """
        Calculate consensus from multiple agent suggestions

        Args:
            agent_results: Dict mapping agent names to results

        Returns:
            {
                'suggested_states': {
                    'state1': {'count': 2, 'avg_confidence': 0.85},
                    ...
                },
                'consensus_state': 'state1' or None,
                'agreement_level': 'high'/'medium'/'low'
            }
        """
        # Collect all suggested states
        suggested_states = {}

        for agent_name, result in agent_results.items():
            if "error" in result:
                continue

            suggestion = result.get("suggestion", {})
            suggested_state = suggestion.get("suggested_state")
            confidence = suggestion.get("confidence", 0.0)

            if suggested_state:
                if suggested_state not in suggested_states:
                    suggested_states[suggested_state] = {"count": 0, "confidences": []}

                suggested_states[suggested_state]["count"] += 1
                suggested_states[suggested_state]["confidences"].append(confidence)

        # Calculate averages
        for state, data in suggested_states.items():
            confidences = data["confidences"]
            data["avg_confidence"] = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

        # Find consensus state (most votes)
        consensus_state = None
        max_count = 0

        for state, data in suggested_states.items():
            if data["count"] > max_count:
                max_count = data["count"]
                consensus_state = state

        # Determine agreement level
        total_agents = len([r for r in agent_results.values() if "error" not in r])
        agreement_level = "none"

        if consensus_state and total_agents > 0:
            agreement_ratio = max_count / total_agents

            if agreement_ratio >= 0.8:
                agreement_level = "high"
            elif agreement_ratio >= 0.5:
                agreement_level = "medium"
            else:
                agreement_level = "low"

        return {
            "suggested_states": {
                state: {
                    "count": data["count"],
                    "avg_confidence": round(data["avg_confidence"], 3),
                }
                for state, data in suggested_states.items()
            },
            "consensus_state": consensus_state,
            "agreement_level": agreement_level,
        }

    def _select_best_suggestion(self, agent_results: Dict, consensus: Dict) -> Dict:
        """
        Select best suggestion from all agents

        Priority:
        1. Consensus state with high agreement
        2. Highest confidence suggestion
        3. First agent in priority list

        Args:
            agent_results: Agent results dict
            consensus: Consensus dict

        Returns:
            Best suggestion dict with 'agent' field added
        """
        consensus_state = consensus.get("consensus_state")
        agreement_level = consensus.get("agreement_level")

        # If high consensus, return consensus suggestion
        if agreement_level == "high" and consensus_state:
            # Find agent that suggested consensus state with highest confidence
            best_agent = None
            best_confidence = 0.0

            for agent_name, result in agent_results.items():
                if "error" in result:
                    continue

                suggestion = result.get("suggestion", {})
                if suggestion.get("suggested_state") == consensus_state:
                    confidence = suggestion.get("confidence", 0.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_agent = agent_name

            if best_agent:
                suggestion = agent_results[best_agent]["suggestion"].copy()
                suggestion["agent"] = best_agent
                suggestion["selection_reason"] = "high_consensus"
                return suggestion

        # Otherwise, select highest confidence across all agents
        best_agent = None
        best_suggestion = None
        best_confidence = 0.0

        for agent_name in self.agent_priority:
            result = agent_results.get(agent_name, {})

            if "error" in result:
                continue

            suggestion = result.get("suggestion", {})
            confidence = suggestion.get("confidence", 0.0)

            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent_name
                best_suggestion = suggestion.copy()

        if best_suggestion:
            best_suggestion["agent"] = best_agent
            best_suggestion["selection_reason"] = "highest_confidence"
            return best_suggestion

        # No valid suggestion
        return {
            "agent": None,
            "suggested_state": None,
            "confidence": 0.0,
            "justification": "No agents provided valid suggestions",
            "selection_reason": "no_suggestions",
        }

    # ========== Validation ==========

    def validate_transition_with_all_agents(
        self, process_id: str, target_state: str
    ) -> Dict:
        """
        Validate transition with all agents

        Args:
            process_id: Process ID
            target_state: Target state

        Returns:
            {
                'process_id': 'proc_123',
                'target_state': 'state2',
                'validations': {
                    'generic': {...},
                    'pattern': {...},
                    'rule': {...}
                },
                'overall_valid': True/False,
                'max_risk_level': 'high'/'medium'/'low',
                'all_warnings': [...]
            }
        """
        validations = {}

        # Validate with each agent
        for agent_name in ["generic", "pattern", "rule"]:
            agent = self.get_agent(agent_name)

            if agent:
                try:
                    validation = agent.validate_transition(process_id, target_state)
                    validations[agent_name] = validation
                except Exception as e:
                    validations[agent_name] = {"error": str(e)}

        # Aggregate validations
        overall_valid = all(
            v.get("valid", False) for v in validations.values() if "error" not in v
        )

        # Find maximum risk level
        risk_levels = {"low": 1, "medium": 2, "high": 3}
        max_risk = "low"

        for validation in validations.values():
            if "error" in validation:
                continue

            risk_level = validation.get("risk_level", "low")
            if risk_levels.get(risk_level, 0) > risk_levels.get(max_risk, 0):
                max_risk = risk_level

        # Collect all warnings
        all_warnings = []
        for validation in validations.values():
            if "error" not in validation:
                all_warnings.extend(validation.get("warnings", []))

        # Remove duplicates
        all_warnings = list(set(all_warnings))

        return {
            "process_id": process_id,
            "target_state": target_state,
            "validations": validations,
            "overall_valid": overall_valid,
            "max_risk_level": max_risk,
            "all_warnings": all_warnings,
        }

    # ========== Feedback Loop Integration ==========

    def record_transition_feedback(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        agent_analysis: Dict,
        success: bool,
    ) -> bool:
        """
        Record feedback for a transition using agent analysis results

        Args:
            process_id: Process ID
            from_state: Previous state
            to_state: Actual state transitioned to
            agent_analysis: Results from analyze_with_all_agents()
            success: Whether transition succeeded

        Returns:
            True if feedback recorded
        """
        if not self.feedback_loop:
            return False

        # Extract suggestion IDs from agent analysis
        for agent_name, result in agent_analysis.get("agents", {}).items():
            if "error" in result:
                continue

            suggestion = result.get("suggestion", {})
            feedback_id = suggestion.get("feedback_id")

            if feedback_id:
                suggested_state = suggestion.get("suggested_state")
                was_accepted = suggested_state == to_state

                self.feedback_loop.record_outcome(
                    suggestion_id=feedback_id,
                    was_accepted=was_accepted,
                    actual_state=to_state,
                    success=success,
                    outcome_notes=f"Transition from {from_state} to {to_state}",
                )

        return True

    def get_agent_performance_stats(self, days: int = 30) -> Dict:
        """
        Get agent performance statistics from feedback loop

        Args:
            days: Number of days to analyze

        Returns:
            Performance statistics for all agents
        """
        if not self.feedback_loop:
            return {"error": "Feedback loop not configured"}

        return self.feedback_loop.get_all_agent_statistics(days)

    def get_learning_insights(
        self, kanban_id: Optional[str] = None, days: int = 30
    ) -> Dict:
        """
        Get learning insights from feedback loop

        Args:
            kanban_id: Optional kanban filter
            days: Number of days to analyze

        Returns:
            Learning insights and recommendations
        """
        if not self.feedback_loop:
            return {"error": "Feedback loop not configured"}

        return self.feedback_loop.get_learning_insights(kanban_id, days)
