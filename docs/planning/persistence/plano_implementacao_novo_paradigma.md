# Plano de Implementação: Novo Paradigma de Persistência VibeCForms

**Data**: 2026-01-27
**Versão**: 2.1 (Greenfield - AI Agents)
**Status**: Aguardando Aprovação

---

## Sumário Executivo

Este plano implementa o **Modelo Híbrido Simplificado** de persistência como uma **implementação greenfield** (novo sistema do zero), conforme recomendado no documento `analise_comparativa_paradigma_relacional.md`.

### ⚠️ Escopo: Greenfield (Sem Retrocompatibilidade)

**Este plano NÃO inclui:**
- Migração de dados existentes
- Compatibilidade com campos `search+datasource` legados
- Scripts de migração de specs existentes
- Renomeação de tabelas/arquivos existentes

**A migração de definições e dados existentes será tratada em uma tarefa separada.**

### Características do Novo Modelo

1. **Tabelas específicas por relacionamento** (`rel_{source}_{type}_{target}`) - Convenção #1 respeitada
2. **Audit trail básico** (created_at, created_by, removed_at, removed_by)
3. **Soft delete** via campo `removed_at`
4. **Sincronização sempre EAGER** (simplificado)
5. **Suporte multi-formato** (TXT, JSON, CSV, XML, SQLite, MySQL, PostgreSQL, MongoDB)

### Diferenças do Modelo Anterior (Tabela Universal)

| Aspecto | Modelo Anterior | Novo Modelo |
|---------|-----------------|-------------|
| Tabela de relacionamentos | Universal (`relationships`) | Específica (`rel_{source}_{type}_{target}`) |
| Display values | Prefixo `_campo_display` | Valores reais (sem prefixo) |
| Sincronização | 3 estratégias (EAGER/LAZY/SCHEDULED) | Sempre EAGER |
| Complexidade | ~1000 linhas | ~300-400 linhas |
| Convenção #1 | Viola (tabela universal) | Respeita (tabela por tipo) |

---

## Arquitetura para Execução por AI Agents

### Padrão Orchestrator

Cada FASE utiliza o padrão **Implementation → Verification Loop**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                                                                  │
│   ┌──────────────┐                      ┌──────────────────┐    │
│   │ Implementation│───────────────────▶│    Verification   │    │
│   │    Agent      │                     │      Agent        │    │
│   │  (gus agent)  │◀─────────────────── │  (tir agent)      │    │
│   └──────────────┘   "NOT Good Enough"  └──────────────────┘    │
│          │                                      │                │
│          │                                      │                │
│          ▼                                      ▼                │
│   Creates/Modifies                      Returns verdict:         │
│   files based on                        - "Good Enough" → NEXT  │
│   phase requirements                    - "NOT Good Enough" +    │
│                                           specific fixes needed  │
└─────────────────────────────────────────────────────────────────┘
```

### Regras do Loop

1. **Implementação**: O `gus` agent executa a etapa
2. **Verificação**: O `tir` agent valida com critérios pragmáticos
3. **Loop**: Se "NOT Good Enough", `gus` recebe feedback específico e corrige
4. **Avanço**: Se "Good Enough", avança para próxima etapa
5. **Máximo 3 iterações** por etapa antes de escalar para humano

---

## Referências Chave do Codebase

### Arquivos Essenciais (LEITURA OBRIGATÓRIA antes de implementar)

| Arquivo | Propósito | Quando Ler |
|---------|-----------|------------|
| [base.py](src/persistence/base.py) | Interface BaseRepository com 23 métodos abstratos | FASE 1, 2, 3 |
| [factory.py](src/persistence/factory.py) | RepositoryFactory e cache de instâncias | FASE 4 |
| [sqlite_adapter.py](src/persistence/adapters/sqlite_adapter.py) | Implementação SQLite existente | FASE 3 |
| [txt_adapter.py](src/persistence/adapters/txt_adapter.py) | Implementação TXT existente | FASE 3 |
| [forms.py](src/controllers/forms.py) | Controller de formulários CRUD | FASE 4 |
| [spec_renderer.py](src/utils/spec_renderer.py) | Renderização de campos de formulário | FASE 4, 7 |
| [search_autocomplete.html](src/templates/fields/search_autocomplete.html) | Template de campo search atual | FASE 4 |

### Convenções de Código

- **Type hints**: Obrigatórios em todos os parâmetros e retornos
- **Docstrings**: Em português, estilo Google
- **Logging**: Usar `logging.getLogger(__name__)`
- **Testes**: pytest com fixtures em `tests/conftest.py`
- **IDs**: Crockford Base32, 27 caracteres (ver `src/utils/crockford.py`)

### Convenções de Relacionamentos

#### IMPORTANTE: Nomes no Singular

**Regra Fundamental**: Todos os nomes de tabelas e forms DEVEM estar no **singular**.

**Correto**:
- `pedido`, `cliente`, `produto`, `user`, `category`
- `rel_pedido_has_cliente`, `rel_user_is_a_user_type`

**Incorreto**:
- ~~`pedidos`~~, ~~`clientes`~~, ~~`produtos`~~, ~~`users`~~, ~~`categories`~~

**Motivo**: Consistência com padrões de modelagem de dados e clareza semântica (a tabela representa o conceito "pedido", não "pedidos").

#### Nomenclatura de Tabelas de Relacionamento

**Formato**: `rel_{source_table}_{relationship_type}_{target_table}`

**Tipos de Relacionamento Comuns** (graph-style, não limitados a estes):
- `has` - Relacionamento de posse/associação (ex: pedido **has** cliente)
- `is_a` - Relacionamento de classificação/tipo (ex: user **is_a** user_type)

**Exemplos**:
- `rel_pedido_has_cliente` - Pedido possui um cliente
- `rel_pedido_has_produto` - Pedido possui produtos
- `rel_user_is_a_user_type` - Usuário é de um tipo

**Domínios (Tabelas de Classe)**:
Para tabelas que representam classes/domínios (ex: "gender", "user_type", "status"), sempre usar `has`:
- `rel_user_has_gender` - Usuário tem um gênero
- `rel_product_has_category` - Produto tem uma categoria

#### Cardinalidades e Constraints

**Cardinalidades Suportadas**:
- `one-to-one` - Um source relaciona com exatamente um target
- `one-to-many` - Um source relaciona com múltiplos targets
- `many-to-one` - Múltiplos sources relacionam com um target (MAIS COMUM para domínios)
- `many-to-many` - Múltiplos sources relacionam com múltiplos targets (sem constraints)

**Constraints na Tabela de Relacionamento**:

| Cardinalidade | Constraint em `source_uuid` | Constraint em `target_uuid` |
|---------------|-----------------------------|-----------------------------|
| one-to-one    | UNIQUE                      | UNIQUE                      |
| one-to-many   | (nenhum)                    | UNIQUE                      |
| many-to-one   | UNIQUE                      | (nenhum)                    |
| many-to-many  | (nenhum)                    | (nenhum)                    |

**Nota sobre Domínios**:
Para relacionamentos com tabelas de domínio (gender, status, category), o padrão é `many-to-one`:
- Muitos `user` podem ter o mesmo `gender` → `many-to-one`
- Muitos `product` podem ter a mesma `category` → `many-to-one`

O sistema deve preferir `many-to-one` sobre `one-to-many` quando apropriado (a diferença prática é apenas a ordem dos campos na constraint).

#### Relacionamentos Reversos

Quando **duas forms definem o mesmo relacionamento** (ex: "pedido" tem campo "cliente" E "cliente" tem campo "pedidos"), **apenas UMA tabela deve ser criada**.

**Regra**: A segunda form deve usar `reverse: true` para indicar que está utilizando um relacionamento já existente.

**Exemplo - Relacionamento Direto (em pedido.json)**:
```json
{
  "name": "cliente",
  "type": "relationship",
  "target_table": "cliente",
  "relationship_table": "rel_pedido_has_cliente",
  "cardinality": "many-to-one",
  "reverse": false
}
```

**Exemplo - Relacionamento Reverso (em cliente.json)**:
```json
{
  "name": "pedidos",
  "type": "relationship",
  "target_table": "pedido",
  "relationship_table": "rel_pedido_has_cliente",
  "cardinality": "one-to-many",
  "reverse": true
}
```

**Comportamento**:
- `reverse: false` (default): Sistema cria a tabela de relacionamento se não existir
- `reverse: true`: Sistema usa tabela existente, não tenta criar

---

## FASE 1: Fundamentos e Contratos

**Objetivo**: Estabelecer interfaces, modelos e estrutura base
**Estimativa de Complexidade**: Baixa
**Dependências**: Nenhuma

### Etapa 1.1: Definir Interface IRelationshipService

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/contracts/relationship_service.py`

**Requisitos da Interface**:
- 8 métodos abstratos: `create`, `remove`, `get`, `get_reverse`, `sync_display_values`, `validate_reference`, `ensure_relationship_table`, `get_relationship_table_name`
- Herdar de `ABC`
- Type hints completos
- Docstrings em português

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/contracts/relationship_service.py`
- [ ] Contém classe `IRelationshipService` herdando de `ABC`
- [ ] Todos os 8 métodos definidos com `@abstractmethod`
- [ ] Type hints em todos os parâmetros e retornos
- [ ] `mypy --strict src/persistence/contracts/relationship_service.py` passa sem erros
- [ ] `python -c "from persistence.contracts.relationship_service import IRelationshipService"` executa sem erro

**Verdito "Good Enough" se**: Todos os 6 critérios passam.

---

### Etapa 1.2: Definir Modelos de Dados

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/models/relationship.py`

**Modelos necessários**:

1. `RelationshipRecord` (dataclass):
   - `source_uuid: str`
   - `target_uuid: str`
   - `created_at: str` (ISO 8601)
   - `created_by: Optional[str] = None`
   - `removed_at: Optional[str] = None`
   - `removed_by: Optional[str] = None`

2. `RelationshipFieldSpec` (dataclass):
   - `name: str`
   - `target_table: str` - Tabela alvo no singular (ex: "cliente")
   - `target_field: str` - Campo de identificação na tabela alvo (ex: "_record_id")
   - `relationship_type: Literal["has", "is_a", ...] = "has"` - Tipo do relacionamento (graph-style)
   - `relationship_table: Optional[str] = None` - Nome explícito da tabela de relacionamento (se None, usa convenção)
   - `reverse: bool = False` - Se True, este campo usa um relacionamento definido por outra tabela (evita duplicação)
   - `cardinality: Literal["one-to-one", "one-to-many", "many-to-one", "many-to-many"]`
   - `search_field: str`
   - `display_fields: List[str]`
   - `cascade: Literal["none", "delete", "nullify"] = "none"`
   - `required: bool = False`

**Nota sobre Cardinalidades:**
- `one-to-one`: UNIQUE em source_uuid E target_uuid
- `one-to-many`: UNIQUE apenas em target_uuid
- `many-to-one`: UNIQUE apenas em source_uuid (MAIS COMUM para domínios)
- `many-to-many`: Sem constraints

**Nota sobre Relacionamentos Reversos:**
Quando duas forms definem o mesmo relacionamento (ex: "pedido" tem "cliente" E "cliente" lista "pedidos"),
apenas UMA tabela de relacionamento deve ser criada. A segunda form deve usar `reverse: true` para indicar
que está usando um relacionamento já definido pela outra tabela.

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/models/relationship.py`
- [ ] Usa `@dataclass` decorator
- [ ] Ambos modelos definidos com campos corretos
- [ ] `from persistence.models.relationship import RelationshipRecord, RelationshipFieldSpec` funciona
- [ ] Instanciação de teste funciona: `RelationshipRecord(source_uuid="A", target_uuid="B", created_at="2026-01-01T00:00:00Z")`

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 1.3: Criar Estrutura de Diretórios e __init__.py

**Agent**: `gus`
**Ação**: CREATE múltiplos arquivos

**Diretórios e arquivos a criar**:
```
src/persistence/
├── contracts/
│   └── __init__.py           # Export: IRelationshipService
├── models/
│   └── __init__.py           # Export: RelationshipRecord, RelationshipFieldSpec
└── relationships/
    ├── __init__.py           # Export: RelationshipService
    └── adapters/
        └── __init__.py       # Export: RELATIONSHIP_ADAPTERS dict
```

**Critérios de Verificação (tir agent)**:
- [ ] Todos os diretórios existem
- [ ] Todos os `__init__.py` contêm exports apropriados
- [ ] `from persistence.contracts import IRelationshipService` funciona
- [ ] `from persistence.models import RelationshipRecord, RelationshipFieldSpec` funciona
- [ ] Nenhum import circular: `python -c "import persistence"` executa sem erro

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 1.4: Documentar Schema do Campo "relationship" no CLAUDE.md

**Agent**: `gus`
**Ação**: EDIT arquivo existente

**Arquivo a modificar**: `CLAUDE.md`

**Seção a adicionar** (após "Search with Datasource Format"):

```markdown
**IMPORTANTE: Nomes no Singular**
Todos os nomes de tabelas e forms DEVEM estar no singular: `pedido`, `cliente`, `produto` (não `pedidos`, `clientes`, `produtos`).

**Relationship Field Format:**
```json
{
  "name": "cliente",
  "label": "Cliente",
  "type": "relationship",
  "target_table": "cliente",
  "target_field": "_record_id",
  "relationship_type": "has",
  "relationship_table": "rel_pedido_has_cliente",
  "cardinality": "many-to-one",
  "search_field": "nome",
  "display_fields": ["nome", "cpf"],
  "cascade": "none",
  "required": true
}
```

**Cardinalidades e Constraints:**
- `one-to-one`: UNIQUE em source_uuid E target_uuid
- `one-to-many`: UNIQUE apenas em target_uuid
- `many-to-one`: UNIQUE apenas em source_uuid (MAIS COMUM para domínios)
- `many-to-many`: Sem constraints

**Convenção de Nome de Tabela de Relacionamento:**
- Formato: `rel_{source_table}_{relationship_type}_{target_table}` (singular!)
- Tipos comuns: "has", "is_a" (mas não limitados a estes - pense em graph relationships)
- Para domínios (tabelas de classe como "gender", "user_type"): sempre usar `rel_{source}_has_{domain}`
- Exemplo: `rel_pedido_has_cliente`, `rel_user_is_a_user_type`

**Relacionamentos Reversos:**
Quando duas forms definem o mesmo relacionamento, use `reverse: true` na segunda:
```json
{
  "name": "pedidos_do_cliente",
  "label": "Pedidos do Cliente",
  "type": "relationship",
  "target_table": "pedido",
  "target_field": "_record_id",
  "relationship_type": "has",
  "relationship_table": "rel_pedido_has_cliente",
  "reverse": true,
  "cardinality": "one-to-many"
}
```

**Comportamento:**
1. Framework detecta `type: "relationship"`
2. Se `reverse: false` (default): cria tabela `rel_{source}_{type}_{target}` (ou usa nome explícito)
3. Se `reverse: true`: usa tabela existente definida por outra form (não cria duplicada)
4. Aplica constraints conforme cardinalidade
5. Adiciona campos desnormalizados: `{name}_{display_field}` para cada display_field
6. UI renderiza componente de busca/seleção
```

**Critérios de Verificação (tir agent)**:
- [ ] CLAUDE.md contém seção "Relationship Field Format"
- [ ] Exemplo JSON está correto e válido
- [ ] Documentação do comportamento presente
- [ ] Formato markdown válido (sem erros de sintaxe)

**Verdito "Good Enough" se**: Todos os 4 critérios passam.

---

## FASE 2: Implementação Core

**Objetivo**: Implementar serviço de relacionamentos e geração de tabelas
**Estimativa de Complexidade**: Média
**Dependências**: FASE 1 completa

### Etapa 2.1: Implementar RelationshipService

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/relationships/service.py`

**Referências a consultar ANTES de implementar**:
- [base.py](src/persistence/base.py) - Interface BaseRepository
- [factory.py](src/persistence/factory.py) - Como obter repositórios
- [crockford.py](src/utils/crockford.py) - Geração de IDs

**Classe a implementar**: `RelationshipService(IRelationshipService)`

**Métodos obrigatórios**:

1. `__init__(self, repository_factory: RepositoryFactory)`
   - Recebe factory por injeção de dependência
   - Armazena referência para uso posterior

2. `create(self, source_table, source_uuid, target_table, target_uuid, relationship_type="has", relationship_table=None, created_by=None) -> bool`
   - Validar source_uuid existe via `repository.read_by_id()`
   - Validar target_uuid existe
   - Obter adapter para tabela de relacionamento
   - Determinar nome da tabela: usa `relationship_table` se fornecido, senão `rel_{source}_{type}_{target}`
   - Inserir registro com `source_uuid` e `target_uuid`
   - Buscar display values do target
   - Atualizar campos desnormalizados no source
   - Retornar sucesso/falha

3. `remove(self, source_table, source_uuid, target_table, target_uuid, relationship_type="has", relationship_table=None, removed_by=None) -> bool`
   - Soft delete via `removed_at` timestamp
   - NÃO deletar dados, apenas marcar

4. `get(self, source_table, source_uuid, target_table, relationship_type="has", relationship_table=None, active_only=True) -> List[str]`
   - Retorna lista de UUIDs dos targets relacionados
   - Filtrar por `removed_at IS NULL` se `active_only=True`

5. `get_reverse(self, target_table, target_uuid, source_table, relationship_type="has", relationship_table=None, active_only=True) -> List[str]`
   - Busca reversa (target → sources)

9. `get_relationship_table_name(self, source_table, target_table, relationship_type="has", relationship_table=None) -> str`
   - Se `relationship_table` fornecido, retorna ele diretamente
   - Senão, retorna convenção: `rel_{source}_{type}_{target}`

6. `sync_display_values(self, source_table, source_id, spec) -> bool`
   - Ler spec para identificar display_fields
   - Buscar valores atuais do target
   - Atualizar campos desnormalizados no source

7. `validate_reference(self, target_table, target_id) -> bool`
   - Verificar se record existe
   - Usar `repository.read_by_id()`

8. `ensure_relationship_table(self, source_table, target_table) -> bool`
   - Criar tabela `r{source}_{target}` se não existir
   - Delegar para TableGenerator

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/relationships/service.py`
- [ ] Classe implementa `IRelationshipService`
- [ ] Todos os 9 métodos implementados (não apenas assinaturas)
- [ ] Logging estratégico presente (mínimo: log de create e remove)
- [ ] `from persistence.relationships.service import RelationshipService` funciona
- [ ] Não há `pass` statements em métodos (implementação real)

**Verdito "Good Enough" se**: Todos os 6 critérios passam.

---

### Etapa 2.2: Implementar TableGenerator

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/relationships/table_generator.py`

**Classe a implementar**: `TableGenerator`

**Métodos obrigatórios**:

1. `generate_table_name(source_table: str, target_table: str, relationship_type: str = "has") -> str`
   - Retorna: `rel_{source}_{type}_{target}` (normalizado, lowercase, sem caracteres especiais)
   - Tipos comuns: "has", "is_a" (mas pode aceitar qualquer tipo graph-style)

2. `get_relationship_schema() -> Dict`
   - Retorna schema padrão para tabelas de relacionamento:
   ```python
   {
       "fields": [
           {"name": "source_uuid", "type": "text", "required": True},
           {"name": "target_uuid", "type": "text", "required": True},
           {"name": "created_at", "type": "text", "required": True},
           {"name": "created_by", "type": "text", "required": False},
           {"name": "removed_at", "type": "text", "required": False},
           {"name": "removed_by", "type": "text", "required": False},
       ]
   }
   ```

3. `create_relationship_table(repository: BaseRepository, source_table: str, target_table: str, relationship_type: str = "has", cardinality: str = "many-to-one", relationship_table: str = None) -> bool`
   - Gera nome da tabela (usa `relationship_table` se fornecido, senão convenção)
   - Verifica se é relacionamento reverso (se tabela já existe, não cria duplicada)
   - Cria via `repository.create_storage()`
   - Aplica constraints de cardinalidade:
     - `one-to-one`: UNIQUE em source_uuid E target_uuid
     - `one-to-many`: UNIQUE apenas em target_uuid
     - `many-to-one`: UNIQUE apenas em source_uuid
     - `many-to-many`: Sem constraints adicionais
   - Cria índices: `source_uuid`, `target_uuid`, `(source_uuid, removed_at)`

4. `get_denormalized_field_names(relationship_name: str, display_fields: List[str]) -> List[str]`
   - Retorna: `["{relationship_name}_{field}" for field in display_fields]`
   - Ex: `["cliente_nome", "cliente_cpf"]`

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/relationships/table_generator.py`
- [ ] `generate_table_name("pedido", "cliente")` retorna `"rel_pedido_has_cliente"`
- [ ] `generate_table_name("pedido", "cliente", "has")` retorna `"rel_pedido_has_cliente"`
- [ ] `generate_table_name("user", "user_type", "is_a")` retorna `"rel_user_is_a_user_type"`
- [ ] `get_denormalized_field_names("cliente", ["nome", "cpf"])` retorna `["cliente_nome", "cliente_cpf"]`
- [ ] Schema contém os 6 campos obrigatórios (source_uuid, target_uuid, created_at, created_by, removed_at, removed_by)
- [ ] Import funciona: `from persistence.relationships.table_generator import TableGenerator`

**Verdito "Good Enough" se**: Todos os 7 critérios passam.

---

## FASE 3: Adapters de Persistência

**Objetivo**: Implementar adapters para SQLite e TXT
**Estimativa de Complexidade**: Média-Alta
**Dependências**: FASE 2 completa

### Etapa 3.1: Implementar BaseRelationshipAdapter

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/relationships/adapters/base_relationship_adapter.py`

**Referência obrigatória**: [base.py](src/persistence/base.py) - Padrão de interface abstrata

**Classe a implementar**: `BaseRelationshipAdapter(ABC)`

**Métodos abstratos** (7 total):

```python
@abstractmethod
def create_table(self, source_table: str, target_table: str) -> bool

@abstractmethod
def insert(self, table_name: str, record: RelationshipRecord) -> bool

@abstractmethod
def soft_delete(self, table_name: str, source_uuid: str, target_uuid: str, removed_by: str) -> bool

@abstractmethod
def select_by_source(self, table_name: str, source_uuid: str, active_only: bool = True) -> List[str]

@abstractmethod
def select_by_target(self, table_name: str, target_uuid: str, active_only: bool = True) -> List[str]

@abstractmethod
def exists(self, table_name: str, source_uuid: str, target_uuid: str) -> bool

@abstractmethod
def table_exists(self, table_name: str) -> bool
```

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/relationships/adapters/base_relationship_adapter.py`
- [ ] Classe herda de `ABC`
- [ ] Todos os 7 métodos definidos com `@abstractmethod`
- [ ] Type hints completos em todos os métodos
- [ ] Import funciona

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 3.2: Implementar SQLiteRelationshipAdapter

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/relationships/adapters/sqlite_relationship_adapter.py`

**Referência OBRIGATÓRIA antes de implementar**: [sqlite_adapter.py](src/persistence/adapters/sqlite_adapter.py)

**Padrões a seguir do sqlite_adapter existente**:
- Usar `sqlite3.connect()` com timeout de 10 segundos
- Queries parametrizadas com `?` (NUNCA string interpolation)
- Context manager para conexões
- Transações para operações compostas

**Schema SQL da tabela** (base, sem constraints de cardinalidade):
```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    source_uuid TEXT NOT NULL,
    target_uuid TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT,
    removed_at TEXT,
    removed_by TEXT,
    PRIMARY KEY (source_uuid, target_uuid)
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_source ON {table_name}(source_uuid);
CREATE INDEX IF NOT EXISTS idx_{table_name}_target ON {table_name}(target_uuid);
CREATE INDEX IF NOT EXISTS idx_{table_name}_active ON {table_name}(source_uuid) WHERE removed_at IS NULL;
```

**Constraints de Cardinalidade** (adicionais ao schema base):
```sql
-- one-to-one: UNIQUE em ambos
CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_source_unique ON {table_name}(source_uuid) WHERE removed_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_target_unique ON {table_name}(target_uuid) WHERE removed_at IS NULL;

-- one-to-many: UNIQUE apenas em target
CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_target_unique ON {table_name}(target_uuid) WHERE removed_at IS NULL;

-- many-to-one: UNIQUE apenas em source (MAIS COMUM para domínios)
CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_source_unique ON {table_name}(source_uuid) WHERE removed_at IS NULL;

-- many-to-many: Sem constraints adicionais
```

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/relationships/adapters/sqlite_relationship_adapter.py`
- [ ] Herda de `BaseRelationshipAdapter`
- [ ] Todos os 7 métodos implementados (não apenas herdados)
- [ ] Usa `?` para parâmetros SQL (grep por `%s` ou `f"` + SQL deve retornar vazio)
- [ ] Trata exceções `sqlite3.Error` apropriadamente
- [ ] Import funciona: `from persistence.relationships.adapters.sqlite_relationship_adapter import SQLiteRelationshipAdapter`

**Verdito "Good Enough" se**: Todos os 6 critérios passam.

---

### Etapa 3.3: Implementar TxtRelationshipAdapter

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/persistence/relationships/adapters/txt_relationship_adapter.py`

**Referência OBRIGATÓRIA antes de implementar**: [txt_adapter.py](src/persistence/adapters/txt_adapter.py)

**Formato de arquivo**:
```
source_uuid;target_uuid;created_at;created_by;removed_at;removed_by
ABC123;CLI456;2026-01-27T10:30:00Z;user1;;
DEF789;CLI456;2026-01-27T11:00:00Z;user2;2026-01-27T12:00:00Z;user2
```

**Padrões a seguir do txt_adapter existente**:
- Delimitador: `;`
- Encoding: `utf-8`
- Primeira linha é header
- Campos vazios representados por string vazia

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `src/persistence/relationships/adapters/txt_relationship_adapter.py`
- [ ] Herda de `BaseRelationshipAdapter`
- [ ] Todos os 7 métodos implementados
- [ ] Usa `;` como delimitador (consistente com txt_adapter.py)
- [ ] Escreve header na primeira linha ao criar arquivo
- [ ] Import funciona

**Verdito "Good Enough" se**: Todos os 6 critérios passam.

---

### Etapa 3.4: Registrar Adapters no __init__.py

**Agent**: `gus`
**Ação**: EDIT arquivo

**Arquivo a modificar**: `src/persistence/relationships/adapters/__init__.py`

**Conteúdo**:
```python
from .base_relationship_adapter import BaseRelationshipAdapter
from .sqlite_relationship_adapter import SQLiteRelationshipAdapter
from .txt_relationship_adapter import TxtRelationshipAdapter

RELATIONSHIP_ADAPTERS = {
    "sqlite": SQLiteRelationshipAdapter,
    "txt": TxtRelationshipAdapter,
}

__all__ = [
    "BaseRelationshipAdapter",
    "SQLiteRelationshipAdapter",
    "TxtRelationshipAdapter",
    "RELATIONSHIP_ADAPTERS",
]
```

**Critérios de Verificação (tir agent)**:
- [ ] `from persistence.relationships.adapters import RELATIONSHIP_ADAPTERS` funciona
- [ ] `RELATIONSHIP_ADAPTERS["sqlite"]` retorna a classe correta
- [ ] `RELATIONSHIP_ADAPTERS["txt"]` retorna a classe correta

**Verdito "Good Enough" se**: Todos os 3 critérios passam.

---

## FASE 4: Integração com Sistema Existente

**Objetivo**: Integrar relacionamentos com FormController e UI
**Estimativa de Complexidade**: Alta
**Dependências**: FASE 3 completa

### Etapa 4.1: Adicionar get_relationship_service() ao Factory

**Agent**: `gus`
**Ação**: EDIT arquivo

**Arquivo a modificar**: [factory.py](src/persistence/factory.py)

**Mudanças**:
1. Adicionar import: `from persistence.relationships.service import RelationshipService`
2. Adicionar cache: `_relationship_service_cache: Optional[RelationshipService] = None`
3. Adicionar método estático:

```python
@staticmethod
def get_relationship_service() -> RelationshipService:
    """
    Get singleton instance of RelationshipService.

    Returns:
        RelationshipService instance configured with current factory
    """
    global _relationship_service_cache
    if _relationship_service_cache is None:
        _relationship_service_cache = RelationshipService(RepositoryFactory)
        logger.info("Created RelationshipService singleton")
    return _relationship_service_cache
```

4. Atualizar `clear_cache()` para também limpar `_relationship_service_cache`

**Critérios de Verificação (tir agent)**:
- [ ] `RepositoryFactory.get_relationship_service()` retorna instância de RelationshipService
- [ ] Chamadas repetidas retornam mesma instância (singleton)
- [ ] `RepositoryFactory.clear_cache()` limpa o cache do RelationshipService
- [ ] Nenhum import circular

**Verdito "Good Enough" se**: Todos os 4 critérios passam.

---

### Etapa 4.2: Integrar com FormController

**Agent**: `gus`
**Ação**: EDIT arquivo

**Arquivo a modificar**: [forms.py](src/controllers/forms.py)

**Referência OBRIGATÓRIA antes de implementar**: Ler forms.py completamente para entender o fluxo atual

**Mudanças no fluxo de CREATE** (método `create_form` ou similar):
1. Após processar campos normais, detectar campos com `type: "relationship"`
2. Para cada campo relationship:
   - Extrair target_id do form data
   - Validar que target_id existe via `validate_reference()`
   - Após salvar o registro principal (para ter o source_id)
   - Criar relacionamento via `RelationshipService.create()`
3. Sync display values é automático dentro de `create()`

**Mudanças no fluxo de UPDATE**:
1. Detectar se campos relationship mudaram
2. Se mudou: `remove()` relacionamento antigo, `create()` novo
3. Sync display values automático

**Mudanças no fluxo de DELETE**:
1. Verificar `cascade` config no spec
2. Se `cascade="delete"`: remover relacionamentos também
3. Se `cascade="nullify"`: soft delete dos relacionamentos
4. Se `cascade="none"`: apenas remover registro principal

**Critérios de Verificação (tir agent)**:
- [ ] forms.py importa `RepositoryFactory.get_relationship_service()`
- [ ] Fluxo CREATE processa campos `type: "relationship"`
- [ ] Fluxo UPDATE detecta mudanças em campos relationship
- [ ] Fluxo DELETE respeita configuração cascade
- [ ] Testes existentes continuam passando: `uv run pytest tests/test_form.py -v`

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 4.3: Criar Template relationship.html

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `src/templates/fields/relationship.html`

**Referência OBRIGATÓRIA**: [search_autocomplete.html](src/templates/fields/search_autocomplete.html) - Template similar existente

**Funcionalidades obrigatórias**:
1. Campo de busca com autocomplete (reutilizar lógica de search_autocomplete)
2. Suporte a `cardinality: "one"` (seleção única)
3. Suporte a `cardinality: "many"` (seleção múltipla com chips/tags)
4. Exibição de display_fields selecionados
5. Botão para remover seleção
6. Campo(s) hidden com UUID(s) selecionado(s)
7. Keyboard navigation (↑↓ Enter ESC)
8. Debounce de 200ms nas buscas

**Estrutura HTML básica**:
```html
<div class="relationship-field" data-cardinality="{{ field.cardinality }}">
    <!-- Input de busca -->
    <input type="text" class="relationship-search" autocomplete="off">

    <!-- Dropdown de resultados -->
    <div class="relationship-dropdown"></div>

    <!-- Seleções atuais (para cardinality: many) -->
    <div class="relationship-selections"></div>

    <!-- Hidden field(s) com UUIDs -->
    <input type="hidden" name="{{ field.name }}" class="relationship-value">
</div>
```

**Critérios de Verificação (tir agent)**:
- [ ] Template existe em `src/templates/fields/relationship.html`
- [ ] Suporta `cardinality: "one"` (campo hidden único)
- [ ] Suporta `cardinality: "many"` (múltiplos valores, separados por vírgula ou JSON)
- [ ] Usa debounce de 200ms
- [ ] Tem keyboard navigation funcional
- [ ] HTML é válido (sem tags não fechadas)

**Verdito "Good Enough" se**: Todos os 6 critérios passam.

---

### Etapa 4.4: Registrar Template no spec_renderer

**Agent**: `gus`
**Ação**: EDIT arquivo

**Arquivo a modificar**: [spec_renderer.py](src/utils/spec_renderer.py)

**Mudança**:
Adicionar `"relationship"` ao mapeamento de tipos para templates, apontando para `relationship.html`

**Critérios de Verificação (tir agent)**:
- [ ] spec_renderer reconhece `type: "relationship"`
- [ ] Renderiza usando `fields/relationship.html`
- [ ] Passa `field.cardinality`, `field.target`, `field.display_fields` para o template

**Verdito "Good Enough" se**: Todos os 3 critérios passam.

---

### Etapa 4.5: Criar/Atualizar Endpoint de API para Busca

**Agent**: `gus`
**Ação**: EDIT arquivo ou CREATE arquivo

**Verificar primeiro**: Se `/api/search/<target>` já existe em forms.py e pode ser reutilizado

**Se precisar criar novo endpoint**:
- `GET /api/relationship/search/<target>?q=<query>&limit=5`
- Retorna: `[{"record_id": "UUID", "display_label": "Nome - CPF"}, ...]`
- Usar `display_fields` para construir `display_label`

**Critérios de Verificação (tir agent)**:
- [ ] Endpoint acessível via curl: `curl "http://localhost:5000/api/search/contatos?q=jo"`
- [ ] Retorna JSON array com `record_id` e `display_label`
- [ ] Limite de 5 resultados funciona
- [ ] Case-insensitive matching funciona

**Verdito "Good Enough" se**: Todos os 4 critérios passam.

---

## FASE 5: Testes

**Objetivo**: Garantir qualidade via testes automatizados
**Estimativa de Complexidade**: Média
**Dependências**: FASE 4 completa

### Etapa 5.1: Testes do RelationshipService

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `tests/test_relationship_service.py`

**Referência**: [test_form.py](tests/test_form.py) - Padrão de testes existente

**Casos de teste obrigatórios** (12 mínimo):

```python
def test_create_relationship_success(tmp_path)
def test_create_relationship_invalid_source(tmp_path)
def test_create_relationship_invalid_target(tmp_path)
def test_create_relationship_duplicate_is_idempotent(tmp_path)
def test_remove_relationship_success(tmp_path)
def test_remove_relationship_not_found(tmp_path)
def test_get_relationships_empty(tmp_path)
def test_get_relationships_with_data(tmp_path)
def test_get_relationships_active_only(tmp_path)
def test_get_reverse_relationships(tmp_path)
def test_sync_display_values_success(tmp_path)
def test_validate_reference_exists(tmp_path)
def test_validate_reference_not_exists(tmp_path)
```

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `tests/test_relationship_service.py`
- [ ] Mínimo 12 testes definidos
- [ ] `uv run pytest tests/test_relationship_service.py -v` passa sem erros
- [ ] Usa `tmp_path` fixture para isolamento
- [ ] Coverage > 80% do service (verificar com `uv run pytest --cov=persistence.relationships.service`)

**Verdito "Good Enough" se**: 4 primeiros critérios passam (coverage é nice-to-have).

---

### Etapa 5.2: Testes dos Adapters

**Agent**: `gus`
**Ação**: CREATE arquivos

**Arquivos a criar**:
- `tests/test_sqlite_relationship_adapter.py`
- `tests/test_txt_relationship_adapter.py`

**Casos de teste por adapter** (10 cada):

```python
def test_create_table_success(tmp_path)
def test_create_table_already_exists(tmp_path)
def test_insert_success(tmp_path)
def test_insert_duplicate(tmp_path)
def test_soft_delete_success(tmp_path)
def test_select_by_source_all(tmp_path)
def test_select_by_source_active_only(tmp_path)
def test_select_by_target(tmp_path)
def test_exists_true(tmp_path)
def test_exists_false(tmp_path)
```

**Critérios de Verificação (tir agent)**:
- [ ] Ambos arquivos existem
- [ ] Cada arquivo tem mínimo 10 testes
- [ ] `uv run pytest tests/test_sqlite_relationship_adapter.py -v` passa
- [ ] `uv run pytest tests/test_txt_relationship_adapter.py -v` passa
- [ ] Ambos adapters comportam-se identicamente (mesmos inputs → mesmos outputs)

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 5.3: Teste de Integração E2E

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `tests/test_relationship_integration.py`

**Cenários E2E obrigatórios**:

1. **Fluxo completo de pedido**:
   - Criar cliente
   - Criar produto
   - Criar pedido com relacionamento cliente + produto
   - Verificar display values desnormalizados
   - Atualizar nome do cliente
   - Verificar sync automático do display value

2. **Cascade delete**:
   - Criar relacionamento
   - Deletar registro principal
   - Verificar comportamento conforme cascade config

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `tests/test_relationship_integration.py`
- [ ] Cenário 1 implementado e passa
- [ ] Cenário 2 implementado e passa
- [ ] `uv run pytest tests/test_relationship_integration.py -v` passa
- [ ] Nenhum teste existente quebra: `uv run hatch run test`

**Verdito "Good Enough" se**: Todos os 5 critérios passam.

---

### Etapa 5.4: Criar Spec de Teste (pedido.json)

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `examples/ponto-de-vendas/specs/pedido.json`

**Nota**: O nome do arquivo é `pedido.json` (singular), não `pedidos.json`.

**Conteúdo**:
```json
{
  "title": "Pedido",
  "icon": "fa-shopping-cart",
  "fields": [
    {
      "name": "numero",
      "label": "Número do Pedido",
      "type": "number",
      "required": true
    },
    {
      "name": "cliente",
      "label": "Cliente",
      "type": "relationship",
      "target_table": "contato",
      "target_field": "_record_id",
      "relationship_type": "has",
      "relationship_table": "rel_pedido_has_contato",
      "cardinality": "many-to-one",
      "search_field": "nome",
      "display_fields": ["nome", "telefone"],
      "required": true
    },
    {
      "name": "itens",
      "label": "Produtos",
      "type": "relationship",
      "target_table": "produto",
      "target_field": "_record_id",
      "relationship_type": "has",
      "relationship_table": "rel_pedido_has_produto",
      "cardinality": "many-to-many",
      "search_field": "nome",
      "display_fields": ["nome", "valor"],
      "required": true
    },
    {
      "name": "observacoes",
      "label": "Observações",
      "type": "textarea",
      "required": false
    }
  ]
}
```

**Nota sobre Cardinalidades**:
- `cliente`: `many-to-one` - Muitos pedidos podem ter o mesmo cliente (UNIQUE em source_uuid)
- `itens`: `many-to-many` - Um pedido pode ter muitos produtos E um produto pode estar em muitos pedidos

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `examples/ponto-de-vendas/specs/pedido.json` (singular!)
- [ ] JSON é válido: `python -c "import json; json.load(open('examples/ponto-de-vendas/specs/pedido.json'))"`
- [ ] Aplicação inicia sem erros: `timeout 5 uv run app examples/ponto-de-vendas || true` (verifica que não crasheia)

**Verdito "Good Enough" se**: Todos os 3 critérios passam.

---

## FASE 6: Documentação

**Objetivo**: Documentar sistema para desenvolvedores futuros
**Estimativa de Complexidade**: Baixa
**Dependências**: FASE 5 completa

### Etapa 6.1: Atualizar CLAUDE.md com Exemplos Completos

**Agent**: `gus`
**Ação**: EDIT arquivo

**Arquivo a modificar**: `CLAUDE.md`

**Seções a adicionar/atualizar**:
1. Exemplo completo de spec com relationship
2. Configuração de cascade options
3. Comportamento de sincronização EAGER
4. Como adicionar novo adapter de relacionamento

**Critérios de Verificação (tir agent)**:
- [ ] CLAUDE.md contém seção sobre campo relationship
- [ ] Exemplos de cascade ("none", "delete", "nullify") documentados
- [ ] Sincronização EAGER mencionada

**Verdito "Good Enough" se**: Todos os 3 critérios passam.

---

### Etapa 6.2: Criar RELATIONSHIP_SYSTEM.md

**Agent**: `gus`
**Ação**: CREATE arquivo

**Arquivo a criar**: `docs/RELATIONSHIP_SYSTEM.md`

**Seções obrigatórias**:
1. Arquitetura do sistema
2. Fluxogramas de CREATE/UPDATE/DELETE
3. Schema das tabelas
4. Guia para novos adapters
5. Troubleshooting

**Critérios de Verificação (tir agent)**:
- [ ] Arquivo existe em `docs/RELATIONSHIP_SYSTEM.md`
- [ ] Todas as 5 seções presentes
- [ ] Markdown válido
- [ ] Mínimo 200 linhas de conteúdo útil

**Verdito "Good Enough" se**: Todos os 4 critérios passam.

---

## ~~FASE 7: Migração de Specs Existentes~~ (REMOVIDA)

> **NOTA**: Esta fase foi removida do escopo deste plano.
>
> A migração de specs existentes (campos `search+datasource` → `relationship`) e a padronização de nomes para singular serão tratadas em uma **tarefa separada de migração**.
>
> Este plano foca exclusivamente na implementação greenfield do novo sistema de relacionamentos.

---

## Resumo de Arquivos

### Arquivos a Criar (17)

| Arquivo | Fase | Propósito |
|---------|------|-----------|
| `src/persistence/contracts/__init__.py` | 1.3 | Package init |
| `src/persistence/contracts/relationship_service.py` | 1.1 | Interface |
| `src/persistence/models/__init__.py` | 1.3 | Package init |
| `src/persistence/models/relationship.py` | 1.2 | Modelos |
| `src/persistence/relationships/__init__.py` | 1.3 | Package init |
| `src/persistence/relationships/service.py` | 2.1 | Serviço principal |
| `src/persistence/relationships/table_generator.py` | 2.2 | Geração de tabelas |
| `src/persistence/relationships/adapters/__init__.py` | 3.4 | Registro |
| `src/persistence/relationships/adapters/base_relationship_adapter.py` | 3.1 | Interface |
| `src/persistence/relationships/adapters/sqlite_relationship_adapter.py` | 3.2 | SQLite |
| `src/persistence/relationships/adapters/txt_relationship_adapter.py` | 3.3 | TXT |
| `src/templates/fields/relationship.html` | 4.3 | Template UI |
| `tests/test_relationship_service.py` | 5.1 | Testes |
| `tests/test_sqlite_relationship_adapter.py` | 5.2 | Testes SQLite |
| `tests/test_txt_relationship_adapter.py` | 5.2 | Testes TXT |
| `tests/test_relationship_integration.py` | 5.3 | Testes E2E |
| `examples/ponto-de-vendas/specs/pedido.json` | 5.4 | Spec exemplo (singular!) |
| `docs/RELATIONSHIP_SYSTEM.md` | 6.2 | Documentação |

### Arquivos a Modificar (4)

| Arquivo | Fase | Mudança |
|---------|------|---------|
| `CLAUDE.md` | 1.4, 6.1 | Documentar relationship |
| [factory.py](src/persistence/factory.py) | 4.1 | get_relationship_service() |
| [forms.py](src/controllers/forms.py) | 4.2 | Integrar CRUD |
| [spec_renderer.py](src/utils/spec_renderer.py) | 4.4 | Registrar template relationship |

---

## Comandos de Verificação Global

### Verificar Tudo Passa

```bash
# Todos os testes
uv run hatch run test

# Lint/format
uv run hatch run lint
uv run hatch run format

# Aplicação inicia
uv run app examples/ponto-de-vendas
```

### Verificação Manual Final (Humano)

1. Acessar http://localhost:5000
2. Navegar até Pedidos
3. Criar pedido selecionando cliente e produtos
4. Verificar display values aparecem
5. Editar cliente, verificar sync automático
6. Deletar pedido, verificar cascade

---

## Critérios de Aceite Final

- [ ] `uv run hatch run test` - Todos passam
- [ ] `uv run hatch run lint` - Sem erros
- [ ] Aplicação inicia sem warnings críticos
- [ ] Homologação manual aprovada
- [ ] Code review aprovado
- [ ] Commit realizado com mensagem adequada

---

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VibeCForms Application                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │ FormController│───▶│ Relationship │───▶│ RelationshipService      │  │
│  │              │    │ Field Type   │    │ - create()               │  │
│  │ - create     │    │              │    │ - remove()               │  │
│  │ - update     │    │ Template:    │    │ - get()                  │  │
│  │ - delete     │    │ relationship │    │ - sync_display_values()  │  │
│  └──────────────┘    │ .html        │    │ - validate_reference()   │  │
│                      └──────────────┘    └───────────┬──────────────┘  │
│                                                      │                  │
│  ┌───────────────────────────────────────────────────┼──────────────┐  │
│  │                    TableGenerator                  │              │  │
│  │  - generate_table_name()                          │              │  │
│  │  - create_relationship_table()                    │              │  │
│  │  - add_denormalized_columns()                     │              │  │
│  └───────────────────────────────────────────────────┼──────────────┘  │
│                                                      │                  │
│  ┌───────────────────────────────────────────────────┼──────────────┐  │
│  │              BaseRelationshipAdapter              │              │  │
│  │  (Abstract Interface)                             ▼              │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │  │
│  │  │ SQLite Adapter  │  │  TXT Adapter    │  │ Future Adapters │  │  │
│  │  └────────┬────────┘  └────────┬────────┘  │ - JSON, CSV     │  │  │
│  │           │                    │           │ - MySQL, Postgres│  │  │
│  │           ▼                    ▼           └─────────────────┘  │  │
│  │     ┌──────────┐         ┌──────────┐                          │  │
│  │     │  .db     │         │  .txt    │                          │  │
│  │     │rel_pedid.│         │rel_pedid.│                          │  │
│  │     │has_client│         │has_client│                          │  │
│  │     └──────────┘         └──────────┘                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Notas para o Orchestrator Agent

### Como Executar Este Plano

1. **Iniciar com FASE 1, Etapa 1.1**
2. **Para cada etapa**:
   - Invocar `gus` agent com prompt específico da etapa
   - Aguardar conclusão
   - Invocar `tir` agent com critérios de verificação
   - Se "NOT Good Enough": re-invocar `gus` com feedback do `tir`
   - Se "Good Enough": avançar para próxima etapa
3. **Máximo 3 iterações por etapa**
4. **Se após 3 iterações ainda "NOT Good Enough"**: escalar para humano
5. **Paralelização permitida**:
   - FASE 5 e FASE 6 podem rodar em paralelo
   - Dentro de cada FASE, etapas são sequenciais
6. **Escopo**: Este plano é greenfield - não há migração de dados existentes

### Prompt Template para gus Agent

```
## Contexto
Implementando FASE X, Etapa X.Y do plano em:
docs/planning/persistence/plano_implementacao_novo_paradigma.md

## Tarefa
[Copiar descrição da etapa]

## Referências a Ler ANTES de Implementar
[Listar arquivos de referência]

## Arquivo(s) a Criar/Modificar
[Listar]

## Requisitos Específicos
[Copiar requisitos da etapa]

## Importante
- Seguir convenções de código do CLAUDE.md
- Não fazer over-engineering
- Implementação pragmática e funcional
```

### Prompt Template para tir Agent

```
## Contexto
Verificando FASE X, Etapa X.Y do plano em:
docs/planning/persistence/plano_implementacao_novo_paradigma.md

## Critérios de Verificação
[Copiar checklist da etapa]

## Instruções
1. Verificar CADA critério da lista
2. Para cada critério, executar comando ou verificação
3. Retornar:
   - "Good Enough" se TODOS os critérios passam
   - "NOT Good Enough" + lista de critérios que falharam + como corrigir

## Importante
- Ser pragmático, não perfeccionista
- Foco em: funciona para a próxima etapa?
- Não bloquear por issues cosméticos
```
