# Manual de Configuração JSON - VibeCForms

Este manual explica todos os arquivos de configuração JSON utilizados no VibeCForms v3.0, incluindo o sistema de persistência plugável, especificações de formulários e configurações de pastas.

---

## Índice

1. [Sistema de Configuração](#sistema-de-configuração)
2. [Persistência: persistence.json](#persistência-persistencejson)
3. [Histórico de Schema: schema_history.json](#histórico-de-schema-schema_historyjson)
4. [Especificações de Formulários](#especificações-de-formulários)
5. [Configuração de Pastas: _folder.json](#configuração-de-pastas-_folderjson)
6. [Processo de Migração](#processo-de-migração)
7. [Exemplos Práticos](#exemplos-práticos)

---

## Sistema de Configuração

O VibeCForms utiliza arquivos JSON para configurar todos os aspectos do sistema sem necessidade de alterar código Python. Este design declarativo permite:

- **Flexibilidade**: Adicionar novos formulários apenas criando arquivos JSON
- **Manutenibilidade**: Configurações centralizadas e versionadas
- **Extensibilidade**: Suporte a múltiplos backends de persistência
- **Rastreabilidade**: Histórico automático de mudanças em schemas

### Localização dos Arquivos

```
VibeCForms/
├── src/
│   ├── config/
│   │   ├── persistence.json       # Configuração de backends
│   │   └── schema_history.json    # Histórico automático
│   └── specs/
│       ├── contatos.json          # Especificação de formulário
│       ├── produtos.json
│       ├── _folder.json           # Configuração de pasta (opcional)
│       └── financeiro/
│           ├── _folder.json
│           ├── contas.json
│           └── pagamentos.json
```

---

## Persistência: persistence.json

**Arquivo**: `src/config/persistence.json`

Este arquivo configura o sistema de persistência plugável, permitindo que diferentes formulários utilizem diferentes backends de armazenamento (TXT, SQLite, MySQL, PostgreSQL, MongoDB, CSV, JSON, XML).

### Estrutura Completa

```json
{
  "version": "1.0",
  "default_backend": "txt",

  "backends": {
    "txt": { /* configuração TXT */ },
    "sqlite": { /* configuração SQLite */ },
    "mysql": { /* configuração MySQL */ },
    "postgres": { /* configuração PostgreSQL */ },
    "mongodb": { /* configuração MongoDB */ },
    "csv": { /* configuração CSV */ },
    "json": { /* configuração JSON */ },
    "xml": { /* configuração XML */ }
  },

  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "sqlite",
    "*": "default_backend"
  },

  "auto_create_storage": true,
  "auto_migrate_schema": true,
  "backup_before_migrate": true,
  "backup_path": "src/backups/"
}
```

### Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `version` | string | Versão do formato de configuração |
| `default_backend` | string | Backend padrão para novos formulários |
| `backends` | object | Configurações de cada backend disponível |
| `form_mappings` | object | Mapeamento de formulários para backends |
| `auto_create_storage` | boolean | Criar armazenamento automaticamente se não existir |
| `auto_migrate_schema` | boolean | Migrar schema automaticamente quando detectar mudanças |
| `backup_before_migrate` | boolean | Criar backup antes de migrações |
| `backup_path` | string | Diretório para armazenar backups |

### Backends Suportados

#### 1. TXT (Arquivos de Texto)

```json
"txt": {
  "type": "txt",
  "path": "src/",
  "delimiter": ";",
  "encoding": "utf-8",
  "extension": ".txt"
}
```

**Campos**:
- `type`: Tipo do backend (sempre "txt")
- `path`: Diretório onde os arquivos serão salvos
- `delimiter`: Caractere separador de campos (padrão: ";")
- `encoding`: Codificação dos arquivos (padrão: "utf-8")
- `extension`: Extensão dos arquivos (padrão: ".txt")

**Uso**: Backend original, ideal para dados simples e portabilidade.

#### 2. SQLite (Banco de Dados Embutido)

```json
"sqlite": {
  "type": "sqlite",
  "database": "src/vibecforms.db",
  "timeout": 10,
  "check_same_thread": false
}
```

**Campos**:
- `type`: Tipo do backend (sempre "sqlite")
- `database`: Caminho do arquivo de banco de dados
- `timeout`: Timeout para operações em segundos
- `check_same_thread`: Permitir acesso de múltiplas threads

**Uso**: Ideal para aplicações com múltiplos formulários, oferece queries SQL e melhor performance.

#### 3. MySQL (Banco de Dados Relacional)

```json
"mysql": {
  "type": "mysql",
  "host": "localhost",
  "port": 3306,
  "database": "vibecforms",
  "user": "root",
  "password": "${MYSQL_PASSWORD}",
  "charset": "utf8mb4",
  "pool_size": 5
}
```

**Campos**:
- `type`: Tipo do backend (sempre "mysql")
- `host`: Endereço do servidor MySQL
- `port`: Porta do servidor (padrão: 3306)
- `database`: Nome do banco de dados
- `user`: Usuário de conexão
- `password`: Senha (suporta variáveis de ambiente com `${VAR}`)
- `charset`: Conjunto de caracteres (recomendado: "utf8mb4")
- `pool_size`: Tamanho do pool de conexões

**Uso**: Para ambientes multiusuário e integração com sistemas existentes.

#### 4. PostgreSQL (Banco de Dados Relacional Avançado)

```json
"postgres": {
  "type": "postgres",
  "host": "localhost",
  "port": 5432,
  "database": "vibecforms",
  "user": "postgres",
  "password": "${POSTGRES_PASSWORD}",
  "schema": "public",
  "pool_size": 5
}
```

**Campos**:
- `type`: Tipo do backend (sempre "postgres")
- `host`: Endereço do servidor PostgreSQL
- `port`: Porta do servidor (padrão: 5432)
- `database`: Nome do banco de dados
- `user`: Usuário de conexão
- `password`: Senha (suporta variáveis de ambiente)
- `schema`: Schema do banco (padrão: "public")
- `pool_size`: Tamanho do pool de conexões

**Uso**: Para aplicações críticas que requerem recursos avançados e conformidade.

#### 5. MongoDB (Banco NoSQL)

```json
"mongodb": {
  "type": "mongodb",
  "host": "localhost",
  "port": 27017,
  "database": "vibecforms",
  "user": "",
  "password": "${MONGO_PASSWORD}"
}
```

**Campos**:
- `type`: Tipo do backend (sempre "mongodb")
- `host`: Endereço do servidor MongoDB
- `port`: Porta do servidor (padrão: 27017)
- `database`: Nome do banco de dados
- `user`: Usuário de conexão (opcional)
- `password`: Senha (opcional, suporta variáveis de ambiente)

**Uso**: Para dados semi-estruturados e schemas flexíveis.

#### 6. CSV (Valores Separados por Vírgula)

```json
"csv": {
  "type": "csv",
  "path": "src/data/csv/",
  "delimiter": ",",
  "encoding": "utf-8",
  "quoting": "minimal"
}
```

**Campos**:
- `type`: Tipo do backend (sempre "csv")
- `path`: Diretório onde os arquivos CSV serão salvos
- `delimiter`: Caractere separador (padrão: ",")
- `encoding`: Codificação dos arquivos
- `quoting`: Estratégia de aspas ("minimal", "all", "nonnumeric", "none")

**Uso**: Para exportação/importação com Excel e outras ferramentas.

#### 7. JSON (JavaScript Object Notation)

```json
"json": {
  "type": "json",
  "path": "src/data/json/",
  "encoding": "utf-8",
  "indent": 2
}
```

**Campos**:
- `type`: Tipo do backend (sempre "json")
- `path`: Diretório onde os arquivos JSON serão salvos
- `encoding`: Codificação dos arquivos
- `indent`: Espaços de indentação para formatação (0 = compacto)

**Uso**: Para APIs, integração com JavaScript e legibilidade humana.

#### 8. XML (Extensible Markup Language)

```json
"xml": {
  "type": "xml",
  "path": "src/data/xml/",
  "encoding": "utf-8",
  "pretty_print": true
}
```

**Campos**:
- `type`: Tipo do backend (sempre "xml")
- `path`: Diretório onde os arquivos XML serão salvos
- `encoding`: Codificação dos arquivos
- `pretty_print`: Formatar com indentação para legibilidade

**Uso**: Para integração com sistemas legados e compatibilidade com padrões corporativos.

### Form Mappings (Mapeamento de Formulários)

O objeto `form_mappings` define qual backend cada formulário deve usar:

```json
"form_mappings": {
  "contatos": "sqlite",           // Formulário 'contatos' usa SQLite
  "produtos": "sqlite",           // Formulário 'produtos' usa SQLite
  "financeiro/contas": "postgres", // Formulário aninhado
  "*": "default_backend"          // Todos os demais usam backend padrão
}
```

**Regras**:
- Chaves são os nomes dos formulários (sem extensão .json)
- Valores são os nomes dos backends configurados
- `"*"` é o fallback para formulários não mapeados
- Suporta caminhos aninhados (ex: "financeiro/contas")

### Opções de Comportamento

```json
"auto_create_storage": true,      // Criar tabelas/arquivos automaticamente
"auto_migrate_schema": true,      // Migrar schemas automaticamente
"backup_before_migrate": true,    // Backup antes de migrações
"backup_path": "src/backups/"     // Diretório de backups
```

---

## Histórico de Schema: schema_history.json

**Arquivo**: `src/config/schema_history.json`

Este arquivo é **gerado e mantido automaticamente** pelo sistema. Ele rastreia o estado de cada formulário para detectar mudanças em schemas e backends.

### Estrutura

```json
{
  "contatos": {
    "last_spec_hash": "ee014237f822ba2d7ea15758cd6056dd",
    "last_backend": "sqlite",
    "last_updated": "2025-10-16T17:29:30.878397",
    "record_count": 23
  },
  "produtos": {
    "last_spec_hash": "8e699969d9a6b89b7fc69a8901a4b138",
    "last_backend": "sqlite",
    "last_updated": "2025-10-16T16:43:38.148813",
    "record_count": 17
  }
}
```

### Campos por Formulário

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `last_spec_hash` | string | Hash MD5 da última especificação conhecida |
| `last_backend` | string | Último backend utilizado |
| `last_updated` | string | Timestamp ISO 8601 da última atualização |
| `record_count` | integer | Número de registros no último acesso |

### Uso pelo Sistema

O sistema utiliza este arquivo para:

1. **Detectar Mudanças em Schema**: Compara hash atual com `last_spec_hash`
2. **Detectar Mudanças em Backend**: Compara backend atual com `last_backend`
3. **Confirmar Migrações**: Usa `record_count` para saber se há dados a migrar
4. **Prevenir Perda de Dados**: Solicita confirmação antes de operações destrutivas

**⚠️ IMPORTANTE**: Este arquivo não deve ser editado manualmente. Deixe o sistema gerenciá-lo automaticamente.

---

## Especificações de Formulários

**Arquivos**: `src/specs/*.json`

Cada formulário é definido por um arquivo JSON na pasta `specs/`. O sistema suporta estruturas hierárquicas criando subpastas.

### Estrutura Completa

```json
{
  "title": "Título do Formulário",
  "icon": "fa-icon-name",
  "fields": [
    {
      "name": "nome_campo",
      "label": "Rótulo Exibido",
      "type": "text",
      "required": true,
      "placeholder": "Texto de exemplo",
      "options": [],
      "min": 0,
      "max": 100,
      "step": 1
    }
  ],
  "validation_messages": {
    "all_empty": "Mensagem quando todos os campos estão vazios",
    "nome_campo": "Mensagem específica do campo"
  }
}
```

### Campos do Formulário

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `title` | ✅ Sim | Título exibido no cabeçalho do formulário |
| `icon` | ❌ Não | Ícone Font Awesome (ex: "fa-address-book") |
| `fields` | ✅ Sim | Array de campos do formulário |
| `validation_messages` | ❌ Não | Mensagens customizadas de validação |

### Tipos de Campo Suportados (20 tipos HTML5)

#### 1. Campos de Texto Básicos

**text** - Entrada de texto livre
```json
{
  "name": "nome",
  "label": "Nome Completo",
  "type": "text",
  "required": true,
  "placeholder": "Digite seu nome"
}
```

**email** - Entrada de e-mail com validação
```json
{
  "name": "email",
  "label": "E-mail",
  "type": "email",
  "required": true
}
```

**tel** - Entrada de telefone
```json
{
  "name": "telefone",
  "label": "Telefone",
  "type": "tel",
  "required": false,
  "placeholder": "(11) 99999-9999"
}
```

**url** - Entrada de URL com validação
```json
{
  "name": "website",
  "label": "Website",
  "type": "url",
  "required": false,
  "placeholder": "https://exemplo.com"
}
```

**password** - Entrada de senha (caracteres ocultos)
```json
{
  "name": "senha",
  "label": "Senha",
  "type": "password",
  "required": true
}
```

**search** - Campo de busca (pode ter datasource para autocomplete)
```json
{
  "name": "busca",
  "label": "Buscar",
  "type": "search",
  "datasource": "contatos",  // Opcional: autocomplete
  "required": false
}
```

#### 2. Campos Numéricos

**number** - Entrada numérica
```json
{
  "name": "idade",
  "label": "Idade",
  "type": "number",
  "required": true,
  "min": 0,
  "max": 120
}
```

**range** - Slider com valor numérico
```json
{
  "name": "prioridade",
  "label": "Prioridade",
  "type": "range",
  "min": 1,
  "max": 10,
  "step": 1,
  "required": false
}
```

#### 3. Campos de Data e Hora

**date** - Seletor de data
```json
{
  "name": "nascimento",
  "label": "Data de Nascimento",
  "type": "date",
  "required": true
}
```

**time** - Seletor de hora
```json
{
  "name": "horario",
  "label": "Horário",
  "type": "time",
  "required": false
}
```

**datetime-local** - Seletor de data e hora
```json
{
  "name": "agendamento",
  "label": "Data e Hora do Agendamento",
  "type": "datetime-local",
  "required": true
}
```

**month** - Seletor de mês e ano
```json
{
  "name": "mes_referencia",
  "label": "Mês de Referência",
  "type": "month",
  "required": false
}
```

**week** - Seletor de semana
```json
{
  "name": "semana",
  "label": "Semana",
  "type": "week",
  "required": false
}
```

#### 4. Campos de Seleção

**select** - Lista suspensa (dropdown)
```json
{
  "name": "estado",
  "label": "Estado",
  "type": "select",
  "required": true,
  "options": [
    {"value": "SP", "label": "São Paulo"},
    {"value": "RJ", "label": "Rio de Janeiro"},
    {"value": "MG", "label": "Minas Gerais"}
  ]
}
```

**radio** - Grupo de botões de opção
```json
{
  "name": "genero",
  "label": "Gênero",
  "type": "radio",
  "required": true,
  "options": [
    {"value": "M", "label": "Masculino"},
    {"value": "F", "label": "Feminino"},
    {"value": "O", "label": "Outro"}
  ]
}
```

**checkbox** - Caixa de seleção (booleano)
```json
{
  "name": "ativo",
  "label": "Ativo",
  "type": "checkbox",
  "required": false
}
```

#### 5. Campos de Texto Longo

**textarea** - Área de texto multilinha
```json
{
  "name": "descricao",
  "label": "Descrição",
  "type": "textarea",
  "required": false,
  "placeholder": "Digite uma descrição detalhada"
}
```

#### 6. Campos Especiais

**color** - Seletor de cor
```json
{
  "name": "cor_favorita",
  "label": "Cor Favorita",
  "type": "color",
  "required": false
}
```

**hidden** - Campo oculto (não exibido)
```json
{
  "name": "id_interno",
  "label": "ID Interno",
  "type": "hidden",
  "required": false
}
```

### Atributos Comuns dos Campos

| Atributo | Tipos | Descrição |
|----------|-------|-----------|
| `name` | Todos | Nome do campo (usado como chave no banco de dados) |
| `label` | Todos | Rótulo exibido ao usuário |
| `type` | Todos | Tipo do campo (um dos 20 tipos suportados) |
| `required` | Todos | Se o campo é obrigatório (true/false) |
| `placeholder` | text, email, tel, url, search, textarea | Texto de exemplo exibido quando vazio |
| `options` | select, radio | Array de opções com value e label |
| `min` | number, range | Valor mínimo permitido |
| `max` | number, range | Valor máximo permitido |
| `step` | number, range | Incremento/decremento |
| `datasource` | search | Nome do formulário para autocomplete |

### Mensagens de Validação

```json
"validation_messages": {
  "all_empty": "Por favor, preencha pelo menos um campo obrigatório.",
  "nome": "O nome é obrigatório.",
  "email": "Por favor, informe um e-mail válido.",
  "telefone": "O telefone é obrigatório."
}
```

- `all_empty`: Mensagem exibida quando todos os campos obrigatórios estão vazios
- `<nome_campo>`: Mensagem específica para cada campo obrigatório

---

## Configuração de Pastas: _folder.json

**Arquivos**: `src/specs/<pasta>/_folder.json`

Cada pasta dentro de `specs/` pode ter um arquivo `_folder.json` opcional para customizar sua aparência e comportamento no menu.

### Estrutura

```json
{
  "name": "Nome Exibido",
  "description": "Descrição opcional da pasta",
  "icon": "fa-icon-name",
  "order": 1
}
```

### Campos

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `name` | ❌ Não | Nome customizado exibido no menu (padrão: nome da pasta capitalizado) |
| `description` | ❌ Não | Descrição da categoria (para documentação) |
| `icon` | ❌ Não | Ícone Font Awesome (padrão: ícone genérico) |
| `order` | ❌ Não | Ordem de exibição no menu (menor = primeiro) |

### Exemplo Real: financeiro/_folder.json

```json
{
  "name": "Financeiro",
  "description": "Gestão financeira e contábil",
  "icon": "fa-dollar-sign",
  "order": 2
}
```

Sem `_folder.json`, a pasta "financeiro" apareceria como "Financeiro" (capitalizado) com ícone padrão.

### Exemplo Real: rh/_folder.json

```json
{
  "name": "Recursos Humanos",
  "description": "Gestão de pessoas e departamentos",
  "icon": "fa-users",
  "order": 1
}
```

Com `order: 1`, a pasta "Recursos Humanos" aparece antes de "Financeiro" (order: 2) no menu.

---

## Processo de Migração

O VibeCForms v3.0 inclui um sistema automático de migração que detecta mudanças em backends e schemas, solicitando confirmação quando há risco de perda de dados.

### Fluxo de Migração de Backend

1. **Detecção Automática**: Sistema compara `persistence.json` com `schema_history.json`
2. **Confirmação do Usuário**: Se houver dados, exibe tela de confirmação com:
   - Backend origem e destino
   - Número de registros a migrar
   - Aviso sobre backup automático
3. **Backup Automático**: Cria backup em `src/backups/migrations/`
4. **Migração de Dados**: Copia todos os registros para o novo backend
5. **Atualização do Histórico**: Atualiza `schema_history.json`

### Exemplo: TXT → SQLite

**Antes da migração** (`persistence.json`):
```json
"form_mappings": {
  "contatos": "txt",  // Usando TXT
  "*": "default_backend"
}
```

**Alterando para SQLite**:
```json
"form_mappings": {
  "contatos": "sqlite",  // Mudando para SQLite
  "*": "default_backend"
}
```

**Resultado**:
1. Sistema detecta mudança: TXT → SQLite
2. Verifica `schema_history.json`: contatos tem 23 registros
3. Exibe tela de confirmação: "Migrar 23 registros de TXT para SQLite?"
4. Usuário clica "Confirmar e Migrar"
5. Sistema cria backup: `src/backups/migrations/contatos_txt_to_sqlite_20251016_173045.txt`
6. Migra 23 registros para tabela SQLite `contatos`
7. Atualiza `schema_history.json`:
   ```json
   "contatos": {
     "last_backend": "sqlite",
     "record_count": 23,
     "last_updated": "2025-10-16T17:30:45.123456"
   }
   ```

### Detecção de Mudanças em Schema

O sistema também detecta mudanças na especificação do formulário:

**Tipos de Mudança**:
- ✅ **ADD_FIELD**: Campo adicionado (sem confirmação)
- ⚠️ **REMOVE_FIELD**: Campo removido (requer confirmação se há dados)
- ⚠️ **CHANGE_TYPE**: Tipo de campo alterado (requer confirmação)
- ⚠️ **CHANGE_REQUIRED**: Flag obrigatório alterado (pode causar problemas)

**Exemplo**: Adicionar campo "cpf" ao formulário "contatos"

```json
// contatos.json - ANTES
{
  "fields": [
    {"name": "nome", "type": "text"},
    {"name": "telefone", "type": "tel"}
  ]
}

// contatos.json - DEPOIS
{
  "fields": [
    {"name": "nome", "type": "text"},
    {"name": "telefone", "type": "tel"},
    {"name": "cpf", "type": "text"}  // NOVO CAMPO
  ]
}
```

**Resultado**: Sistema adiciona coluna "cpf" automaticamente (registros existentes terão valor vazio).

---

## Exemplos Práticos

### Exemplo 1: Criando um Novo Formulário com SQLite

**Passo 1**: Criar especificação `src/specs/clientes.json`
```json
{
  "title": "Cadastro de Clientes",
  "icon": "fa-user-tie",
  "fields": [
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "email", "label": "E-mail", "type": "email", "required": true},
    {"name": "telefone", "label": "Telefone", "type": "tel", "required": false},
    {"name": "ativo", "label": "Cliente Ativo", "type": "checkbox", "required": false}
  ],
  "validation_messages": {
    "all_empty": "Preencha pelo menos os campos obrigatórios.",
    "nome": "O nome do cliente é obrigatório.",
    "email": "Informe um e-mail válido."
  }
}
```

**Passo 2**: Configurar backend em `persistence.json`
```json
"form_mappings": {
  "clientes": "sqlite",  // Usar SQLite para clientes
  "*": "default_backend"
}
```

**Passo 3**: Acessar `/clientes` no navegador
- Sistema cria tabela automaticamente
- Formulário pronto para uso!

### Exemplo 2: Organizando Formulários em Pastas

**Estrutura**:
```
src/specs/
├── vendas/
│   ├── _folder.json
│   ├── pedidos.json
│   ├── orcamentos.json
│   └── clientes.json
```

**vendas/_folder.json**:
```json
{
  "name": "Gestão de Vendas",
  "description": "Pedidos, orçamentos e clientes",
  "icon": "fa-shopping-cart",
  "order": 1
}
```

**vendas/pedidos.json**:
```json
{
  "title": "Pedidos de Venda",
  "icon": "fa-file-invoice",
  "fields": [
    {"name": "numero", "label": "Número do Pedido", "type": "text", "required": true},
    {"name": "cliente", "label": "Cliente", "type": "search", "datasource": "clientes", "required": true},
    {"name": "data", "label": "Data", "type": "date", "required": true},
    {"name": "valor", "label": "Valor Total", "type": "number", "min": 0, "required": true},
    {"name": "status", "label": "Status", "type": "select", "required": true, "options": [
      {"value": "pendente", "label": "Pendente"},
      {"value": "aprovado", "label": "Aprovado"},
      {"value": "cancelado", "label": "Cancelado"}
    ]}
  ]
}
```

**Configurar em persistence.json**:
```json
"form_mappings": {
  "vendas/pedidos": "sqlite",
  "vendas/orcamentos": "sqlite",
  "vendas/clientes": "sqlite",
  "*": "default_backend"
}
```

### Exemplo 3: Formulário com Todos os Tipos de Campo

Ver arquivo completo em: `src/specs/formulario_completo.json`

Este exemplo demonstra os 20 tipos de campo suportados em um único formulário:

```json
{
  "title": "Formulário Demonstrativo Completo",
  "icon": "fa-clipboard-list",
  "fields": [
    {"name": "nome", "type": "text", "label": "Nome Completo"},
    {"name": "email", "type": "email", "label": "E-mail"},
    {"name": "telefone", "type": "tel", "label": "Telefone"},
    {"name": "website", "type": "url", "label": "Website"},
    {"name": "senha", "type": "password", "label": "Senha"},
    {"name": "busca", "type": "search", "label": "Buscar"},
    {"name": "idade", "type": "number", "label": "Idade", "min": 0, "max": 120},
    {"name": "prioridade", "type": "range", "label": "Prioridade", "min": 1, "max": 10},
    {"name": "nascimento", "type": "date", "label": "Data de Nascimento"},
    {"name": "horario", "type": "time", "label": "Horário"},
    {"name": "agendamento", "type": "datetime-local", "label": "Data e Hora"},
    {"name": "mes", "type": "month", "label": "Mês"},
    {"name": "semana", "type": "week", "label": "Semana"},
    {"name": "estado", "type": "select", "label": "Estado", "options": [...]},
    {"name": "genero", "type": "radio", "label": "Gênero", "options": [...]},
    {"name": "ativo", "type": "checkbox", "label": "Ativo"},
    {"name": "observacoes", "type": "textarea", "label": "Observações"},
    {"name": "cor", "type": "color", "label": "Cor Favorita"},
    {"name": "id_interno", "type": "hidden", "label": "ID Interno"}
  ]
}
```

### Exemplo 4: Migração Planejada MySQL → PostgreSQL

Para migrar um formulário de MySQL para PostgreSQL:

**Passo 1**: Verificar dados atuais
```bash
# Verificar quantos registros existem
curl http://localhost:5000/api/forms/clientes | jq 'length'
```

**Passo 2**: Configurar PostgreSQL em `persistence.json`
```json
"postgres": {
  "type": "postgres",
  "host": "localhost",
  "port": 5432,
  "database": "vibecforms_prod",
  "user": "postgres",
  "password": "${POSTGRES_PASSWORD}",
  "schema": "public"
}
```

**Passo 3**: Alterar mapeamento
```json
"form_mappings": {
  "clientes": "postgres",  // Mudado de "mysql" para "postgres"
  "*": "default_backend"
}
```

**Passo 4**: Acessar `/clientes`
- Sistema detecta mudança MySQL → PostgreSQL
- Exibe confirmação de migração
- Cria backup em `src/backups/migrations/`
- Migra todos os dados

---

## Resumo de Boas Práticas

### ✅ DO (Faça)

- Use `persistence.json` para configurar backends centralizadamente
- Deixe o sistema gerenciar `schema_history.json` automaticamente
- Use `_folder.json` para organizar categorias de formulários
- Configure backups automáticos antes de migrações
- Use variáveis de ambiente para senhas (`${VAR}`)
- Teste mudanças em ambiente de desenvolvimento primeiro
- Documente o propósito de cada formulário no campo `description` de pastas

### ❌ DON'T (Não Faça)

- Não edite `schema_history.json` manualmente
- Não altere backends em produção sem testar antes
- Não remova campos com dados sem backup
- Não commite senhas em `persistence.json` (use variáveis de ambiente)
- Não use o mesmo banco de dados para desenvolvimento e produção
- Não ignore avisos de confirmação de migração

---

## Referências

- **Documentação Completa**: Ver `docs/plano_persistencia.md`
- **Histórico de Implementação**: Ver `docs/prompts.md` (Prompts 20-23)
- **Testes Unitários**: Ver `tests/test_sqlite_adapter.py`, `test_backend_migration.py`, `test_change_detection.py`
- **Código Fonte**: Ver `src/persistence/` (adapters, migration_manager, schema_detector)

---

## Sistema de Workflow (v4.0)

O VibeCForms v4.0 introduz um **sistema completo de workflow baseado em Kanban** que se integra perfeitamente com os formulários existentes.

### Recursos Principais

- **Criação automática de processos** - Formulários vinculados a kanbans criam processos automaticamente
- **Gestão de estados** - Transições manuais e automáticas entre colunas
- **Regras de negócio** - Pré-requisitos e validações para transições
- **Inteligência artificial** - 4 agentes especializados, análise de padrões, detecção de anomalias
- **Machine Learning** - Previsão de duração de processos
- **Dashboard analytics** - Métricas em tempo real e identificação de gargalos
- **Exportação** - CSV, Excel e PDF
- **Auditoria** - Trilha completa para compliance

### Configuração

O sistema de workflow **não requer configuração adicional** - utiliza o mesmo sistema de persistência configurado em `persistence.json`. Processos são armazenados usando TXT ou SQLite automaticamente.

### Documentação

Para informações detalhadas sobre o sistema de workflow, consulte:

- **CLAUDE.md** - Seção "Workflow System (Version 4.0)" com arquitetura completa
- **CHANGELOG.md** - Seção "Version 4.0" com todas as features implementadas
- **README.md** - Overview do sistema de workflow
- **docs/workflow_phase*.md** - Sumários detalhados de cada fase de implementação
- **Testes**: `tests/test_kanban*.py`, `tests/test_prerequisite*.py`, `tests/test_auto_transition*.py` e outros (224 testes, 100% passando)

### REST API

Endpoints disponíveis em `/workflow/api/*`:
- `GET /workflow/api/kanbans` - Listar kanbans
- `GET /workflow/api/kanban/<kanban_id>` - Detalhes do kanban
- `POST /workflow/api/kanban` - Criar kanban
- `GET /workflow/api/processes` - Listar processos
- `GET /workflow/api/process/<process_id>` - Detalhes do processo
- `POST /workflow/api/process/<process_id>/transition` - Transicionar processo

---

**VibeCForms v4.0** - Sistema de Persistência Plugável + Workflow com Kanban
Última atualização: 2025-11-04
