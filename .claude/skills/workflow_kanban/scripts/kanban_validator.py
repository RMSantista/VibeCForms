#!/usr/bin/env python3
"""
Kanban JSON Validator
Validates kanban definition JSON files for the VibeCForms Workflow system.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class KanbanValidator:
    """Validates kanban JSON structure and business rules."""

    REQUIRED_FIELDS = ["id", "name", "states", "transitions"]
    REQUIRED_STATE_FIELDS = ["id", "name"]
    REQUIRED_TRANSITION_FIELDS = ["from", "to"]
    VALID_TRANSITION_TYPES = ["manual", "system", "agent"]
    VALID_PREREQUISITE_TYPES = [
        "field_check",
        "external_api",
        "time_elapsed",
        "custom_script",
    ]

    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.data: Dict = {}

    def validate(self) -> bool:
        """Run all validations. Returns True if valid, False otherwise."""
        if not self._load_json():
            return False

        self._validate_required_fields()
        self._validate_states()
        self._validate_transitions()
        self._detect_infinite_cycles()

        return len(self.errors) == 0

    def _load_json(self) -> bool:
        """Load and parse JSON file."""
        try:
            if not self.json_path.exists():
                self.errors.append(f"File not found: {self.json_path}")
                return False

            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            return True

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON syntax: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading file: {e}")
            return False

    def _validate_required_fields(self):
        """Validate top-level required fields."""
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                self.errors.append(f"Missing required field: '{field}'")
            elif not self.data[field]:
                self.errors.append(f"Required field '{field}' is empty")

    def _validate_states(self):
        """Validate states array and individual state objects."""
        if "states" not in self.data:
            return

        states = self.data["states"]

        if not isinstance(states, list):
            self.errors.append("Field 'states' must be an array")
            return

        if len(states) == 0:
            self.errors.append("At least one state is required")
            return

        state_ids: Set[str] = set()

        for idx, state in enumerate(states):
            if not isinstance(state, dict):
                self.errors.append(f"State at index {idx} must be an object")
                continue

            # Check required state fields
            for field in self.REQUIRED_STATE_FIELDS:
                if field not in state:
                    self.errors.append(f"State at index {idx}: missing field '{field}'")

            # Check for duplicate state IDs
            state_id = state.get("id")
            if state_id:
                if state_id in state_ids:
                    self.errors.append(f"Duplicate state ID: '{state_id}'")
                state_ids.add(state_id)

            # Validate auto_transition_to if present
            if "auto_transition_to" in state:
                auto_to = state["auto_transition_to"]
                if auto_to and auto_to not in state_ids and auto_to != state_id:
                    # Will validate after all states are collected
                    pass

    def _validate_transitions(self):
        """Validate transitions array and transition rules."""
        if "transitions" not in self.data or "states" not in self.data:
            return

        transitions = self.data["transitions"]

        if not isinstance(transitions, list):
            self.errors.append("Field 'transitions' must be an array")
            return

        # Collect valid state IDs
        valid_state_ids = {
            state["id"] for state in self.data["states"] if "id" in state
        }

        for idx, trans in enumerate(transitions):
            if not isinstance(trans, dict):
                self.errors.append(f"Transition at index {idx} must be an object")
                continue

            # Check required fields
            for field in self.REQUIRED_TRANSITION_FIELDS:
                if field not in trans:
                    self.errors.append(
                        f"Transition at index {idx}: missing field '{field}'"
                    )

            # Validate 'from' state exists
            from_state = trans.get("from")
            if from_state and from_state not in valid_state_ids:
                self.errors.append(
                    f"Transition at index {idx}: 'from' state '{from_state}' does not exist"
                )

            # Validate 'to' state exists
            to_state = trans.get("to")
            if to_state and to_state not in valid_state_ids:
                self.errors.append(
                    f"Transition at index {idx}: 'to' state '{to_state}' does not exist"
                )

            # Validate transition type if present
            trans_type = trans.get("type", "manual")
            if trans_type not in self.VALID_TRANSITION_TYPES:
                self.errors.append(
                    f"Transition at index {idx}: invalid type '{trans_type}'. "
                    f"Valid types: {', '.join(self.VALID_TRANSITION_TYPES)}"
                )

            # Validate prerequisites if present
            if "prerequisites" in trans:
                self._validate_prerequisites(trans["prerequisites"], idx)

    def _validate_prerequisites(self, prerequisites: List, transition_idx: int):
        """Validate prerequisite definitions."""
        if not isinstance(prerequisites, list):
            self.warnings.append(
                f"Transition at index {transition_idx}: 'prerequisites' should be an array"
            )
            return

        for prereq_idx, prereq in enumerate(prerequisites):
            if not isinstance(prereq, dict):
                self.warnings.append(
                    f"Transition {transition_idx}, prerequisite {prereq_idx}: must be an object"
                )
                continue

            prereq_type = prereq.get("type")
            if not prereq_type:
                self.warnings.append(
                    f"Transition {transition_idx}, prerequisite {prereq_idx}: missing 'type' field"
                )
            elif prereq_type not in self.VALID_PREREQUISITE_TYPES:
                self.warnings.append(
                    f"Transition {transition_idx}, prerequisite {prereq_idx}: "
                    f"invalid type '{prereq_type}'. "
                    f"Valid types: {', '.join(self.VALID_PREREQUISITE_TYPES)}"
                )

    def _detect_infinite_cycles(self):
        """Detect potential infinite loops in auto-transitions."""
        if "states" not in self.data:
            return

        # Build auto-transition graph
        auto_graph: Dict[str, str] = {}
        for state in self.data["states"]:
            if "auto_transition_to" in state and state.get("auto_transition_to"):
                state_id = state.get("id")
                auto_to = state["auto_transition_to"]
                if state_id:
                    auto_graph[state_id] = auto_to

        # Detect cycles using Floyd's cycle detection
        for start_state in auto_graph:
            visited: Set[str] = set()
            current = start_state

            while current in auto_graph:
                if current in visited:
                    # Cycle detected
                    cycle_path = [start_state]
                    temp = start_state
                    while auto_graph.get(temp) != start_state:
                        temp = auto_graph.get(temp, "")
                        if temp:
                            cycle_path.append(temp)
                        else:
                            break
                    cycle_path.append(start_state)

                    self.warnings.append(
                        f"Potential infinite auto-transition cycle detected: "
                        f"{' → '.join(cycle_path)}"
                    )
                    break

                visited.add(current)
                current = auto_graph.get(current, "")

    def print_report(self):
        """Print validation report to stdout."""
        print(f"\n{'=' * 70}")
        print(f"Kanban Validation Report")
        print(f"{'=' * 70}")
        print(f"File: {self.json_path}")

        if self.data.get("name"):
            print(f"Kanban Name: {self.data['name']}")
        if self.data.get("id"):
            print(f"Kanban ID: {self.data['id']}")

        print(f"\n{'-' * 70}")

        if not self.errors and not self.warnings:
            print("✅ VALID - No errors or warnings found!")
            print(f"\nSummary:")
            print(f"  States: {len(self.data.get('states', []))}")
            print(f"  Transitions: {len(self.data.get('transitions', []))}")
        else:
            if self.errors:
                print(f"\n❌ ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")

            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")

            print(f"\n{'-' * 70}")
            if self.errors:
                print("❌ VALIDATION FAILED - Please fix errors above")
            else:
                print("✅ VALIDATION PASSED - Review warnings if needed")

        print(f"{'=' * 70}\n")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: kanban_validator.py <kanban_json_file>")
        print("\nExample:")
        print("  python3 kanban_validator.py /path/to/pedidos.json")
        sys.exit(1)

    json_file = sys.argv[1]
    validator = KanbanValidator(json_file)

    is_valid = validator.validate()
    validator.print_report()

    # Exit code: 0 if valid, 1 if errors (warnings allowed)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
