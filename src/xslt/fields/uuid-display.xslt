<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- UUID display field (read-only, shown only when editing existing records) -->
  <xsl:template match="field[@name='_record_id']" mode="form">
    <xsl:if test="@value != ''">
      <div class="mb-4 flex items-center gap-2">
        <label class="w-48 font-semibold text-gray-700">
          ID do Registro:
        </label>
        <div class="flex-1 px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-gray-600 font-mono text-sm">
          <xsl:value-of select="@value"/>
        </div>
      </div>
    </xsl:if>
  </xsl:template>

  <!-- UUID field in table mode (not displayed) -->
  <xsl:template match="field[@name='_record_id']" mode="table">
    <!-- UUID is not displayed in table -->
  </xsl:template>

</xsl:stylesheet>
