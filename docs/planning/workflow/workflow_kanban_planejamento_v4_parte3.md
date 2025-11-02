# Sistema de Workflow Kanban - VibeCForms v4.0
## Planejamento Completo com IA, Analytics e Visual Editor
## PARTE 3: Implementação e Testes

**Versão:** 4.0 - Parte 3 de 3
**Data:** Outubro 2025
**Autor:** Rodrigo Santista (com assistência de Claude Code)

---

## Índice - Parte 3

13. [Exemplo Completo - Fluxo de Pedidos](#13-exemplo-completo-fluxo-de-pedidos)
14. [Fases de Implementação](#14-fases-de-implementação)
15. [Estratégia de Testes](#15-estratégia-de-testes)

**Parte 1:** Fundamentos, Arquitetura Core, IA (Seções 1-8)
**Parte 2:** Editor Visual, Exportações, Auditoria, Arquitetura (Seções 9-12)

---

## 13. Exemplo Completo - Fluxo de Pedidos

### 13.1 Definição Completa do Kanban

**Arquivo:** `src/config/kanbans/pedidos_kanban.json`

```json
{
  "kanban_id": "pedidos",
  "title": "Fluxo de Pedidos",
  "description": "Gerenciamento completo do ciclo de vida de pedidos de clientes",
  "icon": "fa-shopping-cart",
  "version": "4.0",
  "created_at": "2025-08-15T10:00:00",
  "updated_at": "2025-10-27T14:30:00",

  "linked_forms": [
    {
      "form_path": "pedidos",
      "primary": true,
      "auto_create_process": true
    },
    {
      "form_path": "pedidos_urgentes",
      "primary": false,
      "auto_create_process": true
    }
  ],

  "field_mapping": {
    "process_title_template": "Pedido #{id} - {cliente}",
    "process_description_template": "{quantidade}x {produto} - R$ {valor_total}",
    "custom_fields_mapping": {
      "cliente": "process_data.cliente",
      "produto": "process_data.produto",
      "quantidade": "process_data.quantidade",
      "valor_total": "process_data.valor_total",
      "aprovado_cliente": "process_data.aprovado_cliente",
      "pagamento_recebido": "process_data.pagamento_recebido"
    }
  },

  "states": [
    {
      "id": "orcamento",
      "name": "Orçamento",
      "order": 0,
      "color": "#6c757d",
      "icon": "fa-file-invoice-dollar",
      "description": "Pedido em fase de orçamento, aguardando aprovação do cliente",
      "prerequisites": [],
      "timeouts": [
        {
          "id": "lembrete_24h",
          "hours": 24,
          "action": "send_notification",
          "notification": {
            "type": "email",
            "recipients": ["{process_data.cliente_email}"],
            "template": "orcamento_follow_up",
            "subject": "Seu orçamento está aguardando aprovação"
          }
        },
        {
          "id": "escalar_72h",
          "hours": 72,
          "action": "escalate",
          "escalation": {
            "type": "supervisor",
            "message": "Orçamento sem resposta há 3 dias"
          }
        }
      ],
      "agent_config": {
        "enabled": true,
        "agent_class": "OrcamentoAgent",
        "analysis_frequency_hours": 12,
        "min_confidence": 0.7
      }
    },
    {
      "id": "pedido",
      "name": "Pedido Confirmado",
      "order": 1,
      "color": "#007bff",
      "icon": "fa-check-circle",
      "description": "Cliente aprovou o orçamento, aguardando pagamento",
      "prerequisites": [
        {
          "id": "cliente_aprovacao",
          "name": "Aprovação do Cliente",
          "type": "field_check",
          "field": "aprovado_cliente",
          "condition": "equals",
          "value": true,
          "blocking": false,
          "message": "Aguardando aprovação do cliente para o orçamento"
        }
      ],
      "timeouts": [
        {
          "id": "lembrete_pagamento_48h",
          "hours": 48,
          "action": "send_notification",
          "notification": {
            "type": "email",
            "recipients": ["{process_data.cliente_email}"],
            "template": "pagamento_lembrete",
            "subject": "Lembrete: Pagamento pendente - Pedido #{process_data.id}"
          }
        }
      ],
      "agent_config": {
        "enabled": true,
        "agent_class": "PedidoAgent",
        "analysis_frequency_hours": 6,
        "min_confidence": 0.8
      }
    },
    {
      "id": "entrega",
      "name": "Em Entrega",
      "order": 2,
      "color": "#ffc107",
      "icon": "fa-truck",
      "description": "Pedido em processo de entrega",
      "prerequisites": [
        {
          "id": "pagamento_confirmado",
          "name": "Pagamento Confirmado",
          "type": "field_check",
          "field": "pagamento_recebido",
          "condition": "equals",
          "value": true,
          "blocking": false,
          "message": "Aguardando confirmação de pagamento antes de enviar"
        },
        {
          "id": "estoque_disponivel",
          "name": "Estoque Disponível",
          "type": "external_api",
          "api_endpoint": "https://api.erp.empresa.com/check_stock",
          "api_method": "POST",
          "api_headers": {
            "Authorization": "Bearer ${ERP_API_TOKEN}",
            "Content-Type": "application/json"
          },
          "api_payload": {
            "produto_id": "{process_data.produto_id}",
            "quantidade": "{process_data.quantidade}"
          },
          "expected_response": {"available": true},
          "timeout_seconds": 5,
          "blocking": false,
          "message": "Produto fora de estoque"
        }
      ],
      "timeouts": [
        {
          "id": "alerta_atraso_120h",
          "hours": 120,
          "action": "escalate",
          "escalation": {
            "type": "logistics",
            "message": "Entrega atrasada há 5 dias"
          }
        }
      ],
      "agent_config": {
        "enabled": true,
        "agent_class": "EntregaAgent",
        "analysis_frequency_hours": 24,
        "min_confidence": 0.75
      }
    },
    {
      "id": "concluido",
      "name": "Concluído",
      "order": 3,
      "color": "#28a745",
      "icon": "fa-flag-checkered",
      "description": "Pedido entregue e finalizado",
      "prerequisites": [],
      "is_final": true
    }
  ],

  "initial_state": "orcamento",

  "transition_rules": {
    "allow_backward": true,
    "require_justification_backward": true,
    "allow_skip_states": false,
    "allowed_transitions": {
      "orcamento": ["pedido"],
      "pedido": ["orcamento", "entrega"],
      "entrega": ["pedido", "concluido"],
      "concluido": ["entrega"]
    }
  },

  "auto_transition_config": {
    "enable_cascade": true,
    "max_cascade_depth": 3,
    "cascade_delay_ms": 100
  },

  "kpis": [
    {
      "id": "tempo_medio_conclusao",
      "name": "Tempo Médio de Conclusão",
      "calculation": "avg_duration_from_created_to_completed",
      "unit": "days",
      "target_value": 5.0,
      "warning_threshold": 6.0,
      "critical_threshold": 8.0
    },
    {
      "id": "taxa_conversao_orcamento",
      "name": "Taxa de Conversão (Orçamento → Pedido)",
      "calculation": "conversion_rate",
      "from_state": "orcamento",
      "to_state": "pedido",
      "unit": "percentage",
      "target_value": 75.0
    },
    {
      "id": "valor_medio_pedido",
      "name": "Valor Médio por Pedido",
      "calculation": "avg_field_value",
      "field": "valor_total",
      "unit": "currency",
      "target_value": 2000.0
    }
  ]
}
```

### 13.2 Definição do Formulário "pedidos"

**Arquivo:** `src/specs/pedidos.json`

```json
{
  "title": "Pedidos",
  "icon": "fa-shopping-cart",
  "fields": [
    {
      "name": "cliente",
      "label": "Cliente",
      "type": "text",
      "required": true
    },
    {
      "name": "cliente_email",
      "label": "Email do Cliente",
      "type": "email",
      "required": true
    },
    {
      "name": "produto_id",
      "label": "Código do Produto",
      "type": "text",
      "required": true
    },
    {
      "name": "produto",
      "label": "Nome do Produto",
      "type": "text",
      "required": true
    },
    {
      "name": "quantidade",
      "label": "Quantidade",
      "type": "number",
      "required": true
    },
    {
      "name": "valor_unitario",
      "label": "Valor Unitário (R$)",
      "type": "number",
      "required": true
    },
    {
      "name": "valor_total",
      "label": "Valor Total (R$)",
      "type": "number",
      "required": true
    },
    {
      "name": "aprovado_cliente",
      "label": "Cliente Aprovou Orçamento?",
      "type": "checkbox",
      "required": false
    },
    {
      "name": "pagamento_recebido",
      "label": "Pagamento Recebido?",
      "type": "checkbox",
      "required": false
    },
    {
      "name": "observacoes",
      "label": "Observações",
      "type": "textarea",
      "required": false
    }
  ],
  "validation_messages": {
    "all_empty": "Preencha pelo menos os campos obrigatórios",
    "cliente": "Nome do cliente é obrigatório",
    "cliente_email": "Email do cliente é obrigatório",
    "produto_id": "Código do produto é obrigatório",
    "produto": "Nome do produto é obrigatório",
    "quantidade": "Quantidade é obrigatória",
    "valor_unitario": "Valor unitário é obrigatório",
    "valor_total": "Valor total é obrigatório"
  }
}
```

### 13.3 Cenário Passo a Passo Detalhado

#### DIA 1 - 27/10/2025 10:00 - Criação do Pedido

**1. Usuário acessa sistema:**

```
Navegador → http://localhost:5000/workflow/board/pedidos

Tela exibida:
┌──────────────────────────────────────────────────────────────┐
│ 🛒 Fluxo de Pedidos                    [+ Novo Processo]     │
├───────────┬────────────────┬────────────────┬────────────────┤
│ Orçamento │ Pedido         │ Em Entrega     │ Concluído      │
│ (2)       │ Confirmado (3) │ (1)            │ (15)           │
├───────────┼────────────────┼────────────────┼────────────────┤
│           │                │                │                │
│ [Cards    │ [Cards...]     │ [Cards...]     │ [Cards...]     │
│  antigos] │                │                │                │
│           │                │                │                │
└───────────┴────────────────┴────────────────┴────────────────┘
```

**2. Clica [+ Novo Processo]:**

```
Sistema verifica linked_forms do Kanban:
- pedidos (primary: true)
- pedidos_urgentes (primary: false)

Como há múltiplos formulários, mostra modal:

┌────────────────────────────────────────────┐
│ Selecione o tipo de pedido    [✕ Fechar]  │
├────────────────────────────────────────────┤
│                                            │
│ ⦿ Pedido Normal                            │
│   Fluxo completo desde orçamento           │
│                                            │
│ ○ Pedido Urgente                           │
│   Pula orçamento, inicia em "Pedido"      │
│                                            │
│ [Cancelar]               [Continuar]      │
└────────────────────────────────────────────┘
```

**3. Seleciona "Pedido Normal" e clica [Continuar]:**

```
Sistema redireciona para:
http://localhost:5000/pedidos?kanban_redirect=pedidos

Formulário exibido:
┌──────────────────────────────────────────────────────────────┐
│ 🛒 Pedidos                                                    │
│ ℹ️ Este formulário está vinculado ao Kanban "Fluxo de Pedidos"│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Cliente: *                                                   │
│ [_______________________________________]                    │
│                                                              │
│ Email do Cliente: *                                          │
│ [_______________________________________]                    │
│                                                              │
│ Código do Produto: *                                         │
│ [_______________________________________]                    │
│                                                              │
│ Nome do Produto: *                                           │
│ [_______________________________________]                    │
│                                                              │
│ Quantidade: *                                                │
│ [_______________________________________]                    │
│                                                              │
│ Valor Unitário (R$): *                                       │
│ [_______________________________________]                    │
│                                                              │
│ Valor Total (R$): *                                          │
│ [_______________________________________]                    │
│                                                              │
│ ☐ Cliente Aprovou Orçamento?                                │
│                                                              │
│ ☐ Pagamento Recebido?                                        │
│                                                              │
│ Observações:                                                 │
│ [_____________________________________________]              │
│ [_____________________________________________]              │
│                                                              │
│ [Salvar]                                                     │
└──────────────────────────────────────────────────────────────┘
```

**4. Preenche formulário:**

```
Cliente: ACME Corporation
Email: contato@acmecorp.com
Código do Produto: WGT-PREM-001
Nome do Produto: Widget Premium
Quantidade: 100
Valor Unitário: 15.00
Valor Total: 1500.00
☐ Cliente Aprovou Orçamento? (desmarcado)
☐ Pagamento Recebido? (desmarcado)
Observações: Cliente solicitou entrega em 2 semanas
```

**5. Clica [Salvar]:**

```
Backend (VibeCForms.py):

POST /pedidos

1. Valida dados do formulário
   ✅ Todos campos obrigatórios preenchidos

2. Salva em BaseRepository
   → RepositoryFactory.get_repository("pedidos")
   → Retorna SQLiteAdapter (configurado em persistence.json)
   → SQLiteAdapter.create(form_path="pedidos", spec={...}, data={...})
   → INSERT INTO pedidos VALUES (...)
   → Retorna: form_id = 42

3. Chama FormTriggerManager.on_form_saved()
   → form_path="pedidos", form_id=42, form_data={...}, user_id="user123"

4. FormTriggerManager:
   → KanbanRegistry.get_kanbans_for_form("pedidos")
   → Retorna: ["pedidos"]
   → KanbanRegistry.should_auto_create_process("pedidos", "pedidos")
   → Retorna: True

5. ProcessFactory.create_from_form()
   → kanban_id="pedidos"
   → form_path="pedidos"
   → form_id=42
   → form_data={cliente:"ACME Corporation", produto:"Widget Premium", ...}
   → created_by="user123"

6. ProcessFactory carrega Kanban config:
   → Carrega pedidos_kanban.json
   → initial_state = "orcamento"
   → process_title_template = "Pedido #{id} - {cliente}"
   → Aplica template: "Pedido #42 - ACME Corporation"

7. ProcessFactory cria processo:
   → process_id = "proc_pedidos_1730032800_42"
   → current_state = "orcamento"
   → title = "Pedido #42 - ACME Corporation"
   → description = "100x Widget Premium - R$ 1500.00"
   → source_form = "pedidos"
   → source_form_id = 42
   → process_data = {cliente: "ACME Corporation", ...}
   → history = [{timestamp, action:"created", to_state:"orcamento", ...}]

8. Salva em WorkflowRepository
   → SQLiteAdapter.create("workflows/pedidos", spec={...}, data={...})

9. AutoTransitionEngine.check_and_transition(process_id)
   → Carrega processo
   → Estado atual: "orcamento"
   → Próximo estado: "pedido"
   → Pré-requisitos de "pedido":
      - aprovado_cliente = true
   → process_data.aprovado_cliente = false
   → Resultado: NOT SATISFIED
   → Não move automaticamente
   → Retorna

10. Redireciona para /workflow/board/pedidos
    → Flash message: "✅ Dados salvos com sucesso! Processo criado no Kanban 'Fluxo de Pedidos'"
```

**6. Tela após salvar:**

```
Navegador → http://localhost:5000/workflow/board/pedidos

┌──────────────────────────────────────────────────────────────┐
│ 🛒 Fluxo de Pedidos                    [+ Novo Processo]     │
├───────────┬────────────────┬────────────────┬────────────────┤
│ Orçamento │ Pedido         │ Em Entrega     │ Concluído      │
│ (3) ⬆️     │ Confirmado (3) │ (1)            │ (15)           │
├───────────┼────────────────┼────────────────┼────────────────┤
│           │                │                │                │
│ ┌─────────┐│               │                │                │
│ │🆕 Ped #42││               │                │                │
│ │ ACME    ││               │                │                │
│ │         ││               │                │                │
│ │ 100x    ││               │                │                │
│ │ Widget  ││               │                │                │
│ │         ││               │                │                │
│ │ ⚠️ Aguar.││               │                │                │
│ │ aprovação│               │                │                │
│ └─────────┘│               │                │                │
│           │                │                │                │
│ [Cards    │                │                │                │
│  antigos] │                │                │                │
└───────────┴────────────────┴────────────────┴────────────────┘

Toast notification:
┌────────────────────────────────────────────┐
│ ✅ Dados salvos com sucesso!                │
│ Processo criado no Kanban 'Fluxo de Pedidos'│
│ [Ver Processo]                             │
└────────────────────────────────────────────┘
```

---

#### DIA 1 - 27/10/2025 12:00 - Primeira Análise de IA

**7. Cron job executa análise de agents (a cada hora):**

```
AgentOrchestrator.analyze_all_active_processes()

1. Busca todos processos ativos:
   → WorkflowRepository.find_processes({"status": "active"})
   → Retorna: [..., proc_pedidos_1730032800_42, ...]

2. Para processo proc_pedidos_1730032800_42:
   → AgentOrchestrator.analyze_process("proc_pedidos_1730032800_42")

3. Carrega processo:
   → current_state = "orcamento"
   → time_in_state = 2 horas

4. Identifica agent configurado:
   → pedidos_kanban.json → states[0].agent_config
   → agent_class = "OrcamentoAgent"
   → analysis_frequency_hours = 12
   → min_confidence = 0.7

5. Verifica se deve analisar:
   → time_in_state (2h) < analysis_frequency_hours (12h)
   → Ainda não (precisa esperar 10 horas)
   → Pula análise deste processo
```

---

#### DIA 2 - 28/10/2025 14:30 - Cliente Aprova Orçamento

**8. Usuário acessa lista de pedidos:**

```
Navegador → http://localhost:5000/pedidos

Tabela exibida:
┌──────────────────────────────────────────────────────────────┐
│ Cliente        │ Produto        │ Qtd │ Valor    │ Ações   │
├────────────────┼────────────────┼─────┼──────────┼─────────┤
│ ...            │ ...            │ ... │ ...      │ ...     │
│ ACME Corp      │ Widget Premium │ 100 │ 1500.00  │[Edit]   │
│ ...            │ ...            │ ... │ ...      │ ...     │
└──────────────────────────────────────────────────────────────┘
```

**9. Clica [Edit] do pedido ACME Corp:**

```
Navegador → http://localhost:5000/pedidos/edit/42

Formulário pré-preenchido:
┌──────────────────────────────────────────────────────────────┐
│ 🛒 Editar: Pedidos                                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Cliente: *                                                   │
│ [ACME Corporation___________________]                        │
│                                                              │
│ Email do Cliente: *                                          │
│ [contato@acmecorp.com_______________]                        │
│                                                              │
│ ... (outros campos preenchidos) ...                          │
│                                                              │
│ ☐ Cliente Aprovou Orçamento?         ← DESMARCADO           │
│                                                              │
│ ☐ Pagamento Recebido?                                        │
│                                                              │
│ [Salvar]                                                     │
└──────────────────────────────────────────────────────────────┘
```

**10. Marca checkbox "Cliente Aprovou Orçamento?" e clica [Salvar]:**

```
POST /pedidos/edit/42

Backend:

1. Atualiza registro no BaseRepository
   → SQLiteAdapter.update(form_path="pedidos", spec={...}, idx=42, data={...})
   → UPDATE pedidos SET aprovado_cliente=true WHERE id=42
   → ✅ Sucesso

2. Chama FormTriggerManager.on_form_updated()
   → form_path="pedidos", form_id=42, form_data={...}, user_id="user123"

3. FormTriggerManager:
   → ProcessFactory.find_processes_by_source("pedidos", 42)
   → Retorna: [proc_pedidos_1730032800_42]

4. Para cada processo encontrado:
   → ProcessFactory.update_process_data("proc_pedidos_1730032800_42", new_data={...})
   → Atualiza process_data.aprovado_cliente = true

5. AutoTransitionEngine.check_and_transition("proc_pedidos_1730032800_42")

6. AutoTransitionEngine:
   → Carrega processo
   → Estado atual: "orcamento"
   → Busca próximo estado na ordem:
      - states[1].id = "pedido"
   → Busca pré-requisitos de "pedido":
      - prerequisites[0]: cliente_aprovacao
        type: field_check
        field: aprovado_cliente
        condition: equals
        value: true

7. PrerequisiteChecker.check_all(process, prerequisites)
   → _check_field(process, prereq):
      - field_name = "aprovado_cliente"
      - condition = "equals"
      - expected_value = true
      - actual_value = process_data.aprovado_cliente = true
      - Resultado: SATISFIED ✅

8. PrerequisiteChecker retorna:
   → all_satisfied = True

9. AutoTransitionEngine:
   → ✅ Todos pré-requisitos satisfeitos!
   → Chama TransitionHandler.transition()
      - process_id = "proc_pedidos_1730032800_42"
      - to_state = "pedido"
      - actor = "system"
      - actor_type = "auto_transition"
      - trigger = "prerequisite_met"
      - metadata = {prerequisites_checked: {...}}

10. TransitionHandler:
    → Atualiza current_state: "orcamento" → "pedido"
    → Registra no histórico:
       {
         timestamp: "2025-10-28T14:30:15",
         action: "auto_transitioned",
         from_state: "orcamento",
         to_state: "pedido",
         actor: "system",
         actor_type: "auto_transition",
         trigger: "prerequisite_met",
         forced: false,
         prerequisites_checked: {
           cliente_aprovacao: {satisfied: true, ...}
         }
       }
    → Salva em WorkflowRepository

11. AutoTransitionEngine (recursão - cascata):
    → Estado atual agora: "pedido"
    → Busca próximo estado: "entrega"
    → Pré-requisitos de "entrega":
       - pagamento_confirmado: pagamento_recebido = true
       - estoque_disponivel: API externa
    → process_data.pagamento_recebido = false
    → Resultado: NOT SATISFIED
    → Para cascata aqui

12. Redireciona para /pedidos
    → Flash message: "✅ Dados atualizados! Processo movido automaticamente para 'Pedido Confirmado'"
```

**11. Tela após salvar:**

```
Navegador → http://localhost:5000/pedidos

Toast notification:
┌────────────────────────────────────────────┐
│ ✅ Dados atualizados!                       │
│ 🤖 Processo movido automaticamente para    │
│    'Pedido Confirmado'                     │
│ [Ver Processo no Kanban]                   │
└────────────────────────────────────────────┘

Usuário clica [Ver Processo no Kanban]
→ Redireciona para /workflow/board/pedidos

┌──────────────────────────────────────────────────────────────┐
│ 🛒 Fluxo de Pedidos                    [+ Novo Processo]     │
├───────────┬────────────────┬────────────────┬────────────────┤
│ Orçamento │ Pedido         │ Em Entrega     │ Concluído      │
│ (2)       │ Confirmado (4)⬆│ (1)            │ (15)           │
├───────────┼────────────────┼────────────────┼────────────────┤
│           │                │                │                │
│ [Cards    │ ┌─────────┐    │                │                │
│  antigos] │ │💫 Ped #42│    │                │                │
│           │ │ ACME    │    │                │                │
│           │ │         │    │                │                │
│           │ │ 100x    │    │                │                │
│           │ │ Widget  │    │                │                │
│           │ │         │    │                │                │
│           │ │ ⚠️ Aguar.│    │                │                │
│           │ │ pagamento│   │                │                │
│           │ └─────────┘    │                │                │
│           │                │                │                │
│           │ [Cards antigos]│                │                │
└───────────┴────────────────┴────────────────┴────────────────┘

💫 = Animação de transição recente
```

---

#### DIA 2 - 28/10/2025 18:00 - Análise de IA do Processo

**12. Cron job executa análise (6h após última):**

```
AgentOrchestrator.analyze_process("proc_pedidos_1730032800_42")

1. Carrega processo:
   → process_id = "proc_pedidos_1730032800_42"
   → current_state = "pedido"
   → time_in_state = 3.5 horas

2. Identifica agent:
   → Estado "pedido".agent_config.agent_class = "PedidoAgent"

3. Carrega contexto:
   → ContextLoader.load_full_context("proc_pedidos_1730032800_42")

4. ContextLoader busca:
   → process: {...}
   → history: [{created}, {auto_transitioned}]
   → form_data: {cliente:"ACME Corp", aprovado_cliente:true, pagamento_recebido:false, ...}
   → kanban_config: {pedidos_kanban.json}
   → historical_patterns (PatternAnalyzer):
      - avg_payment_time_hours: 30.0
      - common_sequence: "orcamento→pedido→entrega→concluido"
   → similar_processes:
      - 15 processos similares (cliente_similar, valor_similar)
      - 93% tiveram pagamento em até 48h
   → client_history:
      - Cliente: ACME Corp
      - total_processes: 5
      - avg_payment_time_hours: 24.0
      - payment_reliability: 1.0 (100%)

5. PedidoAgent.analyze(process, context):

   time_in_state = 3.5 horas
   pagamento_recebido = false
   avg_payment_time_cliente = 24 horas
   payment_reliability = 100%

   Decisão:
   - Processo há apenas 3.5h em "Pedido"
   - Cliente ACME Corp é confiável (100% pagamentos)
   - Média de pagamento do cliente: 24h
   - Ainda dentro do esperado

   Retorna:
   {
     should_transition: false,
     target_state: null,
     confidence: 0.9,
     justification: "Processo dentro do tempo esperado para pagamento. Cliente ACME Corp tem histórico de 100% pagamentos e média de 24 horas.",
     reasoning: [
       "Tempo no estado: 3.5 horas",
       "Tempo médio do cliente: 24 horas",
       "Confiabilidade de pagamento: 100%",
       "Ainda dentro do padrão normal"
     ],
     recommendations: [],
     risk_factors: []
   }

6. AgentOrchestrator:
   → Salva análise no WorkflowRepository
   → Não há recomendações high priority
   → Não notifica usuário
```

---

#### DIA 3 - 29/10/2025 09:00 - Pagamento Confirmado

**13. Usuário acessa edição do pedido:**

```
Navegador → http://localhost:5000/pedidos/edit/42
```

**14. Marca "Pagamento Recebido?" e clica [Salvar]:**

```
POST /pedidos/edit/42

Backend (fluxo idêntico ao anterior):

1. Atualiza: pagamento_recebido = true

2. FormTriggerManager.on_form_updated()
   → Atualiza process_data do processo

3. AutoTransitionEngine.check_and_transition()
   → Estado atual: "pedido"
   → Próximo estado: "entrega"
   → Pré-requisitos:
      a) pagamento_confirmado (field_check):
         - field: pagamento_recebido
         - value: true
         - actual: true ✅ SATISFIED

      b) estoque_disponivel (external_api):
         - Endpoint: https://api.erp.empresa.com/check_stock
         - Payload: {produto_id: "WGT-PREM-001", quantidade: 100}
         - Request HTTP POST com Authorization header
         - Response esperada: {available: true}
         - Response recebida: {available: true, quantity_available: 250}
         - ✅ SATISFIED

   → all_satisfied = True
   → Move automaticamente: "pedido" → "entrega"

4. Registra histórico:
   {
     timestamp: "2025-10-29T09:00:22",
     action: "auto_transitioned",
     from_state: "pedido",
     to_state: "entrega",
     actor: "system",
     actor_type: "auto_transition",
     trigger: "prerequisite_met",
     forced: false,
     prerequisites_checked: {
       pagamento_confirmado: {satisfied: true, ...},
       estoque_disponivel: {satisfied: true, api_response: {...}}
     }
   }

5. Verifica próximo estado: "concluido"
   → Não tem pré-requisitos
   → is_final = true
   → Não move automaticamente (estados finais requerem ação manual)
   → Para cascata

6. Redireciona com mensagem:
   "✅ Dados atualizados! Processo movido para 'Em Entrega'"
```

**15. Quadro Kanban atualizado:**

```
┌──────────────────────────────────────────────────────────────┐
│ 🛒 Fluxo de Pedidos                    [+ Novo Processo]     │
├───────────┬────────────────┬────────────────┬────────────────┤
│ Orçamento │ Pedido         │ Em Entrega     │ Concluído      │
│ (2)       │ Confirmado (3) │ (2) ⬆️          │ (15)           │
├───────────┼────────────────┼────────────────┼────────────────┤
│           │                │                │                │
│ [Cards]   │ [Cards]        │ ┌─────────┐    │                │
│           │                │ │💫 Ped #42│    │                │
│           │                │ │ ACME    │    │                │
│           │                │ │         │    │                │
│           │                │ │ ✅ Pronto│    │                │
│           │                │ │ p/ entreg│   │                │
│           │                │ └─────────┘    │                │
│           │                │                │                │
│           │                │ [Card antigo]  │                │
└───────────┴────────────────┴────────────────┴────────────────┘
```

---

#### DIA 5 - 30/10/2025 16:00 - Entrega Concluída

**16. Usuário arrasta card no Kanban:**

```
Navegador → http://localhost:5000/workflow/board/pedidos

Ação: Usuário arrasta card "Pedido #42" de "Em Entrega" para "Concluído"

Frontend (JavaScript):
→ Evento drag-and-drop capturado
→ AJAX POST para /api/transition/proc_pedidos_1730032800_42

Payload:
{
  to_state: "concluido",
  actor_type: "user",
  trigger: "drag_and_drop"
}

Backend:

1. TransitionHandler recebe requisição

2. Valida transição:
   → Verifica se "entrega" → "concluido" é permitido
   → transition_rules.allowed_transitions.entrega: ["pedido", "concluido"]
   → ✅ Permitido

3. Verifica pré-requisitos de "concluido":
   → prerequisites: [] (nenhum)
   → ✅ Nenhum pré-requisito

4. Executa transição:
   → current_state: "entrega" → "concluido"
   → Registra histórico:
      {
        timestamp: "2025-10-30T16:00:00",
        action: "manual_transition",
        from_state: "entrega",
        to_state: "concluido",
        actor: "user123",
        actor_type: "user",
        trigger: "drag_and_drop",
        forced: false
      }

5. Calcula métricas:
   → Tempo total: created_at (27/10 10:00) → concluido (30/10 16:00)
   → Duração: 3.25 dias (78 horas)
   → Meta: 5.0 dias
   → Performance: 35% mais rápido ✅

6. Retorna sucesso:
   {status: "success", message: "Processo concluído!"}

Frontend:
→ Animação de card movendo para coluna "Concluído"
→ Toast: "✅ Processo concluído em 3.2 dias (35% mais rápido que a meta!)"
```

**17. Quadro final:**

```
┌──────────────────────────────────────────────────────────────┐
│ 🛒 Fluxo de Pedidos                    [+ Novo Processo]     │
├───────────┬────────────────┬────────────────┬────────────────┤
│ Orçamento │ Pedido         │ Em Entrega     │ Concluído      │
│ (2)       │ Confirmado (3) │ (1)            │ (16) ⬆️         │
├───────────┼────────────────┼────────────────┼────────────────┤
│           │                │                │                │
│ [Cards]   │ [Cards]        │ [Card]         │ ┌─────────┐    │
│           │                │                │ │🎉 Ped #42│    │
│           │                │                │ │ ACME    │    │
│           │                │                │ │         │    │
│           │                │                │ │ 3.2 dias│    │
│           │                │                │ │ ⚡ 35%   │    │
│           │                │                │ │ mais rápido│  │
│           │                │                │ └─────────┘    │
│           │                │                │                │
│           │                │                │ [Cards antigos]│
└───────────┴────────────────┴────────────────┴────────────────┘
```

### 13.4 Histórico Completo do Processo

Ao clicar no card "Pedido #42" → [Ver Histórico]:

```
+------------------------------------------------------------------+
|  📜 Histórico Completo: Pedido #42 - ACME Corp                   |
+------------------------------------------------------------------+
|                                                                  |
|  Duração Total: 3.2 dias (78 horas)                              |
|  Meta: 5.0 dias                                                  |
|  Performance: ⚡ 35% mais rápido                                 |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 27/10/2025 10:30:00                                          |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ ✨ Processo Criado                                      │    |
|  │ Actor: system (FormTriggerManager)                      │    |
|  │ Estado: → Orçamento                                     │    |
|  │ Origem: Formulário "pedidos" (ID: 42)                   │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  28 horas em "Orçamento"                                         |
|  (Média: 18.5 horas) ⚠️ 51% acima da média                      |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 28/10/2025 14:30:15                                          |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🤖 Transição Automática                                 │    |
|  │ Actor: system (AutoTransitionEngine)                    │    |
|  │ Transição: Orçamento → Pedido Confirmado               │    |
|  │ Trigger: Pré-requisito "cliente_aprovacao" satisfeito  │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  18.5 horas em "Pedido"                                          |
|  (Média: 36.0 horas) ✅ 49% abaixo da média                     |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 29/10/2025 09:00:22                                          |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🤖 Transição Automática                                 │    |
|  │ Actor: system (AutoTransitionEngine)                    │    |
|  │ Transição: Pedido → Em Entrega                         │    |
|  │ Trigger: Pré-requisitos satisfeitos                    │    |
|  │   ✅ pagamento_confirmado                               │    |
|  │   ✅ estoque_disponivel (API externa)                   │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  31.0 horas em "Entrega"                                         |
|  (Média: 48.0 horas) ✅ 35% abaixo da média                     |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 30/10/2025 16:00:00                                          |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 👤 Transição Manual                                     │    |
|  │ Actor: user123 (João Silva)                            │    |
|  │ Transição: Em Entrega → Concluído                      │    |
|  │ Método: Drag-and-drop no Kanban                        │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📊 RESUMO DO PROCESSO                                           |
|                                                                  |
|  Total de Transições: 3                                          |
|  • Automáticas (System): 2                                       |
|  • Manuais (User): 1                                             |
|  • Por Agent (IA): 0                                             |
|                                                                  |
|  Transições Forçadas: 0                                          |
|  Retrocessos: 0                                                  |
|                                                                  |
|  Performance Geral: ⚡ Excelente                                 |
|  • Tempo total: 35% abaixo da meta                              |
|  • Estado "Pedido": 49% mais rápido                             |
|  • Estado "Entrega": 35% mais rápido                            |
|                                                                  |
|  [Exportar Histórico] [Fechar]                                  |
|                                                                  |
+------------------------------------------------------------------+
```

---

## 14. Fases de Implementação

### 14.1 Visão Geral das 5 Fases MVP

```
+------------------------------------------------------------------+
|                  Roadmap de Implementação v4.0                   |
+------------------------------------------------------------------+

FASE 1: Core Kanban-Form Integration (Sprints 1-2) ━━━ 10 dias
├─ KanbanRegistry
├─ FormTriggerManager
├─ ProcessFactory
└─ CRUD básico de processos

FASE 2: AutoTransitionEngine (Sprints 3-4) ━━━━━━━━━━ 10 dias
├─ 3 tipos de transição (Manual, System, Agent)
├─ PrerequisiteChecker (4 tipos)
├─ Progressão em cascata
└─ Timeout handlers

FASE 3: IA Básica (Sprints 5-6) ━━━━━━━━━━━━━━━━━━━━━ 10 dias
├─ BaseAgent (abstrato)
├─ 3 agents concretos (Orcamento, Pedido, Entrega)
├─ AgentOrchestrator
└─ PatternAnalyzer inicial

FASE 4: Editor Visual + Dashboard (Sprints 7-8) ━━━━━ 10 dias
├─ Interface admin do Editor Visual
├─ Drag & Drop de estados
├─ Dashboard básico de Analytics
└─ Gráficos essenciais

FASE 5: Funcionalidades Avançadas (Sprints 9-10) ━━━━ 10 dias
├─ AnomalyDetector completo
├─ Exportações (CSV, PDF)
├─ Auditoria visual
└─ Otimizações e refinamentos

TOTAL: 50 dias (~10 semanas)
```

### 14.2 Fase 1: Core Kanban-Form Integration (10 dias)

#### Sprint 1 (Dias 1-5)

**Objetivo:** Estabelecer fundação do sistema de vinculação

**Dia 1-2: Estruturas de Dados**

```
✅ TAREFAS:
├─ Definir schema de vinculação Kanban↔Form
│  └─ Campo linked_forms em Kanban JSON
├─ Criar estrutura de kanban_registry.json
├─ Definir tabelas de banco de dados
│  ├─ kanbans
│  ├─ kanban_forms (N:N relationship)
│  └─ workflow_processes
└─ Criar exemplos de Kanban com vinculação

📁 ARQUIVOS CRIADOS:
- src/config/kanban_registry.json
- docs/schemas/kanban_schema.json
- tests/fixtures/sample_kanban_with_links.json

🧪 TESTES:
- Validação de schema JSON
```

**Dia 3-4: KanbanRegistry**

```
✅ TAREFAS:
├─ Implementar classe KanbanRegistry
│  ├─ get_kanbans_for_form()
│  ├─ get_forms_for_kanban()
│  ├─ get_primary_form()
│  └─ should_auto_create_process()
├─ Loader de kanban_registry.json
└─ Cache de 5 minutos

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/kanban_registry.py
- tests/test_kanban_registry.py

🧪 TESTES:
- test_get_kanbans_for_form()
- test_get_forms_for_kanban()
- test_get_primary_form()
- test_should_auto_create_process()
- test_cache_expiration()

✅ CRITÉRIO DE ACEITE:
- Todos testes passando
- Cobertura > 90%
```

**Dia 5: Integração com Sistema Existente**

```
✅ TAREFAS:
├─ Integrar KanbanRegistry com rotas existentes
├─ Atualizar loader de Kanbans
└─ Script de migração para Kanbans antigos

📁 ARQUIVOS MODIFICADOS:
- src/VibeCForms.py (imports)
- src/workflow/__init__.py

🧪 TESTES:
- test_registry_loads_at_startup()
- test_registry_handles_missing_file()
```

#### Sprint 2 (Dias 6-10)

**Objetivo:** Implementar criação automática de processos

**Dia 6-7: ProcessFactory**

```
✅ TAREFAS:
├─ Implementar classe ProcessFactory
│  ├─ create_from_form()
│  ├─ _apply_template()
│  ├─ find_processes_by_source()
│  └─ update_process_data()
├─ Geração de process_id único
└─ Mapeamento de campos

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/process_factory.py
- tests/test_process_factory.py

🧪 TESTES:
- test_create_from_form()
- test_apply_template()
- test_find_processes_by_source()
- test_process_id_uniqueness()

✅ CRITÉRIO DE ACEITE:
- Processo criado com todos campos corretos
- Templates aplicados corretamente
- IDs únicos garantidos
```

**Dia 8-9: FormTriggerManager**

```
✅ TAREFAS:
├─ Implementar classe FormTriggerManager
│  ├─ on_form_saved()
│  ├─ on_form_updated()
│  └─ on_form_deleted() [opcional]
├─ Integração com KanbanRegistry
└─ Integração com ProcessFactory

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/form_trigger_manager.py
- tests/test_form_trigger_manager.py

🧪 TESTES:
- test_on_form_saved_creates_process()
- test_on_form_saved_no_kanban()
- test_on_form_updated_updates_process()
- test_multiple_kanbans_for_one_form()

✅ CRITÉRIO DE ACEITE:
- Processos criados automaticamente
- Múltiplos Kanbans suportados
- Atualização de process_data funciona
```

**Dia 10: Integração com Rotas de Formulários**

```
✅ TAREFAS:
├─ Modificar POST /<form_path> para chamar FormTriggerManager
├─ Modificar POST /<form_path>/edit/<id>
└─ Adicionar mensagens de feedback ao usuário

📁 ARQUIVOS MODIFICADOS:
- src/VibeCForms.py (route handlers)

🧪 TESTES DE INTEGRAÇÃO:
- test_form_save_creates_process_integration()
- test_form_update_updates_process_integration()
- test_redirect_to_kanban_after_save()

✅ CRITÉRIO DE ACEITE:
- Salvar formulário cria processo
- Mensagem de sucesso mostrada
- Botão "Ver no Kanban" funciona
```

**Entregável Fase 1:**
- Processos criados automaticamente ao salvar formulários ✅
- Vinculação Kanban↔Form funcionando ✅
- 15+ testes unitários + 5+ testes integração ✅

---

### 14.3 Fase 2: AutoTransitionEngine (10 dias)

#### Sprint 3 (Dias 11-15)

**Objetivo:** Implementar sistema de pré-requisitos e checker

**Dia 11-12: PrerequisiteChecker - field_check**

```
✅ TAREFAS:
├─ Implementar classe PrerequisiteChecker
├─ Método check_all()
├─ Método _check_field()
│  ├─ Suporte a 10 condições (equals, not_equals, etc)
│  └─ Busca em process_data
└─ Classe CheckResult

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/prerequisite_checker.py
- tests/test_prerequisite_checker.py

🧪 TESTES:
- test_check_field_equals()
- test_check_field_greater_than()
- test_check_field_contains()
- test_check_field_not_empty()
- test_all_conditions()

✅ CRITÉRIO DE ACEITE:
- Todas 10 condições funcionando
- Retorna CheckResult com detalhes
```

**Dia 13: PrerequisiteChecker - time_elapsed**

```
✅ TAREFAS:
├─ Método _check_time()
├─ Suporte a from_state
├─ Suporte a from_transition
└─ Cálculo de tempo decorrido

🧪 TESTES:
- test_check_time_since_created()
- test_check_time_since_last_transition()
- test_check_time_in_specific_state()
- test_check_time_max_exceeded()
```

**Dia 14: PrerequisiteChecker - external_api**

```
✅ TAREFAS:
├─ Método _check_api()
├─ Substituição de variáveis em payload
├─ Timeout handling
├─ Retry logic (3 tentativas)
└─ Parsing de resposta

🧪 TESTES:
- test_check_api_success()
- test_check_api_timeout()
- test_check_api_variable_substitution()
- test_check_api_retry_on_failure()

🔒 SEGURANÇA:
- Validação de URL
- Headers sanitizados
- Timeout obrigatório (max 10s)
```

**Dia 15: PrerequisiteChecker - custom_script**

```
✅ TAREFAS:
├─ Método _check_script()
├─ Execução segura de scripts Python
├─ Sandbox environment
├─ Timeout handling
└─ Validação de retorno

🧪 TESTES:
- test_check_script_success()
- test_check_script_timeout()
- test_check_script_invalid_return()
- test_check_script_security()

🔒 SEGURANÇA:
- Scripts em diretório específico
- Sem acesso a imports perigosos
- Timeout obrigatório (max 30s)
```

#### Sprint 4 (Dias 16-20)

**Objetivo:** Implementar AutoTransitionEngine e TransitionHandler

**Dia 16-17: TransitionHandler**

```
✅ TAREFAS:
├─ Implementar classe TransitionHandler
├─ Método transition()
├─ Validação de transições permitidas
├─ Registro no histórico
└─ Integração com WorkflowRepository

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/transition_handler.py
- tests/test_transition_handler.py

🧪 TESTES:
- test_transition_success()
- test_transition_invalid()
- test_transition_registers_history()
- test_transition_forced()
```

**Dia 18-19: AutoTransitionEngine**

```
✅ TAREFAS:
├─ Implementar classe AutoTransitionEngine
├─ Método check_and_transition()
├─ Lógica de progressão em cascata
├─ Limite de segurança (max 3 cascatas)
└─ Delay configurável entre transições

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/auto_transition_engine.py
- tests/test_auto_transition_engine.py

🧪 TESTES:
- test_auto_transition_single_state()
- test_auto_transition_cascade()
- test_auto_transition_stops_at_unsatisfied()
- test_auto_transition_max_cascade_limit()
- test_auto_transition_delay()

✅ CRITÉRIO DE ACEITE:
- Transições automáticas funcionam
- Cascata para em pré-req não satisfeito
- Limite de segurança respeitado
- Histórico completo registrado
```

**Dia 20: Timeout Handlers**

```
✅ TAREFAS:
├─ Implementar TimeoutManager
├─ Verificação periódica (cron job)
├─ Ações suportadas:
│  ├─ send_notification
│  ├─ escalate
│  ├─ auto_transition
│  └─ run_script
└─ Registro de timeouts executados

📁 ARQUIVOS CRIADOS:
- src/workflow/engine/timeout_manager.py
- tests/test_timeout_manager.py

🧪 TESTES:
- test_timeout_send_notification()
- test_timeout_escalate()
- test_timeout_auto_transition()
- test_timeout_not_triggered_before_time()
```

**Entregável Fase 2:**
- AutoTransitionEngine completo ✅
- 4 tipos de pré-requisitos funcionando ✅
- Progressão em cascata ✅
- Timeout handlers ✅
- 30+ testes unitários ✅

---

### 14.4 Fase 3: IA Básica (10 dias)

#### Sprint 5 (Dias 21-25)

**Objetivo:** Implementar sistema de agentes de IA

**Dia 21-22: BaseAgent e AgentOrchestrator**

```
✅ TAREFAS:
├─ Implementar BaseAgent (abstrato)
│  ├─ Método analyze() (abstrato)
│  ├─ Método get_required_context()
│  └─ Método load_context()
├─ Implementar AgentOrchestrator
│  ├─ analyze_process()
│  ├─ analyze_all_active_processes()
│  └─ _notify_user()
└─ Sistema de registro de agents por estado

📁 ARQUIVOS CRIADOS:
- src/workflow/agents/base_agent.py
- src/workflow/agents/agent_orchestrator.py
- tests/test_base_agent.py
- tests/test_agent_orchestrator.py

✅ CRITÉRIO DE ACEITE:
- BaseAgent é abstrato
- AgentOrchestrator coordena agents
- Notificações enviadas corretamente
```

**Dia 23: OrcamentoAgent**

```
✅ TAREFAS:
├─ Implementar OrcamentoAgent
├─ Análise de tempo no estado
├─ Comparação com histórico do cliente
├─ Recomendações (contact_client, review_pricing)
└─ Identificação de fatores de risco

📁 ARQUIVOS CRIADOS:
- src/workflow/agents/orcamento_agent.py
- tests/test_orcamento_agent.py

🧪 TESTES:
- test_orcamento_agent_normal_time()
- test_orcamento_agent_delayed()
- test_orcamento_agent_recommendations()
```

**Dia 24: PedidoAgent**

```
✅ TAREFAS:
├─ Implementar PedidoAgent
├─ Verificação de pagamento
├─ Análise de confiabilidade do cliente
├─ Sugestões de transição
└─ Cálculo de duração esperada

📁 ARQUIVOS CRIADOS:
- src/workflow/agents/pedido_agent.py
- tests/test_pedido_agent.py

🧪 TESTES:
- test_pedido_agent_payment_pending()
- test_pedido_agent_payment_received()
- test_pedido_agent_reliable_client()
- test_pedido_agent_unreliable_client()
```

**Dia 25: EntregaAgent**

```
✅ TAREFAS:
├─ Implementar EntregaAgent
├─ Análise de logística
├─ Detecção de atrasos
└─ Sugestões de escalação

📁 ARQUIVOS CRIADOS:
- src/workflow/agents/entrega_agent.py
- tests/test_entrega_agent.py
```

#### Sprint 6 (Dias 26-30)

**Objetivo:** Implementar PatternAnalyzer inicial

**Dia 26-27: PatternAnalyzer - Básico**

```
✅ TAREFAS:
├─ Implementar PatternAnalyzer
├─ analyze_transition_patterns()
├─ analyze_state_durations()
└─ Estatísticas básicas (média, mediana, desvio)

📁 ARQUIVOS CRIADOS:
- src/workflow/analytics/pattern_analyzer.py
- tests/test_pattern_analyzer.py

🧪 TESTES:
- test_analyze_transition_patterns()
- test_analyze_state_durations()
- test_common_patterns_detection()
```

**Dia 28: ContextLoader**

```
✅ TAREFAS:
├─ Implementar ContextLoader
├─ load_full_context()
├─ Integração com PatternAnalyzer
└─ Busca de processos similares

📁 ARQUIVOS CRIADOS:
- src/workflow/agents/context_loader.py
- tests/test_context_loader.py
```

**Dia 29-30: Integração e Testes E2E**

```
✅ TAREFAS:
├─ Integrar agents com AgentOrchestrator
├─ Cron job para análise periódica
├─ Testes end-to-end completos
└─ Ajustes e refinamentos

🧪 TESTES E2E:
- test_full_agent_analysis_flow()
- test_agent_recommendations_displayed()
- test_agent_notification_sent()
```

**Entregável Fase 3:**
- 3 agents concretos funcionando ✅
- AgentOrchestrator coordenando análises ✅
- PatternAnalyzer fornecendo contexto ✅
- Notificações de IA funcionando ✅
- 20+ testes unitários + 5+ E2E ✅

---

### 14.5 Fase 4: Editor Visual + Dashboard (10 dias)

#### Sprint 7 (Dias 31-35)

**Objetivo:** Criar interface admin do Editor Visual

**Dia 31-32: Editor - Estrutura Base**

```
✅ TAREFAS:
├─ Criar rota /workflow/admin
├─ Lista de Kanbans existentes
├─ Botão "+ Novo Kanban"
├─ Template admin/editor.html
└─ CSS e JavaScript básicos

📁 ARQUIVOS CRIADOS:
- src/templates/workflow/admin/editor.html
- src/templates/workflow/admin/kanban_list.html
- static/css/kanban_editor.css
- static/js/kanban_editor.js

🎨 UI:
- Layout responsivo
- Cards de Kanbans
- Busca e filtros
```

**Dia 33: Editor - Formulário de Criação**

```
✅ TAREFAS:
├─ Wizard multi-step (4 passos)
│  ├─ Passo 1: Informações básicas
│  ├─ Passo 2: Definir estados
│  ├─ Passo 3: Vincular formulários
│  └─ Passo 4: Revisar e salvar
├─ Validação em tempo real (JavaScript)
└─ Seletor de ícones

📁 ARQUIVOS:
- static/js/kanban_wizard.js
- src/templates/workflow/admin/wizard_steps.html
```

**Dia 34: Editor - Drag & Drop de Estados**

```
✅ TAREFAS:
├─ Biblioteca Sortable.js para drag-drop
├─ Reordenação visual de estados
├─ Modal de edição de estado
└─ Configuração de cores e ícones

📁 ARQUIVOS:
- static/js/state_dragdrop.js
- src/templates/workflow/admin/edit_state_modal.html

🎨 UI:
- Animações suaves
- Feedback visual
- Preview em tempo real
```

**Dia 35: Editor - Configuração de Pré-requisitos**

```
✅ TAREFAS:
├─ Interface para adicionar pré-requisitos
├─ Modal com seletor de tipo
├─ Forms específicos para cada tipo
└─ Validação de configuração

📁 ARQUIVOS:
- src/templates/workflow/admin/prerequisite_modal.html
- static/js/prerequisite_editor.js
```

#### Sprint 8 (Dias 36-40)

**Objetivo:** Implementar Dashboard de Analytics

**Dia 36: Dashboard - KPIs Principais**

```
✅ TAREFAS:
├─ Criar rota /workflow/analytics
├─ Template analytics.html
├─ Cálculo de KPIs:
│  ├─ Processos ativos
│  ├─ Taxa de conclusão
│  ├─ Tempo médio
│  └─ Volume por estado
└─ Cards de KPI

📁 ARQUIVOS CRIADOS:
- src/templates/workflow/analytics.html
- src/workflow/analytics/dashboard_generator.py
- tests/test_dashboard_generator.py
```

**Dia 37: Dashboard - Gráficos**

```
✅ TAREFAS:
├─ Biblioteca Chart.js
├─ Funil de conversão
├─ Linha do tempo de volume
├─ Distribuição por estado
└─ Heatmap de transições (ASCII)

📁 ARQUIVOS:
- static/js/charts.js
- static/css/analytics.css

🎨 GRÁFICOS:
- Interativos
- Responsivos
- Exportáveis como imagem
```

**Dia 38: Dashboard - Filtros**

```
✅ TAREFAS:
├─ Filtro por Kanban
├─ Filtro por período
├─ Filtro por estado
└─ Atualização AJAX dos dados

📁 ARQUIVOS:
- static/js/analytics_filters.js
```

**Dia 39-40: KanbanEditorController e Backend**

```
✅ TAREFAS:
├─ Implementar KanbanEditorController
│  ├─ save_kanban()
│  ├─ load_kanban()
│  └─ validate_kanban()
├─ KanbanValidator
├─ KanbanJSONBuilder
└─ API endpoints

📁 ARQUIVOS CRIADOS:
- src/workflow/editor/kanban_editor_controller.py
- src/workflow/editor/kanban_validator.py
- src/workflow/editor/kanban_json_builder.py
- tests/test_kanban_editor.py

🧪 TESTES:
- test_save_kanban_valid()
- test_save_kanban_invalid()
- test_validation_errors()
- test_json_generation()
```

**Entregável Fase 4:**
- Editor Visual completo ✅
- Drag & Drop funcionando ✅
- Dashboard com KPIs e gráficos ✅
- Filtros dinâmicos ✅
- 15+ testes ✅

---

### 14.6 Fase 5: Funcionalidades Avançadas (10 dias)

#### Sprint 9 (Dias 41-45)

**Objetivo:** Completar IA e Analytics avançados

**Dia 41-42: AnomalyDetector Completo**

```
✅ TAREFAS:
├─ Implementar AnomalyDetector
├─ detect_stuck_processes()
├─ detect_anomalous_transitions()
├─ Algoritmo Isolation Forest
└─ Alertas e notificações

📁 ARQUIVOS CRIADOS:
- src/workflow/analytics/anomaly_detector.py
- tests/test_anomaly_detector.py

🧪 TESTES:
- test_detect_stuck_processes()
- test_detect_anomalous_transitions()
- test_isolation_forest_scoring()
```

**Dia 43: BottleneckAnalyzer**

```
✅ TAREFAS:
├─ Implementar BottleneckAnalyzer
├─ identify_bottlenecks()
├─ Análise de root causes
└─ Recomendações de otimização

📁 ARQUIVOS CRIADOS:
- src/workflow/analytics/bottleneck_analyzer.py
- tests/test_bottleneck_analyzer.py
```

**Dia 44-45: Clustering e ML Básico**

```
✅ TAREFAS:
├─ cluster_similar_processes() (K-means)
├─ Predição de duração (regressão linear simples)
├─ Identificação de fatores de risco
└─ Relatórios semanais automáticos

📁 ARQUIVOS CRIADOS:
- src/workflow/analytics/workflow_ml_model.py
- tests/test_workflow_ml.py

📊 MODELOS:
- Scikit-learn para clustering
- Pandas para análise de dados
```

#### Sprint 10 (Dias 46-50)

**Objetivo:** Exportações, Auditoria e Polish

**Dia 46: Exportações CSV e Excel**

```
✅ TAREFAS:
├─ Implementar CSVExporter
├─ Implementar ExcelExporter
├─ API endpoint /api/workflows/export
└─ Filtros de exportação

📁 ARQUIVOS CRIADOS:
- src/workflow/export/csv_exporter.py
- src/workflow/export/excel_exporter.py
- tests/test_exporters.py
```

**Dia 47: Exportações PDF**

```
✅ TAREFAS:
├─ Implementar PDFExporter
├─ Templates de relatórios
├─ Geração de gráficos para PDF
└─ Agendamento de relatórios

📁 ARQUIVOS CRIADOS:
- src/workflow/export/pdf_exporter.py
- src/workflow/export/report_scheduler.py
- src/templates/reports/executive_pdf.html
- tests/test_pdf_exporter.py

📦 DEPENDÊNCIAS:
- WeasyPrint para PDF
- Jinja2 para templates
```

**Dia 48: Interface de Auditoria**

```
✅ TAREFAS:
├─ Criar rota /workflow/audit
├─ Timeline visual de mudanças
├─ Filtros por usuário, data, ação
├─ Detalhes de cada transição
└─ Exportação de logs

📁 ARQUIVOS CRIADOS:
- src/templates/workflow/audit.html
- src/workflow/audit/audit_viewer.py
- src/workflow/audit/timeline_generator.py
- static/js/audit_timeline.js
- tests/test_audit_viewer.py
```

**Dia 49: Otimizações e Refinamentos**

```
✅ TAREFAS:
├─ Cache de queries frequentes
├─ Índices de banco de dados
├─ Lazy loading de processos no Kanban
├─ Compressão de assets (CSS/JS)
└─ Review de performance

🚀 OTIMIZAÇÕES:
- Cache de KanbanRegistry (5 min)
- Índices: idx_processes_source, idx_processes_kanban
- Paginação de processos (20 por vez)
- Minificação de JS/CSS
```

**Dia 50: Testes Finais e Documentação**

```
✅ TAREFAS:
├─ Testes de regressão completos
├─ Testes de carga básicos
├─ Atualizar CLAUDE.md
├─ Atualizar README.md
├─ Changelog v4.0
└─ Deploy de demonstração

📝 DOCUMENTAÇÃO:
- Guia de uso do Editor Visual
- Guia de configuração de Agents
- API documentation
- Troubleshooting guide

✅ CRITÉRIOS FINAIS:
- Todos 150+ testes passando
- Cobertura > 80%
- Performance aceitável (<500ms páginas)
- Documentação completa
```

**Entregável Final v4.0:**
- Sistema completo funcionando ✅
- IA com 3 agents + Analytics avançado ✅
- Editor Visual + Dashboard ✅
- Exportações + Auditoria ✅
- 150+ testes, cobertura >80% ✅
- Documentação completa ✅

---

### 14.7 Cronograma Visual

```
Semana 1-2 (Fase 1):  [████████████████████] Core Kanban-Form
Semana 3-4 (Fase 2):  [████████████████████] AutoTransitionEngine
Semana 5-6 (Fase 3):  [████████████████████] IA Básica
Semana 7-8 (Fase 4):  [████████████████████] Editor + Dashboard
Semana 9-10 (Fase 5): [████████████████████] Avançado + Polish

Total: 10 semanas (50 dias úteis)

Marcos:
✓ Semana 2: Processos criados automaticamente
✓ Semana 4: Transições automáticas funcionando
✓ Semana 6: Agents de IA analisando processos
✓ Semana 8: Editor Visual completo
✓ Semana 10: v4.0 LANÇAMENTO
```

---

## 15. Estratégia de Testes

### 15.1 Pirâmide de Testes

```
                    /\
                   /  \
                  / E2E \          10 testes (~7%)
                 /______\
                /        \
               / Integração \      30 testes (~20%)
              /____________\
             /              \
            / Testes Unitários \   110 testes (~73%)
           /____________________\

Total: ~150 testes
Meta de cobertura: 80%+
```

### 15.2 Testes Unitários (~110 testes)

#### 15.2.1 KanbanRegistry (10 testes)

```python
# tests/test_kanban_registry.py

import pytest
from src.workflow.engine.kanban_registry import KanbanRegistry

def test_get_kanbans_for_form():
    """Testa busca de Kanbans por formulário."""
    registry = KanbanRegistry()
    kanbans = registry.get_kanbans_for_form("pedidos")
    assert "pedidos" in kanbans
    assert len(kanbans) >= 1

def test_get_forms_for_kanban():
    """Testa busca de formulários por Kanban."""
    registry = KanbanRegistry()
    forms = registry.get_forms_for_kanban("pedidos")
    assert len(forms) > 0
    assert any(f['form_path'] == "pedidos" for f in forms)

def test_get_primary_form():
    """Testa identificação de formulário principal."""
    registry = KanbanRegistry()
    primary = registry.get_primary_form("pedidos")
    assert primary == "pedidos"

def test_should_auto_create_process():
    """Testa verificação de auto-criação."""
    registry = KanbanRegistry()
    should_create = registry.should_auto_create_process("pedidos", "pedidos")
    assert should_create is True

def test_get_kanbans_for_nonexistent_form():
    """Testa busca por formulário inexistente."""
    registry = KanbanRegistry()
    kanbans = registry.get_kanbans_for_form("form_inexistente")
    assert kanbans == []

def test_cache_expiration():
    """Testa expiração do cache."""
    registry = KanbanRegistry()
    # Primeira chamada carrega do disco
    forms1 = registry.get_forms_for_kanban("pedidos")
    # Segunda chamada usa cache
    forms2 = registry.get_forms_for_kanban("pedidos")
    assert forms1 == forms2
    # Força expiração do cache
    registry._cache_timestamp = 0
    # Terceira chamada recarrega do disco
    forms3 = registry.get_forms_for_kanban("pedidos")
    assert forms3 == forms1

def test_registry_handles_missing_file():
    """Testa comportamento com arquivo ausente."""
    registry = KanbanRegistry()
    registry.registry_file = "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        registry._load_registry()

def test_registry_handles_invalid_json():
    """Testa comportamento com JSON inválido."""
    # Criar arquivo temporário com JSON inválido
    # Verificar que lança exceção apropriada
    pass

def test_registry_reload():
    """Testa reload manual do registry."""
    registry = KanbanRegistry()
    registry.reload()
    # Verifica que dados foram recarregados
    assert registry._kanban_to_forms is not None

def test_multiple_forms_one_kanban():
    """Testa Kanban com múltiplos formulários."""
    registry = KanbanRegistry()
    forms = registry.get_forms_for_kanban("pedidos")
    assert len(forms) >= 2  # pedidos + pedidos_urgentes
```

#### 15.2.2 ProcessFactory (12 testes)

```python
# tests/test_process_factory.py

import pytest
from src.workflow.engine.process_factory import ProcessFactory
from src.persistence.workflow_repository import WorkflowRepository

@pytest.fixture
def factory():
    repo = WorkflowRepository()
    return ProcessFactory(repo)

def test_create_from_form(factory):
    """Testa criação de processo a partir de formulário."""
    form_data = {
        "cliente": "ACME Corp",
        "produto": "Widget Premium",
        "quantidade": 10,
        "valor_total": 1500.00
    }

    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data=form_data,
        created_by="user123"
    )

    assert process_id is not None
    assert process_id.startswith("proc_pedidos_")

def test_apply_template(factory):
    """Testa aplicação de templates."""
    template = "Pedido #{id} - {cliente}"
    data = {"cliente": "ACME Corp", "produto": "Widget"}
    extra = {"id": 42}

    result = factory._apply_template(template, data, extra)
    assert result == "Pedido #42 - ACME Corp"

def test_apply_template_missing_variable(factory):
    """Testa template com variável ausente."""
    template = "Pedido #{id} - {cliente_inexistente}"
    data = {"cliente": "ACME"}
    extra = {"id": 42}

    result = factory._apply_template(template, data, extra)
    # Deve retornar template original sem substituir
    assert result == template

def test_find_processes_by_source(factory):
    """Testa busca de processos por formulário origem."""
    # Criar processo de teste
    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data={"cliente": "Test"},
        created_by="user123"
    )

    # Buscar
    processes = factory.find_processes_by_source("pedidos", 42)
    assert len(processes) >= 1
    assert any(p['process_id'] == process_id for p in processes)

def test_update_process_data(factory):
    """Testa atualização de process_data."""
    # Criar processo
    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data={"cliente": "ACME", "aprovado_cliente": False},
        created_by="user123"
    )

    # Atualizar
    new_data = {"cliente": "ACME", "aprovado_cliente": True}
    factory.update_process_data(process_id, new_data)

    # Verificar
    repo = WorkflowRepository()
    process = repo.get_process(process_id)
    assert process['process_data']['aprovado_cliente'] is True

def test_process_id_uniqueness(factory):
    """Testa unicidade de process_ids."""
    ids = set()
    for i in range(100):
        process_id = factory.create_from_form(
            kanban_id="pedidos",
            form_path="pedidos",
            form_id=i,
            form_data={"cliente": f"Test{i}"},
            created_by="user123"
        )
        assert process_id not in ids
        ids.add(process_id)

def test_process_initial_state(factory):
    """Testa estado inicial do processo."""
    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data={"cliente": "Test"},
        created_by="user123"
    )

    repo = WorkflowRepository()
    process = repo.get_process(process_id)
    assert process['current_state'] == "orcamento"

def test_process_history_created(factory):
    """Testa que histórico é criado."""
    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data={"cliente": "Test"},
        created_by="user123"
    )

    repo = WorkflowRepository()
    process = repo.get_process(process_id)
    assert len(process['history']) == 1
    assert process['history'][0]['action'] == "created"
    assert process['history'][0]['to_state'] == "orcamento"

def test_process_with_multiple_kanbans(factory):
    """Testa formulário vinculado a múltiplos Kanbans."""
    # Se um formulário estiver vinculado a 2 Kanbans,
    # criar processo deve funcionar para ambos
    pass

def test_custom_initial_state(factory):
    """Testa processo com estado inicial customizado."""
    # pedidos_urgentes deve iniciar em "pedido" ao invés de "orcamento"
    pass

def test_field_mapping_complex(factory):
    """Testa mapeamento complexo de campos."""
    # Testar mapeamentos aninhados, arrays, etc.
    pass
```

#### 15.2.3 PrerequisiteChecker (20 testes)

```python
# tests/test_prerequisite_checker.py

import pytest
from src.workflow.engine.prerequisite_checker import PrerequisiteChecker

@pytest.fixture
def checker():
    return PrerequisiteChecker()

@pytest.fixture
def sample_process():
    return {
        "process_id": "proc_test_001",
        "kanban_id": "pedidos",
        "current_state": "orcamento",
        "process_data": {
            "cliente": "ACME Corp",
            "aprovado_cliente": False,
            "pagamento_recebido": False,
            "valor_total": 1500.00
        },
        "history": [
            {
                "timestamp": "2025-10-27T10:00:00",
                "action": "created",
                "to_state": "orcamento"
            }
        ]
    }

# field_check tests (10 testes)

def test_check_field_equals_true(checker, sample_process):
    """Testa condição equals com boolean true."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "aprovado_cliente",
        "condition": "equals",
        "value": False
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is True

def test_check_field_equals_false(checker, sample_process):
    """Testa condição equals não satisfeita."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "aprovado_cliente",
        "condition": "equals",
        "value": True
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is False

def test_check_field_greater_than(checker, sample_process):
    """Testa condição greater_than."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "valor_total",
        "condition": "greater_than",
        "value": 1000
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is True

def test_check_field_less_than(checker, sample_process):
    """Testa condição less_than."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "valor_total",
        "condition": "less_than",
        "value": 2000
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is True

def test_check_field_contains(checker, sample_process):
    """Testa condição contains."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "cliente",
        "condition": "contains",
        "value": "ACME"
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is True

def test_check_field_not_empty(checker, sample_process):
    """Testa condição not_empty."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "cliente",
        "condition": "not_empty"
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is True

def test_check_field_not_empty_fail(checker, sample_process):
    """Testa not_empty com campo vazio."""
    sample_process['process_data']['campo_vazio'] = ""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "campo_vazio",
        "condition": "not_empty"
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is False

def test_check_field_nonexistent(checker, sample_process):
    """Testa campo inexistente."""
    prereq = {
        "id": "test",
        "type": "field_check",
        "field": "campo_inexistente",
        "condition": "equals",
        "value": "qualquer"
    }
    result = checker._check_field(sample_process, prereq)
    assert result.satisfied is False

def test_check_all_satisfied(checker, sample_process):
    """Testa múltiplos pré-requisitos todos satisfeitos."""
    prereqs = [
        {
            "id": "test1",
            "type": "field_check",
            "field": "aprovado_cliente",
            "condition": "equals",
            "value": False
        },
        {
            "id": "test2",
            "type": "field_check",
            "field": "valor_total",
            "condition": "greater_than",
            "value": 1000
        }
    ]
    result = checker.check_all(sample_process, prereqs)
    assert result.all_satisfied is True

def test_check_all_not_satisfied(checker, sample_process):
    """Testa múltiplos pré-requisitos com algum não satisfeito."""
    prereqs = [
        {
            "id": "test1",
            "type": "field_check",
            "field": "aprovado_cliente",
            "condition": "equals",
            "value": True  # Não satisfeito
        },
        {
            "id": "test2",
            "type": "field_check",
            "field": "valor_total",
            "condition": "greater_than",
            "value": 1000  # Satisfeito
        }
    ]
    result = checker.check_all(sample_process, prereqs)
    assert result.all_satisfied is False
    assert len(result.not_satisfied) == 1

# time_elapsed tests (5 testes)

def test_check_time_since_created(checker, sample_process):
    """Testa tempo desde criação."""
    # Mock time for testing
    pass

def test_check_time_in_state(checker, sample_process):
    """Testa tempo no estado atual."""
    pass

def test_check_time_max_exceeded(checker, sample_process):
    """Testa tempo máximo excedido."""
    pass

# external_api tests (3 testes)

def test_check_api_success(checker, sample_process):
    """Testa API retornando sucesso."""
    # Mock HTTP request
    pass

def test_check_api_timeout(checker, sample_process):
    """Testa API com timeout."""
    pass

def test_check_api_variable_substitution(checker, sample_process):
    """Testa substituição de variáveis no payload."""
    pass

# custom_script tests (2 testes)

def test_check_script_success(checker, sample_process):
    """Testa script retornando sucesso."""
    pass

def test_check_script_timeout(checker, sample_process):
    """Testa script com timeout."""
    pass
```

#### 15.2.4 AutoTransitionEngine (15 testes)

#### 15.2.5 Agents (15 testes - 5 por agent)

#### 15.2.6 PatternAnalyzer (10 testes)

#### 15.2.7 AnomalyDetector (8 testes)

#### 15.2.8 KanbanEditor (10 testes)

#### 15.2.9 Exporters (10 testes)

### 15.3 Testes de Integração (~30 testes)

```python
# tests/test_workflow_integration.py

def test_form_save_creates_process_integration(client):
    """
    Testa integração completa: salvar formulário → criar processo.
    """
    response = client.post('/pedidos', data={
        'cliente': 'ACME Corp',
        'produto': 'Widget Premium',
        'quantidade': '10',
        'valor_total': '1500.00',
        'aprovado_cliente': '',
        'pagamento_recebido': ''
    })

    assert response.status_code == 302  # Redirect

    # Verifica que processo foi criado
    repo = WorkflowRepository()
    processes = repo.find_processes(filters={"kanban_id": "pedidos"})
    assert len(processes) > 0

def test_form_update_triggers_auto_transition(client):
    """
    Testa: atualizar formulário → atualizar process_data → auto-transição.
    """
    # Criar processo inicial
    # Atualizar formulário marcando aprovado_cliente
    # Verificar que processo moveu para "pedido"
    pass

def test_agent_analysis_flow(client):
    """
    Testa: criar processo → agent analisa → salva recomendações.
    """
    pass

def test_kanban_editor_saves_valid_json(client):
    """
    Testa: criar Kanban no editor → salva JSON válido.
    """
    pass

def test_export_csv_processes(client):
    """
    Testa: exportar processos → CSV válido gerado.
    """
    pass
```

### 15.4 Testes End-to-End (~10 testes)

```python
# tests/test_workflow_e2e.py

def test_complete_pedidos_workflow_e2e(client):
    """
    Testa fluxo completo de pedido:
    1. Criar pedido via formulário
    2. Verificar processo em "Orçamento"
    3. Aprovar cliente → Auto-transição para "Pedido"
    4. Confirmar pagamento → Auto-transição para "Entrega"
    5. Mover manualmente para "Concluído"
    """
    repo = WorkflowRepository()

    # 1. Criar pedido
    response = client.post('/pedidos', data={
        'cliente': 'E2E Test Client',
        'produto': 'E2E Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': '',
        'pagamento_recebido': ''
    })

    # Encontrar processo criado
    processes = repo.find_processes(filters={
        "source_form": "pedidos",
        "process_data.cliente": "E2E Test Client"
    })
    assert len(processes) == 1
    process = processes[0]

    # 2. Verificar estado inicial
    assert process['current_state'] == "orcamento"

    # 3. Aprovar cliente
    form_id = process['source_form_id']
    client.post(f'/pedidos/edit/{form_id}', data={
        'cliente': 'E2E Test Client',
        'produto': 'E2E Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': 'on',
        'pagamento_recebido': ''
    })

    # Verificar auto-transição
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "pedido"
    assert len(process['history']) == 2

    # 4. Confirmar pagamento
    client.post(f'/pedidos/edit/{form_id}', data={
        'cliente': 'E2E Test Client',
        'produto': 'E2E Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': 'on',
        'pagamento_recebido': 'on'
    })

    # Verificar auto-transição para "Entrega"
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "entrega"
    assert len(process['history']) == 3

    # 5. Mover manualmente para "Concluído"
    response = client.post(
        f'/api/transition/{process["process_id"]}',
        json={
            'to_state': 'concluido',
            'actor_type': 'user'
        }
    )
    assert response.status_code == 200

    # Verificar estado final
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "concluido"
    assert len(process['history']) == 4

def test_forced_transition_with_justification_e2e(client):
    """
    Testa transição forçada com justificativa.
    """
    pass

def test_agent_recommendations_displayed_e2e(client):
    """
    Testa que recomendações de agent aparecem na UI.
    """
    pass

def test_dashboard_analytics_e2e(client):
    """
    Testa dashboard carrega com métricas corretas.
    """
    pass

def test_kanban_editor_create_and_use_e2e(client):
    """
    Testa criar Kanban no editor e usar imediatamente.
    """
    pass
```

### 15.5 Cobertura de Testes

**Meta:** 80%+ de cobertura

```bash
# Executar testes com cobertura
uv run pytest --cov=src --cov-report=html --cov-report=term

# Resultado esperado:
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
src/workflow/engine/kanban_registry.py           45      3    93%
src/workflow/engine/process_factory.py           78      8    90%
src/workflow/engine/prerequisite_checker.py     120     15    88%
src/workflow/engine/auto_transition_engine.py    95     10    89%
src/workflow/agents/base_agent.py                35      2    94%
src/workflow/agents/orcamento_agent.py           55      7    87%
src/workflow/agents/pedido_agent.py              60      8    87%
src/workflow/analytics/pattern_analyzer.py      110     18    84%
src/workflow/analytics/anomaly_detector.py       85     12    86%
src/workflow/editor/kanban_editor.py             70      9    87%
src/workflow/export/csv_exporter.py              40      4    90%
-----------------------------------------------------------------
TOTAL                                          1250    185    85%
```

---

## Conclusão Final

O **Sistema de Workflow Kanban v4.0** representa uma evolução completa do VibeCForms com:

✅ **Arquitetura Sólida**: Kanban-Form integration, persistência plugável, Repository pattern

✅ **IA Completa**: 3 agents especializados, PatternAnalyzer, AnomalyDetector, ML básico

✅ **Interface Visual**: Editor drag-and-drop, Dashboard analytics, Timeline de auditoria

✅ **Automação**: AutoTransitionEngine, 4 tipos de pré-requisitos, progressão em cascata

✅ **Exportações**: CSV, PDF, Excel com relatórios customizáveis

✅ **Qualidade**: 150+ testes, cobertura >80%, documentação completa

**Implementação:** 50 dias (10 semanas) divididos em 5 fases MVP

**Resultado:** Sistema enterprise-grade de gestão de workflows com IA integrada, mantendo a simplicidade e filosofia "Avisar, Não Bloquear" do VibeCForms.

---

**Elaborado por:** Rodrigo Santista
**Com assistência de:** Claude Code (Anthropic)
**Data:** Outubro 2025
**Versão:** 4.0 - Parte 3 de 3 (FINAL)
