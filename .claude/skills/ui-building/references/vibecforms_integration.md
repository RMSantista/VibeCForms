# XSLT Integration with VibeCForms Conventions

This guide shows how XSLT 3.0 aligns with VibeCForms' eight core conventions, providing concrete integration patterns.

## Convention #1: 1:1 CRUD-to-Table Mapping

XSLT doesn't affect this convention - it's purely a data persistence pattern. The transformation occurs after data is retrieved from storage.

```python
# VibeCForms controller
spec = load_spec("contatos.json")
records = repository.read_all("contatos", spec)  # 1:1 mapping

# XSLT transformation (separate concern)
data = {"spec": spec, "records": records}
html = xslt_renderer.render(data, "templates/form.xslt")
```

## Convention #2: Shared Metadata

**XSLT perfectly implements Shared Metadata.** The same JSON spec drives both UI rendering and database schema.

### Current Jinja2 Approach

```python
# Shared metadata with Jinja2
spec = load_spec("contatos.json")  # Single source of truth

# UI rendering
html = render_template("form.html",
    title=spec["title"],
    fields=spec["fields"],
    records=records)

# Database operations
repository.create("contatos", spec, form_data)  # Same spec
```

### XSLT Approach (Even More Direct)

```python
# Shared metadata with XSLT
spec = load_spec("contatos.json")  # Single source of truth

# UI rendering: Pass spec directly to XSLT
data = {"spec": spec, "records": records}
html = xslt_renderer.render(data, "templates/form.xslt")

# Database operations: Same spec
repository.create("contatos", spec, form_data)
```

**Benefit**: XSLT eliminates the intermediate `render_template()` parameter mapping. The spec flows directly through the transformation.

### XSLT Template for Shared Metadata

```xslt
<xsl:template match="map(*)[?spec]">
  <html>
    <head>
      <title><xsl:value-of select="?spec?title"/></title>
    </head>
    <body>
      <!-- Form driven by spec -->
      <xsl:apply-templates select="?spec" mode="form"/>

      <!-- Table driven by spec + records -->
      <xsl:apply-templates select="." mode="table"/>
    </body>
  </html>
</xsl:template>

<!-- Spec defines form structure -->
<xsl:template match="map(*)[?fields]" mode="form">
  <form>
    <xsl:apply-templates select="?fields?*"/>
  </form>
</xsl:template>

<!-- Spec + records define table -->
<xsl:template match="map(*)[?spec and ?records]" mode="table">
  <table>
    <thead>
      <tr>
        <!-- Headers from spec -->
        <xsl:for-each select="?spec?fields?*[not(?hidden)]">
          <th><xsl:value-of select="?label"/></th>
        </xsl:for-each>
      </tr>
    </thead>
    <tbody>
      <!-- Data from records -->
      <xsl:apply-templates select="?records?*" mode="table-row">
        <xsl:with-param name="fields" select="?spec?fields"/>
      </xsl:apply-templates>
    </tbody>
  </table>
</xsl:template>
```

## Convention #3: Relationship Tables

XSLT doesn't directly interact with relationship tables (they're a persistence pattern), but it can render relationships when they're loaded:

```xslt
<!-- Render relationship data -->
<xsl:template match="map(*)[?relationships]">
  <div class="relationships">
    <h3>Related Items</h3>
    <xsl:apply-templates select="?relationships?*" mode="relationship-link"/>
  </div>
</xsl:template>

<xsl:template match="map(*)" mode="relationship-link">
  <a href="/{?entity_type}/{?entity_id}">
    <xsl:value-of select="?display_name"/>
  </a>
</xsl:template>
```

## Convention #4: Tags as State

XSLT can render tag visualizations declaratively:

### Rendering Tags

```xslt
<!-- Render tags for a record -->
<xsl:template match="array(*)" mode="tags">
  <div class="tags-container">
    <xsl:apply-templates select="?*" mode="tag-badge"/>
  </div>
</xsl:template>

<!-- Individual tag badge -->
<xsl:template match="map(*)" mode="tag-badge">
  <span class="tag tag-color-{position() mod 10}">
    <xsl:value-of select="?tag"/>
  </span>
</xsl:template>

<!-- Tag in table cell -->
<xsl:template match="map(*)" mode="table-row-with-tags">
  <tr>
    <xsl:for-each select="?fields?*">
      <td><xsl:value-of select="?*"/></td>
    </xsl:for-each>
    <td class="tags-cell">
      <xsl:apply-templates select="?tags" mode="tags"/>
    </td>
  </tr>
</xsl:template>
```

### State-Based Rendering

```xslt
<!-- Render differently based on tags (state) -->
<xsl:template match="map(*)[?tags]" mode="deal-card">
  <xsl:variable name="state" select="?tags?*[1]?tag"/>  <!-- Primary state -->

  <div class="deal-card state-{$state}">
    <h4><xsl:value-of select="?name"/></h4>
    <xsl:apply-templates select="?tags" mode="tags"/>

    <!-- Conditional rendering based on state -->
    <xsl:choose>
      <xsl:when test="$state = 'closed'">
        <div class="success-badge">Closed Won</div>
      </xsl:when>
      <xsl:when test="$state = 'negotiation'">
        <div class="warning-badge">In Negotiation</div>
      </xsl:when>
    </xsl:choose>
  </div>
</xsl:template>
```

## Convention #5: Kanbans for State Transitions

XSLT can render Kanban boards declaratively:

```xslt
<!-- Render Kanban board -->
<xsl:template match="map(*)[?kanban_config]">
  <div class="kanban-board">
    <xsl:apply-templates select="?kanban_config?columns?*" mode="kanban-column">
      <xsl:with-param name="records" select="?records"/>
    </xsl:apply-templates>
  </div>
</xsl:template>

<!-- Kanban column -->
<xsl:template match="map(*)" mode="kanban-column">
  <xsl:param name="records"/>
  <xsl:variable name="column-tag" select="?tag"/>

  <div class="kanban-column" data-tag="{$column-tag}">
    <h3><xsl:value-of select="?label"/></h3>
    <div class="cards-container">
      <!-- Filter records by tag -->
      <xsl:apply-templates select="$records?*[?tags?*[?tag = $column-tag]]"
                           mode="kanban-card"/>
    </div>
  </div>
</xsl:template>

<!-- Kanban card -->
<xsl:template match="map(*)" mode="kanban-card">
  <div class="kanban-card" data-id="{?uuid}" draggable="true">
    <h4><xsl:value-of select="?title"/></h4>
    <p><xsl:value-of select="?description"/></p>
    <xsl:apply-templates select="?tags" mode="tags"/>
  </div>
</xsl:template>
```

## Convention #6: Uniform Actor Interface

XSLT renders the same data regardless of who performed the action (human, AI, or code):

```xslt
<!-- Render tag with actor information -->
<xsl:template match="map(*)" mode="tag-with-actor">
  <span class="tag" title="Applied by {?applied_by} at {?applied_at}">
    <xsl:value-of select="?tag"/>
  </span>
</xsl:template>

<!-- Activity log showing all actors uniformly -->
<xsl:template match="array(*)" mode="activity-log">
  <ul class="activity-log">
    <xsl:apply-templates select="?*" mode="activity-entry"/>
  </ul>
</xsl:template>

<xsl:template match="map(*)" mode="activity-entry">
  <li class="activity-item actor-{?actor_type}">
    <span class="actor-badge">
      <xsl:choose>
        <xsl:when test="?actor_type = 'human'">👤</xsl:when>
        <xsl:when test="?actor_type = 'ai'">🤖</xsl:when>
        <xsl:when test="?actor_type = 'code'">⚙️</xsl:when>
      </xsl:choose>
      <xsl:value-of select="?actor_name"/>
    </span>
    <span class="activity-description">
      <xsl:value-of select="?action"/>
    </span>
    <span class="activity-timestamp">
      <xsl:value-of select="?timestamp"/>
    </span>
  </li>
</xsl:template>
```

## Convention #7: Tag-Based Notifications

While notifications are triggered by code, XSLT can render notification preferences:

```xslt
<!-- Notification preferences form -->
<xsl:template match="map(*)[?notification_config]">
  <form class="notification-preferences">
    <h3>Tag Notifications</h3>
    <xsl:apply-templates select="?notification_config?tag_subscriptions?*"
                         mode="notification-toggle"/>
  </form>
</xsl:template>

<xsl:template match="map(*)" mode="notification-toggle">
  <div class="notification-row">
    <label>
      <input type="checkbox" name="notify_{?tag}"
             checked="{if (?enabled) then 'checked' else ''}"/>
      Notify on tag: <code><xsl:value-of select="?tag"/></code>
    </label>
  </div>
</xsl:template>
```

## Convention #8: Convention → Configuration → Code

XSLT reinforces this hierarchy:

### Convention (No Configuration)

```xslt
<!-- Convention: All text-like fields use same template -->
<xsl:template match="map(*)[?type = ('text', 'email', 'tel', 'url')]">
  <input type="{?type}" name="{?name}">
    <xsl:if test="?required = true()">
      <xsl:attribute name="required">required</xsl:attribute>
    </xsl:if>
  </input>
</xsl:template>
```

**No configuration needed** - the template automatically applies to all text-like fields.

### Configuration (JSON Customization)

```json
{
  "fields": [
    {
      "name": "priority",
      "type": "range",
      "min": 1,
      "max": 10,
      "step": 1,
      "default": 5
    }
  ]
}
```

```xslt
<!-- Configuration: Read min/max/step from spec -->
<xsl:template match="map(*)[?type = 'range']">
  <input type="range" name="{?name}"
         min="{?min}" max="{?max}" step="{(?step, 1)[1]}"
         value="{(?default, ?min)[1]}"/>
</xsl:template>
```

**Configuration only** - no code changes needed.

### Code (Custom Logic)

```xslt
<!-- Code: Custom business logic -->
<xsl:template match="map(*)[?type = 'text' and ?name = 'uuid']">
  <!-- Custom rendering for UUID fields -->
  <div class="uuid-display">
    <input type="text" name="{?name}" value="{?value}"
           readonly="readonly" class="uuid-field"/>
    <button type="button" onclick="copyUUID('{?value}')">
      Copy UUID
    </button>
  </div>
</xsl:template>
```

**Code only when needed** - for truly unique requirements.

## Complete Integration Example

Here's how all conventions work together in an XSLT template:

```xslt
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:map="http://www.w3.org/2005/xpath-functions/map"
                xmlns:array="http://www.w3.org/2005/xpath-functions/array">

  <xsl:output method="html" indent="yes" omit-xml-declaration="yes"/>

  <!-- Root template: Shared Metadata (Convention #2) -->
  <xsl:template match="map(*)[?spec and ?records]">
    <html>
      <head>
        <title><xsl:value-of select="?spec?title"/></title>
        <link rel="stylesheet" href="/static/styles.css"/>
      </head>
      <body>
        <div class="container">
          <h2><xsl:value-of select="?spec?title"/></h2>

          <!-- Form rendering -->
          <xsl:apply-templates select="?spec" mode="form"/>

          <!-- Table rendering with tags -->
          <xsl:apply-templates select="." mode="table-with-tags"/>
        </div>
      </body>
    </html>
  </xsl:template>

  <!-- Form mode: Convention over Configuration (Convention #8) -->
  <xsl:template match="map(*)[?fields]" mode="form">
    <form method="post">
      <xsl:apply-templates select="?fields?*[not(?hidden)]"/>
      <button type="submit">Submit</button>
    </form>
  </xsl:template>

  <!-- Field rendering: Convention for standard types -->
  <xsl:template match="map(*)[?type = ('text', 'email', 'tel')]">
    <div class="form-row">
      <label><xsl:value-of select="?label"/>:</label>
      <input type="{?type}" name="{?name}">
        <xsl:if test="?required = true()">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Table with tags: Tags as State (Convention #4) -->
  <xsl:template match="map(*)[?spec and ?records]" mode="table-with-tags">
    <table>
      <thead>
        <tr>
          <xsl:for-each select="?spec?fields?*[not(?hidden)]">
            <th><xsl:value-of select="?label"/></th>
          </xsl:for-each>
          <th>Tags</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <xsl:apply-templates select="?records?*" mode="table-row-with-tags">
          <xsl:with-param name="fields" select="?spec?fields"/>
        </xsl:apply-templates>
      </tbody>
    </table>
  </xsl:template>

  <!-- Table row with tags -->
  <xsl:template match="map(*)" mode="table-row-with-tags">
    <xsl:param name="fields"/>

    <tr data-uuid="{?uuid}">
      <!-- Data cells -->
      <xsl:for-each select="$fields?*[not(?hidden)]">
        <xsl:variable name="field-name" select="?name"/>
        <xsl:variable name="field-value" select="current()?($field-name)"/>
        <td><xsl:value-of select="$field-value"/></td>
      </xsl:for-each>

      <!-- Tags cell: Tags as State (Convention #4) -->
      <td class="tags-cell">
        <xsl:apply-templates select="?tags" mode="tags"/>
      </td>

      <!-- Actions cell -->
      <td>
        <a href="/{?form_path}/edit/{?uuid}">Edit</a>
        <a href="/{?form_path}/delete/{?uuid}">Delete</a>
      </td>
    </tr>
  </xsl:template>

  <!-- Tag rendering: Uniform Actor Interface (Convention #6) -->
  <xsl:template match="array(*)" mode="tags">
    <xsl:apply-templates select="?*" mode="tag-badge"/>
  </xsl:template>

  <xsl:template match="map(*)" mode="tag-badge">
    <span class="tag tag-color-{position() mod 10}"
          title="Applied by {?applied_by} ({?actor_type})">
      <xsl:value-of select="?tag"/>
    </span>
  </xsl:template>

</xsl:stylesheet>
```

## Flask Integration Pattern

```python
from flask import Flask, request
from scripts.xslt_renderer import XSLTRenderer

app = Flask(__name__)
renderer = XSLTRenderer()

# Load templates on startup
renderer.load_template("templates/form.xslt")

@app.route("/<path:form_path>", methods=["GET", "POST"])
def form_view(form_path):
    # Load spec (Shared Metadata - Convention #2)
    spec = load_spec(form_path)

    # Load records (1:1 CRUD-to-Table Mapping - Convention #1)
    records = repository.read_all(form_path, spec)

    # Load tags for each record (Tags as State - Convention #4)
    for record in records:
        record['tags'] = tag_service.get_tags(record['uuid'])

    # Render with XSLT
    data = {
        "spec": spec,
        "records": records,
        "form_path": form_path
    }

    html = renderer.render(data, "templates/form.xslt", pretty_print=True)
    return html
```

## Benefits of XSLT with VibeCForms

1. **Stronger Shared Metadata**: Spec flows directly through transformation
2. **Declarative Tag Rendering**: Tags as state maps naturally to pattern matching
3. **Consistent Actor Display**: Uniform rendering regardless of actor type
4. **Convention Enforcement**: Pattern matching enforces consistent field rendering
5. **Configuration Flexibility**: XSLT reads configuration directly from specs
6. **Clear Separation**: Transformation logic separate from Python business logic

## Tailwind Styling Conventions

Tailwind CSS integrates with VibeCForms conventions by providing consistent, utility-based styling that aligns with the framework's philosophy.

### Convention-Based Styling Patterns

**Form Row Pattern (Shared Metadata):**
```xslt
<!-- Consistent layout for all field types -->
<div class="flex items-center gap-3 mb-4">
  <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
  <div class="flex-1">
```

**Tag Badges (Tags as State):**
```xslt
<xsl:template match="map(*)" mode="tag-badge">
  <span class="px-3 py-1 rounded-full text-xs font-semibold {
    if (?color = 'active') then 'bg-green-500 text-white'
    else if (?color = 'pending') then 'bg-orange-500 text-white'
    else 'bg-gray-500 text-white'
  }">
    <xsl:value-of select="?tag"/>
  </span>
</xsl:template>
```

**Kanban Columns (Convention #5):**
```xslt
<div class="flex-shrink-0 w-80 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="font-semibold"><xsl:value-of select="?column_label"/></h3>
    <span class="px-2 py-1 bg-gray-200 rounded-full text-xs">
      <xsl:value-of select="count(?cards?*)"/>
    </span>
  </div>
</div>
```

### Configuration over Code

Tailwind classes can be configured via spec extensions:

```json
{
  "title": "High Priority Tasks",
  "fields": [...],
  "ui_config": {
    "theme": "red",
    "highlight": true
  }
}
```

```xslt
<div class="{
  if (?ui_config?theme = 'red') then 'border-l-4 border-red-500'
  else if (?ui_config?theme = 'blue') then 'border-l-4 border-blue-500'
  else ''
}">
```

### VibeCForms Color Palette

Map VibeCForms colors to Tailwind:

| VibeCForms | Tailwind      | Usage                    |
|-----------|---------------|--------------------------|
| Primary   | `blue-500`    | Buttons, links, focus    |
| Success   | `green-500`   | Success states, active tags |
| Warning   | `orange-500`  | Warnings, pending states |
| Danger    | `red-500`     | Errors, delete actions   |
| Dark BG   | `gray-800`    | Sidebar, navigation      |

### Responsive & Dark Mode (Convention over Configuration)

Apply responsive and dark mode automatically:

```xslt
<!-- No configuration needed - convention handles it -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

<!-- Dark mode variants applied consistently -->
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
```

This demonstrates **Convention over Configuration**: standard Tailwind patterns work without custom configuration.
