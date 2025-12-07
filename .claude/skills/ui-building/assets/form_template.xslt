<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:map="http://www.w3.org/2005/xpath-functions/map"
                xmlns:array="http://www.w3.org/2005/xpath-functions/array"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                exclude-result-prefixes="map array xs">

  <xsl:output method="html"
              indent="yes"
              omit-xml-declaration="yes"
              encoding="UTF-8"/>

  <!-- Root template: Match VibeCForms data structure -->
  <xsl:template match="map(*)[?spec and ?records]">
    <html>
      <head>
        <title><xsl:value-of select="?spec?title"/></title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
        <style>
          * { box-sizing: border-box; }
          body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 20px; }
          .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
          h2 { text-align: center; margin-bottom: 25px; color: #2c3e50; }
          form { display: flex; flex-direction: column; gap: 15px; margin-bottom: 30px; }
          .form-row { display: flex; align-items: center; gap: 10px; }
          label { font-weight: bold; color: #2c3e50; min-width: 180px; }
          input, textarea, select { padding: 7px; border-radius: 5px; border: 1px solid #bbb; flex: 1; }
          textarea { min-height: 80px; resize: vertical; }
          button { background: #3498db; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; }
          button:hover { background: #2980b9; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; }
          th { background: #3498db; color: #fff; }
          .tag { display: inline-block; color: #fff; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin: 2px; }
          .tag-color-0 { background: #3498db; }
          .tag-color-1 { background: #27ae60; }
          .tag-color-2 { background: #e74c3c; }
          .tag-color-3 { background: #f39c12; }
          .tag-color-4 { background: #9b59b6; }
        </style>
      </head>
      <body>
        <div class="container">
          <h2><xsl:value-of select="?spec?title"/></h2>

          <!-- Render form -->
          <xsl:apply-templates select="?spec" mode="form"/>

          <!-- Render table -->
          <h3>Registered Records:</h3>
          <xsl:apply-templates select="." mode="table"/>
        </div>
      </body>
    </html>
  </xsl:template>

  <!-- Form rendering mode -->
  <xsl:template match="map(*)[?fields]" mode="form">
    <form method="post">
      <xsl:apply-templates select="?fields?*"/>
      <div class="form-actions">
        <button type="submit">
          <i class="fa fa-plus"></i> Register
        </button>
      </div>
    </form>
  </xsl:template>

  <!-- Field rendering: Text-like inputs -->
  <xsl:template match="map(*)[?type = ('text', 'email', 'tel', 'url', 'number', 'date', 'time')]">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="{?type}" name="{?name}" id="{?name}">
        <xsl:if test="?required = true()">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
        <xsl:if test="?value">
          <xsl:attribute name="value" select="?value"/>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Textarea -->
  <xsl:template match="map(*)[?type = 'textarea']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <textarea name="{?name}" id="{?name}">
        <xsl:if test="?required = true()">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
        <xsl:value-of select="?value"/>
      </textarea>
    </div>
  </xsl:template>

  <!-- Select dropdown -->
  <xsl:template match="map(*)[?type = 'select']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <select name="{?name}" id="{?name}">
        <xsl:if test="?required = true()">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
        <option value="">-- Select --</option>
        <xsl:apply-templates select="?options?*" mode="option"/>
      </select>
    </div>
  </xsl:template>

  <!-- Option element -->
  <xsl:template match="map(*)" mode="option">
    <option value="{?value}">
      <xsl:if test="?selected = true()">
        <xsl:attribute name="selected">selected</xsl:attribute>
      </xsl:if>
      <xsl:value-of select="?label"/>
    </option>
  </xsl:template>

  <!-- Checkbox -->
  <xsl:template match="map(*)[?type = 'checkbox']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="checkbox" name="{?name}" id="{?name}">
        <xsl:if test="?checked = true()">
          <xsl:attribute name="checked">checked</xsl:attribute>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Range slider -->
  <xsl:template match="map(*)[?type = 'range']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="range" name="{?name}" id="{?name}"
             min="{?min}" max="{?max}" step="{(?step, 1)[1]}"
             value="{(?value, ?min)[1]}"/>
      <span class="range-value"><xsl:value-of select="(?value, ?min)[1]"/></span>
    </div>
  </xsl:template>

  <!-- Hidden field -->
  <xsl:template match="map(*)[?type = 'hidden']">
    <input type="hidden" name="{?name}" value="{?value}"/>
  </xsl:template>

  <!-- Color picker -->
  <xsl:template match="map(*)[?type = 'color']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="color" name="{?name}" id="{?name}"
             value="{(?value, '#000000')[1]}"/>
    </div>
  </xsl:template>

  <!-- Table rendering -->
  <xsl:template match="map(*)[?spec and ?records]" mode="table">
    <xsl:choose>
      <xsl:when test="array:size(?records) gt 0">
        <table>
          <thead>
            <tr>
              <!-- Generate headers from spec fields (excluding hidden) -->
              <xsl:for-each select="?spec?fields?*[not(?hidden = true())]">
                <th><xsl:value-of select="?label"/></th>
              </xsl:for-each>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <xsl:apply-templates select="?records?*" mode="table-row">
              <xsl:with-param name="fields" select="?spec?fields"/>
            </xsl:apply-templates>
          </tbody>
        </table>
      </xsl:when>
      <xsl:otherwise>
        <p>No records found.</p>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Table row -->
  <xsl:template match="map(*)" mode="table-row">
    <xsl:param name="fields"/>

    <tr>
      <!-- Render each field value -->
      <xsl:for-each select="$fields?*[not(?hidden = true())]">
        <xsl:variable name="field-name" select="?name"/>
        <xsl:variable name="field-type" select="?type"/>
        <xsl:variable name="field-value" select="current()?($field-name)"/>

        <td>
          <xsl:choose>
            <!-- Password: mask value -->
            <xsl:when test="$field-type = 'password'">
              <xsl:text>********</xsl:text>
            </xsl:when>
            <!-- Default: show value -->
            <xsl:otherwise>
              <xsl:value-of select="$field-value"/>
            </xsl:otherwise>
          </xsl:choose>
        </td>
      </xsl:for-each>

      <!-- Actions column -->
      <td>
        <a href="/edit/{position()}">Edit</a> |
        <a href="/delete/{position()}">Delete</a>
      </td>
    </tr>
  </xsl:template>

  <!-- Fallback template for unknown field types -->
  <xsl:template match="map(*)[?type]" priority="-1">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="text" name="{?name}" id="{?name}"/>
      <xsl:comment>Unknown field type: <xsl:value-of select="?type"/></xsl:comment>
    </div>
  </xsl:template>

</xsl:stylesheet>
