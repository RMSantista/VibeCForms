# Changelog

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
