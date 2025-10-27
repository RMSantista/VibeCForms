"""
Workflow Repository Layer

Camada de persistência inteligente para workflows.
Estende o BaseRepository existente com operações específicas.
"""

from .workflow_repository import WorkflowRepository

__all__ = ['WorkflowRepository']
