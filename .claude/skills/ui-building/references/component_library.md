# VibeCForms UI Component Library

Reusable XSLT component patterns with Tailwind CSS for VibeCForms.

## Core Components

### Form Component

**Complete CRUD Form:**
```xslt
<xsl:template match="map(*)[?spec]" mode="form">
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-3">
        <i class="fas {?spec?icon} text-2xl text-blue-600"></i>
        <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100">
          <xsl:value-of select="?spec?title"/>
        </h2>
      </div>
    </div>

    <!-- Form fields -->
    <form method="POST" class="space-y-4">
      <xsl:apply-templates select="?spec?fields?*" mode="field"/>

      <!-- Submit buttons -->
      <div class="flex gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
        <button type="submit" class="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold
                                     hover:bg-blue-600 active:scale-95 transition-all">
          Submit
        </button>
        <button type="button" class="px-6 py-3 bg-gray-200 dark:bg-gray-700 rounded-lg">
          Cancel
        </button>
      </div>
    </form>
  </div>
</xsl:template>
```

### Field Components

**Text Input:**
```xslt
<xsl:template match="map(*)[?type = 'text']" mode="field">
  <div class="flex items-center gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
      <xsl:value-of select="?label"/>
      <xsl:if test="?required">
        <span class="text-red-500 ml-1">*</span>
      </xsl:if>
    </label>
    <input type="text" name="{?name}" value="{?value}"
           class="flex-1 px-3 py-2 rounded-lg border border-gray-300
                  focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                  dark:bg-gray-700 dark:border-gray-600"/>
  </div>
</xsl:template>
```

**Select Dropdown:**
```xslt
<xsl:template match="map(*)[?type = 'select']" mode="field">
  <div class="flex items-center gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
      <xsl:value-of select="?label"/>
    </label>
    <select name="{?name}"
            class="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white
                   focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                   dark:bg-gray-700 dark:border-gray-600">
      <option value="">-- Select --</option>
      <xsl:apply-templates select="?options?*" mode="option"/>
    </select>
  </div>
</xsl:template>

<xsl:template match="map(*)" mode="option">
  <option value="{?value}">
    <xsl:if test="?selected">
      <xsl:attribute name="selected">selected</xsl:attribute>
    </xsl:if>
    <xsl:value-of select="?label"/>
  </option>
</xsl:template>
```

**Textarea:**
```xslt
<xsl:template match="map(*)[?type = 'textarea']" mode="field">
  <div class="flex gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300 pt-2">
      <xsl:value-of select="?label"/>
    </label>
    <textarea name="{?name}" rows="4"
              class="flex-1 px-3 py-2 rounded-lg border border-gray-300
                     focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                     resize-vertical dark:bg-gray-700 dark:border-gray-600">
      <xsl:value-of select="?value"/>
    </textarea>
  </div>
</xsl:template>
```

### Table Component

**Data Table with Actions:**
```xslt
<xsl:template match="array(*)" mode="table">
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
      <thead class="bg-gray-50 dark:bg-gray-800">
        <tr>
          <xsl:for-each select="?(1)?*[not(starts-with(local-name(), '_'))]">
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400
                       uppercase tracking-wider">
              <xsl:value-of select="local-name()"/>
            </th>
          </xsl:for-each>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400
                     uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
        <xsl:apply-templates select="?*" mode="table-row"/>
      </tbody>
    </table>
  </div>
</xsl:template>

<xsl:template match="map(*)" mode="table-row">
  <tr class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
    <xsl:for-each select="?*[not(starts-with(local-name(), '_'))]">
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
        <xsl:value-of select="."/>
      </td>
    </xsl:for-each>
    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
      <a href="/edit/{?_uuid}" class="text-blue-600 hover:text-blue-900 dark:text-blue-400">
        Edit
      </a>
      <a href="/delete/{?_uuid}" class="text-red-600 hover:text-red-900 dark:text-red-400">
        Delete
      </a>
    </td>
  </tr>
</xsl:template>
```

### Card Component (Index Page)

**Form Card for Landing Page:**
```xslt
<xsl:template match="map(*)[?title]" mode="card">
  <a href="/{?path}" class="block group">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6
                transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
      <!-- Icon -->
      <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg
                  flex items-center justify-center mb-4
                  group-hover:scale-110 transition-transform">
        <i class="fas {?icon} fa-2x text-blue-600 dark:text-blue-400"></i>
      </div>

      <!-- Title -->
      <h3 class="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2
                 group-hover:text-blue-600 transition-colors">
        <xsl:value-of select="?title"/>
      </h3>

      <!-- Description (optional) -->
      <xsl:if test="?description">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          <xsl:value-of select="?description"/>
        </p>
      </xsl:if>

      <!-- Record count badge -->
      <xsl:if test="?count">
        <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span class="text-xs text-gray-500 dark:text-gray-400">
            <xsl:value-of select="?count"/> records
          </span>
        </div>
      </xsl:if>
    </div>
  </a>
</xsl:template>
```

## Specialized Components

### UUID Display

**Read-only UUID Field:**
```xslt
<xsl:template match="map(*)[?type = 'uuid_display']" mode="field">
  <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800
              rounded-lg p-4 mb-4">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs text-gray-600 dark:text-gray-400 mb-1 font-medium">Record UUID</p>
        <code class="text-sm font-mono text-gray-800 dark:text-gray-200">
          <xsl:value-of select="?value"/>
        </code>
      </div>
      <button type="button" onclick="navigator.clipboard.writeText('{?value}')"
              class="px-3 py-1 bg-blue-500 text-white text-sm rounded
                     hover:bg-blue-600 transition-colors">
        <i class="fas fa-copy mr-1"></i> Copy
      </button>
    </div>
  </div>
</xsl:template>
```

### Tag System

**Tag Badges:**
```xslt
<xsl:template match="map(*)" mode="tag-badge">
  <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold
               transition-transform hover:scale-110 {
    if (?color = 'red') then 'bg-red-500 text-white'
    else if (?color = 'green') then 'bg-green-500 text-white'
    else if (?color = 'blue') then 'bg-blue-500 text-white'
    else if (?color = 'orange') then 'bg-orange-500 text-white'
    else if (?color = 'purple') then 'bg-purple-500 text-white'
    else 'bg-gray-500 text-white'
  }">
    <xsl:value-of select="?label"/>
    <xsl:if test="?removable">
      <button type="button" class="hover:bg-white/20 rounded-full p-0.5">
        <i class="fas fa-times text-xs"></i>
      </button>
    </xsl:if>
  </span>
</xsl:template>

**Tag Display in Form:**
```xslt
<div class="flex items-start gap-3 mb-4">
  <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300 pt-2">
    Tags
  </label>
  <div class="flex-1 flex flex-wrap gap-2">
    <xsl:apply-templates select="?tags?*" mode="tag-badge"/>
    <xsl:if test="count(?tags?*) = 0">
      <span class="text-sm text-gray-500 dark:text-gray-400 italic">No tags</span>
    </xsl:if>
  </div>
</div>
```

### Search with Autocomplete

**Search Input with Datalist:**
```xslt
<xsl:template match="map(*)[?type = 'search' and ?datasource]" mode="field">
  <div class="flex items-center gap-3 mb-4">
    <label class="min-w-[180px] text-sm font-medium text-gray-700 dark:text-gray-300">
      <xsl:value-of select="?label"/>
    </label>
    <div class="flex-1 relative">
      <input type="search" name="{?name}" list="{?datasource}-datalist"
             placeholder="Search {?datasource}..."
             class="w-full px-3 py-2 pl-10 rounded-lg border border-gray-300
                    focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                    dark:bg-gray-700 dark:border-gray-600"/>
      <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
      <datalist id="{?datasource}-datalist">
        <!-- Populated dynamically via API -->
      </datalist>
    </div>
  </div>
</xsl:template>
```

### Navigation Sidebar

**Sidebar Menu:**
```xslt
<xsl:template match="map(*)" mode="sidebar">
  <nav class="bg-gray-800 text-gray-100 w-64 h-full overflow-y-auto fixed left-0 top-0">
    <div class="p-4">
      <!-- Logo/Title -->
      <div class="mb-6 pb-4 border-b border-gray-700">
        <h2 class="text-2xl font-bold text-white">VibeCForms</h2>
      </div>

      <!-- Menu items -->
      <xsl:apply-templates select="?items?*" mode="menu-item"/>
    </div>
  </nav>
</xsl:template>

<xsl:template match="map(*)" mode="menu-item">
  <a href="{?path}"
     class="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300
            hover:bg-gray-700 hover:text-white transition-colors mb-1">
    <i class="fas {?icon} w-5"></i>
    <span><xsl:value-of select="?label"/></span>
    <xsl:if test="?badge">
      <span class="ml-auto px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
        <xsl:value-of select="?badge"/>
      </span>
    </xsl:if>
  </a>
</xsl:template>
```

### Kanban Components

**Kanban Column:**
```xslt
<xsl:template match="map(*)" mode="kanban-column">
  <div class="flex-shrink-0 w-80 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
    <!-- Column header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-800 dark:text-gray-100">
        <xsl:value-of select="?label"/>
      </h3>
      <span class="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded-full text-xs">
        <xsl:value-of select="count(?cards?*)"/>
      </span>
    </div>

    <!-- Cards container -->
    <div class="space-y-3">
      <xsl:apply-templates select="?cards?*" mode="kanban-card"/>
    </div>
  </div>
</xsl:template>

<xsl:template match="map(*)" mode="kanban-card">
  <div class="bg-white dark:bg-gray-900 rounded-lg p-4 shadow-md
              cursor-move hover:shadow-lg transition-shadow"
       draggable="true">
    <h4 class="font-medium text-gray-800 dark:text-gray-100 mb-2">
      <xsl:value-of select="?title"/>
    </h4>
    <xsl:if test="?description">
      <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
        <xsl:value-of select="?description"/>
      </p>
    </xsl:if>
    <div class="flex items-center gap-2 flex-wrap">
      <xsl:apply-templates select="?tags?*" mode="tag-badge"/>
    </div>
  </div>
</xsl:template>
```

## Layout Components

### Page Container

**Main Layout with Sidebar:**
```xslt
<div class="flex h-screen">
  <!-- Sidebar -->
  <aside class="fixed left-0 top-0 w-64 h-full">
    <xsl:apply-templates select="?menu" mode="sidebar"/>
  </aside>

  <!-- Main content -->
  <main class="ml-64 flex-1 p-6 bg-gray-50 dark:bg-gray-900 overflow-y-auto">
    <xsl:apply-templates select="?content"/>
  </main>
</div>
```

### Grid Layouts

**Responsive Card Grid:**
```xslt
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
  <xsl:apply-templates select="?items?*" mode="card"/>
</div>
```

**Two-Column Form:**
```xslt
<div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
  <xsl:apply-templates select="?fields?*[position() mod 2 = 1]" mode="field"/>
  <xsl:apply-templates select="?fields?*[position() mod 2 = 0]" mode="field"/>
</div>
```

## Best Practices

1. **Modes**: Use modes for different rendering contexts (`form`, `card`, `table`, `field`)
2. **Consistency**: Follow VibeCForms spacing/color conventions
3. **Accessibility**: Include proper labels, ARIA attributes, focus states
4. **Dark Mode**: Always include dark mode variants
5. **Responsive**: Design mobile-first, add larger breakpoints as needed
6. **Reusability**: Create template modes that can render same data differently
