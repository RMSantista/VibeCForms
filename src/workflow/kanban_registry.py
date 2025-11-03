"""
KanbanRegistry - Mapeamento bidirectional Kanban ↔ Forms

Responsabilidades:
- Carregar definições de kanbans de src/config/kanbans/*.json
- Mapear forms para kanbans (N:1 - vários forms podem usar o mesmo kanban)
- Mapear kanbans para forms (1:N - um kanban pode ter vários linked_forms)
- Validar se form está vinculado a kanban
- Get kanban definition by ID ou by form
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path


class KanbanRegistry:
    """
    Registry for Kanban-Form mappings

    Singleton pattern - only one instance should exist in the app
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, kanbans_dir: str = "src/config/kanbans"):
        """
        Initialize KanbanRegistry

        Args:
            kanbans_dir: Directory containing kanban JSON files
        """
        # Only initialize once (singleton)
        if hasattr(self, "_initialized"):
            return

        self.kanbans_dir = kanbans_dir
        self._kanbans: Dict[str, dict] = {}  # kanban_id -> kanban_def
        self._form_to_kanban: Dict[str, str] = {}  # form_path -> kanban_id

        self.load_kanbans()
        self._initialized = True

    # ========== Loading ==========

    def load_kanbans(self) -> None:
        """
        Load all kanban definitions from kanbans_dir

        Scans directory for *.json files and loads them.
        Each kanban must have:
            - id (str)
            - name (str)
            - states (list)
            - transitions (list)
            - linked_forms (list) - forms that trigger this kanban

        Raises:
            FileNotFoundError: If kanbans_dir doesn't exist
            ValueError: If kanban JSON is invalid
        """
        if not os.path.exists(self.kanbans_dir):
            os.makedirs(self.kanbans_dir, exist_ok=True)
            print(f"⚠️  Created kanbans directory: {self.kanbans_dir}")
            return

        json_files = Path(self.kanbans_dir).glob("*.json")

        loaded_count = 0
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    kanban_def = json.load(f)

                # Validate required fields
                self._validate_kanban(kanban_def, json_file.name)

                # Register kanban
                kanban_id = kanban_def["id"]
                self._kanbans[kanban_id] = kanban_def

                # Register form mappings
                linked_forms = kanban_def.get("linked_forms", [])
                for form_path in linked_forms:
                    self._form_to_kanban[form_path] = kanban_id

                loaded_count += 1

            except json.JSONDecodeError as e:
                print(f"❌ Error parsing {json_file.name}: {e}")
                continue
            except ValueError as e:
                print(f"❌ Invalid kanban {json_file.name}: {e}")
                continue

        print(f"✅ Loaded {loaded_count} kanban(s) from {self.kanbans_dir}")

    def reload(self) -> None:
        """
        Reload all kanbans from disk

        Useful when kanbans are modified during runtime
        """
        self._kanbans.clear()
        self._form_to_kanban.clear()
        self.load_kanbans()

    def _validate_kanban(self, kanban_def: dict, filename: str) -> None:
        """
        Validate kanban definition structure

        Args:
            kanban_def: Kanban definition dict
            filename: File name (for error messages)

        Raises:
            ValueError: If validation fails
        """
        # Required fields - "transitions" OR "recommended_transitions" for backward compatibility
        required_fields = ["id", "name", "states"]

        for field in required_fields:
            if field not in kanban_def:
                raise ValueError(f"Missing required field '{field}' in {filename}")

        # Validate states structure
        if not isinstance(kanban_def["states"], list):
            raise ValueError(f"'states' must be a list in {filename}")

        if len(kanban_def["states"]) == 0:
            raise ValueError(f"'states' cannot be empty in {filename}")

        # Validate each state has id and name
        for state in kanban_def["states"]:
            if "id" not in state or "name" not in state:
                raise ValueError(f"Each state must have 'id' and 'name' in {filename}")

        state_ids = [s["id"] for s in kanban_def["states"]]

        # Validate recommended_transitions (optional, for UI/documentation)
        if "recommended_transitions" in kanban_def or "transitions" in kanban_def:
            transitions = kanban_def.get(
                "recommended_transitions", kanban_def.get("transitions", [])
            )
            if not isinstance(transitions, list):
                raise ValueError(
                    f"'recommended_transitions' or 'transitions' must be a list in {filename}"
                )

            for transition in transitions:
                if "from" not in transition or "to" not in transition:
                    raise ValueError(
                        f"Each transition must have 'from' and 'to' in {filename}"
                    )

                # Check that from/to states exist
                if transition["from"] not in state_ids:
                    raise ValueError(
                        f"Transition 'from' state '{transition['from']}' not found in {filename}"
                    )
                if transition["to"] not in state_ids:
                    raise ValueError(
                        f"Transition 'to' state '{transition['to']}' not found in {filename}"
                    )

        # Validate blocked_transitions (optional, for restrictions)
        if "blocked_transitions" in kanban_def:
            if not isinstance(kanban_def["blocked_transitions"], list):
                raise ValueError(f"'blocked_transitions' must be a list in {filename}")

            for transition in kanban_def["blocked_transitions"]:
                if "from" not in transition or "to" not in transition:
                    raise ValueError(
                        f"Each blocked transition must have 'from' and 'to' in {filename}"
                    )

                # Check that from/to states exist
                if transition["from"] not in state_ids:
                    raise ValueError(
                        f"Blocked transition 'from' state '{transition['from']}' not found in {filename}"
                    )
                if transition["to"] not in state_ids:
                    raise ValueError(
                        f"Blocked transition 'to' state '{transition['to']}' not found in {filename}"
                    )

        # Validate warned_transitions (optional, for abnormal flows)
        if "warned_transitions" in kanban_def:
            if not isinstance(kanban_def["warned_transitions"], list):
                raise ValueError(f"'warned_transitions' must be a list in {filename}")

            for transition in kanban_def["warned_transitions"]:
                if "from" not in transition or "to" not in transition:
                    raise ValueError(
                        f"Each warned transition must have 'from' and 'to' in {filename}"
                    )

                # Check that from/to states exist
                if transition["from"] not in state_ids:
                    raise ValueError(
                        f"Warned transition 'from' state '{transition['from']}' not found in {filename}"
                    )
                if transition["to"] not in state_ids:
                    raise ValueError(
                        f"Warned transition 'to' state '{transition['to']}' not found in {filename}"
                    )

        # Validate linked_forms if present
        if "linked_forms" in kanban_def:
            if not isinstance(kanban_def["linked_forms"], list):
                raise ValueError(f"'linked_forms' must be a list in {filename}")

    # ========== Queries ==========

    def get_kanban(self, kanban_id: str) -> Optional[dict]:
        """
        Get kanban definition by ID

        Args:
            kanban_id: Kanban ID to retrieve

        Returns:
            Kanban definition dict or None if not found
        """
        return self._kanbans.get(kanban_id)

    def get_kanban_by_form(self, form_path: str) -> Optional[dict]:
        """
        Get kanban definition linked to a form

        Args:
            form_path: Form path (e.g., "pedidos", "financeiro/contas")

        Returns:
            Kanban definition dict or None if form not linked
        """
        kanban_id = self._form_to_kanban.get(form_path)
        if kanban_id:
            return self.get_kanban(kanban_id)
        return None

    def get_all_kanbans(self) -> Dict[str, dict]:
        """
        Get all kanban definitions

        Returns:
            Dict mapping kanban_id -> kanban_def
        """
        return self._kanbans.copy()

    def get_linked_forms(self, kanban_id: str) -> List[str]:
        """
        Get all forms linked to a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            List of form paths
        """
        kanban = self.get_kanban(kanban_id)
        if kanban:
            return kanban.get("linked_forms", [])
        return []

    def is_form_linked(self, form_path: str) -> bool:
        """
        Check if a form is linked to any kanban

        Args:
            form_path: Form path to check

        Returns:
            True if form is linked to a kanban
        """
        return form_path in self._form_to_kanban

    def get_kanban_id_for_form(self, form_path: str) -> Optional[str]:
        """
        Get kanban ID for a form

        Args:
            form_path: Form path

        Returns:
            Kanban ID or None if not linked
        """
        return self._form_to_kanban.get(form_path)

    # ========== State Queries ==========

    def get_states(self, kanban_id: str) -> List[dict]:
        """
        Get all states for a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            List of state dicts
        """
        kanban = self.get_kanban(kanban_id)
        if kanban:
            return kanban.get("states", [])
        return []

    def get_initial_state(self, kanban_id: str) -> Optional[dict]:
        """
        Get initial state for a kanban

        Args:
            kanban_id: Kanban ID

        Returns:
            Initial state dict or None
        """
        states = self.get_states(kanban_id)
        for state in states:
            if state.get("is_initial", False):
                return state
        # Fallback to first state if no explicit initial state
        return states[0] if states else None

    def get_state(self, kanban_id: str, state_id: str) -> Optional[dict]:
        """
        Get a specific state by ID

        Args:
            kanban_id: Kanban ID
            state_id: State ID

        Returns:
            State dict or None
        """
        states = self.get_states(kanban_id)
        for state in states:
            if state.get("id") == state_id:
                return state
        return None

    # ========== Transition Queries ==========

    def get_transitions(self, kanban_id: str) -> List[dict]:
        """
        Get all RECOMMENDED transitions for a kanban (for UI/documentation)

        Args:
            kanban_id: Kanban ID

        Returns:
            List of recommended transition dicts
        """
        kanban = self.get_kanban(kanban_id)
        if kanban:
            # Support both old "transitions" and new "recommended_transitions"
            return kanban.get("recommended_transitions", kanban.get("transitions", []))
        return []

    def get_available_transitions(
        self, kanban_id: str, current_state: str
    ) -> List[dict]:
        """
        Get available transitions from a current state

        Args:
            kanban_id: Kanban ID
            current_state: Current state ID

        Returns:
            List of transition dicts where from=current_state
        """
        transitions = self.get_transitions(kanban_id)
        return [t for t in transitions if t.get("from") == current_state]

    def can_transition(self, kanban_id: str, from_state: str, to_state: str) -> bool:
        """
        Check if a transition is allowed

        IMPORTANT: Following VibeCForms philosophy, ALL transitions are allowed by default.
        Only explicitly BLOCKED transitions are forbidden.

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            True if transition is allowed (default), False only if explicitly blocked
        """
        # Check if transition is explicitly blocked
        return not self.is_transition_blocked(kanban_id, from_state, to_state)

    def get_transition(
        self, kanban_id: str, from_state: str, to_state: str
    ) -> Optional[dict]:
        """
        Get specific RECOMMENDED transition definition

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            Recommended transition dict or None if not found
        """
        transitions = self.get_transitions(kanban_id)
        for t in transitions:
            if t.get("from") == from_state and t.get("to") == to_state:
                return t
        return None

    def is_transition_blocked(
        self, kanban_id: str, from_state: str, to_state: str
    ) -> bool:
        """
        Check if a transition is explicitly BLOCKED

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            True if transition is blocked, False otherwise
        """
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return False

        blocked_transitions = kanban.get("blocked_transitions", [])
        for t in blocked_transitions:
            if t.get("from") == from_state and t.get("to") == to_state:
                return True
        return False

    def get_blocked_transition(
        self, kanban_id: str, from_state: str, to_state: str
    ) -> Optional[dict]:
        """
        Get blocked transition definition (includes reason)

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            Blocked transition dict or None if not blocked
        """
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return None

        blocked_transitions = kanban.get("blocked_transitions", [])
        for t in blocked_transitions:
            if t.get("from") == from_state and t.get("to") == to_state:
                return t
        return None

    def is_transition_warned(
        self, kanban_id: str, from_state: str, to_state: str
    ) -> bool:
        """
        Check if a transition should show a warning (abnormal flow)

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            True if transition should warn user, False otherwise
        """
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return False

        warned_transitions = kanban.get("warned_transitions", [])
        for t in warned_transitions:
            if t.get("from") == from_state and t.get("to") == to_state:
                return True
        return False

    def get_warned_transition(
        self, kanban_id: str, from_state: str, to_state: str
    ) -> Optional[dict]:
        """
        Get warned transition definition (includes warning message and justification requirement)

        Args:
            kanban_id: Kanban ID
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            Warned transition dict or None if no warning
        """
        kanban = self.get_kanban(kanban_id)
        if not kanban:
            return None

        warned_transitions = kanban.get("warned_transitions", [])
        for t in warned_transitions:
            if t.get("from") == from_state and t.get("to") == to_state:
                return t
        return None

    # ========== Registry Management ==========

    def register_kanban(self, kanban_def: dict, save_to_disk: bool = True) -> bool:
        """
        Programmatically register a kanban (e.g., from Visual Editor)

        Args:
            kanban_def: Kanban definition dict
            save_to_disk: If True, save to JSON file

        Returns:
            True if registered successfully

        Raises:
            ValueError: If validation fails
        """
        # Validate
        self._validate_kanban(kanban_def, "programmatic")

        kanban_id = kanban_def["id"]

        # Register in memory
        self._kanbans[kanban_id] = kanban_def

        # Update form mappings
        linked_forms = kanban_def.get("linked_forms", [])
        for form_path in linked_forms:
            self._form_to_kanban[form_path] = kanban_id

        # Save to disk if requested
        if save_to_disk:
            os.makedirs(self.kanbans_dir, exist_ok=True)
            file_path = os.path.join(self.kanbans_dir, f"{kanban_id}.json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(kanban_def, f, indent=2, ensure_ascii=False)

            print(f"✅ Saved kanban '{kanban_id}' to {file_path}")

        return True

    def unregister_kanban(self, kanban_id: str, delete_from_disk: bool = False) -> bool:
        """
        Remove a kanban from registry

        Args:
            kanban_id: Kanban ID to remove
            delete_from_disk: If True, delete JSON file

        Returns:
            True if removed successfully
        """
        if kanban_id not in self._kanbans:
            return False

        # Remove form mappings
        linked_forms = self.get_linked_forms(kanban_id)
        for form_path in linked_forms:
            if form_path in self._form_to_kanban:
                del self._form_to_kanban[form_path]

        # Remove from registry
        del self._kanbans[kanban_id]

        # Delete file if requested
        if delete_from_disk:
            file_path = os.path.join(self.kanbans_dir, f"{kanban_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️  Deleted kanban file {file_path}")

        return True

    # ========== Debugging ==========

    def print_registry(self) -> None:
        """Print registry contents (for debugging)"""
        print("\n" + "=" * 60)
        print("KANBAN REGISTRY")
        print("=" * 60)

        print(f"\n📊 Total Kanbans: {len(self._kanbans)}")
        print(f"📝 Total Form Mappings: {len(self._form_to_kanban)}")

        print("\n🔹 KANBANS:")
        for kanban_id, kanban_def in self._kanbans.items():
            print(f"  - {kanban_id}: {kanban_def.get('name')}")
            print(f"    States: {len(kanban_def.get('states', []))}")
            print(f"    Transitions: {len(kanban_def.get('transitions', []))}")
            print(f"    Linked Forms: {kanban_def.get('linked_forms', [])}")

        print("\n🔹 FORM → KANBAN MAPPINGS:")
        for form_path, kanban_id in self._form_to_kanban.items():
            print(f"  - {form_path} → {kanban_id}")

        print("=" * 60 + "\n")


# ========== Singleton Access ==========


def get_registry(kanbans_dir: str = "src/config/kanbans") -> KanbanRegistry:
    """
    Get singleton KanbanRegistry instance

    Args:
        kanbans_dir: Directory containing kanban JSON files

    Returns:
        KanbanRegistry instance
    """
    return KanbanRegistry(kanbans_dir=kanbans_dir)
