# Data Preparation and Output Guide for XSLT Templates

This guide covers how to prepare data for XSLT transformation and control HTML output formatting.

## Input Data Format

### Expected JSON Structure

XSLT templates in this skill expect a specific JSON structure matching VibeCForms' data model:

```json
{
  "spec": {
    "title": "Form Title",
    "icon": "fa-icon-name",
    "fields": [
      {
        "name": "field_name",
        "label": "Field Label",
        "type": "text",
        "required": true
      }
    ]
  },
  "records": [
    {
      "field_name": "value1",
      "uuid": "generated-uuid"
    },
    {
      "field_name": "value2",
      "uuid": "generated-uuid"
    }
  ]
}
```

### Required Fields

**Top-level structure:**
- `spec` (object) - Form specification, required
- `records` (array) - List of data records, required (can be empty)

**Spec object:**
- `title` (string) - Form title, required
- `fields` (array) - Field definitions, required
- `icon` (string) - Font Awesome icon class, optional

**Field object:**
- `name` (string) - Field identifier, required
- `label` (string) - Display label, required
- `type` (string) - Field type, required
- `required` (boolean) - Whether field is required, optional
- `value` (any) - Default/current value, optional
- `options` (array) - For select/radio fields, optional
- `min`, `max`, `step` (number) - For number/range fields, optional
- `hidden` (boolean) - Whether field is hidden, optional

**Record object:**
- Keys must match field names from spec
- `uuid` (string) - Unique identifier, recommended
- Additional metadata (tags, timestamps, etc.) - optional

### Data Type Mapping

XSLT 3.0 maps JSON types to XPath data types:

| JSON Type | XPath Type | Example |
|-----------|------------|---------|
| String | `xs:string` | `"John Doe"` |
| Number | `xs:double` | `42`, `3.14` |
| Boolean | `xs:boolean` | `true`, `false` |
| Null | Empty sequence | `null` → `()` |
| Object | `map(*)` | `{"key": "value"}` |
| Array | `array(*)` | `["item1", "item2"]` |

**Important**: JSON `null` becomes an empty sequence in XPath. Always provide default values for nullable fields.

## Preparing VibeCForms Data

### Basic Preparation

```python
from scripts.xslt_renderer import XSLTRenderer

# Load VibeCForms data
spec = load_spec("contatos.json")
records = repository.read_all("contatos", spec)

# Prepare data for XSLT
data = {
    "spec": spec,
    "records": records
}

# Render
renderer = XSLTRenderer()
renderer.load_template("templates/form.xslt")
html = renderer.render(data)
```

### Adding Tags to Records

```python
# Enrich records with tags
for record in records:
    record['tags'] = tag_service.get_tags(record['uuid'])

data = {
    "spec": spec,
    "records": records
}
```

**Tag structure:**
```json
{
  "tags": [
    {
      "tag": "customer",
      "applied_at": "2025-11-29T10:30:00",
      "applied_by": "user@example.com",
      "actor_type": "human"
    }
  ]
}
```

### Adding Form Metadata

```python
data = {
    "spec": spec,
    "records": records,
    "form_path": form_path,        # For edit/delete URLs
    "user": current_user,           # Current user info
    "permissions": permissions,     # User permissions
    "config": app_config           # App configuration
}
```

### Handling Select Fields

Ensure select field options are properly structured:

```python
# Good: Structured options
field = {
    "name": "category",
    "type": "select",
    "options": [
        {"value": "lead", "label": "Lead"},
        {"value": "customer", "label": "Customer"}
    ]
}

# Bad: String array (won't work with XSLT templates)
field = {
    "name": "category",
    "type": "select",
    "options": ["Lead", "Customer"]  # Missing value/label structure
}
```

**Convert string arrays to proper structure:**

```python
def normalize_select_options(field):
    """Convert string array to proper option structure."""
    if 'options' in field and field['options']:
        if isinstance(field['options'][0], str):
            field['options'] = [
                {"value": opt.lower(), "label": opt}
                for opt in field['options']
            ]
    return field

# Apply to all select fields
for field in spec['fields']:
    if field['type'] in ('select', 'radio'):
        normalize_select_options(field)
```

### Handling Missing Fields

Ensure all records have all fields (even if empty):

```python
def normalize_records(records, spec):
    """Ensure all records have all field keys."""
    field_names = [f['name'] for f in spec['fields']]

    for record in records:
        for field_name in field_names:
            if field_name not in record:
                record[field_name] = None  # or "" for strings

    return records

records = normalize_records(records, spec)
```

### Handling Nested Data

XSLT works well with nested structures. For relationships:

```python
# Add related data to records
for record in records:
    record['customer'] = customer_service.get_customer(record['customer_id'])
    record['orders'] = order_service.get_orders(record['uuid'])

data = {
    "spec": spec,
    "records": records
}
```

**XSLT can access nested data:**
```xslt
<xsl:template match="map(*)" mode="table-row">
  <tr>
    <td><xsl:value-of select="?name"/></td>
    <td><xsl:value-of select="?customer?name"/></td>
    <td><xsl:value-of select="array:size(?orders)"/> orders</td>
  </tr>
</xsl:template>
```

## Output Formatting

### HTML Output Options

Control HTML output format via renderer parameters:

```python
# Pretty-printed HTML (development)
html = renderer.render(data,
    pretty_print=True,
    indent=2
)
```

**Output:**
```html
<html>
  <head>
    <title>Contacts</title>
  </head>
  <body>
    <div class="container">
      <h2>Contacts</h2>
      <form method="post">
        <div class="form-row">
          <label for="nome">Name:</label>
          <input type="text" name="nome" id="nome" required="required"/>
        </div>
      </form>
    </div>
  </body>
</html>
```

```python
# Compressed HTML (production)
html = renderer.render(data,
    pretty_print=False
)
```

**Output:**
```html
<html><head><title>Contacts</title></head><body><div class="container"><h2>Contacts</h2><form method="post"><div class="form-row"><label for="nome">Name:</label><input type="text" name="nome" id="nome" required="required"/></div></form></div></body></html>
```

### XSLT Output Control

Control formatting in XSLT template itself:

```xslt
<xsl:output method="html"
            indent="yes"           <!-- Pretty print -->
            omit-xml-declaration="yes"
            encoding="UTF-8"
            doctype-system="about:legacy-compat"/>
```

**Parameters:**
- `method`: `html`, `xml`, `text`, `json` (XSLT 3.0)
- `indent`: `yes` (pretty) or `no` (compressed)
- `omit-xml-declaration`: `yes` to skip `<?xml...?>`
- `encoding`: Character encoding (usually `UTF-8`)
- `doctype-system`: HTML5 doctype declaration

### Indentation Control

```xslt
<!-- Development: readable HTML -->
<xsl:output indent="yes"/>

<!-- Production: compressed HTML -->
<xsl:output indent="no"/>
```

### Custom Indentation

```python
# Control indent size via parameter
html = renderer.render(data,
    pretty_print=True,
    indent=4  # 4 spaces instead of default 2
)
```

## Data Limitations and Constraints

### Size Limitations

**Large datasets:**
- XSLT loads entire JSON into memory
- Recommended limit: ~10,000 records per transformation
- For larger datasets, use pagination

```python
# Pagination approach
page_size = 100
page = 1

paginated_data = {
    "spec": spec,
    "records": records[(page-1)*page_size : page*page_size],
    "pagination": {
        "page": page,
        "page_size": page_size,
        "total": len(records)
    }
}
```

### String Length

- No hard limits, but very long strings (>1MB) may impact performance
- Textarea values should be reasonable (<10k chars)

### Nesting Depth

- XSLT handles deep nesting well
- Recommended max depth: 5-7 levels
- Deeply nested structures may be hard to maintain

### Special Characters

**Characters that need escaping:**
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`
- `"` → `&quot;`
- `'` → `&apos;`

**Python handles this automatically:**
```python
record = {
    "description": "Company <ABC> & Partners"
}
# Automatically escaped in JSON → XSLT → HTML
```

### Circular References

XSLT cannot handle circular references. Ensure data is a tree structure:

```python
# Bad: Circular reference
customer['orders'] = [order1, order2]
order1['customer'] = customer  # Circular!

# Good: Use IDs instead
customer['orders'] = [order1, order2]
order1['customer_id'] = customer['uuid']
```

## Best Practices

### 1. Validate Data Structure

```python
def validate_xslt_data(data):
    """Validate data structure before XSLT transformation."""
    assert 'spec' in data, "Missing 'spec' key"
    assert 'records' in data, "Missing 'records' key"
    assert isinstance(data['records'], list), "'records' must be array"

    spec = data['spec']
    assert 'title' in spec, "Missing spec.title"
    assert 'fields' in spec, "Missing spec.fields"
    assert isinstance(spec['fields'], list), "spec.fields must be array"

    return True

# Before rendering
validate_xslt_data(data)
html = renderer.render(data)
```

### 2. Use Default Values

```python
# Provide defaults for optional fields
field = {
    "name": "priority",
    "label": "Priority",
    "type": "range",
    "min": 1,
    "max": 10,
    "step": field.get('step', 1),        # Default to 1
    "value": field.get('value', 5)       # Default to middle
}
```

### 3. Normalize Data Types

```python
def normalize_boolean_fields(record, spec):
    """Ensure boolean fields are actual booleans."""
    for field in spec['fields']:
        if field['type'] == 'checkbox':
            field_name = field['name']
            if field_name in record:
                # Convert truthy values to boolean
                record[field_name] = bool(record[field_name])
    return record
```

### 4. Handle Null Values

```python
def handle_nulls(data):
    """Replace None with empty string for better XSLT handling."""
    def replace_none(obj):
        if isinstance(obj, dict):
            return {k: replace_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_none(item) for item in obj]
        elif obj is None:
            return ""
        else:
            return obj

    return replace_none(data)

data = handle_nulls(data)
```

### 5. Optimize for Performance

```python
# Cache renderer and templates
class FormRenderer:
    def __init__(self):
        self.renderer = XSLTRenderer()
        self.templates = {}

    def render_form(self, form_path, data):
        # Load template once, cache it
        template_path = f"templates/{form_path}.xslt"

        if template_path not in self.templates:
            self.renderer.load_template(template_path)
            self.templates[template_path] = True

        return self.renderer.render(data, template_path=template_path)

# Reuse renderer instance
form_renderer = FormRenderer()
html = form_renderer.render_form("contatos", data)
```

## Complete Example

### VibeCForms Integration

```python
from flask import Flask, request
from scripts.xslt_renderer import XSLTRenderer
import json

app = Flask(__name__)
renderer = XSLTRenderer()
renderer.load_template("templates/form.xslt")

def prepare_form_data(form_path):
    """Prepare complete data structure for XSLT rendering."""
    # Load spec
    spec = load_spec(form_path)

    # Normalize select fields
    for field in spec['fields']:
        if field['type'] in ('select', 'radio'):
            normalize_select_options(field)

    # Load records
    records = repository.read_all(form_path, spec)

    # Normalize records
    records = normalize_records(records, spec)

    # Add tags
    for record in records:
        record['tags'] = tag_service.get_tags(record['uuid'])

    # Handle nulls
    records = handle_nulls(records)

    # Build data structure
    data = {
        "spec": spec,
        "records": records,
        "form_path": form_path,
        "metadata": {
            "total_records": len(records),
            "timestamp": datetime.now().isoformat()
        }
    }

    # Validate
    validate_xslt_data(data)

    return data

@app.route("/<path:form_path>")
def form_view(form_path):
    """Render form using XSLT."""
    try:
        # Prepare data
        data = prepare_form_data(form_path)

        # Render with XSLT
        html = renderer.render(
            data,
            template_path="templates/form.xslt",
            pretty_print=app.debug,  # Pretty in debug, compressed in prod
            debug=app.debug
        )

        return html

    except Exception as e:
        app.logger.error(f"XSLT rendering failed: {e}")
        return f"Error rendering form: {e}", 500
```

### Sample Data Flow

**1. Load from database:**
```python
{
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "nome": "John Doe",
    "email": "john@example.com",
    "category": "customer"
}
```

**2. Enrich with tags:**
```python
{
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "nome": "John Doe",
    "email": "john@example.com",
    "category": "customer",
    "tags": [
        {"tag": "vip", "applied_by": "admin", "actor_type": "human"}
    ]
}
```

**3. Combine with spec:**
```python
{
    "spec": {
        "title": "Contacts",
        "fields": [
            {"name": "nome", "label": "Name", "type": "text", "required": true},
            {"name": "email", "label": "Email", "type": "email", "required": false},
            {"name": "category", "label": "Category", "type": "select",
             "options": [
                 {"value": "lead", "label": "Lead"},
                 {"value": "customer", "label": "Customer"}
             ]}
        ]
    },
    "records": [/* enriched records */]
}
```

**4. Transform via XSLT → HTML output**

## Troubleshooting

### Common Issues

**Issue**: `KeyError: 'field_name'`
**Solution**: Use `normalize_records()` to ensure all fields exist in all records

**Issue**: Select dropdown shows values instead of labels
**Solution**: Ensure options have both `value` and `label` keys

**Issue**: Boolean checkboxes not rendering correctly
**Solution**: Use `normalize_boolean_fields()` to convert truthy values

**Issue**: XSLT transformation is slow
**Solution**: Cache renderer instance, reduce record count, disable pretty-printing

**Issue**: Special characters display incorrectly
**Solution**: Ensure UTF-8 encoding throughout (JSON → XSLT → HTML)

**Issue**: Nested data not accessible
**Solution**: Check XSLT pattern syntax (`?customer?name` for nested access)

### Debug Mode

```python
# Enable debug output
html = renderer.render(data, debug=True)

# Outputs:
# [XSLT Debug] Input JSON:
# {...}
# [XSLT Debug] Output HTML length: 15432 chars
```

### Validation Script

```python
#!/usr/bin/env python3
"""Validate data structure before XSLT transformation."""

import json
import sys

def validate_data_file(filepath):
    with open(filepath) as f:
        data = json.load(f)

    validate_xslt_data(data)
    print(f"✅ {filepath} is valid for XSLT transformation")

if __name__ == '__main__':
    validate_data_file(sys.argv[1])
```

Usage:
```bash
python3 validate_data.py data.json
```
