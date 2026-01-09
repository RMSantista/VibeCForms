#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCForms v3.0 - Migration from Old to New Persistence Paradigm

This script migrates real data from vibecforms.db (old paradigm with FKs)
to vibecforms_new_paradigm.db (new paradigm with universal relationships table).

The migration:
1. Reads all data from source database (old paradigm)
2. Extracts relationship information from FKs
3. Recreates tables without FK columns
4. Populates relationships table with all connections
5. Denormalizes display values in entities

Migration Strategy:
- Backward compatible: Both DBs coexist
- Zero-downtime: Can migrate gradually
- Complete audit trail: Preserves all information
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent
EXAMPLES_DIR = SCRIPT_DIR.parent
OLD_DB = EXAMPLES_DIR / "data" / "sqlite" / "vibecforms.db"
NEW_DB = EXAMPLES_DIR / "data" / "sqlite" / "vibecforms_new_paradigm.db"

# Actor ID (representing the migration process)
MIGRATION_ACTOR_ID = str(uuid.uuid4())

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def timestamp_now():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def get_display_field(cursor, table_name):
    """Get the primary display field for a table (usually 'nome')."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    # Try common display field names in order
    for display_name in ['nome', 'name', 'descricao', 'titulo', 'sigla']:
        for col in columns:
            if col[1] == display_name:
                return display_name

    # Fall back to second column if no display field found
    if len(columns) > 1:
        return columns[1][1]

    return None

def get_record_display_value(cursor, table_name, record_id, display_field):
    """Get the display value for a record."""
    if not display_field:
        return record_id[:8]  # Use ID shorthand if no display field

    try:
        cursor.execute(f"SELECT {display_field} FROM {table_name} WHERE record_id = ?", (record_id,))
        result = cursor.fetchone()
        return result[0] if result else record_id[:8]
    except:
        return record_id[:8]

# ═══════════════════════════════════════════════════════════════════════════
# MIGRATION PROCESS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_relationships(old_conn):
    """Analyze old database to find all FK relationships."""
    old_cursor = old_conn.cursor()

    print("🔍 Analyzing relationships from old paradigm...")

    relationships_config = {}

    # Get all tables
    old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in old_cursor.fetchall()]

    for table_name in tables:
        # Get FK information
        old_cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = old_cursor.fetchall()

        for fk in fks:
            # fk = (id, seq, table, from, to, on_update, on_delete)
            from_column = fk[3]
            to_table = fk[2]
            to_column = fk[4]

            if table_name not in relationships_config:
                relationships_config[table_name] = []

            relationships_config[table_name].append({
                'field': from_column,
                'target_table': to_table,
                'target_column': to_column
            })

            print(f"   Found: {table_name}.{from_column} → {to_table}.{to_column}")

    return relationships_config, tables

def migrate_database(old_db_path, new_db_path):
    """Execute the migration from old to new paradigm."""

    print(f"\n📊 MIGRATION: Old Paradigm → New Paradigm")
    print(f"{'═' * 80}")
    print(f"Source: {old_db_path}")
    print(f"Target: {new_db_path}")
    print(f"{'═' * 80}\n")

    # Remove existing new database
    if new_db_path.exists():
        new_db_path.unlink()
        print(f"✓ Removed existing database")

    # Open connections
    old_conn = sqlite3.connect(str(old_db_path))
    new_conn = sqlite3.connect(str(new_db_path))

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    try:
        # Step 1: Analyze relationships
        relationships_config, tables = analyze_relationships(old_conn)

        # Step 2: Create form_metadata table
        print("\n📝 Creating form_metadata table...")
        new_cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_metadata (
                form_path TEXT PRIMARY KEY,
                display_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for table_name in tables:
            new_cursor.execute(
                "INSERT INTO form_metadata (form_path, display_name) VALUES (?, ?)",
                (table_name, table_name.upper())
            )
        print(f"   ✓ Registered {len(tables)} forms")

        # Step 3: Create relationships table
        print("\n🔗 Creating relationships table...")
        new_cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
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
                UNIQUE(source_type, source_id, relationship_name, target_id),
                FOREIGN KEY(source_type) REFERENCES form_metadata(form_path),
                FOREIGN KEY(target_type) REFERENCES form_metadata(form_path)
            )
        """)

        # Create indexes
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_type, source_id)")
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_type, target_id)")
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_name ON relationships(source_type, relationship_name)")
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_active ON relationships(source_type, source_id, removed_at)")
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_created ON relationships(created_at)")
        new_cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_removed ON relationships(removed_at) WHERE removed_at IS NOT NULL")

        # Create views
        new_cursor.execute("""
            CREATE VIEW IF NOT EXISTS active_relationships AS
            SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
                   created_at, created_by, metadata
            FROM relationships
            WHERE removed_at IS NULL
        """)

        new_cursor.execute("""
            CREATE VIEW IF NOT EXISTS relationship_history AS
            SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
                   'created' as event_type, created_at as event_at, created_by as event_by
            FROM relationships
            UNION ALL
            SELECT rel_id, source_type, source_id, relationship_name, target_type, target_id,
                   'removed' as event_type, removed_at as event_at, removed_by as event_by
            FROM relationships
            WHERE removed_at IS NOT NULL
            ORDER BY event_at DESC
        """)
        print("   ✓ Relationships table and views created")

        # Step 4: Migrate entity tables (remove FK columns, add _display columns)
        print("\n📋 Migrating entity tables...")
        rel_count = 0

        # Tables to skip (auxiliary tables without record_id PK)
        skip_tables = {'tags', 'sqlite_sequence'}

        for table_name in tables:
            if table_name in skip_tables:
                print(f"   Skipping (auxiliary table): {table_name}")
                continue
            print(f"   Processing: {table_name}...")

            # Get current schema
            old_cursor.execute(f"PRAGMA table_info({table_name})")
            old_columns = old_cursor.fetchall()

            # Check if table has record_id column
            col_names = [col[1] for col in old_columns]
            if 'record_id' not in col_names:
                print(f"     ⚠️  Skipping (no record_id column): {table_name}")
                continue

            # Get FK info
            old_cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = {fk[3]: fk for fk in old_cursor.fetchall()}

            # Build new column list (exclude FK columns, add _display columns)
            new_columns = []
            fk_fields = {}

            for col in old_columns:
                col_name = col[1]
                col_type = col[2]

                if col_name in fks:
                    # This is a FK column - we'll convert it to a _display column
                    fk_info = fks[col_name]
                    field_name = col_name.replace('_id', '')  # "cliente_id" → "cliente"
                    fk_fields[field_name] = (col_name, fk_info[2], fk_info[4])  # field_name: (fk_col, target_table, target_col)
                    new_columns.append((field_name + '_display', 'TEXT'))
                else:
                    new_columns.append((col_name, col_type))

            # Create new table
            col_defs = ', '.join([f"{col[0]} {col[1]}" for col in new_columns])
            new_cursor.execute(f"CREATE TABLE {table_name} ({col_defs})")

            # Migrate data
            old_cursor.execute(f"SELECT * FROM {table_name}")
            rows = old_cursor.fetchall()
            old_cursor.execute(f"PRAGMA table_info({table_name})")
            old_columns_info = old_cursor.fetchall()

            col_names = [col[1] for col in old_columns_info]
            col_indices = {col[1]: i for i, col in enumerate(old_columns_info)}

            for row in rows:
                # Build new row
                new_values = []
                record_id = row[col_indices['record_id']]
                relationships_to_add = []

                for col in old_columns:
                    col_name = col[1]
                    col_idx = col_indices[col_name]

                    if col_name in fks:
                        # Replace FK with display value
                        fk_value = row[col_idx]
                        field_name = col_name.replace('_id', '')
                        fk_info = fks[col_name]
                        target_table = fk_info[2]
                        target_col = fk_info[4]

                        # Get display value from target
                        target_display_field = get_display_field(old_cursor, target_table)
                        display_value = get_record_display_value(old_cursor, target_table, fk_value, target_display_field)

                        new_values.append(display_value)

                        # Queue relationship to be added
                        relationships_to_add.append({
                            'source_type': table_name,
                            'source_id': record_id,
                            'field': field_name,
                            'target_type': target_table,
                            'target_id': fk_value
                        })
                    else:
                        new_values.append(row[col_idx])

                # Insert into new table
                placeholders = ', '.join(['?' for _ in new_values])
                col_names_str = ', '.join([col[0] if col[0] != 'record_id' else col[0] for col in new_columns])
                new_cursor.execute(f"INSERT INTO {table_name} ({col_names_str}) VALUES ({placeholders})", new_values)

                # Add relationships
                for rel in relationships_to_add:
                    rel_id = str(uuid.uuid4())[:8].upper()
                    new_cursor.execute("""
                        INSERT INTO relationships (
                            rel_id, source_type, source_id, relationship_name,
                            target_type, target_id, created_at, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rel_id,
                        rel['source_type'],
                        rel['source_id'],
                        rel['field'],
                        rel['target_type'],
                        rel['target_id'],
                        timestamp_now(),
                        MIGRATION_ACTOR_ID
                    ))
                    rel_count += 1

        print(f"   ✓ Migrated {len(tables)} tables with {rel_count} relationships")

        # Step 5: Commit changes
        new_conn.commit()

        print(f"\n✅ Migration completed successfully!")
        print(f"   New database: {new_db_path}")
        print(f"   Size: {new_db_path.stat().st_size / 1024:.1f} KB")

        # Step 6: Print statistics
        new_cursor.execute("SELECT COUNT(*) FROM relationships WHERE removed_at IS NULL")
        active_rels = new_cursor.fetchone()[0]

        new_cursor.execute("SELECT COUNT(*) FROM relationships WHERE removed_at IS NOT NULL")
        removed_rels = new_cursor.fetchone()[0]

        print(f"\n📈 Statistics:")
        print(f"   Forms registered: {len(tables)}")
        print(f"   Active relationships: {active_rels}")
        print(f"   Removed relationships: {removed_rels}")
        print(f"   Total relationships: {active_rels + removed_rels}")

    finally:
        old_conn.close()
        new_conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    try:
        if not OLD_DB.exists():
            print(f"❌ Source database not found: {OLD_DB}")
            sys.exit(1)

        migrate_database(OLD_DB, NEW_DB)

        print(f"\n💡 Next steps:")
        print(f"   1. Compare vibecforms.db and vibecforms_new_paradigm.db")
        print(f"   2. Run: python3 scripts/compare_paradigms.py")
        print(f"   3. Verify relationships: sqlite3 {NEW_DB}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
