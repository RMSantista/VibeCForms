<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Error message template -->
  <xsl:template name="error-message">
    <xsl:param name="error" as="xs:string"/>

    <xsl:if test="$error != ''">
      <div class="bg-red-50 border border-red-500 text-red-700 px-4 py-3 rounded mb-4 flex items-center gap-2">
        <i class="fa fa-exclamation-triangle"></i>
        <span><xsl:value-of select="$error"/></span>
      </div>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
