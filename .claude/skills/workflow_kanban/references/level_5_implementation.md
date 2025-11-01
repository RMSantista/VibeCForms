# Level 5: Implementation
# Sistema Kanban-Workflow VibeCForms v4.0

**Nível de conhecimento**: Master (Mestre)
**Para quem**: Gerentes de projeto e implementadores
**Conteúdo**: Exemplo completo (Order Flow), 5 fases de implementação (50 dias), estratégia de testes (150+ tests)

---

## Navegação

- **Anterior**: [Level 4 - Architecture](level_4_architecture.md)
- **Você está aqui**: Level 5 - Implementation
- **Outros níveis**: [Level 1](level_1_fundamentals.md) | [Level 2](level_2_engine.md) | [Level 3](level_3_interface.md)

---

## 12. Exemplo Completo - Order Flow (Fluxo de Pedidos)

### 12.1 Definição Completa do Kanban

```json
{
  "id": "pedidos",
  "name": "Fluxo de Pedidos",
  "description": "Gerenciamento completo do ciclo de vida de pedidos",
  "icon": "fa-shopping-cart",
  "version": "1.0",

  "states": [
    {
      "id": "orcamento",
      "name": "Orçamento",
      "description": "Solicitação inicial de orçamento",
      "color": "#FFA500",
      "icon": "fa-file-invoice",
      "is_initial": true,
      "auto_transition_to": null,
      "timeout_hours": null,
      "prerequisites": []
    },
    {
      "id": "orcamento_aprovado",
      "name": "Orçamento Aprovado",
      "description": "Orçamento aprovado pelo cliente",
      "color": "#4169E1",
      "icon": "fa-check-circle",
      "is_initial": false,
      "auto_transition_to": null,
      "timeout_hours": 48,
      "timeout_action": {
        "type": "notification",
        "target": "gestor@empresa.com",
        "message": "Orçamento aprovado há 48h sem conversão em pedido"
      }
    },
    {
      "id": "pedido",
      "name": "Pedido Confirmado",
      "description": "Pedido confirmado e em produção",
      "color": "#9370DB",
      "icon": "fa-shopping-basket",
      "is_initial": false,
      "auto_transition_to": "em_entrega",
      "timeout_hours": 48,
      "prerequisites": []
    },
    {
      "id": "em_entrega",
      "name": "Em Entrega",
      "description": "Pedido em processo de entrega",
      "color": "#20B2AA",
      "icon": "fa-truck",
      "is_initial": false,
      "auto_transition_to": null,
      "timeout_hours": 72,
      "timeout_action": {
        "type": "escalation",
        "target": "logistica@empresa.com",
        "message": "Entrega atrasada - investigar"
      }
    },
    {
      "id": "concluido",
      "name": "Concluído",
      "description": "Pedido entregue e finalizado",
      "color": "#32CD32",
      "icon": "fa-check-double",
      "is_initial": false,
      "is_final": true
    },
    {
      "id": "cancelado",
      "name": "Cancelado",
      "description": "Pedido cancelado",
      "color": "#DC143C",
      "icon": "fa-times-circle",
      "is_initial": false,
      "is_final": true
    }
  ],

  "transitions": [
    {
      "from": "orcamento",
      "to": "orcamento_aprovado",
      "type": "manual",
      "label": "Aprovar Orçamento",
      "icon": "fa-thumbs-up",
      "prerequisites": [
        {
          "type": "field_check",
          "field": "valor_total",
          "condition": "not_empty",
          "message": "Valor total deve estar preenchido"
        },
        {
          "type": "field_check",
          "field": "cliente",
          "condition": "not_empty",
          "message": "Cliente deve estar identificado"
        }
      ]
    },
    {
      "from": "orcamento_aprovado",
      "to": "pedido",
      "type": "manual",
      "label": "Confirmar Pedido",
      "icon": "fa-shopping-cart",
      "prerequisites": [
        {
          "type": "field_check",
          "field": "forma_pagamento",
          "condition": "not_empty",
          "message": "Forma de pagamento deve estar definida"
        },
        {
          "type": "external_api",
          "url": "https://api.payment.com/verify/{process_id}",
          "method": "GET",
          "timeout_seconds": 5,
          "message": "Verificação de pagamento pendente"
        }
      ]
    },
    {
      "from": "pedido",
      "to": "em_entrega",
      "type": "system",
      "label": "Iniciar Entrega",
      "auto_trigger": true,
      "prerequisites": []
    },
    {
      "from": "em_entrega",
      "to": "concluido",
      "type": "manual",
      "label": "Finalizar Entrega",
      "icon": "fa-check",
      "prerequisites": [
        {
          "type": "field_check",
          "field": "comprovante_entrega",
          "condition": "not_empty",
          "message": "Comprovante de entrega deve ser anexado"
        }
      ]
    },
    {
      "from": "orcamento",
      "to": "cancelado",
      "type": "manual",
      "label": "Cancelar",
      "icon": "fa-times",
      "prerequisites": []
    },
    {
      "from": "orcamento_aprovado",
      "to": "cancelado",
      "type": "manual",
      "label": "Cancelar",
      "icon": "fa-times",
      "prerequisites": []
    },
    {
      "from": "pedido",
      "to": "cancelado",
      "type": "manual",
      "label": "Cancelar",
      "icon": "fa-times",
      "prerequisites": [
        {
          "type": "field_check",
          "field": "motivo_cancelamento",
          "condition": "not_empty",
          "message": "Motivo do cancelamento deve ser informado"
        }
      ]
    }
  ],

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
      "forma_pagamento": "process_data.forma_pagamento"
    }
  },

  "analytics": {
    "track_duration": true,
    "track_transitions": true,
    "enable_pattern_analysis": true,
    "enable_anomaly_detection": true,
    "kpi_targets": {
      "avg_completion_hours": 72,
      "completion_rate": 0.85,
      "max_time_in_state": {
        "orcamento": 24,
        "pedido": 48,
        "em_entrega": 24
      }
    }
  }
}
```

### 12.2 Formulário "pedidos" Vinculado

```json
{
  "title": "Pedidos",
  "icon": "fa-shopping-cart",
  "fields": [
    {"name": "cliente", "label": "Cliente", "type": "text", "required": true},
    {"name": "produto", "label": "Produto", "type": "text", "required": true},
    {"name": "quantidade", "label": "Quantidade", "type": "number", "required": true},
    {"name": "valor_unitario", "label": "Valor Unitário", "type": "number", "required": true},
    {"name": "valor_total", "label": "Valor Total", "type": "number", "required": true},
    {
      "name": "forma_pagamento",
      "label": "Forma de Pagamento",
      "type": "select",
      "required": true,
      "options": [
        {"value": "boleto", "label": "Boleto"},
        {"value": "cartao", "label": "Cartão"},
        {"value": "pix", "label": "PIX"}
      ]
    },
    {"name": "comprovante_entrega", "label": "Comprovante de Entrega", "type": "text", "required": false},
    {"name": "motivo_cancelamento", "label": "Motivo Cancelamento", "type": "textarea", "required": false}
  ]
}
```

### 12.3 Cenário Passo-a-Passo (5 dias de processo)

**Dia 1 - Segunda, 10:00 - CRIAÇÃO**
```
Maria (vendas) preenche formulário "pedidos":
  - Cliente: ACME Corp
  - Produto: Widget Premium
  - Quantidade: 10
  - Valor unitário: R$ 150,00
  - Valor total: R$ 1500,00
  - Forma pagamento: (vazio)

Clica "Salvar" → Sistema cria processo automaticamente
  process_id: proc_pedidos_1730718000_1
  Estado inicial: "orcamento"
  Título: "Pedido #1 - ACME Corp"
```

**Dia 1 - Segunda, 14:30 - APROVAÇÃO DE ORÇAMENTO**
```
João (gestor comercial) vê processo no quadro Kanban
Tenta mover "orcamento" → "orcamento_aprovado"

Sistema verifica pré-requisitos:
  ✅ valor_total = 1500.00 (not_empty)
  ✅ cliente = "ACME Corp" (not_empty)

Transição permitida → Processo move para "orcamento_aprovado"

Histórico registrado:
  {
    "timestamp": "2025-10-28T14:30:00",
    "from_state": "orcamento",
    "to_state": "orcamento_aprovado",
    "actor": "joao@empresa.com",
    "actor_type": "user",
    "trigger": "manual",
    "prerequisites_satisfied": true
  }
```

**Dia 2 - Terça, 09:00 - CONFIRMAÇÃO DE PEDIDO**
```
Maria atualiza formulário:
  - Forma pagamento: PIX

João tenta mover "orcamento_aprovado" → "pedido"

Sistema verifica pré-requisitos:
  ✅ forma_pagamento = "PIX" (not_empty)
  ⏳ Chamando API: https://api.payment.com/verify/proc_pedidos_1730718000_1
  ❌ API retornou 404 (pagamento não confirmado)

Modal de aviso:
  "⚠️ Pré-requisito pendente:
   Verificação de pagamento falhou (API não confirmou)

   Deseja continuar mesmo assim?"

   [Cancelar] [Continuar com Justificativa]

João clica "Continuar com Justificativa":
  Justificativa: "Cliente VIP - pagamento verbal confirmado por telefone"

Transição forçada → Processo move para "pedido"

Histórico registrado:
  {
    "timestamp": "2025-10-29T09:00:00",
    "from_state": "orcamento_aprovado",
    "to_state": "pedido",
    "actor": "joao@empresa.com",
    "actor_type": "user",
    "trigger": "manual",
    "forced": true,
    "prerequisites_satisfied": false,
    "justification": "Cliente VIP - pagamento verbal confirmado por telefone",
    "failed_prerequisites": ["external_api: payment verification"]
  }
```

**Dia 4 - Quinta, 09:00 - AUTO-TRANSIÇÃO PARA ENTREGA**
```
AutoTransitionEngine detecta:
  - Estado atual: "pedido"
  - Configuração: auto_transition_to = "em_entrega"
  - Timeout: 48 horas
  - Processo está em "pedido" há 48 horas

Sistema executa transição automática → "em_entrega"

Histórico registrado:
  {
    "timestamp": "2025-10-31T09:00:00",
    "from_state": "pedido",
    "to_state": "em_entrega",
    "actor": "system",
    "actor_type": "system",
    "trigger": "auto_transition",
    "timeout_triggered": true
  }
```

**Dia 5 - Sexta, 16:00 - CONCLUSÃO**
```
Carlos (logística) atualiza formulário:
  - Comprovante entrega: "COMP-2025-001"

Move "em_entrega" → "concluido"

Sistema verifica:
  ✅ comprovante_entrega = "COMP-2025-001" (not_empty)

Transição permitida → Processo finalizado

Histórico registrado:
  {
    "timestamp": "2025-11-01T16:00:00",
    "from_state": "em_entrega",
    "to_state": "concluido",
    "actor": "carlos@empresa.com",
    "actor_type": "user",
    "trigger": "manual",
    "prerequisites_satisfied": true
  }

Analytics atualizado:
  - Duração total: 102 horas (4.25 dias)
  - Tempo em orcamento: 4.5h
  - Tempo em orcamento_aprovado: 18.5h
  - Tempo em pedido: 48h
  - Tempo em em_entrega: 31h
```

---

## 13. Fases de Implementação

### 13.1 Overview das 5 Fases MVP

```
+------------------------------------------------------------------+
|                     ROADMAP DE IMPLEMENTAÇÃO                     |
|                        50 dias (10 semanas)                      |
+------------------------------------------------------------------+

FASE 1: Core Kanban-Form Integration (10 dias)
  └─→ Objetivo: Vincular forms a kanbans, gerar processos

FASE 2: AutoTransitionEngine (10 dias)
  └─→ Objetivo: Transições automáticas, pré-requisitos, timeouts

FASE 3: Basic AI (10 dias)
  └─→ Objetivo: Pattern analysis, agentes básicos, sugestões

FASE 4: Visual Editor + Dashboard (10 dias)
  └─→ Objetivo: Interface para criar kanbans, analytics dashboard

FASE 5: Advanced Features (10 dias)
  └─→ Objetivo: Exports, auditoria, ML avançado
```

### 13.2 Fase 1: Core Kanban-Form Integration (Dias 1-10)

**Objetivo**: Sistema básico funcional - forms criam processos em kanbans

**Entregas:**
- KanbanRegistry (mapeamento bidirectional)
- FormTriggerManager (hook em form saves)
- ProcessFactory (criação de processos)
- Kanban Board básico (visualização)
- Transições manuais funcionando

**Tarefas por dia:**

```
Dia 1-2: Setup inicial
  - Criar estrutura de diretórios src/workflow/
  - Criar src/config/kanbans/
  - Implementar BaseRepository extension (WorkflowRepository)

Dia 3-4: KanbanRegistry + FormTriggerManager
  - Implementar kanban_registry.py
  - Implementar form_trigger_manager.py
  - Criar testes unitários

Dia 5-6: ProcessFactory
  - Implementar process_factory.py
  - Implementar field_mapping
  - Testar criação de processos

Dia 7-8: Kanban Board UI
  - Criar template workflow_board.html
  - Implementar drag & drop básico
  - CSS/JS para quadro kanban

Dia 9-10: Transições Manuais
  - Implementar endpoint POST /workflow/transition
  - Registrar histórico
  - Testes end-to-end
```

**Testes (30):**
- kanban_registry: 8 tests
- form_trigger_manager: 6 tests
- process_factory: 8 tests
- workflow_repository: 5 tests
- kanban_board UI: 3 tests

### 13.3 Fase 2: AutoTransitionEngine (Dias 11-20)

**Objetivo**: Transições automáticas e sistema de pré-requisitos

**Entregas:**
- AutoTransitionEngine completo
- PrerequisiteChecker (4 tipos)
- Cascade progression (max 3 níveis)
- Timeout handlers
- Transições forçadas com justificativa

**Tarefas por dia:**

```
Dia 11-12: AutoTransitionEngine base
  - Implementar auto_transition_engine.py
  - Lógica de check_auto_progression()
  - Cascade detection

Dia 13-15: PrerequisiteChecker
  - Implementar prerequisite_checker.py
  - Tipo 1: field_check (5 condições)
  - Tipo 2: external_api
  - Tipo 3: time_elapsed
  - Tipo 4: custom_script

Dia 16-17: Timeout System
  - Implementar timeout detection
  - Timeout handlers (4 tipos)
  - Scheduler para verificação periódica

Dia 18-20: Forced Transitions
  - Modal de aviso de pré-requisitos
  - Justification system
  - Audit logging de transições forçadas
```

**Testes (40):**
- auto_transition_engine: 15 tests
- prerequisite_checker: 16 tests
- timeout_system: 6 tests
- forced_transitions: 3 tests

### 13.4 Fase 3: Basic AI (Dias 21-30)

**Objetivo**: Análise de padrões e agentes de IA básicos

**Entregas:**
- PatternAnalyzer (frequent patterns)
- AnomalyDetector (processos travados)
- BaseAgent + 3 agentes concretos
- AgentOrchestrator
- UI de sugestões de IA

**Tarefas por dia:**

```
Dia 21-23: PatternAnalyzer
  - Implementar pattern_analyzer.py
  - Algoritmo de frequent pattern mining
  - Sequential pattern analysis

Dia 24-25: AnomalyDetector
  - Implementar anomaly_detector.py
  - Detecção de processos travados
  - Statistical outliers

Dia 26-28: AI Agents
  - Implementar base_agent.py (abstract)
  - Implementar 3 agentes concretos
  - AgentOrchestrator
  - ContextLoader

Dia 29-30: UI de Sugestões
  - Badge de sugestão em kanban board
  - Modal com análise do agente
  - Botão "Aceitar Sugestão"
```

**Testes (40):**
- pattern_analyzer: 10 tests
- anomaly_detector: 8 tests
- base_agent: 6 tests
- agent_orchestrator: 8 tests
- agent_ui: 8 tests

### 13.5 Fase 4: Visual Editor + Dashboard (Dias 31-40)

**Objetivo**: Interface visual para criar kanbans e analytics

**Entregas:**
- Visual Kanban Editor (admin)
- Analytics Dashboard
- Export básico (CSV)
- Gráficos e KPIs

**Tarefas por dia:**

```
Dia 31-35: Visual Editor
  - Template workflow_admin.html
  - Drag & drop de estados
  - Editor de transições
  - Modal de pré-requisitos
  - Preview de kanban
  - Salvamento como JSON

Dia 36-40: Analytics Dashboard
  - Template workflow_analytics.html
  - KPIs principais (3 cards)
  - Gráfico de volume por estado
  - Gráfico de tempo médio
  - Bottleneck identification
  - Export CSV básico
```

**Testes (30):**
- visual_editor: 15 tests
- analytics_dashboard: 10 tests
- csv_export: 5 tests

### 13.6 Fase 5: Advanced Features (Dias 41-50)

**Objetivo**: Features avançadas e polimento

**Entregas:**
- Audit timeline visual
- Export PDF/Excel
- ML models (duration predictor)
- Notification system
- Report scheduling

**Testes (10):**
- audit_timeline: 3 tests
- pdf_export: 2 tests
- excel_export: 2 tests
- ml_models: 3 tests

---

## 14. Estratégia de Testes

### 14.1 Pirâmide de Testes

```
          /\
         /  \  E2E Tests (~10)
        /────\
       / Integ.\  Integration Tests (~30)
      /  Tests  \
     /───────────\
    /    Unit     \  Unit Tests (~110)
   /    Tests      \
  /_________________\

TOTAL: ~150 testes
Coverage target: 80%+
```

### 14.2 Unit Tests (~110 testes)

**Persistence Layer (20)**
- BaseRepository: 5
- TxtAdapter: 5
- SQLiteAdapter: 5
- WorkflowRepository: 5

**Workflow Engine (50)**
- KanbanRegistry: 8
- FormTriggerManager: 6
- ProcessFactory: 8
- AutoTransitionEngine: 15
- PrerequisiteChecker: 16
- Timeout System: 6

**Analytics & AI (25)**
- PatternAnalyzer: 10
- AnomalyDetector: 8
- BaseAgent: 6
- AgentOrchestrator: 8

**Exports (15)**
- CSV Exporter: 5
- PDF Exporter: 5
- Excel Exporter: 5

### 14.3 Integration Tests (~30 testes)

**Form → Process Creation (8)**
- Form save triggers process creation
- Field mapping works correctly
- Multiple kanbans per form
- Primary form detection

**Auto-Transitions (10)**
- Auto-progression works
- Cascade progression (3 levels)
- Timeout triggers
- Prerequisite checks in transitions

**Agent Suggestions (6)**
- Agent analyzes context
- Suggestions appear in UI
- Accept suggestion works

**Analytics (6)**
- Dashboard loads correctly
- Filters work
- Export generates files

### 14.4 End-to-End Tests (~10 testes)

**Complete Workflows:**
- Order Flow (orcamento → concluido): 1 test
- Support Ticket Flow: 1 test
- Hiring Flow: 1 test
- Visual Editor (create kanban): 2 tests
- Analytics Dashboard: 2 tests
- Forced Transition with justification: 1 test
- Timeout triggers transition: 1 test
- Agent suggestion accepted: 1 test

### 14.5 Coverage Target: 80%+

```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Target coverage by module:
src/workflow/: 85%+
src/persistence/: 90%+
src/analytics/: 75%+
src/exports/: 70%+
```

---

## Próximos Passos

Você completou todos os 5 níveis! 🎉

**Para começar a implementar:**

1. Use `template_generator.py` para criar JSONs de exemplo
2. Use `kanban_validator.py` para validar suas configurações
3. Use `implementation_assistant.py` para guiar implementação fase a fase
4. Consulte os outros níveis conforme necessário

**Referência rápida:**
- [Level 1 - Fundamentals](level_1_fundamentals.md): Conceitos base
- [Level 2 - Engine](level_2_engine.md): AutoTransition, AI Agents
- [Level 3 - Interface](level_3_interface.md): Visual Editor, Dashboard
- [Level 4 - Architecture](level_4_architecture.md): Arquitetura técnica

---

**Referência original**: `VibeCForms/docs/planning/workflow/workflow_kanban_planejamento_v4_parte3.md` (Seções 13-15)
