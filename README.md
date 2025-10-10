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
- **dotenv** (environment management)  
- **VSCode**  
- **GitHub Copilot (free version)**
- **ChatGPT (Support and Consulting)** 

---

## 🚧 Current Status
- ✅ First version completed: **simple contact form with CRUD** (create, read, update, delete).
- ✅ Unit tests implemented with `pytest` (16 tests passing).
- ✅ Validations included (no empty records, required name/phone).
- 🎨 Styled with CSS + icons (FontAwesome).

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
  - Support for multiple field types (text, email, number, checkbox, textarea)
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
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── index.html            # Landing page template
│   │   ├── form.html             # Main CRUD form template
│   │   └── edit.html             # Edit form template
│   ├── specs/                    # Form specification files (JSON)
│   │   ├── contatos.json         # Contacts form spec (with icon)
│   │   ├── produtos.json         # Products form spec (with icon)
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
│   ├── contatos.txt              # Contact data storage
│   ├── produtos.txt              # Product data storage
│   ├── financeiro_contas.txt     # Financial accounts data
│   └── rh_funcionarios.txt       # HR employees data
│
├── tests/                         # Unit tests (16 tests)
│   └── test_form.py
│
├── docs/                          # Documentation
│   ├── prompts.md                # All prompts with detailed results
│   ├── learning_notes.md         # Learning notes and reflections
│   ├── roadmap.md                # Future evolution plan
│   └── dynamic_forms.md          # Dynamic forms guide
│
├── README.md
├── pyproject.toml                 # Project configuration
├── .gitignore
└── LICENSE
```

---

## 📚 Documentation
- [docs/prompts.md](docs/prompts.md) → contains the exact prompts used and AI responses.
  > ⚠️ All prompts are **kept in Portuguese** to preserve the originality of the author's interaction with the AI.
- [docs/learning_notes.md](docs/learning_notes.md) → author's notes and reflections while learning.
- [docs/roadmap.md](docs/roadmap.md) → planned next steps and evolution of the project.
- **[docs/dynamic_forms.md](docs/dynamic_forms.md)** → complete guide on creating dynamic forms (NEW!)  

---

## ▶️ How to Run
Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/VibeCForms.git
cd VibeCForms
uv sync
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
- ✅ 16 testes unitários (todos passando)

📌 Toda a documentação de prompts está mantida em português para preservar a originalidade do que foi solicitado à IA.
📌 Este é o meu primeiro projeto publicado, criado totalmente com ferramentas gratuitas.
📌 O projeto evoluiu de um CRUD simples para um sistema completo de gerenciamento de formulários com navegação hierárquica.
📌 Serve como guia prático para iniciantes que queiram aprender Vibe Coding — programação com IA.

