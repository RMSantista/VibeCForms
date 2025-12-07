<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:map="http://www.w3.org/2005/xpath-functions/map"
                xmlns:array="http://www.w3.org/2005/xpath-functions/array"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:local="http://local-functions"
                exclude-result-prefixes="map array xs local">

  <!--
    Reusable XSLT templates for rendering tables in VibeCForms.
    Supports dynamic columns, tags, actions, and custom rendering.
  -->

  <xsl:output method="html" indent="yes" omit-xml-declaration="yes"/>

  <!-- ========================================
       MAIN TABLE TEMPLATE
       ======================================== -->

  <!-- Render table from VibeCForms data structure -->
  <xsl:template match=".[. instance of map(*) and exists(?spec) and exists(?records)]" mode="table">
    <xsl:choose>
      <xsl:when test="array:size(?records) gt 0">
        <div class="table-wrapper">
          <table>
            <!-- Table header -->
            <xsl:call-template name="render-table-header">
              <xsl:with-param name="fields" select="?spec?fields"/>
              <xsl:with-param name="show-tags" select="true()"/>
              <xsl:with-param name="show-actions" select="true()"/>
            </xsl:call-template>

            <!-- Table body -->
            <tbody>
              <xsl:apply-templates select="?records?*" mode="table-row">
                <xsl:with-param name="fields" select="?spec?fields"/>
                <xsl:with-param name="show-tags" select="true()"/>
                <xsl:with-param name="show-actions" select="true()"/>
              </xsl:apply-templates>
            </tbody>
          </table>
        </div>
      </xsl:when>
      <xsl:otherwise>
        <p class="no-records">No records found.</p>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ========================================
       TABLE HEADER
       ======================================== -->

  <!-- Render table header -->
  <xsl:template name="render-table-header">
    <xsl:param name="fields"/>
    <xsl:param name="show-tags" select="false()"/>
    <xsl:param name="show-actions" select="false()"/>

    <thead>
      <tr>
        <!-- Field headers (excluding hidden fields) -->
        <xsl:for-each select="$fields?*[not(?hidden = true())]">
          <th>
            <xsl:value-of select="?label"/>
            <xsl:if test="?required = true()">
              <span class="required-indicator">*</span>
            </xsl:if>
          </th>
        </xsl:for-each>

        <!-- Tags column header -->
        <xsl:if test="$show-tags">
          <th>Tags</th>
        </xsl:if>

        <!-- Actions column header -->
        <xsl:if test="$show-actions">
          <th>Actions</th>
        </xsl:if>
      </tr>
    </thead>
  </xsl:template>

  <!-- ========================================
       TABLE ROW
       ======================================== -->

  <!-- Render table row -->
  <xsl:template match=".[. instance of map(*)]" mode="table-row">
    <xsl:param name="fields"/>
    <xsl:param name="show-tags" select="false()"/>
    <xsl:param name="show-actions" select="false()"/>

    <tr data-id="{?uuid}">
      <!-- Render each field value -->
      <xsl:for-each select="$fields?*[not(?hidden = true())]">
        <xsl:variable name="field-name" select="?name"/>
        <xsl:variable name="field-type" select="?type"/>
        <xsl:variable name="field-value" select="current()?($field-name)"/>

        <xsl:call-template name="render-table-cell">
          <xsl:with-param name="field-type" select="$field-type"/>
          <xsl:with-param name="field-value" select="$field-value"/>
          <xsl:with-param name="field-spec" select="."/>
        </xsl:call-template>
      </xsl:for-each>

      <!-- Tags cell -->
      <xsl:if test="$show-tags">
        <td class="tags-cell">
          <xsl:apply-templates select="?tags" mode="tags"/>
        </td>
      </xsl:if>

      <!-- Actions cell -->
      <xsl:if test="$show-actions">
        <td class="actions-cell">
          <xsl:call-template name="render-actions">
            <xsl:with-param name="record-id" select="?uuid"/>
            <xsl:with-param name="record-index" select="position()"/>
          </xsl:call-template>
        </td>
      </xsl:if>
    </tr>
  </xsl:template>

  <!-- ========================================
       TABLE CELL RENDERING
       ======================================== -->

  <!-- Render individual table cell based on field type -->
  <xsl:template name="render-table-cell">
    <xsl:param name="field-type"/>
    <xsl:param name="field-value"/>
    <xsl:param name="field-spec"/>

    <td>
      <xsl:choose>
        <!-- Password: mask value -->
        <xsl:when test="$field-type = 'password'">
          <xsl:text>********</xsl:text>
        </xsl:when>

        <!-- Checkbox: show icon -->
        <xsl:when test="$field-type = 'checkbox'">
          <xsl:choose>
            <xsl:when test="$field-value = true()">
              <i class="fa fa-check-square" style="color: #27ae60;"></i>
            </xsl:when>
            <xsl:otherwise>
              <i class="fa fa-square" style="color: #95a5a6;"></i>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>

        <!-- Color: show color swatch -->
        <xsl:when test="$field-type = 'color'">
          <div class="color-swatch" style="background-color: {$field-value};">
            <xsl:value-of select="$field-value"/>
          </div>
        </xsl:when>

        <!-- Select: show label instead of value -->
        <xsl:when test="$field-type = 'select'">
          <xsl:variable name="selected-option"
                        select="$field-spec?options?*[?value = $field-value]"/>
          <xsl:choose>
            <xsl:when test="$selected-option">
              <xsl:value-of select="$selected-option?label"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$field-value"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>

        <!-- URL: show as link -->
        <xsl:when test="$field-type = 'url'">
          <a href="{$field-value}" target="_blank">
            <xsl:value-of select="$field-value"/>
          </a>
        </xsl:when>

        <!-- Email: show as mailto link -->
        <xsl:when test="$field-type = 'email'">
          <a href="mailto:{$field-value}">
            <xsl:value-of select="$field-value"/>
          </a>
        </xsl:when>

        <!-- Telephone: show as tel link -->
        <xsl:when test="$field-type = 'tel'">
          <a href="tel:{$field-value}">
            <xsl:value-of select="$field-value"/>
          </a>
        </xsl:when>

        <!-- UUID: show in monospace -->
        <xsl:when test="$field-type = 'uuid_display'">
          <code class="uuid"><xsl:value-of select="$field-value"/></code>
        </xsl:when>

        <!-- Textarea: truncate long text -->
        <xsl:when test="$field-type = 'textarea'">
          <xsl:choose>
            <xsl:when test="string-length($field-value) gt 50">
              <xsl:value-of select="substring($field-value, 1, 50)"/>
              <xsl:text>...</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$field-value"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>

        <!-- Default: show value as-is -->
        <xsl:otherwise>
          <xsl:value-of select="$field-value"/>
        </xsl:otherwise>
      </xsl:choose>
    </td>
  </xsl:template>

  <!-- ========================================
       TAGS RENDERING
       ======================================== -->

  <!-- Render tags array -->
  <xsl:template match=".[. instance of array(*)]" mode="tags">
    <xsl:apply-templates select="?*" mode="tag-badge"/>
  </xsl:template>

  <!-- Render individual tag -->
  <xsl:template match=".[. instance of map(*)]" mode="tag-badge">
    <span class="tag tag-color-{position() mod 10}"
          title="Applied by {?applied_by} ({?actor_type})">
      <xsl:value-of select="?tag"/>
    </span>
  </xsl:template>

  <!-- Empty tags -->
  <xsl:template match=".[. instance of array(*) and array:size(.) = 0]" mode="tags">
    <span class="no-tags">-</span>
  </xsl:template>

  <!-- ========================================
       ACTIONS RENDERING
       ======================================== -->

  <!-- Render action buttons -->
  <xsl:template name="render-actions">
    <xsl:param name="record-id"/>
    <xsl:param name="record-index"/>

    <div class="action-buttons">
      <!-- Edit button -->
      <a href="/edit/{$record-index}" class="icon-btn edit" title="Edit">
        <i class="fa fa-edit"></i>
      </a>

      <!-- Delete button -->
      <a href="/delete/{$record-index}" class="icon-btn delete" title="Delete"
         onclick="return confirm('Are you sure you want to delete this record?')">
        <i class="fa fa-trash"></i>
      </a>

      <!-- View tags button (if tags exist) -->
      <xsl:if test="?tags and array:size(?tags) gt 0">
        <button type="button" class="icon-btn view-tags" title="Manage Tags"
                onclick="showTagsModal('{$record-id}')">
          <i class="fa fa-tags"></i>
        </button>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- ========================================
       SIMPLIFIED TABLE (NO SPEC)
       ======================================== -->

  <!-- Render simple table from array (when spec not available) -->
  <xsl:template match=".[. instance of array(*)]" mode="simple-table">
    <xsl:if test="array:size(.) gt 0">
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
          <xsl:apply-templates select="?*" mode="simple-table-row"/>
        </tbody>
      </table>
    </xsl:if>
  </xsl:template>

  <!-- Simple table row -->
  <xsl:template match=".[. instance of map(*)]" mode="simple-table-row">
    <tr>
      <xsl:for-each select="?*">
        <td><xsl:value-of select="."/></td>
      </xsl:for-each>
    </tr>
  </xsl:template>

  <!-- ========================================
       COMPACT TABLE (FEWER COLUMNS)
       ======================================== -->

  <!-- Render compact table with selected fields only -->
  <xsl:template name="render-compact-table">
    <xsl:param name="records"/>
    <xsl:param name="display-fields"/>  <!-- Array of field names to display -->

    <table class="compact-table">
      <thead>
        <tr>
          <xsl:for-each select="$display-fields?*">
            <th><xsl:value-of select="."/></th>
          </xsl:for-each>
        </tr>
      </thead>
      <tbody>
        <xsl:for-each select="$records?*">
          <tr>
            <xsl:for-each select="$display-fields?*">
              <xsl:variable name="field-name" select="."/>
              <td><xsl:value-of select="current()?($field-name)"/></td>
            </xsl:for-each>
          </tr>
        </xsl:for-each>
      </tbody>
    </table>
  </xsl:template>

  <!-- ========================================
       UTILITY FUNCTIONS
       ======================================== -->

  <!-- Get hash-based color for tag -->
  <xsl:function name="local:get-tag-color-class">
    <xsl:param name="tag-name"/>
    <!-- Simple hash: sum of character codes mod 10 -->
    <xsl:variable name="hash" select="string-length($tag-name) mod 10"/>
    <xsl:value-of select="concat('tag-color-', $hash)"/>
  </xsl:function>

  <!-- Format timestamp -->
  <xsl:template name="format-timestamp">
    <xsl:param name="timestamp"/>
    <!-- Basic timestamp formatting - can be enhanced -->
    <xsl:value-of select="substring($timestamp, 1, 19)"/>
  </xsl:template>

</xsl:stylesheet>
