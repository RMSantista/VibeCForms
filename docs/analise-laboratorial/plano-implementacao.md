# Plano de Implementação: Sistema de Análises Laboratoriais
## VibeCForms - Controle de Qualidade de Água e Alimentos

**Data:** 2025-12-08
**Projeto:** /home/rodrigo/VibeCForms
**Business Case:** examples/analise-laboratorial/

---

## 📋 Sumário Executivo

Implementação completa de sistema de análises laboratoriais usando o framework VibeCForms, com 9 entidades principais, persistência SQLite, relacionamentos N:N automáticos e workflow com Kanban boards.

**Escopo Definido:**
- ✅ Sistema completo (todas 8 fases)
- ✅ Relacionamentos N:N gerenciados por código (não visíveis no menu)
- ✅ Workflow customizado com 3 Kanban boards
- ✅ Desenvolvimento paralelo (3-4 agentes simultâneos)

**Tempo Estimado:** 22-30 horas de implementação

---

## 🎯 Entidades do Sistema

### 1. Entidades Independentes (4)
Sem relacionamentos, podem ser criadas primeiro:
- **Clientes** - Nome, CPF/CNPJ, SIF, IMA
- **Acreditadores** - Nome do acreditador
- **Tipo de Amostra** - Tipo, Temperatura Padrão
- **Metodologias** - Metodologia, Bibliografia, Referência

### 2. Entidades com Relacionamentos 1:N (3)
Dependem das entidades independentes:
- **Matriz de Amostras** → Acreditadores
- **Análises** → Matriz de Amostras, Metodologias
- **Amostras** → Clientes, Tipo de Amostra

### 3. Entidades Complexas (2)
Hub do sistema com relacionamentos N:N:
- **Ordens de Serviço** → Clientes + N:N com Amostras e Análises
- **Resultados** → Ordens de Serviço, Análises

### 4. Relacionamentos N:N (Automáticos)
Gerenciados por código Python, não visíveis no menu:
- **ordens_amostras** - Vincula ordens a múltiplas amostras
- **ordens_analises** - Vincula ordens a múltiplas análises

---

## 🔄 Workflow e Estados

### Estados de Ordens de Serviço (5 estados)
```
orcamento → aprovado → em_analise → concluido → entregue
```

### Estados de Amostras (3 estados)
```
recebida → em_analise → finalizada
```

### Estados de Resultados (4 estados)
```
em_andamento → aguardando_revisao → aprovado → liberado
```

---

## 📁 Estrutura de Diretórios

```
/home/rodrigo/VibeCForms/examples/analise-laboratorial/
├── specs/
│   ├── _folder.json                  # Config: "Laboratório" icon="fa-flask"
│   ├── clientes.json                 # 6 campos
│   ├── acreditadores.json            # 3 campos
│   ├── tipo_amostra.json             # 3 campos
│   ├── metodologias.json             # 4 campos
│   ├── matriz_amostras.json          # 3 campos (search → acreditadores)
│   ├── analises.json                 # 6 campos (search → matriz, metodologias)
│   ├── amostras.json                 # 9 campos (search → clientes, tipo)
│   ├── ordens_servico.json           # 6 campos + gestão N:N via código
│   └── resultados.json               # 8 campos (search → ordens, analises)
│
├── config/
│   ├── persistence.json              # SQLite para todas entidades
│   └── kanban_boards.json            # 3 boards: OS, Amostras, Resultados
│
├── data/
│   └── sqlite/
│       └── vibecforms.db             # Banco SQLite (criado automaticamente)
│
└── backups/
    └── migrations/                   # Backups automáticos
```

**IMPORTANTE:** Não haverá pasta `specs/relacionamentos/` pois os relacionamentos N:N serão gerenciados automaticamente por código.

---

## 🛠️ Alterações de Código Necessárias

### Arquivo: `/home/rodrigo/VibeCForms/src/VibeCForms.py`

#### 1. Endpoints de Search API (≈200 linhas)
Adicionar após linha 782, seguindo padrão de `/api/search/contatos`:

```python
# 9 endpoints de search para autocomplete
@app.route("/api/search/clientes")
@app.route("/api/search/acreditadores")
@app.route("/api/search/matriz_amostras")
@app.route("/api/search/tipo_amostra")
@app.route("/api/search/metodologias")
@app.route("/api/search/amostras")
@app.route("/api/search/analises")
@app.route("/api/search/ordens_servico")
@app.route("/api/search/resultados")  # Opcional, caso precise
```

#### 2. Gestão de Relacionamentos N:N (≈150 linhas)
Adicionar funções para gerenciar tabelas intermediárias:

```python
# Funções auxiliares para relacionamentos N:N

def get_ordens_amostras(ordem_id):
    """Retorna amostras vinculadas a uma ordem."""
    # Query: SELECT * FROM ordens_amostras WHERE ordem_servico_id = ?

def add_amostra_to_ordem(ordem_id, amostra_id, quantidade):
    """Vincula amostra a ordem de serviço."""
    # INSERT INTO ordens_amostras VALUES (uuid, ordem_id, amostra_id, qtd)

def get_ordens_analises(ordem_id):
    """Retorna análises vinculadas a uma ordem."""

def add_analise_to_ordem(ordem_id, analise_id, valor_unitario):
    """Vincula análise a ordem de serviço."""

def remove_vinculo_amostra(ordem_id, amostra_id):
    """Remove vínculo amostra-ordem."""

def remove_vinculo_analise(ordem_id, analise_id):
    """Remove vínculo análise-ordem."""
```

#### 3. Interface de Gestão de Vínculos (≈100 linhas)
Adicionar rotas para gerenciar vínculos via interface web:

```python
@app.route("/<path:form_path>/vinculos/<record_id>", methods=["GET", "POST"])
def manage_vinculos(form_path, record_id):
    """Interface para gerenciar amostras e análises vinculadas a uma ordem."""
    if form_path == "ordens_servico":
        if request.method == "POST":
            # Processar vínculos de amostras e análises
            amostras_selecionadas = request.form.getlist("amostras[]")
            analises_selecionadas = request.form.getlist("analises[]")
            # ... adicionar vínculos

        # Renderizar template com multi-select de amostras e análises
        return render_template("vinculos.html", ...)
```

#### 4. Template de Vínculos (novo arquivo)
Criar `/home/rodrigo/VibeCForms/src/templates/vinculos.html`:
- Multi-select de amostras com autocomplete
- Multi-select de análises com autocomplete
- Lista atual de vínculos com opção de remover
- Cálculo automático de valor total

**Total de Código Novo:** ≈450 linhas Python + 1 template HTML (≈150 linhas)

---

## 📊 Configurações JSON

### persistence.json

```json
{
  "version": "1.0",
  "default_backend": "sqlite",
  "data_root": "data",

  "backends": {
    "sqlite": {
      "type": "sqlite",
      "database": "data/sqlite/vibecforms.db",
      "timeout": 10,
      "check_same_thread": false
    }
  },

  "form_mappings": {
    "clientes": "sqlite",
    "acreditadores": "sqlite",
    "matriz_amostras": "sqlite",
    "tipo_amostra": "sqlite",
    "metodologias": "sqlite",
    "analises": "sqlite",
    "amostras": "sqlite",
    "ordens_servico": "sqlite",
    "resultados": "sqlite",
    "*": "default_backend"
  },

  "auto_create_storage": true,
  "auto_migrate_schema": true,
  "backup_before_migrate": true,
  "backup_path": "backups/migrations/"
}
```

### kanban_boards.json

```json
{
  "boards": {
    "pipeline_laboratorio": {
      "title": "Pipeline de Ordens",
      "form": "ordens_servico",
      "columns": [
        {"tag": "orcamento", "label": "Orçamento", "color": "#6c757d"},
        {"tag": "aprovado", "label": "Aprovado", "color": "#17a2b8"},
        {"tag": "em_analise", "label": "Em Análise", "color": "#007bff"},
        {"tag": "concluido", "label": "Concluído", "color": "#28a745"},
        {"tag": "entregue", "label": "Entregue", "color": "#20c997"}
      ]
    },

    "fluxo_amostras": {
      "title": "Fluxo de Amostras",
      "form": "amostras",
      "columns": [
        {"tag": "recebida", "label": "Recebida", "color": "#6c757d"},
        {"tag": "em_analise", "label": "Em Análise", "color": "#007bff"},
        {"tag": "finalizada", "label": "Finalizada", "color": "#28a745"}
      ]
    },

    "aprovacao_resultados": {
      "title": "Aprovação de Resultados",
      "form": "resultados",
      "columns": [
        {"tag": "em_andamento", "label": "Em Andamento", "color": "#007bff"},
        {"tag": "aguardando_revisao", "label": "Aguardando Revisão", "color": "#ffc107"},
        {"tag": "aprovado", "label": "Aprovado", "color": "#6610f2"},
        {"tag": "liberado", "label": "Liberado", "color": "#28a745"}
      ]
    }
  }
}
```

---

## 🗄️ Schema do Banco de Dados

### Tabelas Principais (9)

Todas criadas automaticamente pelo SQLiteAdapter baseado nas specs JSON.

**UUIDs Crockford Base32** (27 caracteres) como chave primária lógica:
- Exemplo: `3HNMQR8PJSG0C9VWBYTE12K`
- URL-safe, human-readable, com checksum

### Tabelas de Relacionamento N:N (2)

Criadas via código Python:

```sql
CREATE TABLE ordens_amostras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE NOT NULL,
    ordem_servico_id TEXT NOT NULL,
    amostra_id TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ordens_analises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE NOT NULL,
    ordem_servico_id TEXT NOT NULL,
    analise_id TEXT NOT NULL,
    valor_unitario INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela de Tags (já existe)

```sql
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    applied_by TEXT NOT NULL,
    removed_at TEXT,
    removed_by TEXT,
    metadata TEXT
);
```

---

## 📝 TODO Detalhado por Fase

### ✅ FASE 1: Fundação (Entidades Independentes) - CONCLUÍDA
**Duração:** 2-3 horas | **Complexidade:** ⭐⭐☆☆☆

**Status:** ✅ **CONCLUÍDA EM 2025-12-10**

#### Tarefas Realizadas:
- ✅ **1.1** Estrutura de diretórios completa criada
- ✅ **1.2** persistence.json criado (SQLite para todas entidades)
- ✅ **1.3** specs/_folder.json criado (Laboratório, icon: fa-flask)
- ✅ **1.4** specs/clientes.json criado (6 campos)
- ✅ **1.5** specs/acreditadores.json criado (3 campos)
- ✅ **1.6** specs/tipo_amostra.json criado (3 campos + temperatura_conservacao)
- ✅ **1.7** specs/metodologias.json criado (5 campos + valor_referencia)
- ✅ **1.8** Aplicação executada com sucesso
- ✅ **1.9** Menu verificado com 4 entidades visíveis
- ✅ **1.10** Dados de teste cadastrados:
  - ✅ 3 clientes
  - ✅ 2 acreditadores
  - ✅ 5 tipos de amostra
  - ✅ 8 metodologias
- ✅ **1.11** SQLite verificado (4 tabelas criadas)
- ✅ **1.12** UUIDs Crockford Base32 de 27 caracteres validados
- ✅ **1.13** CRUD completo testado em todas entidades
- ✅ **1.14** schema_history.json criado automaticamente

#### Correções Críticas Realizadas:
- ✅ **SQLiteAdapter corrigido** para usar `record_id TEXT PRIMARY KEY` exclusivamente
- ✅ **7 métodos alterados:** create_storage, read_all, update, delete, rename_field, change_field_type, remove_field
- ✅ **test_delete_record corrigido** para ordenação alfabética de UUIDs
- ✅ **133 testes passando**, 4 skipped, 0 falhas

**Resultado Final da Fase 1:**
✅ 4 entidades funcionando perfeitamente
✅ CRUD completo testado
✅ Tabelas criadas no SQLite com UUIDs exclusivos
✅ Nenhum erro no console
✅ Zero regressões detectadas
✅ Sistema 100% funcional com UUID como chave primária

---

### 🔄 FASE 2: Relacionamentos 1:N + Endpoints API
**Duração:** 3-4 horas | **Complexidade:** ⭐⭐⭐☆☆

**Status:** ⏸️ **AGUARDANDO INÍCIO**

**Desenvolvimento Paralelo:** Usar 2 agentes em paralelo
- **Agente 1:** Adicionar 9 endpoints de search no VibeCForms.py
- **Agente 2:** Criar specs com campos search (matriz_amostras, analises, amostras)

#### Tarefas:

**Bloco 2.1: Endpoints API**
- [ ] **2.1** Adicionar endpoint `/api/search/clientes` em VibeCForms.py (após linha 782)
  ```python
  @app.route("/api/search/clientes")
  def api_search_clientes():
      query = request.args.get("q", "").strip().lower()
      if not query:
          return jsonify([])
      try:
          spec = load_spec("clientes")
          forms = read_forms(spec, "clientes")
          results = []
          for form in forms:
              nome = form.get("nome", "").lower()
              if query in nome:
                  results.append(form.get("nome", ""))
          return jsonify(results)
      except:
          return jsonify([])
  ```

- [ ] **2.2** Adicionar endpoints restantes (seguir mesmo padrão):
  - [ ] /api/search/acreditadores
  - [ ] /api/search/tipo_amostra
  - [ ] /api/search/metodologias
  - [ ] /api/search/matriz_amostras
  - [ ] /api/search/amostras
  - [ ] /api/search/analises
  - [ ] /api/search/ordens_servico

- [ ] **2.3** Testar endpoints via curl:
  ```bash
  curl "http://localhost:5000/api/search/clientes?q=teste"
  # Deve retornar JSON com lista de nomes
  ```

**Bloco 2.2: Specs com Relacionamentos 1:N**
- [ ] **2.4** Criar specs/matriz_amostras.json
  ```json
  {
    "fields": [
      {
        "name": "acreditador",
        "type": "search",
        "datasource": "acreditadores",
        "required": true
      },
      {"name": "grupo_amostra", "type": "text", "required": true}
    ]
  }
  ```

- [ ] **2.5** Criar specs/analises.json (6 campos)
  - Campo: matriz_amostra (search → matriz_amostras)
  - Campo: metodologia (search → metodologias)
  - Campo: tipo_analise (select: microbiologica, fisico_quimica)

- [ ] **2.6** Criar specs/amostras.json (9 campos)
  - Campo: cliente (search → clientes)
  - Campo: tipo_amostra (search → tipo_amostra)

**Bloco 2.3: Testes**
- [ ] **2.7** Cadastrar 3 matrizes de amostras (verificar autocomplete de acreditadores)

- [ ] **2.8** Cadastrar 10 análises (verificar autocomplete de matriz e metodologia)

- [ ] **2.9** Cadastrar 15 amostras (verificar autocomplete de cliente e tipo)

- [ ] **2.10** Verificar no SQLite que UUIDs estão sendo salvos (não textos):
  ```sql
  SELECT * FROM amostras LIMIT 3;
  -- Campo 'cliente' deve ter UUID de 27 chars
  ```

- [ ] **2.11** Testar edição de registros com relacionamentos

- [ ] **2.12** Validar integridade: todos os UUIDs devem existir nas tabelas referenciadas

**Critério de Sucesso:**
✅ Autocomplete funcionando em todos os campos search
✅ 7 entidades funcionando (4 antigas + 3 novas)
✅ UUIDs salvos corretamente (não nomes)
✅ Relacionamentos 1:N testados

---

### 🔄 FASE 3: Entidades Complexas (OS e Resultados)
**Duração:** 2-3 horas | **Complexidade:** ⭐⭐⭐☆☆

**Status:** ⏸️ **AGUARDANDO FASE 2**

**Desenvolvimento Paralelo:** Sequencial (1 agente)
- Depende das fases anteriores estarem completas

#### Tarefas:

- [ ] **3.1** Criar specs/ordens_servico.json (6 campos)
  ```json
  {
    "title": "Ordens de Serviço",
    "icon": "fa-file-invoice",
    "fields": [
      {"name": "cliente", "type": "search", "datasource": "clientes"},
      {"name": "data_criacao", "type": "date"},
      {"name": "quantidade_amostras", "type": "number"},
      {"name": "valor_total", "type": "number"},
      {"name": "aprovado", "type": "checkbox"},
      {"name": "observacoes", "type": "textarea"}
    ]
  }
  ```

- [ ] **3.2** Criar specs/resultados.json (8 campos)
  - Campo: ordem_servico (search → ordens_servico)
  - Campo: analise (search → analises)
  - Campo: inicio_analise (datetime-local)
  - Campo: termino_analise (datetime-local)
  - Campo: conforme (checkbox)

- [ ] **3.3** Cadastrar 5 ordens de serviço com diferentes clientes

- [ ] **3.4** Cadastrar 8 resultados vinculados a ordens e análises

- [ ] **3.5** Verificar integridade dos relacionamentos:
  ```sql
  SELECT o.*, c.nome AS cliente_nome
  FROM ordens_servico o
  JOIN clientes c ON o.cliente = c.record_id;
  ```

- [ ] **3.6** Testar campos datetime-local (início e término de análise)

- [ ] **3.7** Verificar cálculo de duração (término - início)

**Critério de Sucesso:**
✅ 9 entidades principais funcionando
✅ Ordens de serviço criadas e vinculadas a clientes
✅ Resultados vinculados a ordens e análises
✅ Todos relacionamentos 1:N validados

---

### 🔄 FASE 4: Relacionamentos N:N Automáticos
**Duração:** 5-6 horas | **Complexidade:** ⭐⭐⭐⭐☆

**Status:** ⏸️ **AGUARDANDO FASE 3**

**Desenvolvimento Paralelo:** Usar 2 agentes em paralelo
- **Agente 1:** Criar funções auxiliares para gestão de vínculos
- **Agente 2:** Criar interface web e template vinculos.html

#### Tarefas:

**Bloco 4.1: Tabelas de Relacionamento**
- [ ] **4.1** Criar script SQL para tabelas N:N:
  ```python
  # Adicionar em VibeCForms.py (função de inicialização)
  def create_relationship_tables():
      """Cria tabelas de relacionamento N:N se não existirem."""
      repo = RepositoryFactory.get_repository_by_type('sqlite')

      # Tabela ordens_amostras
      repo._execute("""
          CREATE TABLE IF NOT EXISTS ordens_amostras (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              record_id TEXT UNIQUE NOT NULL,
              ordem_servico_id TEXT NOT NULL,
              amostra_id TEXT NOT NULL,
              quantidade INTEGER NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
      """)

      # Tabela ordens_analises
      repo._execute("""
          CREATE TABLE IF NOT EXISTS ordens_analises (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              record_id TEXT UNIQUE NOT NULL,
              ordem_servico_id TEXT NOT NULL,
              analise_id TEXT NOT NULL,
              valor_unitario INTEGER NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
      """)

      # Índices para performance
      repo._execute("CREATE INDEX IF NOT EXISTS idx_oa_ordem ON ordens_amostras(ordem_servico_id)")
      repo._execute("CREATE INDEX IF NOT EXISTS idx_oan_ordem ON ordens_analises(ordem_servico_id)")
  ```

- [ ] **4.2** Chamar create_relationship_tables() na inicialização do app

- [ ] **4.3** Verificar tabelas criadas:
  ```bash
  sqlite3 data/sqlite/vibecforms.db ".schema ordens_amostras"
  ```

**Bloco 4.2: Funções Auxiliares**
- [ ] **4.4** Adicionar funções de gestão de vínculos em VibeCForms.py:

  ```python
  def get_amostras_da_ordem(ordem_id):
      """Retorna lista de amostras vinculadas."""
      repo = RepositoryFactory.get_repository_by_type('sqlite')
      query = """
          SELECT a.*, oa.quantidade
          FROM ordens_amostras oa
          JOIN amostras a ON oa.amostra_id = a.record_id
          WHERE oa.ordem_servico_id = ?
      """
      return repo._execute(query, (ordem_id,)).fetchall()

  def add_amostra_to_ordem(ordem_id, amostra_id, quantidade):
      """Vincula amostra a ordem."""
      repo = RepositoryFactory.get_repository_by_type('sqlite')
      record_id = generate_id()
      repo._execute("""
          INSERT INTO ordens_amostras (record_id, ordem_servico_id, amostra_id, quantidade)
          VALUES (?, ?, ?, ?)
      """, (record_id, ordem_id, amostra_id, quantidade))

  def get_analises_da_ordem(ordem_id):
      """Retorna análises vinculadas."""
      # Similar ao get_amostras_da_ordem

  def add_analise_to_ordem(ordem_id, analise_id, valor):
      """Vincula análise a ordem."""
      # Similar ao add_amostra_to_ordem

  def remove_amostra_da_ordem(ordem_id, amostra_id):
      """Remove vínculo."""
      repo = RepositoryFactory.get_repository_by_type('sqlite')
      repo._execute("""
          DELETE FROM ordens_amostras
          WHERE ordem_servico_id = ? AND amostra_id = ?
      """, (ordem_id, amostra_id))

  def calcular_valor_total_ordem(ordem_id):
      """Calcula valor total baseado nas análises vinculadas."""
      repo = RepositoryFactory.get_repository_by_type('sqlite')
      result = repo._execute("""
          SELECT SUM(valor_unitario) as total
          FROM ordens_analises
          WHERE ordem_servico_id = ?
      """, (ordem_id,)).fetchone()
      return result['total'] or 0
  ```

- [ ] **4.5** Testar funções auxiliares diretamente no console Python

**Bloco 4.3: Interface Web**
- [ ] **4.6** Adicionar rota para gestão de vínculos:
  ```python
  @app.route("/<path:form_path>/vinculos/<record_id>", methods=["GET", "POST"])
  def manage_vinculos(form_path, record_id):
      if form_path != "ordens_servico":
          return "Vínculos disponíveis apenas para ordens de serviço", 400

      if request.method == "POST":
          # Processar amostras selecionadas
          amostras = request.form.getlist("amostras[]")
          for amostra_id in amostras:
              quantidade = request.form.get(f"qtd_{amostra_id}", 1)
              add_amostra_to_ordem(record_id, amostra_id, quantidade)

          # Processar análises selecionadas
          analises = request.form.getlist("analises[]")
          for analise_id in analises:
              valor = request.form.get(f"valor_{analise_id}", 0)
              add_analise_to_ordem(record_id, analise_id, valor)

          # Atualizar valor total da ordem
          valor_total = calcular_valor_total_ordem(record_id)
          update_ordem_valor_total(record_id, valor_total)

          return redirect(f"/ordens_servico")

      # GET: Renderizar interface de vínculos
      ordem = read_ordem_by_id(record_id)
      amostras_disponiveis = read_all_amostras()
      analises_disponiveis = read_all_analises()
      amostras_vinculadas = get_amostras_da_ordem(record_id)
      analises_vinculadas = get_analises_da_ordem(record_id)

      return render_template("vinculos.html",
          ordem=ordem,
          amostras_disponiveis=amostras_disponiveis,
          analises_disponiveis=analises_disponiveis,
          amostras_vinculadas=amostras_vinculadas,
          analises_vinculadas=analises_vinculadas
      )
  ```

- [ ] **4.7** Criar template src/templates/vinculos.html (≈150 linhas):
  - Seção de amostras com multi-select + autocomplete
  - Seção de análises com multi-select + autocomplete
  - Lista atual de vínculos com botão "Remover"
  - Cálculo automático de valor total (JavaScript)

- [ ] **4.8** Modificar template form.html para adicionar botão "Gerenciar Vínculos" na tabela de ordens

**Bloco 4.4: Testes**
- [ ] **4.9** Criar 1 ordem de serviço

- [ ] **4.10** Acessar interface de vínculos: `/ordens_servico/vinculos/<UUID>`

- [ ] **4.11** Vincular 3 amostras à ordem

- [ ] **4.12** Verificar no SQLite:
  ```sql
  SELECT * FROM ordens_amostras WHERE ordem_servico_id = '<UUID>';
  ```

- [ ] **4.13** Vincular 5 análises à ordem

- [ ] **4.14** Verificar cálculo automático de valor total

- [ ] **4.15** Testar remoção de vínculo

- [ ] **4.16** Criar query de relatório:
  ```sql
  SELECT
      o.record_id AS ordem_id,
      c.nome AS cliente,
      a.nome_oficial AS analise,
      oa.valor_unitario
  FROM ordens_servico o
  JOIN clientes c ON o.cliente = c.record_id
  JOIN ordens_analises oa ON oa.ordem_servico_id = o.record_id
  JOIN analises a ON oa.analise_id = a.record_id;
  ```

- [ ] **4.17** Validar integridade referencial (todos UUIDs devem existir)

**Critério de Sucesso:**
✅ Tabelas N:N criadas e funcionando
✅ Interface web para gerenciar vínculos
✅ Ordem pode ter múltiplas amostras e análises
✅ Valor total calculado automaticamente
✅ Queries de relatório funcionando

---

### 🔄 FASE 5: Workflow e Kanban Boards
**Duração:** 3-4 horas | **Complexidade:** ⭐⭐⭐⭐☆

**Status:** ⏸️ **AGUARDANDO FASE 4**

**Desenvolvimento Paralelo:** Usar 2 agentes em paralelo
- **Agente 1:** Configurar kanban_boards.json
- **Agente 2:** Aplicar tags iniciais e testar transições

#### Tarefas:

**Bloco 5.1: Configuração**
- [ ] **5.1** Criar config/kanban_boards.json com 3 boards (conforme seção "Configurações JSON" acima)

- [ ] **5.2** Verificar que sistema de tags já existe (tabela tags no SQLite)

- [ ] **5.3** Reiniciar aplicação para carregar configuração

**Bloco 5.2: Testes de Workflow - Ordens**
- [ ] **5.4** Criar 10 ordens de serviço

- [ ] **5.5** Aplicar tags iniciais manualmente:
  ```python
  # Via console Python ou API
  from persistence.factory import RepositoryFactory
  repo = RepositoryFactory.get_repository('ordens_servico')

  # Aplicar tag "orcamento" a 5 ordens
  for ordem_id in ordem_ids[:5]:
      repo.add_tag('ordens_servico', ordem_id, 'orcamento', 'sistema')

  # Aplicar tag "aprovado" a 3 ordens
  for ordem_id in ordem_ids[5:8]:
      repo.add_tag('ordens_servico', ordem_id, 'aprovado', 'sistema')
  ```

- [ ] **5.6** Verificar tags no SQLite:
  ```sql
  SELECT * FROM tags WHERE object_type = 'ordens_servico';
  ```

- [ ] **5.7** Acessar Kanban board de ordens (verificar rota em VibeCForms.py)

- [ ] **5.8** Verificar ordens aparecem nas colunas corretas

- [ ] **5.9** Testar drag & drop entre colunas (orcamento → aprovado → em_analise)

- [ ] **5.10** Verificar transições de tags no banco após drag & drop

**Bloco 5.3: Testes de Workflow - Amostras**
- [ ] **5.11** Aplicar tags às 15 amostras criadas:
  - 5 amostras com tag "recebida"
  - 6 amostras com tag "em_analise"
  - 4 amostras com tag "finalizada"

- [ ] **5.12** Acessar board "Fluxo de Amostras"

- [ ] **5.13** Verificar distribuição nas 3 colunas

- [ ] **5.14** Testar transições: recebida → em_analise → finalizada

**Bloco 5.4: Testes de Workflow - Resultados**
- [ ] **5.15** Aplicar tags aos 8 resultados:
  - 2 com "em_andamento"
  - 3 com "aguardando_revisao"
  - 2 com "aprovado"
  - 1 com "liberado"

- [ ] **5.16** Acessar board "Aprovação de Resultados"

- [ ] **5.17** Testar fluxo completo de aprovação

**Bloco 5.5: Consultas e Estatísticas**
- [ ] **5.18** Testar consulta por tag:
  ```python
  ordens_em_analise = repo.get_objects_by_tag('ordens_servico', 'em_analise')
  print(f"Ordens em análise: {len(ordens_em_analise)}")
  ```

- [ ] **5.19** Verificar histórico de tags:
  ```sql
  SELECT
      object_id,
      tag,
      applied_at,
      applied_by,
      removed_at
  FROM tags
  WHERE object_type = 'ordens_servico'
  ORDER BY applied_at DESC;
  ```

- [ ] **5.20** Testar estatísticas:
  ```python
  stats = repo.get_tag_statistics('ordens_servico')
  print(stats)  # {'orcamento': 5, 'aprovado': 3, ...}
  ```

**Critério de Sucesso:**
✅ 3 Kanban boards funcionando
✅ Tags aplicadas corretamente
✅ Drag & drop funciona
✅ Histórico de tags registrado
✅ Consultas por tag funcionando

---

### 🔄 FASE 6: Testes e Validação
**Duração:** 4-5 horas | **Complexidade:** ⭐⭐⭐⭐⭐

**Status:** ⏸️ **AGUARDANDO FASE 5**

**Desenvolvimento Paralelo:** Usar 3 agentes em paralelo
- **Agente 1:** Executar testes do VibeCForms
- **Agente 2:** Criar dados de teste realistas
- **Agente 3:** Validar integridade e performance

#### Tarefas:

**Bloco 6.1: Testes Regressão**
- [ ] **6.1** Executar suite de testes do VibeCForms:
  ```bash
  cd /home/rodrigo/VibeCForms
  uv run pytest tests/ -v
  ```

- [ ] **6.2** Verificar que todos os 41 testes passam (regressão zero)

- [ ] **6.3** Se houver falhas, corrigir antes de prosseguir

**Bloco 6.2: Dados de Teste Volumosos**
- [ ] **6.4** Criar script create_test_data.py:
  ```python
  import requests
  import random
  from datetime import datetime, timedelta

  BASE_URL = "http://localhost:5000"

  # Criar 20 clientes
  clientes_ids = []
  for i in range(20):
      data = {
          "nome": f"Cliente Teste {i+1}",
          "cpf_cnpj": f"{random.randint(10000000000, 99999999999)}",
          "telefone": f"11{random.randint(900000000, 999999999)}"
      }
      # POST para criar cliente e coletar UUID retornado

  # Criar 10 acreditadores
  # Criar 30 tipos de amostra
  # Criar 50 metodologias
  # Criar 30 matrizes de amostras
  # Criar 100 análises
  # Criar 200 amostras
  # Criar 50 ordens de serviço
  # Criar 300 vínculos ordens↔amostras
  # Criar 400 vínculos ordens↔análises
  # Criar 150 resultados
  ```

- [ ] **6.5** Executar script:
  ```bash
  python create_test_data.py
  ```

- [ ] **6.6** Verificar totais no SQLite:
  ```sql
  SELECT
      'clientes' as tabela, COUNT(*) as total FROM clientes
  UNION ALL
  SELECT 'amostras', COUNT(*) FROM amostras
  UNION ALL
  SELECT 'ordens_servico', COUNT(*) FROM ordens_servico
  UNION ALL
  SELECT 'ordens_amostras', COUNT(*) FROM ordens_amostras;
  ```

**Bloco 6.3: Validação de Integridade**
- [ ] **6.7** Verificar integridade referencial (script SQL):
  ```sql
  -- Ordens sem cliente válido
  SELECT COUNT(*) FROM ordens_servico o
  WHERE NOT EXISTS (SELECT 1 FROM clientes c WHERE c.record_id = o.cliente);
  -- Deve retornar 0

  -- Amostras sem tipo válido
  SELECT COUNT(*) FROM amostras a
  WHERE NOT EXISTS (SELECT 1 FROM tipo_amostra t WHERE t.record_id = a.tipo_amostra);
  -- Deve retornar 0

  -- Vínculos órfãos
  SELECT COUNT(*) FROM ordens_amostras oa
  WHERE NOT EXISTS (SELECT 1 FROM ordens_servico o WHERE o.record_id = oa.ordem_servico_id)
     OR NOT EXISTS (SELECT 1 FROM amostras a WHERE a.record_id = oa.amostra_id);
  -- Deve retornar 0
  ```

- [ ] **6.8** Se houver inconsistências, corrigir manualmente

**Bloco 6.4: Performance**
- [ ] **6.9** Medir performance de queries:
  ```sql
  EXPLAIN QUERY PLAN
  SELECT * FROM ordens_servico WHERE cliente = '<UUID>';
  -- Deve usar índice idx_ordens_servico_record_id
  ```

- [ ] **6.10** Verificar índices criados:
  ```sql
  SELECT name, sql FROM sqlite_master WHERE type='index';
  ```

- [ ] **6.11** Medir tempo de autocomplete com 200 amostras:
  ```bash
  time curl "http://localhost:5000/api/search/amostras?q=teste"
  # Deve ser < 500ms
  ```

- [ ] **6.12** Medir tempo de carregamento de ordem com vínculos:
  ```bash
  time curl "http://localhost:5000/ordens_servico"
  # Deve ser < 1s
  ```

**Bloco 6.5: Testes Manuais**
- [ ] **6.13** Testar fluxo completo:
  1. Cadastrar cliente novo
  2. Cadastrar amostra para esse cliente
  3. Criar ordem de serviço para o cliente
  4. Vincular amostras e análises à ordem
  5. Aplicar tag "orcamento"
  6. Mover para "aprovado" via Kanban
  7. Registrar resultado
  8. Mover resultado por fluxo de aprovação

- [ ] **6.14** Testar em diferentes navegadores (Chrome, Firefox)

- [ ] **6.15** Verificar responsividade em mobile

**Critério de Sucesso:**
✅ Todos testes do VibeCForms passam
✅ Dados volumosos carregados sem erros
✅ Integridade referencial 100%
✅ Performance adequada (<1s para queries)
✅ Fluxo completo testado manualmente

---

### 🔄 FASE 7: Documentação
**Duração:** 2-3 horas | **Complexidade:** ⭐⭐☆☆☆

**Status:** ⏸️ **AGUARDANDO FASE 6**

**Desenvolvimento Paralelo:** Sequencial (1 agente)

#### Tarefas:

- [ ] **7.1** Criar README.md:
  ```markdown
  # Sistema de Análises Laboratoriais

  ## Visão Geral
  Sistema completo para laboratórios de análises de água e alimentos.

  ## Como Executar
  ```bash
  cd /home/rodrigo/VibeCForms
  uv run app examples/analise-laboratorial
  ```

  ## Entidades
  - 9 entidades principais
  - 2 tabelas de relacionamento N:N automáticas
  - 3 Kanban boards para workflow

  ## Workflow
  [Descrever estados e transições]
  ```

- [ ] **7.2** Criar MODELO_DADOS.md com diagrama ER

- [ ] **7.3** Documentar endpoints API customizados

- [ ] **7.4** Criar QUERIES_UTEIS.md com consultas SQL frequentes:
  - Ordens de um cliente
  - Análises de uma ordem
  - Amostras de uma ordem
  - Histórico de workflow
  - Resultados pendentes de revisão

- [ ] **7.5** Documentar funções de gestão de vínculos

- [ ] **7.6** Criar guia de usuário básico (PDF ou MD)

- [ ] **7.7** Adicionar screenshots do sistema

- [ ] **7.8** Criar CHANGELOG.md

**Critério de Sucesso:**
✅ README completo e claro
✅ Modelo de dados documentado
✅ Queries úteis documentadas
✅ Sistema pronto para uso

---

### 🔄 FASE 8: Refinamentos e Melhorias
**Duração:** 2-3 horas | **Complexidade:** ⭐⭐⭐☆☆

**Status:** ⏸️ **AGUARDANDO FASE 7**

**Desenvolvimento Paralelo:** Usar 2 agentes em paralelo
- **Agente 1:** Implementar validações adicionais
- **Agente 2:** Criar relatórios e dashboards

#### Tarefas (Opcionais):

**Bloco 8.1: Validações**
- [ ] **8.1** Validar CPF/CNPJ em clientes

- [ ] **8.2** Validar temperatura dentro de range esperado

- [ ] **8.3** Alertar se data de validade < data de entrada

- [ ] **8.4** Impedir deletar ordem com vínculos

**Bloco 8.2: Relatórios**
- [ ] **8.5** Endpoint `/api/relatorios/ordens_status`:
  ```python
  @app.route("/api/relatorios/ordens_status")
  def relatorio_status_ordens():
      repo = RepositoryFactory.get_repository('ordens_servico')
      stats = repo.get_tag_statistics('ordens_servico')
      return jsonify(stats)
  ```

- [ ] **8.6** Endpoint `/api/dashboard/metricas`:
  - Total de ordens ativas
  - Ordens por cliente
  - Análises mais solicitadas
  - Amostras por tipo

- [ ] **8.7** Criar página de dashboard simples

**Bloco 8.3: UX**
- [ ] **8.8** Adicionar tooltips explicativos

- [ ] **8.9** Melhorar mensagens de validação

- [ ] **8.10** Adicionar confirmação antes de deletar

**Critério de Sucesso:**
✅ Validações adicionais funcionando
✅ Relatórios básicos disponíveis
✅ UX aprimorada

---

## 🚀 Estratégia de Desenvolvimento Paralelo

### Configuração de 3-4 Agentes Simultâneos

**FASE 1 (3 agentes):**
```
Agente A: Estrutura + Clientes + Acreditadores
Agente B: Tipo Amostra + Metodologias
Agente C: Configurações (persistence.json, _folder.json)
```

**FASE 2 (2 agentes):**
```
Agente A: 9 endpoints de search
Agente B: Specs com relacionamentos 1:N
```

**FASE 4 (2 agentes):**
```
Agente A: Funções auxiliares de vínculos
Agente B: Interface web + template
```

**FASE 5 (2 agentes):**
```
Agente A: Configuração Kanban
Agente B: Aplicação de tags e testes
```

**FASE 6 (3 agentes):**
```
Agente A: Testes regressão
Agente B: Criar dados de teste
Agente C: Validação integridade
```

---

## 📊 Progresso e Métricas

### Estimativas de Tempo

| Fase | Duração | Complexidade | Agentes | Status |
|------|---------|--------------|---------|--------|
| 1. Fundação | 2-3h | ⭐⭐☆☆☆ | 3 | ✅ CONCLUÍDA |
| 2. Relacionamentos 1:N | 3-4h | ⭐⭐⭐☆☆ | 2 | ⏸️ Aguardando |
| 3. Entidades Complexas | 2-3h | ⭐⭐⭐☆☆ | 1 | ⏸️ Aguardando |
| 4. Relacionamentos N:N | 5-6h | ⭐⭐⭐⭐☆ | 2 | ⏸️ Aguardando |
| 5. Workflow Kanban | 3-4h | ⭐⭐⭐⭐☆ | 2 | ⏸️ Aguardando |
| 6. Testes | 4-5h | ⭐⭐⭐⭐⭐ | 3 | ⏸️ Aguardando |
| 7. Documentação | 2-3h | ⭐⭐☆☆☆ | 1 | ⏸️ Aguardando |
| 8. Refinamentos | 2-3h | ⭐⭐⭐☆☆ | 2 | ⏸️ Aguardando |
| **TOTAL** | **23-31h** | | | **12.5% Completo** |

### Métricas de Sucesso

- ✅ 4/9 entidades principais funcionando
- ✅ SQLite com UUIDs Crockford
- ⏸️ Relacionamentos 1:N via campo search (pendente)
- ⏸️ Relacionamentos N:N automáticos funcionando (pendente)
- ⏸️ 3 Kanban boards operacionais (pendente)
- ⏸️ Sistema de tags rastreando workflow (pendente)
- ✅ Todos 133 testes do VibeCForms passando
- ⏸️ Performance < 1s para queries principais (a validar)
- ✅ Integridade referencial 100% (Fase 1)
- ⏸️ Documentação completa (pendente)

---

## ⚠️ Riscos e Mitigações

### Risco 1: Relacionamentos N:N Automáticos
**Impacto:** Alto | **Probabilidade:** Média

**Problema:** Código customizado para N:N pode ser complexo

**Mitigação:**
- Criar funções bem isoladas e testadas
- Usar transactions para garantir consistência
- Implementar rollback em caso de erro
- Testar exaustivamente antes de avançar

### Risco 2: Performance com Dados Volumosos
**Impacto:** Médio | **Probabilidade:** Baixa

**Problema:** Autocomplete pode ficar lento com >1000 registros

**Mitigação:**
- Limitar retorno a 50 primeiros resultados
- Adicionar cache se necessário
- Implementar paginação nos endpoints
- Considerar migração para PostgreSQL se necessário

### Risco 3: Integridade Referencial
**Impacto:** Alto | **Probabilidade:** Baixa

**Problema:** SQLite com TEXT não garante foreign keys

**Mitigação:**
- Validação rigorosa na camada de aplicação
- Script de validação periódica
- Considerar triggers SQLite se necessário
- Testar deleções em cascata manualmente

---

## 📁 Arquivos Críticos

### Para Modificar
1. `/home/rodrigo/VibeCForms/src/VibeCForms.py` - Adicionar ≈450 linhas
2. `/home/rodrigo/VibeCForms/src/templates/vinculos.html` - Criar novo (≈150 linhas)
3. `/home/rodrigo/VibeCForms/src/templates/form.html` - Adicionar botão "Vínculos" (≈10 linhas)

### Para Criar (Specs JSON - 11 arquivos)
4. `/examples/analise-laboratorial/specs/_folder.json` ✅
5. `/examples/analise-laboratorial/specs/clientes.json` ✅
6. `/examples/analise-laboratorial/specs/acreditadores.json` ✅
7. `/examples/analise-laboratorial/specs/tipo_amostra.json` ✅
8. `/examples/analise-laboratorial/specs/metodologias.json` ✅
9. `/examples/analise-laboratorial/specs/matriz_amostras.json` ⏸️
10. `/examples/analise-laboratorial/specs/analises.json` ⏸️
11. `/examples/analise-laboratorial/specs/amostras.json` ⏸️
12. `/examples/analise-laboratorial/specs/ordens_servico.json` ⏸️
13. `/examples/analise-laboratorial/specs/resultados.json` ⏸️

### Para Criar (Configurações - 2 arquivos)
14. `/examples/analise-laboratorial/config/persistence.json` ✅
15. `/examples/analise-laboratorial/config/kanban_boards.json` ⏸️

### Para Referência
- `/home/rodrigo/VibeCForms/src/templates/fields/search_autocomplete.html` - Padrão de search
- `/home/rodrigo/VibeCForms/src/persistence/adapters/sqlite_adapter.py` ✅ - Operações SQLite (CORRIGIDO)
- `/home/rodrigo/VibeCForms/CLAUDE.md` - Convenções do framework

---

## ✅ Checklist Geral de Aprovação

Antes de considerar o projeto concluído:

- [x] Fase 1 completa ✅
- [ ] Todas as 8 fases completas
- [x] Todos os testes passando (133 originais) ✅
- [x] Sistema rodando sem erros (Fase 1) ✅
- [x] Dados de teste realistas carregados (19 registros) ✅
- [ ] Performance validada
- [x] Integridade referencial verificada (Fase 1) ✅
- [ ] Documentação completa
- [ ] README criado
- [ ] Usuário homologou o sistema

---

## 🎓 Próximos Passos Pós-Implementação

### Curto Prazo (após entrega)
- Treinamento de usuários
- Ajustes baseados em feedback
- Correção de bugs descobertos em produção

### Médio Prazo (1-3 meses)
- Relatórios customizados
- Exportação para PDF
- Dashboard com métricas
- Validação avançada de CPF/CNPJ

### Longo Prazo (3-6 meses)
- Migração para PostgreSQL (se necessário)
- Sistema de autenticação
- API RESTful completa
- Aplicativo mobile

---

**Fim do Plano de Implementação**

Este plano está pronto para execução. Todas as decisões arquiteturais foram tomadas e validadas com o usuário.

**Status Atual:** Fase 1 concluída com 100% de sucesso. Próximo passo: iniciar Fase 2 (Relacionamentos 1:N + Endpoints API).
