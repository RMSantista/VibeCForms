#!/usr/bin/env python3
"""
Kanban Template Generator
Generates pre-configured kanban templates for the VibeCForms Workflow system.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict

TEMPLATES = {
    'order_flow': {
        'id': 'order_flow',
        'name': 'Fluxo de Pedidos',
        'description': 'Workflow completo para gestão de pedidos: orçamento → pedido → entrega → concluído',
        'states': [
            {
                'id': 'orcamento',
                'name': 'Orçamento',
                'description': 'Solicitação inicial de orçamento',
                'color': '#FFA500',
                'is_initial': True
            },
            {
                'id': 'orcamento_aprovado',
                'name': 'Orçamento Aprovado',
                'description': 'Orçamento aprovado pelo cliente',
                'color': '#4169E1'
            },
            {
                'id': 'pedido',
                'name': 'Pedido Confirmado',
                'description': 'Pedido confirmado e em produção',
                'color': '#9370DB',
                'auto_transition_to': 'em_entrega',
                'timeout_hours': 48
            },
            {
                'id': 'em_entrega',
                'name': 'Em Entrega',
                'description': 'Pedido em processo de entrega',
                'color': '#20B2AA'
            },
            {
                'id': 'concluido',
                'name': 'Concluído',
                'description': 'Pedido entregue e finalizado',
                'color': '#32CD32',
                'is_final': True
            },
            {
                'id': 'cancelado',
                'name': 'Cancelado',
                'description': 'Pedido cancelado',
                'color': '#DC143C',
                'is_final': True
            }
        ],
        'transitions': [
            {
                'from': 'orcamento',
                'to': 'orcamento_aprovado',
                'type': 'manual',
                'label': 'Aprovar Orçamento',
                'prerequisites': [
                    {
                        'type': 'field_check',
                        'field': 'valor_total',
                        'condition': 'not_empty',
                        'message': 'Valor total deve estar preenchido'
                    }
                ]
            },
            {
                'from': 'orcamento_aprovado',
                'to': 'pedido',
                'type': 'manual',
                'label': 'Confirmar Pedido',
                'prerequisites': [
                    {
                        'type': 'field_check',
                        'field': 'forma_pagamento',
                        'condition': 'not_empty',
                        'message': 'Forma de pagamento deve estar definida'
                    }
                ]
            },
            {
                'from': 'pedido',
                'to': 'em_entrega',
                'type': 'system',
                'label': 'Iniciar Entrega',
                'auto_trigger': True
            },
            {
                'from': 'em_entrega',
                'to': 'concluido',
                'type': 'manual',
                'label': 'Finalizar Entrega'
            },
            {
                'from': 'orcamento',
                'to': 'cancelado',
                'type': 'manual',
                'label': 'Cancelar'
            },
            {
                'from': 'orcamento_aprovado',
                'to': 'cancelado',
                'type': 'manual',
                'label': 'Cancelar'
            },
            {
                'from': 'pedido',
                'to': 'cancelado',
                'type': 'manual',
                'label': 'Cancelar'
            }
        ],
        'linked_forms': ['pedidos', 'orcamentos']
    },

    'support_ticket': {
        'id': 'support_ticket',
        'name': 'Tickets de Suporte',
        'description': 'Workflow para gerenciamento de tickets de suporte técnico',
        'states': [
            {
                'id': 'novo',
                'name': 'Novo',
                'description': 'Ticket recém-criado',
                'color': '#FFD700',
                'is_initial': True,
                'auto_transition_to': 'em_analise',
                'timeout_hours': 1
            },
            {
                'id': 'em_analise',
                'name': 'Em Análise',
                'description': 'Ticket sendo analisado',
                'color': '#4169E1'
            },
            {
                'id': 'aguardando_cliente',
                'name': 'Aguardando Cliente',
                'description': 'Aguardando resposta do cliente',
                'color': '#FF8C00',
                'timeout_hours': 72
            },
            {
                'id': 'resolvido',
                'name': 'Resolvido',
                'description': 'Problema resolvido',
                'color': '#32CD32',
                'is_final': True
            },
            {
                'id': 'fechado',
                'name': 'Fechado',
                'description': 'Ticket fechado sem solução',
                'color': '#808080',
                'is_final': True
            }
        ],
        'transitions': [
            {
                'from': 'novo',
                'to': 'em_analise',
                'type': 'system',
                'label': 'Iniciar Análise',
                'auto_trigger': True
            },
            {
                'from': 'em_analise',
                'to': 'aguardando_cliente',
                'type': 'manual',
                'label': 'Solicitar Informações'
            },
            {
                'from': 'em_analise',
                'to': 'resolvido',
                'type': 'manual',
                'label': 'Resolver'
            },
            {
                'from': 'aguardando_cliente',
                'to': 'em_analise',
                'type': 'manual',
                'label': 'Cliente Respondeu'
            },
            {
                'from': 'aguardando_cliente',
                'to': 'fechado',
                'type': 'system',
                'label': 'Timeout - Sem Resposta'
            },
            {
                'from': 'novo',
                'to': 'fechado',
                'type': 'manual',
                'label': 'Fechar Ticket'
            }
        ],
        'linked_forms': ['tickets', 'chamados']
    },

    'hiring': {
        'id': 'hiring',
        'name': 'Processo de Contratação',
        'description': 'Workflow para gestão de processos seletivos e contratações',
        'states': [
            {
                'id': 'candidatura',
                'name': 'Candidatura Recebida',
                'description': 'Candidato se inscreveu para vaga',
                'color': '#87CEEB',
                'is_initial': True
            },
            {
                'id': 'triagem',
                'name': 'Triagem',
                'description': 'Análise inicial de currículo',
                'color': '#4169E1'
            },
            {
                'id': 'entrevista_rh',
                'name': 'Entrevista RH',
                'description': 'Entrevista com RH',
                'color': '#9370DB'
            },
            {
                'id': 'entrevista_tecnica',
                'name': 'Entrevista Técnica',
                'description': 'Entrevista com gestor/equipe técnica',
                'color': '#8B4789'
            },
            {
                'id': 'proposta',
                'name': 'Proposta Enviada',
                'description': 'Proposta de emprego enviada',
                'color': '#FFD700'
            },
            {
                'id': 'contratado',
                'name': 'Contratado',
                'description': 'Candidato aceitou proposta',
                'color': '#32CD32',
                'is_final': True
            },
            {
                'id': 'rejeitado',
                'name': 'Rejeitado',
                'description': 'Candidato não aprovado',
                'color': '#DC143C',
                'is_final': True
            }
        ],
        'transitions': [
            {
                'from': 'candidatura',
                'to': 'triagem',
                'type': 'manual',
                'label': 'Iniciar Triagem'
            },
            {
                'from': 'triagem',
                'to': 'entrevista_rh',
                'type': 'manual',
                'label': 'Aprovar para RH',
                'prerequisites': [
                    {
                        'type': 'field_check',
                        'field': 'curriculo',
                        'condition': 'not_empty',
                        'message': 'Currículo deve estar anexado'
                    }
                ]
            },
            {
                'from': 'entrevista_rh',
                'to': 'entrevista_tecnica',
                'type': 'manual',
                'label': 'Aprovar para Técnica'
            },
            {
                'from': 'entrevista_tecnica',
                'to': 'proposta',
                'type': 'manual',
                'label': 'Enviar Proposta'
            },
            {
                'from': 'proposta',
                'to': 'contratado',
                'type': 'manual',
                'label': 'Proposta Aceita'
            },
            {
                'from': 'candidatura',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar'
            },
            {
                'from': 'triagem',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar'
            },
            {
                'from': 'entrevista_rh',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar'
            },
            {
                'from': 'entrevista_tecnica',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar'
            },
            {
                'from': 'proposta',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Proposta Recusada'
            }
        ],
        'linked_forms': ['candidatos', 'vagas']
    },

    'approval': {
        'id': 'approval',
        'name': 'Fluxo de Aprovação',
        'description': 'Workflow genérico para aprovação de documentos/solicitações',
        'states': [
            {
                'id': 'pendente',
                'name': 'Pendente',
                'description': 'Aguardando revisão',
                'color': '#FFA500',
                'is_initial': True
            },
            {
                'id': 'em_revisao',
                'name': 'Em Revisão',
                'description': 'Sendo revisado',
                'color': '#4169E1'
            },
            {
                'id': 'aprovado',
                'name': 'Aprovado',
                'description': 'Aprovado',
                'color': '#32CD32',
                'is_final': True
            },
            {
                'id': 'rejeitado',
                'name': 'Rejeitado',
                'description': 'Rejeitado - necessita correções',
                'color': '#DC143C',
                'is_final': True
            }
        ],
        'transitions': [
            {
                'from': 'pendente',
                'to': 'em_revisao',
                'type': 'manual',
                'label': 'Iniciar Revisão'
            },
            {
                'from': 'em_revisao',
                'to': 'aprovado',
                'type': 'manual',
                'label': 'Aprovar'
            },
            {
                'from': 'em_revisao',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar',
                'prerequisites': [
                    {
                        'type': 'field_check',
                        'field': 'motivo_rejeicao',
                        'condition': 'not_empty',
                        'message': 'Motivo da rejeição deve ser informado'
                    }
                ]
            },
            {
                'from': 'pendente',
                'to': 'rejeitado',
                'type': 'manual',
                'label': 'Rejeitar Diretamente'
            }
        ],
        'linked_forms': []
    }
}


def list_templates():
    """Print available templates."""
    print("\nAvailable Templates:")
    print("=" * 70)
    for template_id, template in TEMPLATES.items():
        print(f"\n  {template_id}")
        print(f"    Name: {template['name']}")
        print(f"    Description: {template['description']}")
        print(f"    States: {len(template['states'])}")
        print(f"    Transitions: {len(template['transitions'])}")
    print(f"\n{'=' * 70}\n")


def generate_template(template_id: str, output_path: str = None):
    """Generate kanban JSON from template."""
    if template_id not in TEMPLATES:
        print(f"❌ Error: Template '{template_id}' not found")
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    template_data = TEMPLATES[template_id]

    # Determine output path
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = Path(f"{template_id}.json")

    # Write JSON
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Template generated successfully!")
        print(f"   File: {out_file.absolute()}")
        print(f"   Template: {template_data['name']}")
        print(f"   States: {len(template_data['states'])}")
        print(f"   Transitions: {len(template_data['transitions'])}")

    except Exception as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate pre-configured kanban templates for VibeCForms Workflow system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available templates
  %(prog)s --list

  # Generate order flow template
  %(prog)s --template order_flow

  # Generate and save to specific file
  %(prog)s --template support_ticket --output tickets.json
        """
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available templates'
    )

    parser.add_argument(
        '--template',
        type=str,
        choices=list(TEMPLATES.keys()),
        help='Template to generate'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: <template_id>.json)'
    )

    args = parser.parse_args()

    if args.list:
        list_templates()
    elif args.template:
        generate_template(args.template, args.output)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
