"""
Schema change detection for VibeCForms persistence layer.

This module detects changes in form specifications and backend configurations,
enabling automatic migrations with user confirmation when needed.
"""

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of schema changes."""
    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"
    RENAME_FIELD = "rename_field"
    CHANGE_TYPE = "change_type"
    CHANGE_REQUIRED = "change_required"
    BACKEND_CHANGE = "backend_change"


@dataclass
class FieldChange:
    """Represents a change to a single field."""
    change_type: ChangeType
    field_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    requires_confirmation: bool = False
    data_loss_risk: bool = False
    details: str = ""


@dataclass
class SchemaChange:
    """Represents a complete schema change with all field modifications."""
    form_path: str
    changes: List[FieldChange] = field(default_factory=list)
    has_data: bool = False
    requires_confirmation: bool = False

    def add_change(self, change: FieldChange):
        """Add a field change to this schema change."""
        self.changes.append(change)
        if change.requires_confirmation:
            self.requires_confirmation = True

    def get_summary(self) -> Dict[str, int]:
        """Get summary counts of changes by type."""
        summary = {}
        for change in self.changes:
            change_type = change.change_type.value
            summary[change_type] = summary.get(change_type, 0) + 1
        return summary

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.changes) > 0


@dataclass
class BackendChange:
    """Represents a change in persistence backend."""
    form_path: str
    old_backend: str
    new_backend: str
    has_data: bool = False
    record_count: int = 0
    requires_confirmation: bool = True

    def get_description(self) -> str:
        """Get human-readable description of the backend change."""
        desc = f"Backend mudou de '{self.old_backend}' para '{self.new_backend}'"
        if self.has_data:
            desc += f" ({self.record_count} registros existentes)"
        return desc


class SchemaChangeDetector:
    """
    Detects and analyzes changes in form specifications and backend configurations.

    This class compares old and new specifications to identify:
    - Added fields
    - Removed fields
    - Renamed fields (by analyzing field positions and types)
    - Changed field types
    - Changed required status
    - Backend changes
    """

    @staticmethod
    def compute_spec_hash(spec: Dict[str, Any]) -> str:
        """
        Compute MD5 hash of a spec for quick comparison.

        Args:
            spec: Form specification dictionary

        Returns:
            MD5 hash of the spec's fields
        """
        # Only hash the fields, not title or other metadata
        fields_json = json.dumps(spec.get("fields", []), sort_keys=True)
        return hashlib.md5(fields_json.encode()).hexdigest()

    @staticmethod
    def detect_changes(
        form_path: str,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any],
        has_data: bool = False
    ) -> SchemaChange:
        """
        Detect all changes between two specifications.

        Args:
            form_path: Path to the form
            old_spec: Previous specification
            new_spec: New specification
            has_data: Whether the form has existing data

        Returns:
            SchemaChange object with all detected changes
        """
        schema_change = SchemaChange(form_path=form_path, has_data=has_data)

        old_fields = {f["name"]: f for f in old_spec.get("fields", [])}
        new_fields = {f["name"]: f for f in new_spec.get("fields", [])}

        old_names = set(old_fields.keys())
        new_names = set(new_fields.keys())

        # Detect added fields
        added = new_names - old_names
        for name in added:
            change = FieldChange(
                change_type=ChangeType.ADD_FIELD,
                field_name=name,
                new_value=new_fields[name],
                requires_confirmation=False,
                data_loss_risk=False,
                details=f"Campo '{name}' foi adicionado"
            )
            schema_change.add_change(change)

        # Detect removed fields
        removed = old_names - new_names
        for name in removed:
            change = FieldChange(
                change_type=ChangeType.REMOVE_FIELD,
                field_name=name,
                old_value=old_fields[name],
                requires_confirmation=has_data,
                data_loss_risk=has_data,
                details=f"Campo '{name}' será removido" +
                       (" (DADOS SERÃO PERDIDOS!)" if has_data else "")
            )
            schema_change.add_change(change)

        # Detect changed fields (same name, different properties)
        common = old_names & new_names
        for name in common:
            old_field = old_fields[name]
            new_field = new_fields[name]

            # Check type change
            if old_field.get("type") != new_field.get("type"):
                change = FieldChange(
                    change_type=ChangeType.CHANGE_TYPE,
                    field_name=name,
                    old_value=old_field.get("type"),
                    new_value=new_field.get("type"),
                    requires_confirmation=has_data,
                    data_loss_risk=not SchemaChangeDetector._is_type_compatible(
                        old_field.get("type"), new_field.get("type")
                    ),
                    details=f"Campo '{name}': tipo mudou de '{old_field.get('type')}' "
                           f"para '{new_field.get('type')}'"
                )
                schema_change.add_change(change)

            # Check required change
            old_required = old_field.get("required", False)
            new_required = new_field.get("required", False)
            if old_required != new_required:
                change = FieldChange(
                    change_type=ChangeType.CHANGE_REQUIRED,
                    field_name=name,
                    old_value=old_required,
                    new_value=new_required,
                    requires_confirmation=has_data and new_required and not old_required,
                    data_loss_risk=False,
                    details=f"Campo '{name}': obrigatoriedade mudou de "
                           f"{old_required} para {new_required}"
                )
                schema_change.add_change(change)

        # Try to detect renames (heuristic based on position and type)
        if removed and added:
            renames = SchemaChangeDetector._detect_renames(
                old_spec, new_spec, removed, added
            )
            for old_name, new_name in renames:
                # Remove the ADD and REMOVE changes for these fields
                schema_change.changes = [
                    c for c in schema_change.changes
                    if not (c.field_name in [old_name, new_name] and
                           c.change_type in [ChangeType.ADD_FIELD, ChangeType.REMOVE_FIELD])
                ]

                # Add a RENAME change instead
                change = FieldChange(
                    change_type=ChangeType.RENAME_FIELD,
                    field_name=old_name,
                    old_value=old_name,
                    new_value=new_name,
                    requires_confirmation=has_data,
                    data_loss_risk=False,
                    details=f"Campo '{old_name}' será renomeado para '{new_name}'"
                )
                schema_change.add_change(change)

        return schema_change

    @staticmethod
    def _detect_renames(
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any],
        removed: set,
        added: set
    ) -> List[Tuple[str, str]]:
        """
        Heuristically detect field renames.

        Looks for removed and added fields in the same position with the same type.

        Returns:
            List of tuples (old_name, new_name)
        """
        renames = []
        old_fields = old_spec.get("fields", [])
        new_fields = new_spec.get("fields", [])

        # Create position maps
        old_positions = {f["name"]: i for i, f in enumerate(old_fields)}
        new_positions = {f["name"]: i for i, f in enumerate(new_fields)}

        for old_name in removed:
            old_idx = old_positions.get(old_name)
            if old_idx is None:
                continue

            old_field = old_fields[old_idx]
            old_type = old_field.get("type")

            # Look for added field at same position with same type
            for new_name in added:
                new_idx = new_positions.get(new_name)
                if new_idx != old_idx:
                    continue

                new_field = new_fields[new_idx]
                new_type = new_field.get("type")

                if old_type == new_type:
                    renames.append((old_name, new_name))
                    break

        return renames

    @staticmethod
    def _is_type_compatible(old_type: str, new_type: str) -> bool:
        """
        Check if two field types are compatible for automatic conversion.

        Args:
            old_type: Original field type
            new_type: New field type

        Returns:
            True if types are compatible, False if data loss is likely
        """
        # Text types are generally compatible with each other
        text_types = {"text", "tel", "email", "url", "search", "textarea", "password"}
        if old_type in text_types and new_type in text_types:
            return True

        # Number types
        number_types = {"number", "range"}
        if old_type in number_types and new_type in number_types:
            return True

        # Date/time types
        datetime_types = {"date", "time", "datetime-local", "month", "week"}
        if old_type in datetime_types and new_type in datetime_types:
            return True

        # Text to anything is usually safe (can always convert back to string)
        if old_type in text_types:
            return True

        # Other conversions may lose data
        return False

    @staticmethod
    def requires_confirmation(schema_change: SchemaChange) -> bool:
        """
        Check if a schema change requires user confirmation.

        Args:
            schema_change: The schema change to check

        Returns:
            True if confirmation is needed
        """
        if not schema_change.has_data:
            return False

        return schema_change.requires_confirmation

    @staticmethod
    def detect_backend_change(
        form_path: str,
        old_backend: str,
        new_backend: str,
        record_count: int = 0
    ) -> Optional[BackendChange]:
        """
        Detect a change in persistence backend.

        Args:
            form_path: Path to the form
            old_backend: Previous backend type
            new_backend: Current backend type
            record_count: Number of existing records

        Returns:
            BackendChange object if backend changed, None otherwise
        """
        if old_backend == new_backend:
            return None

        has_data = record_count > 0

        backend_change = BackendChange(
            form_path=form_path,
            old_backend=old_backend,
            new_backend=new_backend,
            has_data=has_data,
            record_count=record_count,
            requires_confirmation=has_data
        )

        logger.info(f"Backend change detected for '{form_path}': {old_backend} -> {new_backend}")
        if has_data:
            logger.warning(f"Form has {record_count} existing records, migration required")

        return backend_change

    @staticmethod
    def get_confirmation_message(schema_change: SchemaChange) -> str:
        """
        Generate a user-friendly confirmation message for a schema change.

        Args:
            schema_change: The schema change

        Returns:
            Human-readable confirmation message
        """
        if not schema_change.has_changes():
            return "Nenhuma alteração detectada."

        summary = schema_change.get_summary()
        lines = [f"Alterações detectadas no formulário '{schema_change.form_path}':"]

        if summary.get("add_field", 0) > 0:
            lines.append(f"  • {summary['add_field']} campo(s) adicionado(s)")

        if summary.get("remove_field", 0) > 0:
            lines.append(f"  • {summary['remove_field']} campo(s) removido(s) ⚠️")

        if summary.get("rename_field", 0) > 0:
            lines.append(f"  • {summary['rename_field']} campo(s) renomeado(s)")

        if summary.get("change_type", 0) > 0:
            lines.append(f"  • {summary['change_type']} campo(s) com tipo alterado")

        if schema_change.has_data:
            lines.append("\n⚠️ O formulário possui dados existentes.")

            has_data_loss = any(c.data_loss_risk for c in schema_change.changes)
            if has_data_loss:
                lines.append("🔴 ATENÇÃO: Algumas alterações podem causar PERDA DE DADOS!")

        lines.append("\nDeseja continuar?")
        return "\n".join(lines)

    @staticmethod
    def get_backend_confirmation_message(backend_change: BackendChange) -> str:
        """
        Generate a user-friendly confirmation message for a backend change.

        Args:
            backend_change: The backend change

        Returns:
            Human-readable confirmation message
        """
        lines = [
            f"Mudança de backend detectada no formulário '{backend_change.form_path}':",
            f"  • Origem: {backend_change.old_backend}",
            f"  • Destino: {backend_change.new_backend}"
        ]

        if backend_change.has_data:
            lines.append(f"\n⚠️ O formulário possui {backend_change.record_count} registro(s) existente(s).")
            lines.append("Os dados serão migrados automaticamente para o novo backend.")
            lines.append("\n✅ Um backup será criado antes da migração.")

        lines.append("\nDeseja continuar com a migração?")
        return "\n".join(lines)
