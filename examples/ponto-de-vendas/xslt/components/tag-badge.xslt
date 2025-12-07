<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!--
    BUSINESS CASE OVERRIDE: Ponto de Vendas
    This template overrides the default tag badge with custom styling
    for retail/point-of-sale contexts.

    Customizations:
    - Larger badges (text-sm instead of text-xs, more padding)
    - Pill-shaped (rounded-full instead of rounded-xl)
    - Shopping cart icon prefix for product-related tags
    - Different hover effect (scale instead of translate)
    - Bold font weight
  -->

  <!-- Tag badge template with retail-focused styling -->
  <xsl:template name="tag-badge">
    <xsl:param name="tag" as="xs:string"/>

    <xsl:variable name="color-class">
      <xsl:call-template name="tag-color-hash">
        <xsl:with-param name="tag" select="$tag"/>
      </xsl:call-template>
    </xsl:variable>

    <span class="inline-flex items-center gap-1 text-white px-4 py-2 rounded-full text-sm font-bold m-1 whitespace-nowrap transition-transform hover:scale-110 shadow-md {$color-class}"
          style="cursor: default;"
          title="Tag: {$tag}">
      <!-- Add shopping cart icon for product-related tags -->
      <xsl:if test="contains($tag, 'produto') or contains($tag, 'venda') or contains($tag, 'estoque')">
        <i class="fa fa-shopping-cart text-xs"></i>
      </xsl:if>
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
