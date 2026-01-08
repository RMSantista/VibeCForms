# Novo Paradigma de Persistência VibeCForms

**Data**: 2026-01-04
**Versão**: 1.0
**Autor**: Equipe Arquitetura VibeCForms
**Status**: 📋 Em Análise

---

## Sumário Executivo

Este documento apresenta uma proposta de mudança arquitetural fundamental no modelo de persistência do VibeCForms, transformando o paradigma de relacionamentos entidade-relacional tradicional para um modelo baseado em:

1. **UUIDs como chaves universais**
2. **Tabelas de relacionamento para TODOS os relacionamentos** (independente de cardinalidade)
3. **Desnormalização na tabela principal** (valores legíveis persistidos)

### Impacto Esperado

- ⚡ **Performance de leitura**: 5-10x mais rápida
- 🔄 **Flexibilidade**: Relacionamentos dinâmicos sem migrações
- 📊 **Auditoria**: Rastreabilidade total de relacionamentos
- ⚠️ **Trade-off**: Complexidade de escrita e sincronização

---

## 1. Contexto e Motivação

### 1.1 Estado Atual

O VibeCForms v2.0+ já implementa:
- ✅ UUIDs Crockford Base32 (27 caracteres)
- ✅ Repository Pattern com múltiplos backends
- ✅ Tags as State (relacionamentos via tags)
- ⚠️ Relacionamentos mistos: alguns via FK, outros via tabelas intermediárias

**Problema**: Inconsistência no tratamento de relacionamentos.

### 1.2 Visão do Novo Paradigma

```
┌─────────────────────────────────────────────────────────────────┐
│                     NOVO PARADIGMA                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REGRA 1: UUID como chave única universal                      │
│  ─────────────────────────────────────────                      │
│  Todos os objetos identificados por Crockford Base32           │
│                                                                 │
│  REGRA 2: Tabelas de relacionamento para TUDO                  │
│  ─────────────────────────────────────────────                  │
│  1:1, 1:N, N:N → sempre via tabela intermediária               │
│                                                                 │
│  REGRA 3: Desnormalização na tabela principal                  │
│  ─────────────────────────────────────────────                  │
│  Valores legíveis persistidos junto com UUIDs                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Análise Comparativa com Modelos Existentes

### 2.1 Modelo Tradicional vs. Modelo Proposto

**Cenário**: Pedido com Cliente e Produto

```sql
-- ═══════════════════════════════════════════════════════════════
-- MODELO TRADICIONAL (atual)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE pedidos (
    record_id TEXT PRIMARY KEY,
    cliente_id TEXT REFERENCES clientes(record_id),  -- FK direta
    produto_id TEXT REFERENCES produtos(record_id),  -- FK direta
    quantidade INTEGER,
    observacoes TEXT
);

-- Leitura requer JOIN
SELECT p.*, c.nome as cliente_nome, pr.nome as produto_nome
FROM pedidos p
JOIN clientes c ON p.cliente_id = c.record_id
JOIN produtos pr ON p.produto_id = pr.record_id;

-- ═══════════════════════════════════════════════════════════════
-- MODELO PROPOSTO
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE pedidos (
    record_id TEXT PRIMARY KEY,
    quantidade INTEGER,
    observacoes TEXT,

    -- Valores desnormalizados (display values)
    _cliente_display TEXT,      -- "João Silva"
    _produto_display TEXT,      -- "Notebook Dell XPS"

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE relationships (
    rel_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,      -- "pedidos"
    source_id TEXT NOT NULL,        -- UUID do pedido
    relationship_name TEXT NOT NULL, -- "cliente", "produto"
    target_type TEXT NOT NULL,      -- "clientes", "produtos"
    target_id TEXT NOT NULL,        -- UUID do cliente/produto
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    metadata TEXT,

    UNIQUE(source_type, source_id, relationship_name, target_id)
);

-- Leitura simples
SELECT * FROM pedidos;  -- Valores já disponíveis!

-- Navegação de relacionamentos (quando necessário)
SELECT r.*, c.*
FROM relationships r
JOIN clientes c ON r.target_id = c.record_id
WHERE r.source_type = 'pedidos'
  AND r.source_id = 'ABC123...';
```

### 2.2 Padrões Arquiteturais Similares

| Padrão | Similaridade | Características |
|--------|--------------|-----------------|
| **Graph Database** (Neo4j) | 85% | Relacionamentos como cidadãos de primeira classe |
| **Event Sourcing + CQRS** | 70% | Separação write model / read model |
| **Document Store** (MongoDB) | 60% | Embedding de valores relacionados |
| **EAV** (Entity-Attribute-Value) | 40% | Flexibilidade extrema de schema |

**Conclusão**: O modelo proposto é mais próximo de um **Graph DB híbrido com CQRS**.

---

## 3. Análise de Trade-offs

### 3.1 Vantagens ✅

| Aspecto | Benefício | Impacto Quantitativo |
|---------|-----------|----------------------|
| **Performance de Leitura** | Sem JOINs para exibição | ⚡ **5-10x mais rápido** |
| **Flexibilidade** | Relacionamentos dinâmicos | 🔄 Mudanças sem migração de schema |
| **Auditoria** | Histórico de relacionamentos | 📊 Rastreabilidade total + temporal queries |
| **Distribuição** | Sem FK = fácil sharding | 🌐 Escalabilidade horizontal |
| **Multi-cardinalidade** | Mesmo padrão para 1:1, 1:N, N:N | 🎯 Simplicidade conceitual |
| **Cache** | Objetos auto-contidos | 💾 Cache simples e eficiente |
| **Versionamento** | Snapshot histórico preservado | 🕐 Time-travel queries possíveis |
| **Convenção #3** | Alinhamento total | ✅ Fortalece arquitetura VibeCForms |

### 3.2 Desvantagens ⚠️

| Aspecto | Problema | Impacto | Mitigação |
|---------|----------|---------|-----------|
| **Consistência** | Dados duplicados podem divergir | 🔴 **Crítico** | Triggers de sync automático |
| **Atualização** | Cascade manual em múltiplas tabelas | 🟠 Complexidade | API abstrai operações |
| **Storage** | Dados repetidos ocupam espaço | 🟡 ~20-30% mais espaço | Compressão, cleanup jobs |
| **Escrita** | Múltiplas operações por transação | 🟠 2-3x mais lento | Batch operations, async |
| **Integridade** | Sem FK constraints nativas | 🔴 **Crítico** | Validação em camada aplicação |
| **Migração** | Transformação complexa | 🟡 Esforço pontual | Migração incremental |

### 3.3 Matriz de Decisão

```
                    LEITURA   ESCRITA   CONSISTÊNCIA   FLEXIBILIDADE   MANUTENÇÃO
Modelo Tradicional    ●○○       ●●●        ●●●            ●○○            ●●○
Modelo Proposto       ●●●       ●●○        ●●○            ●●●            ●○○

Legenda:
● = Excelente (3 pontos)
● = Bom (2 pontos)
○ = Regular (1 ponto)

SCORE TOTAL:
- Tradicional: 11/15 (73%)
- Proposto: 12/15 (80%)
```

---

## 4. Design Arquitetural Detalhado

### 4.1 Schema Completo

```sql
-- ═══════════════════════════════════════════════════════════════
-- TABELA PRINCIPAL (padrão para todas as formas)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE {form_path} (
    -- Chave primária
    record_id TEXT PRIMARY KEY,           -- UUID Crockford (27 chars)

    -- Metadados de sistema
    created_at TEXT NOT NULL,             -- ISO 8601
    updated_at TEXT NOT NULL,             -- ISO 8601
    created_by TEXT,                      -- Actor UUID
    updated_by TEXT,                      -- Actor UUID

    -- Campos do formulário (definidos na spec)
    {campo1} {tipo1},
    {campo2} {tipo2},
    ...

    -- Valores desnormalizados (display values)
    -- Padrão: _<nome_campo>_display
    _cliente_display TEXT,                -- Nome legível do cliente
    _produto_display TEXT,                -- Nome legível do produto
    _categoria_display TEXT               -- Nome legível da categoria
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA DE RELACIONAMENTOS UNIVERSAL
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE relationships (
    -- Chave primária
    rel_id TEXT PRIMARY KEY,              -- UUID do relacionamento

    -- Entidade origem
    source_type TEXT NOT NULL,            -- Form path: "pedidos"
    source_id TEXT NOT NULL,              -- UUID do registro origem

    -- Campo do relacionamento
    relationship_name TEXT NOT NULL,      -- Nome do campo: "cliente", "produtos"

    -- Entidade destino
    target_type TEXT NOT NULL,            -- Form path: "clientes", "produtos"
    target_id TEXT NOT NULL,              -- UUID do registro destino

    -- Metadados do relacionamento
    created_at TEXT NOT NULL,             -- ISO 8601
    created_by TEXT NOT NULL,             -- Actor UUID
    removed_at TEXT,                      -- Soft delete
    removed_by TEXT,                      -- Actor que removeu
    metadata TEXT,                        -- JSON adicional

    -- Constraint: evitar duplicatas
    UNIQUE(source_type, source_id, relationship_name, target_id)
);

-- Índices otimizados
CREATE INDEX idx_rel_source ON relationships(source_type, source_id);
CREATE INDEX idx_rel_target ON relationships(target_type, target_id);
CREATE INDEX idx_rel_name ON relationships(source_type, relationship_name);
CREATE INDEX idx_rel_active ON relationships(source_type, source_id, removed_at);

-- ═══════════════════════════════════════════════════════════════
-- VIEW HELPER: Relacionamentos Ativos
-- ═══════════════════════════════════════════════════════════════
CREATE VIEW active_relationships AS
SELECT *
FROM relationships
WHERE removed_at IS NULL;
```

### 4.2 Spec Atualizado

```json
{
  "title": "Pedidos",
  "icon": "fa-shopping-cart",
  "fields": [
    {
      "name": "cliente",
      "label": "Cliente",
      "type": "relationship",
      "target": "clientes",
      "cardinality": "one",
      "display_field": "nome",
      "required": true
    },
    {
      "name": "produtos",
      "label": "Produtos",
      "type": "relationship",
      "target": "produtos",
      "cardinality": "many",
      "display_field": "nome",
      "required": true
    },
    {
      "name": "quantidade",
      "label": "Quantidade",
      "type": "number",
      "required": true
    },
    {
      "name": "observacoes",
      "label": "Observações",
      "type": "textarea",
      "required": false
    }
  ],
  "relationships": {
    "cliente": {
      "type": "one_to_one",
      "sync_strategy": "eager"
    },
    "produtos": {
      "type": "one_to_many",
      "sync_strategy": "lazy"
    }
  }
}
```

### 4.3 Estratégias de Sincronização

```python
from enum import Enum

class SyncStrategy(Enum):
    """
    Estratégias para manter consistência entre relationships e display values
    """

    # ═══════════════════════════════════════════════════════════════
    # EAGER: Atualização imediata (consistência forte)
    # ═══════════════════════════════════════════════════════════════
    EAGER = "eager"
    # - Quando: Relacionamentos críticos (ex: cliente, fornecedor)
    # - Como: Trigger após UPDATE na tabela alvo
    # - Custo: Alto (I/O adicional imediato)
    # - Garantia: Consistência sempre

    # ═══════════════════════════════════════════════════════════════
    # LAZY: Atualização na próxima leitura (eventual consistency)
    # ═══════════════════════════════════════════════════════════════
    LAZY = "lazy"
    # - Quando: Relacionamentos não-críticos (ex: categorias, tags)
    # - Como: Check + update no método read_by_id()
    # - Custo: Médio (apenas se desatualizado)
    # - Garantia: Eventual (segundos a minutos)

    # ═══════════════════════════════════════════════════════════════
    # SCHEDULED: Job periódico (batch update)
    # ═══════════════════════════════════════════════════════════════
    SCHEDULED = "scheduled"
    # - Quando: Relacionamentos de análise (ex: estatísticas)
    # - Como: Cron job a cada N minutos
    # - Custo: Baixo (batch otimizado)
    # - Garantia: Eventual (minutos a horas)
```

### 4.4 API de Relacionamentos

```python
class RelationshipRepository:
    """
    Repository especializado para gerenciar relacionamentos
    """

    def create_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str,
        target_type: str,
        target_id: str,
        created_by: str,
        metadata: dict = None
    ) -> str:
        """
        Cria um relacionamento e atualiza display value

        Returns:
            rel_id: UUID do relacionamento criado
        """
        pass

    def remove_relationship(
        self,
        rel_id: str,
        removed_by: str
    ) -> bool:
        """
        Remove relacionamento (soft delete) e atualiza display value
        """
        pass

    def get_relationships(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str = None,
        active_only: bool = True
    ) -> list[dict]:
        """
        Lista relacionamentos de um objeto
        """
        pass

    def get_reverse_relationships(
        self,
        target_type: str,
        target_id: str,
        relationship_name: str = None
    ) -> list[dict]:
        """
        Lista objetos que apontam para este (navegação reversa)
        """
        pass

    def sync_display_values(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str = None
    ) -> bool:
        """
        Sincroniza valores de display de relacionamentos
        """
        pass
```

---

## 5. Avaliação de Performance

### 5.1 Cenários de Leitura

```
┌─────────────────────────────────────────────────────────────────┐
│ BENCHMARK: Listagem de Pedidos (100 registros)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ MODELO ATUAL (com JOINs):                                      │
│ ─────────────────────────                                      │
│ SELECT p.*, c.nome, pr.nome                                    │
│ FROM pedidos p                                                 │
│ JOIN clientes c ON p.cliente_id = c.record_id                  │
│ JOIN produtos pr ON p.produto_id = pr.record_id                │
│                                                                 │
│ Operações:                                                      │
│   - 3 table scans (pedidos, clientes, produtos)                │
│   - 2 hash joins                                               │
│   - Index lookups: ~200                                        │
│                                                                 │
│ Tempo estimado: ~50ms (3 tabelas, 2 JOINs)                     │
│                                                                 │
│ ───────────────────────────────────────────────────────────    │
│                                                                 │
│ MODELO PROPOSTO (desnormalizado):                              │
│ ──────────────────────────────────                             │
│ SELECT * FROM pedidos                                          │
│                                                                 │
│ Operações:                                                      │
│   - 1 table scan (pedidos)                                     │
│   - 0 joins                                                    │
│   - Index lookups: 0                                           │
│                                                                 │
│ Tempo estimado: ~5ms (1 tabela, 0 JOINs)                       │
│                                                                 │
│ ═══════════════════════════════════════════════════════════    │
│ GANHO: 10x mais rápido para leitura                            │
│ ═══════════════════════════════════════════════════════════    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Cenários de Escrita

```
┌─────────────────────────────────────────────────────────────────┐
│ BENCHMARK: Criar Pedido                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ MODELO ATUAL:                                                  │
│ ─────────────                                                  │
│ INSERT INTO pedidos (record_id, cliente_id, produto_id, ...)   │
│ VALUES ('ABC123', 'CLIENTE_UUID', 'PRODUTO_UUID', ...);        │
│                                                                 │
│ Operações:                                                      │
│   - 1 INSERT                                                   │
│   - 2 FK validations                                           │
│                                                                 │
│ Tempo estimado: ~10ms                                          │
│                                                                 │
│ ───────────────────────────────────────────────────────────    │
│                                                                 │
│ MODELO PROPOSTO:                                               │
│ ────────────────                                               │
│ BEGIN TRANSACTION;                                             │
│                                                                 │
│   -- 1. Buscar display values                                  │
│   SELECT nome FROM clientes WHERE record_id = 'CLIENTE_UUID';  │
│   SELECT nome FROM produtos WHERE record_id = 'PRODUTO_UUID';  │
│                                                                 │
│   -- 2. Inserir pedido com valores                             │
│   INSERT INTO pedidos (                                        │
│     record_id, quantidade,                                     │
│     _cliente_display, _produto_display                         │
│   ) VALUES ('ABC123', 10, 'João Silva', 'Notebook Dell');      │
│                                                                 │
│   -- 3. Criar relacionamentos                                  │
│   INSERT INTO relationships (                                  │
│     rel_id, source_type, source_id,                            │
│     relationship_name, target_type, target_id, ...             │
│   ) VALUES ('REL001', 'pedidos', 'ABC123',                     │
│              'cliente', 'clientes', 'CLIENTE_UUID', ...);       │
│                                                                 │
│   INSERT INTO relationships (...)                              │
│   VALUES ('REL002', 'pedidos', 'ABC123',                       │
│            'produto', 'produtos', 'PRODUTO_UUID', ...);         │
│                                                                 │
│ COMMIT;                                                        │
│                                                                 │
│ Operações:                                                      │
│   - 2 SELECTs (buscar display)                                 │
│   - 1 INSERT (pedido)                                          │
│   - 2 INSERTs (relationships)                                  │
│   - Total: 5 operações em transação                            │
│                                                                 │
│ Tempo estimado: ~25ms (2.5x mais lento)                        │
│                                                                 │
│ ═══════════════════════════════════════════════════════════    │
│ CUSTO: 2-3x mais lento para escrita (ACEITÁVEL)                │
│ ═══════════════════════════════════════════════════════════    │
│                                                                 │
│ Nota: Em sistemas read-heavy (90% leitura), o ganho global     │
│       é significativo mesmo com escrita mais lenta.             │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Cenários de Atualização

```
┌─────────────────────────────────────────────────────────────────┐
│ BENCHMARK: Atualizar Nome de Cliente                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ MODELO ATUAL:                                                  │
│ ─────────────                                                  │
│ UPDATE clientes SET nome = 'João Silva Santos'                 │
│ WHERE record_id = 'CLIENTE_UUID';                              │
│                                                                 │
│ Operações: 1 UPDATE                                            │
│ Tempo: ~5ms                                                    │
│ Propagação: Automática (JOIN em leitura)                       │
│                                                                 │
│ ───────────────────────────────────────────────────────────    │
│                                                                 │
│ MODELO PROPOSTO (Sync EAGER):                                 │
│ ──────────────────────────────                                 │
│ BEGIN TRANSACTION;                                             │
│                                                                 │
│   -- 1. Atualizar cliente                                      │
│   UPDATE clientes SET nome = 'João Silva Santos'               │
│   WHERE record_id = 'CLIENTE_UUID';                            │
│                                                                 │
│   -- 2. Sincronizar display values (via trigger)               │
│   UPDATE pedidos                                               │
│   SET _cliente_display = 'João Silva Santos',                  │
│       updated_at = CURRENT_TIMESTAMP                           │
│   WHERE record_id IN (                                         │
│     SELECT source_id FROM relationships                        │
│     WHERE target_id = 'CLIENTE_UUID'                           │
│       AND relationship_name = 'cliente'                        │
│   );                                                           │
│                                                                 │
│ COMMIT;                                                        │
│                                                                 │
│ Operações:                                                      │
│   - 1 UPDATE (cliente)                                         │
│   - 1 SELECT (buscar relacionamentos)                          │
│   - N UPDATEs (pedidos relacionados)                           │
│                                                                 │
│ Tempo: ~15ms (para 10 pedidos relacionados)                    │
│                                                                 │
│ ───────────────────────────────────────────────────────────    │
│                                                                 │
│ MODELO PROPOSTO (Sync LAZY):                                  │
│ ─────────────────────────────                                  │
│ UPDATE clientes SET nome = 'João Silva Santos'                 │
│ WHERE record_id = 'CLIENTE_UUID';                              │
│                                                                 │
│ -- Sincronização adiada para próxima leitura                   │
│                                                                 │
│ Tempo: ~5ms (mesma performance)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Riscos e Mitigações

### 6.1 Matriz de Riscos

| ID | Risco | Probabilidade | Impacto | Severidade | Mitigação |
|----|-------|---------------|---------|------------|-----------|
| R1 | Dados inconsistentes após atualização | Média (40%) | Alto | 🔴 **Crítico** | Triggers de sincronização + jobs de validação |
| R2 | Storage aumentado significativamente | Alta (70%) | Baixo | 🟡 Moderado | Compressão + cleanup jobs periódicos |
| R3 | Queries complexas difíceis de otimizar | Baixa (20%) | Médio | 🟡 Moderado | Abstrair no Repository + índices adequados |
| R4 | Migração de dados falha parcialmente | Média (30%) | Alto | 🔴 **Crítico** | Backup completo + migração incremental + rollback plan |
| R5 | Performance de escrita degrada | Média (50%) | Médio | 🟠 Atenção | Batch operations + async processing |
| R6 | Falta de integridade referencial | Baixa (15%) | Alto | 🟠 Atenção | Validação em camada aplicação + monitoring |
| R7 | Desenvolvedores não seguem padrão | Alta (60%) | Médio | 🟠 Atenção | Documentação + code review + linters |

### 6.2 Plano de Mitigação Detalhado

#### R1: Inconsistência de Dados

**Estratégias**:

1. **Triggers de Sincronização (SQLite)**:
```sql
CREATE TRIGGER sync_cliente_display
AFTER UPDATE ON clientes
FOR EACH ROW
WHEN NEW.nome != OLD.nome
BEGIN
    UPDATE pedidos
    SET _cliente_display = NEW.nome,
        updated_at = CURRENT_TIMESTAMP
    WHERE record_id IN (
        SELECT source_id FROM relationships
        WHERE target_id = NEW.record_id
          AND relationship_name = 'cliente'
          AND removed_at IS NULL
    );
END;
```

2. **Job de Validação Periódico**:
```python
def validate_consistency():
    """
    Valida se display values estão sincronizados
    """
    inconsistencies = []

    # Para cada relacionamento ativo
    for rel in relationships.all(active_only=True):
        # Buscar valor real
        actual_value = get_display_value(rel.target_type, rel.target_id)

        # Buscar valor armazenado
        stored_value = get_stored_display(rel.source_type, rel.source_id, rel.name)

        # Comparar
        if actual_value != stored_value:
            inconsistencies.append({
                'relationship': rel.rel_id,
                'expected': actual_value,
                'found': stored_value
            })

    return inconsistencies
```

#### R4: Falha na Migração

**Plano de Rollback**:

```bash
#!/bin/bash
# rollback_migration.sh

echo "Iniciando rollback da migração..."

# 1. Restaurar backup
cp data/backup/vibecforms_pre_migration.db data/sqlite/vibecforms.db

# 2. Restaurar código anterior
git checkout v2.4.0

# 3. Reiniciar serviço
systemctl restart vibecforms

# 4. Validar
python scripts/validate_rollback.py

echo "Rollback concluído!"
```

---

## 7. Alinhamento com Convenções VibeCForms

### 7.1 Impacto nas 8 Convenções

| # | Convenção | Status Atual | Status Proposto | Impacto |
|---|-----------|--------------|-----------------|---------|
| 1 | 1:1 CRUD-to-Table | ✅ Implementada | ✅ **Mantida** | Sem mudança |
| 2 | Shared Metadata | ✅ Implementada | ✅ **Mantida** | Spec define relationships |
| 3 | Relationship Tables | ⚠️ Opcional | ✅ **OBRIGATÓRIA** | Torna-se regra universal |
| 4 | Tags as State | ✅ Implementada | ✅ **Mantida** | Tags são tipo especial de rel |
| 5 | Kanbans for Transitions | ✅ Implementada | ✅ **Mantida** | Não afetado |
| 6 | Uniform Actor Interface | ✅ Implementada | ✅ **Mantida** | API abstrai complexidade |
| 7 | Tag-Based Notifications | ⚠️ Padrão | ✅ **Expandida** | Notificações em relationships |
| 8 | Convention > Config > Code | ✅ Implementada | ✅ **FORTALECIDA** | Nova convenção clara |

### 7.2 Nova Convenção Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONVENÇÃO #9                                 │
│              Universal Relationship Pattern                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TODO relacionamento, independente de cardinalidade,            │
│  DEVE ser representado em duas camadas:                         │
│                                                                 │
│  1. CAMADA DE LEITURA (tabela principal)                       │
│     - Display values (_<campo>_display)                        │
│     - Otimizada para velocidade                                │
│                                                                 │
│  2. CAMADA DE NAVEGAÇÃO (relationships)                        │
│     - UUIDs para navegação                                     │
│     - Source of truth                                          │
│                                                                 │
│  Sincronização DEVE ser gerenciada automaticamente             │
│  baseada em sync_strategy definida na spec.                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Arquitetura Híbrida Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                     ARQUITETURA HÍBRIDA                         │
│                      (CQRS-inspired)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────┐      ┌─────────────────────────┐   │
│  │   WRITE MODEL          │      │   READ MODEL            │   │
│  │   (Source of Truth)    │      │   (Optimized)           │   │
│  ├────────────────────────┤      ├─────────────────────────┤   │
│  │                        │      │                         │   │
│  │ relationships          │─sync─▶│ {form}_display_values  │   │
│  │ ─────────────          │      │ ─────────────────────   │   │
│  │ - rel_id (PK)          │      │ Dentro da tabela        │   │
│  │ - source_id            │      │ principal:              │   │
│  │ - target_id            │      │   _cliente_display      │   │
│  │ - metadata             │      │   _produto_display      │   │
│  │ - created_at           │      │   ...                   │   │
│  │                        │      │                         │   │
│  │ Normalizado            │      │ Desnormalizado          │   │
│  │ Consistência ●●●       │      │ Velocidade ●●●          │   │
│  │ Velocidade   ●○○       │      │ Consistência ●●○        │   │
│  │                        │      │                         │   │
│  └────────────────────────┘      └─────────────────────────┘   │
│           │                                  ▲                  │
│           │                                  │                  │
│           │      ┌──────────────────┐       │                  │
│           │      │  SYNC ENGINE     │       │                  │
│           └─────▶│  ──────────────  │───────┘                  │
│                  │  - Triggers      │                          │
│                  │  - Lazy load     │                          │
│                  │  - Scheduled job │                          │
│                  └──────────────────┘                          │
│                                                                 │
│  API UNIFICADA (BaseRepository)                                │
│  ─────────────────────────────────                             │
│  create(), read_by_id(), update(), delete()                    │
│  → Transparência total para o desenvolvedor                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Plano de Implementação Detalhado

### 9.1 Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────┐
│                   TIMELINE DE IMPLEMENTAÇÃO                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Fase 1: Design & Prototipagem        [████░░░░░░] 2 semanas   │
│  Fase 2: Implementação Core           [████████░░] 4 semanas   │
│  Fase 3: Sincronização & Triggers     [██████░░░░] 3 semanas   │
│  Fase 4: Migração de Dados            [████░░░░░░] 2 semanas   │
│  Fase 5: Testes & Validação           [██████░░░░] 3 semanas   │
│  Fase 6: Documentação & Rollout       [████░░░░░░] 2 semanas   │
│                                                                 │
│  TOTAL ESTIMADO: 16 semanas (4 meses)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### FASE 1: Design & Prototipagem

**Duração**: 2 semanas
**Objetivo**: Validar conceito e definir contratos de API

#### 1.1 Atividades

##### 1.1.1 Definição de Schema (3 dias)

**Entregáveis**:

```sql
-- File: docs/design/schema_relationships.sql

-- Versão final do schema relationships
CREATE TABLE relationships (
    rel_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    relationship_name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    removed_at TEXT,
    removed_by TEXT,
    metadata TEXT,

    UNIQUE(source_type, source_id, relationship_name, target_id)
);

-- Índices
CREATE INDEX idx_rel_source ON relationships(source_type, source_id);
CREATE INDEX idx_rel_target ON relationships(target_type, target_id);
CREATE INDEX idx_rel_name ON relationships(source_type, relationship_name);
CREATE INDEX idx_rel_active ON relationships(source_type, source_id, removed_at);

-- Views auxiliares
CREATE VIEW active_relationships AS
SELECT * FROM relationships WHERE removed_at IS NULL;
```

##### 1.1.2 Definição de Contratos de API (4 dias)

**Entregáveis**:

```python
# File: src/persistence/contracts/relationship_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum

class SyncStrategy(Enum):
    EAGER = "eager"
    LAZY = "lazy"
    SCHEDULED = "scheduled"

class IRelationshipRepository(ABC):
    """
    Interface para gerenciamento de relacionamentos
    """

    @abstractmethod
    def create_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_name: str,
        target_type: str,
        target_id: str,
        created_by: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Cria um relacionamento entre dois objetos

        Args:
            source_type: Form path da entidade origem (ex: "pedidos")
            source_id: UUID do registro origem
            relationship_name: Nome do campo de relacionamento (ex: "cliente")
            target_type: Form path da entidade destino (ex: "clientes")
            target_id: UUID do registro destino
            created_by: UUID do actor que criou
            metadata: Dados adicionais (opcional)

        Returns:
            rel_id: UUID do relacionamento criado

        Raises:
            ValidationError: Se dados inválidos
            TargetNotFoundError: Se target_id não existe
        """
        pass

    @abstractmethod
    def remove_relationship(
        self,
        rel_id: str,
        removed_by: str
    ) -> bool:
        """
        Remove relacionamento (soft delete)
        """
        pass

    @abstractmethod
    def get_relationships(
        self,
        source_type: str,
        source_id: str,
        relationship_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Lista relacionamentos de um objeto
        """
        pass

    @abstractmethod
    def sync_display_values(
        self,
        source_type: str,
        source_id: str,
        relationship_name: Optional[str] = None
    ) -> bool:
        """
        Sincroniza valores de display
        """
        pass
```

##### 1.1.3 Prototipagem (5 dias)

**Entregáveis**:

```python
# File: prototypes/relationship_poc.py

"""
Proof of Concept: Relacionamentos com display values
"""

import sqlite3
from datetime import datetime

def create_poc_database():
    """Cria banco de dados de prova de conceito"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Tabela clientes
    cursor.execute("""
        CREATE TABLE clientes (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL
        )
    """)

    # Tabela pedidos (com display)
    cursor.execute("""
        CREATE TABLE pedidos (
            record_id TEXT PRIMARY KEY,
            quantidade INTEGER,
            _cliente_display TEXT
        )
    """)

    # Tabela relationships
    cursor.execute("""
        CREATE TABLE relationships (
            rel_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relationship_name TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    """)

    return conn

def test_create_with_relationship():
    """Testa criação de pedido com relacionamento"""
    conn = create_poc_database()
    cursor = conn.cursor()

    # 1. Criar cliente
    cursor.execute("""
        INSERT INTO clientes (record_id, nome)
        VALUES ('CLIENTE_001', 'João Silva')
    """)

    # 2. Criar pedido com display value
    cursor.execute("""
        INSERT INTO pedidos (record_id, quantidade, _cliente_display)
        VALUES ('PEDIDO_001', 10, 'João Silva')
    """)

    # 3. Criar relationship
    cursor.execute("""
        INSERT INTO relationships (
            rel_id, source_type, source_id,
            relationship_name, target_type, target_id,
            created_at, created_by
        ) VALUES (
            'REL_001', 'pedidos', 'PEDIDO_001',
            'cliente', 'clientes', 'CLIENTE_001',
            ?, 'system'
        )
    """, (datetime.now().isoformat(),))

    conn.commit()

    # 4. Verificar leitura rápida
    result = cursor.execute("""
        SELECT record_id, quantidade, _cliente_display
        FROM pedidos
        WHERE record_id = 'PEDIDO_001'
    """).fetchone()

    print(f"Pedido: {result}")  # PEDIDO_001, 10, João Silva
    print("✅ Leitura sem JOIN!")

if __name__ == '__main__':
    test_create_with_relationship()
```

#### 1.2 Critérios de Conclusão

- [ ] Schema final aprovado pela equipe
- [ ] Contratos de API definidos e documentados
- [ ] POC validado com cenários reais
- [ ] Performance medida e aceita (>5x leitura)

---

### FASE 2: Implementação Core

**Duração**: 4 semanas
**Objetivo**: Implementar RelationshipRepository e integrar com BaseRepository

#### 2.1 Atividades

##### 2.1.1 Criar RelationshipRepository (1 semana)

**Arquivo**: `src/persistence/relationship_repository.py`

**Tarefas**:

1. Implementar `create_relationship()` (2 dias)
```python
def create_relationship(self, source_type, source_id, relationship_name,
                       target_type, target_id, created_by, metadata=None):
    # 1. Validar que target existe
    # 2. Gerar rel_id
    # 3. INSERT em relationships
    # 4. Atualizar display value (se sync=eager)
    # 5. Retornar rel_id
```

2. Implementar `get_relationships()` (1 dia)
```python
def get_relationships(self, source_type, source_id,
                     relationship_name=None, active_only=True):
    # 1. SELECT em relationships com filtros
    # 2. JOIN com target (opcional) para enriquecer
    # 3. Retornar lista de dicts
```

3. Implementar `remove_relationship()` (1 dia)
```python
def remove_relationship(self, rel_id, removed_by):
    # 1. Soft delete (UPDATE removed_at)
    # 2. Atualizar display value (se sync=eager)
    # 3. Retornar bool
```

4. Implementar `sync_display_values()` (2 dias)
```python
def sync_display_values(self, source_type, source_id, relationship_name=None):
    # 1. Buscar relationships ativos
    # 2. Para cada relationship:
    #    a. Buscar valor atual do target
    #    b. Comparar com display armazenado
    #    c. UPDATE se diferente
    # 3. Retornar count de atualizações
```

##### 2.1.2 Integrar com BaseRepository (1 semana)

**Tarefas**:

1. Adicionar métodos à interface `BaseRepository` (1 dia)
```python
# File: src/persistence/base.py

class BaseRepository(ABC):
    # ... métodos existentes ...

    @abstractmethod
    def create_with_relationships(
        self, form_path, spec, data, relationships, created_by
    ) -> str:
        """Cria registro + relationships em transação"""
        pass

    @abstractmethod
    def update_with_relationships(
        self, form_path, spec, record_id, data, relationships, updated_by
    ) -> bool:
        """Atualiza registro + relationships"""
        pass
```

2. Implementar em `SQLiteRepository` (3 dias)
```python
# File: src/persistence/adapters/sqlite_adapter.py

def create_with_relationships(self, form_path, spec, data, relationships, created_by):
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
        # 1. Criar registro principal
        record_id = self._generate_id()

        # 2. Processar relationships e buscar display values
        display_values = {}
        for rel in relationships:
            display_value = self._get_display_value(
                rel['target_type'],
                rel['target_id'],
                rel.get('display_field', 'nome')
            )
            display_values[f"_{rel['name']}_display"] = display_value

        # 3. INSERT com display values
        data.update(display_values)
        self._insert_record(cursor, form_path, spec, record_id, data)

        # 4. Criar relationships
        rel_repo = RelationshipRepository(conn)
        for rel in relationships:
            rel_repo.create_relationship(
                source_type=form_path,
                source_id=record_id,
                relationship_name=rel['name'],
                target_type=rel['target_type'],
                target_id=rel['target_id'],
                created_by=created_by
            )

        conn.commit()
        return record_id

    except Exception as e:
        conn.rollback()
        raise
```

3. Implementar em `TxtRepository` (2 dias)

##### 2.1.3 Atualizar Specs (1 semana)

**Tarefas**:

1. Criar novo tipo de campo `relationship` (2 dias)
```json
{
  "name": "cliente",
  "label": "Cliente",
  "type": "relationship",
  "target": "clientes",
  "cardinality": "one",
  "display_field": "nome",
  "sync_strategy": "eager",
  "required": true
}
```

2. Implementar validação de specs (2 dias)
```python
# File: src/utils/spec_validator.py

def validate_relationship_field(field_def, all_specs):
    # 1. Verificar que target existe
    # 2. Validar cardinality (one, many)
    # 3. Validar sync_strategy (eager, lazy, scheduled)
    # 4. Verificar se display_field existe no target
```

3. Converter specs existentes (search → relationship) (1 dia)

##### 2.1.4 Atualizar Forms Controller (1 semana)

**Tarefas**:

1. Modificar `save_form()` para processar relationships (3 dias)
```python
# File: src/controllers/forms.py

@app.route('/forms/<path:form_path>/save', methods=['POST'])
def save_form(form_path):
    data = request.json

    # Separar campos normais de relationships
    normal_fields = {}
    relationships = []

    for field_name, value in data.items():
        field_def = spec.get_field(field_name)

        if field_def['type'] == 'relationship':
            relationships.append({
                'name': field_name,
                'target_type': field_def['target'],
                'target_id': value,  # UUID selecionado
                'display_field': field_def.get('display_field', 'nome')
            })
        else:
            normal_fields[field_name] = value

    # Criar com relationships
    record_id = repo.create_with_relationships(
        form_path, spec, normal_fields, relationships,
        created_by=current_user()
    )

    return jsonify({'record_id': record_id})
```

2. Criar API de navegação de relacionamentos (2 dias)
```python
@app.route('/api/relationships/<source_type>/<source_id>')
def get_relationships(source_type, source_id):
    rel_repo = RelationshipRepository()
    relationships = rel_repo.get_relationships(source_type, source_id)
    return jsonify(relationships)

@app.route('/api/relationships/reverse/<target_type>/<target_id>')
def get_reverse_relationships(target_type, target_id):
    rel_repo = RelationshipRepository()
    relationships = rel_repo.get_reverse_relationships(target_type, target_id)
    return jsonify(relationships)
```

#### 2.2 Critérios de Conclusão

- [ ] RelationshipRepository implementado e testado
- [ ] BaseRepository integrado em SQLite e TXT
- [ ] Specs atualizadas com tipo `relationship`
- [ ] Forms Controller processa relationships
- [ ] Testes unitários passando (>80% cobertura)

---

### FASE 3: Sincronização & Triggers

**Duração**: 3 semanas
**Objetivo**: Implementar mecanismos de sincronização automática

#### 3.1 Atividades

##### 3.1.1 Implementar Sync Engine (1.5 semanas)

**Arquivo**: `src/persistence/sync_engine.py`

**Tarefas**:

1. Criar SyncEngine base (2 dias)
```python
class SyncEngine:
    """
    Engine central de sincronização de display values
    """

    def __init__(self, repository):
        self.repo = repository
        self.strategies = {
            'eager': EagerSyncStrategy(repository),
            'lazy': LazySyncStrategy(repository),
            'scheduled': ScheduledSyncStrategy(repository)
        }

    def sync(self, source_type, source_id, relationship_name, strategy='eager'):
        """Delega para estratégia apropriada"""
        return self.strategies[strategy].sync(
            source_type, source_id, relationship_name
        )
```

2. Implementar EagerSyncStrategy (3 dias)
```python
class EagerSyncStrategy:
    """Sincronização imediata"""

    def sync(self, source_type, source_id, relationship_name):
        # 1. Buscar relationship
        rel = self.repo.get_relationship(source_type, source_id, relationship_name)

        # 2. Buscar valor atual do target
        target_value = self.repo.read_by_id(
            rel['target_type'],
            None,
            rel['target_id']
        )
        display_value = target_value.get(rel['display_field'])

        # 3. Atualizar display na source
        self.repo.update_display_value(
            source_type, source_id,
            f"_{relationship_name}_display",
            display_value
        )
```

3. Implementar LazySyncStrategy (2 dias)
```python
class LazySyncStrategy:
    """Sincronização na leitura"""

    def sync(self, source_type, source_id, relationship_name):
        # Marca para sincronização futura
        # Implementado em read_by_id()
        pass
```

4. Implementar ScheduledSyncStrategy (3 dias)
```python
class ScheduledSyncStrategy:
    """Sincronização via job"""

    def schedule_sync(self, source_type, source_id, relationship_name):
        # Adiciona à fila de sincronização
        sync_queue.add({
            'source_type': source_type,
            'source_id': source_id,
            'relationship_name': relationship_name,
            'scheduled_at': datetime.now()
        })
```

##### 3.1.2 Criar Triggers SQLite (1 semana)

**Tarefas**:

1. Criar trigger de atualização (2 dias)
```sql
-- File: src/persistence/sql/triggers/sync_display_values.sql

-- Trigger: Quando target é atualizado, sincronizar display
CREATE TRIGGER IF NOT EXISTS sync_display_on_update_{target_table}
AFTER UPDATE ON {target_table}
FOR EACH ROW
WHEN NEW.{display_field} != OLD.{display_field}
BEGIN
    -- Atualizar display values em todas as tabelas que referenciam
    UPDATE {source_table}
    SET _{relationship_name}_display = NEW.{display_field},
        updated_at = CURRENT_TIMESTAMP
    WHERE record_id IN (
        SELECT source_id
        FROM relationships
        WHERE target_type = '{target_table}'
          AND target_id = NEW.record_id
          AND relationship_name = '{relationship_name}'
          AND removed_at IS NULL
    );
END;
```

2. Gerar triggers dinamicamente (3 days)
```python
# File: src/persistence/trigger_generator.py

class TriggerGenerator:
    """
    Gera triggers de sincronização baseado nas specs
    """

    def generate_triggers_for_spec(self, spec):
        triggers = []

        # Para cada campo de relationship na spec
        for field in spec['fields']:
            if field['type'] == 'relationship':
                if field.get('sync_strategy') == 'eager':
                    trigger_sql = self._create_sync_trigger(
                        source_table=spec['form_path'],
                        target_table=field['target'],
                        relationship_name=field['name'],
                        display_field=field.get('display_field', 'nome')
                    )
                    triggers.append(trigger_sql)

        return triggers

    def install_triggers(self, conn, triggers):
        for trigger in triggers:
            conn.execute(trigger)
```

##### 3.1.3 Implementar Job de Sincronização (0.5 semana)

**Tarefas**:

1. Criar script de sync job (2 dias)
```python
# File: scripts/sync_display_values_job.py

"""
Job periódico para sincronização de display values (strategy=scheduled)
"""

import schedule
import time
from persistence.sync_engine import SyncEngine

def sync_all_scheduled():
    """Sincroniza todos os relationships com strategy=scheduled"""

    engine = SyncEngine(repository)

    # Buscar todos os relationships com strategy=scheduled
    scheduled_rels = engine.repo.get_scheduled_relationships()

    count = 0
    for rel in scheduled_rels:
        engine.sync(
            rel['source_type'],
            rel['source_id'],
            rel['relationship_name'],
            strategy='scheduled'
        )
        count += 1

    print(f"✅ Sincronizados {count} relacionamentos")

if __name__ == '__main__':
    # Executar a cada 5 minutos
    schedule.every(5).minutes.do(sync_all_scheduled)

    while True:
        schedule.run_pending()
        time.sleep(60)
```

#### 3.2 Critérios de Conclusão

- [ ] SyncEngine implementado com 3 estratégias
- [ ] Triggers SQLite gerando e instalando corretamente
- [ ] Job de sincronização rodando e testado
- [ ] Performance de sync aceitável (<100ms)

---

### FASE 4: Migração de Dados

**Duração**: 2 semanas
**Objetivo**: Migrar dados existentes para novo modelo

#### 4.1 Atividades

##### 4.1.1 Criar Script de Migração (1 semana)

**Arquivo**: `scripts/migrate_to_relationships.py`

**Tarefas**:

1. Analisar dados existentes (2 dias)
```python
def analyze_existing_data():
    """
    Analisa banco atual para identificar:
    - Campos que são FKs (search type)
    - Quantidade de relacionamentos
    - Estimativa de display values a criar
    """

    analysis = {
        'forms': [],
        'total_relationships': 0,
        'estimated_storage_increase': 0
    }

    for spec in all_specs:
        search_fields = [f for f in spec['fields'] if f['type'] == 'search']

        for field in search_fields:
            count = repo.count_non_null(spec['form_path'], field['name'])
            analysis['total_relationships'] += count
            analysis['forms'].append({
                'form': spec['form_path'],
                'field': field['name'],
                'count': count
            })

    return analysis
```

2. Implementar migração (3 days)
```python
def migrate_form(form_path, spec, dry_run=False):
    """
    Migra uma forma do modelo antigo para novo
    """

    print(f"Migrando {form_path}...")

    # 1. Backup
    if not dry_run:
        backup_table(form_path)

    # 2. Criar coluna display para cada relationship
    search_fields = [f for f in spec['fields'] if f['type'] == 'search']

    for field in search_fields:
        column_name = f"_{field['name']}_display"
        if not dry_run:
            add_column(form_path, column_name, 'TEXT')

    # 3. Migrar dados
    records = repo.read_all(form_path, spec)

    for record in records:
        relationships = []
        display_updates = {}

        # Para cada campo search
        for field in search_fields:
            target_id = record.get(field['name'])
            if target_id:
                # Buscar display value
                target_spec = load_spec(field['datasource'])
                target_record = repo.read_by_id(
                    field['datasource'], target_spec, target_id
                )

                display_value = target_record.get('nome', str(target_id))
                display_updates[f"_{field['name']}_display"] = display_value

                # Criar relationship
                relationships.append({
                    'source_type': form_path,
                    'source_id': record['_record_id'],
                    'relationship_name': field['name'],
                    'target_type': field['datasource'],
                    'target_id': target_id
                })

        # Atualizar registro
        if not dry_run:
            repo.update_by_id(
                form_path, spec, record['_record_id'], display_updates
            )

            # Criar relationships
            for rel in relationships:
                rel_repo.create_relationship(**rel, created_by='migration')

    print(f"✅ {form_path}: {len(records)} registros migrados")

def migrate_all(dry_run=True):
    """Migra todos os forms"""

    print("=" * 60)
    print("MIGRAÇÃO PARA NOVO PARADIGMA DE PERSISTÊNCIA")
    print("=" * 60)

    if dry_run:
        print("⚠️  MODO DRY RUN - Nenhuma alteração será feita")

    analysis = analyze_existing_data()
    print(f"\nTotal de relacionamentos a migrar: {analysis['total_relationships']}")
    print(f"Aumento estimado de storage: {analysis['estimated_storage_increase']}MB")

    if not dry_run:
        confirm = input("\n⚠️  CONFIRMAR MIGRAÇÃO? (sim/não): ")
        if confirm.lower() != 'sim':
            print("Migração cancelada.")
            return

    for spec in all_specs:
        migrate_form(spec['form_path'], spec, dry_run)

    print("\n✅ Migração concluída!")
```

##### 4.1.2 Testes de Migração (1 semana)

**Tarefas**:

1. Criar ambiente de teste (1 dia)
```bash
# Copiar dados de produção para teste
cp data/sqlite/vibecforms.db data/sqlite/vibecforms_test.db
```

2. Executar migração em teste (2 dias)
```bash
# Dry run
python scripts/migrate_to_relationships.py --dry-run

# Migração real em teste
python scripts/migrate_to_relationships.py --database=vibecforms_test.db
```

3. Validar resultados (2 dias)
```python
# File: scripts/validate_migration.py

def validate_migration():
    """Valida que migração foi bem-sucedida"""

    issues = []

    # 1. Verificar que relationships foram criados
    for spec in all_specs:
        expected_count = count_search_fields(spec)
        actual_count = count_relationships(spec['form_path'])

        if expected_count != actual_count:
            issues.append({
                'form': spec['form_path'],
                'expected': expected_count,
                'actual': actual_count
            })

    # 2. Verificar display values
    for spec in all_specs:
        records = repo.read_all(spec['form_path'], spec)

        for record in records:
            for field in spec['fields']:
                if field['type'] == 'relationship':
                    display_col = f"_{field['name']}_display"

                    if display_col not in record:
                        issues.append({
                            'form': spec['form_path'],
                            'record_id': record['_record_id'],
                            'missing_display': field['name']
                        })

    # 3. Report
    if issues:
        print(f"❌ {len(issues)} problemas encontrados:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Migração validada com sucesso!")
        return True
```

#### 4.2 Critérios de Conclusão

- [ ] Script de migração implementado e testado
- [ ] Migração executada em ambiente de teste
- [ ] Validação passando sem erros
- [ ] Rollback testado e funcional
- [ ] Documentação de migração completa

---

### FASE 5: Testes & Validação

**Duração**: 3 semanas
**Objetivo**: Garantir qualidade e performance

#### 5.1 Atividades

##### 5.1.1 Testes Unitários (1 semana)

**Tarefas**:

1. Testes de RelationshipRepository (2 dias)
```python
# File: tests/persistence/test_relationship_repository.py

import pytest
from persistence.relationship_repository import RelationshipRepository

class TestRelationshipRepository:

    def test_create_relationship(self, db):
        repo = RelationshipRepository(db)

        rel_id = repo.create_relationship(
            source_type='pedidos',
            source_id='PEDIDO_001',
            relationship_name='cliente',
            target_type='clientes',
            target_id='CLIENTE_001',
            created_by='test'
        )

        assert rel_id is not None
        assert len(rel_id) == 27  # Crockford UUID

    def test_get_relationships(self, db):
        repo = RelationshipRepository(db)

        # Criar relacionamentos
        repo.create_relationship(...)

        # Buscar
        rels = repo.get_relationships('pedidos', 'PEDIDO_001')

        assert len(rels) == 1
        assert rels[0]['relationship_name'] == 'cliente'

    def test_sync_display_values(self, db):
        repo = RelationshipRepository(db)

        # Criar pedido com cliente
        # Atualizar nome do cliente
        # Sincronizar
        repo.sync_display_values('pedidos', 'PEDIDO_001', 'cliente')

        # Verificar que display foi atualizado
        pedido = repo.read_by_id('pedidos', None, 'PEDIDO_001')
        assert pedido['_cliente_display'] == 'João Silva Santos'
```

2. Testes de SyncEngine (2 dias)
3. Testes de integração (1 dia)

##### 5.1.2 Testes de Performance (1 semana)

**Tarefas**:

1. Benchmark de leitura (2 dias)
```python
# File: tests/performance/benchmark_read.py

import time

def benchmark_read_traditional():
    """Leitura com JOINs"""
    start = time.time()

    results = db.execute("""
        SELECT p.*, c.nome, pr.nome
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.record_id
        JOIN produtos pr ON p.produto_id = pr.record_id
        LIMIT 100
    """).fetchall()

    elapsed = (time.time() - start) * 1000
    print(f"Tradicional: {elapsed:.2f}ms")
    return elapsed

def benchmark_read_new_model():
    """Leitura desnormalizada"""
    start = time.time()

    results = db.execute("""
        SELECT * FROM pedidos LIMIT 100
    """).fetchall()

    elapsed = (time.time() - start) * 1000
    print(f"Novo modelo: {elapsed:.2f}ms")
    return elapsed

if __name__ == '__main__':
    traditional = benchmark_read_traditional()
    new_model = benchmark_read_new_model()

    improvement = traditional / new_model
    print(f"\n✅ Melhoria: {improvement:.1f}x mais rápido")
```

2. Benchmark de escrita (2 dias)
3. Benchmark de sincronização (1 dia)

##### 5.1.3 Testes de Integridade (1 semana)

**Tarefas**:

1. Testes de consistência (3 dias)
```python
# File: tests/integrity/test_consistency.py

def test_display_values_consistency():
    """Verifica que display values estão sincronizados"""

    # Para cada relacionamento ativo
    for rel in all_active_relationships():
        # Buscar valor real
        target_record = repo.read_by_id(rel.target_type, None, rel.target_id)
        actual_value = target_record['nome']

        # Buscar valor armazenado
        source_record = repo.read_by_id(rel.source_type, None, rel.source_id)
        stored_value = source_record[f'_{rel.relationship_name}_display']

        # Comparar
        assert actual_value == stored_value, \
            f"Inconsistência em {rel.source_type}/{rel.source_id}"
```

2. Testes de orfãos (2 dias)
```python
def test_no_orphan_relationships():
    """Verifica que não há relationships órfãos"""

    orphans = db.execute("""
        SELECT r.*
        FROM relationships r
        LEFT JOIN {source_table} s ON r.source_id = s.record_id
        LEFT JOIN {target_table} t ON r.target_id = t.record_id
        WHERE s.record_id IS NULL OR t.record_id IS NULL
    """).fetchall()

    assert len(orphans) == 0, f"Encontrados {len(orphans)} relacionamentos órfãos"
```

3. Testes de stress (2 dias)

#### 5.2 Critérios de Conclusão

- [ ] >90% cobertura de testes
- [ ] Todos os testes passando
- [ ] Performance 5x+ em leitura confirmada
- [ ] Sem inconsistências de dados
- [ ] Stress tests passando

---

### FASE 6: Documentação & Rollout

**Duração**: 2 semanas
**Objetivo**: Documentar e implantar em produção

#### 6.1 Atividades

##### 6.1.1 Documentação (1 semana)

**Entregáveis**:

1. Guia do desenvolvedor (2 dias)
```markdown
# File: docs/developer/relationships_guide.md

# Guia de Relacionamentos VibeCForms

## Introdução

O novo paradigma de relacionamentos utiliza...

## Criando relacionamentos

### No spec:

\`\`\`json
{
  "name": "cliente",
  "type": "relationship",
  "target": "clientes",
  "cardinality": "one",
  "display_field": "nome",
  "sync_strategy": "eager"
}
\`\`\`

### No código:

\`\`\`python
repo.create_with_relationships(
    'pedidos', spec, data,
    relationships=[{...}],
    created_by='user123'
)
\`\`\`

## Navegando relacionamentos

...
```

2. Guia de migração (2 dias)
3. API reference (1 dia)

##### 6.1.2 Rollout em Produção (1 semana)

**Tarefas**:

1. Preparação (1 dia)
```bash
# Backup completo
./scripts/backup_production.sh

# Validar ambiente
./scripts/validate_environment.sh
```

2. Migração (1 dia)
```bash
# Dry run em produção
python scripts/migrate_to_relationships.py --dry-run

# Migração real
python scripts/migrate_to_relationships.py --confirm

# Validação
python scripts/validate_migration.py
```

3. Monitoramento (3 dias)
```python
# Monitorar por 72h após deploy
- Performance
- Erros de sincronização
- Uso de storage
- Logs de aplicação
```

4. Ajustes e otimizações (2 dias)

#### 6.2 Critérios de Conclusão

- [ ] Documentação completa publicada
- [ ] Migração em produção bem-sucedida
- [ ] Sistema estável por 72h
- [ ] Equipe treinada no novo modelo
- [ ] Retrospectiva realizada

---

## 10. Métricas de Sucesso

### 10.1 KPIs

| Métrica | Baseline | Meta | Crítico |
|---------|----------|------|---------|
| Tempo de leitura (100 registros) | 50ms | <10ms | <20ms |
| Tempo de escrita | 10ms | <30ms | <50ms |
| Sincronização (eager) | N/A | <100ms | <200ms |
| Inconsistências | 0 | 0 | <0.1% |
| Uptime durante migração | 100% | >99% | >95% |
| Storage overhead | 0 | <30% | <50% |

### 10.2 Monitoramento

```python
# File: src/monitoring/relationship_metrics.py

class RelationshipMetrics:
    """
    Coleta métricas sobre relacionamentos
    """

    def collect_metrics(self):
        return {
            'total_relationships': self.count_all_relationships(),
            'active_relationships': self.count_active_relationships(),
            'avg_sync_time': self.measure_avg_sync_time(),
            'inconsistency_rate': self.check_inconsistencies(),
            'storage_usage': self.measure_storage()
        }

    def alert_if_needed(self, metrics):
        if metrics['inconsistency_rate'] > 0.001:  # >0.1%
            send_alert("Alta taxa de inconsistência!")

        if metrics['avg_sync_time'] > 200:  # >200ms
            send_alert("Sincronização lenta!")
```

---

## 11. Conclusão

### 11.1 Benefícios Esperados

1. **Performance**: 5-10x mais rápido em leitura
2. **Flexibilidade**: Relacionamentos dinâmicos sem migrações
3. **Auditoria**: Rastreabilidade total de relacionamentos
4. **Escalabilidade**: Sharding facilitado
5. **Convenção**: Alinhamento com filosofia VibeCForms

### 11.2 Riscos Residuais

1. **Consistência**: Requer monitoramento contínuo
2. **Complexidade**: Curva de aprendizado para desenvolvedores
3. **Storage**: Aumento de 20-30% de espaço

### 11.3 Próximos Passos

1. ✅ Aprovar documento
2. ✅ Alocar equipe
3. ✅ Iniciar Fase 1 (Design & Prototipagem)

---

## 12. Referências

- [VibeCForms Conventions](../conventions.md)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Graph Database Concepts](https://neo4j.com/docs/getting-started/)

---

**Documento vivo**: Este documento será atualizado conforme a implementação avança.

**Última atualização**: 2026-01-04
**Versão**: 1.0
**Status**: 📋 Aguardando Aprovação
