"""
Testes para TransitionHandler e PrerequisiteChecker

Valida:
- Validação de pré-requisitos (6 tipos)
- Filosofia "Avisar, Não Bloquear"
- Execução de transições
- Histórico e transições disponíveis
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
from workflow.engine.transition_handler import TransitionHandler
from workflow.engine.prerequisite_checker import PrerequisiteChecker


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
def transition_handler(workflow_manager):
    """Cria TransitionHandler."""
    return TransitionHandler(workflow_manager)


@pytest.fixture
def kanban_with_prerequisites(workflow_manager):
    """Cria Kanban com pré-requisitos em cada estado."""
    kanban_def = {
        "kanban_name": "test_prereq_kanban",
        "title": "Test Kanban with Prerequisites",
        "description": "Kanban para testar pré-requisitos",
        "states": [
            {
                "id": "draft",
                "name": "Rascunho",
                "order": 1,
                "color": "#CCCCCC"
            },
            {
                "id": "review",
                "name": "Revisão",
                "order": 2,
                "color": "#FFAA00",
                "prerequisites": [
                    {
                        "id": "doc_upload",
                        "type": "document_upload",
                        "label": "Upload de Documento",
                        "document_field": "attachment",
                        "blocking": True,
                        "alert_message": "Documento obrigatório não foi enviado"
                    },
                    {
                        "id": "title_filled",
                        "type": "field_validation",
                        "label": "Título Preenchido",
                        "field_name": "title",
                        "blocking": False,
                        "alert_message": "Título não foi preenchido"
                    }
                ]
            },
            {
                "id": "approved",
                "name": "Aprovado",
                "order": 3,
                "color": "#00AA00",
                "prerequisites": [
                    {
                        "id": "manager_approval",
                        "type": "approval",
                        "label": "Aprovação do Gerente",
                        "approver_role": "manager",
                        "blocking": True,
                        "alert_message": "Aguardando aprovação do gerente"
                    }
                ]
            },
            {
                "id": "paid",
                "name": "Pago",
                "order": 4,
                "color": "#0000AA",
                "prerequisites": [
                    {
                        "id": "payment_confirmed",
                        "type": "payment",
                        "label": "Pagamento Confirmado",
                        "amount": 100.00,
                        "blocking": True,
                        "alert_message": "Pagamento não foi confirmado"
                    }
                ]
            },
            {
                "id": "completed",
                "name": "Concluído",
                "order": 5,
                "color": "#00FF00"
            }
        ],
        "agents": {
            "enabled": True,
            "flow_sequence": ["draft", "review", "approved", "paid", "completed"]
        }
    }

    workflow_manager.create_kanban(kanban_def)
    return "test_prereq_kanban"


# ========== PREREQUISITE CHECKER TESTS ==========

class TestPrerequisiteChecker:
    """Testa PrerequisiteChecker."""

    def test_no_prerequisites(self):
        """Testa estado sem pré-requisitos."""
        checker = PrerequisiteChecker()

        result = checker.check_prerequisites([], {}, "target_state")

        assert result['all_met'] is True
        assert result['total'] == 0
        assert result['met'] == 0
        assert len(result['warnings']) == 0
        assert len(result['errors']) == 0

    def test_document_upload_met(self):
        """Testa validação de documento (atendido)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "doc1",
            "type": "document_upload",
            "label": "Upload Documento",
            "document_field": "attachment",
            "blocking": True
        }]

        process_data = {
            "form_data": {
                "attachment": "documento.pdf"
            }
        }

        result = checker.check_prerequisites(prereqs, process_data, "review")

        assert result['all_met'] is True
        assert result['met'] == 1
        assert result['blocking_count'] == 0

    def test_document_upload_unmet(self):
        """Testa validação de documento (não atendido)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "doc1",
            "type": "document_upload",
            "label": "Upload Documento",
            "document_field": "attachment",
            "blocking": True,
            "alert_message": "Documento obrigatório"
        }]

        process_data = {
            "form_data": {}
        }

        result = checker.check_prerequisites(prereqs, process_data, "review")

        assert result['all_met'] is False
        assert result['met'] == 0
        assert result['unmet'] == 1
        assert result['blocking_count'] == 1
        assert len(result['errors']) == 1
        assert "Documento obrigatório" in result['errors'][0]

    def test_field_validation_met(self):
        """Testa validação de campo (atendido)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "field1",
            "type": "field_validation",
            "label": "Título",
            "field_name": "title",
            "blocking": False
        }]

        process_data = {
            "form_data": {
                "title": "Meu Título"
            }
        }

        result = checker.check_prerequisites(prereqs, process_data, "review")

        assert result['all_met'] is True
        assert result['met'] == 1

    def test_field_validation_with_expected_value(self):
        """Testa validação de campo com valor esperado."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "field1",
            "type": "field_validation",
            "label": "Status",
            "field_name": "status",
            "expected_value": "approved",
            "blocking": False
        }]

        # Valor correto
        process_data1 = {"form_data": {"status": "approved"}}
        result1 = checker.check_prerequisites(prereqs, process_data1, "review")
        assert result1['all_met'] is True

        # Valor incorreto
        process_data2 = {"form_data": {"status": "pending"}}
        result2 = checker.check_prerequisites(prereqs, process_data2, "review")
        assert result2['all_met'] is False

    def test_approval_met(self):
        """Testa validação de aprovação (atendida)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "approval1",
            "type": "approval",
            "label": "Aprovação Gerente",
            "approver_role": "manager",
            "blocking": True
        }]

        process_data = {
            "metadata": {
                "approvals": [
                    {"role": "manager", "approved": True, "user": "John"}
                ]
            }
        }

        result = checker.check_prerequisites(prereqs, process_data, "approved")

        assert result['all_met'] is True
        assert result['met'] == 1

    def test_approval_unmet(self):
        """Testa validação de aprovação (não atendida)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "approval1",
            "type": "approval",
            "label": "Aprovação Gerente",
            "approver_role": "manager",
            "blocking": True,
            "alert_message": "Aguardando aprovação"
        }]

        process_data = {"metadata": {}}

        result = checker.check_prerequisites(prereqs, process_data, "approved")

        assert result['all_met'] is False
        assert result['blocking_count'] == 1
        assert "Aguardando aprovação" in result['errors'][0]

    def test_payment_met(self):
        """Testa validação de pagamento (atendido)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "payment1",
            "type": "payment",
            "label": "Pagamento",
            "amount": 100.00,
            "blocking": True
        }]

        process_data = {
            "metadata": {
                "payment": {
                    "confirmed": True,
                    "amount": 150.00
                }
            }
        }

        result = checker.check_prerequisites(prereqs, process_data, "paid")

        assert result['all_met'] is True

    def test_payment_unmet(self):
        """Testa validação de pagamento (não atendido)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "payment1",
            "type": "payment",
            "label": "Pagamento",
            "amount": 100.00,
            "blocking": True
        }]

        # Pagamento não confirmado
        process_data1 = {"metadata": {"payment": {"confirmed": False}}}
        result1 = checker.check_prerequisites(prereqs, process_data1, "paid")
        assert result1['all_met'] is False

        # Valor insuficiente
        process_data2 = {"metadata": {"payment": {"confirmed": True, "amount": 50.00}}}
        result2 = checker.check_prerequisites(prereqs, process_data2, "paid")
        assert result2['all_met'] is False

    def test_external_dependency_met(self):
        """Testa validação de dependência externa (atendida)."""
        checker = PrerequisiteChecker()

        prereqs = [{
            "id": "ext1",
            "type": "external_dependency",
            "label": "API Externa",
            "dependency_key": "external_api",
            "blocking": True
        }]

        process_data = {
            "metadata": {
                "external_dependencies": {
                    "external_api": {"met": True}
                }
            }
        }

        result = checker.check_prerequisites(prereqs, process_data, "completed")

        assert result['all_met'] is True

    def test_custom_validator(self):
        """Testa validador customizado."""
        checker = PrerequisiteChecker()

        # Registra validador customizado
        def custom_validator(prereq, process_data):
            return process_data.get('form_data', {}).get('custom_field') == 'valid'

        checker.register_validator('custom_test', custom_validator)

        prereqs = [{
            "id": "custom1",
            "type": "custom",
            "label": "Custom Check",
            "validator_id": "custom_test",
            "blocking": False
        }]

        # Validação passa
        process_data1 = {"form_data": {"custom_field": "valid"}}
        result1 = checker.check_prerequisites(prereqs, process_data1, "completed")
        assert result1['all_met'] is True

        # Validação falha
        process_data2 = {"form_data": {"custom_field": "invalid"}}
        result2 = checker.check_prerequisites(prereqs, process_data2, "completed")
        assert result2['all_met'] is False

    def test_blocking_vs_nonblocking(self):
        """Testa diferença entre blocking e non-blocking."""
        checker = PrerequisiteChecker()

        prereqs = [
            {
                "id": "p1",
                "type": "field_validation",
                "label": "Campo Bloqueante",
                "field_name": "field1",
                "blocking": True,
                "alert_message": "Erro bloqueante"
            },
            {
                "id": "p2",
                "type": "field_validation",
                "label": "Campo Não Bloqueante",
                "field_name": "field2",
                "blocking": False,
                "alert_message": "Aviso não bloqueante"
            }
        ]

        process_data = {"form_data": {}}

        result = checker.check_prerequisites(prereqs, process_data, "review")

        assert result['all_met'] is False
        assert result['unmet'] == 2
        assert result['blocking_count'] == 1
        assert len(result['warnings']) == 1
        assert len(result['errors']) == 1


# ========== TRANSITION HANDLER TESTS ==========

class TestTransitionHandler:
    """Testa TransitionHandler."""

    def test_handle_valid_transition(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa validação de transição válida."""
        # Cria processo
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test"}
        )

        # Valida transição
        result = transition_handler.handle(process_id, "review")

        assert result['can_proceed'] is True  # SEMPRE True!
        assert result['transition_valid'] is True
        assert result['current_state'] == "draft"
        assert result['target_state'] == "review"
        assert 'prerequisites' in result

    def test_handle_invalid_state(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa validação com estado inválido."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test"}
        )

        result = transition_handler.handle(process_id, "nonexistent_state")

        assert result['can_proceed'] is True  # SEMPRE True! (filosofia)
        assert result['transition_valid'] is False
        assert len(result['errors']) > 0

    def test_handle_with_unmet_prerequisites(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa validação com pré-requisitos não atendidos."""
        # Cria processo sem documento e sem título
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={}  # Sem dados
        )

        # Valida transição para review (requer documento e título)
        result = transition_handler.handle(process_id, "review")

        # Deve permitir prosseguir mas mostrar avisos
        assert result['can_proceed'] is True  # SEMPRE True!
        assert result['transition_valid'] is True
        assert len(result['errors']) > 0  # Documento bloqueante
        assert len(result['warnings']) > 0  # Título não bloqueante
        assert result['prerequisites']['all_met'] is False

    def test_execute_valid_transition(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa execução de transição válida."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test", "attachment": "doc.pdf"}
        )

        # Executa transição
        result = transition_handler.execute(
            process_id=process_id,
            target_state="review",
            triggered_by="user",
            justification="Moving to review"
        )

        assert result['success'] is True
        assert result['previous_state'] == "draft"
        assert result['current_state'] == "review"
        assert 'transition_id' in result

        # Verifica que processo foi atualizado
        process = workflow_manager.get_process(process_id)
        assert process['current_state'] == "review"

    def test_execute_with_unmet_prerequisites(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa que execução SEMPRE ocorre, mesmo sem pré-requisitos."""
        # Cria processo SEM pré-requisitos atendidos
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={}  # Sem dados
        )

        # Executa transição (deve funcionar!)
        result = transition_handler.execute(
            process_id=process_id,
            target_state="review",
            triggered_by="user"
        )

        # FILOSOFIA: SEMPRE executa!
        assert result['success'] is True
        assert result['current_state'] == "review"

        # Mas registra os avisos/erros
        assert len(result['validation']['errors']) > 0

    def test_execute_invalid_state(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa que estado inválido lança exceção."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test"}
        )

        # Estado inválido DEVE lançar exceção
        with pytest.raises(ValueError, match="Invalid target state"):
            transition_handler.execute(process_id, "invalid_state")

    def test_get_available_transitions(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa listagem de transições disponíveis."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test", "attachment": "doc.pdf"}
        )

        available = transition_handler.get_available_transitions(process_id)

        # Deve listar todos os estados exceto o atual (draft)
        assert len(available) == 4  # review, approved, paid, completed

        # Verifica estrutura
        for trans in available:
            assert 'state_id' in trans
            assert 'state_name' in trans
            assert 'prerequisites' in trans
            assert 'all_prerequisites_met' in trans

        # Estado review deve ter pré-requisitos atendidos
        review = next(t for t in available if t['state_id'] == 'review')
        assert review['all_prerequisites_met'] is True

    def test_get_transition_history(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa busca de histórico de transições."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test"}
        )

        # Executa múltiplas transições
        transition_handler.execute(process_id, "review", "user", "First transition")
        transition_handler.execute(process_id, "approved", "user", "Second transition")

        # Busca histórico
        history = transition_handler.get_transition_history(process_id)

        assert len(history) == 2
        # Mais recente primeiro
        assert history[0]['to_state'] == "approved"
        assert history[1]['to_state'] == "review"

    def test_get_next_auto_state(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa identificação de próximo estado automático."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={"title": "Test"}
        )

        # Estado atual: draft, próximo: review
        next_state = transition_handler.get_next_auto_state(process_id)
        assert next_state == "review"

        # Avança para review
        transition_handler.execute(process_id, "review")

        # Agora próximo: approved
        next_state = transition_handler.get_next_auto_state(process_id)
        assert next_state == "approved"

    def test_force_flag(self, transition_handler, kanban_with_prerequisites, workflow_manager):
        """Testa flag force ignora avisos."""
        process_id = workflow_manager.create_process(
            kanban_name=kanban_with_prerequisites,
            form_data={}  # Sem dados
        )

        # Sem force: mostra avisos
        result1 = transition_handler.handle(process_id, "review", force=False)
        assert len(result1['warnings']) > 0

        # Com force: ignora avisos
        result2 = transition_handler.handle(process_id, "review", force=True)
        assert result2['force'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
