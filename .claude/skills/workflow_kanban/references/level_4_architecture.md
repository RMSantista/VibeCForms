# Level 4: Architecture
# Sistema Kanban-Workflow VibeCForms v4.0

**Nível de conhecimento**: Advanced (Avançado)
**Para quem**: Arquitetos e tech leads
**Conteúdo**: Arquitetura técnica completa, diagramas de componentes, estrutura de diretórios, dependências entre módulos

---

## Navegação

- **Anterior**: [Level 3 - Interface](level_3_interface.md)
- **Você está aqui**: Level 4 - Architecture
- **Próximo**: [Level 5 - Implementation](level_5_implementation.md)
- **Outros níveis**: [Level 1](level_1_fundamentals.md) | [Level 2](level_2_engine.md)

---

## 11. Complete Technical Architecture

### 11.1 Diagrama Completo de Componentes (ASCII)

```
+------------------------------------------------------------------+
|                     VIBECFORMS WORKFLOW v4.0                     |
|                    ARQUITETURA COMPLETA                          |
+------------------------------------------------------------------+

┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Landing     │  │ Kanban Board │  │ Visual Editor│          │
│  │  Page        │  │  (Drag&Drop) │  │ (Admin)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Form Pages  │  │  Analytics   │  │ Audit View   │          │
│  │  (CRUD)      │  │  Dashboard   │  │ (Timeline)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    VibeCForms.py                          │  │
│  │                   (Flask Routes)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │               │               │                     │
│           ▼               ▼               ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │FormTrigger  │  │AutoTransit. │  │AgentOrch.   │            │
│  │Manager      │  │Engine       │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│           │               │               │                     │
│           └───────────────┴───────────────┘                     │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BUSINESS LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ProcessFact. │  │KanbanReg.   │  │Prerequisite │            │
│  │             │  │             │  │Checker      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │PatternAnal. │  │AnomalyDet.  │  │BottleneckAn.│            │
│  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │             AI AGENTS (BaseAgent)                    │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │       │
│  │  │Orcamento │  │ Pedido   │  │ Entrega  │          │       │
│  │  │Agent     │  │ Agent    │  │ Agent    │          │       │
│  │  └──────────┘  └──────────┘  └──────────┘          │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RepositoryFactory                            │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│          ┌───────────┴───────────┬───────────┐                 │
│          ▼                       ▼           ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │WorkflowRepo │  │FormRepo     │  │BaseRepo     │            │
│  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│          │                       │           │                 │
│          └───────────┬───────────┴───────────┘                 │
│                      │                                          │
│          ┌───────────┴───────────┬───────────┐                 │
│          ▼                       ▼           ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │TxtAdapter   │  │SQLiteAdapter│  │MySQLAdapter │            │
│  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  *.txt      │  │vibecforms.db│  │  MySQL DB   │            │
│  │  files      │  │  (SQLite)   │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Diagrama de Classes Principais

```
┌──────────────────────────────────────────────────────────────┐
│                       CLASS DIAGRAM                           │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  BaseRepository     │  (Abstract)
├─────────────────────┤
│ + create()          │
│ + read_all()        │
│ + update()          │
│ + delete()          │
│ + exists()          │
│ + has_data()        │
│ + create_storage()  │
│ + drop_storage()    │
│ + count()           │
│ + search()          │
│ + backup()          │
└─────────────────────┘
          △
          │
    ┌─────┴─────┬─────────────────┐
    │           │                 │
┌───────────┐ ┌──────────────┐ ┌──────────────┐
│TxtAdapter │ │SQLiteAdapter │ │MySQLAdapter  │
└───────────┘ └──────────────┘ └──────────────┘


┌──────────────────────┐
│ WorkflowRepository   │  (Extends BaseRepository)
├──────────────────────┤
│ + get_processes_by_kanban()      │
│ + get_processes_by_source_form() │
│ + update_process_state()         │
│ + get_process_history()          │
│ + get_analytics_data()           │
└──────────────────────┘


┌─────────────────────┐
│  BaseAgent          │  (Abstract)
├─────────────────────┤
│ + analyze_context() │
│ + suggest_transition()│
│ + validate_transition()│
└─────────────────────┘
          △
          │
    ┌─────┴─────┬─────────────┐
    │           │             │
┌───────────┐ ┌────────┐ ┌─────────┐
│Orcamento  │ │Pedido  │ │Entrega  │
│Agent      │ │Agent   │ │Agent    │
└───────────┘ └────────┘ └─────────┘


┌─────────────────────────┐
│  ProcessFactory         │
├─────────────────────────┤
│ + create_from_form()    │
│ + apply_field_mapping() │
│ + generate_process_id() │
└─────────────────────────┘


┌─────────────────────────┐
│  AutoTransitionEngine   │
├─────────────────────────┤
│ + check_auto_progression()│
│ + execute_transition()  │
│ + validate_prerequisites()│
│ + handle_timeout()      │
└─────────────────────────┘


┌─────────────────────────┐
│  KanbanRegistry         │
├─────────────────────────┤
│ + get_kanbans_for_form()│
│ + get_forms_for_kanban()│
│ + get_primary_form()    │
│ + should_auto_create()  │
└─────────────────────────┘
```

### 11.3 Fluxo de Dados End-to-End

```
FLUXO COMPLETO: Form Save → Process Creation → Auto-Transition → Agent Suggestion

[1] USER FILLS FORM
         │
         ▼
[2] POST /pedidos (submit form)
         │
         ▼
[3] VibeCForms.py: @app.route('/pedidos', methods=['POST'])
         │
         ▼
[4] repo.create(form_path, spec, data)
         │
         ▼
[5] FormTriggerManager.on_form_saved()
         │
         ├─→ KanbanRegistry.get_kanbans_for_form("pedidos")
         │        └─→ Returns: ["pedidos_kanban"]
         │
         ├─→ ProcessFactory.create_from_form()
         │        ├─→ Load kanban config
         │        ├─→ Get initial state
         │        ├─→ Apply field_mapping
         │        ├─→ Generate process_id
         │        └─→ Save to WorkflowRepository
         │
         ▼
[6] process_id = "proc_pedidos_1730032800_42"
         │
         ▼
[7] AutoTransitionEngine.check_auto_progression(process_id)
         │
         ├─→ Load process
         ├─→ Check if current_state has auto_transition_to
         ├─→ If YES:
         │      ├─→ Check prerequisites (non-blocking)
         │      ├─→ Check timeout
         │      ├─→ Execute transition
         │      └─→ Recurse (max 3 levels)
         │
         ▼
[8] AgentOrchestrator.run_analysis(process_id)
         │
         ├─→ Get agent for current state
         ├─→ agent.analyze_context()
         ├─→ agent.suggest_transition()
         └─→ Store suggestion
         │
         ▼
[9] Redirect to /workflow/board/pedidos
         │
         ▼
[10] USER SEES:
     - Process card in kanban board
     - Agent suggestion badge (if any)
     - Analytics updated
```

### 11.4 Estrutura de Diretórios

```
VibeCForms/
│
├── src/
│   ├── VibeCForms.py                # Main Flask application
│   │
│   ├── templates/                   # Jinja2 templates
│   │   ├── index.html              # Landing page
│   │   ├── form.html               # Form CRUD page
│   │   ├── edit.html               # Edit page
│   │   ├── workflow_board.html     # Kanban board
│   │   ├── workflow_admin.html     # Visual editor
│   │   ├── workflow_analytics.html # Analytics dashboard
│   │   ├── workflow_audit.html     # Audit timeline
│   │   └── fields/                 # Field templates
│   │       ├── input.html
│   │       ├── textarea.html
│   │       ├── checkbox.html
│   │       ├── select.html
│   │       └── ...
│   │
│   ├── static/                      # Static assets
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── kanban.css
│   │   └── js/
│   │       ├── kanban_board.js     # Drag & drop
│   │       ├── visual_editor.js    # Admin editor
│   │       └── analytics.js        # Charts
│   │
│   ├── specs/                       # Form specifications
│   │   ├── contatos.json
│   │   ├── pedidos.json
│   │   └── rh/
│   │       └── candidatos.json
│   │
│   ├── config/                      # Configuration files
│   │   ├── persistence.json        # Backend config
│   │   ├── schema_history.json     # Schema tracking
│   │   └── kanbans/                # Kanban definitions
│   │       ├── pedidos.json
│   │       ├── tickets.json
│   │       └── contratacao.json
│   │
│   ├── persistence/                 # Persistence layer
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseRepository
│   │   ├── factory.py              # RepositoryFactory
│   │   ├── workflow_repository.py  # WorkflowRepository
│   │   ├── config.py               # Config loader
│   │   ├── migration_manager.py    # Migration system
│   │   ├── schema_detector.py      # Schema change detection
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── txt_adapter.py      # TXT backend
│   │       ├── sqlite_adapter.py   # SQLite backend
│   │       ├── mysql_adapter.py    # MySQL backend
│   │       └── postgresql_adapter.py
│   │
│   ├── workflow/                    # Workflow engine
│   │   ├── __init__.py
│   │   ├── kanban_registry.py      # Kanban-Form mapping
│   │   ├── form_trigger_manager.py # Form save hooks
│   │   ├── process_factory.py      # Process creation
│   │   ├── auto_transition_engine.py # Auto-transitions
│   │   ├── prerequisite_checker.py # Prerequisite validation
│   │   └── agents/                 # AI Agents
│   │       ├── __init__.py
│   │       ├── base_agent.py       # BaseAgent class
│   │       ├── agent_orchestrator.py
│   │       ├── context_loader.py
│   │       ├── orcamento_agent.py
│   │       ├── pedido_agent.py
│   │       └── entrega_agent.py
│   │
│   ├── analytics/                   # Analytics & ML
│   │   ├── __init__.py
│   │   ├── pattern_analyzer.py     # Pattern detection
│   │   ├── anomaly_detector.py     # Anomaly detection
│   │   ├── bottleneck_analyzer.py  # Bottleneck identification
│   │   └── ml_models/
│   │       ├── duration_predictor.py
│   │       └── risk_classifier.py
│   │
│   ├── exports/                     # Export handlers
│   │   ├── __init__.py
│   │   ├── csv_exporter.py
│   │   ├── pdf_exporter.py
│   │   └── excel_exporter.py
│   │
│   ├── *.txt                        # Data files (TXT backend)
│   ├── vibecforms.db                # SQLite database
│   │
│   └── backups/                     # Backup directory
│       └── migrations/
│
├── tests/                           # Test suite
│   ├── test_form.py                # Form tests (16 tests)
│   ├── test_persistence.py         # Persistence tests
│   ├── test_workflow.py            # Workflow tests
│   ├── test_agents.py              # Agent tests
│   └── test_analytics.py           # Analytics tests
│
├── docs/                            # Documentation
│   ├── CLAUDE.md                   # Claude Code guide
│   ├── planning/
│   │   └── workflow/
│   │       ├── workflow_kanban_planejamento_v4_parte1.md
│   │       ├── workflow_kanban_planejamento_v4_parte2.md
│   │       └── workflow_kanban_planejamento_v4_parte3.md
│   └── prompts.md                  # AI prompt history
│
├── pyproject.toml                   # Project config (Hatch)
├── requirements.txt                 # Dependencies
└── README.md                        # Project overview
```

### 11.5 Dependências Entre Módulos

```
VibeCForms.py (Flask app)
    │
    ├─→ persistence/factory.py (RepositoryFactory)
    │       └─→ persistence/adapters/*.py (Backends)
    │
    ├─→ workflow/form_trigger_manager.py
    │       ├─→ workflow/kanban_registry.py
    │       └─→ workflow/process_factory.py
    │               └─→ persistence/workflow_repository.py
    │
    ├─→ workflow/auto_transition_engine.py
    │       ├─→ workflow/prerequisite_checker.py
    │       └─→ persistence/workflow_repository.py
    │
    ├─→ workflow/agents/agent_orchestrator.py
    │       ├─→ workflow/agents/base_agent.py
    │       ├─→ workflow/agents/*_agent.py
    │       └─→ workflow/agents/context_loader.py
    │
    ├─→ analytics/pattern_analyzer.py
    │       └─→ persistence/workflow_repository.py
    │
    ├─→ analytics/anomaly_detector.py
    │       └─→ persistence/workflow_repository.py
    │
    └─→ exports/*.py
            └─→ persistence/workflow_repository.py


EXTERNAL DEPENDENCIES:
├─→ Flask (web framework)
├─→ scikit-learn (ML models)
├─→ pandas (data analysis)
├─→ reportlab (PDF generation)
├─→ openpyxl (Excel export)
└─→ pymysql / psycopg2 (SQL drivers)
```

---

## Próximos Passos

Após dominar a arquitetura, avance para:

**[Level 5 - Implementation](level_5_implementation.md)**: Exemplo completo (Order Flow), fases de implementação (50 dias), estratégia de testes

---

**Referência original**: `VibeCForms/docs/planning/workflow/workflow_kanban_planejamento_v4_parte2.md` (Seção 12)
