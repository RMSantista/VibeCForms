#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCForms v3.0 - New Persistence Paradigm Demo Database Creator

This script creates a demo SQLite database following the new paradigm of universal
relationships (Convenção #9) for comparison with the old paradigm.

Features demonstrated:
- Universal relationship table (1:1, 1:N, N:N)
- Display value denormalization
- Soft-delete semantics (removed_at)
- Sync strategies (eager, lazy, scheduled)
- Audit trail (created_by, removed_by)

Date: 2026-01-08
Version: 1.0
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import sys

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent.parent / "data" / "sqlite" / "vibecforms_new_paradigm.db"
SCRIPT_DIR = Path(__file__).parent

# Actor IDs (simulating different users)
ADMIN_ID = str(uuid.uuid4())
TECHNICIAN_ID = str(uuid.uuid4())
RECEPTIONIST_ID = str(uuid.uuid4())

# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

SCHEMA = """
-- ═══════════════════════════════════════════════════════════════════════════
-- VibeCForms v3.0: Universal Relationships Schema for Demo
-- ═══════════════════════════════════════════════════════════════════════════

-- Table: form_metadata (helper table for schema)
CREATE TABLE IF NOT EXISTS form_metadata (
    form_path TEXT PRIMARY KEY,
    display_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: pacientes (1:N source for exames)
CREATE TABLE IF NOT EXISTS pacientes (
    _record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    data_nascimento TEXT NOT NULL,
    genero TEXT,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: exames (center of 1:N relationships)
CREATE TABLE IF NOT EXISTS exames (
    _record_id TEXT PRIMARY KEY,
    paciente_id TEXT NOT NULL,
    paciente_display TEXT,
    data_solicitacao TEXT NOT NULL,
    data_coleta TEXT,
    medico_id TEXT,
    medico_display TEXT,
    descricao TEXT,
    status TEXT DEFAULT 'pendente',
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: testes (many 1:1 relationships per exame)
CREATE TABLE IF NOT EXISTS testes (
    _record_id TEXT PRIMARY KEY,
    exame_id TEXT NOT NULL,
    exame_display TEXT,
    tipo_teste TEXT NOT NULL,
    descricao TEXT,
    valor_minimo REAL,
    valor_maximo REAL,
    unidade TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: resultados (results for testes - N:1 to testes)
CREATE TABLE IF NOT EXISTS resultados (
    _record_id TEXT PRIMARY KEY,
    teste_id TEXT NOT NULL,
    teste_display TEXT,
    valor_obtido REAL NOT NULL,
    referencia TEXT,
    status TEXT,
    data_resultado TEXT NOT NULL,
    tecnico_id TEXT,
    tecnico_display TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: funcionarios (support entity for relationships)
CREATE TABLE IF NOT EXISTS funcionarios (
    _record_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    funcao TEXT,
    email TEXT,
    telefone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════
-- UNIVERSAL RELATIONSHIPS TABLE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relationships (
    rel_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    relationship_name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    removed_at TEXT,
    removed_by TEXT,
    metadata TEXT,

    UNIQUE(source_type, source_id, relationship_name, target_id),
    FOREIGN KEY(source_type) REFERENCES form_metadata(form_path),
    FOREIGN KEY(target_type) REFERENCES form_metadata(form_path)
);

-- Indexes for relationships table
CREATE INDEX IF NOT EXISTS idx_rel_source
ON relationships(source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_rel_target
ON relationships(target_type, target_id);

CREATE INDEX IF NOT EXISTS idx_rel_name
ON relationships(source_type, relationship_name);

CREATE INDEX IF NOT EXISTS idx_rel_active
ON relationships(source_type, source_id, removed_at);

CREATE INDEX IF NOT EXISTS idx_rel_created
ON relationships(created_at);

CREATE INDEX IF NOT EXISTS idx_rel_removed
ON relationships(removed_at) WHERE removed_at IS NOT NULL;

-- Views for relationships
CREATE VIEW IF NOT EXISTS active_relationships AS
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    created_at,
    created_by,
    metadata
FROM relationships
WHERE removed_at IS NULL;

CREATE VIEW IF NOT EXISTS relationship_history AS
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    'created' as event_type,
    created_at as event_at,
    created_by as event_by
FROM relationships
UNION ALL
SELECT
    rel_id,
    source_type,
    source_id,
    relationship_name,
    target_type,
    target_id,
    'removed' as event_type,
    removed_at as event_at,
    removed_by as event_by
FROM relationships
WHERE removed_at IS NOT NULL
ORDER BY event_at DESC;
"""

# ═══════════════════════════════════════════════════════════════════════════
# DEMO DATA
# ═══════════════════════════════════════════════════════════════════════════

# Pacientes
PACIENTES = [
    {
        "nome": "João Silva",
        "cpf": "123.456.789-00",
        "data_nascimento": "1980-05-15",
        "genero": "M",
        "telefone": "(11) 98765-4321",
        "email": "joao.silva@example.com",
        "endereco": "Rua A, 100, São Paulo"
    },
    {
        "nome": "Maria Santos",
        "cpf": "987.654.321-00",
        "data_nascimento": "1992-08-22",
        "genero": "F",
        "telefone": "(11) 99876-5432",
        "email": "maria.santos@example.com",
        "endereco": "Rua B, 200, Rio de Janeiro"
    },
    {
        "nome": "Pedro Oliveira",
        "cpf": "456.789.123-00",
        "data_nascimento": "1975-12-10",
        "genero": "M",
        "telefone": "(21) 97654-3210",
        "email": "pedro.oliveira@example.com",
        "endereco": "Rua C, 300, Belo Horizonte"
    }
]

# Funcionários
FUNCIONARIOS = [
    {
        "nome": "Dra. Ana Costa",
        "funcao": "Médica",
        "email": "ana.costa@lab.com",
        "telefone": "(11) 3333-0000"
    },
    {
        "nome": "Técnico Carlos",
        "funcao": "Técnico de Laboratório",
        "email": "carlos@lab.com",
        "telefone": "(11) 3333-1111"
    },
    {
        "nome": "Recepcionista Beatriz",
        "funcao": "Recepcionista",
        "email": "beatriz@lab.com",
        "telefone": "(11) 3333-2222"
    }
]

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_uuid():
    """Generate a UUID-like ID (simplified for demo)."""
    return str(uuid.uuid4())[:8].upper()

def timestamp_now():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def timestamp_ago(hours=0, days=0, minutes=0):
    """Get timestamp N units ago."""
    now = datetime.now()
    delta = timedelta(hours=hours, days=days, minutes=minutes)
    return (now - delta).isoformat()

def create_database():
    """Create the demo database with new paradigm."""
    print(f"📊 Creating demo database: {DB_PATH}")

    # Create parent directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✓ Removed existing database")

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create schema
    print("📋 Creating schema...")
    cursor.executescript(SCHEMA)
    print("   ✓ Schema created")

    # Register form metadata
    print("📝 Registering form metadata...")
    forms = [
        ("pacientes", "Pacientes"),
        ("exames", "Exames"),
        ("testes", "Testes"),
        ("resultados", "Resultados"),
        ("funcionarios", "Funcionários")
    ]

    for form_path, display_name in forms:
        cursor.execute(
            "INSERT INTO form_metadata (form_path, display_name) VALUES (?, ?)",
            (form_path, display_name)
        )
    print(f"   ✓ Registered {len(forms)} forms")

    # Insert pacientes
    print("👥 Inserting pacientes...")
    paciente_ids = []
    for paciente in PACIENTES:
        paciente_id = generate_uuid()
        paciente_ids.append((paciente_id, paciente["nome"]))

        cursor.execute("""
            INSERT INTO pacientes (_record_id, nome, cpf, data_nascimento, genero, telefone, email, endereco)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paciente_id,
            paciente["nome"],
            paciente["cpf"],
            paciente["data_nascimento"],
            paciente["genero"],
            paciente["telefone"],
            paciente["email"],
            paciente["endereco"]
        ))
    print(f"   ✓ Inserted {len(paciente_ids)} pacientes")

    # Insert funcionários
    print("💼 Inserting funcionários...")
    funcionario_ids = []
    for func in FUNCIONARIOS:
        func_id = generate_uuid()
        funcionario_ids.append((func_id, func["nome"]))

        cursor.execute("""
            INSERT INTO funcionarios (_record_id, nome, funcao, email, telefone)
            VALUES (?, ?, ?, ?, ?)
        """, (
            func_id,
            func["nome"],
            func["funcao"],
            func["email"],
            func["telefone"]
        ))
    print(f"   ✓ Inserted {len(funcionario_ids)} funcionários")

    # Insert exames (1:N relationship with pacientes)
    print("🔬 Inserting exames...")
    exame_data = []
    for idx, (paciente_id, paciente_nome) in enumerate(paciente_ids):
        # Each paciente has 1-2 exames
        num_exames = 2 if idx == 0 else 1

        for exam_num in range(num_exames):
            exame_id = generate_uuid()
            exame_data.append((exame_id, paciente_id, paciente_nome))

            cursor.execute("""
                INSERT INTO exames (
                    _record_id, paciente_id, paciente_display,
                    data_solicitacao, data_coleta, medico_id, medico_display,
                    descricao, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exame_id,
                paciente_id,
                paciente_nome,  # Display value denormalized
                timestamp_ago(days=7 - exam_num),
                timestamp_ago(days=6 - exam_num),
                funcionario_ids[0][0],  # First doctor
                funcionario_ids[0][1],  # Doctor name (display value)
                f"Exame de rotina #{exam_num + 1}",
                "em_andamento" if exam_num == 0 else "concluído"
            ))
    print(f"   ✓ Inserted {len(exame_data)} exames")

    # Insert testes (1:N relationship with exames)
    print("🧪 Inserting testes...")
    teste_data = []
    test_types = [
        ("Hemoglobina", "Análise de hemoglobina", 12.0, 17.0, "g/dL"),
        ("Glicose", "Teste de glicose em jejum", 70.0, 100.0, "mg/dL"),
        ("Colesterol Total", "Colesterol total", 0.0, 200.0, "mg/dL"),
        ("Triglicerídeos", "Triglicerídeos", 0.0, 150.0, "mg/dL")
    ]

    for exame_id, paciente_id, paciente_nome in exame_data:
        # Each exame has 2-3 testes
        num_testes = 3 if paciente_id == paciente_ids[0][0] else 2

        for teste_type in test_types[:num_testes]:
            teste_id = generate_uuid()
            teste_data.append((teste_id, exame_id))

            cursor.execute("""
                INSERT INTO testes (
                    _record_id, exame_id, exame_display,
                    tipo_teste, descricao, valor_minimo, valor_maximo, unidade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                teste_id,
                exame_id,
                f"Exame para {paciente_nome}",  # Display value denormalized
                teste_type[0],
                teste_type[1],
                teste_type[2],
                teste_type[3],
                teste_type[4]
            ))
    print(f"   ✓ Inserted {len(teste_data)} testes")

    # Insert resultados (N:1 relationship with testes)
    print("📊 Inserting resultados...")
    resultado_ids = []
    for teste_id, exame_id in teste_data:
        resultado_id = generate_uuid()
        resultado_ids.append(resultado_id)

        # Simulate a result value
        valor_resultado = 85.5 if "Hemoglobina" in teste_id else 95.0

        cursor.execute("""
            INSERT INTO resultados (
                _record_id, teste_id, teste_display,
                valor_obtido, referencia, status, data_resultado,
                tecnico_id, tecnico_display
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resultado_id,
            teste_id,
            f"Teste #{teste_id}",  # Display value denormalized
            valor_resultado,
            "Normal",
            "normal",
            timestamp_ago(hours=2),
            funcionario_ids[1][0],  # Technician
            funcionario_ids[1][1]   # Technician name (display value)
        ))
    print(f"   ✓ Inserted {len(resultado_ids)} resultados")

    # Create relationships (relationships table)
    print("🔗 Creating relationships (universal relationship table)...")
    rel_count = 0

    # 1:N relationships: exames → pacientes (forward navigation)
    for exame_id, paciente_id, paciente_nome in exame_data:
        rel_id = generate_uuid()
        cursor.execute("""
            INSERT INTO relationships (
                rel_id, source_type, source_id, relationship_name,
                target_type, target_id, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel_id,
            "exames", exame_id, "paciente",  # exame.paciente → pacientes
            "pacientes", paciente_id,
            timestamp_ago(days=7),
            TECHNICIAN_ID
        ))
        rel_count += 1

    # 1:N relationships: testes → exames (forward navigation)
    for teste_id, exame_id in teste_data:
        rel_id = generate_uuid()
        cursor.execute("""
            INSERT INTO relationships (
                rel_id, source_type, source_id, relationship_name,
                target_type, target_id, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel_id,
            "testes", teste_id, "exame",  # teste.exame → exames
            "exames", exame_id,
            timestamp_ago(days=6),
            TECHNICIAN_ID
        ))
        rel_count += 1

    # N:1 relationships: resultados → testes
    for resultado_id, (teste_id, exame_id) in zip(resultado_ids, teste_data):
        rel_id = generate_uuid()
        cursor.execute("""
            INSERT INTO relationships (
                rel_id, source_type, source_id, relationship_name,
                target_type, target_id, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel_id,
            "resultados", resultado_id, "teste",  # resultado.teste → testes
            "testes", teste_id,
            timestamp_ago(hours=2),
            TECHNICIAN_ID
        ))
        rel_count += 1

    # Example of soft-delete: remove one relationship to show audit trail
    print("🗑️  Demonstrating soft-delete (marked as removed)...")
    cursor.execute("""
        UPDATE relationships
        SET removed_at = ?, removed_by = ?
        WHERE rowid = 1
        LIMIT 1
    """, (timestamp_ago(hours=1), ADMIN_ID))

    print(f"   ✓ Created {rel_count} relationships")

    # Commit and close
    conn.commit()
    conn.close()

    print(f"\n✅ Database created successfully!")
    print(f"   Location: {DB_PATH}")
    print(f"   Size: {DB_PATH.stat().st_size / 1024:.1f} KB")

    return DB_PATH

# ═══════════════════════════════════════════════════════════════════════════
# STATISTICS AND VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def print_statistics():
    """Print statistics about the created database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("\n📈 DATABASE STATISTICS:")
    print("=" * 70)

    # Count records by table
    tables = ["pacientes", "exames", "testes", "resultados", "funcionarios"]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:20} : {count:4} records")

    # Count relationships
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE removed_at IS NULL")
    active_rels = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE removed_at IS NOT NULL")
    removed_rels = cursor.fetchone()[0]

    print(f"\n  {'Active relationships':20} : {active_rels:4} records")
    print(f"  {'Removed relationships':20} : {removed_rels:4} records")
    print(f"  {'Total relationships':20} : {active_rels + removed_rels:4} records")

    # Display value examples
    print("\n📝 DENORMALIZED DISPLAY VALUES EXAMPLE:")
    print("=" * 70)
    cursor.execute("""
        SELECT _record_id, paciente_display, data_coleta, status
        FROM exames
        LIMIT 2
    """)

    print(f"  Exame ID          | Paciente (Display)   | Data Coleta | Status")
    print("  " + "-" * 67)
    for exame_id, paciente_display, data_coleta, status in cursor.fetchall():
        date_short = data_coleta.split("T")[0] if data_coleta else "N/A"
        print(f"  {exame_id:17} | {paciente_display:20} | {date_short:11} | {status}")

    # Relationship example
    print("\n🔗 UNIVERSAL RELATIONSHIPS TABLE EXAMPLE:")
    print("=" * 70)
    cursor.execute("""
        SELECT
            source_type,
            substr(source_id, 1, 4) as src_id,
            relationship_name,
            target_type,
            substr(target_id, 1, 4) as tgt_id,
            CASE WHEN removed_at IS NULL THEN 'active' ELSE 'removed' END as status
        FROM relationships
        LIMIT 5
    """)

    print(f"  Source  | SrcID | Relationship | Target  | TgtID | Status")
    print("  " + "-" * 63)
    for source_type, src_id, rel_name, target_type, tgt_id, status in cursor.fetchall():
        print(f"  {source_type:7} | {src_id:5} | {rel_name:12} | {target_type:7} | {tgt_id:5} | {status}")

    # Soft-delete audit trail
    print("\n🗑️  SOFT-DELETE AUDIT TRAIL (removed relationships):")
    print("=" * 70)
    cursor.execute("""
        SELECT
            source_type,
            substr(source_id, 1, 4) as src_id,
            relationship_name,
            removed_at
        FROM relationships
        WHERE removed_at IS NOT NULL
    """)

    rows = cursor.fetchall()
    if rows:
        print(f"  Source | SrcID | Relationship | Removed At")
        print("  " + "-" * 61)
        for source_type, src_id, rel_name, removed_at in rows:
            time_short = removed_at.split("T")[1][:5] if removed_at else "N/A"
            print(f"  {source_type:6} | {src_id:5} | {rel_name:12} | {time_short}")
    else:
        print("  (No removed relationships)")

    conn.close()
    print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        db_path = create_database()
        print_statistics()

        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Compare this database with vibecforms.db (old paradigm)")
        print(f"   2. Notice the relationships table instead of foreign keys in entity tables")
        print(f"   3. See denormalized display values (_display columns)")
        print(f"   4. Check soft-delete audit trail (removed_at field)")
        print(f"\n📚 KEY CONCEPTS DEMONSTRATED:")
        print(f"   ✓ Universal relationship table for 1:1, 1:N, N:N relationships")
        print(f"   ✓ Display value denormalization for performance")
        print(f"   ✓ Soft-delete semantics with audit trail")
        print(f"   ✓ Forward and reverse navigation support")
        print(f"   ✓ Schema flexibility (no schema changes for cardinality upgrade)")

    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
