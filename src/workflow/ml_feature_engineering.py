"""
MLFeatureEngineering - Advanced feature engineering for workflow ML

Responsabilidades:
- Extrair features avançadas de processos
- Análise de importância de features
- Feature store para caching
- Encoding de sequências e estados
- Features temporais e contextuais
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import hashlib


logger = logging.getLogger(__name__)


class MLFeatureEngineering:
    """
    Advanced feature engineering for workflow ML models

    Provides sophisticated feature extraction including:
    - Temporal features (time of day, day of week, seasonality)
    - Sequence encoding (state transitions, n-grams)
    - Statistical features (aggregations, distributions)
    - Contextual features (field values, tags, assignments)
    - SLA-based features (deadline proximity, breach probability)
    """

    def __init__(self, workflow_repo, kanban_registry):
        """
        Initialize MLFeatureEngineering

        Args:
            workflow_repo: WorkflowRepository instance
            kanban_registry: KanbanRegistry instance
        """
        self.repo = workflow_repo
        self.registry = kanban_registry

        # Feature cache for performance
        self.feature_cache = {}

        # Feature importance scores (updated during training)
        self.feature_importance = {}

        logger.info("MLFeatureEngineering initialized")

    # ========== Core Feature Extraction ==========

    def extract_features(
        self, process: Dict, include_temporal: bool = True
    ) -> Dict[str, float]:
        """
        Extract comprehensive feature set from a process

        Args:
            process: Process dict
            include_temporal: Include time-based features

        Returns:
            Dict mapping feature names to numeric values
        """
        features = {}

        # Basic features
        features.update(self._extract_basic_features(process))

        # Temporal features
        if include_temporal:
            features.update(self._extract_temporal_features(process))

        # Sequence features
        features.update(self._extract_sequence_features(process))

        # Field value features
        features.update(self._extract_field_features(process))

        # Metadata features
        features.update(self._extract_metadata_features(process))

        # SLA features
        features.update(self._extract_sla_features(process))

        # State features
        features.update(self._extract_state_features(process))

        return features

    def _extract_basic_features(self, process: Dict) -> Dict[str, float]:
        """Extract basic numeric features"""
        features = {}

        # Duration
        duration_hours = self._calculate_duration_hours(process)
        features["duration_hours"] = duration_hours
        features["duration_days"] = duration_hours / 24
        features["log_duration_hours"] = self._safe_log(duration_hours + 1)

        # Transition count
        history = process.get("history", [])
        features["transition_count"] = len(history)
        features["log_transition_count"] = self._safe_log(len(history) + 1)

        # Unique states visited
        unique_states = set(t["to_state"] for t in history)
        unique_states.add(process.get("current_state"))
        features["unique_states_count"] = len(unique_states)

        # Field completeness
        features["field_completeness"] = self._calculate_field_completeness(process)

        # Tag count
        features["tag_count"] = len(process.get("tags", []))

        # Has assignment
        features["has_assignment"] = 1.0 if process.get("assigned_to") else 0.0

        return features

    def _extract_temporal_features(self, process: Dict) -> Dict[str, float]:
        """Extract time-based features"""
        features = {}

        created_at = process.get("created_at")
        if not created_at:
            return features

        try:
            created_dt = datetime.fromisoformat(created_at)

            # Hour of day (0-23)
            features["created_hour"] = created_dt.hour
            features["created_hour_normalized"] = created_dt.hour / 24.0

            # Day of week (0=Monday, 6=Sunday)
            features["created_day_of_week"] = created_dt.weekday()
            features["created_is_weekend"] = 1.0 if created_dt.weekday() >= 5 else 0.0

            # Business hours
            is_business_hours = (9 <= created_dt.hour < 18) and (
                created_dt.weekday() < 5
            )
            features["created_in_business_hours"] = 1.0 if is_business_hours else 0.0

            # Month and quarter
            features["created_month"] = created_dt.month
            features["created_quarter"] = (created_dt.month - 1) // 3 + 1

            # Time since creation
            now = datetime.now()
            hours_since_creation = (now - created_dt).total_seconds() / 3600
            features["hours_since_creation"] = hours_since_creation
            features["days_since_creation"] = hours_since_creation / 24

        except Exception as e:
            logger.warning(f"Error extracting temporal features: {e}")

        return features

    def _extract_sequence_features(self, process: Dict) -> Dict[str, float]:
        """Extract features from state transition sequences"""
        features = {}

        history = process.get("history", [])

        if not history:
            return features

        # State sequence
        states = [t["to_state"] for t in history]

        # Sequence length
        features["sequence_length"] = len(states)

        # Loop detection (state revisits)
        state_counts = Counter(states)
        features["max_state_revisits"] = (
            max(state_counts.values()) - 1 if state_counts else 0
        )
        features["has_loops"] = 1.0 if features["max_state_revisits"] > 0 else 0.0

        # Unique transitions
        transitions = [(states[i], states[i + 1]) for i in range(len(states) - 1)]
        features["unique_transitions"] = len(set(transitions))

        # Transition diversity (unique / total)
        features["transition_diversity"] = (
            features["unique_transitions"] / len(transitions) if transitions else 0.0
        )

        # Average time per state
        if len(history) > 1:
            total_duration = self._calculate_duration_hours(process)
            features["avg_hours_per_state"] = total_duration / len(history)
        else:
            features["avg_hours_per_state"] = 0.0

        # Last transition recency
        if history:
            last_transition = history[-1]
            last_timestamp = last_transition.get("timestamp")
            if last_timestamp:
                try:
                    last_dt = datetime.fromisoformat(last_timestamp)
                    hours_since_last = (datetime.now() - last_dt).total_seconds() / 3600
                    features["hours_since_last_transition"] = hours_since_last
                except:
                    pass

        return features

    def _extract_field_features(self, process: Dict) -> Dict[str, float]:
        """Extract features from field values"""
        features = {}

        field_values = process.get("field_values", {})

        if not field_values:
            return features

        # Field count
        features["total_fields"] = len(field_values)

        # Filled fields
        filled = sum(1 for v in field_values.values() if v not in [None, "", []])
        features["filled_fields"] = filled
        features["field_fill_rate"] = (
            filled / len(field_values) if field_values else 0.0
        )

        # Empty fields
        features["empty_fields"] = len(field_values) - filled

        # Numeric field aggregations
        numeric_values = []
        for value in field_values.values():
            if isinstance(value, (int, float)):
                numeric_values.append(value)

        if numeric_values:
            features["numeric_fields_count"] = len(numeric_values)
            features["numeric_fields_sum"] = sum(numeric_values)
            features["numeric_fields_avg"] = sum(numeric_values) / len(numeric_values)
            features["numeric_fields_max"] = max(numeric_values)
            features["numeric_fields_min"] = min(numeric_values)

        # String field statistics
        string_values = [v for v in field_values.values() if isinstance(v, str) and v]
        if string_values:
            features["string_fields_count"] = len(string_values)
            features["avg_string_length"] = sum(len(s) for s in string_values) / len(
                string_values
            )

        return features

    def _extract_metadata_features(self, process: Dict) -> Dict[str, float]:
        """Extract features from metadata"""
        features = {}

        # Tags
        tags = process.get("tags", [])
        features["has_priority_tag"] = (
            1.0 if any("priority" in str(t).lower() for t in tags) else 0.0
        )
        features["has_urgent_tag"] = (
            1.0 if any("urgent" in str(t).lower() for t in tags) else 0.0
        )

        # Assignment
        assigned_to = process.get("assigned_to")
        if assigned_to:
            # Hash assignment for anonymity (consistent numeric representation)
            assignment_hash = int(
                hashlib.md5(str(assigned_to).encode()).hexdigest()[:8], 16
            )
            features["assignment_hash"] = (
                assignment_hash % 1000
            )  # Modulo for reasonable range

        # Metadata fields
        metadata = process.get("metadata", {})
        features["has_metadata"] = 1.0 if metadata else 0.0
        features["metadata_field_count"] = len(metadata)

        return features

    def _extract_sla_features(self, process: Dict) -> Dict[str, float]:
        """Extract SLA-related features"""
        features = {}

        sla = process.get("sla")
        if not sla:
            features["has_sla"] = 0.0
            return features

        features["has_sla"] = 1.0

        deadline = sla.get("deadline")
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline)
                now = datetime.now()

                # Hours until deadline
                hours_remaining = (deadline_dt - now).total_seconds() / 3600
                features["sla_hours_remaining"] = hours_remaining
                features["sla_days_remaining"] = hours_remaining / 24

                # Is overdue
                features["sla_is_overdue"] = 1.0 if hours_remaining < 0 else 0.0

                # Deadline proximity (0=at deadline, 1=far from deadline)
                total_hours = sla.get("total_hours", 168)  # Default 1 week
                if total_hours > 0:
                    features["sla_deadline_proximity"] = max(
                        0, hours_remaining / total_hours
                    )

                # Is in warning zone
                warning_threshold = sla.get("warning_threshold", 0.2)
                features["sla_in_warning_zone"] = (
                    1.0
                    if 0 < features["sla_deadline_proximity"] < warning_threshold
                    else 0.0
                )

            except Exception as e:
                logger.warning(f"Error extracting SLA features: {e}")

        return features

    def _extract_state_features(self, process: Dict) -> Dict[str, float]:
        """Extract features about current and historical states"""
        features = {}

        kanban_id = process.get("kanban_id")
        current_state = process.get("current_state")

        if not kanban_id or not current_state:
            return features

        # Get state info from registry
        kanban = self.registry.get_kanban(kanban_id)
        if not kanban:
            return features

        state = self.registry.get_state_by_id(kanban_id, current_state)
        if state:
            # State type encoding
            state_type = state.get("type", "intermediate")
            features["state_is_initial"] = 1.0 if state_type == "initial" else 0.0
            features["state_is_final"] = 1.0 if state_type == "final" else 0.0
            features["state_is_intermediate"] = (
                1.0 if state_type == "intermediate" else 0.0
            )

        # Available transitions count
        available_transitions = self.registry.get_available_transitions(
            kanban_id, current_state
        )
        features["available_transitions_count"] = len(available_transitions)

        # Historical state duration
        history = process.get("history", [])
        if history:
            # Time in current state
            last_transition = history[-1]
            last_timestamp = last_transition.get("timestamp")
            if last_timestamp:
                try:
                    last_dt = datetime.fromisoformat(last_timestamp)
                    hours_in_state = (datetime.now() - last_dt).total_seconds() / 3600
                    features["hours_in_current_state"] = hours_in_state
                    features["days_in_current_state"] = hours_in_state / 24
                except:
                    pass

        return features

    # ========== Batch Feature Extraction ==========

    def extract_features_batch(
        self, processes: List[Dict], use_cache: bool = True
    ) -> List[Dict[str, float]]:
        """
        Extract features for multiple processes efficiently

        Args:
            processes: List of process dicts
            use_cache: Use cached features if available

        Returns:
            List of feature dicts
        """
        features_list = []

        for process in processes:
            process_id = process.get("process_id")

            # Check cache
            if use_cache and process_id in self.feature_cache:
                cached = self.feature_cache[process_id]
                # Invalidate if process was updated
                if cached["updated_at"] == process.get("updated_at"):
                    features_list.append(cached["features"])
                    continue

            # Extract features
            features = self.extract_features(process)

            # Cache result
            if process_id:
                self.feature_cache[process_id] = {
                    "features": features,
                    "updated_at": process.get("updated_at"),
                    "cached_at": datetime.now().isoformat(),
                }

            features_list.append(features)

        return features_list

    # ========== Feature Selection & Importance ==========

    def calculate_feature_importance(
        self, features_list: List[Dict[str, float]], target_values: List[float]
    ) -> Dict[str, float]:
        """
        Calculate feature importance using correlation with target

        Args:
            features_list: List of feature dicts
            target_values: Target values (e.g., durations) for each process

        Returns:
            Dict mapping feature names to importance scores (0-1)
        """
        if (
            not features_list
            or not target_values
            or len(features_list) != len(target_values)
        ):
            return {}

        # Get all feature names
        feature_names = set()
        for features in features_list:
            feature_names.update(features.keys())

        importance_scores = {}

        for feature_name in feature_names:
            # Extract feature values (handle missing values)
            feature_values = []
            corresponding_targets = []

            for features, target in zip(features_list, target_values):
                if feature_name in features:
                    feature_values.append(features[feature_name])
                    corresponding_targets.append(target)

            # Calculate correlation
            if len(feature_values) >= 3:
                correlation = self._calculate_correlation(
                    feature_values, corresponding_targets
                )
                importance_scores[feature_name] = abs(correlation)

        # Store for future reference
        self.feature_importance = importance_scores

        return importance_scores

    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top N most important features

        Args:
            n: Number of features to return

        Returns:
            List of (feature_name, importance_score) tuples
        """
        if not self.feature_importance:
            return []

        sorted_features = sorted(
            self.feature_importance.items(), key=lambda x: x[1], reverse=True
        )

        return sorted_features[:n]

    def select_features(
        self, features: Dict[str, float], min_importance: float = 0.1
    ) -> Dict[str, float]:
        """
        Select only important features

        Args:
            features: Full feature dict
            min_importance: Minimum importance threshold

        Returns:
            Filtered feature dict
        """
        if not self.feature_importance:
            return features

        selected = {}
        for feature_name, value in features.items():
            importance = self.feature_importance.get(feature_name, 0.0)
            if importance >= min_importance:
                selected[feature_name] = value

        return selected

    # ========== Feature Analysis ==========

    def analyze_feature_distributions(
        self, kanban_id: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze feature distributions for a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            Dict mapping feature names to distribution statistics
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if not processes:
            return {}

        # Extract features for all processes
        features_list = self.extract_features_batch(processes)

        # Aggregate statistics
        distributions = defaultdict(lambda: {"values": []})

        for features in features_list:
            for feature_name, value in features.items():
                distributions[feature_name]["values"].append(value)

        # Calculate statistics
        result = {}
        for feature_name, data in distributions.items():
            values = data["values"]
            if values:
                result[feature_name] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": self._calculate_std_dev(values),
                }

        return result

    # ========== Helper Methods ==========

    def _calculate_duration_hours(self, process: Dict) -> float:
        """Calculate process duration in hours"""
        created_at = process.get("created_at")
        if not created_at:
            return 0.0

        try:
            start = datetime.fromisoformat(created_at)
            now = datetime.now()
            return (now - start).total_seconds() / 3600
        except:
            return 0.0

    def _calculate_field_completeness(self, process: Dict) -> float:
        """Calculate field completeness ratio"""
        field_values = process.get("field_values", {})
        if not field_values:
            return 0.0

        filled = sum(1 for v in field_values.values() if v not in [None, "", []])
        return filled / len(field_values)

    def _safe_log(self, value: float) -> float:
        """Safe logarithm (handles zero)"""
        import math

        return math.log(max(value, 1.0))

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if not x or not y or len(x) != len(y):
            return 0.0

        n = len(x)
        if n < 2:
            return 0.0

        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Calculate correlation
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        return numerator / (denominator_x * denominator_y)

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance**0.5

    def clear_cache(self):
        """Clear feature cache"""
        self.feature_cache.clear()
        logger.info("Feature cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_processes": len(self.feature_cache),
            "total_features": sum(
                len(cached["features"]) for cached in self.feature_cache.values()
            ),
        }
