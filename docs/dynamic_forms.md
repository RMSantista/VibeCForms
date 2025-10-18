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

## Armazenamento de Dados (v3.0 - Sistema de Persistência Plugável)

A partir da versão 3.0, o VibeCForms suporta **múltiplos backends de armazenamento**. Você pode escolher onde seus dados serão armazenados sem alterar código, apenas configurando o arquivo `src/config/persistence.json`.

### Backends Suportados

#### 1. TXT (Padrão Original)
Arquivos de texto delimitados por ponto-e-vírgula.
- Localização: `src/<form_name>.txt`
- Formato: Uma linha por registro, campos separados por `;`
- Exemplo de `contatos.txt`:
  ```
  João Silva;11999999999;True
  Maria Santos;11988888888;False
  ```

#### 2. SQLite (Implementado)
Banco de dados embutido, zero configuração.
- Localização: `src/vibecforms.db`
- Cada formulário vira uma tabela
- Suporte a tipos (text, number, boolean, date)
- Melhor performance para múltiplos formulários

#### 3. Outros Backends (Configurados)
O sistema está preparado para suportar:
- **MySQL**: Banco relacional multiusuário
- **PostgreSQL**: Banco relacional avançado
- **MongoDB**: Banco NoSQL para dados semi-estruturados
- **CSV**: Arquivos CSV para integração com Excel
- **JSON**: Arquivos JSON para APIs
- **XML**: Arquivos XML para sistemas legados

### Configurando o Backend

Edite o arquivo `src/config/persistence.json`:

```json
{
  "version": "1.0",
  "default_backend": "txt",

  "form_mappings": {
    "contatos": "sqlite",    // Usar SQLite para contatos
    "produtos": "sqlite",    // Usar SQLite para produtos
    "usuarios": "txt",       // Usar TXT para usuários
    "*": "default_backend"   // Padrão para formulários não especificados
  }
}
```

**Exemplo**: Para usar SQLite para um formulário chamado "clientes":
```json
"form_mappings": {
  "clientes": "sqlite",
  "*": "default_backend"
}
```

### Migração Automática de Dados

Quando você altera o backend de um formulário (ex: TXT → SQLite), o sistema:
1. **Detecta a mudança** automaticamente
2. **Exibe tela de confirmação** com número de registros a migrar
3. **Cria backup** automático em `src/backups/migrations/`
4. **Migra todos os dados** preservando integridade
5. **Atualiza histórico** em `src/config/schema_history.json`

**Exemplo de migração bem-sucedida:**
- contatos: 23 registros migrados de TXT → SQLite
- produtos: 17 registros migrados de TXT → SQLite

### Como Migrar um Formulário

**Passo 1**: Verifique os dados atuais acessando o formulário

**Passo 2**: Edite `persistence.json` alterando o backend:
```json
"form_mappings": {
  "meu_formulario": "sqlite"  // Altere de "txt" para "sqlite"
}
```

**Passo 3**: Acesse o formulário no navegador

**Passo 4**: O sistema exibirá tela de confirmação:
- Backend origem: TXT
- Backend destino: SQLite
- Número de registros: X
- [Confirmar e Migrar]

**Passo 5**: Clique em "Confirmar e Migrar"
- Backup criado automaticamente
- Dados migrados
- Pronto para uso!

### Verificando o Backend Atual

Você pode verificar qual backend um formulário está usando consultando o arquivo `src/config/schema_history.json`:

```json
{
  "contatos": {
    "last_backend": "sqlite",
    "record_count": 23,
    "last_updated": "2025-10-16T17:29:30.878397"
  }
}
```

### Consulta Manual ao SQLite

Para consultar dados diretamente no SQLite:

```bash
# Via linha de comando
sqlite3 src/vibecforms.db "SELECT * FROM contatos;"

# Modo interativo
sqlite3 src/vibecforms.db
sqlite> .tables
sqlite> SELECT * FROM contatos;
sqlite> .quit
```

### Documentação Completa

Para informações detalhadas sobre configuração de backends, consulte:
- **[docs/Manual.md](Manual.md)**: Guia completo de configuração JSON
- **[CHANGELOG.md](../CHANGELOG.md)**: Detalhes da implementação v3.0

## Rotas da API

Para cada formulário `<form_name>`, as seguintes rotas estão disponíveis:

- `GET /<form_name>`: Exibe o formulário e a lista de registros
- `POST /<form_name>`: Cria um novo registro
- `GET /<form_name>/edit/<idx>`: Exibe formulário de edição
- `POST /<form_name>/edit/<idx>`: Atualiza um registro
- `GET /<form_name>/delete/<idx>`: Deleta um registro

## Migração de Dados Existentes

Se você tinha dados no formato antigo (`registros.txt`), eles foram automaticamente copiados para `contatos.txt`. As rotas antigas (`/`, `/edit/<idx>`, `/delete/<idx>`) redirecionam para as novas rotas de contatos para manter compatibilidade.
