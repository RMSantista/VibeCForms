<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Checkbox field template -->
  <xsl:template match="field[@type='checkbox']" mode="form">
    <div class="mb-4 flex items-center gap-2">
      <label for="{@name}" class="w-48 font-semibold text-gray-700">
        <xsl:value-of select="@label"/>:
      </label>
      <input
        type="checkbox"
        name="{@name}"
        id="{@name}"
        class="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500">
        <xsl:if test="@value = 'true' or @value = 'True' or @value = '1'">
          <xsl:attribute name="checked">checked</xsl:attribute>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Checkbox field in table mode (Sim/Não) -->
  <xsl:template match="field[@type='checkbox']" mode="table">
    <xsl:choose>
      <xsl:when test="@value = 'true' or @value = 'True' or @value = '1'">Sim</xsl:when>
      <xsl:otherwise>Não</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
