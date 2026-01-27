#!/usr/bin/env python3
"""Script de teste simples para validar as correções"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.adapters.txt_adapter import TxtRepository
from persistence.adapters.sqlite_adapter import SQLiteRepository
from utils.crockford import generate_id, validate_id


def test_uuid_txt():
    """Teste: UUID em registros TXT"""
    print("\n=== TEST UUID TXT ===")

    tmpdir = tempfile.mkdtemp()
    try:
        adapter = TxtRepository({"data_dir": tmpdir})

        spec = {
            "fields": [
                {"name": "nome", "type": "text"},
                {"name": "idade", "type": "number"}
            ]
        }

        # Criar registro
        data = {"nome": "João", "idade": 30}
        record_id = adapter.create("pessoas", spec, data)

        print(f"✅ Registro criado com UUID: {record_id}")
        assert record_id and validate_id(record_id), "UUID inválido"

        # Ler registros
        records = adapter.read_all("pessoas", spec)
        assert len(records) == 1, f"Esperado 1 registro, encontrado {len(records)}"
        assert records[0]["_record_id"] == record_id, "UUID não preservado"

        print(f"✅ UUID preservado na leitura")

        # Simular registro legado (adicionar linha sem UUID)
        file_path = os.path.join(tmpdir, "pessoas.txt")

        # Verificar conteúdo atual
        with open(file_path, "r") as f:
            print(f"DEBUG: Arquivo antes: {f.read()}")

        with open(file_path, "a") as f:
            f.write("Maria;25\n")

        # Verificar conteúdo depois
        with open(file_path, "r") as f:
            content = f.read()
            print(f"DEBUG: Arquivo depois: {content}")
            print(f"DEBUG: Linhas: {content.splitlines()}")

        # Ler novamente
        records = adapter.read_all("pessoas", spec)
        print(f"DEBUG: Records lidos: {len(records)}")
        for i, r in enumerate(records):
            print(f"DEBUG: Record {i}: {r}")

        assert len(records) == 2, f"Esperado 2 registros, encontrado {len(records)}"

        # Encontrar registro legado
        maria = [r for r in records if r["nome"] == "Maria"][0]
        assert "_record_id" in maria, "Registro legado sem _record_id em memória"
        assert validate_id(maria["_record_id"]), f"UUID gerado inválido: {maria['_record_id']}"

        print(f"✅ Registro legado recebeu UUID em memória: {maria['_record_id']}")

        # Atualizar registro legado
        adapter.update("pessoas", spec, 1, {"nome": "Maria Silva", "idade": 26})

        # Verificar arquivo
        with open(file_path, "r") as f:
            lines = f.readlines()

        maria_line = [l for l in lines if "Maria Silva" in l][0]
        parts = maria_line.strip().split(";")
        assert len(parts) == 3, f"Registro sem UUID no arquivo: {maria_line}"
        assert validate_id(parts[0]), f"UUID no arquivo inválido: {parts[0]}"

        print(f"✅ UUID persistido no arquivo: {parts[0]}")
        print("✅✅✅ TESTE UUID TXT PASSOU!")

    finally:
        shutil.rmtree(tmpdir)


def test_valores_decimais():
    """Teste: Valores decimais em campos monetários"""
    print("\n=== TEST VALORES DECIMAIS ===")

    tmpdir = tempfile.mkdtemp()
    try:
        adapter = TxtRepository({"data_dir": tmpdir})

        spec = {
            "fields": [
                {"name": "produto", "type": "text"},
                {"name": "preco", "type": "number"},
                {"name": "valor", "type": "number"},
                {"name": "quantidade", "type": "number"}
            ]
        }

        data = {
            "produto": "Teste",
            "preco": "99.99",
            "valor": "123.45",
            "quantidade": "10"
        }

        adapter.create("produtos", spec, data)
        records = adapter.read_all("produtos", spec)

        r = records[0]

        # Verificar decimais
        assert isinstance(r["preco"], float), f"preco não é float: {type(r['preco'])}"
        assert r["preco"] == 99.99, f"preco incorreto: {r['preco']}"
        print(f"✅ Campo 'preco' aceita decimais: {r['preco']}")

        assert isinstance(r["valor"], float), f"valor não é float: {type(r['valor'])}"
        assert r["valor"] == 123.45, f"valor incorreto: {r['valor']}"
        print(f"✅ Campo 'valor' aceita decimais: {r['valor']}")

        # Verificar inteiro
        assert isinstance(r["quantidade"], int), f"quantidade não é int: {type(r['quantidade'])}"
        assert r["quantidade"] == 10, f"quantidade incorreto: {r['quantidade']}"
        print(f"✅ Campo normal continua inteiro: {r['quantidade']}")

        print("✅✅✅ TESTE VALORES DECIMAIS PASSOU!")

    finally:
        shutil.rmtree(tmpdir)


def test_api_reversa():
    """Teste: API reversa UUID -> Nome"""
    print("\n=== TEST API REVERSA ===")

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test.db")
        adapter = SQLiteRepository({"database": db_path})

        spec = {
            "fields": [
                {"name": "nome", "type": "text", "required": True},
                {"name": "email", "type": "email"}
            ]
        }

        # Criar cliente
        cliente_id = adapter.create("contatos", spec, {
            "nome": "João Silva",
            "email": "joao@email.com"
        })

        print(f"✅ Cliente criado: {cliente_id[:10]}...")

        # Buscar por UUID
        cliente = adapter.read_by_id("contatos", spec, cliente_id)
        assert cliente, "read_by_id retornou None"
        assert cliente["nome"] == "João Silva", f"Nome incorreto: {cliente['nome']}"
        assert cliente["_record_id"] == cliente_id, "UUID não corresponde"

        print(f"✅ API reversa funciona: {cliente_id[:10]}... → '{cliente['nome']}'")
        print("✅✅✅ TESTE API REVERSA PASSOU!")

    finally:
        shutil.rmtree(tmpdir)


def main():
    print("=" * 70)
    print("TESTES DE HOMOLOGAÇÃO - FASE 3")
    print("=" * 70)

    try:
        test_uuid_txt()
        test_valores_decimais()
        test_api_reversa()

        print("\n" + "=" * 70)
        print("✅✅✅ TODOS OS TESTES PASSARAM! ✅✅✅")
        print("=" * 70)
        return 0

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌❌❌ TESTE FALHOU! ❌❌❌")
        print("=" * 70)
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
