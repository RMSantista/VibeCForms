<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Recursive menu template -->
  <xsl:template match="menu" mode="sidebar">
    <nav class="w-64 bg-gray-800 text-white fixed h-screen flex flex-col z-50">
      <!-- Header -->
      <div class="px-5 py-5 border-b border-gray-700">
        <h1 class="text-2xl italic text-blue-400">VibeCForms</h1>
        <p class="text-xs text-gray-400 mt-1">Formulários Dinâmicos</p>
      </div>

      <!-- Menu Container -->
      <div class="flex-1 overflow-y-auto">
        <ul class="list-none p-0 m-0">
          <xsl:apply-templates select="item" mode="menu-item"/>
        </ul>

        <!-- Home Link -->
        <a href="/" class="flex items-center gap-3 px-5 py-4 text-gray-200 hover:bg-gray-700 hover:text-blue-400 transition-all border-t border-gray-700 mt-2.5">
          <i class="fa fa-home w-5 text-center text-lg"></i>
          <span>Página Inicial</span>
        </a>
      </div>
    </nav>
  </xsl:template>

  <!-- Menu item template -->
  <xsl:template match="item" mode="menu-item">
    <xsl:choose>
      <!-- Form item -->
      <xsl:when test="@type = 'form'">
        <li>
          <a href="/{@path}" class="flex items-center gap-3 px-5 py-4 text-gray-200 hover:bg-gray-700 hover:text-blue-400 transition-all whitespace-nowrap">
            <xsl:if test="@active = 'true'">
              <xsl:attribute name="class">flex items-center gap-3 px-5 py-4 text-white bg-blue-500 hover:bg-blue-600 transition-all whitespace-nowrap</xsl:attribute>
            </xsl:if>
            <i class="fa {@icon} w-5 text-center text-lg"></i>
            <span><xsl:value-of select="@title"/></span>
          </a>
        </li>
      </xsl:when>

      <!-- Folder item with submenu -->
      <xsl:otherwise>
        <li class="relative group">
          <a href="#" class="flex items-center gap-3 px-5 py-4 text-gray-200 hover:bg-gray-700 hover:text-blue-400 transition-all whitespace-nowrap">
            <xsl:if test="@active-path = 'true'">
              <xsl:attribute name="class">flex items-center gap-3 px-5 py-4 text-gray-200 bg-gray-700 hover:bg-gray-700 transition-all whitespace-nowrap</xsl:attribute>
            </xsl:if>
            <i class="fa {@icon} w-5 text-center text-lg"></i>
            <span><xsl:value-of select="@title"/></span>
            <i class="fa fa-chevron-right text-xs ml-auto"></i>
          </a>

          <!-- Submenu -->
          <xsl:if test="item">
            <ul class="hidden group-hover:block fixed left-64 bg-gray-700 min-w-[220px] shadow-lg rounded z-[2000] list-none p-0 m-0">
              <xsl:apply-templates select="item" mode="submenu-item"/>
            </ul>
          </xsl:if>
        </li>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Submenu item template -->
  <xsl:template match="item" mode="submenu-item">
    <xsl:choose>
      <!-- Form item -->
      <xsl:when test="@type = 'form'">
        <li>
          <a href="/{@path}" class="flex items-center gap-3 px-5 py-3 text-sm text-gray-200 hover:bg-gray-600 hover:text-blue-400 transition-all whitespace-nowrap">
            <xsl:if test="@active = 'true'">
              <xsl:attribute name="class">flex items-center gap-3 px-5 py-3 text-sm text-white bg-blue-500 hover:bg-blue-600 transition-all whitespace-nowrap</xsl:attribute>
            </xsl:if>
            <xsl:if test="@icon != ''">
              <i class="fa {@icon} w-5 text-center"></i>
            </xsl:if>
            <span><xsl:value-of select="@title"/></span>
          </a>
        </li>
      </xsl:when>

      <!-- Nested folder -->
      <xsl:otherwise>
        <li class="relative group/nested">
          <a href="#" class="flex items-center gap-3 px-5 py-3 text-sm text-gray-200 hover:bg-gray-600 hover:text-blue-400 transition-all whitespace-nowrap">
            <xsl:if test="@active-path = 'true'">
              <xsl:attribute name="class">flex items-center gap-3 px-5 py-3 text-sm text-gray-200 bg-gray-600 hover:bg-gray-600 transition-all whitespace-nowrap</xsl:attribute>
            </xsl:if>
            <i class="fa {@icon} w-5 text-center"></i>
            <span><xsl:value-of select="@title"/></span>
            <i class="fa fa-chevron-right text-xs ml-auto"></i>
          </a>

          <!-- Nested submenu -->
          <xsl:if test="item">
            <ul class="hidden group-hover/nested:block fixed left-[calc(16rem+220px)] bg-gray-800 min-w-[220px] shadow-lg rounded z-[2000] list-none p-0 m-0">
              <xsl:apply-templates select="item" mode="submenu-item"/>
            </ul>
          </xsl:if>
        </li>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
