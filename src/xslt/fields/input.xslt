<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <!-- Input field template (text, email, tel, number, password, date, url, etc.) -->
  <xsl:template match="field[@type='text'] | field[@type='email'] | field[@type='tel'] |
                       field[@type='number'] | field[@type='password'] | field[@type='date'] |
                       field[@type='url'] | field[@type='search'] | field[@type='datetime-local'] |
                       field[@type='time'] | field[@type='month'] | field[@type='week']" mode="form">
    <div class="mb-4 flex items-center gap-2">
      <label for="{@name}" class="w-48 font-semibold text-gray-700">
        <xsl:value-of select="@label"/>:
      </label>
      <input
        type="{@type}"
        name="{@name}"
        id="{@name}"
        value="{@value}"
        class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
        <xsl:if test="@required = 'true'">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
      </input>
    </div>
  </xsl:template>

  <!-- Input field in table mode -->
  <xsl:template match="field[@type='text'] | field[@type='email'] | field[@type='tel'] |
                       field[@type='number'] | field[@type='date'] | field[@type='url'] |
                       field[@type='search'] | field[@type='datetime-local'] | field[@type='time'] |
                       field[@type='month'] | field[@type='week']" mode="table">
    <xsl:value-of select="."/>
  </xsl:template>

  <!-- Password field in table mode (masked) -->
  <xsl:template match="field[@type='password']" mode="table">
    <xsl:if test="string-length(.) &gt; 0">••••••••</xsl:if>
  </xsl:template>

</xsl:stylesheet>
