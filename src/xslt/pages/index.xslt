<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:import href="../base/html-shell.xslt"/>
  <xsl:import href="../components/menu.xslt"/>
  <xsl:import href="../components/form-card.xslt"/>

  <!--
    Index/Landing Page Template
    Displays a grid of form cards for all available forms
  -->

  <xsl:template match="index-page">
    <xsl:call-template name="html-shell">
      <xsl:with-param name="title">VibeCForms</xsl:with-param>
      <xsl:with-param name="content">
        <xsl:call-template name="index-content"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="index-content">
    <div class="min-h-screen bg-gray-800 flex items-center justify-center">
      <div class="max-w-6xl w-11/12 bg-gray-800 p-16 rounded-2xl shadow-xl text-center">
        <h1 class="text-7xl italic text-blue-500 mb-5">VibeCForms</h1>
        <p class="text-lg text-gray-200 my-5 leading-relaxed">
          Bem-vindo ao VibeCForms - Uma aplicação web de gerenciamento de formulários dinâmicos<br/>
          construída com o conceito de <strong>Vibe Coding</strong>, programação assistida por IA.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 mt-10">
          <xsl:for-each select="forms/form">
            <xsl:apply-templates select="." mode="card"/>
          </xsl:for-each>
        </div>
      </div>
    </div>
  </xsl:template>

</xsl:stylesheet>
