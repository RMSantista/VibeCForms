# XSLT Pattern Matching Deep Dive

Pattern matching is the core paradigm of XSLT. Instead of writing explicit loops and conditionals, you define transformation rules (templates) that automatically apply when data matches specific patterns.

## Core Concept: Declarative Transformation

**Imperative approach (Jinja2, Python):**
```python
for field in fields:
    if field['type'] == 'text':
        render_text_input(field)
    elif field['type'] == 'select':
        render_select(field)
```

**Declarative approach (XSLT):**
```xslt
<!-- Define rules, engine applies them -->
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}"/>
</xsl:template>

<xsl:template match="map(*)[?type = 'select']">
  <select name="{?name}">
    <xsl:apply-templates select="?options?*"/>
  </select>
</xsl:template>

<!-- Trigger transformation -->
<xsl:apply-templates select="?fields?*"/>
```

The XSLT engine automatically finds and applies the matching template for each field.

## Match Pattern Syntax

### Basic Patterns

```xslt
<!-- Match any element -->
<xsl:template match="*">

<!-- Match any map -->
<xsl:template match="map(*)">

<!-- Match any array -->
<xsl:template match="array(*)">

<!-- Match text nodes -->
<xsl:template match="text()">

<!-- Match root -->
<xsl:template match="/">
```

### Predicate Patterns

Predicates `[...]` filter matches based on conditions:

```xslt
<!-- Match maps with specific key -->
<xsl:template match="map(*)[?name]">

<!-- Match maps with specific key-value pair -->
<xsl:template match="map(*)[?type = 'text']">

<!-- Match maps with multiple conditions -->
<xsl:template match="map(*)[?type = 'text' and ?required]">

<!-- Match maps where key exists and is truthy -->
<xsl:template match="map(*)[?active = true()]">

<!-- Negative matching -->
<xsl:template match="map(*)[not(?hidden)]">
```

### Combining Patterns

```xslt
<!-- Match either condition -->
<xsl:template match="map(*)[?type = 'text' or ?type = 'email']">

<!-- Match nested conditions -->
<xsl:template match="map(*)[?type = 'select'][?options]">
  <!-- Both predicates must match -->
</xsl:template>
```

## Template Priority and Conflict Resolution

When multiple templates match the same node, XSLT uses priority rules:

### Default Priority

```xslt
<!-- Lower priority (general pattern) -->
<xsl:template match="map(*)">
  <!-- Fallback for any map -->
</xsl:template>

<!-- Higher priority (specific pattern) -->
<xsl:template match="map(*)[?type = 'text']">
  <!-- More specific, takes precedence -->
</xsl:template>
```

More specific patterns automatically have higher priority.

### Explicit Priority

```xslt
<!-- Force high priority -->
<xsl:template match="map(*)" priority="10">
  <!-- Always wins -->
</xsl:template>

<!-- Force low priority (fallback) -->
<xsl:template match="map(*)" priority="-1">
  <!-- Only if no other template matches -->
</xsl:template>
```

### Example: Field Type Hierarchy

```xslt
<!-- Catch-all fallback (priority -1) -->
<xsl:template match="map(*)[?type]" priority="-1">
  <xsl:message>Unknown field type: <xsl:value-of select="?type"/></xsl:message>
  <input type="text" name="{?name}"/>  <!-- Safe fallback -->
</xsl:template>

<!-- Specific field types (default priority) -->
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}"/>
</xsl:template>

<xsl:template match="map(*)[?type = 'email']">
  <input type="email" name="{?name}"/>
</xsl:template>

<xsl:template match="map(*)[?type = 'password']">
  <input type="password" name="{?name}"/>
</xsl:template>

<!-- Very specific override (higher priority) -->
<xsl:template match="map(*)[?type = 'text' and ?name = 'uuid']">
  <!-- Special handling for UUID text fields -->
  <input type="text" name="{?name}" readonly="readonly" class="uuid"/>
</xsl:template>
```

## Template Modes

Modes allow different transformations of the same data in different contexts:

```xslt
<!-- Default mode: render form -->
<xsl:apply-templates select="?spec"/>

<!-- Table mode: render as table -->
<xsl:apply-templates select="?spec" mode="table"/>

<!-- Edit mode: pre-fill with values -->
<xsl:apply-templates select="?spec" mode="edit">
  <xsl:with-param name="record" select="$current_record"/>
</xsl:apply-templates>
```

### Mode Examples

```xslt
<!-- Form rendering mode -->
<xsl:template match="map(*)[?fields]" mode="form">
  <form>
    <xsl:apply-templates select="?fields?*" mode="form-field"/>
  </form>
</xsl:template>

<!-- Table rendering mode -->
<xsl:template match="map(*)[?fields]" mode="table-header">
  <thead>
    <tr>
      <xsl:apply-templates select="?fields?*" mode="table-header-cell"/>
    </tr>
  </thead>
</xsl:template>

<!-- Field as form input -->
<xsl:template match="map(*)[?type = 'text']" mode="form-field">
  <input type="text" name="{?name}"/>
</xsl:template>

<!-- Field as table header -->
<xsl:template match="map(*)[?type = 'text']" mode="table-header-cell">
  <th><xsl:value-of select="?label"/></th>
</xsl:template>
```

## Parameters in Templates

Templates can accept parameters for context-specific behavior:

```xslt
<!-- Pass parameter -->
<xsl:apply-templates select="?fields?*">
  <xsl:with-param name="mode" select="'edit'"/>
  <xsl:with-param name="record" select="$current_record"/>
</xsl:apply-templates>

<!-- Receive parameter -->
<xsl:template match="map(*)[?type = 'text']">
  <xsl:param name="mode" select="'create'"/>
  <xsl:param name="record" select="map{}"/>

  <input type="text" name="{?name}">
    <xsl:if test="$mode = 'edit'">
      <xsl:attribute name="value" select="$record(?name)"/>
    </xsl:if>
  </input>
</xsl:template>
```

## Recursive Pattern Application

XSLT automatically handles recursion:

```xslt
<!-- Process nested structure -->
<xsl:template match="map(*)[?children]">
  <div class="parent">
    <xsl:value-of select="?name"/>
    <!-- Recursively process children -->
    <xsl:apply-templates select="?children?*"/>
  </div>
</xsl:template>

<!-- Child items will match the same template if they have children -->
<!-- Or different templates if their structure differs -->
```

## VibeCForms Pattern Examples

### Form Spec Patterns

```xslt
<!-- Match root data structure -->
<xsl:template match="map(*)[?spec and ?records]">
  <html>
    <head>
      <title><xsl:value-of select="?spec?title"/></title>
    </head>
    <body>
      <xsl:apply-templates select="?spec" mode="form"/>
      <xsl:apply-templates select="?records" mode="table"/>
    </body>
  </html>
</xsl:template>

<!-- Match form spec -->
<xsl:template match="map(*)[?fields]" mode="form">
  <form>
    <xsl:apply-templates select="?fields?*"/>
  </form>
</xsl:template>
```

### Field Type Patterns

```xslt
<!-- Text-like inputs -->
<xsl:template match="map(*)[?type = ('text', 'email', 'tel', 'url')]">
  <input type="{?type}" name="{?name}">
    <xsl:if test="?required = true()">
      <xsl:attribute name="required">required</xsl:attribute>
    </xsl:if>
  </input>
</xsl:template>

<!-- Select field -->
<xsl:template match="map(*)[?type = 'select']">
  <select name="{?name}">
    <xsl:apply-templates select="?options?*" mode="option"/>
  </select>
</xsl:template>

<!-- Option within select -->
<xsl:template match="map(*)" mode="option">
  <option value="{?value}">
    <xsl:value-of select="?label"/>
  </option>
</xsl:template>

<!-- Checkbox -->
<xsl:template match="map(*)[?type = 'checkbox']">
  <input type="checkbox" name="{?name}">
    <xsl:if test="?checked = true()">
      <xsl:attribute name="checked">checked</xsl:attribute>
    </xsl:if>
  </input>
</xsl:template>

<!-- Range with display -->
<xsl:template match="map(*)[?type = 'range']">
  <input type="range" name="{?name}"
         min="{?min}" max="{?max}" step="{(?step, 1)[1]}"/>
  <span class="range-value"><xsl:value-of select="(?value, ?min)[1]"/></span>
</xsl:template>
```

### Table Rendering Patterns

```xslt
<!-- Match records array -->
<xsl:template match="array(*)" mode="table">
  <xsl:if test="array:size(.) gt 0">
    <table>
      <thead>
        <xsl:call-template name="table-header">
          <xsl:with-param name="first-record" select="?(1)"/>
        </xsl:call-template>
      </thead>
      <tbody>
        <xsl:apply-templates select="?*" mode="table-row"/>
      </tbody>
    </table>
  </xsl:if>
</xsl:template>

<!-- Match individual record -->
<xsl:template match="map(*)" mode="table-row">
  <tr>
    <xsl:for-each select="?*">
      <td><xsl:value-of select="."/></td>
    </xsl:for-each>
  </tr>
</xsl:template>
```

### Conditional Field Rendering

```xslt
<!-- Only render visible fields -->
<xsl:template match="map(*)[?type and not(?hidden = true())]">
  <div class="form-row">
    <label><xsl:value-of select="?label"/>:</label>
    <xsl:apply-templates select="." mode="{?type}"/>
  </div>
</xsl:template>

<!-- Hidden fields: no visual rendering -->
<xsl:template match="map(*)[?type = 'hidden']">
  <!-- No output, or just the input tag without wrapper -->
  <input type="hidden" name="{?name}" value="{?value}"/>
</xsl:template>

<!-- Password fields: mask in table view -->
<xsl:template match="map(*)[?type = 'password']" mode="table-cell">
  <td>********</td>
</xsl:template>
```

## Advanced Patterns

### Dynamic Mode Selection

```xslt
<!-- Select mode based on data -->
<xsl:template match="map(*)[?fields]">
  <xsl:variable name="render-mode" select="
    if (?read_only = true()) then 'display'
    else 'edit'
  "/>

  <xsl:apply-templates select="?fields?*" mode="{$render-mode}"/>
</xsl:template>
```

### Grouping and Sorting

```xslt
<!-- Group fields by category -->
<xsl:template match="map(*)[?fields]">
  <form>
    <xsl:for-each-group select="?fields?*" group-by="?category">
      <fieldset>
        <legend><xsl:value-of select="current-grouping-key()"/></legend>
        <xsl:apply-templates select="current-group()"/>
      </fieldset>
    </xsl:for-each-group>
  </form>
</xsl:template>

<!-- Sort fields by order -->
<xsl:template match="map(*)[?fields]">
  <form>
    <xsl:apply-templates select="?fields?*">
      <xsl:sort select="?order" data-type="number"/>
    </xsl:apply-templates>
  </form>
</xsl:template>
```

### Custom Field Types

```xslt
<!-- VibeCForms UUID display -->
<xsl:template match="map(*)[?type = 'uuid_display']">
  <div class="uuid-container">
    <code class="uuid"><xsl:value-of select="?value"/></code>
    <button type="button" class="copy-uuid" data-value="{?value}">
      Copy
    </button>
  </div>
</xsl:template>

<!-- Search with datasource -->
<xsl:template match="map(*)[?type = 'search' and ?datasource]">
  <input type="search" name="{?name}"
         list="{?datasource}-list"
         placeholder="Search {?datasource}..."/>
  <datalist id="{?datasource}-list">
    <!-- Populated dynamically via JavaScript -->
  </datalist>
</xsl:template>
```

## Best Practices

1. **Use specific patterns** - More specific patterns are easier to understand and maintain
2. **Leverage default priorities** - Avoid explicit priority unless needed
3. **Use modes for different contexts** - Don't duplicate templates
4. **Provide fallbacks** - Use `priority="-1"` for catch-all templates
5. **Document complex patterns** - Add XML comments explaining matching logic
6. **Test incrementally** - Add patterns one at a time
7. **Use named templates for utilities** - Not everything needs pattern matching

## Debugging Pattern Matches

```xslt
<!-- Add debug messages -->
<xsl:template match="map(*)[?type = 'text']">
  <xsl:message>Matched text field: <xsl:value-of select="?name"/></xsl:message>
  <input type="text" name="{?name}"/>
</xsl:template>

<!-- Show what data reached the template -->
<xsl:template match="map(*)[?fields]">
  <xsl:message>
    Rendering form with <xsl:value-of select="array:size(?fields)"/> fields
  </xsl:message>
  <xsl:apply-templates select="?fields?*"/>
</xsl:template>
```

## Common Pitfalls

### Overly Broad Patterns

```xslt
<!-- Bad: Too broad, matches everything -->
<xsl:template match="map(*)">
  <div>...</div>
</xsl:template>

<!-- Good: Specific pattern -->
<xsl:template match="map(*)[?type and ?name]">
  <div>...</div>
</xsl:template>
```

### Forgetting Array Iteration

```xslt
<!-- Bad: Tries to process array directly -->
<xsl:apply-templates select="?fields"/>

<!-- Good: Process array items -->
<xsl:apply-templates select="?fields?*"/>
```

### Mode Confusion

```xslt
<!-- Bad: Forgetting mode in nested apply-templates -->
<xsl:template match="map(*)" mode="table">
  <xsl:apply-templates select="?children"/>  <!-- Loses mode! -->
</xsl:template>

<!-- Good: Preserve mode -->
<xsl:template match="map(*)" mode="table">
  <xsl:apply-templates select="?children" mode="table"/>
</xsl:template>
```
