-- ═══════════════════════════════════════════════════════════════════════════
-- VibeCForms v3.0: Universal Relationships Schema
-- ═══════════════════════════════════════════════════════════════════════════
-- Description: Schema for the new persistence paradigm
-- Date: 2026-01-08
-- Version: 1.0
-- Status: Design Phase
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: relationships
-- PURPOSE: Universal relationship table for ALL relationships (1:1, 1:N, N:N)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS relationships (
    -- Primary Key
    rel_id TEXT PRIMARY KEY,                    -- UUID Crockford Base32 (27 chars)

    -- Source (origin entity)
    source_type TEXT NOT NULL,                  -- Form path: "pedidos", "clientes", etc
    source_id TEXT NOT NULL,                    -- UUID of source record

    -- Relationship Name
    relationship_name TEXT NOT NULL,            -- Field name: "cliente", "produtos", "categoria"

    -- Target (destination entity)
    target_type TEXT NOT NULL,                  -- Form path: "clientes", "produtos", etc
    target_id TEXT NOT NULL,                    -- UUID of target record

    -- Metadata
    created_at TEXT NOT NULL,                   -- ISO 8601 timestamp
    created_by TEXT NOT NULL,                   -- UUID of actor who created
    removed_at TEXT,                            -- ISO 8601 timestamp (soft delete)
    removed_by TEXT,                            -- UUID of actor who removed
    metadata TEXT,                              -- JSON with additional context

    -- Constraints
    UNIQUE(source_type, source_id, relationship_name, target_id),

    -- Indexes for performance
    FOREIGN KEY(source_type) REFERENCES form_metadata(form_path),
    FOREIGN KEY(target_type) REFERENCES form_metadata(form_path)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES: Optimized query patterns
-- ═══════════════════════════════════════════════════════════════════════════

-- Find all relationships FROM a source
CREATE INDEX IF NOT EXISTS idx_rel_source
ON relationships(source_type, source_id);

-- Find all relationships TO a target
CREATE INDEX IF NOT EXISTS idx_rel_target
ON relationships(target_type, target_id);

-- Find relationships by name (for cardinality validation)
CREATE INDEX IF NOT EXISTS idx_rel_name
ON relationships(source_type, relationship_name);

-- Find active relationships (WHERE removed_at IS NULL)
CREATE INDEX IF NOT EXISTS idx_rel_active
ON relationships(source_type, source_id, removed_at);

-- Find relationships created within date range
CREATE INDEX IF NOT EXISTS idx_rel_created
ON relationships(created_at);

-- Find relationships removed within date range
CREATE INDEX IF NOT EXISTS idx_rel_removed
ON relationships(removed_at) WHERE removed_at IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: active_relationships
-- PURPOSE: Simplified view of non-deleted relationships
-- ═══════════════════════════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS active_relationships AS
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    created_at,
    created_by,
    metadata
FROM relationships
WHERE removed_at IS NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: relationship_history
-- PURPOSE: View all relationship changes (including deletions)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS relationship_history AS
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    'created' as event_type,
    created_at as event_at,
    created_by as event_by
FROM relationships
UNION ALL
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    'removed' as event_type,
    removed_at as event_at,
    removed_by as event_by
FROM relationships
WHERE removed_at IS NOT NULL
ORDER BY event_at DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: form_metadata (helper table for schema)
-- PURPOSE: Track form paths (used for FK in relationships table)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS form_metadata (
    form_path TEXT PRIMARY KEY,
    display_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
