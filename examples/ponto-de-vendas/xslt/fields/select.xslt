<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!--
    BUSINESS CASE OVERRIDE: Ponto de Vendas
    This template overrides the default select field with custom styling
    for the Ponto de Vendas business case.

    Customizations:
    - Larger fonts (text-lg)
    - Blue theme instead of default gray
    - Wider label (w-56 instead of w-48)
    - Thicker border (border-2)
    - Custom placeholder text in Portuguese
  -->

  <!-- Form mode: editable dropdown with custom styling -->
  <xsl:template match="field[@type='select']" mode="form">
    <div class="mb-6 flex items-center gap-3">
      <label for="{@name}" class="w-56 text-lg font-bold text-blue-800">
        <xsl:value-of select="@label"/>:
      </label>
      <select name="{@name}" id="{@name}"
              class="flex-1 px-4 py-3 text-lg border-2 border-blue-400 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600">
        <xsl:if test="@required='true'">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
        <option value="">-- Escolha uma opção --</option>
        <xsl:apply-templates select="options/option" mode="option">
          <xsl:with-param name="selected-value" select="@value"/>
        </xsl:apply-templates>
      </select>
    </div>
  </xsl:template>

  <!-- Option template (reusable) -->
  <xsl:template match="option" mode="option">
    <xsl:param name="selected-value"/>
    <option value="{@value}">
      <xsl:if test="@value = $selected-value">
        <xsl:attribute name="selected">selected</xsl:attribute>
      </xsl:if>
      <xsl:value-of select="@label"/>
    </option>
  </xsl:template>

  <!-- Table mode: display label with blue badge -->
  <xsl:template match="field[@type='select']" mode="table">
    <td class="px-4 py-2 text-center border-b border-gray-200">
      <xsl:variable name="value" select="@value"/>
      <span class="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
        <xsl:value-of select="(options/option[@value=$value]/@label, @value)[1]"/>
      </span>
    </td>
  </xsl:template>

</xsl:stylesheet>
