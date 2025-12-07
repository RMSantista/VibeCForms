<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="../base/html-shell.xslt"/>
  <xsl:import href="../components/menu.xslt"/>

  <!--
    Kanban Board Page Template (Placeholder)
    Future implementation for visual workflow management
  -->

  <xsl:template match="kanban-page">
    <xsl:call-template name="html-shell">
      <xsl:with-param name="title">Kanban Board</xsl:with-param>
      <xsl:with-param name="content">
        <xsl:call-template name="kanban-content"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="kanban-content">
    <div class="flex min-h-screen">
      <!-- Sidebar Menu -->
      <xsl:call-template name="sidebar-menu">
        <xsl:with-param name="menu-items" select="menu"/>
        <xsl:with-param name="active-form" select="@form-name"/>
      </xsl:call-template>

      <!-- Main Content -->
      <div class="flex-1 ml-64 p-10">
        <div class="max-w-6xl mx-auto bg-white p-8 rounded-lg shadow-md">
          <h2 class="text-3xl font-bold text-center mb-6 text-gray-800">
            <i class="fa fa-columns"></i> Kanban Board
          </h2>
          <div class="bg-blue-50 border-l-4 border-blue-500 p-6 rounded text-center">
            <i class="fa fa-info-circle text-blue-500 text-4xl mb-4"></i>
            <p class="text-lg text-gray-700">
              Kanban board - coming soon
            </p>
            <p class="text-sm text-gray-500 mt-2">
              This feature will enable visual workflow management with drag-and-drop cards.
            </p>
          </div>
        </div>
      </div>
    </div>
  </xsl:template>

</xsl:stylesheet>
