# XSLT Templates Quick Reference

## Template Modes

### Form Mode (mode="form")
Renders input fields for data entry.

```xml
<xsl:apply-templates select="spec/fields/field" mode="form"/>
```

### Table Mode (mode="table")
Renders field values in table cells with transformations.

```xml
<xsl:apply-templates select="field" mode="table"/>
```

### Menu Modes
- `mode="sidebar"` - Main sidebar menu container
- `mode="menu-item"` - Top-level menu items
- `mode="submenu-item"` - Nested submenu items

## Adding a New Field Type

To add support for a new field type (e.g., `range`):

1. **Create field template** (`src/xslt/fields/range.xslt`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Form mode: render range slider -->
  <xsl:template match="field[@type='range']" mode="form">
    <div class="mb-4 flex items-center gap-2">
      <label for="{@name}" class="w-48 font-semibold text-gray-700">
        <xsl:value-of select="@label"/>:
      </label>
      <input
        type="range"
        name="{@name}"
        id="{@name}"
        min="{@min}"
        max="{@max}"
        step="{@step}"
        value="{@value}"
        class="flex-1"/>
    </div>
  </xsl:template>

  <!-- Table mode: render value -->
  <xsl:template match="field[@type='range']" mode="table">
    <xsl:value-of select="."/>
  </xsl:template>

</xsl:stylesheet>
```

2. **Include in page template** (`src/xslt/pages/form.xslt`):

```xml
<xsl:include href="../fields/range.xslt"/>
```

3. **Include in table-row** (`src/xslt/components/table-row.xslt`):

```xml
<xsl:include href="../fields/range.xslt"/>
```

Done! The new field type will now render in both form and table.

## Common Tailwind Patterns

### Form Elements
```xml
<!-- Form row -->
<div class="mb-4 flex items-center gap-2">

<!-- Label -->
<label class="w-48 font-semibold text-gray-700">Label:</label>

<!-- Input -->
<input class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"/>

<!-- Select -->
<select class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"/>

<!-- Checkbox -->
<input type="checkbox" class="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"/>
```

### Buttons
```xml
<!-- Primary button -->
<button class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">

<!-- Edit button -->
<a class="inline-block bg-yellow-500 text-white px-3 py-2 rounded hover:bg-yellow-600 transition-colors">

<!-- Delete button -->
<a class="inline-block bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600 transition-colors">
```

### Table
```xml
<!-- Table container -->
<div class="w-full overflow-x-auto">

<!-- Table -->
<table class="w-full border-collapse min-w-[600px]">

<!-- Header cell -->
<th class="px-4 py-3 text-center bg-blue-500 text-white">

<!-- Data cell -->
<td class="px-4 py-3 text-center align-middle whitespace-nowrap overflow-hidden text-ellipsis">

<!-- Row -->
<tr class="border-b border-gray-200 hover:bg-gray-50">
```

### Layout
```xml
<!-- Page wrapper -->
<div class="flex min-h-screen">

<!-- Sidebar -->
<nav class="w-64 bg-gray-800 text-white fixed h-screen flex flex-col z-50">

<!-- Main content -->
<div class="ml-64 flex-1 p-10">

<!-- Container -->
<div class="max-w-6xl mx-auto bg-white p-8 rounded-lg shadow-md">
```

## XSLT Patterns to Avoid

### ❌ Don't Use For-Each
```xml
<!-- BAD -->
<xsl:for-each select="spec/fields/field">
  <div><xsl:value-of select="@label"/></div>
</xsl:for-each>
```

### ✅ Use Apply-Templates Instead
```xml
<!-- GOOD -->
<xsl:apply-templates select="spec/fields/field" mode="form"/>
```

### ❌ Don't Use Position-Based Logic
```xml
<!-- BAD -->
<xsl:if test="position() = 1">First item</xsl:if>
```

### ✅ Use Pattern Matching Instead
```xml
<!-- GOOD -->
<xsl:template match="field[1]" mode="special">
  First item
</xsl:template>
```

## XPath Selectors

### Common Selectors
```xml
<!-- Attribute value -->
<xsl:value-of select="@name"/>

<!-- Text content -->
<xsl:value-of select="."/>

<!-- Child element -->
<xsl:value-of select="spec/@title"/>

<!-- Descendant -->
<xsl:apply-templates select="spec/fields/field"/>

<!-- Filtered -->
<xsl:apply-templates select="field[@type='text']"/>

<!-- Multiple conditions -->
<xsl:apply-templates select="field[@type!='hidden' and @name!='_record_id']"/>

<!-- Child count -->
<xsl:if test="count(item) > 0">
```

### Variables
```xml
<!-- String variable -->
<xsl:variable name="form-name" select="@form-name"/>

<!-- Node variable -->
<xsl:variable name="field-value" select="@value"/>

<!-- Complex expression -->
<xsl:variable name="color-class">
  <xsl:call-template name="tag-color-hash">
    <xsl:with-param name="tag" select="."/>
  </xsl:call-template>
</xsl:variable>
```

## Conditional Logic

### If Statement
```xml
<xsl:if test="@error != ''">
  <div class="error">
    <xsl:value-of select="@error"/>
  </div>
</xsl:if>
```

### Choose/When/Otherwise
```xml
<xsl:choose>
  <xsl:when test="@type = 'form'">
    <a href="/{@path}">Form Link</a>
  </xsl:when>
  <xsl:otherwise>
    <div>Folder</div>
  </xsl:otherwise>
</xsl:choose>
```

## Named Templates vs Match Templates

### Named Template (called explicitly)
```xml
<xsl:template name="tag-badge">
  <xsl:param name="tag" as="xs:string"/>
  <span class="tag"><xsl:value-of select="$tag"/></span>
</xsl:template>

<!-- Call it -->
<xsl:call-template name="tag-badge">
  <xsl:with-param name="tag" select="'lead'"/>
</xsl:call-template>
```

### Match Template (pattern-based)
```xml
<xsl:template match="field[@type='text']" mode="form">
  <input type="text" name="{@name}"/>
</xsl:template>

<!-- Apply it -->
<xsl:apply-templates select="spec/fields/field" mode="form"/>
```

## Attribute Value Templates (AVT)

Use `{...}` to insert dynamic values in attributes:

```xml
<!-- Dynamic attribute values -->
<input type="text" name="{@name}" value="{@value}"/>

<!-- Multiple values -->
<div class="tag {$color-class}" title="Tag: {@tag}">

<!-- Concatenation -->
<a href="/{$form-name}/edit/{@id}">
```

## CDATA Sections for JavaScript

Wrap JavaScript in CDATA to avoid XML parsing:

```xml
<script>
  <xsl:text disable-output-escaping="yes"><![CDATA[
    // Your JavaScript here
    async function loadTags(recordId, formName) {
      const response = await fetch(`/api/${formName}/tags/${recordId}`);
      // ...
    }
  ]]></xsl:text>
</script>
```

## Testing Templates

### Compile Test
```python
from saxonche import PySaxonProcessor

proc = PySaxonProcessor(license=False)
xslt = proc.new_xslt30_processor()
stylesheet = xslt.compile_stylesheet(stylesheet_file='src/xslt/pages/form.xslt')
print('✓ Compiled successfully')
```

### Render Test
```python
from src.rendering.xslt_renderer import XSLTRenderer

renderer = XSLTRenderer(
    business_case_root="examples/ponto-de-vendas",
    src_root="src"
)

html = renderer.render_form_page(
    spec=spec,
    form_name="test",
    records=records,
    menu_items=menu_items,
    error="",
    new_record_id=""
)

assert "expected content" in html
```

## Debugging Tips

### 1. Check XML Structure
Save XML to file to inspect:
```python
xml_root = XMLBuilder.build_form_page_xml(...)
xml_str = XMLBuilder.element_to_string(xml_root)
with open("debug.xml", "w") as f:
    f.write(xml_str)
```

### 2. Check HTML Output
Save rendered HTML:
```python
html = renderer.render_form_page(...)
with open("debug.html", "w") as f:
    f.write(html)
```

### 3. Add Debug Output
Temporary debug statements in XSLT:
```xml
<!-- Debug: show current element -->
<xsl:comment>
  Processing field: <xsl:value-of select="@name"/>
</xsl:comment>
```

### 4. Validate XPath
Test XPath in Python:
```python
import xml.etree.ElementTree as ET

root = ET.fromstring(xml_string)
results = root.findall(".//field[@type='text']")
print(f"Found {len(results)} text fields")
```

## Common Issues

### Issue: Template Not Matching
**Problem:** Field not rendering
**Solution:** Check mode attribute matches

```xml
<!-- Make sure modes match -->
<xsl:apply-templates select="field" mode="form"/>
<xsl:template match="field[@type='text']" mode="form">
```

### Issue: Attribute Value Not Showing
**Problem:** `{@name}` shows as literal text
**Solution:** Use AVT (Attribute Value Template)

```xml
<!-- WRONG -->
<input name="@name"/>

<!-- RIGHT -->
<input name="{@name}"/>
```

### Issue: JavaScript Breaking XML
**Problem:** `<` and `>` in JavaScript break parsing
**Solution:** Use CDATA section

```xml
<script>
  <xsl:text disable-output-escaping="yes"><![CDATA[
    if (x < 5) { ... }
  ]]></xsl:text>
</script>
```

### Issue: Namespace Errors
**Problem:** Template imports fail
**Solution:** Check namespace declarations

```xml
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">
```

## File Organization

Keep templates modular and focused:

```
base/          - HTML structure, layouts
components/    - Reusable UI components
fields/        - Field type templates
pages/         - Full page templates
```

Each template should have a single responsibility and be independently testable.
