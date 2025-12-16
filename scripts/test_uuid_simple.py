#!/usr/bin/env python3
"""
Teste simplificado de preservação de UUID.

Testa se os adapters preservam UUIDs existentes quando fornecidos.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistence.adapters.sqlite_adapter import SQLiteRepository
from persistence.adapters.txt_adapter import TxtRepository
from VibeCForms import load_spec


def test_sqlite_preserves_uuid():
    """Testa se SQLiteRepository preserva UUID fornecido."""
    print("\n" + "=" * 70)
    print("TESTE 1: SQLiteRepository preserva UUID fornecido")
    print("=" * 70)

    # Configuração
    sqlite_config = {
        "database": "data/sqlite/test_uuid.db",
        "timeout": 10
    }
    sqlite_repo = SQLiteRepository(sqlite_config)

    # Spec simples para teste
    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text"},
            {"name": "email", "label": "Email", "type": "email"}
        ]
    }

    form_path = "test_uuid"

    # Criar storage
    if sqlite_repo.exists(form_path):
        # Limpar dados existentes
        existing = sqlite_repo.read_all(form_path, spec)
        for i in range(len(existing)):
            sqlite_repo.delete(form_path, spec, 0)
    else:
        sqlite_repo.create_storage(form_path, spec)

    # Dados com UUID pré-definido
    predefined_uuid = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # 27 chars (invalid but for testing)
    test_data = {
        "_record_id": predefined_uuid,
        "nome": "João Silva",
        "email": "joao@example.com"
    }

    print(f"\n1️⃣  UUID fornecido: {predefined_uuid}")

    # Criar registro
    returned_uuid = sqlite_repo.create(form_path, spec, test_data)
    print(f"2️⃣  UUID retornado: {returned_uuid}")

    # Ler registro
    records = sqlite_repo.read_all(form_path, spec)
    if records:
        stored_uuid = records[0].get('_record_id')
        print(f"3️⃣  UUID armazenado: {stored_uuid}")

        if stored_uuid == predefined_uuid:
            print(f"\n✅ SUCESSO: UUID foi preservado!")
            # Limpeza
            sqlite_repo.delete(form_path, spec, 0)
            return True
        else:
            print(f"\n❌ FALHA: UUID não foi preservado")
            print(f"   Esperado: {predefined_uuid}")
            print(f"   Obtido:   {stored_uuid}")
            return False
    else:
        print(f"\n❌ FALHA: Nenhum registro encontrado")
        return False


def test_txt_preserves_uuid():
    """Testa se TxtRepository preserva UUID fornecido."""
    print("\n" + "=" * 70)
    print("TESTE 2: TxtRepository preserva UUID fornecido")
    print("=" * 70)

    # Configuração
    txt_config = {
        "path": "data/txt",
        "delimiter": ";",
        "encoding": "utf-8"
    }
    txt_repo = TxtRepository(txt_config)

    # Spec simples para teste
    spec = {
        "title": "Test Form",
        "fields": [
            {"name": "nome", "label": "Nome", "type": "text"},
            {"name": "telefone", "label": "Telefone", "type": "tel"}
        ]
    }

    form_path = "test_uuid_txt"

    # Criar storage
    if txt_repo.exists(form_path):
        # Limpar dados existentes
        existing = txt_repo.read_all(form_path, spec)
        for i in range(len(existing)):
            txt_repo.delete(form_path, spec, 0)
    else:
        txt_repo.create_storage(form_path, spec)

    # Dados com UUID pré-definido
    predefined_uuid = "ABCDEFGHJKMNPQRSTVWXYZ0123456789"  # 27 chars different
    test_data = {
        "_record_id": predefined_uuid,
        "nome": "Maria Santos",
        "telefone": "11-99999-8888"
    }

    print(f"\n1️⃣  UUID fornecido: {predefined_uuid}")

    # Criar registro
    returned_uuid = txt_repo.create(form_path, spec, test_data)
    print(f"2️⃣  UUID retornado: {returned_uuid}")

    # Ler registro
    records = txt_repo.read_all(form_path, spec)
    if records:
        stored_uuid = records[0].get('_record_id')
        print(f"3️⃣  UUID armazenado: {stored_uuid}")

        if stored_uuid == predefined_uuid:
            print(f"\n✅ SUCESSO: UUID foi preservado!")
            # Limpeza
            txt_repo.delete(form_path, spec, 0)
            return True
        else:
            print(f"\n❌ FALHA: UUID não foi preservado")
            print(f"   Esperado: {predefined_uuid}")
            print(f"   Obtido:   {stored_uuid}")
            return False
    else:
        print(f"\n❌ FALHA: Nenhum registro encontrado")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 70)
    print("TESTES SIMPLIFICADOS DE PRESERVAÇÃO DE UUID")
    print("=" * 70)

    results = []

    # Teste 1: SQLite
    try:
        result1 = test_sqlite_preserves_uuid()
        results.append(("SQLiteRepository", result1))
    except Exception as e:
        print(f"\n❌ ERRO no teste SQLite: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SQLiteRepository", False))

    # Teste 2: TXT
    try:
        result2 = test_txt_preserves_uuid()
        results.append(("TxtRepository", result2))
    except Exception as e:
        print(f"\n❌ ERRO no teste TXT: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TxtRepository", False))

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
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\n⚠ ALGUNS TESTES FALHARAM!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
