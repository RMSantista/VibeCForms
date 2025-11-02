# Sistema de Workflow Kanban - VibeCForms v4.0
## Planejamento Completo com IA, Analytics e Visual Editor
## PARTE 2: Editor Visual, Exportações e Arquitetura

**Versão:** 4.0 - Parte 2 de 3
**Data:** Outubro 2025
**Autor:** Rodrigo Santista (com assistência de Claude Code)

---

## Índice - Parte 2

9. [Editor Visual de Kanbans (Área Admin)](#9-editor-visual-de-kanbans-área-admin)
10. [Exportações e Relatórios](#10-exportações-e-relatórios)
11. [Interface de Auditoria Visual](#11-interface-de-auditoria-visual)
12. [Arquitetura Técnica Completa](#12-arquitetura-técnica-completa)

**Parte 1:** Fundamentos, Arquitetura Core, IA (Seções 1-8)
**Parte 3:** Exemplo Completo, Implementação, Testes (Seções 13-15)

---

## 9. Editor Visual de Kanbans (Área Admin)

### 9.1 Visão Geral do Editor Visual

O **Editor Visual de Kanbans** é uma funcionalidade CRÍTICA que estava ausente na v3.0. Permite criar e editar Kanbans completos através de uma interface web intuitiva, **sem precisar editar JSON manualmente**.

```
+------------------------------------------------------------------+
|                    Editor Visual de Kanbans                      |
+------------------------------------------------------------------+
|                                                                  |
|  ANTES (v3.0):                                                   |
|  ✏️ Editar arquivo JSON manualmente                             |
|  ❌ Propenso a erros de sintaxe                                 |
|  ❌ Difícil para usuários não técnicos                          |
|  ❌ Sem validação em tempo real                                 |
|                                                                  |
|  AGORA (v4.0):                                                   |
|  🎨 Interface visual drag-and-drop                              |
|  ✅ Validação em tempo real                                     |
|  ✅ Preview do Kanban antes de salvar                           |
|  ✅ Acessível para qualquer usuário                             |
|  ✅ Salva JSON automaticamente                                  |
|                                                                  |
+------------------------------------------------------------------+
```

**Características principais:**

- **Zero código**: Criar Kanbans completos sem escrever JSON
- **Drag & Drop**: Organizar estados visualmente
- **Validação em tempo real**: Erros mostrados imediatamente
- **Preview**: Visualizar como ficará antes de salvar
- **Templates**: Começar com templates pré-configurados
- **Import/Export**: Importar Kanbans existentes ou exportar para JSON

### 9.2 Interface Web para Criar/Editar Kanbans SEM Editar JSON

#### 9.2.1 Tela Inicial - Lista de Kanbans

```
+------------------------------------------------------------------+
|  🔧 Administração de Kanbans                    [+ Novo Kanban]  |
+------------------------------------------------------------------+
|                                                                  |
|  Buscar: [________________] 🔍                                   |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 🛒 Fluxo de Pedidos                    [Editar] [Clone] │     |
|  ├────────────────────────────────────────────────────────┤     |
|  │ 4 estados • 2 formulários vinculados                   │     |
|  │ 127 processos ativos • 78% taxa de conclusão           │     |
|  │ Criado: 15/08/2025 • Atualizado: 27/10/2025            │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 📋 Gestão de Projetos                 [Editar] [Clone] │     |
|  ├────────────────────────────────────────────────────────┤     |
|  │ 6 estados • 3 formulários vinculados                   │     |
|  │ 45 processos ativos • 82% taxa de conclusão            │     |
|  │ Criado: 20/09/2025 • Atualizado: 25/10/2025            │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 👥 RH - Contratação                   [Editar] [Clone] │     |
|  ├────────────────────────────────────────────────────────┤     |
|  │ 5 estados • 1 formulário vinculado                     │     |
|  │ 12 processos ativos • 91% taxa de conclusão            │     |
|  │ Criado: 05/10/2025 • Atualizado: 26/10/2025            │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
+------------------------------------------------------------------+
```

#### 9.2.2 Tela de Criação - Informações Básicas

```
+------------------------------------------------------------------+
|  📝 Criar Novo Kanban                          [Salvar] [Preview]|
+------------------------------------------------------------------+
|                                                                  |
|  Passo 1 de 4: Informações Básicas                              |
|  [●────────────────]                                            |
|                                                                  |
|  ID do Kanban:                                                   |
|  [pedidos________________]                                       |
|  ℹ️ Identificador único (letras minúsculas, números, underscore)|
|                                                                  |
|  Nome do Kanban:                                                 |
|  [Fluxo de Pedidos_______]                                       |
|                                                                  |
|  Descrição:                                                      |
|  [________________________________________________]               |
|  [Gerenciamento do ciclo completo de pedidos     ]               |
|  [de clientes, desde orçamento até entrega       ]               |
|                                                                  |
|  Ícone:                                                          |
|  [🛒 Selecionar Ícone ▼]                                        |
|  ┌────────────────────────────────────┐                         |
|  │ 🛒 fa-shopping-cart   📦 fa-box    │                         |
|  │ 📋 fa-clipboard       💼 fa-briefcase│                        |
|  │ 🎯 fa-bullseye        ⚙️ fa-cogs    │                         |
|  └────────────────────────────────────┘                         |
|                                                                  |
|  Estado Inicial:                                                 |
|  (Será definido após criar estados)                              |
|                                                                  |
|  [Cancelar]                               [Próximo: Estados →]  |
|                                                                  |
+------------------------------------------------------------------+
```

#### 9.2.3 Tela de Criação - Drag & Drop para Organizar Estados

```
+------------------------------------------------------------------+
|  📝 Criar Novo Kanban                          [Salvar] [Preview]|
+------------------------------------------------------------------+
|                                                                  |
|  Passo 2 de 4: Definir Estados                                  |
|  [●●────────────]                                               |
|                                                                  |
|  Arraste os estados para reordenar:                              |
|                                                                  |
|  ┌──────────────────┐  ┌──────────────────┐                     |
|  │ 1. Orçamento     │  │ 2. Pedido        │                     |
|  │    (Inicial)     │  │    Confirmado    │                     |
|  │                  │  │                  │                     |
|  │ 🎨 #6c757d       │  │ 🎨 #007bff       │                     |
|  │ 🔧 [Editar]      │  │ 🔧 [Editar]      │                     |
|  │ ❌ [Remover]     │  │ ❌ [Remover]     │                     |
|  └──────────────────┘  └──────────────────┘                     |
|                                                                  |
|  ┌──────────────────┐  ┌──────────────────┐                     |
|  │ 3. Em Entrega    │  │ 4. Concluído     │                     |
|  │                  │  │    (Final)       │                     |
|  │                  │  │                  │                     |
|  │ 🎨 #ffc107       │  │ 🎨 #28a745       │                     |
|  │ 🔧 [Editar]      │  │ 🔧 [Editar]      │                     |
|  │ ❌ [Remover]     │  │ ❌ [Remover]     │                     |
|  └──────────────────┘  └──────────────────┘                     |
|                                                                  |
|  [+ Adicionar Estado]                                            |
|                                                                  |
|  [← Voltar]                       [Próximo: Pré-requisitos →]   |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.3 Editor Visual de Transições

#### 9.3.1 Configuração de Transições por Estado

```
+------------------------------------------------------------------+
|  🔧 Editar Estado: "Pedido Confirmado"                [Salvar]   |
+------------------------------------------------------------------+
|                                                                  |
|  Aba: [Informações] [Pré-requisitos] [Transições] [Avançado]    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|  ABA: Transições                                                 |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  Transições Permitidas:                                          |
|                                                                  |
|  De: Pedido Confirmado                                           |
|                                                                  |
|  Para:                                                           |
|  ☑️ Orçamento (retrocesso)                                      |
|  ☑️ Em Entrega (avanço)                                         |
|  ☐ Concluído (pular estado)                                     |
|  ☐ Cancelado                                                     |
|                                                                  |
|  Regras de Transição:                                            |
|                                                                  |
|  ☑️ Permitir retrocesso                                         |
|  ☑️ Requerer justificativa em retrocessos                       |
|  ☐ Permitir pular estados                                       |
|  ☐ Requerer aprovação de supervisor                             |
|                                                                  |
|  Transição Automática (System):                                  |
|  ☑️ Habilitar auto-transição quando pré-requisitos satisfeitos  |
|                                                                  |
|  Próximo Estado Padrão: [Em Entrega ▼]                          |
|                                                                  |
|  [Cancelar]                                         [Salvar]     |
|                                                                  |
+------------------------------------------------------------------+
```

#### 9.3.2 Seleção de Tipo de Transição (System/Manual/Agent)

```
+------------------------------------------------------------------+
|  🔧 Editar Estado: "Pedido Confirmado"                [Salvar]   |
+------------------------------------------------------------------+
|                                                                  |
|  Aba: [Informações] [Pré-requisitos] [Transições] [Avançado]    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|  ABA: Avançado                                                   |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  Tipos de Transição Habilitados:                                |
|                                                                  |
|  ☑️ MANUAL                                                      |
|     Usuário pode mover processos arrastando no Kanban           |
|                                                                  |
|  ☑️ SYSTEM                                                      |
|     Sistema move automaticamente quando pré-requisitos OK       |
|     Configuração de cascata:                                     |
|     • Máximo de transições em cascata: [3__]                    |
|     • Delay entre transições (ms): [100_]                       |
|                                                                  |
|  ☑️ AGENT                                                       |
|     IA Agent analisa e sugere transições                        |
|     Agente configurado: [PedidoAgent ▼]                         |
|     Modo: ⦿ Sugestão (requer aprovação)                        |
|           ○ Automático (executa diretamente)                    |
|     Confiança mínima: [0.80_____] (0.0 - 1.0)                   |
|     Análise periódica: ☑️ A cada [1__] hora(s)                 |
|                                                                  |
|  Timeouts:                                                       |
|  [+ Adicionar Timeout]                                           |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ Timeout 1: Lembrete 24h                                 │    |
|  │ Após: [24] horas                                        │    |
|  │ Ação: [Enviar Notificação ▼]                           │    |
|  │ [🔧 Configurar]  [❌ Remover]                           │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  [Cancelar]                                         [Salvar]     |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.4 Configuração de Prerequisites

#### 9.4.1 Interface Visual de Pré-requisitos

```
+------------------------------------------------------------------+
|  🔧 Editar Estado: "Em Entrega"                       [Salvar]   |
+------------------------------------------------------------------+
|                                                                  |
|  Aba: [Informações] [Pré-requisitos] [Transições] [Avançado]    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|  ABA: Pré-requisitos                                             |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  Pré-requisitos para entrar neste estado:                       |
|                                                                  |
|  [+ Adicionar Pré-requisito]                                     |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 1. Pagamento Confirmado                      [⬆️] [⬇️]   │    |
|  │    Tipo: Field Check                          [❌ Remover]│    |
|  ├─────────────────────────────────────────────────────────┤    |
|  │ Campo: pagamento_recebido                               │    |
|  │ Condição: [Igual a ▼]                                   │    |
|  │ Valor: ☑️ true                                          │    |
|  │                                                         │    |
|  │ ☐ Bloqueante (impede transição)                        │    |
|  │ Mensagem: [Aguardando confirmação de pagamento]        │    |
|  │                                                         │    |
|  │ [🔧 Editar]                                             │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 2. Estoque Disponível                        [⬆️] [⬇️]   │    |
|  │    Tipo: External API                         [❌ Remover]│    |
|  ├─────────────────────────────────────────────────────────┤    |
|  │ API Endpoint: https://api.erp.com/check_stock          │    |
|  │ Método: [POST ▼]                                        │    |
|  │                                                         │    |
|  │ Payload:                                                │    |
|  │ {                                                       │    |
|  │   "produto_id": "{process_data.produto_id}",           │    |
|  │   "quantidade": "{process_data.quantidade}"            │    |
|  │ }                                                       │    |
|  │                                                         │    |
|  │ Resposta Esperada: {"available": true}                 │    |
|  │ Timeout: [5__] segundos                                │    |
|  │                                                         │    |
|  │ ☐ Bloqueante                                           │    |
|  │ Mensagem: [Produto fora de estoque]                    │    |
|  │                                                         │    |
|  │ [🔧 Editar]                                             │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  [Cancelar]                                         [Salvar]     |
|                                                                  |
+------------------------------------------------------------------+
```

#### 9.4.2 Modal de Adição de Pré-requisito

```
+------------------------------------------------------------------+
|  ➕ Adicionar Pré-requisito                           [✕ Fechar] |
+------------------------------------------------------------------+
|                                                                  |
|  Selecione o tipo de pré-requisito:                             |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 📝 Field Check                              [Selecionar]│     |
|  │    Verifica valor de campo do formulário               │     |
|  │    Exemplo: aprovado_cliente = true                    │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 🌐 External API                             [Selecionar]│     |
|  │    Consulta API externa para validação                 │     |
|  │    Exemplo: Verificar estoque no ERP                   │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ ⏱️ Time Elapsed                             [Selecionar]│     |
|  │    Verifica tempo decorrido desde evento               │     |
|  │    Exemplo: Mínimo 24h desde criação                   │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 💻 Custom Script                            [Selecionar]│     |
|  │    Executa script Python customizado                   │     |
|  │    Exemplo: Validação complexa de negócio              │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  [Cancelar]                                                      |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.5 Regras de Auto-Transição

```
+------------------------------------------------------------------+
|  ⚙️ Configurações de Auto-Transição                              |
+------------------------------------------------------------------+
|                                                                  |
|  Estado: Pedido Confirmado → Em Entrega                          |
|                                                                  |
|  ☑️ Habilitar Auto-Transição                                    |
|                                                                  |
|  Condições para Auto-Transição:                                  |
|                                                                  |
|  ⦿ Quando TODOS os pré-requisitos forem satisfeitos             |
|  ○ Quando QUALQUER pré-requisito for satisfeito                 |
|  ○ Customizado (expressão lógica)                               |
|                                                                  |
|  Expressão Customizada:                                          |
|  [(pagamento_recebido = true) AND (estoque_disponivel = true)]  |
|                                                                  |
|  Opções Avançadas:                                               |
|                                                                  |
|  ☑️ Habilitar Progressão em Cascata                             |
|     Continuar movendo se próximo estado também satisfaz         |
|     Máximo de estados em cascata: [3__]                         |
|     Delay entre transições: [100_] ms                           |
|                                                                  |
|  ☑️ Registrar Auditoria Detalhada                               |
|     Salva todos pré-requisitos verificados no histórico         |
|                                                                  |
|  ☑️ Notificar Usuário                                           |
|     Enviar notificação quando auto-transição ocorrer            |
|     Template: [Processo movido automaticamente ▼]               |
|                                                                  |
|  [Cancelar]                                         [Salvar]     |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.6 Vinculação Visual de Formulários

```
+------------------------------------------------------------------+
|  📝 Criar Novo Kanban                          [Salvar] [Preview]|
+------------------------------------------------------------------+
|                                                                  |
|  Passo 3 de 4: Vincular Formulários                             |
|  [●●●───────────]                                               |
|                                                                  |
|  Formulários vinculados a este Kanban:                           |
|                                                                  |
|  [+ Adicionar Formulário]                                        |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🛒 pedidos                                   [⬆️] [⬇️]   │    |
|  │                                               [❌ Remover]│    |
|  ├─────────────────────────────────────────────────────────┤    |
|  │ ☑️ Formulário Principal                                 │    |
|  │    (Usado ao clicar "Novo Processo" no Kanban)          │    |
|  │                                                         │    |
|  │ ☑️ Criar Processo Automaticamente                       │    |
|  │    (Ao salvar este formulário)                          │    |
|  │                                                         │    |
|  │ Estado Inicial: [Orçamento ▼]                          │    |
|  │                                                         │    |
|  │ Mapeamento de Campos:                                   │    |
|  │ Template de Título:                                     │    |
|  │ [Pedido #{id} - {cliente}___________________]           │    |
|  │                                                         │    |
|  │ Template de Descrição:                                  │    |
|  │ [{quantidade}x {produto} - R$ {valor_total}_]           │    |
|  │                                                         │    |
|  │ [🔧 Configurar Mapeamento Avançado]                     │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🚨 pedidos_urgentes                          [⬆️] [⬇️]   │    |
|  │                                               [❌ Remover]│    |
|  ├─────────────────────────────────────────────────────────┤    |
|  │ ☐ Formulário Principal                                  │    |
|  │ ☑️ Criar Processo Automaticamente                       │    |
|  │ Estado Inicial: [Pedido ▼] (pula Orçamento)            │    |
|  │                                                         │    |
|  │ Template de Título:                                     │    |
|  │ [🚨 URGENTE - Pedido #{id} - {cliente}_____]           │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  [← Voltar]                              [Próximo: Revisar →]   |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.7 Preview do Kanban

```
+------------------------------------------------------------------+
|  👁️ Preview: Fluxo de Pedidos                        [✕ Fechar] |
+------------------------------------------------------------------+
|                                                                  |
|  Visualização de como o Kanban aparecerá:                        |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 🛒 Fluxo de Pedidos                [+ Novo Processo]   │     |
|  ├────────────────┬────────────────┬────────────────────┐ │     |
|  │  Orçamento     │ Pedido         │ Em Entrega         │ │     |
|  │  (2)           │ Confirmado (3) │ (1)                │ │     |
|  ├────────────────┼────────────────┼────────────────────┤ │     |
|  │                │                │                    │ │     |
|  │ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐     │ │     |
|  │ │ Pedido #1  │ │ │ Pedido #2  │ │ │ Pedido #3  │     │ │     |
|  │ │ ACME Corp  │ │ │ XYZ Ltda   │ │ │ Beta Inc   │     │ │     |
|  │ │            │ │ │            │ │ │            │     │ │     |
|  │ │ ⚠️ Aguard.  │ │ │ ⚠️ Aguard.  │ │ │ ✅ Pronto  │     │ │     |
|  │ │ aprovação  │ │ │ pagamento  │ │ │            │     │ │     |
|  │ └────────────┘ │ └────────────┘ │ └────────────┘     │ │     |
|  │                │                │                    │ │     |
|  └────────────────┴────────────────┴────────────────────┴─┘     |
|                                                                  |
|  Configuração:                                                   |
|  • 4 estados definidos                                           |
|  • 2 formulários vinculados                                      |
|  • 3 tipos de transição habilitados (Manual, System, Agent)     |
|  • 5 pré-requisitos configurados                                 |
|  • 2 timeouts ativos                                             |
|                                                                  |
|  [Editar]                                      [Salvar Kanban]   |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.8 Validação em Tempo Real

O editor realiza validações conforme o usuário preenche:

```
+------------------------------------------------------------------+
|  ✅ Validações em Tempo Real                                     |
+------------------------------------------------------------------+
|                                                                  |
|  ✅ ID do Kanban:                                                |
|     • Único (não existe outro Kanban com este ID)               |
|     • Formato válido (apenas letras minúsculas, números, _)     |
|                                                                  |
|  ✅ Estados:                                                     |
|     • Pelo menos 2 estados definidos                            |
|     • IDs únicos entre estados                                  |
|     • Estado inicial configurado                                |
|     • Cores no formato hexadecimal válido                       |
|                                                                  |
|  ⚠️ Transições:                                                  |
|     • Estado "Pedido" não tem transições definidas              |
|       → Recomendação: Adicionar transição para "Entrega"        |
|                                                                  |
|  ✅ Pré-requisitos:                                              |
|     • Todos pré-requisitos têm tipo válido                      |
|     • Campos referenciados existem nos formulários              |
|     • APIs externas têm endpoints válidos                       |
|                                                                  |
|  ✅ Formulários:                                                 |
|     • Pelo menos 1 formulário vinculado                         |
|     • Formulários existem no sistema                            |
|     • Exatamente 1 marcado como principal                       |
|     • Templates de título/descrição têm sintaxe válida          |
|                                                                  |
|  ⚠️ Avisos:                                                      |
|     • Estado "Orçamento" sem timeout configurado                |
|       → Recomendação: Adicionar lembrete após 24h               |
|                                                                  |
|  Status: Pronto para salvar (2 avisos, 0 erros)                 |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.9 Templates de Kanban

O sistema oferece templates pré-configurados para começar rapidamente:

```
+------------------------------------------------------------------+
|  📋 Selecionar Template de Kanban                    [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Comece com um template ou crie do zero:                         |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 🛒 E-Commerce - Pedidos                    [Usar]      │     |
|  │                                                        │     |
|  │ Estados: Carrinho → Pedido → Pagamento → Envio →      │     |
|  │          Entregue                                      │     |
|  │                                                        │     |
|  │ Inclui:                                                │     |
|  │ • 5 estados pré-configurados                           │     |
|  │ • Pré-requisitos para pagamento e envio                │     |
|  │ • Auto-transição após confirmação                      │     |
|  │ • Timeouts para lembretes                              │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 📋 Gestão de Projetos (Scrum)             [Usar]      │     |
|  │                                                        │     |
|  │ Estados: Backlog → Sprint → Em Progresso → Review →   │     |
|  │          Concluído                                     │     |
|  │                                                        │     |
|  │ Inclui:                                                │     |
|  │ • 6 estados baseados em Scrum                          │     |
|  │ • Pré-requisitos para Definition of Done               │     |
|  │ • Timeouts para sprints (14 dias)                      │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 👥 RH - Recrutamento e Seleção             [Usar]      │     |
|  │                                                        │     |
|  │ Estados: Triagem → Entrevista → Teste Técnico →       │     |
|  │          Proposta → Contratado                         │     |
|  │                                                        │     |
|  │ Inclui:                                                │     |
|  │ • 5 estados do processo seletivo                       │     |
|  │ • Agents de IA para triagem                            │     |
|  │ • Timeouts para respostas de candidatos                │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ 📝 Simples (3 Estados)                     [Usar]      │     |
|  │                                                        │     |
|  │ Estados: A Fazer → Em Progresso → Concluído           │     |
|  │                                                        │     |
|  │ Kanban básico para começar do zero                     │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  ┌────────────────────────────────────────────────────────┐     |
|  │ ⚡ Em Branco                               [Usar]      │     |
|  │                                                        │     |
|  │ Criar Kanban completamente do zero                     │     |
|  └────────────────────────────────────────────────────────┘     |
|                                                                  |
|  [Cancelar]                                                      |
|                                                                  |
+------------------------------------------------------------------+
```

### 9.10 Salva como JSON Automaticamente

Quando o usuário clica "Salvar", o sistema:

1. **Valida** toda a configuração
2. **Gera JSON** automaticamente a partir dos dados da interface
3. **Salva** em `src/config/kanbans/<kanban_id>_kanban.json`
4. **Atualiza KanbanRegistry**
5. **Mostra mensagem** de sucesso

```python
class KanbanEditorController:
    """
    Controller para o Editor Visual de Kanbans.
    """

    def save_kanban(self, kanban_data: dict) -> dict:
        """
        Salva Kanban criado/editado no editor visual.

        Args:
            kanban_data: Dados do formulário do editor

        Returns:
            {
                "status": "success" | "error",
                "kanban_id": str,
                "message": str,
                "json_path": str
            }
        """
        # 1. Valida dados
        validator = KanbanValidator()
        validation_result = validator.validate(kanban_data)

        if not validation_result.is_valid:
            return {
                "status": "error",
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            }

        # 2. Converte dados do editor para formato JSON
        json_builder = KanbanJSONBuilder()
        kanban_json = json_builder.build(kanban_data)

        # 3. Salva arquivo JSON
        kanban_id = kanban_data['kanban_id']
        json_path = f"src/config/kanbans/{kanban_id}_kanban.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(kanban_json, f, indent=2, ensure_ascii=False)

        # 4. Atualiza KanbanRegistry
        registry = KanbanRegistry()
        registry.reload()

        # 5. Retorna sucesso
        return {
            "status": "success",
            "kanban_id": kanban_id,
            "message": f"Kanban '{kanban_data['title']}' salvo com sucesso!",
            "json_path": json_path,
            "warnings": validation_result.warnings
        }
```

---

## 10. Exportações e Relatórios

### 10.1 Export CSV: Processos, Transições, Analytics

#### 10.1.1 Exportar Processos

```
+------------------------------------------------------------------+
|  📥 Exportar Processos                               [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Kanban: [Fluxo de Pedidos ▼]                                   |
|                                                                  |
|  Período:                                                        |
|  De: [01/10/2025]  Até: [31/10/2025]                            |
|                                                                  |
|  Estados: ☑️ Todos                                              |
|           ☐ Selecionar estados específicos                      |
|                                                                  |
|  Incluir:                                                        |
|  ☑️ Dados do processo (ID, título, descrição)                   |
|  ☑️ Dados do formulário (process_data)                          |
|  ☑️ Estado atual                                                |
|  ☑️ Datas de criação e atualização                              |
|  ☑️ Usuário criador                                             |
|  ☑️ Formulário origem                                           |
|  ☐ Histórico completo de transições                            |
|                                                                  |
|  Formato:                                                        |
|  ⦿ CSV (Excel)                                                  |
|  ○ JSON                                                         |
|  ○ Excel (XLSX)                                                 |
|                                                                  |
|  [Cancelar]                              [Exportar]             |
|                                                                  |
+------------------------------------------------------------------+
```

**Exemplo de CSV gerado:**

```csv
process_id,kanban_id,title,description,current_state,created_at,created_by,source_form,source_form_id,cliente,produto,quantidade,valor_total,aprovado_cliente,pagamento_recebido
proc_pedidos_1730032800_42,pedidos,Pedido #42 - ACME Corp,10x Widget Premium - R$ 1500.00,concluido,2025-10-27T10:30:00,user123,pedidos,42,ACME Corp,Widget Premium,10,1500.00,true,true
proc_pedidos_1730033900_43,pedidos,Pedido #43 - XYZ Ltda,5x Gadget Pro - R$ 750.00,pedido,2025-10-27T11:45:00,user456,pedidos,43,XYZ Ltda,Gadget Pro,5,750.00,true,false
proc_pedidos_1730035000_44,pedidos,Pedido #44 - Beta Inc,20x Tool Standard - R$ 3000.00,entrega,2025-10-27T13:10:00,user789,pedidos,44,Beta Inc,Tool Standard,20,3000.00,true,true
```

#### 10.1.2 Exportar Transições

```csv
process_id,timestamp,action,from_state,to_state,actor,actor_type,trigger,forced,justification,prerequisites_not_met
proc_pedidos_1730032800_42,2025-10-27T10:30:00,created,null,orcamento,system,system,form_save,false,null,[]
proc_pedidos_1730032800_42,2025-10-28T14:30:00,auto_transitioned,orcamento,pedido,system,auto_transition,prerequisite_met,false,null,[]
proc_pedidos_1730032800_42,2025-10-28T18:00:00,auto_transitioned,pedido,entrega,system,auto_transition,prerequisite_met,false,null,[]
proc_pedidos_1730032800_42,2025-10-30T16:00:00,manual_transition,entrega,concluido,user123,user,drag_and_drop,false,null,[]
```

#### 10.1.3 Exportar Analytics

```csv
kanban_id,state,avg_duration_hours,median_duration_hours,process_count,min_duration_hours,max_duration_hours
pedidos,orcamento,18.5,12.0,207,2.0,72.0
pedidos,pedido,36.0,24.0,162,8.0,120.0
pedidos,entrega,48.0,36.0,152,12.0,144.0
```

### 10.2 Export PDF: Relatórios Formatados

```
+------------------------------------------------------------------+
|  📄 Gerar Relatório PDF                              [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Tipo de Relatório:                                              |
|  ⦿ Relatório Executivo (resumo gerencial)                       |
|  ○ Relatório Detalhado (análise completa)                       |
|  ○ Relatório de Processos (lista processos)                     |
|  ○ Relatório de Auditoria (histórico transições)                |
|                                                                  |
|  Kanban: [Fluxo de Pedidos ▼]                                   |
|                                                                  |
|  Período:                                                        |
|  [Últimos 30 dias ▼]                                             |
|                                                                  |
|  Incluir:                                                        |
|  ☑️ Capa com logo e informações                                 |
|  ☑️ Sumário executivo                                           |
|  ☑️ KPIs principais                                             |
|  ☑️ Gráficos (funil, linha do tempo, heatmap)                   |
|  ☑️ Tabela de processos                                         |
|  ☑️ Análise de gargalos                                         |
|  ☑️ Insights de IA                                              |
|  ☐ Histórico detalhado de cada processo                         |
|                                                                  |
|  Orientação: ⦿ Retrato  ○ Paisagem                             |
|                                                                  |
|  Template: [Padrão Corporativo ▼]                               |
|                                                                  |
|  [Cancelar]                              [Gerar PDF]            |
|                                                                  |
+------------------------------------------------------------------+
```

**Estrutura do PDF gerado:**

```
┌────────────────────────────────────────┐
│         RELATÓRIO EXECUTIVO            │
│       Fluxo de Pedidos - Outubro       │
│                                        │
│  [Logo da Empresa]                     │
│                                        │
│  Período: 01/10/2025 - 31/10/2025     │
│  Gerado em: 31/10/2025 18:30          │
└────────────────────────────────────────┘

                SUMÁRIO

1. KPIs Principais........................2
2. Análise de Volume......................3
3. Tempos por Estado......................4
4. Funil de Conversão.....................5
5. Gargalos Identificados.................6
6. Insights de IA.........................7
7. Recomendações..........................8
8. Apêndice: Tabela de Processos.........9

─────────────────────────────────────────

1. KPIs PRINCIPAIS

┌─────────────────────────────────────┐
│ Processos Criados:      207         │
│ Processos Concluídos:   162 (78.3%)│
│ Tempo Médio:            4.2 dias    │
│ Taxa de Sucesso:        88.9%       │
└─────────────────────────────────────┘

[Gráficos e detalhes...]
```

### 10.3 Agendamento de Relatórios

```python
class ReportScheduler:
    """
    Agendador de relatórios periódicos.
    """

    def schedule_report(
        self,
        kanban_id: str,
        report_type: str,
        frequency: str,
        recipients: list,
        config: dict
    ):
        """
        Agenda relatório periódico.

        Args:
            kanban_id: ID do Kanban
            report_type: "executive" | "detailed" | "audit"
            frequency: "daily" | "weekly" | "monthly"
            recipients: Lista de emails
            config: Configuração do relatório

        Exemplo de uso:
        >>> scheduler.schedule_report(
        ...     kanban_id="pedidos",
        ...     report_type="executive",
        ...     frequency="weekly",
        ...     recipients=["gerente@empresa.com", "diretor@empresa.com"],
        ...     config={
        ...         "format": "pdf",
        ...         "include_graphs": True,
        ...         "include_ai_insights": True
        ...     }
        ... )
        """
```

**Interface de agendamento:**

```
+------------------------------------------------------------------+
|  📅 Agendar Relatório                                [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Tipo: [Relatório Executivo ▼]                                  |
|  Kanban: [Fluxo de Pedidos ▼]                                   |
|                                                                  |
|  Frequência:                                                     |
|  ⦿ Diariamente                                                  |
|     Horário: [08:00]                                            |
|                                                                  |
|  ○ Semanalmente                                                 |
|     Dia: [Segunda-feira ▼]  Horário: [08:00]                   |
|                                                                  |
|  ○ Mensalmente                                                  |
|     Dia: [1 ▼]  Horário: [08:00]                               |
|                                                                  |
|  Destinatários:                                                  |
|  [gerente@empresa.com__________________] [+ Adicionar]          |
|  [diretor@empresa.com__________________] [❌]                   |
|                                                                  |
|  Formato: ⦿ PDF  ○ Excel  ○ Ambos                              |
|                                                                  |
|  Assunto do Email:                                               |
|  [Relatório Semanal - Fluxo de Pedidos__________]               |
|                                                                  |
|  Mensagem:                                                       |
|  [________________________________________________]               |
|  [Segue relatório semanal do fluxo de pedidos.   ]               |
|  [________________________________________________]               |
|                                                                  |
|  [Cancelar]                              [Agendar]              |
|                                                                  |
+------------------------------------------------------------------+
```

### 10.4 Templates Customizáveis

Relatórios podem usar templates personalizados:

```python
# templates/reports/custom_template.html

<!DOCTYPE html>
<html>
<head>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        .header {
            background-color: #007bff;
            color: white;
            padding: 20px;
        }
        .kpi-box {
            border: 2px solid #28a745;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ kanban_title }}</h1>
        <p>Relatório de {{ period_start }} a {{ period_end }}</p>
    </div>

    <div class="kpi-box">
        <h2>KPIs Principais</h2>
        <p>Processos: {{ total_processes }}</p>
        <p>Taxa de Conclusão: {{ completion_rate }}%</p>
        <p>Tempo Médio: {{ avg_duration }} dias</p>
    </div>

    {% for graph in graphs %}
    <div class="graph">
        <img src="{{ graph.image_data }}" alt="{{ graph.title }}">
    </div>
    {% endfor %}

    <!-- Mais seções... -->
</body>
</html>
```

### 10.5 API de Exportação

Para integração com sistemas externos:

```python
# Endpoint: GET /api/workflows/export

@app.route('/api/workflows/export', methods=['GET'])
def export_workflows():
    """
    API para exportar dados de workflows.

    Query Parameters:
        kanban_id: ID do Kanban (opcional, todos se omitido)
        format: csv | json | xlsx (padrão: json)
        start_date: Data início (ISO format)
        end_date: Data fim (ISO format)
        include: processos,transições,analytics (separado por vírgula)

    Exemplo:
    GET /api/workflows/export?kanban_id=pedidos&format=json&start_date=2025-10-01&end_date=2025-10-31&include=processos,analytics

    Returns:
        {
            "status": "success",
            "data": {
                "processos": [...],
                "analytics": {...}
            },
            "metadata": {
                "kanban_id": "pedidos",
                "period": "2025-10-01 to 2025-10-31",
                "total_processes": 207,
                "export_date": "2025-10-31T18:30:00"
            }
        }
    """
```

---

## 11. Interface de Auditoria Visual

### 11.1 Timeline Visual de Mudanças

```
+------------------------------------------------------------------+
|  🔍 Auditoria: Pedido #42 - ACME Corp                            |
+------------------------------------------------------------------+
|                                                                  |
|  [Filtros] [Exportar]                                            |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 27/10/2025 10:30                                            |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ ✨ Processo Criado                                      │    |
|  │                                                         │    |
|  │ Actor: system (auto)                                    │    |
|  │ Estado: → Orçamento                                     │    |
|  │ Origem: Formulário "pedidos" (ID: 42)                   │    |
|  │                                                         │    |
|  │ Dados iniciais:                                         │    |
|  │ • Cliente: ACME Corp                                    │    |
|  │ • Produto: Widget Premium                               │    |
|  │ • Quantidade: 10                                        │    |
|  │ • Valor Total: R$ 1.500,00                              │    |
|  │ • Aprovado: false                                       │    |
|  │ • Pagamento: false                                      │    |
|  │                                                         │    |
|  │ [Ver Detalhes]                                          │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 28/10/2025 14:30                                            |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 📝 Formulário Atualizado                                │    |
|  │                                                         │    |
|  │ Actor: user123 (João Silva)                            │    |
|  │ Ação: Edição do formulário origem                       │    |
|  │                                                         │    |
|  │ Alterações:                                             │    |
|  │ • aprovado_cliente: false → true ✅                     │    |
|  │                                                         │    |
|  │ [Ver Diff Completo]                                     │    |
|  └─────────────────────────────────────────────────────────┘    |
|         |                                                        |
|         v (500ms depois)                                         |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🤖 Transição Automática                                 │    |
|  │                                                         │    |
|  │ Actor: system (AutoTransitionEngine)                    │    |
|  │ Transição: Orçamento → Pedido Confirmado               │    |
|  │ Trigger: Pré-requisito "cliente_aprovacao" satisfeito  │    |
|  │                                                         │    |
|  │ Pré-requisitos verificados:                             │    |
|  │ ✅ aprovado_cliente = true                              │    |
|  │                                                         │    |
|  │ Tempo em "Orçamento": 28.0 horas                        │    |
|  │ (Média: 18.5 horas)                                     │    |
|  │                                                         │    |
|  │ [Ver Detalhes da Transição]                             │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 29/10/2025 09:00                                            |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 📝 Formulário Atualizado                                │    |
|  │                                                         │    |
|  │ Actor: user456 (Maria Santos)                          │    |
|  │                                                         │    |
|  │ Alterações:                                             │    |
|  │ • pagamento_recebido: false → true ✅                   │    |
|  │                                                         │    |
|  │ [Ver Diff]                                              │    |
|  └─────────────────────────────────────────────────────────┘    |
|         |                                                        |
|         v (200ms depois)                                         |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 🤖 Transição Automática                                 │    |
|  │                                                         │    |
|  │ Actor: system (AutoTransitionEngine)                    │    |
|  │ Transição: Pedido → Em Entrega                         │    |
|  │ Trigger: Pré-requisito "pagamento_confirmado" OK       │    |
|  │                                                         │    |
|  │ Tempo em "Pedido": 18.5 horas                           │    |
|  │ (Abaixo da média: 36.0 horas) ✅                        │    |
|  │                                                         │    |
|  │ [Ver Detalhes]                                          │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  📅 30/10/2025 16:00                                            |
|  ┌─────────────────────────────────────────────────────────┐    |
|  │ 👤 Transição Manual                                     │    |
|  │                                                         │    |
|  │ Actor: user123 (João Silva)                            │    |
|  │ Transição: Em Entrega → Concluído                      │    |
|  │ Método: Drag-and-drop no Kanban                        │    |
|  │                                                         │    |
|  │ Pré-requisitos: Nenhum configurado                      │    |
|  │                                                         │    |
|  │ Tempo em "Entrega": 31.0 horas                          │    |
|  │ (Dentro da média: 48.0 horas) ✅                        │    |
|  │                                                         │    |
|  │ ✅ Processo Concluído                                   │    |
|  │ Tempo Total: 3.2 dias                                   │    |
|  │ (Meta: 5.0 dias) 🎯 36% mais rápido                    │    |
|  │                                                         │    |
|  │ [Ver Detalhes]                                          │    |
|  └─────────────────────────────────────────────────────────┘    |
|                                                                  |
+------------------------------------------------------------------+
```

### 11.2 Filtros por Usuário, Data, Ação

```
+------------------------------------------------------------------+
|  🔍 Auditoria de Workflows                     [Exportar]        |
+------------------------------------------------------------------+
|                                                                  |
|  Filtros:                                                        |
|  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            |
|  │ Kanban:      │ │ Usuário:     │ │ Tipo Ação:   │            |
|  │ [Todos    ▼]│ │ [Todos    ▼] │ │ [Todas    ▼] │            |
|  └──────────────┘ └──────────────┘ └──────────────┘            |
|                                                                  |
|  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            |
|  │ Data Início: │ │ Data Fim:    │ │ Processo:    │            |
|  │ [01/10/2025] │ │ [31/10/2025] │ │ [Buscar...▼] │            |
|  └──────────────┘ └──────────────┘ └──────────────┘            |
|                                                                  |
|  Tipo de Ação:                                                   |
|  ☑️ Criação de processos                                        |
|  ☑️ Transições manuais                                          |
|  ☑️ Transições automáticas (System)                             |
|  ☑️ Transições por Agent (IA)                                   |
|  ☑️ Atualizações de formulário                                  |
|  ☐ Apenas transições forçadas                                   |
|  ☐ Apenas com justificativa                                     |
|                                                                  |
|  Usuários:                                                       |
|  ☑️ Todos usuários                                              |
|  ☐ Selecionar específicos:                                      |
|     [ ] João Silva (user123)                                    |
|     [ ] Maria Santos (user456)                                  |
|     [ ] Pedro Costa (user789)                                   |
|                                                                  |
|  [Limpar Filtros]                              [Aplicar]        |
|                                                                  |
+------------------------------------------------------------------+
|                                                                  |
|  Resultados: 487 eventos encontrados                             |
|                                                                  |
|  [Lista de eventos filtrados...]                                 |
|                                                                  |
+------------------------------------------------------------------+
```

### 11.3 Detalhes de Cada Transição

Ao clicar "Ver Detalhes" em um evento:

```
+------------------------------------------------------------------+
|  📊 Detalhes da Transição                            [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Processo: Pedido #42 - ACME Corp                                |
|  Transição: Orçamento → Pedido Confirmado                       |
|  Tipo: Automática (System)                                       |
|  Data/Hora: 28/10/2025 14:30:15                                 |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  INFORMAÇÕES GERAIS:                                             |
|                                                                  |
|  Actor: system (AutoTransitionEngine)                            |
|  Trigger: prerequisite_met                                       |
|  Forçada: Não                                                    |
|  Justificativa: -                                                |
|                                                                  |
|  Tempo no Estado Anterior:                                       |
|  28.0 horas (1 dia, 4 horas)                                     |
|  Média histórica: 18.5 horas                                     |
|  Desvio: +51% acima da média                                     |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  PRÉ-REQUISITOS VERIFICADOS:                                     |
|                                                                  |
|  ✅ Aprovação do Cliente (cliente_aprovacao)                    |
|     Tipo: field_check                                           |
|     Campo: aprovado_cliente                                     |
|     Condição: equals true                                       |
|     Valor atual: true                                           |
|     Status: Satisfeito                                          |
|     Timestamp verificação: 28/10/2025 14:30:14                  |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  CONTEXTO DA TRANSIÇÃO:                                          |
|                                                                  |
|  Alteração no Formulário:                                        |
|  • Campo "aprovado_cliente" alterado de false → true            |
|  • Alterado por: user123 (João Silva)                           |
|  • Data: 28/10/2025 14:30:10                                    |
|                                                                  |
|  Cascata:                                                        |
|  • Esta foi a 1ª transição em cascata                           |
|  • Verificou próximo estado "Em Entrega"                        |
|  • Pré-requisito "pagamento_recebido" não satisfeito            |
|  • Cascata parou aqui                                           |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  METADATA COMPLETA:                                              |
|                                                                  |
|  {                                                               |
|    "transition_id": "trans_1730126415_001",                     |
|    "process_id": "proc_pedidos_1730032800_42",                  |
|    "timestamp": "2025-10-28T14:30:15",                          |
|    "action": "auto_transitioned",                               |
|    "from_state": "orcamento",                                   |
|    "to_state": "pedido",                                        |
|    "actor": "system",                                           |
|    "actor_type": "auto_transition",                             |
|    "trigger": "prerequisite_met",                               |
|    "forced": false,                                             |
|    "justification": null,                                       |
|    "prerequisites_checked": {                                   |
|      "cliente_aprovacao": {                                     |
|        "satisfied": true,                                       |
|        "field": "aprovado_cliente",                             |
|        "expected": true,                                        |
|        "actual": true                                           |
|      }                                                          |
|    },                                                           |
|    "cascade_level": 1,                                          |
|    "time_in_previous_state_hours": 28.0,                        |
|    "avg_time_in_state_hours": 18.5                              |
|  }                                                               |
|                                                                  |
|  [Copiar JSON]                                                   |
|                                                                  |
|  [Fechar]                                                        |
|                                                                  |
+------------------------------------------------------------------+
```

### 11.4 Justificativas Registradas

Transições forçadas sempre têm justificativas registradas:

```
+------------------------------------------------------------------+
|  📊 Detalhes da Transição                            [✕ Fechar]  |
+------------------------------------------------------------------+
|                                                                  |
|  Processo: Pedido #50 - Tech Solutions                           |
|  Transição: Orçamento → Em Entrega                              |
|  Tipo: Manual (Forçada)                                          |
|  Data/Hora: 29/10/2025 11:45:30                                 |
|                                                                  |
|  ⚠️ TRANSIÇÃO FORÇADA                                           |
|                                                                  |
|  Actor: user789 (Pedro Costa - Gerente)                         |
|  Método: Drag-and-drop no Kanban                                |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  PRÉ-REQUISITOS NÃO SATISFEITOS:                                 |
|                                                                  |
|  ❌ Aprovação do Cliente (cliente_aprovacao)                    |
|     Campo: aprovado_cliente                                     |
|     Esperado: true                                              |
|     Atual: false                                                |
|                                                                  |
|  ❌ Pagamento Confirmado (pagamento_confirmado)                 |
|     Campo: pagamento_recebido                                   |
|     Esperado: true                                              |
|     Atual: false                                                |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  JUSTIFICATIVA FORNECIDA:                                        |
|                                                                  |
|  "Cliente Tech Solutions é parceiro estratégico com crédito     |
|   pré-aprovado. Gerência comercial autorizou envio imediato     |
|   com pagamento a ser confirmado em até 48h. Processo urgente   |
|   para atender prazo de projeto crítico do cliente."            |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  ANÁLISE DE RISCO:                                               |
|                                                                  |
|  🟡 Risco Médio                                                 |
|                                                                  |
|  Fatores:                                                        |
|  • Cliente tem histórico de 100% pagamentos (15 pedidos)        |
|  • Valor do pedido: R$ 8.500,00 (médio)                         |
|  • Autorizado por gerente (user789)                             |
|                                                                  |
|  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
|                                                                  |
|  SEGUIMENTO:                                                     |
|                                                                  |
|  📅 30/10/2025 09:15: Pagamento confirmado                      |
|     (18 horas após transição forçada)                           |
|                                                                  |
|  Resultado: ✅ Decisão correta, sem prejuízos                   |
|                                                                  |
|  [Fechar]                                                        |
|                                                                  |
+------------------------------------------------------------------+
```

### 11.5 Integração com Sistema de Logs

O sistema de auditoria se integra com logs do sistema:

```python
import logging
from datetime import datetime

class AuditLogger:
    """
    Logger especializado para auditoria de workflows.
    """

    def __init__(self):
        self.logger = logging.getLogger('workflow_audit')
        self.logger.setLevel(logging.INFO)

        # File handler: salva em arquivo
        fh = logging.FileHandler('logs/workflow_audit.log')
        fh.setLevel(logging.INFO)

        # Formato detalhado
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def log_transition(
        self,
        process_id: str,
        from_state: str,
        to_state: str,
        actor: str,
        actor_type: str,
        forced: bool = False,
        justification: str = None
    ):
        """
        Registra transição no log de auditoria.
        """
        message = (
            f"TRANSITION | process={process_id} | "
            f"from={from_state} | to={to_state} | "
            f"actor={actor} | type={actor_type} | "
            f"forced={forced}"
        )

        if justification:
            message += f" | justification=\"{justification}\""

        if forced:
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def log_forced_transition_alert(
        self,
        process_id: str,
        actor: str,
        prerequisites_not_met: list
    ):
        """
        Alerta para transições forçadas.
        """
        prereqs_str = ", ".join(prerequisites_not_met)
        self.logger.warning(
            f"FORCED_TRANSITION_ALERT | process={process_id} | "
            f"actor={actor} | prerequisites_not_met=[{prereqs_str}]"
        )
```

**Exemplo de arquivo de log:**

```
2025-10-27 10:30:00 | INFO | TRANSITION | process=proc_pedidos_1730032800_42 | from=null | to=orcamento | actor=system | type=system | forced=False
2025-10-28 14:30:15 | INFO | TRANSITION | process=proc_pedidos_1730032800_42 | from=orcamento | to=pedido | actor=system | type=auto_transition | forced=False
2025-10-29 09:00:22 | INFO | TRANSITION | process=proc_pedidos_1730032800_42 | from=pedido | to=entrega | actor=system | type=auto_transition | forced=False
2025-10-29 11:45:30 | WARNING | FORCED_TRANSITION_ALERT | process=proc_pedidos_1730033900_50 | actor=user789 | prerequisites_not_met=[cliente_aprovacao, pagamento_confirmado]
2025-10-29 11:45:30 | WARNING | TRANSITION | process=proc_pedidos_1730033900_50 | from=orcamento | to=entrega | actor=user789 | type=user | forced=True | justification="Cliente Tech Solutions é parceiro estratégico..."
```

---

## 12. Arquitetura Técnica Completa

### 12.1 Diagrama de Componentes Completo (ASCII)

```
+--------------------------------------------------------------------+
|                    VibeCForms v4.0 - Arquitetura Completa          |
+--------------------------------------------------------------------+

                              FRONTEND
+--------------------------------------------------------------------+
|                                                                    |
|  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            |
|  │ Landing Page │  │ Form Pages   │  │ Workflow UI  │            |
|  │              │  │              │  │              │            |
|  │ • Cards      │  │ • Dynamic    │  │ • Kanban     │            |
|  │ • Menu       │  │ • Validation │  │   Board      │            |
|  └──────┬───────┘  └──────┬───────┘  │ • Analytics  │            |
|         |                 |           │ • Editor     │            |
|         |                 |           │ • Audit      │            |
|         |                 |           └──────┬───────┘            |
|         └─────────────────┴──────────────────┘                    |
|                           |                                        |
+---------------------------┼----------------------------------------+
                            |
                  Flask Routes (VibeCForms.py)
+---------------------------┼----------------------------------------+
|                           v                                        |
|  ┌────────────────────────────────────────────────────────┐       |
|  │                     Route Layer                        │       |
|  ├────────────────────────────────────────────────────────┤       |
|  │ • GET /                                                │       |
|  │ • GET/POST /<form_path>                                │       |
|  │ • GET/POST /<form_path>/edit/<id>                      │       |
|  │ • GET /workflow/kanbans                                │       |
|  │ • GET /workflow/board/<kanban_id>                      │       |
|  │ • GET /workflow/analytics                              │       |
|  │ • GET /workflow/admin                                  │       |
|  │ • POST /api/transition/<process_id>                    │       |
|  │ • GET /api/workflows/export                            │       |
|  └────────────┬──────────────────────┬────────────────────┘       |
|               |                      |                            |
+---------------┼──────────────────────┼----------------------------+
                |                      |
        ┌───────┴────────┐    ┌────────┴────────┐
        v                v    v                 v
+----------------+  +-------------------+  +------------------+
| FormTrigger    |  | TransitionHandler |  | KanbanEditor     |
| Manager        |  |                   |  | Controller       |
+-------┬--------+  +---------┬---------+  +--------┬---------+
        |                     |                     |
        |                     |                     |
        v                     v                     v
+----------------+  +-------------------+  +------------------+
| ProcessFactory |  | AutoTransition    |  | KanbanValidator  |
|                |  | Engine            |  |                  |
+-------┬--------+  +---------┬---------+  +--------┬---------+
        |                     |                     |
        |                     |                     |
        v                     v                     v
+----------------+  +-------------------+  +------------------+
| KanbanRegistry |  | Prerequisite      |  | KanbanJSON       |
|                |  | Checker           |  | Builder          |
+-------┬--------+  +---------┬---------+  +--------┬---------+
        |                     |                     |
        └─────────────────────┴─────────────────────┘
                              |
                              v
                   +----------------------+
                   | WorkflowRepository   |
                   +----------┬-----------+
                              |
        ┌─────────────────────┼─────────────────────┐
        v                     v                     v
+----------------+  +-------------------+  +------------------+
| PatternAnalyzer|  | AnomalyDetector   |  | AgentOrchestrator|
+-------┬--------+  +---------┬---------+  +--------┬---------+
        |                     |                     |
        └─────────────────────┴─────────────────────┘
                              |
                              v
                   +----------------------+
                   | BaseAgent (Abstract) |
                   +----------┬-----------+
                              |
        ┌─────────────────────┼─────────────────────┐
        v                     v                     v
+----------------+  +-------------------+  +------------------+
| OrcamentoAgent |  | PedidoAgent       |  | EntregaAgent     |
+----------------+  +-------------------+  +------------------+

                              |
                              v
                   +----------------------+
                   | RepositoryFactory    |
                   +----------┬-----------+
                              |
        ┌─────────────────────┼─────────────────────┐
        v                     v                     v
+----------------+  +-------------------+  +------------------+
| TxtAdapter     |  | SQLiteAdapter     |  | MySQLAdapter     |
| (Default)      |  |                   |  |                  |
+----------------+  +-------------------+  +------------------+

                              |
                              v
                   +----------------------+
                   | Persistence Layer    |
                   +----------┬-----------+
                              |
        ┌─────────────────────┼─────────────────────┐
        v                     v                     v
   +-----------+        +------------+        +------------+
   | .txt      |        | SQLite     |        | MySQL      |
   | files     |        | Database   |        | Database   |
   +-----------+        +------------+        +------------+
```

### 12.2 Diagrama de Classes Principais

```
+--------------------------------------------------------------------+
|                      Diagrama de Classes                           |
+--------------------------------------------------------------------+

BaseRepository (ABC)
├─ create(form_path, spec, data)
├─ read_all(form_path, spec)
├─ update(form_path, spec, idx, data)
├─ delete(form_path, spec, idx)
├─ exists(form_path)
├─ has_data(form_path)
├─ create_storage(form_path, spec)
├─ drop_storage(form_path)
├─ count(form_path)
├─ search(form_path, spec, filters)
└─ backup(form_path, backup_dir)
      |
      +-- TxtAdapter
      |     ├─ _read_file()
      |     ├─ _write_file()
      |     └─ _parse_line()
      |
      +-- SQLiteAdapter
      |     ├─ _get_connection()
      |     ├─ _create_table()
      |     └─ _map_field_type()
      |
      +-- MySQLAdapter
      |
      +-- WorkflowRepository
            ├─ get_processes_by_kanban()
            ├─ get_processes_by_source_form()
            ├─ update_process_state()
            ├─ get_process_history()
            └─ get_analytics_data()

───────────────────────────────────────────────────────────────────

KanbanRegistry
├─ _kanban_to_forms: dict
├─ _form_to_kanbans: dict
├─ get_kanbans_for_form(form_path)
├─ get_forms_for_kanban(kanban_id)
├─ get_primary_form(kanban_id)
└─ should_auto_create_process(form_path, kanban_id)

FormTriggerManager
├─ registry: KanbanRegistry
├─ process_factory: ProcessFactory
├─ on_form_saved(form_path, form_id, form_data, user_id)
└─ on_form_updated(form_path, form_id, form_data, user_id)

ProcessFactory
├─ repo: WorkflowRepository
├─ create_from_form(kanban_id, form_path, form_id, form_data, created_by)
├─ _apply_template(template, data, extra_vars)
├─ find_processes_by_source(form_path, form_id)
└─ update_process_data(process_id, new_data)

───────────────────────────────────────────────────────────────────

AutoTransitionEngine
├─ repo: WorkflowRepository
├─ checker: PrerequisiteChecker
├─ check_and_transition(process_id, max_cascade)
├─ _get_next_state(kanban, current_state)
└─ _execute_transition(process_id, to_state, metadata)

PrerequisiteChecker
├─ check_all(process, prerequisites)
├─ _check_field(process, prereq)
├─ _check_api(process, prereq)
├─ _check_time(process, prereq)
├─ _check_script(process, prereq)
└─ _evaluate_condition(actual_value, condition, expected_value)

TransitionHandler
├─ transition(process_id, to_state, actor, actor_type, trigger, justification, metadata)
├─ _validate_transition(process, to_state)
├─ _update_process_state(process, to_state)
└─ _register_history(process_id, transition_data)

───────────────────────────────────────────────────────────────────

BaseAgent (ABC)
├─ state_id: str
├─ kanban_id: str
├─ analyze(process, context)
├─ get_required_context()
└─ load_context(process_id)
      |
      +-- OrcamentoAgent
      |     ├─ _calculate_time_in_state()
      |     ├─ _get_avg_approval_time()
      |     └─ analyze(process, context)
      |
      +-- PedidoAgent
      |     ├─ _get_avg_payment_time()
      |     ├─ _get_payment_reliability()
      |     └─ analyze(process, context)
      |
      +-- EntregaAgent

AgentOrchestrator
├─ agents: dict
├─ analyze_process(process_id)
├─ analyze_all_active_processes(kanban_id)
├─ _get_agent_for_state(kanban_id, state_id)
├─ _save_analysis(process_id, analysis)
└─ _notify_user(process, analysis)

───────────────────────────────────────────────────────────────────

PatternAnalyzer
├─ analyze_transition_patterns(kanban_id, min_support)
├─ analyze_state_durations(kanban_id)
├─ cluster_similar_processes(kanban_id, n_clusters)
├─ _extract_sequence(process_history)
└─ _calculate_duration(process_history, state_id)

AnomalyDetector
├─ detect_stuck_processes(kanban_id, threshold_hours)
├─ detect_anomalous_transitions(kanban_id, look_back_days)
├─ _calculate_anomaly_score(process)
└─ _identify_root_cause(process, anomaly)

───────────────────────────────────────────────────────────────────

KanbanEditorController
├─ save_kanban(kanban_data)
├─ load_kanban(kanban_id)
├─ validate_kanban(kanban_data)
└─ preview_kanban(kanban_data)

KanbanValidator
├─ validate(kanban_data)
├─ _validate_basic_info(data)
├─ _validate_states(states)
├─ _validate_transitions(transitions)
├─ _validate_prerequisites(prerequisites)
└─ _validate_linked_forms(linked_forms)

KanbanJSONBuilder
├─ build(kanban_data)
├─ _build_states(states_data)
├─ _build_prerequisites(prereqs_data)
└─ _build_linked_forms(forms_data)
```

### 12.3 Fluxo de Dados End-to-End

```
USUÁRIO SALVA FORMULÁRIO:
═══════════════════════════════════════════════════════════════════

[1] POST /pedidos
     ↓
[2] Route Handler (VibeCForms.py)
     ├─ Valida dados do formulário
     ├─ Salva em BaseRepository (via RepositoryFactory)
     └─ Chama FormTriggerManager.on_form_saved()
          ↓
[3] FormTriggerManager
     ├─ Consulta KanbanRegistry
     ├─ Encontra Kanban "pedidos" vinculado
     └─ Chama ProcessFactory.create_from_form()
          ↓
[4] ProcessFactory
     ├─ Carrega config do Kanban
     ├─ Aplica templates de título/descrição
     ├─ Monta estrutura do processo
     ├─ Salva em WorkflowRepository
     └─ Retorna process_id
          ↓
[5] FormTriggerManager (retorno)
     ├─ Recebe process_id
     └─ Chama AutoTransitionEngine.check_and_transition()
          ↓
[6] AutoTransitionEngine
     ├─ Busca processo no WorkflowRepository
     ├─ Identifica estado atual: "orcamento"
     ├─ Busca próximo estado: "pedido"
     ├─ Chama PrerequisiteChecker.check_all()
     |    ├─ Verifica pré-req "aprovado_cliente = true"
     |    ├─ Atual: false
     |    └─ Retorna: not_satisfied
     ├─ Não move (pré-requisitos não satisfeitos)
     └─ Retorna ao Route Handler
          ↓
[7] Route Handler (resposta)
     ├─ Redireciona para /workflow/board/pedidos
     └─ Flash message: "Processo criado!"


USUÁRIO EDITA FORMULÁRIO E MARCA APROVADO:
═══════════════════════════════════════════════════════════════════

[1] POST /pedidos/edit/42
     ↓
[2] Route Handler
     ├─ Atualiza dados no BaseRepository
     └─ Chama FormTriggerManager.on_form_updated()
          ↓
[3] FormTriggerManager
     ├─ Busca processos criados a partir deste form
     |    (form_path="pedidos", form_id=42)
     ├─ Encontra: proc_pedidos_xxx_42
     ├─ Atualiza process_data com novos dados
     |    (aprovado_cliente: false → true)
     └─ Chama AutoTransitionEngine.check_and_transition()
          ↓
[4] AutoTransitionEngine
     ├─ Busca processo
     ├─ Estado atual: "orcamento"
     ├─ Próximo estado: "pedido"
     ├─ Chama PrerequisiteChecker.check_all()
     |    ├─ Verifica "aprovado_cliente = true"
     |    ├─ Atual: true (acabou de ser atualizado!)
     |    └─ Retorna: all_satisfied
     ├─ ✅ Move processo: orcamento → pedido
     ├─ Registra no histórico
     ├─ Recursão: verifica próximo estado "entrega"
     |    ├─ Pré-req: "pagamento_recebido = true"
     |    ├─ Atual: false
     |    └─ Para cascata aqui
     └─ Retorna
          ↓
[5] Route Handler
     ├─ Redireciona para /pedidos
     └─ Flash: "Dados salvos! Processo movido automaticamente."


AGENT IA ANALISA PROCESSO:
═══════════════════════════════════════════════════════════════════

[1] Cron Job (a cada hora)
     ↓
[2] AgentOrchestrator.analyze_all_active_processes()
     ├─ Busca todos processos ativos
     └─ Para cada processo:
          ↓
[3] AgentOrchestrator.analyze_process(process_id)
     ├─ Carrega processo do WorkflowRepository
     ├─ Identifica estado: "pedido"
     ├─ Busca agent configurado: PedidoAgent
     ├─ Chama agent.load_context(process_id)
     |    ├─ Carrega histórico
     |    ├─ Carrega padrões históricos (PatternAnalyzer)
     |    ├─ Carrega processos similares
     |    └─ Carrega dados do cliente
     └─ Chama agent.analyze(process, context)
          ↓
[4] PedidoAgent.analyze()
     ├─ Calcula tempo no estado: 120 horas
     ├─ Verifica média do cliente: 30 horas
     ├─ Confiabilidade pagamento: 95%
     ├─ Pré-req pendente: pagamento_recebido
     ├─ Gera recomendação:
     |    ├─ should_transition: false
     |    ├─ confidence: 0.85
     |    ├─ justification: "Aguardando pagamento..."
     |    └─ recommendations: ["send_reminder", "escalate"]
     └─ Retorna análise
          ↓
[5] AgentOrchestrator (retorno)
     ├─ Salva análise no WorkflowRepository
     ├─ Verifica se tem recomendações high priority: Sim
     ├─ Chama _notify_user()
     |    ├─ Envia email para usuário
     |    └─ Cria notificação no sistema
     └─ Retorna
```

### 12.4 Estrutura de Diretórios

```
VibeCForms/
├── src/
│   ├── VibeCForms.py                 # Flask app principal
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── persistence.json          # Config de backends
│   │   ├── schema_history.json       # Histórico de schemas
│   │   ├── kanban_registry.json      # Mapeamento Kanban↔Form
│   │   └── kanbans/
│   │       ├── pedidos_kanban.json
│   │       ├── projetos_kanban.json
│   │       └── rh_contratacao_kanban.json
│   │
│   ├── specs/
│   │   ├── contatos.json
│   │   ├── pedidos.json
│   │   ├── financeiro/
│   │   │   ├── _folder.json
│   │   │   └── contas.json
│   │   └── rh/
│   │       ├── _folder.json
│   │       └── candidatos.json
│   │
│   ├── templates/
│   │   ├── index.html                # Landing page
│   │   ├── form.html                 # Form page
│   │   ├── edit.html                 # Edit page
│   │   │
│   │   ├── fields/                   # Field templates
│   │   │   ├── input.html
│   │   │   ├── textarea.html
│   │   │   ├── checkbox.html
│   │   │   ├── select.html
│   │   │   ├── radio.html
│   │   │   ├── color.html
│   │   │   ├── range.html
│   │   │   └── search_autocomplete.html
│   │   │
│   │   ├── workflow/                 # Workflow templates
│   │   │   ├── kanbans_list.html
│   │   │   ├── board.html
│   │   │   ├── analytics.html
│   │   │   ├── audit.html
│   │   │   └── admin/
│   │   │       ├── editor.html
│   │   │       ├── edit_state.html
│   │   │       └── edit_prerequisites.html
│   │   │
│   │   └── reports/                  # Report templates
│   │       ├── executive_pdf.html
│   │       ├── detailed_pdf.html
│   │       └── audit_pdf.html
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseRepository (ABC)
│   │   ├── factory.py                # RepositoryFactory
│   │   ├── config.py                 # Config loader
│   │   ├── change_manager.py
│   │   ├── migration_manager.py
│   │   ├── schema_detector.py
│   │   ├── schema_history.py
│   │   ├── workflow_repository.py    # WorkflowRepository
│   │   │
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── txt_adapter.py        # TxtAdapter
│   │       ├── sqlite_adapter.py     # SQLiteAdapter
│   │       ├── mysql_adapter.py      # MySQLAdapter
│   │       ├── postgresql_adapter.py
│   │       └── mongodb_adapter.py
│   │
│   ├── workflow/
│   │   ├── __init__.py
│   │   │
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── kanban_registry.py    # KanbanRegistry
│   │   │   ├── form_trigger_manager.py
│   │   │   ├── process_factory.py
│   │   │   ├── auto_transition_engine.py
│   │   │   ├── prerequisite_checker.py
│   │   │   └── transition_handler.py
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py         # BaseAgent (ABC)
│   │   │   ├── agent_orchestrator.py
│   │   │   ├── context_loader.py
│   │   │   ├── orcamento_agent.py
│   │   │   ├── pedido_agent.py
│   │   │   └── entrega_agent.py
│   │   │
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── pattern_analyzer.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── bottleneck_analyzer.py
│   │   │   ├── workflow_ml_model.py
│   │   │   └── dashboard_generator.py
│   │   │
│   │   ├── editor/
│   │   │   ├── __init__.py
│   │   │   ├── kanban_editor_controller.py
│   │   │   ├── kanban_validator.py
│   │   │   ├── kanban_json_builder.py
│   │   │   └── templates_manager.py
│   │   │
│   │   ├── export/
│   │   │   ├── __init__.py
│   │   │   ├── csv_exporter.py
│   │   │   ├── pdf_exporter.py
│   │   │   ├── excel_exporter.py
│   │   │   ├── report_generator.py
│   │   │   └── report_scheduler.py
│   │   │
│   │   └── audit/
│   │       ├── __init__.py
│   │       ├── audit_logger.py
│   │       ├── audit_viewer.py
│   │       └── timeline_generator.py
│   │
│   ├── data/                         # Data files (TXT backend)
│   │   ├── contatos.txt
│   │   ├── pedidos.txt
│   │   └── workflows/
│   │       └── pedidos/
│   │           ├── proc_001.json
│   │           └── proc_002.json
│   │
│   ├── backups/
│   │   └── migrations/
│   │       └── 2025-10-27_14-30_pedidos.txt
│   │
│   └── vibecforms.db                 # SQLite database (opcional)
│
├── tests/
│   ├── test_form.py                  # Testes de formulários
│   ├── test_workflow_integration.py
│   ├── test_kanban_registry.py
│   ├── test_process_factory.py
│   ├── test_auto_transition.py
│   ├── test_agents.py
│   ├── test_pattern_analyzer.py
│   └── test_kanban_editor.py
│
├── docs/
│   ├── planning/
│   │   └── workflow/
│   │       ├── workflow_kanban_planejamento_v4_parte1.md
│   │       ├── workflow_kanban_planejamento_v4_parte2.md
│   │       └── workflow_kanban_planejamento_v4_parte3.md
│   ├── prompts.md
│   └── roadmap.md
│
├── logs/
│   ├── workflow_audit.log
│   └── app.log
│
├── scripts/
│   ├── prerequisites/
│   │   ├── check_approval.py
│   │   └── check_stock.py
│   └── migrations/
│       └── migrate_to_sqlite.py
│
├── CLAUDE.md                         # Guia para Claude Code
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

### 12.5 Dependências entre Módulos

```
┌─────────────────────────────────────────────────────────────┐
│                    Dependency Graph                         │
└─────────────────────────────────────────────────────────────┘

VibeCForms.py (Flask App)
    │
    ├─→ FormTriggerManager
    │       ├─→ KanbanRegistry
    │       ├─→ ProcessFactory
    │       │       └─→ WorkflowRepository
    │       │               └─→ RepositoryFactory
    │       │                       └─→ BaseRepository
    │       │                               ├─→ TxtAdapter
    │       │                               ├─→ SQLiteAdapter
    │       │                               └─→ MySQLAdapter
    │       └─→ AutoTransitionEngine
    │               ├─→ PrerequisiteChecker
    │               └─→ TransitionHandler
    │
    ├─→ AgentOrchestrator
    │       ├─→ BaseAgent
    │       │       ├─→ OrcamentoAgent
    │       │       ├─→ PedidoAgent
    │       │       └─→ EntregaAgent
    │       └─→ ContextLoader
    │               ├─→ PatternAnalyzer
    │               └─→ WorkflowRepository
    │
    ├─→ KanbanEditorController
    │       ├─→ KanbanValidator
    │       ├─→ KanbanJSONBuilder
    │       └─→ KanbanRegistry
    │
    ├─→ ReportGenerator
    │       ├─→ CSVExporter
    │       ├─→ PDFExporter
    │       ├─→ ExcelExporter
    │       └─→ WorkflowRepository
    │
    └─→ AuditViewer
            ├─→ AuditLogger
            └─→ WorkflowRepository

Observações:
• Setas (→) indicam dependência
• Camadas bem definidas evitam dependências circulares
• WorkflowRepository é usado por múltiplos módulos
• BaseRepository é abstrato, adaptadores implementam
```

---

## Conclusão da Parte 2

Esta segunda parte apresentou as **funcionalidades avançadas** do Sistema de Workflow Kanban v4.0:

✅ **Editor Visual de Kanbans**: Interface completa para criar Kanbans sem editar JSON

✅ **Drag & Drop**: Organizar estados, configurar transições e pré-requisitos visualmente

✅ **Preview e Validação**: Visualizar e validar antes de salvar

✅ **Templates**: Começar com templates pré-configurados

✅ **Exportações**: CSV, PDF, Excel com relatórios customizáveis

✅ **Agendamento**: Relatórios periódicos automáticos

✅ **Auditoria Visual**: Timeline completa de mudanças

✅ **Filtros e Detalhes**: Buscar transições por usuário, data, tipo

✅ **Justificativas**: Todas transições forçadas registradas

✅ **Arquitetura Completa**: Diagramas de componentes, classes, fluxos e diretórios

---

**Continua na Parte 3:**

- **Seção 13**: Exemplo Completo - Fluxo de Pedidos (Detalhado com Screenshots)
- **Seção 14**: Fases de Implementação (5 Fases MVP com cronograma)
- **Seção 15**: Estratégia de Testes (Unitários, Integração, E2E)

---

**Elaborado por:** Rodrigo Santista
**Com assistência de:** Claude Code (Anthropic)
**Data:** Outubro 2025
**Versão:** 4.0 - Parte 2 de 3
