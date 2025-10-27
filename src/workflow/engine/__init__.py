"""
Workflow Engine Layer

Lógica de negócio do sistema de workflows:
- WorkflowManager: CRUD de kanbans e processos
- TransitionHandler: Gerenciamento de transições
- PrerequisiteChecker: Validação de pré-requisitos
- AuditLogger: Sistema de auditoria
- AutoTransitionEngine: Progressão automática
"""

from .workflow_manager import WorkflowManager
from .transition_handler import TransitionHandler
from .prerequisite_checker import PrerequisiteChecker
from .audit_logger import AuditLogger
from .auto_transition_engine import AutoTransitionEngine

__all__ = [
    'WorkflowManager',
    'TransitionHandler',
    'PrerequisiteChecker',
    'AuditLogger',
    'AutoTransitionEngine'
]
