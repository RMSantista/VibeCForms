#!/usr/bin/env python3
"""Testa inserção de registro em tabela SQLite."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistence.factory import RepositoryFactory
from VibeCForms import load_spec

def test_insert():
    """Testa inserção em rh/departamentos/areas."""
    form_path = "rh/departamentos/areas"
    spec = load_spec(form_path)
    repo = RepositoryFactory.get_repository(form_path)

    # Contar registros antes
    records_before = repo.read_all(form_path, spec)
    count_before = len(records_before)
    print(f"Registros antes: {count_before}")

    # Inserir novo registro
    new_data = {
        "nome_area": "TESTE INSERÇÃO",
        "responsavel": "Claude Code",
        "num_funcionarios": 5,
        "descricao": "Teste de inserção após migração UUID"
    }

    print(f"\nInserindo novo registro...")
    record_id = repo.create(form_path, spec, new_data)

    if record_id:
        print(f"✅ Registro criado com UUID: {record_id}")
    else:
        print(f"❌ Falha ao criar registro!")
        return False

    # Contar registros depois
    records_after = repo.read_all(form_path, spec)
    count_after = len(records_after)
    print(f"Registros depois: {count_after}")

    if count_after == count_before + 1:
        print(f"\n✅ SUCESSO: Registro inserido corretamente!")

        # Remover o registro de teste
        last_idx = count_after - 1
        repo.delete(form_path, spec, last_idx)
        print(f"✅ Registro de teste removido")
        return True
    else:
        print(f"\n❌ FALHA: Esperado {count_before + 1}, encontrado {count_after}")
        return False

if __name__ == '__main__':
    success = test_insert()
    sys.exit(0 if success else 1)
