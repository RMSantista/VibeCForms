#!/usr/bin/env python3
"""
Script para migrar dados de src/ para data/

Este script:
1. Cria backup completo dos dados atuais
2. Move todos os arquivos .txt de src/ para data/txt/
3. Move vibecforms.db de src/ para data/sqlite/
4. Move backups existentes de src/backups/ para data/backups/
5. Gera log detalhado da operação

Uso:
    python scripts/migrate_data_folder.py [--dry-run]

Opções:
    --dry-run: Simula a migração sem mover arquivos
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path


class DataFolderMigrator:
    """Gerenciador de migração de dados src/ → data/"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.data_dir = self.project_root / "data"

        # Estatísticas
        self.stats = {
            "txt_files_moved": 0,
            "db_files_moved": 0,
            "backup_files_moved": 0,
            "errors": [],
            "started_at": datetime.now().isoformat(),
        }

        # Log de operações
        self.operations_log = []

    def log(self, message, operation_type="INFO"):
        """Log de operação"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": operation_type,
            "message": message,
        }
        self.operations_log.append(log_entry)
        print(f"[{operation_type}] {message}")

    def create_backup(self):
        """Cria backup completo antes da migração"""
        backup_dir = self.data_dir / "backups" / "migrations" / "pre_reorganization"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        self.log(f"Criando backup em: {backup_path}")

        if self.dry_run:
            self.log("DRY-RUN: Backup não criado", "DRYRUN")
            return backup_path

        # Copiar todos os .txt
        txt_files = list(self.src_dir.glob("*.txt"))
        for txt_file in txt_files:
            shutil.copy2(txt_file, backup_path / txt_file.name)

        # Copiar vibecforms.db se existir
        db_file = self.src_dir / "vibecforms.db"
        if db_file.exists():
            shutil.copy2(db_file, backup_path / db_file.name)

        # Copiar backups existentes se existirem
        src_backups = self.src_dir / "backups"
        if src_backups.exists():
            shutil.copytree(src_backups, backup_path / "backups", dirs_exist_ok=True)

        self.log(f"✅ Backup criado com sucesso: {len(txt_files)} arquivos TXT")
        return backup_path

    def move_txt_files(self):
        """Move todos os arquivos .txt de src/ para data/txt/"""
        self.log("Iniciando migração de arquivos TXT...")

        dest_dir = self.data_dir / "txt"
        dest_dir.mkdir(parents=True, exist_ok=True)

        txt_files = list(self.src_dir.glob("*.txt"))
        self.log(f"Encontrados {len(txt_files)} arquivos TXT para migrar")

        for txt_file in txt_files:
            dest_file = dest_dir / txt_file.name
            self.log(f"  Movendo: {txt_file.name}")

            if self.dry_run:
                self.log(f"    DRY-RUN: {txt_file} → {dest_file}", "DRYRUN")
            else:
                try:
                    shutil.move(str(txt_file), str(dest_file))
                    self.stats["txt_files_moved"] += 1
                except Exception as e:
                    error_msg = f"Erro ao mover {txt_file.name}: {e}"
                    self.log(error_msg, "ERROR")
                    self.stats["errors"].append(error_msg)

        self.log(f"✅ Arquivos TXT migrados: {self.stats['txt_files_moved']}")

    def move_database_files(self):
        """Move vibecforms.db de src/ para data/sqlite/"""
        self.log("Iniciando migração de arquivos de banco de dados...")

        dest_dir = self.data_dir / "sqlite"
        dest_dir.mkdir(parents=True, exist_ok=True)

        db_file = self.src_dir / "vibecforms.db"
        if not db_file.exists():
            self.log("  Nenhum arquivo .db encontrado em src/", "WARNING")
            return

        dest_file = dest_dir / db_file.name
        self.log(f"  Movendo: {db_file.name}")

        if self.dry_run:
            self.log(f"    DRY-RUN: {db_file} → {dest_file}", "DRYRUN")
        else:
            try:
                shutil.move(str(db_file), str(dest_file))
                self.stats["db_files_moved"] += 1
                self.log(f"✅ Banco de dados migrado: {db_file.name}")
            except Exception as e:
                error_msg = f"Erro ao mover {db_file.name}: {e}"
                self.log(error_msg, "ERROR")
                self.stats["errors"].append(error_msg)

    def move_backup_files(self):
        """Move src/backups/ para data/backups/"""
        self.log("Iniciando migração de backups existentes...")

        src_backups = self.src_dir / "backups"
        if not src_backups.exists():
            self.log("  Nenhum diretório de backups encontrado", "WARNING")
            return

        dest_backups = self.data_dir / "backups" / "migrations"
        dest_backups.mkdir(parents=True, exist_ok=True)

        # Mover conteúdo de src/backups/migrations/ para data/backups/migrations/
        src_migrations = src_backups / "migrations"
        if src_migrations.exists():
            self.log(f"  Movendo backups de migrações...")

            if self.dry_run:
                self.log(f"    DRY-RUN: {src_migrations} → {dest_backups}", "DRYRUN")
            else:
                try:
                    # Copiar arquivos (não mover para preservar estrutura)
                    for item in src_migrations.iterdir():
                        dest_item = dest_backups / item.name
                        if item.is_file():
                            shutil.copy2(item, dest_item)
                            self.stats["backup_files_moved"] += 1
                        elif item.is_dir():
                            shutil.copytree(item, dest_item, dirs_exist_ok=True)
                            self.stats["backup_files_moved"] += 1

                    self.log(f"✅ Backups migrados: {self.stats['backup_files_moved']}")

                    # Remover src/backups/ após copiar
                    shutil.rmtree(src_backups)
                    self.log("✅ Diretório src/backups/ removido")

                except Exception as e:
                    error_msg = f"Erro ao mover backups: {e}"
                    self.log(error_msg, "ERROR")
                    self.stats["errors"].append(error_msg)

    def verify_migration(self):
        """Verifica integridade da migração"""
        self.log("Verificando integridade da migração...")

        # Verificar se src/ está vazio de dados
        remaining_txt = list(self.src_dir.glob("*.txt"))
        remaining_db = list(self.src_dir.glob("*.db"))

        if remaining_txt or remaining_db:
            warning_msg = (
                f"ATENÇÃO: Ainda existem arquivos de dados em src/: "
                f"{len(remaining_txt)} TXT, {len(remaining_db)} DB"
            )
            self.log(warning_msg, "WARNING")
            self.stats["errors"].append(warning_msg)
        else:
            self.log("✅ Nenhum arquivo de dados permanece em src/")

        # Verificar se data/ tem os arquivos
        data_txt = list((self.data_dir / "txt").glob("*.txt"))
        data_db = list((self.data_dir / "sqlite").glob("*.db"))

        self.log(f"✅ Arquivos em data/txt/: {len(data_txt)}")
        self.log(f"✅ Arquivos em data/sqlite/: {len(data_db)}")

        # Verificar contagem
        expected_txt = self.stats["txt_files_moved"]
        expected_db = self.stats["db_files_moved"]

        if len(data_txt) == expected_txt and len(data_db) == expected_db:
            self.log("✅ Contagem de arquivos conferida!")
        else:
            error_msg = (
                f"ERRO: Contagem não confere. "
                f"TXT: esperado {expected_txt}, encontrado {len(data_txt)}. "
                f"DB: esperado {expected_db}, encontrado {len(data_db)}"
            )
            self.log(error_msg, "ERROR")
            self.stats["errors"].append(error_msg)

    def save_migration_log(self):
        """Salva log detalhado da migração"""
        log_dir = self.data_dir / "backups" / "migrations"
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"reorganization_log_{timestamp}.json"

        self.stats["completed_at"] = datetime.now().isoformat()
        migration_log = {"stats": self.stats, "operations": self.operations_log}

        if self.dry_run:
            self.log(f"DRY-RUN: Log não salvo em {log_file}", "DRYRUN")
            return

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(migration_log, f, indent=2, ensure_ascii=False)

        self.log(f"✅ Log de migração salvo: {log_file}")

    def run(self):
        """Executa migração completa"""
        mode = "DRY-RUN MODE" if self.dry_run else "MIGRATION MODE"
        self.log(f"{'=' * 60}")
        self.log(f"MIGRAÇÃO DE DADOS: src/ → data/")
        self.log(f"Modo: {mode}")
        self.log(f"{'=' * 60}")

        try:
            # 1. Criar backup
            backup_path = self.create_backup()

            # 2. Mover arquivos TXT
            self.move_txt_files()

            # 3. Mover banco de dados
            self.move_database_files()

            # 4. Mover backups existentes
            self.move_backup_files()

            # 5. Verificar migração
            self.verify_migration()

            # 6. Salvar log
            self.save_migration_log()

            # Resumo final
            self.log(f"{'=' * 60}")
            self.log("RESUMO DA MIGRAÇÃO")
            self.log(f"{'=' * 60}")
            self.log(f"Arquivos TXT movidos: {self.stats['txt_files_moved']}")
            self.log(f"Arquivos DB movidos: {self.stats['db_files_moved']}")
            self.log(f"Backups migrados: {self.stats['backup_files_moved']}")
            self.log(f"Erros: {len(self.stats['errors'])}")

            if self.stats["errors"]:
                self.log("⚠️ ERROS ENCONTRADOS:", "WARNING")
                for error in self.stats["errors"]:
                    self.log(f"  - {error}", "ERROR")
            else:
                self.log("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")

            return len(self.stats["errors"]) == 0

        except Exception as e:
            self.log(f"ERRO FATAL durante migração: {e}", "ERROR")
            raise


def main():
    """Função principal"""
    import sys

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("\n⚠️ MODO DRY-RUN ATIVADO - Nenhum arquivo será movido\n")

    migrator = DataFolderMigrator(dry_run=dry_run)
    success = migrator.run()

    if not success:
        print("\n❌ Migração falhou. Verifique os erros acima.")
        sys.exit(1)
    else:
        if not dry_run:
            print("\n✅ Migração concluída com sucesso!")
            print("\nPróximos passos:")
            print("1. Atualizar src/config/persistence.json com novos caminhos")
            print("2. Atualizar adapters (txt_adapter.py, sqlite_adapter.py)")
            print("3. Executar testes: uv run pytest")
        sys.exit(0)


if __name__ == "__main__":
    main()
