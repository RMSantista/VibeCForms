<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Textarea Field Template
    Supports both form rendering and table display modes
  -->

  <!-- Form mode: renders editable textarea -->
  <xsl:template match="field[@type='textarea']" mode="form">
    <div class="mb-4">
      <label for="{@name}" class="block text-sm font-medium text-gray-700 mb-1">
        <xsl:value-of select="@label"/>
        <xsl:if test="@required = 'true'">
          <span class="text-red-500">*</span>
        </xsl:if>
      </label>
      <textarea
        name="{@name}"
        id="{@name}"
        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y min-h-24"
        style="resize: vertical;">
        <xsl:if test="@required = 'true'">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
        <xsl:value-of select="@value"/>
      </textarea>
    </div>
  </xsl:template>

  <!-- Table mode: displays text value -->
  <xsl:template match="field[@type='textarea']" mode="table">
    <td class="px-4 py-2 border-b">
      <xsl:value-of select="@value"/>
    </td>
  </xsl:template>

</xsl:stylesheet>
