# Prompts

## Prompt 1
Preciso criar, testar e ao final, estando tudo correto, executar um CRUD simples para cadastrar apenas o nome do cliente, seu telefone e marcar se o telefone tem WhatsApp. Os dados serão persistidos em um arquivo texto nessa pasta.

**Required dependencies:**
- Ambiente virtual dotenv para rodar a aplicação.
- Utilize pytest para fazer os testes unitários.
- Por fim, execute o programa em um navegador.

---

## Prompt 2
Funcionou, porém o programa só está cadastrando e exibindo. Para um CRUD completo preciso que os dados possam ser também alterados e excluídos. Crie também os respectivos testes unitários para essas funcionalidades.

---

## Prompt 3
Ótimo, o CRUD está funcional, porém ele está com um layout muito "cru". Gostaria que aplicasse um CSS e deixasse ele mais apresentável.

- Coloque a exibição dos dados dentro de uma tabela.
- Onde se usa hiperlinks para editar, excluir ou cancelar, troque por botões ou ícones intuitivos.
- Alinhe os campos do cadastro.
- Troque o nome de "Cadastro de Clientes" para "Agenda Pessoal".

---

## Prompt 4
- Alinhe o botão cadastrar abaixo do campo WhatsApp.
- Desabilite que ao clicar na tecla Enter, ele clique automaticamente em cadastrar.

---

## Prompt 5
- Alargue lateralmente o painel e a tabela de forma que na exibição os números de telefone, nomes não muito extensos, telefones e botões ocupem apenas uma única linha por registro.

---

## Prompt 6
Adicione as seguintes regras de validação no cadastro que exibam mensagens na tela caso ocorram:
- Não existe cadastro vazio (sem nome e telefone).
- É obrigatório cadastrar ao menos um nome, caso não seja informado.
- O contato deve ter um telefone, caso esse não seja informado.
- Quando alguma dessas situações ocorrer, a mensagem deve ser exibida e não permitir o cadastro ou alteração.
- Assim que os campos forem devidamente preenchidos e o botão cadastrar ou salvar forem clicados, a ação será realizada normalmente.

---

## Prompt 7 - Formulários Dinâmicos

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Modo:** Plan mode (planejamento colaborativo antes da execução)

### Solicitação Original:
"I want to change this project so it can read from a spec file with fields and types to generate the form dynamically. The name of the spec file should be part of the URL (not a parameter)"

### Plano Apresentado e Aprovado:

**Mudanças na Arquitetura:**
1. Estrutura de URL: `/<form_name>` (ex: `/contatos`, `/produtos`)
2. Arquivos de especificação JSON em `src/specs/`
3. Cada formulário tem seu próprio arquivo de dados: `<form_name>.txt`

**Formato do Arquivo de Especificação (JSON):**
```json
{
  "title": "Título do Formulário",
  "fields": [
    {"name": "campo", "label": "Rótulo", "type": "text", "required": true}
  ],
  "validation_messages": {
    "all_empty": "Mensagem para campos vazios",
    "campo": "Mensagem específica do campo"
  }
}
```

**Tipos de Campos Suportados:**
- `text` - Campo de texto
- `tel` - Telefone
- `email` - Email
- `number` - Numérico
- `checkbox` - Caixa de seleção (booleano)
- `textarea` - Área de texto multilinha

**Etapas de Implementação:**
1. Criar estrutura de specs e arquivo `contatos.json`
2. Adicionar função de carregamento de specs com validação
3. Refatorar `read_forms()` e `write_forms()` para campos dinâmicos
4. Criar funções geradoras de templates HTML dinâmicos
5. Atualizar rotas para usar padrão `/<form_name>`
6. Implementar lógica de validação dinâmica
7. Migrar `registros.txt` para `contatos.txt`
8. Atualizar testes para arquitetura dinâmica
9. Executar testes para verificar funcionamento

### Resultado da Implementação:

**Novas Funções Criadas:**
- `load_spec(form_name)` - Carrega e valida arquivos de especificação
- `get_data_file(form_name)` - Obtém caminho do arquivo de dados
- `generate_form_field(field, form_data)` - Gera HTML de campo dinamicamente
- `generate_table_headers(spec)` - Gera cabeçalhos de tabela
- `generate_table_row(form_data, spec, idx, form_name)` - Gera linhas da tabela
- `validate_form_data(spec, form_data)` - Validação dinâmica
- `get_main_template()` - Template da página principal
- `get_edit_template()` - Template da página de edição

**Novas Rotas:**
- `GET/POST /<form_name>` - Página principal do formulário
- `GET/POST /<form_name>/edit/<idx>` - Edição de registro
- `GET /<form_name>/delete/<idx>` - Exclusão de registro
- Rotas antigas redirecionam para `/contatos/*` (compatibilidade)

**Arquivos Criados:**
- `src/specs/contatos.json` - Especificação do formulário de contatos
- `src/specs/produtos.json` - Especificação de exemplo (produtos)
- `docs/dynamic_forms.md` - Guia completo de uso
- `CHANGELOG.md` - Registro de mudanças versão 2.0

**Testes Atualizados:**
- Todos os testes refatorados para arquitetura dinâmica
- Novo teste: `test_validation()` - Valida lógica de validação dinâmica
- Novo teste: `test_load_spec()` - Valida carregamento de specs
- ✅ Todos os 5 testes passando

**Compatibilidade:**
- Dados migrados de `registros.txt` para `contatos.txt`
- URL raiz `/` redireciona para `/contatos`
- Rotas antigas mantidas com redirecionamento

### Impacto:
O projeto evoluiu de um CRUD fixo para um **sistema gerador de formulários dinâmicos**. Agora é possível criar novos tipos de formulários apenas adicionando um arquivo JSON de especificação, sem necessidade de alterar código Python.

---

## Prompt 8 - Página Principal e Menu Lateral Persistente

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Janeiro 2025

### Solicitação 1: Página Principal
"Existem 2 problemas: 1 - O sistema não deve abrir diretamente em um formulário. Crie uma página main que apresente o nome do projeto em letras grandes e em itálico. Esta deve ser a página para onde a aplicação deve abrir ao ser executada."

### Resultado:
- Criada rota `/` que renderiza página principal
- Página main com design gradient roxo/azul
- Título "VibeCForms" em fonte grande (72px) e itálico
- Links para formulários existentes (Agenda Pessoal e Catálogo de Produtos)
- Removido redirecionamento automático para `/contatos`

### Solicitação 2: Menu Lateral Persistente
"A navegação está ocorrendo por substituição direta do nome do formulário no fim da URL. Crie um menu persistente na lateral esquerda da tela, para que eu possa navegar entre os formulários. O painel onde o formulário é exibido precisa ser extendido para a direita de forma a acomodar a largura original do formulário + a largura do menu lateral."

### Resultado:
- Criado menu sidebar fixo de 250px à esquerda
- Container do formulário expandido para 1200px
- Layout flexbox: sidebar + main-content
- Menu com estilo gradient e hover effects
- Implementado em ambos templates (main e edit)

---

## Prompt 9 - Menu Dinâmico com Submenus Hierárquicos

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Janeiro 2025

### Solicitação Original:
"Sim deixe o menu dinâmico mas agregue a seguinte funcionalidade: Subpastas dentro da pasta spec são agrupamentos de formulários. Ao passar o mouse sobre o agrupamento, os subagrupamentos e/ou os formulários que estão agrupados devem aparecer em um menu se extendendo mais para a direita."

### Requisitos Adicionais:
1. Criar arquivos e pastas de exemplo
2. Ícones intuitivos para pastas (ex: financeiro = cifrão)
3. Primeira letra do nome da pasta em maiúscula
4. Título do formulário obtido do campo `title` do JSON
5. Ícones apenas para formulários não agrupados
6. Destaque do item de menu ativo

### Implementação:

**Nova Estrutura de Arquivos:**
```
specs/
├── contatos.json
├── produtos.json
├── financeiro/
│   ├── contas.json
│   └── pagamentos.json
└── rh/
    ├── funcionarios.json
    └── departamentos/
        └── areas.json
```

**Novas Funções:**

1. `get_folder_icon(folder_name)` - Mapeia nomes de pasta para ícones Font Awesome:
   - financeiro → fa-dollar-sign
   - rh → fa-users
   - departamentos → fa-sitemap
   - padrão → fa-folder

2. `scan_specs_directory(base_path, relative_path)` - Varre recursivamente o diretório specs:
   - Retorna lista hierárquica de itens
   - Diferencia formulários (type: "form") de pastas (type: "folder")
   - Cada formulário: {type, name, path, title, icon}
   - Cada pasta: {type, name, path, icon, children[]}

3. `generate_menu_html(menu_items, current_form_path, level)` - Gera HTML do menu:
   - Recursivo para suportar aninhamento infinito
   - Adiciona classe "has-submenu" para pastas
   - Adiciona classe "active" para item atual
   - Capitaliza primeira letra dos nomes de pastas
   - Submenus com classe "submenu level-N"

**Atualização de Rotas:**
- Alterado de `/<form_name>` para `/<path:form_name>`
- Suporta caminhos aninhados: `/financeiro/contas`, `/rh/departamentos/areas`
- `load_spec()` e `get_data_file()` adaptados para caminhos com `/`
- Arquivos de dados usam underscores: `financeiro_contas.txt`

**CSS para Submenus:**
```css
.has-submenu:hover > .submenu {
    display: block;
}
.submenu {
    position: fixed;
    left: 250px;
    z-index: 2000;
}
```

**JavaScript para Posicionamento Dinâmico:**
- Event listener em `.has-submenu`
- Calcula posição top baseada no `getBoundingClientRect()`
- Submenus aninhados posicionados à direita do pai

### Resultado:
✅ Menu dinâmico que escaneia estrutura de pastas automaticamente
✅ Suporte a múltiplos níveis de aninhamento
✅ Submenus aparecem ao hover, flutuando sobre o conteúdo
✅ Ícones intuitivos atribuídos automaticamente
✅ Item ativo destacado visualmente
✅ 6 formulários criados em estrutura hierárquica

---

## Prompt 10 - Correção de Overflow de Submenus

**Problema Reportado:**
"Os menus continuam se extendendo no frame do menu, criando uma barra de rolagem ao invés de extender sobre o formulário aberto. Corrija."

### Análise do Problema:
- Sidebar tinha `overflow-y: auto`
- Submenus com `position: absolute` ficavam contidos pelo parent com overflow
- Causava barra de rolagem no sidebar ao invés de flutuar sobre o conteúdo

### Solução Implementada:

**Reestruturação do Sidebar:**
```css
.sidebar {
    display: flex;
    flex-direction: column;
}
.menu-container {
    flex: 1;
    overflow-y: auto;
    position: relative;
}
.menu li {
    position: static;  /* Crucial para libertar submenus */
}
.submenu {
    position: fixed;  /* Alterado de absolute para fixed */
    left: 250px;
    z-index: 2000;
}
```

**JavaScript Aprimorado:**
- Cálculo dinâmico da posição top do submenu
- Diferenciação entre submenus de primeiro nível e aninhados
- Submenus aninhados: `left = rect.right` (não 250px fixo)

### Resultado:
✅ Submenus flutuam sobre o formulário aberto
✅ Sidebar não cria barra de rolagem horizontal
✅ Múltiplos níveis funcionam corretamente

---

## Prompt 11 - Correção de Alinhamento de Texto

**Problema Reportado:**
"Os menus continuam desalinhados. Formulários não agrupados estão com os textos alinhados à direita em relação aos ícones. Ajuste para que fiquem alinhados às pastas."

### Causa:
CSS `justify-content: space-between` distribuía elementos, empurrando texto para longe do ícone.

### Solução:
```css
.menu a {
    display: flex;
    align-items: center;
    gap: 12px;  /* Espaçamento consistente */
    /* Removido: justify-content: space-between */
}
.submenu-arrow {
    margin-left: auto;  /* Empurra seta para direita */
}
```

### Resultado:
✅ Textos alinhados à esquerda consistentemente
✅ Ícones e textos com espaçamento uniforme de 12px
✅ Setas de submenu permanecem à direita

---

## Prompt 12 - Página Principal Dinâmica com Cards

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Janeiro 2025

### Solicitação:
"A main page deve contemplar todos os formulários de forma dinâmica. Eles devem ser colocados como os botões (como os formulários Agenda Pessoal e Catálogo de Produtos), distribuídos na tela."

### Implementação:

**Nova Função:**
```python
def get_all_forms_flat(menu_items=None, prefix=""):
    """Achata estrutura hierárquica do menu para listar todos os formulários.

    Retorna lista de dicionários:
    - title: Título do formulário
    - path: Caminho completo (ex: "financeiro/contas")
    - icon: Ícone Font Awesome
    - category: Categoria baseada na pasta pai (ex: "Financeiro")
    """
```

**Lógica de Categorização:**
- Formulários no root: categoria = "Geral"
- Formulários em pasta: categoria = nome da pasta pai capitalizado
- Recursivo: percorre toda a hierarquia

**Redesign da Página Principal:**

CSS Grid Layout:
```css
.forms-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}
```

Cards de Formulário:
```css
.form-card {
    background: #667eea;
    padding: 40px 30px;
    border-radius: 15px;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: all 0.3s;
}
.form-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
}
```

Elementos do Card:
- Ícone grande (48px) com opacidade 0.9
- Título do formulário (20px, bold)
- Badge de categoria (12px, semi-transparente)

**Atualização da Rota:**
```python
@app.route("/")
def main_page():
    forms = get_all_forms_flat()
    return render_template_string(get_main_page_template(), forms=forms)
```

### Resultado:
✅ 6 formulários exibidos dinamicamente
✅ Layout responsivo com CSS Grid
✅ Cards distribuídos uniformemente
✅ Categorias atribuídas automaticamente:
  - Agenda Pessoal (Geral)
  - Catálogo de Produtos (Geral)
  - Contas (Financeiro)
  - Pagamentos (Financeiro)
  - Funcionários (Rh)
  - Áreas (Departamentos)
✅ Hover effects com elevação e sombra
✅ Container expandido para 1200px

---

## Resumo das Funcionalidades Implementadas

### Sistema de Navegação:
1. **Página Principal** - Landing page com cards de todos os formulários
2. **Menu Lateral Persistente** - 250px fixo, sempre visível
3. **Menu Dinâmico Hierárquico** - Escaneia estrutura de pastas automaticamente
4. **Submenus Multi-nível** - Hover revela, flutua sobre conteúdo
5. **Destaque de Item Ativo** - Indicador visual do formulário atual

### Sistema de Ícones:
- Mapeamento inteligente: financeiro → cifrão, rh → pessoas, etc.
- Ícones apenas para formulários não agrupados (requisito atendido)
- Fallback para ícone genérico de pasta

### Arquitetura de Dados:
- Suporte a caminhos aninhados na URL
- Arquivos de dados com nomes seguros (underscores)
- Carregamento de specs por path completo

### Testes Unitários:
✅ 11 testes implementados, todos passando
- `test_get_folder_icon` - Validação de mapeamento de ícones
- `test_scan_specs_directory` - Validação de estrutura do menu
- `test_get_all_forms_flat` - Validação de achatamento da hierarquia
- `test_generate_menu_html` - Validação de geração HTML
- `test_load_spec_nested` - Carregamento de specs aninhados
- `test_generate_menu_html_with_active` - Destaque de item ativo

### Impacto Final:
O VibeCForms evoluiu de uma aplicação CRUD simples para um **sistema completo de gerenciamento de formulários dinâmicos com navegação hierárquica**. A interface permite:
- Adicionar novos formulários sem código
- Organizar formulários em categorias e subcategorias
- Navegação intuitiva via menu e página principal
- Escalabilidade ilimitada de níveis de aninhamento

---

## Prompt 13 - Suporte a Ícones Personalizados (PR #5, Melhoria #1)

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Janeiro 2025

### Contexto:
Os ícones dos formulários eram atribuídos através de mapeamentos hardcoded na função `get_folder_icon()`. Isso exigia mudanças no código Python sempre que um novo ícone era necessário.

### Solicitação:
Implementar suporte a campo `icon` opcional nos arquivos de especificação dos formulários.

### Implementação:

**Alterações no formato do spec:**
```json
{
  "title": "Agenda Pessoal",
  "icon": "fa-address-book",
  "fields": [...]
}
```

**Função atualizada:**
- `scan_specs_directory()` - Passou a ler o campo `icon` dos specs
- Formulários sem ícone recebem fallback "fa-file-alt"
- Ícones são usados no menu lateral e nos cards da página principal

**Specs atualizados:**
- `contatos.json` - Adicionado `"icon": "fa-address-book"`
- `produtos.json` - Adicionado `"icon": "fa-box"`
- `financeiro/contas.json` - Adicionado `"icon": "fa-file-invoice-dollar"`
- `financeiro/pagamentos.json` - Adicionado `"icon": "fa-money-check-alt"`
- `rh/funcionarios.json` - Adicionado `"icon": "fa-id-card"`
- `rh/departamentos/areas.json` - Adicionado `"icon": "fa-project-diagram"`

**Novos testes:**
- `test_icon_from_spec()` - Valida leitura de ícones dos specs
- `test_icon_in_menu_items()` - Verifica ícones na estrutura do menu

### Resultado:
✅ Ícones personalizáveis por formulário via configuração JSON
✅ Elimina necessidade de mapeamento hardcoded
✅ Consistência visual entre menu e página principal
✅ Mais flexibilidade para personalização

---

## Prompt 14 - Sistema de Configuração de Pastas (PR #5, Melhoria #2)

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Janeiro 2025

### Contexto:
As pastas de specs tinham nomes técnicos (ex: "rh" em vez de "Recursos Humanos") e não havia forma de customizar ícones, descrições ou ordem de exibição sem alterar código Python.

### Solicitação:
Implementar sistema de configuração declarativa para pastas usando arquivos `_folder.json`.

### Implementação:

**Formato do arquivo _folder.json:**
```json
{
  "name": "Nome de Exibição",
  "description": "Descrição opcional da categoria",
  "icon": "fa-icon-name",
  "order": 1
}
```

**Exemplos criados:**

**src/specs/financeiro/_folder.json:**
```json
{
  "name": "Financeiro",
  "description": "Gestão financeira e contábil",
  "icon": "fa-dollar-sign",
  "order": 1
}
```

**src/specs/rh/_folder.json:**
```json
{
  "name": "Recursos Humanos",
  "description": "Gestão de pessoas e departamentos",
  "icon": "fa-users",
  "order": 2
}
```

**src/specs/rh/departamentos/_folder.json:**
```json
{
  "name": "Departamentos",
  "description": "Estrutura organizacional",
  "icon": "fa-sitemap",
  "order": 1
}
```

**Nova função:**
- `load_folder_config(folder_path)` - Carrega e parseia _folder.json

**Função atualizada:**
- `scan_specs_directory()` - Aplica configuração de _folder.json quando disponível
- Menu ordenado automaticamente pelo campo `order`

**Novos testes:**
- `test_folder_config_loading()` - Valida carregamento dos arquivos de configuração
- `test_folder_items_use_config()` - Verifica aplicação das configurações
- `test_menu_items_sorted_by_order()` - Valida ordenação pelo campo order

### Resultado:
✅ Customização declarativa de pastas
✅ Nomes de exibição mais profissionais
✅ Descrições opcionais para documentação
✅ Controle de ordem de exibição
✅ Ícones customizáveis por pasta
✅ Escalável para estruturas complexas

---

## Prompt 15 - Sistema de Templates Jinja2 (PR #5, Melhoria #3)

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Outubro 2025

### Contexto:
O código do VibeCForms.py havia crescido para 925 linhas, com cerca de 330 linhas sendo strings HTML/CSS/JavaScript embutidas em três funções de template. Isso dificultava a manutenção e não seguia as melhores práticas do Flask.

### Solicitação:
"Implemente o Sistema de Templates"
(Sugestão #3 do code review do PR #5)

### Plano de Implementação (11 tarefas):

1. **Criar diretório src/templates/**
2. **Extrair index.html** (landing page)
3. **Extrair form.html** (formulário principal)
4. **Extrair edit.html** (página de edição)
5. **Modificar imports** no VibeCForms.py
6. **Configurar Flask template_folder**
7. **Substituir render_template_string por render_template**
8. **Remover funções get_*_template()**
9. **Rodar suite de testes completa**
10. **Testar aplicação manualmente**
11. **Commit e push das mudanças**

### Arquivos de Template Criados:

**1. src/templates/index.html** (99 linhas)
- Landing page com grid de formulários
- Cards interativos com ícones, títulos e categorias
- Background gradient (#2c3e50)
- Hover effects com elevação e sombra

**2. src/templates/form.html** (124 linhas)
- Página principal CRUD com sidebar persistente
- Menu lateral com navegação hierárquica
- Formulário de cadastro com validação
- Tabela de registros com botões editar/excluir
- JavaScript para posicionamento de submenus

**3. src/templates/edit.html** (101 linhas)
- Página de edição de registros
- Sidebar idêntico ao form.html para consistência
- Formulário pré-preenchido com dados atuais
- Botões Salvar e Cancelar

### Mudanças no VibeCForms.py:

**Import atualizado:**
```python
# Antes:
from flask import Flask, render_template_string, request, redirect, abort

# Depois:
from flask import Flask, render_template, request, redirect, abort
```

**Configuração do Flask:**
```python
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=TEMPLATE_DIR)
```

**Substituição nas rotas:**
```python
# Antes:
return render_template_string(get_main_template(), title=..., ...)

# Depois:
return render_template('form.html', title=..., ...)
```

**Funções removidas:**
- `get_main_template()` (~126 linhas)
- `get_edit_template()` (~103 linhas)
- `get_main_page_template()` (~101 linhas)

### Resultados:

**Redução de Código:**
- VibeCForms.py: 925 → 587 linhas
- Redução de 338 linhas (36.5%)

**Benefícios Obtidos:**
- ✅ Separação clara entre lógica (Python) e apresentação (HTML)
- ✅ Syntax highlighting adequado para HTML/CSS/JavaScript
- ✅ Melhor suporte de IDEs para templates
- ✅ Facilita manutenção e modificação de UI
- ✅ Segue melhores práticas do Flask
- ✅ Reutilização de código via herança de templates (preparado para futuro)

**Testes:**
- ✅ Todos os 16 testes unitários continuam passando
- ✅ Nenhuma mudança funcional, apenas arquitetural
- ✅ Aplicação testada manualmente (navegação, CRUD, validações)

### Impacto:
A implementação do sistema de templates representa uma melhoria significativa na **qualidade do código** e **manutenibilidade** do projeto, sem alterar funcionalidades. O VibeCForms agora segue a arquitetura padrão do Flask, separando preocupações e facilitando futuras evoluções da interface.

---

## Resumo das Melhorias - Versão 2.1 (PR #5)

### Overview das 3 Melhorias Implementadas:

**Melhoria #1: Suporte a Ícones Personalizados**
- Campo `icon` opcional em specs de formulários
- Elimina hardcoding de ícones no código Python
- Consistência visual entre menu e landing page

**Melhoria #2: Sistema de Configuração de Pastas**
- Arquivos `_folder.json` para customização declarativa
- Nomes profissionais, descrições, ícones e ordenação
- Escalável para estruturas organizacionais complexas

**Melhoria #3: Sistema de Templates Jinja2**
- Separação HTML/CSS/JS do código Python
- Redução de 36.5% no tamanho do código (925 → 587 linhas)
- Arquitetura padrão Flask com melhor manutenibilidade

### Testes Implementados:
Total: **16 testes unitários**, todos passando ✅
- 5 testes originais (CRUD básico)
- 6 testes de formulários dinâmicos
- 2 testes de suporte a ícones
- 3 testes de configuração de pastas

### Arquivos Adicionados:
**Templates:**
- `src/templates/index.html` (99 linhas)
- `src/templates/form.html` (124 linhas)
- `src/templates/edit.html` (101 linhas)

**Configurações de pastas:**
- `src/specs/financeiro/_folder.json`
- `src/specs/rh/_folder.json`
- `src/specs/rh/departamentos/_folder.json`

**Ícones adicionados aos specs:**
- Todos os 6 formulários atualizados com campo `icon`

### Arquivos Modificados:
- `src/VibeCForms.py` - Reduzido de 925 para 587 linhas
- `tests/test_form.py` - 5 novos testes adicionados

### Benefícios Acumulados:
1. **Configurabilidade**: Ícones e pastas configuráveis via JSON
2. **Manutenibilidade**: Código Python mais enxuto e focado
3. **Escalabilidade**: Estrutura preparada para crescimento
4. **Padronização**: Segue melhores práticas do Flask
5. **Documentação**: Código autodocumentado via specs

### Impacto Geral:
As 3 melhorias transformam o VibeCForms em um sistema ainda mais **declarativo** e **profissional**, onde praticamente **tudo é configurável via JSON** sem necessidade de tocar no código Python. A separação de templates prepara o projeto para futuras evoluções da UI e facilita colaboração entre desenvolvedores front-end e back-end.

---

## Prompt 16 - Templates por Campo de Formulário e Novos Tipos (Versão 2.2)

**Ferramenta:** Claude Code (claude.ai/code)
**Modelo:** Claude Sonnet 4.5
**Data:** Outubro 2025
**Branch:** dev_vcforms_cc

### Solicitação 1: Templates Individuais por Campo
"Criar um template por campo de formulário na branch dev_vcforms_cc do repositório VibeCForms."

### Implementação:

**Diretório criado:**
- `src/templates/fields/` - Pasta para templates de campos

**Templates criados:**

**1. src/templates/fields/input.html**
```html
<div class="form-row">
    <label for="{{ field_name }}">{{ field_label }}:</label>
    <input type="{{ input_type }}" name="{{ field_name }}"
           id="{{ field_name }}" {% if required %}required{% endif %}
           value="{{ value }}">
</div>
```

**2. src/templates/fields/textarea.html**
```html
<div class="form-row">
    <label for="{{ field_name }}">{{ field_label }}:</label>
    <textarea name="{{ field_name }}" id="{{ field_name }}"
              {% if required %}required{% endif %}>{{ value }}</textarea>
</div>
```

**3. src/templates/fields/checkbox.html**
```html
<div class="form-row">
    <label for="{{ field_name }}">{{ field_label }}:</label>
    <input type="checkbox" name="{{ field_name }}"
           id="{{ field_name }}" {% if checked %}checked{% endif %}>
</div>
```

**Refatoração de `generate_form_field()`:**
```python
def generate_form_field(field, form_data=None):
    """Generate HTML for a single form field based on spec using templates."""
    # Carrega template apropriado baseado no tipo do campo
    template_path = os.path.join(TEMPLATE_DIR, "fields")

    if field_type == "checkbox":
        template_file = os.path.join(template_path, "checkbox.html")
        # Renderiza com render_template_string()
    elif field_type == "textarea":
        template_file = os.path.join(template_path, "textarea.html")
    else:
        template_file = os.path.join(template_path, "input.html")
        # Suporta: text, tel, email, number
```

### Solicitação 2: Novos Tipos de Campo
"Crie templates ou ajuste os existentes para campos: Senha e Data."

**Atualização da função:**
- Adicionado `"password"` e `"date"` à lista de tipos válidos
- Template `input.html` já suporta qualquer tipo de input HTML

**Spec de exemplo criado:**
`src/specs/usuarios.json` - Formulário de cadastro de usuários com novos campos:
```json
{
  "title": "Cadastro de Usuários",
  "icon": "fa-user-plus",
  "fields": [
    {"name": "nome", "type": "text", "required": true},
    {"name": "email", "type": "email", "required": true},
    {"name": "senha", "type": "password", "required": true},
    {"name": "data_nascimento", "type": "date", "required": true},
    {"name": "ativo", "type": "checkbox", "required": false}
  ]
}
```

**Tipos de campo agora suportados (8 total):**
1. `text` - Texto simples
2. `tel` - Telefone
3. `email` - E-mail
4. `number` - Numérico
5. `password` - Senha (mascarada) ⭐ **NOVO**
6. `date` - Seletor de data ⭐ **NOVO**
7. `textarea` - Texto multilinha
8. `checkbox` - Booleano

### Solicitação 3: Ajustes de Layout CSS

**Primeira tentativa - Campos em linha:**
"Ajuste os nomes dos campos no formulário, para que apareçam em uma única linha."

CSS implementado:
```css
form { display: flex; flex-wrap: wrap; gap: 15px; }
.form-row {
    display: flex;
    flex-direction: column;
    flex: 1 1 200px;
    min-width: 200px;
}
```
Resultado: Múltiplos campos lado a lado com layout responsivo

**Correção - Campos verticais:**
"Os campos devem se manter um abaixo do outro."

CSS corrigido:
```css
form { display: flex; flex-direction: column; gap: 15px; }
label { font-weight: bold; min-width: 180px; }
input, textarea { flex: 1; }
.form-row { display: flex; align-items: center; gap: 10px; }
```

**Layout final:**
- Campos empilhados verticalmente (um abaixo do outro)
- Dentro de cada campo: label e input na mesma linha horizontal
- Label com largura fixa de 180px à esquerda
- Input ocupando o espaço restante à direita

Aplicado em ambos templates:
- `src/templates/form.html` (cadastro)
- `src/templates/edit.html` (edição)

### Resultados:

**Arquivos criados:**
- 3 templates de campos individuais
- 1 spec de exemplo (usuarios.json)

**Arquivos modificados:**
- `src/VibeCForms.py` - Função `generate_form_field()` refatorada
- `src/templates/form.html` - CSS atualizado
- `src/templates/edit.html` - CSS atualizado
- `CLAUDE.md` - Documentação atualizada
- `docs/prompts.md` - Este arquivo

**Testes:**
- ✅ Todos os 16 testes unitários continuam passando
- ✅ Servidor rodando em modo desenvolvimento
- ✅ Formulários testados visualmente no navegador

### Benefícios:

1. **Modularização de Templates**
   - HTML separado por tipo de campo
   - Fácil customização de aparência por tipo
   - Reduz acoplamento no código Python

2. **Expansibilidade de Tipos**
   - Suporte a password e date sem código adicional
   - Preparado para novos tipos HTML5
   - Template genérico reutilizável

3. **Layout Profissional**
   - Label e input alinhados horizontalmente
   - Campos organizados verticalmente
   - Design consistente e responsivo

4. **Manutenibilidade**
   - Separação completa de estrutura HTML
   - CSS isolado e modular
   - Alterações sem impactar lógica

### Impacto:
A **Versão 2.2** completa a separação de templates iniciada na versão anterior, granularizando até o nível de campo individual. Isso torna o VibeCForms ainda mais flexível e customizável, permitindo ajustar a apresentação de cada tipo de campo de forma independente.
