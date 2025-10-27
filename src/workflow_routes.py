"""
Flask routes for Workflow API

Endpoints REST para gerenciamento de Kanbans e Processos.
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

from workflow.engine.workflow_manager import WorkflowManager
from workflow.engine.transition_handler import TransitionHandler

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

# Initialize WorkflowManager and TransitionHandler (singletons)
workflow_manager = WorkflowManager()
transition_handler = TransitionHandler(workflow_manager)


# ========== ERROR HANDLERS ==========

@workflow_bp.errorhandler(ValueError)
def handle_value_error(e):
    """Handle ValueError exceptions."""
    return jsonify({'error': str(e)}), 400


@workflow_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handle generic exceptions."""
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


# ========== KANBAN ENDPOINTS ==========

@workflow_bp.route('/kanbans', methods=['POST'])
def create_kanban():
    """
    Cria um novo Kanban.

    Request Body:
        JSON com definição completa do Kanban

    Returns:
        201: Kanban criado com sucesso
        400: Definição inválida
    """
    try:
        definition = request.get_json()

        if not definition:
            return jsonify({'error': 'Request body is required'}), 400

        kanban_name = workflow_manager.create_kanban(definition)

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'message': f"Kanban '{kanban_name}' created successfully"
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@workflow_bp.route('/kanbans', methods=['GET'])
def list_kanbans():
    """
    Lista todos os Kanbans disponíveis.

    Returns:
        200: Lista de Kanbans
    """
    kanbans = workflow_manager.list_kanbans()

    return jsonify({
        'success': True,
        'count': len(kanbans),
        'kanbans': kanbans
    }), 200


@workflow_bp.route('/kanbans/<kanban_name>', methods=['GET'])
def get_kanban(kanban_name: str):
    """
    Busca definição de um Kanban específico.

    Args:
        kanban_name: Nome do Kanban

    Returns:
        200: Definição do Kanban
        404: Kanban não encontrado
    """
    try:
        definition = workflow_manager.get_kanban(kanban_name)

        return jsonify({
            'success': True,
            'kanban': definition
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@workflow_bp.route('/kanbans/<kanban_name>', methods=['PUT'])
def update_kanban(kanban_name: str):
    """
    Atualiza definição de um Kanban existente.

    Args:
        kanban_name: Nome do Kanban

    Request Body:
        JSON com nova definição

    Returns:
        200: Kanban atualizado
        400: Definição inválida
        404: Kanban não encontrado
    """
    try:
        definition = request.get_json()

        if not definition:
            return jsonify({'error': 'Request body is required'}), 400

        # Garante que kanban_name no body corresponde ao da URL
        definition['kanban_name'] = kanban_name

        workflow_manager.update_kanban(kanban_name, definition)

        return jsonify({
            'success': True,
            'message': f"Kanban '{kanban_name}' updated successfully"
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@workflow_bp.route('/kanbans/<kanban_name>', methods=['DELETE'])
def delete_kanban(kanban_name: str):
    """
    Deleta um Kanban.

    Args:
        kanban_name: Nome do Kanban

    Query Params:
        force: Se 'true', deleta mesmo com processos ativos

    Returns:
        200: Kanban deletado
        400: Kanban tem processos ativos e force=false
        404: Kanban não encontrado
    """
    try:
        force = request.args.get('force', 'false').lower() == 'true'

        workflow_manager.delete_kanban(kanban_name, force=force)

        return jsonify({
            'success': True,
            'message': f"Kanban '{kanban_name}' deleted successfully"
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ========== PROCESS ENDPOINTS ==========

@workflow_bp.route('/processes', methods=['POST'])
def create_process():
    """
    Cria um novo processo.

    Request Body:
        {
            "kanban_name": "pedidos",
            "form_data": {...},
            "initial_state": "orcamento" (optional),
            "metadata": {...} (optional)
        }

    Returns:
        201: Processo criado
        400: Dados inválidos
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        kanban_name = data.get('kanban_name')
        form_data = data.get('form_data', {})
        initial_state = data.get('initial_state')
        metadata = data.get('metadata')

        if not kanban_name:
            return jsonify({'error': 'kanban_name is required'}), 400

        process_id = workflow_manager.create_process(
            kanban_name=kanban_name,
            form_data=form_data,
            initial_state=initial_state,
            metadata=metadata
        )

        return jsonify({
            'success': True,
            'process_id': process_id,
            'message': f"Process '{process_id}' created successfully"
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@workflow_bp.route('/processes/<process_id>', methods=['GET'])
def get_process(process_id: str):
    """
    Busca um processo por ID.

    Args:
        process_id: ID do processo

    Query Params:
        kanban_name: Nome do Kanban (opcional, melhora performance)

    Returns:
        200: Dados do processo
        404: Processo não encontrado
    """
    try:
        kanban_name = request.args.get('kanban_name')

        process = workflow_manager.get_process(process_id, kanban_name)

        return jsonify({
            'success': True,
            'process': process
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@workflow_bp.route('/processes', methods=['GET'])
def list_processes():
    """
    Lista processos de um Kanban.

    Query Params:
        kanban (required): Nome do Kanban
        state: Filtrar por estado
        limit: Limitar quantidade de resultados

    Returns:
        200: Lista de processos
        400: kanban não fornecido
    """
    try:
        kanban_name = request.args.get('kanban')

        if not kanban_name:
            return jsonify({'error': 'Query parameter "kanban" is required'}), 400

        state = request.args.get('state')
        limit = request.args.get('limit', type=int)

        processes = workflow_manager.list_processes(
            kanban_name=kanban_name,
            state=state,
            limit=limit
        )

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'state': state,
            'count': len(processes),
            'processes': processes
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@workflow_bp.route('/processes/<process_id>', methods=['PUT'])
def update_process(process_id: str):
    """
    Atualiza dados de um processo.

    Args:
        process_id: ID do processo

    Request Body:
        JSON com campos a atualizar

    Returns:
        200: Processo atualizado
        400: Dados inválidos
        404: Processo não encontrado
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        workflow_manager.update_process(process_id, data)

        return jsonify({
            'success': True,
            'message': f"Process '{process_id}' updated successfully"
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@workflow_bp.route('/processes/<process_id>', methods=['DELETE'])
def delete_process(process_id: str):
    """
    Deleta um processo.

    Args:
        process_id: ID do processo

    Returns:
        200: Processo deletado
        404: Processo não encontrado
    """
    try:
        workflow_manager.delete_process(process_id)

        return jsonify({
            'success': True,
            'message': f"Process '{process_id}' deleted successfully"
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ========== TRANSITION ENDPOINTS ==========

@workflow_bp.route('/processes/<process_id>/transition', methods=['POST'])
def execute_transition(process_id: str):
    """
    Executa transição de estado.

    IMPORTANTE: SEMPRE executa a transição (filosofia "Avisar, Não Bloquear").

    Args:
        process_id: ID do processo

    Request Body:
        {
            "target_state": "novo_estado",
            "triggered_by": "user" (optional),
            "justification": "..." (optional),
            "metadata": {...} (optional),
            "force": false (optional)
        }

    Returns:
        200: Transição executada
        400: Dados inválidos ou estado alvo inválido
        404: Processo não encontrado
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        target_state = data.get('target_state')
        if not target_state:
            return jsonify({'error': 'target_state is required'}), 400

        triggered_by = data.get('triggered_by', 'user')
        justification = data.get('justification')
        metadata = data.get('metadata')
        force = data.get('force', False)

        result = transition_handler.execute(
            process_id=process_id,
            target_state=target_state,
            triggered_by=triggered_by,
            justification=justification,
            metadata=metadata,
            force=force
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@workflow_bp.route('/processes/<process_id>/transition/validate', methods=['POST'])
def validate_transition(process_id: str):
    """
    Valida transição sem executá-la.

    Args:
        process_id: ID do processo

    Request Body:
        {
            "target_state": "novo_estado",
            "triggered_by": "user" (optional),
            "justification": "..." (optional),
            "force": false (optional)
        }

    Returns:
        200: Validação completa
        400: Dados inválidos
        404: Processo não encontrado
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        target_state = data.get('target_state')
        if not target_state:
            return jsonify({'error': 'target_state is required'}), 400

        triggered_by = data.get('triggered_by', 'user')
        justification = data.get('justification')
        force = data.get('force', False)

        result = transition_handler.handle(
            process_id=process_id,
            target_state=target_state,
            triggered_by=triggered_by,
            justification=justification,
            force=force
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@workflow_bp.route('/processes/<process_id>/transitions/available', methods=['GET'])
def get_available_transitions(process_id: str):
    """
    Lista transições disponíveis para um processo.

    Args:
        process_id: ID do processo

    Returns:
        200: Lista de transições disponíveis
        404: Processo não encontrado
    """
    try:
        available = transition_handler.get_available_transitions(process_id)

        return jsonify({
            'success': True,
            'process_id': process_id,
            'count': len(available),
            'transitions': available
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@workflow_bp.route('/processes/<process_id>/transitions/history', methods=['GET'])
def get_transition_history(process_id: str):
    """
    Busca histórico de transições de um processo.

    Args:
        process_id: ID do processo

    Query Params:
        limit: Limitar quantidade de resultados

    Returns:
        200: Histórico de transições
        404: Processo não encontrado
    """
    try:
        limit = request.args.get('limit', type=int)

        history = transition_handler.get_transition_history(process_id, limit)

        return jsonify({
            'success': True,
            'process_id': process_id,
            'count': len(history),
            'history': history
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ========== AUDIT ENDPOINTS ==========

@workflow_bp.route('/audit/<kanban_name>/timeline/<process_id>', methods=['GET'])
def get_process_timeline(kanban_name: str, process_id: str):
    """
    Busca timeline completo de um processo.

    Args:
        kanban_name: Nome do Kanban
        process_id: ID do processo

    Query Params:
        include_transitions: Incluir transições (default: true)
        include_actions: Incluir ações (default: true)

    Returns:
        200: Timeline do processo
        404: Processo não encontrado
    """
    try:
        from workflow.engine.audit_logger import AuditLogger

        include_transitions = request.args.get('include_transitions', 'true').lower() == 'true'
        include_actions = request.args.get('include_actions', 'true').lower() == 'true'

        audit_logger = AuditLogger(kanban_name)
        timeline = audit_logger.get_process_timeline(
            process_id,
            include_transitions=include_transitions,
            include_actions=include_actions
        )

        return jsonify({
            'success': True,
            'process_id': process_id,
            'kanban_name': kanban_name,
            'count': len(timeline),
            'timeline': timeline
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/audit/<kanban_name>/actions', methods=['GET'])
def get_audit_logs(kanban_name: str):
    """
    Busca logs de ações com filtros.

    Args:
        kanban_name: Nome do Kanban

    Query Params:
        action_type: Filtrar por tipo de ação
        performed_by: Filtrar por usuário
        entity_id: Filtrar por entidade
        start_date: Data inicial (ISO)
        end_date: Data final (ISO)
        limit: Limitar resultados

    Returns:
        200: Logs de ações
    """
    try:
        from workflow.engine.audit_logger import AuditLogger

        action_type = request.args.get('action_type')
        performed_by = request.args.get('performed_by')
        entity_id = request.args.get('entity_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int)

        audit_logger = AuditLogger(kanban_name)
        logs = audit_logger.get_audit_logs(
            action_type=action_type,
            performed_by=performed_by,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'count': len(logs),
            'logs': logs
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/audit/<kanban_name>/transitions', methods=['GET'])
def get_transition_logs(kanban_name: str):
    """
    Busca logs de transições com filtros.

    Args:
        kanban_name: Nome do Kanban

    Query Params:
        from_state: Filtrar por estado origem
        to_state: Filtrar por estado destino
        triggered_by: Filtrar por quem disparou
        only_anomalies: Apenas transições anômalas (true/false)
        start_date: Data inicial (ISO)
        end_date: Data final (ISO)
        limit: Limitar resultados

    Returns:
        200: Logs de transições
    """
    try:
        from workflow.engine.audit_logger import AuditLogger

        from_state = request.args.get('from_state')
        to_state = request.args.get('to_state')
        triggered_by = request.args.get('triggered_by')
        only_anomalies = request.args.get('only_anomalies', 'false').lower() == 'true'
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int)

        audit_logger = AuditLogger(kanban_name)
        logs = audit_logger.get_transition_logs(
            from_state=from_state,
            to_state=to_state,
            triggered_by=triggered_by,
            only_anomalies=only_anomalies,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'count': len(logs),
            'logs': logs
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/audit/<kanban_name>/summary', methods=['GET'])
def get_activity_summary(kanban_name: str):
    """
    Calcula resumo de atividade do workflow.

    Args:
        kanban_name: Nome do Kanban

    Query Params:
        start_date: Data inicial (ISO)
        end_date: Data final (ISO)

    Returns:
        200: Resumo de atividade
    """
    try:
        from workflow.engine.audit_logger import AuditLogger

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        audit_logger = AuditLogger(kanban_name)
        summary = audit_logger.get_activity_summary(
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'summary': summary
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/audit/<kanban_name>/metrics/<process_id>', methods=['GET'])
def get_state_metrics(kanban_name: str, process_id: str):
    """
    Calcula métricas de tempo em estados para um processo.

    Args:
        kanban_name: Nome do Kanban
        process_id: ID do processo

    Returns:
        200: Métricas de tempo por estado
    """
    try:
        from workflow.engine.audit_logger import AuditLogger

        audit_logger = AuditLogger(kanban_name)
        metrics = audit_logger.get_state_metrics(process_id)

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'metrics': metrics
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== AUTO-TRANSITION ENDPOINTS ==========

@workflow_bp.route('/auto-transition/process/<process_id>', methods=['POST'])
def auto_transition_process(process_id: str):
    """
    Executa auto-transição para um processo específico.

    Args:
        process_id: ID do processo

    Query Params:
        max_transitions: Máximo de transições consecutivas (default: 10)

    Returns:
        200: Processamento concluído
        404: Processo não encontrado
    """
    try:
        from workflow.engine.auto_transition_engine import AutoTransitionEngine

        max_transitions = request.args.get('max_transitions', 10, type=int)

        engine = AutoTransitionEngine(workflow_manager)
        result = engine.check_and_execute(process_id, max_transitions=max_transitions)

        return jsonify({
            'success': True,
            'result': result
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/auto-transition/kanban/<kanban_name>', methods=['POST'])
def auto_transition_kanban(kanban_name: str):
    """
    Processa todos os processos de um Kanban.

    Args:
        kanban_name: Nome do Kanban

    Query Params:
        max_processes: Máximo de processos a processar

    Returns:
        200: Processamento concluído
    """
    try:
        from workflow.engine.auto_transition_engine import AutoTransitionEngine

        max_processes = request.args.get('max_processes', type=int)

        engine = AutoTransitionEngine(workflow_manager)
        result = engine.process_kanban(kanban_name, max_processes=max_processes)

        return jsonify({
            'success': True,
            'result': result
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/auto-transition/all', methods=['POST'])
def auto_transition_all():
    """
    Processa todos os Kanbans do sistema.

    Returns:
        200: Processamento concluído
    """
    try:
        from workflow.engine.auto_transition_engine import AutoTransitionEngine

        engine = AutoTransitionEngine(workflow_manager)
        result = engine.process_all_kanbans()

        return jsonify({
            'success': True,
            'result': result
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/auto-transition/eligible/<kanban_name>', methods=['GET'])
def get_eligible_processes(kanban_name: str):
    """
    Lista processos elegíveis para auto-transição.

    Args:
        kanban_name: Nome do Kanban

    Returns:
        200: Lista de processos elegíveis
    """
    try:
        from workflow.engine.auto_transition_engine import AutoTransitionEngine

        engine = AutoTransitionEngine(workflow_manager)
        eligible = engine.get_eligible_processes(kanban_name)

        return jsonify({
            'success': True,
            'kanban_name': kanban_name,
            'count': len(eligible),
            'eligible_processes': eligible
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== UTILITY ENDPOINTS ==========

@workflow_bp.route('/reload-cache', methods=['POST'])
def reload_cache():
    """
    Recarrega cache de definições de Kanbans.

    Returns:
        200: Cache recarregado
    """
    count = workflow_manager.reload_cache()

    return jsonify({
        'success': True,
        'message': f"Reloaded {count} Kanbans into cache"
    }), 200


# ========== UI ENDPOINTS ==========

@workflow_bp.route('/board/<kanban_name>', methods=['GET'])
def show_board(kanban_name: str):
    """
    Exibe board visual do Kanban.

    Args:
        kanban_name: Nome do Kanban

    Returns:
        HTML: Página do board
    """
    try:
        from flask import render_template

        kanban_def = workflow_manager.get_kanban(kanban_name)

        return render_template(
            'workflow/board.html',
            kanban=kanban_def
        )

    except ValueError as e:
        return f"<h1>Erro: {e}</h1>", 404
    except Exception as e:
        return f"<h1>Erro interno: {e}</h1>", 500


@workflow_bp.route('/kanbans-list', methods=['GET'])
def list_kanbans_ui():
    """
    Lista todos os Kanbans para UI.

    Returns:
        HTML: Página com lista de Kanbans
    """
    try:
        from flask import render_template

        kanbans = workflow_manager.list_kanbans()

        return render_template(
            'workflow/kanbans_list.html',
            kanbans=kanbans
        )

    except Exception as e:
        return f"<h1>Erro: {e}</h1>", 500


# Export blueprint
__all__ = ['workflow_bp']
