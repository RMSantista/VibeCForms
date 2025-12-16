#!/usr/bin/env python3
"""
Script para limpar todos os dados do VibeCForms mantendo estruturas.

Este script:
- Limpa todos os arquivos TXT (deixa vazios)
- Remove todos os registros das tabelas SQLite (mantém as tabelas)
- Limpa dados dos examples
- Cria backup antes de limpar
- Gera relatório detalhado

Uso: python scripts/clean_all_data.py [--backup] [--no-confirm]
"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import json


class DataCleaner:
    """Gerenciador de limpeza de dados do VibeCForms"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.examples_dir = self.base_dir / "examples"
        self.backup_dir = self.data_dir / "backups" / f"clean_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.stats = {
            "txt_files_cleaned": 0,
            "txt_records_removed": 0,
            "sqlite_tables_cleaned": 0,
            "sqlite_records_removed": 0,
            "example_files_cleaned": 0,
            "errors": []
        }

    def create_backup(self):
        """Cria backup completo antes da limpeza"""
        print(f"\n🔄 Criando backup em: {self.backup_dir}")

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup TXT files
            txt_backup = self.backup_dir / "txt"
            txt_backup.mkdir(exist_ok=True)

            txt_dir = self.data_dir / "txt"
            if txt_dir.exists():
                for txt_file in txt_dir.glob("*.txt"):
                    if txt_file.is_file():
                        shutil.copy2(txt_file, txt_backup / txt_file.name)

            # Backup SQLite databases
            sqlite_backup = self.backup_dir / "sqlite"
            sqlite_backup.mkdir(exist_ok=True)

            sqlite_dir = self.data_dir / "sqlite"
            if sqlite_dir.exists():
                for db_file in sqlite_dir.glob("*.db"):
                    if db_file.is_file():
                        shutil.copy2(db_file, sqlite_backup / db_file.name)

            # Backup examples
            if self.examples_dir.exists():
                examples_backup = self.backup_dir / "examples"
                shutil.copytree(self.examples_dir, examples_backup, dirs_exist_ok=True)

            print(f"✅ Backup criado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            self.stats["errors"].append(f"Backup error: {e}")
            return False

    def clean_txt_files(self):
        """Limpa todos os arquivos TXT mantendo os arquivos vazios"""
        print(f"\n🧹 Limpando arquivos TXT...")

        txt_dir = self.data_dir / "txt"
        if not txt_dir.exists():
            print("⚠️  Diretório data/txt não encontrado")
            return

        for txt_file in txt_dir.glob("*.txt"):
            if txt_file.is_file() and txt_file.name != "test_uuid_txt.txt":
                try:
                    # Contar registros antes de limpar
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        records = len([line for line in f if line.strip()])

                    # Limpar arquivo (deixar vazio)
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        pass  # Arquivo vazio

                    self.stats["txt_files_cleaned"] += 1
                    self.stats["txt_records_removed"] += records
                    print(f"  ✓ {txt_file.name}: {records} registros removidos")

                except Exception as e:
                    error_msg = f"Erro ao limpar {txt_file.name}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats["errors"].append(error_msg)

    def clean_sqlite_tables(self):
        """Remove todos os registros das tabelas SQLite mantendo as estruturas"""
        print(f"\n🧹 Limpando bancos SQLite...")

        sqlite_dir = self.data_dir / "sqlite"
        if not sqlite_dir.exists():
            print("⚠️  Diretório data/sqlite não encontrado")
            return

        for db_file in sqlite_dir.glob("*.db"):
            if db_file.is_file():
                try:
                    print(f"\n  📦 {db_file.name}:")
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()

                    # Obter todas as tabelas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tables = cursor.fetchall()

                    total_records = 0
                    for (table_name,) in tables:
                        # Contar registros antes de deletar
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]

                        if count > 0:
                            # Deletar todos os registros
                            cursor.execute(f"DELETE FROM {table_name}")

                            # Reset auto-increment (se houver)
                            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")

                            self.stats["sqlite_tables_cleaned"] += 1
                            total_records += count
                            print(f"    ✓ {table_name}: {count} registros removidos")
                        else:
                            print(f"    ○ {table_name}: já vazia")

                    conn.commit()
                    conn.close()

                    self.stats["sqlite_records_removed"] += total_records
                    print(f"  ✅ Total: {total_records} registros removidos")

                except Exception as e:
                    error_msg = f"Erro ao limpar {db_file.name}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats["errors"].append(error_msg)

    def clean_examples_data(self):
        """Limpa dados dos diretórios de examples"""
        print(f"\n🧹 Limpando dados dos examples...")

        if not self.examples_dir.exists():
            print("⚠️  Diretório examples não encontrado")
            return

        for example_dir in self.examples_dir.iterdir():
            if example_dir.is_dir():
                print(f"\n  📁 {example_dir.name}:")

                # Limpar TXT files do example
                example_data_txt = example_dir / "data" / "txt"
                if example_data_txt.exists():
                    for txt_file in example_data_txt.glob("*.txt"):
                        if txt_file.is_file():
                            try:
                                with open(txt_file, 'r', encoding='utf-8') as f:
                                    records = len([line for line in f if line.strip()])

                                with open(txt_file, 'w', encoding='utf-8') as f:
                                    pass

                                self.stats["example_files_cleaned"] += 1
                                print(f"    ✓ {txt_file.name}: {records} registros removidos")
                            except Exception as e:
                                print(f"    ❌ Erro em {txt_file.name}: {e}")

                # Limpar SQLite do example
                example_data_sqlite = example_dir / "data" / "sqlite"
                if example_data_sqlite.exists():
                    for db_file in example_data_sqlite.glob("*.db"):
                        if db_file.is_file():
                            try:
                                conn = sqlite3.connect(db_file)
                                cursor = conn.cursor()

                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                                tables = cursor.fetchall()

                                for (table_name,) in tables:
                                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                    count = cursor.fetchone()[0]

                                    if count > 0:
                                        cursor.execute(f"DELETE FROM {table_name}")
                                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                                        print(f"    ✓ {db_file.name}/{table_name}: {count} registros removidos")

                                conn.commit()
                                conn.close()
                                self.stats["example_files_cleaned"] += 1

                            except Exception as e:
                                print(f"    ❌ Erro em {db_file.name}: {e}")

                # Limpar vibecforms.db na raiz do example
                example_db = example_dir / "vibecforms.db"
                if example_db.exists():
                    try:
                        conn = sqlite3.connect(example_db)
                        cursor = conn.cursor()

                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                        tables = cursor.fetchall()

                        total = 0
                        for (table_name,) in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]

                            if count > 0:
                                cursor.execute(f"DELETE FROM {table_name}")
                                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                                total += count

                        conn.commit()
                        conn.close()

                        if total > 0:
                            print(f"    ✓ vibecforms.db: {total} registros removidos")

                    except Exception as e:
                        print(f"    ❌ Erro em vibecforms.db: {e}")

    def generate_report(self):
        """Gera relatório final da limpeza"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE LIMPEZA DE DADOS")
        print("="*60)

        print(f"\n✅ Arquivos TXT limpos: {self.stats['txt_files_cleaned']}")
        print(f"   Registros removidos: {self.stats['txt_records_removed']}")

        print(f"\n✅ Tabelas SQLite limpas: {self.stats['sqlite_tables_cleaned']}")
        print(f"   Registros removidos: {self.stats['sqlite_records_removed']}")

        print(f"\n✅ Arquivos de examples limpos: {self.stats['example_files_cleaned']}")

        total_removed = self.stats['txt_records_removed'] + self.stats['sqlite_records_removed']
        print(f"\n🎯 TOTAL DE REGISTROS REMOVIDOS: {total_removed}")

        if self.stats['errors']:
            print(f"\n⚠️  Erros encontrados ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"   - {error}")
        else:
            print(f"\n✨ Nenhum erro encontrado!")

        print(f"\n💾 Backup salvo em: {self.backup_dir}")
        print("="*60)

        # Salvar relatório em JSON
        report_file = self.backup_dir / "cleaning_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats,
                "backup_location": str(self.backup_dir)
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Relatório salvo em: {report_file}")

    def run(self, create_backup=True, confirm=True):
        """Executa a limpeza completa"""
        print("="*60)
        print("🧹 LIMPEZA DE DADOS - VibeCForms")
        print("="*60)
        print("\nEste script irá:")
        print("  • Limpar todos os arquivos TXT (deixar vazios)")
        print("  • Remover todos os registros das tabelas SQLite")
        print("  • Limpar dados dos examples")
        print("  • Manter todas as estruturas (arquivos e tabelas)")

        if create_backup:
            print("  • Criar backup antes de limpar")

        if confirm:
            response = input("\n⚠️  Deseja continuar? (s/N): ")
            if response.lower() != 's':
                print("\n❌ Operação cancelada pelo usuário")
                return False

        # Criar backup
        if create_backup:
            if not self.create_backup():
                print("\n❌ Falha ao criar backup. Operação cancelada.")
                return False

        # Executar limpeza
        self.clean_txt_files()
        self.clean_sqlite_tables()
        self.clean_examples_data()

        # Gerar relatório
        self.generate_report()

        return True


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Limpa todos os dados do VibeCForms')
    parser.add_argument('--no-backup', action='store_true', help='Não criar backup antes de limpar')
    parser.add_argument('--no-confirm', action='store_true', help='Não pedir confirmação')

    args = parser.parse_args()

    # Detectar diretório base do projeto
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # Criar e executar cleaner
    cleaner = DataCleaner(base_dir)
    success = cleaner.run(
        create_backup=not args.no_backup,
        confirm=not args.no_confirm
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
