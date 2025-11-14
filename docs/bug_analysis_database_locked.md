# Análise: SQLite Database Locked Error (Branch add-uuids)

**Data:** 2025-11-13
**Branch Afetada:** `add-uuids`
**Severidade:** 🔴 Alta
**Status:** Identificado - Aguardando Correção

---

## 📋 Sumário Executivo

Erro crítico de `sqlite3.OperationalError: database is locked` ocorre ao tentar inserir registros na branch `add-uuids`. O problema é causado por **resource leak** (conexão SQLite não fechada) quando exceções ocorrem durante operações de escrita.

**Impacto:**
- ❌ Cadastro de novos registros falha
- ❌ Banco de dados fica bloqueado
- ❌ Requer reinício do servidor para recuperar
- ✅ Branch `main` aparenta funcionar melhor (mas também possui o bug)

---

## 🔍 Detalhes do Erro

### Stack Trace

```
OperationalError
sqlite3.OperationalError: database is locked

Traceback (most recent call last):
  File "/home/rodrigo/VibeCForms/src/VibeCForms.py", line 687, in index
    record_id = repo.create(form_name, spec, form_data)

  File "/home/rodrigo/VibeCForms/src/persistence/adapters/sqlite_adapter.py", line 305, in create
    cursor.execute(insert_sql, values)

sqlite3.OperationalError: database is locked
```

### Arquivo Afetado

- **Path:** `src/persistence/adapters/sqlite_adapter.py`
- **Método:** `create()`
- **Linhas:** 302-314

---

## 🐛 Causa Raiz

### Problema 1: Resource Leak (Connection Não Fechada)

```python
# ❌ CÓDIGO PROBLEMÁTICO (add-uuids - linhas 302-314)
try:
    conn = self._get_connection()           # 1. Abre conexão
    cursor = conn.cursor()
    cursor.execute(insert_sql, values)      # 2. Se der erro AQUI...
    conn.commit()                            # 3. ...ou AQUI...
    conn.close()                             # 4. Esta linha NÃO executa!

    logger.debug(f"Inserted record {record_id} into {table_name}")
    return record_id

except Exception as e:
    logger.error(f"Failed to insert into {table_name}: {e}")
    raise  # 5. Propaga exceção SEM fechar conexão! 🐛
```

**Fluxo do Bug:**
1. Método abre conexão SQLite (`conn = self._get_connection()`)
2. Ocorre erro durante `cursor.execute()` ou `conn.commit()`
3. Controle pula para o bloco `except`
4. `conn.close()` nunca é executado → **conexão vaza**
5. Transação fica pendente → SQLite bloqueia o arquivo `.db`
6. Próximas tentativas de escrita encontram banco **locked** 🔒
7. Aplicação torna-se inutilizável até reiniciar

### Problema 2: Diferença Entre Main e add-uuids

**Por que main aparenta funcionar melhor?**

| Aspecto | Branch `main` | Branch `add-uuids` |
|---------|---------------|-------------------|
| **Retorno** | `bool` (True/False) | `str` (record_id UUID) |
| **Tratamento erro** | `return False` | `raise Exception` |
| **Visibilidade** | Bug menos visível | Bug muito visível |
| **Impacto** | Menor (retorna False) | Maior (exceção não tratada) |

**Código na main (linhas 238-250):**
```python
try:
    conn = self._get_connection()
    cursor = conn.cursor()
    cursor.execute(insert_sql, values)
    conn.commit()
    conn.close()  # ← Também não fecha se der erro!

    logger.debug(f"Inserted record into {table_name}")
    return True

except Exception as e:
    logger.error(f"Failed to insert into {table_name}: {e}")
    return False  # ← Retorna False em vez de raise
```

**Conclusão:** Ambas as branches têm o bug, mas em `main` ele é menos visível porque retorna `False` em vez de propagar a exceção.

---

## 🔬 Análise Técnica

### Como SQLite Gerencia Locks

**SQLite Database Locking:**
1. **Unlocked:** Nenhuma conexão ativa
2. **Shared:** Múltiplas leituras simultâneas permitidas
3. **Reserved:** Uma transação de escrita preparando
4. **Pending:** Aguardando locks compartilhados liberarem
5. **Exclusive:** Escrevendo no banco (bloqueia tudo)

**Problema no Código:**
- Conexão abre com transação implícita
- Erro ocorre durante transação
- Conexão não é fechada → transação não finaliza
- SQLite mantém lock **Exclusive** ou **Reserved**
- Novas conexões ficam esperando → **timeout → "database is locked"**

### Arquivos Envolvidos no Lock

```bash
src/
├── vibecforms.db          # Banco principal
├── vibecforms.db-shm      # Shared Memory (WAL mode)
└── vibecforms.db-wal      # Write-Ahead Log (WAL mode)
```

Se houver conexões pendentes, os arquivos `-shm` e `-wal` impedem acesso.

---

## ✅ Soluções Propostas

### Solução 1: Try/Finally (⭐ Recomendada)

**Garantir que conexão sempre fecha, com ou sem erro:**

```python
def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> str:
    """Insert a new record into the table with generated UUID.

    Returns:
        str: The generated UUID for the new record
    """
    table_name = self._get_table_name(form_path)

    if not self.exists(form_path):
        self.create_storage(form_path, spec)

    # Generate UUID
    record_id = crockford.generate_id()

    # Build INSERT statement including id column
    columns = ["id"] + [field["name"] for field in spec["fields"]]
    placeholders = ", ".join(["?" for _ in columns])
    columns_str = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

    # Build values list starting with UUID
    values = [record_id]
    for field in spec["fields"]:
        field_name = field["name"]
        field_type = field["type"]
        value = data.get(field_name, "")

        # Convert based on field type
        if field_type == "checkbox":
            values.append(1 if value else 0)
        elif field_type == "number" or field_type == "range":
            try:
                values.append(int(value) if value else 0)
            except ValueError:
                values.append(0)
        else:
            values.append(str(value) if value else "")

    conn = None
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(insert_sql, values)
        conn.commit()

        logger.debug(f"Inserted record {record_id} into {table_name}")
        return record_id

    except Exception as e:
        if conn:
            conn.rollback()  # ← Rollback transação em caso de erro
        logger.error(f"Failed to insert into {table_name}: {e}")
        raise

    finally:
        if conn:
            conn.close()  # ← SEMPRE fecha, com ou sem erro!
```

**Vantagens:**
- ✅ Conexão sempre fechada (garante limpeza de recursos)
- ✅ Rollback explícito em caso de erro
- ✅ Simples de entender e manter
- ✅ Padrão amplamente usado

---

### Solução 2: Context Manager (Alternativa Elegante)

**Implementar context manager para gestão automática:**

```python
from contextlib import contextmanager

class SQLiteRepository(BaseRepository):
    # ... código existente ...

    @contextmanager
    def get_connection(self):
        """Context manager for database connections.

        Ensures proper connection cleanup and transaction management.
        """
        conn = sqlite3.connect(
            self.database,
            timeout=self.timeout,
            check_same_thread=self.check_same_thread
        )
        conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()  # Auto-commit se sucesso
        except Exception:
            conn.rollback()  # Auto-rollback se erro
            raise
        finally:
            conn.close()  # Sempre fecha

    def create(self, form_path: str, spec: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Insert a new record into the table with generated UUID."""
        table_name = self._get_table_name(form_path)

        if not self.exists(form_path):
            self.create_storage(form_path, spec)

        record_id = crockford.generate_id()

        # Build INSERT statement
        columns = ["id"] + [field["name"] for field in spec["fields"]]
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Build values
        values = [record_id]
        for field in spec["fields"]:
            field_name = field["name"]
            field_type = field["type"]
            value = data.get(field_name, "")

            if field_type == "checkbox":
                values.append(1 if value else 0)
            elif field_type == "number" or field_type == "range":
                try:
                    values.append(int(value) if value else 0)
                except ValueError:
                    values.append(0)
            else:
                values.append(str(value) if value else "")

        # Use context manager - commit/close automáticos!
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)

        logger.debug(f"Inserted record {record_id} into {table_name}")
        return record_id
```

**Vantagens:**
- ✅ Código mais limpo e pythônico
- ✅ Gestão automática de commit/rollback/close
- ✅ Reutilizável em todos os métodos
- ✅ Menos código repetitivo
- ✅ Menor chance de esquecer de fechar conexão

---

### Solução 3: WAL Mode (Complementar)

**Habilitar Write-Ahead Logging para melhor concorrência:**

```python
def __init__(self, config: Dict[str, Any]):
    """Initialize SQLite repository adapter."""
    self.database = config.get("database", "src/vibecforms.db")
    self.timeout = config.get("timeout", 10)
    self.check_same_thread = config.get("check_same_thread", False)

    # Ensure database directory exists
    db_dir = os.path.dirname(self.database)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)

    # ✅ ADICIONAR: Habilita WAL mode para melhor concorrência
    try:
        conn = self._get_connection()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 segundos
        conn.close()
        logger.info("SQLite WAL mode enabled")
    except Exception as e:
        logger.warning(f"Failed to enable WAL mode: {e}")

    logger.info(f"SQLiteRepository initialized: database={self.database}")
```

**Benefícios do WAL:**
- ✅ Permite leituras durante escritas (concorrência)
- ✅ Melhor performance para múltiplas transações
- ✅ Reduz chance de locks
- ✅ Checkpoint automático gerenciado pelo SQLite
- ✅ Padrão recomendado para aplicações web

**PRAGMAs Úteis:**
```sql
PRAGMA journal_mode=WAL;        -- Habilita WAL
PRAGMA busy_timeout=30000;      -- Timeout de 30s
PRAGMA synchronous=NORMAL;      -- Balance performance/safety
PRAGMA cache_size=-64000;       -- Cache de 64MB
```

---

### Solução 4: Aumentar Timeout (Paliativo)

**No `__init__`, aumentar timeout padrão:**

```python
def __init__(self, config: Dict[str, Any]):
    self.database = config.get("database", "src/vibecforms.db")
    self.timeout = config.get("timeout", 30)  # ← 10 → 30 segundos
    self.check_same_thread = config.get("check_same_thread", False)
    # ...
```

**Atenção:** Isto é apenas um paliativo, não resolve o problema raiz!

---

## 🎯 Plano de Ação Recomendado

### Fase 1: Correção Urgente (add-uuids)

**Prioridade:** 🔴 Crítica

1. ✅ **Implementar Solução 1** (try/finally) no método `create()`
2. ✅ **Implementar Solução 3** (WAL mode) no `__init__`
3. ✅ **Testar** cadastro de múltiplos registros
4. ✅ **Commitar** correção na branch `add-uuids`

### Fase 2: Correção Preventiva (add-uuids)

**Prioridade:** 🟡 Alta

Aplicar try/finally em TODOS os métodos que usam conexão:

- [ ] `update()` (linha 316)
- [ ] `update_by_id()` (linha 382)
- [ ] `delete()` (linha 445)
- [ ] `delete_by_id()` (linha 476)
- [ ] `read_all()` (linha 160)
- [ ] `read_one()` (linha 205)
- [ ] `read_by_id()` (linha 219)
- [ ] `id_exists()` (linha 510)
- [ ] `exists()` (linha 559)
- [ ] `has_data()` (linha 579)
- [ ] `create_storage()` (linha 121)
- [ ] `drop_storage()` (linha 532)
- [ ] `migrate_schema()` (linha 599)

### Fase 3: Refatoração (add-uuids)

**Prioridade:** 🟢 Média

1. ✅ **Implementar Solução 2** (context manager)
2. ✅ **Refatorar** todos os métodos para usar context manager
3. ✅ **Adicionar testes** de concorrência
4. ✅ **Documentar** boas práticas

### Fase 4: Backport (main)

**Prioridade:** 🟡 Alta

1. ✅ Aplicar mesmas correções na branch `main`
2. ✅ Garantir zero regressão
3. ✅ Atualizar testes

---

## 🔧 Workarounds Temporários

Enquanto não aplica a correção:

### 1. Reiniciar Servidor

```bash
# Matar processo Flask
pkill -f "hatch run dev"

# Reiniciar
uv run hatch run dev
```

### 2. Limpar Arquivos de Lock

```bash
cd /home/rodrigo/VibeCForms/src
rm -f vibecforms.db-shm vibecforms.db-wal
```

**Atenção:** Só faça isso com servidor parado!

### 3. Usar Backend TXT Temporariamente

Editar `src/config/persistence.json`:

```json
{
  "default_backend": "txt",
  "backends": { ... }
}
```

### 4. Deletar e Recriar Banco

```bash
cd /home/rodrigo/VibeCForms/src
mv vibecforms.db vibecforms.db.backup
# Servidor recria automaticamente na próxima operação
```

---

## 📊 Comparação: Main vs add-uuids

| Aspecto | main | add-uuids |
|---------|------|-----------|
| **Método create()** | Retorna `bool` | Retorna `str` (UUID) |
| **IDs nos registros** | ❌ Não (usa índice) | ✅ Sim (Crockford Base32) |
| **Tratamento de erro** | `return False` | `raise Exception` |
| **Bug de resource leak** | ✅ Presente | ✅ Presente |
| **Visibilidade do bug** | 🟡 Baixa | 🔴 Alta |
| **Impacto operacional** | 🟢 Menor | 🔴 Maior |
| **Necessita correção?** | ✅ Sim | ✅ Sim (urgente) |

---

## 📝 Testes para Validar Correção

### Teste 1: Cadastro Simples

```python
def test_create_record():
    """Testa inserção básica."""
    repo = SQLiteRepository(config)

    data = {"nome": "João", "email": "joao@example.com"}
    record_id = repo.create("contatos", spec, data)

    assert record_id is not None
    assert len(record_id) == 27  # Crockford Base32
```

### Teste 2: Erro Forçado

```python
def test_create_record_with_error():
    """Testa que conexão é fechada mesmo com erro."""
    repo = SQLiteRepository(config)

    # Dados inválidos que causarão erro
    data = {"email": "invalid"}  # Falta campo required

    with pytest.raises(Exception):
        repo.create("contatos", spec, data)

    # Deve conseguir inserir novamente (conexão foi fechada)
    valid_data = {"nome": "Maria", "email": "maria@example.com"}
    record_id = repo.create("contatos", spec, valid_data)
    assert record_id is not None
```

### Teste 3: Concorrência

```python
import threading

def test_concurrent_inserts():
    """Testa múltiplas inserções simultâneas."""
    repo = SQLiteRepository(config)
    results = []

    def insert_record(i):
        data = {"nome": f"User{i}", "email": f"user{i}@example.com"}
        try:
            record_id = repo.create("contatos", spec, data)
            results.append(("success", record_id))
        except Exception as e:
            results.append(("error", str(e)))

    # Cria 10 threads inserindo simultaneamente
    threads = [threading.Thread(target=insert_record, args=(i,)) for i in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Todas devem ter sucesso
    successes = [r for r in results if r[0] == "success"]
    assert len(successes) == 10
```

---

## 🔗 Referências

### Documentação SQLite

- [SQLite Locking](https://www.sqlite.org/lockingv3.html)
- [Write-Ahead Logging](https://www.sqlite.org/wal.html)
- [PRAGMA Statements](https://www.sqlite.org/pragma.html)

### Python sqlite3

- [sqlite3 Module](https://docs.python.org/3/library/sqlite3.html)
- [Context Managers](https://docs.python.org/3/library/contextlib.html)
- [PEP 343 - with Statement](https://peps.python.org/pep-0343/)

### Arquivos do Projeto

- `src/persistence/adapters/sqlite_adapter.py` (Arquivo com bug)
- `src/utils/crockford.py` (Geração de UUIDs)
- `docs/crockford_ids.md` (Documentação sobre IDs)
- `task-tag-as-state.md` (Filosofia da branch add-uuids)

---

## 📌 Conclusão

O erro `database is locked` na branch `add-uuids` é causado por **resource leak** - conexões SQLite não são fechadas quando exceções ocorrem. A branch `main` tem o mesmo bug, mas é menos visível devido ao tratamento diferente de erros.

**Correção Recomendada:**
1. Implementar **try/finally** em todos os métodos (Solução 1)
2. Habilitar **WAL mode** no inicializador (Solução 3)
3. Refatorar para **context manager** futuramente (Solução 2)

**Impacto da Correção:**
- ✅ Elimina locks no banco de dados
- ✅ Permite cadastros funcionarem consistentemente
- ✅ Melhora robustez e confiabilidade
- ✅ Facilita concorrência no futuro

---

**Próximo Passo:** Aplicar Solução 1 + Solução 3 na branch `add-uuids`
