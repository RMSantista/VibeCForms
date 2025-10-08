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
