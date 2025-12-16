#!/usr/bin/env python3
"""
Testa se os UUIDs são preservados durante migração entre backends.

Este teste verifica:
1. TXT → SQLite: UUIDs devem ser preservados
2. SQLite → TXT: UUIDs devem ser preservados
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistence.factory import RepositoryFactory
from persistence.config import get_config
from VibeCForms import load_spec


def test_txt_to_sqlite_uuid_preservation():
    """Testa preservação de UUID: TXT → SQLite."""
    print("\n" + "=" * 70)
    print("TESTE 1: Migração TXT → SQLite (Preservação de UUID)")
    print("=" * 70)

    form_path = "usuarios"
    spec = load_spec(form_path)
    config = get_config()

    # 1. Ler dados originais do TXT
    print("\n1️⃣  Lendo dados originais do TXT...")
    config.form_mappings[form_path] = "txt"
    RepositoryFactory.clear_cache()  # Force new repository instance
    txt_repo = RepositoryFactory.get_repository(form_path)
    original_data = txt_repo.read_all(form_path, spec)

    if not original_data:
        print("❌ FALHA: Nenhum dado encontrado no TXT")
        return False

    # Capturar UUIDs originais
    original_uuids = [rec.get('_record_id') for rec in original_data]
    print(f"✓ {len(original_data)} registros lidos do TXT")
    print(f"✓ UUIDs originais capturados: {len([u for u in original_uuids if u])}/{len(original_uuids)}")

    # 2. Migrar para SQLite
    print("\n2️⃣  Migrando para SQLite...")
    config.form_mappings[form_path] = "sqlite"
    RepositoryFactory.clear_cache()  # Force new repository instance
    sqlite_repo = RepositoryFactory.get_repository(form_path)

    # Criar storage se não existir
    if not sqlite_repo.exists(form_path):
        sqlite_repo.create_storage(form_path, spec)

    # Limpar dados existentes
    existing = sqlite_repo.read_all(form_path, spec)
    for i in range(len(existing)):
        sqlite_repo.delete(form_path, spec, 0)

    # Migrar cada registro
    migrated_uuids = []
    for record in original_data:
        new_uuid = sqlite_repo.create(form_path, spec, record)
        migrated_uuids.append(new_uuid)

    print(f"✓ {len(migrated_uuids)} registros migrados")

    # 3. Ler dados do SQLite
    print("\n3️⃣  Verificando dados no SQLite...")
    sqlite_data = sqlite_repo.read_all(form_path, spec)
    sqlite_uuids = [rec.get('_record_id') for rec in sqlite_data]

    print(f"✓ {len(sqlite_data)} registros no SQLite")
    print(f"✓ UUIDs no SQLite: {len([u for u in sqlite_uuids if u])}/{len(sqlite_uuids)}")

    # 4. Comparar UUIDs
    print("\n4️⃣  Comparando UUIDs...")
    all_preserved = True
    for i, (orig_uuid, sqlite_uuid) in enumerate(zip(original_uuids, sqlite_uuids)):
        if orig_uuid != sqlite_uuid:
            print(f"❌ Registro {i}: UUID alterado!")
            print(f"   Original:  {orig_uuid}")
            print(f"   SQLite:    {sqlite_uuid}")
            all_preserved = False

    if all_preserved and len(original_uuids) == len(sqlite_uuids):
        print(f"✅ SUCESSO: Todos os {len(original_uuids)} UUIDs foram preservados!")
        return True
    else:
        print(f"❌ FALHA: UUIDs não foram preservados corretamente")
        return False


def test_sqlite_to_txt_uuid_preservation():
    """Testa preservação de UUID: SQLite → TXT."""
    print("\n" + "=" * 70)
    print("TESTE 2: Migração SQLite → TXT (Preservação de UUID)")
    print("=" * 70)

    form_path = "produtos"  # Este já está em SQLite
    spec = load_spec(form_path)
    config = get_config()

    # 1. Ler dados originais do SQLite
    print("\n1️⃣  Lendo dados originais do SQLite...")
    config.form_mappings[form_path] = "sqlite"
    RepositoryFactory.clear_cache()  # Force new repository instance
    sqlite_repo = RepositoryFactory.get_repository(form_path)
    original_data = sqlite_repo.read_all(form_path, spec)

    if not original_data:
        print("❌ FALHA: Nenhum dado encontrado no SQLite")
        return False

    # Capturar UUIDs originais
    original_uuids = [rec.get('_record_id') for rec in original_data]
    print(f"✓ {len(original_data)} registros lidos do SQLite")
    print(f"✓ UUIDs originais capturados: {len([u for u in original_uuids if u])}/{len(original_uuids)}")

    # 2. Migrar para TXT
    print("\n2️⃣  Migrando para TXT...")
    config.form_mappings[form_path] = "txt"
    RepositoryFactory.clear_cache()  # Force new repository instance
    txt_repo = RepositoryFactory.get_repository(form_path)

    # Criar storage se não existir
    if not txt_repo.exists(form_path):
        txt_repo.create_storage(form_path, spec)

    # Limpar dados existentes
    existing = txt_repo.read_all(form_path, spec)
    for i in range(len(existing)):
        txt_repo.delete(form_path, spec, 0)

    # Migrar cada registro
    migrated_uuids = []
    for record in original_data:
        new_uuid = txt_repo.create(form_path, spec, record)
        migrated_uuids.append(new_uuid)

    print(f"✓ {len(migrated_uuids)} registros migrados")

    # 3. Ler dados do TXT
    print("\n3️⃣  Verificando dados no TXT...")
    txt_data = txt_repo.read_all(form_path, spec)
    txt_uuids = [rec.get('_record_id') for rec in txt_data]

    print(f"✓ {len(txt_data)} registros no TXT")
    print(f"✓ UUIDs no TXT: {len([u for u in txt_uuids if u])}/{len(txt_uuids)}")

    # 4. Comparar UUIDs
    print("\n4️⃣  Comparando UUIDs...")
    all_preserved = True
    for i, (orig_uuid, txt_uuid) in enumerate(zip(original_uuids, txt_uuids)):
        if orig_uuid != txt_uuid:
            print(f"❌ Registro {i}: UUID alterado!")
            print(f"   Original:  {orig_uuid}")
            print(f"   TXT:       {txt_uuid}")
            all_preserved = False

    if all_preserved and len(original_uuids) == len(txt_uuids):
        print(f"✅ SUCESSO: Todos os {len(original_uuids)} UUIDs foram preservados!")

        # Restaurar configuração original (produtos deve voltar para SQLite)
        config.form_mappings[form_path] = "sqlite"
        config.save()

        return True
    else:
        print(f"❌ FALHA: UUIDs não foram preservados corretamente")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 70)
    print("TESTE DE PRESERVAÇÃO DE UUID DURANTE MIGRAÇÃO")
    print("=" * 70)

    results = []

    # Teste 1: TXT → SQLite
    try:
        result1 = test_txt_to_sqlite_uuid_preservation()
        results.append(("TXT → SQLite", result1))
    except Exception as e:
        print(f"\n❌ ERRO no teste TXT → SQLite: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TXT → SQLite", False))

    # Teste 2: SQLite → TXT
    try:
        result2 = test_sqlite_to_txt_uuid_preservation()
        results.append(("SQLite → TXT", result2))
    except Exception as e:
        print(f"\n❌ ERRO no teste SQLite → TXT: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SQLite → TXT", False))

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")

    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    print("=" * 70)

    if passed == total:
        print("\n🎉 TODOS OS TESTES DE PRESERVAÇÃO DE UUID PASSARAM!")
        return 0
    else:
        print("\n⚠ ALGUNS TESTES FALHARAM!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
