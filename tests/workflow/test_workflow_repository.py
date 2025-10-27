"""
Testes para WorkflowRepository

Valida persistência de processos e transições usando backend JSON.
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime

# Adiciona src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from workflow.repository.workflow_repository import WorkflowRepository


@pytest.fixture
def temp_workflow_dir(tmp_path):
    """Cria diretório temporário para dados de workflow."""
    workflow_dir = tmp_path / "workflows"
    workflow_dir.mkdir()
    return workflow_dir


@pytest.fixture
def workflow_repo(temp_workflow_dir, monkeypatch, request):
    """
    Cria WorkflowRepository configurado para usar diretório temporário.

    Usa monkeypatch para modificar o path do JSONRepository.
    Cada teste usa um kanban_name único baseado no nome do teste.
    """
    # Configura path temporário para JSON adapter
    from persistence.adapters.json_adapter import JSONRepository
    original_init = JSONRepository.__init__

    def mock_init(self, config):
        config = config.copy()
        config['path'] = str(temp_workflow_dir)
        original_init(self, config)

    monkeypatch.setattr(JSONRepository, '__init__', mock_init)

    # Usa nome do teste como nome do kanban para isolamento
    test_name = request.node.name
    kanban_name = f"test_{test_name}"

    # Cria repository para processos
    repo = WorkflowRepository(kanban_name, 'processes')
    return repo


class TestWorkflowRepositoryBasicOperations:
    """Testa operações CRUD básicas."""

    def test_create_process(self, workflow_repo):
        """Testa criação de processo."""
        process_data = {
            'id': 'proc_001',
            'kanban_name': 'pedidos',
            'current_state': 'orcamento',
            'previous_state': None,
            'form_data': {
                'cliente': 'Acme Corp',
                'produtos': ['Produto A', 'Produto B'],
                'valor_total': 1500.00
            },
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {
                'priority': 'high',
                'tags': ['urgente', 'cliente-vip']
            }
        }

        # Cria processo
        process_id = workflow_repo.create(process_data)

        assert process_id == 'proc_001'

        # Verifica que foi criado
        all_processes = workflow_repo.read_all()
        assert len(all_processes) == 1
        assert all_processes[0]['id'] == 'proc_001'
        assert all_processes[0]['kanban_name'] == 'pedidos'

    def test_read_all_processes(self, workflow_repo):
        """Testa leitura de todos os processos."""
        # Cria múltiplos processos
        for i in range(3):
            process_data = {
                'id': f'proc_{i:03d}',
                'kanban_name': 'pedidos',
                'current_state': 'orcamento',
                'previous_state': None,
                'form_data': {'cliente': f'Cliente {i}'},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {}
            }
            workflow_repo.create(process_data)

        # Lê todos
        all_processes = workflow_repo.read_all()

        assert len(all_processes) == 3
        assert all_processes[0]['id'] == 'proc_000'
        assert all_processes[1]['id'] == 'proc_001'
        assert all_processes[2]['id'] == 'proc_002'

    def test_get_by_id(self, workflow_repo):
        """Testa busca por ID."""
        # Cria processo
        process_data = {
            'id': 'proc_test',
            'kanban_name': 'pedidos',
            'current_state': 'orcamento',
            'previous_state': None,
            'form_data': {'cliente': 'Test Client'},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {}
        }
        workflow_repo.create(process_data)

        # Busca por ID
        found_process = workflow_repo.get_by_id('proc_test')

        assert found_process is not None
        assert found_process['id'] == 'proc_test'
        assert found_process['kanban_name'] == 'pedidos'

        # Busca ID inexistente
        not_found = workflow_repo.get_by_id('proc_nao_existe')
        assert not_found is None


class TestWorkflowRepositoryStateManagement:
    """Testa operações específicas de workflow (mudança de estado)."""

    def test_change_state(self, workflow_repo):
        """Testa mudança de estado de um processo."""
        # Cria processo
        process_data = {
            'id': 'proc_state_test',
            'kanban_name': 'pedidos',
            'current_state': 'orcamento',
            'previous_state': None,
            'form_data': {'cliente': 'Test'},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {}
        }
        workflow_repo.create(process_data)

        # Muda estado
        updated_process = workflow_repo.change_state(
            'proc_state_test',
            'aprovacao',
            justification='Teste de mudança de estado'
        )

        assert updated_process['current_state'] == 'aprovacao'
        assert updated_process['previous_state'] == 'orcamento'
        assert updated_process['last_transition']['from_state'] == 'orcamento'
        assert updated_process['last_transition']['to_state'] == 'aprovacao'
        assert updated_process['last_transition']['justification'] == 'Teste de mudança de estado'

    def test_change_state_nonexistent_process(self, workflow_repo):
        """Testa mudança de estado de processo inexistente."""
        with pytest.raises(ValueError, match="not found"):
            workflow_repo.change_state('proc_nao_existe', 'aprovacao')

    def test_get_all_by_state(self, workflow_repo):
        """Testa busca de processos por estado."""
        # Cria processos em estados diferentes
        states = ['orcamento', 'orcamento', 'aprovacao', 'entrega', 'orcamento']

        for i, state in enumerate(states):
            process_data = {
                'id': f'proc_{i}',
                'kanban_name': 'pedidos',
                'current_state': state,
                'previous_state': None,
                'form_data': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {}
            }
            workflow_repo.create(process_data)

        # Busca por estado
        orcamento_processes = workflow_repo.get_all_by_state('orcamento')
        aprovacao_processes = workflow_repo.get_all_by_state('aprovacao')
        entrega_processes = workflow_repo.get_all_by_state('entrega')
        concluido_processes = workflow_repo.get_all_by_state('concluido')

        assert len(orcamento_processes) == 3
        assert len(aprovacao_processes) == 1
        assert len(entrega_processes) == 1
        assert len(concluido_processes) == 0


class TestWorkflowRepositoryTransitions:
    """Testa log de transições (auditoria)."""

    def test_log_transition(self, temp_workflow_dir, monkeypatch):
        """Testa registro de transição."""
        # Configura mock do JSONRepository
        from persistence.adapters.json_adapter import JSONRepository
        original_init = JSONRepository.__init__

        def mock_init(self, config):
            config = config.copy()
            config['path'] = str(temp_workflow_dir)
            original_init(self, config)

        monkeypatch.setattr(JSONRepository, '__init__', mock_init)

        # Cria repository de processos
        process_repo = WorkflowRepository('pedidos', 'processes')

        # Registra transição
        transition_id = process_repo.log_transition(
            process_id='proc_001',
            from_state='orcamento',
            to_state='aprovacao',
            triggered_by='manual',
            justification='Cliente solicitou urgência',
            prerequisites_status={'cliente_informado': True, 'produtos_selecionados': True},
            was_anomaly=False,
            anomaly_reason=None
        )

        assert transition_id is not None
        assert transition_id.startswith('trans_')

        # Verifica que transição foi criada
        transitions_repo = WorkflowRepository('pedidos', 'transitions')
        all_transitions = transitions_repo.read_all()

        assert len(all_transitions) == 1
        assert all_transitions[0]['process_id'] == 'proc_001'
        assert all_transitions[0]['from_state'] == 'orcamento'
        assert all_transitions[0]['to_state'] == 'aprovacao'
        assert all_transitions[0]['triggered_by'] == 'manual'
        assert all_transitions[0]['justification'] == 'Cliente solicitou urgência'

    def test_get_transition_history(self, temp_workflow_dir, monkeypatch):
        """Testa busca de histórico de transições de um processo."""
        # Configura mock
        from persistence.adapters.json_adapter import JSONRepository
        original_init = JSONRepository.__init__

        def mock_init(self, config):
            config = config.copy()
            config['path'] = str(temp_workflow_dir)
            original_init(self, config)

        monkeypatch.setattr(JSONRepository, '__init__', mock_init)

        # Cria repository de processos
        process_repo = WorkflowRepository('pedidos', 'processes')

        # Cria múltiplas transições para o mesmo processo
        transitions_data = [
            ('orcamento', 'aprovacao', '2025-10-26T10:00:00'),
            ('aprovacao', 'entrega', '2025-10-26T14:00:00'),
            ('entrega', 'concluido', '2025-10-26T18:00:00'),
        ]

        for from_state, to_state, timestamp in transitions_data:
            process_repo.log_transition(
                process_id='proc_123',
                from_state=from_state,
                to_state=to_state,
                triggered_by='system',
                prerequisites_status={}
            )

        # Busca histórico
        history = process_repo.get_transition_history('proc_123')

        assert len(history) == 3
        # Histórico deve estar ordenado por timestamp (mais recente primeiro)
        assert history[0]['to_state'] == 'concluido'
        assert history[1]['to_state'] == 'entrega'
        assert history[2]['to_state'] == 'aprovacao'


class TestWorkflowRepositoryDataSerialization:
    """Testa serialização/deserialização de dados complexos."""

    def test_serialize_complex_data(self, workflow_repo):
        """Testa que dados complexos (objetos, arrays) são serializados corretamente."""
        process_data = {
            'id': 'proc_complex',
            'kanban_name': 'pedidos',
            'current_state': 'orcamento',
            'previous_state': None,
            'form_data': {
                'cliente': 'Acme Corp',
                'produtos': ['Produto A', 'Produto B', 'Produto C'],
                'valores': {
                    'subtotal': 1000,
                    'desconto': 100,
                    'total': 900
                }
            },
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {
                'prioridade': 'alta',
                'tags': ['urgente', 'vip'],
                'historico': [
                    {'data': '2025-10-26', 'acao': 'criado'},
                    {'data': '2025-10-26', 'acao': 'atualizado'}
                ]
            }
        }

        # Cria processo
        workflow_repo.create(process_data)

        # Lê processo
        retrieved_process = workflow_repo.get_by_id('proc_complex')

        # Verifica que dados complexos foram preservados
        assert isinstance(retrieved_process['form_data'], dict)
        assert isinstance(retrieved_process['form_data']['produtos'], list)
        assert len(retrieved_process['form_data']['produtos']) == 3
        assert retrieved_process['form_data']['valores']['total'] == 900

        assert isinstance(retrieved_process['metadata'], dict)
        assert isinstance(retrieved_process['metadata']['tags'], list)
        assert len(retrieved_process['metadata']['tags']) == 2
        assert isinstance(retrieved_process['metadata']['historico'], list)
        assert len(retrieved_process['metadata']['historico']) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
