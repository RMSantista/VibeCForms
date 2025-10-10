# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeCForms is a Flask-based dynamic form management system built as an exploration of "Vibe Coding" - AI-assisted development. The project serves as both a functional CRUD application and a learning journey documenting how to build software with AI assistance.

The system generates forms dynamically from JSON specification files, supports hierarchical navigation, and requires no code changes to add new forms.

## Core Architecture

### Template System (Version 2.1 - Improvement #3)
The application uses Flask's standard template system with Jinja2 templates separated into dedicated files in `src/templates/`:
- `index.html` - Landing page with form cards grid (99 lines)
- `form.html` - Main CRUD form page with sidebar navigation (124 lines)
- `edit.html` - Edit form page (101 lines)

This separation improves maintainability and follows Flask best practices by keeping HTML/CSS/JavaScript separate from Python logic in `src/VibeCForms.py` (now 587 lines, down from 925).

### Dynamic Form Generation
Forms are defined by JSON specification files in `src/specs/`:

**Form Specification Format:**
```json
{
  "title": "Form Title",
  "icon": "fa-icon-name",
  "fields": [
    {"name": "field", "label": "Label", "type": "text", "required": true}
  ],
  "validation_messages": {
    "all_empty": "Message for all empty",
    "field": "Field-specific message"
  }
}
```

**Icon Support (Version 2.1 - Improvement #1):**
- Optional `icon` field in spec files (e.g., "fa-address-book")
- Icons display in menu and landing page cards
- Falls back to "fa-file-alt" if not specified

### Folder Configuration System (Version 2.1 - Improvement #2)
Folders can be customized via `_folder.json` files:

```json
{
  "name": "Display Name",
  "description": "Optional description",
  "icon": "fa-icon-name",
  "order": 1
}
```

**Features:**
- Custom folder names (e.g., "Recursos Humanos" instead of "Rh")
- Optional descriptions for documentation
- Custom icons override default mappings
- Order field for sorting menu items

### Data Persistence
Data is stored in semicolon-delimited text files, one per form:
- `src/contatos.txt` - Contact data
- `src/financeiro_contas.txt` - Financial accounts data
- etc.

File names are derived from form paths with slashes replaced by underscores.

The application uses spec-aware functions for data operations:
- `read_forms(spec, data_file)`: Reads and parses data based on spec
- `write_forms(forms, spec, data_file)`: Writes data according to spec

### Route Structure
- `/` (GET): Main landing page with all forms as cards
- `/<path:form_name>` (GET/POST): Dynamic form page (supports nested paths)
- `/<path:form_name>/edit/<int:idx>` (GET/POST): Edit form entry
- `/<path:form_name>/delete/<int:idx>` (GET): Delete form entry

**Examples:**
- `/contatos` - Root level form
- `/financeiro/contas` - Nested form
- `/rh/departamentos/areas` - Multi-level nested form

All operations use the index position in the forms list (not a unique ID) to identify records.

## Development Commands

### Install dependencies
```bash
uv sync
```

### Run the application (development mode)
```bash
uv run hatch run dev
```
The server starts on `http://0.0.0.0:5000` with debug mode enabled

### Run the application (production mode with Gunicorn)
```bash
uv run hatch run serve
```
Runs with 4 workers on `http://0.0.0.0:5000`

### Run all tests
```bash
uv run hatch run test
```

### Run a specific test
```bash
uv run pytest tests/test_form.py::test_write_and_read_forms
```

### Run tests with verbose output
```bash
uv run pytest -v
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

## Testing Approach

Tests in `tests/test_form.py` (16 total) import functions directly from `VibeCForms.py` and use pytest's `tmp_path` fixture to create temporary data files.

**Test Coverage:**
- Form read/write operations with specs
- CRUD operations (create, update, delete)
- Dynamic validation based on specs
- Spec file loading and validation
- Icon support in specs
- Folder configuration loading
- Menu generation with icons
- Hierarchical menu structure
- Sorting by order field

All tests pass without functional regressions.

## Important Constraints

### Validation Rules
Validation messages are defined in each form's spec file under `validation_messages`:
- `all_empty`: Message when all required fields are empty
- `<field_name>`: Field-specific validation message

The `validate_form_data(spec, form_data)` function processes validation dynamically based on the spec.

### Data Integrity
Since records are identified by index position rather than unique IDs, concurrent edits or deletions can cause race conditions. The application is designed for single-user local use.

### Adding New Forms
To add a new form, simply:
1. Create a JSON spec file in `src/specs/` (optionally in a subfolder)
2. Include optional `icon` field for custom icon
3. The form will automatically appear in the menu and landing page
4. Data will be persisted to `<form_path_with_underscores>.txt`

### Customizing Folders
To customize a folder:
1. Create `_folder.json` in the folder
2. Specify `name`, `description`, `icon`, and `order`
3. The menu will automatically use these settings

## Recent Improvements (Version 2.1)

### Improvement #1: Icon Support
- Added optional `icon` field to form specs
- Eliminates hardcoded icon mappings
- Icons display consistently in menu and cards

### Improvement #2: Folder Configuration
- Added `_folder.json` for declarative folder config
- Supports custom names, descriptions, icons, and sort order
- No code changes needed for customization

### Improvement #3: Template System
- Separated HTML into dedicated template files
- Reduced main file from 925 to 587 lines (-36.5%)
- Better IDE support and maintainability
- Follows Flask best practices

## Future Evolution

The project roadmap (see `docs/roadmap.md`) includes plans for additional features. When working on new features, consider:
- Maintain backward compatibility with existing spec format
- Document all AI prompts and interactions in `docs/prompts.md` (in Portuguese)
- Add tests for new functionality
- Update relevant documentation files
