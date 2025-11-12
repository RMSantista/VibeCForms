"""
AnomalyDetector - Identifies anomalous processes and behaviors

Responsibilities:
- Detect stuck processes (excessive time in state)
- Identify unusual transition sequences
- Find processes with abnormal durations
- Detect looping patterns
- Flag processes requiring intervention

Techniques:
- Statistical outlier detection (Z-score, IQR)
- Duration-based anomaly detection
- Pattern deviation analysis
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import statistics
from collections import Counter


class AnomalyDetector:
    """
    Detector for workflow anomalies and stuck processes

    Uses statistical analysis to identify processes
    requiring attention or intervention.
    """

    def __init__(self, workflow_repo):
        """
        Initialize AnomalyDetector

        Args:
            workflow_repo: WorkflowRepository instance for data access
        """
        self.repo = workflow_repo

    # ========== Stuck Process Detection ==========

    def detect_stuck_processes(
        self, kanban_id: str, threshold_hours: int = 48
    ) -> List[Dict]:
        """
        Identify processes stuck in a state longer than expected

        Args:
            kanban_id: Kanban ID to analyze
            threshold_hours: Minimum hours to consider "stuck"

        Returns:
            List of stuck processes:
            [
                {
                    'process_id': 'proc_123',
                    'current_state': 'em_analise',
                    'hours_stuck': 96.5,
                    'expected_duration': 24.0,
                    'anomaly_score': 0.95,
                    'last_transition': '2025-01-01T10:00:00'
                },
                ...
            ]
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if not processes:
            return []

        # Calculate average durations per state
        state_durations = self._calculate_average_state_durations(processes)

        # Identify stuck processes
        stuck = []
        now = datetime.now(timezone.utc)

        for process in processes:
            current_state = process.get("current_state")
            history = process.get("history", [])

            # Get timestamp of last transition or creation
            if history:
                last_transition_time = history[-1].get("timestamp")
            else:
                last_transition_time = process.get("created_at")

            if not last_transition_time:
                continue

            try:
                last_time = datetime.fromisoformat(last_transition_time)
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)

                hours_in_state = (now - last_time).total_seconds() / 3600

                # Check if stuck
                if hours_in_state >= threshold_hours:
                    expected_duration = state_durations.get(
                        current_state, threshold_hours
                    )
                    anomaly_score = min(1.0, hours_in_state / (expected_duration * 2))

                    stuck.append(
                        {
                            "process_id": process["process_id"],
                            "current_state": current_state,
                            "hours_stuck": round(hours_in_state, 2),
                            "expected_duration": round(expected_duration, 2),
                            "anomaly_score": round(anomaly_score, 3),
                            "last_transition": last_transition_time,
                        }
                    )

            except (ValueError, TypeError):
                pass

        # Sort by hours_stuck (descending)
        stuck.sort(key=lambda x: x["hours_stuck"], reverse=True)

        return stuck

    def _calculate_average_state_durations(
        self, processes: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate average time spent in each state

        Args:
            processes: List of process dicts

        Returns:
            Dict mapping state to average hours: {'state1': 24.5, ...}
        """
        state_durations = {}

        # Collect all durations per state
        durations_by_state = {}

        for process in processes:
            history = process.get("history", [])

            for i in range(len(history)):
                transition = history[i]
                from_state = transition.get("from_state")
                timestamp = transition.get("timestamp")

                if not from_state or not timestamp:
                    continue

                # Find next transition or use now
                if i + 1 < len(history):
                    next_timestamp = history[i + 1].get("timestamp")
                else:
                    next_timestamp = datetime.now(timezone.utc).isoformat()

                try:
                    start = datetime.fromisoformat(timestamp)
                    end = datetime.fromisoformat(next_timestamp)
                    duration_hours = (end - start).total_seconds() / 3600

                    if from_state not in durations_by_state:
                        durations_by_state[from_state] = []
                    durations_by_state[from_state].append(duration_hours)

                except (ValueError, TypeError):
                    pass

        # Calculate averages
        for state, durations in durations_by_state.items():
            if durations:
                state_durations[state] = statistics.mean(durations)

        return state_durations

    # ========== Duration Anomaly Detection ==========

    def detect_duration_anomalies(
        self, kanban_id: str, z_score_threshold: float = 2.0
    ) -> List[Dict]:
        """
        Detect processes with abnormally long/short durations using Z-score

        Args:
            kanban_id: Kanban ID
            z_score_threshold: Z-score threshold (default: 2.0 = 95% confidence)

        Returns:
            List of anomalous processes:
            [
                {
                    'process_id': 'proc_456',
                    'total_duration_hours': 240.5,
                    'expected_duration': 48.0,
                    'z_score': 3.2,
                    'anomaly_type': 'too_long',
                    'states_visited': ['state1', 'state2', ...]
                },
                ...
            ]
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if len(processes) < 3:
            return []  # Need minimum sample size for statistics

        # Calculate total duration for each process
        process_durations = []
        for process in processes:
            duration = self._calculate_total_duration(process)
            if duration is not None:
                process_durations.append(
                    {
                        "process_id": process["process_id"],
                        "duration": duration,
                        "states": self._get_states_visited(process),
                    }
                )

        if len(process_durations) < 3:
            return []

        # Calculate mean and std dev
        durations = [p["duration"] for p in process_durations]
        mean_duration = statistics.mean(durations)
        std_dev = statistics.stdev(durations) if len(durations) > 1 else 0

        # Identify anomalies
        anomalies = []

        for item in process_durations:
            if std_dev == 0:
                continue

            z_score = (item["duration"] - mean_duration) / std_dev

            if abs(z_score) >= z_score_threshold:
                anomaly_type = "too_long" if z_score > 0 else "too_short"

                anomalies.append(
                    {
                        "process_id": item["process_id"],
                        "total_duration_hours": round(item["duration"], 2),
                        "expected_duration": round(mean_duration, 2),
                        "z_score": round(z_score, 2),
                        "anomaly_type": anomaly_type,
                        "states_visited": item["states"],
                    }
                )

        # Sort by absolute z_score (descending)
        anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)

        return anomalies

    def _calculate_total_duration(self, process: Dict) -> Optional[float]:
        """
        Calculate total duration from creation to current state

        Returns duration in hours, or None if cannot calculate
        """
        created_at = process.get("created_at")
        history = process.get("history", [])

        if not created_at:
            return None

        try:
            start = datetime.fromisoformat(created_at)

            # Use last transition or current time
            if history:
                end_time = history[-1].get("timestamp")
                end = (
                    datetime.fromisoformat(end_time)
                    if end_time
                    else datetime.now(timezone.utc)
                )
            else:
                end = datetime.now(timezone.utc)

            # Make timezone-aware
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            duration_hours = (end - start).total_seconds() / 3600
            return duration_hours

        except (ValueError, TypeError):
            return None

    def _get_states_visited(self, process: Dict) -> List[str]:
        """Get list of all states visited by process"""
        states = []
        history = process.get("history", [])

        for transition in history:
            from_state = transition.get("from_state")
            to_state = transition.get("to_state")

            if from_state and from_state not in states:
                states.append(from_state)
            if to_state and to_state not in states:
                states.append(to_state)

        return states

    # ========== Loop Detection ==========

    def detect_loops(self, kanban_id: str, max_loop_size: int = 3) -> List[Dict]:
        """
        Detect processes with looping patterns (revisiting states)

        Args:
            kanban_id: Kanban ID
            max_loop_size: Maximum loop size to detect

        Returns:
            List of processes with loops:
            [
                {
                    'process_id': 'proc_789',
                    'loops_detected': [
                        {
                            'loop': ['state1', 'state2', 'state1'],
                            'occurrences': 3,
                            'total_duration_hours': 48.0
                        }
                    ]
                },
                ...
            ]
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        processes_with_loops = []

        for process in processes:
            loops = self._find_loops_in_process(process, max_loop_size)

            if loops:
                processes_with_loops.append(
                    {"process_id": process["process_id"], "loops_detected": loops}
                )

        return processes_with_loops

    def _find_loops_in_process(self, process: Dict, max_loop_size: int) -> List[Dict]:
        """Find looping patterns in a single process"""
        history = process.get("history", [])

        if len(history) < 2:
            return []

        # Extract state sequence
        states = []
        for transition in history:
            from_state = transition.get("from_state")
            if not states and from_state:
                states.append(from_state)

            to_state = transition.get("to_state")
            if to_state:
                states.append(to_state)

        # Detect loops (state appearing multiple times)
        loops_found = []
        state_positions = {}

        for i, state in enumerate(states):
            if state in state_positions:
                # Found a revisit - this is a loop
                loop_start = state_positions[state]
                loop = states[loop_start : i + 1]

                # Only consider loops up to max_loop_size
                if len(loop) <= max_loop_size + 1:
                    loops_found.append(
                        {
                            "loop": loop,
                            "occurrences": 1,  # Simplified - could count multiple occurrences
                            "total_duration_hours": 0.0,  # Would need timestamps to calculate
                        }
                    )

            state_positions[state] = i

        return loops_found

    # ========== Unusual Transition Detection ==========

    def detect_unusual_transitions(
        self, kanban_id: str, rarity_threshold: float = 0.05
    ) -> List[Dict]:
        """
        Detect processes with rare/unusual transitions

        Args:
            kanban_id: Kanban ID
            rarity_threshold: Transitions occurring less than this % are considered unusual

        Returns:
            List of processes with unusual transitions:
            [
                {
                    'process_id': 'proc_999',
                    'unusual_transitions': [
                        {
                            'from_state': 'state1',
                            'to_state': 'state5',
                            'occurrence_rate': 0.02,
                            'total_occurrences': 2
                        }
                    ]
                },
                ...
            ]
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        # Count all transitions
        transition_counts = Counter()
        total_transitions = 0

        for process in processes:
            history = process.get("history", [])

            for transition in history:
                from_state = transition.get("from_state")
                to_state = transition.get("to_state")

                if from_state and to_state:
                    transition_key = f"{from_state}->{to_state}"
                    transition_counts[transition_key] += 1
                    total_transitions += 1

        if total_transitions == 0:
            return []

        # Calculate occurrence rates
        rare_transitions = set()
        for transition_key, count in transition_counts.items():
            occurrence_rate = count / total_transitions

            if occurrence_rate < rarity_threshold:
                rare_transitions.add(transition_key)

        # Find processes with rare transitions
        unusual_processes = []

        for process in processes:
            unusual_trans = []
            history = process.get("history", [])

            for transition in history:
                from_state = transition.get("from_state")
                to_state = transition.get("to_state")

                if from_state and to_state:
                    transition_key = f"{from_state}->{to_state}"

                    if transition_key in rare_transitions:
                        count = transition_counts[transition_key]
                        occurrence_rate = count / total_transitions

                        unusual_trans.append(
                            {
                                "from_state": from_state,
                                "to_state": to_state,
                                "occurrence_rate": round(occurrence_rate, 4),
                                "total_occurrences": count,
                            }
                        )

            if unusual_trans:
                unusual_processes.append(
                    {
                        "process_id": process["process_id"],
                        "unusual_transitions": unusual_trans,
                    }
                )

        return unusual_processes

    # ========== Summary Report ==========

    def generate_anomaly_report(self, kanban_id: str) -> Dict:
        """
        Generate comprehensive anomaly report for kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            Dict with all anomaly types:
            {
                'stuck_processes': [...],
                'duration_anomalies': [...],
                'loops': [...],
                'unusual_transitions': [...],
                'summary': {
                    'total_processes': 100,
                    'stuck_count': 5,
                    'duration_anomalies_count': 3,
                    'loops_count': 2,
                    'unusual_transitions_count': 7
                }
            }
        """
        stuck = self.detect_stuck_processes(kanban_id)
        duration_anomalies = self.detect_duration_anomalies(kanban_id)
        loops = self.detect_loops(kanban_id)
        unusual = self.detect_unusual_transitions(kanban_id)

        # Get total process count
        processes = self.repo.get_processes_by_kanban(kanban_id)

        return {
            "stuck_processes": stuck,
            "duration_anomalies": duration_anomalies,
            "loops": loops,
            "unusual_transitions": unusual,
            "summary": {
                "total_processes": len(processes),
                "stuck_count": len(stuck),
                "duration_anomalies_count": len(duration_anomalies),
                "loops_count": len(loops),
                "unusual_transitions_count": len(unusual),
            },
        }
