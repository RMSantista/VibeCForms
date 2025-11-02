# Sistema de Workflow Kanban - VibeCForms v3.0
## Planejamento Completo da Arquitetura de Vinculação Kanban-Formulário

**Versão:** 3.0
**Data:** Outubro 2025
**Autor:** Rodrigo Santista (com assistência de Claude Code)

---

## Índice

1. [Visão Geral e Conceitos Fundamentais](#1-visão-geral-e-conceitos-fundamentais)
2. [Arquitetura de Vinculação Kanban-Formulário](#2-arquitetura-de-vinculação-kanban-formulário)
3. [Fluxos de Usuário](#3-fluxos-de-usuário)
4. [Estrutura de Persistência](#4-estrutura-de-persistência)
5. [Arquitetura Técnica Existente](#5-arquitetura-técnica-existente)
6. [Novos Componentes de Integração](#6-novos-componentes-de-integração)
7. [Exemplo Completo: Fluxo de Pedidos](#7-exemplo-completo-fluxo-de-pedidos)
8. [Fases de Implementação](#8-fases-de-implementação)
9. [Estratégia de Testes](#9-estratégia-de-testes)
10. [Considerações de Performance](#10-considerações-de-performance)

---

## 1. Visão Geral e Conceitos Fundamentais

### 1.1 Conceito Central: Kanban Define o Workflow

O sistema de workflow do VibeCForms é fundamentado no princípio de que **o Kanban é o elemento central que define as regras de negócio e o workflow**.

```
┌─────────────────────────────────────────────────────────────┐
│                    KANBAN = WORKFLOW                        │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │  Estado 1  │───>│  Estado 2  │───>│  Estado 3  │       │
│  │            │    │            │    │            │       │
│  │ Pré-req A  │    │ Pré-req B  │    │ Pré-req C  │       │
│  └────────────┘    └────────────┘    └────────────┘       │
│                                                             │
│  Formulários vinculados: [Form A, Form B, Form C]          │
└─────────────────────────────────────────────────────────────┘
```

**Princípios fundamentais:**

1. **Kanban como Definidor**: O Kanban define quais estados existem, suas transições e pré-requisitos
2. **Vinculação com Formulários**: Cada Kanban pode estar vinculado a um ou mais formulários
3. **Geração Automática de Processos**: Quando um formulário vinculado é salvo, um processo é automaticamente criado no Kanban correspondente
4. **Acesso via Kanban**: Clicar em um Kanban para criar novo processo abre o formulário vinculado apropriado

### 1.2 Relacionamento Kanban ↔ Formulários

A relação entre Kanban e Formulários é **um-para-muitos (1:N)**:

```
Kanban: "Fluxo de Pedidos"
    |
    +--- Formulário: "pedidos"
    +--- Formulário: "pedidos_urgentes"
    +--- Formulário: "pedidos_especiais"
```

**Diagrama conceitual:**

```
┌───────────────────┐
│  KANBAN BOARD     │
│  "Pedidos"        │
├───────────────────┤
│ linked_forms:     │
│  - pedidos        │
│  - pedidos_urg    │
└───────────────────┘
         |
         | (vincula)
         v
┌───────────────────┐     ┌───────────────────┐
│  FORMULÁRIO       │     │  FORMULÁRIO       │
│  "pedidos"        │     │  "pedidos_urg"    │
├───────────────────┤     ├───────────────────┤
│ - cliente         │     │ - cliente         │
│ - produto         │     │ - produto         │
│ - quantidade      │     │ - prazo           │
└───────────────────┘     └───────────────────┘
         |                         |
         | (save)                  | (save)
         v                         v
    ┌─────────────────────────────────┐
    │  PROCESSO CRIADO AUTOMATICAMENTE│
    │  no Kanban "Pedidos"            │
    │  Estado inicial: "Orçamento"    │
    └─────────────────────────────────┘
```

### 1.3 Geração Automática de Processos

**Fluxo de criação automática:**

```
Usuário preenche formulário
         |
         v
Clica em "Salvar"
         |
         v
Sistema salva dados do formulário
         |
         v
FormTriggerManager detecta que formulário está vinculado a Kanban
         |
         v
ProcessFactory cria novo processo no Kanban
         |
         v
Processo aparece no quadro Kanban no estado inicial
```

---

## 2. Arquitetura de Vinculação Kanban-Formulário

### 2.1 Estrutura de Dados do Kanban

A definição de um Kanban agora inclui a lista de formulários vinculados:

```json
{
  "kanban_id": "pedidos",
  "title": "Fluxo de Pedidos",
  "description": "Gerenciamento completo do ciclo de vida de pedidos",
  "icon": "fa-shopping-cart",

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

  "states": [
    {
      "id": "orcamento",
      "name": "Orçamento",
      "order": 0,
      "color": "#6c757d",
      "prerequisites": []
    },
    {
      "id": "pedido",
      "name": "Pedido Confirmado",
      "order": 1,
      "color": "#007bff",
      "prerequisites": [
        {
          "id": "cliente_aprovacao",
          "type": "field_check",
          "field": "aprovado_cliente",
          "condition": "equals",
          "value": true,
          "blocking": false,
          "message": "Aguardando aprovação do cliente"
        }
      ]
    },
    {
      "id": "entrega",
      "name": "Em Entrega",
      "order": 2,
      "color": "#ffc107",
      "prerequisites": [
        {
          "id": "pagamento_confirmado",
          "type": "field_check",
          "field": "pagamento_recebido",
          "condition": "equals",
          "value": true,
          "blocking": false,
          "message": "Aguardando confirmação de pagamento"
        }
      ]
    },
    {
      "id": "concluido",
      "name": "Concluído",
      "order": 3,
      "color": "#28a745",
      "prerequisites": []
    }
  ],

  "initial_state": "orcamento",

  "transition_rules": {
    "allow_backward": true,
    "require_justification_backward": true,
    "allow_skip_states": false
  }
}
```

### 2.2 Campos da Vinculação

**Estrutura de `linked_forms`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `form_path` | string | Caminho do formulário (ex: "pedidos", "rh/funcionarios") |
| `primary` | boolean | Indica se é o formulário principal (usado por padrão ao clicar "Novo" no Kanban) |
| `auto_create_process` | boolean | Se `true`, salvar este formulário cria automaticamente um processo |

### 2.3 Mapeamento de Campos

O sistema mapeia campos do formulário para o processo criado:

```json
{
  "field_mapping": {
    "process_title_template": "Pedido #{id} - {cliente}",
    "process_description_template": "{quantidade}x {produto}",
    "custom_fields_mapping": {
      "cliente": "process_data.cliente",
      "produto": "process_data.produto",
      "quantidade": "process_data.quantidade",
      "valor_total": "process_data.valor"
    }
  }
}
```

**Exemplo de processo criado:**

```json
{
  "process_id": "proc_001",
  "kanban_id": "pedidos",
  "current_state": "orcamento",
  "title": "Pedido #001 - ACME Corp",
  "description": "10x Widget Premium",
  "created_at": "2025-10-27T10:30:00",
  "created_by": "user123",
  "source_form": "pedidos",
  "source_form_id": 42,

  "process_data": {
    "cliente": "ACME Corp",
    "produto": "Widget Premium",
    "quantidade": 10,
    "valor": 1500.00,
    "aprovado_cliente": false,
    "pagamento_recebido": false
  },

  "history": [
    {
      "timestamp": "2025-10-27T10:30:00",
      "action": "created",
      "from_state": null,
      "to_state": "orcamento",
      "actor": "system",
      "trigger": "form_save"
    }
  ]
}
```

---

## 3. Fluxos de Usuário

### 3.1 Fluxo A: Criação via Kanban

**Usuário inicia pelo quadro Kanban:**

```
1. Usuário acessa "/workflow/kanbans"
         |
         v
2. Visualiza lista de Kanbans disponíveis
         |
         v
3. Clica no card "Fluxo de Pedidos"
         |
         v
4. Sistema abre "/workflow/board/pedidos"
         |
         v
5. Usuário clica no botão "+ Novo Processo"
         |
         v
6. Sistema verifica linked_forms do Kanban
         |
         +---> Se houver apenas 1 formulário: Abre diretamente
         |
         +---> Se houver múltiplos: Mostra seletor
                    |
                    v
               Usuário escolhe formulário
         |
         v
7. Sistema abre "/pedidos" (formulário)
         |
         v
8. Usuário preenche campos:
   - cliente: "ACME Corp"
   - produto: "Widget Premium"
   - quantidade: 10
         |
         v
9. Usuário clica "Salvar"
         |
         v
10. Sistema salva dados em formulário
         |
         v
11. FormTriggerManager detecta vinculação com Kanban
         |
         v
12. ProcessFactory cria processo:
    - kanban_id: "pedidos"
    - current_state: "orcamento"
    - title: "Pedido #001 - ACME Corp"
         |
         v
13. Sistema redireciona para "/workflow/board/pedidos"
         |
         v
14. Processo aparece na coluna "Orçamento"
```

### 3.2 Fluxo B: Criação via Formulário

**Usuário inicia pelo formulário:**

```
1. Usuário acessa "/" (landing page)
         |
         v
2. Clica no card "Pedidos"
         |
         v
3. Sistema abre "/pedidos"
         |
         v
4. Usuário preenche formulário
         |
         v
5. Clica "Salvar"
         |
         v
6. Sistema salva dados do formulário
         |
         v
7. FormTriggerManager verifica se formulário está vinculado a algum Kanban
         |
         +---> Se NÃO: Apenas salva e mostra mensagem "Salvo com sucesso"
         |
         +---> Se SIM e auto_create_process = true:
                    |
                    v
               ProcessFactory cria processo automaticamente
                    |
                    v
               Sistema mostra mensagem:
               "Dados salvos com sucesso!
                Processo criado no quadro 'Fluxo de Pedidos'"
                    |
                    v
               Botão: [Ver no Quadro Kanban]
```

### 3.3 Fluxo de Transição Automática

**AutoTransitionEngine em ação:**

```
1. Processo está em "Pedido Confirmado"
   Pré-requisito: pagamento_recebido = true
         |
         v
2. Usuário edita formulário original (id=42)
         |
         v
3. Atualiza campo: pagamento_recebido = true
         |
         v
4. Sistema salva formulário
         |
         v
5. FormTriggerManager detecta que formulário tem processo vinculado
         |
         v
6. Sistema atualiza process_data do processo
         |
         v
7. AutoTransitionEngine verifica pré-requisitos do próximo estado ("Em Entrega")
         |
         v
8. Pré-requisito "pagamento_confirmado" agora está satisfeito
         |
         v
9. AutoTransitionEngine move processo automaticamente:
   "Pedido Confirmado" ---> "Em Entrega"
         |
         v
10. Sistema registra no histórico:
    - action: "auto_transitioned"
    - trigger: "prerequisite_met"
    - prerequisite_id: "pagamento_confirmado"
```

---

## 4. Estrutura de Persistência

### 4.1 Hierarquia de Dados

```
Sistema VibeCForms
    |
    +--- Formulários (src/specs/)
    |       |
    |       +--- contatos.json
    |       +--- pedidos.json
    |       +--- financeiro/
    |               +--- contas.json
    |
    +--- Dados de Formulários (src/ ou database)
    |       |
    |       +--- contatos.txt / contatos table
    |       +--- pedidos.txt / pedidos table
    |
    +--- Kanbans (src/config/kanbans/)
    |       |
    |       +--- pedidos_kanban.json
    |       +--- projetos_kanban.json
    |       +--- rh_contratacao_kanban.json
    |
    +--- Processos de Workflow (src/data/workflows/ ou database)
            |
            +--- pedidos/
            |       +--- proc_001.json
            |       +--- proc_002.json
            |
            +--- projetos/
                    +--- proc_003.json
```

### 4.2 Arquivo de Registro de Vinculações

**`src/config/kanban_registry.json`:**

Este arquivo mantém o mapeamento bidirecional entre Kanbans e Formulários:

```json
{
  "version": "3.0",
  "last_updated": "2025-10-27T10:00:00",

  "kanban_to_forms": {
    "pedidos": ["pedidos", "pedidos_urgentes"],
    "projetos": ["projetos", "projetos/propostas"],
    "rh_contratacao": ["rh/candidatos"]
  },

  "form_to_kanbans": {
    "pedidos": ["pedidos"],
    "pedidos_urgentes": ["pedidos"],
    "projetos": ["projetos"],
    "projetos/propostas": ["projetos"],
    "rh/candidatos": ["rh_contratacao"]
  },

  "auto_create_config": {
    "pedidos": {
      "kanban": "pedidos",
      "enabled": true,
      "initial_state": "orcamento"
    },
    "pedidos_urgentes": {
      "kanban": "pedidos",
      "enabled": true,
      "initial_state": "pedido"
    }
  }
}
```

### 4.3 Schema de Banco de Dados (SQLite/MySQL/PostgreSQL)

**Tabela: `kanbans`**

```sql
CREATE TABLE kanbans (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tabela: `kanban_forms`** (relacionamento N:N)

```sql
CREATE TABLE kanban_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanban_id TEXT NOT NULL,
    form_path TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    auto_create_process BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kanban_id) REFERENCES kanbans(id),
    UNIQUE(kanban_id, form_path)
);
```

**Tabela: `workflow_processes`**

```sql
CREATE TABLE workflow_processes (
    id TEXT PRIMARY KEY,
    kanban_id TEXT NOT NULL,
    current_state TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source_form TEXT,
    source_form_id INTEGER,
    process_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kanban_id) REFERENCES kanbans(id)
);
```

**Tabela: `workflow_history`**

```sql
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    actor TEXT,
    actor_type TEXT,
    trigger TEXT,
    justification TEXT,
    metadata JSON,
    FOREIGN KEY (process_id) REFERENCES workflow_processes(id)
);
```

---

## 5. Arquitetura Técnica Existente

### 5.1 Componentes do Sistema de Workflow (v2.0)

O sistema atual já possui componentes sólidos que serão mantidos e integrados:

```
┌──────────────────────────────────────────────────────────────┐
│                    Workflow Engine v2.0                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐        ┌────────────────────┐       │
│  │ AutoTransition     │        │ Transition         │       │
│  │ Engine             │───────>│ Handler            │       │
│  │                    │        │                    │       │
│  │ - Detecta pré-req  │        │ - Valida transição │       │
│  │ - Move automático  │        │ - Registra história│       │
│  │ - Executa checks   │        │ - Chama agents     │       │
│  └────────────────────┘        └────────────────────┘       │
│           |                             |                    │
│           v                             v                    │
│  ┌────────────────────┐        ┌────────────────────┐       │
│  │ Prerequisite       │        │ BaseAgent          │       │
│  │ Checker            │        │                    │       │
│  │                    │        │ - Análise de       │       │
│  │ - field_check      │        │   transições       │       │
│  │ - external_api     │        │ - Justificativa    │       │
│  │ - time_elapsed     │        │   obrigatória      │       │
│  │ - custom_script    │        │ - Sugestões        │       │
│  └────────────────────┘        └────────────────────┘       │
│           |                             |                    │
│           v                             v                    │
│  ┌─────────────────────────────────────────────────┐        │
│  │            AuditLogger                          │        │
│  │                                                 │        │
│  │  - Registra todas transições                   │        │
│  │  - Timestamps e atores                         │        │
│  │  - Metadados e justificativas                  │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Filosofia: "Avisar, Não Bloquear"

**Princípio fundamental:**

> O sistema NUNCA bloqueia transições. Pré-requisitos servem apenas para avisar e registrar, mas o usuário sempre tem autonomia para prosseguir.

**Tipos de pré-requisitos:**

1. **field_check**: Verifica valor de campo
2. **external_api**: Consulta API externa
3. **time_elapsed**: Verifica tempo decorrido
4. **custom_script**: Executa script Python customizado

**Comportamento:**

```
Usuário move processo de "A" para "B"
         |
         v
PrerequisiteChecker avalia pré-requisitos de "B"
         |
         +---> Todos satisfeitos:
         |         - Transição ocorre silenciosamente
         |         - Registra no histórico
         |
         +---> Algum não satisfeito:
                   - Mostra modal de aviso
                   - Lista pré-requisitos pendentes
                   - Usuário pode:
                       [Cancelar] ou [Continuar Mesmo Assim]
                   - Se continuar:
                       * Solicita justificativa (opcional para usuários)
                       * Registra no histórico com flag "forced"
```

### 5.3 Tipos de Transição

| Tipo | Descrição | Ator | Justificativa |
|------|-----------|------|---------------|
| **System** | Transição automática por pré-requisitos | AutoTransitionEngine | Não requerida |
| **Manual** | Usuário arrasta card no Kanban | Usuário humano | Opcional (obrigatória se houver avisos) |
| **Agent** | IA Agent realiza análise e move | BaseAgent (IA) | Sempre obrigatória |

### 5.4 AutoTransitionEngine

**Funcionamento:**

1. **Trigger**: Executado quando dados do processo são atualizados
2. **Avaliação**: Verifica pré-requisitos do próximo estado (em ordem)
3. **Decisão**: Se todos pré-requisitos satisfeitos, move automaticamente
4. **Registro**: Grava histórico com `trigger: "prerequisite_met"`

**Exemplo de código (conceitual):**

```python
class AutoTransitionEngine:
    def check_and_transition(self, process_id):
        process = self.repo.get_process(process_id)
        kanban = self.repo.get_kanban(process.kanban_id)
        current_state = process.current_state

        # Encontra próximo estado na ordem
        next_state = self._get_next_state(kanban, current_state)

        if next_state:
            # Verifica pré-requisitos
            checker = PrerequisiteChecker()
            results = checker.check_all(process, next_state.prerequisites)

            if results.all_satisfied:
                # Move automaticamente
                self.transition_handler.transition(
                    process_id=process_id,
                    to_state=next_state.id,
                    actor="system",
                    actor_type="auto_transition",
                    trigger="prerequisite_met",
                    metadata={"prerequisites_checked": results.details}
                )

                # Recursão: verifica se pode avançar mais
                self.check_and_transition(process_id)
```

---

## 6. Novos Componentes de Integração

### 6.1 KanbanRegistry

**Responsabilidade:** Manter mapeamento bidirecional entre Kanbans e Formulários

```python
class KanbanRegistry:
    """
    Gerencia o registro de vinculações entre Kanbans e Formulários.

    Carrega configurações de:
    - Definições de Kanban (linked_forms)
    - Arquivo de registro (kanban_registry.json)
    """

    def __init__(self):
        self.registry_file = "src/config/kanban_registry.json"
        self._kanban_to_forms = {}
        self._form_to_kanbans = {}
        self._load_registry()

    def get_kanbans_for_form(self, form_path: str) -> list:
        """
        Retorna lista de Kanbans vinculados a um formulário.

        Args:
            form_path: Caminho do formulário (ex: "pedidos")

        Returns:
            Lista de kanban_ids
        """
        return self._form_to_kanbans.get(form_path, [])

    def get_forms_for_kanban(self, kanban_id: str) -> list:
        """
        Retorna lista de formulários vinculados a um Kanban.

        Args:
            kanban_id: ID do Kanban

        Returns:
            Lista de dicionários com form_path e configurações
        """
        return self._kanban_to_forms.get(kanban_id, [])

    def get_primary_form(self, kanban_id: str) -> str:
        """
        Retorna o formulário principal de um Kanban.
        Usado quando usuário clica "Novo" no quadro Kanban.
        """
        forms = self.get_forms_for_kanban(kanban_id)
        primary = [f for f in forms if f.get('primary', False)]
        return primary[0]['form_path'] if primary else forms[0]['form_path']

    def should_auto_create_process(self, form_path: str, kanban_id: str) -> bool:
        """
        Verifica se salvar o formulário deve criar processo automaticamente.
        """
        forms = self.get_forms_for_kanban(kanban_id)
        for form_config in forms:
            if form_config['form_path'] == form_path:
                return form_config.get('auto_create_process', True)
        return False
```

### 6.2 FormTriggerManager

**Responsabilidade:** Detectar salvamento de formulários e disparar criação de processos

```python
class FormTriggerManager:
    """
    Gerencia triggers de formulários para criação automática de processos.

    Integra-se aos endpoints de salvamento de formulários para detectar
    quando um formulário vinculado a Kanban é salvo.
    """

    def __init__(self, registry: KanbanRegistry, process_factory: ProcessFactory):
        self.registry = registry
        self.process_factory = process_factory

    def on_form_saved(self, form_path: str, form_id: int, form_data: dict,
                      user_id: str) -> list:
        """
        Callback chamado quando um formulário é salvo.

        Args:
            form_path: Caminho do formulário
            form_id: ID do registro salvo
            form_data: Dados do formulário
            user_id: ID do usuário que salvou

        Returns:
            Lista de process_ids criados
        """
        created_processes = []

        # Busca Kanbans vinculados
        kanbans = self.registry.get_kanbans_for_form(form_path)

        for kanban_id in kanbans:
            # Verifica se deve criar automaticamente
            if self.registry.should_auto_create_process(form_path, kanban_id):
                # Cria processo
                process_id = self.process_factory.create_from_form(
                    kanban_id=kanban_id,
                    form_path=form_path,
                    form_id=form_id,
                    form_data=form_data,
                    created_by=user_id
                )
                created_processes.append(process_id)

                # Registra log
                logger.info(f"Processo {process_id} criado automaticamente "
                           f"no Kanban '{kanban_id}' a partir do formulário "
                           f"'{form_path}' (id={form_id})")

        return created_processes

    def on_form_updated(self, form_path: str, form_id: int, form_data: dict,
                        user_id: str):
        """
        Callback chamado quando um formulário é atualizado.

        Atualiza process_data de processos vinculados e dispara
        AutoTransitionEngine para verificar transições automáticas.
        """
        # Busca processos criados a partir deste formulário
        processes = self.process_factory.find_processes_by_source(
            form_path=form_path,
            form_id=form_id
        )

        for process in processes:
            # Atualiza dados do processo
            self.process_factory.update_process_data(
                process_id=process.id,
                new_data=form_data
            )

            # Dispara verificação de transição automática
            auto_engine = AutoTransitionEngine()
            auto_engine.check_and_transition(process.id)
```

### 6.3 ProcessFactory

**Responsabilidade:** Criar instâncias de processos a partir de dados de formulários

```python
class ProcessFactory:
    """
    Factory para criação de processos de workflow a partir de formulários.

    Mapeia campos do formulário para estrutura de processo.
    """

    def __init__(self, workflow_repo: WorkflowRepository):
        self.repo = workflow_repo

    def create_from_form(self, kanban_id: str, form_path: str,
                         form_id: int, form_data: dict,
                         created_by: str) -> str:
        """
        Cria um novo processo a partir de dados de formulário.

        Args:
            kanban_id: ID do Kanban onde criar o processo
            form_path: Caminho do formulário origem
            form_id: ID do registro no formulário
            form_data: Dados do formulário
            created_by: ID do usuário

        Returns:
            process_id do processo criado
        """
        # Carrega configuração do Kanban
        kanban = self.repo.get_kanban(kanban_id)

        # Obtém estado inicial
        initial_state = kanban.get('initial_state', kanban['states'][0]['id'])

        # Aplica template de título e descrição
        title = self._apply_template(
            kanban.get('field_mapping', {}).get('process_title_template',
                                                 '{form_path} #{form_id}'),
            form_data,
            {'form_path': form_path, 'id': form_id}
        )

        description = self._apply_template(
            kanban.get('field_mapping', {}).get('process_description_template', ''),
            form_data,
            {}
        )

        # Gera process_id único
        process_id = f"proc_{kanban_id}_{int(time.time())}_{form_id}"

        # Monta estrutura do processo
        process = {
            "process_id": process_id,
            "kanban_id": kanban_id,
            "current_state": initial_state,
            "title": title,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "source_form": form_path,
            "source_form_id": form_id,
            "process_data": form_data,
            "history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "created",
                    "from_state": None,
                    "to_state": initial_state,
                    "actor": "system",
                    "trigger": "form_save"
                }
            ]
        }

        # Salva no repositório
        self.repo.create_process(process)

        return process_id

    def _apply_template(self, template: str, data: dict,
                       extra_vars: dict) -> str:
        """
        Aplica template string substituindo variáveis.

        Exemplo: "Pedido #{id} - {cliente}" -> "Pedido #42 - ACME Corp"
        """
        merged_data = {**data, **extra_vars}
        try:
            return template.format(**merged_data)
        except KeyError:
            return template

    def find_processes_by_source(self, form_path: str,
                                 form_id: int) -> list:
        """
        Encontra processos criados a partir de um formulário específico.
        """
        return self.repo.find_processes(
            filters={
                "source_form": form_path,
                "source_form_id": form_id
            }
        )

    def update_process_data(self, process_id: str, new_data: dict):
        """
        Atualiza process_data de um processo.
        Usado quando formulário origem é editado.
        """
        process = self.repo.get_process(process_id)
        process['process_data'] = new_data
        process['updated_at'] = datetime.now().isoformat()
        self.repo.update_process(process)
```

### 6.4 Diagrama de Integração Completa

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VibeCForms v3.0                              │
│                  Workflow + Formulários Integrados                  │
└─────────────────────────────────────────────────────────────────────┘
                                  |
                                  |
        ┌─────────────────────────┴─────────────────────────┐
        |                                                   |
        v                                                   v
┌──────────────────┐                              ┌──────────────────┐
│   Form Routes    │                              │  Workflow Routes │
│                  │                              │                  │
│  POST /pedidos   │                              │  GET /workflow/  │
│  POST /contatos  │                              │      board/:id   │
└────────┬─────────┘                              └────────┬─────────┘
         |                                                 |
         | (save)                                          | (view/move)
         v                                                 v
┌──────────────────┐                              ┌──────────────────┐
│ FormTrigger      │<────────────────────────────>│ TransitionHandler│
│ Manager          │    (update process_data)     │                  │
└────────┬─────────┘                              └────────┬─────────┘
         |                                                 |
         | (check kanbans)                                 | (validate)
         v                                                 v
┌──────────────────┐                              ┌──────────────────┐
│ KanbanRegistry   │                              │ PrerequisiteChecker│
│                  │                              │                  │
│ - Form→Kanbans   │                              │ - field_check    │
│ - Kanban→Forms   │                              │ - external_api   │
└────────┬─────────┘                              └────────┬─────────┘
         |                                                 |
         | (create process)                                | (all met?)
         v                                                 v
┌──────────────────┐                              ┌──────────────────┐
│ ProcessFactory   │                              │ AutoTransition   │
│                  │                              │ Engine           │
│ - Map fields     │                              │                  │
│ - Generate title │                              │ - Auto move      │
│ - Set initial st │                              │ - Recursive check│
└────────┬─────────┘                              └────────┬─────────┘
         |                                                 |
         |                                                 |
         └─────────────────┬───────────────────────────────┘
                           v
                  ┌─────────────────┐
                  │ WorkflowRepo    │
                  │                 │
                  │ - Save process  │
                  │ - Update state  │
                  │ - Log history   │
                  └────────┬────────┘
                           |
                           v
                  ┌─────────────────┐
                  │  Persistence    │
                  │  (TXT/SQLite/   │
                  │   JSON/MySQL)   │
                  └─────────────────┘
```

---

## 7. Exemplo Completo: Fluxo de Pedidos

### 7.1 Definição do Kanban

**Arquivo:** `src/config/kanbans/pedidos_kanban.json`

```json
{
  "kanban_id": "pedidos",
  "title": "Fluxo de Pedidos",
  "description": "Gerenciamento do ciclo completo de pedidos de clientes",
  "icon": "fa-shopping-cart",

  "linked_forms": [
    {
      "form_path": "pedidos",
      "primary": true,
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
      "description": "Pedido em fase de orçamento",
      "prerequisites": []
    },
    {
      "id": "pedido",
      "name": "Pedido Confirmado",
      "order": 1,
      "color": "#007bff",
      "icon": "fa-check-circle",
      "description": "Cliente aprovou o orçamento",
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
      ]
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
        }
      ]
    },
    {
      "id": "concluido",
      "name": "Concluído",
      "order": 3,
      "color": "#28a745",
      "icon": "fa-flag-checkered",
      "description": "Pedido entregue e finalizado",
      "prerequisites": []
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
  }
}
```

### 7.2 Definição do Formulário

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
      "name": "produto",
      "label": "Produto",
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
      "label": "Cliente Aprovou?",
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
    "produto": "Nome do produto é obrigatório",
    "quantidade": "Quantidade é obrigatória",
    "valor_unitario": "Valor unitário é obrigatório",
    "valor_total": "Valor total é obrigatório"
  }
}
```

### 7.3 Cenário Completo de Uso

**Dia 1 - 10:00 - Criação do Pedido:**

1. Usuário acessa `/workflow/board/pedidos`
2. Clica "+ Novo Processo"
3. Sistema redireciona para `/pedidos` (formulário primary)
4. Usuário preenche:
   - cliente: "ACME Corporation"
   - produto: "Widget Premium"
   - quantidade: 100
   - valor_unitario: 15.00
   - valor_total: 1500.00
   - aprovado_cliente: ☐ (desmarcado)
   - pagamento_recebido: ☐ (desmarcado)
5. Clica "Salvar"

**Sistema:**
- FormTriggerManager detecta salvamento
- ProcessFactory cria processo:
  ```json
  {
    "process_id": "proc_pedidos_1730032800_42",
    "kanban_id": "pedidos",
    "current_state": "orcamento",
    "title": "Pedido #42 - ACME Corporation",
    "description": "100x Widget Premium - R$ 1500.00",
    "source_form": "pedidos",
    "source_form_id": 42
  }
  ```
- Redireciona para `/workflow/board/pedidos`
- Card aparece na coluna "Orçamento"

---

**Dia 2 - 14:30 - Cliente Aprova:**

1. Usuário acessa `/pedidos/edit/42`
2. Marca: aprovado_cliente: ☑
3. Clica "Salvar"

**Sistema:**
- FormTriggerManager detecta atualização
- Atualiza `process_data.aprovado_cliente = true`
- AutoTransitionEngine verifica pré-requisitos de "Pedido Confirmado"
- Pré-requisito "cliente_aprovacao" satisfeito!
- **Move automaticamente**: "Orçamento" → "Pedido Confirmado"
- Registra histórico:
  ```json
  {
    "timestamp": "2025-10-28T14:30:00",
    "action": "auto_transitioned",
    "from_state": "orcamento",
    "to_state": "pedido",
    "actor": "system",
    "actor_type": "auto_transition",
    "trigger": "prerequisite_met",
    "metadata": {
      "prerequisite_id": "cliente_aprovacao",
      "prerequisite_name": "Aprovação do Cliente"
    }
  }
  ```

---

**Dia 3 - 09:00 - Pagamento Recebido:**

1. Usuário acessa `/pedidos/edit/42`
2. Marca: pagamento_recebido: ☑
3. Clica "Salvar"

**Sistema:**
- Atualiza `process_data.pagamento_recebido = true`
- AutoTransitionEngine verifica "Em Entrega"
- Pré-requisito "pagamento_confirmado" satisfeito!
- **Move automaticamente**: "Pedido Confirmado" → "Em Entrega"

---

**Dia 5 - 16:00 - Entrega Realizada:**

1. Usuário acessa `/workflow/board/pedidos`
2. Arrasta card "Pedido #42" de "Em Entrega" para "Concluído"
3. Não há pré-requisitos para "Concluído"
4. Transição ocorre imediatamente
5. Registra histórico:
   ```json
   {
     "timestamp": "2025-10-30T16:00:00",
     "action": "manual_transition",
     "from_state": "entrega",
     "to_state": "concluido",
     "actor": "user123",
     "actor_type": "user",
     "trigger": "drag_and_drop"
   }
   ```

### 7.4 Visualização no Quadro Kanban

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Fluxo de Pedidos                                   │
│  [+ Novo Processo]                                        [☰ Filtros]    │
├──────────────────┬──────────────────┬──────────────────┬────────────────┤
│   Orçamento      │ Pedido Confirmado│   Em Entrega     │   Concluído    │
│   (2 processos)  │   (3 processos)  │   (1 processo)   │ (15 processos) │
├──────────────────┼──────────────────┼──────────────────┼────────────────┤
│                  │                  │                  │                │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌────────────┐ │
│ │ Pedido #43   │ │ │ Pedido #40   │ │ │ Pedido #42   │ │ │ Pedido #35 │ │
│ │ XYZ Ltda     │ │ │ Beta Inc     │ │ │ ACME Corp    │ │ │ ...        │ │
│ │              │ │ │              │ │ │              │ │ └────────────┘ │
│ │ 50x Gadget   │ │ │ 200x Tool    │ │ │ 100x Widget  │ │                │
│ │ R$ 750.00    │ │ │ R$ 3000.00   │ │ │ R$ 1500.00   │ │ [Ver mais...] │
│ │              │ │ │              │ │ │              │ │                │
│ │ ⚠️ Aguardando │ │ │ ⚠️ Aguardando │ │ │ ✅ Pronto    │ │                │
│ │   aprovação  │ │ │   pagamento  │ │ │   para       │ │                │
│ │   cliente    │ │ │              │ │ │   concluir   │ │                │
│ └──────────────┘ │ └──────────────┘ │ └──────────────┘ │                │
│                  │                  │                  │                │
│ ┌──────────────┐ │ ┌──────────────┐ │                  │                │
│ │ Pedido #44   │ │ │ Pedido #41   │ │                  │                │
│ │ ...          │ │ │ ...          │ │                  │                │
│ └──────────────┘ │ └──────────────┘ │                  │                │
│                  │                  │                  │                │
└──────────────────┴──────────────────┴──────────────────┴────────────────┘
```

**Legenda dos ícones nos cards:**
- ⚠️ Pré-requisitos pendentes
- ✅ Todos pré-requisitos satisfeitos
- 🤖 Transição automática disponível

---

## 8. Fases de Implementação

### 8.1 Visão Geral das Fases

```
Fase 1: Fundação         [3 dias]
    |
    +---> KanbanRegistry
    +---> Estruturas de dados
    +---> Testes unitários

Fase 2: Trigger System   [4 dias]
    |
    +---> FormTriggerManager
    +---> ProcessFactory
    +---> Integração com rotas de formulários
    +---> Testes de integração

Fase 3: Auto-Transição   [3 dias]
    |
    +---> Integração FormTrigger → AutoTransitionEngine
    +---> Update process_data em edições
    +---> Testes end-to-end

Fase 4: UI e Refinamentos [4 dias]
    |
    +---> Botão "Novo Processo" no Kanban
    +---> Seletor de formulários
    +---> Mensagens de feedback
    +---> Breadcrumbs Kanban ↔ Form
    +---> Polish e UX

Fase 5: Documentação     [2 dias]
    |
    +---> Atualização de docs
    +---> Guia de uso
    +---> Exemplos práticos
```

### 8.2 Fase 1: Fundação (3 dias)

**Objetivo:** Criar estruturas de dados e KanbanRegistry

**Tarefas:**

1. **Definir schema de vinculação** (0.5 dia)
   - [ ] Adicionar campo `linked_forms` ao schema de Kanban
   - [ ] Criar estrutura de `kanban_registry.json`
   - [ ] Definir tabelas de banco de dados (`kanban_forms`)

2. **Implementar KanbanRegistry** (1 dia)
   - [ ] Criar classe `KanbanRegistry` em `src/persistence/kanban_registry.py`
   - [ ] Método `get_kanbans_for_form()`
   - [ ] Método `get_forms_for_kanban()`
   - [ ] Método `get_primary_form()`
   - [ ] Método `should_auto_create_process()`
   - [ ] Carregamento de definições de Kanban e registry.json

3. **Testes unitários** (1 dia)
   - [ ] `tests/test_kanban_registry.py`
   - [ ] Testar mapeamento Form → Kanbans
   - [ ] Testar mapeamento Kanban → Forms
   - [ ] Testar identificação de formulário principal
   - [ ] Testar configuração de auto_create_process

4. **Migração de dados existentes** (0.5 dia)
   - [ ] Script para adicionar `linked_forms` vazio aos Kanbans existentes
   - [ ] Documentar como configurar vinculações

**Entregável:** KanbanRegistry funcional com testes

---

### 8.3 Fase 2: Trigger System (4 dias)

**Objetivo:** Implementar criação automática de processos ao salvar formulários

**Tarefas:**

1. **Implementar ProcessFactory** (1.5 dias)
   - [ ] Criar classe `ProcessFactory` em `src/workflow/engine/process_factory.py`
   - [ ] Método `create_from_form()`
   - [ ] Método `_apply_template()` para títulos/descrições
   - [ ] Método `find_processes_by_source()`
   - [ ] Método `update_process_data()`
   - [ ] Geração de `process_id` único

2. **Implementar FormTriggerManager** (1.5 dias)
   - [ ] Criar classe `FormTriggerManager` em `src/workflow/engine/form_trigger_manager.py`
   - [ ] Método `on_form_saved()`
   - [ ] Método `on_form_updated()`
   - [ ] Método `on_form_deleted()` (opcional)
   - [ ] Integração com KanbanRegistry

3. **Integrar com rotas de formulários** (0.5 dia)
   - [ ] Modificar `POST /<form_path>` em `src/VibeCForms.py`
   - [ ] Adicionar callback `FormTriggerManager.on_form_saved()`
   - [ ] Modificar `POST /<form_path>/edit/<id>`
   - [ ] Adicionar callback `FormTriggerManager.on_form_updated()`

4. **Testes de integração** (0.5 dia)
   - [ ] `tests/test_process_factory.py`
   - [ ] `tests/test_form_trigger_manager.py`
   - [ ] Testar criação de processo ao salvar formulário
   - [ ] Testar mapping de campos
   - [ ] Testar templates de título/descrição

**Entregável:** Processos criados automaticamente ao salvar formulários

---

### 8.4 Fase 3: Auto-Transição (3 dias)

**Objetivo:** Conectar atualizações de formulários com AutoTransitionEngine

**Tarefas:**

1. **Conectar FormTrigger → AutoTransition** (1 dia)
   - [ ] Em `on_form_updated()`, chamar `AutoTransitionEngine.check_and_transition()`
   - [ ] Garantir que `process_data` é atualizado antes de checar transições
   - [ ] Testar fluxo completo

2. **Refinar PrerequisiteChecker** (1 dia)
   - [ ] Garantir que `field_check` busca em `process_data`
   - [ ] Adicionar suporte a condições complexas (`greater_than`, `not_empty`, etc.)
   - [ ] Testes para todos tipos de pré-requisitos

3. **Testes end-to-end** (1 dia)
   - [ ] `tests/test_workflow_integration.py`
   - [ ] Cenário: Salvar form → Criar processo → Editar form → Auto-transição
   - [ ] Testar com múltiplos pré-requisitos
   - [ ] Testar transições em cascata (múltiplos estados)

**Entregável:** Transições automáticas funcionando com atualizações de formulários

---

### 8.5 Fase 4: UI e Refinamentos (4 dias)

**Objetivo:** Criar interface de usuário para vinculação Kanban-Form

**Tarefas:**

1. **Botão "Novo Processo" no Kanban** (1 dia)
   - [ ] Adicionar botão no template `board.html`
   - [ ] Criar rota `GET /workflow/board/<kanban_id>/new`
   - [ ] Se houver 1 formulário: redirecionar direto
   - [ ] Se houver múltiplos: mostrar seletor

2. **Seletor de formulários** (1 dia)
   - [ ] Template `select_form.html`
   - [ ] Listar formulários vinculados
   - [ ] Mostrar ícones e descrições
   - [ ] Redirecionar para `/<form_path>?kanban_redirect=<kanban_id>`

3. **Mensagens de feedback** (1 dia)
   - [ ] Após salvar formulário, mostrar: "Processo criado no Kanban X"
   - [ ] Botão [Ver no Quadro Kanban] → redireciona para `/workflow/board/<kanban_id>`
   - [ ] Toast notification quando AutoTransition ocorre

4. **Breadcrumbs e navegação** (0.5 dia)
   - [ ] No formulário, mostrar badge "Vinculado ao Kanban: Pedidos"
   - [ ] No card do processo, botão "Editar Formulário Original"
   - [ ] Navegação fluida entre Kanban e Form

5. **Polish e UX** (0.5 dia)
   - [ ] Animações de transição automática
   - [ ] Loading states
   - [ ] Tratamento de erros

**Entregável:** UI completa para criação e navegação Kanban ↔ Form

---

### 8.6 Fase 5: Documentação (2 dias)

**Tarefas:**

1. **Atualizar CLAUDE.md** (0.5 dia)
   - [ ] Seção sobre Kanban-Form binding
   - [ ] Exemplos de configuração
   - [ ] Diagramas

2. **Criar guia de uso** (1 dia)
   - [ ] `docs/guides/kanban_form_integration.md`
   - [ ] Como vincular formulários a Kanbans
   - [ ] Como configurar field_mapping
   - [ ] Exemplos práticos

3. **Atualizar prompts** (0.5 dia)
   - [ ] `docs/prompts.md` com prompts usados nesta fase
   - [ ] Changelog atualizado

**Entregável:** Documentação completa

---

## 9. Estratégia de Testes

### 9.1 Testes Unitários

**Arquivo:** `tests/test_kanban_registry.py`

```python
import pytest
from src.persistence.kanban_registry import KanbanRegistry

def test_get_kanbans_for_form():
    registry = KanbanRegistry()
    kanbans = registry.get_kanbans_for_form("pedidos")
    assert "pedidos" in kanbans

def test_get_forms_for_kanban():
    registry = KanbanRegistry()
    forms = registry.get_forms_for_kanban("pedidos")
    assert len(forms) > 0
    assert any(f['form_path'] == "pedidos" for f in forms)

def test_get_primary_form():
    registry = KanbanRegistry()
    primary = registry.get_primary_form("pedidos")
    assert primary == "pedidos"

def test_should_auto_create_process():
    registry = KanbanRegistry()
    should_create = registry.should_auto_create_process("pedidos", "pedidos")
    assert should_create is True
```

**Arquivo:** `tests/test_process_factory.py`

```python
import pytest
from src.workflow.engine.process_factory import ProcessFactory
from src.persistence.workflow_repository import WorkflowRepository

def test_create_from_form():
    repo = WorkflowRepository()
    factory = ProcessFactory(repo)

    form_data = {
        "cliente": "ACME Corp",
        "produto": "Widget",
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

    process = repo.get_process(process_id)
    assert process['kanban_id'] == "pedidos"
    assert process['current_state'] == "orcamento"
    assert process['source_form'] == "pedidos"
    assert process['source_form_id'] == 42
    assert process['process_data']['cliente'] == "ACME Corp"

def test_apply_template():
    factory = ProcessFactory(WorkflowRepository())

    template = "Pedido #{id} - {cliente}"
    data = {"cliente": "ACME Corp", "produto": "Widget"}
    extra = {"id": 42}

    result = factory._apply_template(template, data, extra)
    assert result == "Pedido #42 - ACME Corp"
```

### 9.2 Testes de Integração

**Arquivo:** `tests/test_form_trigger_integration.py`

```python
import pytest
from src.app import app
from src.workflow.engine.form_trigger_manager import FormTriggerManager
from src.persistence.workflow_repository import WorkflowRepository

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_form_save_creates_process(client):
    # Salva formulário
    response = client.post('/pedidos', data={
        'cliente': 'ACME Corp',
        'produto': 'Widget Premium',
        'quantidade': '10',
        'valor_total': '1500.00'
    })

    assert response.status_code == 302  # Redirect

    # Verifica que processo foi criado
    repo = WorkflowRepository()
    processes = repo.find_processes(filters={"kanban_id": "pedidos"})

    assert len(processes) > 0
    latest = processes[-1]
    assert latest['source_form'] == "pedidos"
    assert latest['process_data']['cliente'] == "ACME Corp"

def test_form_update_triggers_auto_transition(client):
    # Cria processo inicial
    repo = WorkflowRepository()
    factory = ProcessFactory(repo)

    process_id = factory.create_from_form(
        kanban_id="pedidos",
        form_path="pedidos",
        form_id=42,
        form_data={
            "cliente": "ACME",
            "aprovado_cliente": False
        },
        created_by="user123"
    )

    # Verifica estado inicial
    process = repo.get_process(process_id)
    assert process['current_state'] == "orcamento"

    # Atualiza formulário marcando aprovação
    response = client.post('/pedidos/edit/42', data={
        'cliente': 'ACME',
        'aprovado_cliente': 'on'  # Checkbox marcado
    })

    # Verifica transição automática
    process = repo.get_process(process_id)
    assert process['current_state'] == "pedido"

    # Verifica histórico
    last_event = process['history'][-1]
    assert last_event['action'] == "auto_transitioned"
    assert last_event['trigger'] == "prerequisite_met"
```

### 9.3 Testes End-to-End

**Arquivo:** `tests/test_workflow_e2e.py`

```python
import pytest
from src.app import app
from src.persistence.workflow_repository import WorkflowRepository

def test_complete_pedidos_workflow(client):
    """
    Testa fluxo completo:
    1. Criar pedido via formulário
    2. Processo criado automaticamente em "Orçamento"
    3. Aprovar cliente → Auto-transição para "Pedido"
    4. Confirmar pagamento → Auto-transição para "Entrega"
    5. Mover manualmente para "Concluído"
    """
    repo = WorkflowRepository()

    # 1. Criar pedido
    response = client.post('/pedidos', data={
        'cliente': 'Test Client',
        'produto': 'Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': '',  # Desmarcado
        'pagamento_recebido': ''  # Desmarcado
    })

    # Encontra processo criado
    processes = repo.find_processes(filters={
        "source_form": "pedidos",
        "process_data.cliente": "Test Client"
    })
    assert len(processes) == 1
    process = processes[0]

    # 2. Verifica estado inicial
    assert process['current_state'] == "orcamento"

    # 3. Aprovar cliente
    form_id = process['source_form_id']
    client.post(f'/pedidos/edit/{form_id}', data={
        'cliente': 'Test Client',
        'produto': 'Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': 'on',  # Marcado
        'pagamento_recebido': ''
    })

    # Verifica transição automática
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "pedido"

    # 4. Confirmar pagamento
    client.post(f'/pedidos/edit/{form_id}', data={
        'cliente': 'Test Client',
        'produto': 'Test Product',
        'quantidade': '5',
        'valor_total': '500.00',
        'aprovado_cliente': 'on',
        'pagamento_recebido': 'on'  # Marcado
    })

    # Verifica transição automática para "Entrega"
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "entrega"

    # 5. Mover manualmente para "Concluído"
    response = client.post(f'/workflow/transition/{process["process_id"]}', json={
        'to_state': 'concluido',
        'actor_type': 'user',
        'justification': ''
    })

    assert response.status_code == 200

    # Verifica estado final
    process = repo.get_process(process['process_id'])
    assert process['current_state'] == "concluido"

    # Verifica histórico completo (4 eventos: created + 3 transições)
    assert len(process['history']) == 4
    assert process['history'][0]['action'] == "created"
    assert process['history'][1]['action'] == "auto_transitioned"
    assert process['history'][2]['action'] == "auto_transitioned"
    assert process['history'][3]['action'] == "manual_transition"
```

### 9.4 Matriz de Cobertura de Testes

| Componente | Unitário | Integração | E2E |
|------------|----------|------------|-----|
| KanbanRegistry | ✅ | ✅ | ✅ |
| ProcessFactory | ✅ | ✅ | ✅ |
| FormTriggerManager | ✅ | ✅ | ✅ |
| AutoTransitionEngine | ✅ | ✅ | ✅ |
| PrerequisiteChecker | ✅ | ✅ | ✅ |
| TransitionHandler | ✅ | ✅ | ✅ |
| WorkflowRepository | ✅ | ✅ | ✅ |
| Form Routes Integration | - | ✅ | ✅ |
| Workflow Routes | ✅ | ✅ | ✅ |

**Meta de cobertura:** 85%+

---

## 10. Considerações de Performance

### 10.1 Otimizações

**1. Cache de KanbanRegistry:**

```python
class KanbanRegistry:
    def __init__(self):
        self._cache_ttl = 300  # 5 minutos
        self._cache_timestamp = None
        self._cached_data = None

    def _load_registry(self):
        now = time.time()
        if (self._cached_data is None or
            now - self._cache_timestamp > self._cache_ttl):
            # Recarrega do disco
            self._cached_data = self._load_from_disk()
            self._cache_timestamp = now
        return self._cached_data
```

**2. Índices de Banco de Dados:**

```sql
-- Acelera busca de processos por formulário origem
CREATE INDEX idx_processes_source ON workflow_processes(source_form, source_form_id);

-- Acelera busca de processos por Kanban
CREATE INDEX idx_processes_kanban ON workflow_processes(kanban_id, current_state);

-- Acelera histórico por processo
CREATE INDEX idx_history_process ON workflow_history(process_id, timestamp);
```

**3. Lazy Loading de Processos:**

No quadro Kanban, carregar apenas processos visíveis (paginação):

```python
def get_processes_for_state(kanban_id, state_id, limit=20, offset=0):
    return repo.find_processes(
        filters={"kanban_id": kanban_id, "current_state": state_id},
        limit=limit,
        offset=offset,
        order_by="created_at DESC"
    )
```

**4. Batch Updates:**

Quando múltiplos formulários são salvos em sequência, agrupar criações de processo:

```python
class FormTriggerManager:
    def __init__(self):
        self.pending_creates = []
        self.batch_timer = None

    def on_form_saved(self, form_path, form_id, form_data, user_id):
        self.pending_creates.append({
            'form_path': form_path,
            'form_id': form_id,
            'form_data': form_data,
            'user_id': user_id
        })

        # Agenda execução em batch após 2 segundos
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = Timer(2.0, self._execute_batch)
        self.batch_timer.start()

    def _execute_batch(self):
        # Processa todos pending_creates de uma vez
        for item in self.pending_creates:
            self._create_process(item)
        self.pending_creates.clear()
```

### 10.2 Benchmarks Esperados

| Operação | Tempo Esperado | Observações |
|----------|----------------|-------------|
| Salvar formulário (sem Kanban) | < 100ms | Performance atual |
| Salvar formulário (com Kanban) | < 200ms | +100ms para criar processo |
| AutoTransition check | < 50ms | Por estado verificado |
| Carregar quadro Kanban (100 processos) | < 500ms | Com índices otimizados |
| Transição manual | < 150ms | Inclui validação e logging |

### 10.3 Alertas de Performance

**Monitorar:**

1. **Número de pré-requisitos por estado**: Máximo recomendado: 5
2. **Profundidade de auto-transições em cascata**: Máximo 3 estados
3. **Número de processos por Kanban**: Arquivar processos concluídos após 90 dias
4. **Tamanho de `process_data`**: Máximo 100KB por processo

**Logs de performance:**

```python
import time
import logging

def timed_operation(operation_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start

            if elapsed > 1.0:  # Alerta se > 1s
                logging.warning(f"{operation_name} took {elapsed:.2f}s")
            else:
                logging.debug(f"{operation_name} took {elapsed:.2f}s")

            return result
        return wrapper
    return decorator

@timed_operation("create_process_from_form")
def create_from_form(self, kanban_id, form_path, form_id, form_data, created_by):
    # ...
```

---

## Conclusão

Este documento apresenta a arquitetura completa do **Sistema de Workflow Kanban v3.0** com foco na **vinculação entre Kanbans e Formulários**.

### Principais Inovações da v3.0:

1. **Kanban como Definidor de Workflow**: O Kanban é o centro do sistema, definindo estados, pré-requisitos e regras de negócio

2. **Vinculação Kanban ↔ Formulários**: Relacionamento explícito (1:N) permitindo múltiplos formulários alimentarem um mesmo Kanban

3. **Geração Automática de Processos**: Ao salvar um formulário vinculado, um processo é criado automaticamente no Kanban

4. **Integração Bidirecional**: Editar formulário atualiza processo e pode disparar transições automáticas via AutoTransitionEngine

5. **Navegação Fluida**: Usuário pode iniciar pelo Kanban (clicando "Novo") ou pelo formulário, com criação automática de processos

### Estrutura de Persistência:

```
Kanban → Linked Forms → States → Prerequisites
   ↓
Process → Source Form → Process Data → Auto-Transitions
```

### Próximos Passos:

1. Implementar **Fase 1** (KanbanRegistry e estruturas de dados)
2. Criar testes unitários para validar mapeamentos
3. Avançar para **Fase 2** (FormTriggerManager e ProcessFactory)
4. Integrar com rotas existentes de formulários
5. Completar **Fase 3** (AutoTransitionEngine integration)
6. Desenvolver UI na **Fase 4**
7. Documentar na **Fase 5**

**Prazo estimado:** 16 dias (3+4+3+4+2)

---

**Elaborado por:** Rodrigo Santista
**Com assistência de:** Claude Code (Anthropic)
**Data:** Outubro 2025
**Versão:** 3.0
