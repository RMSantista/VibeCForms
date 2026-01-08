#!/usr/bin/env python3
"""
Script para popular dados realistas no LIMS refatorado.
Popula todas as 15 tabelas com dados de exemplo coerentes e relacionados.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "sqlite" / "vibecforms.db"
SPECS_DIR = BASE_DIR / "specs"

# Ensure database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class LIMSDataPopulator:
    """Populator para dados do LIMS."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.ids = {
            "acreditadores": [],
            "funcionarios": [],
            "clientes": [],
            "metodologias": [],
            "classificacao": [],
            "tipo_amostra": [],
            "amostra_especifica": [],
            "analises": [],
            "parciais": [],
            "matriz": [],
            "orcamento": [],
            "amostra": [],
            "fracionamento": [],
            "resultado": [],
            "laudo": [],
        }

    def connect(self):
        """Conecta ao banco de dados."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        print(f"Conectado ao banco de dados: {self.db_path}")

    def disconnect(self):
        """Desconecta do banco de dados."""
        if self.conn:
            self.conn.close()
            print("Desconectado do banco de dados")

    def create_tables(self):
        """Cria as tabelas necessárias (com base nos specs)."""
        print("\n=== Criando tabelas ===")

        # Acreditadores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS acreditadores (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                sigla TEXT NOT NULL,
                tipo_certificado TEXT NOT NULL
            )
        """)

        # Funcionários
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                funcao TEXT NOT NULL,
                crq TEXT,
                ativo INTEGER
            )
        """)

        # Clientes
        self.cursor.execute("""
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
                cep TEXT,
                desconto_padrao REAL
            )
        """)

        # Metodologias
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS metodologias (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                bibliografia TEXT NOT NULL,
                referencia TEXT NOT NULL,
                versao TEXT
            )
        """)

        # Classificação de Amostra
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS classificacao (
                record_id TEXT PRIMARY KEY,
                acreditador TEXT NOT NULL,
                nome TEXT NOT NULL
            )
        """)

        # Tipo de Amostra
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_amostra (
                record_id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                classificacao TEXT NOT NULL,
                temperatura_padrao REAL
            )
        """)

        # Amostra Específica
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS amostra_especifica (
                record_id TEXT PRIMARY KEY,
                tipo_amostra TEXT NOT NULL,
                nome TEXT NOT NULL,
                marca TEXT,
                lote TEXT,
                validade TEXT
            )
        """)

        # Análises
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS analises (
                record_id TEXT PRIMARY KEY,
                nome_oficial TEXT NOT NULL,
                tipo TEXT NOT NULL,
                tem_parciais INTEGER,
                gera_complementar INTEGER,
                analise_complementar TEXT
            )
        """)

        # Resultados Parciais
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parciais (
                record_id TEXT PRIMARY KEY,
                analise TEXT NOT NULL,
                nome TEXT NOT NULL,
                ordem INTEGER NOT NULL,
                formula TEXT,
                unidade TEXT
            )
        """)

        # Matriz de Análises
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matriz (
                record_id TEXT PRIMARY KEY,
                tipo_amostra TEXT NOT NULL,
                analise TEXT NOT NULL,
                metodologia TEXT NOT NULL,
                padrao_referencia TEXT NOT NULL,
                valor REAL NOT NULL
            )
        """)

        # Orçamento
        self.cursor.execute("""
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
                observacoes TEXT
            )
        """)

        # Amostra (Entrada no Lab)
        self.cursor.execute("""
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
                anomalias TEXT
            )
        """)

        # Fracionamento
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fracionamento (
                record_id TEXT PRIMARY KEY,
                amostra TEXT NOT NULL,
                porcao INTEGER NOT NULL,
                matriz TEXT NOT NULL,
                responsavel TEXT NOT NULL,
                data_hora TEXT NOT NULL
            )
        """)

        # Resultado
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resultado (
                record_id TEXT PRIMARY KEY,
                fracionamento TEXT NOT NULL,
                analista TEXT NOT NULL,
                inicio TEXT NOT NULL,
                termino TEXT,
                valores_parciais TEXT,
                resultado_final TEXT NOT NULL,
                conformidade TEXT NOT NULL,
                observacoes TEXT
            )
        """)

        # Laudo
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS laudo (
                record_id TEXT PRIMARY KEY,
                orcamento TEXT NOT NULL,
                numero TEXT NOT NULL,
                data_emissao TEXT NOT NULL,
                rt TEXT NOT NULL,
                parecer TEXT NOT NULL,
                observacoes TEXT
            )
        """)

        self.conn.commit()
        print("Tabelas criadas com sucesso")

    def _generate_id(self):
        """Gera um UUID para records."""
        return str(uuid.uuid4())

    def populate_acreditadores(self):
        """Popula acreditadores."""
        print("\n=== Populando Acreditadores ===")
        data = [
            {
                "nome": "Ministério da Agricultura, Pecuária e Abastecimento",
                "sigla": "MAPA",
                "tipo_certificado": "oficial",
            },
            {
                "nome": "Instituto Mineiro de Agropecuária",
                "sigla": "IMA",
                "tipo_certificado": "oficial",
            },
            {
                "nome": "Instituto Nacional de Metrologia, Qualidade e Tecnologia",
                "sigla": "INMETRO",
                "tipo_certificado": "oficial",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            self.cursor.execute(
                """
                INSERT INTO acreditadores (record_id, nome, sigla, tipo_certificado)
                VALUES (?, ?, ?, ?)
            """,
                (record_id, item["nome"], item["sigla"], item["tipo_certificado"]),
            )
            self.ids["acreditadores"].append(record_id)
            print(f"  - {item['sigla']}")

        self.conn.commit()

    def populate_funcionarios(self):
        """Popula funcionários."""
        print("\n=== Populando Funcionários ===")
        data = [
            {
                "nome": "João da Silva",
                "funcao": "rt",
                "crq": "CRQ-1001",
                "ativo": 1,
            },
            {
                "nome": "Maria Santos",
                "funcao": "analista",
                "crq": "CRQ-1002",
                "ativo": 1,
            },
            {
                "nome": "Carlos Oliveira",
                "funcao": "analista",
                "crq": "CRQ-1003",
                "ativo": 1,
            },
            {
                "nome": "Ana Costa",
                "funcao": "supervisor",
                "crq": "CRQ-1004",
                "ativo": 1,
            },
            {
                "nome": "Pedro Ferreira",
                "funcao": "coletor",
                "crq": None,
                "ativo": 1,
            },
            {
                "nome": "Lucia Martins",
                "funcao": "recepcao",
                "crq": None,
                "ativo": 1,
            },
            {
                "nome": "Renato Gomes",
                "funcao": "administrativo",
                "crq": None,
                "ativo": 1,
            },
            {
                "nome": "Fernanda Silva",
                "funcao": "analista",
                "crq": "CRQ-1005",
                "ativo": 1,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            self.cursor.execute(
                """
                INSERT INTO funcionarios (record_id, nome, funcao, crq, ativo)
                VALUES (?, ?, ?, ?, ?)
            """,
                (record_id, item["nome"], item["funcao"], item["crq"], item["ativo"]),
            )
            self.ids["funcionarios"].append(record_id)
            print(f"  - {item['nome']} ({item['funcao']})")

        self.conn.commit()

    def populate_clientes(self):
        """Popula clientes."""
        print("\n=== Populando Clientes ===")
        data = [
            {
                "nome": "Indústria de Laticínios Silva",
                "cpf_cnpj": "12.345.678/0001-90",
                "codigo_sif": "SIF-0001",
                "codigo_ima": "IMA-001",
                "email": "contato@laticinossilva.com.br",
                "telefone": "(31) 3333-1234",
                "endereco": "Rua das Flores, 123",
                "cidade": "Belo Horizonte",
                "uf": "MG",
                "cep": "30123-456",
                "desconto_padrao": 5.0,
            },
            {
                "nome": "Frigorífico Premium Carnes",
                "cpf_cnpj": "98.765.432/0001-11",
                "codigo_sif": "SIF-0002",
                "codigo_ima": "IMA-002",
                "email": "laboratorio@frigorificopremium.com.br",
                "telefone": "(31) 3333-5678",
                "endereco": "Av. Industrial, 456",
                "cidade": "Contagem",
                "uf": "MG",
                "cep": "32210-780",
                "desconto_padrao": 7.5,
            },
            {
                "nome": "Distribuidora de Bebidas do Centro-Oeste",
                "cpf_cnpj": "45.678.901/0001-22",
                "codigo_sif": None,
                "codigo_ima": "IMA-003",
                "email": "qualidade@distribuiadorabebidas.com.br",
                "telefone": "(31) 3333-9999",
                "endereco": "Rua do Comércio, 789",
                "cidade": "Betim",
                "uf": "MG",
                "cep": "32604-100",
                "desconto_padrao": 3.0,
            },
            {
                "nome": "Estação de Tratamento de Água Municipal",
                "cpf_cnpj": "01.234.567/0001-33",
                "codigo_sif": None,
                "codigo_ima": None,
                "email": "laboratorio@etamunicipal.gov.br",
                "telefone": "(31) 3333-4444",
                "endereco": "Rod. BR-262, Km 5",
                "cidade": "Lagoa Santa",
                "uf": "MG",
                "cep": "33400-000",
                "desconto_padrao": 10.0,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            self.cursor.execute(
                """
                INSERT INTO clientes (record_id, nome, cpf_cnpj, codigo_sif, codigo_ima,
                                     email, telefone, endereco, cidade, uf, cep, desconto_padrao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    item["nome"],
                    item["cpf_cnpj"],
                    item["codigo_sif"],
                    item["codigo_ima"],
                    item["email"],
                    item["telefone"],
                    item["endereco"],
                    item["cidade"],
                    item["uf"],
                    item["cep"],
                    item["desconto_padrao"],
                ),
            )
            self.ids["clientes"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_metodologias(self):
        """Popula metodologias."""
        print("\n=== Populando Metodologias ===")
        data = [
            {
                "nome": "Acidez Titulável (Método Clássico)",
                "bibliografia": "BRASIL. Ministério da Agricultura",
                "referencia": "MAPA - MA 1001/2000",
                "versao": "1.0",
            },
            {
                "nome": "Contagem de Coliformes (Técnica MPN)",
                "bibliografia": "APHA Standard Methods",
                "referencia": "AOAC 990.12",
                "versao": "2021",
            },
            {
                "nome": "Determinação de pH (Potenciometria)",
                "bibliografia": "ISO 10523:2008",
                "referencia": "ISO 10523",
                "versao": "2008",
            },
            {
                "nome": "Determinação de Proteína Bruta (Kjeldahl)",
                "bibliografia": "AOAC Official Methods",
                "referencia": "AOAC 984.13",
                "versao": "2016",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            self.cursor.execute(
                """
                INSERT INTO metodologias (record_id, nome, bibliografia, referencia, versao)
                VALUES (?, ?, ?, ?, ?)
            """,
                (record_id, item["nome"], item["bibliografia"], item["referencia"], item["versao"]),
            )
            self.ids["metodologias"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_classificacoes(self):
        """Popula classificações de amostra."""
        print("\n=== Populando Classificações de Amostra ===")
        data = [
            {"acreditador": 0, "nome": "Alimento de Origem Animal (MAPA)"},
            {"acreditador": 0, "nome": "Produto Lácteo (MAPA)"},
            {"acreditador": 1, "nome": "Produto de Origem Animal (IMA)"},
            {"acreditador": 2, "nome": "Água Potável (INMETRO)"},
        ]

        for item in data:
            record_id = self._generate_id()
            acreditador_id = self.ids["acreditadores"][item["acreditador"]]
            self.cursor.execute(
                """
                INSERT INTO classificacao (record_id, acreditador, nome)
                VALUES (?, ?, ?)
            """,
                (record_id, acreditador_id, item["nome"]),
            )
            self.ids["classificacao"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_tipos_amostra(self):
        """Popula tipos de amostra."""
        print("\n=== Populando Tipos de Amostra ===")
        data = [
            {
                "nome": "Lácteos",
                "classificacao": 1,
                "temperatura_padrao": 4.0,
            },
            {
                "nome": "Carnes",
                "classificacao": 2,
                "temperatura_padrao": -18.0,
            },
            {
                "nome": "Água",
                "classificacao": 3,
                "temperatura_padrao": 20.0,
            },
            {
                "nome": "Bebidas",
                "classificacao": 0,
                "temperatura_padrao": 5.0,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            classificacao_id = self.ids["classificacao"][item["classificacao"]]
            self.cursor.execute(
                """
                INSERT INTO tipo_amostra (record_id, nome, classificacao, temperatura_padrao)
                VALUES (?, ?, ?, ?)
            """,
                (record_id, item["nome"], classificacao_id, item["temperatura_padrao"]),
            )
            self.ids["tipo_amostra"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_amostras_especificas(self):
        """Popula amostras específicas (produtos reais)."""
        print("\n=== Populando Amostras Específicas ===")
        data = [
            {
                "tipo_amostra": 0,
                "nome": "Leite Integral Pasteurizado",
                "marca": "Bom Leite",
                "lote": "LT-2024-001",
                "validade": "2026-02-28",
            },
            {
                "tipo_amostra": 0,
                "nome": "Queijo Meia Cura",
                "marca": "Fazenda Serrana",
                "lote": "QJ-2024-002",
                "validade": "2026-06-15",
            },
            {
                "tipo_amostra": 1,
                "nome": "Carne Vermelha - Picanha",
                "marca": "Frigorífico Premium",
                "lote": "CV-2024-003",
                "validade": "2026-01-20",
            },
            {
                "tipo_amostra": 1,
                "nome": "Carne de Frango - Peito",
                "marca": "Frigorífico Premium",
                "lote": "CF-2024-004",
                "validade": "2026-01-25",
            },
            {
                "tipo_amostra": 2,
                "nome": "Água Filtrada - Poço Profundo",
                "marca": "ETA Municipal",
                "lote": "AG-2024-005",
                "validade": "2026-01-30",
            },
            {
                "tipo_amostra": 3,
                "nome": "Suco Natural - Laranja",
                "marca": "Distribuidora Centro-Oeste",
                "lote": "SC-2024-006",
                "validade": "2026-01-15",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            tipo_amostra_id = self.ids["tipo_amostra"][item["tipo_amostra"]]
            self.cursor.execute(
                """
                INSERT INTO amostra_especifica (record_id, tipo_amostra, nome, marca, lote, validade)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    tipo_amostra_id,
                    item["nome"],
                    item["marca"],
                    item["lote"],
                    item["validade"],
                ),
            )
            self.ids["amostra_especifica"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_analises(self):
        """Popula análises."""
        print("\n=== Populando Análises ===")
        data = [
            {
                "nome_oficial": "Acidez Titulável",
                "tipo": "fisico_quimica",
                "tem_parciais": True,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Coliformes Totais",
                "tipo": "microbiologica",
                "tem_parciais": False,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "pH",
                "tipo": "fisico_quimica",
                "tem_parciais": False,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Proteína Bruta",
                "tipo": "fisico_quimica",
                "tem_parciais": True,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Coliformes Fecais",
                "tipo": "microbiologica",
                "tem_parciais": False,
                "gera_complementar": True,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Gordura Bruta",
                "tipo": "fisico_quimica",
                "tem_parciais": False,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Umidade",
                "tipo": "fisico_quimica",
                "tem_parciais": False,
                "gera_complementar": False,
                "analise_complementar": None,
            },
            {
                "nome_oficial": "Cinzas Totais",
                "tipo": "fisico_quimica",
                "tem_parciais": False,
                "gera_complementar": False,
                "analise_complementar": None,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            self.cursor.execute(
                """
                INSERT INTO analises (record_id, nome_oficial, tipo, tem_parciais,
                                     gera_complementar, analise_complementar)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    item["nome_oficial"],
                    item["tipo"],
                    int(item["tem_parciais"]),
                    int(item["gera_complementar"]),
                    item["analise_complementar"],
                ),
            )
            self.ids["analises"].append(record_id)
            print(f"  - {item['nome_oficial']}")

        self.conn.commit()

    def populate_parciais(self):
        """Popula resultados parciais."""
        print("\n=== Populando Resultados Parciais ===")
        data = [
            {
                "analise": 0,  # Acidez Titulável
                "nome": "Volume de NaOH (mL)",
                "ordem": 1,
                "unidade": "mL",
                "formula": None,
            },
            {
                "analise": 0,
                "nome": "Fator de Correção",
                "ordem": 2,
                "unidade": None,
                "formula": None,
            },
            {
                "analise": 0,
                "nome": "Acidez Titulável",
                "ordem": 3,
                "unidade": "% ácido lático",
                "formula": "(V × f × N × 100) / m",
            },
            {
                "analise": 3,  # Proteína Bruta
                "nome": "Massa da Amostra (g)",
                "ordem": 1,
                "unidade": "g",
                "formula": None,
            },
            {
                "analise": 3,
                "nome": "Volume de HCl (mL)",
                "ordem": 2,
                "unidade": "mL",
                "formula": None,
            },
            {
                "analise": 3,
                "nome": "Proteína Bruta",
                "ordem": 3,
                "unidade": "% proteína",
                "formula": "(V × N × 1.4 × 100) / m",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            analise_id = self.ids["analises"][item["analise"]]
            self.cursor.execute(
                """
                INSERT INTO parciais (record_id, analise, nome, ordem, unidade, formula)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (record_id, analise_id, item["nome"], item["ordem"], item["unidade"], item["formula"]),
            )
            self.ids["parciais"].append(record_id)
            print(f"  - {item['nome']}")

        self.conn.commit()

    def populate_matrizes(self):
        """Popula matrizes (combinações Tipo Amostra + Análise + Metodologia)."""
        print("\n=== Populando Matrizes ===")
        data = [
            {
                "tipo_amostra": 0,  # Lácteos
                "analise": 0,  # Acidez Titulável
                "metodologia": 0,  # Método Clássico
                "padrao_referencia": "ISO 734-1",
                "valor": 150.00,
            },
            {
                "tipo_amostra": 0,
                "analise": 2,  # pH
                "metodologia": 2,
                "padrao_referencia": "ISO 10523",
                "valor": 100.00,
            },
            {
                "tipo_amostra": 1,  # Carnes
                "analise": 1,  # Coliformes
                "metodologia": 1,
                "padrao_referencia": "AOAC 990.12",
                "valor": 200.00,
            },
            {
                "tipo_amostra": 1,
                "analise": 3,  # Proteína Bruta
                "metodologia": 3,
                "padrao_referencia": "AOAC 984.13",
                "valor": 250.00,
            },
            {
                "tipo_amostra": 2,  # Água
                "analise": 1,  # Coliformes
                "metodologia": 1,
                "padrao_referencia": "AOAC 990.12",
                "valor": 180.00,
            },
            {
                "tipo_amostra": 2,
                "analise": 2,  # pH
                "metodologia": 2,
                "padrao_referencia": "ISO 10523",
                "valor": 80.00,
            },
            {
                "tipo_amostra": 3,  # Bebidas
                "analise": 0,  # Acidez Titulável
                "metodologia": 0,
                "padrao_referencia": "ISO 734-1",
                "valor": 140.00,
            },
            {
                "tipo_amostra": 3,
                "analise": 2,  # pH
                "metodologia": 2,
                "padrao_referencia": "ISO 10523",
                "valor": 90.00,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            tipo_amostra_id = self.ids["tipo_amostra"][item["tipo_amostra"]]
            analise_id = self.ids["analises"][item["analise"]]
            metodologia_id = self.ids["metodologias"][item["metodologia"]]
            self.cursor.execute(
                """
                INSERT INTO matriz (record_id, tipo_amostra, analise, metodologia,
                                   padrao_referencia, valor)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    tipo_amostra_id,
                    analise_id,
                    metodologia_id,
                    item["padrao_referencia"],
                    item["valor"],
                ),
            )
            self.ids["matriz"].append(record_id)
            print(f"  - Matriz {len(self.ids['matriz'])}")

        self.conn.commit()

    def populate_orcamentos(self):
        """Popula orçamentos."""
        print("\n=== Populando Orçamentos ===")
        data = [
            {
                "cliente": 0,  # Indústria de Laticínios Silva
                "acreditador": 0,  # MAPA
                "data": "2025-01-05",
                "qtd_amostras": 3,
                "urgente": False,
                "coleta": True,
                "taxa_coleta": 100.0,
                "desconto": 5.0,
                "observacoes": "Coleta em Belo Horizonte",
            },
            {
                "cliente": 1,  # Frigorífico
                "acreditador": 0,
                "data": "2025-01-06",
                "qtd_amostras": 4,
                "urgente": True,
                "coleta": False,
                "taxa_coleta": None,
                "desconto": 0.0,
                "observacoes": "Análise urgente de carne vermelha",
            },
            {
                "cliente": 2,  # Distribuidora
                "acreditador": 1,
                "data": "2025-01-07",
                "qtd_amostras": 2,
                "urgente": False,
                "coleta": False,
                "taxa_coleta": None,
                "desconto": 0.0,
                "observacoes": None,
            },
            {
                "cliente": 3,  # ETA Municipal
                "acreditador": 2,  # INMETRO
                "data": "2025-01-07",
                "qtd_amostras": 5,
                "urgente": False,
                "coleta": True,
                "taxa_coleta": 150.0,
                "desconto": 10.0,
                "observacoes": "Análise de água de consumo - coleta inclusa",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            cliente_id = self.ids["clientes"][item["cliente"]]
            acreditador_id = self.ids["acreditadores"][item["acreditador"]]
            self.cursor.execute(
                """
                INSERT INTO orcamento (record_id, cliente, acreditador, data, qtd_amostras,
                                      urgente, coleta, taxa_coleta, desconto, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    cliente_id,
                    acreditador_id,
                    item["data"],
                    item["qtd_amostras"],
                    int(item["urgente"]),
                    int(item["coleta"]),
                    item["taxa_coleta"],
                    item["desconto"],
                    item["observacoes"],
                ),
            )
            self.ids["orcamento"].append(record_id)
            print(f"  - Orçamento {len(self.ids['orcamento'])}")

        self.conn.commit()

    def populate_amostras(self):
        """Popula amostras (entrada no lab)."""
        print("\n=== Populando Amostras (Entrada no Lab) ===")
        data = [
            {
                "orcamento": 0,
                "amostra_especifica": 0,  # Leite Integral
                "data_entrada": "2025-01-05 09:30:00",
                "recebedor": 5,  # Lucia (Recepção)
                "temperatura": 4.0,
                "lacre": "L-2025-001",
                "lacre_ok": True,
                "quantidade": "1 litro",
                "anomalias": None,
            },
            {
                "orcamento": 0,
                "amostra_especifica": 1,  # Queijo
                "data_entrada": "2025-01-05 09:45:00",
                "recebedor": 5,
                "temperatura": 4.0,
                "lacre": "L-2025-002",
                "lacre_ok": True,
                "quantidade": "250g",
                "anomalias": None,
            },
            {
                "orcamento": 1,
                "amostra_especifica": 2,  # Carne Vermelha
                "data_entrada": "2025-01-06 11:00:00",
                "recebedor": 5,
                "temperatura": -18.0,
                "lacre": "L-2025-003",
                "lacre_ok": True,
                "quantidade": "300g",
                "anomalias": None,
            },
            {
                "orcamento": 3,
                "amostra_especifica": 4,  # Água
                "data_entrada": "2025-01-07 14:20:00",
                "recebedor": 5,
                "temperatura": 20.0,
                "lacre": "L-2025-004",
                "lacre_ok": True,
                "quantidade": "1 litro",
                "anomalias": None,
            },
        ]

        for item in data:
            record_id = self._generate_id()
            orcamento_id = self.ids["orcamento"][item["orcamento"]]
            amostra_especifica_id = self.ids["amostra_especifica"][item["amostra_especifica"]]
            recebedor_id = self.ids["funcionarios"][item["recebedor"]]
            self.cursor.execute(
                """
                INSERT INTO amostra (record_id, orcamento, amostra_especifica, data_entrada,
                                   recebedor, temperatura, lacre, lacre_ok, quantidade, anomalias)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    orcamento_id,
                    amostra_especifica_id,
                    item["data_entrada"],
                    recebedor_id,
                    item["temperatura"],
                    item["lacre"],
                    int(item["lacre_ok"]),
                    item["quantidade"],
                    item["anomalias"],
                ),
            )
            self.ids["amostra"].append(record_id)
            print(f"  - Amostra {len(self.ids['amostra'])}")

        self.conn.commit()

    def populate_fracionamentos(self):
        """Popula fracionamentos."""
        print("\n=== Populando Fracionamentos ===")
        data = [
            {
                "amostra": 0,
                "porcao": 1,
                "matriz": 0,  # Acidez em Lácteos
                "responsavel": 1,  # Maria (Analista)
                "data_hora": "2025-01-05 10:15:00",
            },
            {
                "amostra": 0,
                "porcao": 2,
                "matriz": 1,  # pH em Lácteos
                "responsavel": 2,  # Carlos (Analista)
                "data_hora": "2025-01-05 10:30:00",
            },
            {
                "amostra": 1,
                "porcao": 1,
                "matriz": 0,  # Acidez em Lácteos
                "responsavel": 1,
                "data_hora": "2025-01-05 11:00:00",
            },
            {
                "amostra": 2,
                "porcao": 1,
                "matriz": 2,  # Coliformes em Carnes
                "responsavel": 2,
                "data_hora": "2025-01-06 11:30:00",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            amostra_id = self.ids["amostra"][item["amostra"]]
            matriz_id = self.ids["matriz"][item["matriz"]]
            responsavel_id = self.ids["funcionarios"][item["responsavel"]]
            self.cursor.execute(
                """
                INSERT INTO fracionamento (record_id, amostra, porcao, matriz, responsavel, data_hora)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (record_id, amostra_id, item["porcao"], matriz_id, responsavel_id, item["data_hora"]),
            )
            self.ids["fracionamento"].append(record_id)
            print(f"  - Fracionamento {len(self.ids['fracionamento'])}")

        self.conn.commit()

    def populate_resultados(self):
        """Popula resultados."""
        print("\n=== Populando Resultados ===")
        data = [
            {
                "fracionamento": 0,
                "analista": 1,  # Maria
                "inicio": "2025-01-05 10:45:00",
                "termino": "2025-01-05 11:30:00",
                "valores_parciais": '{"volume_naoh": 5.2, "fator": 1.0}',
                "resultado_final": "0.364% ácido lático",
                "conformidade": "conforme",
                "observacoes": "Análise realizada sem incidentes",
            },
            {
                "fracionamento": 1,
                "analista": 2,  # Carlos
                "inicio": "2025-01-05 11:00:00",
                "termino": "2025-01-05 11:45:00",
                "valores_parciais": None,
                "resultado_final": "pH 6.8",
                "conformidade": "conforme",
                "observacoes": None,
            },
            {
                "fracionamento": 2,
                "analista": 1,
                "inicio": "2025-01-05 11:15:00",
                "termino": "2025-01-05 12:00:00",
                "valores_parciais": '{"volume_naoh": 4.8, "fator": 1.0}',
                "resultado_final": "0.336% ácido lático",
                "conformidade": "conforme",
                "observacoes": None,
            },
            {
                "fracionamento": 3,
                "analista": 7,  # Fernanda
                "inicio": "2025-01-06 12:00:00",
                "termino": "2025-01-06 14:30:00",
                "valores_parciais": None,
                "resultado_final": "<3 NMP/mL",
                "conformidade": "conforme",
                "observacoes": "Sem detecção de coliformes",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            fracionamento_id = self.ids["fracionamento"][item["fracionamento"]]
            analista_id = self.ids["funcionarios"][item["analista"]]
            self.cursor.execute(
                """
                INSERT INTO resultado (record_id, fracionamento, analista, inicio, termino,
                                      valores_parciais, resultado_final, conformidade, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record_id,
                    fracionamento_id,
                    analista_id,
                    item["inicio"],
                    item["termino"],
                    item["valores_parciais"],
                    item["resultado_final"],
                    item["conformidade"],
                    item["observacoes"],
                ),
            )
            self.ids["resultado"].append(record_id)
            print(f"  - Resultado {len(self.ids['resultado'])}")

        self.conn.commit()

    def populate_laudos(self):
        """Popula laudos."""
        print("\n=== Populando Laudos ===")
        data = [
            {
                "orcamento": 0,
                "numero": "LD-2025-001",
                "data_emissao": "2025-01-07",
                "rt": 0,  # João (RT)
                "parecer": "conforme",
                "observacoes": "Todas as análises conforme esperado",
            },
            {
                "orcamento": 1,
                "numero": "LD-2025-002",
                "data_emissao": "2025-01-07",
                "rt": 0,
                "parecer": "conforme",
                "observacoes": "Produto em condições apropriadas",
            },
            {
                "orcamento": 2,
                "numero": "LD-2025-003",
                "data_emissao": "2025-01-08",
                "rt": 0,
                "parecer": "conforme",
                "observacoes": None,
            },
            {
                "orcamento": 3,
                "numero": "LD-2025-004",
                "data_emissao": "2025-01-08",
                "rt": 0,
                "parecer": "conforme",
                "observacoes": "Água segura para consumo",
            },
        ]

        for item in data:
            record_id = self._generate_id()
            orcamento_id = self.ids["orcamento"][item["orcamento"]]
            rt_id = self.ids["funcionarios"][item["rt"]]
            self.cursor.execute(
                """
                INSERT INTO laudo (record_id, orcamento, numero, data_emissao, rt, parecer, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (record_id, orcamento_id, item["numero"], item["data_emissao"], rt_id, item["parecer"], item["observacoes"]),
            )
            self.ids["laudo"].append(record_id)
            print(f"  - Laudo {len(self.ids['laudo'])}")

        self.conn.commit()

    def print_summary(self):
        """Imprime resumo dos dados inseridos."""
        print("\n" + "=" * 60)
        print("RESUMO DA POPULAÇÃO DE DADOS")
        print("=" * 60)

        tables = [
            ("Acreditadores", "acreditadores"),
            ("Funcionários", "funcionarios"),
            ("Clientes", "clientes"),
            ("Metodologias", "metodologias"),
            ("Classificações", "classificacao"),
            ("Tipos de Amostra", "tipo_amostra"),
            ("Amostras Específicas", "amostra_especifica"),
            ("Análises", "analises"),
            ("Resultados Parciais", "parciais"),
            ("Matrizes", "matriz"),
            ("Orçamentos", "orcamento"),
            ("Amostras (Entrada)", "amostra"),
            ("Fracionamentos", "fracionamento"),
            ("Resultados", "resultado"),
            ("Laudos", "laudo"),
        ]

        for label, table_name in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = self.cursor.fetchone()[0]
            print(f"{label:.<40} {count:>3} registros")

        print("=" * 60)

    def run(self):
        """Executa todo o processo de população."""
        try:
            self.connect()
            self.create_tables()
            self.populate_acreditadores()
            self.populate_funcionarios()
            self.populate_clientes()
            self.populate_metodologias()
            self.populate_classificacoes()
            self.populate_tipos_amostra()
            self.populate_amostras_especificas()
            self.populate_analises()
            self.populate_parciais()
            self.populate_matrizes()
            self.populate_orcamentos()
            self.populate_amostras()
            self.populate_fracionamentos()
            self.populate_resultados()
            self.populate_laudos()
            self.print_summary()
            print("\nPopulação de dados concluída com sucesso!")
            return True
        except Exception as e:
            print(f"\nErro durante a população: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()


if __name__ == "__main__":
    populator = LIMSDataPopulator(DB_PATH)
    success = populator.run()
    sys.exit(0 if success else 1)
