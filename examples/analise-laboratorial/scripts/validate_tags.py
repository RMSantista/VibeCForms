#!/usr/bin/env python3
"""
Script de validacao para a tabela tags do sistema LIMS.
Verifica integridade, cobertura de estados e distribuicao de registros.
"""

import sqlite3
from pathlib import Path
import sys


def get_db_path():
    """Retorna o caminho do banco de dados LIMS."""
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "data" / "sqlite" / "lims.db"
    return db_path


def check_table_exists(conn):
    """Verifica se tabela tags existe."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
    )
    return cursor.fetchone() is not None


def validate_tags(conn):
    """Valida integridade e cobertura das tags."""
    cursor = conn.cursor()

    # Verificacoes esperadas
    expected_workflows = {
        "orcamento": {"rascunho", "enviado", "aprovado", "em_andamento"},
        "amostra": {"aguardando", "recebida", "fracionada"},
        "resultado": {"aguardando", "em_execucao", "concluida"},
        "laudo": {"rascunho", "revisao", "liberado", "entregue"},
    }

    issues = []
    coverage = {}

    for workflow, expected_tags in expected_workflows.items():
        cursor.execute(
            """SELECT DISTINCT tag FROM tags WHERE object_name = ?
               ORDER BY tag""",
            (workflow,)
        )
        existing_tags = {row[0] for row in cursor.fetchall()}
        coverage[workflow] = existing_tags

        # Verificar se todos os estados estao presentes
        missing = expected_tags - existing_tags
        extra = existing_tags - expected_tags

        if missing:
            issues.append(f"{workflow}: FALTAM estados: {missing}")
        if extra:
            issues.append(f"{workflow}: ESTADOS EXTRAS: {extra}")

        # Verificar count de registros
        cursor.execute(
            "SELECT COUNT(*) FROM tags WHERE object_name = ?",
            (workflow,)
        )
        count = cursor.fetchone()[0]
        if count < 4:
            issues.append(f"{workflow}: APENAS {count} registros (esperado >= 4)")

    return issues, coverage


def print_report(conn):
    """Imprime relatorio completo de validacao."""
    print("\n" + "=" * 70)
    print("RELATORIO DE VALIDACAO - TAGS KANBAN")
    print("=" * 70)

    if not check_table_exists(conn):
        print("X TABELA 'tags' NAO EXISTE!")
        return False

    print("✓ Tabela 'tags' existe")

    cursor = conn.cursor()

    # Total de tags
    cursor.execute("SELECT COUNT(*) FROM tags")
    total = cursor.fetchone()[0]
    print(f"✓ Total de tags: {total}")

    # Validacao de integridade
    issues, coverage = validate_tags(conn)

    if not issues:
        print("✓ Todos os workflows possuem cobertura de estados!")
    else:
        print("\nAVISOS:")
        for issue in issues:
            print(f"  ! {issue}")

    # Detalhamento por workflow
    print("\nDETALHES POR WORKFLOW:")
    print("-" * 70)

    for workflow in sorted(coverage.keys()):
        tags = coverage[workflow]
        cursor.execute(
            "SELECT COUNT(*) FROM tags WHERE object_name = ?",
            (workflow,)
        )
        count = cursor.fetchone()[0]
        print(f"\n{workflow.upper()}")
        print(f"  Registros: {count}")
        print(f"  Estados: {', '.join(sorted(tags))}")

        # Distribuicao de tags
        cursor.execute(
            """SELECT tag, COUNT(*) as qty FROM tags 
               WHERE object_name = ? GROUP BY tag ORDER BY tag""",
            (workflow,)
        )
        print("  Distribuicao:")
        for tag, qty in cursor.fetchall():
            print(f"    - {tag:20} : {qty} registro(s)")

    # Verificar registros orfaos (com IDs inconsistentes)
    print("\n" + "-" * 70)
    print("VERIFICACAO DE CONSISTENCIA:")
    cursor.execute(
        """SELECT object_name, object_id, COUNT(*) as qty FROM tags
           GROUP BY object_name, object_id ORDER BY object_name, object_id"""
    )
    print("\nRegistros por entidade:")
    current_name = None
    for object_name, object_id, qty in cursor.fetchall():
        if current_name != object_name:
            current_name = object_name
            print(f"\n{object_name}:")
        print(f"  {object_id}: {qty} tag(s)")

    print("\n" + "=" * 70)
    return not issues


def main():
    """Funcao principal."""
    db_path = get_db_path()

    print(f"Validando tags do sistema LIMS")
    print(f"Banco de dados: {db_path}\n")

    if not db_path.exists():
        print(f"X Banco de dados nao encontrado: {db_path}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(str(db_path))
        success = print_report(conn)
        conn.close()

        sys.exit(0 if success else 1)

    except sqlite3.Error as e:
        print(f"X Erro ao acessar banco: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
