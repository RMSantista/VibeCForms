# Level 3: Interface
# Sistema Kanban-Workflow VibeCForms v4.0

**Nível de conhecimento**: Proficient (Proficiente)
**Para quem**: Desenvolvedores trabalhando em UI/UX
**Conteúdo**: Visual Editor, Dashboard Analytics, Exports (CSV/PDF/Excel), Auditoria Visual

---

## Navegação

- **Anterior**: [Level 2 - Engine](level_2_engine.md)
- **Você está aqui**: Level 3 - Interface
- **Próximo**: [Level 4 - Architecture](level_4_architecture.md)
- **Outros níveis**: [Level 1](level_1_fundamentals.md) | [Level 5](level_5_implementation.md)

---

## 7. Visual Kanban Editor (Admin Area)

### 7.1 Editor Visual - Criação de Kanbans SEM Editar JSON

**Rota**: `/workflow/admin`

O Editor Visual permite criar/editar Kanbans através de interface drag-and-drop, eliminando necessidade de editar JSON manualmente.

**Interface principal:**

```
+------------------------------------------------------------------+
|                    EDITOR VISUAL DE KANBAN                       |
+------------------------------------------------------------------+
|                                                                  |
|  Nome: [Fluxo de Pedidos___________]  Ícone: [🛒]               |
|  Descrição: [Gerenciamento de ciclo de vida de pedidos______]   |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |                      ESTADOS                               |  |
|  +------------------------------------------------------------+  |
|  |                                                            |  |
|  |  [+ Adicionar Estado]                                      |  |
|  |                                                            |  |
|  |  +-------------+  +-------------+  +-------------+         |  |
|  |  | Orçamento   |  | Pedido      |  | Entrega     |         |  |
|  |  | 🟧 Laranja  |  | 🟦 Azul    |  | 🟨 Amarelo |          |  |
|  |  | [Edit] [Del]|  | [Edit] [Del]|  | [Edit] [Del]|         |  |
|  |  +-------------+  +-------------+  +-------------+         |  |
|  |                                                            |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |                     TRANSIÇÕES                             |  |
|  +------------------------------------------------------------+  |
|  |                                                            |  |
|  |  Orçamento → Pedido          [Manual]   [Editar]           |  |
|  |    └─ Pré-req: valor_total not_empty                       |  |
|  |                                                            |  |
|  |  Pedido → Entrega            [System]   [Editar]           |  |
|  |    └─ Auto-transition após 2h                              |  |
|  |                                                            |  |
|  |  [+ Adicionar Transição]                                   |  |
|  |                                                            |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  [Salvar Kanban] [Visualizar JSON] [Cancelar]                    |
|                                                                  |
+------------------------------------------------------------------+
```

### 7.2 Web Interface - Funcionalidades

**Principais funcionalidades:**

1. **Criação de Estados (Drag & Drop)**
   - Arrastar cards para criar novos estados
   - Configurar nome, cor, ícone visualmente
   - Marcar estado inicial/final com checkboxes
   - Configurar timeout com slider (0-168 horas)

2. **Editor de Transições Visual**
   - Seletor dropdown: Estado origem → Estado destino
   - Radio buttons: Manual / System / Agent
   - Botão "Adicionar Pré-requisito" abre modal

3. **Configuração de Pré-requisitos (Modal)**
   ```
   +-----------------------------------------------+
   |  Adicionar Pré-requisito                      |
   +-----------------------------------------------+
   |                                               |
   |  Tipo: [field_check ▼]                        |
   |                                               |
   |  Campo: [valor_total_____]                    |
   |  Condição: [not_empty ▼]                      |
   |  Mensagem: [Valor deve estar preenchido___]   |
   |                                               |
   |  [Adicionar] [Cancelar]                       |
   +-----------------------------------------------+
   ```

4. **Vinculação de Formulários**
   - Busca de formulários com autocomplete
   - Checkbox "Primary" para formulário principal
   - Checkbox "Auto-create process" para criação automática

5. **Preview de Kanban**
   - Visualização em tempo real do quadro
   - Mostra como ficará para usuários finais

6. **Validação em Tempo Real**
   - Valida campos obrigatórios
   - Verifica ciclos infinitos
   - Alerta sobre transições inválidas
   - Feedback visual (borda vermelha em erros)

7. **Templates de Kanban**
   - Galeria de templates pré-configurados
   - Um clique para aplicar template
   - Customização posterior

8. **Salvamento Automático como JSON**
   - Gera JSON válido automaticamente
   - Salva em `src/config/kanbans/<kanban_id>.json`
   - Botão "Visualizar JSON" mostra código gerado

---

## 8. Dashboard de Analytics

### 8.1 Overview do Dashboard

**Rota**: `/workflow/analytics/<kanban_id>`

Dashboard com métricas e KPIs em tempo real do workflow.

**Layout principal:**

```
+------------------------------------------------------------------+
|                    DASHBOARD - Fluxo de Pedidos                  |
+------------------------------------------------------------------+
|                                                                  |
|  📊 KPIs PRINCIPAIS                                              |
|  +---------------+  +---------------+  +---------------+         |
|  | Processos     |  | Taxa de       |  | Tempo Médio   |         |
|  | Ativos        |  | Conclusão     |  | de Conclusão  |         |
|  |               |  |               |  |               |         |
|  |      142      |  |      87%      |  |    3.2 dias   |         |
|  +---------------+  +---------------+  +---------------+         |
|                                                                  |
|  📈 VOLUME POR ESTADO (Últimos 30 dias)                          |
|  +------------------------------------------------------------+  |
|  |        ▃▅▇█                                                |  |
|  | Orç.  ▅███  Ped. ███▇  Entr. ██▅  Conc. ████████████     |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  ⏱️ TEMPO MÉDIO POR ESTADO                                       |
|  +------------------------------------------------------------+  |
|  | Orçamento       ████████     (8h)                          |  |
|  | Pedido          ████████████████  (16h)  ⚠️ GARGALO       |  |
|  | Entrega         ████████   (8h)                            |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  🤖 INSIGHTS DE IA                                               |
|  +------------------------------------------------------------+  |
|  | • Estado "Pedido" está 2x mais lento que esperado          |  |
|  | • 15 processos travados há mais de 48h                     |  |
|  | • Padrão anômalo: 10% dos pedidos pulam etapa Entrega      |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  [Exportar CSV] [Exportar PDF] [Configurar Alertas]             |
|                                                                  |
+------------------------------------------------------------------+
```

### 8.2 Métricas Disponíveis

**KPIs principais:**
- Total de processos ativos
- Taxa de conclusão (%)
- Tempo médio de conclusão
- Processos criados hoje/semana/mês
- Taxa de cancelamento

**Gráficos:**
- Volume de processos por estado (barras)
- Timeline de criação vs conclusão (linha)
- Funil de conversão (funil)
- Heatmap de transições (matriz)
- Distribuição de tempo por estado (boxplot)

**Tabelas:**
- Top 10 processos mais lentos
- Processos travados
- Histórico de transições recentes

### 8.3 Filtros

```
+-----------------------------------------------+
|  FILTROS                                      |
+-----------------------------------------------+
|  Período: [Últimos 30 dias ▼]                 |
|  Estado: [Todos ▼]                            |
|  Formulário origem: [Todos ▼]                 |
|  Data criação: [____/__/__ até ____/__/__]    |
|  Buscar: [ID ou título do processo_______]    |
|                                               |
|  [Aplicar Filtros] [Limpar]                   |
+-----------------------------------------------+
```

### 8.4 Identificação de Bottlenecks

Sistema identifica automaticamente gargalos:

```
⚠️ GARGALO IDENTIFICADO

Estado: Pedido
Tempo médio atual: 16 horas
Tempo esperado: 8 horas
Diferença: +100%
Processos afetados: 45

Recomendações:
• Adicionar mais recursos ao estado
• Automatizar verificações
• Implementar priorização
```

---

## 9. Exports e Reports

### 9.1 Exportação CSV

**Endpoint**: `GET /workflow/export/<kanban_id>/csv`

Exporta dados de processos em formato CSV para análise em Excel/Google Sheets.

**Colunas exportadas:**
- process_id
- current_state
- created_at
- updated_at
- duration_hours
- source_form
- title
- description
- [campos customizados do process_data]

**Exemplo CSV:**

```csv
process_id,current_state,created_at,duration_hours,cliente,valor_total
proc_001,concluido,2025-10-20T10:00:00,72,ACME Corp,1500.00
proc_002,em_entrega,2025-10-21T14:30:00,48,Tech Solutions,3200.00
```

### 9.2 Exportação PDF

**Endpoint**: `GET /workflow/export/<kanban_id>/pdf`

Gera relatório PDF formatado com gráficos e tabelas.

**Estrutura do PDF:**

```
+---------------------------------------+
|  RELATÓRIO DE WORKFLOW                |
|  Kanban: Fluxo de Pedidos             |
|  Período: 01/10/2025 a 31/10/2025     |
+---------------------------------------+

1. RESUMO EXECUTIVO
   - Total de processos: 142
   - Concluídos: 123 (87%)
   - Em andamento: 19 (13%)

2. GRÁFICOS
   [Gráfico de barras: Volume por estado]
   [Gráfico de linha: Timeline]
   [Gráfico de funil: Conversão]

3. TABELAS DETALHADAS
   [Processos por estado]
   [Tempo médio por transição]

4. ANÁLISES
   - Bottlenecks identificados
   - Padrões observados
   - Recomendações
```

### 9.3 Exportação Excel

**Endpoint**: `GET /workflow/export/<kanban_id>/excel`

Gera arquivo .xlsx com múltiplas abas:

- **Aba 1**: Resumo (KPIs + gráficos)
- **Aba 2**: Lista completa de processos
- **Aba 3**: Histórico de transições
- **Aba 4**: Analytics (tempo por estado, etc.)

### 9.4 Report Scheduling

Agendar envio automático de relatórios:

```json
{
  "schedule": {
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00",
    "format": "pdf",
    "recipients": ["gestor@empresa.com"]
  }
}
```

### 9.5 Templates Customizáveis

Criar templates de relatório personalizados:

```
+---------------------------------------+
|  TEMPLATE DE RELATÓRIO                |
+---------------------------------------+
|  Nome: Relatório Gerencial            |
|                                       |
|  Seções incluídas:                    |
|  ☑ Resumo executivo                   |
|  ☑ Gráfico de volume                  |
|  ☐ Tabela de processos completa       |
|  ☑ Top 10 processos lentos            |
|  ☑ Bottlenecks                        |
|                                       |
|  [Salvar Template]                    |
+---------------------------------------+
```

---

## 10. Visual Audit Interface

### 10.1 Timeline Visual de Mudanças

**Rota**: `/workflow/audit/<process_id>`

Interface visual mostrando histórico completo de um processo.

```
+------------------------------------------------------------------+
|                  AUDITORIA - Processo #42                        |
+------------------------------------------------------------------+
|                                                                  |
|  27/10 10:30   🔵 CRIADO                                         |
|  │             Sistema criou processo a partir de form "pedidos" |
|  │             Usuário: Auto (form save)                         |
|  │                                                               |
|  │  8h                                                           |
|  │                                                               |
|  27/10 18:30   🟢 ORÇAMENTO → PEDIDO                             |
|  │             João Silva aprovou orçamento                      |
|  │             ✅ Todos pré-requisitos OK                         |
|  │                                                               |
|  │  16h  ⚠️ (2x mais lento que média)                            |
|  │                                                               |
|  28/10 10:30   🟡 PEDIDO → ENTREGA                               |
|  │             Maria Santos moveu manualmente                    |
|  │             ⚠️ Forçou transição (pré-req pendente)            |
|  │             Justificativa: "Cliente VIP - urgente"            |
|  │                                                               |
|  │  6h                                                           |
|  │                                                               |
|  28/10 16:30   ✅ ENTREGA → CONCLUÍDO                            |
|  │             Sistema progrediu automaticamente                 |
|  │             ✅ Entrega confirmada via API                      |
|  │                                                               |
|  └─────────── Total: 30 horas                                   |
|                                                                  |
+------------------------------------------------------------------+
```

### 10.2 Filtros por Usuário, Data, Ação

```
+-----------------------------------------------+
|  FILTROS DE AUDITORIA                         |
+-----------------------------------------------+
|  Usuário: [Todos ▼]                           |
|  Ação: [Todas ▼]                              |
|  Período: [____/__/__ até ____/__/__]         |
|  Mostrar apenas forçadas: [ ]                 |
|                                               |
|  [Aplicar]                                    |
+-----------------------------------------------+
```

### 10.3 Detalhes de Cada Transição

Clicar em qualquer transição mostra modal com detalhes completos:

```
+-----------------------------------------------+
|  DETALHES DA TRANSIÇÃO                        |
+-----------------------------------------------+
|  De: Pedido                                   |
|  Para: Entrega                                |
|  Data: 28/10/2025 10:30:45                    |
|  Usuário: Maria Santos (maria@empresa.com)    |
|  Tipo: Manual                                 |
|  Forçada: Sim ⚠️                               |
|                                               |
|  Justificativa:                               |
|  "Cliente VIP - solicitação urgente"          |
|                                               |
|  Pré-requisitos no momento:                   |
|  ✅ Campo 'valor_confirmado' = true           |
|  ❌ API externa retornou 404                  |
|  ✅ Tempo mínimo (24h) atingido               |
|                                               |
|  Metadados:                                   |
|  IP: 192.168.1.100                            |
|  User-Agent: Chrome 118.0                     |
|                                               |
|  [Fechar]                                     |
+-----------------------------------------------+
```

### 10.4 Justificativas Registradas

Todas transições forçadas exigem justificativa:

```json
{
  "transition_id": "trans_12345",
  "forced": true,
  "justification": "Cliente VIP - solicitação urgente",
  "approved_by": "maria@empresa.com",
  "approval_timestamp": "2025-10-28T10:30:45Z"
}
```

---

## Próximos Passos

Após dominar as interfaces, avance para:

**[Level 4 - Architecture](level_4_architecture.md)**: Arquitetura técnica completa, diagramas, estrutura de diretórios

---

**Referência original**: `VibeCForms/docs/planning/workflow/workflow_kanban_planejamento_v4_parte2.md` (Seções 8-11)
