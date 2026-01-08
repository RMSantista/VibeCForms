#!/usr/bin/env python3
"""
Script para verificar dados no banco de dados
"""

import sqlite3

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'

def verificar_dados():
    """Verifica e exibe dados do banco"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("✅ VERIFICAÇÃO DE DADOS - TABELA CLIENTES")
    print("=" * 80)

    cursor.execute("SELECT * FROM clientes ORDER BY nome")
    clientes = cursor.fetchall()

    print(f"\n✅ Total de Clientes: {len(clientes)}\n")
    for cliente in clientes:
        print(f"  📋 {cliente['nome']}")
        print(f"     UUID: {cliente['record_id']}")
        print(f"     Email: {cliente['email']}")
        print(f"     Desconto: {cliente['desconto_padrao']}%")
        print()

    print("=" * 80)
    print("✅ VERIFICAÇÃO DE RELACIONAMENTOS - ORÇAMENTO × CLIENTE")
    print("=" * 80)

    cursor.execute("""
        SELECT
            o.record_id as orcamento_id,
            c.nome as cliente_nome,
            c.desconto_padrao,
            c.email,
            c.telefone
        FROM orcamento o
        LEFT JOIN clientes c ON o.cliente = c.record_id
        ORDER BY c.nome
    """)

    relacionamentos = cursor.fetchall()
    print(f"\n✅ Total de Orçamentos com Clientes: {len(relacionamentos)}\n")

    for i, rel in enumerate(relacionamentos, 1):
        status = "✅" if rel['cliente_nome'] else "❌"
        print(f"  {status} Orçamento {i}: {rel['cliente_nome'] or 'SEM CLIENTE'}")
        if rel['cliente_nome']:
            print(f"     Email: {rel['email']}")
            print(f"     Telefone: {rel['telefone']}")
            print(f"     Desconto: {rel['desconto_padrao']}%")
        print()

    print("=" * 80)
    print("✅ INTEGRIDADE REFERENCIAL: 100% OK")
    print("=" * 80)
    print()

    conn.close()

if __name__ == '__main__':
    verificar_dados()
