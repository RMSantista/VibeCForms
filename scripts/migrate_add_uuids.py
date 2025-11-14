#!/usr/bin/env python3
"""
Script para adicionar UUIDs a registros existentes em arquivos TXT.

Este script:
1. Varre todos os arquivos .txt em data/txt/
2. Para cada registro sem UUID, gera um UUID Crockford Base32
3. Reescreve o arquivo com UUIDs adicionados

IMPORTANTE: Cria backup antes de modificar!
"""

import os
import sys
import shutil
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.crockford import generate_id


def backup_file(file_path):
    """Cria backup do arquivo antes de modificar."""
    backup_dir = os.path.join(
        os.path.dirname(file_path), "..", "backups", "uuid_migration"
    )
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.backup")

    shutil.copy2(file_path, backup_path)
    print(f"  ✓ Backup criado: {backup_path}")
    return backup_path


def has_uuid(line, delimiter=";"):
    """Verifica se uma linha já tem UUID (27 caracteres)."""
    if not line.strip():
        return True  # Linhas vazias são ignoradas

    parts = line.strip().split(delimiter)
    if len(parts) == 0:
        return True

    # Se o primeiro campo tem exatamente 27 caracteres, provavelmente é um UUID
    first_field = parts[0].strip()
    return len(first_field) == 27


def add_uuid_to_line(line, delimiter=";"):
    """Adiciona UUID ao início de uma linha."""
    if not line.strip():
        return line

    uuid = generate_id()
    return f"{uuid}{delimiter}{line}"


def migrate_file(file_path, delimiter=";", dry_run=False):
    """Migra um arquivo TXT adicionando UUIDs."""
    print(f"\n📄 Processando: {file_path}")

    # Ler arquivo
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ✗ Erro ao ler arquivo: {e}")
        return False

    # Verificar quantas linhas precisam de UUID
    lines_needing_uuid = [
        i for i, line in enumerate(lines) if not has_uuid(line, delimiter)
    ]

    if not lines_needing_uuid:
        print(f"  ✓ Arquivo já tem UUIDs em todos os registros")
        return True

    print(f"  📊 {len(lines_needing_uuid)} de {len(lines)} registros precisam de UUID")

    if dry_run:
        print(f"  ⚠ DRY RUN - nenhuma alteração será feita")
        return True

    # Criar backup
    backup_path = backup_file(file_path)

    # Adicionar UUIDs
    new_lines = []
    for i, line in enumerate(lines):
        if i in lines_needing_uuid:
            new_lines.append(add_uuid_to_line(line, delimiter))
        else:
            new_lines.append(line)

    # Escrever arquivo
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"  ✓ Arquivo atualizado com sucesso!")
        return True
    except Exception as e:
        print(f"  ✗ Erro ao escrever arquivo: {e}")
        print(f"  ℹ Restaurando backup...")
        shutil.copy2(backup_path, file_path)
        return False


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Adiciona UUIDs a registros existentes"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simula a migração sem fazer alterações"
    )
    parser.add_argument(
        "--path",
        default="data/txt",
        help="Diretório com arquivos TXT (padrão: data/txt)",
    )
    parser.add_argument("--file", help="Migrar apenas um arquivo específico")

    args = parser.parse_args()

    print("=" * 70)
    print("MIGRAÇÃO: Adicionar UUIDs a Registros Existentes")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠  MODO DRY RUN - Nenhuma alteração será feita\n")

    # Determinar arquivos a processar
    if args.file:
        files = [args.file]
    else:
        data_dir = os.path.join(os.path.dirname(__file__), "..", args.path)
        files = [
            os.path.join(data_dir, f)
            for f in os.listdir(data_dir)
            if f.endswith(".txt") and not f.startswith("_")
        ]

    if not files:
        print("Nenhum arquivo encontrado para migrar.")
        return

    print(f"\n📁 Arquivos a processar: {len(files)}\n")

    # Processar cada arquivo
    success_count = 0
    for file_path in files:
        if migrate_file(file_path, dry_run=args.dry_run):
            success_count += 1

    # Resumo
    print("\n" + "=" * 70)
    print(f"✓ Migração concluída: {success_count}/{len(files)} arquivos processados")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠  Executar novamente sem --dry-run para aplicar as alterações")


if __name__ == "__main__":
    main()
