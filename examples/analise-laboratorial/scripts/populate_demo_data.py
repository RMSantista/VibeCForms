#!/usr/bin/env python3
"""
Script para popular dados de demonstração realistas no sistema LIMS refatorado.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = 'examples/analise-laboratorial/data/sqlite/vibecforms.db'

def generate_record_id():
    """Gera um UUID para record_id."""
    return str(uuid.uuid4())

def populate_acreditadores(conn):
    """Popula tabela de acreditadores."""
    cursor = conn.cursor()
    acreditadores = [
        (generate_record_id(), 'MAPA', 'Ministério da Agricultura', 'oficial'),
        (generate_record_id(), 'IMA', 'Instituto Mineiro de Agropecuária', 'oficial'),
        (generate_record_id(), 'INMETRO', 'Instituto Nacional de Metrologia', 'oficial'),
    ]

    for record_id, sigla, nome, tipo_certificado in acreditadores:
        cursor.execute("""
            INSERT INTO acreditadores (record_id, sigla, nome, tipo_certificado)
            VALUES (?, ?, ?, ?)
        """, (record_id, sigla, nome, tipo_certificado))

    conn.commit()
    print("✅ 3 acreditadores populados")
    return acreditadores

def populate_funcionarios(conn):
    """Popula tabela de funcionários."""
    cursor = conn.cursor()
    funcionarios = [
        (generate_record_id(), 'João da Silva', 'rt', 'CRQ123456', 1),
        (generate_record_id(), 'Maria Santos', 'analista', 'CRQ654321', 1),
        (generate_record_id(), 'Pedro Oliveira', 'analista', 'CRQ789123', 1),
        (generate_record_id(), 'Ana Costa', 'supervisor', None, 1),
        (generate_record_id(), 'Carlos Mendes', 'coletor', None, 1),
        (generate_record_id(), 'Fernanda Silva', 'recepcao', None, 1),
        (generate_record_id(), 'Roberto Lima', 'analista', 'CRQ456789', 1),
        (generate_record_id(), 'Juliana Gomes', 'administrativo', None, 1),
    ]

    for record_id, nome, funcao, crq, ativo in funcionarios:
        cursor.execute("""
            INSERT INTO funcionarios (record_id, nome, funcao, crq, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, (record_id, nome, funcao, crq, ativo))

    conn.commit()
    print("✅ 8 funcionários populados")
    return funcionarios

def populate_clientes(conn):
    """Popula tabela de clientes."""
    cursor = conn.cursor()
    clientes = [
        (generate_record_id(), 'Indústria de Laticínios Silva', '12345678901234', 'silva@industria.com.br', '(31) 3333-4444', 'Rua A, 123', 'Belo Horizonte', 'MG', '30123-456', 5.0),
        (generate_record_id(), 'Frigorífico Central Brasil', '98765432109876', 'contato@frigocentral.com.br', '(31) 3333-5555', 'Avenida B, 456', 'Divinópolis', 'MG', '35123-789', 7.0),
        (generate_record_id(), 'Distribuidora de Água Pura', '11223344556677', 'vendas@aguapura.com.br', '(31) 3333-6666', 'Rua C, 789', 'Contagem', 'MG', '32123-000', 3.0),
        (generate_record_id(), 'Bebidas e Sucos Naturais', '55667788990011', 'comercial@bebidas.com.br', '(31) 3333-7777', 'Av. D, 321', 'Ipatinga', 'MG', '35164-123', 10.0),
    ]

    for record_id, nome, cpf_cnpj, email, telefone, endereco, cidade, uf, cep, desconto in clientes:
        cursor.execute("""
            INSERT INTO clientes (record_id, nome, cpf_cnpj, email, telefone, endereco, cidade, uf, cep, desconto_padrao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, nome, cpf_cnpj, email, telefone, endereco, cidade, uf, cep, desconto))

    conn.commit()
    print("✅ 4 clientes populados")
    return clientes

def populate_metodologias(conn):
    """Popula tabela de metodologias."""
    cursor = conn.cursor()
    metodologias = [
        (generate_record_id(), 'Contagem de Coliformes Totais', 'ISO 4832:2006', 'Norma ISO Internacional', '1.0'),
        (generate_record_id(), 'Determinação de pH', 'AOAC 981.12', 'Norma AOAC Oficial', '1.0'),
        (generate_record_id(), 'Acidez Titulável', 'AOAC 942.15', 'Titulação com NaOH 0,1N', '1.0'),
        (generate_record_id(), 'Determinação de Proteína Bruta', 'AOAC 920.87', 'Método de Kjeldahl', '2.0'),
    ]

    for record_id, nome, referencia, bibliografia, versao in metodologias:
        cursor.execute("""
            INSERT INTO metodologias (record_id, nome, referencia, bibliografia, versao)
            VALUES (?, ?, ?, ?, ?)
        """, (record_id, nome, referencia, bibliografia, versao))

    conn.commit()
    print("✅ 4 metodologias populadas")
    return metodologias

def populate_classificacao(conn, acreditadores):
    """Popula tabela de classificações."""
    cursor = conn.cursor()
    # Usando os record_ids dos acreditadores
    mapa_id = acreditadores[0][0]
    ima_id = acreditadores[1][0]

    classificacoes = [
        (generate_record_id(), mapa_id, 'Lácteos e Derivados'),
        (generate_record_id(), mapa_id, 'Carnes e Derivados'),
        (generate_record_id(), ima_id, 'Produtos de Origem Animal'),
        (generate_record_id(), ima_id, 'Água para Consumo'),
    ]

    for record_id, acreditador_id, nome in classificacoes:
        cursor.execute("""
            INSERT INTO classificacao (record_id, acreditador, nome)
            VALUES (?, ?, ?)
        """, (record_id, acreditador_id, nome))

    conn.commit()
    print("✅ 4 classificações populadas")
    return classificacoes

def populate_tipo_amostra(conn, classificacoes):
    """Popula tabela de tipos de amostra."""
    cursor = conn.cursor()

    tipos = [
        (generate_record_id(), 'Leite UHT', classificacoes[0][0], 4.0),
        (generate_record_id(), 'Linguiças', classificacoes[1][0], 2.0),
        (generate_record_id(), 'Água Mineral', classificacoes[3][0], 10.0),
        (generate_record_id(), 'Suco Natural', classificacoes[3][0], 8.0),
    ]

    for record_id, nome, classificacao_id, temp in tipos:
        cursor.execute("""
            INSERT INTO tipo_amostra (record_id, nome, classificacao, temperatura_padrao)
            VALUES (?, ?, ?, ?)
        """, (record_id, nome, classificacao_id, temp))

    conn.commit()
    print("✅ 4 tipos de amostra populados")
    return tipos

def populate_amostra_especifica(conn, tipos):
    """Popula tabela de amostras específicas."""
    cursor = conn.cursor()

    amostras = [
        (generate_record_id(), tipos[0][0], 'Leite Italac Integral 1L', 'Italac', 'LOTE001', datetime.now() + timedelta(days=30)),
        (generate_record_id(), tipos[1][0], 'Linguiça de Pernil Sadia 1kg', 'Sadia', 'LOTE002', datetime.now() + timedelta(days=15)),
        (generate_record_id(), tipos[2][0], 'Água Mineral Cristal 1,5L', 'Cristal', 'LOTE003', None),
        (generate_record_id(), tipos[3][0], 'Suco Natural Laranja 500mL', 'Natural', 'LOTE004', datetime.now() + timedelta(days=60)),
        (generate_record_id(), tipos[0][0], 'Leite Integral Italac 2L', 'Italac', 'LOTE005', datetime.now() + timedelta(days=30)),
        (generate_record_id(), tipos[1][0], 'Linguiça Toscana Sadia 500g', 'Sadia', 'LOTE006', datetime.now() + timedelta(days=15)),
    ]

    for record_id, tipo_id, nome, marca, lote, validade in amostras:
        cursor.execute("""
            INSERT INTO amostra_especifica (record_id, tipo_amostra, nome, marca, lote, validade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (record_id, tipo_id, nome, marca, lote, validade.date() if validade else None))

    conn.commit()
    print("✅ 6 amostras específicas populadas")
    return amostras

def populate_analises(conn):
    """Popula tabela de análises."""
    cursor = conn.cursor()

    analises = [
        (generate_record_id(), 'Coliformes Totais', 'microbiologica', 0, 0),
        (generate_record_id(), 'pH', 'fisico_quimica', 0, 0),
        (generate_record_id(), 'Acidez Titulável', 'fisico_quimica', 1, 0),
        (generate_record_id(), 'Proteína Bruta', 'fisico_quimica', 0, 0),
        (generate_record_id(), 'Gordura Total', 'fisico_quimica', 0, 0),
        (generate_record_id(), 'Umidade', 'fisico_quimica', 0, 0),
        (generate_record_id(), 'Salmonella', 'microbiologica', 0, 1),
        (generate_record_id(), 'E. coli', 'microbiologica', 0, 0),
    ]

    for record_id, nome, tipo, tem_parciais, gera_comp in analises:
        cursor.execute("""
            INSERT INTO analises (record_id, nome, tipo, tem_parciais, gera_complementar)
            VALUES (?, ?, ?, ?, ?)
        """, (record_id, nome, tipo, tem_parciais, gera_comp))

    conn.commit()
    print("✅ 8 análises populadas")
    return analises

def populate_parciais(conn, analises):
    """Popula tabela de parciais (resultados intermediários)."""
    cursor = conn.cursor()

    # Apenas para Acidez Titulável (analises[2])
    acidez_id = analises[2][0]

    parciais = [
        (generate_record_id(), acidez_id, 'Volume de NaOH (mL)', 1, None, 'mL'),
        (generate_record_id(), acidez_id, 'Fator de Correção', 2, None, None),
        (generate_record_id(), acidez_id, 'Normalidade da Solução', 3, None, 'N'),
    ]

    for record_id, analise_id, nome, ordem, formula, unidade in parciais:
        cursor.execute("""
            INSERT INTO parciais (record_id, analise, nome, ordem, formula, unidade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (record_id, analise_id, nome, ordem, formula, unidade))

    conn.commit()
    print("✅ 3 parciais populados")
    return parciais

def populate_matriz(conn, tipos, analises, metodologias):
    """Popula tabela de matriz."""
    cursor = conn.cursor()

    matrizes = [
        (generate_record_id(), tipos[0][0], analises[1][0], metodologias[1][0], 'Faixa: 6,4-6,8', 150.00),  # Leite - pH
        (generate_record_id(), tipos[0][0], analises[2][0], metodologias[2][0], 'Faixa: 14-18°D', 200.00),  # Leite - Acidez
        (generate_record_id(), tipos[1][0], analises[4][0], metodologias[3][0], 'Máx: 35%', 250.00),  # Linguiça - Gordura
        (generate_record_id(), tipos[2][0], analises[0][0], metodologias[0][0], 'Ausência', 180.00),  # Água - Coliformes
        (generate_record_id(), tipos[0][0], analises[3][0], metodologias[3][0], 'Mín: 3%', 220.00),  # Leite - Proteína
        (generate_record_id(), tipos[3][0], analises[1][0], metodologias[1][0], 'Faixa: 3,0-4,0', 170.00),  # Suco - pH
        (generate_record_id(), tipos[1][0], analises[0][0], metodologias[0][0], 'Máx: 10⁴ UFC', 200.00),  # Linguiça - Coliformes
        (generate_record_id(), tipos[2][0], analises[7][0], metodologias[0][0], 'Ausência', 180.00),  # Água - E. coli
    ]

    for record_id, tipo_id, analise_id, metodologia_id, padrao, valor in matrizes:
        cursor.execute("""
            INSERT INTO matriz (record_id, tipo_amostra, analise, metodologia, padrao_referencia, valor)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (record_id, tipo_id, analise_id, metodologia_id, padrao, valor))

    conn.commit()
    print("✅ 8 matrizes populadas")
    return matrizes

def populate_orcamento(conn, clientes, acreditadores):
    """Popula tabela de orçamentos."""
    cursor = conn.cursor()

    orcamentos = [
        (generate_record_id(), clientes[0][0], acreditadores[0][0], '2026-01-07', 3, 0, 0, 0, 'Análises solicitadas via telefone'),
        (generate_record_id(), clientes[1][0], acreditadores[0][0], '2026-01-06', 5, 0, 0, 5, 'Coleta incluída'),
        (generate_record_id(), clientes[2][0], acreditadores[2][0], '2026-01-05', 2, 1, 50.00, 0, 'Urgente - entrega em 2 dias'),
        (generate_record_id(), clientes[3][0], acreditadores[1][0], '2026-01-04', 4, 0, 0, 8, 'Cliente frequente'),
    ]

    for record_id, cliente_id, acreditador_id, data, qtd, urgente, taxa, desconto, obs in orcamentos:
        cursor.execute("""
            INSERT INTO orcamento (record_id, cliente, acreditador, data, qtd_amostras, urgente, coleta, taxa_coleta, desconto, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, cliente_id, acreditador_id, data, qtd, urgente, 1 if taxa else 0, taxa if taxa else None, desconto, obs))

    conn.commit()
    print("✅ 4 orçamentos populados")
    return orcamentos

def populate_amostra(conn, orcamentos, amostras, funcionarios):
    """Popula tabela de amostras (entrada no lab)."""
    cursor = conn.cursor()

    amostras_entrada = [
        (generate_record_id(), orcamentos[0][0], amostras[0][0], '2026-01-07 09:30', funcionarios[5][0], 4.0, 'LAC001', 1, '1 litro', None),
        (generate_record_id(), orcamentos[1][0], amostras[1][0], '2026-01-06 14:15', funcionarios[5][0], 2.0, 'LIN002', 1, '1 kg', None),
        (generate_record_id(), orcamentos[2][0], amostras[2][0], '2026-01-05 10:00', funcionarios[5][0], 10.0, 'AGU003', 1, '1,5 litros', None),
        (generate_record_id(), orcamentos[3][0], amostras[3][0], '2026-01-04 16:45', funcionarios[5][0], 8.0, 'SUC004', 1, '500 mL', 'Amostra com pequeno amassado na embalagem'),
    ]

    for record_id, orcamento_id, amostra_id, data, recebedor_id, temp, lacre, lacre_ok, qtd, anom in amostras_entrada:
        cursor.execute("""
            INSERT INTO amostra (record_id, orcamento, amostra_especifica, data_entrada, recebedor, temperatura, lacre, lacre_ok, quantidade, anomalias)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, orcamento_id, amostra_id, data, recebedor_id, temp, lacre, lacre_ok, qtd, anom))

    conn.commit()
    print("✅ 4 amostras (entrada) populadas")
    return amostras_entrada

def populate_fracionamento(conn, amostras_entrada, matrizes, funcionarios):
    """Popula tabela de fracionamento."""
    cursor = conn.cursor()

    fracionamentos = [
        (generate_record_id(), amostras_entrada[0][0], 1, matrizes[0][0], funcionarios[0][0], '2026-01-07 10:00'),
        (generate_record_id(), amostras_entrada[1][0], 1, matrizes[2][0], funcionarios[0][0], '2026-01-06 15:00'),
        (generate_record_id(), amostras_entrada[2][0], 1, matrizes[3][0], funcionarios[0][0], '2026-01-05 11:00'),
        (generate_record_id(), amostras_entrada[3][0], 1, matrizes[5][0], funcionarios[0][0], '2026-01-04 17:00'),
    ]

    for record_id, amostra_id, porcao, matriz_id, resp_id, data_hora in fracionamentos:
        cursor.execute("""
            INSERT INTO fracionamento (record_id, amostra, porcao, matriz, responsavel, data_hora)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (record_id, amostra_id, porcao, matriz_id, resp_id, data_hora))

    conn.commit()
    print("✅ 4 fracionamentos populados")
    return fracionamentos

def populate_resultado(conn, fracionamentos, funcionarios):
    """Popula tabela de resultados."""
    cursor = conn.cursor()

    resultados = [
        (generate_record_id(), fracionamentos[0][0], funcionarios[1][0], '2026-01-07 11:00', '2026-01-07 11:45', '{"volume": 1.5, "fator": 0.98}', '6.7°D', 'conforme', 'Conforme padrão'),
        (generate_record_id(), fracionamentos[1][0], funcionarios[1][0], '2026-01-06 16:00', '2026-01-06 17:30', None, '32%', 'conforme', None),
        (generate_record_id(), fracionamentos[2][0], funcionarios[2][0], '2026-01-05 12:00', '2026-01-05 13:00', None, 'Ausência', 'conforme', 'Coliformes não detectados'),
        (generate_record_id(), fracionamentos[3][0], funcionarios[2][0], '2026-01-04 18:00', '2026-01-04 19:00', None, 'pH 3.4', 'conforme', None),
    ]

    for record_id, fracao_id, analista_id, inicio, termino, parciais, resultado, conform, obs in resultados:
        cursor.execute("""
            INSERT INTO resultado (record_id, fracionamento, analista, inicio, termino, valores_parciais, resultado_final, conformidade, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, fracao_id, analista_id, inicio, termino, parciais, resultado, conform, obs))

    conn.commit()
    print("✅ 4 resultados populados")
    return resultados

def populate_laudo(conn, orcamentos, funcionarios):
    """Popula tabela de laudos."""
    cursor = conn.cursor()

    laudos = [
        (generate_record_id(), orcamentos[0][0], 'LAB/2026/001', '2026-01-07', funcionarios[0][0], 'conforme', 'Todas as análises conforme padrão'),
        (generate_record_id(), orcamentos[1][0], 'LAB/2026/002', '2026-01-06', funcionarios[0][0], 'conforme', 'Produto conforme especificações'),
        (generate_record_id(), orcamentos[2][0], 'LAB/2026/003', '2026-01-05', funcionarios[0][0], 'conforme', 'Água própria para consumo'),
        (generate_record_id(), orcamentos[3][0], 'LAB/2026/004', '2026-01-04', funcionarios[0][0], 'conforme', 'Suco dentro dos padrões de qualidade'),
    ]

    for record_id, orcamento_id, numero, data, rt_id, parecer, obs in laudos:
        cursor.execute("""
            INSERT INTO laudo (record_id, orcamento, numero, data_emissao, rt, parecer, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (record_id, orcamento_id, numero, data, rt_id, parecer, obs))

    conn.commit()
    print("✅ 4 laudos populados")
    return laudos

def main():
    """Executa população de dados."""
    print("\n" + "="*60)
    print("POPULAÇÃO DE DADOS DE DEMONSTRAÇÃO - LIMS REFATORADO")
    print("="*60 + "\n")

    conn = sqlite3.connect(DB_PATH)

    try:
        # Ordem importa para respeitar relacionamentos
        acreditadores = populate_acreditadores(conn)
        funcionarios = populate_funcionarios(conn)
        clientes = populate_clientes(conn)
        metodologias = populate_metodologias(conn)
        classificacoes = populate_classificacao(conn, acreditadores)
        tipos = populate_tipo_amostra(conn, classificacoes)
        amostras_especificas = populate_amostra_especifica(conn, tipos)
        analises = populate_analises(conn)
        parciais = populate_parciais(conn, analises)
        matrizes = populate_matriz(conn, tipos, analises, metodologias)
        orcamentos = populate_orcamento(conn, clientes, acreditadores)
        amostras_entrada = populate_amostra(conn, orcamentos, amostras_especificas, funcionarios)
        fracionamentos = populate_fracionamento(conn, amostras_entrada, matrizes, funcionarios)
        resultados = populate_resultado(conn, fracionamentos, funcionarios)
        laudos = populate_laudo(conn, orcamentos, funcionarios)

        print("\n" + "="*60)
        print("✅ POPULAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\nResumo:")
        print("  • 3 Acreditadores")
        print("  • 8 Funcionários")
        print("  • 4 Clientes")
        print("  • 4 Metodologias")
        print("  • 4 Classificações")
        print("  • 4 Tipos de Amostra")
        print("  • 6 Amostras Específicas")
        print("  • 8 Análises")
        print("  • 3 Resultados Parciais")
        print("  • 8 Matrizes")
        print("  • 4 Orçamentos")
        print("  • 4 Amostras (Entrada)")
        print("  • 4 Fracionamentos")
        print("  • 4 Resultados")
        print("  • 4 Laudos")
        print("\n")

    except Exception as e:
        print(f"\n❌ Erro durante população: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
