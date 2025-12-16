#!/usr/bin/env python3
"""
Script para adicionar coluna record_id às tabelas SQLite existentes.

Este script:
1. Conecta ao banco SQLite
2. Para cada tabela, verifica se tem coluna record_id
3. Se não tiver, adiciona a coluna e popula com UUIDs
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.crockford import generate_id


def get_tables(conn):
    """Lista todas as tabelas no banco."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'tags' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def has_record_id_column(conn, table_name):
    """Verifica se uma tabela tem a coluna record_id."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return 'record_id' in columns


def add_record_id_column(conn, table_name):
    """Adiciona coluna record_id à tabela."""
    cursor = conn.cursor()

    print(f"  📝 Adicionando coluna record_id...")
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN record_id TEXT")

    # Criar índice único
    print(f"  📝 Criando índice único...")
    cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_record_id ON {table_name}(record_id)")

    conn.commit()
    print(f"  ✓ Coluna record_id adicionada")


def populate_record_ids(conn, table_name):
    """Popula record_id com UUIDs para registros existentes."""
    cursor = conn.cursor()

    # Contar registros sem UUID
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE record_id IS NULL")
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"  ✓ Todos os registros já têm UUID")
        return

    print(f"  📊 {count} registros precisam de UUID")

    # Obter IDs dos registros sem UUID
    cursor.execute(f"SELECT id FROM {table_name} WHERE record_id IS NULL")
    record_ids = [row[0] for row in cursor.fetchall()]

    # Gerar e atualizar UUIDs
    for record_id in record_ids:
        uuid = generate_id()
        cursor.execute(f"UPDATE {table_name} SET record_id = ? WHERE id = ?", (uuid, record_id))

    conn.commit()
    print(f"  ✓ {count} registros atualizados com UUID")


def migrate_table(conn, table_name):
    """Migra uma tabela adicionando record_id."""
    print(f"\n📄 Processando tabela: {table_name}")

    # Verificar se já tem record_id
    if has_record_id_column(conn, table_name):
        print(f"  ✓ Tabela já tem coluna record_id")
        # Ainda assim, verificar se há registros sem UUID
        populate_record_ids(conn, table_name)
        return True

    try:
        # Adicionar coluna
        add_record_id_column(conn, table_name)

        # Popular com UUIDs
        populate_record_ids(conn, table_name)

        return True
    except Exception as e:
        print(f"  ✗ Erro ao migrar tabela: {e}")
        return False


def backup_database(db_path):
    """Cria backup do banco de dados."""
    backup_dir = os.path.join(os.path.dirname(db_path), '..', 'backups', 'sqlite_uuid_migration')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = os.path.basename(db_path)
    backup_path = os.path.join(backup_dir, f"{db_name}.{timestamp}.backup")

    # Copiar arquivo
    import shutil
    shutil.copy2(db_path, backup_path)

    print(f"  ✓ Backup criado: {backup_path}")
    return backup_path


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Adiciona record_id a tabelas SQLite')
    parser.add_argument('--database', default='data/sqlite/vibecforms.db',
                       help='Caminho do banco SQLite (padrão: data/sqlite/vibecforms.db)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simula a migração sem fazer alterações')

    args = parser.parse_args()

    print("=" * 70)
    print("MIGRAÇÃO SQLite: Adicionar record_id às Tabelas")
    print("=" * 70)

    # Caminho do banco
    db_path = os.path.join(os.path.dirname(__file__), '..', args.database)

    if not os.path.exists(db_path):
        print(f"\n✗ Banco de dados não encontrado: {db_path}")
        return 1

    print(f"\n📁 Banco de dados: {db_path}")

    if args.dry_run:
        print("\n⚠  MODO DRY RUN - Nenhuma alteração será feita\n")
        # Em dry-run, não fazemos backup nem alterações
        conn = sqlite3.connect(db_path)
        tables = get_tables(conn)
        print(f"\n📊 Tabelas encontradas: {len(tables)}")
        for table in tables:
            has_uuid = has_record_id_column(conn, table)
            status = "✓ tem record_id" if has_uuid else "✗ NÃO tem record_id"
            print(f"  - {table}: {status}")
        conn.close()
        return 0

    # Criar backup
    print(f"\n💾 Criando backup...")
    backup_path = backup_database(db_path)

    # Conectar ao banco
    conn = sqlite3.connect(db_path)

    # Obter tabelas
    tables = get_tables(conn)
    print(f"\n📊 Tabelas a processar: {len(tables)}\n")

    # Migrar cada tabela
    success_count = 0
    for table in tables:
        if migrate_table(conn, table):
            success_count += 1

    conn.close()

    # Resumo
    print("\n" + "=" * 70)
    print(f"✓ Migração concluída: {success_count}/{len(tables)} tabelas processadas")
    print("=" * 70)


if __name__ == '__main__':
    sys.exit(main())
