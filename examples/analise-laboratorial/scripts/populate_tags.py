#!/usr/bin/env python3
"""
Script para criar e popular tags nos 4 workflows Kanban do sistema LIMS.

Workflows:
- orcamento (4 estados): rascunho, enviado, aprovado, em_andamento
- amostra (3 estados): aguardando, recebida, fracionada
- resultado (3 estados): aguardando, em_execucao, concluida
- laudo (4 estados): rascunho, revisao, liberado, entregue

Estrutura da tabela tags:
- object_name: nome da entidade (orcamento, amostra, resultado, laudo)
- object_id: ID do registro (formato: entity_id, ex: orcamento_1)
- tag: estado/tag do registro
- applied_at: timestamp quando a tag foi aplicada
- applied_by: quem aplicou a tag (sistema ou usuário)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def get_db_path():
    """Retorna o caminho do banco de dados LIMS."""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "data" / "sqlite" / "lims.db"
    return db_path


def create_tags_table(conn):
    """Cria a tabela tags se não existir."""
    cursor = conn.cursor()

    sql_create = """
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_name TEXT NOT NULL,
        object_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        applied_by TEXT DEFAULT 'sistema',
        UNIQUE(object_name, object_id, tag)
    )
    """

    cursor.execute(sql_create)
    conn.commit()
    print("✓ Tabela 'tags' criada/verificada com sucesso")


def populate_tags(conn):
    """Popula a tabela tags com os dados do Kanban."""
    cursor = conn.cursor()

    # Dados de populacao dos 4 workflows
    tags_data = [
        # ORCAMENTO: 4 orçamentos em 4 estados diferentes
        ("orcamento", "orcamento_1", "rascunho"),
        ("orcamento", "orcamento_2", "enviado"),
        ("orcamento", "orcamento_3", "aprovado"),
        ("orcamento", "orcamento_4", "em_andamento"),

        # AMOSTRA: 4 amostras distribuidas em 3 estados
        ("amostra", "amostra_1", "aguardando"),
        ("amostra", "amostra_2", "recebida"),
        ("amostra", "amostra_3", "fracionada"),
        ("amostra", "amostra_4", "recebida"),

        # RESULTADO: 4 resultados distribuidos em 3 estados
        ("resultado", "resultado_1", "aguardando"),
        ("resultado", "resultado_2", "em_execucao"),
        ("resultado", "resultado_3", "concluida"),
        ("resultado", "resultado_4", "em_execucao"),

        # LAUDO: 4 laudos em 4 estados diferentes
        ("laudo", "laudo_1", "rascunho"),
        ("laudo", "laudo_2", "revisao"),
        ("laudo", "laudo_3", "liberado"),
        ("laudo", "laudo_4", "entregue"),
    ]

    timestamp = datetime.now().isoformat()
    applied_by = "sistema"

    inserted_count = 0
    skipped_count = 0

    for object_name, object_id, tag in tags_data:
        try:
            cursor.execute(
                """INSERT INTO tags (object_name, object_id, tag, applied_at, applied_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (object_name, object_id, tag, timestamp, applied_by)
            )
            inserted_count += 1
            print(f"  ✓ {object_name:10} | {object_id:12} | {tag:15} | inserted")
        except sqlite3.IntegrityError:
            skipped_count += 1
            print(f"  ⊘ {object_name:10} | {object_id:12} | {tag:15} | already exists")

    conn.commit()
    print(f"\nResumo de Populacao:")
    print(f"  Inseridas: {inserted_count} tags")
    print(f"  Duplicadas (skip): {skipped_count} tags")
    print(f"  Total: {inserted_count + skipped_count} tags processadas")


def validate_tags(conn):
    """Valida e exibe estatísticas das tags criadas."""
    cursor = conn.cursor()

    # Total de tags
    cursor.execute("SELECT COUNT(*) FROM tags")
    total = cursor.fetchone()[0]
    print(f"\nValidacao - Total de tags: {total}")

    # Tags por workflow
    cursor.execute("""
        SELECT object_name, COUNT(*) as count
        FROM tags
        GROUP BY object_name
        ORDER BY object_name
    """)

    print("\nTags por workflow:")
    for workflow, count in cursor.fetchall():
        print(f"  {workflow:15} : {count:2} tags")

    # Tags por estado
    print("\nTags por estado:")
    cursor.execute("""
        SELECT object_name, tag, COUNT(*) as count
        FROM tags
        GROUP BY object_name, tag
        ORDER BY object_name, tag
    """)

    for workflow, tag, count in cursor.fetchall():
        print(f"  {workflow:15} | {tag:15} : {count}")


def main():
    """Função principal."""
    db_path = get_db_path()

    print(f"Criando/Populando tags Kanban para sistema LIMS")
    print(f"Banco de dados: {db_path}")
    print()

    # Verificar se o banco existe
    if not db_path.exists():
        print(f"✗ Banco de dados não encontrado: {db_path}")
        sys.exit(1)

    # Conectar ao banco
    try:
        conn = sqlite3.connect(str(db_path))
        print("✓ Conectado ao banco de dados")
    except sqlite3.Error as e:
        print(f"✗ Erro ao conectar ao banco: {e}")
        sys.exit(1)

    try:
        # Criar tabela tags
        create_tags_table(conn)

        # Popular tags
        print("\nPopulando tags:")
        populate_tags(conn)

        # Validar e exibir estatísticas
        validate_tags(conn)

        print("\n✓ Script concluído com sucesso!")

    except sqlite3.Error as e:
        print(f"\n✗ Erro ao processar banco: {e}")
        conn.close()
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    main()
