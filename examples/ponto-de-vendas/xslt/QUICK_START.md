# Quick Start: Template Overrides

## What's Here?

Two example XSLT template overrides demonstrating business case customization:

1. **Select Field** (`fields/select.xslt`) - Blue theme, larger fonts
2. **Tag Badge** (`components/tag-badge.xslt`) - Icons, bigger size, hover effects

## File Structure

```
xslt/
├── fields/
│   └── select.xslt          ← Override select field styling
├── components/
│   └── tag-badge.xslt       ← Override tag badge styling
├── tag-colors.css           ← Color definitions for tags
├── README.md                ← Complete documentation
├── CUSTOMIZATIONS.md        ← Detailed comparison of changes
├── QUICK_START.md           ← This file
└── OVERRIDE_TEST.md         ← Testing instructions
```

## How It Works

```
You request a form
       ↓
App needs to render "fields/select.xslt"
       ↓
TemplateResolver checks:
  1. examples/ponto-de-vendas/xslt/fields/select.xslt exists?
     → YES, use this! (OVERRIDE)
  2. src/xslt/fields/select.xslt exists?
     → Would use if override didn't exist (FALLBACK)
       ↓
Your custom select field renders with blue theme
```

## Start Here

### 1. Run the App
```bash
cd /Users/ronie/code/python/VibeCForms
uv run app examples/ponto-de-vendas
```
Open `http://localhost:5000`

### 2. See the Overrides in Action

**Select Field Override**:
- Open any form (e.g., `/contatos`)
- Look for select/dropdown fields
- Should be blue-themed with larger fonts

**Tag Badge Override**:
- Navigate to Kanban view (or tags manager)
- Look for state tags
- Should have icons and be larger

### 3. Read More Details
- `README.md` - Complete override documentation
- `CUSTOMIZATIONS.md` - Before/after comparison
- `OVERRIDE_TEST.md` - Step-by-step testing

## The Two Overrides

### Override 1: Select Field
**File**: `fields/select.xslt`

**Changes**:
- Larger font (18px)
- Blue borders (not gray)
- Wider labels (256px)
- Better focus state
- Hover effects
- Portuguese placeholder
- Table display as badges

**Where used**: All dropdown fields in forms

### Override 2: Tag Badge
**File**: `components/tag-badge.xslt`

**Changes**:
- Larger size (2x padding)
- Icon prefix for each tag
- Fully rounded corners
- Hover scale-up effect
- Better shadows
- Bold font weight

**Where used**: Kanban board tags, state display

## Creating Your Own Override

### Step 1: Pick a Template to Override
```bash
# See available templates
ls -R src/xslt/
```

### Step 2: Copy It
```bash
# Example: override table-row component
cp src/xslt/components/table-row.xslt \
   examples/ponto-de-vendas/xslt/components/
```

### Step 3: Customize
Edit the file with your changes. Keep the XSLT structure the same, just change the styling or HTML.

### Step 4: Test
```bash
uv run app examples/ponto-de-vendas
```

### Step 5: Document
Add a comment header explaining your override:
```xslt
<!--
  PONTO-DE-VENDAS OVERRIDE: Table Row

  Custom styling for table rows:
  - Alternating row colors
  - Larger padding for mobile
  - Custom action buttons
-->
```

## Key Points

✓ **Simple**: Just copy a template and modify it
✓ **Safe**: Doesn't affect other business cases or default templates
✓ **Fallback**: If you delete an override, default template is used
✓ **No Code**: Pure XSLT + Tailwind CSS, no Python changes needed
✓ **Professional**: Make templates match your brand

## Common Customizations

### Change Colors
Modify Tailwind classes like `text-blue-800` or `bg-blue-100`

### Change Sizes
Adjust padding (`px-4`, `py-2`) or font size (`text-lg`)

### Change Layout
Modify `flex`, `grid`, or `block` classes

### Add Elements
Insert icons, badges, or additional HTML

### Change Behavior
Modify hover states, focus styles, or animations

## Testing Checklist

- [ ] App starts without errors
- [ ] Override files exist in correct locations
- [ ] Forms display with customized styling
- [ ] Tags display with customized styling
- [ ] Hover effects work
- [ ] Mobile responsive (if relevant)
- [ ] No console errors in browser DevTools

## Troubleshooting

### Override not working?
1. Check file is in correct directory: `examples/ponto-de-vendas/xslt/<path>`
2. Check file name matches exactly
3. Check XSLT syntax with: `xmllint --noout <file>`
4. Restart the application

### Styles not appearing?
1. Verify Tailwind classes are correct (check Tailwind docs)
2. Restart app to rebuild CSS
3. Hard refresh browser (Cmd+Shift+R)

### Can't find template to override?
1. List available: `find src/xslt -name "*.xslt"`
2. Check directory structure matches

## Related Files

| File | Purpose |
|------|---------|
| `src/rendering/template_resolver.py` | Override resolution logic |
| `src/xslt/` | Default templates to override |
| `CLAUDE.md` | Framework documentation |
| `examples/ponto-de-vendas/` | Business case root |

## Next Steps

1. **Explore**: Look at the two example overrides
2. **Understand**: Read how each customizes the default
3. **Modify**: Change colors, sizes, or layout to your preference
4. **Create**: Add your own overrides for other components
5. **Deploy**: Use in production with BUSINESS_CASE_PATH

## Questions?

See `README.md` for comprehensive documentation including:
- How override resolution works
- Creating new overrides
- Best practices
- Troubleshooting guide
- Available templates

---

**Get started**: `uv run app examples/ponto-de-vendas` and visit `http://localhost:5000`
