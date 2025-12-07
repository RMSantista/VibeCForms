<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="../base/html-shell.xslt"/>
  <xsl:import href="../components/menu.xslt"/>
  <xsl:import href="../components/error-message.xslt"/>
  <xsl:import href="../components/tag-badge.xslt"/>
  <xsl:import href="../fields/input.xslt"/>
  <xsl:import href="../fields/textarea.xslt"/>
  <xsl:import href="../fields/select.xslt"/>
  <xsl:import href="../fields/checkbox.xslt"/>
  <xsl:import href="../fields/radio.xslt"/>
  <xsl:import href="../fields/color.xslt"/>
  <xsl:import href="../fields/range.xslt"/>
  <xsl:import href="../fields/search-autocomplete.xslt"/>
  <xsl:import href="../fields/uuid-display.xslt"/>
  <xsl:import href="../fields/hidden.xslt"/>

  <!--
    Edit Page Template
    Displays a form for editing an existing record with pre-populated values
  -->

  <xsl:template match="edit-page">
    <xsl:call-template name="html-shell">
      <xsl:with-param name="title">Editar - <xsl:value-of select="spec/@title"/></xsl:with-param>
      <xsl:with-param name="content">
        <xsl:call-template name="edit-content"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="edit-content">
    <div class="flex min-h-screen">
      <!-- Sidebar Menu -->
      <xsl:apply-templates select="menu" mode="sidebar"/>

      <!-- Main Content -->
      <div class="flex-1 ml-64 p-10">
        <div class="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow-md">
          <h2 class="text-2xl font-bold text-center mb-6 text-gray-800">
            Editar - <xsl:value-of select="spec/@title"/>
          </h2>

          <!-- Record ID Display -->
          <xsl:if test="record/@id">
            <div class="bg-gray-100 border-l-4 border-blue-500 p-3 mb-5 rounded">
              <strong class="text-gray-800">ID do Registro:</strong>
              <span class="font-mono text-xs text-gray-600 bg-white px-2 py-1 rounded ml-2 select-all">
                <xsl:value-of select="record/@id"/>
              </span>
            </div>
          </xsl:if>

          <!-- Error Message -->
          <xsl:if test="@error">
            <xsl:call-template name="error-message">
              <xsl:with-param name="error" select="@error"/>
            </xsl:call-template>
          </xsl:if>

          <!-- Tags Display (Read-only) -->
          <xsl:if test="tags/tag">
            <div class="bg-green-50 border-l-4 border-green-500 p-3 mb-5 rounded">
              <strong class="text-gray-800 block mb-2">
                <i class="fa fa-tags"></i> Tags Atuais:
              </strong>
              <div class="flex flex-wrap gap-2">
                <xsl:apply-templates select="tags/tag" mode="tag-display"/>
              </div>
              <p class="text-xs text-gray-500 mt-2 italic">
                Use o Gerenciador de Tags (menu) para adicionar ou remover tags.
              </p>
            </div>
          </xsl:if>

          <!-- Edit Form -->
          <form method="post" class="flex flex-col gap-4">
            <xsl:for-each select="spec/fields/field">
              <xsl:apply-templates select="." mode="form"/>
            </xsl:for-each>

            <!-- Form Actions -->
            <div class="flex justify-end gap-3 mt-4">
              <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
                <i class="fa fa-save"></i> Salvar
              </button>
              <a href="/{/edit-page/@form-name}" class="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500 transition-colors no-underline inline-block">
                <i class="fa fa-times"></i> Cancelar
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </xsl:template>

</xsl:stylesheet>
