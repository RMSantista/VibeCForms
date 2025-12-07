<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Range Field Template
    Supports both form rendering (slider + value display) and table display (numeric value)
  -->

  <!-- Form mode: renders range slider with live value display -->
  <xsl:template match="field[@type='range']" mode="form">
    <xsl:variable name="min">
      <xsl:choose>
        <xsl:when test="@min"><xsl:value-of select="@min"/></xsl:when>
        <xsl:otherwise>0</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="max">
      <xsl:choose>
        <xsl:when test="@max"><xsl:value-of select="@max"/></xsl:when>
        <xsl:otherwise>100</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="step">
      <xsl:choose>
        <xsl:when test="@step"><xsl:value-of select="@step"/></xsl:when>
        <xsl:otherwise>1</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="currentValue">
      <xsl:choose>
        <xsl:when test="@value and @value != ''"><xsl:value-of select="@value"/></xsl:when>
        <xsl:otherwise><xsl:value-of select="$min"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <div class="mb-4">
      <label for="{@name}" class="block text-sm font-medium text-gray-700 mb-1">
        <xsl:value-of select="@label"/>
        <xsl:if test="@required = 'true'">
          <span class="text-red-500">*</span>
        </xsl:if>
      </label>
      <div class="flex items-center gap-3">
        <input
          type="range"
          name="{@name}"
          id="{@name}"
          min="{$min}"
          max="{$max}"
          step="{$step}"
          value="{$currentValue}"
          class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
          <xsl:if test="@required = 'true'">
            <xsl:attribute name="required">required</xsl:attribute>
          </xsl:if>
        </input>
        <span id="{@name}_display" class="min-w-12 text-center font-bold text-gray-700">
          <xsl:value-of select="$currentValue"/>
        </span>
      </div>
    </div>

    <script>
      <xsl:text disable-output-escaping="yes"><![CDATA[
      (function() {
        const rangeInput = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[');
        const displaySpan = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[_display');
        if (rangeInput && displaySpan) {
          rangeInput.addEventListener('input', function() {
            displaySpan.textContent = this.value;
          });
        }
      })();
      ]]></xsl:text>
    </script>
  </xsl:template>

  <!-- Table mode: displays numeric value -->
  <xsl:template match="field[@type='range']" mode="table">
    <td class="px-4 py-2 border-b">
      <xsl:value-of select="@value"/>
    </td>
  </xsl:template>

</xsl:stylesheet>
