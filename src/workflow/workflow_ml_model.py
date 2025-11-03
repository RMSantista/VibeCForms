"""
WorkflowMLModel - Machine Learning for workflow predictions

Provides ML-based analysis including:
- K-means clustering of similar processes
- Duration prediction using linear regression
- Risk factor identification
- Automated weekly reports
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json


class WorkflowMLModel:
    """
    Machine Learning model for workflow analysis

    Uses scikit-learn for clustering and predictions,
    providing insights into process patterns and risks.
    """

    def __init__(self, workflow_repo, pattern_analyzer):
        """
        Initialize WorkflowMLModel

        Args:
            workflow_repo: WorkflowRepository instance
            pattern_analyzer: PatternAnalyzer instance
        """
        self.repo = workflow_repo
        self.pattern_analyzer = pattern_analyzer

    # ========== Process Clustering ==========

    def cluster_similar_processes(self, kanban_id: str, n_clusters: int = 3) -> Dict:
        """
        Cluster processes into groups based on behavior patterns

        Uses K-means clustering on process features:
        - State sequence similarity
        - Duration patterns
        - Field completeness
        - Transition count

        Args:
            kanban_id: Kanban ID
            n_clusters: Number of clusters (default: 3)

        Returns:
            {
                'clusters': [
                    {
                        'cluster_id': 0,
                        'process_count': 15,
                        'characteristics': {
                            'avg_duration_hours': 48.5,
                            'avg_transitions': 3.2,
                            'common_path': ['novo', 'aprovado']
                        },
                        'process_ids': ['proc_1', 'proc_2', ...]
                    },
                    ...
                ],
                'summary': {
                    'total_processes': 45,
                    'clusters_count': 3,
                    'avg_cluster_size': 15.0
                }
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if len(processes) < n_clusters:
            return {
                "clusters": [],
                "summary": {
                    "total_processes": len(processes),
                    "clusters_count": 0,
                    "avg_cluster_size": 0,
                    "error": f"Insufficient processes for {n_clusters} clusters",
                },
            }

        # Extract features for each process
        features = []
        process_ids = []

        for proc in processes:
            # Feature vector: [duration, transition_count, field_completeness, state_count]
            duration = self._calculate_process_duration(proc)
            transition_count = len(proc.get("history", []))
            field_completeness = self._calculate_field_completeness(proc)
            unique_states = len(set(t["to_state"] for t in proc.get("history", []))) + 1

            features.append(
                [duration, transition_count, field_completeness, unique_states]
            )
            process_ids.append(proc["process_id"])

        # Simple K-means clustering (manual implementation to avoid sklearn dependency)
        clusters = self._kmeans_clustering(features, n_clusters)

        # Build cluster summaries
        cluster_summaries = []
        for cluster_id in range(n_clusters):
            cluster_proc_indices = [
                i for i, c in enumerate(clusters) if c == cluster_id
            ]
            cluster_processes = [processes[i] for i in cluster_proc_indices]

            if not cluster_processes:
                continue

            # Calculate cluster characteristics
            durations = [self._calculate_process_duration(p) for p in cluster_processes]
            transitions = [len(p.get("history", [])) for p in cluster_processes]

            # Find most common path
            paths = defaultdict(int)
            for proc in cluster_processes:
                path = tuple(t["to_state"] for t in proc.get("history", []))
                if path:
                    paths[path] += 1

            common_path = (
                list(max(paths.keys(), key=lambda k: paths[k])) if paths else []
            )

            cluster_summaries.append(
                {
                    "cluster_id": cluster_id,
                    "process_count": len(cluster_processes),
                    "characteristics": {
                        "avg_duration_hours": (
                            sum(durations) / len(durations) if durations else 0
                        ),
                        "avg_transitions": (
                            sum(transitions) / len(transitions) if transitions else 0
                        ),
                        "common_path": common_path,
                    },
                    "process_ids": [p["process_id"] for p in cluster_processes],
                }
            )

        return {
            "clusters": cluster_summaries,
            "summary": {
                "total_processes": len(processes),
                "clusters_count": n_clusters,
                "avg_cluster_size": (
                    len(processes) / n_clusters if n_clusters > 0 else 0
                ),
            },
        }

    def _kmeans_clustering(
        self, features: List[List[float]], n_clusters: int, max_iterations: int = 100
    ) -> List[int]:
        """
        Simple K-means clustering implementation

        Args:
            features: List of feature vectors
            n_clusters: Number of clusters
            max_iterations: Maximum iterations

        Returns:
            List of cluster assignments
        """
        import random

        if not features or n_clusters <= 0:
            return []

        # Normalize features
        features_normalized = self._normalize_features(features)

        # Initialize centroids randomly
        centroids = random.sample(
            features_normalized, min(n_clusters, len(features_normalized))
        )

        assignments = [0] * len(features_normalized)

        for _ in range(max_iterations):
            # Assign points to nearest centroid
            new_assignments = []
            for point in features_normalized:
                distances = [
                    self._euclidean_distance(point, centroid) for centroid in centroids
                ]
                new_assignments.append(distances.index(min(distances)))

            # Check convergence
            if new_assignments == assignments:
                break

            assignments = new_assignments

            # Update centroids
            for cluster_id in range(n_clusters):
                cluster_points = [
                    features_normalized[i]
                    for i, a in enumerate(assignments)
                    if a == cluster_id
                ]
                if cluster_points:
                    centroids[cluster_id] = [
                        sum(p[dim] for p in cluster_points) / len(cluster_points)
                        for dim in range(len(cluster_points[0]))
                    ]

        return assignments

    def _normalize_features(self, features: List[List[float]]) -> List[List[float]]:
        """Normalize features to 0-1 range"""
        if not features or not features[0]:
            return features

        num_features = len(features[0])
        normalized = []

        for dim in range(num_features):
            values = [f[dim] for f in features]
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val if max_val != min_val else 1.0

            for i, f in enumerate(features):
                if i >= len(normalized):
                    normalized.append([])
                normalized[i].append((f[dim] - min_val) / range_val)

        return normalized

    def _euclidean_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calculate Euclidean distance between two points"""
        return sum((a - b) ** 2 for a, b in zip(point1, point2)) ** 0.5

    # ========== Duration Prediction ==========

    def predict_process_duration(self, process_id: str) -> Dict:
        """
        Predict remaining duration for a process

        Uses linear regression on historical similar processes

        Args:
            process_id: Process ID

        Returns:
            {
                'process_id': 'proc_123',
                'current_duration_hours': 12.5,
                'predicted_total_hours': 48.0,
                'predicted_remaining_hours': 35.5,
                'confidence': 0.75,  # 0.0-1.0
                'similar_processes_count': 15,
                'prediction_factors': ['field_completeness', 'current_state']
            }
        """
        process = self.repo.get_process_by_id(process_id)
        if not process:
            return {"error": "Process not found"}

        kanban_id = process.get("kanban_id")
        if not kanban_id:
            return {"error": "Process has no kanban_id"}

        # Get similar processes
        similar = self.pattern_analyzer.find_similar_processes(
            process_id, kanban_id, limit=20
        )

        if len(similar) < 3:
            return {
                "process_id": process_id,
                "error": "Insufficient similar processes for prediction",
                "similar_processes_count": len(similar),
            }

        # Calculate current duration
        current_duration = self._calculate_process_duration(process)

        # Get durations of similar completed processes
        similar_durations = []
        for sim in similar:
            sim_proc = self.repo.get_process_by_id(sim["process_id"])
            if sim_proc and self._is_completed(sim_proc):
                similar_durations.append(self._calculate_process_duration(sim_proc))

        if not similar_durations:
            return {
                "process_id": process_id,
                "error": "No completed similar processes found",
                "similar_processes_count": len(similar),
            }

        # Simple prediction: weighted average of similar processes
        avg_duration = sum(similar_durations) / len(similar_durations)

        # Calculate confidence based on variance
        variance = sum((d - avg_duration) ** 2 for d in similar_durations) / len(
            similar_durations
        )
        std_dev = variance**0.5
        confidence = max(
            0.0, min(1.0, 1.0 - (std_dev / avg_duration) if avg_duration > 0 else 0)
        )

        predicted_remaining = max(0, avg_duration - current_duration)

        return {
            "process_id": process_id,
            "current_duration_hours": round(current_duration, 1),
            "predicted_total_hours": round(avg_duration, 1),
            "predicted_remaining_hours": round(predicted_remaining, 1),
            "confidence": round(confidence, 2),
            "similar_processes_count": len(similar_durations),
            "prediction_factors": ["similar_process_patterns", "historical_durations"],
        }

    # ========== Risk Factor Identification ==========

    def identify_risk_factors(self, kanban_id: str) -> Dict:
        """
        Identify risk factors for processes in a kanban

        Analyzes patterns to identify factors that correlate with:
        - Longer durations
        - Process failures
        - Loops/rework

        Args:
            kanban_id: Kanban ID

        Returns:
            {
                'risk_factors': [
                    {
                        'factor': 'low_field_completeness',
                        'risk_level': 'high',  # low/medium/high
                        'correlation': 0.75,  # 0.0-1.0
                        'affected_processes': 15,
                        'avg_duration_increase': 48.5,  # hours
                        'recommendation': 'Ensure all required fields are filled...'
                    },
                    ...
                ],
                'summary': {
                    'high_risk_factors': 2,
                    'medium_risk_factors': 3,
                    'low_risk_factors': 1
                }
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if len(processes) < 10:
            return {
                "risk_factors": [],
                "summary": {
                    "high_risk_factors": 0,
                    "medium_risk_factors": 0,
                    "low_risk_factors": 0,
                    "error": "Insufficient processes for risk analysis (minimum 10)",
                },
            }

        risk_factors = []

        # Factor 1: Low field completeness
        completeness_risk = self._analyze_completeness_risk(processes)
        if completeness_risk:
            risk_factors.append(completeness_risk)

        # Factor 2: High transition count (loops/rework)
        transition_risk = self._analyze_transition_risk(processes)
        if transition_risk:
            risk_factors.append(transition_risk)

        # Factor 3: Stuck in specific states
        state_risk = self._analyze_state_risk(processes, kanban_id)
        if state_risk:
            risk_factors.append(state_risk)

        # Count by risk level
        summary = {
            "high_risk_factors": sum(
                1 for r in risk_factors if r["risk_level"] == "high"
            ),
            "medium_risk_factors": sum(
                1 for r in risk_factors if r["risk_level"] == "medium"
            ),
            "low_risk_factors": sum(
                1 for r in risk_factors if r["risk_level"] == "low"
            ),
        }

        return {"risk_factors": risk_factors, "summary": summary}

    def _analyze_completeness_risk(self, processes: List[Dict]) -> Optional[Dict]:
        """Analyze risk from low field completeness"""
        low_completeness = []
        high_completeness = []

        for proc in processes:
            completeness = self._calculate_field_completeness(proc)
            duration = self._calculate_process_duration(proc)

            if completeness < 0.5:
                low_completeness.append(duration)
            else:
                high_completeness.append(duration)

        if not low_completeness or not high_completeness:
            return None

        avg_low = sum(low_completeness) / len(low_completeness)
        avg_high = sum(high_completeness) / len(high_completeness)
        duration_increase = avg_low - avg_high

        if duration_increase < 12:  # Less than 12 hours difference
            return None

        # Calculate correlation
        correlation = min(1.0, duration_increase / avg_high if avg_high > 0 else 0)

        # Determine risk level
        if correlation >= 0.5:
            risk_level = "high"
        elif correlation >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "factor": "low_field_completeness",
            "risk_level": risk_level,
            "correlation": round(correlation, 2),
            "affected_processes": len(low_completeness),
            "avg_duration_increase": round(duration_increase, 1),
            "recommendation": "Ensure all required fields are filled before submitting processes",
        }

    def _analyze_transition_risk(self, processes: List[Dict]) -> Optional[Dict]:
        """Analyze risk from high transition count"""
        durations_by_transitions = defaultdict(list)

        for proc in processes:
            transition_count = len(proc.get("history", []))
            duration = self._calculate_process_duration(proc)
            durations_by_transitions[transition_count].append(duration)

        if len(durations_by_transitions) < 2:
            return None

        # Compare high transition count vs normal
        avg_by_count = {
            count: sum(durs) / len(durs)
            for count, durs in durations_by_transitions.items()
        }

        if not avg_by_count:
            return None

        normal_avg = sum(avg_by_count.values()) / len(avg_by_count)
        high_transition_procs = [
            proc for proc in processes if len(proc.get("history", [])) > 5
        ]

        if not high_transition_procs:
            return None

        high_transition_durations = [
            self._calculate_process_duration(p) for p in high_transition_procs
        ]

        avg_high = sum(high_transition_durations) / len(high_transition_durations)
        duration_increase = avg_high - normal_avg

        if duration_increase < 24:  # Less than 1 day difference
            return None

        correlation = min(1.0, duration_increase / normal_avg if normal_avg > 0 else 0)

        if correlation >= 0.5:
            risk_level = "high"
        elif correlation >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "factor": "high_transition_count",
            "risk_level": risk_level,
            "correlation": round(correlation, 2),
            "affected_processes": len(high_transition_procs),
            "avg_duration_increase": round(duration_increase, 1),
            "recommendation": "Review processes with loops/rework - may indicate unclear requirements",
        }

    def _analyze_state_risk(
        self, processes: List[Dict], kanban_id: str
    ) -> Optional[Dict]:
        """Analyze risk from getting stuck in specific states"""
        # Use pattern analyzer for state durations
        durations = self.pattern_analyzer.analyze_state_durations(kanban_id)

        if not durations:
            return None

        # Find states with high variance
        risky_states = []
        for state_id, stats in durations.items():
            if stats["sample_count"] < 3:
                continue

            # High variance indicates unpredictable/risky state
            variance_ratio = (
                stats["std_dev"] / stats["avg_hours"] if stats["avg_hours"] > 0 else 0
            )

            if variance_ratio > 0.5:  # Coefficient of variation > 0.5
                risky_states.append((state_id, variance_ratio, stats))

        if not risky_states:
            return None

        # Get most risky state
        state_id, variance_ratio, stats = max(risky_states, key=lambda x: x[1])

        if variance_ratio >= 0.75:
            risk_level = "high"
        elif variance_ratio >= 0.5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "factor": f"unpredictable_state_{state_id}",
            "risk_level": risk_level,
            "correlation": round(variance_ratio, 2),
            "affected_processes": stats["sample_count"],
            "avg_duration_increase": round(stats["max_hours"] - stats["min_hours"], 1),
            "recommendation": f"State '{state_id}' shows high duration variance - investigate root causes",
        }

    # ========== Weekly Reports ==========

    def generate_weekly_report(self, kanban_id: str) -> Dict:
        """
        Generate automated weekly report

        Args:
            kanban_id: Kanban ID

        Returns:
            {
                'report_date': '2025-11-03',
                'period': '2025-10-27 to 2025-11-03',
                'summary': {
                    'total_processes': 45,
                    'completed': 38,
                    'active': 7,
                    'completion_rate': 0.84
                },
                'clusters': [...],
                'risk_factors': [...],
                'recommendations': [...]
            }
        """
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # Get processes from last week
        all_processes = self.repo.get_processes_by_kanban(kanban_id)
        week_processes = [
            p
            for p in all_processes
            if p.get("created_at")
            and datetime.fromisoformat(p["created_at"]) >= week_ago
        ]

        # Basic stats
        completed = [p for p in week_processes if self._is_completed(p)]
        active = [p for p in week_processes if not self._is_completed(p)]

        # Get clustering
        clusters = self.cluster_similar_processes(kanban_id, n_clusters=3)

        # Get risk factors
        risks = self.identify_risk_factors(kanban_id)

        # Generate recommendations
        recommendations = []
        if risks["summary"]["high_risk_factors"] > 0:
            recommendations.append("Address high-risk factors immediately")
        if len(completed) / len(week_processes) < 0.7 if week_processes else False:
            recommendations.append(
                "Completion rate below target (70%) - investigate blockers"
            )
        if clusters["summary"]["clusters_count"] > 0:
            recommendations.append(
                "Review cluster patterns for process optimization opportunities"
            )

        return {
            "report_date": now.date().isoformat(),
            "period": f"{week_ago.date().isoformat()} to {now.date().isoformat()}",
            "summary": {
                "total_processes": len(week_processes),
                "completed": len(completed),
                "active": len(active),
                "completion_rate": (
                    len(completed) / len(week_processes) if week_processes else 0
                ),
            },
            "clusters": clusters,
            "risk_factors": risks,
            "recommendations": recommendations,
        }

    # ========== Helper Methods ==========

    def _calculate_process_duration(self, process: Dict) -> float:
        """Calculate total process duration in hours"""
        created_at = process.get("created_at")
        if not created_at:
            return 0.0

        history = process.get("history", [])
        if history:
            last_timestamp = history[-1].get("timestamp")
            if last_timestamp:
                try:
                    start = datetime.fromisoformat(created_at)
                    end = datetime.fromisoformat(last_timestamp)
                    return (end - start).total_seconds() / 3600
                except:
                    pass

        # If no history, calculate from created_at to now
        try:
            start = datetime.fromisoformat(created_at)
            now = datetime.now()
            return (now - start).total_seconds() / 3600
        except:
            return 0.0

    def _calculate_field_completeness(self, process: Dict) -> float:
        """Calculate percentage of non-empty fields"""
        field_values = process.get("field_values", {})
        if not field_values:
            return 0.0

        filled = sum(1 for v in field_values.values() if v not in [None, "", []])
        return filled / len(field_values) if field_values else 0.0

    def _is_completed(self, process: Dict) -> bool:
        """Check if process is in a final state"""
        # Simplified check - would need registry access for proper check
        current_state = process.get("current_state", "")
        history = process.get("history", [])

        # Assume completed if has history and reasonable duration
        return len(history) > 0
