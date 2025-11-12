"""
KanbanEditor - Visual editor for creating and managing kanban definitions

Provides high-level API for:
- Creating new kanbans from scratch
- Editing existing kanban definitions
- Adding/removing states and transitions
- Validating kanban structure
- Exporting kanban to JSON
"""

from typing import Dict, List, Optional, Set
import json
import os
from datetime import datetime


class KanbanEditor:
    """
    Visual editor for kanban workflow definitions

    Supports fluent API for building kanbans programmatically
    and validates structure before saving.
    """

    def __init__(self, kanban_registry):
        """
        Initialize KanbanEditor

        Args:
            kanban_registry: KanbanRegistry instance for loading/saving
        """
        self.registry = kanban_registry
        self.current_kanban = None
        self.validation_errors = []

    # ========== Kanban Creation ==========

    def create_kanban(
        self, kanban_id: str, name: str, description: str = ""
    ) -> "KanbanEditor":
        """
        Start creating a new kanban

        Args:
            kanban_id: Unique kanban identifier
            name: Human-readable kanban name
            description: Optional description

        Returns:
            Self for chaining
        """
        self.current_kanban = {
            "id": kanban_id,
            "name": name,
            "description": description,
            "states": {},
            "initial_state": None,
            "form_mappings": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.validation_errors = []
        return self

    def load_kanban(self, kanban_id: str) -> "KanbanEditor":
        """
        Load existing kanban for editing

        Args:
            kanban_id: Kanban ID to load

        Returns:
            Self for chaining
        """
        kanban = self.registry.get_kanban(kanban_id)

        if not kanban:
            raise ValueError(f"Kanban '{kanban_id}' not found")

        # Convert from registry format (list states) to editor format (dict states)
        self.current_kanban = self._convert_from_registry_format(kanban.copy())
        self.current_kanban["updated_at"] = datetime.now().isoformat()
        self.validation_errors = []
        return self

    # ========== State Management ==========

    def add_state(
        self,
        state_id: str,
        name: str,
        type: str = "intermediate",
        description: str = "",
        color: str = "#3B82F6",
        auto_transition_to: Optional[str] = None,
        timeout_hours: Optional[int] = None,
    ) -> "KanbanEditor":
        """
        Add a new state to the kanban

        Args:
            state_id: Unique state identifier
            name: Human-readable state name
            type: 'initial', 'intermediate', or 'final'
            description: Optional state description
            color: Hex color for visual display
            auto_transition_to: State to auto-transition to
            timeout_hours: Hours before timeout transition

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError(
                "No kanban loaded. Call create_kanban() or load_kanban() first"
            )

        if state_id in self.current_kanban["states"]:
            raise ValueError(f"State '{state_id}' already exists")

        state = {
            "name": name,
            "type": type,
            "description": description,
            "color": color,
            "transitions": [],
            "auto_transition_to": auto_transition_to,
            "timeout_hours": timeout_hours,
        }

        self.current_kanban["states"][state_id] = state

        # Set as initial state if it's the first state or explicitly typed as initial
        if type == "initial" or not self.current_kanban["initial_state"]:
            self.current_kanban["initial_state"] = state_id

        return self

    def remove_state(self, state_id: str, force: bool = False) -> "KanbanEditor":
        """
        Remove a state from the kanban

        Args:
            state_id: State ID to remove
            force: If True, remove even if referenced by transitions

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if state_id not in self.current_kanban["states"]:
            raise ValueError(f"State '{state_id}' not found")

        # Check if state is referenced by transitions
        if not force:
            for s_id, state in self.current_kanban["states"].items():
                if state_id in state.get("transitions", []):
                    raise ValueError(
                        f"Cannot remove state '{state_id}': referenced by transition from '{s_id}'. "
                        f"Use force=True to remove anyway."
                    )

        # Remove state
        del self.current_kanban["states"][state_id]

        # Remove transitions pointing to this state
        for state in self.current_kanban["states"].values():
            if state_id in state.get("transitions", []):
                state["transitions"].remove(state_id)

        # Clear initial_state if removed
        if self.current_kanban.get("initial_state") == state_id:
            # Set to first remaining state
            if self.current_kanban["states"]:
                self.current_kanban["initial_state"] = list(
                    self.current_kanban["states"].keys()
                )[0]
            else:
                self.current_kanban["initial_state"] = None

        return self

    def update_state(
        self,
        state_id: str,
        name: Optional[str] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        auto_transition_to: Optional[str] = None,
        timeout_hours: Optional[int] = None,
    ) -> "KanbanEditor":
        """
        Update state properties

        Args:
            state_id: State ID to update
            name: New name (optional)
            type: New type (optional)
            description: New description (optional)
            color: New color (optional)
            auto_transition_to: New auto_transition target (optional)
            timeout_hours: New timeout (optional)

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if state_id not in self.current_kanban["states"]:
            raise ValueError(f"State '{state_id}' not found")

        state = self.current_kanban["states"][state_id]

        if name is not None:
            state["name"] = name
        if type is not None:
            state["type"] = type
        if description is not None:
            state["description"] = description
        if color is not None:
            state["color"] = color
        if auto_transition_to is not None:
            state["auto_transition_to"] = auto_transition_to
        if timeout_hours is not None:
            state["timeout_hours"] = timeout_hours

        return self

    # ========== Transition Management ==========

    def add_transition(
        self, from_state: str, to_state: str, prerequisites: Optional[List[Dict]] = None
    ) -> "KanbanEditor":
        """
        Add a transition between states

        Args:
            from_state: Source state ID
            to_state: Target state ID
            prerequisites: Optional list of prerequisite checks

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if from_state not in self.current_kanban["states"]:
            raise ValueError(f"Source state '{from_state}' not found")
        if to_state not in self.current_kanban["states"]:
            raise ValueError(f"Target state '{to_state}' not found")

        state = self.current_kanban["states"][from_state]

        if to_state not in state["transitions"]:
            state["transitions"].append(to_state)

        # Store prerequisites in registry format if provided
        if prerequisites:
            # Prerequisites will be stored separately in registry
            # For now, just note that we need to handle this
            pass

        return self

    def remove_transition(self, from_state: str, to_state: str) -> "KanbanEditor":
        """
        Remove a transition

        Args:
            from_state: Source state ID
            to_state: Target state ID

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if from_state not in self.current_kanban["states"]:
            raise ValueError(f"Source state '{from_state}' not found")

        state = self.current_kanban["states"][from_state]

        if to_state in state["transitions"]:
            state["transitions"].remove(to_state)

        return self

    # ========== Form Mappings ==========

    def map_form(self, form_path: str) -> "KanbanEditor":
        """
        Map a form to this kanban

        Args:
            form_path: Form path to map

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if form_path not in self.current_kanban.get("form_mappings", []):
            if "form_mappings" not in self.current_kanban:
                self.current_kanban["form_mappings"] = []
            self.current_kanban["form_mappings"].append(form_path)

        return self

    def unmap_form(self, form_path: str) -> "KanbanEditor":
        """
        Remove form mapping

        Args:
            form_path: Form path to unmap

        Returns:
            Self for chaining
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if form_path in self.current_kanban.get("form_mappings", []):
            self.current_kanban["form_mappings"].remove(form_path)

        return self

    # ========== Validation ==========

    def validate(self) -> bool:
        """
        Validate current kanban structure

        Returns:
            True if valid, False otherwise
            Errors stored in self.validation_errors
        """
        if not self.current_kanban:
            self.validation_errors = ["No kanban loaded"]
            return False

        self.validation_errors = []

        # Check required fields
        if not self.current_kanban.get("id"):
            self.validation_errors.append("Kanban ID is required")
        if not self.current_kanban.get("name"):
            self.validation_errors.append("Kanban name is required")

        # Check states
        if not self.current_kanban.get("states"):
            self.validation_errors.append("Kanban must have at least one state")
        else:
            # Check initial state
            if not self.current_kanban.get("initial_state"):
                self.validation_errors.append("Kanban must have an initial state")
            elif (
                self.current_kanban["initial_state"]
                not in self.current_kanban["states"]
            ):
                self.validation_errors.append(
                    f"Initial state '{self.current_kanban['initial_state']}' not found in states"
                )

            # Validate each state
            for state_id, state in self.current_kanban["states"].items():
                # Check state type
                if state.get("type") not in ["initial", "intermediate", "final"]:
                    self.validation_errors.append(
                        f"State '{state_id}': invalid type '{state.get('type')}'"
                    )

                # Check transitions reference valid states
                for trans_to in state.get("transitions", []):
                    if trans_to not in self.current_kanban["states"]:
                        self.validation_errors.append(
                            f"State '{state_id}': transition to unknown state '{trans_to}'"
                        )

                # Check auto_transition_to references valid state
                auto_to = state.get("auto_transition_to")
                if auto_to and auto_to not in self.current_kanban["states"]:
                    self.validation_errors.append(
                        f"State '{state_id}': auto_transition_to unknown state '{auto_to}'"
                    )

            # Check for unreachable states (except initial)
            reachable = self._find_reachable_states()
            all_states = set(self.current_kanban["states"].keys())
            unreachable = all_states - reachable

            if unreachable:
                self.validation_errors.append(
                    f"Unreachable states detected: {', '.join(unreachable)}"
                )

        return len(self.validation_errors) == 0

    def _find_reachable_states(self) -> Set[str]:
        """Find all states reachable from initial state"""
        if not self.current_kanban or not self.current_kanban.get("initial_state"):
            return set()

        reachable = set()
        to_visit = [self.current_kanban["initial_state"]]

        while to_visit:
            state_id = to_visit.pop()
            if state_id in reachable:
                continue

            reachable.add(state_id)
            state = self.current_kanban["states"].get(state_id, {})

            for trans_to in state.get("transitions", []):
                if trans_to not in reachable:
                    to_visit.append(trans_to)

        return reachable

    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.validation_errors.copy()

    # ========== Export/Save ==========

    def to_dict(self) -> Dict:
        """
        Export current kanban to dictionary

        Returns:
            Kanban definition as dict
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        return self.current_kanban.copy()

    def to_json(self, indent: int = 2) -> str:
        """
        Export current kanban to JSON string

        Args:
            indent: JSON indentation level

        Returns:
            Kanban definition as JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, validate: bool = True) -> bool:
        """
        Save current kanban to registry

        Args:
            validate: If True, validate before saving

        Returns:
            True if saved successfully
        """
        if not self.current_kanban:
            raise ValueError("No kanban loaded")

        if validate and not self.validate():
            raise ValueError(
                f"Kanban validation failed: {', '.join(self.validation_errors)}"
            )

        # Update timestamp
        self.current_kanban["updated_at"] = datetime.now().isoformat()

        # Convert format for registry (dict states → list states)
        registry_format = self._convert_to_registry_format()

        # Register kanban
        kanban_id = self.current_kanban["id"]
        self.registry.register_kanban(registry_format)

        # Update form mappings
        for form_path in self.current_kanban.get("form_mappings", []):
            self.registry.map_form_to_kanban(form_path, kanban_id)

        return True

    def _convert_to_registry_format(self) -> dict:
        """
        Convert internal format (dict states) to registry format (list states)

        Internal format (KanbanEditor):
        {
            "states": {"novo": {"name": "Novo", "transitions": ["concluido"]}}
        }

        Registry format (KanbanRegistry):
        {
            "states": [{"id": "novo", "name": "Novo"}],
            "recommended_transitions": [{"from": "novo", "to": "concluido"}]
        }
        """
        registry_kanban = {
            "id": self.current_kanban["id"],
            "name": self.current_kanban["name"],
            "description": self.current_kanban.get("description", ""),
            "states": [],
            "recommended_transitions": [],
            "initial_state": self.current_kanban.get("initial_state"),
            "created_at": self.current_kanban.get("created_at"),
            "updated_at": self.current_kanban.get("updated_at"),
            "form_mappings": self.current_kanban.get("form_mappings", []),
        }

        # Convert states from dict to list
        for state_id, state_data in self.current_kanban.get("states", {}).items():
            state_entry = {
                "id": state_id,
                "name": state_data["name"],
                "type": state_data.get("type", "intermediate"),
                "description": state_data.get("description", ""),
                "color": state_data.get("color", "#95a5a6"),
            }
            registry_kanban["states"].append(state_entry)

            # Extract transitions
            for target_state in state_data.get("transitions", []):
                transition = {"from": state_id, "to": target_state}
                registry_kanban["recommended_transitions"].append(transition)

        return registry_kanban

    def _convert_from_registry_format(self, kanban_def: dict) -> dict:
        """
        Convert registry format (list states) to internal editor format (dict states)

        Registry format (KanbanRegistry):
        {
            "states": [{"id": "novo", "name": "Novo"}],
            "recommended_transitions": [{"from": "novo", "to": "concluido"}]
        }

        Internal format (KanbanEditor):
        {
            "states": {"novo": {"name": "Novo", "transitions": ["concluido"]}}
        }
        """
        # If already in editor format (states is dict), return as is
        if isinstance(kanban_def.get("states"), dict):
            return kanban_def

        editor_kanban = {
            "id": kanban_def["id"],
            "name": kanban_def["name"],
            "description": kanban_def.get("description", ""),
            "states": {},
            "initial_state": kanban_def.get("initial_state"),
            "created_at": kanban_def.get("created_at"),
            "updated_at": kanban_def.get("updated_at"),
            "form_mappings": kanban_def.get("form_mappings", []),
        }

        # Convert states from list to dict
        for state in kanban_def.get("states", []):
            state_id = state["id"]
            editor_kanban["states"][state_id] = {
                "name": state["name"],
                "type": state.get("type", "intermediate"),
                "description": state.get("description", ""),
                "color": state.get("color", "#95a5a6"),
                "transitions": [],
            }

        # Extract transitions from recommended_transitions
        for transition in kanban_def.get("recommended_transitions", []):
            from_state = transition["from"]
            to_state = transition["to"]
            if from_state in editor_kanban["states"]:
                editor_kanban["states"][from_state]["transitions"].append(to_state)

        return editor_kanban

    def save_to_file(self, file_path: str, validate: bool = True) -> bool:
        """
        Save current kanban to JSON file

        Args:
            file_path: Path to save JSON file
            validate: If True, validate before saving

        Returns:
            True if saved successfully
        """
        if validate and not self.validate():
            raise ValueError(
                f"Kanban validation failed: {', '.join(self.validation_errors)}"
            )

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

        return True

    # ========== Utility Methods ==========

    def get_state_count(self) -> int:
        """Get number of states in current kanban"""
        if not self.current_kanban:
            return 0
        return len(self.current_kanban.get("states", {}))

    def get_transition_count(self) -> int:
        """Get total number of transitions in current kanban"""
        if not self.current_kanban:
            return 0

        count = 0
        for state in self.current_kanban.get("states", {}).values():
            count += len(state.get("transitions", []))
        return count

    def list_states(self) -> List[str]:
        """Get list of all state IDs"""
        if not self.current_kanban:
            return []
        return list(self.current_kanban.get("states", {}).keys())

    def get_state_details(self, state_id: str) -> Optional[Dict]:
        """Get details of a specific state"""
        if not self.current_kanban:
            return None
        return self.current_kanban.get("states", {}).get(state_id)
