"""
Transition Handler - Gerenciamento de Transições de Estado

Gerencia transições entre estados do workflow seguindo a filosofia "Avisar, Não Bloquear".

IMPORTANTE: Este handler NUNCA bloqueia transições.
Sempre executa a transição, mesmo que pré-requisitos não estejam atendidos.
Apenas reporta avisos e erros para o usuário.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import WorkflowManager e PrerequisiteChecker
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflow.engine.workflow_manager import WorkflowManager
from workflow.engine.prerequisite_checker import PrerequisiteChecker
from workflow.repository.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class TransitionHandler:
    """
    Gerencia transições de estado em processos de workflow.

    Filosofia: "Avisar, Não Bloquear"
    - handle() detecta problemas mas NÃO bloqueia
    - execute() SEMPRE executa transição
    - Todas as transições são auditadas
    """

    def __init__(self, workflow_manager: Optional[WorkflowManager] = None):
        """
        Inicializa TransitionHandler.

        Args:
            workflow_manager: Instância de WorkflowManager (opcional)
        """
        self.workflow_manager = workflow_manager or WorkflowManager()
        self.prerequisite_checker = PrerequisiteChecker()

        logger.info("TransitionHandler initialized")

    def handle(
        self,
        process_id: str,
        target_state: str,
        triggered_by: str = 'user',
        justification: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Valida e prepara transição (SEM executá-la).

        Args:
            process_id: ID do processo
            target_state: Estado de destino
            triggered_by: Quem disparou ('user', 'auto', 'system')
            justification: Justificativa da transição
            force: Se True, ignora avisos de pré-requisitos

        Returns:
            Dicionário com informações da transição:
            {
                'can_proceed': bool,  # SEMPRE True (filosofia "Avisar, Não Bloquear")
                'process_id': str,
                'current_state': str,
                'target_state': str,
                'transition_valid': bool,  # Estado alvo existe?
                'prerequisites': {...},     # Resultado do PrerequisiteChecker
                'warnings': [str],
                'errors': [str],
                'force': bool
            }
        """
        # Busca processo
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']
        current_state = process['current_state']

        # Busca definição do Kanban
        kanban_def = self.workflow_manager.get_kanban(kanban_name)

        # Valida que estado alvo existe
        valid_states = [s['id'] for s in kanban_def['states']]
        transition_valid = target_state in valid_states

        warnings = []
        errors = []
        prerequisites_result = None

        if not transition_valid:
            errors.append(f"Estado '{target_state}' não existe no Kanban '{kanban_name}'")

        if transition_valid:
            # Busca definição do estado alvo
            target_state_def = next(
                (s for s in kanban_def['states'] if s['id'] == target_state),
                None
            )

            # Valida pré-requisitos
            if target_state_def and 'prerequisites' in target_state_def:
                prerequisites_result = self.prerequisite_checker.check_prerequisites(
                    prerequisites=target_state_def['prerequisites'],
                    process_data=process,
                    target_state=target_state
                )

                # Coleta avisos e erros dos pré-requisitos
                if not force:
                    warnings.extend(prerequisites_result.get('warnings', []))
                    errors.extend(prerequisites_result.get('errors', []))

        # IMPORTANTE: SEMPRE pode prosseguir (filosofia "Avisar, Não Bloquear")
        return {
            'can_proceed': True,  # SEMPRE True!
            'process_id': process_id,
            'current_state': current_state,
            'target_state': target_state,
            'transition_valid': transition_valid,
            'prerequisites': prerequisites_result,
            'warnings': warnings,
            'errors': errors,
            'force': force,
            'checked_at': datetime.utcnow().isoformat()
        }

    def execute(
        self,
        process_id: str,
        target_state: str,
        triggered_by: str = 'user',
        justification: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Executa transição de estado.

        IMPORTANTE: Esta função SEMPRE executa a transição,
        mesmo que pré-requisitos não estejam atendidos.

        Args:
            process_id: ID do processo
            target_state: Estado de destino
            triggered_by: Quem disparou ('user', 'auto', 'system')
            justification: Justificativa da transição
            metadata: Metadados adicionais da transição
            force: Se True, ignora avisos

        Returns:
            Dicionário com resultado da transição

        Raises:
            ValueError: Apenas se processo não existe ou estado alvo inválido
        """
        # Primeiro valida (mas não bloqueia)
        validation = self.handle(process_id, target_state, triggered_by, justification, force)

        # Se estado alvo inválido, lança exceção
        if not validation['transition_valid']:
            raise ValueError(f"Invalid target state '{target_state}'")

        # Busca processo
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']
        current_state = process['current_state']

        # Cria repositório para transições
        transitions_repo = WorkflowRepository(kanban_name, 'transitions')

        # Prepara status de pré-requisitos
        prereq_validation = validation.get('prerequisites')
        prerequisites_status = None
        if prereq_validation and prereq_validation.get('results'):
            prerequisites_status = {
                r['id']: r['met']
                for r in prereq_validation['results']
            }

        # Determina se há anomalia (bloqueantes não atendidos)
        was_anomaly = False
        anomaly_reason = None
        if prereq_validation and prereq_validation.get('blocking_count', 0) > 0:
            was_anomaly = True
            anomaly_reason = f"{prereq_validation['blocking_count']} blocking prerequisite(s) unmet"
            if force:
                anomaly_reason += " (forced transition)"

        # Loga transição
        transition_id = transitions_repo.log_transition(
            process_id=process_id,
            from_state=current_state,
            to_state=target_state,
            triggered_by=triggered_by,
            justification=justification,
            prerequisites_status=prerequisites_status,
            was_anomaly=was_anomaly,
            anomaly_reason=anomaly_reason
        )

        # Executa mudança de estado no processo
        processes_repo = WorkflowRepository(kanban_name, 'processes')
        updated_process = processes_repo.change_state(
            process_id=process_id,
            new_state=target_state,
            justification=justification
        )

        logger.info(
            f"Transition executed: {process_id} {current_state} -> {target_state} "
            f"(triggered_by={triggered_by}, force={force})"
        )

        return {
            'success': True,
            'transition_id': transition_id,
            'process_id': process_id,
            'previous_state': current_state,
            'current_state': target_state,
            'triggered_by': triggered_by,
            'validation': validation,
            'executed_at': datetime.utcnow().isoformat()
        }

    def get_available_transitions(
        self,
        process_id: str
    ) -> List[Dict[str, Any]]:
        """
        Lista transições disponíveis para um processo.

        Args:
            process_id: ID do processo

        Returns:
            Lista de estados possíveis com informações de pré-requisitos
        """
        # Busca processo
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']
        current_state = process['current_state']

        # Busca definição do Kanban
        kanban_def = self.workflow_manager.get_kanban(kanban_name)

        available = []

        # Para cada estado do Kanban
        for state_def in kanban_def['states']:
            state_id = state_def['id']

            # Pula estado atual
            if state_id == current_state:
                continue

            # Valida pré-requisitos
            prerequisites_result = None
            if 'prerequisites' in state_def:
                prerequisites_result = self.prerequisite_checker.check_prerequisites(
                    prerequisites=state_def['prerequisites'],
                    process_data=process,
                    target_state=state_id
                )

            available.append({
                'state_id': state_id,
                'state_name': state_def['name'],
                'state_order': state_def.get('order', 0),
                'state_color': state_def.get('color'),
                'state_icon': state_def.get('icon'),
                'prerequisites': prerequisites_result,
                'all_prerequisites_met': (
                    prerequisites_result.get('all_met', True)
                    if prerequisites_result
                    else True
                ),
                'blocking_prerequisites_unmet': (
                    prerequisites_result.get('blocking_count', 0)
                    if prerequisites_result
                    else 0
                )
            })

        # Ordena por order
        available.sort(key=lambda s: s['state_order'])

        return available

    def get_transition_history(
        self,
        process_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca histórico de transições de um processo.

        Args:
            process_id: ID do processo
            limit: Limitar quantidade de resultados

        Returns:
            Lista de transições (mais recente primeiro)
        """
        # Busca processo para obter kanban_name
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']

        # Busca histórico
        transitions_repo = WorkflowRepository(kanban_name, 'transitions')
        history = transitions_repo.get_transition_history(process_id)

        # Aplica limite
        if limit:
            history = history[:limit]

        return history

    def get_next_auto_state(
        self,
        process_id: str
    ) -> Optional[str]:
        """
        Identifica próximo estado na sequência automática.

        Args:
            process_id: ID do processo

        Returns:
            ID do próximo estado ou None se não há sequência
        """
        # Busca processo
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']
        current_state = process['current_state']

        # Busca definição do Kanban
        kanban_def = self.workflow_manager.get_kanban(kanban_name)

        # Verifica se tem flow_sequence definido
        flow_sequence = kanban_def.get('agents', {}).get('flow_sequence', [])
        if not flow_sequence:
            return None

        # Encontra estado atual na sequência
        try:
            current_idx = flow_sequence.index(current_state)
        except ValueError:
            # Estado atual não está na sequência
            return None

        # Verifica se há próximo estado
        if current_idx + 1 < len(flow_sequence):
            return flow_sequence[current_idx + 1]

        return None
