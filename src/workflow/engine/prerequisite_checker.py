"""
Prerequisite Checker - Validação de Pré-requisitos

Valida pré-requisitos de estados do workflow SEM BLOQUEAR transições.
Filosofia: "Avisar, Não Bloquear"

Tipos de pré-requisitos suportados:
- document_upload: Validação de upload de documentos
- field_validation: Validação de campos do formulário
- approval: Aprovação de stakeholder
- payment: Confirmação de pagamento
- external_dependency: Dependência externa
- custom: Validação customizada
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class PrerequisiteChecker:
    """
    Valida pré-requisitos de estados do workflow.

    IMPORTANTE: Esta classe NUNCA bloqueia transições.
    Apenas reporta quais pré-requisitos foram atendidos e quais não foram.

    Filosofia: "Avisar, Não Bloquear"
    """

    # Tipos de pré-requisitos reconhecidos
    PREREQUISITE_TYPES = {
        'document_upload',
        'field_validation',
        'approval',
        'payment',
        'external_dependency',
        'custom'
    }

    def __init__(self):
        """Inicializa PrerequisiteChecker."""
        # Registry de validadores customizados
        self._custom_validators: Dict[str, Callable] = {}

        logger.info("PrerequisiteChecker initialized")

    def check_prerequisites(
        self,
        prerequisites: List[Dict[str, Any]],
        process_data: Dict[str, Any],
        target_state: str
    ) -> Dict[str, Any]:
        """
        Valida todos os pré-requisitos de um estado.

        Args:
            prerequisites: Lista de pré-requisitos do estado
            process_data: Dados do processo
            target_state: Estado de destino

        Returns:
            Dicionário com resultado da validação:
            {
                'all_met': bool,  # Todos pré-requisitos atendidos?
                'total': int,     # Total de pré-requisitos
                'met': int,       # Quantidade atendida
                'unmet': int,     # Quantidade não atendida
                'blocking_count': int,  # Quantidade de bloqueantes não atendidos
                'results': [      # Lista de resultados individuais
                    {
                        'id': str,
                        'type': str,
                        'label': str,
                        'met': bool,
                        'blocking': bool,
                        'message': str,
                        'checked_at': str
                    }
                ],
                'warnings': [str],  # Lista de avisos
                'errors': [str]     # Lista de erros (não bloqueiam!)
            }
        """
        if not prerequisites:
            return {
                'all_met': True,
                'total': 0,
                'met': 0,
                'unmet': 0,
                'blocking_count': 0,
                'results': [],
                'warnings': [],
                'errors': []
            }

        results = []
        warnings = []
        errors = []

        for prereq in prerequisites:
            result = self._check_single_prerequisite(prereq, process_data, target_state)
            results.append(result)

            # Coleta avisos e erros
            if not result['met']:
                if result['blocking']:
                    errors.append(result['message'])
                else:
                    warnings.append(result['message'])

        # Calcula estatísticas
        met_count = sum(1 for r in results if r['met'])
        unmet_count = len(results) - met_count
        blocking_unmet = sum(1 for r in results if not r['met'] and r['blocking'])

        return {
            'all_met': met_count == len(results),
            'total': len(results),
            'met': met_count,
            'unmet': unmet_count,
            'blocking_count': blocking_unmet,
            'results': results,
            'warnings': warnings,
            'errors': errors
        }

    def _check_single_prerequisite(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any],
        target_state: str
    ) -> Dict[str, Any]:
        """
        Valida um pré-requisito individual.

        Args:
            prereq: Definição do pré-requisito
            process_data: Dados do processo
            target_state: Estado de destino

        Returns:
            Resultado da validação
        """
        prereq_id = prereq.get('id', 'unknown')
        prereq_type = prereq.get('type', 'custom')
        label = prereq.get('label', prereq_id)
        blocking = prereq.get('blocking', False)
        alert_message = prereq.get('alert_message', f"Pré-requisito '{label}' não atendido")

        # Chama validador apropriado
        try:
            if prereq_type == 'document_upload':
                met = self._validate_document_upload(prereq, process_data)
            elif prereq_type == 'field_validation':
                met = self._validate_field(prereq, process_data)
            elif prereq_type == 'approval':
                met = self._validate_approval(prereq, process_data)
            elif prereq_type == 'payment':
                met = self._validate_payment(prereq, process_data)
            elif prereq_type == 'external_dependency':
                met = self._validate_external(prereq, process_data)
            elif prereq_type == 'custom':
                met = self._validate_custom(prereq, process_data)
            else:
                # Tipo desconhecido, assume não atendido
                logger.warning(f"Unknown prerequisite type: {prereq_type}")
                met = False
        except Exception as e:
            logger.error(f"Error checking prerequisite {prereq_id}: {e}", exc_info=True)
            met = False

        return {
            'id': prereq_id,
            'type': prereq_type,
            'label': label,
            'met': met,
            'blocking': blocking,
            'message': alert_message if not met else f"Pré-requisito '{label}' atendido",
            'checked_at': datetime.utcnow().isoformat()
        }

    # ========== VALIDADORES POR TIPO ==========

    def _validate_document_upload(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida se documento foi uploadado.

        Args:
            prereq: Definição com 'document_field'
            process_data: Dados do processo

        Returns:
            True se documento existe
        """
        document_field = prereq.get('document_field')
        if not document_field:
            return False

        # Verifica se campo existe e não está vazio
        form_data = process_data.get('form_data', {})
        document_value = form_data.get(document_field)

        return bool(document_value and str(document_value).strip())

    def _validate_field(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida se campo do formulário está preenchido/válido.

        Args:
            prereq: Definição com 'field_name' e opcional 'expected_value'
            process_data: Dados do processo

        Returns:
            True se campo válido
        """
        field_name = prereq.get('field_name')
        if not field_name:
            return False

        form_data = process_data.get('form_data', {})
        field_value = form_data.get(field_name)

        # Se tem valor esperado, compara
        if 'expected_value' in prereq:
            expected = prereq['expected_value']
            return field_value == expected

        # Senão, apenas verifica se não está vazio
        return bool(field_value and str(field_value).strip())

    def _validate_approval(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida se aprovação foi concedida.

        Args:
            prereq: Definição com 'approver_role' (opcional)
            process_data: Dados do processo

        Returns:
            True se aprovado
        """
        metadata = process_data.get('metadata', {})
        approvals = metadata.get('approvals', [])

        # Se especificou role, verifica se tem aprovação desse role
        if 'approver_role' in prereq:
            required_role = prereq['approver_role']
            return any(
                approval.get('role') == required_role and approval.get('approved', False)
                for approval in approvals
            )

        # Senão, apenas verifica se tem qualquer aprovação
        return len(approvals) > 0 and any(a.get('approved', False) for a in approvals)

    def _validate_payment(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida se pagamento foi confirmado.

        Args:
            prereq: Definição com opcional 'amount'
            process_data: Dados do processo

        Returns:
            True se pagamento confirmado
        """
        metadata = process_data.get('metadata', {})
        payment = metadata.get('payment', {})

        # Verifica se pagamento foi confirmado
        if not payment.get('confirmed', False):
            return False

        # Se especificou valor, verifica se bate
        if 'amount' in prereq:
            expected_amount = prereq['amount']
            paid_amount = payment.get('amount', 0)
            return paid_amount >= expected_amount

        return True

    def _validate_external(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida dependência externa.

        Args:
            prereq: Definição com 'dependency_key'
            process_data: Dados do processo

        Returns:
            True se dependência atendida
        """
        dependency_key = prereq.get('dependency_key')
        if not dependency_key:
            return False

        metadata = process_data.get('metadata', {})
        dependencies = metadata.get('external_dependencies', {})

        # Verifica se dependência está marcada como atendida
        return dependencies.get(dependency_key, {}).get('met', False)

    def _validate_custom(
        self,
        prereq: Dict[str, Any],
        process_data: Dict[str, Any]
    ) -> bool:
        """
        Valida usando validador customizado.

        Args:
            prereq: Definição com 'validator_id'
            process_data: Dados do processo

        Returns:
            True se validação passou
        """
        validator_id = prereq.get('validator_id')
        if not validator_id:
            return False

        # Busca validador no registry
        validator_func = self._custom_validators.get(validator_id)
        if not validator_func:
            logger.warning(f"Custom validator '{validator_id}' not found")
            return False

        # Executa validador
        try:
            return validator_func(prereq, process_data)
        except Exception as e:
            logger.error(f"Error in custom validator '{validator_id}': {e}", exc_info=True)
            return False

    # ========== REGISTRO DE VALIDADORES CUSTOMIZADOS ==========

    def register_validator(self, validator_id: str, validator_func: Callable) -> None:
        """
        Registra validador customizado.

        Args:
            validator_id: ID único do validador
            validator_func: Função validadora (prereq, process_data) -> bool
        """
        self._custom_validators[validator_id] = validator_func
        logger.info(f"Registered custom validator: {validator_id}")

    def unregister_validator(self, validator_id: str) -> None:
        """
        Remove validador customizado.

        Args:
            validator_id: ID do validador
        """
        if validator_id in self._custom_validators:
            del self._custom_validators[validator_id]
            logger.info(f"Unregistered custom validator: {validator_id}")
