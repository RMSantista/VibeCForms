"""
Testes para WorkflowManager

Valida CRUD de Kanbans e Processos.
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime

# Adiciona src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from workflow.engine.workflow_manager import WorkflowManager


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
def sample_kanban_definition():
    """Retorna definição de Kanban de exemplo."""
    return {
        "kanban_name": "test_kanban",
        "title": "Test Kanban",
        "description": "Kanban para testes",
        "icon": "fa-test",
        "states": [
            {
                "id": "todo",
                "name": "To Do",
                "order": 1,
                "color": "#FF0000",
                "icon": "fa-list"
            },
            {
                "id": "doing",
                "name": "Doing",
                "order": 2,
                "color": "#00FF00",
                "icon": "fa-cog"
            },
            {
                "id": "done",
                "name": "Done",
                "order": 3,
                "color": "#0000FF",
                "icon": "fa-check"
            }
        ],
        "agents": {
            "enabled": False,
            "flow_sequence": ["todo", "doing", "done"]
        }
    }


class TestWorkflowManagerKanbans:
    """Testa operações de Kanban."""

    def test_create_kanban(self, workflow_manager, sample_kanban_definition):
        """Testa criação de Kanban."""
        kanban_name = workflow_manager.create_kanban(sample_kanban_definition)

        assert kanban_name == "test_kanban"

        # Verifica que arquivo foi criado
        kanban_file = workflow_manager.workflows_dir / "test_kanban.json"
        assert kanban_file.exists()

        # Verifica conteúdo
        with open(kanban_file) as f:
            saved_definition = json.load(f)

        assert saved_definition['kanban_name'] == "test_kanban"
        assert saved_definition['title'] == "Test Kanban"
        assert 'created_at' in saved_definition

    def test_create_duplicate_kanban(self, workflow_manager, sample_kanban_definition):
        """Testa que não permite criar Kanban duplicado."""
        workflow_manager.create_kanban(sample_kanban_definition)

        with pytest.raises(ValueError, match="already exists"):
            workflow_manager.create_kanban(sample_kanban_definition)

    def test_get_kanban(self, workflow_manager, sample_kanban_definition):
        """Testa busca de Kanban."""
        workflow_manager.create_kanban(sample_kanban_definition)

        definition = workflow_manager.get_kanban("test_kanban")

        assert definition['kanban_name'] == "test_kanban"
        assert definition['title'] == "Test Kanban"
        assert len(definition['states']) == 3

    def test_get_nonexistent_kanban(self, workflow_manager):
        """Testa busca de Kanban inexistente."""
        with pytest.raises(ValueError, match="not found"):
            workflow_manager.get_kanban("nonexistent")

    def test_list_kanbans(self, workflow_manager, sample_kanban_definition):
        """Testa listagem de Kanbans."""
        # Cria múltiplos Kanbans
        workflow_manager.create_kanban(sample_kanban_definition)

        kanban2 = sample_kanban_definition.copy()
        kanban2['kanban_name'] = "test_kanban2"
        kanban2['title'] = "Test Kanban 2"
        workflow_manager.create_kanban(kanban2)

        # Lista
        kanbans = workflow_manager.list_kanbans()

        assert len(kanbans) == 2
        assert kanbans[0]['kanban_name'] == "test_kanban"
        assert kanbans[1]['kanban_name'] == "test_kanban2"
        assert 'states_count' in kanbans[0]
        assert kanbans[0]['states_count'] == 3

    def test_update_kanban(self, workflow_manager, sample_kanban_definition):
        """Testa atualização de Kanban."""
        workflow_manager.create_kanban(sample_kanban_definition)

        # Atualiza
        updated_def = sample_kanban_definition.copy()
        updated_def['title'] = "Updated Title"

        result = workflow_manager.update_kanban("test_kanban", updated_def)
        assert result is True

        # Verifica atualização
        definition = workflow_manager.get_kanban("test_kanban")
        assert definition['title'] == "Updated Title"

    def test_delete_kanban(self, workflow_manager, sample_kanban_definition):
        """Testa deleção de Kanban sem processos."""
        # Usa nome único para este teste
        sample_kanban_definition['kanban_name'] = "test_delete_kanban"

        workflow_manager.create_kanban(sample_kanban_definition)

        result = workflow_manager.delete_kanban("test_delete_kanban")
        assert result is True

        # Verifica que não existe mais
        with pytest.raises(ValueError, match="not found"):
            workflow_manager.get_kanban("test_delete_kanban")

    def test_validate_kanban_definition(self, workflow_manager):
        """Testa validação de definição inválida."""
        # Definição sem fields obrigatórios
        invalid_def = {
            "kanban_name": "invalid"
            # Falta 'title' e 'states'
        }

        with pytest.raises(ValueError, match="Invalid Kanban definition"):
            workflow_manager.create_kanban(invalid_def)


class TestWorkflowManagerProcesses:
    """Testa operações de Processo."""

    @pytest.fixture
    def kanban_with_manager(self, workflow_manager, sample_kanban_definition, request):
        """Cria Kanban com nome único por teste e retorna manager."""
        # Nome único baseado no teste + timestamp para garantir unicidade absoluta
        test_name = request.node.name
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        unique_kanban_name = f"test_{test_name}_{timestamp}"

        # Atualiza definição com nome único
        sample_kanban_definition['kanban_name'] = unique_kanban_name

        workflow_manager.create_kanban(sample_kanban_definition)

        # Retorna manager e kanban_name para uso nos testes
        workflow_manager.test_kanban_name = unique_kanban_name
        return workflow_manager

    def test_create_process(self, kanban_with_manager):
        """Testa criação de processo."""
        kanban_name = kanban_with_manager.test_kanban_name

        process_id = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Test Task", "description": "Test description"}
        )

        assert process_id is not None
        assert process_id.startswith(f"proc_{kanban_name}_")

        # Verifica que foi criado
        process = kanban_with_manager.get_process(process_id, kanban_name)
        assert process['id'] == process_id
        assert process['kanban_name'] == kanban_name
        assert process['current_state'] == "todo"  # Primeiro estado do flow_sequence

    def test_create_process_with_initial_state(self, kanban_with_manager):
        """Testa criação com estado inicial específico."""
        kanban_name = kanban_with_manager.test_kanban_name

        process_id = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Test"},
            initial_state="doing"
        )

        process = kanban_with_manager.get_process(process_id, kanban_name)
        assert process['current_state'] == "doing"

    def test_create_process_invalid_state(self, kanban_with_manager):
        """Testa criação com estado inicial inválido."""
        kanban_name = kanban_with_manager.test_kanban_name

        with pytest.raises(ValueError, match="Invalid initial state"):
            kanban_with_manager.create_process(
                kanban_name=kanban_name,
                form_data={},
                initial_state="invalid_state"
            )

    def test_get_process(self, kanban_with_manager):
        """Testa busca de processo."""
        kanban_name = kanban_with_manager.test_kanban_name

        process_id = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Test"}
        )

        process = kanban_with_manager.get_process(process_id, kanban_name)

        assert process['id'] == process_id
        assert process['form_data']['title'] == "Test"

    def test_get_nonexistent_process(self, kanban_with_manager):
        """Testa busca de processo inexistente."""
        kanban_name = kanban_with_manager.test_kanban_name

        with pytest.raises(ValueError, match="not found"):
            kanban_with_manager.get_process("proc_nonexistent", kanban_name)

    def test_list_processes(self, kanban_with_manager):
        """Testa listagem de processos."""
        kanban_name = kanban_with_manager.test_kanban_name

        # Cria múltiplos processos
        for i in range(3):
            kanban_with_manager.create_process(
                kanban_name=kanban_name,
                form_data={"title": f"Task {i}"}
            )

        processes = kanban_with_manager.list_processes(kanban_name)

        assert len(processes) == 3
        # Verifica ordenação por updated_at (mais recente primeiro)
        assert processes[0]['form_data']['title'] == "Task 2"

    def test_list_processes_by_state(self, kanban_with_manager):
        """Testa listagem filtrada por estado."""
        kanban_name = kanban_with_manager.test_kanban_name

        # Cria processos em estados diferentes
        p1 = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Task 1"},
            initial_state="todo"
        )
        p2 = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Task 2"},
            initial_state="doing"
        )
        p3 = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Task 3"},
            initial_state="todo"
        )

        # Lista por estado
        todo_processes = kanban_with_manager.list_processes(kanban_name, state="todo")
        doing_processes = kanban_with_manager.list_processes(kanban_name, state="doing")

        assert len(todo_processes) == 2
        assert len(doing_processes) == 1

    def test_update_process(self, kanban_with_manager):
        """Testa atualização de processo."""
        kanban_name = kanban_with_manager.test_kanban_name

        process_id = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Original"}
        )

        # Atualiza
        result = kanban_with_manager.update_process(
            process_id,
            {"form_data": {"title": "Updated"}}
        )
        assert result is True

        # Verifica atualização
        process = kanban_with_manager.get_process(process_id, kanban_name)
        assert process['form_data']['title'] == "Updated"

    def test_delete_process(self, kanban_with_manager):
        """Testa deleção de processo."""
        kanban_name = kanban_with_manager.test_kanban_name

        process_id = kanban_with_manager.create_process(
            kanban_name=kanban_name,
            form_data={"title": "Test"}
        )

        result = kanban_with_manager.delete_process(process_id)
        assert result is True

        # Verifica que não existe mais
        with pytest.raises(ValueError, match="not found"):
            kanban_with_manager.get_process(process_id, kanban_name)


class TestWorkflowManagerCache:
    """Testa cache de definições."""

    def test_cache_after_load(self, workflow_manager, sample_kanban_definition):
        """Testa que definição é cacheada após load."""
        workflow_manager.create_kanban(sample_kanban_definition)

        # Primeiro load (do arquivo)
        definition1 = workflow_manager.get_kanban("test_kanban")

        # Segundo load (do cache)
        definition2 = workflow_manager.get_kanban("test_kanban")

        assert definition1 == definition2
        assert "test_kanban" in workflow_manager._kanban_cache

    def test_reload_cache(self, workflow_manager, sample_kanban_definition):
        """Testa reload do cache."""
        workflow_manager.create_kanban(sample_kanban_definition)

        # Limpa cache manualmente
        workflow_manager._kanban_cache.clear()
        assert len(workflow_manager._kanban_cache) == 0

        # Reload
        count = workflow_manager.reload_cache()

        assert count == 1
        assert "test_kanban" in workflow_manager._kanban_cache


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
