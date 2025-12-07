# XSLT Form Page Implementation

## Overview

This document describes the complete XSLT template system for rendering VibeCForms form pages. The implementation provides a working proof-of-concept for migrating from Jinja2 to XSLT 3.0 + Tailwind CSS.

## Implementation Status

**Status:** ✅ Complete and Working

All 12 XSLT templates have been implemented and tested successfully:
- All templates compile without errors
- Full form page rendering works correctly
- Tests pass (4/4 passing)
- HTML output matches Jinja2 design with Tailwind styling

## Architecture

### Template Structure

```
src/xslt/
├── base/
│   └── html-shell.xslt          # HTML wrapper with Tailwind CDN and Font Awesome
├── components/
│   ├── menu.xslt                # Recursive sidebar menu
│   ├── error-message.xslt       # Error message display
│   ├── table-header.xslt        # Table column headers
│   ├── table-row.xslt           # Table rows with field transformations
│   └── tag-badge.xslt           # Tag badge with color hashing
├── fields/
│   ├── input.xslt               # Text, email, tel, number, password, date, etc.
│   ├── select.xslt              # Select dropdown with label lookup
│   ├── checkbox.xslt            # Checkbox with Sim/Não display
│   ├── uuid-display.xslt        # UUID display field
│   └── hidden.xslt              # Hidden input field
└── pages/
    └── form.xslt                # Main form page that imports everything
```

### Template Organization

**Base Templates:**
- `html-shell.xslt` - Provides the HTML5 wrapper with Tailwind CSS CDN and Font Awesome

**Component Templates:**
- `menu.xslt` - Recursive menu with support for forms, folders, and nested submenus
- `error-message.xslt` - Conditional error message rendering
- `table-header.xslt` - Generates table headers from spec fields
- `table-row.xslt` - Renders table rows with field-specific transformations
- `tag-badge.xslt` - Tag rendering with color hashing algorithm

**Field Templates:**
Each field template implements two modes:
- `mode="form"` - Renders the input field for the form
- `mode="table"` - Renders the field value in the table

**Page Templates:**
- `form.xslt` - Main entry point that orchestrates all components

## XML Structure

The XMLBuilder generates XML like this:

```xml
<form-page form-name="contatos" error="" new-record-id="abc123">
  <spec title="Contatos" icon="fa-address-book">
    <fields>
      <field name="nome" label="Nome" type="text" required="true" value=""/>
      <field name="estado" label="Estado" type="select" required="false" value="">
        <options>
          <option value="SP" label="São Paulo"/>
          <option value="RJ" label="Rio de Janeiro"/>
        </options>
      </field>
    </fields>
    <default-tags>
      <tag>lead</tag>
    </default-tags>
  </spec>
  <records>
    <record id="uuid-1">
      <field name="nome" type="text">João Silva</field>
      <field name="estado" type="select" value="SP">
        <options>
          <option value="SP" label="São Paulo"/>
          <option value="RJ" label="Rio de Janeiro"/>
        </options>
      </field>
    </record>
  </records>
  <menu>
    <item type="form" path="contatos" title="Contatos" icon="fa-address-book" active="true"/>
    <item type="folder" path="financeiro" title="Financeiro" icon="fa-folder" active-path="false">
      <item type="form" path="financeiro/contas" title="Contas" icon=""/>
    </item>
  </menu>
</form-page>
```

## XSLT Best Practices Used

### 1. Template Matching with Modes

Instead of loops, we use pattern matching:

```xml
<!-- Form mode: render input field -->
<xsl:template match="field[@type='text']" mode="form">
  <div class="mb-4 flex items-center gap-2">
    <label for="{@name}" class="w-48 font-semibold text-gray-700">
      <xsl:value-of select="@label"/>:
    </label>
    <input type="text" name="{@name}" value="{@value}"
           class="flex-1 px-3 py-2 border border-gray-300 rounded-md"/>
  </div>
</xsl:template>

<!-- Table mode: render plain text -->
<xsl:template match="field[@type='text']" mode="table">
  <xsl:value-of select="."/>
</xsl:template>
```

### 2. Apply-Templates Instead of For-Each

```xml
<!-- Good: Pattern matching -->
<xsl:apply-templates select="spec/fields/field" mode="form"/>

<!-- Avoided: Imperative loops -->
<!-- <xsl:for-each select="spec/fields/field">...</xsl:for-each> -->
```

### 3. Reusable Named Templates

```xml
<xsl:template name="tag-badge">
  <xsl:param name="tag" as="xs:string"/>
  <span class="tag tag-color-{...}">
    <xsl:value-of select="$tag"/>
  </span>
</xsl:template>
```

### 4. Template Includes

```xml
<xsl:include href="../fields/input.xslt"/>
<xsl:include href="../fields/select.xslt"/>
<xsl:include href="../components/menu.xslt"/>
```

## Tailwind CSS Usage

All styling uses Tailwind utility classes:

**Form Layout:**
- Form row: `mb-4 flex items-center gap-2`
- Label: `w-48 font-semibold text-gray-700`
- Input: `flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500`

**Table Styling:**
- Table: `w-full border-collapse min-w-[600px]`
- Header: `bg-blue-500 text-white px-4 py-3 text-center`
- Cell: `px-4 py-3 text-center align-middle`

**Sidebar Menu:**
- Container: `w-64 bg-gray-800 text-white fixed h-screen flex flex-col z-50`
- Active item: `bg-blue-500 text-white`
- Hover: `hover:bg-gray-700 hover:text-blue-400`

**Buttons:**
- Primary: `bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600`
- Edit: `bg-yellow-500 text-white px-3 py-2 rounded hover:bg-yellow-600`
- Delete: `bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600`

## Field Type Support

### Form Rendering (mode="form")

All fields render as horizontal label-input pairs:

**Input Types:**
- `text`, `email`, `tel`, `number`, `password`, `date`, `url`, `search`
- `datetime-local`, `time`, `month`, `week`

**Select:**
- Dropdown with "-- Selecione --" placeholder
- Options from spec

**Checkbox:**
- Standard checkbox input

**Hidden:**
- Hidden input (not visible)

**UUID:**
- Read-only display (only shown when editing existing records)

### Table Rendering (mode="table")

Field values transform based on type:

| Field Type | Transformation |
|------------|----------------|
| text, email, tel, number, date, etc. | Plain text value |
| password | Masked as `••••••••` |
| checkbox | `Sim` or `Não` |
| select | Display option label instead of value |
| hidden | Not displayed |
| UUID | Not displayed |

## JavaScript Preservation

All JavaScript from the Jinja2 template is preserved in `<![CDATA[...]]>` sections:

**Tag Management:**
- `loadTags(recordId, formName)` - Loads tags via API
- `getTagColorClass(tag)` - Hash function for consistent colors
- `displayTags(recordId, formName, tags)` - Renders tag badges
- `addTag(recordId, formName, tag)` - Adds a tag
- `removeTag(recordId, formName, tag)` - Removes a tag
- `validateTagName(tag)` - Validates tag format

**Menu Positioning:**
- Dynamic submenu positioning based on parent position
- Handles nested submenus

**Form Behavior:**
- Prevents Enter key from submitting form
- Auto-loads tags for all records on page load

## Tag Color Hashing

Tags are assigned consistent colors using a simple hash function:

```xslt
<xsl:template name="tag-color-hash">
  <xsl:param name="tag" as="xs:string"/>

  <xsl:variable name="hash" as="xs:integer">
    <xsl:value-of select="
      sum(
        for $char in string-to-codepoints($tag)
        return $char
      ) mod 10
    "/>
  </xsl:variable>

  <xsl:value-of select="concat('tag-color-', $hash)"/>
</xsl:template>
```

This produces classes like `tag-color-0` through `tag-color-9`, which map to predefined color values in CSS.

## Menu Rendering

The menu supports recursive nesting:

**Structure:**
- Forms: Direct links with active state
- Folders: Contain submenus with nested items
- Nested folders: Multiple levels supported

**Active States:**
- `active="true"` - Current form (blue background)
- `active-path="true"` - Parent folder of current form (gray background)

**Hover Behavior:**
- Submenus appear on hover
- Position dynamically calculated via JavaScript

## Testing

All tests pass successfully:

```bash
$ uv run pytest tests/test_xslt_form_rendering.py -v
tests/test_xslt_form_rendering.py::test_form_page_rendering PASSED
tests/test_xslt_form_rendering.py::test_form_page_with_error PASSED
tests/test_xslt_form_rendering.py::test_form_page_empty_records PASSED
tests/test_xslt_form_rendering.py::test_xml_structure PASSED
```

**Test Coverage:**
- Complete form page rendering with all field types
- Error message display
- Empty records handling
- XML structure validation
- Select option label lookup
- Checkbox Sim/Não display
- Password masking
- Tag badge rendering
- JavaScript preservation
- Menu rendering

## Next Steps

This proof-of-concept demonstrates that XSLT migration is viable. Next phases:

1. **Index Page** - Implement `pages/index.xslt` for landing page
2. **Edit Page** - Implement `pages/edit.xslt` for record editing
3. **Additional Fields** - Add templates for remaining field types:
   - `textarea.xslt`
   - `radio.xslt`
   - `color.xslt`
   - `range.xslt`
4. **Route Integration** - Update Flask routes to use XSLT renderer
5. **Performance Testing** - Measure rendering speed vs Jinja2
6. **Business Case Overrides** - Test template override system

## Files Implemented

All templates are in `/Users/ronie/code/python/VibeCForms/src/xslt/`:

```
base/html-shell.xslt
components/menu.xslt
components/error-message.xslt
components/table-header.xslt
components/table-row.xslt
components/tag-badge.xslt
fields/input.xslt
fields/select.xslt
fields/checkbox.xslt
fields/uuid-display.xslt
fields/hidden.xslt
pages/form.xslt
```

Test file: `/Users/ronie/code/python/VibeCForms/tests/test_xslt_form_rendering.py`

## Summary

The XSLT form page implementation is complete and working:

✅ All 12 templates implemented
✅ Tailwind CSS styling applied
✅ Pattern matching instead of loops
✅ Field type transformations (form + table modes)
✅ Recursive menu rendering
✅ Tag color hashing
✅ JavaScript preserved
✅ All tests passing
✅ HTML output matches Jinja2 design

The proof-of-concept successfully demonstrates that XSLT 3.0 can handle VibeCForms' rendering requirements with clean, maintainable templates.
