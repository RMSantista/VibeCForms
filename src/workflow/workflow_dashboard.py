"""
WorkflowDashboard - Analytics and monitoring dashboard for workflows

Provides high-level metrics and insights including:
- Kanban health scores
- Process statistics
- Throughput metrics
- Bottleneck identification
- Agent performance tracking
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class WorkflowDashboard:
    """
    Comprehensive dashboard for workflow monitoring and analytics

    Aggregates data from multiple sources to provide
    actionable insights about workflow health and performance.
    """

    def __init__(
        self,
        workflow_repo,
        kanban_registry,
        pattern_analyzer,
        anomaly_detector,
        agent_orchestrator,
    ):
        """
        Initialize WorkflowDashboard

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
            pattern_analyzer: PatternAnalyzer instance
            anomaly_detector: AnomalyDetector instance
            agent_orchestrator: AgentOrchestrator instance
        """
        self.repo = workflow_repo
        self.registry = kanban_registry
        self.pattern_analyzer = pattern_analyzer
        self.anomaly_detector = anomaly_detector
        self.orchestrator = agent_orchestrator

    # ========== Kanban Health Metrics ==========

    def get_kanban_health(self, kanban_id: str) -> Dict:
        """
        Calculate comprehensive health metrics for a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            {
                'kanban_id': 'kanban_pedidos',
                'health_score': 0.85,  # 0.0-1.0
                'status': 'healthy' | 'warning' | 'critical',
                'metrics': {
                    'total_processes': 100,
                    'active_processes': 45,
                    'completed_processes': 50,
                    'stuck_processes': 5,
                    'avg_completion_time_hours': 72.5,
                    'throughput_per_day': 2.3
                },
                'issues': [
                    {'type': 'stuck', 'count': 5, 'severity': 'high'},
                    {'type': 'loops', 'count': 2, 'severity': 'medium'}
                ],
                'recommendations': [...]
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        # Calculate basic metrics
        total_count = len(processes)
        active = [
            p
            for p in processes
            if p.get("current_state")
            and self._get_state_type(kanban_id, p["current_state"]) != "final"
        ]
        completed = [
            p
            for p in processes
            if p.get("current_state")
            and self._get_state_type(kanban_id, p["current_state"]) == "final"
        ]

        # Get anomaly report
        anomaly_report = self.anomaly_detector.generate_anomaly_report(kanban_id)

        # Calculate completion times
        completion_times = []
        for proc in completed:
            created_at = proc.get("created_at")
            history = proc.get("history", [])

            if created_at and history:
                # Find last transition timestamp
                last_trans = history[-1].get("timestamp") if history else None
                if last_trans:
                    try:
                        start = datetime.fromisoformat(created_at)
                        end = datetime.fromisoformat(last_trans)
                        hours = (end - start).total_seconds() / 3600
                        completion_times.append(hours)
                    except:
                        pass

        avg_completion = (
            sum(completion_times) / len(completion_times) if completion_times else 0
        )

        # Calculate throughput (completed per day)
        # Use last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_completed = [
            p
            for p in completed
            if p.get("created_at")
            and datetime.fromisoformat(p["created_at"]) > thirty_days_ago
        ]
        throughput = len(recent_completed) / 30.0

        # Build issues list
        issues = []
        if anomaly_report["summary"]["stuck_count"] > 0:
            severity = (
                "high" if anomaly_report["summary"]["stuck_count"] > 5 else "medium"
            )
            issues.append(
                {
                    "type": "stuck_processes",
                    "count": anomaly_report["summary"]["stuck_count"],
                    "severity": severity,
                }
            )

        if anomaly_report["summary"]["loops_count"] > 0:
            issues.append(
                {
                    "type": "loops",
                    "count": anomaly_report["summary"]["loops_count"],
                    "severity": "medium",
                }
            )

        if anomaly_report["summary"]["duration_anomalies_count"] > 0:
            issues.append(
                {
                    "type": "duration_anomalies",
                    "count": anomaly_report["summary"]["duration_anomalies_count"],
                    "severity": "low",
                }
            )

        # Calculate health score (0.0-1.0)
        health_score = self._calculate_health_score(
            total_count, len(active), anomaly_report["summary"]
        )

        # Determine status
        if health_score >= 0.8:
            status = "healthy"
        elif health_score >= 0.6:
            status = "warning"
        else:
            status = "critical"

        # Generate recommendations
        recommendations = self._generate_recommendations(anomaly_report, issues)

        return {
            "kanban_id": kanban_id,
            "health_score": round(health_score, 3),
            "status": status,
            "metrics": {
                "total_processes": total_count,
                "active_processes": len(active),
                "completed_processes": len(completed),
                "stuck_processes": anomaly_report["summary"]["stuck_count"],
                "avg_completion_time_hours": round(avg_completion, 1),
                "throughput_per_day": round(throughput, 2),
            },
            "issues": issues,
            "recommendations": recommendations,
        }

    def _get_state_type(self, kanban_id: str, state_id: str) -> Optional[str]:
        """Get state type from kanban definition"""
        state = self.registry.get_state(kanban_id, state_id)
        return state.get("type") if state else None

    def _calculate_health_score(
        self, total: int, active: int, anomaly_summary: Dict
    ) -> float:
        """Calculate overall health score"""
        if total == 0:
            return 1.0

        # Start with perfect score
        score = 1.0

        # Penalize for stuck processes (heavy penalty)
        stuck_ratio = anomaly_summary["stuck_count"] / total
        score -= stuck_ratio * 0.5

        # Penalize for loops (medium penalty)
        loops_ratio = anomaly_summary["loops_count"] / total
        score -= loops_ratio * 0.3

        # Penalize for duration anomalies (light penalty)
        anomalies_ratio = anomaly_summary["duration_anomalies_count"] / total
        score -= anomalies_ratio * 0.2

        return max(0.0, min(1.0, score))

    def _generate_recommendations(
        self, anomaly_report: Dict, issues: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Recommendations for stuck processes
        if anomaly_report["summary"]["stuck_count"] > 0:
            recommendations.append(
                f"Review {anomaly_report['summary']['stuck_count']} stuck process(es) "
                "and consider manual intervention or process redesign"
            )

        # Recommendations for loops
        if anomaly_report["summary"]["loops_count"] > 0:
            recommendations.append(
                "Investigate process loops - may indicate rework cycles or validation issues"
            )

        # Recommendations for unusual transitions
        if anomaly_report["summary"]["unusual_transitions_count"] > 5:
            recommendations.append(
                "High number of unusual transitions detected - review kanban workflow design"
            )

        # General recommendation
        if not recommendations:
            recommendations.append("Workflow operating normally - continue monitoring")

        return recommendations

    # ========== Process Statistics ==========

    def get_process_stats(self, kanban_id: str, days: int = 30) -> Dict:
        """
        Get detailed process statistics for a time period

        Args:
            kanban_id: Kanban ID
            days: Number of days to analyze

        Returns:
            {
                'period_days': 30,
                'created': 45,
                'completed': 38,
                'active': 7,
                'completion_rate': 0.84,
                'avg_cycle_time_hours': 72.5,
                'states_distribution': {
                    'novo': 5,
                    'em_analise': 15,
                    'aprovado': 38,
                    ...
                },
                'daily_throughput': {...}
            }
        """
        start_date = datetime.now() - timedelta(days=days)
        all_processes = self.repo.get_processes_by_kanban(kanban_id)

        # Filter to period
        period_processes = [
            p
            for p in all_processes
            if p.get("created_at")
            and datetime.fromisoformat(p["created_at"]) >= start_date
        ]

        # Count by status
        created_count = len(period_processes)
        completed = [
            p
            for p in period_processes
            if self._get_state_type(kanban_id, p.get("current_state", "")) == "final"
        ]
        completed_count = len(completed)
        active_count = created_count - completed_count

        # Completion rate
        completion_rate = completed_count / created_count if created_count > 0 else 0

        # Calculate cycle times
        cycle_times = []
        for proc in completed:
            created_at = proc.get("created_at")
            history = proc.get("history", [])

            if created_at and history:
                last_trans = history[-1].get("timestamp")
                if last_trans:
                    try:
                        start = datetime.fromisoformat(created_at)
                        end = datetime.fromisoformat(last_trans)
                        hours = (end - start).total_seconds() / 3600
                        cycle_times.append(hours)
                    except:
                        pass

        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0

        # State distribution
        states_dist = Counter(p.get("current_state") for p in period_processes)

        # Daily throughput
        daily_throughput = self._calculate_daily_throughput(completed, days)

        return {
            "period_days": days,
            "created": created_count,
            "completed": completed_count,
            "active": active_count,
            "completion_rate": round(completion_rate, 3),
            "avg_cycle_time_hours": round(avg_cycle_time, 1),
            "states_distribution": dict(states_dist),
            "daily_throughput": daily_throughput,
        }

    def _calculate_daily_throughput(
        self, completed_processes: List[Dict], days: int
    ) -> Dict:
        """Calculate completed processes per day"""
        # Group by completion date
        by_date = defaultdict(int)

        for proc in completed_processes:
            history = proc.get("history", [])
            if history:
                last_trans = history[-1].get("timestamp")
                if last_trans:
                    try:
                        date = datetime.fromisoformat(last_trans).date().isoformat()
                        by_date[date] += 1
                    except:
                        pass

        return dict(by_date)

    # ========== Bottleneck Analysis ==========

    def identify_bottlenecks(self, kanban_id: str) -> Dict:
        """
        Identify workflow bottlenecks

        Args:
            kanban_id: Kanban ID

        Returns:
            {
                'bottleneck_states': [
                    {
                        'state_id': 'em_analise',
                        'avg_duration_hours': 120.5,
                        'expected_duration_hours': 24.0,
                        'slowdown_factor': 5.0,
                        'process_count': 15
                    },
                    ...
                ],
                'slow_transitions': [...],
                'recommendations': [...]
            }
        """
        # Analyze state durations
        durations = self.pattern_analyzer.analyze_state_durations(kanban_id)

        # Identify unusually long states
        bottleneck_states = []

        for state_id, stats in durations.items():
            # Consider a bottleneck if avg > 2x min
            if stats["sample_count"] >= 3:
                slowdown = (
                    stats["avg_hours"] / stats["min_hours"]
                    if stats["min_hours"] > 0
                    else 1.0
                )

                if slowdown >= 2.0:
                    bottleneck_states.append(
                        {
                            "state_id": state_id,
                            "avg_duration_hours": round(stats["avg_hours"], 1),
                            "min_duration_hours": round(stats["min_hours"], 1),
                            "slowdown_factor": round(slowdown, 1),
                            "process_count": stats["sample_count"],
                        }
                    )

        # Sort by slowdown factor
        bottleneck_states.sort(key=lambda x: x["slowdown_factor"], reverse=True)

        # Generate recommendations
        recommendations = []
        if bottleneck_states:
            top_bottleneck = bottleneck_states[0]
            recommendations.append(
                f"State '{top_bottleneck['state_id']}' is {top_bottleneck['slowdown_factor']}x slower "
                f"than optimal - investigate delays"
            )

        return {
            "bottleneck_states": bottleneck_states,
            "recommendations": recommendations,
        }

    # ========== Agent Performance ==========

    def get_agent_performance(self, kanban_id: str, sample_size: int = 20) -> Dict:
        """
        Analyze AI agent suggestion performance

        Args:
            kanban_id: Kanban ID
            sample_size: Number of recent processes to analyze

        Returns:
            {
                'agents': {
                    'generic': {
                        'avg_confidence': 0.75,
                        'suggestion_count': 18,
                        'high_confidence_count': 12  # >= 0.8
                    },
                    'pattern': {...},
                    'rule': {...}
                },
                'consensus': {
                    'high_agreement_rate': 0.85,  # % with high consensus
                    'avg_agreement_level': 'high'
                }
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        # Take random sample (or last N)
        sample = processes[-sample_size:] if len(processes) > sample_size else processes

        agent_stats = {
            "generic": {"confidences": [], "high_conf_count": 0},
            "pattern": {"confidences": [], "high_conf_count": 0},
            "rule": {"confidences": [], "high_conf_count": 0},
        }

        consensus_stats = {
            "high_agreement": 0,
            "medium_agreement": 0,
            "low_agreement": 0,
        }

        # Analyze each process
        for proc in sample:
            try:
                analysis = self.orchestrator.analyze_with_all_agents(proc["process_id"])

                # Collect agent confidences
                for agent_name in ["generic", "pattern", "rule"]:
                    agent_result = analysis["agents"].get(agent_name, {})
                    suggestion = agent_result.get("suggestion", {})
                    confidence = suggestion.get("confidence", 0.0)

                    if confidence > 0:
                        agent_stats[agent_name]["confidences"].append(confidence)
                        if confidence >= 0.8:
                            agent_stats[agent_name]["high_conf_count"] += 1

                # Track consensus
                agreement = analysis["consensus"].get("agreement_level", "none")
                if agreement == "high":
                    consensus_stats["high_agreement"] += 1
                elif agreement == "medium":
                    consensus_stats["medium_agreement"] += 1
                else:
                    consensus_stats["low_agreement"] += 1

            except Exception:
                # Skip processes that can't be analyzed
                continue

        # Calculate averages
        agent_performance = {}
        for agent_name, stats in agent_stats.items():
            confidences = stats["confidences"]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            agent_performance[agent_name] = {
                "avg_confidence": round(avg_conf, 3),
                "suggestion_count": len(confidences),
                "high_confidence_count": stats["high_conf_count"],
            }

        # Consensus metrics
        total_analyzed = sum(consensus_stats.values())
        high_agreement_rate = (
            consensus_stats["high_agreement"] / total_analyzed
            if total_analyzed > 0
            else 0
        )

        return {
            "sample_size": len(sample),
            "agents": agent_performance,
            "consensus": {
                "high_agreement_count": consensus_stats["high_agreement"],
                "high_agreement_rate": round(high_agreement_rate, 3),
            },
        }

    # ========== Summary Dashboard ==========

    def get_dashboard_summary(self, kanban_id: str) -> Dict:
        """
        Get comprehensive dashboard summary

        Args:
            kanban_id: Kanban ID

        Returns:
            Complete dashboard data including all metrics
        """
        health = self.get_kanban_health(kanban_id)
        stats = self.get_process_stats(kanban_id, days=30)
        bottlenecks = self.identify_bottlenecks(kanban_id)

        return {
            "kanban_id": kanban_id,
            "generated_at": datetime.now().isoformat(),
            "health": health,
            "statistics": stats,
            "bottlenecks": bottlenecks,
        }
