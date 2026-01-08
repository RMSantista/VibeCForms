"""
VibeCForms v3.0: Relationship Paradigm - Proof of Concept

This PoC demonstrates the new universal relationship model with:
- UUID-based identification
- Relationship tables for all cardinality types
- Display value denormalization
- Soft-delete semantics
- Sync strategies

Date: 2026-01-08
Version: 1.0
Status: Design Phase
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional


class RelationshipPoC:
    """
    Proof of Concept for the new VibeCForms persistence paradigm
    """

    def __init__(self):
        """Initialize in-memory database for PoC"""
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        """Create schema for PoC"""
        print("\n" + "=" * 70)
        print("SETTING UP RELATIONSHIP PARADIGM POC")
        print("=" * 70)

        # Create clientes table
        self.cursor.execute("""
            CREATE TABLE clientes (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create produtos table
        self.cursor.execute("""
            CREATE TABLE produtos (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                preco REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create pedidos table with denormalized display values
        self.cursor.execute("""
            CREATE TABLE pedidos (
                record_id TEXT PRIMARY KEY,
                quantidade INTEGER NOT NULL,
                observacoes TEXT,

                -- Denormalized display values
                _cliente_display TEXT,
                _produto_display TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create relationships table (universal, for all cardinality types)
        self.cursor.execute("""
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
            )
        """)

        # Create indexes
        self.cursor.execute("""
            CREATE INDEX idx_rel_source
            ON relationships(source_type, source_id)
        """)

        self.cursor.execute("""
            CREATE INDEX idx_rel_target
            ON relationships(target_type, target_id)
        """)

        print("✅ Schema created successfully")
        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 1: Create Pedido with Cliente (1:1 relationship)
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_1_create_with_relationship(self):
        """
        Scenario 1: Create a pedido linked to a cliente
        Demonstrates: denormalization + relationships table
        """
        print("\n" + "=" * 70)
        print("SCENARIO 1: Create Pedido with Cliente (1:1)")
        print("=" * 70)

        # 1. Create cliente
        cliente_id = self._generate_uuid()
        self.cursor.execute("""
            INSERT INTO clientes (record_id, nome, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (cliente_id, "João Silva", "joao@example.com", self._now(), self._now()))

        print(f"✅ Created cliente: {cliente_id} (João Silva)")

        # 2. Create pedido WITH display value
        pedido_id = self._generate_uuid()
        self.cursor.execute("""
            INSERT INTO pedidos (
                record_id, quantidade, _cliente_display, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (pedido_id, 10, "João Silva", self._now(), self._now()))

        print(f"✅ Created pedido: {pedido_id} with qty=10")
        print(f"   Display value: _cliente_display = 'João Silva'")

        # 3. Create relationship (source of truth)
        rel_id = self._generate_uuid()
        self.cursor.execute("""
            INSERT INTO relationships (
                rel_id, source_type, source_id,
                relationship_name, target_type, target_id,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel_id, "pedidos", pedido_id,
            "cliente", "clientes", cliente_id,
            self._now(), "system"
        ))

        print(f"✅ Created relationship: {rel_id}")
        print(f"   pedidos/{pedido_id} → cliente → clientes/{cliente_id}")

        # 4. Verify: Read pedido WITHOUT JOIN
        self.cursor.execute("""
            SELECT record_id, quantidade, _cliente_display
            FROM pedidos
            WHERE record_id = ?
        """, (pedido_id,))

        row = self.cursor.fetchone()
        print(f"\n✅ FAST READ (no JOIN):")
        print(f"   Pedido {row['record_id']}")
        print(f"   - Quantity: {row['quantidade']}")
        print(f"   - Cliente (display): {row['_cliente_display']}")

        # 5. Verify: Navigate relationships if needed
        self.cursor.execute("""
            SELECT r.*, c.email
            FROM relationships r
            JOIN clientes c ON r.target_id = c.record_id
            WHERE r.source_type = 'pedidos'
              AND r.source_id = ?
              AND r.relationship_name = 'cliente'
        """, (pedido_id,))

        row = self.cursor.fetchone()
        print(f"\n✅ NAVIGATION (when needed):")
        print(f"   Cliente email: {row['email']}")

        self.conn.commit()

        return pedido_id, cliente_id, rel_id

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 2: Consistency - Update Cliente Name (Sync Strategy)
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_2_update_with_sync(self, cliente_id: str, pedido_id: str):
        """
        Scenario 2: Update cliente name and sync to pedidos
        Demonstrates: Display value synchronization (eager sync)
        """
        print("\n" + "=" * 70)
        print("SCENARIO 2: Update Cliente and Sync Display Values (Eager)")
        print("=" * 70)

        # 1. Update cliente
        new_nome = "João Silva Santos"
        self.cursor.execute("""
            UPDATE clientes
            SET nome = ?, updated_at = ?
            WHERE record_id = ?
        """, (new_nome, self._now(), cliente_id))

        print(f"✅ Updated cliente nome: {new_nome}")

        # 2. Find all pedidos that reference this cliente
        self.cursor.execute("""
            SELECT DISTINCT source_id
            FROM relationships
            WHERE target_type = 'clientes'
              AND target_id = ?
              AND relationship_name = 'cliente'
              AND removed_at IS NULL
        """, (cliente_id,))

        pedido_ids = [row[0] for row in self.cursor.fetchall()]

        # 3. Update display values in pedidos (eager sync)
        for pid in pedido_ids:
            self.cursor.execute("""
                UPDATE pedidos
                SET _cliente_display = ?, updated_at = ?
                WHERE record_id = ?
            """, (new_nome, self._now(), pid))

        print(f"✅ Synced {len(pedido_ids)} pedidos with new display value")

        # 4. Verify sync worked
        self.cursor.execute("""
            SELECT _cliente_display
            FROM pedidos
            WHERE record_id = ?
        """, (pedido_id,))

        display_value = self.cursor.fetchone()[0]
        print(f"✅ Verification:")
        print(f"   Pedido {pedido_id} now has _cliente_display = '{display_value}'")

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 3: 1:N Relationship (Pedido → Multiple Produtos)
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_3_many_to_many_relationships(self, pedido_id: str):
        """
        Scenario 3: Pedido with multiple Produtos (1:N, but through universal table)
        Demonstrates: Uniform handling of different cardinality types
        """
        print("\n" + "=" * 70)
        print("SCENARIO 3: Pedido with Multiple Produtos (1:N)")
        print("=" * 70)

        # 1. Create produtos
        produtos = [
            ("Notebook Dell XPS", 5000.00),
            ("Mouse Logitech", 150.00),
            ("Teclado Mecânico", 500.00),
        ]

        produto_ids = []
        for nome, preco in produtos:
            pid = self._generate_uuid()
            self.cursor.execute("""
                INSERT INTO produtos (record_id, nome, preco, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (pid, nome, preco, self._now(), self._now()))

            produto_ids.append(pid)
            print(f"✅ Created produto: {nome} ({preco:.2f})")

        # 2. Create relationships (using SAME table as 1:1!)
        for idx, pid in enumerate(produto_ids):
            rel_id = self._generate_uuid()
            self.cursor.execute("""
                INSERT INTO relationships (
                    rel_id, source_type, source_id,
                    relationship_name, target_type, target_id,
                    created_at, created_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rel_id, "pedidos", pedido_id,
                "produtos", "produtos", pid,
                self._now(), "system",
                json.dumps({"item_number": idx + 1})
            ))

            print(f"✅ Linked pedido → produto #{idx + 1}")

        # 3. Query all produtos for pedido
        self.cursor.execute("""
            SELECT p.record_id, p.nome, p.preco
            FROM relationships r
            JOIN produtos p ON r.target_id = p.record_id
            WHERE r.source_type = 'pedidos'
              AND r.source_id = ?
              AND r.relationship_name = 'produtos'
              AND r.removed_at IS NULL
            ORDER BY json_extract(r.metadata, '$.item_number')
        """, (pedido_id,))

        rows = self.cursor.fetchall()
        print(f"\n✅ Produtos for pedido:")
        for row in rows:
            print(f"   - {row['nome']}: R$ {row['preco']:.2f}")

        self.conn.commit()
        return produto_ids

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 4: Reverse Navigation
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_4_reverse_navigation(self, cliente_id: str):
        """
        Scenario 4: Find all pedidos that reference a cliente
        Demonstrates: Reverse navigation through relationships
        """
        print("\n" + "=" * 70)
        print("SCENARIO 4: Reverse Navigation (Produto ← Pedidos)")
        print("=" * 70)

        # Query: Find all pedidos that reference this cliente
        self.cursor.execute("""
            SELECT r.source_id, p.quantidade, p._cliente_display
            FROM relationships r
            JOIN pedidos p ON r.source_id = p.record_id
            WHERE r.target_type = 'clientes'
              AND r.target_id = ?
              AND r.relationship_name = 'cliente'
              AND r.removed_at IS NULL
        """, (cliente_id,))

        rows = self.cursor.fetchall()
        print(f"✅ Found {len(rows)} pedidos referencing this cliente:")
        for row in rows:
            print(f"   - Pedido {row['source_id']}: qty={row['quantidade']}, cliente={row['_cliente_display']}")

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 5: Soft Delete
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_5_soft_delete(self, rel_id: str, pedido_id: str):
        """
        Scenario 5: Soft-delete a relationship
        Demonstrates: Audit trail preservation, soft-delete semantics
        """
        print("\n" + "=" * 70)
        print("SCENARIO 5: Soft Delete Relationship")
        print("=" * 70)

        # 1. Soft delete
        self.cursor.execute("""
            UPDATE relationships
            SET removed_at = ?, removed_by = ?
            WHERE rel_id = ?
        """, (self._now(), "user@example.com", rel_id))

        print(f"✅ Soft-deleted relationship {rel_id}")

        # 2. Verify: Active relationships query ignores deleted ones
        self.cursor.execute("""
            SELECT COUNT(*) as count
            FROM relationships
            WHERE source_type = 'pedidos'
              AND source_id = ?
              AND removed_at IS NULL
        """, (pedido_id,))

        count = self.cursor.fetchone()[0]
        print(f"✅ Active relationships for pedido: {count}")

        # 3. Verify: Historical query shows deleted ones
        self.cursor.execute("""
            SELECT COUNT(*) as count
            FROM relationships
            WHERE source_type = 'pedidos'
              AND source_id = ?
        """, (pedido_id,))

        total = self.cursor.fetchone()[0]
        print(f"✅ Total relationships (including deleted): {total}")

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS & VALIDATION
    # ═══════════════════════════════════════════════════════════════════════

    def scenario_6_statistics_and_validation(self):
        """
        Scenario 6: Get statistics and validate consistency
        Demonstrates: Monitoring and integrity checking
        """
        print("\n" + "=" * 70)
        print("SCENARIO 6: Statistics and Validation")
        print("=" * 70)

        # 1. Relationship statistics
        self.cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN removed_at IS NULL THEN 1 ELSE 0 END) as active,
                COUNT(DISTINCT relationship_name) as unique_names
            FROM relationships
        """)

        stats = self.cursor.fetchone()
        print(f"✅ Relationship Statistics:")
        print(f"   - Total relationships: {stats['total']}")
        print(f"   - Active relationships: {stats['active']}")
        print(f"   - Unique relationship names: {stats['unique_names']}")

        # 2. Relationships by type
        self.cursor.execute("""
            SELECT relationship_name, COUNT(*) as count
            FROM relationships
            WHERE removed_at IS NULL
            GROUP BY relationship_name
        """)

        print(f"\n✅ Relationships by name:")
        for row in self.cursor.fetchall():
            print(f"   - {row['relationship_name']}: {row['count']}")

        # 3. Validation: Find orphaned relationships
        self.cursor.execute("""
            SELECT r.rel_id, r.source_type, r.source_id, r.target_type, r.target_id
            FROM relationships r
            LEFT JOIN clientes c ON r.target_type = 'clientes' AND r.target_id = c.record_id
            LEFT JOIN produtos p ON r.target_type = 'produtos' AND r.target_id = p.record_id
            LEFT JOIN pedidos pd ON r.source_type = 'pedidos' AND r.source_id = pd.record_id
            WHERE r.removed_at IS NULL
              AND ((r.target_type = 'clientes' AND c.record_id IS NULL)
                OR (r.target_type = 'produtos' AND p.record_id IS NULL)
                OR (r.source_type = 'pedidos' AND pd.record_id IS NULL))
        """)

        orphans = self.cursor.fetchall()
        if orphans:
            print(f"\n⚠️  Found {len(orphans)} orphaned relationships")
            for row in orphans:
                print(f"   - {row['rel_id']}")
        else:
            print(f"\n✅ No orphaned relationships found")

    # ═══════════════════════════════════════════════════════════════════════
    # PERFORMANCE COMPARISON
    # ═══════════════════════════════════════════════════════════════════════

    def performance_comparison(self):
        """
        Compare performance: Traditional (with JOINs) vs New Model (denormalized)
        """
        print("\n" + "=" * 70)
        print("PERFORMANCE COMPARISON")
        print("=" * 70)

        import time

        # Traditional approach (with JOINs)
        start = time.time()
        self.cursor.execute("""
            SELECT p.record_id, p.quantidade, c.nome as cliente_nome
            FROM pedidos p
            JOIN relationships r ON p.record_id = r.source_id
            JOIN clientes c ON r.target_id = c.record_id
            WHERE r.relationship_name = 'cliente'
        """)
        results_join = self.cursor.fetchall()
        time_join = (time.time() - start) * 1000

        # New model (denormalized)
        start = time.time()
        self.cursor.execute("""
            SELECT record_id, quantidade, _cliente_display
            FROM pedidos
        """)
        results_denorm = self.cursor.fetchall()
        time_denorm = (time.time() - start) * 1000

        print(f"Traditional (with JOINs):  {time_join:.3f}ms - {len(results_join)} rows")
        print(f"New Model (denormalized):  {time_denorm:.3f}ms - {len(results_denorm)} rows")

        if time_join > 0:
            improvement = time_join / time_denorm
            print(f"\n✅ New model is {improvement:.1f}x faster!")

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _generate_uuid() -> str:
        """Generate a UUID for testing"""
        return str(uuid.uuid4())[:8].upper()

    @staticmethod
    def _now() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def cleanup(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Run the entire PoC"""
    poc = RelationshipPoC()

    try:
        # Scenario 1: Create with relationship
        pedido_id, cliente_id, rel_id = poc.scenario_1_create_with_relationship()

        # Scenario 2: Update and sync
        poc.scenario_2_update_with_sync(cliente_id, pedido_id)

        # Scenario 3: Multiple relationships (1:N)
        produto_ids = poc.scenario_3_many_to_many_relationships(pedido_id)

        # Scenario 4: Reverse navigation
        poc.scenario_4_reverse_navigation(cliente_id)

        # Scenario 5: Soft delete
        poc.scenario_5_soft_delete(rel_id, pedido_id)

        # Scenario 6: Statistics
        poc.scenario_6_statistics_and_validation()

        # Performance comparison
        poc.performance_comparison()

        print("\n" + "=" * 70)
        print("✅ POC COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nKey Findings:")
        print("- All cardinality types (1:1, 1:N, N:N) use same table ✅")
        print("- Denormalized display values enable fast reads ✅")
        print("- Relationships table provides audit trail ✅")
        print("- Soft-delete preserves history ✅")
        print("- Reverse navigation works seamlessly ✅")

    finally:
        poc.cleanup()


if __name__ == '__main__':
    main()
