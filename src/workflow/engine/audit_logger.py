"""
Audit Logger - Sistema de Auditoria de Workflows

Registra e consulta logs de auditoria para todas as operações do workflow:
- Transições de estado
- CRUD de processos
- CRUD de kanbans
- Ações customizadas

Prover queries avançadas e métricas de auditoria.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Import WorkflowRepository
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflow.repository.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Sistema de auditoria para workflows.

    Responsabilidades:
    - Registrar ações e eventos do workflow
    - Consolidar logs de transições e ações
    - Prover queries avançadas de auditoria
    - Calcular métricas e estatísticas
    """

    # Tipos de ação reconhecidos
    ACTION_TYPES = {
        # Transições
        'transition',
        # CRUD de Processos
        'process_created',
        'process_updated',
        'process_deleted',
        # CRUD de Kanbans
        'kanban_created',
        'kanban_updated',
        'kanban_deleted',
        # Outras ações
        'comment_added',
        'attachment_added',
        'assignment_changed',
        'custom_action'
    }

    def __init__(self, kanban_name: str):
        """
        Inicializa AuditLogger para um Kanban específico.

        Args:
            kanban_name: Nome do Kanban
        """
        self.kanban_name = kanban_name
        self.transitions_repo = WorkflowRepository(kanban_name, 'transitions')
        self.actions_repo = WorkflowRepository(kanban_name, 'actions')

        logger.info(f"AuditLogger initialized for Kanban: {kanban_name}")

    # ========== REGISTRO DE AÇÕES ==========

    def log_action(
        self,
        action_type: str,
        entity_id: str,
        performed_by: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra ação de auditoria.

        Args:
            action_type: Tipo de ação (ex: 'process_created', 'process_updated')
            entity_id: ID da entidade afetada (process_id, kanban_name, etc)
            performed_by: Quem executou a ação ('user:john', 'system', 'agent:xxx')
            description: Descrição legível da ação
            metadata: Metadados adicionais
            changes: Dicionário de mudanças (before/after)

        Returns:
            ID do log criado
        """
        action_id = f"action_{int(datetime.utcnow().timestamp() * 1000)}"

        action_data = {
            'id': action_id,
            'action_type': action_type,
            'entity_id': entity_id,
            'performed_by': performed_by,
            'description': description,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {},
            'changes': changes or {}
        }

        self.actions_repo.create(action_data)

        logger.debug(
            f"Action logged: {action_type} on {entity_id} by {performed_by}"
        )

        return action_id

    def log_process_created(
        self,
        process_id: str,
        created_by: str,
        form_data: Dict[str, Any],
        initial_state: str
    ) -> str:
        """
        Registra criação de processo.

        Args:
            process_id: ID do processo criado
            created_by: Quem criou
            form_data: Dados do formulário
            initial_state: Estado inicial

        Returns:
            ID do log
        """
        return self.log_action(
            action_type='process_created',
            entity_id=process_id,
            performed_by=created_by,
            description=f"Process '{process_id}' created in state '{initial_state}'",
            metadata={
                'initial_state': initial_state,
                'form_fields_count': len(form_data)
            }
        )

    def log_process_updated(
        self,
        process_id: str,
        updated_by: str,
        changes: Dict[str, Any]
    ) -> str:
        """
        Registra atualização de processo.

        Args:
            process_id: ID do processo
            updated_by: Quem atualizou
            changes: Dicionário de mudanças {'field': {'old': ..., 'new': ...}}

        Returns:
            ID do log
        """
        fields_changed = list(changes.keys())

        return self.log_action(
            action_type='process_updated',
            entity_id=process_id,
            performed_by=updated_by,
            description=f"Process '{process_id}' updated: {', '.join(fields_changed)}",
            changes=changes,
            metadata={
                'fields_changed': fields_changed,
                'changes_count': len(changes)
            }
        )

    def log_process_deleted(
        self,
        process_id: str,
        deleted_by: str,
        reason: Optional[str] = None
    ) -> str:
        """
        Registra deleção de processo.

        Args:
            process_id: ID do processo
            deleted_by: Quem deletou
            reason: Motivo da deleção

        Returns:
            ID do log
        """
        return self.log_action(
            action_type='process_deleted',
            entity_id=process_id,
            performed_by=deleted_by,
            description=f"Process '{process_id}' deleted",
            metadata={'reason': reason} if reason else {}
        )

    # ========== CONSULTAS DE AUDITORIA ==========

    def get_process_timeline(
        self,
        process_id: str,
        include_transitions: bool = True,
        include_actions: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca timeline completo de um processo (transições + ações).

        Args:
            process_id: ID do processo
            include_transitions: Incluir transições de estado
            include_actions: Incluir outras ações

        Returns:
            Lista ordenada de eventos (mais recente primeiro)
        """
        timeline = []

        # Busca transições
        if include_transitions:
            transitions = self.transitions_repo.get_transition_history(process_id)
            for trans in transitions:
                timeline.append({
                    'event_type': 'transition',
                    'id': trans.get('id'),
                    'timestamp': trans.get('timestamp'),
                    'from_state': trans.get('from_state'),
                    'to_state': trans.get('to_state'),
                    'triggered_by': trans.get('triggered_by'),
                    'justification': trans.get('justification'),
                    'was_anomaly': trans.get('was_anomaly', False),
                    'prerequisites_status': trans.get('prerequisites_status')
                })

        # Busca ações
        if include_actions:
            all_actions = self.actions_repo.read_all()
            process_actions = [a for a in all_actions if a.get('entity_id') == process_id]

            for action in process_actions:
                timeline.append({
                    'event_type': 'action',
                    'id': action.get('id'),
                    'timestamp': action.get('timestamp'),
                    'action_type': action.get('action_type'),
                    'performed_by': action.get('performed_by'),
                    'description': action.get('description'),
                    'changes': action.get('changes'),
                    'metadata': action.get('metadata')
                })

        # Ordena por timestamp (mais recente primeiro)
        timeline.sort(key=lambda e: e.get('timestamp', ''), reverse=True)

        return timeline

    def get_audit_logs(
        self,
        action_type: Optional[str] = None,
        performed_by: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca logs de auditoria com filtros.

        Args:
            action_type: Filtrar por tipo de ação
            performed_by: Filtrar por quem executou
            entity_id: Filtrar por entidade específica
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            limit: Limitar quantidade de resultados

        Returns:
            Lista de logs de ações filtrados
        """
        all_actions = self.actions_repo.read_all()

        # Aplica filtros
        filtered = all_actions

        if action_type:
            filtered = [a for a in filtered if a.get('action_type') == action_type]

        if performed_by:
            filtered = [a for a in filtered if a.get('performed_by') == performed_by]

        if entity_id:
            filtered = [a for a in filtered if a.get('entity_id') == entity_id]

        if start_date:
            filtered = [a for a in filtered if a.get('timestamp', '') >= start_date]

        if end_date:
            filtered = [a for a in filtered if a.get('timestamp', '') <= end_date]

        # Ordena por timestamp (mais recente primeiro)
        filtered.sort(key=lambda a: a.get('timestamp', ''), reverse=True)

        # Aplica limite
        if limit:
            filtered = filtered[:limit]

        return filtered

    def get_transition_logs(
        self,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        triggered_by: Optional[str] = None,
        only_anomalies: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca logs de transições com filtros.

        Args:
            from_state: Filtrar por estado origem
            to_state: Filtrar por estado destino
            triggered_by: Filtrar por quem disparou
            only_anomalies: Mostrar apenas transições anômalas
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            limit: Limitar quantidade de resultados

        Returns:
            Lista de transições filtradas
        """
        all_transitions = self.transitions_repo.read_all()

        # Aplica filtros
        filtered = all_transitions

        if from_state:
            filtered = [t for t in filtered if t.get('from_state') == from_state]

        if to_state:
            filtered = [t for t in filtered if t.get('to_state') == to_state]

        if triggered_by:
            filtered = [t for t in filtered if t.get('triggered_by') == triggered_by]

        if only_anomalies:
            filtered = [t for t in filtered if t.get('was_anomaly', False)]

        if start_date:
            filtered = [t for t in filtered if t.get('timestamp', '') >= start_date]

        if end_date:
            filtered = [t for t in filtered if t.get('timestamp', '') <= end_date]

        # Ordena por timestamp (mais recente primeiro)
        filtered.sort(key=lambda t: t.get('timestamp', ''), reverse=True)

        # Aplica limite
        if limit:
            filtered = filtered[:limit]

        return filtered

    # ========== MÉTRICAS E ESTATÍSTICAS ==========

    def get_activity_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula resumo de atividade do workflow.

        Args:
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)

        Returns:
            Dicionário com estatísticas de atividade
        """
        # Busca logs no período
        actions = self.get_audit_logs(start_date=start_date, end_date=end_date)
        transitions = self.get_transition_logs(start_date=start_date, end_date=end_date)

        # Conta por tipo de ação
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action.get('action_type', 'unknown')] += 1

        # Conta transições por estado destino
        state_transitions = defaultdict(int)
        for trans in transitions:
            state_transitions[trans.get('to_state', 'unknown')] += 1

        # Conta anomalias
        anomaly_count = sum(1 for t in transitions if t.get('was_anomaly', False))

        # Conta usuários ativos
        users = set()
        for action in actions:
            users.add(action.get('performed_by', 'unknown'))
        for trans in transitions:
            users.add(trans.get('triggered_by', 'unknown'))

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_actions': len(actions),
            'total_transitions': len(transitions),
            'total_events': len(actions) + len(transitions),
            'action_counts': dict(action_counts),
            'state_transitions': dict(state_transitions),
            'anomaly_count': anomaly_count,
            'anomaly_rate': anomaly_count / len(transitions) if transitions else 0,
            'active_users_count': len(users),
            'active_users': list(users)
        }

    def get_state_metrics(
        self,
        process_id: str
    ) -> Dict[str, Any]:
        """
        Calcula métricas de tempo em cada estado para um processo.

        Args:
            process_id: ID do processo

        Returns:
            Métricas de tempo por estado
        """
        transitions = self.transitions_repo.get_transition_history(process_id)

        if not transitions:
            return {
                'process_id': process_id,
                'total_transitions': 0,
                'time_in_states': {},
                'average_time_per_state': None
            }

        # Ordena por timestamp (mais antigo primeiro)
        transitions.sort(key=lambda t: t.get('timestamp', ''))

        # Calcula tempo em cada estado
        time_in_states = defaultdict(float)
        current_state = None
        state_start = None

        for trans in transitions:
            timestamp = datetime.fromisoformat(trans.get('timestamp', ''))

            # Se havia um estado anterior, calcula tempo nele
            if current_state and state_start:
                duration = (timestamp - state_start).total_seconds()
                time_in_states[current_state] += duration

            # Atualiza estado atual
            current_state = trans.get('to_state')
            state_start = timestamp

        # Estado atual (se ainda está em um estado)
        if current_state and state_start:
            now = datetime.utcnow()
            duration = (now - state_start).total_seconds()
            time_in_states[current_state] += duration

        # Converte para formato legível (horas)
        time_in_states_hours = {
            state: round(seconds / 3600, 2)
            for state, seconds in time_in_states.items()
        }

        total_time = sum(time_in_states.values())
        avg_time = total_time / len(time_in_states) if time_in_states else 0

        return {
            'process_id': process_id,
            'total_transitions': len(transitions),
            'time_in_states_hours': time_in_states_hours,
            'total_time_hours': round(total_time / 3600, 2),
            'average_time_per_state_hours': round(avg_time / 3600, 2),
            'current_state': current_state
        }
