# Tailwind Integration with XSLT

Comprehensive guide on integrating Tailwind CSS with XSLT 3.0 templates for VibeCForms.

## Overview

Tailwind utility classes work seamlessly with XSLT templates. Apply classes directly in XSLT elements using:
- Literal strings for static styling
- `<xsl:attribute>` for conditional styling
- Attribute Value Templates (AVT) for dynamic styling

## Applying Tailwind Classes

### Static Classes

```xslt
<input type="text" class="px-3 py-2 rounded-lg border border-gray-300" name="{?name}"/>
```

### Conditional Classes

Use `<xsl:attribute>` and `<xsl:choose>` for data-driven styling:

```xslt
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}">
    <xsl:attribute name="class">
      <xsl:text>flex-1 px-3 py-2 rounded-lg border transition-colors </xsl:text>
      <xsl:choose>
        <xsl:when test="?required">
          <xsl:text>border-red-500 focus:border-red-600 focus:ring-red-200</xsl:text>
        </xsl:when>
        <xsl:when test="?disabled">
          <xsl:text>border-gray-200 bg-gray-100 cursor-not-allowed opacity-50</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>border-gray-300 focus:border-blue-500 focus:ring-blue-200</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
  </input>
</xsl:template>
```

### Dynamic Classes with AVT

Use XPath expressions within attribute values:

```xslt
<!-- Dynamic color based on status -->
<span class="px-3 py-1 rounded-full text-white {
  if (?status = 'active') then 'bg-green-500'
  else if (?status = 'pending') then 'bg-orange-500'
  else if (?status = 'error') then 'bg-red-500'
  else 'bg-gray-500'
}">
  <xsl:value-of select="?label"/>
</span>

<!-- Dynamic sizing -->
<div class="{if (count(?items?*) > 10) then 'h-96 overflow-y-auto' else 'h-auto'}">

<!-- Conditional display -->
<div class="{if (?visible) then 'block' else 'hidden'}">
```

## Common VibeCForms Patterns

### Form Layouts

**Form Container:**
```xslt
<form class="space-y-4 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
```

**Form Row (Label + Input):**
```xslt
<div class="flex items-center gap-3 mb-4">
  <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
  <div class="flex-1">
```

**Form Sections:**
```xslt
<div class="space-y-6 divide-y divide-gray-200 dark:divide-gray-700">
  <section class="pt-6 first:pt-0">
```

### Responsive Layouts

**Responsive Grid:**
```xslt
<!-- Card grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

<!-- Two-column form -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
```

**Sidebar Layout:**
```xslt
<div class="flex h-screen">
  <!-- Fixed sidebar -->
  <aside class="fixed left-0 top-0 w-64 h-full bg-gray-800 overflow-y-auto">

  <!-- Main content with offset -->
  <main class="ml-64 flex-1 p-6 bg-gray-50 dark:bg-gray-900">
</div>
```

**Responsive Visibility:**
```xslt
<!-- Mobile menu -->
<div class="block md:hidden">

<!-- Desktop sidebar -->
<div class="hidden md:flex">
```

### Interactive States

**Hover Effects:**
```xslt
class="hover:bg-gray-100 hover:shadow-lg hover:scale-105 transition-all duration-200"
```

**Focus States:**
```xslt
class="focus:outline-none focus:ring-4 focus:ring-blue-200 focus:border-blue-500"
```

**Active/Pressed States:**
```xslt
class="active:scale-95 active:bg-blue-700"
```

**Disabled States:**
```xslt
class="disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100"
```

**Group Hover (Parent-Child):**
```xslt
<a href="#" class="group">
  <div class="group-hover:shadow-xl">
  <span class="group-hover:text-blue-600">
</a>
```

### Dark Mode

Apply dark mode variants:

```xslt
<!-- Background -->
class="bg-white dark:bg-gray-800"

<!-- Text -->
class="text-gray-900 dark:text-gray-100"

<!-- Borders -->
class="border-gray-200 dark:border-gray-700"

<!-- Inputs -->
class="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
```

### Tables

**Responsive Table Wrapper:**
```xslt
<div class="overflow-x-auto">
  <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
    <thead class="bg-gray-50 dark:bg-gray-800">
      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
    <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200">
      <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
```

### Buttons

**Primary Button:**
```xslt
class="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold
       hover:bg-blue-600 active:scale-95 transition-all duration-200
       focus:outline-none focus:ring-4 focus:ring-blue-200"
```

**Secondary Button:**
```xslt
class="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200
       rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600"
```

**Danger Button:**
```xslt
class="px-6 py-3 bg-red-500 text-white rounded-lg font-semibold
       hover:bg-red-600 focus:ring-4 focus:ring-red-200"
```

### Cards

**Basic Card:**
```xslt
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6
            transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
```

**Card with Header:**
```xslt
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
  <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
    <h3 class="text-lg font-semibold">
  </div>
  <div class="p-6">
</div>
```

## VibeCForms Color Mapping

| VibeCForms      | Hex       | Tailwind      |
|-----------------|-----------|---------------|
| Primary         | `#3498db` | `blue-500`    |
| Dark BG         | `#2c3e50` | `gray-800`    |
| Success         | `#27ae60` | `green-500`   |
| Danger          | `#e74c3c` | `red-500`     |
| Warning         | `#f39c12` | `orange-500`  |
| Info            | `#9b59b6` | `purple-500`  |
| Light BG        | `#f7f7f7` | `gray-100`    |

## Typography

```xslt
<!-- Page title -->
<h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">

<!-- Section header -->
<h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100">

<!-- Card title -->
<h3 class="text-xl font-semibold text-gray-800 dark:text-gray-100">

<!-- Labels -->
<label class="text-sm font-medium text-gray-700 dark:text-gray-300">

<!-- Body text -->
<p class="text-base text-gray-600 dark:text-gray-400">

<!-- Small text -->
<span class="text-xs text-gray-500 dark:text-gray-500">
```

## Spacing

```xslt
<!-- Form spacing -->
<div class="space-y-4">        <!-- 1rem vertical spacing -->
<div class="gap-3">             <!-- 0.75rem gap in flex/grid -->

<!-- Card grid spacing -->
<div class="gap-6">             <!-- 1.5rem gap between cards -->

<!-- Padding -->
<div class="p-6">               <!-- 1.5rem padding all sides -->
<div class="px-6 py-4">         <!-- 1.5rem horizontal, 1rem vertical -->
```

## Best Practices

1. **Consistent Spacing**: Use `gap-3` for form rows, `gap-6` for card grids
2. **Dark Mode**: Always include dark mode variants for backgrounds, text, and borders
3. **Transitions**: Add `transition-*` classes for smooth state changes
4. **Focus States**: Always include focus rings for accessibility
5. **Responsive**: Use `sm:`, `md:`, `lg:` breakpoints for responsive layouts
6. **Hover Effects**: Use `hover:scale-*` sparingly for visual feedback
