#!/usr/bin/env python3
"""
Script para corrigir o schema mismatch entre specs e SQLite.

Este script:
1. Faz backup do banco de dados
2. Adiciona colunas faltantes
3. Renomeia colunas quando necessário
4. Remove colunas obsoletas (opcional)
5. Valida a correção
"""

import sqlite3
import shutil
import json
from datetime import datetime
from pathlib import Path

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'
BACKUP_DIR = 'examples/analise-laboratorial/backups/schema_fix'

# Mapeamento de correções
SCHEMA_FIXES = {
    'metodologias': {
        'add_columns': [
            ('versao', 'TEXT', None)  # (nome, tipo, valor_padrao)
        ]
    },
    'classificacao_amostras': {
        'rename_columns': [
            ('nome', 'classificacao')  # (antigo, novo)
        ]
    },
    'fracionamento': {
        'rename_columns': [
            ('entrada_amostra', 'entrada'),
        ],
        'add_columns': [
            ('data_hora', 'TEXT', None)
        ],
        'drop_columns': [
            'data_fracionamento',
            'hora_fracionamento'
        ]
    },
    'laudo': {
        'add_columns': [
            ('observacoes', 'TEXT', None)
        ],
        'drop_columns': [
            'status_tag'
        ]
    },
    'precos_cliente': {
        'rename_columns': [
            ('data_inicio', 'vigencia_inicio'),
            ('data_fim', 'vigencia_fim')
        ]
    },
    'tipos_amostras': {
        'rename_columns': [
            ('nome', 'tipo')
        ]
    },
    'analises_resultados': {
        'add_columns': [
            ('analise', 'TEXT', None),
            ('analista', 'TEXT', None),
            ('observacoes', 'TEXT', None)
        ],
        'drop_columns': [
            'status_tag'
        ]
    }
}


def backup_database():
    """Cria backup do banco de dados."""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{BACKUP_DIR}/vibecforms_{timestamp}.db'

    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path


def add_column(conn, table_name, column_name, column_type, default_value=None):
    """Adiciona uma coluna à tabela."""
    try:
        cursor = conn.cursor()

        # SQLite não suporta DEFAULT com NULL, então usamos DEFAULT '' para TEXT
        if default_value is None and column_type == 'TEXT':
            default_clause = "DEFAULT ''"
        elif default_value is not None:
            default_clause = f"DEFAULT {default_value}"
        else:
            default_clause = ""

        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {default_clause}"
        cursor.execute(sql)
        conn.commit()
        print(f"  ✓ Adicionada coluna {column_name} em {table_name}")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"  ⚠️  Coluna {column_name} já existe em {table_name}")
            return True
        else:
            print(f"  ❌ Erro ao adicionar {column_name} em {table_name}: {e}")
            return False


def rename_column_via_recreation(conn, table_name, old_name, new_name):
    """Renomeia coluna recriando a tabela (SQLite não tem RENAME COLUMN antes 3.25.0)."""
    try:
        cursor = conn.cursor()

        # 1. Obter schema atual
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 2. Construir lista de colunas com o novo nome
        column_defs = []
        column_names_old = []
        column_names_new = []

        for col in columns:
            col_name = col[1]
            col_type = col[2]
            col_notnull = col[3]
            col_pk = col[5]

            # Nome da coluna
            if col_name == old_name:
                new_col_name = new_name
            else:
                new_col_name = col_name

            # Definição da coluna
            col_def = f"{new_col_name} {col_type}"
            if col_notnull:
                col_def += " NOT NULL"
            if col_pk:
                col_def += " PRIMARY KEY"

            column_defs.append(col_def)
            column_names_old.append(col_name)
            column_names_new.append(new_col_name)

        # 3. Criar nova tabela temporária
        temp_table = f"{table_name}_temp"
        create_sql = f"CREATE TABLE {temp_table} ({', '.join(column_defs)})"
        cursor.execute(create_sql)

        # 4. Copiar dados
        columns_list_old = ', '.join(column_names_old)
        columns_list_new = ', '.join(column_names_new)
        cursor.execute(f"INSERT INTO {temp_table} ({columns_list_new}) SELECT {columns_list_old} FROM {table_name}")

        # 5. Dropar tabela antiga
        cursor.execute(f"DROP TABLE {table_name}")

        # 6. Renomear tabela temporária
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

        conn.commit()
        print(f"  ✓ Renomeada coluna {old_name} → {new_name} em {table_name}")
        return True

    except Exception as e:
        print(f"  ❌ Erro ao renomear {old_name} em {table_name}: {e}")
        conn.rollback()
        return False


def drop_column_via_recreation(conn, table_name, column_name):
    """Remove coluna recriando a tabela."""
    try:
        cursor = conn.cursor()

        # 1. Obter schema atual
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 2. Filtrar a coluna a ser removida
        column_defs = []
        column_names = []

        for col in columns:
            col_name = col[1]
            if col_name == column_name:
                continue  # Pula a coluna a ser removida

            col_type = col[2]
            col_notnull = col[3]
            col_pk = col[5]

            col_def = f"{col_name} {col_type}"
            if col_notnull:
                col_def += " NOT NULL"
            if col_pk:
                col_def += " PRIMARY KEY"

            column_defs.append(col_def)
            column_names.append(col_name)

        if not column_names:
            print(f"  ⚠️  Nenhuma coluna restante após remover {column_name}")
            return False

        # 3. Criar nova tabela temporária
        temp_table = f"{table_name}_temp"
        create_sql = f"CREATE TABLE {temp_table} ({', '.join(column_defs)})"
        cursor.execute(create_sql)

        # 4. Copiar dados
        columns_list = ', '.join(column_names)
        cursor.execute(f"INSERT INTO {temp_table} ({columns_list}) SELECT {columns_list} FROM {table_name}")

        # 5. Dropar tabela antiga
        cursor.execute(f"DROP TABLE {table_name}")

        # 6. Renomear tabela temporária
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

        conn.commit()
        print(f"  ✓ Removida coluna {column_name} de {table_name}")
        return True

    except Exception as e:
        print(f"  ❌ Erro ao remover {column_name} de {table_name}: {e}")
        conn.rollback()
        return False


def apply_fixes():
    """Aplica todas as correções de schema."""
    print("\n" + "="*60)
    print("CORREÇÃO DE SCHEMA MISMATCH")
    print("="*60)

    # 1. Backup
    print("\n1️⃣  CRIANDO BACKUP")
    print("-" * 60)
    backup_path = backup_database()

    # 2. Aplicar correções
    print("\n2️⃣  APLICANDO CORREÇÕES")
    print("-" * 60)

    conn = sqlite3.connect(DB_PATH)

    for table_name, fixes in SCHEMA_FIXES.items():
        print(f"\n📋 {table_name}:")

        # Adicionar colunas
        if 'add_columns' in fixes:
            for col_name, col_type, default_val in fixes['add_columns']:
                add_column(conn, table_name, col_name, col_type, default_val)

        # Renomear colunas
        if 'rename_columns' in fixes:
            for old_name, new_name in fixes['rename_columns']:
                rename_column_via_recreation(conn, table_name, old_name, new_name)

        # Remover colunas
        if 'drop_columns' in fixes:
            for col_name in fixes['drop_columns']:
                drop_column_via_recreation(conn, table_name, col_name)

    conn.close()

    # 3. Validação
    print("\n3️⃣  VALIDAÇÃO")
    print("-" * 60)
    validate_fixes()

    print("\n" + "="*60)
    print("✅ CORREÇÕES CONCLUÍDAS!")
    print("="*60)
    print(f"\nBackup salvo em: {backup_path}")
    print("Caso haja problemas, você pode restaurar com:")
    print(f"  cp {backup_path} {DB_PATH}")


def validate_fixes():
    """Valida que as correções foram aplicadas corretamente."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table_name in SCHEMA_FIXES.keys():
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]

        # Carregar spec
        spec_path = f'examples/analise-laboratorial/specs/{table_name}.json'
        with open(spec_path) as f:
            spec = json.load(f)

        spec_fields = {field['name'] for field in spec['fields']}
        sqlite_fields = set(col_names) - {'record_id'}

        if spec_fields == sqlite_fields:
            print(f"  ✅ {table_name}: Schema OK")
        else:
            missing = spec_fields - sqlite_fields
            extra = sqlite_fields - spec_fields
            if missing:
                print(f"  ⚠️  {table_name}: Faltando {missing}")
            if extra:
                print(f"  ⚠️  {table_name}: Extra {extra}")

    conn.close()


if __name__ == '__main__':
    apply_fixes()
