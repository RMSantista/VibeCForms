# Ponto-de-Vendas XSLT Template Overrides

This directory demonstrates VibeCForms' template override mechanism, allowing business cases to customize the visual rendering without modifying core templates.

## Overview

VibeCForms uses XSLT 3.0 templates to render all HTML output. The **TemplateResolver** system provides a fallback mechanism that allows business cases to override default templates:

1. **Priority 1**: Business case templates (`examples/ponto-de-vendas/xslt/`)
2. **Priority 2**: Default templates (`src/xslt/`)

If a template exists in the business case directory, it will be used instead of the default. This enables complete visual customization without maintaining a fork of the framework.

## Directory Structure

```
examples/ponto-de-vendas/xslt/
├── fields/
│   └── select.xslt          # Custom select field styling
├── components/
│   └── tag-badge.xslt       # Custom tag badge styling
├── tag-colors.css           # Tag color definitions
└── README.md                # This file
```

## Override Examples

### 1. Select Field Override (`fields/select.xslt`)

**Purpose**: Customize the appearance of dropdown select fields throughout the application.

**Customizations**:
- **Larger fonts**: `text-lg` instead of default size
- **Blue theme**: Blue borders and focus rings for POS system
- **Wider labels**: `w-64` (250px) for better form alignment
- **Enhanced hover effects**: Smooth transitions and visual feedback
- **Custom placeholder**: Portuguese placeholder text "-- Escolha uma opção --"
- **Badge display in tables**: Selected values displayed as blue badges instead of plain text

**How it works**:
1. The form rendering system looks for `fields/select.xslt` in the business case XSLT directory
2. Finds this file and uses it instead of `src/xslt/fields/select.xslt`
3. All select fields in the POS application now render with the customized styling

**Testing the override**:
1. Look at the "Contatos" or "Produtos" forms (both have select fields)
2. Select fields should appear with:
   - Larger text
   - Blue borders and focus rings
   - Wider labels
   - Smooth hover effects

### 2. Tag Badge Override (`components/tag-badge.xslt`)

**Purpose**: Customize how state tags are displayed in the Kanban and tags management interfaces.

**Customizations**:
- **Larger badges**: `px-4 py-2` (up from `px-2 py-1`) for better visibility
- **Icon prefixes**: Each tag type shows a relevant Font Awesome icon
- **Enhanced hover**: `hover:scale-110 hover:shadow-lg` for interactive feedback
- **Modern design**: Rounded corners (`rounded-full`) and drop shadows
- **Sales-specific icons**:
  - "lead" → target icon
  - "qualified" → check-circle icon
  - "proposal" → file-alt icon
  - "negotiation" → handshake icon
  - "won"/"closed" → trophy icon
  - "lost" → times-circle icon
  - Generic fallback → tag icon

**How it works**:
1. The tag rendering system resolves `components/tag-badge.xslt`
2. Finds this override and uses it instead of the default
3. All tags displayed in Kanban boards and tag managers use the customized styling
4. The `tag-icon` template maps tag names to appropriate Font Awesome icons

**Color System**:
- Tags use a consistent color hash: tag name → number (0-9) → color class
- `tag-colors.css` defines the 10 color classes
- Colors are sales-pipeline themed (cyan, emerald, blue, violet, etc.)

**Testing the override**:
1. Navigate to the Kanban view (if available)
2. Look at tags displayed on cards
3. Tags should appear as:
   - Larger, more prominent badges
   - With relevant icons (target, trophy, etc.)
   - With smooth scaling animations on hover

## How Template Overrides Work

### Template Resolution Flow

```
User requests page
    ↓
XSLT renderer needs template (e.g., "fields/select.xslt")
    ↓
TemplateResolver.resolve("fields/select.xslt")
    ↓
Check: examples/ponto-de-vendas/xslt/fields/select.xslt exists?
    ├─ YES → Use this file ✓
    └─ NO → Check next location
         ↓
    Check: src/xslt/fields/select.xslt exists?
         ├─ YES → Use this file ✓
         └─ NO → Raise FileNotFoundError
```

### Python Implementation

The resolver is located in `src/rendering/template_resolver.py`:

```python
class TemplateResolver:
    def resolve(self, template_name: str) -> str:
        # Check business case first
        business_path = os.path.join(self.business_case_xslt, template_name)
        if os.path.exists(business_path):
            return business_path

        # Fallback to src
        src_path = os.path.join(self.src_xslt, template_name)
        if os.path.exists(src_path):
            return src_path

        raise FileNotFoundError(f"Template not found: {template_name}")
```

## Creating New Overrides

To add a new override for your business case:

### Step 1: Copy the Default Template
```bash
# Find the template you want to override
find src/xslt -name "*.xslt"

# Copy the structure to your business case
mkdir -p examples/ponto-de-vendas/xslt/components
cp src/xslt/components/form-card.xslt examples/ponto-de-vendas/xslt/components/
```

### Step 2: Modify the Template
Edit the copied file with your customizations. For example, changing colors, fonts, spacing, or HTML structure.

### Step 3: Add Comments
Include a header comment explaining:
- What business case this is for
- What customizations were made
- Why these changes were made

Example:
```xslt
<!--
  PONTO-DE-VENDAS BUSINESS CASE OVERRIDE
  Custom form card styling for retail operations

  Customizations:
  - Larger card shadows for better depth
  - Orange accent color for buttons
  - Smaller text for compact layout
-->
```

### Step 4: Test
Run the application and verify the override works:
```bash
uv run app examples/ponto-de-vendas
```

## Available Templates to Override

Templates you can customize (by copying from `src/xslt/`):

**Fields** (`xslt/fields/`):
- `input.xslt` - Text, email, tel, number, etc.
- `select.xslt` - Dropdown fields (EXAMPLE: Already overridden)
- `radio.xslt` - Radio button groups
- `checkbox.xslt` - Checkbox fields
- `textarea.xslt` - Multi-line text
- `color.xslt` - Color picker
- `range.xslt` - Slider input
- `search-autocomplete.xslt` - Search with autocomplete
- `hidden.xslt` - Hidden fields
- `uuid-display.xslt` - UUID display

**Components** (`xslt/components/`):
- `form-card.xslt` - Form cards on landing page
- `table-header.xslt` - Table column headers
- `table-row.xslt` - Table data rows
- `tag-badge.xslt` - Tag display badges (EXAMPLE: Already overridden)
- `error-message.xslt` - Error message display
- `menu.xslt` - Navigation menu

**Pages** (`xslt/pages/`):
- `index.xslt` - Landing page
- `form.xslt` - Form page
- `edit.xslt` - Edit page
- `kanban.xslt` - Kanban board
- `tags-manager.xslt` - Tags management
- `migration-confirm.xslt` - Migration confirmation

**Base** (`xslt/base/`):
- `html-shell.xslt` - HTML document structure

## Best Practices

### 1. Keep Overrides Minimal
Only override templates that need customization. Keep the base structure the same to maintain compatibility with future framework updates.

### 2. Maintain Mode Compatibility
XSLT uses modes for rendering in different contexts (form, table, display). Ensure all modes are implemented:
```xslt
<!-- Form mode - used in input forms -->
<xsl:template match="field[@type='select']" mode="form">
  <!-- ... -->
</xsl:template>

<!-- Table mode - used in data tables -->
<xsl:template match="field[@type='select']" mode="table">
  <!-- ... -->
</xsl:template>
```

### 3. Use Tailwind Classes
VibeCForms uses Tailwind CSS for styling. Continue using Tailwind in overrides for consistency:
```xslt
<div class="mb-4 flex items-center gap-2">
  <!-- Tailwind classes: mb-4, flex, items-center, gap-2 -->
</div>
```

### 4. Include Documentation Comments
Always explain what the override does and why:
```xslt
<!--
  BUSINESS-CASE OVERRIDE HEADER

  Purpose: Clear description
  Customizations:
  - Change 1
  - Change 2
  - Change 3
-->
```

### 5. Test Thoroughly
- Test forms with the overridden field
- Test data display in tables
- Test responsive behavior
- Test with different field configurations

## Troubleshooting

### Override Not Being Applied

1. **Check path**: Verify the file is in the correct directory structure
   ```bash
   ls -R examples/ponto-de-vendas/xslt/
   # Should show fields/ and components/ subdirectories
   ```

2. **Check template name**: Template name must match exactly
   ```
   examples/ponto-de-vendas/xslt/fields/select.xslt
   ✓ Matches "fields/select.xslt"
   ```

3. **Check XSLT syntax**: Verify the file is valid XML/XSLT
   ```bash
   # Look for parse errors in application logs
   uv run app examples/ponto-de-vendas 2>&1 | grep -i error
   ```

### Styles Not Appearing

1. **Ensure Tailwind classes are used**: Overrides should use Tailwind classes that are scanned by Tailwind
2. **Check CSS generation**: Make sure `tag-colors.css` is included in the Tailwind configuration if using custom classes
3. **Test in browser**: Open DevTools and verify the CSS is loaded

## Running with Overrides

Start the application with the business case:

```bash
# Development
uv run app examples/ponto-de-vendas

# Production
BUSINESS_CASE_PATH=examples/ponto-de-vendas uv run hatch run serve
```

The application will automatically detect and use templates from the business case's `xslt/` directory.

## Related Files

- `src/rendering/template_resolver.py` - Resolution logic
- `src/rendering/xslt_renderer.py` - XSLT rendering engine
- `src/xslt/` - Default templates
- `CLAUDE.md` - Framework documentation
