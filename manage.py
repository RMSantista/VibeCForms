#!/usr/bin/env python3
"""
VibeCForms Management CLI

CLI de gerenciamento para operações administrativas do VibeCForms:
- Migração de dados entre backends
- Gerenciamento de schemas
- Backup e restore
- Validação de integridade

Uso:
    python manage.py migrate <form> --from txt --to sqlite
    python manage.py list
    python manage.py status <form>
    python manage.py backup <form>
    python manage.py validate <form>
"""

import sys
import os
import argparse
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.factory import RepositoryFactory
from persistence.migration_manager import MigrationManager
from persistence.config import get_config
from persistence.schema_history import get_history
from VibeCForms import load_spec, SPECS_DIR


def list_forms(args):
    """Lista todos os formulários e seus backends configurados."""
    print("=" * 70)
    print("FORMULÁRIOS CADASTRADOS")
    print("=" * 70)

    config = get_config()
    history = get_history()

    # Encontrar todos os specs
    forms = []
    for root, dirs, files in os.walk(SPECS_DIR):
        for file in files:
            if file.endswith('.json') and not file.startswith('_'):
                rel_path = os.path.relpath(os.path.join(root, file), SPECS_DIR)
                form_path = rel_path[:-5]  # Remove .json
                forms.append(form_path)

    if not forms:
        print("\nNenhum formulário encontrado.")
        return

    print(f"\n📊 Total: {len(forms)} formulários\n")

    for form_path in sorted(forms):
        try:
            spec = load_spec(form_path)
            backend_config = config.get_backend_config(form_path)
            backend_type = backend_config.get('type', 'unknown')

            form_history = history.get_form_history(form_path)
            record_count = form_history.get('record_count', 0) if form_history else 0

            print(f"📄 {form_path}")
            print(f"   Título: {spec.get('title', 'N/A')}")
            print(f"   Backend: {backend_type}")
            print(f"   Registros: {record_count}")
            print()

        except Exception as e:
            print(f"📄 {form_path}")
            print(f"   ⚠ Erro ao carregar: {e}")
            print()


def form_status(args):
    """Exibe status detalhado de um formulário."""
    form_path = args.form
    print("=" * 70)
    print(f"STATUS: {form_path}")
    print("=" * 70)

    try:
        # Carregar spec
        spec = load_spec(form_path)
        print(f"\n📄 Título: {spec.get('title')}")
        print(f"📋 Campos: {len(spec.get('fields', []))}")

        # Backend atual
        config = get_config()
        backend_config = config.get_backend_config(form_path)
        backend_type = backend_config.get('type')
        print(f"\n🔧 Backend Atual: {backend_type}")

        # Histórico
        history = get_history()
        form_history = history.get_form_history(form_path)

        if form_history:
            print(f"\n📊 Estatísticas:")
            print(f"   Registros: {form_history.get('record_count', 0)}")
            print(f"   Última atualização: {form_history.get('last_updated', 'N/A')}")
            print(f"   Hash do schema: {form_history.get('last_spec_hash', 'N/A')[:16]}...")

        # Verificar dados
        repo = RepositoryFactory.get_repository(form_path)
        if repo.exists(form_path):
            records = repo.read_all(form_path, spec)
            print(f"\n✅ Storage existe")
            print(f"   Registros atuais: {len(records)}")

            # Verificar UUIDs
            records_with_uuid = sum(1 for r in records if r.get('_record_id'))
            print(f"   Com UUID: {records_with_uuid}/{len(records)}")
        else:
            print(f"\n⚠ Storage não existe")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def migrate_form(args):
    """Migra dados de um backend para outro."""
    form_path = args.form
    source_backend = args.source
    target_backend = args.target

    print("=" * 70)
    print(f"MIGRAÇÃO: {form_path}")
    print("=" * 70)
    print(f"\nBackend Origem: {source_backend}")
    print(f"Backend Destino: {target_backend}")

    if source_backend == target_backend:
        print("\n❌ Erro: Backend origem e destino são iguais!")
        return 1

    try:
        # Carregar spec
        spec = load_spec(form_path)
        print(f"\n📄 Formulário: {spec.get('title')}")

        # Obter repositórios
        config = get_config()

        # Criar repositório de origem
        source_config = config.backends.get(source_backend)
        if not source_config:
            print(f"\n❌ Backend '{source_backend}' não encontrado!")
            return 1

        # Configuração temporária para origem
        original_mapping = config.form_mappings.get(form_path)
        config.form_mappings[form_path] = source_backend
        RepositoryFactory.clear_cache()  # Force new repository instance
        source_repo = RepositoryFactory.get_repository(form_path)

        # Verificar se origem tem dados
        if not source_repo.exists(form_path):
            print(f"\n⚠ Origem não tem dados para migrar!")
            # Restaurar configuração
            if original_mapping:
                config.form_mappings[form_path] = original_mapping
            else:
                del config.form_mappings[form_path]
            return 0

        # Ler dados da origem
        source_data = source_repo.read_all(form_path, spec)
        print(f"\n📊 Registros na origem: {len(source_data)}")

        if not source_data:
            print("\n⚠ Nenhum registro para migrar!")
            # Restaurar configuração
            if original_mapping:
                config.form_mappings[form_path] = original_mapping
            else:
                del config.form_mappings[form_path]
            return 0

        # Confirmar migração
        if not args.yes:
            response = input(f"\nConfirma migração de {len(source_data)} registros? (s/N): ")
            if response.lower() != 's':
                print("\nMigração cancelada.")
                # Restaurar configuração
                if original_mapping:
                    config.form_mappings[form_path] = original_mapping
                else:
                    del config.form_mappings[form_path]
                return 0

        # Configurar destino
        config.form_mappings[form_path] = target_backend
        RepositoryFactory.clear_cache()  # Force new repository instance
        target_repo = RepositoryFactory.get_repository(form_path)

        # Criar storage de destino
        if not target_repo.exists(form_path):
            print(f"\n🔧 Criando storage de destino...")
            target_repo.create_storage(form_path, spec)

        # Verificar se destino já tem dados
        existing_data = target_repo.read_all(form_path, spec) if target_repo.exists(form_path) else []
        if existing_data and not args.force:
            print(f"\n⚠ Destino já tem {len(existing_data)} registros!")
            print("Use --force para sobrescrever")
            # Restaurar configuração
            if original_mapping:
                config.form_mappings[form_path] = original_mapping
            else:
                del config.form_mappings[form_path]
            return 1

        # Limpar destino se --force
        if args.force and existing_data:
            print(f"\n🧹 Limpando {len(existing_data)} registros existentes...")
            for i in range(len(existing_data)):
                target_repo.delete(form_path, spec, 0)

        # Migrar dados
        print(f"\n📦 Migrando {len(source_data)} registros...")
        migrated = 0
        for i, record in enumerate(source_data, 1):
            # IMPORTANT: Preserve _record_id to maintain referential integrity
            # The target repository will use existing UUID if present
            record_id = target_repo.create(form_path, spec, record)
            if record_id:
                migrated += 1
                if i % 10 == 0:
                    print(f"   Migrados: {i}/{len(source_data)}")
            else:
                print(f"   ⚠ Falha ao migrar registro {i}")

        print(f"\n✅ Migração concluída: {migrated}/{len(source_data)} registros")

        # Atualizar configuração permanente se solicitado
        if args.update_config:
            print(f"\n🔧 Atualizando persistence.json...")
            config.form_mappings[form_path] = target_backend
            config.save()
            print(f"✅ Configuração atualizada")
        else:
            # Restaurar configuração original
            if original_mapping:
                config.form_mappings[form_path] = original_mapping
            else:
                if form_path in config.form_mappings:
                    del config.form_mappings[form_path]
            print(f"\n💡 Use --update-config para atualizar persistence.json")

        return 0

    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()
        return 1


def backup_form(args):
    """Cria backup de um formulário."""
    form_path = args.form
    print("=" * 70)
    print(f"BACKUP: {form_path}")
    print("=" * 70)

    try:
        spec = load_spec(form_path)
        repo = RepositoryFactory.get_repository(form_path)

        if not repo.exists(form_path):
            print("\n⚠ Formulário não tem dados para backup!")
            return 1

        # Ler dados
        data = repo.read_all(form_path, spec)
        print(f"\n📊 Registros: {len(data)}")

        # Criar diretório de backup
        backup_dir = os.path.join('data', 'backups', 'manual')
        os.makedirs(backup_dir, exist_ok=True)

        # Nome do arquivo de backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = form_path.replace('/', '_')
        backup_file = os.path.join(backup_dir, f"{safe_name}_{timestamp}.json")

        # Salvar backup
        backup_data = {
            'form_path': form_path,
            'spec': spec,
            'records': data,
            'timestamp': timestamp,
            'record_count': len(data)
        }

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Backup criado: {backup_file}")
        print(f"📦 {len(data)} registros salvos")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_form(args):
    """Valida integridade dos dados de um formulário."""
    form_path = args.form
    print("=" * 70)
    print(f"VALIDAÇÃO: {form_path}")
    print("=" * 70)

    try:
        spec = load_spec(form_path)
        repo = RepositoryFactory.get_repository(form_path)

        if not repo.exists(form_path):
            print("\n⚠ Formulário não tem dados!")
            return 0

        # Ler dados
        data = repo.read_all(form_path, spec)
        print(f"\n📊 Total de registros: {len(data)}")

        # Validações
        issues = []

        # 1. Verificar UUIDs
        records_without_uuid = [i for i, r in enumerate(data) if not r.get('_record_id')]
        if records_without_uuid:
            issues.append(f"⚠ {len(records_without_uuid)} registros sem UUID")

        # 2. Verificar UUIDs duplicados
        uuids = [r.get('_record_id') for r in data if r.get('_record_id')]
        if len(uuids) != len(set(uuids)):
            issues.append(f"⚠ UUIDs duplicados encontrados!")

        # 3. Verificar campos obrigatórios
        required_fields = [f['name'] for f in spec['fields'] if f.get('required')]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    issues.append(f"⚠ Registro {i}: campo '{field}' obrigatório está vazio")

        # Resultado
        if not issues:
            print("\n✅ Validação bem-sucedida!")
            print("   Todos os registros estão íntegros")
            return 0
        else:
            print(f"\n⚠ {len(issues)} problemas encontrados:")
            for issue in issues[:10]:  # Mostrar no máximo 10
                print(f"   {issue}")
            if len(issues) > 10:
                print(f"   ... e mais {len(issues) - 10} problemas")
            return 1

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """CLI principal."""
    parser = argparse.ArgumentParser(
        description='VibeCForms Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando: list
    parser_list = subparsers.add_parser('list', help='Lista todos os formulários')
    parser_list.set_defaults(func=list_forms)

    # Comando: status
    parser_status = subparsers.add_parser('status', help='Exibe status de um formulário')
    parser_status.add_argument('form', help='Caminho do formulário (ex: contatos)')
    parser_status.set_defaults(func=form_status)

    # Comando: migrate
    parser_migrate = subparsers.add_parser('migrate', help='Migra dados entre backends')
    parser_migrate.add_argument('form', help='Caminho do formulário')
    parser_migrate.add_argument('--from', dest='source', required=True,
                               help='Backend de origem (txt, sqlite, etc)')
    parser_migrate.add_argument('--to', dest='target', required=True,
                               help='Backend de destino (txt, sqlite, etc)')
    parser_migrate.add_argument('--force', action='store_true',
                               help='Sobrescrever dados existentes no destino')
    parser_migrate.add_argument('--update-config', action='store_true',
                               help='Atualizar persistence.json com novo backend')
    parser_migrate.add_argument('--yes', '-y', action='store_true',
                               help='Confirmar automaticamente')
    parser_migrate.set_defaults(func=migrate_form)

    # Comando: backup
    parser_backup = subparsers.add_parser('backup', help='Cria backup de um formulário')
    parser_backup.add_argument('form', help='Caminho do formulário')
    parser_backup.set_defaults(func=backup_form)

    # Comando: validate
    parser_validate = subparsers.add_parser('validate', help='Valida integridade dos dados')
    parser_validate.add_argument('form', help='Caminho do formulário')
    parser_validate.set_defaults(func=validate_form)

    # Parse e executar
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
