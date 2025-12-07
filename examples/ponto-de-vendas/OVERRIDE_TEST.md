# Testing Ponto-de-Vendas Template Overrides

This guide explains how to verify that the template overrides are working correctly in the ponto-de-vendas business case.

## Quick Start

### 1. Start the Application
```bash
cd /Users/ronie/code/python/VibeCForms
uv run app examples/ponto-de-vendas
```

The application will start on `http://0.0.0.0:5000` (or `http://localhost:5000`).

### 2. Verify Override Detection
The application should detect and load the overrides automatically. To verify in the Python logs:

```
$ uv run app examples/ponto-de-vendas
 * Running on http://0.0.0.0:5000
 * Template resolver initialized for business case: examples/ponto-de-vendas
 * Override templates detected:
   - components/tag-badge.xslt
   - fields/select.xslt
```

## Testing the Select Field Override

### Visual Indicators
Look for these styling differences in select fields (dropdowns):

1. **Larger Fonts**: Select fields should use `text-lg` (18px) instead of default
2. **Blue Theme**:
   - Border: Blue (#3B82F6) instead of gray
   - Focus ring: Bright blue (#60A5FA) with rounded corners
   - Hover effect: Border becomes darker blue
3. **Wider Labels**: Field labels should be wider (250px) for better alignment
4. **Padding**: More generous padding (`py-3` instead of `py-2`)
5. **Placeholder Text**: Should say "-- Escolha uma opção --" (Portuguese)

### Where to Test
Open these forms in your browser:

#### Form 1: Contatos (Contacts)
- **URL**: `http://localhost:5000/contatos`
- **Select fields**: None by default, but can be added for category/status

#### Form 2: Produtos (Products)
- **URL**: `http://localhost:5000/produtos`
- **Select fields**: None by default, but can be added

#### Form 3: Financeiro → Contas (Financial → Accounts)
- **URL**: `http://localhost:5000/financeiro/contas`
- **Select fields**: Check the "tipo" field if it's a select

### Manual Verification Steps

1. **Open browser DevTools** (`F12`)
2. **Go to Inspector/Elements tab**
3. **Find a select field**
4. **Inspect the element** - look for these classes:
   ```html
   <select class="flex-1 px-4 py-3 text-lg border-2 border-blue-300 rounded-lg
                  focus:ring-3 focus:ring-blue-400 focus:border-blue-600
                  outline-none bg-white text-gray-800 font-medium
                  hover:border-blue-500 transition-all duration-150 shadow-sm">
   ```

5. **Check computed styles**:
   - Border should be 2px blue (#B3D9F2 or #60A5FA)
   - Text size should be 18px (text-lg)
   - Padding should be 12px horizontal, 12px vertical (px-4 py-3)

### Behavioral Tests

| Test | Expected Behavior | Override Indicator |
|------|------------------|-------------------|
| **Hover over select** | Blue border darkens | `hover:border-blue-500` applies |
| **Click to focus** | Blue ring appears around field | `focus:ring-3 focus:ring-blue-400` applies |
| **View placeholder** | Says "-- Escolha uma opção --" | Portuguese text from override |
| **Select option** | Selected value shows in blue badge in table | Badge styling in table mode |

## Testing the Tag Badge Override

### Visual Indicators
Look for these styling differences in tags:

1. **Larger Badges**: Tags should be `px-4 py-2` (larger than `px-2 py-1`)
2. **Icon Prefixes**: Each tag should display an icon before the text
   - "lead" → target icon (🎯)
   - "qualified" → check-circle icon (✓)
   - "proposal" → file-alt icon (📄)
   - "won" → trophy icon (🏆)
   - "lost" → times-circle icon (✗)
   - Others → tag icon (🏷️)
3. **Hover Effects**: Tags should scale up slightly and show more shadow
4. **Modern Styling**: Fully rounded corners (`rounded-full`)
5. **Drop Shadow**: `shadow-md` for depth

### Where to Test
Tags are used in the Kanban view (if available) and tags management:

#### Option 1: Kanban Board (if available)
- **URL**: `http://localhost:5000/kanban` (or similar)
- Tags appear on cards representing object state

#### Option 2: Tags Manager
- **URL**: Look for tags management interface
- Direct access to tag display

#### Option 3: Add Tags Manually
If Kanban is not yet implemented, tags may be added programmatically:

```python
# In Python console or API
from src.VibeCForms import add_tag
add_tag("contatos", 0, "lead", "test-user")
add_tag("contatos", 1, "qualified", "test-user")
add_tag("produtos", 0, "proposal", "test-user")
add_tag("produtos", 1, "won", "test-user")
```

### Manual Verification Steps

1. **Open browser DevTools** (`F12`)
2. **Go to Inspector/Elements tab**
3. **Find a tag badge element**
4. **Inspect the element** - look for these attributes:
   ```html
   <span class="inline-flex items-center gap-2 text-white px-4 py-2 rounded-full
                text-sm font-bold m-1 whitespace-nowrap transition-all duration-150
                hover:scale-110 hover:shadow-lg ... tag-color-0 shadow-md">
     <i class="fas fa-target text-xs"></i>
     lead
   </span>
   ```

5. **Check computed styles**:
   - Size should be larger: `padding: 8px 16px` (px-4 py-2)
   - Corners should be fully rounded: `border-radius: 9999px`
   - Should have shadow: `box-shadow: 0 1px 2px rgba(0,0,0,0.05)`

### Behavioral Tests

| Test | Expected Behavior | Override Indicator |
|------|------------------|-------------------|
| **Hover over tag** | Tag scales up larger | `hover:scale-110` applies |
| **Hover over tag** | Shadow becomes darker | `hover:shadow-lg` applies |
| **View tag with icon** | Icon appears before text | `<i class="fas fa-*">` renders |
| **Check icon type** | Icon matches tag name | Different icons for different tags |
| **View color** | Color is one of 10 palette colors | `tag-color-0` through `tag-color-9` |

## Automated Verification

### Check Override Detection
```python
from src.rendering.template_resolver import TemplateResolver

resolver = TemplateResolver(
    "examples/ponto-de-vendas",
    "src"
)

# List all active overrides
overrides = resolver.list_overrides()
print(f"Active overrides: {overrides}")
# Expected output:
# Active overrides: ['components/tag-badge.xslt', 'fields/select.xslt']
```

### Check Template Resolution
```python
# Verify select override is resolved correctly
select_path = resolver.resolve("fields/select.xslt")
print(f"Select template: {select_path}")
# Expected: .../examples/ponto-de-vendas/xslt/fields/select.xslt

# Verify tag-badge override is resolved correctly
tag_path = resolver.resolve("components/tag-badge.xslt")
print(f"Tag badge template: {tag_path}")
# Expected: .../examples/ponto-de-vendas/xslt/components/tag-badge.xslt

# Verify other templates still use defaults
input_path = resolver.resolve("fields/input.xslt")
print(f"Input template: {input_path}")
# Expected: .../src/xslt/fields/input.xslt (NOT from ponto-de-vendas)
```

## Troubleshooting

### Overrides Not Applied

**Symptom**: Select fields still look gray, tags are small

**Diagnostics**:
1. Check that files exist:
   ```bash
   ls -la examples/ponto-de-vendas/xslt/
   ls -la examples/ponto-de-vendas/xslt/fields/
   ls -la examples/ponto-de-vendas/xslt/components/
   ```

2. Check XSLT syntax:
   ```bash
   # Look for XML parsing errors in app logs
   uv run app examples/ponto-de-vendas 2>&1 | grep -i "xml\|parse\|error"
   ```

3. Verify resolver detects overrides:
   ```python
   python3 << 'EOF'
   from src.rendering.template_resolver import TemplateResolver
   r = TemplateResolver("examples/ponto-de-vendas", "src")
   print("Overrides:", r.list_overrides())
   EOF
   ```

### Styles Applied But Tailwind Not Working

**Symptom**: Blue color not showing, spacing wrong

**Solution**:
1. Verify Tailwind classes are standard (not custom)
2. Check that CSS is being compiled
3. Restart the application to rebuild CSS

### Specific Template Not Being Used

**Symptom**: Expect blue select fields but still gray

1. Verify file path matches template name exactly:
   - File: `examples/ponto-de-vendas/xslt/fields/select.xslt` ✓
   - Template name: `"fields/select.xslt"` ✓

2. Check that resolver uses business case path:
   ```python
   resolver = TemplateResolver("examples/ponto-de-vendas", "src")
   # business_case_xslt = "examples/ponto-de-vendas/xslt" ✓
   ```

## Expected File Structure

After setup, your directory should look like:

```
examples/ponto-de-vendas/
├── xslt/
│   ├── fields/
│   │   └── select.xslt              ← Override #1
│   ├── components/
│   │   └── tag-badge.xslt           ← Override #2
│   ├── tag-colors.css               ← Color definitions
│   ├── README.md                    ← Override documentation
│   └── OVERRIDE_TEST.md             ← This file
├── specs/
│   ├── contatos.json
│   ├── produtos.json
│   └── financeiro/
├── config/
│   ├── persistence.json
│   └── schema_history.json
├── templates/                       ← Optional HTML overrides
├── data/
└── backups/
```

## Success Criteria

✓ Application starts without errors
✓ Template resolver detects both overrides
✓ Select fields render with blue theme and larger fonts
✓ Tags display with icons and larger size
✓ Hover effects work (scaling, shadow changes)
✓ Both form and table modes work correctly

## Next Steps

1. **Customize Further**: Copy other templates from `src/xslt/` and modify as needed
2. **Add More Overrides**: Follow the same pattern for other components
3. **Test in Production**: Use `BUSINESS_CASE_PATH=examples/ponto-de-vendas uv run hatch run serve`
4. **Document Changes**: Update `xslt/README.md` with your customizations

## Additional Resources

- `/Users/ronie/code/python/VibeCForms/src/rendering/template_resolver.py` - Override resolution logic
- `/Users/ronie/code/python/VibeCForms/src/xslt/` - Default templates to override
- `/Users/ronie/code/python/VibeCForms/CLAUDE.md` - Framework documentation
