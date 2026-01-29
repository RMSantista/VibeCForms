# Plano de Implementação: Novo Paradigma de Persistência VibeCForms

**Data**: 2026-01-27
**Versão**: 1.0
**Status**: Aguardando Aprovação

---

## Sumário Executivo

Este plano implementa o **Modelo Híbrido Simplificado** de persistência, conforme recomendado no documento `analise_comparativa_paradigma_relacional.md`. O modelo combina:

1. **Tabelas específicas por relacionamento** (`r{Source}_{Target}`) - Convenção #1 respeitada
2. **Audit trail básico** (created_at, created_by, removed_at, removed_by)
3. **Soft delete** via campo `removed_at`
4. **Sincronização sempre EAGER** (simplificado)
5. **Suporte multi-formato** (TXT, JSON, CSV, XML, SQLite, MySQL, PostgreSQL, MongoDB)

### Diferenças do Modelo Anterior (Tabela Universal)

| Aspecto | Modelo Anterior | Novo Modelo |
|---------|-----------------|-------------|
| Tabela de relacionamentos | Universal (`relationships`) | Específica (`r{Source}_{Target}`) |
| Display values | Prefixo `_campo_display` | Valores reais (sem prefixo) |
| Sincronização | 3 estratégias (EAGER/LAZY/SCHEDULED) | Sempre EAGER |
| Complexidade | ~1000 linhas | ~300-400 linhas |
| Convenção #1 | Viola (tabela universal) | Respeita (tabela por tipo) |

---

## FASE 1: Fundamentos e Contratos
**Objetivo**: Estabelecer interfaces, modelos e estrutura base
**Duração Estimada**: 1-2 dias

### Etapa 1.1: Definir Contratos e Interfaces

**Arquivos a criar**:
- `src/persistence/contracts/relationship_service.py`

**Conteúdo**:
```python
class IRelationshipService(ABC):
    """Interface para serviço de relacionamentos simplificado"""

    @abstractmethod
    def create(self, source_table: str, source_id: str,
               target_table: str, target_id: str,
               created_by: str = None) -> bool

    @abstractmethod
    def remove(self, source_table: str, source_id: str,
               target_table: str, target_id: str,
               removed_by: str = None) -> bool

    @abstractmethod
    def get(self, source_table: str, source_id: str,
            target_table: str, active_only: bool = True) -> List[str]

    @abstractmethod
    def get_reverse(self, target_table: str, target_id: str,
                    source_table: str, active_only: bool = True) -> List[str]

    @abstractmethod
    def sync_display_values(self, source_table: str, source_id: str,
                            spec: dict) -> bool

    @abstractmethod
    def validate_reference(self, target_table: str, target_id: str) -> bool

    @abstractmethod
    def ensure_relationship_table(self, source_table: str,
                                  target_table: str) -> bool
```

**Critérios de sucesso**:
- [ ] Interface define 7 métodos essenciais
- [ ] Docstrings completas em português
- [ ] Type hints em todos os parâmetros e retornos

---

### Etapa 1.2: Definir Modelos de Dados

**Arquivos a criar**:
- `src/persistence/models/relationship.py`

**Conteúdo**:
```python
@dataclass
class RelationshipRecord:
    """Registro de relacionamento entre duas entidades"""
    uuid_source: str
    uuid_target: str
    created_at: str  # ISO 8601
    created_by: Optional[str] = None
    removed_at: Optional[str] = None  # Soft delete
    removed_by: Optional[str] = None

@dataclass
class RelationshipFieldSpec:
    """Especificação de campo do tipo relationship"""
    name: str
    target: str  # Tabela alvo
    cardinality: str  # "one" ou "many"
    search_field: str  # Campo para busca
    display_fields: List[str]  # Campos para exibição
    cascade: str = "none"  # "none", "delete", "nullify"
    required: bool = False
```

**Critérios de sucesso**:
- [ ] Dataclasses com campos documentados
- [ ] Validação básica de cardinality ("one", "many")
- [ ] Campos opcionais com defaults apropriados

---

### Etapa 1.3: Definir Schema do Campo "relationship"

**Arquivos a modificar**:
- `CLAUDE.md` (documentação do tipo de campo)

**Formato do campo no spec JSON**:
```json
{
  "name": "cliente",
  "label": "Cliente",
  "type": "relationship",
  "target": "clientes",
  "cardinality": "one",
  "search_field": "cpf",
  "display_fields": ["nome", "cpf"],
  "cascade": "none",
  "required": true
}
```

**Comportamento**:
1. Framework detecta `type: "relationship"`
2. Cria automaticamente tabela `r{form_path}_{target}`
3. Adiciona campos desnormalizados: `{name}_{display_field}` para cada display_field
4. UI renderiza componente de busca/seleção

**Critérios de sucesso**:
- [ ] Schema JSON documentado
- [ ] Exemplo funcional em spec de teste
- [ ] Validação de campos obrigatórios (target, cardinality)

---

### Etapa 1.4: Criar Estrutura de Diretórios

**Arquivos a criar**:
```
src/persistence/
├── contracts/
│   ├── __init__.py
│   └── relationship_service.py    # Nova interface
├── models/
│   ├── __init__.py
│   └── relationship.py            # Novos modelos
├── relationships/
│   ├── __init__.py
│   ├── service.py                 # Serviço principal
│   ├── table_generator.py         # Geração automática de tabelas
│   └── adapters/
│       ├── __init__.py
│       ├── base_relationship_adapter.py
│       ├── sqlite_relationship_adapter.py
│       └── txt_relationship_adapter.py
```

**Critérios de sucesso**:
- [ ] Estrutura de diretórios criada
- [ ] Arquivos `__init__.py` com exports apropriados
- [ ] Nenhum import circular

---

## FASE 2: Implementação Core
**Objetivo**: Implementar serviço de relacionamentos e geração de tabelas
**Duração Estimada**: 2-3 dias
**Dependências**: FASE 1 completa

### Etapa 2.1: Implementar RelationshipService Base

**Arquivos a criar**:
- `src/persistence/relationships/service.py`

**Métodos a implementar**:
1. `__init__(repository_factory)` - Injeção de dependência
2. `create()` - Cria relacionamento + sincroniza display values
3. `remove()` - Soft delete do relacionamento
4. `get()` - Lista UUIDs relacionados (direção: source → target)
5. `get_reverse()` - Lista UUIDs relacionados (direção: target → source)
6. `sync_display_values()` - Atualiza valores desnormalizados
7. `validate_reference()` - Verifica se target_id existe

**Lógica de create()**:
```python
def create(self, source_table, source_id, target_table, target_id, created_by=None):
    # 1. Validar que source_id existe
    # 2. Validar que target_id existe
    # 3. Obter adapter para tabela de relacionamento
    # 4. Inserir registro em r{source}_{target}
    # 5. Buscar display values do target
    # 6. Atualizar campos desnormalizados no source
    # 7. Retornar sucesso
```

**Critérios de sucesso**:
- [ ] Todos os 7 métodos implementados
- [ ] Validação de referências antes de criar
- [ ] Display values sincronizados automaticamente (EAGER)
- [ ] Logs estratégicos para debugging

---

### Etapa 2.2: Implementar TableGenerator

**Arquivos a criar**:
- `src/persistence/relationships/table_generator.py`

**Responsabilidades**:
1. Gerar nome da tabela: `r{source}_{target}` (normalizado)
2. Criar estrutura da tabela (schema)
3. Criar índices otimizados
4. Adicionar campos desnormalizados à tabela source

**Schema da tabela de relacionamento**:
```sql
CREATE TABLE r{source}_{target} (
    uuid_source TEXT NOT NULL,
    uuid_target TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    removed_at TEXT,
    removed_by TEXT,
    PRIMARY KEY (uuid_source, uuid_target)
);

CREATE INDEX idx_{source}_{target}_source ON r{source}_{target}(uuid_source);
CREATE INDEX idx_{source}_{target}_target ON r{source}_{target}(uuid_target);
CREATE INDEX idx_{source}_{target}_active ON r{source}_{target}(uuid_source, removed_at);
```

**Critérios de sucesso**:
- [ ] Nomes de tabela normalizados (sem caracteres especiais)
- [ ] Índices criados para performance
- [ ] Suporte a soft delete via removed_at

---

### Etapa 2.3: Implementar Lógica de Desnormalização

**Arquivos a modificar**:
- `src/persistence/relationships/service.py`

**Lógica**:
1. Ler spec do target para identificar display_fields
2. Buscar registro do target por UUID
3. Extrair valores dos display_fields
4. Atualizar source com campos: `{relationship_name}_{display_field}`

**Exemplo**:
- Relationship: `pedido.cliente → clientes`
- display_fields: `["nome", "cpf"]`
- Campos criados em pedidos: `cliente_nome`, `cliente_cpf`

**Critérios de sucesso**:
- [ ] Campos desnormalizados com nomenclatura consistente
- [ ] Sincronização automática no create
- [ ] Método para re-sincronizar sob demanda

---

## FASE 3: Adapters de Persistência
**Objetivo**: Implementar adapters para diferentes backends
**Duração Estimada**: 3-4 dias
**Dependências**: FASE 2 completa

### Etapa 3.1: Implementar BaseRelationshipAdapter

**Arquivos a criar**:
- `src/persistence/relationships/adapters/base_relationship_adapter.py`

**Interface abstrata**:
```python
class BaseRelationshipAdapter(ABC):
    @abstractmethod
    def create_table(self, source_table: str, target_table: str) -> bool

    @abstractmethod
    def insert(self, table_name: str, record: RelationshipRecord) -> bool

    @abstractmethod
    def soft_delete(self, table_name: str, uuid_source: str,
                    uuid_target: str, removed_by: str) -> bool

    @abstractmethod
    def select_by_source(self, table_name: str, uuid_source: str,
                         active_only: bool = True) -> List[str]

    @abstractmethod
    def select_by_target(self, table_name: str, uuid_target: str,
                         active_only: bool = True) -> List[str]

    @abstractmethod
    def exists(self, table_name: str, uuid_source: str,
               uuid_target: str) -> bool

    @abstractmethod
    def table_exists(self, table_name: str) -> bool
```

**Critérios de sucesso**:
- [ ] Interface define 7 métodos
- [ ] Métodos cobrem CRUD + verificação de existência
- [ ] Suporte a soft delete nativo

---

### Etapa 3.2: Implementar SQLiteRelationshipAdapter (Prioridade 1)

**Arquivos a criar**:
- `src/persistence/relationships/adapters/sqlite_relationship_adapter.py`

**Implementação**:
- Usar conexão do SQLiteRepository existente
- Queries parametrizadas (prevenção SQL injection)
- Transações para operações compostas
- Índices automáticos na criação

**Critérios de sucesso**:
- [ ] Todas as operações funcionam com SQLite
- [ ] Queries usam placeholders `?` (não string interpolation)
- [ ] Transações com rollback em caso de erro
- [ ] Testes unitários passando

---

### Etapa 3.3: Implementar TxtRelationshipAdapter (Prioridade 2)

**Arquivos a criar**:
- `src/persistence/relationships/adapters/txt_relationship_adapter.py`

**Formato de arquivo**:
```
# Arquivo: data/txt/r_pedidos_clientes.txt
uuid_source;uuid_target;created_at;created_by;removed_at;removed_by
ABC123;CLI456;2026-01-27T10:30:00Z;user1;;
DEF789;CLI456;2026-01-27T11:00:00Z;user2;2026-01-27T12:00:00Z;user2
```

**Implementação**:
- Seguir padrão do TxtRepository existente
- Delimitador `;`
- Encoding UTF-8
- Backup antes de operações destrutivas

**Critérios de sucesso**:
- [ ] Formato compatível com outros arquivos TXT
- [ ] Soft delete preserva histórico
- [ ] Leitura/escrita atômica

---

### Etapa 3.4: Preparar Interface para Futuros Adapters

**Arquivos a criar**:
- `src/persistence/relationships/adapters/__init__.py`

**Registro de adapters disponíveis**:
```python
RELATIONSHIP_ADAPTERS = {
    "sqlite": SQLiteRelationshipAdapter,
    "txt": TxtRelationshipAdapter,
    # Futuros:
    # "mysql": MySQLRelationshipAdapter,
    # "postgres": PostgresRelationshipAdapter,
    # "mongodb": MongoDBRelationshipAdapter,
    # "json": JSONRelationshipAdapter,
    # "csv": CSVRelationshipAdapter,
    # "xml": XMLRelationshipAdapter,
}
```

**Critérios de sucesso**:
- [ ] Factory pattern para criação de adapters
- [ ] Estrutura preparada para novos backends
- [ ] Documentação de como adicionar novo adapter

---

## FASE 4: Integração com Sistema Existente
**Objetivo**: Integrar relacionamentos com FormController e UI
**Duração Estimada**: 2-3 dias
**Dependências**: FASE 3 completa

### Etapa 4.1: Integrar com RepositoryFactory

**Arquivos a modificar**:
- `src/persistence/factory.py`

**Mudanças**:
1. Adicionar método `get_relationship_service()`
2. Cache singleton do RelationshipService
3. Injeção automática do adapter correto baseado em config

**Critérios de sucesso**:
- [ ] RelationshipService acessível via factory
- [ ] Adapter selecionado baseado em persistence.json
- [ ] Cache evita múltiplas instâncias

---

### Etapa 4.2: Integrar com FormController

**Arquivos a modificar**:
- `src/controllers/forms.py`

**Mudanças no fluxo de CREATE**:
1. Detectar campos `type: "relationship"` no spec
2. Para cada campo relationship:
   - Validar que target_id existe
   - Criar relacionamento via RelationshipService
   - Sincronizar display values
3. Salvar registro principal com campos desnormalizados

**Mudanças no fluxo de UPDATE**:
1. Detectar mudanças em campos relationship
2. Se mudou: remover relacionamento antigo, criar novo
3. Re-sincronizar display values

**Mudanças no fluxo de DELETE**:
1. Baseado em `cascade`:
   - "none": apenas remover registro principal
   - "delete": remover relacionamentos também
   - "nullify": soft delete dos relacionamentos

**Critérios de sucesso**:
- [ ] CRUD funciona com campos relationship
- [ ] Validação de referências antes de salvar
- [ ] Cascade configurável por campo

---

### Etapa 4.3: Criar Template para Campo Relationship

**Arquivos a criar**:
- `src/templates/fields/relationship.html`

**Funcionalidades**:
1. Campo de busca com autocomplete
2. Dropdown de resultados (máx 5)
3. Seleção única (cardinality: "one") ou múltipla (cardinality: "many")
4. Exibição de display values selecionados
5. Botão para remover seleção
6. Campo hidden com UUID(s) selecionado(s)

**Critérios de sucesso**:
- [ ] UI funcional para busca e seleção
- [ ] Suporte a cardinality "one" e "many"
- [ ] Acessibilidade (keyboard navigation)
- [ ] Responsivo

---

### Etapa 4.4: Criar Endpoints de API

**Arquivos a modificar**:
- `src/controllers/forms.py` ou criar `src/controllers/relationships.py`

**Endpoints**:
1. `GET /api/relationship/search/<target>?q=<query>&limit=5`
   - Busca registros no target para seleção
   - Retorna: `[{record_id, display_label}, ...]`

2. `GET /api/relationship/<source>/<source_id>/<relationship_name>`
   - Lista relacionamentos de um registro
   - Retorna: `[{target_id, display_values}, ...]`

**Critérios de sucesso**:
- [ ] Endpoints funcionais
- [ ] Resposta em JSON
- [ ] Limite de resultados para performance

---

## FASE 5: Testes e Validação
**Objetivo**: Garantir qualidade e permitir homologação humana
**Duração Estimada**: 2-3 dias
**Dependências**: FASE 4 completa

### Etapa 5.1: Testes Unitários do RelationshipService

**Arquivos a criar**:
- `tests/test_relationship_service.py`

**Casos de teste**:
1. `test_create_relationship_success`
2. `test_create_relationship_invalid_source`
3. `test_create_relationship_invalid_target`
4. `test_create_relationship_duplicate`
5. `test_remove_relationship_success`
6. `test_remove_relationship_not_found`
7. `test_get_relationships_empty`
8. `test_get_relationships_with_data`
9. `test_get_relationships_active_only`
10. `test_sync_display_values_success`
11. `test_validate_reference_exists`
12. `test_validate_reference_not_exists`

**Critérios de sucesso**:
- [ ] Mínimo 12 testes unitários
- [ ] Coverage > 80% do RelationshipService
- [ ] Todos os testes passando

---

### Etapa 5.2: Testes Unitários dos Adapters

**Arquivos a criar**:
- `tests/test_sqlite_relationship_adapter.py`
- `tests/test_txt_relationship_adapter.py`

**Casos de teste por adapter**:
1. `test_create_table_success`
2. `test_create_table_already_exists`
3. `test_insert_success`
4. `test_insert_duplicate`
5. `test_soft_delete_success`
6. `test_select_by_source_all`
7. `test_select_by_source_active_only`
8. `test_select_by_target`
9. `test_exists_true`
10. `test_exists_false`

**Critérios de sucesso**:
- [ ] 10 testes por adapter
- [ ] Ambos adapters funcionando identicamente
- [ ] Testes isolados (fixtures de setup/teardown)

---

### Etapa 5.3: Testes de Integração End-to-End

**Arquivos a criar**:
- `tests/test_relationship_integration.py`

**Cenários E2E**:
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

3. **Migração de backend**:
   - Criar relacionamentos em TXT
   - Migrar para SQLite
   - Verificar integridade

**Critérios de sucesso**:
- [ ] Fluxos E2E funcionando
- [ ] Dados consistentes após operações
- [ ] Nenhuma regressão em funcionalidades existentes

---

### Etapa 5.4: Spec de Teste para Homologação Humana

**Arquivos a criar**:
- `examples/ponto-de-vendas/specs/pedidos.json`

**Spec de exemplo**:
```json
{
  "title": "Pedidos",
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
      "target": "contatos",
      "cardinality": "one",
      "search_field": "nome",
      "display_fields": ["nome", "telefone"],
      "required": true
    },
    {
      "name": "produtos",
      "label": "Produtos",
      "type": "relationship",
      "target": "produtos",
      "cardinality": "many",
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

**Roteiro de homologação**:
1. Iniciar aplicação: `uv run app examples/ponto-de-vendas`
2. Criar 2-3 contatos
3. Criar 2-3 produtos
4. Acessar formulário de Pedidos
5. Criar pedido selecionando cliente e produtos
6. Verificar que display values aparecem corretamente
7. Editar um contato (mudar nome)
8. Verificar que pedido reflete a mudança
9. Listar pedidos e verificar dados

**Critérios de sucesso**:
- [ ] Aplicação inicia sem erros
- [ ] Formulário de pedidos renderiza corretamente
- [ ] Relacionamentos funcionam na UI
- [ ] Display values sincronizam automaticamente

---

## FASE 6: Documentação e Finalização
**Objetivo**: Documentar e preparar para produção
**Duração Estimada**: 1 dia
**Dependências**: FASE 5 completa (homologação aprovada)

### Etapa 6.1: Atualizar CLAUDE.md

**Seções a adicionar/atualizar**:
1. Documentação do campo `type: "relationship"`
2. Exemplos de specs com relacionamentos
3. Configuração de cascade
4. Comportamento de sincronização

---

### Etapa 6.2: Criar Documentação Técnica

**Arquivos a criar**:
- `docs/RELATIONSHIP_SYSTEM.md`

**Conteúdo**:
1. Arquitetura do sistema de relacionamentos
2. Diagramas de fluxo (CREATE, UPDATE, DELETE)
3. Schema das tabelas de relacionamento
4. Guia para adicionar novos adapters
5. Troubleshooting

---

### Etapa 6.3: Commit e Merge

**Comandos**:
```bash
git add .
git commit -m "feat: implement simplified relationship paradigm

- Add relationship field type with automatic table generation
- Implement RelationshipService with EAGER sync strategy
- Add SQLite and TXT relationship adapters
- Integrate with FormController and templates
- Add comprehensive test suite
- Update documentation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push origin New_Persistence
```

---

## FASE 7: Migração de Specs Existentes
**Objetivo**: Migrar campos `search` com `datasource` para o novo tipo `relationship`
**Duração Estimada**: 1-2 dias
**Dependências**: FASE 5 completa (homologação aprovada)

### Etapa 7.1: Identificar Specs com Search+Datasource

**Business cases afetados**:
- `examples/analise-laboratorial/` - 11+ specs com search+datasource

**Specs a migrar**:
| Spec | Campo | Datasource |
|------|-------|------------|
| `orcamento.json` | cliente | clientes |
| `orcamento.json` | acreditador | acreditadores |
| `amostra.json` | orcamento | orcamento |
| `amostra.json` | amostra_especifica | amostra_especifica |
| `amostra.json` | recebedor | funcionarios |
| `amostra_especifica.json` | tipo_amostra | tipo_amostra |
| `fracionamento.json` | amostra | amostra |
| `fracionamento.json` | matriz | matriz |
| `fracionamento.json` | responsavel | funcionarios |
| `resultado.json` | fracionamento | fracionamento |
| `resultado.json` | analista | funcionarios |
| `laudo.json` | orcamento | orcamento |
| `laudo.json` | rt | funcionarios |
| `matriz.json` | tipo_amostra | tipo_amostra |
| `matriz.json` | analise | analises |
| `matriz.json` | metodologia | metodologias |

---

### Etapa 7.2: Script de Migração Automática

**Arquivos a criar**:
- `scripts/migrate_search_to_relationship.py`

**Lógica de transformação**:
```python
# Antes (search+datasource)
{
    "name": "cliente",
    "type": "search",
    "datasource": "clientes",
    "required": true
}

# Depois (relationship)
{
    "name": "cliente",
    "type": "relationship",
    "target": "clientes",
    "cardinality": "one",
    "search_field": "nome",  # Auto-detectado: primeiro campo text required
    "display_fields": ["nome"],
    "required": true
}
```

**Critérios de sucesso**:
- [ ] Script identifica todos os campos search+datasource
- [ ] Transformação preserva required e label
- [ ] Auto-detecção de search_field funciona
- [ ] Backup dos specs originais antes de modificar

---

### Etapa 7.3: Deprecar Campo Search+Datasource

**Arquivos a modificar**:
- `src/controllers/forms.py`
- `src/utils/spec_renderer.py`

**Comportamento**:
1. Campo `search` com `datasource` emite `DeprecationWarning`
2. Log: "Campo 'search' com 'datasource' está deprecated. Use 'type: relationship' em vez disso."
3. Funcionalidade mantida temporariamente para backwards compatibility

**Critérios de sucesso**:
- [ ] Warning emitido quando search+datasource detectado
- [ ] Funcionalidade existente não quebra
- [ ] Documentação atualizada com nota de deprecação

---

### Etapa 7.4: Remover Código do Modelo Anterior

**Arquivos a remover/limpar**:
- `src/persistence/relationship_repository.py` (se existir - modelo tabela universal)
- `src/persistence/contracts/relationship_interface.py` (interface antiga)
- Tabela `relationships` universal (manter para migração de dados)

**Critérios de sucesso**:
- [ ] Código do modelo anterior removido
- [ ] Testes antigos removidos ou adaptados
- [ ] Nenhuma referência ao modelo antigo no código

---

## Resumo de Arquivos

### Arquivos a Criar (16)
| Arquivo | Fase | Propósito |
|---------|------|-----------|
| `src/persistence/contracts/relationship_service.py` | 1.1 | Interface do serviço |
| `src/persistence/models/relationship.py` | 1.2 | Modelos de dados |
| `src/persistence/relationships/__init__.py` | 1.4 | Package init |
| `src/persistence/relationships/service.py` | 2.1 | Serviço principal |
| `src/persistence/relationships/table_generator.py` | 2.2 | Geração de tabelas |
| `src/persistence/relationships/adapters/__init__.py` | 3.4 | Registro de adapters |
| `src/persistence/relationships/adapters/base_relationship_adapter.py` | 3.1 | Interface base |
| `src/persistence/relationships/adapters/sqlite_relationship_adapter.py` | 3.2 | Adapter SQLite |
| `src/persistence/relationships/adapters/txt_relationship_adapter.py` | 3.3 | Adapter TXT |
| `src/templates/fields/relationship.html` | 4.3 | Template UI |
| `tests/test_relationship_service.py` | 5.1 | Testes do serviço |
| `tests/test_sqlite_relationship_adapter.py` | 5.2 | Testes SQLite |
| `tests/test_txt_relationship_adapter.py` | 5.2 | Testes TXT |
| `tests/test_relationship_integration.py` | 5.3 | Testes E2E |
| `examples/ponto-de-vendas/specs/pedidos.json` | 5.4 | Spec de teste |
| `scripts/migrate_search_to_relationship.py` | 7.2 | Script de migração |

### Arquivos a Modificar (5)
| Arquivo | Fase | Mudança |
|---------|------|---------|
| `src/persistence/factory.py` | 4.1 | Adicionar get_relationship_service() |
| `src/controllers/forms.py` | 4.2 | Integrar campos relationship |
| `src/utils/spec_renderer.py` | 7.3 | Deprecation warning para search+datasource |
| `CLAUDE.md` | 6.1 | Documentar novo tipo de campo |
| `docs/RELATIONSHIP_SYSTEM.md` | 6.2 | Documentação técnica |

---

## Critérios de Aceite Final

1. [ ] Todos os testes passando (unitários + integração)
2. [ ] Homologação humana aprovada
3. [ ] Nenhuma regressão em funcionalidades existentes
4. [ ] Documentação completa
5. [ ] Code review aprovado
6. [ ] Commit realizado na branch New_Persistence

---

## Verificação de Implementação

**Comando para rodar testes**:
```bash
uv run hatch run test
```

**Comando para iniciar aplicação de teste**:
```bash
uv run app examples/ponto-de-vendas
```

**Verificação manual**:
1. Acessar http://localhost:5000
2. Navegar até formulário de Pedidos
3. Criar pedido com cliente e produtos
4. Verificar dados na listagem

---

## Roadmap de Adapters Futuros

### Prioridade 1: Implementação Atual
| Adapter | Status | Fase |
|---------|--------|------|
| SQLiteRelationshipAdapter | 🟡 Planejado | 3.2 |
| TxtRelationshipAdapter | 🟡 Planejado | 3.3 |

### Prioridade 2: Formatos de Arquivo
| Adapter | Status | Descrição |
|---------|--------|-----------|
| JSONRelationshipAdapter | 📋 Futuro | Arquivos .json estruturados |
| CSVRelationshipAdapter | 📋 Futuro | Arquivos .csv delimitados |
| XMLRelationshipAdapter | 📋 Futuro | Arquivos .xml estruturados |
| XLSXRelationshipAdapter | 📋 Futuro | Planilhas Excel |

### Prioridade 3: Bancos de Dados Relacionais
| Adapter | Status | Descrição |
|---------|--------|-----------|
| MySQLRelationshipAdapter | 📋 Futuro | MySQL / MariaDB |
| PostgresRelationshipAdapter | 📋 Futuro | PostgreSQL |
| OracleRelationshipAdapter | 📋 Futuro | Oracle Database |
| SQLServerRelationshipAdapter | 📋 Futuro | Microsoft SQL Server |

### Prioridade 4: Bancos NoSQL
| Adapter | Status | Descrição |
|---------|--------|-----------|
| MongoDBRelationshipAdapter | 📋 Futuro | MongoDB (documentos) |
| RedisRelationshipAdapter | 📋 Futuro | Redis (cache/key-value) |

---

## Future Features (Implementação Posterior)

### FF-01: Cross-Backend Relationships
**Descrição**: Permitir relacionamentos entre entidades em backends diferentes (ex: pedido em SQLite relacionado com cliente em TXT).

**Desafios**:
- Sem garantias de integridade referencial nativa
- Transações distribuídas não suportadas
- Sincronização de display values entre backends

**Abordagem proposta**:
- Validação em camada de aplicação
- Eventual consistency para display values
- Flag de configuração para habilitar/desabilitar

**Status**: 📋 Planejado para versão futura

---

### FF-02: Migração de Dados Entre Backends
**Descrição**: Ferramenta para migrar dados e relacionamentos de um backend para outro.

**Cenários**:
- TXT → SQLite (upgrade de performance)
- SQLite → PostgreSQL (escala enterprise)
- JSON → MongoDB (migração de stack)

**Abordagem proposta**:
1. Export de dados + relacionamentos do backend origem
2. Transformação de formato se necessário
3. Import no backend destino
4. Validação de integridade
5. Rollback em caso de falha

**Status**: 📋 Planejado para versão futura

---

### FF-03: Índices de Busca Full-Text
**Descrição**: Índices otimizados para busca full-text em campos de relacionamento.

**Backends suportados**:
- SQLite: FTS5
- PostgreSQL: tsvector/tsquery
- MongoDB: Text indexes

**Status**: 📋 Planejado para versão futura

---

### FF-04: Cache de Display Values
**Descrição**: Cache em memória para display values frequentemente acessados.

**Benefícios**:
- Redução de I/O em leituras
- Latência menor para autocomplete
- Menor carga no backend

**Abordagem proposta**:
- LRU cache com TTL configurável
- Invalidação automática em updates
- Configuração por campo

**Status**: 📋 Planejado para versão futura

---

### FF-05: Histórico de Relacionamentos
**Descrição**: Auditoria completa de criação/remoção de relacionamentos com timeline.

**Dados rastreados**:
- Quem criou/removeu
- Quando (timestamp preciso)
- Contexto (metadata JSON)

**Uso**:
- Compliance e auditoria
- Desfazer operações
- Análise de comportamento

**Status**: 📋 Planejado para versão futura

---

### FF-06: Relacionamentos Bidirecionais Automáticos
**Descrição**: Criar relacionamento reverso automaticamente quando configurado.

**Exemplo**:
- Criar `pedido → cliente` automaticamente cria `cliente ← pedido`
- Navegação bidirecional sem duplicação de lógica

**Status**: 📋 Planejado para versão futura

---

### FF-07: Validação de Cardinalidade
**Descrição**: Enforcement de cardinalidade em tempo de execução.

**Regras**:
- `one`: Máximo 1 relacionamento por source
- `many`: Ilimitado (ou configurável com max)

**Comportamento**:
- Erro se tentar criar segundo relacionamento em `one`
- Warning se atingir limite em `many`

**Status**: 📋 Planejado para versão futura

---

## Diagrama de Arquitetura Final

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
│  │  │ (Prioridade 1)  │  │ (Prioridade 1)  │  │                 │  │  │
│  │  └────────┬────────┘  └────────┬────────┘  │ - JSON          │  │  │
│  │           │                    │           │ - CSV           │  │  │
│  │           ▼                    ▼           │ - XML           │  │  │
│  │     ┌──────────┐         ┌──────────┐     │ - XLSX          │  │  │
│  │     │  .db     │         │  .txt    │     │ - MySQL         │  │  │
│  │     │ r_pedidos│         │ r_pedidos│     │ - PostgreSQL    │  │  │
│  │     │ _clientes│         │ _clientes│     │ - Oracle        │  │  │
│  │     └──────────┘         └──────────┘     │ - SQL Server    │  │  │
│  │                                            │ - MongoDB       │  │  │
│  │                                            └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Cronograma Resumido

| Fase | Descrição | Duração | Dependência |
|------|-----------|---------|-------------|
| **FASE 1** | Fundamentos e Contratos | 1-2 dias | - |
| **FASE 2** | Implementação Core | 2-3 dias | FASE 1 |
| **FASE 3** | Adapters (SQLite + TXT) | 3-4 dias | FASE 2 |
| **FASE 4** | Integração com Sistema | 2-3 dias | FASE 3 |
| **FASE 5** | Testes e Validação | 2-3 dias | FASE 4 |
| **FASE 6** | Documentação | 1 dia | FASE 5 |
| **FASE 7** | Migração de Specs | 1-2 dias | FASE 5 |
| **TOTAL** | | **12-18 dias** | |

---

## Notas de Implementação

### Convenções de Nomenclatura

1. **Tabelas de relacionamento**: `r_{source}_{target}`
   - Exemplo: `r_pedidos_clientes`, `r_pedidos_produtos`
   - Normalização: letras minúsculas, underscores

2. **Campos desnormalizados**: `{relationship_name}_{display_field}`
   - Exemplo: `cliente_nome`, `cliente_cpf`, `produto_nome`
   - Sem prefixo especial (diferente do modelo anterior `_campo_display`)

3. **Arquivos TXT de relacionamento**: `data/txt/r_{source}_{target}.txt`
   - Seguem padrão de outros arquivos TXT

### Tratamento de Erros

1. **Referência inválida**: Retornar erro claro antes de criar relacionamento
2. **Duplicata**: Ignorar silenciosamente (idempotência)
3. **Backend indisponível**: Propagar exceção com contexto

### Performance

1. **Índices**: Sempre criar em uuid_source e uuid_target
2. **Batch operations**: Suportar criação/remoção em lote
3. **Connection pooling**: Reutilizar conexões existentes
