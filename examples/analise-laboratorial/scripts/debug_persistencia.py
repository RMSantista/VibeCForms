#!/usr/bin/env python3
"""
Debug script para rastrear falhas na persistência
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from persistence.repository_factory import RepositoryFactory

# Set up paths
spec_dir = 'examples/analise-laboratorial/specs'
config_path = 'examples/analise-laboratorial/config/persistence.json'

print("=" * 80)
print("🔍 DEBUG: Rastreando leitura de dados da persistência")
print("=" * 80)

# Load config
print(f"\n📋 Carregando configuração: {config_path}")
with open(config_path) as f:
    persistence_config = json.load(f)
print(f"   ✓ Backend padrão: {persistence_config['default_backend']}")

# Load spec
print(f"\n📋 Carregando spec: {spec_dir}/clientes.json")
with open(f"{spec_dir}/clientes.json") as f:
    spec = json.load(f)
print(f"   ✓ Campos no spec: {[f['name'] for f in spec['fields']]}")

# Create repository
print(f"\n📋 Criando repositório")
factory = RepositoryFactory(persistence_config, spec_dir)
repo = factory.get_repository('clientes')
print(f"   ✓ Tipo: {type(repo).__name__}")
print(f"   ✓ Database: {repo.database if hasattr(repo, 'database') else 'N/A'}")

# Check if table exists
print(f"\n📋 Verificando se tabela existe")
exists = repo.exists('clientes')
print(f"   {'✓' if exists else '✗'} Tabela 'clientes' existe: {exists}")

# Try to read data
print(f"\n📋 Tentando ler dados")
try:
    data = repo.read_all('clientes', spec)
    print(f"   ✓ Sucesso! Registros lidos: {len(data)}")

    if data:
        print(f"\n📊 Dados encontrados:")
        for i, record in enumerate(data[:2], 1):
            print(f"   Registro {i}:")
            for key, value in record.items():
                print(f"      {key}: {value}")
    else:
        print(f"   ⚠️  Nenhum dado retornado")

except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
