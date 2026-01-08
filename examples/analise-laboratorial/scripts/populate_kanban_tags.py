#!/usr/bin/env python3
"""
Script para popular tags de workflow Kanban no sistema LIMS.
"""

import sqlite3
from datetime import datetime

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'

def populate_kanban_tags():
    """Popula tags para os 4 workflows Kanban."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Criar tabela tags se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_name TEXT NOT NULL,
            object_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            applied_by TEXT,
            UNIQUE(object_name, object_id, tag)
        )
    """)

    now = datetime.now().isoformat()
    tags_config = []

    # 1. Workflow ORCAMENTO - 4 estados
    print("📋 Populando tags para Workflow: ORCAMENTO")
    cursor.execute("SELECT record_id FROM orcamento ORDER BY rowid")
    orcamentos = [row[0] for row in cursor.fetchall()]

    if len(orcamentos) >= 4:
        tags_config.extend([
            ('orcamento', orcamentos[0], 'rascunho', now),
            ('orcamento', orcamentos[1], 'enviado', now),
            ('orcamento', orcamentos[2], 'aprovado', now),
            ('orcamento', orcamentos[3], 'em_andamento', now),
        ])
    print(f"   ✓ {len(orcamentos)} orçamentos distribu ídos em 4 estados")

    # 2. Workflow AMOSTRA - 3 estados
    print("📦 Populando tags para Workflow: AMOSTRA")
    cursor.execute("SELECT record_id FROM amostra ORDER BY rowid")
    amostras = [row[0] for row in cursor.fetchall()]

    if len(amostras) >= 3:
        tags_config.extend([
            ('amostra', amostras[0], 'aguardando', now),
            ('amostra', amostras[1], 'recebida', now),
            ('amostra', amostras[2], 'fracionada', now),
        ])
        if len(amostras) > 3:
            tags_config.append(('amostra', amostras[3], 'recebida', now))
    print(f"   ✓ {len(amostras)} amostras distribuídas em 3 estados")

    # 3. Workflow RESULTADO - 3 estados
    print("🧪 Populando tags para Workflow: RESULTADO")
    cursor.execute("SELECT record_id FROM resultado ORDER BY rowid")
    resultados = [row[0] for row in cursor.fetchall()]

    if len(resultados) >= 3:
        tags_config.extend([
            ('resultado', resultados[0], 'aguardando', now),
            ('resultado', resultados[1], 'em_execucao', now),
            ('resultado', resultados[2], 'concluida', now),
        ])
        if len(resultados) > 3:
            tags_config.append(('resultado', resultados[3], 'em_execucao', now))
    print(f"   ✓ {len(resultados)} resultados distribuídos em 3 estados")

    # 4. Workflow LAUDO - 4 estados
    print("📄 Populando tags para Workflow: LAUDO")
    cursor.execute("SELECT record_id FROM laudo ORDER BY rowid")
    laudos = [row[0] for row in cursor.fetchall()]

    if len(laudos) >= 4:
        tags_config.extend([
            ('laudo', laudos[0], 'rascunho', now),
            ('laudo', laudos[1], 'revisao', now),
            ('laudo', laudos[2], 'liberado', now),
            ('laudo', laudos[3], 'entregue', now),
        ])
    print(f"   ✓ {len(laudos)} laudos distribuídos em 4 estados")

    # Inserir todas as tags
    for object_name, object_id, tag, applied_at in tags_config:
        try:
            cursor.execute("""
                INSERT INTO tags (object_name, object_id, tag, applied_at, applied_by)
                VALUES (?, ?, ?, ?, ?)
            """, (object_name, object_id, tag, applied_at, 'sistema'))
        except sqlite3.IntegrityError:
            # Tag já existe, ignora
            pass

    conn.commit()

    # Verificar totais
    cursor.execute("SELECT COUNT(*) FROM tags")
    total_tags = cursor.fetchone()[0]

    cursor.execute("SELECT object_name, COUNT(*) FROM tags GROUP BY object_name")
    tag_counts = cursor.fetchall()

    conn.close()

    print("\n" + "="*60)
    print("✅ TAGS KANBAN POPULADAS COM SUCESSO!")
    print("="*60)
    print(f"\nTotal de tags criadas: {total_tags}")
    print("\nDistribuição por workflow:")
    for obj_name, count in tag_counts:
        print(f"  • {obj_name.upper()}: {count} tags")
    print("\n")

if __name__ == '__main__':
    populate_kanban_tags()
