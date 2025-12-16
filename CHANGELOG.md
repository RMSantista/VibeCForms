# Changelog

## Version 4.0.0 - UUID System, Tags as State & Kanban Visual (2025-11-22)

### Overview
Esta versão marca uma evolução fundamental no VibeCForms, implementando três pilares essenciais da arquitetura de workflow: **sistema de identificação único (UUID)**, **tags como estados (Tags as State - Convention #4)** e **interface visual Kanban**. Estas features transformam o VibeCForms de um sistema CRUD simples para uma plataforma completa de rastreamento de processos colaborativos entre humanos, agentes de IA e código.

**Merged via PR #23** - dev-wk-essential → main (2025-11-19)

**Estatísticas**:
- 13.410 linhas adicionadas, 922 deletadas
- 79 arquivos modificados
- 138 testes passando (0 falhando, 4 skipped)
- 100% backward compatible

---

### 🆔 Feature #1: UUID System (Crockford Base32)

#### Identificação Única de Registros
Migração completa de índices para IDs únicos baseados em UUID com encoding Crockford Base32, eliminando race conditions e permitindo sistemas distribuídos.

**Formato do ID:**
- 27 caracteres (26 UUID + 1 check digit)
- Character set: `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (exclui I, L, O, U)
- Exemplo: `3HNMQR8PJSG0C9VWBYTE12K`
- URL-safe, human-readable, case-insensitive input

**Arquivos Criados:**
- `src/utils/crockford.py` (316 linhas) - Encoder/decoder Crockford Base32
- `src/utils/__init__.py` - Utils package
- `docs/crockford_ids.md` (500 linhas) - Documentação completa do sistema
- `tests/test_crockford.py` (288 linhas) - Suite completa de testes
- `scripts/demo_crockford.py` (286 linhas) - Script de demonstração
- `scripts/migrate_add_uuids.py` (173 linhas) - Script de migração

**Implementação:**

**BaseRepository Interface** (`src/persistence/base.py`):
- ✅ Novos métodos UUID-based:
  - `read_by_id(form_path, spec, record_id)` - Leitura por ID
  - `update_by_id(form_path, spec, record_id, data)` - Atualização por ID
  - `delete_by_id(form_path, spec, record_id)` - Deleção por ID
  - `id_exists(form_path, record_id)` - Verificação de existência
- ⚠️ Métodos index-based marcados como deprecated:
  - `read_one(idx)` → usar `read_by_id()`
  - `update(idx, data)` → usar `update_by_id()`
  - `delete(idx)` → usar `delete_by_id()`

**TXT Backend** (`src/persistence/adapters/txt_adapter.py`):
- Novo formato: `UUID;field1;field2;...` (ID na primeira coluna)
- Suporte completo a operações UUID
- Mantém backward compatibility para leitura

**SQLite Backend** (`src/persistence/adapters/sqlite_adapter.py`):
- Schema: `id TEXT PRIMARY KEY` (27 caracteres)
- Remoção de AUTOINCREMENT
- Índices otimizados para busca por ID

**Application Layer** (`src/VibeCForms.py`):
- Rotas atualizadas: `/<form>/edit/<id>`, `/<form>/delete/<id>`
- Validação de check digit antes de operações
- Display de IDs em fonte monospace (copyable)

**Benefits:**
- ✅ Eliminação de race conditions
- ✅ Suporte a sistemas distribuídos
- ✅ IDs podem ser gerados offline
- ✅ Detecção de erros via check digit
- ✅ URLs mais descritivos e debugáveis

---

### 🏷️ Feature #2: Tags as State System (Convention #4)

#### Sistema Completo de Tags para Workflow
Implementação da Convention #4 do VibeCForms: "Tags as State" - objetos movem através de estados representados por tags, permitindo colaboração entre humanos, AI agents e subsistemas.

**Arquivos Criados:**
- `src/services/tag_service.py` (522 linhas) - Serviço de gerenciamento de tags
- `src/templates/tags_manager.html` (517 linhas) - Interface web de gerenciamento
- `docs/tags_guide.md` (747 linhas) - Guia completo de uso
- `docs/homologacao_tags.md` (537 linhas) - Documentação de homologação
- `tests/test_tags_api.py` (468 linhas) - 18 testes de API
- `tests/test_tags_e2e.py` (441 linhas) - 21 testes end-to-end

**TagService API:**

**Core Operations:**
```python
tag_service.add_tag(form_path, object_id, tag, applied_by, metadata=None)
tag_service.remove_tag(form_path, object_id, tag, removed_by)
tag_service.has_tag(form_path, object_id, tag) → bool
tag_service.get_tags(form_path, object_id) → List[Dict]
tag_service.get_objects_by_tag(form_path, tag) → List[str]
tag_service.transition(form_path, object_id, from_tag, to_tag, applied_by)
```

**REST Endpoints:**
- `GET /tags/manager` - Interface de gerenciamento completa
- `GET /api/<form>/tags/<id>` - Obter todas as tags de um objeto
- `POST /api/<form>/tags/<id>` - Adicionar tag (body: `{"tag": "qualified", "applied_by": "user"}`)
- `DELETE /api/<form>/tags/<id>/<tag>` - Remover tag específica
- `GET /api/<form>/tags/<id>/history` - Histórico completo de tags (incluindo removidas)
- `GET /api/<form>/search/tags?tag=<tag>` - Buscar objetos por tag

**BaseRepository Interface Extensions:**
- `add_tag(object_type, object_id, tag, applied_by, metadata)` - Adicionar tag
- `remove_tag(object_type, object_id, tag, removed_by)` - Remover tag
- `has_tag(object_type, object_id, tag)` - Verificar tag
- `get_tags(object_type, object_id)` - Obter tags ativas
- `get_objects_by_tag(object_type, tag)` - Buscar por tag
- `get_tag_history(object_type, object_id)` - Histórico completo

**TXT Backend - Tags Storage:**
- Arquivo: `<form>_tags.txt`
- Formato: `object_id;tag;applied_at;applied_by;removed_at;removed_by;metadata_json`
- Preserva histórico completo de tags

**SQLite Backend - Tags Storage:**
- Tabela global: `tags`
- Schema: `id, object_type, object_id, tag, applied_at, applied_by, removed_at, removed_by, metadata`
- Índices: `idx_object_id`, `idx_tag`, `idx_object_type_tag`

**Features:**
- ✅ Tags representam estados de workflow (lead → qualified → proposal → closed)
- ✅ Múltiplas tags por objeto
- ✅ Histórico completo preservado (audit trail)
- ✅ Validação de nomes (lowercase, números, underscore apenas)
- ✅ Metadata opcional para contexto adicional
- ✅ State transitions atômicas
- ✅ Interface web dedicada para gerenciamento

---

### 📊 Feature #3: Kanban Visual System

#### Interface Visual Drag & Drop para Workflow
Sistema completo de Kanban boards configuráveis para visualizar e gerenciar transições de estado via tags.

**Arquivos Criados:**
- `src/services/kanban_service.py` (368 linhas) - Lógica de negócio Kanban
- `src/templates/kanban.html` (426 linhas) - Interface visual drag & drop
- `src/config/kanban_boards.json` (40 linhas) - Configuração de boards
- `docs/KANBAN_README.md` (323 linhas) - Documentação completa
- `tests/test_kanban.py` (336 linhas) - 25 testes unitários

**KanbanService (Singleton):**
```python
kanban_service.load_board(board_name) → Dict
kanban_service.get_column_cards(board_name, column_tag, form_path) → List[Dict]
kanban_service.move_card(board_name, object_id, from_column, to_column, moved_by) → bool
kanban_service.validate_transition(board_name, from_column, to_column) → bool
```

**Configuration** (`kanban_boards.json`):
```json
{
  "sales_pipeline": {
    "name": "Sales Pipeline",
    "description": "Manage deals through sales stages",
    "object_type": "deals",
    "columns": [
      {"tag": "lead", "label": "Leads", "color": "#6c757d"},
      {"tag": "qualified", "label": "Qualified", "color": "#0d6efd"},
      {"tag": "proposal", "label": "Proposal", "color": "#ffc107"},
      {"tag": "closed", "label": "Closed Won", "color": "#198754"}
    ]
  }
}
```

**REST Endpoints:**
- `GET /kanban/<board_name>` - Interface visual do board
- `POST /api/kanban/<board_name>/move` - Mover card (body: `{"object_id": "...", "from_column": "lead", "to_column": "qualified", "moved_by": "user"}`)

**Features:**
- ✅ Drag & drop nativo para mover cards entre colunas
- ✅ Configuração declarativa via JSON
- ✅ Colunas representam tags (estados)
- ✅ Cards mostram informações do objeto
- ✅ Cores customizáveis por coluna
- ✅ Validação de transições permitidas
- ✅ Singleton pattern para consistência
- ✅ Integração total com TagService

---

### 🔧 Feature #4: Data Architecture Reorganization

#### Migração src/ → data/
Reorganização da estrutura de dados para separar código fonte de dados persistidos.

**Nova Estrutura:**
```
data/
├── txt/                    # TXT backend files
│   ├── contatos.txt
│   ├── produtos.txt
│   └── ...
├── sqlite/                 # SQLite databases
│   └── vibecforms.db
└── backups/               # Backup files
    ├── migrations/        # Migration backups
    └── full_backup_*/     # Full system backups
```

**Script de Migração:**
- `scripts/migrate_data_folder.py` (324 linhas)
- Backup automático antes da migração
- Log detalhado em JSON
- Rollback capability

**Benefits:**
- ✅ Separação clara entre código e dados
- ✅ Facilita backups
- ✅ Simplifica .gitignore
- ✅ Melhor organização multi-backend

---

### 🏢 Feature #5: Multi-Business Case Architecture

#### Suporte a Múltiplos Casos de Uso Isolados
Sistema para executar múltiplas instâncias isoladas do VibeCForms, cada uma com suas próprias specs, dados e configurações.

**Business Case Structure:**
```
examples/<business-case-name>/
├── specs/              # Form specifications
├── config/             # Configuration files
│   ├── persistence.json
│   ├── kanban_boards.json
│   └── schema_history.json
├── templates/          # Custom templates (optional)
├── data/              # Data storage
│   ├── txt/
│   ├── sqlite/
│   └── backups/
```

**Available Business Cases:**
- `examples/ponto-de-vendas/` - Point of Sale system
- `examples/processo-seletivo/` - Recruitment process
- `examples/demo/` - Demo forms with Kanban and Tags
- `examples/analise-laboratorial/` - Laboratory analysis (template)

**Running a Business Case:**
```bash
uv run app examples/ponto-de-vendas
# or
python src/VibeCForms.py examples/demo
```

**Features:**
- ✅ Complete isolation between cases
- ✅ Independent data, specs, and configuration
- ✅ Template customization per case
- ✅ Easy to create new cases

---

### 🐛 Bug Fixes & Improvements

#### Critical Performance Fix
- **Issue**: Browser freezing on pages with 23+ records
- **Cause**: Automatic inline tag loading doing simultaneous AJAX for all records
- **Fix**: Disabled automatic inline loading, users use dedicated Tags Manager
- **File**: `src/templates/form.html:194-212`

#### SQLite Adapter Fixes
- Fixed `delete_by_id` using list comprehension (critical bug)
- Added field name validation against SQL injection
- Improved exception handling (specific vs generic)
- Added type hints for critical methods

#### Code Quality
- 10 arquivos reformatados com Black
- Constantes nomeadas para legibilidade
- Melhoria em documentação inline
- Remoção de código morto

---

### 📈 Testing & Quality

**Test Coverage:**
- 138 testes passando, 0 falhando, 4 skipped
- 25 testes de Kanban (unit tests)
- 18 testes de Tags API (endpoint tests)
- 21 testes de Tags E2E (end-to-end tests)
- 33 testes de Crockford encoding
- Performance benchmarks inclusos

**Benchmark Results** (`tests/benchmark_performance.py`):
- Tag operations: < 10ms (SQLite), < 5ms (TXT)
- UUID generation: < 1ms
- Kanban load: < 50ms (100 cards)

---

### 📚 Documentation

**New Documentation Files:**
- `docs/crockford_ids.md` (500 linhas) - UUID system guide
- `docs/tags_guide.md` (747 linhas) - Tags as State complete guide
- `docs/KANBAN_README.md` (323 linhas) - Kanban system guide
- `docs/homologacao_tags.md` (537 linhas) - Tags homologation docs
- `docs/MIGRATION.md` (658 linhas) - Migration guide
- `docs/essential/tags-as-state-uuid-migration-plan.md` (454 linhas) - Planning docs

**Updated Documentation:**
- `CLAUDE.md` - Extended with UUID, Tags, and Kanban conventions
- `README.md` - Updated with new features and examples
- `ARCHITECTURE.md` → `docs/ARCHITECTURE.md` (reorganized)

---

### 🔄 Breaking Changes

**NONE** - Esta versão é 100% backward compatible:
- ✅ Métodos index-based ainda funcionam (deprecated)
- ✅ Formato TXT antigo pode ser lido
- ✅ Rotas antigas continuam funcionando
- ✅ Todos os 138 testes passando

**Deprecation Warnings:**
- Index-based methods (`read_one`, `update`, `delete`) serão removidos na v5.0
- Recomendado migrar para UUID-based methods

---

### 🎯 Migration Path

**Para Migrar de v3.0 para v4.0:**

1. **Sem ação necessária** - sistema é backward compatible
2. **Opcional**: Migrar dados para usar UUIDs:
   ```bash
   python scripts/migrate_add_uuids.py
   ```
3. **Opcional**: Configurar Tags para seus formulários
4. **Opcional**: Criar Kanban boards em `config/kanban_boards.json`

---

### 🚀 Upgrade Instructions

**Atualizar VibeCForms:**
```bash
git pull origin main
uv sync
uv run hatch run test  # Verificar que tudo está OK
```

**Explorar Novas Features:**
```bash
# Executar demo business case com Kanban e Tags
uv run app examples/demo

# Acessar:
# - http://127.0.0.1:5000/tags/manager - Tags Manager
# - http://127.0.0.1:5000/kanban/sales_pipeline - Kanban Board
```

---

### 🎉 Summary

**Version 4.0.0** transforma VibeCForms de um framework CRUD simples para uma **plataforma completa de rastreamento de processos colaborativos**:

✅ **UUID System** - Identificação única, distribuída e confiável
✅ **Tags as State** - Estados explícitos, queryable e auditáveis
✅ **Kanban Visual** - Interface intuitiva para gerenciar workflows
✅ **Multi-Business Cases** - Suporte a múltiplos casos de uso isolados
✅ **138 Testes** - Cobertura completa e qualidade garantida
✅ **Zero Breaking Changes** - Migração suave e segura

**Próximos Passos**: Implementação de notificações baseadas em tags e interfaces de AI agents (v5.0)

---

## Version 3.0 - Sistema de Persistência Plugável

### Overview
Esta versão implementa um sistema completo de persistência multi-backend, permitindo que diferentes formulários utilizem diferentes sistemas de armazenamento (TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML). Inclui migração automática de dados, detecção de mudanças em schemas, confirmação de usuário para operações críticas e sistema de backup.

**Status**: Fase 1.5 completa (SQLite + Sistema de Migração)

---

### Feature #1: Arquitetura de Persistência Plugável

#### 🗄️ Multi-Backend Support
- Sistema baseado em Repository Pattern + Adapter Pattern
- Suporte a 8 tipos de backend configuráveis via JSON
- Factory Pattern para instanciar repositórios apropriados
- Interface `BaseRepository` unificada com 11 métodos

#### Backends Implementados

**✅ TXT (Fase 0 - Existente)**
- Backend original mantido para compatibilidade
- Arquivos delimitados por ponto-e-vírgula
- Codificação UTF-8 configurável

**✅ SQLite (Fase 1)**
- Banco de dados embutido, zero configuração
- Cada formulário vira uma tabela
- Suporte completo a tipos de campo (text, number, boolean, date)
- Pool de conexões e timeout configurável

**⏳ MySQL, PostgreSQL, MongoDB, CSV, JSON, XML (Fases Futuras)**
- Configurações prontas em `persistence.json`
- Arquitetura preparada para implementação

#### Configuração via JSON

**Arquivo**: `src/config/persistence.json`
```json
{
  "version": "1.0",
  "default_backend": "txt",
  "backends": {
    "txt": {...},
    "sqlite": {...},
    "mysql": {...},
    ...
  },
  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "sqlite",
    "*": "default_backend"
  },
  "auto_create_storage": true,
  "auto_migrate_schema": true,
  "backup_before_migrate": true
}
```

---

### Feature #2: Sistema de Migração Automática

#### 🔄 Backend Migration com Confirmação
- Detecção automática de mudanças de backend
- Interface web para confirmação de migração
- Cópia completa de dados entre backends
- Rollback automático em caso de falha
- Backup automático antes de migrações

#### Fluxo de Migração
1. Sistema detecta mudança em `persistence.json` (ex: TXT → SQLite)
2. Compara com `schema_history.json` para verificar dados existentes
3. Exibe tela de confirmação: `/migrate/confirm/<form_path>`
4. Usuário confirma: `/migrate/execute/<form_path>`
5. Cria backup em `src/backups/migrations/`
6. Migra todos os registros
7. Atualiza `schema_history.json`

#### Migrações Realizadas com Sucesso
- ✅ **contatos**: 23 registros migrados de TXT para SQLite
- ✅ **produtos**: 17 registros migrados de TXT para SQLite
- ✅ Total: 40 registros migrados sem perda de dados

#### Rotas de Migração
**Nova rota:**
```python
@app.route("/migrate/confirm/<path:form_path>")
def migrate_confirm(form_path):
    """Exibe confirmação de migração."""

@app.route("/migrate/execute/<path:form_path>", methods=["POST"])
def migrate_execute(form_path):
    """Executa migração após confirmação."""
```

---

### Feature #3: Detecção de Mudanças em Schema

#### 🔍 Schema Change Detection
- Hash MD5 de especificações para detectar mudanças
- Rastreamento automático de schemas em `schema_history.json`
- Detecção de 4 tipos de mudança:
  - `ADD_FIELD` - Campo adicionado (sem confirmação)
  - `REMOVE_FIELD` - Campo removido (requer confirmação se há dados)
  - `CHANGE_TYPE` - Tipo alterado (requer confirmação)
  - `CHANGE_REQUIRED` - Flag obrigatório alterado (aviso)

#### Schema History Tracking

**Arquivo**: `src/config/schema_history.json` (gerado automaticamente)
```json
{
  "contatos": {
    "last_spec_hash": "ee014237f822ba2d7ea15758cd6056dd",
    "last_backend": "sqlite",
    "last_updated": "2025-10-16T17:29:30.878397",
    "record_count": 23
  }
}
```

#### Change Manager
- `SchemaChangeDetector` - Detecta mudanças em specs
- `BackendChange` - Representa mudança de backend
- `ChangeManager` - Coordena detecção e confirmação
- Prevenção de perda de dados acidental

---

### Feature #4: Sistema de Backup

#### 💾 Backup Automático
- Backup antes de todas as migrações
- Formato: `<form>_<old_backend>_to_<new_backend>_<timestamp>.txt`
- Localização: `src/backups/migrations/`
- Preserva dados originais para recovery

#### Exemplo de Backup
```
src/backups/migrations/
├── contatos_txt_to_sqlite_20251016_172945.txt
└── produtos_txt_to_sqlite_20251016_164338.txt
```

---

### Architecture & Code Structure

#### Nova Estrutura de Diretórios
```
src/
├── persistence/
│   ├── __init__.py
│   ├── base_repository.py         # Interface BaseRepository
│   ├── repository_factory.py      # Factory para criar repositórios
│   ├── migration_manager.py       # Gerencia migrações
│   ├── schema_detector.py         # Detecção de mudanças
│   └── adapters/
│       ├── __init__.py
│       ├── txt_adapter.py         # TxtRepository (refatorado)
│       └── sqlite_adapter.py      # SQLiteRepository (novo)
├── config/
│   ├── persistence.json           # Configuração de backends
│   └── schema_history.json        # Histórico automático
└── backups/
    └── migrations/                # Backups de migrações
```

#### Principais Classes

**BaseRepository** (Interface):
```python
class BaseRepository(ABC):
    @abstractmethod
    def create(self, form_path, spec, data): pass
    @abstractmethod
    def read_all(self, form_path, spec): pass
    @abstractmethod
    def update(self, form_path, spec, idx, data): pass
    @abstractmethod
    def delete(self, form_path, spec, idx): pass
    @abstractmethod
    def exists(self, form_path): pass
    @abstractmethod
    def has_data(self, form_path): pass
    @abstractmethod
    def create_storage(self, form_path, spec): pass
    @abstractmethod
    def drop_storage(self, form_path): pass
    # ... +3 métodos auxiliares
```

**RepositoryFactory**:
```python
@staticmethod
def get_repository(backend_type: str) -> BaseRepository:
    """Retorna instância do repositório apropriado."""
```

**MigrationManager**:
```python
@staticmethod
def migrate_backend(form_path, spec, old_backend, new_backend, record_count):
    """Migra dados entre backends com backup."""
```

**SchemaChangeDetector**:
```python
@staticmethod
def detect_changes(form_path, old_spec, new_spec, has_data):
    """Detecta e retorna mudanças em schema."""
```

---

### Testing & Quality Assurance

#### ✅ Cobertura de Testes Expandida

**Novos arquivos de teste:**
- `tests/test_sqlite_adapter.py` - 10 testes para SQLiteRepository
- `tests/test_backend_migration.py` - 6 testes para migração (2 passando, 4 skipped*)
- `tests/test_change_detection.py` - 13 testes para detecção de mudanças

**Total**: 29 novos testes, 41 testes no total
**Status**: 41 passing, 4 skipped

*Nota: 4 testes skipped devido a MigrationManager usar configuração global (requer refatoração arquitetural). Funcionalidade verificada funcionando em produção com migrações reais.

#### Testes do SQLite Adapter (10 testes)
- ✅ Inicialização de repositório
- ✅ Criação de storage (tabelas)
- ✅ Operações CRUD (create, read, update, delete)
- ✅ Verificação de existência e dados
- ✅ Múltiplos formulários no mesmo banco
- ✅ Conversão de tipos (boolean, number, text)
- ✅ Drop de storage

#### Testes de Migração (6 testes)
- ✅ Migração de storage vazio (passando)
- ✅ Rollback em caso de falha (passando)
- ⏭️ Migração com dados (skipped - requer refatoração)
- ⏭️ Criação de backup (skipped - requer refatoração)
- ⏭️ Preservação de integridade (skipped - requer refatoração)
- ⏭️ Caminhos aninhados (skipped - requer refatoração)

#### Testes de Detecção de Mudanças (13 testes)
- ✅ Computação de hash MD5
- ✅ Detecção de campo adicionado
- ✅ Detecção de campo removido (com/sem dados)
- ✅ Detecção de mudança de tipo
- ✅ Detecção de mudança em flag required
- ✅ Detecção de mudança de backend
- ✅ Lógica de confirmação
- ✅ Compatibilidade de tipos
- ✅ Geração de sumário de mudanças

#### Testes Existentes (16 testes)
- ✅ Todos os 16 testes originais continuam passando
- ✅ Zero regressões funcionais
- ✅ Compatibilidade total com TXT backend

---

### Documentation

#### 📚 Nova Documentação Completa

**Novo arquivo:**
- **`docs/Manual.md`** - Manual completo de configuração JSON (470+ linhas)
  - Explicação de todos os backends (8 tipos)
  - Guia completo de `persistence.json`
  - Documentação de `schema_history.json`
  - Referência de 20 tipos de campo
  - Exemplos práticos de migração
  - Boas práticas e troubleshooting

**Arquivos atualizados:**
- `README.md` - Adicionadas features de persistência
- `CLAUDE.md` - Arquitetura de persistência documentada
- `docs/dynamic_forms.md` - Informações sobre backends
- `docs/prompts.md` - Prompts 20-23 adicionados
- `docs/roadmap.md` - Fase 1.5 marcada como completa
- `CHANGELOG.md` - Esta entrada

---

### Geração de Dados de Exemplo

#### 🎲 Sample Data Generation
- Script automatizado para popular formulários com dados realistas
- Gerados 139 registros distribuídos em 8 formulários:
  - contatos: 23 registros
  - produtos: 17 registros
  - financeiro/contas: 23 registros
  - financeiro/pagamentos: 15 registros
  - rh/funcionarios: 20 registros
  - rh/departamentos/areas: 11 registros
  - usuarios: 19 registros
  - formulario_completo: 11 registros

#### Benefícios
- Dados realistas para demonstração
- Testes manuais mais efetivos
- Validação de migrações com volume de dados

---

### Breaking Changes & Compatibility

#### ⚠️ Mudanças na API Interna

**VibeCForms.py - Refatoração de Persistência**:
- Funções `read_forms()` e `write_forms()` agora usam RepositoryFactory
- Adicão de lógica de detecção de mudanças em `read_forms()`
- Novas rotas: `/migrate/confirm/<form_path>` e `/migrate/execute/<form_path>`

**Compatibilidade**:
- ✅ Backward compatible - TXT backend continua funcionando
- ✅ Dados existentes preservados (23+17 registros migrados com sucesso)
- ✅ Todos os 16 testes originais passando
- ✅ Zero breaking changes na interface do usuário

#### Migração Suave
- Sistema detecta automaticamente formulários usando TXT
- Migração para SQLite é opt-in via `persistence.json`
- Backup automático garante segurança dos dados

---

### Implementation Timeline

#### Fase 1.5 - SQLite + Migração (Completa) ✅
- **Duração**: ~3 dias
- **Commits**: 15+ commits
- **Linhas adicionadas**: ~1.200 linhas
- **Arquivos criados**: 8 novos arquivos (adapters, managers, tests)
- **Migrações realizadas**: 2 (contatos, produtos)
- **Dados migrados**: 40 registros (100% integridade)

#### Prompts de Implementação
- **Prompt 20**: Implementação inicial do sistema de persistência
- **Prompt 21**: Geração de dados de exemplo (139 registros)
- **Prompt 22**: Correções de bugs de migração e testes
- **Prompt 23**: Criação de testes unitários completos

---

### Summary of Changes

**Arquivos Criados:**
- `src/persistence/base_repository.py` - Interface base
- `src/persistence/repository_factory.py` - Factory pattern
- `src/persistence/migration_manager.py` - Gerenciador de migrações
- `src/persistence/schema_detector.py` - Detector de mudanças
- `src/persistence/adapters/txt_adapter.py` - TxtRepository refatorado
- `src/persistence/adapters/sqlite_adapter.py` - SQLiteRepository novo
- `src/config/persistence.json` - Configuração de backends
- `src/config/schema_history.json` - Histórico automático (gerado)
- `tests/test_sqlite_adapter.py` - 10 testes
- `tests/test_backend_migration.py` - 6 testes
- `tests/test_change_detection.py` - 13 testes
- `docs/Manual.md` - Manual completo de configuração (470+ linhas)

**Arquivos Modificados:**
- `src/VibeCForms.py` - Integração com RepositoryFactory e sistema de migração
- `README.md` - Features de persistência
- `CLAUDE.md` - Arquitetura documentada
- `docs/dynamic_forms.md` - Informações de backend
- `docs/prompts.md` - Prompts 20-23
- `docs/roadmap.md` - Fase 1.5 completa
- `CHANGELOG.md` - Esta entrada

**Diretórios Criados:**
- `src/persistence/` - Sistema de persistência
- `src/persistence/adapters/` - Implementações de backend
- `src/backups/migrations/` - Backups de migrações

**Métricas:**
- Backends suportados: 8 (1 refatorado, 1 implementado, 6 configurados)
- Testes novos: 29 (41 total)
- Linhas de código: +1.200 linhas
- Documentação: +470 linhas (Manual.md)
- Dados migrados: 40 registros (100% sucesso)

---

### Next Steps (Roadmap)

Ver `docs/roadmap.md` para planos futuros:
- **Fase 2**: MySQL + PostgreSQL (RDBMS completo)
- **Fase 3**: MongoDB (NoSQL)
- **Fase 4**: CSV + JSON + XML (Formatos de arquivo)
- **Fase 5**: Interface web de administração

---

## Version 2.4.0 - UUID Search Integration & Generic API (2025-12-15)

### Overview
This version implements a complete overhaul of the search field system, adding UUID-based relationship support and a generic API that automatically adapts to any entity. The new dual-field architecture allows users to search and select records by name while the system transparently stores UUID references, maintaining data integrity in 1:N relationships.

**Key Achievements:**
- 200 lines of duplicated code replaced with 64-line generic solution
- Zero configuration required - auto-detects display fields from specs
- Full keyboard navigation support (↑↓, Enter, ESC)
- Compatible with both TXT and SQLite backends
- All 133 tests passing (0 failures, 4 skipped)

---

### Enhancement #1: Generic Search API with UUID Support

#### 🔍 Auto-Detecting Generic Search Endpoint
Replaced 8+ hardcoded search endpoints with a single parameterized route that automatically detects the appropriate display field from each entity's spec.

**New generic API endpoint:**
```python
@forms_bp.route("/api/search/<datasource>")
def api_search_generic(datasource):
    """Generic API endpoint to search any entity with autocomplete.

    Automatically detects the primary display field from the spec
    (first required text field) and returns results as
    {record_id, label} pairs for UUID-based relationships.
    """
```

**Auto-Detection Logic:**
- Scans spec for first required text field (text, email, tel, url, search)
- Falls back to first text field if no required text field exists
- No hardcoded field names - works with any entity structure

**UUID-based Response Format:**
```json
[
  {"record_id": "5GHJJD0E2197X85MASWYNSPREYT", "label": "ANVISA"},
  {"record_id": "7KMNPR2G4TS9X12VWBYTE45Q", "label": "INMETRO"}
]
```

**Benefits:**
- **Maintainability**: 200 lines of duplicated code eliminated
- **Scalability**: Built-in LIMIT 5 for performance
- **Flexibility**: Works automatically for new entities
- **Data Integrity**: Stores UUIDs, not index positions

**Files Modified:**
- `src/controllers/forms.py` (lines 733-800) - Added generic search endpoint
- Removed 8 hardcoded endpoints (contatos, clientes, fornecedores, produtos, etc.)

---

### Enhancement #2: Enhanced Search Autocomplete Template

#### 🎨 Dual-Field Architecture with Keyboard Navigation
Complete rewrite of search autocomplete template from HTML5 datalist (52 lines) to custom dropdown UI (182 lines) with full keyboard support.

**New Features:**
- **Dual Fields**: Visible input for display name + hidden input for UUID
- **Real-time Dropdown**: Up to 5 suggestions in custom dropdown (not datalist)
- **Keyboard Navigation**:
  - ↑↓ arrow keys to navigate suggestions
  - Enter to select highlighted suggestion
  - ESC to close dropdown
- **Debounced Search**: 200ms delay reduces API load
- **Visual Feedback**: Active state highlighting during keyboard navigation
- **Smart Clearing**: Clears UUID when display field is emptied

**Template Structure:**
```html
<!-- Visible field: user types and selects by name -->
<input type="text" id="field_name_display" placeholder="Digite para buscar...">

<!-- Hidden field: stores UUID for form submission -->
<input type="hidden" name="field_name" id="field_name" value="UUID">

<!-- Custom dropdown with suggestions -->
<div id="field_name_suggestions" class="autocomplete-suggestions"></div>
```

**User Experience:**
1. User types "ANV" in visible field
2. API returns `[{"record_id": "5GH...", "label": "ANVISA"}]`
3. Dropdown shows "ANVISA"
4. User selects → visible field shows "ANVISA", hidden field stores UUID
5. Form submits UUID, maintaining referential integrity

**Files Modified:**
- `src/templates/fields/search_autocomplete.html` - Complete rewrite (52→182 lines)
- `examples/analise-laboratorial/templates/fields/search_autocomplete.html` - Updated

**Migration Note:**
Business cases with custom templates must update their `templates/fields/search_autocomplete.html` by copying from `src/templates/fields/search_autocomplete.html`.

---

### Technical Implementation

**Repository Integration:**
- Uses `_record_id` field (standard from SQLiteAdapter)
- Case-insensitive substring matching
- Compatible with BaseRepository interface

**API Example:**
```bash
curl "http://127.0.0.1:5000/api/search/acreditadores?q=anv"
# Returns: [{"record_id":"5GHJJD0E2197X85MASWYNSPREYT","label":"ANVISA"}]
```

**Spec Format:**
```json
{
  "name": "matriz_amostra",
  "label": "Matriz da Amostra",
  "type": "search",
  "datasource": "matriz_amostras",
  "required": true
}
```

**How It Works:**
1. User types in `matriz_amostra_display` field
2. JavaScript fetches `/api/search/matriz_amostras?q=<query>`
3. API auto-detects display field from `matriz_amostras` spec
4. Returns up to 5 matching records with UUIDs
5. User selects → hidden `matriz_amostra` field receives UUID
6. Form submits UUID to maintain relationship integrity

---

### Testing & Validation

**API Tests:**
```bash
✓ curl "/api/search/acreditadores?q=anv" → Returns ANVISA with UUID
✓ curl "/api/search/clientes?q=couves" → Returns Fazenda Couves Verdes
✓ curl "/api/search/metodologias?q=coli" → Returns 2 E. coli matches
```

**Unit Tests:**
- 133 tests passed, 0 failures, 4 skipped
- Zero regressions introduced
- All existing functionality preserved

**Code Quality:**
- Linter formatted 2 files (forms.py, sqlite_adapter.py)
- No style violations

---

## Version 2.3.1 - Search Autocomplete & Responsive Tables

### Overview
This version adds dynamic search with autocomplete functionality and improves table responsiveness for better mobile/narrow screen support.

---

### Enhancement #1: Search Field with Autocomplete

#### 🔍 Dynamic Search with Datasource
- Added support for search fields with autocomplete from external datasources
- New API endpoint `/api/search/contatos` for querying contact names
- Real-time suggestions as users type (with 300ms debounce)
- Uses HTML5 datalist for native browser autocomplete

#### Implementation
**New template:**
- `src/templates/fields/search_autocomplete.html` - Search field with AJAX autocomplete

**New API endpoint:**
```python
@app.route("/api/search/contatos")
def api_search_contatos():
    """API endpoint to search contacts by name."""
    query = request.args.get('q', '').strip().lower()
    # Returns JSON array of matching contact names
```

**Field specification:**
```json
{
  "name": "contato_favorito",
  "label": "Contato Favorito",
  "type": "search",
  "datasource": "contatos",
  "required": false
}
```

**Enhanced function:**
- `generate_form_field()` - Detects search fields with `datasource` attribute and uses autocomplete template

#### Benefits
- Interactive user experience with real-time suggestions
- Case-insensitive substring matching
- Debounced requests for performance
- Reusable pattern for other datasources
- Native browser autocomplete support

---

### Enhancement #2: Responsive Table with Horizontal Scroll

#### 📱 Improved Table Display
- Added table wrapper with horizontal scroll
- Tables no longer break layout on narrow screens or with many columns
- Minimum table width of 600px for readability
- Smooth scrolling experience

#### CSS Implementation
```css
.table-wrapper {
    width: 100%;
    overflow-x: auto;
    margin-top: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    min-width: 600px;
}
```

**Updated template:**
- `src/templates/form.html` - Wrapped table in scrollable div

#### Benefits
- Responsive design for all screen sizes
- No horizontal page scrolling
- Preserves table layout and readability
- Works seamlessly with forms having 20+ columns

---

### Testing & Quality Assurance

#### ✅ All Tests Passing
- Total: 16 unit tests
- All existing tests continue to pass
- No functional regressions

#### Manual Testing
- ✅ Autocomplete working in `formulario_completo` form
- ✅ API endpoint returning correct results
- ✅ Table scroll working on all forms
- ✅ Responsive behavior verified

---

### Summary of Changes

**Files Added:**
- `src/templates/fields/search_autocomplete.html` - Autocomplete search field

**Files Modified:**
- `src/VibeCForms.py` - Added API endpoint and autocomplete detection
- `src/templates/form.html` - Added table wrapper for horizontal scroll
- `src/specs/formulario_completo.json` - Changed "busca" to "contato_favorito" with datasource

**Updated Documentation:**
- `README.md` - Updated field types list
- `CLAUDE.md` - Added search autocomplete documentation
- `CHANGELOG.md` - This entry

---

## Version 2.3.0 - Complete HTML5 Field Type Support

### Overview
This version expands field type support from 8 to 20 types, achieving 100% HTML5 input coverage. All standard HTML5 input types and form elements are now supported.

---

### Enhancement: Complete Field Type Coverage

#### 🎨 New Field Templates
Created 4 new field-specific templates:
- `src/templates/fields/select.html` - Dropdown selection with options
- `src/templates/fields/radio.html` - Radio button groups
- `src/templates/fields/color.html` - Color picker with live hex display
- `src/templates/fields/range.html` - Slider with live value display

#### 📝 All 20 HTML5 Field Types Now Supported

**Basic Input Types (7):**
- text, tel, email, number, password, url, search

**Date/Time Types (5):**
- date, time, datetime-local, month, week

**Selection Types (3):**
- select (dropdown), radio (radio buttons), checkbox

**Advanced Types (2):**
- color (color picker), range (slider)

**Other Types (3):**
- textarea, hidden, search with autocomplete

#### Implementation Details

**Enhanced function:**
- `generate_form_field()` - Extended to handle all 20 field types
  - Select/radio: Support for `options` array
  - Range: Support for `min`, `max`, `step` attributes
  - Color: Live hex value display
  - Search: Autocomplete when `datasource` specified

**Enhanced function:**
- `generate_table_row()` - Smart display for different field types
  - Select/Radio: Shows label instead of value
  - Color: Displays color swatch + hex code
  - Password: Masked as "••••••••"
  - Hidden: Not displayed in tables

#### Field Specification Examples

**Select field:**
```json
{
  "name": "estado",
  "type": "select",
  "options": [
    {"value": "SP", "label": "São Paulo"},
    {"value": "RJ", "label": "Rio de Janeiro"}
  ],
  "required": true
}
```

**Radio field:**
```json
{
  "name": "genero",
  "type": "radio",
  "options": [
    {"value": "M", "label": "Masculino"},
    {"value": "F", "label": "Feminino"}
  ],
  "required": true
}
```

**Range field:**
```json
{
  "name": "prioridade",
  "type": "range",
  "min": 1,
  "max": 10,
  "step": 1,
  "required": false
}
```

**Color field:**
```json
{
  "name": "cor_favorita",
  "type": "color",
  "required": false
}
```

#### Example Form

**New comprehensive example:**
- `src/specs/formulario_completo.json` - Demonstrates all 20 field types in a single form

#### Benefits
- Complete HTML5 form element support
- Rich user interface options
- Interactive fields (color picker, range slider)
- Consistent rendering across all field types
- Backward compatible - existing forms continue to work
- Prepared for any form design requirement

---

### Testing & Quality Assurance

#### ✅ All Tests Passing
- Total: 16 unit tests
- All existing tests continue to pass
- Zero breaking changes - fully backward compatible

#### Manual Testing
- ✅ All 20 field types rendering correctly
- ✅ Select dropdowns working
- ✅ Radio buttons functioning properly
- ✅ Color picker displaying and updating
- ✅ Range slider showing live values
- ✅ Table display showing appropriate values for each type

---

### Summary of Changes

**Files Added:**
- `src/templates/fields/select.html` - Dropdown field template
- `src/templates/fields/radio.html` - Radio button group template
- `src/templates/fields/color.html` - Color picker template
- `src/templates/fields/range.html` - Range slider template
- `src/specs/formulario_completo.json` - Comprehensive example with all field types

**Files Modified:**
- `src/VibeCForms.py` - Extended `generate_form_field()` and `generate_table_row()`
- `CLAUDE.md` - Updated with complete field type documentation
- `README.md` - Updated feature list

**Field Type Coverage:**
- Before: 8 types (40%)
- After: 20 types (100%)

---

## Version 2.2.0 - Code Quality Improvements (PR #6)

### Overview
This version implements five major improvements focusing on better configuration, maintainability, and following Flask best practices. Improvements #1-3 were suggested in PR #5 code review, while #4-5 further enhance the template system and user experience. All changes maintain backward compatibility with existing functionality.

---

### Improvement #1: Icon Support in Form Specs

#### 🎨 Custom Icons Per Form
- Added optional `icon` field in form specification JSON files
- Icons specified using Font Awesome class names (e.g., "fa-address-book")
- Forms without icons fall back to default "fa-file-alt"
- Icons are displayed in both sidebar menu and main page cards

#### Implementation
**Spec file format:**
```json
{
  "title": "Agenda Pessoal",
  "icon": "fa-address-book",
  "fields": [...]
}
```

**Updated functions:**
- `scan_specs_directory()` - Reads icon from spec files
- Menu and card generation automatically use specified icons

#### Benefits
- More intuitive visual identification of forms
- Eliminates hardcoded icon mappings
- Each form can have its own unique icon
- Maintains consistency across navigation and landing page

---

### Improvement #2: Folder Configuration System

#### 📁 _folder.json Configuration Files
- Created standardized configuration for folders via `_folder.json`
- Supports custom names, descriptions, icons, and display order
- Provides better organization and metadata for categories

#### Configuration Format
**src/specs/financeiro/_folder.json:**
```json
{
  "name": "Financeiro",
  "description": "Gestão financeira e contábil",
  "icon": "fa-dollar-sign",
  "order": 1
}
```

**src/specs/rh/_folder.json:**
```json
{
  "name": "Recursos Humanos",
  "description": "Gestão de pessoas e departamentos",
  "icon": "fa-users",
  "order": 2
}
```

#### Implementation
**New function:**
- `load_folder_config(folder_path)` - Loads _folder.json configuration

**Updated function:**
- `scan_specs_directory()` - Reads folder config and applies customization

**Features:**
- Custom folder display names (e.g., "Recursos Humanos" instead of "Rh")
- Optional descriptions for documentation
- Custom icons override default mapping
- Order field for sorting menu items

#### Benefits
- Declarative folder configuration
- No code changes needed to customize folders
- Better documentation through descriptions
- Flexible display order control
- Scales well for large category structures

---

### Improvement #3: Template System

#### 🎨 Jinja2 Template Separation
- Separated HTML templates from Python code for better maintainability
- Created `src/templates/` directory with three Jinja2 templates:
  * `index.html` - Landing page with form cards grid (99 lines)
  * `form.html` - Main CRUD form page with sidebar (124 lines)
  * `edit.html` - Edit form page (101 lines)
- Migrated from `render_template_string()` to `render_template()`
- Removed three template functions (~338 lines of embedded HTML)

---

### Improvement #4: Field Template System

#### 🎨 Individual Field Templates
- Further modularized templates by creating individual field templates
- Created `src/templates/fields/` directory with three field-specific templates:
  * `input.html` - For text, tel, email, number, password, date input fields
  * `textarea.html` - For textarea fields
  * `checkbox.html` - For checkbox fields
- Refactored `generate_form_field()` to load and render field templates dynamically
- Complete separation of field HTML from Python code

#### New Field Types
- Added support for `password` input type (masked character input)
- Added support for `date` input type (date picker)
- Total of 8 field types now supported

#### Implementation
**Template loading:**
```python
def generate_form_field(field, form_data=None):
    template_path = os.path.join(TEMPLATE_DIR, "fields")

    if field_type == "checkbox":
        template_file = os.path.join(template_path, "checkbox.html")
    elif field_type == "textarea":
        template_file = os.path.join(template_path, "textarea.html")
    else:
        # Supports: text, tel, email, number, password, date
        template_file = os.path.join(template_path, "input.html")
```

**Example spec created:**
- `src/specs/usuarios.json` - User registration form demonstrating password and date fields

#### Benefits
- Individual field templates for maximum flexibility
- Easy to customize appearance per field type
- Reduced coupling between HTML and Python
- Prepared for adding new field types
- Consistent field rendering across all forms

---

### Improvement #5: Form Layout Enhancement

#### 📐 Improved Form Field Layout
- Refined CSS layout for better visual organization
- Fields arranged vertically (stacked one below another)
- Label and input aligned horizontally within each field
- Labels with fixed width (180px) for consistent alignment
- Inputs expand to fill remaining horizontal space
- Applied consistently to both form and edit pages

#### CSS Implementation
```css
form { display: flex; flex-direction: column; gap: 15px; }
label { font-weight: bold; min-width: 180px; }
input, textarea { flex: 1; }
.form-row { display: flex; align-items: center; gap: 10px; }
```

#### Benefits
- Professional, aligned appearance
- Easy to scan and fill out forms
- Responsive design maintained
- Consistent across all form types

---

### Code Quality Metrics

#### 📊 Overall Code Reduction
- `VibeCForms.py` reduced from 925 to 587 lines (-36.5%)
- Better separation of concerns (logic vs presentation)
- Improved syntax highlighting and code formatting
- Follows Flask best practices

#### Implementation Details

**Before:**
```python
from flask import Flask, render_template_string
app = Flask(__name__)

def get_main_template():
    return """<html>...</html>"""

@app.route("/")
def index():
    return render_template_string(get_main_template(), ...)
```

**After:**
```python
from flask import Flask, render_template
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=TEMPLATE_DIR)

@app.route("/")
def index():
    return render_template('index.html', ...)
```

#### Benefits
- Easier template maintenance and modification
- Better IDE support for HTML/CSS/JavaScript
- Clear separation between business logic and presentation
- Standard Flask architecture pattern
- Prepares codebase for future UI enhancements

---

### Testing & Quality Assurance

#### ✅ All Tests Passing
- Total: 16 unit tests
- New tests for folder configuration (`test_folder_config_loading`, `test_folder_items_use_config`)
- New tests for icon support (`test_icon_from_spec`, `test_icon_in_menu_items`)
- All existing tests updated and passing
- No functional regressions

#### Manual Testing
- ✅ All forms accessible and functional
- ✅ Icons displaying correctly in menu and cards
- ✅ Folder configurations applied properly
- ✅ Menu sorted by order field
- ✅ Templates rendering correctly
- ✅ CRUD operations working as expected

---

### Summary of Changes

**Files Added:**
- `src/templates/index.html` - Landing page template
- `src/templates/form.html` - Main form template
- `src/templates/edit.html` - Edit form template
- `src/templates/fields/input.html` - Input field template
- `src/templates/fields/textarea.html` - Textarea field template
- `src/templates/fields/checkbox.html` - Checkbox field template
- `src/specs/usuarios.json` - User registration form example
- `src/specs/financeiro/_folder.json` - Financial folder config
- `src/specs/rh/_folder.json` - HR folder config
- `src/specs/rh/departamentos/_folder.json` - Departments folder config

**Files Modified:**
- `src/VibeCForms.py` - Reduced from 925 to 587 lines, refactored `generate_form_field()`
- `src/templates/form.html` - Updated CSS for improved layout
- `src/templates/edit.html` - Updated CSS for improved layout
- All spec files - Added icon fields
- `tests/test_form.py` - Added new tests for folder config and icons
- `CLAUDE.md` - Updated documentation
- `docs/prompts.md` - Added Prompt 16 documentation

**Lines of Code:**
- Removed: ~338 lines of embedded HTML
- Added: ~324 lines of template files
- Net reduction: ~14 lines, but significantly improved structure

---

## Version 2.0 - Dynamic Forms Implementation

### Major Changes

#### 🎯 Dynamic Form Generation
- Forms are now generated dynamically from JSON specification files
- No code changes needed to create new forms
- URL-based routing with form name in the path (e.g., `/contatos`, `/produtos`)

#### 🗂️ New Architecture

**Spec Files (`src/specs/`):**
- Each form is defined by a JSON spec file
- Specs define fields, types, labels, and validation messages
- Supports multiple field types: text, tel, email, number, checkbox, textarea

**URL Structure:**
- Changed from `/` to `/<form_name>`
- Example: `/contatos` for contacts, `/produtos` for products
- Each form has its own data file: `<form_name>.txt`

**Route Patterns:**
- `GET/POST /<form_name>` - Main form view
- `GET/POST /<form_name>/edit/<idx>` - Edit entry
- `GET /<form_name>/delete/<idx>` - Delete entry

#### 📝 New Functions

1. **`load_spec(form_name)`** - Load and validate JSON spec files
2. **`get_data_file(form_name)`** - Get data file path for a form
3. **`read_forms(spec, data_file)`** - Read forms based on spec (now requires spec parameter)
4. **`write_forms(forms, spec, data_file)`** - Write forms based on spec (now requires spec parameter)
5. **`generate_form_field(field, form_data)`** - Generate HTML for form fields dynamically
6. **`generate_table_headers(spec)`** - Generate table headers from spec
7. **`generate_table_row(form_data, spec, idx, form_name)`** - Generate table rows dynamically
8. **`validate_form_data(spec, form_data)`** - Dynamic validation based on spec
9. **`get_main_template()`** - Returns main page template
10. **`get_edit_template()`** - Returns edit page template

#### 🔄 Migration & Compatibility

- `registros.txt` copied to `contatos.txt` for backward compatibility
- Old routes (`/`, `/edit/<idx>`, `/delete/<idx>`) redirect to `/contatos/*`
- Root URL `/` redirects to `/contatos`

#### ✨ New Features

**Supported Field Types:**
- `text` - Standard text input
- `tel` - Telephone input
- `email` - Email input
- `number` - Numeric input
- `checkbox` - Boolean checkbox
- `textarea` - Multi-line text area

**Dynamic Validation:**
- Required field validation
- Custom validation messages per field
- All-empty validation message

#### 📦 Example Specs Included

1. **contatos.json** - Contact management form (nome, telefone, whatsapp)
2. **produtos.json** - Product catalog form (nome, categoria, preco, descricao, disponivel)

#### 🧪 Updated Tests

All tests updated to work with the new dynamic architecture:
- `test_write_and_read_forms()` - Now uses spec parameter
- `test_update_form()` - Updated for spec-based forms
- `test_delete_form()` - Updated for spec-based forms
- `test_validation()` - New test for dynamic validation
- `test_load_spec()` - New test for spec loading

All tests passing ✅

#### 📚 New Documentation

- **docs/dynamic_forms.md** - Complete guide for creating dynamic forms
- Updated README.md with new features and usage instructions
- This CHANGELOG.md

### Breaking Changes

⚠️ **API Changes:**
- `read_forms()` now requires `(spec, data_file)` parameters
- `write_forms()` now requires `(forms, spec, data_file)` parameters
- Default route changed from `/` to `/<form_name>`

### How to Upgrade

If you have existing code using the old functions:

**Old:**
```python
forms = read_forms()
write_forms(forms)
```

**New:**
```python
spec = load_spec('contatos')
data_file = get_data_file('contatos')
forms = read_forms(spec, data_file)
write_forms(forms, spec, data_file)
```

### Next Steps

See [docs/roadmap.md](docs/roadmap.md) for planned future enhancements.
