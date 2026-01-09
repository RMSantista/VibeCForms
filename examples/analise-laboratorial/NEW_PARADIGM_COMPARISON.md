# VibeCForms v3.0 - New Persistence Paradigm Comparison

**Date:** 2026-01-08
**Status:** Demo Database Ready for Comparison
**Location:** `examples/analise-laboratorial/data/sqlite/`

---

## Overview

This document compares the **Old Paradigm** (v2.4) with the **New Paradigm** (v3.0) implemented in VibeCForms. Both databases are available for comparison in `examples/analise-laboratorial/data/sqlite/`:

- **Old Paradigm:** `vibecforms.db` (current production database)
- **New Paradigm:** `vibecforms_new_paradigm.db` (demo database following Convention #9)

---

## Key Differences

### 1. Relationship Storage

#### Old Paradigm (v2.4)
**Approach:** Foreign Keys embedded in entity tables

```sql
-- OLD: Foreign keys in entity tables
CREATE TABLE exames (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER NOT NULL,  -- ❌ Foreign key stored here
    data_solicitacao TEXT,
    FOREIGN KEY(paciente_id) REFERENCES pacientes(id)
);
```

**Limitations:**
- ❌ Foreign key columns bloat entity tables
- ❌ Difficult to upgrade 1:N to N:N (requires schema migration)
- ❌ No audit trail for relationship changes
- ❌ Hard to implement soft-delete on relationships
- ❌ Difficult to track relationship history

**Benefits:**
- ✅ Simple JOINS for related data
- ✅ Referential integrity via FOREIGN KEY constraint
- ✅ Standard SQL approach

---

#### New Paradigm (v3.0)
**Approach:** Universal Relationship Table (Convention #9)

```sql
-- NEW: Relationships in separate table
CREATE TABLE relationships (
    rel_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,      -- "exames"
    source_id TEXT NOT NULL,        -- UUID of exame
    relationship_name TEXT NOT NULL, -- "paciente" (field name)
    target_type TEXT NOT NULL,      -- "pacientes"
    target_id TEXT NOT NULL,        -- UUID of paciente
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    removed_at TEXT,                -- Soft-delete marker
    removed_by TEXT,
    metadata TEXT,                  -- JSON for additional context
    UNIQUE(source_type, source_id, relationship_name, target_id)
);
```

**Benefits:**
- ✅ Single table handles ALL cardinality types (1:1, 1:N, N:N)
- ✅ Zero schema changes when upgrading cardinality
- ✅ Full audit trail (created_by, created_at, removed_by, removed_at)
- ✅ Soft-delete semantics with recovery capability
- ✅ Relationship history tracking via view
- ✅ Metadata support for additional context
- ✅ Cleaner entity tables (no FK columns)

**Tradeoffs:**
- ⚠️ Slightly more complex queries (explicit JOIN with relationships table)
- ⚠️ Display values must be denormalized for performance

---

### 2. Display Value Handling

#### Old Paradigm (v2.4)
**Problem:** Display values fetched via JOIN at read time

```python
# OLD: Calculate display on read
def get_exame(exame_id):
    exame = db.query("""
        SELECT e.*, p.nome as paciente_nome
        FROM exames e
        JOIN pacientes p ON e.paciente_id = p.id
        WHERE e.id = ?
    """, exame_id)
    return exame
```

**Issues:**
- ❌ Every read requires JOIN (performance impact)
- ❌ Display field changes require scanning all related records
- ❌ Difficult to detect stale display values
- ❌ No history of display value changes

---

#### New Paradigm (v3.0)
**Approach:** Display Values Denormalized in Entity Tables

```python
# NEW: Display values stored in entity tables
CREATE TABLE exames (
    _record_id TEXT PRIMARY KEY,
    paciente_id TEXT NOT NULL,
    paciente_display TEXT,          -- ✅ Denormalized display value
    medico_id TEXT,
    medico_display TEXT,            -- ✅ Denormalized display value
    ...
);
```

**Example:**
```sql
-- Display values are stored and used directly
SELECT
    _record_id,
    paciente_display,  -- No JOIN needed!
    medico_display,
    data_solicitacao
FROM exames
WHERE status = 'em_andamento';
```

**Sync Strategies:**

1. **EAGER:** Immediate synchronization (for critical relationships)
   - When: Customer, Supplier, Account
   - How: Trigger after UPDATE on target table
   - Cost: High (additional I/O immediately)
   - Guarantee: Always consistent

2. **LAZY:** On-read synchronization (for non-critical relationships)
   - When: Categories, Tags, Classifications
   - How: Check + update in `read_by_id()` method
   - Cost: Medium (only if outdated)
   - Guarantee: Eventually consistent (seconds to minutes)

3. **SCHEDULED:** Periodic background job (for analysis relationships)
   - When: Statistics, Aggregates, Denormalized views
   - How: Cron job every N minutes
   - Cost: Low (optimized batch)
   - Guarantee: Eventually consistent (minutes to hours)

---

### 3. Soft-Delete and Audit Trail

#### Old Paradigm (v2.4)
**Approach:** Hard delete or separate archive table

```sql
-- OLD: Record is permanently deleted
DELETE FROM exames WHERE id = 123;
-- ❌ Cannot recover
-- ❌ No audit trail
-- ❌ Difficult to track what was deleted

-- OLD ALTERNATIVE: Archive table
-- Still requires manual sync and additional storage
```

---

#### New Paradigm (v3.0)
**Approach:** Soft-delete with complete audit trail

```sql
-- NEW: Relationship marked as removed, not deleted
UPDATE relationships
SET removed_at = '2026-01-08T16:13:00', removed_by = 'user@example.com'
WHERE rel_id = 'ABC123...';

-- ✅ Record still exists in database
-- ✅ Complete audit trail preserved
-- ✅ Easy to recover if needed
-- ✅ History tracked automatically

-- View only active relationships
SELECT * FROM active_relationships;  -- removed_at IS NULL

-- View complete history (including removals)
SELECT * FROM relationship_history;  -- All events with timestamps
```

---

### 4. Entity Table Structure Comparison

#### Old Paradigm (v2.4)
```
Exames Table:
┌─────────┬──────────┬───────────────┬─────────────┬───────────────┐
│ id      │ paciente_id │ data_solici  │ medico_id │ ... (fks)   │
├─────────┼──────────┼───────────────┼─────────────┼───────────────┤
│ 1001    │ 501      │ 2026-01-02T10 │ 401        │ ...         │
│ 1002    │ 502      │ 2026-01-03T11 │ 402        │ ...         │
└─────────┴──────────┴───────────────┴─────────────┴───────────────┘
```

**Issues:**
- ❌ FK columns (paciente_id, medico_id) clutter entity table
- ❌ To find paciente name: must JOIN every time
- ❌ Schema changes needed to add/remove relationships

---

#### New Paradigm (v3.0)
```
Exames Table:
┌──────────────┬─────────────────────┬──────────────────────┬─────────┐
│ _record_id   │ paciente_display    │ medico_display       │ ...     │
├──────────────┼─────────────────────┼──────────────────────┼─────────┤
│ FA6F0578     │ João Silva          │ Dra. Ana Costa       │ ...     │
│ E3AE0888     │ João Silva          │ Dra. Ana Costa       │ ...     │
└──────────────┴─────────────────────┴──────────────────────┴─────────┘

Relationships Table (separate):
┌──────────────┬──────────┬────────────┬──────────────┬──────────────┐
│ rel_id       │ source   │ rel_name   │ target       │ target_id    │
├──────────────┼──────────┼────────────┼──────────────┼──────────────┤
│ REL_ABC123   │ exames   │ paciente   │ pacientes    │ 9D31BBB0     │
│ REL_XYZ456   │ exames   │ medico     │ funcionarios │ 8F2A7BB0     │
└──────────────┴──────────┴────────────┴──────────────┴──────────────┘
```

**Benefits:**
- ✅ Clean entity tables (only display values, no FK clutter)
- ✅ Display values ready to use (no JOIN needed)
- ✅ Relationships managed in dedicated table
- ✅ Can add/remove relationships without entity table migration

---

## Data Statistics

### Demo Database Created

**vibecforms_new_paradigm.db** contains:

| Entity          | Count | Purpose                           |
|-----------------|-------|-----------------------------------|
| pacientes       | 3     | Base patients for lab analysis    |
| exames          | 4     | Lab examinations requested        |
| testes          | 10    | Individual tests within exams     |
| resultados      | 10    | Results from tests                |
| funcionarios    | 3     | Lab staff (doctors, technicians)  |
| **relationships**   | **24**    | **All 1:1, 1:N, N:N connections** |
| - active        | 23    | Currently valid relationships     |
| - removed       | 1     | Soft-deleted (audit trail demo)   |

---

## Relationship Examples in New Paradigm

### 1:1 Relationship (Exame ↔ Paciente)
One exame belongs to exactly one paciente:

```
Exame FA6F0578 → Paciente João Silva

relationships table:
┌────────────────┬──────────┬───────────┬──────────────┬────────────────┐
│ rel_id         │ source   │ rel_name  │ target       │ target_id      │
├────────────────┼──────────┼───────────┼──────────────┼────────────────┤
│ REL_EXAM_PAC_1 │ exames   │ paciente  │ pacientes    │ CFEFBBB0       │
└────────────────┴──────────┴───────────┴──────────────┴────────────────┘

Display value in exames table:
paciente_display = "João Silva"  ← Denormalized, no JOIN needed
```

### 1:N Relationship (Exame → Testes)
One exame can have many testes:

```
Exame FA6F0578 → [Teste 0EC2, Teste 1F33, Teste 2G44]

relationships table:
┌────────────────┬───────────┬──────────┬────────┬────────────┐
│ rel_id         │ source    │ rel_name │ target │ target_id  │
├────────────────┼───────────┼──────────┼────────┼────────────┤
│ REL_EXAM_TST_1 │ testes    │ exame    │ exames │ FA6F0578   │
│ REL_EXAM_TST_2 │ testes    │ exame    │ exames │ FA6F0578   │
│ REL_EXAM_TST_3 │ testes    │ exame    │ exames │ FA6F0578   │
└────────────────┴───────────┴──────────┴────────┴────────────┘

Display values in testes table:
exame_display = "Exame para João Silva"  ← No JOIN needed
```

### N:1 Relationship (Resultado → Teste)
Many resultados belong to one teste:

```
Teste 0EC2 ← [Resultado RES001, Resultado RES002]

relationships table:
┌────────────────┬──────────────┬──────────┬────────┬───────────┐
│ rel_id         │ source       │ rel_name │ target │ target_id │
├────────────────┼──────────────┼──────────┼────────┼───────────┤
│ REL_RES_TST_1  │ resultados   │ teste    │ testes │ 0EC2      │
│ REL_RES_TST_2  │ resultados   │ teste    │ testes │ 0EC2      │
└────────────────┴──────────────┴──────────┼────────┴───────────┘

Display values in resultados table:
teste_display = "Teste Hemoglobina"  ← No JOIN needed
```

---

## Soft-Delete Example

### Demonstrating Audit Trail

```sql
-- Query: Show removed relationship with audit info
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    created_at,
    created_by,
    removed_at,
    removed_by
FROM relationships
WHERE removed_at IS NOT NULL;

Results:
┌──────────────┬──────────┬────────────┬───────────────┬───────────────────────────┬──────────────────┬───────────────────────────┬──────────────────┐
│ rel_id       │ source   │ src_id     │ rel_name      │ created_at                │ created_by       │ removed_at                │ removed_by       │
├──────────────┼──────────┼────────────┼───────────────┼───────────────────────────┼──────────────────┼───────────────────────────┼──────────────────┤
│ REL_EXAM_001 │ exames   │ FA6F0578   │ paciente      │ 2026-01-02T10:30:00       │ 15ff80dc-1234    │ 2026-01-08T16:13:00       │ e45ad0bb-5678    │
└──────────────┴──────────┴────────────┴───────────────┴───────────────────────────┴──────────────────┴───────────────────────────┴──────────────────┘

✅ Complete audit trail:
- Relationship created by technician on 2026-01-02
- Relationship removed by admin on 2026-01-08 at 16:13
- Can be recovered by restoring (setting removed_at = NULL)
```

---

## Query Pattern Differences

### OLD PARADIGM: Finding Related Data

```python
# OLD: Single JOIN for one-level relationship
def get_exame_with_paciente(exame_id):
    cursor.execute("""
        SELECT e.*, p.nome
        FROM exames e
        JOIN pacientes p ON e.paciente_id = p.id
        WHERE e.id = ?
    """, (exame_id,))
    return cursor.fetchone()

# Result: Efficient for simple relationships
# Issue: Must repeat JOIN for each related field (paciente, medico, etc.)
```

---

### NEW PARADIGM: Finding Related Data

```python
# NEW: Direct field access (display values denormalized)
def get_exame_with_paciente(exame_id):
    cursor.execute("""
        SELECT _record_id, paciente_display, medico_display, data_solicitacao
        FROM exames
        WHERE _record_id = ?
    """, (exame_id,))
    return cursor.fetchone()

# Result: Single table lookup, no JOIN needed!
# Display values: "João Silva", "Dra. Ana Costa" already available
```

### NEW PARADIGM: Finding Relationships (Forward Navigation)

```python
# NEW: Find all relationships FROM a source
def get_related_testes(exame_id):
    cursor.execute("""
        SELECT r.target_id, t.tipo_teste, t.descricao
        FROM relationships r
        JOIN testes t ON r.target_id = t._record_id
        WHERE r.source_type = 'testes'
          AND r.relationship_name = 'exame'
          AND r.target_id = ?
          AND r.removed_at IS NULL
    """, (exame_id,))
    return cursor.fetchall()

# Result: Explicit relationship navigation
# Flexibility: Easy to check if relationship exists, was soft-deleted, etc.
```

### NEW PARADIGM: Finding Relationships (Reverse Navigation)

```python
# NEW: Find all entities pointing TO this record (reverse relationship)
def get_pacientes_with_exames(paciente_id):
    cursor.execute("""
        SELECT DISTINCT r.source_id
        FROM relationships r
        WHERE r.target_type = 'pacientes'
          AND r.target_id = ?
          AND r.relationship_name = 'paciente'
          AND r.removed_at IS NULL
    """, (paciente_id,))
    return [row[0] for row in cursor.fetchall()]

# Result: Can easily navigate in reverse direction
# Issue (OLD): Not possible with foreign keys!
```

---

## Schema Migration Advantages

### Scenario: Upgrading 1:N to N:N

#### Old Paradigm
```
OLD: exames → pacientes (1:N)
- pacientes table has: id, nome, cpf, ...
- exames table has: id, paciente_id, ...

REQUIREMENT: Allow one exame to belong to multiple pacientes (N:N)

SOLUTION NEEDED:
1. Create new bridge table: exames_pacientes (exame_id, paciente_id)
2. Migrate data from exames.paciente_id
3. Drop paciente_id from exames
4. Update application code to use bridge table
5. Update all queries (multiple JOINs)
6. Risk: Data loss during migration

❌ Complex, risky, requires code changes
```

---

#### New Paradigm
```
NEW: exames → pacientes (1:N via relationships table)

REQUIREMENT: Allow one exame to belong to multiple pacientes (N:N)

SOLUTION:
Just insert more relationships! No schema change needed!

Before:
┌─────────────────────────┐
│ relationships           │
├─────────────────────────┤
│ rel_id: ABC             │
│ source: exames          │
│ source_id: FA6F0578     │
│ relationship_name: paciente
│ target: pacientes       │
│ target_id: CFEFBBBB0    │
└─────────────────────────┘

After (adding 2nd paciente):
┌─────────────────────────┐
│ relationships           │
├─────────────────────────┤
│ rel_id: ABC             │
│ source: exames          │
│ source_id: FA6F0578     │ ← SAME exame
│ relationship_name: paciente
│ target: pacientes       │
│ target_id: CFEFBBBB0    │ ← First paciente
├─────────────────────────┤
│ rel_id: XYZ             │
│ source: exames          │
│ source_id: FA6F0578     │ ← SAME exame
│ relationship_name: paciente
│ target: pacientes       │
│ target_id: 9D31CCCC0    │ ← Second paciente
└─────────────────────────┘

✅ No schema changes!
✅ No data migration!
✅ No code changes!
✅ Complete audit trail (both relationships visible)
```

---

## Performance Comparison

### Query Performance

| Operation                           | Old Paradigm | New Paradigm | Note                              |
|-------------------------------------|--------------|--------------|-----------------------------------|
| Get single record + display values  | Fast (1 JOIN) | Fastest (1 SELECT) | New is faster (no JOIN)          |
| Get all records with display        | Medium (FULL JOIN) | Fast (Full scan, no JOIN) | New is faster              |
| Find all related records (1:N)      | Fast (1 JOIN) | Moderate (JOIN via relationships) | Similar performance             |
| Reverse navigation (reverse FK)     | Impossible   | Possible (1 JOIN) | New enables this feature       |
| Find soft-deleted relationships     | N/A          | Fast (WHERE removed_at IS NOT NULL) | New enables audit trail      |
| Upgrade 1:N to N:N                  | Slow (schema migration) | Fast (insert relationship) | New wins dramatically      |

---

## Testing the Demo Database

### Examining the New Paradigm

```bash
# Open SQLite terminal
sqlite3 examples/analise-laboratorial/data/sqlite/vibecforms_new_paradigm.db

# View entity table structure (notice denormalized display values)
.schema exames
-- Shows: paciente_display, medico_display columns

# View relationships
SELECT * FROM active_relationships LIMIT 10;

# View soft-deleted relationships (audit trail)
SELECT * FROM relationships WHERE removed_at IS NOT NULL;

# View relationship history
SELECT * FROM relationship_history;

# Compare display values
SELECT paciente_display, COUNT(*) as exame_count
FROM exames
GROUP BY paciente_display;
```

---

## Migration Strategy

### From Old Paradigm to New Paradigm

The new paradigm is **backward compatible**. Both can coexist:

1. **Phase 1: Dual Write**
   - New relationships table created alongside old FKs
   - Both write to relationships table AND update _display columns
   - Read from old FKs (for compatibility)

2. **Phase 2: Lazy Migration**
   - Read from _display columns when available
   - Fall back to old FKs if _display is NULL
   - Gradually populate _display via background job

3. **Phase 3: Hard Cutover**
   - All reads use relationships table
   - All writes use relationships table
   - Remove old FK columns (optional)

---

## Conclusion

The **New Paradigm (v3.0)** offers:

| Aspect              | Old (v2.4) | New (v3.0) |
|---------------------|-----------|-----------|
| Support Cardinality | 1:1, 1:N (N:N complex) | 1:1, 1:N, N:N (unified)      |
| Schema Flexibility  | Low (requires migration) | High (add relationships)      |
| Audit Trail         | Manual (optional)         | Built-in (automatic)         |
| Soft-Delete         | Not standard              | Standard (removed_at)        |
| Display Values      | Computed on read (JOIN)   | Denormalized (fast)          |
| Reverse Navigation  | Not possible              | Native support               |
| Entity Table Size   | Larger (FKs included)     | Cleaner (FK-free)            |

The new paradigm trades slight query complexity for flexibility, auditability, and zero-migration schema evolution.

---

## Files Involved

- **Old Paradigm DB:** `examples/analise-laboratorial/data/sqlite/vibecforms.db`
- **New Paradigm DB:** `examples/analise-laboratorial/data/sqlite/vibecforms_new_paradigm.db`
- **Creation Script:** `examples/analise-laboratorial/scripts/create_demo_db.py`
- **Schema Definition:** `src/persistence/sql/schema/relationships.sql`
- **Interface Contract:** `src/persistence/contracts/relationship_interface.py`

---

## Next Steps

1. ✅ Compare databases visually using SQLite browser
2. ⏳ Integrate relationships table with BaseRepository
3. ⏳ Create TxtRelationshipRepository adapter
4. ⏳ Implement SyncEngine for display value synchronization
5. ⏳ Create unit tests for relationship operations
6. ⏳ Implement FormController integration
7. ⏳ Add "relationship" field type to specs
8. ⏳ Create data migration script from old to new paradigm

---

**Ready for comparison and feedback!** 🎯
