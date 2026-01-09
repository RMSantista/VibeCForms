#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCForms v3.0 - Paradigm Comparison Script

Compare the old paradigm (v2.4) with the new paradigm (v3.0) databases.
Shows the differences in structure, relationships, and data handling.
"""

import sqlite3
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

EXAMPLES_DIR = Path(__file__).parent.parent
OLD_DB = EXAMPLES_DIR / "data" / "sqlite" / "vibecforms.db"
NEW_DB = EXAMPLES_DIR / "data" / "sqlite" / "vibecforms_new_paradigm.db"

# ═══════════════════════════════════════════════════════════════════════════
# COMPARISON FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def compare_table_structures():
    """Compare table structures between old and new paradigms."""
    print("\n" + "═" * 80)
    print("📊 TABLE STRUCTURE COMPARISON")
    print("═" * 80)

    # Check if new paradigm has relationships table
    print("\n🔗 Universal Relationships Table (NEW PARADIGM ONLY)")
    print("-" * 80)

    try:
        conn = sqlite3.connect(str(NEW_DB))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(relationships)")
        columns = cursor.fetchall()

        print("\nNew Paradigm - relationships table columns:")
        print("\n┌──────────────────┬──────────┬─────────────────────────┐")
        print("│ Column           │ Type     │ Purpose                 │")
        print("├──────────────────┼──────────┼─────────────────────────┤")

        column_info = [
            ("rel_id", "TEXT PRIMARY KEY", "Relationship UUID"),
            ("source_type", "TEXT NOT NULL", "Source entity type"),
            ("source_id", "TEXT NOT NULL", "Source record ID"),
            ("relationship_name", "TEXT NOT NULL", "Field name (e.g., 'paciente')"),
            ("target_type", "TEXT NOT NULL", "Target entity type"),
            ("target_id", "TEXT NOT NULL", "Target record ID"),
            ("created_at", "TEXT NOT NULL", "Creation timestamp"),
            ("created_by", "TEXT NOT NULL", "Actor who created"),
            ("removed_at", "TEXT", "Soft-delete timestamp"),
            ("removed_by", "TEXT", "Actor who removed"),
            ("metadata", "TEXT", "JSON metadata"),
        ]

        for col_name, col_type, purpose in column_info:
            print(f"│ {col_name:16} │ {col_type:8} │ {purpose:23} │")

        print("└──────────────────┴──────────┴─────────────────────────┘")

        # Show example relationships
        print("\n📋 Example Relationships from New Paradigm:")
        print("-" * 80)

        cursor.execute("""
            SELECT
                substr(rel_id, 1, 8) as rel_id_short,
                source_type,
                substr(source_id, 1, 4) as src_id,
                relationship_name,
                target_type,
                substr(target_id, 1, 4) as tgt_id,
                CASE WHEN removed_at IS NULL THEN '✓ Active' ELSE '✗ Removed' END as status
            FROM relationships
            LIMIT 8
        """)

        rows = cursor.fetchall()
        print("\nRel ID   | Source   | SrcID | Relationship | Target     | TgtID | Status")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:8} | {row[1]:8} | {row[2]:5} | {row[3]:12} | {row[4]:10} | {row[5]:5} | {row[6]}")

        conn.close()
    except FileNotFoundError:
        print("\n❌ New paradigm database not found at:", NEW_DB)
    except Exception as e:
        print(f"\n⚠️  Error reading new paradigm: {e}")

def compare_display_values():
    """Compare how display values are handled."""
    print("\n" + "═" * 80)
    print("📝 DISPLAY VALUE HANDLING COMPARISON")
    print("═" * 80)

    print("\n🔴 OLD PARADIGM (v2.4):")
    print("-" * 80)
    print("Display values are COMPUTED on read-time via JOIN:")
    print("""
    SELECT e.id, p.nome, p.cpf, e.data_solicitacao
    FROM exames e
    JOIN pacientes p ON e.paciente_id = p.id
    WHERE e.id = ?

    ⚠️  Issues:
    - Every read requires JOIN (performance)
    - Display values must be recalculated
    - Stale data possible if paciente.nome changes
    - No history of display value changes
    """)

    print("\n🟢 NEW PARADIGM (v3.0):")
    print("-" * 80)
    print("Display values are DENORMALIZED in entity tables:")
    print("""
    SELECT _record_id, paciente_display, data_solicitacao
    FROM exames
    WHERE _record_id = ?

    ✅ Benefits:
    - Single table lookup (no JOIN)
    - Display values ready to use
    - Sync strategies (EAGER, LAZY, SCHEDULED)
    - Audit trail of display value changes
    """)

    # Show actual examples
    try:
        conn = sqlite3.connect(str(NEW_DB))
        cursor = conn.cursor()

        print("\n📋 Example Display Values (New Paradigm):")
        print("-" * 80)

        cursor.execute("""
            SELECT
                substr(_record_id, 1, 8) as exame_id,
                paciente_display,
                medico_display,
                status
            FROM exames
            LIMIT 4
        """)

        rows = cursor.fetchall()
        print("\nExame ID | Paciente Display         | Medico Display       | Status")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:8} | {row[1]:24} | {row[2]:20} | {row[3]}")

        conn.close()
    except Exception as e:
        print(f"\n⚠️  Error: {e}")

def compare_audit_trail():
    """Compare audit trail capabilities."""
    print("\n" + "═" * 80)
    print("🔐 AUDIT TRAIL & SOFT-DELETE COMPARISON")
    print("═" * 80)

    print("\n🔴 OLD PARADIGM (v2.4):")
    print("-" * 80)
    print("""
    DELETE FROM exames WHERE id = 123;

    ❌ Issues:
    - Record is permanently deleted
    - No recovery possible
    - No audit trail (who deleted? when?)
    - Difficult to track historical changes
    """)

    print("\n🟢 NEW PARADIGM (v3.0):")
    print("-" * 80)
    print("""
    UPDATE relationships
    SET removed_at = '2026-01-08T16:13:00', removed_by = 'user@example.com'
    WHERE rel_id = 'ABC123...';

    ✅ Benefits:
    - Record preserved in database
    - Complete audit trail (when, who, why)
    - Easy recovery (set removed_at = NULL)
    - Full history tracking via views
    """)

    # Show actual soft-deleted relationships
    try:
        conn = sqlite3.connect(str(NEW_DB))
        cursor = conn.cursor()

        print("\n📋 Soft-Deleted Relationships (Audit Trail):")
        print("-" * 80)

        cursor.execute("""
            SELECT
                substr(rel_id, 1, 8) as rel_id,
                source_type,
                relationship_name,
                target_type,
                created_at,
                removed_at,
                removed_by
            FROM relationships
            WHERE removed_at IS NOT NULL
        """)

        rows = cursor.fetchall()
        if rows:
            print("\nRel ID   | Source   | Relationship | Target  | Created               | Removed               | Removed By")
            print("-" * 120)
            for row in rows:
                print(f"{row[0]:8} | {row[1]:8} | {row[2]:12} | {row[3]:7} | {row[4]:21} | {row[5]:21} | {row[6]}")
        else:
            print("(No soft-deleted relationships found)")

        conn.close()
    except Exception as e:
        print(f"\n⚠️  Error: {e}")

def compare_schema_evolution():
    """Compare schema evolution capabilities."""
    print("\n" + "═" * 80)
    print("🔄 SCHEMA EVOLUTION (Cardinality Changes)")
    print("═" * 80)

    print("\n📋 Scenario: Upgrade from 1:N to N:N relationship")
    print("(e.g., one exame can belong to multiple pacientes)")
    print("-" * 80)

    print("\n🔴 OLD PARADIGM (v2.4):")
    print("-" * 80)
    print("""
    Current: exames.paciente_id (1:N)

    Required changes:
    1. Create bridge table: exames_pacientes
    2. Migrate data from exames.paciente_id
    3. Add FK to exames_pacientes
    4. Drop paciente_id from exames
    5. Update all application code (JOINs)
    6. Test thoroughly (risk of data loss)

    ⏱️  Time: Days
    📊 Risk: High (schema migration)
    💾 Downtime: Possible (depends on data size)
    """)

    print("\n🟢 NEW PARADIGM (v3.0):")
    print("-" * 80)
    print("""
    Current: relationships table with 1:N entries

    To upgrade to N:N:
    1. Just insert another relationship row!

    INSERT INTO relationships (
        rel_id, source_type, source_id, relationship_name,
        target_type, target_id, created_at, created_by
    ) VALUES (...);

    ✅ No schema changes
    ✅ No data migration
    ✅ Complete audit trail
    ✅ Both relationships visible in history

    ⏱️  Time: Seconds
    📊 Risk: None (simple INSERT)
    💾 Downtime: None
    """)

def compare_statistics():
    """Compare database statistics."""
    print("\n" + "═" * 80)
    print("📈 DATABASE STATISTICS")
    print("═" * 80)

    stats = []

    # Old paradigm
    try:
        conn = sqlite3.connect(str(OLD_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        old_tables = cursor.fetchone()[0]

        cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
        old_size = cursor.fetchone()[0] / 1024  # KB

        stats.append(("Old Paradigm (v2.4)", old_tables, "Various", f"{old_size:.1f} KB", "Foreign Keys"))
        conn.close()
    except Exception as e:
        stats.append(("Old Paradigm (v2.4)", "?", "?", "?", str(e)))

    # New paradigm
    try:
        conn = sqlite3.connect(str(NEW_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        new_tables = cursor.fetchone()[0]

        cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
        new_size = cursor.fetchone()[0] / 1024  # KB

        cursor.execute("SELECT COUNT(*) FROM relationships WHERE removed_at IS NULL")
        active_rels = cursor.fetchone()[0]

        stats.append(("New Paradigm (v3.0)", new_tables, f"{active_rels} active", f"{new_size:.1f} KB", "Relationships Table"))
        conn.close()
    except Exception as e:
        stats.append(("New Paradigm (v3.0)", "?", "?", "?", str(e)))

    print("\nVersion                  | Tables | Relationships | Size      | Key Feature")
    print("-" * 80)
    for stat in stats:
        print(f"{stat[0]:24} | {stat[1]:6} | {stat[2]:13} | {stat[3]:9} | {stat[4]}")

def main():
    """Run comparison."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "VibeCForms v3.0 - Paradigm Comparison" + " " * 27 + "║")
    print("║" + " " * 10 + "Old Paradigm (v2.4) vs New Paradigm (v3.0)" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")

    if not NEW_DB.exists():
        print(f"\n❌ Error: New paradigm database not found at:\n   {NEW_DB}")
        print(f"\nCreate it first with:\n   python3 {Path(__file__).parent}/create_demo_db.py")
        return

    compare_table_structures()
    compare_display_values()
    compare_audit_trail()
    compare_schema_evolution()
    compare_statistics()

    print("\n" + "═" * 80)
    print("📚 SUMMARY")
    print("═" * 80)
    print("""
    Old Paradigm (v2.4):
    ✓ Simple JOINS
    ✓ Standard SQL
    ✗ Foreign key columns in entities
    ✗ Complex N:N handling
    ✗ No built-in soft-delete
    ✗ Difficult schema evolution

    New Paradigm (v3.0):
    ✓ Universal relationship table
    ✓ All cardinalities (1:1, 1:N, N:N)
    ✓ Soft-delete + audit trail
    ✓ Display value denormalization
    ✓ Zero-migration schema evolution
    ✓ Reverse navigation support
    ✗ Slightly more complex queries
    ✗ Must denormalize display values

    Migration Path:
    Both paradigms can coexist during transition.
    Gradual migration possible without downtime.
    """)
    print("═" * 80 + "\n")

if __name__ == "__main__":
    main()
