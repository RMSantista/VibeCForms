# Guia de Inicialização - Sistema LIMS Refatorado

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.10+
- uv (gerenciador de pacotes)
- Dependências instaladas: `uv sync`

### 1. Iniciar o Servidor

```bash
# Dentro do diretório VibeCForms
uv run hatch run dev examples/analise-laboratorial
```

A aplicação iniciará em: **http://localhost:5000**

### 2. Acessar a Interface

Abra o navegador e acesse: **http://127.0.0.1:5000**

---

## 📋 O que Você Verá

### Menu Principal
15 formulários agrupados por categoria:

**Cadastros Básicos**
- Acreditadores (3 registros)
- Clientes (4 registros)
- Funcionários (8 registros)
- Metodologias (4 registros)

**Configuração de Amostras**
- Classificações (4 registros)
- Tipos de Amostra (4 registros)
- Amostras Específicas (6 registros)

**Análises**
- Análises (8 registros)
- Parciais/Etapas (3 registros)
- Matriz de Análises (8 registros)

**Fluxo de Processo**
- Orçamentos (4 registros - 4 estados)
- Amostras/Entrada (4 registros - 3 estados)
- Fracionamento (4 registros)
- Resultados (4 registros - 3 estados)
- Laudos (4 registros - 4 estados)

### Kanban Boards
4 workflows visuais para rastreamento de processos:

1. **ORCAMENTO** → Rascunho → Enviado → Aprovado → Em Andamento
2. **AMOSTRA** → Aguardando → Recebida → Fracionada
3. **RESULTADO** → Aguardando → Em Execução → Concluída
4. **LAUDO** → Rascunho → Revisão → Liberado → Entregue

---

## 🔍 Explorando os Dados

### Fluxo Completo de Exemplo

1. **Acesse ORCAMENTOS**
   - Veja 4 orçamentos em diferentes estados
   - Estado 1: Rascunho (pendente)
   - Estado 2: Enviado (em análise)
   - Estado 3: Aprovado (ok)
   - Estado 4: Em Andamento (em execução)

2. **Navegue para AMOSTRAS (Entrada)**
   - 4 amostras foram registradas
   - Relacionadas aos orçamentos aprovados
   - Contêm dados de recebimento

3. **Veja FRACIONAMENTO**
   - Cada amostra foi dividida em porções
   - Porções preparadas para análise
   - Matricula define tipo de análise

4. **Consulte RESULTADOS**
   - Análises executadas com sucesso
   - Alguns resultados com valores parciais
   - Exemplo: Acidez com volume, fator, resultado

5. **Revise LAUDOS**
   - Documentos finais emitidos
   - Pareceres de conformidade
   - Pronto para entrega ao cliente

---

## 🔗 Relacionamentos Importantes

### Hierarquia de Amostras
```
Acreditador (ex: MAPA)
└── Classificação (ex: Lácteos)
    └── Tipo Amostra (ex: Leite UHT)
        └── Amostra Específica (ex: Italac 1L)
```

### Fluxo de Processo
```
Orçamento (cliente solicita)
    ↓
Amostra (recebida no lab)
    ↓
Fracionamento (dividida em porções)
    ↓
Resultado (análise realizada)
    ↓
Laudo (documento emitido)
```

### Configuração de Análises
```
Matriz = Tipo Amostra + Análise + Metodologia + Preço
         ↓
         Define o que analisar e como
         ↓
         Resultado pode ter parciais (etapas intermediárias)
```

---

## 🎯 Funcionalidades para Testar

### 1. Criar Novo Registro
- Clique em qualquer formulário
- Preencha os campos obrigatórios (destacados)
- Campos com tipo "search" mostram autocomplete
- Clique "Salvar"

### 2. Buscar Registros
- Use a barra de busca em cada formulário
- Funciona para nomes, descrições, etc
- Case-insensitive

### 3. Editar/Deletar
- Clique em um registro na tabela
- Modifique os dados
- Clique "Atualizar" ou "Deletar"

### 4. Kanban Board
- Acesse http://localhost:5000/kanban
- Veja registros distribuídos por estado
- *(Drag-and-drop em desenvolvimento)*

### 5. Autocomplete (Busca)
- Em campos tipo "search", comece a digitar
- Aparecerão sugestões do banco
- Selecione uma opção

---

## 📊 Dados de Demonstração

### Exemplos Realistas Inclusos

**Clientes**
- Indústria de Laticínios Silva (5% desconto)
- Frigorífico Central Brasil (7% desconto)
- Distribuidora de Água Pura (3% desconto)
- Bebidas e Sucos Naturais (10% desconto)

**Análises com Parciais** (Acidez Titulável)
```
Parcial 1: Volume de NaOH (mL)
Parcial 2: Fator de Correção
Parcial 3: Normalidade da Solução
Resultado: Acidez em °D (graus Dornic)
Fórmula: (V × f × N × 100) / m
```

**Fluxo Exemplo**
- Orçamento da Indústria Silva (Estado: Enviado)
- Amostra: Leite Italac 1L (Recebida)
- Fracionamento: Porção para pH (Concluído)
- Resultado: pH 6.7 (Conforme padrão 6.4-6.8)
- Laudo: LAB/2026/001 (Liberado)

---

## 🛠️ Manutenção

### Resetar o Banco de Dados
```bash
# Remover banco antigo
rm examples/analise-laboratorial/data/sqlite/vibecforms.db

# Recriar tabelas
python3 examples/analise-laboratorial/scripts/create_tables.py

# Popular dados
python3 examples/analise-laboratorial/scripts/populate_demo_data.py
python3 examples/analise-laboratorial/scripts/populate_kanban_tags.py
```

### Scripts Disponíveis

1. **create_tables.py**
   - Cria 15 tabelas com schema SQL
   - Usa: `python3 scripts/create_tables.py`

2. **populate_demo_data.py**
   - Popula 77 registros realistas
   - Usa: `python3 scripts/populate_demo_data.py`

3. **populate_kanban_tags.py**
   - Cria tags para workflows
   - Usa: `python3 scripts/populate_kanban_tags.py`

---

## 📚 Documentação Completa

Para detalhes técnicos e arquitetura:
→ `RELATORIO_REFATORACAO_LIMS.md`

Para o plano de refatoração aprovado:
→ `/home/rodrigo/.claude/plans/transient-enchanting-journal.md`

---

## ❓ Suporte

### Erros Comuns

**"Banco vazio" ou "tabelas não encontradas"**
- Execute: `python3 scripts/create_tables.py`
- Depois: `python3 scripts/populate_demo_data.py`

**"Porta 5000 já em uso"**
- Feche aplicação anterior: `pkill -f "uv run"`
- Ou use porta alternativa: `uv run hatch run dev examples/analise-laboratorial -- --port 5001`

**"Relacionamentos não funcionam"**
- Certifique-se que o banco foi populado
- Verifique que `record_id` está presente
- Tente recarregar a página

---

## 🎉 Pronto!

O sistema está 100% operacional. Você pode:

✅ Explorar 77 registros de demonstração
✅ Testar fluxos completos de processo
✅ Criar novos registros
✅ Visualizar Kanban boards
✅ Usar buscas autocomplete

**Aproveite!**

Data: 07 de Janeiro de 2026
Sistema: VibeCForms LIMS Refatorado v2.0

