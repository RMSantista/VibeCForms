#!/usr/bin/env python3
"""
Script para validar as correções críticas via interface web.

Testa:
1. Registros pré-existentes têm UUIDs
2. Inserir novo registro não deleta registros existentes
3. Editar registro preserva outros registros
4. Deletar registro remove apenas o registro específico
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistence.factory import RepositoryFactory


def test_existing_records_have_uuids():
    """Teste 1: Verificar se registros pré-existentes têm UUIDs."""
    print("\n" + "=" * 70)
    print("TESTE 1: Registros pré-existentes têm UUIDs")
    print("=" * 70)

    from VibeCForms import load_spec

    form_path = "contatos"
    spec = load_spec(form_path)
    repo = RepositoryFactory.get_repository(form_path)

    records = repo.read_all(form_path, spec)

    print(f"\n📊 Total de registros em '{form_path}': {len(records)}")

    # Verificar se todos têm _record_id
    records_with_uuid = [r for r in records if r.get('_record_id')]
    records_without_uuid = [r for r in records if not r.get('_record_id')]

    print(f"✓ Registros com UUID: {len(records_with_uuid)}")
    print(f"✗ Registros sem UUID: {len(records_without_uuid)}")

    if records_without_uuid:
        print("\n⚠ FALHA: Alguns registros não têm UUID!")
        for i, rec in enumerate(records_without_uuid[:3]):
            print(f"  - Registro {i}: {rec}")
        return False
    else:
        print("\n✓ SUCESSO: Todos os registros têm UUID!")
        # Mostrar alguns exemplos
        for i, rec in enumerate(records[:3]):
            print(f"  - {rec.get('_record_id')[:10]}... | {rec.get('nome', 'N/A')}")
        return True


def test_insert_preserves_existing_records():
    """Teste 2: Inserir novo registro não deleta registros existentes."""
    print("\n" + "=" * 70)
    print("TESTE 2: Inserir novo registro preserva registros existentes")
    print("=" * 70)

    from VibeCForms import load_spec

    form_path = "contatos"
    spec = load_spec(form_path)
    repo = RepositoryFactory.get_repository(form_path)

    # Contar registros antes
    records_before = repo.read_all(form_path, spec)
    count_before = len(records_before)
    print(f"\n📊 Registros antes: {count_before}")

    # Inserir novo registro
    new_data = {
        "nome": "TESTE VALIDAÇÃO",
        "telefone": "99999-9999",
        "whatsapp": True
    }

    record_id = repo.create(form_path, spec, new_data)
    print(f"✓ Novo registro criado: {record_id}")

    # Contar registros depois
    records_after = repo.read_all(form_path, spec)
    count_after = len(records_after)
    print(f"📊 Registros depois: {count_after}")

    # Verificar
    if count_after != count_before + 1:
        print(f"\n✗ FALHA: Esperado {count_before + 1} registros, encontrado {count_after}")
        return False
    else:
        print(f"\n✓ SUCESSO: Registro inserido sem deletar existentes!")
        # Remover o registro de teste
        last_idx = len(records_after) - 1
        repo.delete(form_path, spec, last_idx)
        print(f"✓ Registro de teste removido")
        return True


def test_update_preserves_other_records():
    """Teste 3: Editar registro preserva outros registros."""
    print("\n" + "=" * 70)
    print("TESTE 3: Editar registro preserva outros registros")
    print("=" * 70)

    from VibeCForms import load_spec

    form_path = "contatos"
    spec = load_spec(form_path)
    repo = RepositoryFactory.get_repository(form_path)

    # Inserir registro de teste
    test_data = {
        "nome": "TESTE UPDATE",
        "telefone": "11111-1111",
        "whatsapp": False
    }
    record_id = repo.create(form_path, spec, test_data)
    print(f"✓ Registro de teste criado: {record_id}")

    # Contar registros
    records_before = repo.read_all(form_path, spec)
    count_before = len(records_before)
    last_idx = count_before - 1
    print(f"📊 Registros antes: {count_before}")

    # Editar o último registro
    updated_data = {
        "nome": "TESTE UPDATE MODIFICADO",
        "telefone": "22222-2222",
        "whatsapp": True
    }
    success = repo.update(form_path, spec, last_idx, updated_data)
    print(f"✓ Registro atualizado: {success}")

    # Contar registros depois
    records_after = repo.read_all(form_path, spec)
    count_after = len(records_after)
    print(f"📊 Registros depois: {count_after}")

    # Verificar
    if count_after != count_before:
        print(f"\n✗ FALHA: Esperado {count_before} registros, encontrado {count_after}")
        return False
    else:
        # Verificar se o registro foi atualizado
        updated_record = records_after[last_idx]
        if updated_record['nome'] == "TESTE UPDATE MODIFICADO":
            print(f"\n✓ SUCESSO: Registro editado sem afetar outros!")
            # Remover o registro de teste
            repo.delete(form_path, spec, last_idx)
            print(f"✓ Registro de teste removido")
            return True
        else:
            print(f"\n✗ FALHA: Registro não foi atualizado corretamente")
            return False


def test_delete_removes_only_target():
    """Teste 4: Deletar registro remove apenas o registro específico."""
    print("\n" + "=" * 70)
    print("TESTE 4: Deletar registro remove apenas o registro específico")
    print("=" * 70)

    from VibeCForms import load_spec

    form_path = "contatos"
    spec = load_spec(form_path)
    repo = RepositoryFactory.get_repository(form_path)

    # Inserir registro de teste
    test_data = {
        "nome": "TESTE DELETE",
        "telefone": "33333-3333",
        "whatsapp": False
    }
    record_id = repo.create(form_path, spec, test_data)
    print(f"✓ Registro de teste criado: {record_id}")

    # Contar registros
    records_before = repo.read_all(form_path, spec)
    count_before = len(records_before)
    last_idx = count_before - 1
    print(f"📊 Registros antes: {count_before}")

    # Deletar o último registro
    success = repo.delete(form_path, spec, last_idx)
    print(f"✓ Registro deletado: {success}")

    # Contar registros depois
    records_after = repo.read_all(form_path, spec)
    count_after = len(records_after)
    print(f"📊 Registros depois: {count_after}")

    # Verificar
    if count_after != count_before - 1:
        print(f"\n✗ FALHA: Esperado {count_before - 1} registros, encontrado {count_after}")
        return False
    else:
        print(f"\n✓ SUCESSO: Apenas o registro específico foi removido!")
        return True


def main():
    """Executa todos os testes de validação."""
    print("=" * 70)
    print("VALIDAÇÃO DAS CORREÇÕES CRÍTICAS")
    print("=" * 70)

    tests = [
        ("UUIDs em registros pré-existentes", test_existing_records_have_uuids),
        ("Inserir sem deletar", test_insert_preserves_existing_records),
        ("Editar sem deletar", test_update_preserves_other_records),
        ("Deletar apenas alvo", test_delete_removes_only_target),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ ERRO: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status}: {name}")

    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    print("=" * 70)

    if passed == total:
        print("\n🎉 TODAS AS CORREÇÕES VALIDADAS COM SUCESSO!")
        return 0
    else:
        print("\n⚠ ALGUMAS VALIDAÇÕES FALHARAM!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
