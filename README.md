# VibeCForms

**VibeCForms** is an open-source project in Python that explores the concept of **Vibe Coding** — programming conducted with Artificial Intelligence.
The project demonstrates how to build a **dynamic form management system** using **only free tools**, with code and tests generated primarily by AI. It features JSON-based form specifications, hierarchical navigation, and a modern web interface.

---

## 🎯 Project Goals
- Explore **Vibe Coding**: coding guided by AI prompts and iterations.  
- Show how to build a working project even as a beginner.  
- Document prompts, results, and learning process as a **guide for others**.  
- Provide a base that can evolve from a **simple form** to **dynamic forms**.  

---

## 🛠️ Tech Stack
- **Python**
- **Flask** (web framework)
- **pytest** (unit testing)
- **SQLite** (embedded database)
- **dotenv** (environment management)
- **VSCode**
- **GitHub Copilot (free version)**
- **ChatGPT (Support and Consulting)** 

---

## 🚧 Current Status
- ✅ First version completed: **simple contact form with CRUD** (create, read, update, delete).
- ✅ Unit tests implemented with `pytest` (41 tests passing).
- ✅ Validations included (no empty records, required name/phone).
- 🎨 Styled with CSS + icons (FontAwesome).

### Latest: Version 4.0 - Workflow System with Kanban
- ✅ **Complete Kanban-Based Workflow System**
  - 5-phase implementation (224 tests, 100% passing)
  - Automatic process creation from forms
  - State management with transitions
  - Prerequisites validation and auto-transitions
  - Real-time workflow analytics

- ✅ **AI-Powered Intelligence**
  - Pattern analysis and clustering
  - Anomaly detection (stuck, delayed, fast-tracked processes)
  - 4 specialized agents (Generic, Pattern, Rule, Orchestrator)
  - Machine learning for duration predictions
  - Risk factor identification

- ✅ **Advanced Features**
  - Interactive Kanban Editor (CRUD operations)
  - Workflow Dashboard with health metrics
  - Multiple export formats (CSV, Excel, PDF)
  - Complete audit trail for compliance
  - Agent performance tracking

- ✅ **Seamless Integration**
  - Forms automatically create workflow processes
  - Bidirectional synchronization (form ↔ process)
  - REST API endpoints (`/workflow/api/*`)
  - Uses same persistence layer (TXT/SQLite)
  - Zero breaking changes (fully optional)

### Version 3.0 - Pluggable Persistence System
- ✅ **Multi-Backend Support (8 backends)**
  - TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML
  - Configurable via `persistence.json`
  - Repository Pattern + Adapter Pattern architecture
  - Factory Pattern for dynamic repository instantiation

- ✅ **Automatic Backend Migration**
  - Detects backend changes automatically
  - User confirmation for migrations with data
  - Complete data migration between backends
  - Automatic backup before migrations
  - Successfully migrated 40 records (contatos: 23, produtos: 17)

- ✅ **Schema Change Detection**
  - MD5 hash-based spec change detection
  - Automatic schema history tracking
  - 4 change types: ADD_FIELD, REMOVE_FIELD, CHANGE_TYPE, CHANGE_REQUIRED
  - Data loss prevention with confirmation dialogs

- ✅ **Comprehensive Test Coverage**
  - 29 new tests (41 total passing, 4 skipped)
  - SQLite adapter tests (10 tests)
  - Backend migration tests (6 tests)
  - Schema change detection tests (13 tests)

- ✅ **Complete Documentation**
  - New `docs/Manual.md` (470+ lines)
  - Complete JSON configuration guide
  - All 8 backends documented with examples
  - Migration workflows and best practices

### Recent Improvements (Version 2.1)
- ✅ **Icon Support in Form Specs**
  - Custom icons per form via JSON spec files
  - Icons display in menu and landing page cards
  - No more hardcoded icon mappings

- ✅ **Folder Configuration System**
  - `_folder.json` files for category customization
  - Custom names, descriptions, icons, and display order
  - Declarative configuration without code changes

- ✅ **Template System**
  - Separation of HTML templates from Python code
  - Jinja2 templates in dedicated `src/templates/` directory
  - Reduced VibeCForms.py from 925 to 587 lines (-36.5%)
  - Better maintainability and follows Flask best practices

### Core Features
- ✅ **Dynamic form generation**
  - Forms are generated from JSON spec files
  - URL-based routing with support for nested paths (e.g., `/contatos`, `/financeiro/contas`)
  - **Complete HTML5 field type support (20 types)**: text, email, tel, number, password, url, search, date, time, datetime-local, month, week, color, range, select, radio, checkbox, textarea, hidden, and search with autocomplete
  - Automatic validation based on specs

- ✅ **Modern Navigation System**
  - 🏠 Main landing page with dynamic form cards
  - 📋 Persistent sidebar menu with hierarchical navigation
  - 📁 Multi-level submenu support (folders as categories)
  - 🎯 Active item highlighting
  - 🔄 Automatic directory scanning for form discovery
  - 🎨 Custom icons for forms and folders  

---

## 📂 Repository Structure
```
VibeCForms/
│
├── src/                           # Main source code
│   ├── VibeCForms.py             # Main application (587 lines)
│   ├── persistence/              # Pluggable persistence system (NEW v3.0)
│   │   ├── base_repository.py    # BaseRepository interface
│   │   ├── repository_factory.py # Factory for repository instantiation
│   │   ├── migration_manager.py  # Backend migration manager
│   │   ├── schema_detector.py    # Schema change detection
│   │   └── adapters/             # Backend implementations
│   │       ├── txt_adapter.py    # TXT backend (refactored)
│   │       └── sqlite_adapter.py # SQLite backend (new)
│   ├── config/                   # Configuration files (NEW v3.0)
│   │   ├── persistence.json      # Backend configurations
│   │   └── schema_history.json   # Automatic schema tracking
│   ├── backups/                  # Automatic backups (NEW v3.0)
│   │   └── migrations/           # Migration backups
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── index.html            # Landing page template
│   │   ├── form.html             # Main CRUD form template
│   │   ├── edit.html             # Edit form template
│   │   └── fields/               # Field-specific templates
│   │       ├── input.html        # Input field template
│   │       ├── textarea.html     # Textarea template
│   │       ├── checkbox.html     # Checkbox template
│   │       ├── select.html       # Select dropdown template
│   │       ├── radio.html        # Radio button template
│   │       ├── color.html        # Color picker template
│   │       └── range.html        # Range slider template
│   ├── specs/                    # Form specification files (JSON)
│   │   ├── contatos.json         # Contacts form spec (with icon)
│   │   ├── produtos.json         # Products form spec (with icon)
│   │   ├── formulario_completo.json # Complete field types demo
│   │   ├── usuarios.json         # User registration form
│   │   ├── financeiro/           # Financial forms category
│   │   │   ├── _folder.json      # Folder configuration
│   │   │   ├── contas.json       # Accounts form
│   │   │   └── pagamentos.json   # Payments form
│   │   └── rh/                   # HR forms category
│   │       ├── _folder.json      # Folder configuration
│   │       ├── funcionarios.json # Employees form
│   │       └── departamentos/    # Departments subcategory
│   │           ├── _folder.json  # Subfolder configuration
│   │           └── areas.json    # Areas form
│   ├── vibecforms.db             # SQLite database (generated)
│   ├── contatos.txt              # Contact data storage (TXT backend)
│   ├── produtos.txt              # Product data storage (TXT backend)
│   ├── financeiro_contas.txt     # Financial accounts data
│   └── rh_funcionarios.txt       # HR employees data
│
├── tests/                         # Unit tests (41 tests passing)
│   ├── test_form.py              # Original form tests (16 tests)
│   ├── test_sqlite_adapter.py    # SQLite adapter tests (10 tests)
│   ├── test_backend_migration.py # Migration tests (6 tests)
│   └── test_change_detection.py  # Schema change tests (13 tests)
│
├── docs/                          # Documentation
│   ├── Manual.md                 # JSON configuration manual (NEW v3.0)
│   ├── prompts.md                # All prompts with detailed results
│   ├── learning_notes.md         # Learning notes and reflections
│   ├── roadmap.md                # Future evolution plan
│   ├── dynamic_forms.md          # Dynamic forms guide
│   └── plano_persistencia.md     # Persistence system plan (v3.0)
│
├── README.md
├── CHANGELOG.md                   # Version history
├── CLAUDE.md                      # Claude Code guidance
├── pyproject.toml                 # Project configuration
├── .gitignore
└── LICENSE
```

---

## 📚 Documentation
- **[docs/Manual.md](docs/Manual.md)** → Complete JSON configuration manual (NEW in v3.0!)
  - Comprehensive guide to all configuration files
  - All 8 backend types explained with examples
  - Form specification reference (20 field types)
  - Migration workflows and best practices
- [docs/prompts.md](docs/prompts.md) → contains the exact prompts used and AI responses.
  > ⚠️ All prompts are **kept in Portuguese** to preserve the originality of the author's interaction with the AI.
- [docs/learning_notes.md](docs/learning_notes.md) → author's notes and reflections while learning.
- [docs/roadmap.md](docs/roadmap.md) → planned next steps and evolution of the project.
- [docs/dynamic_forms.md](docs/dynamic_forms.md) → complete guide on creating dynamic forms.
- [docs/plano_persistencia.md](docs/plano_persistencia.md) → persistence system architecture plan (v3.0).  

---

## ▶️ How to Run
Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/VibeCForms.git
cd VibeCForms
uv sync
uv run pre-commit install  # Install git hooks for code quality checks
```

### Run the application (development mode)
```bash
uv run hatch run dev
```

### Run the application (production mode with Gunicorn)
```bash
uv run hatch run serve
```

Access in your browser:
- http://localhost:5000/ (main page with all forms displayed as cards)
- http://localhost:5000/contatos (contacts form)
- http://localhost:5000/produtos (products form)
- http://localhost:5000/financeiro/contas (nested form example)

The application features:
- **Main Page**: Landing page with all available forms as interactive cards
- **Sidebar Menu**: Persistent left menu with hierarchical navigation (hover over folders to reveal submenus)
- **Dynamic Discovery**: All forms in `src/specs/` are automatically detected and displayed

### Run tests
```bash
uv run hatch run test
```

### Format code
```bash
uv run hatch run format
```

### Check code formatting
```bash
uv run hatch run lint
```

### Run pre-commit hooks
```bash
uv run hatch run check
```

### Creating Your Own Form

**Simple Form (Root Level):**
1. Create a JSON spec file in `src/specs/<form_name>.json`
2. Access `http://localhost:5000/<form_name>`
3. It will appear on the main page and in the sidebar menu

**Organized Form (In Category):**
1. Create a folder in `src/specs/<category>/`
2. Create a JSON spec file in `src/specs/<category>/<form_name>.json`
3. Access `http://localhost:5000/<category>/<form_name>`
4. It will appear under the category folder in the sidebar (hover to reveal)

**Multi-level Organization:**
- You can nest folders indefinitely: `src/specs/rh/departamentos/areas.json`
- Access via: `http://localhost:5000/rh/departamentos/areas`
- Submenus will appear when hovering over parent folders

**Automatic Features:**
- Forms are automatically discovered when you add new spec files
- Icons are assigned based on folder names (financeiro → 💲, rh → 👥)
- Categories are displayed on the main page cards
- Active menu items are highlighted

See [docs/dynamic_forms.md](docs/dynamic_forms.md) for detailed JSON spec format and examples.

---

## 🤝 Contributing

Contributions are welcome!
You can:

Suggest improvements,

Fix issues,

Improve documentation,

Or help evolve towards dynamic forms.

---

## 📌 Personal Note

This is my first open-source project.
I am learning as I build, and my goal is to share both the code and the journey of using AI to develop software from scratch.

---

## 🌍 Português (Resumo)

VibeCForms é um projeto open source em Python que explora o Vibe Coding, ou seja, programação conduzida por IA.

**Funcionalidades Implementadas:**

**Versão 3.0 - Sistema de Persistência Plugável:**
- ✅ Suporte a 8 backends de armazenamento (TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML)
- ✅ Configuração via `persistence.json` sem alterar código
- ✅ Migração automática de dados entre backends
- ✅ Detecção de mudanças em schemas com confirmação de usuário
- ✅ Backup automático antes de migrações
- ✅ 40 registros migrados com sucesso (contatos: 23, produtos: 17)
- ✅ 29 novos testes unitários (41 total passando)
- ✅ Novo manual completo de configuração JSON (470+ linhas)

**Melhorias Recentes (Versão 2.1):**
- ✅ Suporte a ícones personalizados nos specs dos formulários
- ✅ Sistema de configuração de pastas via arquivos `_folder.json`
- ✅ Sistema de templates Jinja2 separados do código Python
- ✅ Redução de 36.5% no tamanho do código principal (925 → 587 linhas)

**Funcionalidades Principais:**
- ✅ Sistema de formulários dinâmicos baseados em especificações JSON
- ✅ Página inicial com cards interativos de todos os formulários
- ✅ Menu lateral persistente com navegação hierárquica
- ✅ Suporte a múltiplos níveis de submenus (pastas como categorias)
- ✅ Descoberta automática de formulários via varredura de diretórios
- ✅ Ícones customizáveis para formulários e pastas
- ✅ CRUD completo (criar, ler, atualizar, deletar) para cada formulário
- ✅ Validações dinâmicas baseadas nas especificações
- ✅ 20 tipos de campos HTML5 suportados
- ✅ 41 testes unitários (todos passando)

📌 Toda a documentação de prompts está mantida em português para preservar a originalidade do que foi solicitado à IA.
📌 Este é o meu primeiro projeto publicado, criado totalmente com ferramentas gratuitas.
📌 O projeto evoluiu de um CRUD simples para um sistema completo de gerenciamento de formulários com navegação hierárquica e persistência plugável.
📌 Serve como guia prático para iniciantes que queiram aprender Vibe Coding — programação com IA.

