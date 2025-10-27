"""
Testes para AutoTransitionEngine

Valida:
- Detecção de elegibilidade para auto-transição
- Execução automática de transições
- Progressão em cadeia
- Prevenção de loops infinitos
- Processamento de Kanbans
"""

import pytest
from pathlib import Path
from datetime import datetime

# Adiciona src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from workflow.engine.workflow_manager import WorkflowManager
from workflow.engine.auto_transition_engine import AutoTransitionEngine


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
def auto_kanban(workflow_manager, request):
    """Cria Kanban com auto-transition habilitado."""
    test_name = request.node.name
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    kanban_name = f"test_auto_{test_name}_{timestamp}"

    kanban_def = {
        "kanban_name": kanban_name,
        "title": "Auto-Transition Test Kanban",
        "description": "Kanban para testar auto-transição",
        "states": [
            {"id": "start", "name": "Start", "order": 1},
            {
                "id": "middle",
                "name": "Middle",
                "order": 2,
                "prerequisites": [
                    {
                        "id": "has_title",
                        "type": "field_validation",
                        "label": "Has Title",
                        "field_name": "title",
                        "blocking": False
                    }
                ]
            },
            {"id": "end", "name": "End", "order": 3}
        ],
        "agents": {
            "enabled": True,
            "flow_sequence": ["start", "middle", "end"]
        }
    }

    workflow_manager.create_kanban(kanban_def)
    return kanban_name


@pytest.fixture
def manual_kanban(workflow_manager, request):
    """Cria Kanban SEM auto-transition."""
    test_name = request.node.name
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    kanban_name = f"test_manual_{test_name}_{timestamp}"

    kanban_def = {
        "kanban_name": kanban_name,
        "title": "Manual Transition Kanban",
        "description": "Kanban sem auto-transição",
        "states": [
            {"id": "todo", "name": "To Do", "order": 1},
            {"id": "done", "name": "Done", "order": 2}
        ],
        "agents": {
            "enabled": False,
            "flow_sequence": ["todo", "done"]
        }
    }

    workflow_manager.create_kanban(kanban_def)
    return kanban_name


@pytest.fixture
def engine(workflow_manager):
    """Cria AutoTransitionEngine."""
    return AutoTransitionEngine(workflow_manager)


# ========== TESTES DE ELEGIBILIDADE ==========

class TestAutoTransitionEligibility:
    """Testa detecção de elegibilidade."""

    def test_can_auto_transition_simple(self, auto_kanban, workflow_manager, engine):
        """Testa que processo pode progredir quando pré-requisitos atendidos."""
        # Cria processo com título (atende pré-requisito)
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test Process'}
        )

        result = engine._can_auto_transition(process_id)

        assert result['can_progress'] is True
        assert result['current_state'] == 'start'
        assert result['next_state'] == 'middle'

    def test_cannot_auto_transition_prerequisites_unmet(
        self, auto_kanban, workflow_manager, engine
    ):
        """Testa que processo NÃO progride quando pré-requisitos não atendidos."""
        # Cria processo SEM título
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={}
        )

        result = engine._can_auto_transition(process_id)

        assert result['can_progress'] is False
        assert 'prerequisite(s) not met' in result['reason']

    def test_cannot_auto_transition_at_final_state(
        self, auto_kanban, workflow_manager, engine
    ):
        """Testa que processo no estado final não progride."""
        # Cria processo direto no estado final
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'},
            initial_state='end'
        )

        result = engine._can_auto_transition(process_id)

        assert result['can_progress'] is False
        assert 'final state' in result['reason']

    def test_cannot_auto_transition_no_flow_sequence(
        self, manual_kanban, workflow_manager, engine
    ):
        """Testa que Kanban sem flow_sequence não progride."""
        # Cria Kanban sem flow_sequence
        kanban_def = workflow_manager.get_kanban(manual_kanban)
        kanban_def['agents']['flow_sequence'] = []
        workflow_manager.update_kanban(manual_kanban, kanban_def)

        process_id = workflow_manager.create_process(
            kanban_name=manual_kanban,
            form_data={'title': 'Test'}
        )

        result = engine._can_auto_transition(process_id)

        assert result['can_progress'] is False
        assert 'No flow_sequence' in result['reason']


# ========== TESTES DE EXECUÇÃO ==========

class TestAutoTransitionExecution:
    """Testa execução de auto-transições."""

    def test_execute_single_transition(self, auto_kanban, workflow_manager, engine):
        """Testa execução de uma transição automática."""
        # Cria processo
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        # Executa auto-transição
        result = engine.check_and_execute(process_id)

        assert result['auto_transition_enabled'] is True
        assert result['transitions_executed'] == 2  # start -> middle -> end
        assert result['current_state'] == 'end'
        assert len(result['transitions']) == 2

    def test_execute_chain_transitions(self, auto_kanban, workflow_manager, engine):
        """Testa progressão em cadeia até o fim."""
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        result = engine.check_and_execute(process_id)

        # Deve ter progredido de start -> middle -> end
        assert result['transitions_executed'] == 2
        assert result['transitions'][0]['from_state'] == 'start'
        assert result['transitions'][0]['to_state'] == 'middle'
        assert result['transitions'][1]['from_state'] == 'middle'
        assert result['transitions'][1]['to_state'] == 'end'

    def test_execute_stops_at_unmet_prerequisites(
        self, auto_kanban, workflow_manager, engine
    ):
        """Testa que execução para quando pré-requisitos não atendidos."""
        # Cria processo sem título
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={}
        )

        result = engine.check_and_execute(process_id)

        # Não deve ter executado nenhuma transição
        assert result['transitions_executed'] == 0
        assert result['current_state'] == 'start'

    def test_execute_respects_max_transitions(
        self, auto_kanban, workflow_manager, engine
    ):
        """Testa que respeita limite de transições."""
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        # Limita a 1 transição
        result = engine.check_and_execute(process_id, max_transitions=1)

        assert result['transitions_executed'] == 1
        assert result['current_state'] == 'middle'  # Parou no meio

    def test_execute_not_enabled_for_manual_kanban(
        self, manual_kanban, workflow_manager, engine
    ):
        """Testa que Kanban manual não executa auto-transição."""
        process_id = workflow_manager.create_process(
            kanban_name=manual_kanban,
            form_data={'title': 'Test'}
        )

        result = engine.check_and_execute(process_id)

        assert result['auto_transition_enabled'] is False
        assert result['transitions_executed'] == 0


# ========== TESTES DE PROCESSAMENTO EM MASSA ==========

class TestAutoTransitionBatch:
    """Testa processamento em massa."""

    def test_process_kanban(self, auto_kanban, workflow_manager, engine):
        """Testa processamento de todos os processos de um Kanban."""
        # Cria múltiplos processos
        for i in range(3):
            workflow_manager.create_process(
                kanban_name=auto_kanban,
                form_data={'title': f'Process {i}'}
            )

        # Processa Kanban
        result = engine.process_kanban(auto_kanban)

        # Deve ter checado 3 processos
        assert result['processes_checked'] == 3
        # Pelo menos alguns devem ter progredido
        assert result['processes_progressed'] > 0
        assert result['total_transitions'] > 0

    def test_process_kanban_with_limit(self, auto_kanban, workflow_manager, engine):
        """Testa processamento com limite de processos."""
        # Cria múltiplos processos
        for i in range(5):
            workflow_manager.create_process(
                kanban_name=auto_kanban,
                form_data={'title': f'Process {i}'}
            )

        # Processa apenas 2
        result = engine.process_kanban(auto_kanban, max_processes=2)

        assert result['processes_checked'] == 2
        # Pelo menos um deve ter progredido
        assert result['processes_progressed'] > 0

    def test_process_all_kanbans(self, auto_kanban, workflow_manager, engine):
        """Testa processamento de todos os Kanbans."""
        # Cria processo
        workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        # Processa todos
        result = engine.process_all_kanbans()

        assert result['kanbans_processed'] >= 1
        assert result['total_processes_checked'] >= 1
        assert result['total_transitions'] >= 2


# ========== TESTES DE CONSULTAS ==========

class TestAutoTransitionQueries:
    """Testa consultas do engine."""

    def test_get_eligible_processes(self, auto_kanban, workflow_manager, engine):
        """Testa listagem de processos elegíveis."""
        # Cria processo elegível
        p1 = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Eligible'}
        )

        # Cria processo não elegível
        p2 = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={}  # Sem título
        )

        # Lista elegíveis
        eligible = engine.get_eligible_processes(auto_kanban)

        # Deve ter pelo menos 1 elegível (p1)
        assert len(eligible) >= 1

        # Verifica que p1 está na lista
        eligible_ids = [e['process_id'] for e in eligible]
        assert p1 in eligible_ids

        # Verifica estrutura do elegível
        p1_eligible = next(e for e in eligible if e['process_id'] == p1)
        assert p1_eligible['current_state'] == 'start'
        assert p1_eligible['next_state'] == 'middle'


# ========== TESTES DE EDGE CASES ==========

class TestAutoTransitionEdgeCases:
    """Testa casos extremos."""

    def test_prevents_duplicate_processing(self, auto_kanban, workflow_manager, engine):
        """Testa que previne processamento duplicado."""
        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        # Adiciona manualmente ao set de processamento
        engine._processing_processes.add(process_id)

        # Tenta processar
        result = engine.check_and_execute(process_id)

        assert result['auto_transition_enabled'] is False
        assert 'already being processed' in result.get('error', '')

    def test_transition_triggered_by_auto(self, auto_kanban, workflow_manager, engine):
        """Testa que transições são registradas como 'auto'."""
        from workflow.engine.audit_logger import AuditLogger

        process_id = workflow_manager.create_process(
            kanban_name=auto_kanban,
            form_data={'title': 'Test'}
        )

        # Executa auto-transição
        engine.check_and_execute(process_id)

        # Verifica histórico de transições usando get_transition_logs
        audit = AuditLogger(auto_kanban)
        history = audit.get_transition_logs(triggered_by='auto')

        assert len(history) >= 2
        assert all(t['triggered_by'] == 'auto' for t in history)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
