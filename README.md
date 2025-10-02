# VibeCForms

**VibeCForms** is an open-source project in Python that explores the concept of **Vibe Coding** — programming conducted with Artificial Intelligence.  
The project demonstrates how to build a **simple CRUD web app** (name, phone number, WhatsApp flag) using **only free tools**, with code and tests generated primarily by AI.

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
- ✅ Unit tests implemented with `pytest`.
- ✅ Validations included (no empty records, required name/phone).
- 🎨 Styled with CSS + icons (FontAwesome).
- ✅ **Dynamic form generation** now implemented!
  - Forms are generated from JSON spec files
  - URL-based routing (e.g., `/contatos`, `/produtos`)
  - Support for multiple field types (text, email, number, checkbox, textarea)
  - Automatic validation based on specs  

---

## 📂 Repository Structure
```
VibeCForms/
│
├── src/                      # Main source code
│   ├── VibeCForms.py        # Main application
│   ├── specs/               # Form specification files (JSON)
│   │   ├── contatos.json    # Contacts form spec
│   │   └── produtos.json    # Products form spec (example)
│   ├── contatos.txt         # Contact data storage
│   └── produtos.txt         # Product data storage
│
├── tests/                    # Unit tests
│   └── test_form.py
│
├── docs/                     # Documentation
│   ├── prompts.md           # Prompts (kept in Portuguese)
│   ├── learning_notes.md    # Learning notes and reflections
│   ├── roadmap.md           # Future evolution plan
│   └── dynamic_forms.md     # Dynamic forms guide (NEW!)
│
├── README.md
├── requirements.txt
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
Run the application:

```bash
uv run python src/VibeCForms.py
```
Access in your browser:
- http://localhost:5000/contatos (contacts form)
- http://localhost:5000/produtos (products form - example)

Run tests with:

```bash
uv run pytest
```

### Creating Your Own Form

1. Create a JSON spec file in `src/specs/<form_name>.json`
2. Access `http://localhost:5000/<form_name>`
3. See [docs/dynamic_forms.md](docs/dynamic_forms.md) for detailed instructions

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
A primeira versão entrega um CRUD simples (nome, telefone e WhatsApp) com validações, testes unitários e layout básico.

📌 Toda a documentação de prompts será mantida em português para preservar a originalidade do que foi solicitado à IA.
📌 Este é o meu primeiro projeto publicado, criado totalmente com ferramentas gratuitas.
A ideia é evoluir futuramente para cadastros dinâmicos e servir como guia para iniciantes que também queiram aprender Vibe Coding.

