<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Radio Field Template
    Supports both form rendering (radio group) and table display (selected label)
  -->

  <!-- Form mode: renders radio button group -->
  <xsl:template match="field[@type='radio']" mode="form">
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">
        <xsl:value-of select="@label"/>
        <xsl:if test="@required = 'true'">
          <span class="text-red-500">*</span>
        </xsl:if>
      </label>
      <div class="flex flex-col gap-2">
        <xsl:for-each select="option">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="{../@name}"
              value="{@value}"
              class="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500">
              <xsl:if test="../@required = 'true'">
                <xsl:attribute name="required">required</xsl:attribute>
              </xsl:if>
              <xsl:if test="@value = ../@value">
                <xsl:attribute name="checked">checked</xsl:attribute>
              </xsl:if>
            </input>
            <span class="text-gray-700"><xsl:value-of select="@label"/></span>
          </label>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>

  <!-- Table mode: displays selected option label -->
  <xsl:template match="field[@type='radio']" mode="table">
    <td class="px-4 py-2 border-b">
      <xsl:variable name="currentValue" select="@value"/>
      <xsl:for-each select="option">
        <xsl:if test="@value = $currentValue">
          <xsl:value-of select="@label"/>
        </xsl:if>
      </xsl:for-each>
    </td>
  </xsl:template>

</xsl:stylesheet>
