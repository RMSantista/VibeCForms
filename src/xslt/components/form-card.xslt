<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Form Card Component
    Renders a clickable card for each form on the landing page
  -->

  <xsl:template match="form" mode="card">
    <a href="/{@path}" class="form-card bg-blue-500 text-white no-underline p-8 rounded-xl flex flex-col items-center gap-4 text-center shadow-md transition-all duration-300 hover:bg-blue-600 hover:-translate-y-1 hover:shadow-xl">
      <i class="fa {@icon} text-5xl opacity-90"></i>
      <div class="form-title font-bold text-xl">
        <xsl:value-of select="@title"/>
      </div>
      <xsl:if test="@category and @category != ''">
        <div class="form-category text-sm opacity-80 bg-white bg-opacity-20 px-3 py-1 rounded-full">
          <xsl:value-of select="@category"/>
        </div>
      </xsl:if>
    </a>
  </xsl:template>

</xsl:stylesheet>
