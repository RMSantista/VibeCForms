<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Select field template -->
  <xsl:template match="field[@type='select']" mode="form">
    <div class="mb-4 flex items-center gap-2">
      <label for="{@name}" class="w-48 font-semibold text-gray-700">
        <xsl:value-of select="@label"/>:
      </label>
      <select
        name="{@name}"
        id="{@name}"
        class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
        <xsl:if test="@required = 'true'">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>

        <option value="">-- Selecione --</option>

        <xsl:apply-templates select="options/option" mode="select-option">
          <xsl:with-param name="selected-value" select="@value"/>
        </xsl:apply-templates>
      </select>
    </div>
  </xsl:template>

  <!-- Select option template -->
  <xsl:template match="option" mode="select-option">
    <xsl:param name="selected-value" as="xs:string"/>

    <option value="{@value}">
      <xsl:if test="@value = $selected-value">
        <xsl:attribute name="selected">selected</xsl:attribute>
      </xsl:if>
      <xsl:value-of select="@label"/>
    </option>
  </xsl:template>

  <!-- Select field in table mode (display label, not value) -->
  <xsl:template match="field[@type='select']" mode="table">
    <xsl:variable name="field-value" select="@value"/>
    <xsl:choose>
      <xsl:when test="options/option[@value = $field-value]">
        <xsl:value-of select="options/option[@value = $field-value]/@label"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$field-value"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
