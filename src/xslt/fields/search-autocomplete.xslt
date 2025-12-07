<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!--
    Search Autocomplete Field Template
    Supports both form rendering (search input + datalist) and table display (value)
  -->

  <!-- Form mode: renders search input with autocomplete datalist -->
  <xsl:template match="field[@type='search']" mode="form">
    <div class="mb-4">
      <label for="{@name}" class="block text-sm font-medium text-gray-700 mb-1">
        <xsl:value-of select="@label"/>
        <xsl:if test="@required = 'true'">
          <span class="text-red-500">*</span>
        </xsl:if>
      </label>
      <input
        type="search"
        name="{@name}"
        id="{@name}"
        list="{@name}_datalist"
        autocomplete="off"
        value="{@value}"
        placeholder="Digite para buscar..."
        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        <xsl:if test="@required = 'true'">
          <xsl:attribute name="required">required</xsl:attribute>
        </xsl:if>
      </input>
      <datalist id="{@name}_datalist"></datalist>
    </div>

    <script>
      <xsl:text disable-output-escaping="yes"><![CDATA[
      (function() {
        const input = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[');
        const datalist = document.getElementById(']]></xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[_datalist');
        let debounceTimer;

        if (input && datalist) {
          input.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
              datalist.innerHTML = '';
              return;
            }

            // Debounce: wait 300ms after user stops typing
            debounceTimer = setTimeout(function() {
              fetch('/api/search/]]></xsl:text>
              <xsl:value-of select="@datasource"/>
              <xsl:text disable-output-escaping="yes"><![CDATA[?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                  datalist.innerHTML = '';
                  data.forEach(nome => {
                    const option = document.createElement('option');
                    option.value = nome;
                    datalist.appendChild(option);
                  });
                })
                .catch(error => {
                  console.error('Erro ao buscar dados:', error);
                });
            }, 300);
          });
        }
      })();
      ]]></xsl:text>
    </script>
  </xsl:template>

  <!-- Table mode: displays value -->
  <xsl:template match="field[@type='search']" mode="table">
    <td class="px-4 py-2 border-b">
      <xsl:value-of select="@value"/>
    </td>
  </xsl:template>

</xsl:stylesheet>
