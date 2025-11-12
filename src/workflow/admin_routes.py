"""
Admin Routes - Interface administrativa para gestão de Workflows/Kanbans

Funcionalidades:
- CRUD completo de kanbans
- Vinculação de formulários
- Configuração de pré-requisitos
- Definição de estados e transições
- Sistema de notificações
- Geração automática de JSON
- Geração de workflows via IA
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def convert_registry_to_editor_format(kanban_def: dict) -> dict:
    """
    Convert registry format (list states) to editor format (dict states)

    Registry format:
    {
        "states": [{"id": "novo", "name": "Novo"}],
        "recommended_transitions": [{"from": "novo", "to": "concluido"}]
    }

    Editor format:
    {
        "states": {"novo": {"name": "Novo", "transitions": ["concluido"]}}
    }
    """
    # If already in editor format (states is dict), return as is
    if isinstance(kanban_def.get("states"), dict):
        return kanban_def

    editor_kanban = {
        "id": kanban_def["id"],
        "name": kanban_def["name"],
        "description": kanban_def.get("description", ""),
        "states": {},
        "initial_state": kanban_def.get("initial_state"),
        "created_at": kanban_def.get("created_at"),
        "updated_at": kanban_def.get("updated_at"),
        "form_mappings": kanban_def.get("form_mappings", []),
    }

    # Convert states from list to dict
    for state in kanban_def.get("states", []):
        state_id = state["id"]
        editor_kanban["states"][state_id] = {
            "name": state["name"],
            "type": state.get("type", "intermediate"),
            "description": state.get("description", ""),
            "color": state.get("color", "#95a5a6"),
            "transitions": [],
        }

    # Extract transitions from recommended_transitions
    for transition in kanban_def.get("recommended_transitions", []):
        from_state = transition["from"]
        to_state = transition["to"]
        if from_state in editor_kanban["states"]:
            editor_kanban["states"][from_state]["transitions"].append(to_state)

    return editor_kanban


def register_admin_routes(
    app, kanban_registry, kanban_editor, workflow_repo, agent_orchestrator
):
    """
    Registra rotas administrativas do workflow

    Args:
        app: Flask application instance
        kanban_registry: KanbanRegistry instance
        kanban_editor: KanbanEditor instance
        workflow_repo: WorkflowRepository instance
        agent_orchestrator: AgentOrchestrator instance
    """

    # Criar blueprint
    admin_bp = Blueprint(
        "workflow_admin",
        __name__,
        url_prefix="/admin/workflow",
        template_folder="../templates/admin",
    )

    # ========== DASHBOARD PRINCIPAL ==========

    @admin_bp.route("/")
    def dashboard():
        """Dashboard principal da área administrativa"""
        try:
            # Estatísticas gerais
            all_kanbans = kanban_registry.get_all_kanbans()
            total_kanbans = len(all_kanbans)

            # Contar processos totais
            all_processes = workflow_repo.get_all_processes()
            total_processes = len(all_processes)

            # Contar formulários com kanbans vinculados
            total_forms = len(
                set(
                    form
                    for kanban in all_kanbans.values()
                    for form in kanban.get("linked_forms", [])
                )
            )

            # Kanbans recentes (ordenados por updated_at)
            recent_kanbans = []
            for kanban_id, kanban in all_kanbans.items():
                # Contar processos deste kanban
                kanban_processes = [
                    p for p in all_processes if p.get("kanban_id") == kanban_id
                ]

                recent_kanbans.append(
                    {
                        "id": kanban_id,
                        "name": kanban.get("name", kanban_id),
                        "description": kanban.get("description", ""),
                        "process_count": len(kanban_processes),
                        "state_count": len(kanban.get("states", [])),
                        "updated_at": kanban.get("updated_at", ""),
                    }
                )

            # Ordenar por updated_at (mais recentes primeiro)
            recent_kanbans.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            return render_template(
                "admin_dashboard.html",
                total_kanbans=total_kanbans,
                total_processes=total_processes,
                total_forms=total_forms,
                recent_kanbans=recent_kanbans[:5],  # Top 5
            )

        except Exception as e:
            logger.error(f"Error rendering admin dashboard: {e}")
            return f"Erro ao carregar dashboard: {str(e)}", 500

    # ========== LISTA DE KANBANS ==========

    @admin_bp.route("/kanbans")
    def list_kanbans():
        """Lista todos os kanbans"""
        try:
            all_kanbans = kanban_registry.get_all_kanbans()
            all_processes = workflow_repo.get_all_processes()

            kanbans_list = []
            for kanban_id, kanban in all_kanbans.items():
                # Contar processos ativos deste kanban
                active_processes = [
                    p for p in all_processes if p.get("kanban_id") == kanban_id
                ]

                # Contar transições
                transitions = kanban.get(
                    "recommended_transitions", kanban.get("transitions", [])
                )

                kanbans_list.append(
                    {
                        "id": kanban_id,
                        "name": kanban.get("name", kanban_id),
                        "description": kanban.get("description", ""),
                        "state_count": len(kanban.get("states", [])),
                        "transition_count": len(transitions),
                        "linked_forms": kanban.get("linked_forms", []),
                        "active_processes": len(active_processes),
                    }
                )

            return render_template("kanban_list.html", kanbans=kanbans_list)

        except Exception as e:
            logger.error(f"Error listing kanbans: {e}")
            return f"Erro ao listar kanbans: {str(e)}", 500

    # ========== CRIAR KANBAN ==========

    @admin_bp.route("/kanbans/create", methods=["GET", "POST"])
    def create_kanban():
        """Criar novo kanban"""
        if request.method == "GET":
            return render_template("kanban_create.html")

        try:
            # Obter dados do formulário
            kanban_id = request.form.get("kanban_id", "").strip()
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()

            if not kanban_id or not name:
                return render_template(
                    "kanban_create.html", error="ID e Nome são obrigatórios"
                )

            # Verificar se já existe
            if kanban_registry.get_kanban(kanban_id):
                return render_template(
                    "kanban_create.html", error=f'Kanban com ID "{kanban_id}" já existe'
                )

            # Criar kanban básico usando KanbanEditor
            kanban_editor.create_kanban(kanban_id, name, description)

            # Adicionar estado inicial padrão
            kanban_editor.add_state("novo", "Novo", type="initial", color="#3498db")

            # Adicionar estado final padrão
            kanban_editor.add_state(
                "concluido", "Concluído", type="final", color="#27ae60"
            )

            # Adicionar transição entre estados padrão
            kanban_editor.add_transition("novo", "concluido")

            # Salvar
            kanban_editor.save()

            logger.info(f"Created kanban: {kanban_id}")

            return redirect(url_for("workflow_admin.edit_kanban", kanban_id=kanban_id))

        except Exception as e:
            logger.error(f"Error creating kanban: {e}")
            return render_template(
                "kanban_create.html", error=f"Erro ao criar kanban: {str(e)}"
            )

    # ========== EDITAR KANBAN ==========

    @admin_bp.route("/kanbans/<kanban_id>/edit", methods=["GET", "POST"])
    def edit_kanban(kanban_id):
        """Editar kanban existente"""
        if request.method == "GET":
            kanban = kanban_registry.get_kanban(kanban_id)
            if not kanban:
                return f"Kanban '{kanban_id}' não encontrado", 404

            # Convert from registry format (list) to editor format (dict) for template
            kanban_editor_format = convert_registry_to_editor_format(kanban)

            return render_template("kanban_edit.html", kanban=kanban_editor_format)

        try:
            # Obter dados do formulário
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()

            if not name:
                kanban = kanban_registry.get_kanban(kanban_id)
                kanban_editor_format = convert_registry_to_editor_format(kanban)
                return render_template(
                    "kanban_edit.html",
                    kanban=kanban_editor_format,
                    error="Nome é obrigatório",
                )

            # Carregar e atualizar
            kanban_editor.load_kanban(kanban_id)
            kanban_editor.current_kanban["name"] = name
            kanban_editor.current_kanban["description"] = description
            kanban_editor.save()

            logger.info(f"Updated kanban: {kanban_id}")

            return redirect(url_for("workflow_admin.list_kanbans"))

        except Exception as e:
            logger.error(f"Error updating kanban: {e}")
            kanban = kanban_registry.get_kanban(kanban_id)
            kanban_editor_format = convert_registry_to_editor_format(kanban)
            return render_template(
                "kanban_edit.html",
                kanban=kanban_editor_format,
                error=f"Erro ao atualizar kanban: {str(e)}",
            )

    # ========== EXCLUIR KANBAN ==========

    @admin_bp.route("/kanbans/<kanban_id>/delete", methods=["GET", "POST"])
    def delete_kanban(kanban_id):
        """Excluir kanban"""
        if request.method == "GET":
            kanban = kanban_registry.get_kanban(kanban_id)
            if not kanban:
                return f"Kanban '{kanban_id}' não encontrado", 404

            # Contar processos vinculados
            all_processes = workflow_repo.get_all_processes()
            linked_processes = [
                p for p in all_processes if p.get("kanban_id") == kanban_id
            ]

            return render_template(
                "kanban_delete_confirm.html",
                kanban=kanban,
                process_count=len(linked_processes),
            )

        try:
            # Excluir kanban
            kanban_registry.unregister_kanban(kanban_id, delete_from_disk=True)

            logger.info(f"Deleted kanban: {kanban_id}")

            return redirect(url_for("workflow_admin.list_kanbans"))

        except Exception as e:
            logger.error(f"Error deleting kanban: {e}")
            return f"Erro ao excluir kanban: {str(e)}", 500

    # ========== VINCULAR FORMULÁRIOS ==========

    @admin_bp.route("/mappings")
    def form_mappings():
        """Interface de vinculação de formulários"""
        try:
            # Obter todos kanbans
            all_kanbans = kanban_registry.get_all_kanbans()

            # Obter todos formulários disponíveis
            # (isso precisa buscar do diretório de specs)
            from VibeCForms import scan_specs_directory

            all_forms = scan_specs_directory()

            return render_template(
                "form_mappings.html", kanbans=all_kanbans, forms=all_forms
            )

        except Exception as e:
            logger.error(f"Error rendering form mappings: {e}")
            return f"Erro ao carregar mapeamentos: {str(e)}", 500

    # ========== API HELPERS ==========

    @admin_bp.route("/api/forms")
    def api_get_forms():
        """API: Listar formulários disponíveis"""
        try:
            from VibeCForms import scan_specs_directory

            forms = scan_specs_directory()

            return jsonify(
                {
                    "success": True,
                    "forms": [
                        {
                            "path": form["path"],
                            "title": form["title"],
                            "category": form.get("category", ""),
                        }
                        for form in forms
                    ],
                }
            )

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Registrar blueprint
    app.register_blueprint(admin_bp)
    logger.info("Registered Workflow Admin Blueprint at /admin/workflow")
