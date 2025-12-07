<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Table header template -->
  <xsl:template match="spec" mode="table-header">
    <thead>
      <tr class="bg-blue-500 text-white">
        <!-- Tags column (15%) -->
        <th class="px-4 py-3 text-center" style="width: 15%;">Tags</th>

        <!-- Field columns (60% total) -->
        <xsl:apply-templates select="fields/field" mode="table-header-cell"/>

        <!-- Actions column (25%) -->
        <th class="px-4 py-3 text-center" style="width: 25%;">Ações</th>
      </tr>
    </thead>
  </xsl:template>

  <!-- Table header cell for each visible field -->
  <xsl:template match="field[@type!='hidden' and @name!='_record_id']" mode="table-header-cell">
    <th class="px-4 py-3 text-center">
      <xsl:value-of select="@label"/>
    </th>
  </xsl:template>

  <!-- Skip hidden and UUID fields in table headers -->
  <xsl:template match="field[@type='hidden' or @name='_record_id']" mode="table-header-cell">
    <!-- Do not render header for hidden or UUID fields -->
  </xsl:template>

</xsl:stylesheet>
