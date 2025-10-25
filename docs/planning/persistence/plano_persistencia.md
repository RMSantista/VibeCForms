# Plano: Sistema de Persistência Plugável - VibeCForms v3.0

**Data de Criação:** Outubro 2025
**Status:** Planejamento Aprovado
**Versão Alvo:** 3.0.0
**Estimativa:** 14 dias (MVP em 3 dias)

---

## 🎯 Objetivo

Implementar um sistema de persistência de dados abstrato e plugável que permita escolher entre múltiplos backends (txt, SQLite, MySQL, PostgreSQL, NoSQL, CSV, JSON, XML, etc.) sem alterar a lógica da aplicação.

## 📊 Análise da Arquitetura Atual

### Acoplamento Direto

A implementação atual está fortemente acoplada a arquivos .txt:

**Funções Atuais:**
- `read_forms(spec, data_file)` → linhas 202-239 de VibeCForms.py
- `write_forms(forms, spec, data_file)` → linhas 242-257 de VibeCForms.py
- `get_data_file(form_path)` → linhas 35-43 de VibeCForms.py

**Características:**
- Delimitador hardcoded: `;`
- Arquivos .txt nomeados como `{form_path}.txt`
- Conversão manual de tipos (checkbox → "True"/"False")
- Sem abstração entre lógica e persistência

**Arquivos de Dados Existentes:**
```
src/contatos.txt
src/produtos.txt
src/financeiro_contas.txt
src/rh_departamentos_areas.txt
```

## 🏗️ Arquitetura Proposta

### Padrões de Design

1. **Repository Pattern** - Interface única para todos os backends
2. **Adapter Pattern** - Cada backend tem seu adapter específico
3. **Factory Pattern** - Cria repositórios baseado em configuração
4. **Strategy Pattern** - Permite trocar estratégia de persistência em runtime

### Estrutura de Diretórios

```
src/
├── persistence/
│   ├── __init__.py
│   ├── base.py                 # BaseRepository (classe abstrata)
│   ├── factory.py              # RepositoryFactory
│   ├── config.py               # PersistenceConfig
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── txt_adapter.py      # TxtRepository (migração do atual)
│   │   ├── sqlite_adapter.py   # SQLiteRepository (Fase 1)
│   │   ├── mysql_adapter.py    # MySQLRepository (Fase 2)
│   │   ├── postgres_adapter.py # PostgresRepository (Fase 2)
│   │   ├── csv_adapter.py      # CSVRepository (Fase 3)
│   │   └── json_adapter.py     # JSONRepository (Fase 3)
│   └── migrations/
│       ├── __init__.py
│       └── migrator.py         # Migração de schemas
├── config/
│   └── persistence.json        # Configuração de persistência
├── VibeCForms.py
└── ...
```

## 📝 Interface BaseRepository

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseRepository(ABC):
    """
    Interface base para todos os adapters de persistência.
    Cada backend (txt, SQLite, MySQL, etc.) implementa esta interface.
    """

    @abstractmethod
    def create_storage(self, form_path: str, spec: Dict) -> bool:
        """
        Cria tabela/arquivo/collection para o formulário.

        Args:
            form_path: Caminho do formulário (ex: 'financeiro/contas')
            spec: Especificação do formulário (JSON)

        Returns:
            True se criado com sucesso, False caso já exista
        """
        pass

    @abstractmethod
    def read_all(self, form_path: str, spec: Dict) -> List[Dict]:
        """
        Lê todos os registros do formulário.

        Args:
            form_path: Caminho do formulário
            spec: Especificação do formulário

        Returns:
            Lista de dicionários com os dados
        """
        pass

    @abstractmethod
    def read_one(self, form_path: str, spec: Dict, idx: int) -> Optional[Dict]:
        """
        Lê um registro específico pelo índice.

        Args:
            form_path: Caminho do formulário
            spec: Especificação do formulário
            idx: Índice do registro (0-based)

        Returns:
            Dicionário com os dados ou None se não encontrado
        """
        pass

    @abstractmethod
    def create(self, form_path: str, spec: Dict, data: Dict) -> bool:
        """
        Insere novo registro.

        Args:
            form_path: Caminho do formulário
            spec: Especificação do formulário
            data: Dados a serem inseridos

        Returns:
            True se inserido com sucesso
        """
        pass

    @abstractmethod
    def update(self, form_path: str, spec: Dict, idx: int, data: Dict) -> bool:
        """
        Atualiza registro existente.

        Args:
            form_path: Caminho do formulário
            spec: Especificação do formulário
            idx: Índice do registro a atualizar
            data: Novos dados

        Returns:
            True se atualizado com sucesso
        """
        pass

    @abstractmethod
    def delete(self, form_path: str, spec: Dict, idx: int) -> bool:
        """
        Deleta registro.

        Args:
            form_path: Caminho do formulário
            spec: Especificação do formulário
            idx: Índice do registro a deletar

        Returns:
            True se deletado com sucesso
        """
        pass

    @abstractmethod
    def drop_storage(self, form_path: str, force: bool = False) -> bool:
        """
        Remove tabela/arquivo completamente.
        Se houver dados e force=False, deve retornar False.

        Args:
            form_path: Caminho do formulário
            force: Se True, remove sem confirmação mesmo com dados

        Returns:
            True se removido, False se cancelado (tem dados e não force)
        """
        pass

    @abstractmethod
    def exists(self, form_path: str) -> bool:
        """
        Verifica se o storage existe.

        Args:
            form_path: Caminho do formulário

        Returns:
            True se existe
        """
        pass

    @abstractmethod
    def has_data(self, form_path: str) -> bool:
        """
        Verifica se há dados no storage.

        Args:
            form_path: Caminho do formulário

        Returns:
            True se há pelo menos um registro
        """
        pass

    @abstractmethod
    def migrate_schema(self, form_path: str, old_spec: Dict, new_spec: Dict) -> bool:
        """
        Migra schema quando a especificação do formulário muda.
        Deve preservar dados existentes quando possível.

        Args:
            form_path: Caminho do formulário
            old_spec: Especificação antiga
            new_spec: Especificação nova

        Returns:
            True se migrado com sucesso
        """
        pass

    @abstractmethod
    def create_index(self, form_path: str, field_name: str) -> bool:
        """
        Cria índice em um campo específico para melhorar performance.

        Args:
            form_path: Caminho do formulário
            field_name: Nome do campo a indexar

        Returns:
            True se criado com sucesso
        """
        pass
```

## 📦 Arquivo de Configuração

**src/config/persistence.json:**

```json
{
  "version": "1.0",
  "default_backend": "txt",

  "backends": {
    "txt": {
      "type": "txt",
      "path": "src/",
      "delimiter": ";",
      "encoding": "utf-8",
      "extension": ".txt"
    },

    "sqlite": {
      "type": "sqlite",
      "database": "src/vibecforms.db",
      "timeout": 10,
      "check_same_thread": false
    },

    "mysql": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "vibecforms",
      "user": "root",
      "password": "${MYSQL_PASSWORD}",
      "charset": "utf8mb4",
      "pool_size": 5
    },

    "postgres": {
      "type": "postgres",
      "host": "localhost",
      "port": 5432,
      "database": "vibecforms",
      "user": "postgres",
      "password": "${POSTGRES_PASSWORD}",
      "schema": "public",
      "pool_size": 5
    },

    "mongodb": {
      "type": "mongodb",
      "host": "localhost",
      "port": 27017,
      "database": "vibecforms",
      "user": "",
      "password": "${MONGO_PASSWORD}"
    },

    "csv": {
      "type": "csv",
      "path": "src/data/csv/",
      "delimiter": ",",
      "encoding": "utf-8",
      "quoting": "minimal"
    },

    "json": {
      "type": "json",
      "path": "src/data/json/",
      "encoding": "utf-8",
      "indent": 2
    },

    "xml": {
      "type": "xml",
      "path": "src/data/xml/",
      "encoding": "utf-8",
      "pretty_print": true
    }
  },

  "form_mappings": {
    "contatos": "txt",
    "produtos": "txt",
    "usuarios": "sqlite",
    "financeiro/*": "mysql",
    "rh/*": "postgres",
    "*": "default_backend"
  },

  "auto_create_storage": true,
  "auto_migrate_schema": true,
  "backup_before_migrate": true,
  "backup_path": "src/backups/"
}
```

### Formato do Spec com Persistência

```json
{
  "title": "Cadastro de Usuários",
  "icon": "fa-user-plus",
  "persistence": {
    "backend": "sqlite",
    "table_name": "usuarios",
    "indexes": ["email", "data_nascimento"]
  },
  "fields": [
    {
      "name": "nome",
      "label": "Nome Completo",
      "type": "text",
      "required": true,
      "indexed": false
    },
    {
      "name": "email",
      "label": "E-mail",
      "type": "email",
      "required": true,
      "indexed": true,
      "unique": true
    },
    {
      "name": "senha",
      "label": "Senha",
      "type": "password",
      "required": true,
      "encrypted": true
    },
    {
      "name": "data_nascimento",
      "label": "Data de Nascimento",
      "type": "date",
      "required": true,
      "indexed": true
    }
  ],
  "validation_messages": {
    "all_empty": "Preencha todos os campos obrigatórios.",
    "nome": "O nome completo é obrigatório.",
    "email": "O e-mail é obrigatório.",
    "senha": "A senha é obrigatória.",
    "data_nascimento": "A data de nascimento é obrigatória."
  }
}
```

## 🎯 Fases de Implementação

### **Fase 1: Fundação e SQLite** ⭐ (Prioridade Máxima)

**Duração Estimada:** 2-3 dias
**Objetivo:** MVP funcional com SQLite

#### 1.1 Criar Estrutura Base (4 horas)

**Arquivos a criar:**
- `src/persistence/__init__.py`
- `src/persistence/base.py` - Classe abstrata `BaseRepository`
- `src/persistence/factory.py` - `RepositoryFactory`
- `src/persistence/config.py` - `PersistenceConfig`
- `src/persistence/adapters/__init__.py`
- `src/config/persistence.json`

**Tarefas:**
1. Implementar `BaseRepository` com todos os métodos abstratos
2. Implementar `PersistenceConfig` para ler persistence.json
3. Implementar `RepositoryFactory.get_repository(form_path)`
4. Adicionar validação de configuração
5. Adicionar logging

#### 1.2 Migrar TXT para Adapter (3 horas)

**Arquivo a criar:**
- `src/persistence/adapters/txt_adapter.py`

**Tarefas:**
1. Copiar lógica de `read_forms()` e `write_forms()` atuais
2. Implementar toda interface `BaseRepository`
3. Manter 100% compatibilidade com formato atual
4. Adicionar método `migrate_schema()` (apenas adiciona campos no final)
5. Testes para garantir zero regressão

#### 1.3 Implementar SQLiteRepository (6 horas)

**Arquivo a criar:**
- `src/persistence/adapters/sqlite_adapter.py`

**Tarefas:**
1. Implementar `create_storage()`:
   - Mapear tipos: text→TEXT, number→INTEGER, checkbox→BOOLEAN, date→DATE, password→TEXT
   - Criar tabela com campos do spec
   - Adicionar coluna `id` como INTEGER PRIMARY KEY AUTOINCREMENT

2. Implementar `read_all()`:
   - SELECT * FROM {table}
   - Converter tipos de volta para Python
   - Retornar lista de dicts

3. Implementar `create()`:
   - INSERT INTO com prepared statements
   - Validar dados antes de inserir

4. Implementar `update()`:
   - UPDATE WHERE id = ?
   - Usar prepared statements

5. Implementar `delete()`:
   - DELETE WHERE id = ?

6. Implementar `create_index()`:
   - CREATE INDEX IF NOT EXISTS

7. Implementar `migrate_schema()`:
   - ALTER TABLE ADD COLUMN para novos campos
   - Backup automático antes

**Mapeamento de Tipos:**
| Spec Type | SQLite Type | Python Type |
|-----------|-------------|-------------|
| text      | TEXT        | str         |
| tel       | TEXT        | str         |
| email     | TEXT        | str         |
| password  | TEXT        | str         |
| number    | INTEGER     | int         |
| date      | DATE        | str         |
| checkbox  | BOOLEAN     | bool        |
| textarea  | TEXT        | str         |

#### 1.4 Integrar Factory no VibeCForms.py (3 horas)

**Alterações em VibeCForms.py:**

```python
# ANTES (linhas 202-257)
def read_forms(spec, data_file):
    if not os.path.exists(data_file):
        return []
    # ... lógica de arquivo txt ...

def write_forms(forms, spec, data_file):
    with open(data_file, "w", encoding="utf-8") as f:
        # ... lógica de arquivo txt ...

# DEPOIS
from persistence.factory import RepositoryFactory

def read_forms(spec, form_path):
    """Read forms using configured persistence backend."""
    repo = RepositoryFactory.get_repository(form_path)
    if not repo.exists(form_path):
        repo.create_storage(form_path, spec)
    return repo.read_all(form_path, spec)

def write_forms(forms, spec, form_path):
    """Write forms using configured persistence backend."""
    repo = RepositoryFactory.get_repository(form_path)
    if not repo.exists(form_path):
        repo.create_storage(form_path, spec)

    # Limpar todos os registros existentes
    current = repo.read_all(form_path, spec)
    for i in range(len(current)):
        repo.delete(form_path, spec, 0)  # Sempre deleta o primeiro

    # Inserir novos
    for form_data in forms:
        repo.create(form_path, spec, form_data)
```

**Alterações em rotas:**
```python
# Substituir todas as chamadas:
# read_forms(spec, data_file) → read_forms(spec, form_name)
# write_forms(forms, spec, data_file) → write_forms(forms, spec, form_name)
```

#### 1.5 Testes (4 horas)

**Arquivos de teste:**
- `tests/test_txt_repository.py`
- `tests/test_sqlite_repository.py`
- `tests/test_persistence_factory.py`
- `tests/test_migration.py`

**Casos de teste:**
1. TXT Repository:
   - test_create_storage()
   - test_crud_operations()
   - test_backward_compatibility()

2. SQLite Repository:
   - test_create_storage_creates_table()
   - test_insert_and_read()
   - test_update_record()
   - test_delete_record()
   - test_field_type_conversion()
   - test_indexes_creation()

3. Factory:
   - test_factory_returns_correct_adapter()
   - test_form_mapping_wildcards()

4. Integration:
   - test_all_16_original_tests_still_pass()

**Entregáveis Fase 1:**
- ✅ Estrutura base do sistema de persistência
- ✅ TXT adapter (código atual migrado)
- ✅ SQLite adapter completo e funcional
- ✅ Factory pattern implementado
- ✅ Configuração via JSON
- ✅ Todos os 16 testes originais passando
- ✅ +15 novos testes para SQLite
- ✅ Documentação básica

---

### **Fase 2: Bancos Relacionais Remotos**

**Duração Estimada:** 3-4 dias
**Objetivo:** Suporte a MySQL e PostgreSQL com acesso remoto

#### 2.1 MySQLRepository (1 dia)

**Arquivo a criar:**
- `src/persistence/adapters/mysql_adapter.py`

**Dependências:**
```toml
mysql = ["pymysql>=1.1.0", "cryptography>=41.0.0"]
```

**Tarefas:**
1. Implementar adapter usando PyMySQL
2. Pool de conexões (usando `sqlalchemy.pool`)
3. Suporte a charset utf8mb4
4. Transaction management
5. Tratamento de erros de conexão
6. Retry logic para falhas temporárias

**Tipos MySQL:**
| Spec Type | MySQL Type     |
|-----------|----------------|
| text      | VARCHAR(255)   |
| tel       | VARCHAR(20)    |
| email     | VARCHAR(255)   |
| password  | VARCHAR(255)   |
| number    | INT            |
| date      | DATE           |
| checkbox  | BOOLEAN        |
| textarea  | TEXT           |

#### 2.2 PostgresRepository (1 dia)

**Arquivo a criar:**
- `src/persistence/adapters/postgres_adapter.py`

**Dependências:**
```toml
postgres = ["psycopg2-binary>=2.9.9"]
```

**Tarefas:**
1. Implementar adapter usando psycopg2
2. Suporte a schemas
3. JSONB para campos complexos (futuro)
4. Arrays para checkboxes múltiplos (futuro)
5. Full-text search indexes

#### 2.3 Sistema de Migração Avançado (2 dias)

**Arquivo a criar:**
- `src/persistence/migrations/migrator.py`
- `src/persistence/migrations/schema_diff.py`
- `src/persistence/migrations/backup.py`

**Tarefas:**

**Detecção de Mudanças:**
```python
class SchemaDiff:
    def compare_specs(old_spec, new_spec):
        return {
            'added_fields': [],
            'removed_fields': [],
            'modified_fields': [],
            'renamed_fields': []
        }
```

**Tipos de Migration:**
1. **ADD COLUMN** - Novos campos
   - Adiciona com valor default baseado no tipo
   - text/email/tel → ""
   - number → 0
   - checkbox → False
   - date → NULL

2. **ALTER COLUMN** - Mudança de tipo
   - Tenta conversão automática
   - Se falhar, avisa usuário

3. **DROP COLUMN** - Remoção de campo
   - Requer confirmação se houver dados
   - Backup automático antes

4. **RENAME COLUMN** - Renomeação
   - Detecta por heurística (similaridade de nome)
   - Pede confirmação ao usuário

**Backup Automático:**
```python
class BackupManager:
    def backup(form_path, spec):
        """
        Cria backup em src/backups/{form_path}_{timestamp}.json
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/{form_path}_{timestamp}.json"
        # Salva todos os dados em JSON
```

**Entregáveis Fase 2:**
- ✅ MySQL adapter completo
- ✅ PostgreSQL adapter completo
- ✅ Sistema de migrations robusto
- ✅ Backup automático funcionando
- ✅ Detecção de mudanças de schema
- ✅ Testes de integração para cada DB
- ✅ Documentação de migrations

---

### **Fase 3: Formatos de Arquivo Alternativos**

**Duração Estimada:** 2 dias
**Objetivo:** Suporte a CSV, JSON, XML

#### 3.1 CSVRepository (4 horas)

**Arquivo a criar:**
- `src/persistence/adapters/csv_adapter.py`

**Tarefas:**
1. Headers automáticos dos nomes de campos
2. Encoding configurável (utf-8, latin1, etc.)
3. Delimitadores configuráveis (`,`, `;`, `\t`)
4. Quoting modes (minimal, all, non-numeric)
5. Escape de caracteres especiais

**Formato:**
```csv
nome,email,senha,data_nascimento,ativo
"João Silva","joao@email.com","hash123","1990-01-15","True"
"Maria Santos","maria@email.com","hash456","1985-05-20","False"
```

#### 3.2 JSONRepository (3 horas)

**Arquivo a criar:**
- `src/persistence/adapters/json_adapter.py`

**Tarefas:**
1. Um arquivo JSON por formulário
2. Array de objetos
3. Pretty print configurável
4. Atomic writes (escreve em temp, depois move)

**Formato:**
```json
[
  {
    "nome": "João Silva",
    "email": "joao@email.com",
    "senha": "hash123",
    "data_nascimento": "1990-01-15",
    "ativo": true
  },
  {
    "nome": "Maria Santos",
    "email": "maria@email.com",
    "senha": "hash456",
    "data_nascimento": "1985-05-20",
    "ativo": false
  }
]
```

#### 3.3 XMLRepository (3 horas)

**Arquivo a criar:**
- `src/persistence/adapters/xml_adapter.py`

**Tarefas:**
1. Schema baseado no spec
2. Pretty print
3. Validação XSD (opcional)
4. Namespaces

**Formato:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<usuarios>
  <usuario>
    <nome>João Silva</nome>
    <email>joao@email.com</email>
    <senha>hash123</senha>
    <data_nascimento>1990-01-15</data_nascimento>
    <ativo>true</ativo>
  </usuario>
</usuarios>
```

#### 3.4 Conversão entre Formatos (2 horas)

**Arquivo a criar:**
- `src/persistence/converter.py`

**Tarefas:**
```python
class DataConverter:
    @staticmethod
    def convert(source_form_path, target_backend, source_backend=None):
        """
        Converte dados de um backend para outro.

        Exemplo:
        converter.convert('contatos', 'sqlite', 'txt')
        # Lê de contatos.txt e salva em SQLite
        """
```

**Entregáveis Fase 3:**
- ✅ CSV adapter completo
- ✅ JSON adapter completo
- ✅ XML adapter completo
- ✅ Ferramenta de conversão entre formatos
- ✅ Testes unitários para cada adapter
- ✅ Exemplos de uso

---

### **Fase 4: NoSQL** (Opcional)

**Duração Estimada:** 2-3 dias
**Objetivo:** Suporte a MongoDB e Redis

#### 4.1 MongoDBRepository (1.5 dias)

**Arquivo a criar:**
- `src/persistence/adapters/mongodb_adapter.py`

**Dependências:**
```toml
nosql = ["pymongo>=4.6.0"]
```

**Tarefas:**
1. Uma collection por formulário
2. Schemas dinâmicos (sem ALTER TABLE)
3. Indexes em campos marcados
4. Aggregation pipelines para queries complexas

**Estrutura:**
```javascript
// Collection: usuarios
{
  "_id": ObjectId("..."),
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "hash123",
  "data_nascimento": ISODate("1990-01-15"),
  "ativo": true,
  "created_at": ISODate("2025-01-15T10:30:00Z"),
  "updated_at": ISODate("2025-01-15T10:30:00Z")
}
```

#### 4.2 RedisRepository (0.5 dia)

**Arquivo a criar:**
- `src/persistence/adapters/redis_adapter.py`

**Dependências:**
```toml
redis = ["redis>=5.0.0"]
```

**Uso:**
- Caching de dados
- Session storage
- Rate limiting
- TTL configurável

**Entregáveis Fase 4:**
- ✅ MongoDB adapter
- ✅ Redis adapter (cache)
- ✅ Testes de integração
- ✅ Exemplos de uso

---

### **Fase 5: UI de Configuração e CLI**

**Duração Estimada:** 2 dias
**Objetivo:** Interface para gerenciar persistência

#### 5.1 Página de Administração (1 dia)

**Arquivos a criar:**
- `src/templates/admin/persistence.html`
- `src/templates/admin/migrate.html`
- `src/templates/admin/backup.html`

**Rotas Flask:**
```python
@app.route("/admin/persistence")
def admin_persistence():
    """Lista backends disponíveis e mapeamentos atuais"""

@app.route("/admin/persistence/backend/<form_path>", methods=["POST"])
def change_backend(form_path):
    """Muda backend de um formulário específico"""

@app.route("/admin/migrate")
def admin_migrate():
    """Interface para executar migrations"""

@app.route("/admin/backup")
def admin_backup():
    """Interface para backup/restore"""
```

**Features:**
- Tabela com todos os formulários e seus backends
- Dropdown para trocar backend
- Botão "Migrate" quando spec mudou
- Histórico de migrations
- Download de backups

#### 5.2 CLI de Administração (1 dia)

**Arquivo a criar:**
- `src/manage.py`

**Comandos:**

```bash
# Listar backends disponíveis
python src/manage.py backend list

# Ver backend atual de um formulário
python src/manage.py backend get contatos

# Mudar backend de um formulário
python src/manage.py backend set contatos sqlite

# Migrar dados de um backend para outro
python src/manage.py migrate-data contatos --from txt --to sqlite

# Executar migration de schema
python src/manage.py migrate contatos

# Backup de todos os dados
python src/manage.py backup --all

# Backup de um formulário específico
python src/manage.py backup contatos

# Restore de um backup
python src/manage.py restore contatos backups/contatos_20250115.json

# Ver status de todos os formulários
python src/manage.py status
```

**Implementação:**
```python
#!/usr/bin/env python
"""
VibeCForms Management CLI
"""
import click
from persistence.factory import RepositoryFactory
from persistence.converter import DataConverter

@click.group()
def cli():
    """VibeCForms Persistence Management"""
    pass

@cli.group()
def backend():
    """Manage persistence backends"""
    pass

@backend.command('list')
def list_backends():
    """List available backends"""
    # Implementação

@backend.command('get')
@click.argument('form_path')
def get_backend(form_path):
    """Get current backend for a form"""
    # Implementação

@backend.command('set')
@click.argument('form_path')
@click.argument('backend_name')
def set_backend(form_path, backend_name):
    """Set backend for a form"""
    # Implementação

if __name__ == '__main__':
    cli()
```

**Entregáveis Fase 5:**
- ✅ Interface web de administração
- ✅ CLI completo com todos os comandos
- ✅ Documentação de uso
- ✅ Tutorial em vídeo (opcional)

---

## 🧪 Estratégia de Testes

### Estrutura de Testes

```
tests/
├── test_form.py                    # 16 testes originais (devem continuar passando)
├── persistence/
│   ├── test_base_repository.py     # Testes da interface base
│   ├── test_txt_repository.py      # Testes do adapter TXT
│   ├── test_sqlite_repository.py   # Testes do adapter SQLite
│   ├── test_mysql_repository.py    # Testes do adapter MySQL
│   ├── test_postgres_repository.py # Testes do adapter PostgreSQL
│   ├── test_csv_repository.py      # Testes do adapter CSV
│   ├── test_json_repository.py     # Testes do adapter JSON
│   └── test_xml_repository.py      # Testes do adapter XML
├── test_factory.py                 # Testes do factory pattern
├── test_migrations.py              # Testes de migrations
├── test_converter.py               # Testes de conversão
└── test_performance.py             # Testes de performance
```

### Testes Unitários por Adapter

**Template de Teste:**
```python
# tests/persistence/test_sqlite_repository.py
import pytest
from persistence.adapters.sqlite_adapter import SQLiteRepository
from persistence.config import PersistenceConfig

@pytest.fixture
def sqlite_repo(tmp_path):
    config = {
        'type': 'sqlite',
        'database': str(tmp_path / 'test.db')
    }
    return SQLiteRepository(config)

@pytest.fixture
def sample_spec():
    return {
        'title': 'Test Form',
        'fields': [
            {'name': 'nome', 'type': 'text', 'required': True},
            {'name': 'idade', 'type': 'number', 'required': False},
            {'name': 'ativo', 'type': 'checkbox', 'required': False}
        ]
    }

def test_create_storage(sqlite_repo, sample_spec):
    """Testa criação de tabela"""
    result = sqlite_repo.create_storage('test_form', sample_spec)
    assert result is True
    assert sqlite_repo.exists('test_form') is True

def test_create_and_read(sqlite_repo, sample_spec):
    """Testa inserção e leitura"""
    sqlite_repo.create_storage('test_form', sample_spec)

    data = {'nome': 'João', 'idade': 30, 'ativo': True}
    sqlite_repo.create('test_form', sample_spec, data)

    records = sqlite_repo.read_all('test_form', sample_spec)
    assert len(records) == 1
    assert records[0]['nome'] == 'João'
    assert records[0]['idade'] == 30
    assert records[0]['ativo'] is True

def test_update(sqlite_repo, sample_spec):
    """Testa atualização"""
    sqlite_repo.create_storage('test_form', sample_spec)

    data = {'nome': 'João', 'idade': 30, 'ativo': True}
    sqlite_repo.create('test_form', sample_spec, data)

    new_data = {'nome': 'João Silva', 'idade': 31, 'ativo': False}
    sqlite_repo.update('test_form', sample_spec, 0, new_data)

    record = sqlite_repo.read_one('test_form', sample_spec, 0)
    assert record['nome'] == 'João Silva'
    assert record['idade'] == 31
    assert record['ativo'] is False

def test_delete(sqlite_repo, sample_spec):
    """Testa deleção"""
    sqlite_repo.create_storage('test_form', sample_spec)

    data = {'nome': 'João', 'idade': 30, 'ativo': True}
    sqlite_repo.create('test_form', sample_spec, data)

    sqlite_repo.delete('test_form', sample_spec, 0)

    records = sqlite_repo.read_all('test_form', sample_spec)
    assert len(records) == 0

def test_has_data(sqlite_repo, sample_spec):
    """Testa verificação de dados"""
    sqlite_repo.create_storage('test_form', sample_spec)
    assert sqlite_repo.has_data('test_form') is False

    data = {'nome': 'João', 'idade': 30, 'ativo': True}
    sqlite_repo.create('test_form', sample_spec, data)
    assert sqlite_repo.has_data('test_form') is True

def test_migrate_add_field(sqlite_repo):
    """Testa adição de campo"""
    old_spec = {
        'fields': [
            {'name': 'nome', 'type': 'text'}
        ]
    }

    new_spec = {
        'fields': [
            {'name': 'nome', 'type': 'text'},
            {'name': 'email', 'type': 'email'}
        ]
    }

    sqlite_repo.create_storage('test_form', old_spec)
    data = {'nome': 'João'}
    sqlite_repo.create('test_form', old_spec, data)

    result = sqlite_repo.migrate_schema('test_form', old_spec, new_spec)
    assert result is True

    records = sqlite_repo.read_all('test_form', new_spec)
    assert 'email' in records[0]
    assert records[0]['email'] == ''

def test_create_index(sqlite_repo, sample_spec):
    """Testa criação de índice"""
    sqlite_repo.create_storage('test_form', sample_spec)
    result = sqlite_repo.create_index('test_form', 'nome')
    assert result is True
```

### Testes de Integração

```python
# tests/test_integration.py
def test_switch_backend_txt_to_sqlite():
    """Testa migração de TXT para SQLite"""
    # 1. Criar dados em TXT
    # 2. Mudar backend para SQLite
    # 3. Verificar que dados foram migrados
    # 4. Verificar que operações funcionam no SQLite

def test_migration_preserves_data():
    """Testa que migration preserva dados existentes"""
    # 1. Criar formulário com dados
    # 2. Adicionar novo campo ao spec
    # 3. Executar migration
    # 4. Verificar que dados antigos ainda existem
    # 5. Verificar que novo campo foi adicionado

def test_concurrent_writes():
    """Testa escritas concorrentes"""
    # Usar threading para simular múltiplos writes
```

### Testes de Performance

```python
# tests/test_performance.py
import time

def test_bulk_insert_1000_records(benchmark_repo):
    """Benchmark de inserção em massa"""
    start = time.time()

    for i in range(1000):
        data = {'nome': f'User {i}', 'idade': i % 100}
        benchmark_repo.create('benchmark', spec, data)

    elapsed = time.time() - start
    print(f"Inseriu 1000 registros em {elapsed:.2f}s")
    assert elapsed < 10  # Deve ser rápido

def test_query_speed_comparison():
    """Compara velocidade de query entre backends"""
    # TXT, SQLite, MySQL
    # Medir tempo de read_all() com 10k registros
```

### Testes de Compatibilidade

```python
# tests/test_backward_compatibility.py
def test_original_tests_still_pass():
    """Garante que os 16 testes originais ainda passam"""
    # Rodar todos os testes de test_form.py
    # Todos devem passar sem modificação
```

## 📚 Dependências

### pyproject.toml

```toml
[project]
name = "vibecforms"
version = "3.0.0"
description = "Flask-based dynamic form system with pluggable persistence"
requires-python = ">=3.8"

dependencies = [
    "flask==2.3.3",
    "python-dotenv==1.0.1",
    "gunicorn>=21.0.0",
    "click>=8.1.0",  # CLI
]

[project.optional-dependencies]
# Core database support
sqlite = []  # Incluído no Python
mysql = [
    "pymysql>=1.1.0",
    "cryptography>=41.0.0",
]
postgres = [
    "psycopg2-binary>=2.9.9",
]

# NoSQL
nosql = [
    "pymongo>=4.6.0",
    "redis>=5.0.0",
]

# File formats
csv = []  # Incluído no Python
json = []  # Incluído no Python
xml = [
    "lxml>=5.0.0",
]

# All backends
all = [
    "vibecforms[mysql,postgres,nosql,xml]",
]

# Development
dev = [
    "pytest==7.4.4",
    "pytest-benchmark>=4.0.0",
    "black>=24.0.0",
    "pre-commit>=3.0.0",
    "hatch>=1.9.0",
]
```

### Instalação

```bash
# Instalação básica (apenas TXT e SQLite)
uv sync

# Com MySQL
uv sync --extra mysql

# Com PostgreSQL
uv sync --extra postgres

# Com todos os backends
uv sync --extra all

# Para desenvolvimento
uv sync --extra dev
```

## 🔄 Migração de Dados Existentes

### Script de Migração

**Arquivo:** `src/scripts/migrate_to_v3.py`

```python
#!/usr/bin/env python
"""
Script de migração para VibeCForms v3.0
Migra dados de .txt para SQLite ou outro backend
"""
import os
import json
from persistence.factory import RepositoryFactory
from persistence.adapters.txt_adapter import TxtRepository
from persistence.adapters.sqlite_adapter import SQLiteRepository

def migrate_all_forms(target_backend='sqlite'):
    """Migra todos os formulários para o backend alvo"""
    specs_dir = 'src/specs'

    # Descobrir todos os formulários
    forms = discover_forms(specs_dir)

    print(f"Encontrados {len(forms)} formulários para migrar")

    for form_path, spec in forms:
        print(f"Migrando {form_path}...")
        migrate_form(form_path, spec, target_backend)
        print(f"✅ {form_path} migrado")

    print("Migração concluída!")

def migrate_form(form_path, spec, target_backend):
    """Migra um formulário específico"""
    # 1. Ler dados do backend atual (TXT)
    txt_config = {'type': 'txt', 'path': 'src/', 'delimiter': ';'}
    txt_repo = TxtRepository(txt_config)

    data = txt_repo.read_all(form_path, spec)

    if not data:
        print(f"  ℹ️  Sem dados em {form_path}")
        return

    # 2. Criar storage no novo backend
    target_repo = RepositoryFactory.get_repository_by_type(target_backend)
    target_repo.create_storage(form_path, spec)

    # 3. Inserir dados
    for record in data:
        target_repo.create(form_path, spec, record)

    print(f"  ✅ {len(data)} registros migrados")

def discover_forms(specs_dir):
    """Descobre todos os formulários recursivamente"""
    forms = []

    for root, dirs, files in os.walk(specs_dir):
        for file in files:
            if file.endswith('.json') and not file.startswith('_'):
                spec_path = os.path.join(root, file)
                with open(spec_path) as f:
                    spec = json.load(f)

                # Calcular form_path relativo
                rel_path = os.path.relpath(spec_path, specs_dir)
                form_path = rel_path[:-5]  # Remove .json

                forms.append((form_path, spec))

    return forms

if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else 'sqlite'
    migrate_all_forms(target)
```

### Uso:

```bash
# Migrar tudo para SQLite
python src/scripts/migrate_to_v3.py sqlite

# Migrar tudo para MySQL
python src/scripts/migrate_to_v3.py mysql

# Migrar formulário específico
python src/manage.py migrate-data contatos --from txt --to sqlite
```

## 📖 Documentação

### Arquivos de Documentação

1. **docs/persistence.md** - Guia completo do sistema
   - Visão geral da arquitetura
   - Como funciona o Repository Pattern
   - Configuração de backends
   - Exemplos de uso

2. **docs/adapters.md** - Guia para desenvolvedores
   - Como criar um novo adapter
   - Implementação da interface BaseRepository
   - Mapeamento de tipos
   - Best practices

3. **docs/migrations.md** - Guia de migrations
   - Como funciona o sistema de migrations
   - Migrations automáticas vs manuais
   - Backup e restore
   - Troubleshooting

4. **docs/api_reference.md** - Referência da API
   - Todos os métodos do BaseRepository
   - Parâmetros e retornos
   - Exemplos de código

5. **CLAUDE.md** - Atualizar com v3.0
   - Nova seção sobre persistência
   - Estrutura de diretórios atualizada
   - Comandos de gerenciamento

### Exemplo de docs/persistence.md

```markdown
# Sistema de Persistência VibeCForms v3.0

## Visão Geral

O VibeCForms v3.0 introduz um sistema de persistência plugável que permite escolher entre múltiplos backends de armazenamento sem alterar o código da aplicação.

## Backends Suportados

### Bancos Relacionais
- **SQLite** - Banco local, zero configuração
- **MySQL/MariaDB** - Banco remoto, alta performance
- **PostgreSQL** - Banco remoto, features avançadas

### Formatos de Arquivo
- **TXT** - Formato original (backward compatible)
- **CSV** - Planilhas e importação/exportação
- **JSON** - Formato estruturado legível
- **XML** - Formato estruturado com schema

### NoSQL
- **MongoDB** - Document store
- **Redis** - Cache e sessions

## Configuração

A configuração é feita via arquivo `src/config/persistence.json`:

```json
{
  "default_backend": "txt",
  "backends": { ... },
  "form_mappings": { ... }
}
```

## Uso Básico

O sistema é transparente para o código da aplicação. As funções `read_forms()` e `write_forms()` automaticamente usam o backend configurado:

```python
# Código da aplicação (não muda)
forms = read_forms(spec, form_path)
write_forms(forms, spec, form_path)
```

## Trocando Backend

### Via Configuração

Edite `persistence.json`:

```json
{
  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "mysql"
  }
}
```

### Via CLI

```bash
python src/manage.py backend set contatos sqlite
```

### Via Interface Web

Acesse `/admin/persistence` e selecione o backend desejado.

## Migrations

Quando a especificação de um formulário muda (adicionar/remover campos), o sistema automaticamente migra o schema:

```bash
python src/manage.py migrate contatos
```

Backup automático é criado antes de qualquer migration.

## Exemplo Completo

### 1. Criar formulário

`src/specs/clientes.json`:
```json
{
  "title": "Clientes",
  "persistence": {
    "backend": "sqlite",
    "indexes": ["email"]
  },
  "fields": [
    {"name": "nome", "type": "text", "required": true},
    {"name": "email", "type": "email", "required": true}
  ]
}
```

### 2. Storage é criado automaticamente

Na primeira inserção, o sistema cria a tabela SQLite:

```sql
CREATE TABLE clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  email TEXT NOT NULL
);
CREATE INDEX idx_clientes_email ON clientes(email);
```

### 3. Adicionar campo

Atualizar spec:
```json
{
  "fields": [
    {"name": "nome", "type": "text"},
    {"name": "email", "type": "email"},
    {"name": "telefone", "type": "tel"}
  ]
}
```

### 4. Migration automática

```bash
python src/manage.py migrate clientes
```

```sql
ALTER TABLE clientes ADD COLUMN telefone TEXT DEFAULT '';
```

## Troubleshooting

### Erro de conexão com MySQL

Verifique as credenciais em `persistence.json` e que o servidor está rodando:

```bash
mysql -h localhost -u root -p
```

### Dados não aparecem após trocar backend

Execute migração de dados:

```bash
python src/manage.py migrate-data clientes --from txt --to sqlite
```

### Performance lenta

Adicione índices nos campos mais consultados:

```json
{
  "persistence": {
    "indexes": ["email", "nome"]
  }
}
```
```

## ⚡ Versionamento

### Versão 3.0.0 (Major)

**Por que major version?**
- Mudança arquitetural significativa
- Breaking changes internos (API interna muda)
- Novo sistema de módulos (`persistence/`)

**Compatibilidade:**
- ✅ Specs de formulários: **100% compatível**
- ✅ Dados em .txt: **100% compatível** (via TxtAdapter)
- ✅ Rotas Flask: **100% compatível**
- ✅ Templates: **100% compatível**
- ⚠️ Código que importava funções internas pode precisar ajustes

**Changelog:**
```markdown
# Version 3.0.0 - Pluggable Persistence System

## 🎯 Major Features

### Sistema de Persistência Plugável
- Suporte a múltiplos backends: TXT, SQLite, MySQL, PostgreSQL, CSV, JSON, XML
- Repository Pattern para abstração de persistência
- Factory Pattern para criação de repositórios
- Configuração declarativa via JSON

### SQLite Support
- Primeira alternativa ao formato TXT
- Mapeamento automático de tipos
- Índices configuráveis
- Migrations automáticas

### Sistema de Migrations
- Detecção automática de mudanças em specs
- ADD COLUMN para novos campos
- ALTER COLUMN para mudanças de tipo
- DROP COLUMN com confirmação
- Backup automático antes de migrations

### CLI de Gerenciamento
- `manage.py` com comandos para administração
- Troca de backend via linha de comando
- Migração de dados entre backends
- Backup e restore

## 🔧 Breaking Changes

### Estrutura de Diretórios
- Novo módulo `src/persistence/`
- Novo diretório `src/config/`

### API Interna
- `read_forms()` agora recebe `form_path` ao invés de `data_file`
- `write_forms()` agora recebe `form_path` ao invés de `data_file`
- Funções movidas para `persistence.adapters.txt_adapter`

## ✅ Backward Compatibility

- Todos os dados existentes em .txt continuam funcionando
- Specs de formulários não precisam ser alterados
- Rotas Flask mantidas inalteradas
- Templates mantidos inalterados
- Todos os 16 testes originais passam sem modificação

## 📦 Dependências Adicionais

Opcional (instalar apenas o necessário):
- `pymysql` - Para suporte a MySQL
- `psycopg2-binary` - Para suporte a PostgreSQL
- `pymongo` - Para suporte a MongoDB
- `redis` - Para suporte a Redis
- `lxml` - Para suporte a XML

## 🚀 Migration Guide

### Para usuários

Nenhuma ação necessária! O sistema continua usando .txt por padrão.

### Para trocar para SQLite

1. Editar `src/config/persistence.json`:
```json
{
  "default_backend": "sqlite"
}
```

2. Migrar dados:
```bash
python src/scripts/migrate_to_v3.py sqlite
```

### Para desenvolvedores

Se você tem código que importa diretamente funções de `VibeCForms.py`:

**Antes:**
```python
from VibeCForms import read_forms, write_forms
```

**Depois:**
```python
# As funções continuam funcionando da mesma forma
from VibeCForms import read_forms, write_forms
# Mas agora aceitam form_path ao invés de data_file
```

## 📚 Documentação

- `docs/persistence.md` - Guia completo do sistema
- `docs/adapters.md` - Como criar adapters customizados
- `docs/migrations.md` - Guia de migrations
- `docs/api_reference.md` - Referência completa da API

## 🧪 Testing

- +50 novos testes unitários
- Testes de integração para cada backend
- Testes de performance
- 100% dos testes originais passando

---

**Full Changelog:** https://github.com/username/VibeCForms/compare/v2.2.0...v3.0.0
```

## ✅ Critérios de Sucesso

### Técnicos

1. ✅ **Zero Regressão**
   - Todos os 16 testes originais passando
   - Código existente funciona sem modificação
   - Dados em .txt continuam funcionando

2. ✅ **SQLite Funcional**
   - CRUD completo
   - Migrations funcionando
   - Performance igual ou melhor que TXT

3. ✅ **Arquitetura Sólida**
   - Repository Pattern implementado corretamente
   - Factory Pattern funcionando
   - Fácil adicionar novos backends

4. ✅ **Configuração Flexível**
   - JSON de configuração validado
   - Mapeamento por formulário funcionando
   - Wildcards funcionando

5. ✅ **Migrations Robustas**
   - Detecção automática de mudanças
   - Backup antes de migrations
   - Rollback em caso de erro

### Funcionais

1. ✅ **Trocar Backend Sem Código**
   - Editar JSON e reiniciar
   - CLI funcionando
   - Interface web funcionando

2. ✅ **Performance Aceitável**
   - Read/write em menos de 100ms (SQLite)
   - Bulk insert de 1000 registros em menos de 10s
   - Sem degradação perceptível na UI

3. ✅ **Usabilidade**
   - Documentação clara
   - Exemplos funcionais
   - Mensagens de erro úteis

### Qualidade

1. ✅ **Cobertura de Testes**
   - >80% de coverage
   - Testes unitários para cada adapter
   - Testes de integração

2. ✅ **Documentação Completa**
   - Guia de uso
   - Guia de desenvolvimento
   - API reference
   - Troubleshooting

3. ✅ **Código Limpo**
   - Formatado com Black
   - Type hints onde apropriado
   - Docstrings em todas as funções públicas
   - Sem code smells

## 📊 Métricas de Sucesso

### Performance Benchmarks

| Operação | TXT | SQLite | MySQL | Target |
|----------|-----|--------|-------|--------|
| Read 100 records | ~10ms | ~5ms | ~8ms | <50ms |
| Write 1 record | ~2ms | ~1ms | ~3ms | <10ms |
| Bulk insert 1000 | ~200ms | ~100ms | ~150ms | <10s |
| Query by index | N/A | ~2ms | ~3ms | <10ms |

### Linhas de Código

| Módulo | Linhas | Observação |
|--------|--------|------------|
| persistence/base.py | ~150 | Interface base |
| persistence/factory.py | ~100 | Factory |
| persistence/config.py | ~80 | Config |
| adapters/txt_adapter.py | ~200 | Migração código atual |
| adapters/sqlite_adapter.py | ~300 | Novo adapter |
| adapters/mysql_adapter.py | ~350 | Novo adapter |
| migrations/migrator.py | ~400 | Sistema migrations |
| manage.py | ~300 | CLI |
| **TOTAL NOVO CÓDIGO** | **~1880** | |

### Testes

| Tipo | Quantidade | Target |
|------|------------|--------|
| Testes originais | 16 | 100% pass |
| Testes TXT adapter | 10 | 100% pass |
| Testes SQLite | 15 | 100% pass |
| Testes MySQL | 15 | 100% pass |
| Testes integração | 10 | 100% pass |
| Testes migration | 8 | 100% pass |
| **TOTAL** | **74** | |

## 🎯 Cronograma Estimado

### Semana 1: Fundação (Fase 1)

| Dia | Atividade | Horas | Entregável |
|-----|-----------|-------|------------|
| 1 | Estrutura base + Config | 4h | Base classes |
| 1 | TXT adapter migration | 3h | TxtRepository |
| 2 | SQLite adapter - parte 1 | 4h | CRUD básico |
| 2 | SQLite adapter - parte 2 | 3h | Indexes + migrations |
| 3 | Integração VibeCForms.py | 3h | Factory integrado |
| 3 | Testes - parte 1 | 2h | Testes TXT |
| 3 | Testes - parte 2 | 2h | Testes SQLite |

**Total Fase 1:** 21 horas (~3 dias)

### Semana 2: Bancos Remotos (Fase 2)

| Dia | Atividade | Horas | Entregável |
|-----|-----------|-------|------------|
| 4 | MySQL adapter | 6h | MySQLRepository |
| 5 | PostgreSQL adapter | 6h | PostgresRepository |
| 6 | Sistema migrations avançado | 6h | Migrator completo |
| 7 | Testes integração | 4h | Testes remotos |

**Total Fase 2:** 22 horas (~3 dias)

### Semana 3: Arquivos e UI (Fases 3 e 5)

| Dia | Atividade | Horas | Entregável |
|-----|-----------|-------|------------|
| 8 | CSV + JSON adapters | 5h | 2 adapters |
| 9 | XML adapter | 3h | XMLRepository |
| 9 | Converter | 2h | Conversão entre formatos |
| 10 | CLI manage.py | 5h | CLI completo |
| 11 | UI admin | 5h | Interface web |

**Total Fases 3+5:** 20 horas (~3 dias)

### Semana 4: NoSQL e Finalização (Fase 4)

| Dia | Atividade | Horas | Entregável |
|-----|-----------|-------|------------|
| 12 | MongoDB adapter | 5h | MongoDBRepository |
| 13 | Redis adapter | 2h | RedisRepository |
| 13-14 | Documentação | 8h | Docs completas |
| 14 | Testes finais | 3h | 100% coverage |
| 14 | Review e polish | 2h | Release ready |

**Total Fase 4:** 20 horas (~3 dias)

### Resumo Total

| Fase | Duração | Horas | Prioridade |
|------|---------|-------|------------|
| Fase 1 (SQLite) | 3 dias | 21h | ⭐⭐⭐ Alta |
| Fase 2 (MySQL/Postgres) | 3 dias | 22h | ⭐⭐ Média |
| Fase 3 (Arquivos) | 2 dias | 10h | ⭐ Baixa |
| Fase 4 (NoSQL) | 2 dias | 7h | Opcional |
| Fase 5 (UI/CLI) | 2 dias | 10h | ⭐⭐ Média |
| Docs e testes | 2 dias | 13h | ⭐⭐⭐ Alta |
| **TOTAL** | **14 dias** | **83h** | |

**MVP (Fase 1):** 3 dias
**Produção completa:** 14 dias

## 📝 Próximos Passos

### Imediato (Quando retomar)

1. ✅ Criar branch `feature/persistence-system`
2. ✅ Criar estrutura de diretórios
3. ✅ Implementar `BaseRepository`
4. ✅ Implementar `PersistenceConfig`
5. ✅ Implementar `RepositoryFactory`
6. ✅ Criar `persistence.json`
7. ✅ Migrar TXT para adapter
8. ✅ Rodar testes originais (devem passar)

### Fase 1 Completa

1. ✅ Implementar SQLite adapter
2. ✅ Integrar factory no VibeCForms.py
3. ✅ Escrever testes SQLite
4. ✅ Documentação básica
5. ✅ Commit e merge na main

### Longo Prazo

1. Fases 2, 3, 4, 5 conforme cronograma
2. Feedbacks de usuários
3. Otimizações de performance
4. Novos backends conforme demanda

---

## 📞 Questões em Aberto

### Decisões Arquiteturais

1. **Módulo único ou múltiplos?**
   - ✅ **Decisão:** Módulo único `persistence/` com subpasta `adapters/`
   - **Motivo:** Melhor organização, fácil importar

2. **ORM ou SQL puro?**
   - ✅ **Decisão:** Hybrid - SQLAlchemy Core (sem ORM) para abstração SQL
   - **Motivo:** Flexibilidade sem complexidade do ORM full

3. **Migrations: automáticas ou manuais?**
   - ✅ **Decisão:** Automáticas por padrão, manual opcional
   - **Motivo:** Usuário quer simplicidade

4. **Índices: automáticos ou configurados?**
   - ✅ **Decisão:** Configurados via spec, criados automaticamente
   - **Motivo:** Performance + controle

5. **IDs: auto-increment ou UUIDs?**
   - ✅ **Decisão:** Auto-increment por padrão
   - **Motivo:** Compatibilidade com sistema atual de índices

### Perguntas para o Usuário

Quando retomar o desenvolvimento, perguntar:

1. ❓ Prioridade 1: SQLite, MySQL ou PostgreSQL?
2. ❓ Já tem servidores MySQL/Postgres configurados para testar?
3. ❓ Quer interface web de admin ou CLI é suficiente?
4. ❓ Precisa de autenticação nos bancos remotos?
5. ❓ Quer sistema de backup automático agendado?

---

## 📄 Licença

Este plano faz parte do projeto VibeCForms (MIT License).

---

**Plano criado em:** Outubro 2025
**Última atualização:** Outubro 2025
**Status:** ✅ Fase 1 completa, Fase 1.5 em andamento
**Próxima revisão:** Após conclusão da Fase 1.5

---

## 🚀 Fase 1.5: Melhorias Críticas de Migration (EM ANDAMENTO)

**Data de Início:** 16 Outubro 2025
**Status:** 🔄 30% Completo (Parte 1 concluída)
**Objetivo:** Implementar funcionalidades críticas de migration identificadas pelo usuário

### Requisitos Adicionais Identificados

Durante a revisão da Fase 1, foram identificados 4 requisitos críticos que devem ser implementados:

1. **Schema Migration Completo**
   - ✅ Já implementado: Adicionar campos
   - ❌ Falta: Alterar campos (tipo, nome, required)
   - ❌ Falta: Remover campos

2. **Migração Automática Entre Backends**
   - Detectar mudança de backend na configuração
   - Migrar dados automaticamente (TXT → SQLite, SQLite → TXT, etc.)
   - Criar backup antes da migração
   - Verificar sucesso da migração

3. **Sistema de Confirmação para Alterações**
   - Detectar alteração de campos com dados
   - Exibir alerta na interface web
   - Pedir confirmação antes de aplicar
   - Tentar preservar dados durante alteração

4. **Sistema de Confirmação para Exclusões**
   - Detectar exclusão de campos com dados
   - Exibir alerta na interface web
   - Avisar sobre perda permanente de dados
   - Pedir confirmação explícita

### Arquitetura da Fase 1.5

#### Novos Componentes Criados

**1. SchemaChangeDetector** (`src/persistence/schema_detector.py` - 430 linhas)
```python
class SchemaChangeDetector:
    - detect_changes(old_spec, new_spec) -> SchemaChange
    - detect_backend_change(form_path, old_backend, new_backend) -> BackendChange
    - _detect_renames(old_spec, new_spec, removed, added) -> List[Tuple]
    - _is_type_compatible(old_type, new_type) -> bool
```

Detecta 5 tipos de mudanças:
- ADD_FIELD - Adicionar campos
- REMOVE_FIELD - Remover campos (destrutivo)
- RENAME_FIELD - Renomear campos (preserva dados)
- CHANGE_TYPE - Alterar tipo de campo
- BACKEND_CHANGE - Mudança de backend de persistência

**2. SchemaHistory** (`src/persistence/schema_history.py` - 250 linhas)
```python
class SchemaHistory:
    - get_form_history(form_path) -> Dict
    - update_form_history(form_path, spec_hash, backend, record_count)
    - has_spec_changed(form_path, current_spec_hash) -> bool
    - has_backend_changed(form_path, current_backend) -> bool
```

Rastreia histórico via `src/config/schema_history.json`:
```json
{
  "contatos": {
    "last_spec_hash": "abc123...",
    "last_backend": "txt",
    "last_updated": "2025-10-16T10:30:00Z",
    "record_count": 42
  }
}
```

**3. ChangeManager** (`src/persistence/change_manager.py` - 200 linhas)
```python
class ChangeManager:
    - check_for_changes(form_path, spec, backend, has_data, record_count)
    - update_tracking(form_path, spec, backend, record_count)
    - requires_confirmation(schema_change, backend_change) -> bool
```

Coordena detecção e rastreamento de mudanças.

**4. BaseRepository - Novos Métodos Abstratos**

Adicionados 3 novos métodos à interface base:

```python
@abstractmethod
def rename_field(form_path, spec, old_name, new_name) -> bool:
    """Renomeia campo preservando dados"""

@abstractmethod
def change_field_type(form_path, spec, field_name, old_type, new_type) -> bool:
    """Altera tipo do campo com conversão de dados"""

@abstractmethod
def remove_field(form_path, spec, field_name) -> bool:
    """Remove campo (destrutivo)"""
```

**5. Hook de Detecção em VibeCForms.py**

Integrado na função `read_forms()`:
```python
def read_forms(spec, form_path):
    # Check for schema or backend changes
    schema_change, backend_change = check_form_changes(
        form_path=form_path,
        spec=spec,
        has_data=has_data,
        record_count=record_count
    )

    # Log detected changes
    if schema_change or backend_change:
        logger.info(f"Changes detected for '{form_path}'")
        # TODO: Redirect to confirmation UI (Part 4)

    # Continue with normal flow...
```

### Implementação por Partes

#### ✅ Parte 1: Infraestrutura de Detecção (100% completa)

**Status:** ✅ Completa
**Tarefas:**
1. ✅ Criar SchemaChangeDetector
2. ✅ Criar SchemaHistory e schema_history.json
3. ✅ Detectar mudança de backend
4. ✅ Hook de detecção em read_forms()

**Resultado:**
- Sistema detecta mudanças de schema e backend
- Logs detalhados no console
- Rastreamento histórico funcional
- Sem impacto no fluxo normal da aplicação

#### 🔄 Parte 2: Schema Migrations Avançadas (0% completa)

**Status:** 🔄 Pendente
**Tarefas:**
1. ❌ Implementar rename_field() no TxtRepository
2. ❌ Implementar rename_field() no SQLiteRepository
3. ❌ Implementar change_field_type() nos adapters
4. ❌ Implementar remove_field() nos adapters
5. ❌ Atualizar migrate_schema() existente

**Estimativa:** ~600 linhas, 4-5 horas

#### ⏳ Parte 3: Migração Entre Backends (0% completa)

**Status:** ⏳ Pendente
**Tarefas:**
1. ❌ Criar MigrationManager.migrate_backend()
2. ❌ Implementar estratégias de conversão
3. ❌ Sistema de backup para cross-backend
4. ❌ Rollback automático em falha

**Estimativa:** ~500 linhas, 3-4 horas

#### ⏳ Parte 4: Interface de Confirmação (0% completa)

**Status:** ⏳ Pendente
**Tarefas:**
1. ❌ Criar template migration_confirm.html
2. ❌ Criar rota /migrate/confirm/<form_path>
3. ❌ Criar rota /migrate/execute/<form_path>
4. ❌ Integrar confirmações no fluxo

**Estimativa:** ~300 linhas, 2-3 horas

### Arquivos Criados/Modificados

**Novos arquivos (4):**
- `src/persistence/schema_detector.py` (430 linhas)
- `src/persistence/schema_history.py` (250 linhas)
- `src/persistence/change_manager.py` (200 linhas)
- `src/config/schema_history.json` (vazio inicialmente)

**Arquivos modificados (2):**
- `src/persistence/base.py` (+97 linhas - 3 novos métodos abstratos)
- `src/VibeCForms.py` (+40 linhas - hook de detecção)

**Total de código novo até agora:** ~1017 linhas
**Estimativa restante:** ~1400 linhas

### Cronograma Atualizado

| Fase | Status | Duração | Prioridade |
|------|--------|---------|------------|
| Fase 1 (Foundation + SQLite) | ✅ Completa | 3 dias | ⭐⭐⭐ |
| **Fase 1.5 (Migrations)** | **🔄 30%** | **2 dias** | **⭐⭐⭐** |
| Fase 2 (MySQL/Postgres) | ⏳ Planejada | 3 dias | ⭐⭐ |
| Fase 3 (Arquivos) | ⏳ Planejada | 2 dias | ⭐ |
| Fase 4 (NoSQL) | ⏳ Planejada | 2 dias | Opcional |
| Fase 5 (UI/CLI) | ⏳ Planejada | 2 dias | ⭐⭐ |

### Próximos Passos

**Imediato (Parte 2):**
1. Implementar `rename_field()` no TxtRepository
2. Implementar `rename_field()` no SQLiteRepository
3. Implementar `change_field_type()` nos adapters
4. Implementar `remove_field()` nos adapters
5. Testes unitários para novos métodos

**Após Parte 2:**
1. Criar MigrationManager para migrations entre backends
2. Implementar UI de confirmação web
3. Testes de integração completos
4. Documentação atualizada

### Decisões Técnicas

1. **Detecção de Renames:** Heurística baseada em posição e tipo
   - Se campo removido e adicionado na mesma posição com mesmo tipo = rename provável

2. **Compatibilidade de Tipos:** Lista de conversões seguras
   - text ↔ email, tel, url, search (safe)
   - number ↔ range (safe)
   - text → any (sempre safe, conversível para string)

3. **Confirmação Obrigatória:** Quando há dados e mudança destrutiva
   - Remover campos: sempre requer confirmação
   - Alterar tipo: se incompatível
   - Renomear: se há dados (para confirmar que é rename, não add+remove)

4. **Backup Automático:** Antes de qualquer migration destrutiva
   - Formato: `src/backups/{form_path}_{timestamp}.json`
   - Preserva dados em formato portável

### Notas de Implementação

**Logging Detalhado:**
```python
logger.info(f"Schema changes detected for 'contatos': {{'add_field': 1, 'remove_field': 1}}")
logger.info(f"Backend change detected for 'produtos': txt -> sqlite (42 records)")
logger.warning(f"Destructive change detected: removing field 'fax' with data")
```

**Próxima Sessão:** Implementar Parte 2 (Schema Migrations Avançadas)
