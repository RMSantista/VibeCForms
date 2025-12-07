<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="../base/html-shell.xslt"/>
  <xsl:import href="../components/menu.xslt"/>

  <!--
    Tags Manager Page Template (Placeholder)
    Future implementation for managing tags on records
  -->

  <xsl:template match="tags-manager-page">
    <xsl:call-template name="html-shell">
      <xsl:with-param name="title">Tags Manager</xsl:with-param>
      <xsl:with-param name="content">
        <xsl:call-template name="tags-manager-content"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="tags-manager-content">
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
            <i class="fa fa-tags"></i> Tags Manager
          </h2>
          <div class="bg-green-50 border-l-4 border-green-500 p-6 rounded text-center">
            <i class="fa fa-info-circle text-green-500 text-4xl mb-4"></i>
            <p class="text-lg text-gray-700">
              Tags manager - coming soon
            </p>
            <p class="text-sm text-gray-500 mt-2">
              This feature will enable adding, removing, and managing tags on records.
            </p>
          </div>
        </div>
      </div>
    </div>
  </xsl:template>

</xsl:stylesheet>
