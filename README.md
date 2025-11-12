# VibeCForms

**VibeCForms** is an AI-first framework for building process tracking systems with seamless human/AI/code collaboration. Built on Python and Flask, it enables rapid development of systems that track multi-step processes (sales pipelines, laboratory workflows, legal case management) through well-defined conventions rather than extensive coding.

---

## 🎯 Vision

Modern business systems need to track processes with multiple steps and states. VibeCForms provides a framework where:

- **AI/Human/Code as Equal Actors** - All actors monitor states (tags), act on objects, and trigger transitions through the same uniform interface
- **Simple Yet Powerful** - Build complex process tracking systems using configurations and conventions, not thousands of lines of code
- **Convention over Configuration, Configuration over Code** - Sensible defaults reduce setup, JSON configuration handles customization, code only for unique logic

---

## 🧭 Core Conventions

VibeCForms provides well-defined conventions that builders can rely on:

1. **1:1 CRUD-to-Table Mapping** - Every form maps directly to one table/storage, no hidden abstractions
2. **Shared Metadata** - UI and database definitions come from the same source, always in sync
3. **Relationship Tables for All Cardinality** - All relationships use relationship tables, regardless of 1:1, 1:N, or N:N
4. **Tags as State** - Object states are represented by tags, making state transitions explicit and trackable
5. **Kanbans for State Transitions** - Visual boards control how objects move between states
6. **Uniform Actor Interface** - Humans, AI agents, and subsystems use the same interface to monitor tags and trigger actions
7. **Tag-Based Notifications** - Simple notification system where any actor can monitor tag changes
8. **Convention over Configuration, Configuration over Code** - Use conventions first, configure when needed, code only for unique logic

---

## 💼 Use Cases

VibeCForms excels at systems that need process tracking with multiple actors:

### Sales Pipeline Management
- **States (Tags)**: Lead → Qualified → Proposal → Negotiation → Closed
- **Actors**:
  - Sales reps move deals between stages (Kanban)
  - AI agent analyzes lead quality and suggests next actions
  - Email subsystem monitors "Proposal" tag and sends follow-ups
  - Notification system alerts manager when deals reach "Negotiation"

### Laboratory Exam Workflow
- **States (Tags)**: Requested → Sample Collected → In Analysis → Results Ready → Delivered
- **Actors**:
  - Lab technicians update sample status (Kanban)
  - AI reviews results and flags anomalies requiring human review
  - Equipment subsystems auto-update when analysis completes
  - Patient portal monitors "Results Ready" tag for notifications

### Legal Case Management
- **States (Tags)**: Filed → Discovery → Motions → Trial → Judgment → Closed
- **Actors**:
  - Attorneys move cases through stages (Kanban)
  - AI assistant monitors deadlines and suggests document templates
  - Court system integration updates filing status
  - Billing system monitors state changes for time tracking

---

## 🏗️ How It Works

VibeCForms implements a clear hierarchy:

### 1. Convention (No Setup Required)
Start building immediately with sensible defaults:
- Create a JSON spec file → instant CRUD form
- Forms auto-map to storage (1:1 mapping)
- Metadata automatically shared between UI and database
- All 20 HTML5 field types supported out of the box

### 2. Configuration (When You Need Customization)
Customize through JSON files, no code required:
- Form specifications define fields, validation, icons
- Folder configurations organize forms hierarchically
- Backend selection (TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML)
- Tag definitions and Kanban board layouts

### 3. Code (Only for Unique Logic)
Write code only when conventions and configuration aren't enough:
- Custom business rules
- External system integrations
- AI agent behaviors
- Complex validations

---

## ⚡ Quick Start

Clone and run:

```bash
git clone https://github.com/rmsantista/VibeCForms.git
cd VibeCForms
uv sync
uv run pre-commit install
uv run hatch run dev
```

Access at `http://localhost:5000`

### Create Your First Form

1. Create `src/specs/customers.json`:
```json
{
  "title": "Customers",
  "icon": "fa-users",
  "fields": [
    {"name": "name", "label": "Name", "type": "text", "required": true},
    {"name": "email", "label": "Email", "type": "email", "required": true},
    {"name": "status", "label": "Status", "type": "select", "options": [
      {"value": "lead", "label": "Lead"},
      {"value": "active", "label": "Active"},
      {"value": "inactive", "label": "Inactive"}
    ]}
  ]
}
```

2. Access `http://localhost:5000/customers` - Your form is ready with full CRUD!

3. No database setup, no migrations, no boilerplate - just works.

See [docs/Manual.md](docs/Manual.md) for complete configuration reference.

---

## 🛠️ Tech Stack

- **Python** with **Flask** (web framework)
- **SQLite** (default), plus support for MySQL, PostgreSQL, MongoDB, TXT, CSV, JSON, XML
- **pytest** (41 tests passing)
- **Jinja2** templates
- **Vibe Coding** - Built with AI assistance (ChatGPT, GitHub Copilot)

---

## 📚 Documentation

- [docs/Manual.md](docs/Manual.md) - Complete configuration reference (470+ lines)
- [docs/prompts.md](docs/prompts.md) - All AI prompts and interactions (Portuguese)
- [docs/learning_notes.md](docs/learning_notes.md) - Learning journey reflections
- [docs/roadmap.md](docs/roadmap.md) - Future evolution plans
- [docs/dynamic_forms.md](docs/dynamic_forms.md) - Dynamic forms guide
- [CLAUDE.md](CLAUDE.md) - AI assistant guidance for building with VibeCForms

---

## 🧪 Testing & Quality

```bash
uv run hatch run test      # Run 41 tests
uv run hatch run format    # Format code
uv run hatch run lint      # Check formatting
uv run hatch run check     # Pre-commit hooks
```

---

## 🤝 Contributing

Contributions welcome! You can:
- Suggest improvements
- Fix issues
- Improve documentation
- Add new features following the conventions

---

## 📌 Personal Note

This is my first open-source project, built entirely with free tools and AI assistance. It started as a learning journey into "Vibe Coding" and evolved into a framework for building process tracking systems. The goal is to show how AI can help anyone build working software, and to provide a foundation that others can build upon.

---

## 🌍 Português (Resumo)

VibeCForms é um framework AI-first para construir sistemas de rastreamento de processos com colaboração fluida entre humanos, IA e código.

### Convenções Principais:
1. **Convenção sobre Configuração, Configuração sobre Código** - Padrões sensatos primeiro, configuração quando necessário, código apenas para lógica única
2. **Mapeamento 1:1 CRUD-Tabela** - Cada formulário mapeia diretamente para uma tabela
3. **Metadados Compartilhados** - UI e banco de dados sempre sincronizados
4. **Tabelas de Relacionamento** - Todos os relacionamentos usam tabelas intermediárias
5. **Tags como Estado** - Estados representados por tags rastreáveis
6. **Kanbans para Transições** - Quadros visuais controlam mudanças de estado
7. **Interface Uniforme** - Humanos, IA e código usam a mesma interface
8. **Notificações Baseadas em Tags** - Sistema simples de monitoramento de mudanças

### Casos de Uso:
- **Pipeline de Vendas**: Lead → Qualificado → Proposta → Negociação → Fechado
- **Exames Laboratoriais**: Solicitado → Coletado → Em Análise → Resultados → Entregue
- **Gestão de Casos Legais**: Protocolado → Investigação → Petições → Julgamento → Encerrado

### Status Atual:
- ✅ 41 testes unitários (todos passando)
- ✅ Sistema de persistência plugável (8 backends: TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML)
- ✅ 20 tipos de campos HTML5 suportados
- ✅ Migração automática entre backends
- ✅ Detecção de mudanças em schemas
- ✅ Sistema de templates Jinja2
- ✅ Navegação hierárquica com ícones customizáveis
- ✅ Documentação completa (470+ linhas)

### Como Começar:
```bash
git clone https://github.com/<seu-usuario>/VibeCForms.git
cd VibeCForms
uv sync
uv run hatch run dev
```

Acesse `http://localhost:5000` e crie seu primeiro formulário em JSON!

📌 Toda a documentação de prompts está em português para preservar a originalidade.
📌 Projeto criado totalmente com ferramentas gratuitas e assistência de IA.
📌 Evolução de CRUD simples para framework completo de rastreamento de processos.
📌 Guia prático para aprender Vibe Coding - programação com IA.
