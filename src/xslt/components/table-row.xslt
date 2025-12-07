<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Note: Field templates are included by the parent (form.xslt) -->
  <!-- Do not include field templates here to avoid circular includes -->

  <!-- Table row template -->
  <xsl:template match="record" mode="table-row">
    <xsl:param name="form-name" as="xs:string"/>

    <xsl:variable name="record-id" select="@id"/>

    <tr class="border-b border-gray-200 hover:bg-gray-50">
      <!-- Tags cell -->
      <td class="px-4 py-3 text-center align-middle tags-cell"
          id="tags-{$record-id}"
          data-record-id="{$record-id}"
          data-form-name="{$form-name}">
        <!-- Tags loaded dynamically via JavaScript -->
      </td>

      <!-- Field cells -->
      <xsl:apply-templates select="field" mode="table-cell"/>

      <!-- Actions cell -->
      <td class="px-4 py-3 text-center align-middle">
        <a href="/{$form-name}/edit/{$record-id}"
           class="inline-block bg-yellow-500 text-white px-3 py-2 rounded hover:bg-yellow-600 transition-colors mx-1">
          <i class="fa fa-edit"></i>
        </a>
        <a href="/{$form-name}/delete/{$record-id}"
           class="inline-block bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600 transition-colors mx-1"
           onclick="return confirm('Tem certeza que deseja excluir este registro?');">
          <i class="fa fa-trash"></i>
        </a>
      </td>
    </tr>
  </xsl:template>

  <!-- Table cell for visible fields -->
  <xsl:template match="field[@type!='hidden' and @name!='_record_id']" mode="table-cell">
    <td class="px-4 py-3 text-center align-middle whitespace-nowrap overflow-hidden text-ellipsis">
      <xsl:apply-templates select="." mode="table"/>
    </td>
  </xsl:template>

  <!-- Skip hidden and UUID fields in table cells -->
  <xsl:template match="field[@type='hidden' or @name='_record_id']" mode="table-cell">
    <!-- Do not render cell for hidden or UUID fields -->
  </xsl:template>

</xsl:stylesheet>
