# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeCForms is a Flask-based dynamic form management system built as an exploration of "Vibe Coding" - AI-assisted development. The project serves as both a functional CRUD application and a learning journey documenting how to build software with AI assistance.

The system generates forms dynamically from JSON specification files, supports hierarchical navigation, and requires no code changes to add new forms.

## Core Architecture

### Template System (Version 2.2 - Improvement #4)
The application uses Flask's standard template system with Jinja2 templates separated into dedicated files in `src/templates/`:
- `index.html` - Landing page with form cards grid (99 lines)
- `form.html` - Main CRUD form page with sidebar navigation (124 lines)
- `edit.html` - Edit form page (101 lines)

**Field Templates (Version 2.3 - Expanded in Improvement #6):**
Form fields are now rendered using individual templates in `src/templates/fields/`:
- `input.html` - Template for simple input types (text, tel, email, number, password, date, url, search, datetime-local, time, month, week, hidden)
- `textarea.html` - Template for textarea fields
- `checkbox.html` - Template for checkbox fields
- `select.html` - Template for dropdown selection fields
- `radio.html` - Template for radio button groups
- `color.html` - Template for color picker with live hex display
- `range.html` - Template for slider with live value display

The `generate_form_field()` function loads the appropriate template based on field type and renders it using `render_template_string()`. This provides:
- Complete separation of HTML from Python code
- Easy customization of field appearance per type
- Consistent field rendering across all forms
- Better maintainability and testability

This separation improves maintainability and follows Flask best practices by keeping HTML/CSS/JavaScript separate from Python logic in `src/VibeCForms.py`.

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

**Supported Field Types (Version 2.3 - Complete HTML5 Support):**
The system now supports all 20 HTML5 input types and form elements:

**Basic Input Types:**
- `text` - Single-line text input
- `tel` - Telephone number input
- `email` - Email address input with validation
- `number` - Numeric input
- `password` - Password input (masked characters, not displayed in tables)
- `url` - URL input with validation
- `search` - Search input with enhanced UX

**Date and Time Types:**
- `date` - Date picker input
- `time` - Time picker input
- `datetime-local` - Combined date and time picker
- `month` - Month and year picker
- `week` - Week picker

**Selection Types:**
- `select` - Dropdown selection list (requires `options` array)
- `radio` - Radio button group (requires `options` array)
- `checkbox` - Boolean checkbox input

**Advanced Types:**
- `color` - Color picker with live hex value display
- `range` - Slider with live value display (supports `min`, `max`, `step` attributes)

**Other Types:**
- `textarea` - Multi-line text input
- `hidden` - Hidden field (not displayed in forms or tables)

**Field Options Format (for select/radio):**
```json
{
  "name": "field_name",
  "type": "select",
  "options": [
    {"value": "val1", "label": "Label 1"},
    {"value": "val2", "label": "Label 2"}
  ]
}
```

**Range Field Format:**
```json
{
  "name": "priority",
  "type": "range",
  "min": 1,
  "max": 10,
  "step": 1
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

## Recent Improvements

### Version 2.3.1

#### Improvement #7: Search with Autocomplete
- Added support for search fields with dynamic autocomplete from datasources
- New API endpoint `/api/search/contatos` for querying contact names
- Real-time suggestions as users type (300ms debounce for performance)
- Uses HTML5 datalist for native browser autocomplete
- Case-insensitive substring matching
- Created `search_autocomplete.html` template
- Enhanced `generate_form_field()` to detect `datasource` attribute
- Example field in `formulario_completo.json`:
  ```json
  {
    "name": "contato_favorito",
    "label": "Contato Favorito",
    "type": "search",
    "datasource": "contatos",
    "required": false
  }
  ```

**Search with Datasource Format:**
```json
{
  "name": "field_name",
  "type": "search",
  "datasource": "contatos"
}
```

#### Improvement #8: Responsive Table with Horizontal Scroll
- Tables now wrapped in scrollable container (`table-wrapper`)
- Horizontal scroll appears automatically when table exceeds container width
- Minimum table width of 600px for readability
- No more layout breaking on narrow screens or forms with many columns
- Applied to `form.html` template
- Seamless experience on mobile devices

### Version 2.3

#### Improvement #6: Complete HTML5 Field Type Support
- Expanded from 8 to 20 supported field types (100% HTML5 coverage)
- Added 4 new field templates:
  - `select.html` - Dropdown selection with options
  - `radio.html` - Radio button groups with options
  - `color.html` - Color picker with live hex display
  - `range.html` - Slider with live value display
- Enhanced `generate_form_field()` to handle:
  - Options array for select/radio fields
  - Min/max/step attributes for range fields
- Improved `generate_table_row()` to display:
  - Labels instead of values for select/radio
  - Color swatches for color fields
  - Masked display for password fields
  - Hidden fields are not displayed
- Added 12 new input types via `input.html`:
  - `url`, `search`, `datetime-local`, `time`, `month`, `week`, `hidden`
- Created comprehensive example: `formulario_completo.json` demonstrating all 20 field types
- All 16 existing tests continue to pass
- Zero breaking changes - fully backward compatible

### Version 2.2

#### Improvement #4: Field Template System
- Separated field rendering into individual Jinja2 templates
- Created `src/templates/fields/` directory with 3 templates:
  - `input.html` - For text, tel, email, number, password, date fields
  - `textarea.html` - For textarea fields
  - `checkbox.html` - For checkbox fields
- Refactored `generate_form_field()` to use template files
- Complete separation of field HTML from Python logic
- Extended support to include password and date input types
- Created example spec (`usuarios.json`) demonstrating new field types
- All 16 tests continue to pass

#### Improvement #5: Form Layout Enhancement
- Improved form field layout with horizontal label-input alignment
- Fields stacked vertically (one below the other)
- Label and input on the same horizontal line within each field
- Labels with fixed width (180px) for consistent alignment
- Inputs expand to fill remaining space
- Applied consistently to both `form.html` and `edit.html` templates
- Responsive design maintained across different screen sizes

### Version 2.1

#### Improvement #1: Icon Support
- Added optional `icon` field to form specs
- Eliminates hardcoded icon mappings
- Icons display consistently in menu and cards

#### Improvement #2: Folder Configuration
- Added `_folder.json` for declarative folder config
- Supports custom names, descriptions, icons, and sort order
- No code changes needed for customization

#### Improvement #3: Template System
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
