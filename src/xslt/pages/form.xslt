<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

  <!-- Import component templates -->
  <xsl:include href="../base/html-shell.xslt"/>
  <xsl:include href="../components/menu.xslt"/>
  <xsl:include href="../components/error-message.xslt"/>
  <xsl:include href="../components/table-header.xslt"/>
  <xsl:include href="../components/table-row.xslt"/>
  <xsl:include href="../components/tag-badge.xslt"/>

  <!-- Import field templates -->
  <xsl:include href="../fields/input.xslt"/>
  <xsl:include href="../fields/select.xslt"/>
  <xsl:include href="../fields/checkbox.xslt"/>
  <xsl:include href="../fields/uuid-display.xslt"/>
  <xsl:include href="../fields/hidden.xslt"/>

  <!-- Main form page template -->
  <xsl:template match="/form-page">
    <xsl:variable name="form-name" select="@form-name"/>
    <xsl:variable name="title" select="spec/@title"/>
    <xsl:variable name="error" select="@error"/>

    <xsl:call-template name="html-shell">
      <xsl:with-param name="title" select="$title"/>
      <xsl:with-param name="content">
        <div class="flex min-h-screen">
          <!-- Sidebar Menu -->
          <xsl:apply-templates select="menu" mode="sidebar"/>

          <!-- Main Content -->
          <div class="ml-64 flex-1 p-10">
            <div class="max-w-6xl mx-auto bg-white p-8 rounded-lg shadow-md">
              <!-- Page Title -->
              <h2 class="text-3xl text-center mb-6 text-gray-800">
                <xsl:value-of select="$title"/>
              </h2>

              <!-- Default Tags Display -->
              <xsl:if test="spec/default-tags/tag">
                <div class="text-center mb-5 -mt-4">
                  <xsl:apply-templates select="spec/default-tags/tag" mode="default-tag"/>
                </div>
              </xsl:if>

              <!-- Error Message -->
              <xsl:call-template name="error-message">
                <xsl:with-param name="error" select="$error"/>
              </xsl:call-template>

              <!-- Form -->
              <form method="post" id="cadastroForm" class="flex flex-col gap-4 mb-8">
                <xsl:apply-templates select="spec/fields/field" mode="form"/>

                <div class="flex gap-2.5 mt-2">
                  <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
                    <i class="fa fa-plus mr-2"></i>Cadastrar
                  </button>
                </div>
              </form>

              <!-- Records Table -->
              <h3 class="text-xl mb-4 mt-8">Registros cadastrados:</h3>
              <div class="w-full overflow-x-auto">
                <table class="w-full border-collapse min-w-[600px]">
                  <xsl:apply-templates select="spec" mode="table-header"/>
                  <tbody>
                    <xsl:apply-templates select="records/record" mode="table-row">
                      <xsl:with-param name="form-name" select="$form-name"/>
                    </xsl:apply-templates>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- JavaScript for tag management and menu positioning -->
        <script>
          <xsl:text disable-output-escaping="yes"><![CDATA[
            // Tag management functions
            async function loadTags(recordId, formName) {
                try {
                    const response = await fetch(`/api/${formName}/tags/${recordId}`);
                    const data = await response.json();

                    if (data.success && data.tags) {
                        displayTags(recordId, formName, data.tags);
                    }
                } catch (error) {
                    console.error('Error loading tags:', error);
                }
            }

            function getTagColorClass(tag) {
                // Simple hash function to assign consistent colors to tags
                let hash = 0;
                for (let i = 0; i < tag.length; i++) {
                    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
                }
                return `tag-color-${Math.abs(hash) % 10}`;
            }

            function displayTags(recordId, formName, tags) {
                const container = document.getElementById(`tags-${recordId}`);
                if (!container) return;

                if (tags.length === 0) {
                    container.innerHTML = '';
                    return;
                }

                // Display tags without remove buttons
                container.innerHTML = tags.map(tagData => {
                    const tag = tagData.tag || tagData;
                    const colorClass = getTagColorClass(tag);
                    return `<span class="inline-block text-white px-2 py-1 rounded-xl text-xs m-0.5 whitespace-nowrap transition-transform hover:translate-y-[-1px] hover:shadow ${colorClass}" style="cursor: default;" title="Tag: ${tag}">
                        ${tag}
                    </span>`;
                }).join('');
            }

            function validateTagName(tag) {
                // Tags must be lowercase, alphanumeric, and underscores only
                const pattern = /^[a-z0-9_]+$/;
                return pattern.test(tag);
            }

            async function addTag(recordId, formName, tag) {
                if (!tag || !tag.trim()) return;

                tag = tag.trim().toLowerCase();

                // Validate tag name
                if (!validateTagName(tag)) {
                    alert('Tag inválida: use apenas letras minúsculas, números e underscore (_)');
                    return;
                }

                try {
                    const response = await fetch(`/api/${formName}/tags/${recordId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tag: tag, applied_by: 'user' })
                    });

                    const data = await response.json();

                    if (data.success) {
                        // Reload tags to show the new one
                        loadTags(recordId, formName);
                    } else {
                        alert('Erro ao adicionar tag: ' + (data.error || 'Desconhecido'));
                    }
                } catch (error) {
                    console.error('Error adding tag:', error);
                    alert('Erro ao adicionar tag: ' + error.message);
                }
            }

            async function removeTag(recordId, formName, tag) {
                try {
                    const response = await fetch(`/api/${formName}/tags/${recordId}/${encodeURIComponent(tag)}?removed_by=user`, {
                        method: 'DELETE'
                    });

                    const data = await response.json();

                    if (data.success) {
                        // Reload tags to remove the deleted one
                        loadTags(recordId, formName);
                    } else {
                        alert('Erro ao remover tag: ' + (data.error || 'Desconhecido'));
                    }
                } catch (error) {
                    console.error('Error removing tag:', error);
                    alert('Erro ao remover tag: ' + error.message);
                }
            }

            window.onload = function() {
                var form = document.getElementById('cadastroForm');
                if (form) {
                    form.onkeydown = function(e) {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            return false;
                        }
                    };
                }

                // Position submenus dynamically
                var menuItems = document.querySelectorAll('.group');
                menuItems.forEach(function(item) {
                    item.addEventListener('mouseenter', function() {
                        var submenu = this.querySelector(':scope > ul');
                        if (submenu) {
                            var rect = this.getBoundingClientRect();
                            submenu.style.top = rect.top + 'px';

                            // For nested submenus, calculate left position
                            if (this.closest('ul.fixed')) {
                                submenu.style.left = (rect.right) + 'px';
                            }
                        }
                    });
                });

                // Load tags automatically for all records (read-only display)
                document.querySelectorAll('.tags-cell').forEach(function(cell) {
                    const recordId = cell.dataset.recordId;
                    const formName = cell.dataset.formName;
                    if (recordId && formName) {
                        loadTags(recordId, formName);
                    }
                });
            };
          ]]></xsl:text>
        </script>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- Default tag template -->
  <xsl:template match="tag" mode="default-tag">
    <xsl:call-template name="tag-badge">
      <xsl:with-param name="tag" select="."/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
