# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeCForms is a Flask-based contact management web application built as an exploration of "Vibe Coding" - AI-assisted development. The project serves as both a functional CRUD application and a learning journey documenting how to build software with AI assistance.

## Core Architecture

### Single-File Application
The entire web application resides in `src/VibeCForms.py` using Flask's `render_template_string` pattern. All HTML, CSS, and JavaScript are embedded directly in the Python file rather than separated into template files.

### Data Persistence
Data is stored in a simple text file (`src/registros.txt`) with semicolon-delimited format:
```
Nome;Telefone;WhatsApp
```
The application uses two core functions for all data operations:
- `read_forms()`: Reads and parses the text file into a list of dictionaries
- `write_forms(forms)`: Writes the entire list back to the file

### Route Structure
- `/` (GET/POST): Main page showing contact list and creation form
- `/edit/<int:idx>` (GET/POST): Edit a contact by its index position
- `/delete/<int:idx>` (GET): Delete a contact by its index position

All operations use the index position in the forms list (not a unique ID) to identify records.

## Development Commands

### Install dependencies
```bash
uv sync
```

### Run the application
```bash
uv run python src/VibeCForms.py
```
The server starts on `http://0.0.0.0:5000`

### Run all tests
```bash
uv run pytest
```

### Run a specific test
```bash
uv run pytest tests/test_form.py::test_write_and_read_forms
```

### Run tests with verbose output
```bash
uv run pytest -v
```

## Testing Approach

Tests in `tests/test_form.py` import functions directly from `VibeCForms.py` and use pytest's `tmp_path` fixture to create temporary data files. Tests temporarily override the global `DATA_FILE` variable to avoid interfering with actual data.

Note: The current test setup uses `globals()` to modify `DATA_FILE`, which is not ideal but functional for this simple application.

## Important Constraints

### Validation Rules
Three validation messages are hardcoded in both the main route and edit route:
1. "Não existe cadastro vazio. Informe nome e telefone." (both fields empty)
2. "É obrigatório cadastrar ao menos um nome." (name missing)
3. "O contato deve ter um telefone." (phone missing)

When modifying validation logic, update both routes to maintain consistency.

### Data Integrity
Since contacts are identified by index position rather than unique IDs, concurrent edits or deletions can cause race conditions. The application is designed for single-user local use.

## Future Evolution

The project roadmap (see `docs/roadmap.md`) includes plans to evolve from this static form into a dynamic form generation system. When working on new features, consider:
- The current architecture's simplicity is intentional for learning purposes
- Maintain backward compatibility with the existing text file format if possible
- Document all AI prompts and interactions in `docs/prompts.md` (in Portuguese)
