# Level 1: Fundamentals
# Sistema Kanban-Workflow VibeCForms v4.0

**Nível de conhecimento**: Novice (Iniciante)
**Para quem**: Desenvolvedores começando no projeto
**Conteúdo**: Conceitos base, arquitetura Kanban-Form (1:N), persistência plugável

---

## Navegação

- **Você está aqui**: Level 1 - Fundamentals
- **Próximo**: [Level 2 - Engine](level_2_engine.md)
- **Outros níveis**: [Level 3](level_3_interface.md) | [Level 4](level_4_architecture.md) | [Level 5](level_5_implementation.md)

---

## 1. Visão Geral e Conceitos Fundamentais

### 1.1 O que é o Sistema de Workflow Kanban

O **Sistema de Workflow Kanban do VibeCForms v4.0** é uma plataforma completa de gerenciamento de processos que combina:

- **Quadros Kanban visuais** para acompanhamento de fluxos de trabalho
- **Formulários dinâmicos** que alimentam automaticamente processos
- **Inteligência Artificial** para análise de padrões e sugestões
- **Analytics avançado** com métricas e KPIs em tempo real
- **Editor Visual** para criar Kanbans sem editar JSON
- **Sistema de Persistência Plugável** (TXT, SQLite, MySQL, PostgreSQL, MongoDB, etc.)

```
+----------------------------------------------------------------+
|                    VibeCForms v4.0 Workflow                    |
+----------------------------------------------------------------+
|                                                                |
|  +------------------+      +------------------+                |
|  |   Formulários    |      |     Kanbans      |                |
|  |   Dinâmicos      |<---->|    (Workflow)    |                |
|  +------------------+      +------------------+                |
|           |                         |                          |
|           v                         v                          |
|  +------------------+      +------------------+                |
|  |   Processos      |      |   IA Agents      |                |
|  |  Automatizados   |<---->|   & Analytics    |                |
|  +------------------+      +------------------+                |
|                                                                |
+----------------------------------------------------------------+
```

### 1.2 Conceito Central: Kanban = Workflow Definition

O princípio fundamental do sistema é que **o Kanban define as regras de negócio e o workflow**:

```
+---------------------------------------------------------------+
|                   KANBAN = WORKFLOW DEFINITION                |
|                                                               |
|  +------------+      +------------+      +------------+       |
|  | Estado 1   |----->| Estado 2   |----->| Estado 3   |       |
|  |            |      |            |      |            |       |
|  | Pré-req A  |      | Pré-req B  |      | Pré-req C  |       |
|  | Timeout 2h |      | Agent IA   |      | System     |       |
|  +------------+      +------------+      +------------+       |
|                                                               |
|  Formulários vinculados: [Form A, Form B, Form C]            |
|  Transições: Manual, System, Agent                           |
+---------------------------------------------------------------+
```

**Características principais:**

1. **Kanban como Definidor**: Define estados, transições, pré-requisitos e regras
2. **Vinculação com Formulários**: Relação 1:N (um Kanban pode ter vários forms)
3. **Geração Automática**: Salvar formulário cria processo automaticamente
4. **3 Tipos de Transição**: Manual (usuário), System (automática), Agent (IA)
5. **Filosofia "Avisar, Não Bloquear"**: Pré-requisitos nunca bloqueiam, apenas alertam

### 1.3 Filosofia: "Avisar, Não Bloquear"

Um dos princípios mais importantes do sistema:

> **Os pré-requisitos NUNCA bloqueiam transições. Eles servem para avisar, registrar e orientar, mas o usuário sempre tem autonomia final para prosseguir.**

**Comportamento padrão:**

```
Usuário tenta mover processo de "A" para "B"
         |
         v
Sistema verifica pré-requisitos de "B"
         |
         +---> Todos satisfeitos?
         |         SIM: Transição ocorre silenciosamente
         |         Registra no histórico
         |
         +---> Algum pendente?
                   - Mostra modal de aviso
                   - Lista pré-requisitos não satisfeitos
                   - Opções: [Cancelar] [Continuar Mesmo Assim]
                   - Se continuar:
                       * Solicita justificativa (opcional)
                       * Registra com flag "forced: true"
                       * Transição ocorre normalmente
```

**Benefícios:**

- **Flexibilidade**: Processos reais nem sempre seguem regras rígidas
- **Autonomia**: Usuários podem tomar decisões contextuais
- **Rastreabilidade**: Todas transições "forçadas" ficam registradas
- **Sem frustração**: Não há bloqueios que impedem trabalho urgente

### 1.4 Relação Kanban ↔ Formulários (1:N)

Um Kanban pode estar vinculado a múltiplos formulários:

```
Kanban: "Fluxo de Pedidos"
    |
    +--- Formulário: "pedidos"           (primary: true)
    +--- Formulário: "pedidos_urgentes"  (primary: false)
    +--- Formulário: "pedidos_especiais" (primary: false)
```

**Diagrama de vinculação:**

```
+-------------------+
|  KANBAN BOARD     |
|  "Pedidos"        |
+-------------------+
| linked_forms:     |
|  - pedidos (P)    |
|  - pedidos_urg    |
+-------------------+
         |
         | (vincula)
         v
+-------------------+     +-------------------+
|  FORMULÁRIO       |     |  FORMULÁRIO       |
|  "pedidos"        |     |  "pedidos_urg"    |
+-------------------+     +-------------------+
| - cliente         |     | - cliente         |
| - produto         |     | - produto         |
| - quantidade      |     | - prazo           |
+-------------------+     +-------------------+
         |                         |
         | (save)                  | (save)
         v                         v
    +-------------------------------------+
    | PROCESSO CRIADO AUTOMATICAMENTE    |
    | no Kanban "Pedidos"                |
    | Estado inicial: "Orçamento"        |
    +-------------------------------------+
```

### 1.5 Geração Automática de Processos

**Fluxo de criação automática:**

```
1. Usuário preenche formulário
         |
         v
2. Clica em "Salvar"
         |
         v
3. Sistema salva dados do formulário
         |
         v
4. FormTriggerManager detecta vinculação com Kanban
         |
         v
5. ProcessFactory cria novo processo no Kanban
         |
         v
6. AutoTransitionEngine verifica se pode auto-progredir
         |
         v
7. Processo aparece no quadro Kanban no estado inicial
```

**Exemplo prático:**

```json
// Usuário salva formulário com dados:
{
  "cliente": "ACME Corp",
  "produto": "Widget Premium",
  "quantidade": 10,
  "valor_total": 1500.00,
  "aprovado_cliente": false
}

// Sistema cria processo automaticamente:
{
  "process_id": "proc_pedidos_1730032800_42",
  "kanban_id": "pedidos",
  "current_state": "orcamento",
  "title": "Pedido #42 - ACME Corp",
  "description": "10x Widget Premium - R$ 1500.00",
  "source_form": "pedidos",
  "source_form_id": 42,
  "process_data": { /* dados do formulário */ },
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

## 2. Arquitetura de Vinculação Kanban-Formulário

### 2.1 KanbanRegistry: Mapeamento Bidirecional

O **KanbanRegistry** é o componente central que gerencia o relacionamento entre Kanbans e Formulários.

```
+------------------------------------------------------------+
|                      KanbanRegistry                        |
+------------------------------------------------------------+
|                                                            |
|  Kanban → Forms Mapping:                                   |
|  {                                                         |
|    "pedidos": ["pedidos", "pedidos_urgentes"],            |
|    "projetos": ["projetos", "projetos/propostas"],        |
|    "rh_contratacao": ["rh/candidatos"]                    |
|  }                                                         |
|                                                            |
|  Form → Kanbans Mapping:                                   |
|  {                                                         |
|    "pedidos": ["pedidos"],                                |
|    "pedidos_urgentes": ["pedidos"],                       |
|    "rh/candidatos": ["rh_contratacao"]                    |
|  }                                                         |
|                                                            |
+------------------------------------------------------------+
```

**Métodos principais:**

```python
class KanbanRegistry:
    def get_kanbans_for_form(self, form_path: str) -> list:
        """
        Retorna lista de Kanbans vinculados a um formulário.

        Exemplo:
        >>> registry.get_kanbans_for_form("pedidos")
        ["pedidos"]
        """

    def get_forms_for_kanban(self, kanban_id: str) -> list:
        """
        Retorna lista de formulários vinculados a um Kanban.

        Exemplo:
        >>> registry.get_forms_for_kanban("pedidos")
        [
            {"form_path": "pedidos", "primary": True, "auto_create_process": True},
            {"form_path": "pedidos_urgentes", "primary": False, "auto_create_process": True}
        ]
        """

    def get_primary_form(self, kanban_id: str) -> str:
        """
        Retorna o formulário principal de um Kanban.
        Usado quando usuário clica "Novo Processo" no quadro.
        """

    def should_auto_create_process(self, form_path: str, kanban_id: str) -> bool:
        """
        Verifica se salvar o formulário deve criar processo automaticamente.
        """
```

### 2.2 FormTriggerManager: Detecta Saves e Dispara Criação

O **FormTriggerManager** monitora salvamentos de formulários e dispara a criação de processos:

```
+------------------------------------------------------------+
|                    FormTriggerManager                      |
+------------------------------------------------------------+
|                                                            |
|  on_form_saved(form_path, form_id, form_data, user_id)    |
|      |                                                     |
|      +---> Consulta KanbanRegistry                        |
|      +---> Para cada Kanban vinculado:                    |
|      |         - Verifica auto_create_process = true      |
|      |         - Chama ProcessFactory.create_from_form()  |
|      +---> Retorna lista de process_ids criados           |
|                                                            |
+------------------------------------------------------------+
```

**Fluxo de integração:**

```
POST /pedidos (salvar formulário)
         |
         v
VibeCForms.py: route handler
         |
         v
Salva dados do formulário
         |
         v
FormTriggerManager.on_form_saved()
         |
         +---> KanbanRegistry: Busca Kanbans vinculados
         |         |
         |         +---> Retorna: ["pedidos"]
         |
         +---> ProcessFactory.create_from_form()
         |         |
         |         +---> Cria processo no Kanban "pedidos"
         |         +---> Retorna: "proc_pedidos_xxx"
         |
         v
Redireciona para /workflow/board/pedidos
```

### 2.3 ProcessFactory: Cria Processos a partir de Forms

O **ProcessFactory** é responsável por criar instâncias de processos de workflow a partir de dados de formulários.

**Exemplo de mapeamento de campos:**

```json
// Configuração no Kanban:
{
  "field_mapping": {
    "process_title_template": "Pedido #{id} - {cliente}",
    "process_description_template": "{quantidade}x {produto} - R$ {valor_total}",
    "custom_fields_mapping": {
      "cliente": "process_data.cliente",
      "produto": "process_data.produto"
    }
  }
}

// Processo gerado:
{
  "process_id": "proc_pedidos_1730032800_42",
  "title": "Pedido #42 - ACME Corp",
  "description": "10x Widget Premium - R$ 1500.00"
}
```

### 2.4 Diagrama ASCII da Arquitetura de Vinculação

```
+------------------------------------------------------------------+
|                    Arquitetura de Vinculação                     |
+------------------------------------------------------------------+

+------------------+       +-------------------+       +------------------+
|   Formulário     |       |  KanbanRegistry   |       |      Kanban      |
|   (Form Spec)    |------>|  (bidirectional)  |<------|   (Workflow)     |
+------------------+       +-------------------+       +------------------+
        |                           |                           |
        | save()                    | lookup()                  | define rules
        v                           v                           v
+------------------+       +-------------------+       +------------------+
| FormTrigger      |       |  ProcessFactory   |       | WorkflowProcess  |
| Manager          |------>|                   |------>|   (Instance)     |
+------------------+       +-------------------+       +------------------+
        |                           |                           |
        | on_saved()                | create_from_form()        | initial_state
        v                           v                           v
+------------------+       +-------------------+       +------------------+
| VibeCForms.py    |       | WorkflowRepo      |       | AutoTransition   |
| (Routes)         |       | (Persistence)     |       | Engine           |
+------------------+       +-------------------+       +------------------+
                                    |
                                    v
                           +-------------------+
                           |  BaseRepository   |
                           |  (TXT/SQLite/     |
                           |   MySQL/etc)      |
                           +-------------------+
```

---

## 3. Sistema de Persistência Plugável

### 3.1 IMPORTANTE: Banco de Dados NÃO é Obrigatório

Um dos diferenciais do VibeCForms é que **banco de dados NÃO é obrigatório**:

```
+---------------------------------------------------------------+
|              Sistema de Persistência Plugável                 |
+---------------------------------------------------------------+
|                                                               |
|  PADRÃO: TXT (Arquivos .txt delimitados por ponto-e-vírgula) |
|                                                               |
|  OPCIONAL: SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML|
|                                                               |
+---------------------------------------------------------------+
```

**Filosofia:**

- **TXT como padrão**: Funciona sem instalar nenhum banco de dados
- **Evolução gradual**: Pode começar com TXT e migrar para SQL depois
- **Escolha por forma**: Cada formulário pode usar backend diferente
- **Zero configuração**: TXT funciona out-of-the-box

### 3.2 BaseRepository Interface (11 Métodos)

Todos os backends implementam a mesma interface:

```python
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    """
    Interface base para todos os backends de persistência.

    Garante que qualquer backend (TXT, SQLite, MySQL, etc.) implemente
    os mesmos métodos, permitindo troca transparente.
    """

    @abstractmethod
    def create(self, form_path: str, spec: dict, data: dict) -> bool:
        """Cria novo registro."""
        pass

    @abstractmethod
    def read_all(self, form_path: str, spec: dict) -> list:
        """Lê todos os registros."""
        pass

    @abstractmethod
    def update(self, form_path: str, spec: dict, idx: int, data: dict) -> bool:
        """Atualiza registro existente."""
        pass

    @abstractmethod
    def delete(self, form_path: str, spec: dict, idx: int) -> bool:
        """Deleta registro."""
        pass

    @abstractmethod
    def exists(self, form_path: str) -> bool:
        """Verifica se storage existe."""
        pass

    @abstractmethod
    def has_data(self, form_path: str) -> bool:
        """Verifica se tem dados."""
        pass

    @abstractmethod
    def create_storage(self, form_path: str, spec: dict) -> bool:
        """Cria storage (arquivo .txt ou tabela SQL)."""
        pass

    @abstractmethod
    def drop_storage(self, form_path: str) -> bool:
        """Remove storage."""
        pass

    @abstractmethod
    def count(self, form_path: str) -> int:
        """Conta registros."""
        pass

    @abstractmethod
    def search(self, form_path: str, spec: dict, filters: dict) -> list:
        """Busca registros com filtros."""
        pass

    @abstractmethod
    def backup(self, form_path: str, backup_dir: str) -> str:
        """Cria backup do storage."""
        pass
```

### 3.3 Backends Suportados

#### 3.3.1 TXT Backend (Padrão)

```
+-------------------------------------------------------+
|                    TXT Adapter                        |
+-------------------------------------------------------+
| Path: src/                                            |
| Extension: .txt                                       |
| Delimiter: ;                                          |
| Encoding: utf-8                                       |
|                                                       |
| Exemplo de arquivo:                                   |
| contatos.txt:                                         |
|   nome;email;telefone                                 |
|   João Silva;joao@email.com;11999999999              |
|   Maria Santos;maria@email.com;11888888888           |
+-------------------------------------------------------+
```

**Vantagens:**
- Zero configuração
- Fácil backup (copiar arquivos)
- Legível por humanos
- Compatível com Git
- Funciona em qualquer OS

**Desvantagens:**
- Performance inferior com muitos registros (>10.000)
- Sem índices
- Sem transações ACID

#### 3.3.2 SQLite Backend (Implementado)

```
+-------------------------------------------------------+
|                  SQLite Adapter                       |
+-------------------------------------------------------+
| Database: src/vibecforms.db                           |
| Cada formulário = 1 tabela                            |
| Timeout: 10 segundos                                  |
|                                                       |
| Mapeamento de tipos:                                  |
|   text, email, url, tel → TEXT                        |
|   number, range → REAL                                |
|   checkbox → INTEGER (0/1)                            |
|   date, datetime-local → TEXT (ISO format)            |
+-------------------------------------------------------+
```

**Vantagens:**
- Melhor performance que TXT
- Suporte a índices
- Transações ACID
- Sem servidor externo
- Um único arquivo .db

**Desvantagens:**
- Não recomendado para alta concorrência
- Limite prático ~2 GB

#### 3.3.3 MySQL/PostgreSQL (Configurado)

**Vantagens:**
- Alta performance
- Suporte a milhões de registros
- Alta concorrência
- Ferramentas de administração robustas
- Backup/restore profissionais

**Desvantagens:**
- Requer servidor de banco de dados
- Configuração mais complexa
- Custo de infraestrutura

#### 3.3.4 MongoDB (Configurado)

```
+-------------------------------------------------------+
|                  MongoDB Adapter                      |
+-------------------------------------------------------+
| NoSQL document-based                                  |
| Cada registro = 1 documento JSON                      |
| Schema-less (flexível)                                |
|                                                       |
| Vantagem: Ideal para process_data dinâmico            |
| Workflow processes têm estrutura variável             |
+-------------------------------------------------------+
```

### 3.4 Configuração via persistence.json

**Arquivo:** `src/config/persistence.json`

```json
{
  "version": "3.0",
  "default_backend": "txt",

  "backends": {
    "txt": {
      "type": "txt",
      "config": {
        "base_path": "src/",
        "extension": ".txt",
        "delimiter": ";",
        "encoding": "utf-8"
      }
    },
    "sqlite": {
      "type": "sqlite",
      "config": {
        "database_path": "src/vibecforms.db",
        "timeout": 10
      }
    }
  },

  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "sqlite",
    "pedidos": "sqlite",
    "financeiro/*": "mysql",
    "*": "default_backend"
  }
}
```

### 3.5 RepositoryFactory Pattern

```python
class RepositoryFactory:
    """
    Factory que cria instâncias de repositórios baseado no tipo de backend.

    Carrega configuração de persistence.json e retorna o adapter apropriado.
    """

    def get_repository(self, form_path: str) -> BaseRepository:
        """
        Retorna repositório apropriado para o formulário.

        Processo:
        1. Consulta form_mappings em persistence.json
        2. Encontra backend configurado (ou usa default)
        3. Carrega configuração do backend
        4. Retorna instância do adapter (TxtAdapter, SQLiteAdapter, etc.)

        Suporta wildcards:
        - "contatos" → exata
        - "financeiro/*" → qualquer sub-path
        - "*" → default
        """
```

### 3.6 WorkflowRepository: Extensão para Workflows

Para processos de workflow, há uma extensão do BaseRepository:

```python
class WorkflowRepository(BaseRepository):
    """
    Repositório especializado para processos de workflow.

    Adiciona métodos específicos para:
    - Buscar processos por Kanban
    - Buscar processos por estado
    - Buscar processos por formulário origem
    - Registrar histórico de transições
    - Consultas complexas para analytics
    """

    def get_processes_by_kanban(
        self,
        kanban_id: str,
        state: str = None,
        limit: int = None,
        offset: int = None
    ) -> list:
        """Busca processos de um Kanban específico."""

    def get_processes_by_source_form(
        self,
        form_path: str,
        form_id: int = None
    ) -> list:
        """Busca processos criados a partir de um formulário."""

    def update_process_state(
        self,
        process_id: str,
        new_state: str,
        actor: str,
        actor_type: str,
        trigger: str,
        justification: str = None,
        metadata: dict = None
    ) -> bool:
        """
        Atualiza estado de um processo e registra no histórico.
        """

    def get_process_history(self, process_id: str) -> list:
        """Retorna histórico completo de um processo."""

    def get_analytics_data(
        self,
        kanban_id: str,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        Retorna dados agregados para analytics:
        - Tempo médio por estado
        - Taxa de conclusão
        - Volume de processos
        - Gargalos identificados
        """
```

---

## Próximos Passos

Após dominar estes fundamentos, avance para:

**[Level 2 - Engine](level_2_engine.md)**: AutoTransitionEngine, AI Agents, Pattern Analysis

---

**Referência original**: `VibeCForms/docs/planning/workflow/workflow_kanban_planejamento_v4_parte1.md` (Seções 1-3)
