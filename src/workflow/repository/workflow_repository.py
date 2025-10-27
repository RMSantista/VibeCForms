"""
Workflow Repository - Persistência inteligente para workflows

Este módulo implementa o repositório de workflows que adiciona operações
específicas sobre o BaseRepository existente.

Filosofia:
- Compõe (não herda) BaseRepository
- Backend-agnostic (usa RepositoryFactory)
- NÃO valida regras de negócio (apenas persiste)
- Operações atômicas e seguras
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# Import from persistence layer
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from persistence.factory import RepositoryFactory
from persistence.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowRepository:
    """
    Repositório inteligente para workflows.

    Funcionalidades:
    - Usa BaseRepository via Factory (backend-agnostic)
    - Adiciona operações específicas de workflow
    - Gerencia processos, transições e padrões
    - NÃO valida regras de negócio (apenas persiste)

    Três tipos de dados gerenciados:
    1. workflows_{kanban}_processes - Processos/cards
    2. workflows_{kanban}_transitions - Log de transições (auditoria)
    3. workflows_{kanban}_patterns - Dados para análise de IA (futuro)
    """

    def __init__(self, kanban_name: str, data_type: str = 'processes'):
        """
        Inicializa repositório para um kanban específico.

        Args:
            kanban_name: Nome do kanban (ex: 'pedidos')
            data_type: Tipo de dado ('processes', 'transitions', 'patterns')
        """
        self.kanban_name = kanban_name
        self.data_type = data_type
        self.form_path = f"workflows_{kanban_name}_{data_type}"

        # Obtém repository via factory (backend configurado)
        self._repo: BaseRepository = RepositoryFactory.get_repository(self.form_path)

        # Spec dinâmico baseado no tipo de dado
        self._spec = self._get_spec_for_type(data_type)

        # Garante que storage existe
        self._ensure_storage()

        logger.info(f"WorkflowRepository initialized: {self.form_path}")

    def _get_spec_for_type(self, data_type: str) -> Dict[str, Any]:
        """Retorna spec apropriado para o tipo de dado."""
        if data_type == 'processes':
            return {
                "title": f"Processos - {self.kanban_name}",
                "fields": [
                    {"name": "id", "type": "text", "label": "ID"},
                    {"name": "kanban_name", "type": "text", "label": "Kanban"},
                    {"name": "current_state", "type": "text", "label": "Estado Atual"},
                    {"name": "previous_state", "type": "text", "label": "Estado Anterior"},
                    {"name": "form_data", "type": "text", "label": "Dados do Form"},
                    {"name": "created_at", "type": "text", "label": "Criado em"},
                    {"name": "updated_at", "type": "text", "label": "Atualizado em"},
                    {"name": "metadata", "type": "text", "label": "Metadados"}
                ]
            }
        elif data_type == 'transitions':
            return {
                "title": f"Transições - {self.kanban_name}",
                "fields": [
                    {"name": "id", "type": "text", "label": "ID"},
                    {"name": "process_id", "type": "text", "label": "ID do Processo"},
                    {"name": "kanban_name", "type": "text", "label": "Kanban"},
                    {"name": "from_state", "type": "text", "label": "De"},
                    {"name": "to_state", "type": "text", "label": "Para"},
                    {"name": "timestamp", "type": "text", "label": "Data/Hora"},
                    {"name": "triggered_by", "type": "text", "label": "Disparado por"},
                    {"name": "prerequisites_status", "type": "text", "label": "Status Pré-requisitos"},
                    {"name": "was_anomaly", "type": "checkbox", "label": "Foi Anomalia"},
                    {"name": "anomaly_reason", "type": "text", "label": "Motivo Anomalia"},
                    {"name": "justification", "type": "text", "label": "Justificativa"}
                ]
            }
        else:  # patterns
            return {
                "title": f"Padrões - {self.kanban_name}",
                "fields": [
                    {"name": "analysis_data", "type": "text", "label": "Dados de Análise"}
                ]
            }

    def _ensure_storage(self):
        """Garante que o storage existe, criando se necessário."""
        try:
            self._repo.create_storage(self.form_path, self._spec)
        except Exception as e:
            # Storage já existe, tudo ok
            logger.debug(f"Storage for {self.form_path} already exists or created: {e}")

    # ========== OPERAÇÕES CRUD BÁSICAS (Wrapper do BaseRepository) ==========

    def create(self, data: Dict[str, Any]) -> str:
        """
        Cria um novo registro.

        Args:
            data: Dicionário com os dados

        Returns:
            ID do registro criado
        """
        # Para JSON, precisamos serializar campos complexos
        serialized_data = self._serialize_data(data)

        success = self._repo.create(self.form_path, self._spec, serialized_data)

        if success:
            return data.get('id', 'unknown')
        else:
            raise Exception(f"Failed to create record in {self.form_path}")

    def read_all(self) -> List[Dict[str, Any]]:
        """Lê todos os registros."""
        records = self._repo.read_all(self.form_path, self._spec)
        return [self._deserialize_data(r) for r in records]

    def read_one(self, idx: int) -> Optional[Dict[str, Any]]:
        """Lê um registro por índice."""
        record = self._repo.read_one(self.form_path, self._spec, idx)
        return self._deserialize_data(record) if record else None

    def update(self, idx: int, data: Dict[str, Any]) -> bool:
        """Atualiza um registro por índice."""
        serialized_data = self._serialize_data(data)
        return self._repo.update(self.form_path, self._spec, idx, serialized_data)

    def delete(self, idx: int) -> bool:
        """Deleta um registro por índice."""
        return self._repo.delete(self.form_path, self._spec, idx)

    # ========== OPERAÇÕES ESPECÍFICAS DE WORKFLOW ==========

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca registro por ID (não por índice).

        Args:
            record_id: ID do processo/transição

        Returns:
            Dicionário com dados ou None
        """
        all_records = self.read_all()
        for record in all_records:
            if record.get('id') == record_id:
                return record
        return None

    def get_by_field(self, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        """
        Busca registros por valor de campo.

        Args:
            field_name: Nome do campo
            field_value: Valor a buscar

        Returns:
            Lista de registros que correspondem
        """
        all_records = self.read_all()
        return [r for r in all_records if r.get(field_name) == field_value]

    def change_state(
        self,
        process_id: str,
        new_state: str,
        justification: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Muda estado de um processo.

        Backend-aware:
        - JSON: Busca processo, atualiza, salva
        - SQL: UPDATE processes SET current_state = ? WHERE id = ?
        - TXT: Reescreve linha com novo estado

        NÃO valida se transição é válida (feito em TransitionHandler).

        Args:
            process_id: ID do processo
            new_state: Novo estado
            justification: Justificativa opcional

        Returns:
            Processo atualizado

        Raises:
            ValueError: Se processo não encontrado
        """
        # Busca processo atual
        all_processes = self.read_all()
        process_idx = None
        process = None

        for idx, p in enumerate(all_processes):
            if p.get('id') == process_id:
                process_idx = idx
                process = p
                break

        if process is None:
            raise ValueError(f"Process {process_id} not found")

        old_state = process.get('current_state')

        # Atualiza estado
        process['previous_state'] = old_state
        process['current_state'] = new_state
        process['updated_at'] = datetime.utcnow().isoformat()
        process['last_transition'] = {
            'from_state': old_state,
            'to_state': new_state,
            'timestamp': datetime.utcnow().isoformat(),
            'justification': justification
        }

        # Persiste (usa método update)
        self.update(process_idx, process)

        return process

    def get_all_by_state(self, state: str) -> List[Dict[str, Any]]:
        """
        Busca todos os processos em um estado específico.

        Backend-aware:
        - SQL: SELECT * FROM processes WHERE current_state = ?
               (usa índice em current_state se existir)
        - JSON/TXT: Filtra em memória (lê todos, filtra)

        Args:
            state: Nome do estado

        Returns:
            Lista de processos no estado
        """
        return self.get_by_field('current_state', state)

    def log_transition(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        triggered_by: str,
        justification: Optional[str] = None,
        prerequisites_status: Optional[Dict[str, bool]] = None,
        was_anomaly: bool = False,
        anomaly_reason: Optional[str] = None
    ) -> str:
        """
        Registra transição no log de auditoria.

        Persiste em workflows_{kanban}_transitions.

        Args:
            process_id: ID do processo
            from_state: Estado origem
            to_state: Estado destino
            triggered_by: Quem/o que disparou ("manual", "system", "agent:xxx")
            justification: Justificativa (opcional)
            prerequisites_status: Status dos pré-requisitos
            was_anomaly: Se foi uma anomalia
            anomaly_reason: Motivo da anomalia

        Returns:
            ID da transição criada
        """
        # Cria repository para transitions
        transitions_repo = WorkflowRepository(self.kanban_name, 'transitions')

        transition = {
            "id": f"trans_{int(datetime.utcnow().timestamp() * 1000)}",
            "process_id": process_id,
            "kanban_name": self.kanban_name,
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": datetime.utcnow().isoformat(),
            "triggered_by": triggered_by,
            "prerequisites_status": prerequisites_status or {},
            "was_anomaly": was_anomaly,
            "anomaly_reason": anomaly_reason,
            "justification": justification
        }

        return transitions_repo.create(transition)

    def get_transition_history(self, process_id: str) -> List[Dict[str, Any]]:
        """
        Busca histórico de transições de um processo.

        Lê do log de transições (workflows_{kanban}_transitions).

        Args:
            process_id: ID do processo

        Returns:
            Lista de transições ordenadas por timestamp
        """
        transitions_repo = WorkflowRepository(self.kanban_name, 'transitions')
        transitions = transitions_repo.get_by_field('process_id', process_id)

        # Ordena por timestamp (mais recente primeiro)
        return sorted(
            transitions,
            key=lambda t: t.get('timestamp', ''),
            reverse=True
        )

    # ========== SERIALIZAÇÃO/DESERIALIZAÇÃO ==========

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serializa dados complexos para strings (JSON).

        Campos como form_data, metadata, prerequisites_status são objetos
        que precisam ser serializados para string no backend.
        """
        serialized = data.copy()

        # Campos que precisam ser serializados
        complex_fields = [
            'form_data', 'metadata', 'last_transition',
            'prerequisites_status'
        ]

        for field in complex_fields:
            if field in serialized and isinstance(serialized[field], (dict, list)):
                serialized[field] = json.dumps(serialized[field], ensure_ascii=False)

        return serialized

    def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserializa dados de strings para objetos Python.

        Converte strings JSON de volta para dicts/lists.
        """
        if not data:
            return data

        deserialized = data.copy()

        # Campos que precisam ser desserializados
        complex_fields = [
            'form_data', 'metadata', 'last_transition',
            'prerequisites_status'
        ]

        for field in complex_fields:
            if field in deserialized and isinstance(deserialized[field], str):
                try:
                    deserialized[field] = json.loads(deserialized[field])
                except (json.JSONDecodeError, TypeError):
                    # Se não for JSON válido, mantém como string
                    pass

        # Converte was_anomaly para boolean se for string
        if 'was_anomaly' in deserialized:
            if isinstance(deserialized['was_anomaly'], str):
                deserialized['was_anomaly'] = deserialized['was_anomaly'].lower() in ['true', '1', 'yes']

        return deserialized
