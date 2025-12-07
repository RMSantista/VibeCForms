# Ponto-de-Vendas Customizations Summary

## Overview

The ponto-de-vendas business case includes two XSLT template overrides that customize the visual appearance of form fields and tags for a Point of Sale system. These overrides demonstrate how to leverage the business case override mechanism to achieve professional-looking, brand-specific styling without forking the framework.

## Overview of Changes

| Component | File | Customizations | Impact |
|-----------|------|---|--------|
| **Select Field** | `fields/select.xslt` | Blue theme, larger fonts, wider labels | All dropdown fields throughout app |
| **Tag Badge** | `components/tag-badge.xslt` | Icons, larger size, hover effects, color scheme | State tracking in Kanban and tags views |

---

## 1. Select Field Override

### File
`examples/ponto-de-vendas/xslt/fields/select.xslt`

### What It Changes

#### Before (Default)
```xslt
<label class="w-48 font-semibold text-gray-700">
<select class="... border border-gray-300 ... focus:ring-2 focus:ring-blue-500 ...">
```

#### After (Override)
```xslt
<label class="w-64 font-bold text-blue-800 text-lg pt-2">
<select class="... border-2 border-blue-300 ... focus:ring-3 focus:ring-blue-400 focus:border-blue-600 ... text-lg ...">
```

### Visual Differences

| Aspect | Default | Override | Notes |
|--------|---------|----------|-------|
| **Label Width** | 192px (w-48) | 256px (w-64) | More room for labels |
| **Label Color** | Gray-700 | Blue-800 | Branded color |
| **Label Weight** | Semibold (600) | Bold (700) | More prominent |
| **Label Size** | Default | Large (18px) | Matches field size |
| **Field Font** | Default | Large (text-lg) | 18px instead of 16px |
| **Border Style** | 1px gray | 2px blue | Stronger, branded appearance |
| **Border Color** | Gray-300 | Blue-300 | Soft blue when unfocused |
| **Focus Ring** | 2px | 3px | More prominent focus state |
| **Focus Ring Color** | Blue-500 | Blue-400 | Slightly different shade |
| **Focus Border** | Default | Blue-600 | Darker blue when focused |
| **Hover Effect** | None | Border darkens | Better interactivity feedback |
| **Placeholder** | "-- Selecione --" | "-- Escolha uma opção --" | Portuguese text |
| **Table Display** | Plain text | Blue badge | Visual distinction |

### Code Differences

**Size and Spacing**:
```diff
- <div class="mb-4 flex items-center gap-2">
+ <div class="mb-6 flex items-start gap-3">

- <label class="w-48 font-semibold text-gray-700">
+ <label class="w-64 font-bold text-blue-800 text-lg pt-2 flex-shrink-0">
```

**Field Styling**:
```diff
- <select class="flex-1 px-3 py-2 border border-gray-300 rounded-md
-         focus:ring-2 focus:ring-blue-500 focus:border-blue-500
-         outline-none bg-white">
+ <select class="flex-1 px-4 py-3 text-lg border-2 border-blue-300 rounded-lg
+         focus:ring-3 focus:ring-blue-400 focus:border-blue-600
+         outline-none bg-white text-gray-800 font-medium
+         hover:border-blue-500 transition-all duration-150 shadow-sm">
```

**Placeholder**:
```diff
- <option value="">-- Selecione --</option>
+ <option value="">-- Escolha uma opção --</option>
```

**Table Mode Display**:
```diff
  <xsl:otherwise>
-   <xsl:value-of select="$field-value"/>
+   <span class="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
+     <xsl:value-of select="options/option[@value = $field-value]/@label"/>
+   </span>
```

### Form Rendering Example

**HTML Output (Override)**:
```html
<div class="mb-6 flex items-start gap-3">
  <label for="categoria" class="w-64 font-bold text-blue-800 text-lg pt-2 flex-shrink-0">
    Categoria:
    <span class="text-red-600 ml-1">*</span>
  </label>
  <select
    name="categoria"
    id="categoria"
    required="required"
    class="flex-1 px-4 py-3 text-lg border-2 border-blue-300 rounded-lg
           focus:ring-3 focus:ring-blue-400 focus:border-blue-600 outline-none
           bg-white text-gray-800 font-medium hover:border-blue-500
           transition-all duration-150 shadow-sm">
    <option value="">-- Escolha uma opção --</option>
    <option value="electronics">Eletrônicos</option>
    <option value="clothing">Vestuário</option>
    <option value="food">Alimentos</option>
  </select>
</div>
```

### Use Cases

- E-commerce product filters
- Point of sale product categories
- Customer type selection
- Payment method selection
- Order status management

---

## 2. Tag Badge Override

### File
`examples/ponto-de-vendas/xslt/components/tag-badge.xslt`

### What It Changes

#### Before (Default)
```xslt
<span class="inline-block text-white px-2 py-1 rounded-xl text-xs m-0.5 whitespace-nowrap
       transition-transform hover:translate-y-[-1px] hover:shadow {$color-class}">
  <xsl:value-of select="$tag"/>
</span>
```

#### After (Override)
```xslt
<span class="inline-flex items-center gap-2 text-white px-4 py-2 rounded-full text-sm font-bold
       m-1 whitespace-nowrap transition-all duration-150 hover:scale-110 hover:shadow-lg cursor-pointer
       select-none {$color-class} shadow-md">
  <i class="fas {$tag-icon} text-xs"></i>
  <xsl:value-of select="$tag"/>
</span>
```

### Visual Differences

| Aspect | Default | Override | Notes |
|--------|---------|----------|-------|
| **Badge Size** | Compact (px-2 py-1) | Larger (px-4 py-2) | 2x the padding |
| **Text Size** | xs (12px) | sm (14px) | More readable |
| **Corner Radius** | rounded-xl | rounded-full | Fully rounded |
| **Font Weight** | Regular | Bold (700) | More prominent |
| **Icon** | None | Font Awesome icon | State visualization |
| **Hover Effect** | Slight upward move | 10% scale increase | Better feedback |
| **Hover Shadow** | Default | Larger shadow | More dramatic effect |
| **Border Spacing** | 0.125rem (m-0.5) | 0.25rem (m-1) | Better separation |
| **Display Mode** | inline-block | inline-flex | Icon + text alignment |
| **Cursor** | default | pointer | Suggests interactivity |
| **Color Consistency** | Hash-based (0-10) | Hash-based (0-10) | Same system, enhanced |

### Code Differences

**Structure and Display**:
```diff
- <span class="inline-block text-white px-2 py-1 rounded-xl text-xs
-       m-0.5 whitespace-nowrap transition-transform
-       hover:translate-y-[-1px] hover:shadow {$color-class}">
-   <xsl:value-of select="$tag"/>
+ <span class="inline-flex items-center gap-2 text-white px-4 py-2 rounded-full
+       text-sm font-bold m-1 whitespace-nowrap transition-all duration-150
+       hover:scale-110 hover:shadow-lg cursor-pointer select-none
+       {$color-class} shadow-md">
+   <i class="fas {$tag-icon} text-xs"></i>
+   <xsl:value-of select="$tag"/>
</span>
```

**Icon Mapping**:
```xslt
<xsl:template name="tag-icon">
  <xsl:param name="tag" as="xs:string"/>
  <xsl:choose>
    <xsl:when test="contains(lower-case($tag), 'lead')">fa-target</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'qualified')">fa-check-circle</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'proposal')">fa-file-alt</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'negotiation')">fa-handshake</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'won') or contains(lower-case($tag), 'closed')">fa-trophy</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'lost')">fa-times-circle</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'pending')">fa-hourglass-half</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'active')">fa-star</xsl:when>
    <xsl:when test="contains(lower-case($tag), 'inactive')">fa-pause-circle</xsl:when>
    <xsl:otherwise>fa-tag</xsl:otherwise>
  </xsl:choose>
</xsl:template>
```

### Icon Reference

| Tag Name | Icon | Font Awesome Class | Meaning |
|----------|------|-------------------|---------|
| Contains "lead" | 🎯 | fa-target | New prospect |
| Contains "qualified" | ✓ | fa-check-circle | Approved, ready |
| Contains "proposal" | 📄 | fa-file-alt | Quote sent |
| Contains "negotiation" | 🤝 | fa-handshake | In discussion |
| Contains "won"/"closed" | 🏆 | fa-trophy | Completed success |
| Contains "lost" | ✗ | fa-times-circle | Failed/rejected |
| Contains "pending" | ⏳ | fa-hourglass-half | Awaiting action |
| Contains "active" | ⭐ | fa-star | Current/ongoing |
| Contains "inactive" | ⏸ | fa-pause-circle | Suspended/paused |
| Default | 🏷 | fa-tag | Generic state |

### Tag Display Example

**HTML Output (Override)**:
```html
<!-- Lead tag -->
<span class="inline-flex items-center gap-2 text-white px-4 py-2 rounded-full text-sm font-bold
       m-1 whitespace-nowrap transition-all duration-150 hover:scale-110 hover:shadow-lg
       cursor-pointer select-none tag-color-3 shadow-md">
  <i class="fas fa-target text-xs"></i>
  lead
</span>

<!-- Won tag -->
<span class="inline-flex items-center gap-2 text-white px-4 py-2 rounded-full text-sm font-bold
       m-1 whitespace-nowrap transition-all duration-150 hover:scale-110 hover:shadow-lg
       cursor-pointer select-none tag-color-1 shadow-md">
  <i class="fas fa-trophy text-xs"></i>
  won
</span>
```

### Color Palette

10 consistent colors assigned by hash function (hash % 10):

```css
tag-color-0 → Cyan-600    (#06B6D4) - Active/Current
tag-color-1 → Emerald-600 (#059669) - Success/Won
tag-color-2 → Blue-600    (#2563EB) - Primary/Qualified
tag-color-3 → Violet-600  (#7C3AED) - Special/High Priority
tag-color-4 → Rose-600    (#DB2777) - Critical/Urgent
tag-color-5 → Orange-600  (#EA580C) - Warning/Pending
tag-color-6 → Green-600   (#16A34A) - Approved/Active
tag-color-7 → Blue-800    (#1E40AF) - Important
tag-color-8 → Purple-600  (#A855F7) - Processing
tag-color-9 → Red-600     (#DC2626) - Closed/Lost
```

### Sales Pipeline Example

In a sales workflow with these tags:
- "lead" → Target icon, violet badge
- "qualified" → Check-circle icon, blue badge
- "proposal" → File icon, green badge
- "negotiation" → Handshake icon, orange badge
- "won" → Trophy icon, emerald badge
- "lost" → X-circle icon, red badge

### Use Cases

- Sales pipeline state visualization
- Order status tracking
- Customer segmentation
- Document workflow states
- Process completion tracking

---

## Comparison Table: Before and After

### Select Field Comparison

| Feature | Default | Ponto-de-Vendas |
|---------|---------|-----------------|
| **Visual** | Subtle gray styling | Branded blue styling |
| **Font Size** | 16px | 18px |
| **Label Alignment** | Center | Top-start |
| **Border** | 1px gray | 2px blue |
| **Focus State** | Subtle ring | Prominent ring + border |
| **Hover Feedback** | None | Border color change |
| **Table Display** | Plain text | Color badge |
| **Language** | English | Portuguese |

### Tag Badge Comparison

| Feature | Default | Ponto-de-Vendas |
|---------|---------|-----------------|
| **Size** | Compact | Large |
| **Icon** | None | State-specific |
| **Shape** | Rounded corners | Fully rounded |
| **Hover Effect** | Shift up | Scale up |
| **Prominence** | Subtle | Bold |
| **Visual Weight** | Light | Heavy |
| **Interactivity** | Not clickable | Cursor pointer |

---

## Implementation Details

### Template Resolution

When the application renders a form or tag:

1. **Request**: "Render select field"
2. **Resolver**: "Where is fields/select.xslt?"
3. **Check**: "Is it in examples/ponto-de-vendas/xslt/fields/?"
4. **Found**: Yes! Use the override
5. **Result**: Blue-themed select field

### No Fallback Needed

These overrides completely replace the default templates, so there's no special fallback logic. All select fields and tags rendered in ponto-de-vendas will use these customized versions.

### CSS Dependencies

Both overrides use Tailwind CSS utility classes. No custom CSS is required (other than `tag-colors.css` which defines the 10 color classes).

Tailwind classes used:
- **Layout**: `flex`, `inline-flex`, `items-center`, `gap-2`, `flex-1`, `flex-shrink-0`
- **Spacing**: `px-4`, `py-3`, `mb-6`, `m-1`, `pt-2`
- **Typography**: `text-lg`, `text-sm`, `font-bold`, `font-medium`
- **Colors**: `text-blue-800`, `bg-blue-100`, `border-blue-300`
- **Borders**: `border-2`, `rounded-lg`, `rounded-full`
- **Effects**: `shadow-md`, `hover:scale-110`, `hover:shadow-lg`, `transition-all`
- **States**: `focus:ring-3`, `focus:border-blue-600`, `hover:border-blue-500`

---

## Testing Customizations

### Select Field Testing

1. **Visual Check**: Open a form with select fields
2. **Verify Blue Theme**: Border should be blue, not gray
3. **Check Fonts**: Text should be noticeably larger
4. **Test Focus**: Click field, ring should be prominent blue
5. **Test Hover**: Hover over field, border should darken
6. **Test Table**: Selected values in tables should appear as badges

### Tag Badge Testing

1. **Find Tags**: Navigate to Kanban or tags manager
2. **Visual Check**: Tags should be larger and have icons
3. **Verify Icons**: Each tag type should have the right icon
4. **Test Hover**: Hover over tag, should scale up and gain shadow
5. **Check Colors**: Tags should have distinct colors

---

## Maintenance and Updates

### Updating the Overrides

If VibeCForms core templates change:

1. Check `src/xslt/fields/select.xslt` for updates
2. Update `examples/ponto-de-vendas/xslt/fields/select.xslt` accordingly
3. Preserve the blue theme customizations
4. Test thoroughly

### Adding More Overrides

To add additional customizations:

1. Copy template from `src/xslt/` to `examples/ponto-de-vendas/xslt/`
2. Modify as needed
3. Add documentation to `xslt/README.md`
4. Test in the application

### Version Compatibility

These overrides are compatible with:
- VibeCForms v4.0+
- XSLT 3.0 processors
- Tailwind CSS v3+
- Font Awesome 6+

---

## Related Documentation

- `xslt/README.md` - Override mechanism documentation
- `OVERRIDE_TEST.md` - Testing guide
- `/src/rendering/template_resolver.py` - Resolution logic
- `/CLAUDE.md` - Framework overview
