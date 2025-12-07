<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Tag badge template with color hashing -->
  <xsl:template name="tag-badge">
    <xsl:param name="tag" as="xs:string"/>

    <xsl:variable name="color-class">
      <xsl:call-template name="tag-color-hash">
        <xsl:with-param name="tag" select="$tag"/>
      </xsl:call-template>
    </xsl:variable>

    <span class="inline-block text-white px-2 py-1 rounded-xl text-xs m-0.5 whitespace-nowrap transition-transform hover:translate-y-[-1px] hover:shadow {$color-class}"
          style="cursor: default;"
          title="Tag: {$tag}">
      <xsl:value-of select="$tag"/>
    </span>
  </xsl:template>

  <!-- Simple hash function to assign consistent colors to tags -->
  <xsl:template name="tag-color-hash">
    <xsl:param name="tag" as="xs:string"/>

    <!-- Convert tag to codepoints and sum them -->
    <xsl:variable name="hash" as="xs:integer">
      <xsl:value-of select="
        sum(
          for $char in string-to-codepoints($tag)
          return $char
        ) mod 10
      "/>
    </xsl:variable>

    <xsl:value-of select="concat('tag-color-', $hash)"/>
  </xsl:template>

  <!-- Mode-based template for tag display -->
  <xsl:template match="tag" mode="tag-display">
    <xsl:call-template name="tag-badge">
      <xsl:with-param name="tag" select="."/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
