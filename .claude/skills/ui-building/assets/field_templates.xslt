<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:map="http://www.w3.org/2005/xpath-functions/map"
                xmlns:array="http://www.w3.org/2005/xpath-functions/array"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                exclude-result-prefixes="map array xs">

  <!--
    Reusable XSLT templates for VibeCForms field types.
    Import this into your main templates with:
    <xsl:import href="field_templates.xslt"/>
  -->

  <xsl:output method="html" indent="yes" omit-xml-declaration="yes"/>

  <!-- ========================================
       TEXT-LIKE INPUT FIELDS
       ======================================== -->

  <!-- Text input -->
  <xsl:template match="map(*)[?type = 'text']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="text" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Email input -->
  <xsl:template match="map(*)[?type = 'email']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="email" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Telephone input -->
  <xsl:template match="map(*)[?type = 'tel']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="tel" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- URL input -->
  <xsl:template match="map(*)[?type = 'url']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="url" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Number input -->
  <xsl:template match="map(*)[?type = 'number']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="number" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
        <xsl:if test="?min">
          <xsl:attribute name="min" select="?min"/>
        </xsl:if>
        <xsl:if test="?max">
          <xsl:attribute name="max" select="?max"/>
        </xsl:if>
        <xsl:if test="?step">
          <xsl:attribute name="step" select="?step"/>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Password input -->
  <xsl:template match="map(*)[?type = 'password']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="password" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Search input -->
  <xsl:template match="map(*)[?type = 'search']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="search" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
        <xsl:if test="?datasource">
          <xsl:attribute name="list" select="concat(?datasource, '-datalist')"/>
          <xsl:attribute name="placeholder" select="concat('Search ', ?datasource, '...')"/>
        </xsl:if>
      </input>
      <xsl:if test="?datasource">
        <datalist id="{?datasource}-datalist">
          <!-- Populated dynamically via JavaScript/API -->
        </datalist>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- ========================================
       DATE AND TIME FIELDS
       ======================================== -->

  <!-- Date input -->
  <xsl:template match="map(*)[?type = 'date']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="date" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Time input -->
  <xsl:template match="map(*)[?type = 'time']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="time" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Datetime-local input -->
  <xsl:template match="map(*)[?type = 'datetime-local']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="datetime-local" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Month input -->
  <xsl:template match="map(*)[?type = 'month']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="month" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- Week input -->
  <xsl:template match="map(*)[?type = 'week']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="week" name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:call-template name="add-value-attribute"/>
      </input>
    </div>
  </xsl:template>

  <!-- ========================================
       SELECTION FIELDS
       ======================================== -->

  <!-- Select dropdown -->
  <xsl:template match="map(*)[?type = 'select']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <select name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <option value="">-- Selecione --</option>
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

  <!-- Radio button group -->
  <xsl:template match="map(*)[?type = 'radio']">
    <div class="form-row">
      <label><xsl:value-of select="?label"/>:</label>
      <div class="radio-group">
        <xsl:apply-templates select="?options?*" mode="radio-option">
          <xsl:with-param name="field-name" select="?name"/>
        </xsl:apply-templates>
      </div>
    </div>
  </xsl:template>

  <!-- Radio option -->
  <xsl:template match="map(*)" mode="radio-option">
    <xsl:param name="field-name"/>
    <label class="radio-label">
      <input type="radio" name="{$field-name}" value="{?value}">
        <xsl:if test="?selected = true()">
          <xsl:attribute name="checked">checked</xsl:attribute>
        </xsl:if>
      </input>
      <xsl:value-of select="?label"/>
    </label>
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

  <!-- ========================================
       ADVANCED INPUT TYPES
       ======================================== -->

  <!-- Textarea -->
  <xsl:template match="map(*)[?type = 'textarea']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <textarea name="{?name}" id="{?name}">
        <xsl:call-template name="add-required-attribute"/>
        <xsl:if test="?rows">
          <xsl:attribute name="rows" select="?rows"/>
        </xsl:if>
        <xsl:if test="?cols">
          <xsl:attribute name="cols" select="?cols"/>
        </xsl:if>
        <xsl:value-of select="?value"/>
      </textarea>
    </div>
  </xsl:template>

  <!-- Color picker -->
  <xsl:template match="map(*)[?type = 'color']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="color" name="{?name}" id="{?name}"
             value="{(?value, '#000000')[1]}"/>
      <span class="color-preview" style="background-color: {(?value, '#000000')[1]}"></span>
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

  <!-- ========================================
       VIBECFORMS CUSTOM FIELDS
       ======================================== -->

  <!-- UUID display field -->
  <xsl:template match="map(*)[?type = 'uuid_display']">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <div class="uuid-display">
        <code class="uuid"><xsl:value-of select="?value"/></code>
        <button type="button" class="copy-btn" onclick="copyToClipboard('{?value}')">
          <i class="fa fa-copy"></i> Copy
        </button>
      </div>
    </div>
  </xsl:template>

  <!-- ========================================
       UTILITY TEMPLATES
       ======================================== -->

  <!-- Add required attribute if needed -->
  <xsl:template name="add-required-attribute">
    <xsl:if test="?required = true()">
      <xsl:attribute name="required">required</xsl:attribute>
    </xsl:if>
  </xsl:template>

  <!-- Add value attribute if present -->
  <xsl:template name="add-value-attribute">
    <xsl:if test="?value">
      <xsl:attribute name="value" select="?value"/>
    </xsl:if>
  </xsl:template>

  <!-- Fallback for unknown field types -->
  <xsl:template match="map(*)[?type]" priority="-1">
    <div class="form-row">
      <label for="{?name}"><xsl:value-of select="?label"/>:</label>
      <input type="text" name="{?name}" id="{?name}"/>
      <span class="field-warning">Unknown type: <xsl:value-of select="?type"/></span>
    </div>
  </xsl:template>

</xsl:stylesheet>
