# Sistema de Workflow Kanban - VibeCForms v4.0
## Planejamento Completo com IA, Analytics e Visual Editor
## PARTE 1: Fundamentos e Arquitetura Core

**Versão:** 4.0 - Parte 1 de 3
**Data:** Outubro 2025
**Autor:** Rodrigo Santista (com assistência de Claude Code)

---

## Índice - Parte 1

1. [Visão Geral e Conceitos Fundamentais](#1-visão-geral-e-conceitos-fundamentais)
2. [Arquitetura de Vinculação Kanban-Formulário](#2-arquitetura-de-vinculação-kanban-formulário)
3. [Sistema de Persistência Plugável](#3-sistema-de-persistência-plugável)
4. [Fluxos de Usuário Completos](#4-fluxos-de-usuário-completos)
5. [Análise de Padrões por IA](#5-análise-de-padrões-por-ia)
6. [Sistema de Agentes de IA](#6-sistema-de-agentes-de-ia)
7. [AutoTransitionEngine Detalhado](#7-autotransitionengine-detalhado)
8. [Dashboard de Analytics](#8-dashboard-de-analytics)

**Continua na Parte 2:** Editor Visual, Exportações, Auditoria, Arquitetura Técnica, Implementação

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

        >>> registry.get_kanbans_for_form("pedidos_urgentes")
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

        Exemplo:
        >>> registry.get_primary_form("pedidos")
        "pedidos"
        """

    def should_auto_create_process(self, form_path: str, kanban_id: str) -> bool:
        """
        Verifica se salvar o formulário deve criar processo automaticamente.

        Exemplo:
        >>> registry.should_auto_create_process("pedidos", "pedidos")
        True
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
|  on_form_updated(form_path, form_id, form_data, user_id)  |
|      |                                                     |
|      +---> Busca processos criados a partir deste form    |
|      +---> Atualiza process_data de cada processo         |
|      +---> Dispara AutoTransitionEngine para cada um      |
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
         +---> Retorna para route handler
         |
         v
Redireciona para /workflow/board/pedidos
ou
Mostra mensagem: "Processo criado no Kanban 'Pedidos'"
```

### 2.3 ProcessFactory: Cria Processos a partir de Forms

O **ProcessFactory** é responsável por criar instâncias de processos de workflow a partir de dados de formulários:

```python
class ProcessFactory:
    """
    Factory para criação de processos de workflow a partir de formulários.

    Mapeia campos do formulário para estrutura de processo usando templates.
    """

    def create_from_form(
        self,
        kanban_id: str,
        form_path: str,
        form_id: int,
        form_data: dict,
        created_by: str
    ) -> str:
        """
        Cria um novo processo a partir de dados de formulário.

        Processo:
        1. Carrega configuração do Kanban
        2. Obtém estado inicial
        3. Aplica templates de título e descrição
        4. Gera process_id único
        5. Monta estrutura do processo
        6. Salva no WorkflowRepository
        7. Retorna process_id

        Args:
            kanban_id: ID do Kanban onde criar o processo
            form_path: Caminho do formulário origem
            form_id: ID do registro no formulário
            form_data: Dados do formulário
            created_by: ID do usuário

        Returns:
            process_id do processo criado
        """
```

**Exemplo de mapeamento de campos:**

```json
// Configuração no Kanban:
{
  "field_mapping": {
    "process_title_template": "Pedido #{id} - {cliente}",
    "process_description_template": "{quantidade}x {produto} - R$ {valor_total}",
    "custom_fields_mapping": {
      "cliente": "process_data.cliente",
      "produto": "process_data.produto",
      "quantidade": "process_data.quantidade",
      "valor_total": "process_data.valor_total"
    }
  }
}

// Dados do formulário (input):
{
  "id": 42,
  "cliente": "ACME Corp",
  "produto": "Widget Premium",
  "quantidade": 10,
  "valor_total": 1500.00
}

// Processo gerado (output):
{
  "process_id": "proc_pedidos_1730032800_42",
  "title": "Pedido #42 - ACME Corp",
  "description": "10x Widget Premium - R$ 1500.00",
  "process_data": {
    "cliente": "ACME Corp",
    "produto": "Widget Premium",
    "quantidade": 10,
    "valor_total": 1500.00
  }
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
|                                                       |
| Exemplo de tabela:                                    |
| CREATE TABLE contatos (                               |
|   id INTEGER PRIMARY KEY AUTOINCREMENT,               |
|   nome TEXT NOT NULL,                                 |
|   email TEXT NOT NULL,                                |
|   telefone TEXT                                       |
| );                                                    |
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
- Limite de tamanho (~140 TB, mas prático ~2 GB)

#### 3.3.3 MySQL/PostgreSQL (Configurado, não implementado)

```
+-------------------------------------------------------+
|              MySQL/PostgreSQL Adapter                 |
+-------------------------------------------------------+
| Connection string em persistence.json                 |
| Pool de conexões configurável                         |
| Suporte a schemas/databases                           |
| Transações ACID completas                             |
|                                                       |
| Configuração exemplo:                                 |
| {                                                     |
|   "host": "localhost",                                |
|   "port": 3306,                                       |
|   "database": "vibecforms",                           |
|   "user": "vibecforms_user",                          |
|   "password": "secure_password",                      |
|   "pool_size": 10                                     |
| }                                                     |
+-------------------------------------------------------+
```

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

#### 3.3.4 MongoDB (Configurado, não implementado)

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
    },
    "mysql": {
      "type": "mysql",
      "config": {
        "host": "localhost",
        "port": 3306,
        "database": "vibecforms",
        "user": "vibecforms_user",
        "password": "${MYSQL_PASSWORD}",
        "pool_size": 10
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

    def __init__(self):
        self.config = self._load_config()
        self._adapters = {}

    def get_repository(self, form_path: str) -> BaseRepository:
        """
        Retorna repositório apropriado para o formulário.

        Processo:
        1. Consulta form_mappings em persistence.json
        2. Encontra backend configurado (ou usa default)
        3. Carrega configuração do backend
        4. Retorna instância do adapter (TxtAdapter, SQLiteAdapter, etc.)

        Exemplo:
        >>> factory = RepositoryFactory()
        >>> repo = factory.get_repository("contatos")
        >>> type(repo)
        <class 'SQLiteAdapter'>

        >>> repo = factory.get_repository("rh/funcionarios")
        >>> type(repo)
        <class 'TxtAdapter'>  # Usa default
        """

    def _load_config(self) -> dict:
        """Carrega persistence.json."""

    def _get_backend_for_form(self, form_path: str) -> str:
        """
        Resolve qual backend usar para um formulário.

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

## 4. Fluxos de Usuário Completos

### 4.1 Fluxo 1: Criar Novo Kanban (via Editor Visual ou JSON)

#### Opção A: Via Editor Visual (Recomendado)

```
1. Usuário acessa "/workflow/admin"
         |
         v
2. Clica em "Criar Novo Kanban"
         |
         v
3. Preenche formulário visual:
   - Nome: "Fluxo de Pedidos"
   - Descrição: "Gerenciamento de ciclo de vida de pedidos"
   - Ícone: Seleciona "fa-shopping-cart" do seletor
         |
         v
4. Adiciona estados arrastando cards:
   - Orçamento (cinza)
   - Pedido (azul)
   - Entrega (amarelo)
   - Concluído (verde)
         |
         v
5. Para cada estado, configura:
   - Nome
   - Cor
   - Ícone
   - Pré-requisitos (via interface visual)
   - Timeout (opcional)
         |
         v
6. Vincula formulários:
   - Busca "pedidos" e marca como primary
   - Busca "pedidos_urgentes" e adiciona
         |
         v
7. Clica "Salvar"
         |
         v
8. Sistema:
   - Valida configuração
   - Gera JSON automaticamente
   - Salva em src/config/kanbans/pedidos_kanban.json
   - Atualiza KanbanRegistry
   - Redireciona para /workflow/board/pedidos
```

#### Opção B: Via JSON (Avançado)

```
1. Usuário cria arquivo manualmente:
   src/config/kanbans/pedidos_kanban.json
         |
         v
2. Define estrutura JSON completa (ver seção 2.1 v3.0)
         |
         v
3. Sistema detecta novo arquivo automaticamente
         |
         v
4. Carrega e valida JSON
         |
         v
5. Kanban aparece em /workflow/kanbans
```

### 4.2 Fluxo 2: Vincular Kanban a Formulários

```
1. Usuário acessa "/workflow/admin/edit/pedidos"
         |
         v
2. Na aba "Formulários Vinculados":
   - Lista atual de formulários
   - Botão [+ Adicionar Formulário]
         |
         v
3. Clica [+ Adicionar Formulário]
         |
         v
4. Modal com busca de formulários:
   - Campo de busca: digita "pedidos"
   - Mostra resultados:
       * pedidos
       * pedidos_urgentes
       * pedidos_especiais
         |
         v
5. Seleciona "pedidos"
   - Checkbox: [x] Formulário principal
   - Checkbox: [x] Criar processo automaticamente
         |
         v
6. Clica "Adicionar"
         |
         v
7. Sistema:
   - Atualiza pedidos_kanban.json
   - Adiciona ao linked_forms
   - Atualiza KanbanRegistry
   - Mostra mensagem de sucesso
```

### 4.3 Fluxo 3: Preencher Formulário → Gerar Processo Automaticamente

#### Cenário A: Inicia pelo Kanban

```
1. Usuário acessa "/workflow/board/pedidos"
         |
         v
2. Vê quadro Kanban com colunas:
   [Orçamento] [Pedido] [Entrega] [Concluído]
         |
         v
3. Clica botão [+ Novo Processo]
         |
         v
4. Sistema verifica linked_forms:
   - Se 1 formulário: Redireciona direto
   - Se múltiplos: Mostra seletor
         |
         v
5. (Caso múltiplos) Modal "Selecione o tipo de pedido":
   - [ ] Pedido Normal
   - [ ] Pedido Urgente
   - [ ] Pedido Especial
         |
         v
6. Usuário seleciona "Pedido Normal"
         |
         v
7. Sistema redireciona para "/pedidos?kanban_redirect=pedidos"
         |
         v
8. Usuário preenche formulário:
   - Cliente: "ACME Corp"
   - Produto: "Widget Premium"
   - Quantidade: 10
   - Valor Total: R$ 1500,00
   - [ ] Aprovado pelo cliente (desmarcado)
   - [ ] Pagamento recebido (desmarcado)
         |
         v
9. Clica [Salvar]
         |
         v
10. Sistema:
    - Salva dados em src/pedidos.txt (ou database)
    - FormTriggerManager.on_form_saved()
    - ProcessFactory cria processo:
        * process_id: "proc_pedidos_xxx_42"
        * kanban_id: "pedidos"
        * current_state: "orcamento"
        * title: "Pedido #42 - ACME Corp"
    - AutoTransitionEngine verifica pré-requisitos de "orcamento"
        * Nenhum pré-requisito → Fica em "orcamento"
    - Redireciona para "/workflow/board/pedidos"
         |
         v
11. Usuário vê:
    - Toast: "✅ Processo criado no Kanban 'Pedidos'"
    - Card aparece na coluna "Orçamento"
    - Card mostra:
        * Título: "Pedido #42 - ACME Corp"
        * Descrição: "10x Widget Premium - R$ 1500,00"
        * ⚠️ Aguardando aprovação do cliente
```

#### Cenário B: Inicia pelo Formulário

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
4-8. (Mesmo processo de preenchimento)
         |
         v
9. Clica [Salvar]
         |
         v
10. Sistema:
     - Salva dados do formulário
     - FormTriggerManager detecta vinculação
     - Cria processo automaticamente
     - Mostra mensagem:
         "✅ Dados salvos com sucesso!
          🎯 Processo criado no quadro 'Fluxo de Pedidos'"
     - Botão: [Ver no Quadro Kanban]
         |
         v
11. (Opcional) Usuário clica [Ver no Quadro Kanban]
         |
         v
12. Redireciona para "/workflow/board/pedidos"
    com destaque no processo recém-criado
```

### 4.4 Fluxo 4: Transitar Estados (Manual, System, Agent)

#### Transição Manual (Usuário)

```
1. Usuário está em "/workflow/board/pedidos"
         |
         v
2. Arrasta card "Pedido #42" de "Orçamento" para "Pedido"
         |
         v
3. Sistema verifica pré-requisitos de "Pedido":
   - Requisito: "aprovado_cliente = true"
   - Status: process_data.aprovado_cliente = false
   - Resultado: NÃO satisfeito
         |
         v
4. Modal de aviso aparece:
   ┌─────────────────────────────────────────┐
   │ ⚠️  Pré-requisitos não satisfeitos       │
   ├─────────────────────────────────────────┤
   │                                         │
   │ O estado "Pedido Confirmado" requer:    │
   │                                         │
   │ ❌ Aprovação do Cliente                 │
   │    Campo: aprovado_cliente              │
   │    Esperado: true                       │
   │    Atual: false                         │
   │                                         │
   │ Deseja continuar mesmo assim?           │
   │                                         │
   │ Justificativa (opcional):               │
   │ [____________________________]          │
   │                                         │
   │ [Cancelar]  [Continuar Mesmo Assim]    │
   └─────────────────────────────────────────┘
         |
         +---> Se clicar [Cancelar]:
         |         - Processo volta para "Orçamento"
         |         - Nenhuma mudança registrada
         |
         +---> Se clicar [Continuar Mesmo Assim]:
                   |
                   v
              Usuário digita justificativa:
              "Cliente aprovou por telefone, aguardando email formal"
                   |
                   v
              Sistema:
              - Move processo para "Pedido"
              - Registra no histórico:
                {
                  "timestamp": "2025-10-27T14:30:00",
                  "action": "manual_transition",
                  "from_state": "orcamento",
                  "to_state": "pedido",
                  "actor": "user123",
                  "actor_type": "user",
                  "trigger": "drag_and_drop",
                  "forced": true,
                  "prerequisites_not_met": ["cliente_aprovacao"],
                  "justification": "Cliente aprovou por telefone..."
                }
              - Card move visualmente para coluna "Pedido"
```

#### Transição System (Automática)

```
1. Processo está em "Pedido Confirmado"
   Pré-requisito do próximo estado ("Entrega"):
   - pagamento_recebido = true
         |
         v
2. Usuário acessa "/pedidos/edit/42"
         |
         v
3. Marca checkbox: [x] Pagamento recebido
         |
         v
4. Clica [Salvar]
         |
         v
5. Sistema:
   - Salva alteração no formulário
   - FormTriggerManager.on_form_updated()
   - Atualiza process_data do processo
   - AutoTransitionEngine.check_and_transition()
         |
         v
6. AutoTransitionEngine avalia:
   - Estado atual: "pedido"
   - Próximo estado: "entrega"
   - Pré-requisito: pagamento_recebido = true
   - process_data.pagamento_recebido = true
   - Resultado: ✅ SATISFEITO
         |
         v
7. Sistema move automaticamente:
   "Pedido Confirmado" → "Em Entrega"
         |
         v
8. Registra no histórico:
   {
     "timestamp": "2025-10-28T09:00:00",
     "action": "auto_transitioned",
     "from_state": "pedido",
     "to_state": "entrega",
     "actor": "system",
     "actor_type": "auto_transition",
     "trigger": "prerequisite_met",
     "prerequisite_id": "pagamento_confirmado",
     "forced": false
   }
         |
         v
9. Verifica próximo estado ("Concluído"):
   - Não tem pré-requisitos
   - Para aqui (não move automaticamente)
         |
         v
10. Usuário recebe notificação:
    "🤖 Processo movido automaticamente para 'Em Entrega'"
```

#### Transição Agent (IA)

```
1. Processo está em "Pedido Confirmado" há 5 dias
   Configuração do estado tem: "agent_analysis": true
         |
         v
2. Sistema (cron job ou evento):
   - AgentOrchestrator.analyze_process("proc_pedidos_xxx_42")
         |
         v
3. AgentOrchestrator carrega contexto:
   - Dados do processo (process_data)
   - Histórico de transições
   - Padrões históricos de processos similares
   - Dados do formulário original
         |
         v
4. Chama BaseAgent específico do estado:
   - PedidoConfirmadoAgent.analyze()
         |
         v
5. Agent IA analisa:
   - Tempo no estado atual: 5 dias (acima da média de 2 dias)
   - Pré-requisitos: pagamento_recebido = false
   - Histórico do cliente: 98% de pagamentos em até 3 dias
   - Padrão detectado: Cliente paga, mas esquece de atualizar
         |
         v
6. Agent gera recomendação:
   {
     "recommendation": "contact_client",
     "confidence": 0.85,
     "reasoning": [
       "Processo há 5 dias no estado 'Pedido'",
       "Cliente ACME Corp tem histórico de 98% pagamento em 3 dias",
       "Possível esquecimento de atualizar status",
       "Recomendar contato para verificação"
     ],
     "suggested_actions": [
       {
         "action": "send_reminder",
         "description": "Enviar lembrete de pagamento"
       },
       {
         "action": "manual_check",
         "description": "Verificar manualmente status do pagamento"
       }
     ]
   }
         |
         v
7. Sistema mostra no card do processo:
   ┌─────────────────────────────────────┐
   │ Pedido #42 - ACME Corp              │
   │ 10x Widget Premium - R$ 1500,00     │
   ├─────────────────────────────────────┤
   │ 🤖 IA Agent detectou:               │
   │                                     │
   │ Processo há 5 dias sem movimento.   │
   │ Cliente tem histórico de pagamento  │
   │ rápido (98% em 3 dias).             │
   │                                     │
   │ Sugestões:                          │
   │ • Enviar lembrete de pagamento      │
   │ • Verificar status manualmente      │
   │                                     │
   │ Confiança: 85%                      │
   │                                     │
   │ [Ver Análise Completa]             │
   └─────────────────────────────────────┘
         |
         v
8. Usuário clica [Ver Análise Completa]
         |
         v
9. Modal mostra análise detalhada da IA
   com todos os raciocínios e dados usados
```

### 4.5 Fluxo 5: Visualizar Dashboard de Analytics

```
1. Usuário acessa "/workflow/analytics"
         |
         v
2. Dashboard carrega com visão geral:
   ┌──────────────────────────────────────────────────────┐
   │  📊 Dashboard de Analytics - Workflows               │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Filtros:                                            │
   │  Kanban: [Todos ▼]  Período: [Últimos 30 dias ▼]    │
   │                                                      │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  KPIs Principais:                                    │
   │  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
   │  │ Processos │  │ Taxa de   │  │ Tempo     │       │
   │  │ Ativos    │  │ Conclusão │  │ Médio     │       │
   │  │   127     │  │   78%     │  │  4.2 dias │       │
   │  └───────────┘  └───────────┘  └───────────┘       │
   │                                                      │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Gráfico: Volume de Processos por Estado            │
   │  [Gráfico de barras visualiza distribuição]         │
   │                                                      │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Gargalos Identificados:                             │
   │  ⚠️  Estado "Pedido": 23 processos há >3 dias       │
   │  ⚠️  Estado "Entrega": Tempo médio 6.5 dias         │
   │                       (acima da meta de 5 dias)     │
   │                                                      │
   └──────────────────────────────────────────────────────┘
         |
         v
3. Usuário seleciona Kanban específico:
   Kanban: [Fluxo de Pedidos ▼]
         |
         v
4. Dashboard atualiza com métricas específicas:
   - Funil de conversão
   - Heatmap de transições
   - Linha do tempo de volume
   - Top 10 processos mais longos
         |
         v
5. Usuário clica em "Heatmap de Transições"
         |
         v
6. Visualização mostra matriz:
              Para:
              Orç  Ped  Ent  Con
   De:   Orç   -   45   2    0
         Ped   3    -   38   1
         Ent   0    2    -   35
         Con   0    0    1    -

   Cores indicam frequência (verde=alto, vermelho=baixo)
   Anomalia detectada: Entrega → Concluído (35 transições)
                       vs Pedido → Entrega (38 transições)
                       = 3 processos "presos" em Entrega
         |
         v
7. Usuário exporta relatório:
   [Exportar PDF] [Exportar CSV] [Agendar Relatório]
```

### 4.6 Diagrama ASCII: Fluxo End-to-End Completo

```
USUÁRIO                  SISTEMA                      IA/ANALYTICS
   |                        |                              |
   +--- 1. Cria Kanban ---->|                              |
   |    (Editor Visual)     |                              |
   |                        +--- Salva JSON               |
   |                        +--- Atualiza Registry        |
   |<---- Kanban pronto ----|                              |
   |                        |                              |
   +--- 2. Vincula Forms -->|                              |
   |                        +--- Atualiza linked_forms    |
   |<---- Vinculação OK ----|                              |
   |                        |                              |
   +--- 3. Preenche Form -->|                              |
   |    (pedidos)           |                              |
   |                        +--- FormTriggerManager       |
   |                        +--- ProcessFactory cria proc |
   |                        +--- AutoTransition verifica  |
   |<---- Processo criado --|                              |
   |                        |                              |
   |                        +--- PatternAnalyzer --------->|
   |                        |                       analisa padrões
   |                        |<------ padrões detectados ---|
   |                        |                              |
   +--- 4. Edita Form ----->|                              |
   |    (marca aprovado)    |                              |
   |                        +--- Atualiza process_data    |
   |                        +--- AutoTransition check     |
   |                        +--- Move automaticamente     |
   |<---- Transição OK -----|                              |
   |    (System)            |                              |
   |                        +--- AnomalyDetector --------->|
   |                        |                       verifica anomalias
   |                        |<------ sem anomalias --------|
   |                        |                              |
   +--- 5. Arrasta Card --->|                              |
   |    (Manual)            |                              |
   |                        +--- Verifica pré-requisitos  |
   |                        +--- Não satisfeitos          |
   |<---- Modal de aviso ---|                              |
   |                        |                              |
   +--- Continuar (forced)->|                              |
   +--- Justificativa ----->|                              |
   |                        +--- Registra transição       |
   |                        +--- Flag "forced: true"      |
   |<---- Processo movido --|                              |
   |                        |                              |
   |                        |<------ Agent Analysis -------|
   |                        |        (assíncrono)          |
   |                        +--- Gera recomendações       |
   |<---- Notificação IA ---|                              |
   |    "Sugestão: ..."     |                              |
   |                        |                              |
   +--- 6. Acessa Analytics>|                              |
   |                        +--- Consulta WorkflowRepo    |
   |                        +--- Agrega métricas --------->|
   |                        |<------ KPIs calculados ------|
   |<---- Dashboard --------|                              |
   |                        |                              |
```

---

## 5. Análise de Padrões por IA

### 5.1 PatternAnalyzer: Detecta Padrões de Transições

O **PatternAnalyzer** é um componente de Machine Learning que analisa o histórico de transições para identificar padrões comuns e raros.

```
+----------------------------------------------------------------+
|                        PatternAnalyzer                         |
+----------------------------------------------------------------+
|                                                                |
|  Funcionalidades:                                              |
|  • Detecta padrões comuns de transições                       |
|  • Identifica sequências típicas de estados                   |
|  • Calcula tempos médios por estado                           |
|  • Detecta padrões raros/anômalos                             |
|  • Gera insights para otimização                              |
|                                                                |
|  Algoritmos:                                                   |
|  • Frequent Pattern Mining (FP-Growth)                        |
|  • Sequential Pattern Analysis                                |
|  • Time Series Analysis                                       |
|  • Clustering (K-means para agrupar processos similares)      |
|                                                                |
+----------------------------------------------------------------+
```

#### 5.1.1 Detecção de Padrões Comuns

**Objetivo:** Identificar os caminhos mais frequentes nos workflows

```python
class PatternAnalyzer:
    """
    Analisa histórico de transições para identificar padrões.
    """

    def analyze_transition_patterns(
        self,
        kanban_id: str,
        min_support: float = 0.1
    ) -> dict:
        """
        Identifica padrões comuns de transições.

        Args:
            kanban_id: ID do Kanban a analisar
            min_support: Frequência mínima para considerar padrão (0.0-1.0)

        Returns:
            {
                "common_patterns": [
                    {
                        "sequence": ["orcamento", "pedido", "entrega", "concluido"],
                        "frequency": 0.75,  # 75% dos processos
                        "avg_duration_days": 4.2,
                        "count": 156
                    },
                    {
                        "sequence": ["orcamento", "pedido", "concluido"],
                        "frequency": 0.15,  # 15% pulam "entrega"
                        "avg_duration_days": 2.8,
                        "count": 31,
                        "note": "Processos digitais sem entrega física"
                    }
                ],
                "rare_patterns": [
                    {
                        "sequence": ["orcamento", "concluido"],
                        "frequency": 0.02,  # 2% pulam direto
                        "count": 4,
                        "flag": "unusual",
                        "note": "Investigar: pular estados pode indicar erro"
                    }
                ]
            }
        """
```

**Exemplo de análise:**

```
Kanban: "Fluxo de Pedidos"
Processos analisados: 207
Período: Últimos 90 dias

Padrões Comuns Detectados:

1. Padrão Principal (75% dos casos):
   Orçamento → Pedido → Entrega → Concluído
   Duração média: 4.2 dias
   Ocorrências: 156

2. Padrão Rápido (15% dos casos):
   Orçamento → Pedido → Concluído
   Duração média: 2.8 dias
   Ocorrências: 31
   Nota: Comum para produtos digitais sem entrega física

3. Padrão com Retrocesso (8% dos casos):
   Orçamento → Pedido → Orçamento → Pedido → Entrega → Concluído
   Duração média: 6.5 dias
   Ocorrências: 17
   Nota: Cliente solicita revisão do orçamento

Padrões Raros/Anômalos:

1. Pulo Direto (2% dos casos):
   Orçamento → Concluído
   Ocorrências: 4
   ⚠️ Alerta: Possível erro ou processo especial não documentado

2. Loop Infinito (0.5% dos casos):
   Pedido ⇄ Entrega (mais de 3 vezes)
   Ocorrências: 1
   ⚠️ Alerta: Problemas de logística ou dados incorretos
```

#### 5.1.2 Análise de Tempos por Estado

```python
class PatternAnalyzer:

    def analyze_state_durations(self, kanban_id: str) -> dict:
        """
        Calcula estatísticas de tempo em cada estado.

        Returns:
            {
                "states": {
                    "orcamento": {
                        "avg_duration_hours": 18.5,
                        "median_duration_hours": 12.0,
                        "std_deviation": 8.2,
                        "min": 2.0,
                        "max": 72.0,
                        "percentile_25": 8.0,
                        "percentile_75": 24.0,
                        "outliers": [
                            {
                                "process_id": "proc_xxx",
                                "duration_hours": 72.0,
                                "note": "3x acima da média"
                            }
                        ]
                    },
                    "pedido": {
                        "avg_duration_hours": 36.0,
                        "median_duration_hours": 24.0,
                        ...
                    }
                },
                "bottlenecks": [
                    {
                        "state": "pedido",
                        "avg_duration_hours": 36.0,
                        "target_hours": 24.0,
                        "deviation_pct": 50.0,
                        "severity": "high",
                        "recommendation": "Analisar pré-requisito 'pagamento_recebido'"
                    }
                ]
            }
        """
```

**Visualização de tempos:**

```
Estado: PEDIDO CONFIRMADO
----------------------------------------
Tempo médio:    36.0 horas
Mediana:        24.0 horas
Desvio padrão:  15.2 horas

Distribuição:
  0-12h:  ████████ (25%)
 12-24h:  ████████████████ (40%)
 24-48h:  ████████ (20%)
 48-72h:  ████ (10%)
   >72h:  ██ (5%)

🔴 GARGALO DETECTADO:
- Meta: 24 horas
- Atual: 36 horas (50% acima da meta)
- Causa provável: Pré-requisito "pagamento_recebido"
  demora em média 30 horas para ser satisfeito

Recomendação:
• Configurar lembrete automático após 12h
• Integrar com gateway de pagamento para atualização automática
• Considerar transição manual se cliente confirmar pagamento
```

#### 5.1.3 Clustering de Processos Similares

```python
class PatternAnalyzer:

    def cluster_similar_processes(
        self,
        kanban_id: str,
        n_clusters: int = 5
    ) -> dict:
        """
        Agrupa processos similares usando K-means.

        Features consideradas:
        - Duração total
        - Número de transições
        - Número de retrocessos
        - Número de transições forçadas
        - Tempo em cada estado
        - Valores de process_data (se numéricos)

        Returns:
            {
                "clusters": [
                    {
                        "cluster_id": 0,
                        "label": "Processos Rápidos",
                        "count": 87,
                        "characteristics": {
                            "avg_total_duration_days": 2.1,
                            "avg_transitions": 3.0,
                            "avg_backward_transitions": 0.0,
                            "common_pattern": "orc→ped→con"
                        },
                        "representative_processes": [
                            "proc_pedidos_xxx_12",
                            "proc_pedidos_xxx_45"
                        ]
                    },
                    {
                        "cluster_id": 1,
                        "label": "Processos Complexos",
                        "count": 31,
                        "characteristics": {
                            "avg_total_duration_days": 8.5,
                            "avg_transitions": 7.2,
                            "avg_backward_transitions": 1.8,
                            "common_pattern": "orc⇄ped→ent⇄con"
                        }
                    }
                ]
            }
        """
```

### 5.2 AnomalyDetector: Identifica Transições Anômalas

O **AnomalyDetector** usa algoritmos de detecção de anomalias para identificar processos que se comportam de forma atípica.

```
+----------------------------------------------------------------+
|                       AnomalyDetector                          |
+----------------------------------------------------------------+
|                                                                |
|  Detecta:                                                      |
|  • Processos muito lentos ou muito rápidos                    |
|  • Sequências de transições anormais                          |
|  • Processos "presos" em um estado                            |
|  • Transições forçadas suspeitas                              |
|  • Padrões de processo_data incomuns                          |
|                                                                |
|  Algoritmos:                                                   |
|  • Isolation Forest                                           |
|  • DBSCAN (Density-Based Clustering)                          |
|  • Statistical Outlier Detection (Z-score, IQR)               |
|  • Sequence Anomaly Detection                                 |
|                                                                |
+----------------------------------------------------------------+
```

#### 5.2.1 Detecção de Processos Presos

```python
class AnomalyDetector:

    def detect_stuck_processes(
        self,
        kanban_id: str,
        threshold_hours: int = 48
    ) -> list:
        """
        Identifica processos que estão há muito tempo no mesmo estado.

        Args:
            kanban_id: ID do Kanban
            threshold_hours: Limite de tempo para considerar "preso"

        Returns:
            [
                {
                    "process_id": "proc_pedidos_xxx_42",
                    "title": "Pedido #42 - ACME Corp",
                    "current_state": "pedido",
                    "hours_in_state": 120.0,
                    "threshold_hours": 48.0,
                    "factor": 2.5,  # 2.5x acima do normal
                    "severity": "high",
                    "recommendation": "Verificar pré-requisito 'pagamento_recebido'",
                    "context": {
                        "prerequisites_not_met": ["pagamento_recebido"],
                        "last_update": "2025-10-22T10:30:00",
                        "expected_duration_hours": 36.0
                    }
                }
            ]
        """
```

**Alerta visual no dashboard:**

```
🚨 ALERTA: 3 Processos Presos Detectados

┌─────────────────────────────────────────────────────────┐
│ Pedido #42 - ACME Corp                                  │
│ Estado: Pedido Confirmado                               │
│ Há: 5 dias (120 horas)                                  │
│ Esperado: 36 horas                                      │
│                                                         │
│ 🔴 2.5x acima do tempo normal                          │
│                                                         │
│ Causa provável:                                         │
│ • Pré-requisito "pagamento_recebido" não satisfeito    │
│                                                         │
│ Sugestões:                                              │
│ • Contatar cliente para verificar pagamento            │
│ • Verificar se houve problema no gateway               │
│ • Considerar escalar para supervisor                   │
│                                                         │
│ [Ver Processo] [Marcar como Resolvido]                │
└─────────────────────────────────────────────────────────┘
```

#### 5.2.2 Detecção de Transições Anômalas

```python
class AnomalyDetector:

    def detect_anomalous_transitions(
        self,
        kanban_id: str,
        look_back_days: int = 90
    ) -> list:
        """
        Detecta transições que fogem do padrão histórico.

        Usa Isolation Forest para identificar:
        - Transições incomuns entre estados
        - Sequências de estados raras
        - Tempos de transição atípicos

        Returns:
            [
                {
                    "process_id": "proc_pedidos_xxx_99",
                    "anomaly_type": "unusual_sequence",
                    "sequence": ["orcamento", "concluido"],
                    "anomaly_score": -0.42,  # Quanto mais negativo, mais anômalo
                    "explanation": "Sequência rara: apenas 2% dos processos",
                    "severity": "medium",
                    "recommendation": "Revisar se todos passos foram cumpridos",
                    "similar_cases": 4
                }
            ]
        """
```

### 5.3 Machine Learning para Análise de Histórico

#### 5.3.1 Treinamento do Modelo

```python
class WorkflowMLModel:
    """
    Modelo de Machine Learning para análise e predição de workflows.

    Usa histórico de processos concluídos para treinar modelos que:
    - Preveem duração total de novos processos
    - Identificam risco de atraso
    - Sugerem próximas ações
    """

    def train(self, kanban_id: str):
        """
        Treina modelo com histórico de processos.

        Features extraídas:
        - process_data (campos numéricos e categóricos)
        - Tempo de criação (dia da semana, hora, mês)
        - Número de transições
        - Número de retrocessos
        - Número de transições forçadas
        - Tempos em cada estado

        Target:
        - Duração total
        - Probabilidade de conclusão em X dias
        - Risco de ficar preso em estado Y
        """

    def predict_duration(self, process_data: dict) -> dict:
        """
        Prevê duração esperada de um novo processo.

        Returns:
            {
                "predicted_duration_days": 4.5,
                "confidence_interval": [3.2, 6.8],
                "confidence_level": 0.95,
                "risk_factors": [
                    {
                        "factor": "valor_total_alto",
                        "impact": "+1.2 days",
                        "explanation": "Pedidos >R$10k demoram 30% mais"
                    }
                ]
            }
        """
```

#### 5.3.2 Predição em Tempo Real

Quando um novo processo é criado, o sistema pode mostrar predições:

```
Processo Criado: Pedido #150 - XYZ Ltda

🤖 Predição de IA:

Duração Esperada: 5.2 dias (±1.5 dias)
Confiança: 92%

Fatores de Risco:
⚠️  Valor alto (R$ 12.000,00) → +1.2 dias
⚠️  Cliente novo → +0.8 dias
✅  Produto em estoque → -0.3 dias

Recomendações:
• Atenção especial ao pré-requisito "pagamento_recebido"
• Considerar solicitar adiantamento (cliente novo)
• Acionar equipe de logística com antecedência (valor alto)

Processos Similares: 12 encontrados
Média de duração: 5.5 dias
Taxa de conclusão: 91.7%
```

### 5.4 Detecção de Gargalos e Otimizações

```python
class BottleneckAnalyzer:
    """
    Analisa workflows para identificar gargalos e sugerir otimizações.
    """

    def identify_bottlenecks(self, kanban_id: str) -> dict:
        """
        Identifica gargalos no workflow.

        Analisa:
        - Estados com maior tempo médio
        - Pré-requisitos que mais atrasam
        - Transições forçadas frequentes (indicam pré-req inadequado)
        - Estados com muitos processos acumulados

        Returns:
            {
                "bottlenecks": [
                    {
                        "type": "state_duration",
                        "state": "pedido",
                        "avg_duration_hours": 48.0,
                        "target_hours": 24.0,
                        "deviation_pct": 100.0,
                        "affected_processes": 34,
                        "root_causes": [
                            {
                                "cause": "prerequisite_delay",
                                "prerequisite_id": "pagamento_recebido",
                                "avg_delay_hours": 30.0,
                                "explanation": "Clientes demoram para confirmar pagamento"
                            }
                        ],
                        "recommendations": [
                            {
                                "recommendation": "automate_payment_check",
                                "description": "Integrar com gateway de pagamento",
                                "estimated_impact": "Redução de 20 horas no tempo médio"
                            },
                            {
                                "recommendation": "add_reminder_system",
                                "description": "Enviar lembretes automáticos após 12h",
                                "estimated_impact": "Redução de 8 horas no tempo médio"
                            }
                        ]
                    }
                ]
            }
        """
```

### 5.5 Relatórios de Padrões

O sistema gera relatórios periódicos (diários, semanais, mensais) com insights:

```
╔══════════════════════════════════════════════════════════════╗
║         RELATÓRIO SEMANAL DE PADRÕES - Fluxo de Pedidos      ║
╠══════════════════════════════════════════════════════════════╣
║  Período: 20/10/2025 a 27/10/2025                            ║
║  Processos analisados: 47                                    ║
╚══════════════════════════════════════════════════════════════╝

📊 ESTATÍSTICAS GERAIS:
────────────────────────────────────────────────────────
• Processos criados:         47
• Processos concluídos:      38 (80.9%)
• Tempo médio de conclusão:  4.1 dias (meta: 5 dias) ✅
• Taxa de sucesso:           95.0% (36/38)

🎯 PADRÕES DETECTADOS:
────────────────────────────────────────────────────────
1. Padrão Principal (78% dos casos):
   Orçamento → Pedido → Entrega → Concluído
   Tempo médio: 4.1 dias

2. Padrão Rápido (15% dos casos):
   Orçamento → Pedido → Concluído
   Tempo médio: 2.3 dias
   Nota: Produtos digitais

3. Padrão com Revisão (7% dos casos):
   Orçamento ⇄ Pedido → Entrega → Concluído
   Tempo médio: 6.8 dias

⚠️  ANOMALIAS DETECTADAS:
────────────────────────────────────────────────────────
• 2 processos presos em "Pedido" há >3 dias
• 1 processo pulou de "Orçamento" para "Concluído"
  → Investigar: Possível erro ou caso especial

🚀 OTIMIZAÇÕES RECOMENDADAS:
────────────────────────────────────────────────────────
1. Estado "Pedido" (Gargalo Médio):
   - Média: 36 horas (meta: 24h)
   - Causa: Pré-requisito "pagamento_recebido"
   - Solução: Integrar API de gateway de pagamento
   - Impacto estimado: -12 horas no tempo médio

2. Transições Forçadas:
   - 5 transições forçadas esta semana
   - Mais comum: Pedido → Entrega (sem pagamento confirmado)
   - Solução: Revisar se pré-requisito é adequado
   - Considerar: Adicionar opção "pagamento_prometido"

📈 TENDÊNCIAS:
────────────────────────────────────────────────────────
• Volume de processos: ↑ 15% vs semana anterior
• Tempo médio: ↓ 0.3 dias vs semana anterior ✅
• Taxa de conclusão: ↑ 5% vs semana anterior ✅

💡 INSIGHTS DE IA:
────────────────────────────────────────────────────────
• Cliente "ACME Corp" tem padrão de pedidos grandes
  às sextas-feiras → Considerar alocação de recursos

• Produtos da categoria "Premium" demoram 40% mais
  → Investigar se precisam de fluxo separado

• Processos iniciados pela manhã (8h-12h) são 25% mais
  rápidos que os da tarde → Otimizar distribuição de tarefas

╔══════════════════════════════════════════════════════════════╗
║  Próximo relatório: 03/11/2025                               ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 6. Sistema de Agentes de IA

### 6.1 BaseAgent: Classe Abstrata para Agentes

O **BaseAgent** é a classe base para criar agentes de IA especializados por estado do Kanban.

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Classe abstrata base para agentes de IA por estado.

    Cada estado de um Kanban pode ter um agent especializado que:
    - Analisa o contexto do processo
    - Sugere transições
    - Fornece recomendações
    - Justifica decisões (obrigatório)
    """

    def __init__(self, state_id: str, kanban_id: str):
        self.state_id = state_id
        self.kanban_id = kanban_id

    @abstractmethod
    def analyze(self, process: dict, context: dict) -> dict:
        """
        Analisa um processo e retorna recomendações.

        Args:
            process: Dados completos do processo
            context: Contexto adicional:
                - historical_patterns: Padrões históricos
                - similar_processes: Processos similares
                - kanban_config: Configuração do Kanban
                - form_data: Dados do formulário original

        Returns:
            {
                "should_transition": bool,
                "target_state": str,
                "confidence": float,  # 0.0 - 1.0
                "justification": str,  # OBRIGATÓRIO
                "reasoning": list,     # Lista de raciocínios
                "recommendations": list,  # Ações sugeridas
                "risk_factors": list,   # Fatores de risco identificados
                "estimated_duration": float  # Dias esperados no próximo estado
            }
        """
        pass

    @abstractmethod
    def get_required_context(self) -> list:
        """
        Retorna lista de dados necessários para análise.

        Returns:
            ["historical_patterns", "similar_processes", "form_data"]
        """
        pass

    def load_context(self, process_id: str) -> dict:
        """
        Carrega contexto necessário para análise.

        Implementação padrão que busca:
        - Histórico do processo
        - Padrões históricos do Kanban
        - Processos similares
        - Dados do formulário original
        """
        pass
```

### 6.2 Agentes Concretos por Estado

#### 6.2.1 OrcamentoAgent (Estado: Orçamento)

```python
class OrcamentoAgent(BaseAgent):
    """
    Agent especializado para o estado "Orçamento".

    Analisa:
    - Tempo no estado
    - Valor do orçamento
    - Histórico do cliente
    - Complexidade do produto
    """

    def analyze(self, process: dict, context: dict) -> dict:
        process_data = process['process_data']
        time_in_state = self._calculate_time_in_state(process)

        # Critérios de análise
        valor = process_data.get('valor_total', 0)
        cliente = process_data.get('cliente', '')

        # Busca histórico do cliente
        client_history = context.get('client_history', [])
        avg_approval_time = self._get_avg_approval_time(client_history)

        # Decisão
        should_transition = False
        justification = []

        if time_in_state > 72:  # >3 dias
            justification.append(
                f"Processo há {time_in_state/24:.1f} dias em Orçamento"
            )

            if avg_approval_time > 0 and time_in_state > avg_approval_time * 1.5:
                justification.append(
                    f"Cliente '{cliente}' normalmente aprova em "
                    f"{avg_approval_time/24:.1f} dias. Tempo atual está "
                    f"50% acima do padrão."
                )
                should_transition = True  # Sugerir contato

        if should_transition:
            return {
                "should_transition": False,  # Não move automaticamente
                "target_state": None,
                "confidence": 0.8,
                "justification": (
                    "Processo está acima do tempo esperado para aprovação. "
                    "Recomendo contato com cliente para verificar status."
                ),
                "reasoning": justification,
                "recommendations": [
                    {
                        "action": "contact_client",
                        "description": "Enviar email de follow-up ao cliente",
                        "priority": "high"
                    },
                    {
                        "action": "review_pricing",
                        "description": "Verificar se valor está adequado ao mercado",
                        "priority": "medium"
                    }
                ],
                "risk_factors": [
                    {
                        "factor": "long_approval_time",
                        "severity": "medium",
                        "description": "Orçamentos longos têm 30% menos chance de aprovação"
                    }
                ]
            }

        return {
            "should_transition": False,
            "target_state": None,
            "confidence": 0.9,
            "justification": "Processo dentro do tempo esperado para aprovação.",
            "reasoning": [
                f"Tempo no estado: {time_in_state/24:.1f} dias",
                f"Tempo médio do cliente: {avg_approval_time/24:.1f} dias",
                "Ainda dentro do padrão normal"
            ],
            "recommendations": [],
            "risk_factors": []
        }
```

#### 6.2.2 PedidoAgent (Estado: Pedido Confirmado)

```python
class PedidoAgent(BaseAgent):
    """
    Agent para o estado "Pedido Confirmado".

    Foca em:
    - Verificação de pagamento
    - Disponibilidade de estoque
    - Prazo de entrega
    """

    def analyze(self, process: dict, context: dict) -> dict:
        process_data = process['process_data']
        time_in_state = self._calculate_time_in_state(process)

        # Verifica se pagamento foi recebido
        pagamento = process_data.get('pagamento_recebido', False)

        # Busca padrão de pagamento do cliente
        client_history = context.get('client_history', [])
        avg_payment_time = self._get_avg_payment_time(client_history)
        payment_reliability = self._get_payment_reliability(client_history)

        justification = []
        recommendations = []
        risk_factors = []

        if pagamento:
            # Pagamento confirmado: pode mover para Entrega
            return {
                "should_transition": True,
                "target_state": "entrega",
                "confidence": 0.95,
                "justification": (
                    "Pagamento confirmado. Todos pré-requisitos satisfeitos. "
                    "Processo pode avançar para 'Em Entrega'."
                ),
                "reasoning": [
                    "Pré-requisito 'pagamento_recebido' = true",
                    "Cliente tem histórico confiável de pagamentos"
                ],
                "recommendations": [
                    {
                        "action": "prepare_shipment",
                        "description": "Iniciar preparação de envio",
                        "priority": "high"
                    }
                ],
                "risk_factors": [],
                "estimated_duration": 2.5  # Dias esperados em Entrega
            }

        # Pagamento pendente
        justification.append(f"Aguardando pagamento há {time_in_state/24:.1f} dias")

        if time_in_state > avg_payment_time * 1.5:
            justification.append(
                f"Tempo acima do padrão do cliente ({avg_payment_time/24:.1f} dias)"
            )

            recommendations.append({
                "action": "send_payment_reminder",
                "description": "Enviar lembrete de pagamento ao cliente",
                "priority": "high"
            })

            if payment_reliability < 0.8:
                risk_factors.append({
                    "factor": "low_payment_reliability",
                    "severity": "high",
                    "description": (
                        f"Cliente tem apenas {payment_reliability*100:.0f}% "
                        "de confiabilidade em pagamentos"
                    )
                })
                recommendations.append({
                    "action": "escalate_to_finance",
                    "description": "Escalar para equipe financeira",
                    "priority": "high"
                })

        return {
            "should_transition": False,
            "target_state": None,
            "confidence": 0.85,
            "justification": (
                "Aguardando confirmação de pagamento. "
                f"Cliente normalmente paga em {avg_payment_time/24:.1f} dias. "
                "Recomendo acompanhamento próximo."
            ),
            "reasoning": justification,
            "recommendations": recommendations,
            "risk_factors": risk_factors,
            "estimated_duration": None
        }
```

### 6.3 Sistema de Orquestração de Agentes

```python
class AgentOrchestrator:
    """
    Orquestra a execução de agents de IA para análise de processos.

    Responsabilidades:
    - Identificar qual agent usar para cada estado
    - Carregar contexto necessário
    - Executar análise
    - Registrar resultados
    - Notificar usuários
    """

    def __init__(self):
        self.agents = self._load_agents()

    def analyze_process(self, process_id: str) -> dict:
        """
        Analisa um processo usando o agent apropriado.

        Fluxo:
        1. Carrega dados do processo
        2. Identifica estado atual
        3. Busca agent configurado para aquele estado
        4. Carrega contexto necessário
        5. Executa agent.analyze()
        6. Registra resultados
        7. Notifica usuário (se necessário)

        Returns:
            Resultados da análise do agent
        """
        repo = WorkflowRepository()
        process = repo.get_process(process_id)

        current_state = process['current_state']
        kanban_id = process['kanban_id']

        # Busca agent configurado
        agent = self._get_agent_for_state(kanban_id, current_state)

        if not agent:
            return {"status": "no_agent_configured"}

        # Carrega contexto
        context = agent.load_context(process_id)

        # Executa análise
        analysis = agent.analyze(process, context)

        # Registra resultado
        self._save_analysis(process_id, analysis)

        # Notifica usuário se houver recomendações high priority
        if self._has_high_priority_recommendations(analysis):
            self._notify_user(process, analysis)

        return analysis

    def analyze_all_active_processes(self, kanban_id: str = None):
        """
        Analisa todos os processos ativos.

        Executado periodicamente (ex: a cada hora) por um cron job.

        Se kanban_id for None, analisa todos os Kanbans.
        """
        repo = WorkflowRepository()

        # Busca processos ativos
        filters = {"status": "active"}
        if kanban_id:
            filters["kanban_id"] = kanban_id

        processes = repo.find_processes(filters)

        results = []
        for process in processes:
            try:
                analysis = self.analyze_process(process['process_id'])
                results.append({
                    "process_id": process['process_id'],
                    "status": "success",
                    "analysis": analysis
                })
            except Exception as e:
                results.append({
                    "process_id": process['process_id'],
                    "status": "error",
                    "error": str(e)
                })

        return results
```

### 6.4 Análise de Contexto

Os agents precisam de contexto rico para tomar decisões informadas:

```python
class ContextLoader:
    """
    Carrega contexto necessário para análise de agents.
    """

    def load_full_context(self, process_id: str) -> dict:
        """
        Carrega contexto completo para análise.

        Returns:
            {
                "process": { /* dados do processo */ },
                "history": [ /* histórico de transições */ ],
                "form_data": { /* dados do formulário original */ },
                "kanban_config": { /* configuração do Kanban */ },
                "historical_patterns": {
                    "common_sequences": [ ... ],
                    "avg_durations": { ... },
                    "success_rates": { ... }
                },
                "similar_processes": [
                    {
                        "process_id": "proc_xxx",
                        "similarity_score": 0.92,
                        "outcome": "success",
                        "duration_days": 4.2
                    }
                ],
                "client_history": {
                    "total_processes": 15,
                    "avg_approval_time_hours": 18.0,
                    "avg_payment_time_hours": 30.0,
                    "payment_reliability": 0.95,
                    "common_issues": []
                },
                "current_datetime": "2025-10-27T14:30:00",
                "business_rules": { /* regras de negócio */ }
            }
        """
```

### 6.5 Sugestões Inteligentes de Transição

Quando um agent sugere transição, o sistema mostra na UI:

```
┌───────────────────────────────────────────────────────────┐
│ 🤖 Sugestão de IA Agent                                   │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ Processo: Pedido #42 - ACME Corp                          │
│ Estado Atual: Pedido Confirmado                           │
│                                                           │
│ 💡 Recomendação: Mover para "Em Entrega"                 │
│ Confiança: 95%                                            │
│                                                           │
│ Justificativa:                                            │
│ Pagamento confirmado. Todos pré-requisitos satisfeitos.   │
│ Processo pode avançar para 'Em Entrega'.                  │
│                                                           │
│ Raciocínio:                                               │
│ • Pré-requisito 'pagamento_recebido' = true              │
│ • Cliente tem histórico confiável de pagamentos           │
│                                                           │
│ Próximas Ações Sugeridas:                                 │
│ 📦 Iniciar preparação de envio (alta prioridade)         │
│                                                           │
│ Duração Esperada em "Entrega": 2.5 dias                  │
│                                                           │
│ [Aceitar Sugestão] [Recusar] [Ver Análise Completa]     │
└───────────────────────────────────────────────────────────┘
```

### 6.6 Sistema de Justificativas (Obrigatório para Agentes)

**Todos os agents DEVEM fornecer justificativas** para suas decisões:

```python
# ❌ ERRADO - Sem justificativa
{
    "should_transition": True,
    "target_state": "entrega"
}

# ✅ CORRETO - Com justificativa obrigatória
{
    "should_transition": True,
    "target_state": "entrega",
    "confidence": 0.95,
    "justification": (
        "Pagamento confirmado. Todos pré-requisitos satisfeitos. "
        "Processo pode avançar para 'Em Entrega'."
    ),
    "reasoning": [
        "Pré-requisito 'pagamento_recebido' = true",
        "Cliente tem histórico confiável de pagamentos",
        "Estoque disponível confirmado"
    ]
}
```

**Benefícios:**

- **Transparência**: Usuários entendem por que IA sugeriu algo
- **Confiança**: Decisões explicáveis aumentam confiança no sistema
- **Auditoria**: Todas decisões de IA são rastreáveis
- **Aprendizado**: Equipe aprende com raciocínio da IA
- **Debug**: Facilita identificar problemas no agent

---

## 7. AutoTransitionEngine Detalhado

### 7.1 3 Tipos de Transição

O sistema suporta três tipos distintos de transição:

```
+----------------------------------------------------------------+
|                    Tipos de Transição                          |
+----------------------------------------------------------------+
|                                                                |
|  1. MANUAL (Usuário)                                           |
|     - Usuário arrasta card no Kanban                           |
|     - Usuário clica botão "Mover para X"                       |
|     - Justificativa opcional (obrigatória se forced)           |
|     - Actor: ID do usuário                                     |
|                                                                |
|  2. SYSTEM (Automática)                                        |
|     - Disparada quando pré-requisitos são satisfeitos          |
|     - Executa automaticamente, sem intervenção                 |
|     - Justificativa: Qual pré-requisito foi satisfeito         |
|     - Actor: "system"                                          |
|                                                                |
|  3. AGENT (IA)                                                 |
|     - IA Agent analisa e sugere transição                      |
|     - Pode ser automática ou requerer aprovação                |
|     - Justificativa SEMPRE obrigatória                         |
|     - Actor: ID do agent (ex: "PedidoAgent")                   |
|                                                                |
+----------------------------------------------------------------+
```

**Tabela comparativa:**

| Aspecto | Manual | System | Agent |
|---------|--------|--------|-------|
| **Iniciador** | Usuário humano | AutoTransitionEngine | IA Agent |
| **Justificativa** | Opcional* | Automática | Obrigatória |
| **Aprovação** | Não requer | Não requer | Configurável |
| **Pré-requisitos** | Avisa, não bloqueia | Aguarda satisfação | Analisa contexto |
| **Registro** | actor_type: "user" | actor_type: "auto_transition" | actor_type: "agent" |

*Obrigatória se houver avisos de pré-requisitos não satisfeitos

### 7.2 Progressão em Cascata (Transições Automáticas Sequenciais)

O AutoTransitionEngine pode mover um processo por **múltiplos estados em sequência** se todos os pré-requisitos estiverem satisfeitos:

```
Cenário: Todos pré-requisitos satisfeitos de uma vez

Estado Inicial: Orçamento

Pré-requisitos:
- Pedido: aprovado_cliente = true
- Entrega: pagamento_recebido = true
- Concluído: (nenhum)

Usuário edita formulário e marca:
- [x] aprovado_cliente
- [x] pagamento_recebido

AutoTransitionEngine executa:

1. Verifica pré-requisitos de "Pedido"
   → aprovado_cliente = true ✅
   → Move: Orçamento → Pedido

2. Verifica pré-requisitos de "Entrega"
   → pagamento_recebido = true ✅
   → Move: Pedido → Entrega

3. Verifica pré-requisitos de "Concluído"
   → Nenhum pré-requisito
   → NÃO move automaticamente (precisa de ação manual)

Resultado:
- Processo salta de "Orçamento" para "Entrega" automaticamente
- 2 transições registradas no histórico
- Tempo total: <1 segundo
```

**Implementação:**

```python
class AutoTransitionEngine:

    def check_and_transition(self, process_id: str, max_cascade: int = 3):
        """
        Verifica e executa transições automáticas em cascata.

        Args:
            process_id: ID do processo
            max_cascade: Limite de transições em cascata (segurança)
        """
        cascade_count = 0

        while cascade_count < max_cascade:
            # Carrega processo atual
            process = self.repo.get_process(process_id)
            current_state = process['current_state']
            kanban = self.repo.get_kanban(process['kanban_id'])

            # Encontra próximo estado
            next_state = self._get_next_state(kanban, current_state)

            if not next_state:
                # Não há próximo estado (fim do workflow)
                break

            # Verifica pré-requisitos
            checker = PrerequisiteChecker()
            results = checker.check_all(process, next_state.get('prerequisites', []))

            if not results.all_satisfied:
                # Pré-requisitos não satisfeitos, para aqui
                break

            # Move automaticamente
            self.transition_handler.transition(
                process_id=process_id,
                to_state=next_state['id'],
                actor="system",
                actor_type="auto_transition",
                trigger="prerequisite_met",
                metadata={
                    "prerequisites_checked": results.details,
                    "cascade_level": cascade_count + 1
                }
            )

            cascade_count += 1

            # Log
            logger.info(
                f"Auto-transition cascade {cascade_count}: "
                f"{current_state} → {next_state['id']} for process {process_id}"
            )
```

**Limite de segurança:**

Para evitar loops infinitos, há um limite de 3 transições em cascata por padrão. Configurável por Kanban:

```json
{
  "auto_transition_config": {
    "enable_cascade": true,
    "max_cascade_depth": 3,
    "cascade_delay_ms": 100
  }
}
```

### 7.3 Prerequisites por Estado (Não-bloqueantes)

Cada estado pode ter múltiplos pré-requisitos de diferentes tipos:

```json
{
  "id": "entrega",
  "name": "Em Entrega",
  "prerequisites": [
    {
      "id": "pagamento_confirmado",
      "name": "Pagamento Confirmado",
      "type": "field_check",
      "field": "pagamento_recebido",
      "condition": "equals",
      "value": true,
      "blocking": false,
      "message": "Aguardando confirmação de pagamento"
    },
    {
      "id": "estoque_disponivel",
      "name": "Estoque Disponível",
      "type": "external_api",
      "api_endpoint": "https://api.erp.com/check_stock",
      "api_method": "POST",
      "api_payload": {
        "produto_id": "{process_data.produto_id}",
        "quantidade": "{process_data.quantidade}"
      },
      "expected_response": {"available": true},
      "blocking": false,
      "message": "Produto fora de estoque"
    },
    {
      "id": "tempo_minimo_pedido",
      "name": "Tempo Mínimo em Pedido",
      "type": "time_elapsed",
      "from_state": "pedido",
      "min_hours": 24,
      "blocking": false,
      "message": "Pedido precisa estar há pelo menos 24h confirmado"
    },
    {
      "id": "aprovacao_gerente",
      "name": "Aprovação do Gerente (Pedidos >R$10k)",
      "type": "custom_script",
      "script_path": "scripts/check_manager_approval.py",
      "condition": "{process_data.valor_total} > 10000",
      "blocking": false,
      "message": "Pedidos acima de R$10k requerem aprovação do gerente"
    }
  ]
}
```

#### 7.3.1 Tipo: field_check

```python
{
  "type": "field_check",
  "field": "aprovado_cliente",
  "condition": "equals",  # equals, not_equals, greater_than, less_than, contains, not_empty
  "value": true,
  "blocking": false,
  "message": "Aguardando aprovação do cliente"
}
```

**Condições suportadas:**

- `equals`: Campo é igual ao valor
- `not_equals`: Campo é diferente do valor
- `greater_than`: Campo > valor (numérico)
- `less_than`: Campo < valor (numérico)
- `greater_or_equal`: Campo >= valor
- `less_or_equal`: Campo <= valor
- `contains`: Campo contém substring (string)
- `not_empty`: Campo não está vazio
- `is_true`: Campo é verdadeiro (boolean)
- `is_false`: Campo é falso (boolean)

#### 7.3.2 Tipo: external_api

```python
{
  "type": "external_api",
  "api_endpoint": "https://api.sistema.com/verificar",
  "api_method": "POST",  # GET, POST, PUT
  "api_headers": {
    "Authorization": "Bearer ${API_TOKEN}",
    "Content-Type": "application/json"
  },
  "api_payload": {
    "field1": "{process_data.campo1}",
    "field2": "{process_data.campo2}"
  },
  "expected_response": {"status": "ok"},
  "timeout_seconds": 5,
  "blocking": false,
  "message": "Aguardando verificação externa"
}
```

**Substituição de variáveis:**

- `{process_data.campo}`: Substitui por valor do process_data
- `${ENV_VAR}`: Substitui por variável de ambiente
- `{process_id}`: Substitui por ID do processo
- `{current_state}`: Substitui por estado atual

#### 7.3.3 Tipo: time_elapsed

```python
{
  "type": "time_elapsed",
  "from_state": "pedido",  # Opcional: estado específico
  "from_transition": "last",  # last, first, created
  "min_hours": 24,
  "max_hours": 168,  # Opcional: alerta se exceder
  "blocking": false,
  "message": "Aguardando tempo mínimo de processamento"
}
```

**Variações:**

```python
# Tempo desde criação do processo
{
  "type": "time_elapsed",
  "from_transition": "created",
  "min_hours": 48
}

# Tempo desde última transição
{
  "type": "time_elapsed",
  "from_transition": "last",
  "min_hours": 2
}

# Tempo no estado específico
{
  "type": "time_elapsed",
  "from_state": "orcamento",
  "min_hours": 12,
  "max_hours": 72  # Alerta se exceder
}
```

#### 7.3.4 Tipo: custom_script

```python
{
  "type": "custom_script",
  "script_path": "scripts/prerequisites/check_approval.py",
  "condition": "{process_data.valor_total} > 5000",  # Quando executar
  "script_args": {
    "process_id": "{process_id}",
    "valor": "{process_data.valor_total}"
  },
  "expected_return": {"approved": true},
  "timeout_seconds": 10,
  "blocking": false,
  "message": "Aguardando script de validação customizado"
}
```

**Exemplo de script:**

```python
# scripts/prerequisites/check_approval.py

import sys
import json

def check_approval(process_id, valor):
    """
    Verifica se processo foi aprovado por gerente.

    Returns:
        {"approved": bool, "approver": str, "timestamp": str}
    """
    # Consulta sistema externo ou banco de dados
    # ...

    return {
        "approved": True,
        "approver": "gerente@empresa.com",
        "timestamp": "2025-10-27T10:30:00"
    }

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    result = check_approval(args['process_id'], args['valor'])
    print(json.dumps(result))
```

### 7.4 Lógica de Auto-Progressão

```python
class PrerequisiteChecker:
    """
    Verifica pré-requisitos de um estado.
    """

    def check_all(self, process: dict, prerequisites: list) -> CheckResult:
        """
        Verifica todos os pré-requisitos de um estado.

        Returns:
            CheckResult com:
            - all_satisfied: bool
            - satisfied: list de pré-requisitos satisfeitos
            - not_satisfied: list de pré-requisitos não satisfeitos
            - details: dict com detalhes de cada verificação
        """
        results = []

        for prereq in prerequisites:
            prereq_type = prereq['type']

            if prereq_type == 'field_check':
                result = self._check_field(process, prereq)
            elif prereq_type == 'external_api':
                result = self._check_api(process, prereq)
            elif prereq_type == 'time_elapsed':
                result = self._check_time(process, prereq)
            elif prereq_type == 'custom_script':
                result = self._check_script(process, prereq)
            else:
                result = PrereqResult(
                    prereq_id=prereq['id'],
                    satisfied=False,
                    error=f"Unknown prerequisite type: {prereq_type}"
                )

            results.append(result)

        all_satisfied = all(r.satisfied for r in results)

        return CheckResult(
            all_satisfied=all_satisfied,
            satisfied=[r for r in results if r.satisfied],
            not_satisfied=[r for r in results if not r.satisfied],
            details={r.prereq_id: r.to_dict() for r in results}
        )

    def _check_field(self, process: dict, prereq: dict) -> PrereqResult:
        """Verifica pré-requisito do tipo field_check."""
        field_name = prereq['field']
        condition = prereq['condition']
        expected_value = prereq['value']

        # Busca valor em process_data
        actual_value = process['process_data'].get(field_name)

        # Avalia condição
        satisfied = self._evaluate_condition(
            actual_value,
            condition,
            expected_value
        )

        return PrereqResult(
            prereq_id=prereq['id'],
            satisfied=satisfied,
            actual_value=actual_value,
            expected_value=expected_value,
            message=prereq.get('message', '')
        )
```

### 7.5 Timeout Handlers

Estados podem ter timeouts configurados para dispara ações automáticas:

```json
{
  "id": "orcamento",
  "name": "Orçamento",
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
        "message": "Orçamento sem resposta há 3 dias",
        "auto_transition_to": null  # Ou estado específico
      }
    },
    {
      "id": "cancelar_168h",
      "hours": 168,  # 7 dias
      "action": "auto_transition",
      "target_state": "cancelado",
      "justification": "Orçamento expirado após 7 dias sem resposta"
    }
  ]
}
```

**Ações suportadas:**

- `send_notification`: Envia notificação (email, SMS, push)
- `escalate`: Escala para supervisor/gerente
- `auto_transition`: Move automaticamente para outro estado
- `run_script`: Executa script customizado
- `call_webhook`: Chama webhook externo

### 7.6 Diagrama de Estados e Transições

```
+------------------------------------------------------------------+
|              Diagrama de Estados: Fluxo de Pedidos               |
+------------------------------------------------------------------+

    [Início]
       |
       v
+-------------+
| Orçamento   |
|             |
| Timeout:    |
| • 24h: ✉️    |
| • 72h: ⚠️    |
| • 168h: ❌   |
+-------------+
       |
       | Manual/System
       | Pré-req: aprovado_cliente = true
       v
+-------------+
|   Pedido    |
| Confirmado  |
|             |
| Agent: ✅    |
| Pré-req:    |
| • pagamento |
| • estoque   |
+-------------+
       |
       | System (auto)
       | Pré-req: pagamento_recebido = true
       v
+-------------+
| Em Entrega  |
|             |
| Timeout:    |
| • 120h: ⚠️   |
+-------------+
       |
       | Manual
       | Sem pré-req
       v
+-------------+
| Concluído   |
| (Final)     |
+-------------+
       |
       v
    [Fim]

Legenda:
✉️  = Notificação
⚠️  = Escalação
❌  = Cancelamento automático
✅  = Agent de IA ativo
```

---

## 8. Dashboard de Analytics

### 8.1 Métricas por Kanban

O Dashboard fornece visão completa das métricas de cada Kanban:

```
+------------------------------------------------------------------+
|         Dashboard de Analytics - Fluxo de Pedidos                |
+------------------------------------------------------------------+
|  Período: Últimos 30 dias                                        |
+------------------------------------------------------------------+

📊 MÉTRICAS PRINCIPAIS:
──────────────────────────────────────────────────────────────────

Tempo Médio por Estado:
  Orçamento:          18.5 horas  (meta: 24h)  ✅
  Pedido Confirmado:  36.0 horas  (meta: 24h)  🔴
  Em Entrega:         48.0 horas  (meta: 48h)  ✅
  Concluído:          -

Taxa de Conclusão:
  Processos iniciados:     207
  Processos concluídos:    162
  Taxa de conclusão:       78.3%

  Abandonados:             12 (5.8%)
  Em andamento:            33 (15.9%)

Gargalos Identificados:
  🔴 Estado "Pedido": 36h (50% acima da meta)
     Causa: Pré-requisito "pagamento_recebido" demora 30h
     Impacto: 34 processos afetados

  🟡 Estado "Orçamento": 15 processos há >48h
     Causa: Aguardando aprovação de clientes
     Impacto: R$ 45.000,00 em orçamentos pendentes

Volume de Processos:
  Total no período:        207
  Média diária:            6.9
  Pico máximo:             15 (23/10/2025)
  Vale mínimo:             2 (29/10/2025 - domingo)

  Por tipo:
    Pedidos normais:       180 (87%)
    Pedidos urgentes:      27 (13%)
```

### 8.2 Gráficos

#### 8.2.1 Funil de Conversão

```
Funil de Conversão - Fluxo de Pedidos
(Últimos 30 dias)

Orçamento          207  ████████████████████████████████  100%
    |
    v (78.3%)
Pedido             162  █████████████████████████         78.3%
    |
    v (93.8%)
Em Entrega         152  ███████████████████████           73.4%
    |
    v (94.7%)
Concluído          144  ██████████████████████            69.6%

Abandonos por Estado:
• Orçamento → Cancelado:      45 processos (21.7%)
• Pedido → Cancelado:         10 processos (4.8%)
• Entrega → Devolvido:        8 processos (3.9%)

Taxa de Sucesso Final: 69.6%
```

#### 8.2.2 Linha do Tempo

```
Volume de Processos Criados - Outubro 2025

20 |                                    ╭──╮
   |                                    │  │
15 |                          ╭──╮     │  │
   |                          │  │     │  │  ╭─╮
10 |        ╭──╮    ╭──╮     │  │ ╭─╮ │  │  │ │
   |   ╭─╮  │  │ ╭─╮│  │  ╭─╮│  │ │ │╭╯  │╭─╯ │
 5 |╭─╮│ │  │  │ │ ││  │  │ ││  │ │ ││   ││   │
   |│ ││ │ ╭╯  │ │ ││  │╭─╯ ╰╯  │ │ ││   ││   │
 0 |╰─╯╰─╯ ╰───╯ ╰─╯╰──╯╰───────╯ ╰─╯╰───╯╰───╯
   +--------------------------------------------------
    1  3  5  7  9  11 13 15 17 19 21 23 25 27 29 31

Tendência: ↗️ Crescimento de 15% vs período anterior
Previsão próximos 7 dias: 52 processos
```

#### 8.2.3 Heatmap de Transições

```
Heatmap de Transições - Fluxo de Pedidos
(Intensidade representa volume)

            Para Estado:
            Orç   Ped   Ent   Con   Can
De Estado:
Orçamento   -    █ 162  ▓ 5   ░ 0   █ 45
Pedido     ▓ 8    -     █152  ░ 2   ▓ 10
Entrega    ░ 0   ▓ 4     -    █144  ▓ 8
Concluído  ░ 0   ░ 0   ░ 1     -    ░ 0

Legenda:
█ = Alto volume (>100)
▓ = Médio volume (10-99)
░ = Baixo volume (1-9)
- = Impossível

Anomalias Detectadas:
⚠️  Entrega → Concluído: 1 transição reversa (investigar)
⚠️  Orçamento → Entrega: 5 transições pulando "Pedido"
```

#### 8.2.4 Distribuição por Estado (Estado Atual)

```
Distribuição Atual de Processos

Orçamento:       15  ████████                23%
Pedido:          12  ██████                  18%
Em Entrega:      6   ███                     9%
Concluído:       144 ████████████████████    69%  (últimos 30 dias)
Cancelado:       30  █████                   14%  (últimos 30 dias)

Total em Andamento: 33 processos
Capacidade: 50 processos (66% utilizada)

Alertas:
🟡 15 processos em "Orçamento" (capacidade OK, mas monitorar)
✅ 12 processos em "Pedido" (dentro do normal)
✅ 6 processos em "Entrega" (dentro do normal)
```

### 8.3 KPIs Configuráveis

Cada Kanban pode ter KPIs personalizados:

```json
{
  "kpis": [
    {
      "id": "tempo_medio_conclusao",
      "name": "Tempo Médio de Conclusão",
      "description": "Tempo desde criação até conclusão",
      "calculation": "avg_duration_from_created_to_completed",
      "unit": "days",
      "target_value": 5.0,
      "warning_threshold": 6.0,
      "critical_threshold": 8.0,
      "chart_type": "line"
    },
    {
      "id": "taxa_conversao",
      "name": "Taxa de Conversão (Orçamento → Pedido)",
      "description": "% de orçamentos que viram pedidos",
      "calculation": "conversion_rate",
      "from_state": "orcamento",
      "to_state": "pedido",
      "unit": "percentage",
      "target_value": 75.0,
      "warning_threshold": 65.0,
      "critical_threshold": 50.0,
      "chart_type": "gauge"
    },
    {
      "id": "valor_medio_pedido",
      "name": "Valor Médio por Pedido",
      "description": "Média do campo valor_total",
      "calculation": "avg_field_value",
      "field": "valor_total",
      "unit": "currency",
      "target_value": 2000.0,
      "chart_type": "number"
    },
    {
      "id": "volume_semanal",
      "name": "Volume Semanal de Processos",
      "description": "Novos processos por semana",
      "calculation": "count_by_period",
      "period": "week",
      "unit": "count",
      "target_value": 50,
      "chart_type": "bar"
    }
  ]
}
```

**Visualização de KPI:**

```
┌─────────────────────────────────────────┐
│ Tempo Médio de Conclusão                │
├─────────────────────────────────────────┤
│                                         │
│          4.2 dias                       │
│                                         │
│  ┌───────────────────────────┐          │
│  │▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░        │          │
│  └───────────────────────────┘          │
│  0        5 (meta)          10          │
│                                         │
│  ✅ 16% abaixo da meta                 │
│  ↗️ Melhorou 0.3 dias vs semana passada │
│                                         │
└─────────────────────────────────────────┘
```

### 8.4 Filtros por Período, Kanban, Estado

```
+------------------------------------------------------------------+
|  📊 Dashboard de Analytics                                       |
+------------------------------------------------------------------+
|                                                                  |
|  Filtros:                                                        |
|  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐           |
|  │ Kanban:     │  │ Período:     │  │ Estado:      │           |
|  │ [Todos   ▼]│  │ [30 dias  ▼] │  │ [Todos    ▼] │           |
|  └─────────────┘  └──────────────┘  └──────────────┘           |
|                                                                  |
|  Opções de Período:                                              |
|  • Hoje                                                          |
|  • Últimos 7 dias                                                |
|  • Últimos 30 dias                                               |
|  • Este mês                                                      |
|  • Mês passado                                                   |
|  • Últimos 3 meses                                               |
|  • Este ano                                                      |
|  • Personalizado (data início - data fim)                        |
|                                                                  |
|  Opções de Kanban:                                               |
|  • Todos                                                         |
|  • Fluxo de Pedidos                                              |
|  • Gestão de Projetos                                            |
|  • RH - Contratação                                              |
|                                                                  |
|  Opções de Estado:                                               |
|  • Todos                                                         |
|  • Apenas ativos (excluir concluídos/cancelados)                 |
|  • Por estado específico                                         |
|                                                                  |
+------------------------------------------------------------------+
```

---

## Conclusão da Parte 1

Esta primeira parte apresentou os **fundamentos e arquitetura core** do Sistema de Workflow Kanban v4.0:

✅ **Conceitos Fundamentais**: Kanban como definidor de workflow, filosofia "Avisar, Não Bloquear"

✅ **Arquitetura de Vinculação**: KanbanRegistry, FormTriggerManager, ProcessFactory

✅ **Persistência Plugável**: TXT como padrão (sem banco obrigatório), suporte a múltiplos backends

✅ **Fluxos de Usuário Completos**: Criação via Kanban ou Form, transições Manual/System/Agent

✅ **IA - PatternAnalyzer**: Detecção de padrões comuns, raros, clustering de processos similares

✅ **IA - AnomalyDetector**: Identificação de processos presos, transições anômalas

✅ **Agentes de IA**: BaseAgent, agents por estado, orquestração, justificativas obrigatórias

✅ **AutoTransitionEngine**: 3 tipos de transição, cascata, pré-requisitos, timeouts

✅ **Dashboard de Analytics**: Métricas, gráficos, KPIs configuráveis, filtros

---

**Continua na Parte 2:**

- **Seção 9**: Editor Visual de Kanbans (Área Admin)
- **Seção 10**: Exportações e Relatórios
- **Seção 11**: Interface de Auditoria Visual
- **Seção 12**: Arquitetura Técnica Completa
- **Seção 13**: Exemplo Completo - Fluxo de Pedidos (Detalhado)
- **Seção 14**: Fases de Implementação (5 Fases MVP)
- **Seção 15**: Estratégia de Testes

---

**Elaborado por:** Rodrigo Santista
**Com assistência de:** Claude Code (Anthropic)
**Data:** Outubro 2025
**Versão:** 4.0 - Parte 1 de 3
