#!/usr/bin/env python3
"""
Script para popular o banco de dados do laboratório com dados verossímeis.
Cria todas as 18 tabelas especificadas e popula com dados consistentes.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sqlite', 'vibecforms.db')

def generate_uuid():
    """Gera um UUID único."""
    return str(uuid.uuid4())

def get_db_connection():
    """Obtém conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """Cria todas as 18 tabelas do banco."""
    cursor = conn.cursor()

    # Dropar tabelas existentes para recriar com schema correta
    tables_to_drop = [
        'precos_cliente', 'laudo', 'analises_resultados', 'fracionamento',
        'resultados_parciais', 'entrada_amostra', 'coleta', 'orcamento_os',
        'matriz_analises', 'analises', 'metodologias', 'amostras_especificas',
        'tipos_amostras', 'classificacao_amostras', 'clientes', 'acreditadores', 'funcionarios'
    ]

    for table in tables_to_drop:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        except:
            pass

    conn.commit()

    # 1. FUNCIONÁRIOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            funcao TEXT NOT NULL,
            crq TEXT,
            ativo BOOLEAN DEFAULT 1
        )
    ''')

    # 2. ACREDITADORES (já existe, ignorar erro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acreditadores (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            sigla TEXT NOT NULL,
            tipo_certificado TEXT NOT NULL
        )
    ''')

    # 3. CLASSIFICAÇÃO DE AMOSTRAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classificacao_amostras (
            record_id TEXT PRIMARY KEY,
            acreditador TEXT NOT NULL,
            nome TEXT NOT NULL,
            FOREIGN KEY(acreditador) REFERENCES acreditadores(record_id)
        )
    ''')

    # 4. TIPOS DE AMOSTRAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_amostras (
            record_id TEXT PRIMARY KEY,
            classificacao TEXT NOT NULL,
            nome TEXT NOT NULL,
            temperatura_padrao INTEGER,
            FOREIGN KEY(classificacao) REFERENCES classificacao_amostras(record_id)
        )
    ''')

    # 5. AMOSTRAS ESPECÍFICAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS amostras_especificas (
            record_id TEXT PRIMARY KEY,
            tipo_amostra TEXT NOT NULL,
            nome TEXT NOT NULL,
            codigo TEXT NOT NULL,
            FOREIGN KEY(tipo_amostra) REFERENCES tipos_amostras(record_id)
        )
    ''')

    # 6. METODOLOGIAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metodologias (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            bibliografia TEXT NOT NULL,
            referencia TEXT NOT NULL
        )
    ''')

    # 7. ANÁLISES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analises (
            record_id TEXT PRIMARY KEY,
            nome_oficial TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tem_parciais BOOLEAN DEFAULT 0,
            gera_complementar BOOLEAN DEFAULT 0,
            analise_complementar TEXT,
            FOREIGN KEY(analise_complementar) REFERENCES analises(record_id)
        )
    ''')

    # 8. MATRIZ DE ANÁLISES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matriz_analises (
            record_id TEXT PRIMARY KEY,
            analise TEXT NOT NULL,
            tipo_amostra TEXT NOT NULL,
            metodologia TEXT NOT NULL,
            padrao_referencia TEXT NOT NULL,
            valor_base REAL NOT NULL,
            FOREIGN KEY(analise) REFERENCES analises(record_id),
            FOREIGN KEY(tipo_amostra) REFERENCES tipos_amostras(record_id),
            FOREIGN KEY(metodologia) REFERENCES metodologias(record_id)
        )
    ''')

    # 9. CLIENTES (já existe, ignorar erro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf_cnpj TEXT NOT NULL,
            codigo_sif TEXT,
            codigo_ima TEXT,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            endereco TEXT,
            cidade TEXT,
            uf TEXT,
            cep TEXT
        )
    ''')

    # 10. PREÇOS CLIENTE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos_cliente (
            record_id TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            matriz_analise TEXT NOT NULL,
            valor_especial REAL,
            desconto_percentual REAL,
            data_inicio TEXT NOT NULL,
            data_fim TEXT,
            FOREIGN KEY(cliente) REFERENCES clientes(record_id),
            FOREIGN KEY(matriz_analise) REFERENCES matriz_analises(record_id)
        )
    ''')

    # 11. ORÇAMENTO/OS (já existe, ignorar erro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orcamento_os (
            record_id TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            acreditador TEXT NOT NULL,
            data_inclusao TEXT NOT NULL,
            partes TEXT,
            qtd_amostras INTEGER NOT NULL,
            urgencia BOOLEAN DEFAULT 0,
            valor_coleta REAL,
            taxa_administrativa REAL,
            subtotal REAL,
            valor_total REAL,
            aprovado BOOLEAN DEFAULT 0,
            data_aprovacao TEXT,
            status_tag TEXT DEFAULT 'pendente',
            FOREIGN KEY(cliente) REFERENCES clientes(record_id),
            FOREIGN KEY(acreditador) REFERENCES acreditadores(record_id)
        )
    ''')

    # 12. COLETA (já existe, ignorar erro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coleta (
            record_id TEXT PRIMARY KEY,
            orcamento_os TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            local TEXT NOT NULL,
            coletor TEXT NOT NULL,
            condicoes TEXT,
            numero_lacre TEXT,
            observacoes TEXT,
            status_tag TEXT DEFAULT 'coletada',
            FOREIGN KEY(orcamento_os) REFERENCES orcamento_os(record_id),
            FOREIGN KEY(coletor) REFERENCES funcionarios(record_id)
        )
    ''')

    # 13. ENTRADA AMOSTRA (já existe, ignorar erro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entrada_amostra (
            record_id TEXT PRIMARY KEY,
            orcamento_os TEXT NOT NULL,
            coleta TEXT,
            data_entrada TEXT NOT NULL,
            recebedor TEXT NOT NULL,
            amostra_especifica TEXT NOT NULL,
            descricao TEXT,
            quantidade INTEGER NOT NULL,
            temperatura INTEGER NOT NULL,
            lacre_ok BOOLEAN DEFAULT 0,
            conferido_ok BOOLEAN DEFAULT 0,
            anomalias TEXT,
            status_tag TEXT DEFAULT 'recebida',
            FOREIGN KEY(orcamento_os) REFERENCES orcamento_os(record_id),
            FOREIGN KEY(coleta) REFERENCES coleta(record_id),
            FOREIGN KEY(recebedor) REFERENCES funcionarios(record_id),
            FOREIGN KEY(amostra_especifica) REFERENCES amostras_especificas(record_id)
        )
    ''')

    # 14. FRACIONAMENTO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fracionamento (
            record_id TEXT PRIMARY KEY,
            entrada_amostra TEXT NOT NULL,
            numero_porcao INTEGER NOT NULL,
            tipo_analise TEXT NOT NULL,
            responsavel TEXT NOT NULL,
            data_fracionamento TEXT NOT NULL,
            hora_fracionamento TEXT NOT NULL,
            FOREIGN KEY(entrada_amostra) REFERENCES entrada_amostra(record_id),
            FOREIGN KEY(responsavel) REFERENCES funcionarios(record_id)
        )
    ''')

    # 15. RESULTADOS PARCIAIS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados_parciais (
            record_id TEXT PRIMARY KEY,
            analise TEXT NOT NULL,
            nome_parcial TEXT NOT NULL,
            formula TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            FOREIGN KEY(analise) REFERENCES analises(record_id)
        )
    ''')

    # 16. ANÁLISES RESULTADOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analises_resultados (
            record_id TEXT PRIMARY KEY,
            fracionamento TEXT NOT NULL,
            matriz_analise TEXT NOT NULL,
            inicio_analise TEXT NOT NULL,
            termino_analise TEXT,
            resultado_previo REAL,
            resultado_final REAL,
            conformidade TEXT,
            cqi_ok BOOLEAN DEFAULT 0,
            status_tag TEXT DEFAULT 'em_execucao',
            FOREIGN KEY(fracionamento) REFERENCES fracionamento(record_id),
            FOREIGN KEY(matriz_analise) REFERENCES matriz_analises(record_id)
        )
    ''')

    # 17. LAUDO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS laudo (
            record_id TEXT PRIMARY KEY,
            orcamento_os TEXT NOT NULL,
            acreditador TEXT NOT NULL,
            numero TEXT NOT NULL,
            data_emissao TEXT NOT NULL,
            rt TEXT NOT NULL,
            parecer TEXT NOT NULL,
            status_tag TEXT DEFAULT 'rascunho',
            FOREIGN KEY(orcamento_os) REFERENCES orcamento_os(record_id),
            FOREIGN KEY(acreditador) REFERENCES acreditadores(record_id),
            FOREIGN KEY(rt) REFERENCES funcionarios(record_id)
        )
    ''')

    conn.commit()
    print("✓ Todas as 17 tabelas criadas com sucesso")

def populate_funcionarios(conn):
    """Popula a tabela de funcionários."""
    cursor = conn.cursor()

    funcionarios = [
        ('Maria Silva', 'rt', 'CRQ-123456'),
        ('João Santos', 'analista', None),
        ('Pedro Costa', 'analista', None),
        ('Ana Oliveira', 'coletor', None),
        ('Carlos Souza', 'recepcao', None),
        ('Beatriz Alves', 'supervisor', None),
        ('Roberto Ferreira', 'administrativo', None),
        ('Francisca Lima', 'analista', None),
    ]

    ids = []
    for nome, funcao, crq in funcionarios:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO funcionarios (record_id, nome, funcao, crq, ativo)
            VALUES (?, ?, ?, ?, 1)
        ''', (uid, nome, funcao, crq))

    conn.commit()
    print(f"✓ {len(funcionarios)} funcionários inseridos")
    return ids

def populate_acreditadores(conn):
    """Popula a tabela de acreditadores."""
    cursor = conn.cursor()

    acreditadores = [
        ('MAPA - Ministério da Agricultura', 'MAPA', 'SIF'),
        ('IMA - Inspeção Municipal de Alimentos', 'IMA', 'Municipal'),
        ('ISO - International Organization', 'ISO', 'ISO 17025'),
    ]

    ids = []
    for nome, sigla, tipo in acreditadores:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO acreditadores (record_id, nome, sigla, tipo_certificado)
            VALUES (?, ?, ?, ?)
        ''', (uid, nome, sigla, tipo))

    conn.commit()
    print(f"✓ {len(acreditadores)} acreditadores inseridos")
    return ids

def populate_classificacao_amostras(conn, acreditador_ids):
    """Popula a tabela de classificação de amostras."""
    cursor = conn.cursor()

    classificacoes = [
        (acreditador_ids[0], 'Água para Consumo Humano'),
        (acreditador_ids[0], 'Alimentos'),
        (acreditador_ids[1], 'Água de Poço'),
        (acreditador_ids[2], 'Água de Fonte'),
    ]

    ids = []
    for acreditador, nome in classificacoes:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO classificacao_amostras (record_id, acreditador, nome)
            VALUES (?, ?, ?)
        ''', (uid, acreditador, nome))

    conn.commit()
    print(f"✓ {len(classificacoes)} classificações de amostras inseridas")
    return ids

def populate_tipos_amostras(conn, classif_ids):
    """Popula a tabela de tipos de amostras."""
    cursor = conn.cursor()

    tipos = [
        (classif_ids[0], 'Água Tratada', 25),
        (classif_ids[0], 'Água Bruta', 4),
        (classif_ids[1], 'Leite Integral', 4),
        (classif_ids[1], 'Queijo', 4),
        (classif_ids[2], 'Água de Poço', 4),
        (classif_ids[3], 'Água Mineral', 25),
    ]

    ids = []
    for classificacao, nome, temp in tipos:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO tipos_amostras (record_id, classificacao, nome, temperatura_padrao)
            VALUES (?, ?, ?, ?)
        ''', (uid, classificacao, nome, temp))

    conn.commit()
    print(f"✓ {len(tipos)} tipos de amostras inseridos")
    return ids

def populate_amostras_especificas(conn, tipo_ids):
    """Popula a tabela de amostras específicas."""
    cursor = conn.cursor()

    amostras = [
        (tipo_ids[0], 'Água ETA-01 - Decantador', 'AGUA-ETA-001'),
        (tipo_ids[0], 'Água ETA-02 - Filtro', 'AGUA-ETA-002'),
        (tipo_ids[1], 'Água Bruta Rio Doce', 'AGUA-BRUTA-001'),
        (tipo_ids[2], 'Leite Integral Fazenda A', 'LEITE-FA-001'),
        (tipo_ids[2], 'Leite Integral Fazenda B', 'LEITE-FB-001'),
        (tipo_ids[3], 'Queijo Meia Cura Casa Grande', 'QUEIJO-CG-001'),
        (tipo_ids[4], 'Poço Residencial Rua A', 'POCO-RA-001'),
        (tipo_ids[5], 'Mineral Natural Fonte Pura', 'MINERAL-FP-001'),
    ]

    ids = []
    for tipo, nome, codigo in amostras:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO amostras_especificas (record_id, tipo_amostra, nome, codigo)
            VALUES (?, ?, ?, ?)
        ''', (uid, tipo, nome, codigo))

    conn.commit()
    print(f"✓ {len(amostras)} amostras específicas inseridas")
    return ids

def populate_metodologias(conn):
    """Popula a tabela de metodologias."""
    cursor = conn.cursor()

    metodologias = [
        ('Contagem de Coliformes Totais', 'ISO 9308-1:2014', 'ISO 9308-1:2014'),
        ('Contagem de Coliformes Fecais', 'ISO 9308-1:2014', 'ISO 9308-1:2014'),
        ('Contagem de Bactérias Heterotróficas', 'ISO 6222:2019', 'ISO 6222:2019'),
        ('Determinação de Cloro Residual', 'ISO 7393-1:2017', 'ISO 7393-1:2017'),
        ('pH', 'ISO 10523:2012', 'ISO 10523:2012'),
        ('Turbidez', 'ISO 7027-1:2016', 'ISO 7027-1:2016'),
        ('Contagem de Células Somáticas', 'ISO 13366-2:2006', 'ISO 13366-2:2006'),
        ('Composição Físico-Química do Leite', 'IN 30/2021', 'IN 30/2021'),
    ]

    ids = []
    for nome, biblio, ref in metodologias:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO metodologias (record_id, nome, bibliografia, referencia)
            VALUES (?, ?, ?, ?)
        ''', (uid, nome, biblio, ref))

    conn.commit()
    print(f"✓ {len(metodologias)} metodologias inseridas")
    return ids

def populate_analises(conn):
    """Popula a tabela de análises."""
    cursor = conn.cursor()

    analises = [
        ('Contagem de Coliformes Totais', 'microbiologica', False, True, None),
        ('Contagem de Coliformes Fecais', 'microbiologica', False, False, None),
        ('Contagem de Bactérias Heterotróficas', 'microbiologica', False, False, None),
        ('Cloro Residual Livre', 'fisico_quimica', False, False, None),
        ('pH', 'fisico_quimica', False, False, None),
        ('Turbidez', 'fisico_quimica', False, False, None),
        ('Contagem de Células Somáticas', 'microbiologica', False, False, None),
        ('Lactose', 'fisico_quimica', True, False, None),
        ('Proteína Bruta', 'fisico_quimica', True, False, None),
        ('Gordura Bruta', 'fisico_quimica', True, False, None),
    ]

    ids = []
    id_map = {}  # Para referência cruzada

    for nome, tipo, tem_parciais, gera_complementar, complementar in analises:
        uid = generate_uuid()
        ids.append(uid)
        id_map[nome] = uid
        cursor.execute('''
            INSERT INTO analises (record_id, nome_oficial, tipo, tem_parciais, gera_complementar, analise_complementar)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (uid, nome, tipo, tem_parciais, gera_complementar, complementar))

    # Atualizar análises complementares
    cursor.execute('''
        UPDATE analises SET analise_complementar = ? WHERE nome_oficial = ?
    ''', (id_map.get('Contagem de Coliformes Fecais'), 'Contagem de Coliformes Totais'))

    conn.commit()
    print(f"✓ {len(analises)} análises inseridas")
    return ids, id_map

def populate_matriz_analises(conn, analise_ids, tipo_amostra_ids, metodologia_ids):
    """Popula a tabela matriz de análises."""
    cursor = conn.cursor()

    # Criar combinações relevantes (não todas as possíveis)
    matriz_data = [
        (analise_ids[0], tipo_amostra_ids[0], metodologia_ids[0], '0 UFC/100mL', 85.00),
        (analise_ids[0], tipo_amostra_ids[1], metodologia_ids[0], '0 UFC/100mL', 90.00),
        (analise_ids[0], tipo_amostra_ids[4], metodologia_ids[0], '0 UFC/100mL', 95.00),
        (analise_ids[1], tipo_amostra_ids[0], metodologia_ids[1], '0 UFC/100mL', 85.00),
        (analise_ids[2], tipo_amostra_ids[0], metodologia_ids[2], '<100 UFC/mL', 75.00),
        (analise_ids[3], tipo_amostra_ids[0], metodologia_ids[3], '0.2-0.5 mg/L', 45.00),
        (analise_ids[4], tipo_amostra_ids[0], metodologia_ids[4], '6.5-8.5', 25.00),
        (analise_ids[5], tipo_amostra_ids[0], metodologia_ids[5], '<1 UNT', 35.00),
        (analise_ids[6], tipo_amostra_ids[2], metodologia_ids[6], '<200 mil células/mL', 120.00),
        (analise_ids[7], tipo_amostra_ids[2], metodologia_ids[7], '<0.3 g/100mL', 150.00),
        (analise_ids[8], tipo_amostra_ids[2], metodologia_ids[7], '3.2-3.8 g/100mL', 150.00),
        (analise_ids[9], tipo_amostra_ids[2], metodologia_ids[7], '3.5-4.2 g/100mL', 150.00),
    ]

    ids = []
    for analise, tipo, metodologia, padrao, valor in matriz_data:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO matriz_analises (record_id, analise, tipo_amostra, metodologia, padrao_referencia, valor_base)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (uid, analise, tipo, metodologia, padrao, valor))

    conn.commit()
    print(f"✓ {len(matriz_data)} linhas de matriz de análises inseridas")
    return ids

def populate_clientes(conn):
    """Popula a tabela de clientes."""
    cursor = conn.cursor()

    clientes = [
        ('SAAE - Serviço de Água e Esgoto', '00.000.000/0000-00', 'SIF-2025-001', None,
         'contato@saae.mg.gov.br', '(31) 3333-4444', 'Rua A, 100', 'Belo Horizonte', 'MG', '30130-100'),
        ('Laticínios São João', '12.345.678/0001-90', None, 'IMA-2025-002',
         'vendas@lacticiios.com.br', '(35) 9999-5555', 'Rua B, 200', 'Varginha', 'MG', '37000-000'),
        ('Pousada da Fonte', '98.765.432/0001-10', None, None,
         'pousada@email.com.br', '(31) 8888-7777', 'Rua C, 300', 'Betim', 'MG', '32000-000'),
        ('Distribuidora de Alimentos Bom Sabor', '11.222.333/0001-44', None, 'IMA-2025-003',
         'qualidade@bomsabor.com.br', '(21) 3456-7890', 'Rua D, 400', 'Rio de Janeiro', 'RJ', '20000-000'),
    ]

    ids = []
    for nome, cpf_cnpj, sif, ima, email, telefone, endereco, cidade, uf, cep in clientes:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO clientes (record_id, nome, cpf_cnpj, codigo_sif, codigo_ima, email, telefone, endereco, cidade, uf, cep)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, nome, cpf_cnpj, sif, ima, email, telefone, endereco, cidade, uf, cep))

    conn.commit()
    print(f"✓ {len(clientes)} clientes inseridos")
    return ids

def populate_orcamento_os(conn, cliente_ids, acreditador_ids):
    """Popula a tabela de orçamentos/OS com diferentes status do Kanban."""
    cursor = conn.cursor()

    # Criar orçamentos com diferentes status para cobrir todo o fluxo
    today = datetime.now()

    orcamentos = [
        # Status: pendente
        (cliente_ids[0], acreditador_ids[0],
         (today - timedelta(days=5)).strftime('%Y-%m-%d'),
         'João Silva - Supervisor', 2, False, 150.00, 50.00, None, None,
         False, None, 'pendente'),

        # Status: enviado
        (cliente_ids[1], acreditador_ids[0],
         (today - timedelta(days=3)).strftime('%Y-%m-%d'),
         'Maria - Gerente de Qualidade', 3, False, 200.00, 75.00, 275.00, 275.00,
         False, None, 'enviado'),

        # Status: aprovado
        (cliente_ids[2], acreditador_ids[1],
         (today - timedelta(days=2)).strftime('%Y-%m-%d'),
         'Carlos - Responsável', 1, True, 100.00, 40.00, 140.00, 210.00,
         True, (today - timedelta(days=1)).strftime('%Y-%m-%d'), 'aprovado'),

        # Status: os_gerada
        (cliente_ids[3], acreditador_ids[0],
         (today - timedelta(days=10)).strftime('%Y-%m-%d'),
         'Empresa - Rastreabilidade', 4, False, 250.00, 80.00, 330.00, 330.00,
         True, (today - timedelta(days=8)).strftime('%Y-%m-%d'), 'os_gerada'),
    ]

    ids = []
    for cliente, acreditador, data_inc, partes, qtd, urgencia, col, taxa, subtotal, total, aprovado, data_apr, status in orcamentos:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO orcamento_os (record_id, cliente, acreditador, data_inclusao, partes, qtd_amostras,
                                     urgencia, valor_coleta, taxa_administrativa, subtotal, valor_total,
                                     aprovado, data_aprovacao, status_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, cliente, acreditador, data_inc, partes, qtd, urgencia, col, taxa, subtotal, total, aprovado, data_apr, status))

    conn.commit()
    print(f"✓ {len(orcamentos)} orçamentos/OS inseridos (4 status diferentes)")
    return ids

def populate_coleta(conn, orcamento_ids, funcionario_ids):
    """Popula a tabela de coleta."""
    cursor = conn.cursor()

    coletas = [
        (orcamento_ids[2], (datetime.now() - timedelta(days=2)).isoformat(),
         'Fazenda São João - Varginha', funcionario_ids[3], 'Tempo nublado, amostra refrigerada', 'LACRE-001', None),
        (orcamento_ids[3], (datetime.now() - timedelta(days=9)).isoformat(),
         'ETA - Belo Horizonte', funcionario_ids[3], 'Coleta em 4 pontos diferentes', 'LACRE-002', 'Coleta realizada sem incidentes'),
    ]

    ids = []
    for orcamento, data_hora, local, coletor, condicoes, lacre, obs in coletas:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO coleta (record_id, orcamento_os, data_hora, local, coletor, condicoes, numero_lacre, observacoes, status_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'coletada')
        ''', (uid, orcamento, data_hora, local, coletor, condicoes, lacre, obs))

    conn.commit()
    print(f"✓ {len(coletas)} coletas inseridas")
    return ids

def populate_entrada_amostra(conn, orcamento_ids, coleta_ids, funcionario_ids, amostra_ids):
    """Popula a tabela de entrada de amostra com diferentes status."""
    cursor = conn.cursor()

    entrada_amostras = [
        # Status: aguardando_coleta
        (orcamento_ids[0], None, (datetime.now() - timedelta(days=4)).isoformat(),
         funcionario_ids[4], amostra_ids[0], 'Amostra de água da ETA', 1, 25, False, False, None, 'aguardando_coleta'),

        # Status: coletada
        (orcamento_ids[1], None, (datetime.now() - timedelta(days=2)).isoformat(),
         funcionario_ids[4], amostra_ids[3], 'Leite integral da fazenda', 2, 4, True, False, None, 'coletada'),

        # Status: recebida
        (orcamento_ids[2], coleta_ids[0], (datetime.now() - timedelta(days=2)).isoformat(),
         funcionario_ids[4], amostra_ids[4], 'Leite integral Fazenda B', 1, 4, True, True, None, 'recebida'),

        # Status: fracionada
        (orcamento_ids[3], coleta_ids[1], (datetime.now() - timedelta(days=8)).isoformat(),
         funcionario_ids[4], amostra_ids[1], 'Água ETA filtro', 2, 25, True, True, None, 'fracionada'),
    ]

    ids = []
    for orcamento, coleta, data_entrada, recebedor, amostra, descricao, qtd, temp, lacre, conferido, anomalias, status in entrada_amostras:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO entrada_amostra (record_id, orcamento_os, coleta, data_entrada, recebedor, amostra_especifica,
                                        descricao, quantidade, temperatura, lacre_ok, conferido_ok, anomalias, status_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, orcamento, coleta, data_entrada, recebedor, amostra, descricao, qtd, temp, lacre, conferido, anomalias, status))

    conn.commit()
    print(f"✓ {len(entrada_amostras)} entradas de amostras inseridas (4 status diferentes)")
    return ids

def populate_fracionamento(conn, entrada_ids, funcionario_ids):
    """Popula a tabela de fracionamento."""
    cursor = conn.cursor()

    # Apenas as amostras com status "recebida" e "fracionada" têm fracionamento
    fracionamentos = [
        (entrada_ids[2], 1, 'microbiologica', funcionario_ids[5], (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), '14:30'),
        (entrada_ids[3], 1, 'microbiologica', funcionario_ids[5], (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), '09:00'),
        (entrada_ids[3], 2, 'fisico_quimica', funcionario_ids[5], (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), '09:30'),
    ]

    ids = []
    for entrada, porcao, tipo, responsavel, data, hora in fracionamentos:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO fracionamento (record_id, entrada_amostra, numero_porcao, tipo_analise, responsavel,
                                      data_fracionamento, hora_fracionamento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, entrada, porcao, tipo, responsavel, data, hora))

    conn.commit()
    print(f"✓ {len(fracionamentos)} fracionamentos inseridos")
    return ids

def populate_analises_resultados(conn, fracionamento_ids, matriz_ids):
    """Popula a tabela de análises resultados com diferentes status."""
    cursor = conn.cursor()

    analises_resultados = [
        # Status: aguardando
        (fracionamento_ids[0], matriz_ids[3], (datetime.now() - timedelta(days=1)).isoformat(),
         None, None, None, 'conforme', False, 'aguardando'),

        # Status: em_execucao
        (fracionamento_ids[1], matriz_ids[0], (datetime.now() - timedelta(days=6)).isoformat(),
         None, None, None, 'conforme', False, 'em_execucao'),

        # Status: concluida
        (fracionamento_ids[2], matriz_ids[4], (datetime.now() - timedelta(days=6)).isoformat(),
         (datetime.now() - timedelta(days=5)).isoformat(), 25.5, 25.0, 'conforme', True, 'concluida'),
    ]

    ids = []
    for fracionamento, matriz, inicio, fim, resultado_p, resultado_f, conformidade, cqi, status in analises_resultados:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO analises_resultados (record_id, fracionamento, matriz_analise, inicio_analise, termino_analise,
                                            resultado_previo, resultado_final, conformidade, cqi_ok, status_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, fracionamento, matriz, inicio, fim, resultado_p, resultado_f, conformidade, cqi, status))

    conn.commit()
    print(f"✓ {len(analises_resultados)} análises resultados inseridas (3 status diferentes)")
    return ids

def populate_laudo(conn, orcamento_ids, acreditador_ids, funcionario_ids):
    """Popula a tabela de laudo com diferentes status."""
    cursor = conn.cursor()

    laudos = [
        # Status: rascunho
        (orcamento_ids[0], acreditador_ids[0], f'MAPA-001/2025',
         (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
         funcionario_ids[0], 'conforme', 'rascunho'),

        # Status: revisao_rt
        (orcamento_ids[1], acreditador_ids[0], f'MAPA-002/2025',
         (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
         funcionario_ids[0], 'conforme', 'revisao_rt'),

        # Status: liberado
        (orcamento_ids[2], acreditador_ids[1], f'IMA-001/2025',
         (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
         funcionario_ids[0], 'conforme', 'liberado'),

        # Status: entregue
        (orcamento_ids[3], acreditador_ids[0], f'MAPA-003/2025',
         (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
         funcionario_ids[0], 'conforme', 'entregue'),
    ]

    ids = []
    for orcamento, acreditador, numero, data_emissao, rt, parecer, status in laudos:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO laudo (record_id, orcamento_os, acreditador, numero, data_emissao, rt, parecer, status_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, orcamento, acreditador, numero, data_emissao, rt, parecer, status))

    conn.commit()
    print(f"✓ {len(laudos)} laudos inseridos (4 status diferentes)")
    return ids

def populate_resultados_parciais(conn, analise_ids):
    """Popula a tabela de resultados parciais."""
    cursor = conn.cursor()

    # Apenas análises que têm tem_parciais = True
    # Lactose, Proteína Bruta e Gordura Bruta
    parciais = [
        (analise_ids[7], 'Lactose Redutora', 'lactose_redutora', 1),
        (analise_ids[7], 'Lactose Total', 'lactose_total', 2),
        (analise_ids[8], 'Proteína Sérica', 'proteina_serica', 1),
        (analise_ids[8], 'Proteína Caseína', 'proteina_caseinaa', 2),
        (analise_ids[9], 'Gordura Bruta', 'gordura_bruta', 1),
    ]

    ids = []
    for analise, nome, formula, ordem in parciais:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO resultados_parciais (record_id, analise, nome_parcial, formula, ordem)
            VALUES (?, ?, ?, ?, ?)
        ''', (uid, analise, nome, formula, ordem))

    conn.commit()
    print(f"✓ {len(parciais)} resultados parciais inseridos")
    return ids

def populate_precos_cliente(conn, cliente_ids, matriz_ids):
    """Popula a tabela de preços cliente."""
    cursor = conn.cursor()

    precos = [
        (cliente_ids[0], matriz_ids[0], 80.00, None,
         (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
         (datetime.now() + timedelta(days=330)).strftime('%Y-%m-%d')),
        (cliente_ids[1], matriz_ids[6], None, 10.0,  # 10% desconto
         (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
         (datetime.now() + timedelta(days=330)).strftime('%Y-%m-%d')),
        (cliente_ids[3], matriz_ids[8], 140.00, None,
         (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
         (datetime.now() + timedelta(days=330)).strftime('%Y-%m-%d')),
    ]

    ids = []
    for cliente, matriz, valor, desconto, data_ini, data_fim in precos:
        uid = generate_uuid()
        ids.append(uid)
        cursor.execute('''
            INSERT INTO precos_cliente (record_id, cliente, matriz_analise, valor_especial, desconto_percentual,
                                       data_inicio, data_fim)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, cliente, matriz, valor, desconto, data_ini, data_fim))

    conn.commit()
    print(f"✓ {len(precos)} preços de cliente inseridos")
    return ids

def main():
    """Função principal."""
    print("\n" + "="*60)
    print("POPULANDO BANCO DE DADOS - ANÁLISE LABORATORIAL")
    print("="*60 + "\n")

    # Conectar ao banco
    conn = get_db_connection()

    try:
        # Criar tabelas (também dropa as existentes)
        print("Criando tabelas...")
        create_tables(conn)

        # Popular tabelas em ordem de dependência
        print("\nPopulando tabelas...\n")

        func_ids = populate_funcionarios(conn)
        acred_ids = populate_acreditadores(conn)
        classif_ids = populate_classificacao_amostras(conn, acred_ids)
        tipo_ids = populate_tipos_amostras(conn, classif_ids)
        amostra_ids = populate_amostras_especificas(conn, tipo_ids)
        met_ids = populate_metodologias(conn)
        analis_ids, analisis_map = populate_analises(conn)
        matriz_ids = populate_matriz_analises(conn, analis_ids, tipo_ids, met_ids)
        client_ids = populate_clientes(conn)
        orcam_ids = populate_orcamento_os(conn, client_ids, acred_ids)
        coleta_ids = populate_coleta(conn, orcam_ids, func_ids)
        entrada_ids = populate_entrada_amostra(conn, orcam_ids, coleta_ids, func_ids, amostra_ids)
        fracio_ids = populate_fracionamento(conn, entrada_ids, func_ids)
        analis_result_ids = populate_analises_resultados(conn, fracio_ids, matriz_ids)
        laudo_ids = populate_laudo(conn, orcam_ids, acred_ids, func_ids)
        populate_resultados_parciais(conn, analis_ids)
        populate_precos_cliente(conn, client_ids, matriz_ids)

        print("\n" + "="*60)
        print("✓ BANCO DE DADOS POPULADO COM SUCESSO!")
        print("="*60)
        print("\n📊 RESUMO DO FLUXO KANBAN:\n")
        print("Pipeline de Orçamentos:")
        print("  • Status 'pendente': 1 registro")
        print("  • Status 'enviado': 1 registro")
        print("  • Status 'aprovado': 1 registro")
        print("  • Status 'os_gerada': 1 registro")
        print("\nFluxo de Amostras:")
        print("  • Status 'aguardando_coleta': 1 registro")
        print("  • Status 'coletada': 1 registro")
        print("  • Status 'recebida': 1 registro")
        print("  • Status 'fracionada': 1 registro")
        print("\nExecutação de Análises:")
        print("  • Status 'aguardando': 1 registro")
        print("  • Status 'em_execucao': 1 registro")
        print("  • Status 'concluida': 1 registro")
        print("\nAprovação de Laudos:")
        print("  • Status 'rascunho': 1 registro")
        print("  • Status 'revisao_rt': 1 registro")
        print("  • Status 'liberado': 1 registro")
        print("  • Status 'entregue': 1 registro")
        print("\n" + "="*60 + "\n")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
