# Guia de Formulários Dinâmicos

## Visão Geral

O VibeCForms agora suporta formulários dinâmicos baseados em arquivos de especificação JSON. Isso permite criar diferentes tipos de formulários sem modificar o código da aplicação.

## Estrutura de URLs

Os formulários são acessados através de URLs que incluem o nome do formulário:

- `http://localhost:5000/contatos` - Formulário de contatos
- `http://localhost:5000/produtos` - Formulário de produtos
- `http://localhost:5000/<form_name>` - Qualquer formulário definido

## Criando um Novo Formulário

### 1. Crie o Arquivo de Especificação

Crie um arquivo JSON em `src/specs/<form_name>.json`:

```json
{
  "title": "Título do Formulário",
  "fields": [
    {
      "name": "campo1",
      "label": "Rótulo do Campo",
      "type": "text",
      "required": true
    }
  ],
  "validation_messages": {
    "all_empty": "Mensagem quando todos os campos obrigatórios estão vazios",
    "campo1": "Mensagem quando campo1 está vazio"
  }
}
```

### 2. Tipos de Campos Suportados (20 tipos)

O VibeCForms agora suporta **todos os 20 tipos de campos HTML5**:

#### Campos Básicos (7):
- **text**: Campo de texto simples
- **tel**: Campo de telefone
- **email**: Campo de email com validação
- **number**: Campo numérico
- **password**: Campo de senha (caracteres mascarados)
- **url**: Campo de URL com validação
- **search**: Campo de busca

#### Campos de Data/Hora (5):
- **date**: Seletor de data
- **time**: Seletor de hora
- **datetime-local**: Seletor de data e hora combinados
- **month**: Seletor de mês e ano
- **week**: Seletor de semana

#### Campos de Seleção (3):
- **select**: Lista suspensa (dropdown) - requer array `options`
- **radio**: Grupo de botões de opção - requer array `options`
- **checkbox**: Caixa de seleção (booleano)

#### Campos Avançados (2):
- **color**: Seletor de cores com exibição hex
- **range**: Slider numérico - requer `min`, `max`, `step`

#### Outros Campos (3):
- **textarea**: Área de texto multilinha
- **hidden**: Campo oculto
- **search com autocomplete**: Campo de busca com sugestões dinâmicas - requer atributo `datasource`

### 3. Propriedades dos Campos

Cada campo pode ter as seguintes propriedades:

#### Propriedades Básicas:
- `name` (obrigatório): Nome interno do campo (usado no armazenamento)
- `label` (obrigatório): Texto exibido ao usuário
- `type` (obrigatório): Tipo do campo (veja lista acima)
- `required` (opcional): Se o campo é obrigatório (padrão: false)

#### Propriedades Específicas por Tipo:

**Para campos select e radio:**
- `options` (obrigatório): Array de objetos com `value` e `label`
  ```json
  "options": [
    {"value": "SP", "label": "São Paulo"},
    {"value": "RJ", "label": "Rio de Janeiro"}
  ]
  ```

**Para campo range:**
- `min` (opcional): Valor mínimo (padrão: 0)
- `max` (opcional): Valor máximo (padrão: 100)
- `step` (opcional): Incremento (padrão: 1)

**Para campo search com autocomplete:**
- `datasource` (opcional): Nome da fonte de dados para autocomplete (ex: "contatos")

### 4. Exemplos de Novos Campos

#### Campo Select (Dropdown):
```json
{
  "name": "estado",
  "label": "Estado",
  "type": "select",
  "options": [
    {"value": "SP", "label": "São Paulo"},
    {"value": "RJ", "label": "Rio de Janeiro"},
    {"value": "MG", "label": "Minas Gerais"}
  ],
  "required": true
}
```

#### Campo Radio:
```json
{
  "name": "genero",
  "label": "Gênero",
  "type": "radio",
  "options": [
    {"value": "M", "label": "Masculino"},
    {"value": "F", "label": "Feminino"},
    {"value": "O", "label": "Outro"}
  ],
  "required": true
}
```

#### Campo Color:
```json
{
  "name": "cor_favorita",
  "label": "Cor Favorita",
  "type": "color",
  "required": false
}
```

#### Campo Range:
```json
{
  "name": "prioridade",
  "label": "Prioridade (1-10)",
  "type": "range",
  "min": 1,
  "max": 10,
  "step": 1,
  "required": false
}
```

#### Campo Search com Autocomplete:
```json
{
  "name": "contato_favorito",
  "label": "Contato Favorito",
  "type": "search",
  "datasource": "contatos",
  "required": false
}
```

#### Campos de Data/Hora:
```json
{
  "name": "data_nascimento",
  "label": "Data de Nascimento",
  "type": "date",
  "required": true
},
{
  "name": "horario",
  "label": "Horário",
  "type": "time",
  "required": false
},
{
  "name": "agendamento",
  "label": "Data e Hora",
  "type": "datetime-local",
  "required": false
}
```

### 5. Mensagens de Validação

O objeto `validation_messages` pode conter:

- `all_empty`: Mensagem quando todos os campos obrigatórios estão vazios
- `<nome_do_campo>`: Mensagem específica quando um campo obrigatório está vazio

## Exemplos

### Exemplo 1: Formulário de Contatos

Arquivo: `src/specs/contatos.json`

```json
{
  "title": "Agenda Pessoal",
  "fields": [
    {
      "name": "nome",
      "label": "Nome",
      "type": "text",
      "required": true
    },
    {
      "name": "telefone",
      "label": "Telefone",
      "type": "tel",
      "required": true
    },
    {
      "name": "whatsapp",
      "label": "WhatsApp",
      "type": "checkbox",
      "required": false
    }
  ]
}
```

Acesso: `http://localhost:5000/contatos`

### Exemplo 2: Formulário de Produtos

Arquivo: `src/specs/produtos.json`

```json
{
  "title": "Catálogo de Produtos",
  "fields": [
    {
      "name": "nome",
      "label": "Nome do Produto",
      "type": "text",
      "required": true
    },
    {
      "name": "categoria",
      "label": "Categoria",
      "type": "text",
      "required": true
    },
    {
      "name": "preco",
      "label": "Preço",
      "type": "number",
      "required": true
    },
    {
      "name": "descricao",
      "label": "Descrição",
      "type": "textarea",
      "required": false
    },
    {
      "name": "disponivel",
      "label": "Disponível",
      "type": "checkbox",
      "required": false
    }
  ]
}
```

Acesso: `http://localhost:5000/produtos`

## Armazenamento de Dados

Cada formulário tem seu próprio arquivo de dados em `src/<form_name>.txt`. Os dados são armazenados em formato delimitado por ponto-e-vírgula (;), com uma linha por registro.

Exemplo de `contatos.txt`:
```
João Silva;11999999999;True
Maria Santos;11988888888;False
```

## Rotas da API

Para cada formulário `<form_name>`, as seguintes rotas estão disponíveis:

- `GET /<form_name>`: Exibe o formulário e a lista de registros
- `POST /<form_name>`: Cria um novo registro
- `GET /<form_name>/edit/<idx>`: Exibe formulário de edição
- `POST /<form_name>/edit/<idx>`: Atualiza um registro
- `GET /<form_name>/delete/<idx>`: Deleta um registro

## Migração de Dados Existentes

Se você tinha dados no formato antigo (`registros.txt`), eles foram automaticamente copiados para `contatos.txt`. As rotas antigas (`/`, `/edit/<idx>`, `/delete/<idx>`) redirecionam para as novas rotas de contatos para manter compatibilidade.
