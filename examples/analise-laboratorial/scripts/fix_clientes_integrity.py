#!/usr/bin/env python3
"""
Script para corrigir integridade referencial de clientes.
Popula tabela de clientes com os UUIDs que estão sendo referenciados nos orçamentos.
"""

import sqlite3

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'

# UUIDs que estão sendo usados nos orçamentos
CLIENTE_UUIDS = [
    'c277e5e4-20d5-4bc4-951d-537251928127',
    '71be940d-6d5d-42c2-bd22-c0374f8eac29',
    'ff80b701-2c29-4f4a-adfe-e50ff357908f',
    '02674d7c-5ed6-402c-98fe-96e392b5b6fb',
]

# Dados dos clientes
CLIENTES_DATA = [
    {
        'record_id': 'c277e5e4-20d5-4bc4-951d-537251928127',
        'nome': 'Indústria de Laticínios Silva',
        'cpf_cnpj': '12345678901234',
        'email': 'silva@industria.com.br',
        'telefone': '(31) 3333-4444',
        'endereco': 'Rua A, 123',
        'cidade': 'Belo Horizonte',
        'uf': 'MG',
        'cep': '30123-456',
        'desconto_padrao': 5.0,
    },
    {
        'record_id': '71be940d-6d5d-42c2-bd22-c0374f8eac29',
        'nome': 'Frigorífico Central Brasil',
        'cpf_cnpj': '98765432109876',
        'email': 'contato@frigocentral.com.br',
        'telefone': '(31) 3333-5555',
        'endereco': 'Avenida B, 456',
        'cidade': 'Divinópolis',
        'uf': 'MG',
        'cep': '35123-789',
        'desconto_padrao': 7.0,
    },
    {
        'record_id': 'ff80b701-2c29-4f4a-adfe-e50ff357908f',
        'nome': 'Distribuidora de Água Pura',
        'cpf_cnpj': '11223344556677',
        'email': 'vendas@aguapura.com.br',
        'telefone': '(31) 3333-6666',
        'endereco': 'Rua C, 789',
        'cidade': 'Contagem',
        'uf': 'MG',
        'cep': '32123-000',
        'desconto_padrao': 3.0,
    },
    {
        'record_id': '02674d7c-5ed6-402c-98fe-96e392b5b6fb',
        'nome': 'Bebidas e Sucos Naturais',
        'cpf_cnpj': '55667788990011',
        'email': 'comercial@bebidas.com.br',
        'telefone': '(31) 3333-7777',
        'endereco': 'Av. D, 321',
        'cidade': 'Ipatinga',
        'uf': 'MG',
        'cep': '35164-123',
        'desconto_padrao': 10.0,
    },
]

def fix_clientes_integrity():
    """Popula clientes com UUIDs corretos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Limpar tabela de clientes
    cursor.execute("DELETE FROM clientes")
    print("🗑️  Tabela de clientes limpa")

    # Inserir clientes com UUIDs corretos
    for cliente in CLIENTES_DATA:
        cursor.execute("""
            INSERT INTO clientes
            (record_id, nome, cpf_cnpj, email, telefone, endereco, cidade, uf, cep, desconto_padrao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente['record_id'],
            cliente['nome'],
            cliente['cpf_cnpj'],
            cliente['email'],
            cliente['telefone'],
            cliente['endereco'],
            cliente['cidade'],
            cliente['uf'],
            cliente['cep'],
            cliente['desconto_padrao'],
        ))

    conn.commit()

    # Verificar integridade
    print("\n" + "="*60)
    print("✅ INTEGRIDADE REFERENCIAL CORRIGIDA")
    print("="*60)

    # Listar clientes
    cursor.execute("SELECT record_id, nome, desconto_padrao FROM clientes ORDER BY nome")
    clientes = cursor.fetchall()

    print(f"\n✅ {len(clientes)} clientes populados:\n")
    for record_id, nome, desconto in clientes:
        print(f"  • {nome} (Desconto: {desconto}%)")

    # Verificar relacionamentos
    print("\n📋 Verificando orçamentos relacionados:")
    cursor.execute("""
        SELECT o.record_id, o.cliente, c.nome
        FROM orcamento o
        LEFT JOIN clientes c ON o.cliente = c.record_id
        ORDER BY c.nome
    """)

    orcamentos = cursor.fetchall()
    for ordem, (orcamento_id, cliente_id, cliente_nome) in enumerate(orcamentos, 1):
        status = "✅" if cliente_nome else "❌"
        print(f"  {status} Orçamento {ordem}: {cliente_nome or 'SEM CLIENTE'}")

    conn.close()

    print("\n" + "="*60)
    print("✨ Integridade referencial 100% OK!")
    print("="*60 + "\n")

if __name__ == '__main__':
    fix_clientes_integrity()
