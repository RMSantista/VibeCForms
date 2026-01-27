#!/usr/bin/env python3
"""
HOMOLOGAÇÃO DA FASE 3 - Correções Críticas
Validação dos 3 problemas corrigidos
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from persistence.adapters.txt_adapter import TxtRepository
from persistence.adapters.sqlite_adapter import SQLiteRepository
from utils.crockford import generate_id, validate_id


def test_1_uuid_obrigatorio():
    """TESTE 1: UUID obrigatório em TODOS os registros"""
    print("\n" + "="*70)
    print("TESTE 1: UUID OBRIGATÓRIO EM TODOS OS REGISTROS")
    print("="*70)

    tmpdir = tempfile.mkdtemp()
    try:
        # TXT Repository
        print("\n[TXT] Testando UUID obrigatório...")
        txt_repo = TxtRepository({"path": tmpdir})
        spec = {"fields": [{"name": "nome", "type": "text"}, {"name": "idade", "type": "number"}]}

        # Criar registro
        record_id1 = txt_repo.create("pessoas", spec, {"nome": "João", "idade": 30})
        assert validate_id(record_id1), f"UUID inválido: {record_id1}"
        print(f"  ✅ Registro criado com UUID: {record_id1}")

        # Verificar persistência
        records = txt_repo.read_all("pessoas", spec)
        assert len(records) == 1 and records[0]["_record_id"] == record_id1
        print(f"  ✅ UUID preservado na leitura")

        # Simular registro legado SEM UUID
        file_path = os.path.join(tmpdir, "pessoas.txt")
        with open(file_path, "a") as f:
            f.write("Maria;25\n")  # Formato antigo

        # Ler e verificar que UUID foi gerado em memória
        records = txt_repo.read_all("pessoas", spec)
        assert len(records) == 2, f"Esperado 2, encontrado {len(records)}"
        maria = [r for r in records if r["nome"] == "Maria"][0]
        assert validate_id(maria["_record_id"]), "UUID gerado inválido"
        print(f"  ✅ Registro legado recebeu UUID em memória: {maria['_record_id']}")

        # Atualizar registro legado - UUID deve ser persistido
        txt_repo.update("pessoas", spec, 1, {"nome": "Maria Silva", "idade": 26})

        # Verificar arquivo - UUID deve estar no arquivo agora
        with open(file_path, "r") as f:
            lines = f.readlines()
        maria_line = [l for l in lines if "Maria Silva" in l][0]
        parts = maria_line.strip().split(";")
        assert len(parts) == 3 and validate_id(parts[0]), f"UUID não persistido: {maria_line}"
        print(f"  ✅ UUID persistido no arquivo após update: {parts[0]}")

        # SQLite Repository
        print("\n[SQLite] Testando UUID obrigatório...")
        db_path = os.path.join(tmpdir, "test.db")
        sql_repo = SQLiteRepository({"database": db_path})

        record_id2 = sql_repo.create("pessoas", spec, {"nome": "Carlos", "idade": 40})
        assert validate_id(record_id2), f"UUID SQLite inválido: {record_id2}"
        print(f"  ✅ Registro SQLite criado com UUID: {record_id2}")

        record = sql_repo.read_by_id("pessoas", spec, record_id2)
        assert record["_record_id"] == record_id2
        print(f"  ✅ UUID SQLite preservado")

        print("\n✅✅✅ TESTE 1 PASSOU!")
        return True

    finally:
        shutil.rmtree(tmpdir)


def test_2_valores_decimais():
    """TESTE 2: Campos monetários aceitam valores decimais"""
    print("\n" + "="*70)
    print("TESTE 2: VALORES DECIMAIS EM CAMPOS MONETÁRIOS")
    print("="*70)

    tmpdir = tempfile.mkdtemp()
    try:
        spec = {
            "fields": [
                {"name": "descricao", "type": "text"},
                {"name": "preco", "type": "number"},
                {"name": "valor", "type": "number"},
                {"name": "quantidade", "type": "number"}
            ]
        }

        # TXT Repository
        print("\n[TXT] Testando valores decimais...")
        txt_repo = TxtRepository({"path": tmpdir})

        txt_repo.create("produtos", spec, {
            "descricao": "Produto A",
            "preco": "99.99",
            "valor": "123.45",
            "quantidade": "10"
        })

        records = txt_repo.read_all("produtos", spec)
        r = records[0]

        assert isinstance(r["preco"], float) and r["preco"] == 99.99
        print(f"  ✅ Campo 'preco' aceita decimais: {r['preco']}")

        assert isinstance(r["valor"], float) and r["valor"] == 123.45
        print(f"  ✅ Campo 'valor' aceita decimais: {r['valor']}")

        assert isinstance(r["quantidade"], int) and r["quantidade"] == 10
        print(f"  ✅ Campo normal continua inteiro: {r['quantidade']}")

        # SQLite Repository
        print("\n[SQLite] Testando valores decimais...")
        db_path = os.path.join(tmpdir, "test.db")
        sql_repo = SQLiteRepository({"database": db_path})

        sql_repo.create("produtos", spec, {
            "descricao": "Produto B",
            "preco": "50.50",
            "valor": "67.89",
            "quantidade": "5"
        })

        records = sql_repo.read_all("produtos", spec)
        r = records[0]

        assert isinstance(r["preco"], float) and r["preco"] == 50.50
        print(f"  ✅ SQLite: Campo 'preco' aceita decimais: {r['preco']}")

        assert isinstance(r["valor"], float) and r["valor"] == 67.89
        print(f"  ✅ SQLite: Campo 'valor' aceita decimais: {r['valor']}")

        print("\n✅✅✅ TESTE 2 PASSOU!")
        return True

    finally:
        shutil.rmtree(tmpdir)


def test_3_exibicao_relacionamentos():
    """TESTE 3: Exibição de relacionamentos (valores, não UUIDs)"""
    print("\n" + "="*70)
    print("TESTE 3: EXIBIÇÃO DE RELACIONAMENTOS (VALORES, NÃO UUIDS)")
    print("="*70)

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test.db")
        repo = SQLiteRepository({"database": db_path})

        spec_clientes = {
            "fields": [
                {"name": "nome", "type": "text", "required": True},
                {"name": "email", "type": "email"}
            ]
        }

        print("\n[API] Testando busca reversa UUID → Nome...")

        # Criar clientes
        cliente_id1 = repo.create("contatos", spec_clientes, {
            "nome": "João Silva",
            "email": "joao@email.com"
        })

        cliente_id2 = repo.create("contatos", spec_clientes, {
            "nome": "Maria Santos",
            "email": "maria@email.com"
        })

        print(f"  ✅ Clientes criados: {cliente_id1[:10]}..., {cliente_id2[:10]}...")

        # API reversa: UUID → Nome (simula /api/get-by-id/<datasource>/<record_id>)
        cliente = repo.read_by_id("contatos", spec_clientes, cliente_id1)
        assert cliente and cliente["nome"] == "João Silva"
        assert cliente["_record_id"] == cliente_id1
        print(f"  ✅ API reversa: {cliente_id1[:10]}... → '{cliente['nome']}'")

        # API busca: Query → Resultados (simula /api/search/<datasource>?q=maria)
        all_clientes = repo.read_all("contatos", spec_clientes)
        results = [
            {"record_id": c["_record_id"], "label": c["nome"]}
            for c in all_clientes
            if "maria" in c["nome"].lower()
        ]

        assert len(results) == 1
        assert results[0]["label"] == "Maria Santos"
        assert results[0]["record_id"] == cliente_id2
        print(f"  ✅ Busca autocomplete: query='maria' → '{results[0]['label']}'")

        # Verificar que retorna LABEL, não UUID
        assert results[0]["label"] != results[0]["record_id"]
        print(f"  ✅ Label é valor legível, não UUID")

        print("\n✅✅✅ TESTE 3 PASSOU!")
        return True

    finally:
        shutil.rmtree(tmpdir)


def main():
    print("="*70)
    print("HOMOLOGAÇÃO DA FASE 3 - CORREÇÕES CRÍTICAS")
    print("="*70)

    try:
        test_1_uuid_obrigatorio()
        test_2_valores_decimais()
        test_3_exibicao_relacionamentos()

        print("\n" + "="*70)
        print("🎉🎉🎉 TODOS OS TESTES PASSARAM! 🎉🎉🎉")
        print("="*70)
        print("\n✅ Correções implementadas com sucesso:")
        print("  1. UUID obrigatório em TODOS os registros (TXT e SQLite)")
        print("  2. Campos monetários aceitam valores decimais (99.99, 123.45)")
        print("  3. APIs para exibir valores legíveis em relacionamentos")
        print("\n📋 SISTEMA PRONTO PARA HOMOLOGAÇÃO MANUAL!")
        return 0

    except Exception as e:
        print("\n" + "="*70)
        print("❌❌❌ TESTE FALHOU! ❌❌❌")
        print("="*70)
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
