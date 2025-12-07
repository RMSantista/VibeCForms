<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Hidden field template -->
  <xsl:template match="field[@type='hidden']" mode="form">
    <input type="hidden" name="{@name}" id="{@name}" value="{@value}"/>
  </xsl:template>

  <!-- Hidden field in table mode (not displayed) -->
  <xsl:template match="field[@type='hidden']" mode="table">
    <!-- Hidden fields are not displayed in table -->
  </xsl:template>

</xsl:stylesheet>
