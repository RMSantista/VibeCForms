<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Color Field Template
    Supports both form rendering (color picker + hex display) and table display (swatch + hex)
  -->

  <!-- Form mode: renders color picker with live hex display -->
  <xsl:template match="field[@type='color']" mode="form">
    <xsl:variable name="fieldId" select="@name"/>
    <xsl:variable name="defaultColor">
      <xsl:choose>
        <xsl:when test="@value and @value != ''">#<xsl:value-of select="substring(@value, 2)"/></xsl:when>
        <xsl:otherwise>#000000</xsl:otherwise>
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
          type="color"
          name="{@name}"
          id="{@name}"
          value="{$defaultColor}"
          class="w-12 h-10 border border-gray-300 rounded cursor-pointer">
          <xsl:if test="@required = 'true'">
            <xsl:attribute name="required">required</xsl:attribute>
          </xsl:if>
        </input>
        <span id="{@name}_display" class="font-mono text-gray-700">
          <xsl:value-of select="translate($defaultColor, 'abcdef', 'ABCDEF')"/>
        </span>
      </div>
    </div>

    <script>
      <xsl:text disable-output-escaping="yes"><![CDATA[
      (function() {
        const colorInput = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[');
        const displaySpan = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[_display');
        if (colorInput && displaySpan) {
          colorInput.addEventListener('input', function() {
            displaySpan.textContent = this.value.toUpperCase();
          });
        }
      })();
      ]]></xsl:text>
    </script>
  </xsl:template>

  <!-- Table mode: displays color swatch + hex value -->
  <xsl:template match="field[@type='color']" mode="table">
    <td class="px-4 py-2 border-b">
      <div class="flex items-center gap-2">
        <div class="w-6 h-6 border border-gray-300 rounded" style="background-color: {@value}"></div>
        <span class="font-mono text-sm">
          <xsl:value-of select="translate(@value, 'abcdef', 'ABCDEF')"/>
        </span>
      </div>
    </td>
  </xsl:template>

</xsl:stylesheet>
