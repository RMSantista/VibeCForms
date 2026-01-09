# Novo Paradigma de Persistência - Demo Database

**Status:** ✅ Pronto para análise
**Data:** 2026-01-08
**Localização:** `examples/analise-laboratorial/`

---

## O Que Foi Criado

Dois arquivos para demonstrar o novo paradigma de relacionamentos (v3.0):

### 1️⃣ **Banco de Dados Demo**
- **Arquivo:** `data/sqlite/vibecforms_new_paradigm.db`
- **Tamanho:** 100 KB
- **Contém:**
  - 3 Pacientes
  - 4 Exames (com display values denormalizados)
  - 10 Testes (com display values denormalizados)
  - 10 Resultados
  - 3 Funcionários (médicos e técnicos)
  - **24 Relacionamentos** (23 ativos, 1 soft-deleted como exemplo)

### 2️⃣ **Scripts de Demonstração**
- `scripts/create_demo_db.py` - Cria o banco de dados com novo paradigma
- `scripts/compare_paradigms.py` - Compara lado-a-lado os dois paradigmas

### 3️⃣ **Documentação Completa**
- `NEW_PARADIGM_COMPARISON.md` - Comparação detalhada entre v2.4 e v3.0

---

## Conceitos Demonstrados

### ✅ Tabela Universal de Relacionamentos

```sql
CREATE TABLE relationships (
    rel_id TEXT PRIMARY KEY,           -- UUID do relacionamento
    source_type TEXT,                  -- "exames", "testes", etc
    source_id TEXT,                    -- UUID do record de origem
    relationship_name TEXT,            -- Nome do campo ("paciente", "exame", etc)
    target_type TEXT,                  -- Tipo do alvo ("pacientes", "exames", etc)
    target_id TEXT,                    -- UUID do record alvo
    created_at TEXT,                   -- Timestamp de criação
    created_by TEXT,                   -- UUID do ator que criou
    removed_at TEXT,                   -- Timestamp soft-delete (NULL = ativo)
    removed_by TEXT,                   -- UUID do ator que removeu
    metadata TEXT                      -- JSON com contexto adicional
);
```

**Vantagens:**
- ✅ Uma única tabela para 1:1, 1:N, N:N
- ✅ Zero migrations quando muda cardinalidade
- ✅ Audit trail completo (created_by, removed_by, timestamps)
- ✅ Soft-delete com recovery possível
- ✅ Histórico de mudanças via views

---

### ✅ Display Values Denormalizados

Em vez de fazer JOIN toda vez que precisa exibir dados:

```python
# ❌ OLD PARADIGM (com JOIN)
SELECT e.id, p.nome, e.data_solicitacao
FROM exames e
JOIN pacientes p ON e.paciente_id = p.id

# ✅ NEW PARADIGM (sem JOIN)
SELECT _record_id, paciente_display, data_solicitacao
FROM exames
```

Os display values ficam armazenados na tabela de exames:
- `paciente_display = "João Silva"` (atualizado via EAGER sync)
- `medico_display = "Dra. Ana Costa"` (atualizado via EAGER sync)

---

### ✅ Soft-Delete com Audit Trail

Relacionamentos não são deletados, apenas marcados como removidos:

```sql
-- Exemplo: remover relacionamento entre exame e paciente
UPDATE relationships
SET removed_at = '2026-01-08T16:13:00', removed_by = 'admin-uuid'
WHERE rel_id = 'ABC123...';

-- ✅ Record preservado
-- ✅ Audit trail completo
-- ✅ Fácil recuperar (SET removed_at = NULL)
-- ✅ Histórico trackado automaticamente
```

---

### ✅ Suporte a Todas as Cardinalidades

#### 1:1 Relationship (Exame ↔ Paciente)
```
Uma exame tem EXATAMENTE UM paciente

relationships:
├─ rel_id: A1B2C3D4
├─ source_type: exames
├─ source_id: FA6F0578
├─ relationship_name: paciente  ← field name em exames.json
├─ target_type: pacientes
└─ target_id: CFEFBBBB0
```

#### 1:N Relationship (Exame → Testes)
```
Um exame tem MUITOS testes

relationships:
├─ rel_id: X1Y2Z3A4
├─ source_type: testes
├─ source_id: 0EC2XXXX
├─ relationship_name: exame     ← field name em testes.json
├─ target_type: exames
└─ target_id: FA6F0578
├─
├─ rel_id: X1Y2Z3B5
├─ source_type: testes
├─ source_id: FA96XXXX
├─ relationship_name: exame
├─ target_type: exames
└─ target_id: FA6F0578
├─
├─ rel_id: X1Y2Z3C6
├─ source_type: testes
├─ source_id: 30CDXXXX
├─ relationship_name: exame
├─ target_type: exames
└─ target_id: FA6F0578
```

#### N:N Relationship (Upgrade automático!)
```
Se precisar de N:N no futuro, é só adicionar outro relacionamento:

relationships:
├─ rel_id: M1N2O3P4
├─ source_type: exames
├─ source_id: FA6F0578
├─ relationship_name: paciente
├─ target_type: pacientes
└─ target_id: CFEFBBBB0
├─
├─ rel_id: M1N2O3P5  ← NOVO!
├─ source_type: exames
├─ source_id: FA6F0578
├─ relationship_name: paciente
├─ target_type: pacientes
└─ target_id: 9D31CCCC0  ← Outro paciente!

✅ NENHUMA mudança de schema!
✅ NENHUMA migração de dados!
✅ Ambos os relacionamentos na história!
```

---

## Como Usar

### 1. Visualizar o Banco de Dados Demo

```bash
# Abrir no SQLite Browser
sqlite3 examples/analise-laboratorial/data/sqlite/vibecforms_new_paradigm.db

# Ver tabelas criadas
.tables
# Output: exames  form_metadata  funcionarios  pacientes  relationships  resultados  testes

# Ver estrutura da tabela relationships
.schema relationships

# Ver exemplo de dados
SELECT * FROM active_relationships LIMIT 5;
SELECT * FROM relationships WHERE removed_at IS NOT NULL;
```

### 2. Executar Comparação

```bash
python3 examples/analise-laboratorial/scripts/compare_paradigms.py
```

**Output mostra:**
- ✅ Estrutura da tabela relationships
- ✅ Exemplos de relacionamentos ativos
- ✅ Display values denormalizados
- ✅ Soft-deleted relationships (audit trail)
- ✅ Comparação de cardinalidades
- ✅ Estatísticas dos bancos

### 3. Recriar o Banco (se necessário)

```bash
python3 examples/analise-laboratorial/scripts/create_demo_db.py
```

---

## Comparando Paradigmas

### Old Paradigm (v2.4)
**Arquivo:** `data/sqlite/vibecforms.db` (banco original)

```
Tabelas:
├─ pacientes
├─ exames (com: paciente_id FK, medico_id FK)
├─ testes (com: exame_id FK)
├─ resultados (com: teste_id FK)
├─ funcionarios
└─ ... (várias outras)

Problema:
❌ FK columns clutter as tabelas
❌ Para 1:1 e 1:N funcionam
❌ N:N requer bridge table
❌ Sem soft-delete
❌ Sem audit trail
```

### New Paradigm (v3.0)
**Arquivo:** `data/sqlite/vibecforms_new_paradigm.db` (demo novo)

```
Tabelas:
├─ pacientes
├─ exames (com: paciente_display, medico_display)
├─ testes (com: exame_display)
├─ resultados (com: teste_display)
├─ funcionarios
├─ form_metadata (registry)
└─ relationships (UNIVERSAL! ← Novo!)

Vantagem:
✅ Tabelas limpas (sem FKs)
✅ Display values prontos (sem JOIN)
✅ 1:1, 1:N, N:N com mesma tabela
✅ Soft-delete built-in
✅ Audit trail automático
✅ Zero-migration schema evolution
```

---

## Queries Exemplo

### Buscar um Exame com Informações de Paciente

```python
# OLD PARADIGM (com JOIN)
SELECT e.*, p.nome as paciente_nome
FROM exames e
JOIN pacientes p ON e.paciente_id = p.id
WHERE e.id = 1001

# NEW PARADIGM (sem JOIN)
SELECT _record_id, paciente_display, medico_display, data_solicitacao
FROM exames
WHERE _record_id = 'FA6F0578'
```

### Buscar Todos os Testes de um Exame

```python
# OLD PARADIGM (com WHERE)
SELECT * FROM testes WHERE exame_id = 1001

# NEW PARADIGM (com relacionamentos)
SELECT t.*
FROM testes t
JOIN relationships r ON r.target_id = t._record_id
WHERE r.source_type = 'exames'
  AND r.source_id = 'FA6F0578'
  AND r.relationship_name = 'exame'
  AND r.removed_at IS NULL
```

### Reverse Navigation (Encontrar Exames de um Paciente)

```python
# OLD PARADIGM
# Impossível direto! Precisa de view ou segunda tabela

# NEW PARADIGM (nativo!)
SELECT DISTINCT e._record_id, e.paciente_display
FROM exames e
JOIN relationships r ON r.source_id = e._record_id
WHERE r.target_type = 'pacientes'
  AND r.target_id = 'CFEFBBBB0'
  AND r.relationship_name = 'paciente'
  AND r.removed_at IS NULL
```

---

## Estrutura de Dados de Exemplo

### Pacientes (3 registros)
| _record_id | nome             | cpf            | data_nascimento |
|------------|-----------------|----------------|-----------------|
| CFEFBBBB0  | João Silva      | 123.456.789-00 | 1980-05-15     |
| 9D31CCCC0  | Maria Santos    | 987.654.321-00 | 1992-08-22     |
| 20E4DDDD0  | Pedro Oliveira  | 456.789.123-00 | 1975-12-10     |

### Exames (4 registros com display values)
| _record_id | paciente_display | medico_display   | status       | paciente_id |
|------------|-----------------|------------------|--------------|-------------|
| FA6F0578   | João Silva      | Dra. Ana Costa   | em_andamento | CFEFBBBB0   |
| E3AE0888   | João Silva      | Dra. Ana Costa   | concluído    | CFEFBBBB0   |
| 9EE9526A   | Maria Santos    | Dra. Ana Costa   | em_andamento | 9D31CCCC0   |
| 43D6F36C   | Pedro Oliveira  | Dra. Ana Costa   | em_andamento | 20E4DDDD0   |

> **Nota:** As colunas `_display` são atualizadas via sync strategies (EAGER, LAZY, ou SCHEDULED).

### Relationships (exemplo)
| rel_id     | source_type | source_id | relationship_name | target_type | target_id | removed_at |
|------------|------------|-----------|------------------|------------|-----------|-----------|
| ABC123DEF  | exames     | FA6F0578  | paciente         | pacientes  | CFEFBBBB0 | NULL      |
| XYZ789ABC  | testes     | 0EC2XXXX  | exame            | exames     | FA6F0578  | NULL      |
| DEF456GHI  | exames     | FA6F0578  | paciente         | pacientes  | CFEFBBBB0 | 2026-01-08T16:13:00 |

> **Nota:** O último relacionamento foi soft-deleted e está no audit trail.

---

## Metricas do Demo Database

```
📊 Banco de Dados: vibecforms_new_paradigm.db

Registros por Tabela:
  pacientes      : 3 records
  exames         : 4 records
  testes         : 10 records
  resultados     : 10 records
  funcionarios   : 3 records

Relacionamentos:
  Active         : 23 records
  Soft-Deleted   : 1 record
  Total          : 24 records

Tamanho do Banco : 100 KB

Índices Criados:
  ✓ idx_rel_source    (source_type, source_id)
  ✓ idx_rel_target    (target_type, target_id)
  ✓ idx_rel_name      (source_type, relationship_name)
  ✓ idx_rel_active    (source_type, source_id, removed_at)
  ✓ idx_rel_created   (created_at)
  ✓ idx_rel_removed   (removed_at WHERE removed_at IS NOT NULL)

Views Criadas:
  ✓ active_relationships   (removed_at IS NULL)
  ✓ relationship_history   (all events with timestamps)
```

---

## Próximos Passos (Roadmap)

Conforme documentado em `docs/planning/novo_paradigma_persistencia.md`:

### FASE 2 (Em Progresso): Integração Core
- [ ] Refatorar IRelationshipRepository para estender BaseRepository
- [ ] Criar TxtRelationshipRepository adapter
- [ ] Integrar com RepositoryFactory
- [ ] Adicionar field type "relationship" em specs

### FASE 3: Sincronização & Triggers
- [ ] Implementar SyncEngine com 3 estratégias (EAGER, LAZY, SCHEDULED)
- [ ] Criar triggers SQLite para soft-delete e sync
- [ ] Job de sincronização em background

### FASE 4: Migração de Dados
- [ ] Script para migrar do paradigma antigo para novo
- [ ] Backup automático pré-migração
- [ ] Validação de integridade pós-migração

### FASE 5: Testes & Validação
- [ ] 30+ unit tests para RelationshipRepository
- [ ] Testes de performance (old vs new paradigm)
- [ ] Testes de integridade de relacionamentos

### FASE 6: Documentação & Rollout
- [ ] Guia do desenvolvedor
- [ ] Guide de migração passo-a-passo
- [ ] Rollout em produção

---

## Contato & Feedback

Este é um **demo database** criado em 2026-01-08 para permitir comparação e validação do novo paradigma.

Para perguntas ou feedback:
1. Verifique `NEW_PARADIGM_COMPARISON.md` para detalhes técnicos completos
2. Execute `compare_paradigms.py` para visualizar análise lado-a-lado
3. Abra `vibecforms_new_paradigm.db` em SQLite browser para explorar dados

---

**Pronto para análise e aprovação!** 🎯
