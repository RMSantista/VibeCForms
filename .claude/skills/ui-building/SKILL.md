---
name: ui-building
description: AUTO-ACTIVATE on keywords (XSLT, saxonche, Tailwind, UI templates, form rendering, declarative templating, pattern matching, component styling, template rules, modes). Build VibeCForms UI using XSLT 3.0 + Tailwind CSS for declarative JSON-to-HTML transformations with utility-first styling and pattern-based component architecture.
---

# UI Building with XSLT 3.0 + Tailwind CSS for VibeCForms

## Overview

Build flexible, component-based UIs for VibeCForms using XSLT 3.0 templating with Tailwind CSS utility classes. This combination provides:

- **Declarative templates** that match data patterns automatically (XSLT)
- **Utility-first styling** through Tailwind classes
- **Component flexibility** through template rules and modes
- **Consistent styling** through Tailwind's design system

This approach aligns with VibeCForms' convention-based philosophy, enabling rapid UI development.

## When to Use This Skill

**Activation Keywords:**
- XSLT, saxonche, XML templating
- Tailwind, CSS utilities, styling, responsive design
- UI components, form rendering, template patterns
- Declarative templating, pattern matching, template rules, modes
- Component styling, HTML generation, JSON-to-HTML

## Quick Start

**Render a VibeCForms UI with XSLT + Tailwind:**

```python
from saxonche import PySaxonProcessor
import json

# Initialize processor
proc = PySaxonProcessor(license=False)
xslt_proc = proc.new_xslt30_processor()

# Load your XSLT template
xslt = xslt_proc.compile_stylesheet(stylesheet_file="templates/form.xslt")

# Prepare VibeCForms data
data = {
    "spec": {
        "title": "Contact Form",
        "fields": [
            {"name": "nome", "label": "Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email"}
        ]
    },
    "records": []
}

# Transform to HTML
html = xslt.transform_to_string(source_node=proc.parse_json(json.dumps(data)))
print(html)
```

**Template structure (form.xslt):**
```xslt
<xsl:template match="map(*)[?spec]">
  <html>
    <head>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 p-6">
      <xsl:apply-templates select="?spec" mode="form"/>
    </body>
  </html>
</xsl:template>
```

## Most Common Patterns (Copy-Paste Ready)

### Text Input with Tailwind

```xslt
<xsl:template match="map(*)[?type = 'text']">
  <div class="flex items-center gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
      <xsl:value-of select="?label"/>
    </label>
    <input type="text" name="{?name}"
           class="flex-1 px-3 py-2 rounded-lg border border-gray-300
                  focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                  dark:bg-gray-700 dark:border-gray-600"/>
  </div>
</xsl:template>
```

### Select Dropdown with Options

```xslt
<xsl:template match="map(*)[?type = 'select']">
  <div class="flex items-center gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700">
      <xsl:value-of select="?label"/>
    </label>
    <select name="{?name}"
            class="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white">
      <option value="">-- Select --</option>
      <xsl:for-each select="?options?*">
        <option value="{?value}">
          <xsl:value-of select="?label"/>
        </option>
      </xsl:for-each>
    </select>
  </div>
</xsl:template>
```

### Responsive Table with Horizontal Scroll

```xslt
<xsl:template match="array(*)" mode="table">
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <xsl:for-each select="?(1)?*">
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <xsl:value-of select="local-name()"/>
            </th>
          </xsl:for-each>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <xsl:apply-templates select="?*" mode="row"/>
      </tbody>
    </table>
  </div>
</xsl:template>

<xsl:template match="map(*)" mode="row">
  <tr class="hover:bg-gray-50 transition-colors">
    <xsl:for-each select="?*">
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        <xsl:value-of select="."/>
      </td>
    </xsl:for-each>
  </tr>
</xsl:template>
```

### Checkbox with Label

```xslt
<xsl:template match="map(*)[?type = 'checkbox']">
  <label class="flex items-center gap-2 cursor-pointer">
    <input type="checkbox" name="{?name}"
           class="w-4 h-4 text-blue-500 rounded focus:ring-4 focus:ring-blue-200">
      <xsl:if test="?checked">
        <xsl:attribute name="checked">checked</xsl:attribute>
      </xsl:if>
    </input>
    <span class="text-sm text-gray-700"><xsl:value-of select="?label"/></span>
  </label>
</xsl:template>
```

### Conditional Styling Based on State

```xslt
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}">
    <xsl:attribute name="class">
      <xsl:text>flex-1 px-3 py-2 rounded-lg border </xsl:text>
      <xsl:choose>
        <xsl:when test="?required">
          <xsl:text>border-red-500 focus:ring-red-200</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>border-gray-300 focus:ring-blue-200</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
  </input>
</xsl:template>
```

**See references below for complete patterns, advanced techniques, and VibeCForms integration.**

## Progressive Learning Path

### Level 1: Fundamentals
Start here to understand core concepts:
- **`references/xslt3_json.md`** - Working with JSON in XSLT 3.0 (map/array syntax)
- **`references/pattern_matching.md`** - How XSLT pattern matching works
- **`references/tailwind_basics.md`** - Tailwind utility classes with XSLT

### Level 2: Building Components
Build VibeCForms UI components:
- **`references/component_library.md`** - Complete field type templates (20+ types)
- **`references/tailwind_integration.md`** - Advanced Tailwind+XSLT patterns
- **`references/template_modes.md`** - Using modes for different UI contexts (form/card/table)

### Level 3: VibeCForms Integration
Integrate with VibeCForms conventions:
- **`references/vibecforms_integration.md`** - Shared Metadata, Tags as State
- **`references/data_preparation.md`** - Preparing VibeCForms data for XSLT
- **`references/flask_integration.md`** - Using XSLTRenderer with Flask routes

### Level 4: Advanced Techniques
Performance, debugging, and optimization:
- **`references/performance.md`** - Template caching, compilation, lazy loading
- **`references/troubleshooting.md`** - Common errors and solutions
- **`references/debugging.md`** - Debugging XSLT transformations

### Assets (Ready-to-Use Templates)

- **`assets/form_template.xslt`** - Complete form template with Tailwind
- **`assets/field_templates.xslt`** - All 20 VibeCForms field types
- **`assets/table_template.xslt`** - Responsive table rendering
- **`assets/card_template.xslt`** - Card/grid layouts
- **`assets/component_examples.xslt`** - Real VibeCForms examples

### Scripts (Python Integration)

- **`scripts/xslt_renderer.py`** - Saxonche wrapper for Flask integration
- **`scripts/convert_jinja_to_xslt.py`** - Migrate from Jinja2 to XSLT
- **`scripts/validate_xslt_data.py`** - Validate data before transformation

Run scripts with: `uv run python scripts/script_name.py`

---

**Start with Level 1 fundamentals, then progress through levels as needed. Reference assets for copy-paste templates.**
