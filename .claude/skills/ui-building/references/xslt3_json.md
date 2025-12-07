# Working with JSON in XSLT 3.0

XSLT 3.0 introduces native support for JSON transformations using XPath 3.1 map and array syntax. This reference covers the essential concepts and patterns for working with JSON in XSLT.

## JSON Data Model in XSLT 3.0

XSLT 3.0 represents JSON using two native data types:

- **Maps** (`map(*)`) - Represent JSON objects
- **Arrays** (`array(*)`) - Represent JSON arrays

### Basic JSON Mapping

```json
{
  "name": "John",
  "age": 30,
  "tags": ["customer", "vip"]
}
```

In XSLT 3.0, this becomes:
- Object: `map(*)`
- Properties: Accessed via `?propertyName`
- Array: `array(*)`
- Array items: Accessed via `?*` or `?(index)`

## XPath 3.1 Syntax for JSON

### Accessing Object Properties

```xslt
<!-- Access 'name' property -->
<xsl:value-of select="?name"/>

<!-- Access nested properties -->
<xsl:value-of select="?address?city"/>

<!-- Access with dynamic key -->
<xsl:value-of select="?(dynamic-key)"/>
```

### Working with Arrays

```xslt
<!-- Iterate over array items -->
<xsl:apply-templates select="?tags?*"/>

<!-- Access specific index (1-based) -->
<xsl:value-of select="?tags?(1)"/>

<!-- Get array size -->
<xsl:value-of select="array:size(?tags)"/>

<!-- Check if empty -->
<xsl:if test="array:size(?tags) gt 0">
  <!-- Has items -->
</xsl:if>
```

### Attribute Value Templates

Use curly braces `{}` to insert values into attributes:

```xslt
<input type="text" name="{?name}" value="{?value}"/>
```

## Pattern Matching JSON Structures

### Matching Objects with Specific Keys

```xslt
<!-- Match any map with a 'fields' key -->
<xsl:template match="map(*)[?fields]">
  <xsl:apply-templates select="?fields?*"/>
</xsl:template>

<!-- Match maps with specific key-value pairs -->
<xsl:template match="map(*)[?type = 'text']">
  <input type="text" name="{?name}"/>
</xsl:template>
```

### Matching Arrays

```xslt
<!-- Match any array -->
<xsl:template match="array(*)">
  <xsl:apply-templates select="?*"/>
</xsl:template>

<!-- Match arrays in specific context -->
<xsl:template match="array(*)" mode="table">
  <table>
    <xsl:apply-templates select="?*"/>
  </table>
</xsl:template>
```

### Complex Pattern Matching

```xslt
<!-- Match objects with multiple required keys -->
<xsl:template match="map(*)[?name and ?type and ?required]">
  <!-- All three keys must exist -->
</xsl:template>

<!-- Match based on value comparison -->
<xsl:template match="map(*)[?required = true()]">
  <!-- required is explicitly true -->
</xsl:template>

<!-- Negative matching -->
<xsl:template match="map(*)[not(?hidden)]">
  <!-- Only if 'hidden' key doesn't exist -->
</xsl:template>
```

## Creating JSON Output

### Creating Maps

```xslt
<xsl:variable name="person" select="map{
  'name': 'John',
  'age': 30,
  'active': true()
}"/>
```

### Creating Arrays

```xslt
<xsl:variable name="colors" select="array{
  'red', 'green', 'blue'
}"/>
```

### Dynamic Construction

```xslt
<!-- Build map from data -->
<xsl:variable name="result" select="map:merge(
  for $field in ?fields?*
  return map{$field?name: $field?value}
)"/>

<!-- Build array from data -->
<xsl:variable name="names" select="array{
  ?records?*?name
}"/>
```

## Common JSON Operations

### Checking if Key Exists

```xslt
<xsl:if test="map:contains(., 'optional_field')">
  <!-- Key exists -->
</xsl:if>

<!-- Or simpler: -->
<xsl:if test="?optional_field">
  <!-- Key exists and is truthy -->
</xsl:if>
```

### Getting Keys

```xslt
<!-- Get all keys in a map -->
<xsl:for-each select="map:keys(.)">
  <xsl:value-of select="."/>
</xsl:for-each>
```

### Merging Maps

```xslt
<xsl:variable name="merged" select="map:merge(($map1, $map2))"/>
```

### Filtering Arrays

```xslt
<!-- Filter array items -->
<xsl:variable name="active-users" select="
  array{?users?*[?active = true()]}
"/>
```

## VibeCForms-Specific Patterns

### Accessing Form Spec

```xslt
<!-- Root data structure -->
<xsl:template match="map(*)[?spec and ?records]">
  <html>
    <head>
      <title><xsl:value-of select="?spec?title"/></title>
    </head>
    <body>
      <!-- Render form from spec -->
      <xsl:apply-templates select="?spec" mode="form"/>

      <!-- Render table from records -->
      <xsl:apply-templates select="?records" mode="table"/>
    </body>
  </html>
</xsl:template>
```

### Processing Field Arrays

```xslt
<!-- Iterate over fields -->
<xsl:template match="map(*)[?fields]" mode="form">
  <form>
    <xsl:apply-templates select="?fields?*"/>
  </form>
</xsl:template>

<!-- Match individual field -->
<xsl:template match="map(*)[?type and ?name]">
  <div class="form-row">
    <label><xsl:value-of select="?label"/>:</label>
    <!-- Field-specific rendering based on ?type -->
    <xsl:apply-templates select="." mode="{?type}"/>
  </div>
</xsl:template>
```

### Handling Options Arrays

```xslt
<!-- Select field with options -->
<xsl:template match="map(*)[?type = 'select']">
  <select name="{?name}">
    <option value="">-- Select --</option>
    <xsl:apply-templates select="?options?*"/>
  </select>
</xsl:template>

<!-- Option item -->
<xsl:template match="map(*)[?value and ?label]">
  <option value="{?value}">
    <xsl:value-of select="?label"/>
  </option>
</xsl:template>
```

## Type Conversion

### JSON to String

```xslt
<!-- Boolean to string -->
<xsl:value-of select="string(?active)"/>  <!-- 'true' or 'false' -->

<!-- Number to string -->
<xsl:value-of select="string(?age)"/>

<!-- Null handling -->
<xsl:value-of select="(?value, 'default')[1]"/>
```

### Testing Types

```xslt
<!-- Check if value is a map -->
<xsl:if test="?field instance of map(*)">
  <!-- It's an object -->
</xsl:if>

<!-- Check if value is an array -->
<xsl:if test="?items instance of array(*)">
  <!-- It's an array -->
</xsl:if>

<!-- Check if value is boolean -->
<xsl:if test="?active instance of xs:boolean">
  <!-- It's a boolean -->
</xsl:if>
```

## Error Handling

### Safe Property Access

```xslt
<!-- Use default value if property doesn't exist -->
<xsl:value-of select="(?optional_field, 'default')[1]"/>

<!-- Check before accessing nested properties -->
<xsl:choose>
  <xsl:when test="?address?city">
    <xsl:value-of select="?address?city"/>
  </xsl:when>
  <xsl:otherwise>
    <xsl:text>No city</xsl:text>
  </xsl:otherwise>
</xsl:choose>
```

### Validating Structure

```xslt
<!-- Ensure required fields exist -->
<xsl:template match="map(*)[?name and ?type]">
  <!-- Safe to access ?name and ?type -->
</xsl:template>

<!-- Fallback for malformed data -->
<xsl:template match="map(*)" priority="-1">
  <xsl:message>Warning: Unexpected map structure</xsl:message>
  <!-- Fallback rendering -->
</xsl:template>
```

## Performance Tips

1. **Use pattern matching instead of xsl:choose** - Let the engine optimize
2. **Cache frequently accessed values** - Use `xsl:variable`
3. **Avoid deep nesting** - Flatten access patterns where possible
4. **Use modes for different contexts** - Enables template reuse

## Examples

### Complete Form Field Rendering

```xslt
<!-- Main template -->
<xsl:template match="map(*)[?spec]">
  <html>
    <head>
      <title><xsl:value-of select="?spec?title"/></title>
    </head>
    <body>
      <h2><xsl:value-of select="?spec?title"/></h2>
      <form>
        <xsl:apply-templates select="?spec?fields?*"/>
      </form>
    </body>
  </html>
</xsl:template>

<!-- Text input -->
<xsl:template match="map(*)[?type = 'text']">
  <div class="form-row">
    <label for="{?name}"><xsl:value-of select="?label"/>:</label>
    <input type="text" id="{?name}" name="{?name}">
      <xsl:if test="?required = true()">
        <xsl:attribute name="required">required</xsl:attribute>
      </xsl:if>
    </input>
  </div>
</xsl:template>

<!-- Select with options -->
<xsl:template match="map(*)[?type = 'select']">
  <div class="form-row">
    <label for="{?name}"><xsl:value-of select="?label"/>:</label>
    <select id="{?name}" name="{?name}">
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

### Table Rendering with Dynamic Columns

```xslt
<xsl:template match="array(*)" mode="table">
  <table>
    <thead>
      <tr>
        <!-- Generate headers from first record's keys -->
        <xsl:for-each select="?(1)?*">
          <th><xsl:value-of select="local-name()"/></th>
        </xsl:for-each>
      </tr>
    </thead>
    <tbody>
      <xsl:for-each select="?*">
        <tr>
          <xsl:for-each select="?*">
            <td><xsl:value-of select="."/></td>
          </xsl:for-each>
        </tr>
      </xsl:for-each>
    </tbody>
  </table>
</xsl:template>
```
