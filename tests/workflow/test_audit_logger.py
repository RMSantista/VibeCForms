"""
Testes para AuditLogger

Valida:
- Registro de ações (create, update, delete)
- Timeline de processos
- Queries avançadas de auditoria
- Métricas e estatísticas
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from workflow.engine.workflow_manager import WorkflowManager
from workflow.engine.transition_handler import TransitionHandler
from workflow.engine.audit_logger import AuditLogger


@pytest.fixture
def temp_workflows_dir(tmp_path):
    """Cria diretório temporário para workflows."""
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    return workflows_dir


@pytest.fixture
def workflow_manager(temp_workflows_dir):
    """Cria WorkflowManager com diretório temporário."""
    return WorkflowManager(workflows_dir=str(temp_workflows_dir))


@pytest.fixture
def simple_kanban(workflow_manager, request):
    """Cria Kanban simples com nome único para testes."""
    # Nome único por teste
    test_name = request.node.name
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    kanban_name = f"test_audit_{test_name}_{timestamp}"

    kanban_def = {
        "kanban_name": kanban_name,
        "title": "Test Audit Kanban",
        "description": "Kanban para testar auditoria",
        "states": [
            {"id": "todo", "name": "To Do", "order": 1},
            {"id": "doing", "name": "Doing", "order": 2},
            {"id": "done", "name": "Done", "order": 3}
        ],
        "agents": {
            "enabled": True,
            "flow_sequence": ["todo", "doing", "done"]
        }
    }

    workflow_manager.create_kanban(kanban_def)
    return kanban_name


@pytest.fixture
def audit_logger(simple_kanban):
    """Cria AuditLogger."""
    return AuditLogger(simple_kanban)


# ========== TESTES DE REGISTRO DE AÇÕES ==========

class TestAuditLogging:
    """Testa registro de ações."""

    def test_log_action_basic(self, audit_logger):
        """Testa registro básico de ação."""
        action_id = audit_logger.log_action(
            action_type='custom_action',
            entity_id='test_entity',
            performed_by='user:john',
            description='Test action'
        )

        assert action_id is not None
        assert action_id.startswith('action_')

    def test_log_action_with_metadata(self, audit_logger):
        """Testa registro com metadados."""
        metadata = {'key': 'value', 'count': 42}
        changes = {'field1': {'old': 'a', 'new': 'b'}}

        action_id = audit_logger.log_action(
            action_type='test_action',
            entity_id='entity123',
            performed_by='system',
            description='Test with metadata',
            metadata=metadata,
            changes=changes
        )

        # Busca ação registrada
        logs = audit_logger.get_audit_logs(entity_id='entity123')
        assert len(logs) == 1
        assert logs[0]['metadata'] == metadata
        assert logs[0]['changes'] == changes

    def test_log_process_created(self, audit_logger):
        """Testa log de criação de processo."""
        form_data = {'title': 'Test', 'description': 'Desc'}

        action_id = audit_logger.log_process_created(
            process_id='proc_123',
            created_by='user:alice',
            form_data=form_data,
            initial_state='todo'
        )

        assert action_id is not None

        # Verifica que foi registrado
        logs = audit_logger.get_audit_logs(action_type='process_created')
        assert len(logs) == 1
        assert logs[0]['entity_id'] == 'proc_123'
        assert logs[0]['performed_by'] == 'user:alice'
        assert logs[0]['metadata']['initial_state'] == 'todo'

    def test_log_process_updated(self, audit_logger):
        """Testa log de atualização de processo."""
        changes = {
            'title': {'old': 'Old Title', 'new': 'New Title'},
            'status': {'old': 'draft', 'new': 'published'}
        }

        action_id = audit_logger.log_process_updated(
            process_id='proc_456',
            updated_by='user:bob',
            changes=changes
        )

        assert action_id is not None

        # Verifica registro
        logs = audit_logger.get_audit_logs(action_type='process_updated')
        assert len(logs) == 1
        assert logs[0]['changes'] == changes
        assert logs[0]['metadata']['changes_count'] == 2

    def test_log_process_deleted(self, audit_logger):
        """Testa log de deleção de processo."""
        action_id = audit_logger.log_process_deleted(
            process_id='proc_789',
            deleted_by='user:admin',
            reason='Test cleanup'
        )

        assert action_id is not None

        # Verifica registro
        logs = audit_logger.get_audit_logs(action_type='process_deleted')
        assert len(logs) == 1
        assert logs[0]['entity_id'] == 'proc_789'
        assert logs[0]['metadata']['reason'] == 'Test cleanup'


# ========== TESTES DE CONSULTAS ==========

class TestAuditQueries:
    """Testa consultas de auditoria."""

    def test_get_process_timeline(self, simple_kanban, workflow_manager, audit_logger):
        """Testa timeline de processo (transições + ações)."""
        # Cria processo
        process_id = workflow_manager.create_process(
            kanban_name=simple_kanban,
            form_data={'title': 'Test'}
        )

        # Registra algumas ações
        audit_logger.log_process_created(
            process_id, 'user:alice', {'title': 'Test'}, 'todo'
        )
        audit_logger.log_process_updated(
            process_id, 'user:bob', {'title': {'old': 'Test', 'new': 'Updated'}}
        )

        # Executa transição
        transition_handler = TransitionHandler(workflow_manager)
        transition_handler.execute(process_id, 'doing', 'user:alice')

        # Busca timeline
        timeline = audit_logger.get_process_timeline(process_id)

        # Deve ter transição + 2 ações
        assert len(timeline) >= 3
        assert any(e['event_type'] == 'transition' for e in timeline)
        assert any(e['event_type'] == 'action' for e in timeline)

    def test_get_process_timeline_only_transitions(
        self, simple_kanban, workflow_manager, audit_logger
    ):
        """Testa timeline apenas com transições."""
        process_id = workflow_manager.create_process(
            kanban_name=simple_kanban,
            form_data={'title': 'Test'}
        )

        # Registra ação
        audit_logger.log_process_created(process_id, 'user:alice', {}, 'todo')

        # Executa transição
        transition_handler = TransitionHandler(workflow_manager)
        transition_handler.execute(process_id, 'doing')

        # Busca apenas transições
        timeline = audit_logger.get_process_timeline(
            process_id,
            include_transitions=True,
            include_actions=False
        )

        # Deve ter apenas transição
        assert all(e['event_type'] == 'transition' for e in timeline)

    def test_get_audit_logs_filtered(self, audit_logger):
        """Testa filtros de consulta de ações."""
        # Registra múltiplas ações
        audit_logger.log_action('process_created', 'proc1', 'user:alice', 'Created 1')
        audit_logger.log_action('process_updated', 'proc1', 'user:bob', 'Updated 1')
        audit_logger.log_action('process_created', 'proc2', 'user:alice', 'Created 2')

        # Filtra por tipo
        logs = audit_logger.get_audit_logs(action_type='process_created')
        assert len(logs) == 2

        # Filtra por usuário
        logs = audit_logger.get_audit_logs(performed_by='user:alice')
        assert len(logs) == 2

        # Filtra por entidade
        logs = audit_logger.get_audit_logs(entity_id='proc1')
        assert len(logs) == 2

    def test_get_audit_logs_with_date_range(self, audit_logger):
        """Testa filtro por período."""
        now = datetime.utcnow()
        yesterday = (now - timedelta(days=1)).isoformat()
        tomorrow = (now + timedelta(days=1)).isoformat()

        # Registra ações
        audit_logger.log_action('test_action', 'entity1', 'user:test', 'Test 1')
        audit_logger.log_action('test_action', 'entity2', 'user:test', 'Test 2')

        # Busca dentro do período
        logs = audit_logger.get_audit_logs(
            start_date=yesterday,
            end_date=tomorrow
        )
        assert len(logs) == 2

        # Busca fora do período
        past = (now - timedelta(days=10)).isoformat()
        logs = audit_logger.get_audit_logs(
            start_date=past,
            end_date=yesterday
        )
        assert len(logs) == 0

    def test_get_audit_logs_with_limit(self, audit_logger):
        """Testa limite de resultados."""
        # Registra múltiplas ações
        for i in range(10):
            audit_logger.log_action('test', f'entity{i}', 'user', f'Action {i}')

        # Busca com limite
        logs = audit_logger.get_audit_logs(limit=5)
        assert len(logs) == 5

    def test_get_transition_logs_filtered(
        self, simple_kanban, workflow_manager, audit_logger
    ):
        """Testa filtros de transições."""
        # Cria processo e executa transições
        process_id = workflow_manager.create_process(
            kanban_name=simple_kanban,
            form_data={'title': 'Test'}
        )

        transition_handler = TransitionHandler(workflow_manager)
        transition_handler.execute(process_id, 'doing', 'user:alice')
        transition_handler.execute(process_id, 'done', 'user:bob')

        # Filtra por estado origem
        logs = audit_logger.get_transition_logs(from_state='todo')
        assert len(logs) >= 1
        assert all(l['from_state'] == 'todo' for l in logs)

        # Filtra por estado destino
        logs = audit_logger.get_transition_logs(to_state='done')
        assert len(logs) >= 1
        assert all(l['to_state'] == 'done' for l in logs)

        # Filtra por quem disparou
        logs = audit_logger.get_transition_logs(triggered_by='user:alice')
        assert len(logs) >= 1


# ========== TESTES DE MÉTRICAS ==========

class TestAuditMetrics:
    """Testa métricas e estatísticas."""

    def test_get_activity_summary(self, simple_kanban, workflow_manager, audit_logger):
        """Testa resumo de atividade."""
        # Cria processo
        process_id = workflow_manager.create_process(
            kanban_name=simple_kanban,
            form_data={'title': 'Test'}
        )

        # Registra ações
        audit_logger.log_process_created(process_id, 'user:alice', {}, 'todo')
        audit_logger.log_process_updated(process_id, 'user:bob', {})

        # Executa transição
        transition_handler = TransitionHandler(workflow_manager)
        transition_handler.execute(process_id, 'doing', 'user:alice')

        # Busca resumo
        summary = audit_logger.get_activity_summary()

        assert summary['total_actions'] >= 2
        assert summary['total_transitions'] >= 1
        assert summary['total_events'] >= 3
        assert 'action_counts' in summary
        assert 'state_transitions' in summary
        assert summary['active_users_count'] >= 2

    def test_get_activity_summary_with_date_range(self, audit_logger):
        """Testa resumo com período."""
        now = datetime.utcnow()
        yesterday = (now - timedelta(days=1)).isoformat()
        tomorrow = (now + timedelta(days=1)).isoformat()

        # Registra ações
        audit_logger.log_action('test1', 'e1', 'user1', 'Test 1')
        audit_logger.log_action('test2', 'e2', 'user2', 'Test 2')

        # Busca resumo no período
        summary = audit_logger.get_activity_summary(
            start_date=yesterday,
            end_date=tomorrow
        )

        assert summary['total_actions'] == 2
        assert summary['period']['start_date'] == yesterday
        assert summary['period']['end_date'] == tomorrow

    def test_get_state_metrics(self, simple_kanban, workflow_manager, audit_logger):
        """Testa métricas de tempo por estado."""
        # Cria processo
        process_id = workflow_manager.create_process(
            kanban_name=simple_kanban,
            form_data={'title': 'Test'}
        )

        # Aguarda um pouco
        time.sleep(0.1)

        # Executa transições
        transition_handler = TransitionHandler(workflow_manager)
        transition_handler.execute(process_id, 'doing')

        time.sleep(0.1)

        transition_handler.execute(process_id, 'done')

        # Busca métricas
        metrics = audit_logger.get_state_metrics(process_id)

        assert metrics['process_id'] == process_id
        assert metrics['total_transitions'] == 2
        assert 'time_in_states_hours' in metrics
        assert 'total_time_hours' in metrics
        assert metrics['current_state'] == 'done'

        # Deve ter tempo nos estados que tiveram transições
        # Note: 'todo' pode não aparecer pois não há transição registrada saindo dele
        assert 'doing' in metrics['time_in_states_hours']
        assert 'done' in metrics['time_in_states_hours']

        # Tempo total deve existir (pode ser muito pequeno)
        assert metrics['total_time_hours'] >= 0

    def test_get_state_metrics_no_transitions(self, audit_logger):
        """Testa métricas de processo sem transições."""
        metrics = audit_logger.get_state_metrics('proc_nonexistent')

        assert metrics['total_transitions'] == 0
        assert metrics['time_in_states'] == {}
        assert metrics['average_time_per_state'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
