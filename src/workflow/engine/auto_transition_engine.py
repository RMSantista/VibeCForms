"""
Auto-Transition Engine - Progressão Automática de Processos

Monitora processos e executa transições automáticas quando pré-requisitos são atendidos.

Funcionalidades:
- Verifica pré-requisitos de próximo estado
- Executa transição automática seguindo flow_sequence
- Previne loops infinitos
- Registra auditoria de transições automáticas
- Suporta habilitação/desabilitação por Kanban
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path

# Import componentes do workflow
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflow.engine.workflow_manager import WorkflowManager
from workflow.engine.transition_handler import TransitionHandler
from workflow.engine.prerequisite_checker import PrerequisiteChecker
from workflow.engine.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class AutoTransitionEngine:
    """
    Engine de progressão automática de processos.

    Monitora processos e executa transições automáticas quando:
    1. Kanban tem auto-transition habilitado
    2. Existe próximo estado na flow_sequence
    3. Todos pré-requisitos do próximo estado foram atendidos
    """

    def __init__(self, workflow_manager: Optional[WorkflowManager] = None):
        """
        Inicializa AutoTransitionEngine.

        Args:
            workflow_manager: Instância de WorkflowManager (opcional)
        """
        self.workflow_manager = workflow_manager or WorkflowManager()
        self.transition_handler = TransitionHandler(self.workflow_manager)
        self.prerequisite_checker = PrerequisiteChecker()

        # Tracking para prevenir loops infinitos
        self._processing_processes: Set[str] = set()

        logger.info("AutoTransitionEngine initialized")

    def check_and_execute(
        self,
        process_id: str,
        max_transitions: int = 10
    ) -> Dict[str, Any]:
        """
        Verifica e executa transições automáticas para um processo.

        Args:
            process_id: ID do processo
            max_transitions: Máximo de transições automáticas consecutivas

        Returns:
            Resultado do processamento:
            {
                'process_id': str,
                'auto_transition_enabled': bool,
                'transitions_executed': int,
                'current_state': str,
                'can_progress': bool,
                'transitions': [...]  # Lista de transições executadas
            }
        """
        # Previne processamento duplicado
        if process_id in self._processing_processes:
            logger.warning(f"Process {process_id} already being processed, skipping")
            return {
                'process_id': process_id,
                'auto_transition_enabled': False,
                'transitions_executed': 0,
                'error': 'Process already being processed'
            }

        try:
            self._processing_processes.add(process_id)

            # Busca processo
            process = self.workflow_manager.get_process(process_id)
            kanban_name = process['kanban_name']
            current_state = process['current_state']

            # Busca definição do Kanban
            kanban_def = self.workflow_manager.get_kanban(kanban_name)

            # Verifica se auto-transition está habilitado
            auto_enabled = kanban_def.get('agents', {}).get('enabled', False)

            if not auto_enabled:
                return {
                    'process_id': process_id,
                    'kanban_name': kanban_name,
                    'auto_transition_enabled': False,
                    'transitions_executed': 0,
                    'current_state': current_state,
                    'message': 'Auto-transition not enabled for this Kanban'
                }

            # Executa transições automáticas em cadeia
            transitions_executed = []
            transitions_count = 0

            while transitions_count < max_transitions:
                # Verifica se pode progredir
                result = self._can_auto_transition(process_id)

                if not result['can_progress']:
                    break

                # Executa transição
                next_state = result['next_state']

                logger.info(
                    f"Auto-transitioning process {process_id} from "
                    f"{result['current_state']} to {next_state}"
                )

                transition_result = self.transition_handler.execute(
                    process_id=process_id,
                    target_state=next_state,
                    triggered_by='auto',
                    justification='Automatic transition - all prerequisites met'
                )

                transitions_executed.append({
                    'from_state': result['current_state'],
                    'to_state': next_state,
                    'transition_id': transition_result.get('transition_id'),
                    'timestamp': transition_result.get('executed_at')
                })

                transitions_count += 1

                # Atualiza processo
                process = self.workflow_manager.get_process(process_id)
                current_state = process['current_state']

            return {
                'process_id': process_id,
                'kanban_name': kanban_name,
                'auto_transition_enabled': True,
                'transitions_executed': transitions_count,
                'current_state': current_state,
                'can_progress': transitions_count < max_transitions and self._can_auto_transition(process_id)['can_progress'],
                'transitions': transitions_executed
            }

        finally:
            self._processing_processes.discard(process_id)

    def _can_auto_transition(self, process_id: str) -> Dict[str, Any]:
        """
        Verifica se processo pode fazer transição automática.

        Args:
            process_id: ID do processo

        Returns:
            Resultado da verificação:
            {
                'can_progress': bool,
                'current_state': str,
                'next_state': str,
                'reason': str
            }
        """
        # Busca processo
        process = self.workflow_manager.get_process(process_id)
        kanban_name = process['kanban_name']
        current_state = process['current_state']

        # Busca definição do Kanban
        kanban_def = self.workflow_manager.get_kanban(kanban_name)

        # Verifica se tem flow_sequence
        flow_sequence = kanban_def.get('agents', {}).get('flow_sequence', [])
        if not flow_sequence:
            return {
                'can_progress': False,
                'current_state': current_state,
                'reason': 'No flow_sequence defined'
            }

        # Encontra próximo estado
        try:
            current_idx = flow_sequence.index(current_state)
        except ValueError:
            return {
                'can_progress': False,
                'current_state': current_state,
                'reason': f"Current state '{current_state}' not in flow_sequence"
            }

        # Verifica se há próximo estado
        if current_idx + 1 >= len(flow_sequence):
            return {
                'can_progress': False,
                'current_state': current_state,
                'reason': 'Already at final state'
            }

        next_state = flow_sequence[current_idx + 1]

        # Busca definição do próximo estado
        next_state_def = next(
            (s for s in kanban_def['states'] if s['id'] == next_state),
            None
        )

        if not next_state_def:
            return {
                'can_progress': False,
                'current_state': current_state,
                'next_state': next_state,
                'reason': f"Next state '{next_state}' not found in Kanban definition"
            }

        # Verifica pré-requisitos do próximo estado
        prerequisites = next_state_def.get('prerequisites', [])

        if not prerequisites:
            # Sem pré-requisitos, pode progredir
            return {
                'can_progress': True,
                'current_state': current_state,
                'next_state': next_state,
                'reason': 'No prerequisites to check'
            }

        # Checa pré-requisitos
        prereq_result = self.prerequisite_checker.check_prerequisites(
            prerequisites=prerequisites,
            process_data=process,
            target_state=next_state
        )

        # Verifica se TODOS pré-requisitos foram atendidos (inclusive bloqueantes)
        all_met = prereq_result.get('all_met', False)

        if all_met:
            return {
                'can_progress': True,
                'current_state': current_state,
                'next_state': next_state,
                'reason': 'All prerequisites met',
                'prerequisites_status': prereq_result
            }
        else:
            return {
                'can_progress': False,
                'current_state': current_state,
                'next_state': next_state,
                'reason': f"{prereq_result['unmet']} prerequisite(s) not met",
                'prerequisites_status': prereq_result
            }

    def process_kanban(
        self,
        kanban_name: str,
        max_processes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processa todos os processos de um Kanban.

        Args:
            kanban_name: Nome do Kanban
            max_processes: Máximo de processos a processar (None = todos)

        Returns:
            Resultado do processamento:
            {
                'kanban_name': str,
                'processes_checked': int,
                'processes_progressed': int,
                'total_transitions': int,
                'results': [...]
            }
        """
        # Lista processos do Kanban
        processes = self.workflow_manager.list_processes(kanban_name)

        if max_processes:
            processes = processes[:max_processes]

        results = []
        processes_progressed = 0
        total_transitions = 0

        for process in processes:
            process_id = process['id']

            result = self.check_and_execute(process_id)
            results.append(result)

            if result.get('transitions_executed', 0) > 0:
                processes_progressed += 1
                total_transitions += result['transitions_executed']

        return {
            'kanban_name': kanban_name,
            'processes_checked': len(processes),
            'processes_progressed': processes_progressed,
            'total_transitions': total_transitions,
            'results': results
        }

    def process_all_kanbans(self) -> Dict[str, Any]:
        """
        Processa todos os Kanbans do sistema.

        Returns:
            Resultado consolidado do processamento
        """
        # Lista todos os Kanbans
        kanbans = self.workflow_manager.list_kanbans()

        results = []
        total_processes = 0
        total_progressed = 0
        total_transitions = 0

        for kanban_info in kanbans:
            kanban_name = kanban_info['kanban_name']

            # Verifica se tem auto-transition habilitado
            kanban_def = self.workflow_manager.get_kanban(kanban_name)
            auto_enabled = kanban_def.get('agents', {}).get('enabled', False)

            if not auto_enabled:
                continue

            result = self.process_kanban(kanban_name)
            results.append(result)

            total_processes += result['processes_checked']
            total_progressed += result['processes_progressed']
            total_transitions += result['total_transitions']

        return {
            'kanbans_processed': len(results),
            'total_processes_checked': total_processes,
            'total_processes_progressed': total_progressed,
            'total_transitions': total_transitions,
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        }

    def get_eligible_processes(
        self,
        kanban_name: str
    ) -> List[Dict[str, Any]]:
        """
        Lista processos elegíveis para auto-transição em um Kanban.

        Args:
            kanban_name: Nome do Kanban

        Returns:
            Lista de processos que podem progredir automaticamente
        """
        # Lista processos
        processes = self.workflow_manager.list_processes(kanban_name)

        eligible = []

        for process in processes:
            process_id = process['id']

            result = self._can_auto_transition(process_id)

            if result['can_progress']:
                eligible.append({
                    'process_id': process_id,
                    'current_state': result['current_state'],
                    'next_state': result['next_state'],
                    'reason': result['reason'],
                    'form_data': process.get('form_data', {})
                })

        return eligible
