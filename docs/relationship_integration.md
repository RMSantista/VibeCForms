# Integração FormController ↔ RelationshipRepository

## Visão Geral

Este documento descreve a integração entre o FormController e o RelationshipRepository no VibeCForms v3.0, implementando suporte completo para gerenciamento de relacionamentos entre entidades.

## Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────┐
│                    FormController (forms.py)                │
├─────────────────────────────────────────────────────────────┤
│  Funções Helper:                                            │
│  • _get_relationship_fields(spec)                           │
│  • _save_relationships(repo, ...)                           │
│  • _update_relationships(repo, ...)                         │
│  • _enrich_with_display_values(repo, ...)                   │
│                                                            │
│  Rotas Modificadas:                                         │
│  • POST /<form_name> - Salva relationships ao criar         │
│  • PUT /<form_name>/edit/<id> - Atualiza relationships      │
│  • GET /api/relationships/<type>/<id> - Lista relationships │
│                                                            │
│  Funções Modificadas:                                       │
│  • read_forms() - Enriquece dados com display values        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              RepositoryFactory                              │
│  get_repository() → BaseRepository                          │
│  get_relationship_repository() → RelationshipRepository     │
└─────────────────────────────────────────────────────────────┘
```

## Componentes Implementados

### 1. Helper Functions

#### `_get_relationship_fields(spec: Dict) -> List[Dict]`

**Propósito:** Detectar campos de relacionamento na especificação do formulário.

**Critério:** Campos do tipo `search` com atributo `datasource`.

**Exemplo:**
```python
spec = {
    "fields": [
        {"name": "cliente", "type": "search", "datasource": "clientes"},
        {"name": "nome", "type": "text"}
    ]
}

relationship_fields = _get_relationship_fields(spec)
# Retorna: [{"name": "cliente", "type": "search", "datasource": "clientes"}]
```

#### `_save_relationships(repo, form_path, record_id, form_data, spec)`

**Propósito:** Salvar relacionamentos após criação de um registro.

**Fluxo:**
1. Obtém `RelationshipRepository` via `repo.get_relationship_repository()`
2. Detecta campos de relacionamento usando `_get_relationship_fields()`
3. Para cada campo:
   - Extrai `target_id` do `form_data`
   - Cria relacionamento via `rel_repo.create_relationship()`
   - Registra sucesso/erro no log

**Parâmetros do Relacionamento:**
- `source_type`: `form_path` (e.g., "laudo")
- `source_id`: `record_id` (UUID do registro criado)
- `relationship_name`: `field_name` (e.g., "cliente")
- `target_type`: `datasource` do campo (e.g., "clientes")
- `target_id`: UUID do registro relacionado
- `created_by`: "system"

**Tratamento de Erros:**
- Se backend não suporta relationships: log debug, retorna sem erro
- Se campo relationship vazio: skip, log debug
- Se falha ao criar relationship: log warning, continua (não quebra o fluxo)

#### `_update_relationships(repo, form_path, record_id, form_data, spec)`

**Propósito:** Atualizar relacionamentos durante edição de um registro.

**Estratégia:** Remove todos os relacionamentos existentes e recria (simples e seguro).

**Fluxo:**
1. Busca relacionamentos existentes via `get_relationships()`
2. Remove todos via `remove_relationship()` (soft-delete)
3. Recria relacionamentos via `_save_relationships()`

**Tratamento de Erros:**
- Log warning se falhar, mas continua com update do registro

#### `_enrich_with_display_values(repo, forms, spec, form_path)`

**Propósito:** Enriquecer dados do formulário com valores de exibição dos relacionamentos.

**Fluxo:**
1. Para cada registro em `forms`:
   - Busca relacionamentos via `get_relationships()`
   - Para cada relacionamento:
     - Obtém `display_value` do target via `_get_display_value()`
     - Adiciona campo `_<field_name>_display` ao registro

**Exemplo:**
```python
# Antes
form_data = {
    "_record_id": "ABC123",
    "cliente": "XYZ789",  # UUID do cliente
    "numero": "001/2024"
}

# Depois do enriquecimento
form_data = {
    "_record_id": "ABC123",
    "cliente": "XYZ789",
    "numero": "001/2024",
    "_cliente_display": "João Silva Ltda"  # Nome do cliente
}
```

**Tratamento de Erros:**
- Log debug se não conseguir obter display value
- Log warning se falhar para um registro, mas continua para os próximos

### 2. Rotas Modificadas

#### POST `/<form_name>` (Criação de Registro)

**Modificação:** Após criar o registro principal, salva relacionamentos.

**Código:**
```python
# Create the new record
record_id = repo.create(form_name, spec, form_data)

if record_id:
    logger.info(f"Created new record {record_id} in {form_name}")

    # Save relationships for the new record
    _save_relationships(repo, form_name, record_id, form_data, spec)

    # Apply default tags...
```

#### PUT `/<form_name>/edit/<record_id>` (Atualização de Registro)

**Modificação:** Após atualizar o registro principal, atualiza relacionamentos.

**Código:**
```python
# Update the record by ID
success = repo.update_by_id(form_name, spec, record_id, form_data)

if success:
    logger.info(f"Updated record {record_id} in {form_name}")

    # Update relationships
    _update_relationships(repo, form_name, record_id, form_data, spec)
```

#### GET `/api/relationships/<source_type>/<source_id>` (Novo Endpoint)

**Propósito:** API para listar relacionamentos de um registro.

**Retorno:**
```json
{
  "relationships": [
    {
      "rel_id": "REL_001",
      "relationship_name": "cliente",
      "target_type": "clientes",
      "target_id": "CLI_001",
      "created_at": "2024-01-09T10:30:00",
      "created_by": "system"
    }
  ],
  "reverse_relationships": [
    {
      "rel_id": "REL_002",
      "source_type": "pedidos",
      "source_id": "PED_001",
      "relationship_name": "laudo",
      "created_at": "2024-01-09T11:00:00",
      "created_by": "system"
    }
  ]
}
```

**Tratamento de Erros:**
- Se backend não suporta relationships: retorna arrays vazios
- Se erro na busca: retorna HTTP 500 com arrays vazios

### 3. Função Modificada

#### `read_forms(spec, form_path)`

**Modificação:** Após ler dados, enriquece com display values.

**Código:**
```python
# Read data
data = repo.read_all(form_path, spec)

# Enrich data with relationship display values
_enrich_with_display_values(repo, data, spec, form_path)

# Update tracking after successful read
update_form_tracking(form_path, spec, len(data))

return data
```

## Fluxo Completo de Dados

### Criação de Registro com Relacionamento

```
1. Usuário preenche formulário:
   - Campo "numero": "001/2024"
   - Campo "cliente" (search): Seleciona "João Silva Ltda"
     → Frontend envia: cliente="CLI_001" (UUID hidden field)

2. POST /<form_name>
   - Cria registro principal → record_id="LAU_001"
   - _save_relationships():
     • Detecta campo "cliente" (search + datasource)
     • Cria relationship:
       - source_type="laudo", source_id="LAU_001"
       - relationship_name="cliente"
       - target_type="clientes", target_id="CLI_001"

3. Tabela relationships:
   | rel_id | source_type | source_id | relationship_name | target_type | target_id |
   |--------|-------------|-----------|-------------------|-------------|-----------|
   | REL_1  | laudo       | LAU_001   | cliente           | clientes    | CLI_001   |
```

### Leitura de Registros com Display Values

```
1. GET /<form_name>
   - read_forms():
     • repo.read_all() → [{"_record_id": "LAU_001", "numero": "001/2024", ...}]
     • _enrich_with_display_values():
       - get_relationships("laudo", "LAU_001")
         → [{relationship_name: "cliente", target_id: "CLI_001"}]
       - _get_display_value("clientes", "CLI_001")
         → "João Silva Ltda"
       - Adiciona: form["_cliente_display"] = "João Silva Ltda"
     • Retorna dados enriquecidos

2. Template rendering:
   - Exibe "João Silva Ltda" ao invés de "CLI_001"
```

### Atualização de Relacionamento

```
1. PUT /<form_name>/edit/<record_id>
   - Update registro principal
   - _update_relationships():
     • get_relationships("laudo", "LAU_001")
       → [REL_1: cliente→CLI_001]
     • remove_relationship(REL_1) (soft-delete)
     • _save_relationships() com novos dados
       → Cria REL_2: cliente→CLI_002 (se mudou)
```

## Convenções e Padrões

### Detecção de Campos de Relacionamento

**Convenção Atual:** Campos `type="search"` com `datasource` são considerados relacionamentos.

**Exemplo de Spec:**
```json
{
  "fields": [
    {
      "name": "cliente",
      "label": "Cliente",
      "type": "search",
      "datasource": "clientes",
      "required": true
    }
  ]
}
```

**NÃO usar novo tipo "relationship"** - Reutilizar infraestrutura existente.

### Nomenclatura de Display Fields

**Padrão:** `_<field_name>_display`

**Exemplos:**
- Campo "cliente" → `_cliente_display`
- Campo "rt" → `_rt_display`
- Campo "orcamento" → `_orcamento_display`

### Tratamento de Erros

**Princípio:** Graceful degradation - nunca quebrar o fluxo principal.

**Estratégias:**
1. **Backend sem suporte:** Log debug, retorna/continua normalmente
2. **Erro ao criar relationship:** Log warning, mas cria o registro principal
3. **Erro ao obter display value:** Log debug, campo display ausente

## Backward Compatibility

✅ **Mantida:** Forms sem relacionamentos continuam funcionando normalmente.

**Como:**
- `_get_relationship_fields()` retorna lista vazia se não há campos search
- Helpers verificam se backend suporta relationships antes de usar
- Enriquecimento apenas adiciona campos, não modifica existentes

## Testes e Validação

### Testes Existentes

✅ Todos os 15 testes em `tests/test_form.py` passam:
- test_write_and_read_forms
- test_update_form
- test_delete_form
- test_validation
- (... outros 11 testes)

### Validação de Sintaxe

✅ `python3 -m py_compile src/controllers/forms.py` - OK

### Cenários de Teste Manual

#### Cenário 1: Criação com Relacionamento
1. Criar spec com campo search + datasource
2. Criar registro preenchendo o campo
3. Verificar:
   - Registro criado em tabela principal
   - Relationship criada em tabela relationships
   - Display value presente ao listar

#### Cenário 2: Edição de Relacionamento
1. Editar registro e mudar campo search
2. Verificar:
   - Relationship antiga soft-deleted
   - Nova relationship criada
   - Display value atualizado

#### Cenário 3: Backend sem Suporte
1. Usar backend TXT (não suporta relationships)
2. Verificar:
   - Registro criado normalmente
   - Nenhum erro no log
   - Sistema continua funcionando

## Limitações Conhecidas

1. **Performance:** Enriquecimento faz N queries (1 por relacionamento por registro)
   - Mitigação futura: Batch queries ou caching

2. **Cardinality:** Atualmente assume 1:1 para campos search
   - RelationshipRepository suporta 1:N e N:N, mas UI só mostra 1:1

3. **Validation:** Não valida se target_id existe antes de criar relationship
   - RelationshipRepository valida, mas erro só aparece no log

## Próximos Passos

### Melhorias Futuras

1. **Performance:**
   - Implementar batch loading de display values
   - Adicionar cache de display values

2. **UI Enhancements:**
   - Exibir relacionamentos na tela de edição
   - Permitir múltiplos relacionamentos (1:N)

3. **Validação:**
   - Validar target existence no frontend
   - Mostrar erros de relationship na UI

4. **Documentação:**
   - Adicionar exemplos de specs completas
   - Criar guia do desenvolvedor

## Referências

- **RelationshipRepository:** `/src/persistence/relationship_repository.py`
- **FormController:** `/src/controllers/forms.py`
- **Interface:** `/src/persistence/contracts/relationship_interface.py`
- **SQLite Adapter:** `/src/persistence/adapters/sqlite_adapter.py`

## Changelog

### 2026-01-09 - Implementação Inicial
- Adicionadas 3 funções helper para gerenciamento de relationships
- Modificado POST handler para salvar relationships
- Modificado PUT handler para atualizar relationships
- Adicionado endpoint API GET `/api/relationships/<type>/<id>`
- Modificado `read_forms()` para enriquecer com display values
- Todos os testes existentes passando
- Backward compatibility mantida

---

*Documento gerado por Arquiteto Agent - VibeCForms v3.0*
