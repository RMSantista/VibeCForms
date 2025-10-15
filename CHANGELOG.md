# Changelog

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
