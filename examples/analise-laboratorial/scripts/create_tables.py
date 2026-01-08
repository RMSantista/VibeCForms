#!/usr/bin/env python3
"""Script para criar as tabelas do banco de dados."""

import sqlite3
from pathlib import Path

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'

# Schema SQL baseado nos specs JSON
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS acreditadores (
    record_id TEXT PRIMARY KEY,
    sigla TEXT NOT NULL,
    nome TEXT NOT NULL,
    tipo_certificado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS funcionarios (
    record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    funcao TEXT NOT NULL,
    crq TEXT,
    ativo INTEGER
);

CREATE TABLE IF NOT EXISTS clientes (
    record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf_cnpj TEXT NOT NULL,
    email TEXT NOT NULL,
    telefone TEXT NOT NULL,
    endereco TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    desconto_padrao REAL
);

CREATE TABLE IF NOT EXISTS metodologias (
    record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    referencia TEXT NOT NULL,
    bibliografia TEXT NOT NULL,
    versao TEXT
);

CREATE TABLE IF NOT EXISTS classificacao (
    record_id TEXT PRIMARY KEY,
    acreditador TEXT NOT NULL,
    nome TEXT NOT NULL,
    FOREIGN KEY(acreditador) REFERENCES acreditadores(record_id)
);

CREATE TABLE IF NOT EXISTS tipo_amostra (
    record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    classificacao TEXT NOT NULL,
    temperatura_padrao REAL,
    FOREIGN KEY(classificacao) REFERENCES classificacao(record_id)
);

CREATE TABLE IF NOT EXISTS amostra_especifica (
    record_id TEXT PRIMARY KEY,
    tipo_amostra TEXT NOT NULL,
    nome TEXT NOT NULL,
    marca TEXT,
    lote TEXT,
    validade TEXT,
    FOREIGN KEY(tipo_amostra) REFERENCES tipo_amostra(record_id)
);

CREATE TABLE IF NOT EXISTS analises (
    record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    tem_parciais INTEGER,
    gera_complementar INTEGER
);

CREATE TABLE IF NOT EXISTS parciais (
    record_id TEXT PRIMARY KEY,
    analise TEXT NOT NULL,
    nome TEXT NOT NULL,
    ordem INTEGER NOT NULL,
    formula TEXT,
    unidade TEXT,
    FOREIGN KEY(analise) REFERENCES analises(record_id)
);

CREATE TABLE IF NOT EXISTS matriz (
    record_id TEXT PRIMARY KEY,
    tipo_amostra TEXT NOT NULL,
    analise TEXT NOT NULL,
    metodologia TEXT NOT NULL,
    padrao_referencia TEXT NOT NULL,
    valor REAL NOT NULL,
    FOREIGN KEY(tipo_amostra) REFERENCES tipo_amostra(record_id),
    FOREIGN KEY(analise) REFERENCES analises(record_id),
    FOREIGN KEY(metodologia) REFERENCES metodologias(record_id)
);

CREATE TABLE IF NOT EXISTS orcamento (
    record_id TEXT PRIMARY KEY,
    cliente TEXT NOT NULL,
    acreditador TEXT NOT NULL,
    data TEXT NOT NULL,
    qtd_amostras INTEGER NOT NULL,
    urgente INTEGER,
    coleta INTEGER,
    taxa_coleta REAL,
    desconto REAL,
    observacoes TEXT,
    FOREIGN KEY(cliente) REFERENCES clientes(record_id),
    FOREIGN KEY(acreditador) REFERENCES acreditadores(record_id)
);

CREATE TABLE IF NOT EXISTS amostra (
    record_id TEXT PRIMARY KEY,
    orcamento TEXT NOT NULL,
    amostra_especifica TEXT NOT NULL,
    data_entrada TEXT NOT NULL,
    recebedor TEXT NOT NULL,
    temperatura REAL,
    lacre TEXT,
    lacre_ok INTEGER,
    quantidade TEXT,
    anomalias TEXT,
    FOREIGN KEY(orcamento) REFERENCES orcamento(record_id),
    FOREIGN KEY(amostra_especifica) REFERENCES amostra_especifica(record_id),
    FOREIGN KEY(recebedor) REFERENCES funcionarios(record_id)
);

CREATE TABLE IF NOT EXISTS fracionamento (
    record_id TEXT PRIMARY KEY,
    amostra TEXT NOT NULL,
    porcao INTEGER NOT NULL,
    matriz TEXT NOT NULL,
    responsavel TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    FOREIGN KEY(amostra) REFERENCES amostra(record_id),
    FOREIGN KEY(matriz) REFERENCES matriz(record_id),
    FOREIGN KEY(responsavel) REFERENCES funcionarios(record_id)
);

CREATE TABLE IF NOT EXISTS resultado (
    record_id TEXT PRIMARY KEY,
    fracionamento TEXT NOT NULL,
    analista TEXT NOT NULL,
    inicio TEXT NOT NULL,
    termino TEXT,
    valores_parciais TEXT,
    resultado_final TEXT NOT NULL,
    conformidade TEXT NOT NULL,
    observacoes TEXT,
    FOREIGN KEY(fracionamento) REFERENCES fracionamento(record_id),
    FOREIGN KEY(analista) REFERENCES funcionarios(record_id)
);

CREATE TABLE IF NOT EXISTS laudo (
    record_id TEXT PRIMARY KEY,
    orcamento TEXT NOT NULL,
    numero TEXT NOT NULL,
    data_emissao TEXT NOT NULL,
    rt TEXT NOT NULL,
    parecer TEXT NOT NULL,
    observacoes TEXT,
    FOREIGN KEY(orcamento) REFERENCES orcamento(record_id),
    FOREIGN KEY(rt) REFERENCES funcionarios(record_id)
);
"""

def create_tables():
    """Cria todas as tabelas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for statement in CREATE_TABLES_SQL.split(';'):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)

    conn.commit()
    conn.close()
    print("✅ Todas as tabelas foram criadas com sucesso!")

if __name__ == '__main__':
    create_tables()
