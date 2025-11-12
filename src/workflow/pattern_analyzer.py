"""
PatternAnalyzer - Analyzes historical transitions to identify frequent patterns

Responsibilities:
- Analyze transition sequences across all processes
- Identify frequent patterns using sequential analysis
- Calculate pattern metrics (support, confidence, duration)
- Detect common paths vs exceptional paths
- Group similar processes using clustering

Techniques:
- Sequential pattern mining
- Statistical analysis of transitions
- Duration-based clustering
"""

from typing import List, Dict, Optional
from collections import defaultdict, Counter
from datetime import datetime
import statistics


class PatternAnalyzer:
    """
    Analyzer for workflow transition patterns

    Identifies frequent sequences, calculates metrics,
    and provides insights for optimization.
    """

    def __init__(self, workflow_repo):
        """
        Initialize PatternAnalyzer

        Args:
            workflow_repo: WorkflowRepository instance for data access
        """
        self.repo = workflow_repo

    # ========== Pattern Detection ==========

    def analyze_transition_patterns(
        self, kanban_id: str, min_support: float = 0.3
    ) -> List[Dict]:
        """
        Identify frequent transition patterns

        Args:
            kanban_id: Kanban ID to analyze
            min_support: Minimum support threshold (0.0 to 1.0)

        Returns:
            List of patterns sorted by support:
            [
                {
                    'pattern': ['state1', 'state2', 'state3'],
                    'support': 0.85,
                    'count': 34,
                    'avg_duration_hours': 72.5,
                    'confidence': 0.92
                },
                ...
            ]
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        if not processes:
            return []

        # Extract sequences from processes
        sequences = self._extract_sequences(processes)

        if not sequences:
            return []

        # Count pattern occurrences
        patterns = self._find_frequent_patterns(sequences, min_support)

        # Calculate metrics for each pattern
        pattern_metrics = []
        for pattern, count in patterns.items():
            support = count / len(sequences)

            # Calculate average duration and confidence
            durations = self._calculate_pattern_durations(pattern, processes)
            avg_duration = statistics.mean(durations) if durations else 0

            confidence = self._calculate_confidence(pattern, sequences)

            pattern_metrics.append(
                {
                    "pattern": list(pattern),
                    "support": round(support, 3),
                    "count": count,
                    "avg_duration_hours": round(avg_duration, 2),
                    "confidence": round(confidence, 3),
                }
            )

        # Sort by support (descending)
        pattern_metrics.sort(key=lambda x: x["support"], reverse=True)

        return pattern_metrics

    def _extract_sequences(self, processes: List[Dict]) -> List[List[str]]:
        """
        Extract state sequences from processes

        Args:
            processes: List of process dicts

        Returns:
            List of state sequences: [['state1', 'state2'], ...]
        """
        sequences = []

        for process in processes:
            sequence = []
            history = process.get("history", [])

            # Add initial state if no history
            if not history:
                current_state = process.get("current_state")
                if current_state:
                    sequences.append([current_state])
                continue

            # Build sequence from history
            for transition in history:
                from_state = transition.get("from_state")
                to_state = transition.get("to_state")

                # Start sequence with from_state if empty
                if not sequence and from_state:
                    sequence.append(from_state)

                # Add to_state
                if to_state:
                    sequence.append(to_state)

            if sequence:
                sequences.append(sequence)

        return sequences

    def _find_frequent_patterns(
        self, sequences: List[List[str]], min_support: float
    ) -> Dict:
        """
        Find frequent sequential patterns

        Args:
            sequences: List of state sequences
            min_support: Minimum support threshold

        Returns:
            Dict of patterns to counts: {(s1, s2): count, ...}
        """
        pattern_counts = Counter()
        min_count = int(len(sequences) * min_support)

        # Count all subsequences of length 2 to 5
        for sequence in sequences:
            # Generate all subsequences
            for length in range(2, min(6, len(sequence) + 1)):
                for i in range(len(sequence) - length + 1):
                    subsequence = tuple(sequence[i : i + length])
                    pattern_counts[subsequence] += 1

        # Filter by minimum support
        frequent_patterns = {
            pattern: count
            for pattern, count in pattern_counts.items()
            if count >= min_count
        }

        return frequent_patterns

    def _calculate_pattern_durations(
        self, pattern: tuple, processes: List[Dict]
    ) -> List[float]:
        """
        Calculate durations for pattern occurrences

        Args:
            pattern: Tuple of states (e.g., ('state1', 'state2'))
            processes: List of all processes

        Returns:
            List of durations in hours
        """
        durations = []

        for process in processes:
            history = process.get("history", [])

            if not history:
                continue

            # Find pattern in history
            for i in range(len(history) - len(pattern) + 1):
                # Check if pattern matches
                matches = True
                for j, state in enumerate(pattern):
                    if i + j >= len(history):
                        matches = False
                        break

                    transition = history[i + j]
                    # First state should match from_state
                    if j == 0 and transition.get("from_state") != state:
                        matches = False
                        break
                    # Other states should match to_state
                    if j > 0 and transition.get("to_state") != state:
                        matches = False
                        break

                if matches:
                    # Calculate duration from first to last transition
                    start_time = history[i].get("timestamp")
                    end_time = history[i + len(pattern) - 1].get("timestamp")

                    if start_time and end_time:
                        try:
                            start = datetime.fromisoformat(start_time)
                            end = datetime.fromisoformat(end_time)
                            duration_hours = (end - start).total_seconds() / 3600
                            durations.append(duration_hours)
                        except (ValueError, TypeError):
                            pass

        return durations

    def _calculate_confidence(
        self, pattern: tuple, sequences: List[List[str]]
    ) -> float:
        """
        Calculate confidence for pattern (% of times pattern completion occurs)

        Confidence = P(last state | previous states)

        Args:
            pattern: Tuple of states
            sequences: All sequences

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if len(pattern) < 2:
            return 1.0

        # Count sequences containing pattern prefix
        prefix = pattern[:-1]
        prefix_count = 0
        pattern_count = 0

        for sequence in sequences:
            # Check if sequence contains prefix
            for i in range(len(sequence) - len(prefix) + 1):
                if tuple(sequence[i : i + len(prefix)]) == prefix:
                    prefix_count += 1

                    # Check if full pattern follows
                    if i + len(pattern) <= len(sequence):
                        if tuple(sequence[i : i + len(pattern)]) == pattern:
                            pattern_count += 1

        if prefix_count == 0:
            return 0.0

        return pattern_count / prefix_count

    # ========== Pattern Classification ==========

    def classify_patterns(
        self,
        patterns: List[Dict],
        support_threshold_common: float = 0.7,
        support_threshold_exceptional: float = 0.1,
    ) -> Dict:
        """
        Classify patterns as common, problematic, or exceptional

        Args:
            patterns: List of pattern dicts from analyze_transition_patterns()
            support_threshold_common: Threshold for "common" classification
            support_threshold_exceptional: Threshold below which patterns are "exceptional"

        Returns:
            Dict with classified patterns:
            {
                'common': [...],      # High support, expected paths
                'problematic': [...],  # Patterns ending in failure states
                'exceptional': [...]   # Low support, unusual paths
            }
        """
        classified = {"common": [], "problematic": [], "exceptional": []}

        for pattern_dict in patterns:
            support = pattern_dict["support"]
            pattern = pattern_dict["pattern"]

            # Check if pattern ends in failure state (heuristic: contains 'cancel', 'reject', 'fail')
            last_state = pattern[-1].lower() if pattern else ""
            is_problematic = any(
                word in last_state for word in ["cancel", "reject", "fail", "error"]
            )

            if is_problematic:
                classified["problematic"].append(pattern_dict)
            elif support >= support_threshold_common:
                classified["common"].append(pattern_dict)
            elif support <= support_threshold_exceptional:
                classified["exceptional"].append(pattern_dict)

        return classified

    # ========== State Transition Matrix ==========

    def build_transition_matrix(self, kanban_id: str) -> Dict:
        """
        Build state transition probability matrix

        Args:
            kanban_id: Kanban ID

        Returns:
            Dict with transition probabilities:
            {
                'state1': {
                    'state2': 0.75,
                    'state3': 0.25
                },
                ...
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        # Count transitions
        transition_counts = defaultdict(lambda: defaultdict(int))
        state_counts = defaultdict(int)

        for process in processes:
            history = process.get("history", [])

            for transition in history:
                from_state = transition.get("from_state")
                to_state = transition.get("to_state")

                if from_state and to_state:
                    transition_counts[from_state][to_state] += 1
                    state_counts[from_state] += 1

        # Calculate probabilities
        transition_matrix = {}
        for from_state, targets in transition_counts.items():
            total = state_counts[from_state]
            transition_matrix[from_state] = {
                to_state: round(count / total, 3) for to_state, count in targets.items()
            }

        return transition_matrix

    # ========== Duration Analysis ==========

    def analyze_state_durations(self, kanban_id: str) -> Dict:
        """
        Analyze average duration in each state

        Args:
            kanban_id: Kanban ID

        Returns:
            Dict with state duration statistics:
            {
                'state1': {
                    'avg_hours': 24.5,
                    'min_hours': 1.2,
                    'max_hours': 120.0,
                    'std_dev': 15.3,
                    'sample_count': 45
                },
                ...
            }
        """
        processes = self.repo.get_processes_by_kanban(kanban_id)

        # Collect durations per state
        state_durations = defaultdict(list)

        for process in processes:
            history = process.get("history", [])

            # Calculate time in each state
            for i in range(len(history)):
                transition = history[i]
                from_state = transition.get("from_state")
                timestamp = transition.get("timestamp")

                if not from_state or not timestamp:
                    continue

                # Find next transition or use current time
                if i + 1 < len(history):
                    next_timestamp = history[i + 1].get("timestamp")
                else:
                    # Use current time for current state
                    next_timestamp = datetime.now().isoformat()

                if next_timestamp:
                    try:
                        start = datetime.fromisoformat(timestamp)
                        end = datetime.fromisoformat(next_timestamp)
                        duration_hours = (end - start).total_seconds() / 3600
                        state_durations[from_state].append(duration_hours)
                    except (ValueError, TypeError):
                        pass

        # Calculate statistics
        duration_stats = {}
        for state, durations in state_durations.items():
            if durations:
                duration_stats[state] = {
                    "avg_hours": round(statistics.mean(durations), 2),
                    "min_hours": round(min(durations), 2),
                    "max_hours": round(max(durations), 2),
                    "std_dev": (
                        round(statistics.stdev(durations), 2)
                        if len(durations) > 1
                        else 0.0
                    ),
                    "sample_count": len(durations),
                }

        return duration_stats

    # ========== Process Similarity ==========

    def find_similar_processes(
        self, process_id: str, kanban_id: str, limit: int = 5
    ) -> List[Dict]:
        """
        Find processes with similar transition patterns

        Uses sequence similarity to find comparable processes.

        Args:
            process_id: Target process ID
            kanban_id: Kanban ID
            limit: Maximum number of similar processes to return

        Returns:
            List of similar processes with similarity scores:
            [
                {
                    'process_id': 'proc_456',
                    'similarity': 0.85,
                    'common_transitions': ['state1->state2', ...]
                },
                ...
            ]
        """
        target_process = self.repo.get_process_by_id(process_id)
        if not target_process:
            return []

        all_processes = self.repo.get_processes_by_kanban(kanban_id)

        # Get target sequence
        target_sequence = self._get_process_sequence(target_process)

        # Calculate similarities
        similarities = []
        for process in all_processes:
            if process["process_id"] == process_id:
                continue

            sequence = self._get_process_sequence(process)
            similarity = self._sequence_similarity(target_sequence, sequence)

            if similarity > 0:
                common_transitions = self._get_common_transitions(
                    target_sequence, sequence
                )
                similarities.append(
                    {
                        "process_id": process["process_id"],
                        "similarity": round(similarity, 3),
                        "common_transitions": common_transitions,
                    }
                )

        # Sort by similarity (descending) and limit
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]

    def _get_process_sequence(self, process: Dict) -> List[str]:
        """Extract state sequence from process"""
        sequence = []
        history = process.get("history", [])

        for transition in history:
            from_state = transition.get("from_state")
            to_state = transition.get("to_state")

            if not sequence and from_state:
                sequence.append(from_state)
            if to_state:
                sequence.append(to_state)

        return sequence

    def _sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """
        Calculate similarity between two sequences

        Uses Jaccard similarity on transitions
        """
        if not seq1 or not seq2:
            return 0.0

        # Convert to transitions
        trans1 = set(f"{seq1[i]}->{seq1[i+1]}" for i in range(len(seq1) - 1))
        trans2 = set(f"{seq2[i]}->{seq2[i+1]}" for i in range(len(seq2) - 1))

        if not trans1 or not trans2:
            return 0.0

        # Jaccard similarity
        intersection = len(trans1 & trans2)
        union = len(trans1 | trans2)

        return intersection / union if union > 0 else 0.0

    def _get_common_transitions(self, seq1: List[str], seq2: List[str]) -> List[str]:
        """Get list of common transitions between sequences"""
        trans1 = set(
            f"{seq1[i]}->{seq1[i+1]}" for i in range(len(seq1) - 1) if i + 1 < len(seq1)
        )
        trans2 = set(
            f"{seq2[i]}->{seq2[i+1]}" for i in range(len(seq2) - 1) if i + 1 < len(seq2)
        )

        return sorted(list(trans1 & trans2))
