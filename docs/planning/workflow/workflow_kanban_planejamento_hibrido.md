# PLANEJAMENTO: Sistema de Workflow Kanban Híbrido
## VibeCForms v4.0 - Regras de Negócio com IA e Aprendizado Emergente

**Data:** 21/10/2025
**Versão:** 1.0 - Planejamento Híbrido
**Autor:** Rodrigo (com assistência Claude Code)
**Status:** Proposta para Aprovação

---

## 📑 ÍNDICE

1. [Contexto e Motivação](#contexto-e-motivação)
2. [Síntese das Análises Anteriores](#síntese-das-análises-anteriores)
3. [O Problema da Rigidez](#o-problema-da-rigidez)
4. [Arquitetura Híbrida Proposta](#arquitetura-híbrida-proposta)
5. [Design Técnico Detalhado](#design-técnico-detalhado)
6. [Modos de Operação](#modos-de-operação)
7. [Fases de Implementação](#fases-de-implementação)
8. [Cronograma e Recursos](#cronograma-e-recursos)
9. [Comparação com Propostas Anteriores](#comparação-com-propostas-anteriores)
10. [Riscos e Mitigações](#riscos-e-mitigações)
11. [Exemplos Práticos](#exemplos-práticos)
12. [Recomendação Final](#recomendação-final)

---

## 1. CONTEXTO E MOTIVAÇÃO

### 1.1. Evolução do Projeto VibeCForms

O VibeCForms evoluiu significativamente desde sua concepção:

- **v1.0**: CRUD básico com formulários dinâmicos (TXT files)
- **v2.0**: Templates Jinja2, field types, layout melhorado
- **v2.2.0**: Sistema de Persistência Plugável (Repository Pattern)
- **v3.0**: Multi-backend (TXT, SQLite) com migrations automáticas
- **v4.0 (Proposta)**: Workflow Kanban com IA e Regras de Negócio

### 1.2. Necessidade Identificada

Usuários precisam de **processos de negócio estruturados**, não apenas CRUD:

- **Pedidos**: Orçamento → Aprovação → Pagamento → Entrega → Concluído
- **Suporte**: Novo → Em Análise → Aguardando Cliente → Resolvido
- **RH - Contratação**: Triagem → Entrevista → Proposta → Admissão

### 1.3. Princípio Fundamental Preservado

> **"Workflows são formulários especiais que armazenam processos e transições usando o mesmo Repository Pattern, suportando QUALQUER backend configurado."**

Assim como formulários podem usar TXT, SQLite, JSON, MongoDB, os workflows também podem.

---

## 2. SÍNTESE DAS ANÁLISES ANTERIORES

### 2.1. Análise v1.0 - Abordagem SQL-Cêntrica

**Documentos:** `VibeCForms_Workflow_Kanban_Analise.pdf`

**Proposta:**
- Workflows armazenados em tabelas SQL relacionais
- Foreign Keys entre `workflow_processes` e `workflow_transitions`
- Dependência explícita de SQL (SQLite, MySQL, PostgreSQL)

**Pontos Fortes:**
- ✅ Queries complexas facilitadas
- ✅ Integridade referencial garantida (FK)
- ✅ Performance com índices

**Problema Identificado:**
- ❌ **Conflito Arquitetural**: VibeCForms é backend-agnostic, v1.0 força SQL
- ❌ Perde flexibilidade do Repository Pattern
- ❌ Usuários de TXT/CSV/JSON não poderiam usar workflows

**Estimativa:** 8 semanas (MVP em 6 semanas)

### 2.2. Análise v2.0 - Backend-Agnostic

**Documentos:** `VibeCForms_Workflow_Kanban_Analise_v2.pdf`

**Proposta:**
- Workflows usam Repository Pattern (qualquer backend)
- Relacionamentos **lógicos** ao invés de físicos (sem FKs)
- Processos self-contained (dados denormalizados)
- Suporta TXT, SQLite, JSON, MongoDB, CSV, XML

**Solução do Conflito:**
```python
# Workflows usam MESMO Repository Pattern
workflow_repo = RepositoryFactory.get_repository(
    'workflow_processes_pedidos'
)

# Funciona com QUALQUER backend:
# - TXT: src/workflow_processes_pedidos.txt
# - SQLite: src/vibecforms.db (tabela)
# - JSON: src/workflow_processes_pedidos.json
# - MongoDB: collection workflow_processes_pedidos
```

**Pontos Fortes:**
- ✅ Mantém 100% da flexibilidade de persistência
- ✅ Consistente com arquitetura VibeCForms
- ✅ Permite migração entre backends

**Limitação Identificada:**
- ⚠️ Ainda é baseada em State Machine rígida (mesma da v1.0)
- ⚠️ Não aborda preocupação sobre "engessar o fluxo"

**Estimativa:** 8-9 semanas (MVP em 6-7 semanas, +1 semana vs v1.0)

### 2.3. Conversa ChatGPT - Preocupação sobre Rigidez

**Documentos:** `ChatGPT.md`

**Preocupação do Parceiro:**
> "State Machines acabam meio que travando o fluxo caso ele siga por algum caminho diferente."

**Proposta Alternativa do Parceiro:**
> "Usuário (ou IA) desenha os Kanbans, vamos monitorando as movimentações. Geramos a máquina de estados a partir do que as pessoas estão fazendo, e não o contrário."

**Análise ChatGPT:**

**Vantagens da Abordagem Emergente:**
- ✅ Não engessa usuário desde o início
- ✅ Fluxo real refletido (não teórico)
- ✅ Adapta-se facilmente a mudanças
- ✅ Ideal para processos imaturos/criativos
- ✅ Alinhado com IA e Vibe Coding

**Riscos da Abordagem Emergente:**
- ❌ Caos inicial (sem regras)
- ❌ Difícil gerar regras confiáveis
- ❌ Ambiguidade (quem está certo?)
- ❌ Auditoria frágil no começo
- ❌ Pode gerar máquina de estados incoerente

**Conclusão ChatGPT:**
> **"O ideal é usar abordagem emergente para DESCOBRIR o fluxo — não para substituir completamente a máquina de estados."**

**Solução Híbrida Sugerida:**
1. **Fase 1 - Livre**: Usuários desenham, movem livremente. Sistema registra.
2. **Fase 2 - Análise IA**: Detecta padrões (80% vão de A→B, nunca pulam C)
3. **Fase 3 - Sugestão**: IA propõe State Machine formal
4. **Fase 4 - Modo Controlado**: Segue máquina, mas permite exceções

---

## 3. O PROBLEMA DA RIGIDEZ

### 3.1. Quando State Machine Tradicional Falha

**Cenário Real:**

Um sistema de **Pedidos** define estados rígidos:

```
Orçamento → Em Preparação → Aguardando Pagamento → Entrega → Concluído
              ↓
          Cancelado
```

**Problemas que surgem:**

1. **Cliente paga antecipado**: Precisa pular "Aguardando Pagamento"
2. **Entrega parcial**: Precisa voltar para "Em Preparação" (loop não previsto)
3. **Erro no orçamento**: Precisa voltar de "Em Preparação" → "Orçamento"
4. **Pedido urgente**: Cliente quer pular "Orçamento" e ir direto para "Em Preparação"

**Com State Machine Rígida:**
- ❌ Cada exceção vira um "hack" no código
- ❌ Ou vira um novo estado (explosão de estados)
- ❌ Ou é bloqueada (frustra usuário)

**Resultado:** Sistema engessado, resistência dos usuários.

### 3.2. Por Que Não Abandonar State Machine?

**Sem State Machine:**
- ❌ Zero controle (qualquer transição é válida)
- ❌ Sem auditoria confiável
- ❌ Sem pré-requisitos (aprovações, pagamentos)
- ❌ Difícil automatizar
- ❌ Caos organizacional

**Analogia:**

- **State Machine Rígida** = Autopista sem saídas (rápido, mas sem flexibilidade)
- **Sem State Machine** = Off-road total (liberdade, mas caótico)
- **State Machine Flexível** = Autopista com saídas marcadas (controle + exceções)

---

## 4. ARQUITETURA HÍBRIDA PROPOSTA

### 4.1. Visão Geral

A proposta combina **3 modos de operação** que podem coexistir:

| Modo | Quando Usar | Controle | Flexibilidade | IA |
|------|-------------|----------|---------------|-----|
| **Discovery** | Processo novo/desconhecido | Nenhum | Total | Observa |
| **Guided** | Processo amadurecido | Médio | Alta | Sugere |
| **Controlled** | Processo crítico/auditado | Alto | Média | Automatiza |

### 4.2. Arquitetura Técnica

```
VibeCForms v4.0 - Hybrid Workflow Engine

┌─────────────────────────────────────────────────┐
│          Existing Modules (mantidos)            │
├─────────────────────────────────────────────────┤
│ • Form Generation (JSON specs)                  │
│ • Persistence Layer (multi-backend)             │
│ • Repository Pattern (TXT, SQLite, JSON, Mongo) │
│ • Template System (Jinja2)                      │
└─────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────┐
│         NEW: Hybrid Workflow Engine             │
├─────────────────────────────────────────────────┤
│ src/workflow/                                   │
│  ├── engine/                                    │
│  │   ├── workflow_manager.py   # Gerencia proc │
│  │   ├── state_machine.py      # State Machine │
│  │   ├── rules_engine.py       # Pré-requisitos│
│  │   ├── transition_validator.py # Valida trans│
│  │   └── event_logger.py       # Histórico     │
│  ├── learning/                  # 🆕 NOVO      │
│  │   ├── pattern_detector.py   # Detecta padrões│
│  │   ├── ai_suggester.py       # IA sugere regras│
│  │   └── learning_mode.py      # Modo descoberta│
│  └── modes/                     # 🆕 NOVO      │
│      ├── discovery_mode.py     # Livre total   │
│      ├── guided_mode.py        # Sugestões IA  │
│      └── controlled_mode.py    # State Machine │
└─────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────┐
│         NEW: Workflow Specs (JSON)              │
├─────────────────────────────────────────────────┤
│ src/workflows/                                  │
│  ├── pedidos_workflow.json     # Specs         │
│  └── suporte_workflow.json                     │
│                                                 │
│ src/rules/                                      │
│  └── prerequisite_rules.json   # Regras        │
└─────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────┐
│         NEW: Kanban UI (Frontend)               │
├─────────────────────────────────────────────────┤
│ src/templates/kanban/                           │
│  ├── board.html                # Board Kanban  │
│  ├── card.html                 # Cards         │
│  └── mode_selector.html        # Seletor modo  │
│                                                 │
│ src/static/js/                                  │
│  ├── kanban.js                 # Drag & drop   │
│  └── ai_suggestions.js         # Sugestões IA  │
└─────────────────────────────────────────────────┘
```

### 4.3. Persistência Backend-Agnostic

**Workflows e Transições usam Repository Pattern:**

```json
// src/config/persistence.json
{
  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "sqlite",
    "workflow_processes_pedidos": "sqlite",    // ← Workflow
    "workflow_transitions_pedidos": "json",     // ← Transições
    "*": "default_backend"
  }
}
```

**Exemplos de persistência:**

| Backend | Workflow Processes | Workflow Transitions |
|---------|-------------------|----------------------|
| TXT | `workflow_processes_pedidos.txt` | `workflow_transitions_pedidos.txt` |
| SQLite | Tabela `workflow_processes_pedidos` | Tabela `workflow_transitions_pedidos` |
| JSON | `workflow_processes_pedidos.json` | `workflow_transitions_pedidos.json` |
| MongoDB | Collection `workflow_processes_pedidos` | Collection `workflow_transitions_pedidos` |

**Vantagens:**
- ✅ Empresa pequena usa TXT (simplicidade)
- ✅ Empresa média usa SQLite (queries)
- ✅ Empresa grande usa MongoDB (escala)
- ✅ Migração fácil entre backends

---

## 5. DESIGN TÉCNICO DETALHADO

### 5.1. Modelo de Dados Backend-Agnostic

**Workflow Process (Processo):**

```python
# Independente de backend (funciona em TXT, SQL, JSON, Mongo)
{
    "id": "proc_001",
    "workflow_name": "pedidos",
    "form_name": "pedidos",
    "record_id": "123",              # ID do registro do formulário
    "current_state": "orcamento",
    "mode": "discovery",             # discovery | guided | controlled
    "created_at": "2025-10-21T10:00:00",
    "updated_at": "2025-10-21T15:30:00",
    "created_by": "joao@empresa.com",
    "assigned_to": "maria@empresa.com",

    # Self-contained: snapshot dos dados do formulário
    "form_data_snapshot": {
        "cliente": "Acme Corp",
        "valor": 1500.00,
        "produtos": ["Produto A", "Produto B"]
    },

    # Metadados do processo
    "metadata": {
        "priority": "high",
        "sla_deadline": "2025-10-25",
        "tags": ["urgente", "cliente-vip"]
    }
}
```

**Workflow Transition (Transição):**

```python
# Relacionamento LÓGICO (não FK física)
{
    "id": "trans_001",
    "process_id": "proc_001",        # Referência lógica
    "from_state": "orcamento",
    "to_state": "em_preparacao",
    "transition_type": "manual",     # manual | automatic | ai_suggested
    "transition_by": "maria@empresa.com",
    "transition_at": "2025-10-21T15:30:00",

    # Pré-requisitos atendidos
    "prerequisites_met": {
        "confirmacao_cliente": true,
        "estoque_disponivel": true,
        "forma_pagamento": true
    },

    # Se foi exceção (bypass de State Machine)
    "is_exception": false,
    "exception_reason": null,

    # Notas do usuário
    "notes": "Cliente confirmou pedido por telefone"
}
```

**Workflow Learning Data (Dados de Aprendizado - IA):**

```python
# Coletado em Discovery Mode para treinar IA
{
    "id": "learn_001",
    "workflow_name": "pedidos",
    "from_state": "orcamento",
    "to_state": "em_preparacao",
    "frequency": 47,                 # Quantas vezes aconteceu
    "success_rate": 0.95,            # Taxa de sucesso
    "avg_time_in_state": 7200,       # 2 horas em média
    "common_prerequisites": [
        "confirmacao_cliente",
        "estoque_disponivel"
    ],
    "exceptions_count": 2            # Quantas exceções ocorreram
}
```

### 5.2. Workflow Specification (JSON)

**Arquivo:** `src/workflows/pedidos_workflow.json`

```json
{
  "workflow_name": "pedidos",
  "title": "Fluxo de Pedidos",
  "form_ref": "pedidos",
  "default_mode": "guided",

  "states": [
    {
      "id": "orcamento",
      "name": "Orçamento",
      "order": 1,
      "color": "#FFC107",
      "icon": "fa-calculator",

      "prerequisites": [
        {
          "id": "cliente_valido",
          "type": "field_check",
          "field": "cliente",
          "condition": "not_empty",
          "label": "Cliente informado",
          "required": true,
          "mode_enforcement": "controlled"  // Apenas em modo controlled
        },
        {
          "id": "produtos_selecionados",
          "type": "field_check",
          "field": "produtos",
          "condition": "not_empty",
          "label": "Produtos selecionados",
          "required": true,
          "mode_enforcement": "controlled"
        }
      ],

      "next_states": ["em_preparacao", "cancelado"],
      "allow_bypass": true,          // Permite pular em discovery/guided
      "ai_suggestions": true         // IA pode sugerir transições
    },
    {
      "id": "em_preparacao",
      "name": "Em Preparação",
      "order": 2,
      "color": "#2196F3",
      "icon": "fa-cogs",

      "prerequisites": [
        {
          "id": "estoque_disponivel",
          "type": "system_check",
          "check": "estoque_disponivel",
          "label": "Verificar Estoque",
          "script": "scripts/check_estoque.py",
          "required": true,
          "mode_enforcement": "controlled"
        }
      ],

      "next_states": ["aguardando_pagamento", "orcamento", "cancelado"],
      "allow_bypass": true,
      "ai_suggestions": true
    },
    {
      "id": "aguardando_pagamento",
      "name": "Aguardando Pagamento",
      "order": 3,
      "color": "#FF9800",
      "icon": "fa-credit-card",

      "prerequisites": [
        {
          "id": "forma_pagamento_confirmada",
          "type": "field_check",
          "field": "forma_pagamento",
          "condition": "not_empty",
          "label": "Forma de Pagamento Confirmada",
          "required": true,
          "mode_enforcement": "guided"  // Obrigatório em guided e controlled
        }
      ],

      "next_states": ["entrega", "cancelado"],
      "allow_bypass": false,         // NUNCA pode pular (crítico)
      "ai_suggestions": false
    },
    {
      "id": "entrega",
      "name": "Em Entrega",
      "order": 4,
      "color": "#9C27B0",
      "icon": "fa-truck",

      "next_states": ["concluido", "em_preparacao"],
      "allow_bypass": true,
      "ai_suggestions": true
    },
    {
      "id": "concluido",
      "name": "Concluído",
      "order": 5,
      "color": "#4CAF50",
      "icon": "fa-check-circle",
      "is_final": true
    },
    {
      "id": "cancelado",
      "name": "Cancelado",
      "order": 99,
      "color": "#F44336",
      "icon": "fa-times-circle",
      "is_final": true
    }
  ],

  "learning_config": {
    "enabled": true,
    "min_samples": 10,               // Mín. de amostras para sugerir regra
    "confidence_threshold": 0.8,     // Confiança mín. para sugestão
    "suggest_new_states": true,      // IA pode sugerir novos estados
    "suggest_prerequisites": true    // IA pode sugerir pré-requisitos
  }
}
```

---

## 6. MODOS DE OPERAÇÃO

### 6.1. Discovery Mode (Modo Descoberta)

**Quando Usar:**
- Processo novo, nunca modelado antes
- Equipe explorando melhor fluxo
- Fase de prototipação

**Características:**
- ✅ **Liberdade Total**: Usuário cria colunas, move cards livremente
- ✅ **Zero Bloqueios**: Qualquer transição é permitida
- ✅ **Observação Silenciosa**: Sistema registra TODAS as movimentações
- ✅ **Sem Pré-requisitos**: Não valida campos, não exige aprovações
- ✅ **IA Aprende**: Coleta dados para padrões

**Exemplo Prático:**

1. Usuário cria workflow "Pedidos" em Discovery Mode
2. Cria colunas: "Novo", "Análise", "Aprovado", "Entregue"
3. Move cards livremente entre colunas
4. Às vezes pula "Análise" e vai direto para "Aprovado"
5. Sistema registra: 80% passa por "Análise", 20% pula

**Interface:**

```
┌────────────────────────────────────────────────────┐
│  🔍 Discovery Mode: Pedidos                        │
│  💡 Sistema está aprendendo seus padrões...        │
│  📊 15 movimentações registradas                   │
└────────────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┬────────┐
│  Novo    │ Análise  │ Aprovado │ Entregue │ Concl. │
├──────────┼──────────┼──────────┼──────────┼────────┤
│ ○ Ped123 │ ○ Ped120 │ ○ Ped115 │ ○ Ped110 │○ Ped100│
│ ○ Ped124 │          │ ○ Ped118 │          │        │
│          │          │          │          │        │
└──────────┴──────────┴──────────┴──────────┴────────┘

[➕ Nova Coluna]  [🤖 Sugerir State Machine]
```

**Dados Coletados:**

```python
# workflow_learning_data
{
    "novo → analise": {"count": 12, "success": 100%},
    "novo → aprovado": {"count": 3, "success": 66%},  # 2 voltaram
    "analise → aprovado": {"count": 12, "success": 100%},
    "aprovado → entregue": {"count": 10, "success": 90%}
}
```

### 6.2. Guided Mode (Modo Guiado)

**Quando Usar:**
- Processo amadurecido (já tem padrões)
- Equipe quer orientação mas precisa de flexibilidade
- Fase de transição entre Discovery e Controlled

**Características:**
- ✅ **IA Sugere**: Sistema sugere próximas ações baseado em padrões
- ✅ **Validações Leves**: Checa pré-requisitos marcados como `mode_enforcement: "guided"`
- ✅ **Bypass Permitido**: Usuário pode ignorar sugestões
- ✅ **Feedback Visual**: Mostra transições "comuns" vs "raras"
- ✅ **Aprendizado Contínuo**: Continua coletando dados

**Exemplo Prático:**

1. Sistema detectou que 95% dos pedidos seguem: Novo → Análise → Aprovado
2. Quando usuário abre card em "Novo", sistema sugere: "Mover para Análise?"
3. Mostra pré-requisitos: ✅ Cliente informado, ✅ Produtos selecionados
4. Usuário pode ignorar e mover direto para "Aprovado" (exceção registrada)

**Interface:**

```
┌────────────────────────────────────────────────────┐
│  🎯 Guided Mode: Pedidos                           │
│  💡 IA está sugerindo ações baseadas em 45 casos   │
└────────────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┬────────┐
│  Novo    │ Análise  │ Aprovado │ Entregue │ Concl. │
│          │  ⭐ 95%  │  ⭐ 90%  │  ⭐ 88%  │        │
├──────────┼──────────┼──────────┼──────────┼────────┤
│ ○ Ped123 │ ○ Ped120 │ ○ Ped115 │ ○ Ped110 │○ Ped100│
│   └─ 💡 Próximo: Análise                          │
│      ✅ Todos pré-requisitos OK                    │
│      [Mover] [Ignorar]                            │
└──────────┴──────────┴──────────┴──────────┴────────┘

⭐ = Taxa de sucesso da transição
```

**Sugestão da IA:**

```json
{
  "process_id": "proc_123",
  "current_state": "novo",
  "ai_suggestion": {
    "recommended_next_state": "analise",
    "confidence": 0.95,
    "reason": "95% dos pedidos seguem para Análise",
    "prerequisites_status": {
      "cliente_informado": "✅ OK",
      "produtos_selecionados": "✅ OK"
    },
    "alternative_paths": [
      {
        "state": "aprovado",
        "probability": 0.05,
        "note": "Raro - apenas para clientes VIP"
      }
    ]
  }
}
```

### 6.3. Controlled Mode (Modo Controlado)

**Quando Usar:**
- Processo crítico, auditado, compliance
- Equipe quer garantir que nada pule etapas obrigatórias
- Produção com SLA e responsabilidades

**Características:**
- ✅ **State Machine Rígida**: Apenas transições definidas são permitidas
- ✅ **Pré-requisitos Obrigatórios**: Valida TODOS os pré-requisitos marcados
- ✅ **Exceções Controladas**: Bypass requer aprovação de gestor
- ✅ **Auditoria Completa**: Histórico detalhado de QUEM fez O QUE e QUANDO
- ✅ **IA Automatiza**: IA pode executar transições automáticas quando regras cumpridas

**Exemplo Prático:**

1. Workflow "Pedidos" em Controlled Mode
2. Usuário tenta mover de "Novo" → "Aprovado" (pular "Análise")
3. Sistema bloqueia: "❌ Transição não permitida. Caminho obrigatório: Novo → Análise → Aprovado"
4. Usuário pede exceção: Modal abre solicitando justificativa
5. Gestor aprova exceção via email
6. Sistema registra exceção com justificativa e aprovação

**Interface:**

```
┌────────────────────────────────────────────────────┐
│  🔒 Controlled Mode: Pedidos                       │
│  ⚠️  Transições controladas - Auditoria ativa      │
└────────────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┬────────┐
│  Novo    │ Análise  │ Aprovado │ Entregue │ Concl. │
│  🔒      │  🔒      │  🔒      │  🔒      │  🔒    │
├──────────┼──────────┼──────────┼──────────┼────────┤
│ ○ Ped123 │ ○ Ped120 │ ○ Ped115 │ ○ Ped110 │○ Ped100│
│   Pré-requisitos:                                  │
│   ✅ Cliente: Acme Corp                            │
│   ✅ Produtos: [A, B, C]                           │
│   ✅ Valor: R$ 1.500,00                            │
│   [▶️ Mover para Análise]                          │
└──────────┴──────────┴──────────┴──────────┴────────┘

❌ Tentativa de mover Novo → Aprovado bloqueada
📋 Solicitar exceção? [Sim] [Não]
```

**Bloqueio de Transição:**

```json
{
  "error": "transition_not_allowed",
  "from_state": "novo",
  "to_state": "aprovado",
  "reason": "Estado 'analise' é obrigatório neste fluxo",
  "allowed_next_states": ["analise", "cancelado"],
  "request_exception_url": "/workflow/exception/request/proc_123"
}
```

**Exceção Aprovada:**

```json
{
  "id": "exc_001",
  "process_id": "proc_123",
  "from_state": "novo",
  "to_state": "aprovado",
  "requested_by": "maria@empresa.com",
  "requested_at": "2025-10-21T16:00:00",
  "approved_by": "gestor@empresa.com",
  "approved_at": "2025-10-21T16:15:00",
  "reason": "Cliente VIP solicitou urgência. Análise já feita por telefone.",
  "status": "approved"
}
```

---

## 7. FASES DE IMPLEMENTAÇÃO

### FASE 1: Foundation + Learning Mode (3 semanas)

**Objetivo:** Infraestrutura básica + Modo Discovery

**Entregáveis:**

**Semana 1:**
- ✅ Estrutura de diretórios (`src/workflow/`, `src/workflows/`)
- ✅ Workflow Manager básico (CRUD de processos usando Repository Pattern)
- ✅ Workflow Specs JSON (parser + validator)
- ✅ API endpoints:
  - `POST /workflow/start` - Criar processo
  - `GET /workflow/process/<id>` - Buscar processo
  - `GET /workflow/processes/<workflow_name>` - Listar processos
  - `POST /workflow/transition` - Transitar estado

**Semana 2:**
- ✅ Discovery Mode (modo livre)
- ✅ Learning Mode (coleta de padrões)
- ✅ Pattern Detector (analisa movimentações)
- ✅ Persistência em múltiplos backends:
  - TXT: `workflow_processes_pedidos.txt`
  - SQLite: Tabela `workflow_processes_pedidos`
  - JSON: `workflow_processes_pedidos.json`

**Semana 3:**
- ✅ Event Logger (histórico completo de transições)
- ✅ Testes unitários (repository pattern, workflows)
- ✅ Documentação técnica (API, modelos de dados)

**Testes de Aceitação:**
1. Criar workflow "Pedidos" em Discovery Mode
2. Criar processo de pedido via API
3. Transitar livremente entre estados (Novo → Análise → Aprovado)
4. Sistema registra padrões corretamente
5. Dados persistidos em TXT, SQLite, JSON simultaneamente

**Stack Técnico:**
- Backend: Python, Flask, Repository Pattern existente
- Persistência: BaseRepository (TXT, SQLite, JSON)
- Testes: pytest, pytest-mock

---

### FASE 2: Kanban UI + Drag & Drop (2 semanas)

**Objetivo:** Interface visual de Kanban

**Entregáveis:**

**Semana 4:**
- ✅ Template `kanban/board.html`
- ✅ Renderização de colunas baseada em estados do workflow
- ✅ Cards de processo (exibem dados do formulário)
- ✅ Drag & Drop com SortableJS
- ✅ Modal de detalhes do processo

**Semana 5:**
- ✅ Mode Selector (Discovery / Guided / Controlled)
- ✅ Indicadores visuais:
  - Taxa de sucesso de transições (⭐ 95%)
  - Pré-requisitos (✅/❌)
  - Sugestões da IA (💡)
- ✅ Filtros (por usuário, data, estado)
- ✅ Busca de processos

**Testes de Aceitação:**
1. Abrir Kanban Board de "Pedidos"
2. Ver colunas baseadas em estados do workflow
3. Arrastar card de "Novo" → "Análise" (drag & drop)
4. Ver transição registrada no histórico
5. Alternar entre Discovery/Guided/Controlled Mode
6. Filtrar processos por estado/usuário

**Stack Técnico:**
- Frontend: Vanilla JS ou Vue.js (lightweight)
- Drag & Drop: SortableJS
- CSS: Tailwind CSS ou Bootstrap 5
- Icons: FontAwesome

---

### FASE 3: Rules Engine + State Machine Flexível (2 semanas)

**Objetivo:** Modos Guided e Controlled

**Entregáveis:**

**Semana 6:**
- ✅ State Machine flexível (python-statemachine)
- ✅ Transition Validator
- ✅ Rules Engine:
  - `field_check` (validação de campos)
  - `system_check` (scripts Python externos)
  - `user_action` (confirmações manuais)
- ✅ Prerequisite Validator

**Semana 7:**
- ✅ Guided Mode (sugestões da IA)
- ✅ Controlled Mode (bloqueios + exceções)
- ✅ Sistema de exceções (request → approval)
- ✅ Notificações (email/webhook) em transições

**Testes de Aceitação:**
1. Workflow em Guided Mode:
   - Sistema sugere próxima ação (💡 "Mover para Análise?")
   - Usuário pode ignorar sugestão
2. Workflow em Controlled Mode:
   - Tentar transição inválida (bloqueado ❌)
   - Solicitar exceção (gestor aprova ✅)
   - Transição executada com registro de exceção
3. Pré-requisitos validados corretamente

**Stack Técnico:**
- State Machine: python-statemachine
- Validators: pydantic
- Scheduler: APScheduler (checagens periódicas)

---

### FASE 4: IA Pattern Recognition + Suggestions (3 semanas)

**Objetivo:** IA que aprende e sugere

**Entregáveis:**

**Semana 8:**
- ✅ AI Pattern Detector (analisa `workflow_learning_data`)
- ✅ Algoritmos de análise:
  - Frequência de transições
  - Taxa de sucesso/falha
  - Tempo médio em cada estado
  - Padrões comuns (sequências)
  - Exceções recorrentes

**Semana 9:**
- ✅ AI Suggester:
  - Sugerir próximo estado (probabilidade)
  - Detectar novos estados emergentes
  - Sugerir pré-requisitos comuns
  - Identificar transições desnecessárias
- ✅ Geração automática de State Machine:
  - Baseado em dados de Discovery Mode
  - Usuário aprova/ajusta sugestões

**Semana 10:**
- ✅ Integração com LLM (OpenAI ou Anthropic Claude)
- ✅ Análise inteligente de processos:
  - Detectar anomalias (preços suspeitos, prazos irreais)
  - Sugerir melhorias de fluxo
  - Auto-completion de campos baseado em histórico
- ✅ Interface de sugestões da IA

**Testes de Aceitação:**
1. Discovery Mode com 50+ transições:
   - IA detecta padrão: 90% seguem Novo → Análise → Aprovado
2. IA sugere State Machine:
   - Estados: Novo, Análise, Aprovado, Entregue
   - Pré-requisitos: cliente_informado, produtos_selecionados
3. Usuário aprova State Machine sugerida
4. Workflow migrado para Guided Mode
5. LLM detecta anomalia: "Pedido com valor R$ 0,00 - suspeito"

**Stack Técnico:**
- IA/ML: scikit-learn (padrões), pandas (análise)
- LLM: langchain + openai/anthropic
- APIs: OpenAI GPT-4 ou Anthropic Claude Sonnet

---

### FASE 5: Integration, Polish & Analytics (2 semanas)

**Objetivo:** Integrar tudo + Dashboard + Docs

**Entregáveis:**

**Semana 11:**
- ✅ Integração formulários ↔ workflows:
  - Criar registro → criar processo automaticamente
  - Workflow selector na criação de form spec
  - Link bidirecional (form ↔ process)
- ✅ Dashboard de Workflows:
  - Visão geral de todos processos
  - Métricas por workflow:
    - Total de processos
    - Taxa de conclusão
    - Tempo médio por estado
    - Gargalos (estados com maior tempo)
    - Taxa de exceções
  - Gráficos (Chart.js):
    - Funil de conversão
    - Timeline de estados
    - Heatmap de transições

**Semana 12:**
- ✅ Analytics avançados:
  - SLA tracking (deadlines)
  - Performance por usuário
  - Comparação entre workflows
- ✅ Exportação de dados:
  - CSV, Excel (relatórios)
  - PDF (processos)
- ✅ Documentação completa:
  - `docs/workflow_system.md`
  - Guia do usuário
  - API Reference
  - Exemplos práticos
- ✅ Testes end-to-end (Playwright)

**Testes de Aceitação:**
1. Criar form "Pedidos" com workflow associado
2. Criar registro → processo criado automaticamente
3. Dashboard mostra métricas:
   - 23 processos ativos
   - 15 concluídos
   - Tempo médio: 2.5 dias
   - Gargalo: estado "Análise" (1.2 dias)
4. Exportar relatório em Excel
5. Documentação completa e testada

**Stack Técnico:**
- Charts: Chart.js
- Exports: openpyxl (Excel), reportlab (PDF)
- E2E Tests: Playwright

---

## 8. CRONOGRAMA E RECURSOS

### 8.1. Resumo das Fases

| Fase | Duração | Complexidade | Recursos |
|------|---------|--------------|----------|
| Fase 1: Foundation + Learning | 3 semanas | Alta | 1 dev backend |
| Fase 2: Kanban UI | 2 semanas | Alta | 1 dev fullstack |
| Fase 3: Rules Engine | 2 semanas | Alta | 1 dev backend |
| Fase 4: IA Pattern Recognition | 3 semanas | Muito Alta | 1 dev + 1 AI specialist |
| Fase 5: Integration & Polish | 2 semanas | Média | 1 dev fullstack |
| **TOTAL** | **12 semanas** | - | - |

### 8.2. MVP (Minimal Viable Product)

**MVP = Fases 1-3 = 7 semanas**

O MVP entrega:
- ✅ Workflows com Discovery, Guided, Controlled modes
- ✅ Interface Kanban funcional
- ✅ Rules Engine com pré-requisitos
- ✅ Persistência multi-backend
- ✅ State Machine flexível

**Suficiente para produção** sem IA avançada.

### 8.3. Comparação com Propostas Anteriores

| Aspecto | v1.0 | v2.0 | **v4.0 Híbrida** |
|---------|------|------|------------------|
| **Persistência** | SQL-only | Backend-agnostic | Backend-agnostic ✅ |
| **State Machine** | Rígida | Rígida | Flexível (3 modos) ✅ |
| **IA** | Não | Opcional (Fase 5) | Integrada (aprendizado) ✅ |
| **Aprendizado Emergente** | Não | Não | Sim (Discovery Mode) ✅ |
| **Exceções** | Não previstas | Não previstas | Sistema de exceções ✅ |
| **MVP** | 6 semanas | 6-7 semanas | 7 semanas |
| **Completo** | 8 semanas | 8-9 semanas | 12 semanas |

### 8.4. Recursos Necessários

**Pessoal:**
- 1 desenvolvedor backend sênior (Fases 1, 3)
- 1 desenvolvedor fullstack (Fases 2, 5)
- 1 especialista IA/ML (Fase 4) - opcional, pode ser o backend sênior com LLM API

**Infraestrutura:**
- Servidor de desenvolvimento
- API keys: OpenAI ou Anthropic (Fase 4)
- Ambiente de testes

**Estimativa de Custo:**
- Desenvolvimento: ~12 semanas × 40h × R$ 150/h = R$ 72.000
- APIs LLM (Fase 4): ~R$ 500/mês
- **Total estimado:** R$ 72.500

---

## 9. COMPARAÇÃO COM PROPOSTAS ANTERIORES

### 9.1. Análise v1.0 vs v4.0

| Critério | v1.0 (SQL) | v4.0 (Híbrida) | Vencedor |
|----------|------------|----------------|----------|
| **Persistência** | ❌ SQL-only | ✅ Qualquer backend | v4.0 |
| **Flexibilidade** | ❌ Perde flexibilidade | ✅ Mantém 100% | v4.0 |
| **State Machine** | ⚠️ Rígida | ✅ 3 modos (flexível) | v4.0 |
| **Exceções** | ❌ Não previstas | ✅ Sistema de exceções | v4.0 |
| **IA** | ❌ Não | ✅ Aprendizado + sugestões | v4.0 |
| **MVP** | ✅ 6 semanas | ⚠️ 7 semanas (+1) | v1.0 |
| **Completo** | ✅ 8 semanas | ⚠️ 12 semanas (+4) | v1.0 |
| **Alinhamento VibeCForms** | ❌ Quebra princípios | ✅ Totalmente alinhado | v4.0 |

**Conclusão:** v4.0 é superior em todos os aspectos exceto tempo (4 semanas a mais para versão completa).

### 9.2. Análise v2.0 vs v4.0

| Critério | v2.0 (Backend-Agnostic) | v4.0 (Híbrida) | Vencedor |
|----------|-------------------------|----------------|----------|
| **Persistência** | ✅ Qualquer backend | ✅ Qualquer backend | Empate |
| **State Machine** | ⚠️ Rígida | ✅ 3 modos (flexível) | v4.0 |
| **Aprendizado Emergente** | ❌ Não | ✅ Discovery Mode + IA | v4.0 |
| **Exceções** | ❌ Não previstas | ✅ Sistema de exceções | v4.0 |
| **IA Sugestões** | ⚠️ Opcional (Fase 5) | ✅ Integrada desde MVP | v4.0 |
| **MVP** | ✅ 6-7 semanas | ✅ 7 semanas (similar) | Empate |
| **Completo** | ✅ 8-9 semanas | ⚠️ 12 semanas (+3) | v2.0 |
| **Atende Parceiro** | ❌ Não (engessa) | ✅ Sim (emergente) | v4.0 |

**Conclusão:** v4.0 resolve TODAS as preocupações (persistência + rigidez + emergência) com custo de +3 semanas.

### 9.3. Proposta ChatGPT vs v4.0

| Critério | ChatGPT (Emergente Puro) | v4.0 (Híbrida) | Vencedor |
|----------|--------------------------|----------------|----------|
| **Liberdade Inicial** | ✅ Total | ✅ Total (Discovery) | Empate |
| **Aprendizado** | ✅ IA aprende padrões | ✅ IA aprende padrões | Empate |
| **Controle** | ❌ Caos inicial | ✅ 3 modos (escolha) | v4.0 |
| **Auditoria** | ❌ Frágil no início | ✅ Desde o início | v4.0 |
| **State Machine** | ⚠️ Gerada depois | ✅ Pode definir antes OU depois | v4.0 |
| **Processos Críticos** | ❌ Não indicado | ✅ Controlled Mode | v4.0 |

**Conclusão:** v4.0 implementa a **ideia do parceiro** (emergente) MAS adiciona controle quando necessário.

---

## 10. RISCOS E MITIGAÇÕES

### 10.1. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Performance com muitos processos** | Média | Alto | Indexação adequada, paginação, cache |
| **Complexidade State Machine** | Média | Alto | Usar biblioteca python-statemachine |
| **IA gerando sugestões ruins** | Alta | Médio | Confiança mínima (80%), usuário aprova |
| **Drag & drop não funcionar mobile** | Média | Baixo | Fallback para botões de ação |
| **Backends não-SQL lentos** | Baixa | Médio | Queries em memória, recomendação SQLite |
| **API LLM indisponível** | Baixa | Baixo | Sistema funciona sem IA (degradação) |

### 10.2. Riscos de Projeto

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Prazo de 12 semanas estourado** | Média | Alto | MVP em 7 semanas é suficiente |
| **Equipe sem experiência IA** | Alta | Médio | Fase 4 é opcional, usar LLM API simplifica |
| **Usuários não entendem 3 modos** | Média | Médio | Iniciar todos em Discovery, educar gradualmente |
| **Resistência a mudanças** | Baixa | Alto | Workflows são opt-in, formulários continuam funcionando |

### 10.3. Riscos de Negócio

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Custo de API LLM alto** | Média | Médio | Opcional, controle de budget, usar apenas quando necessário |
| **Projeto não agrega valor** | Baixa | Alto | Validar MVP (7 semanas) antes de continuar Fase 4 |
| **Parceiro rejeita proposta** | Baixa | Alto | Apresentar comparação com v2.0 e ChatGPT |

---

## 11. EXEMPLOS PRÁTICOS

### 11.1. Caso de Uso: Fluxo de Pedidos

**Empresa:** Loja de Materiais de Construção

**Fase 1: Discovery Mode (Semana 1-2)**

1. Equipe cria workflow "Pedidos" em **Discovery Mode**
2. Cria colunas:
   - "Orçamento Solicitado"
   - "Aguardando Cliente"
   - "Separação"
   - "Entrega Agendada"
   - "Concluído"
3. Usa por 2 semanas, move 30 pedidos livremente
4. Sistema registra padrões:
   - 90% seguem: Orçamento → Aguardando → Separação → Entrega → Concluído
   - 5% pulam "Aguardando" (clientes que já confirmaram)
   - 5% voltam de "Separação" → "Orçamento" (produtos faltando)

**Fase 2: Guided Mode (Semana 3-4)**

1. IA sugere State Machine:
   ```
   Estados: Orçamento, Aguardando Cliente, Separação, Entrega, Concluído
   Transições comuns:
   - Orçamento → Aguardando Cliente (90%)
   - Orçamento → Separação (5% - bypass sugerido)
   - Aguardando Cliente → Separação (100%)
   - Separação → Entrega (95%)
   - Separação → Orçamento (5% - loop detectado)
   ```

2. Equipe aprova State Machine

3. Workflow migrado para **Guided Mode**:
   - Sistema sugere próxima ação: "💡 Mover para Aguardando Cliente?"
   - Usuário pode aceitar ou ignorar
   - Se ignorar, sistema registra como exceção

4. Usa por 1 mês, 80 pedidos processados

**Fase 3: Controlled Mode (Produção)**

1. Workflow amadurecido, equipe decide ativar **Controlled Mode**

2. Configuração:
   - Pré-requisitos obrigatórios:
     - Orçamento: ✅ Cliente confirmado, ✅ Produtos disponíveis
     - Separação: ✅ Forma de pagamento confirmada
     - Entrega: ✅ Endereço validado

3. Transições bloqueadas:
   - ❌ Não pode pular "Aguardando Cliente" (salvo exceção aprovada)
   - ❌ Não pode ir para "Entrega" sem confirmar pagamento

4. Exceções:
   - Cliente VIP pode pular "Aguardando Cliente" (gestor aprova)
   - Registrado como exceção com justificativa

5. Automação via IA:
   - IA detecta pagamento confirmado → move automaticamente para "Separação"
   - IA detecta entrega concluída → move para "Concluído"

**Resultado:**
- ✅ 95% dos pedidos seguem fluxo padrão sem intervenção
- ✅ 5% de exceções controladas e auditadas
- ✅ Tempo médio de processamento reduzido em 30%
- ✅ Zero pedidos "esquecidos" em estados intermediários

### 11.2. Caso de Uso: Suporte Técnico

**Empresa:** SaaS B2B

**Discovery Mode:**

1. Equipe de suporte cria workflow "Tickets"
2. Cria colunas livremente:
   - "Novo"
   - "Triagem"
   - "Desenvolvimento"
   - "Aguardando Cliente"
   - "Resolvido"
   - "Bug Confirmado"
3. Move tickets livremente por 1 mês (100 tickets)

**Padrões Detectados pela IA:**

- 60% seguem: Novo → Triagem → Resolvido (tickets simples)
- 25% seguem: Novo → Triagem → Desenvolvimento → Resolvido (bugs)
- 10% ficam em loop: Desenvolvimento ↔ Aguardando Cliente (clarificações)
- 5% vão direto: Novo → Bug Confirmado (problemas críticos)

**IA Sugere Otimização:**

> "🤖 Detectei que 60% dos tickets são resolvidos rapidamente após Triagem.
> Sugestão: Criar estado 'Resolvido Direto' para evitar passar por Desenvolvimento desnecessariamente."

Equipe aceita sugestão.

**Novo Fluxo:**

```
Novo → Triagem → Resolvido Direto (60%)
           ↓
     Desenvolvimento → Resolvido (25%)
           ↓
     Aguardando Cliente → Desenvolvimento (loop 10%)

Novo → Bug Confirmado (5% - bypass para bugs críticos)
```

**Resultado:**
- ✅ Fluxo otimizado baseado em uso real
- ✅ Estados desnecessários removidos
- ✅ Loops identificados e documentados
- ✅ SLA melhorado (tickets simples resolvidos 40% mais rápido)

---

## 12. RECOMENDAÇÃO FINAL

### 12.1. Conclusão

A **Arquitetura Híbrida v4.0** é a solução mais completa e alinhada com:

1. ✅ **Princípios do VibeCForms** (backend-agnostic, Repository Pattern)
2. ✅ **Análise v2.0** (workflows agnósticos de persistência)
3. ✅ **Preocupação do Parceiro** (não engessa, aprende emergentemente)
4. ✅ **Vibe Coding** (IA integrada, JSON specs, flexibilidade)

### 12.2. Diferenciais Competitivos

**vs v1.0:**
- ✅ Resolve conflito arquitetural
- ✅ Mantém flexibilidade total
- ✅ Adiciona modos flexíveis
- ⚠️ +4 semanas (mas vale a pena)

**vs v2.0:**
- ✅ Resolve preocupação sobre rigidez
- ✅ Adiciona aprendizado emergente
- ✅ Sistema de exceções
- ⚠️ +3 semanas (mas agrega IA desde MVP)

**vs Proposta ChatGPT (Emergente Puro):**
- ✅ Mantém liberdade inicial (Discovery)
- ✅ Adiciona controle quando necessário (Guided/Controlled)
- ✅ Auditoria desde o início
- ✅ Processos críticos suportados

### 12.3. Recomendação

**RECOMENDO PROSSEGUIR COM IMPLEMENTAÇÃO v4.0**

**Abordagem Incremental:**

1. **Fase 1 (3 semanas):** Foundation + Discovery Mode
   - Validar arquitetura backend-agnostic
   - Demonstrar aprendizado emergente
   - **Go/No-Go**: Avaliar se learning mode funciona

2. **Fase 2-3 (4 semanas):** Kanban UI + Rules Engine
   - MVP funcional (7 semanas total)
   - **Go/No-Go**: Validar com usuários reais em produção

3. **Fase 4 (3 semanas):** IA Pattern Recognition (OPCIONAL)
   - Apenas se MVP validado com sucesso
   - Apenas se orçamento disponível para APIs LLM

4. **Fase 5 (2 semanas):** Polish final

**Estimativa Conservadora:**
- **MVP garantido:** 7 semanas
- **Versão completa:** 12 semanas (com IA)
- **Custo:** R$ 72.500 (completo) ou R$ 42.000 (apenas MVP)

### 12.4. Próximos Passos

1. ✅ Aprovar arquitetura v4.0 híbrida
2. ✅ Criar branch Git: `feature/workflow-engine-v4-hybrid`
3. ✅ Configurar ambiente de desenvolvimento
4. ✅ Implementar Fase 1 (Foundation + Discovery)
5. ✅ Demonstrar Discovery Mode funcionando (1ª Go/No-Go)
6. ⏸️ Decidir se continua ou ajusta escopo

---

## 📚 REFERÊNCIAS

**Documentos Analisados:**
- `VibeCForms_Workflow_Kanban_Analise.pdf` (v1.0 - SQL-cêntrica)
- `VibeCForms_Workflow_Kanban_Analise_v2.pdf` (v2.0 - Backend-agnostic)
- `ChatGPT.md` (Discussão sobre rigidez e emergência)
- `VibeCForms/docs/plano_persistencia.md` (Arquitetura atual)
- `VibeCForms/CLAUDE.md` (Guia do projeto)

**Tecnologias Recomendadas:**
- Backend: Python, Flask, Repository Pattern
- Persistência: BaseRepository (TXT, SQLite, JSON, MongoDB)
- State Machine: python-statemachine
- Frontend: Vue.js ou Vanilla JS, SortableJS, Tailwind CSS
- IA/ML: scikit-learn, pandas, langchain, OpenAI/Anthropic
- Testes: pytest, Playwright

**Design Patterns:**
- Repository Pattern (existente)
- Adapter Pattern (existente)
- Factory Pattern (existente)
- Strategy Pattern (modos de operação)
- State Pattern (State Machine)
- Observer Pattern (learning mode)

---

**Documento gerado em:** 21/10/2025
**Análise conduzida com assistência de:** Claude Code (Anthropic)
**Projeto:** VibeCForms - Open Source - Vibe Coding
**Versão:** 1.0 - Planejamento Híbrido

**Status:** ✅ APROVADO PARA APRESENTAÇÃO
