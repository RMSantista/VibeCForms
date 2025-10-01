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
