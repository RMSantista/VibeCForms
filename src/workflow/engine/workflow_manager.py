"""
Workflow Manager - Gerenciamento de Kanbans e Processos

Este módulo implementa o gerenciador central do sistema de workflows,
responsável por CRUD de Kanbans (definições) e Processos (instâncias).

Funcionalidades:
- Carregamento de definições de Kanbans (JSON)
- Validação de estrutura de Kanbans
- CRUD completo de Kanbans
- CRUD completo de Processos
- Cache de definições em memória
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from jsonschema import validate, ValidationError, Draft7Validator

# Import WorkflowRepository
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflow.repository.workflow_repository import WorkflowRepository

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    Gerenciador central de workflows.

    Responsabilidades:
    - CRUD de Kanbans (definições de processos)
    - CRUD de Processos (instâncias)
    - Carregamento e validação de definições
    - Cache de definições em memória
    """

    # JSON Schema para validação de definições de Kanban
    KANBAN_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["kanban_name", "title", "states"],
        "properties": {
            "kanban_name": {"type": "string", "minLength": 1},
            "title": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "icon": {"type": "string"},
            "created_at": {"type": "string"},
            "states": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "name", "order"],
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "order": {"type": "integer"},
                        "color": {"type": "string"},
                        "icon": {"type": "string"},
                        "description": {"type": "string"},
                        "prerequisites": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "type", "label"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "type": {"type": "string"},
                                    "label": {"type": "string"},
                                    "blocking": {"type": "boolean"},
                                    "alert_message": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "agents": {"type": "object"},
            "ai_settings": {"type": "object"},
            "form_integration": {"type": "object"},
            "metadata": {"type": "object"}
        }
    }

    def __init__(self, workflows_dir: Optional[str] = None):
        """
        Inicializa WorkflowManager.

        Args:
            workflows_dir: Diretório com definições de workflows.
                          Default: src/workflows/
        """
        if workflows_dir is None:
            # Default path
            project_root = Path(__file__).parent.parent.parent.parent
            workflows_dir = project_root / "src" / "workflows"

        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Cache de definições de Kanbans em memória
        self._kanban_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"WorkflowManager initialized: workflows_dir={self.workflows_dir}")

    # ========== OPERAÇÕES DE KANBAN (Definições) ==========

    def create_kanban(self, definition: Dict[str, Any]) -> str:
        """
        Cria uma nova definição de Kanban.

        Args:
            definition: Dicionário com definição do Kanban

        Returns:
            Nome do Kanban criado

        Raises:
            ValueError: Se definição é inválida ou Kanban já existe
        """
        # Valida estrutura
        self._validate_kanban_definition(definition)

        kanban_name = definition['kanban_name']

        # Verifica se já existe
        kanban_file = self.workflows_dir / f"{kanban_name}.json"
        if kanban_file.exists():
            raise ValueError(f"Kanban '{kanban_name}' already exists")

        # Adiciona timestamps
        if 'created_at' not in definition:
            definition['created_at'] = datetime.utcnow().isoformat()
        if 'metadata' not in definition:
            definition['metadata'] = {}
        definition['metadata']['last_modified'] = datetime.utcnow().isoformat()

        # Salva arquivo JSON
        with open(kanban_file, 'w', encoding='utf-8') as f:
            json.dump(definition, f, indent=2, ensure_ascii=False)

        # Adiciona ao cache
        self._kanban_cache[kanban_name] = definition

        logger.info(f"Created Kanban: {kanban_name}")
        return kanban_name

    def get_kanban(self, kanban_name: str) -> Dict[str, Any]:
        """
        Busca definição de um Kanban.

        Args:
            kanban_name: Nome do Kanban

        Returns:
            Dicionário com definição do Kanban

        Raises:
            ValueError: Se Kanban não existe
        """
        # Verifica cache
        if kanban_name in self._kanban_cache:
            logger.debug(f"Kanban '{kanban_name}' loaded from cache")
            return self._kanban_cache[kanban_name].copy()

        # Carrega do arquivo
        kanban_file = self.workflows_dir / f"{kanban_name}.json"
        if not kanban_file.exists():
            raise ValueError(f"Kanban '{kanban_name}' not found")

        try:
            with open(kanban_file, 'r', encoding='utf-8') as f:
                definition = json.load(f)

            # Adiciona ao cache
            self._kanban_cache[kanban_name] = definition

            logger.debug(f"Kanban '{kanban_name}' loaded from file")
            return definition.copy()

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Kanban '{kanban_name}': {e}")

    def list_kanbans(self) -> List[Dict[str, Any]]:
        """
        Lista todos os Kanbans disponíveis.

        Returns:
            Lista de dicionários com informações básicas dos Kanbans
        """
        kanbans = []

        # Percorre arquivos .json no diretório de workflows
        for kanban_file in self.workflows_dir.glob("*.json"):
            try:
                definition = self.get_kanban(kanban_file.stem)

                # Retorna apenas informações básicas
                kanbans.append({
                    'kanban_name': definition['kanban_name'],
                    'title': definition['title'],
                    'description': definition.get('description', ''),
                    'icon': definition.get('icon', 'fa-tasks'),
                    'states_count': len(definition['states']),
                    'created_at': definition.get('created_at'),
                    'last_modified': definition.get('metadata', {}).get('last_modified')
                })

            except Exception as e:
                logger.error(f"Error loading Kanban {kanban_file.stem}: {e}")
                continue

        # Ordena por nome
        kanbans.sort(key=lambda k: k['title'])

        logger.debug(f"Listed {len(kanbans)} Kanbans")
        return kanbans

    def update_kanban(self, kanban_name: str, definition: Dict[str, Any]) -> bool:
        """
        Atualiza definição de um Kanban existente.

        Args:
            kanban_name: Nome do Kanban
            definition: Nova definição

        Returns:
            True se atualizado com sucesso

        Raises:
            ValueError: Se Kanban não existe ou definição inválida
        """
        # Verifica se existe
        kanban_file = self.workflows_dir / f"{kanban_name}.json"
        if not kanban_file.exists():
            raise ValueError(f"Kanban '{kanban_name}' not found")

        # Valida estrutura
        self._validate_kanban_definition(definition)

        # Atualiza timestamp
        if 'metadata' not in definition:
            definition['metadata'] = {}
        definition['metadata']['last_modified'] = datetime.utcnow().isoformat()

        # Salva arquivo
        with open(kanban_file, 'w', encoding='utf-8') as f:
            json.dump(definition, f, indent=2, ensure_ascii=False)

        # Atualiza cache
        self._kanban_cache[kanban_name] = definition

        logger.info(f"Updated Kanban: {kanban_name}")
        return True

    def delete_kanban(self, kanban_name: str, force: bool = False) -> bool:
        """
        Deleta um Kanban.

        Args:
            kanban_name: Nome do Kanban
            force: Se True, deleta mesmo com processos ativos

        Returns:
            True se deletado com sucesso

        Raises:
            ValueError: Se Kanban não existe ou tem processos ativos
        """
        # Verifica se existe
        kanban_file = self.workflows_dir / f"{kanban_name}.json"
        if not kanban_file.exists():
            raise ValueError(f"Kanban '{kanban_name}' not found")

        # Verifica se tem processos ativos
        if not force:
            processes_repo = WorkflowRepository(kanban_name, 'processes')
            all_processes = processes_repo.read_all()

            if len(all_processes) > 0:
                raise ValueError(
                    f"Kanban '{kanban_name}' has {len(all_processes)} active processes. "
                    f"Use force=True to delete anyway."
                )

        # Remove arquivo
        kanban_file.unlink()

        # Remove do cache
        if kanban_name in self._kanban_cache:
            del self._kanban_cache[kanban_name]

        logger.info(f"Deleted Kanban: {kanban_name}")
        return True

    # ========== OPERAÇÕES DE PROCESSO (Instâncias) ==========

    def create_process(
        self,
        kanban_name: str,
        form_data: Dict[str, Any],
        initial_state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cria um novo processo (instância de workflow).

        Args:
            kanban_name: Nome do Kanban
            form_data: Dados do formulário associado
            initial_state: Estado inicial (default: primeiro estado do flow_sequence)
            metadata: Metadados adicionais (prioridade, tags, etc)

        Returns:
            ID do processo criado

        Raises:
            ValueError: Se Kanban não existe ou estado inicial inválido
        """
        # Valida que Kanban existe
        kanban_def = self.get_kanban(kanban_name)

        # Define estado inicial
        if initial_state is None:
            # Usa primeiro estado do flow_sequence ou primeiro estado definido
            flow_sequence = kanban_def.get('agents', {}).get('flow_sequence', [])
            if flow_sequence:
                initial_state = flow_sequence[0]
            else:
                initial_state = kanban_def['states'][0]['id']

        # Valida que estado existe
        valid_states = [s['id'] for s in kanban_def['states']]
        if initial_state not in valid_states:
            raise ValueError(f"Invalid initial state '{initial_state}' for Kanban '{kanban_name}'")

        # Cria processo
        process_id = f"proc_{kanban_name}_{int(datetime.utcnow().timestamp() * 1000)}"

        process_data = {
            'id': process_id,
            'kanban_name': kanban_name,
            'current_state': initial_state,
            'previous_state': None,
            'form_data': form_data,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        # Persiste
        processes_repo = WorkflowRepository(kanban_name, 'processes')
        processes_repo.create(process_data)

        logger.info(f"Created process: {process_id} for Kanban '{kanban_name}'")
        return process_id

    def get_process(self, process_id: str, kanban_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Busca um processo por ID.

        Args:
            process_id: ID do processo
            kanban_name: Nome do Kanban (opcional, melhora performance)

        Returns:
            Dicionário com dados do processo

        Raises:
            ValueError: Se processo não encontrado
        """
        # Se kanban_name fornecido, busca direto
        if kanban_name:
            processes_repo = WorkflowRepository(kanban_name, 'processes')
            process = processes_repo.get_by_id(process_id)

            if process:
                return process

        # Senão, busca em todos os Kanbans
        for kanban_info in self.list_kanbans():
            kanban_name = kanban_info['kanban_name']
            processes_repo = WorkflowRepository(kanban_name, 'processes')
            process = processes_repo.get_by_id(process_id)

            if process:
                return process

        raise ValueError(f"Process '{process_id}' not found")

    def list_processes(
        self,
        kanban_name: str,
        state: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista processos de um Kanban.

        Args:
            kanban_name: Nome do Kanban
            state: Filtrar por estado (opcional)
            limit: Limitar quantidade de resultados (opcional)

        Returns:
            Lista de processos
        """
        processes_repo = WorkflowRepository(kanban_name, 'processes')

        if state:
            processes = processes_repo.get_all_by_state(state)
        else:
            processes = processes_repo.read_all()

        # Ordena por updated_at (mais recente primeiro)
        processes.sort(
            key=lambda p: p.get('updated_at', ''),
            reverse=True
        )

        # Aplica limite
        if limit:
            processes = processes[:limit]

        return processes

    def update_process(self, process_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza dados de um processo.

        Args:
            process_id: ID do processo
            data: Dados a atualizar

        Returns:
            True se atualizado com sucesso

        Raises:
            ValueError: Se processo não encontrado
        """
        # Busca processo
        process = self.get_process(process_id)
        kanban_name = process['kanban_name']

        # Atualiza dados
        process.update(data)
        process['updated_at'] = datetime.utcnow().isoformat()

        # Persiste
        processes_repo = WorkflowRepository(kanban_name, 'processes')
        all_processes = processes_repo.read_all()

        # Encontra índice
        idx = None
        for i, p in enumerate(all_processes):
            if p['id'] == process_id:
                idx = i
                break

        if idx is None:
            raise ValueError(f"Process '{process_id}' not found in repository")

        processes_repo.update(idx, process)

        logger.info(f"Updated process: {process_id}")
        return True

    def delete_process(self, process_id: str) -> bool:
        """
        Deleta um processo.

        Args:
            process_id: ID do processo

        Returns:
            True se deletado com sucesso

        Raises:
            ValueError: Se processo não encontrado
        """
        # Busca processo
        process = self.get_process(process_id)
        kanban_name = process['kanban_name']

        # Deleta
        processes_repo = WorkflowRepository(kanban_name, 'processes')
        all_processes = processes_repo.read_all()

        # Encontra índice
        idx = None
        for i, p in enumerate(all_processes):
            if p['id'] == process_id:
                idx = i
                break

        if idx is None:
            raise ValueError(f"Process '{process_id}' not found in repository")

        processes_repo.delete(idx)

        logger.info(f"Deleted process: {process_id}")
        return True

    # ========== MÉTODOS AUXILIARES ==========

    def _validate_kanban_definition(self, definition: Dict[str, Any]) -> None:
        """
        Valida estrutura de definição de Kanban.

        Args:
            definition: Definição a validar

        Raises:
            ValueError: Se definição é inválida
        """
        try:
            validate(instance=definition, schema=self.KANBAN_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid Kanban definition: {e.message}")

        # Validações adicionais
        state_ids = [s['id'] for s in definition['states']]

        # Verifica IDs únicos
        if len(state_ids) != len(set(state_ids)):
            raise ValueError("State IDs must be unique")

        # Valida flow_sequence se existe
        if 'agents' in definition and 'flow_sequence' in definition['agents']:
            flow_sequence = definition['agents']['flow_sequence']
            for state_id in flow_sequence:
                if state_id not in state_ids:
                    raise ValueError(f"Invalid state '{state_id}' in flow_sequence")

    def reload_cache(self) -> int:
        """
        Recarrega cache de definições de Kanbans.

        Returns:
            Quantidade de Kanbans recarregados
        """
        self._kanban_cache.clear()

        count = 0
        for kanban_info in self.list_kanbans():
            self.get_kanban(kanban_info['kanban_name'])
            count += 1

        logger.info(f"Reloaded {count} Kanbans into cache")
        return count
