# XSLT Troubleshooting Guide

Comprehensive troubleshooting reference for XSLT 3.0 transformations with saxonche in VibeCForms.

## Quick Diagnostic Checklist

Before diving into specific issues, run through this checklist:

- [ ] Is saxonche properly installed? (`pip list | grep saxonche`)
- [ ] Is the XSLT version set to 3.0? (`<xsl:stylesheet version="3.0">`)
- [ ] Is the input data valid JSON? (Test with `json.loads()`)
- [ ] Are template patterns matching? (Add `<xsl:message>` tags)
- [ ] Is debug mode enabled? (`renderer.render(data, debug=True)`)

## Installation and Import Issues

### Error: "Unresolved import PySaxonProcessor"

**Symptom:**
```python
from saxonche import PySaxonProcessor
# ModuleNotFoundError: No module named 'saxonche'
```

**Solutions:**

1. **Install saxonche:**
```bash
uv add saxonche
# or
pip install saxonche
```

2. **Verify installation:**
```bash
python3 -c "from saxonche import PySaxonProcessor; print('OK')"
```

3. **Check Python version compatibility:**
```bash
python3 --version  # saxonche requires Python 3.7+
```

**Web References:**
- [saxonche PyPI Documentation](https://pypi.org/project/saxonche/)
- [Saxonica Community: Installation Issues](https://saxonica.plan.io/boards/3)

### Error: "Library not loaded" (macOS)

**Symptom:**
```
Library not loaded: libsaxonhec.dylib
```

**Solution:**
Reinstall saxonche with latest version:
```bash
pip install --upgrade --force-reinstall saxonche
```

## Template Pattern Matching Issues

### Issue: Template Not Matching

**Symptom:**
Expected template doesn't apply, or fallback template is used instead.

**Debug Approach:**

1. **Add diagnostic messages:**
```xslt
<xsl:template match="map(*)[?type = 'text']">
  <xsl:message>✓ Matched text field: <xsl:value-of select="?name"/></xsl:message>
  <input type="text" name="{?name}"/>
</xsl:template>

<xsl:template match="map(*)" priority="-1">
  <xsl:message>⚠ Fallback matched: <xsl:value-of select="serialize(.)"/></xsl:message>
  <div>Unknown</div>
</xsl:template>
```

2. **Check pattern syntax:**
```xslt
<!-- Wrong: Missing ? for map access -->
<xsl:template match="map(*)[type = 'text']">

<!-- Correct: ? accesses map keys -->
<xsl:template match="map(*)[?type = 'text']">
```

3. **Verify data structure:**
```python
# Print data before transformation
import json
print(json.dumps(data, indent=2))
```

**Common Pattern Mistakes:**

| Wrong | Correct | Reason |
|-------|---------|--------|
| `map(*)[type]` | `map(*)[?type]` | Missing `?` for map key access |
| `array(*)` | `array(*)?*` | Need `?*` to access array items |
| `match="*"` | `match="map(*)"` | Too broad, matches everything |
| `?fields` | `?fields?*` | `?fields` is array, need `?*` for items |

**Web References:**
- [Stack Overflow: Pattern matching in XSLT](https://stackoverflow.com/questions/12323776/pattern-match-in-xslt)
- [Mastering Complex XSLT Transformations](https://moldstud.com/articles/p-mastering-complex-xslt-transformations-expert-tips-for-advanced-developers)

### Issue: Template Priority Conflicts

**Symptom:**
Wrong template applies when multiple patterns match.

**Solution:**

Use explicit priority:
```xslt
<!-- General text inputs (default priority) -->
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}"/>
</xsl:template>

<!-- UUID fields (higher priority) -->
<xsl:template match="map(*)[?type = 'text' and ?name = 'uuid']" priority="1">
  <code class="uuid"><xsl:value-of select="?value"/></code>
</xsl:template>

<!-- Unknown fields (fallback) -->
<xsl:template match="map(*)[?type]" priority="-1">
  <input type="text" name="{?name}"/>  <!-- Safe fallback -->
</xsl:template>
```

**Best Practice:**
- Specific patterns get higher default priority automatically
- Use explicit `priority` only when needed
- Use `priority="-1"` for catch-all fallbacks

**Web References:**
- [Saxon Documentation: Template Priority](https://www.saxonica.com/html/documentation11/changes/v8.4/xslt20.html)

## Data Structure Issues

### Error: "A sequence of more than one item is not allowed"

**Symptom:**
```
XPTY0004: A sequence of more than one item is not allowed as the value of variable $record
```

**Cause:**
Trying to assign array to variable instead of single item.

**Solution:**
```xslt
<!-- Wrong: Assigns entire array -->
<xsl:variable name="record" select="?records"/>

<!-- Correct: Assigns first item -->
<xsl:variable name="record" select="?records?(1)"/>

<!-- Or iterate: -->
<xsl:for-each select="?records?*">
  <xsl:variable name="record" select="."/>
  <!-- Process each record -->
</xsl:for-each>
```

### Error: "Cannot compare xs:string to empty sequence"

**Symptom:**
Comparison fails when field is missing or null.

**Solution:**

1. **Use default values:**
```xslt
<!-- Provide default if missing -->
<xsl:value-of select="(?optional_field, 'default')[1]"/>
```

2. **Check existence first:**
```xslt
<xsl:if test="?optional_field">
  <xsl:value-of select="?optional_field"/>
</xsl:if>
```

3. **Normalize data in Python:**
```python
def handle_nulls(data):
    """Replace None with empty string."""
    def replace_none(obj):
        if isinstance(obj, dict):
            return {k: replace_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_none(item) for item in obj]
        elif obj is None:
            return ""
        return obj
    return replace_none(data)

data = handle_nulls(data)
```

### KeyError: Missing Field in Record

**Symptom:**
```python
KeyError: 'field_name'
```

**Solution:**

Normalize records to include all fields:
```python
def normalize_records(records, spec):
    """Ensure all records have all field keys."""
    field_names = [f['name'] for f in spec['fields']]

    for record in records:
        for field_name in field_names:
            if field_name not in record:
                record[field_name] = ""  # or None

    return records

# Before XSLT transformation
records = normalize_records(records, spec)
```

**Web References:**
- [Stack Overflow: XSLT 3.0 JSON Data Types](https://stackoverflow.com/questions/49521311/xslt-3-0-transformation-of-json-to-xml-numeric-data-types)

## JSON Transformation Issues

### Issue: Select Dropdown Shows Values Instead of Labels

**Symptom:**
Dropdown shows "lead", "customer" instead of "Lead", "Customer".

**Cause:**
Options array has wrong structure.

**Solution:**

Ensure proper option structure:
```python
# Wrong: String array
field = {
    "type": "select",
    "options": ["Lead", "Customer"]  # ❌
}

# Correct: Object array
field = {
    "type": "select",
    "options": [
        {"value": "lead", "label": "Lead"},      # ✓
        {"value": "customer", "label": "Customer"}  # ✓
    ]
}

# Normalize function:
def normalize_select_options(field):
    if 'options' in field and field['options']:
        if isinstance(field['options'][0], str):
            field['options'] = [
                {"value": opt.lower(), "label": opt}
                for opt in field['options']
            ]
    return field
```

### Issue: Boolean Values Not Rendering

**Symptom:**
Checkboxes don't check even when value is truthy.

**Cause:**
Python truthiness (`1`, `"true"`) vs XSLT boolean (`true()`).

**Solution:**

Normalize booleans in Python:
```python
def normalize_boolean_fields(record, spec):
    """Convert truthy values to actual booleans."""
    for field in spec['fields']:
        if field['type'] == 'checkbox':
            field_name = field['name']
            if field_name in record:
                record[field_name] = bool(record[field_name])
    return record
```

Or handle in XSLT:
```xslt
<xsl:template match="map(*)[?type = 'checkbox']">
  <input type="checkbox" name="{?name}">
    <!-- Check for any truthy value -->
    <xsl:if test="?checked = true() or ?checked = 'true' or ?checked = 1">
      <xsl:attribute name="checked">checked</xsl:attribute>
    </xsl:if>
  </input>
</xsl:template>
```

### Issue: Nested Data Not Accessible

**Symptom:**
```xslt
<xsl:value-of select="?customer?name"/>  <!-- Returns nothing -->
```

**Debug:**
```xslt
<!-- Check if customer exists -->
<xsl:message>Customer exists: <xsl:value-of select="exists(?customer)"/></xsl:message>

<!-- Check customer type -->
<xsl:message>Customer type: <xsl:value-of select="?customer instance of map(*)"/></xsl:message>

<!-- Serialize customer -->
<xsl:message>Customer data: <xsl:value-of select="serialize(?customer)"/></xsl:message>
```

**Solution:**

Ensure nested data is objects, not strings:
```python
# Wrong: customer_id as string
record = {
    "name": "Deal 1",
    "customer_id": "123"  # ❌ Just an ID
}

# Correct: customer as nested object
record = {
    "name": "Deal 1",
    "customer": {         # ✓ Full object
        "id": "123",
        "name": "ACME Corp"
    }
}
```

**Web References:**
- [Stack Overflow: Traverse JSON in XSLT 3.0](https://stackoverflow.com/questions/72970174/how-to-traverse-json-in-xslt-3-0-when-map-vs-array-is-unknown)

## Saxon Processor Errors

### Error: "Content is not allowed in prolog"

**Symptom:**
```
Content is not allowed in prolog
```

**Cause:**
Passing directory name instead of file name to `source_file`.

**Solution:**
```python
# Wrong: Directory path
renderer.load_template("templates/")

# Correct: File path
renderer.load_template("templates/form.xslt")
```

**Web References:**
- [Saxonica Community: XML Parsing Error](https://saxonica.plan.io/issues/6122)

### Error: "Error reported by XML parser"

**Symptom:**
Generic error message without details.

**Cause:**
Saxon sends errors to stderr; `getMessage()` only returns generic message.

**Solution:**

Enable debug mode for detailed errors:
```python
html = renderer.render(data, debug=True)
```

Check stderr output:
```python
import sys
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

try:
    html = renderer.render(data)
except Exception as e:
    logging.error(f"XSLT Error: {e}", exc_info=True)
```

**Web References:**
- [Saxonica Community: Error Reporting](https://saxonica.plan.io/boards/3/topics/3411)
- [Saxon Error Codes Documentation](https://www.saxonica.com/html/documentation/javadoc/net/sf/saxon/trans/SaxonErrorCode.html)
- [W3C XQuery/XSLT Error Codes](https://www.w3.org/2005/xqt-errors/)

### Error: "XTSE0090: Attribute @X is not allowed on element xsl:Y"

**Symptom:**
```
Static error in xsl:variable/@bla on line 10:
XTSE0090: Attribute @bla is not allowed on element xsl:variable
```

**Cause:**
Invalid attribute on XSLT element.

**Solution:**
Check XSLT specification for allowed attributes:
```xslt
<!-- Wrong: Invalid attribute -->
<xsl:variable name="x" bla="value"/>

<!-- Correct: Only valid attributes -->
<xsl:variable name="x" select="value"/>
```

**Web References:**
- [Saxonica Community: Error Message Format](https://saxonica.plan.io/issues/4633)

### Memory Issues: Increasing Consumption

**Symptom:**
Server gradually runs out of memory when rendering multiple times.

**Cause:**
Not releasing Saxon processor resources.

**Solution:**

1. **Reuse renderer instance:**
```python
# Good: Single renderer instance
class FormRenderer:
    def __init__(self):
        self.renderer = XSLTRenderer()
        self.renderer.load_template("templates/form.xslt")

    def render(self, data):
        return self.renderer.render(data)

# Reuse across requests
form_renderer = FormRenderer()

@app.route("/forms/<path>")
def view_form(path):
    html = form_renderer.render(data)
    return html
```

2. **Explicitly cleanup:**
```python
try:
    html = renderer.render(data)
finally:
    renderer.clear_cache()  # Clear template cache
```

## Output and Formatting Issues

### Issue: HTML Output Not Indented

**Symptom:**
HTML is on one line despite `indent="yes"`.

**Solution:**

Ensure both XSLT and Python settings enable indentation:

**XSLT:**
```xslt
<xsl:output method="html"
            indent="yes"
            omit-xml-declaration="yes"/>
```

**Python:**
```python
html = renderer.render(data, pretty_print=True, indent=2)
```

### Issue: Special Characters Escaped Incorrectly

**Symptom:**
`"Company <ABC> & Partners"` becomes `"Company &lt;ABC&gt; &amp; Partners"` in HTML text.

**Cause:**
Normal XML escaping behavior.

**Solution:**

Use `<xsl:value-of>` for text content (auto-escapes), and disable escaping for HTML:
```xslt
<!-- For text content (auto-escapes): -->
<p><xsl:value-of select="?description"/></p>

<!-- For HTML content (disable escaping): -->
<div>
  <xsl:value-of select="?html_content" disable-output-escaping="yes"/>
</div>
```

### Issue: Forward Slashes Escaped in JSON

**Symptom:**
`"http://example.com"` becomes `"http:\/\/example.com"` in JSON output.

**Cause:**
`fn:serialize` has no escape parameter like `fn:parse-json`.

**Solution:**

Use XML-to-JSON format for more control:
```xslt
<xsl:variable name="json-xml">
  <map xmlns="http://www.w3.org/2005/xpath-functions">
    <string key="url">http://example.com</string>
  </map>
</xsl:variable>

<xsl:value-of select="xml-to-json($json-xml)"/>
```

**Web References:**
- [Stack Overflow: JSON Serialization Character Escaping](https://stackoverflow.com/questions/44610431/json-serialization-with-xpath-3-1-fnserialize)

## Performance Issues

### Issue: Transformation is Slow

**Symptoms:**
- Takes >1 second for small forms
- Memory usage keeps increasing
- Server becomes unresponsive

**Solutions:**

1. **Cache templates:**
```python
# Bad: Recompile template every time
def render_form(data):
    renderer = XSLTRenderer()
    renderer.load_template("form.xslt")  # Compiles on every call
    return renderer.render(data)

# Good: Compile once, reuse
renderer = XSLTRenderer()
renderer.load_template("form.xslt")  # Compile once

def render_form(data):
    return renderer.render(data)  # Reuse compiled template
```

2. **Reduce record count:**
```python
# Paginate large datasets
page_size = 100
data = {
    "spec": spec,
    "records": records[:page_size]  # Limit records
}
```

3. **Disable pretty-printing in production:**
```python
# Development
html = renderer.render(data, pretty_print=True)

# Production
html = renderer.render(data, pretty_print=False)  # Faster
```

4. **Use streaming for large datasets:**
```xslt
<!-- Enable streaming mode (XSLT 3.0) -->
<xsl:mode streamable="yes"/>
```

**Note:** Streaming has restrictions - template body can contain at most one expression that reads contents below matched element.

**Web References:**
- [DeltaXML: Beyond Step-Through XSLT Debugging](https://www.deltaxignia.com/blog/the-world-of-xml-and-json/xslt-debugging/)

## Debugging Techniques

### 1. Printf-Style Debugging with xsl:message

**Most effective debugging approach:**

```xslt
<xsl:template match="map(*)[?fields]">
  <!-- Debug: Show what we're matching -->
  <xsl:message>
    ═══════════════════════════════════════
    Template: Form with fields
    Title: <xsl:value-of select="?title"/>
    Field count: <xsl:value-of select="array:size(?fields)"/>
    ═══════════════════════════════════════
  </xsl:message>

  <form>
    <xsl:apply-templates select="?fields?*"/>
  </form>
</xsl:template>

<xsl:template match="map(*)[?type]">
  <!-- Debug: Show field being processed -->
  <xsl:message>
    → Processing field: <xsl:value-of select="?name"/>
      Type: <xsl:value-of select="?type"/>
      Required: <xsl:value-of select="?required"/>
  </xsl:message>

  <!-- Field rendering... -->
</xsl:template>
```

**Auto-generate and remove:** Use editor snippets to quickly add/remove debug messages.

**Web References:**
- [XML Rocks: Debugging Complex XSLT Modules](https://blog.xml.rocks/debugging-complex-xslt-modules/)
- [Stack Overflow: xsl:message in Saxon](https://stackoverflow.com/questions/27522994/xsltmessage-in-saxon-where-is-the-message)

### 2. Serialize Data for Inspection

```xslt
<!-- Show full data structure -->
<xsl:message>
  Data structure:
  <xsl:value-of select="serialize(., map{'indent': true()})"/>
</xsl:message>

<!-- Show specific field -->
<xsl:message>
  Field options: <xsl:value-of select="serialize(?options)"/>
</xsl:message>
```

### 3. Conditional Breakpoints

```xslt
<xsl:template match="map(*)[?type = 'text']">
  <!-- Debug only specific fields -->
  <xsl:if test="?name = 'email'">
    <xsl:message terminate="no">
      🔍 Debugging email field:
      Value: <xsl:value-of select="?value"/>
      Required: <xsl:value-of select="?required"/>
    </xsl:message>
  </xsl:if>

  <input type="text" name="{?name}"/>
</xsl:template>
```

### 4. Template Application Audit

Track which templates are being applied:
```xslt
<xsl:template match="map(*)" mode="debug-trace">
  <xsl:message>
    Applied template for: <xsl:value-of select="name()"/>
    Keys: <xsl:value-of select="string-join(map:keys(.), ', ')"/>
    Priority: <xsl:value-of select="system-property('xsl:template-priority')"/>
  </xsl:message>
</xsl:template>
```

### 5. Python-Side Debugging

```python
import json
import logging

logging.basicConfig(level=logging.DEBUG)

def debug_render(data, template_path):
    """Render with comprehensive debugging."""

    # 1. Validate data structure
    logging.debug("Validating data structure...")
    validate_xslt_data(data)

    # 2. Show data being sent
    logging.debug("Input data:")
    logging.debug(json.dumps(data, indent=2, default=str))

    # 3. Render with debug mode
    logging.debug(f"Rendering with template: {template_path}")
    try:
        html = renderer.render(data, debug=True)
        logging.debug(f"Output length: {len(html)} chars")
        return html
    except Exception as e:
        logging.error(f"Rendering failed: {e}", exc_info=True)
        raise
```

### 6. Use Saxon Trace Listener (Advanced)

For performance analysis, use Saxon's TraceListener interface to collect detailed tracing information.

**Web References:**
- [Mastering Complex XSLT: Debugging Tips](https://moldstud.com/articles/p-mastering-complex-xslt-transformations-expert-tips-for-advanced-developers)

## IDE and Tool Support

### Visual Studio Code

**Extensions:**
- [VS Code XSLT/XPath](https://marketplace.visualstudio.com/items?itemName=deltaxml.xslt-xpath)
- Syntax highlighting, debugging, XPath evaluation

**Features:**
- Set breakpoints in XSLT
- Step through transformations
- Inspect variables
- XPath evaluation window

**Web References:**
- [VS Code XSLT/XPath: Running XSLT](https://deltaxml.github.io/vscode-xslt-xpath/run-xslt.html)

### Visual Studio (Windows)

Full XSLT debugger with:
- Line-by-line stepping
- Variable inspection
- Call stack
- Breakpoints on patterns

**Web References:**
- [Microsoft Learn: Debug XSLT Style Sheets](https://learn.microsoft.com/en-us/visualstudio/xml-tools/walkthrough-debug-an-xslt-style-sheet?view=vs-2022)

### Oxygen XML Editor

Commercial XML/XSLT IDE with comprehensive debugging.

## VibeCForms-Specific Issues

### Issue: Tags Not Rendering

**Check:**
1. Tags are properly loaded:
```python
for record in records:
    record['tags'] = tag_service.get_tags(record['uuid'])
    print(f"Record {record['uuid']}: {len(record['tags'])} tags")
```

2. XSLT template exists:
```xslt
<xsl:template match="array(*)" mode="tags">
  <xsl:apply-templates select="?*" mode="tag-badge"/>
</xsl:template>
```

3. Template is invoked:
```xslt
<td class="tags-cell">
  <xsl:apply-templates select="?tags" mode="tags"/>
</td>
```

### Issue: Form Fields Not Showing

**Debug checklist:**
```python
# 1. Verify spec structure
print("Fields in spec:", len(spec['fields']))
for field in spec['fields']:
    print(f"  - {field['name']}: {field['type']}")

# 2. Check for hidden fields
visible_fields = [f for f in spec['fields'] if not f.get('hidden')]
print(f"Visible fields: {len(visible_fields)}")

# 3. Verify data structure
validate_xslt_data({"spec": spec, "records": records})
```

### Issue: Edit Form Not Pre-filling Values

**Ensure values are in field spec:**
```python
def prepare_edit_form(form_path, record_id):
    spec = load_spec(form_path)
    record = repository.read(form_path, spec, record_id)

    # Add values to field specs
    for field in spec['fields']:
        field_name = field['name']
        if field_name in record:
            field['value'] = record[field_name]

    return {"spec": spec, "record": record}
```

## Error Reference Table

| Error Code | Meaning | Common Cause | Solution |
|------------|---------|--------------|----------|
| XPTY0004 | Type error | Sequence where single item expected | Use `?records?(1)` not `?records` |
| XTSE0090 | Invalid attribute | Wrong attribute on XSLT element | Check XSLT spec for allowed attributes |
| XPST0003 | Syntax error | Malformed XPath expression | Check `?` syntax for maps/arrays |
| XPDY0002 | Dynamic error | Evaluating expression with no context | Ensure template has matched context |
| FOJS0001 | JSON parse error | Invalid JSON input | Validate JSON with `json.loads()` |
| SXJS0003 | Invalid JSON | JSON function called on non-JSON | Check data type before calling JSON functions |

**Complete error codes:**
- [Saxon Error Codes](https://www.saxonica.com/html/documentation/javadoc/net/sf/saxon/trans/SaxonErrorCode.html)
- [W3C XQuery/XSLT Error Codes](https://www.w3.org/2005/xqt-errors/)

## Getting Help

### Official Resources

1. **Saxon Documentation**
   - [Saxon Documentation](https://www.saxonica.com/documentation/documentation.xml)
   - [Saxon Command Line](https://www.saxonica.com/documentation9.5/using-xsl/commandline.html)

2. **W3C Specifications**
   - [XSLT 3.0 Specification](https://www.w3.org/TR/xslt-30/)
   - [XPath 3.1 Specification](https://www.w3.org/TR/xpath-31/)

### Community Resources

1. **Saxonica Developer Community**
   - [Community Forums](https://saxonica.plan.io/)
   - [Bug Tracker](https://saxonica.plan.io/projects/saxon/issues)

2. **Stack Overflow**
   - [saxon tag](https://stackoverflow.com/questions/tagged/saxon)
   - [xslt-3.0 tag](https://stackoverflow.com/questions/tagged/xslt-3.0)
   - [xpath-3.0 tag](https://stackoverflow.com/questions/tagged/xpath-3.0)

3. **Blogs and Tutorials**
   - [XML Rocks Blog](https://blog.xml.rocks/)
   - [DeltaXML XSLT Resources](https://www.deltaxignia.com/blog/the-world-of-xml-and-json/)
   - [Ralph's Open Source Blog: JSON to XML](https://ralph.blog.imixs.com/2019/08/05/how-to-convert-json-to-xml/)

### VibeCForms Resources

1. **Project Documentation**
   - Check `CLAUDE.md` for VibeCForms conventions
   - Review other skills: `workflow_kanban`

2. **Internal Issues**
   - Check `.claude/` directory for project-specific configs
   - Review `src/specs/` for form specifications

## Validation Script

Create `scripts/validate_xslt_data.py` for pre-transformation validation:

```python
#!/usr/bin/env python3
"""
Validate data structure before XSLT transformation.
Usage: python3 scripts/validate_xslt_data.py data.json
"""

import json
import sys
from pathlib import Path

def validate_xslt_data(data):
    """Validate data structure for XSLT transformation."""
    errors = []

    # Check top-level structure
    if 'spec' not in data:
        errors.append("Missing 'spec' key")
    if 'records' not in data:
        errors.append("Missing 'records' key")

    if errors:
        return False, errors

    spec = data['spec']

    # Validate spec
    if 'title' not in spec:
        errors.append("Missing spec.title")
    if 'fields' not in spec:
        errors.append("Missing spec.fields")
    elif not isinstance(spec['fields'], list):
        errors.append("spec.fields must be an array")

    # Validate fields
    for i, field in enumerate(spec.get('fields', [])):
        if 'name' not in field:
            errors.append(f"Field {i}: missing 'name'")
        if 'type' not in field:
            errors.append(f"Field {i}: missing 'type'")
        if 'label' not in field:
            errors.append(f"Field {i}: missing 'label'")

        # Check select fields have options
        if field.get('type') in ('select', 'radio'):
            if 'options' not in field:
                errors.append(f"Field {field.get('name', i)}: select/radio requires 'options'")
            elif field['options'] and isinstance(field['options'][0], dict):
                if 'value' not in field['options'][0] or 'label' not in field['options'][0]:
                    errors.append(f"Field {field.get('name', i)}: options need 'value' and 'label'")

    # Validate records
    if not isinstance(data['records'], list):
        errors.append("'records' must be an array")

    return len(errors) == 0, errors

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validate_xslt_data.py <data.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    valid, errors = validate_xslt_data(data)

    if valid:
        print(f"✅ {filepath} is valid for XSLT transformation")
        sys.exit(0)
    else:
        print(f"❌ {filepath} has validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
```

Make executable and use:
```bash
chmod +x scripts/validate_xslt_data.py
python3 scripts/validate_xslt_data.py data.json
```

---

## Quick Reference: Debugging Workflow

1. **Enable debug mode**: `renderer.render(data, debug=True)`
2. **Add xsl:message tags**: Track template application
3. **Validate data**: Run validation script
4. **Check patterns**: Verify `?` syntax for maps/arrays
5. **Serialize data**: Use `serialize()` to inspect structures
6. **Check priorities**: Add explicit `priority` if needed
7. **Test incrementally**: Add one template at a time
8. **Review error codes**: Look up specific Saxon error codes
9. **Search community**: Check Stack Overflow and Saxonica forums
10. **Ask for help**: Provide minimal reproducible example

**Remember:** Most XSLT issues are pattern matching or data structure problems. Use `<xsl:message>` liberally to understand what's happening!
