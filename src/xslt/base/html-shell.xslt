<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

  <!-- Main template for HTML shell -->
  <xsl:template name="html-shell">
    <xsl:param name="title" as="xs:string"/>
    <xsl:param name="content" as="node()*"/>

    <html>
      <head>
        <title><xsl:value-of select="$title"/></title>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

        <!-- Tailwind CSS CDN -->
        <script src="https://cdn.tailwindcss.com"></script>

        <!-- Font Awesome -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>

        <!-- Custom CSS for compatibility -->
        <style>
          /* Tag color classes for consistent tag coloring */
          .tag-color-0 { background-color: #3498db; }
          .tag-color-1 { background-color: #27ae60; }
          .tag-color-2 { background-color: #e74c3c; }
          .tag-color-3 { background-color: #f39c12; }
          .tag-color-4 { background-color: #9b59b6; }
          .tag-color-5 { background-color: #1abc9c; }
          .tag-color-6 { background-color: #e67e22; }
          .tag-color-7 { background-color: #34495e; }
          .tag-color-8 { background-color: #16a085; }
          .tag-color-9 { background-color: #2c3e50; }
        </style>
      </head>
      <body class="bg-gray-100 font-sans">
        <xsl:copy-of select="$content"/>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>
