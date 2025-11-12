# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Framework Overview

VibeCForms is an **AI-first framework for building process tracking systems** with seamless collaboration between humans, AI agents, and code. Unlike traditional CRUD frameworks, VibeCForms is designed for systems that track multi-step processes (sales pipelines, laboratory workflows, legal cases) where objects move through states and multiple actors (human, AI, or code) can observe and act on those transitions.

**Core Philosophy: Convention over Configuration, Configuration over Code**

This creates a clear development hierarchy:
1. **Convention** - Use well-defined conventions that require no setup
2. **Configuration** - When customization is needed, use JSON configuration files
3. **Code** - Write code only for truly unique business logic

When building with VibeCForms, always prefer conventions first, fall back to configuration when needed, and only write code when neither convention nor configuration can solve the problem.

---

## Building with VibeCForms

### The Eight Core Conventions

VibeCForms provides eight well-defined conventions that enable rapid development:

#### 1. 1:1 CRUD-to-Table Mapping
**Convention:** Every form maps directly to exactly one table/storage backend.

**Implementation:**
- Form path determines storage location: `contatos` → `contatos.txt` or `contatos` table in SQLite
- Nested forms flatten to underscores: `financeiro/contas` → `financeiro_contas.txt`
- No hidden abstractions or complex ORM mappings
- Each form is independent and self-contained

**When to Use:**
- Default behavior, no action required
- Create a JSON spec file in `src/specs/` and you get automatic storage

**Example:**
```python
# In VibeCForms.py, the mapping is automatic:
data_file = os.path.join('src', form_path.replace('/', '_') + '.txt')
```

#### 2. Shared Metadata
**Convention:** UI and database definitions come from the same source (the form spec JSON), ensuring they're always in sync.

**Implementation:**
- Form spec defines both UI rendering AND data structure
- Template system reads spec to generate HTML forms
- Persistence system reads spec to create/validate database schema
- Single source of truth eliminates sync issues

**When to Use:**
- Always - this is fundamental to VibeCForms
- Add a field to the spec → it appears in UI AND storage automatically

**Example spec** (`src/specs/contatos.json`):
```json
{
  "title": "Contatos",
  "icon": "fa-address-book",
  "fields": [
    {"name": "nome", "label": "Nome", "type": "text", "required": true},
    {"name": "telefone", "label": "Telefone", "type": "tel", "required": true},
    {"name": "email", "label": "Email", "type": "email", "required": false}
  ]
}
```

This single spec drives both the HTML form and the database schema.

#### 3. Relationship Tables for All Cardinality
**Convention:** All relationships use relationship tables, regardless of whether they're 1:1, 1:N, or N:N.

**Implementation:**
- Even 1:1 and 1:N relationships use intermediate tables
- Consistent pattern simplifies queries and migrations
- No foreign keys embedded in entity tables
- Relationship tables always have: `entity1_id`, `entity2_id`, optional metadata

**When to Use:**
- Whenever you need to relate two entities
- Example: `customer_orders` table relates `customers` to `orders` (even though it's 1:N)

**Why This Matters:**
- Uniform interface for AI agents to understand relationships
- Easy to upgrade 1:N to N:N without schema changes
- Simplified audit trails and history tracking

#### 4. Tags as State
**Convention:** Object states are represented by tags, making state explicit and queryable.

**Implementation:**
- Create a `tags` table: `object_name`, `object_id`, `tag`, `applied_at`, `applied_by`
- Tags represent states: "lead", "qualified", "proposal", "negotiation", "closed"
- Objects can have multiple tags simultaneously
- State transitions = tag operations (remove old tag, add new tag)

**When to Use:**
- Any system where objects move through states
- Sales pipelines, case management, workflow systems
- When multiple actors need to monitor state changes

**Example:**
```python
# Checking state
def has_tag(object_id, tag_name):
    return tag_exists(object_id, tag_name)

# Transitioning state
def move_to_proposal(deal_id, user_id):
    remove_tag(deal_id, "qualified")
    add_tag(deal_id, "proposal", user_id)
```

#### 5. Kanbans for State Transitions
**Convention:** Visual Kanban boards control how objects move between states (tags).

**Implementation:**
- Kanban columns represent states (tags)
- Dragging cards between columns = tag transitions
- Board configuration defines allowed transitions
- Each board is a view of objects filtered by relevant tags

**When to Use:**
- User-facing interface for state management
- Workflow systems where humans control progression
- Visual representation of process flow

**Configuration Example:**
```json
{
  "board_name": "Sales Pipeline",
  "columns": [
    {"tag": "lead", "label": "Leads"},
    {"tag": "qualified", "label": "Qualified"},
    {"tag": "proposal", "label": "Proposal Sent"},
    {"tag": "closed", "label": "Closed Won"}
  ],
  "object_type": "deals"
}
```

#### 6. Uniform Actor Interface
**Convention:** Humans, AI agents, and subsystems use the same interface to monitor tags and trigger actions.

**Implementation:**
- All actors query the same `tags` table
- All actors use the same functions: `add_tag()`, `remove_tag()`, `has_tag()`
- Tag changes trigger events that any actor can subscribe to
- No special APIs for different actor types

**When to Use:**
- Always, when building process tracking systems
- Enables seamless collaboration between humans, AI, and code

**Example:**
```python
# Human via Kanban board
kanban.move_card(deal_id, from_column="qualified", to_column="proposal")
  # → calls remove_tag(deal_id, "qualified")
  # → calls add_tag(deal_id, "proposal", user_id)

# AI agent monitoring
def ai_agent_check():
    qualified_deals = get_objects_with_tag("qualified")
    for deal in qualified_deals:
        if ai_recommends_proposal(deal):
            add_tag(deal.id, "ready_for_proposal", "ai_agent")

# Email subsystem
def email_monitor():
    proposal_deals = get_objects_with_tag("proposal")
    for deal in proposal_deals:
        if needs_followup(deal):
            send_followup_email(deal)
```

#### 7. Tag-Based Notifications
**Convention:** Simple notification system where any actor can monitor tag changes and react.

**Implementation:**
- Tag changes are events: `tag_added(object_name, object_id, tag, actor)`
- Actors subscribe to specific tags they care about
- Notifications trigger on tag operations
- No complex event bus - just watch the tags table

**When to Use:**
- When actors need to react to state changes
- Alerting managers when deals reach certain stages
- Triggering automated actions on state transitions

**Example:**
```python
# Manager notification on high-value deals
def notify_manager(object_id, tag_name, actor):
    if tag_name == "negotiation":
        deal = get_deal(object_id)
        if deal.value > 100000:
            send_notification(manager_email, f"High-value deal {deal.id} in negotiation")

# Subscribe to tag events
subscribe_to_tag("negotiation", notify_manager)
```

#### 8. Convention over Configuration, Configuration over Code
**Convention:** Use the hierarchy: conventions → configuration → code.

**Implementation:**
- **Use Convention When:** Standard CRUD, common field types, typical workflows
- **Use Configuration When:** Custom field layouts, specific backend selection, workflow definitions
- **Use Code When:** Complex business rules, external integrations, unique AI behaviors

**Decision Tree:**
1. Can convention handle it? → Use convention (no work required)
2. Can configuration handle it? → Create JSON config (no code required)
3. Neither works? → Write code (only when necessary)

**Examples:**

*Convention (no setup):*
- Directory structure becomes UI hierarchy

*Configuration (JSON only):*
```json
{
  "backend": "sqlite",
  "validation_messages": {
    "email": "Must be a valid email address"
  },
  "icon": "fa-users"
}
```

*Code (when needed):*
```python
def custom_validation(data):
    # Complex business rule that can't be expressed in config
    if data['age'] < 18 and data['type'] == 'unrestricted':
        return False, "Minors cannot have unrestricted access"
    return True, None
```

---

## Technical Implementation

Now that you understand the conventions, here's how to implement them using VibeCForms' existing infrastructure.

### Persistence System (Version 3.0)

The application uses a pluggable persistence system implementing the **1:1 CRUD-to-Table Mapping** convention.

#### Multi-Backend Architecture
The system implements three design patterns:
- **Repository Pattern**: Unified `BaseRepository` interface for all storage operations
- **Adapter Pattern**: Backend-specific implementations (TxtAdapter, SQLiteAdapter, etc.)
- **Factory Pattern**: `RepositoryFactory` creates appropriate repository instances

#### BaseRepository Interface
All backends implement these 11 methods:
```python
class BaseRepository(ABC):
    @abstractmethod
    def create(self, form_path: str, spec: dict, data: dict) -> bool
    @abstractmethod
    def read_all(self, form_path: str, spec: dict) -> list
    @abstractmethod
    def update(self, form_path: str, spec: dict, idx: int, data: dict) -> bool
    @abstractmethod
    def delete(self, form_path: str, spec: dict, idx: int) -> bool
    @abstractmethod
    def exists(self, form_path: str) -> bool
    @abstractmethod
    def has_data(self, form_path: str) -> bool
    @abstractmethod
    def create_storage(self, form_path: str, spec: dict) -> bool
    @abstractmethod
    def drop_storage(self, form_path: str) -> bool
    # ... +3 auxiliary methods
```

#### Supported Backends

**TXT (Original)**: Semicolon-delimited text files
- Path: `src/`
- Extension: `.txt`
- Delimiter: `;`
- Encoding: `utf-8`

**SQLite (Implemented)**: Embedded database
- Database: `src/vibecforms.db`
- Each form becomes a table
- Automatic type mapping (text, number, boolean)
- Timeout: 10 seconds

**Configured (Future)**: MySQL, PostgreSQL, MongoDB, CSV, JSON, XML
- Full configurations in `persistence.json`
- Architecture ready for implementation

#### Configuration (Convention → Configuration)
Backend selection is configured in `src/config/persistence.json`:
```json
{
  "default_backend": "txt",
  "backends": { ... },
  "form_mappings": {
    "contatos": "sqlite",
    "produtos": "sqlite",
    "*": "default_backend"
  }
}
```

This demonstrates **Configuration over Code**: changing backends requires only JSON edits, no code changes.

#### Migration System
The system includes automatic backend migration with:
1. **Change Detection**: Compares `persistence.json` with `schema_history.json`
2. **User Confirmation**: Web UI at `/migrate/confirm/<form_path>`
3. **Automatic Backup**: Creates backup in `src/backups/migrations/`
4. **Data Migration**: Copies all records to new backend
5. **History Update**: Updates `schema_history.json`

Successfully migrated 40 records:
- contatos: 23 records (TXT → SQLite)
- produtos: 17 records (TXT → SQLite)

#### Schema Change Detection (Shared Metadata Convention)
The system tracks schema changes using MD5 hashes, ensuring **UI and database stay in sync**:
- **ADD_FIELD**: Field added (automatic, no confirmation)
- **REMOVE_FIELD**: Field removed (requires confirmation if data exists)
- **CHANGE_TYPE**: Field type changed (requires confirmation)
- **CHANGE_REQUIRED**: Required flag changed (warning)

Schema history is tracked automatically in `src/config/schema_history.json`:
```json
{
  "contatos": {
    "last_spec_hash": "ee014237f822ba2d7ea15758cd6056dd",
    "last_backend": "sqlite",
    "last_updated": "2025-10-16T17:29:30.878397",
    "record_count": 23
  }
}
```

#### Key Classes

**RepositoryFactory** (`src/persistence/repository_factory.py`):
- Creates appropriate repository instances based on backend type
- Loads backend configuration from `persistence.json`

**MigrationManager** (`src/persistence/migration_manager.py`):
- Handles backend migrations
- Creates backups before migrations
- Rollback support on failure

**SchemaChangeDetector** (`src/persistence/schema_detector.py`):
- Computes MD5 hashes of specs
- Detects schema changes
- Identifies backend changes
- Requires confirmation for risky operations

**TxtRepository** (`src/persistence/adapters/txt_adapter.py`):
- Original TXT backend refactored into adapter pattern
- Maintains backward compatibility

**SQLiteRepository** (`src/persistence/adapters/sqlite_adapter.py`):
- New SQLite backend implementation
- Automatic table creation from specs
- Type-safe field mapping

---

### Template System (Shared Metadata Implementation)

The application uses Flask's Jinja2 templates, implementing the **Shared Metadata** convention by reading the same spec for both UI and data operations.

**Main Templates** (`src/templates/`):
- `index.html` - Landing page with form cards grid (99 lines)
- `form.html` - Main CRUD form page with sidebar navigation (124 lines)
- `edit.html` - Edit form page (101 lines)

**Field Templates** (`src/templates/fields/`):
Form fields are rendered using individual templates:
- `input.html` - Simple input types (text, tel, email, number, password, date, url, search, datetime-local, time, month, week, hidden)
- `textarea.html` - Textarea fields
- `checkbox.html` - Checkbox fields
- `select.html` - Dropdown selection fields
- `radio.html` - Radio button groups
- `color.html` - Color picker with live hex display
- `range.html` - Slider with live value display

The `generate_form_field()` function loads the appropriate template based on field type from the **spec** and renders it using `render_template_string()`. This provides:
- Complete separation of HTML from Python code
- UI automatically reflects spec changes
- Consistent field rendering across all forms
- Better maintainability and testability

---

### Dynamic Form Generation (Convention Implementation)

Forms are defined by JSON specification files in `src/specs/`, implementing **Convention over Configuration**.

**Form Specification Format:**
```json
{
  "title": "Form Title",
  "icon": "fa-icon-name",
  "fields": [
    {"name": "field", "label": "Label", "type": "text", "required": true}
  ],
  "validation_messages": {
    "all_empty": "Message for all empty",
    "field": "Field-specific message"
  }
}
```

**Supported Field Types (20 HTML5 types):**

**Basic Input Types:**
- `text` - Single-line text input
- `tel` - Telephone number input
- `email` - Email address input with validation
- `number` - Numeric input
- `password` - Password input (masked characters, not displayed in tables)
- `url` - URL input with validation
- `search` - Search input with enhanced UX

**Date and Time Types:**
- `date` - Date picker input
- `time` - Time picker input
- `datetime-local` - Combined date and time picker
- `month` - Month and year picker
- `week` - Week picker

**Selection Types:**
- `select` - Dropdown selection list (requires `options` array)
- `radio` - Radio button group (requires `options` array)
- `checkbox` - Boolean checkbox input

**Advanced Types:**
- `color` - Color picker with live hex value display
- `range` - Slider with live value display (supports `min`, `max`, `step` attributes)

**Other Types:**
- `textarea` - Multi-line text input
- `hidden` - Hidden field (not displayed in forms or tables)

**Field Options Format (for select/radio):**
```json
{
  "name": "field_name",
  "type": "select",
  "options": [
    {"value": "val1", "label": "Label 1"},
    {"value": "val2", "label": "Label 2"}
  ]
}
```

**Range Field Format:**
```json
{
  "name": "priority",
  "type": "range",
  "min": 1,
  "max": 10,
  "step": 1
}
```

**Search with Datasource Format:**
```json
{
  "name": "field_name",
  "type": "search",
  "datasource": "contatos"
}
```

**Icon Support:**
- Optional `icon` field in spec files (e.g., "fa-address-book")
- Icons display in menu and landing page cards
- Falls back to "fa-file-alt" if not specified

---

### Folder Configuration System (Configuration over Code)

Folders can be customized via `_folder.json` files - demonstrating **Configuration over Code**:

```json
{
  "name": "Display Name",
  "description": "Optional description",
  "icon": "fa-icon-name",
  "order": 1
}
```

**Features:**
- Custom folder names (e.g., "Recursos Humanos" instead of "Rh")
- Optional descriptions for documentation
- Custom icons override default mappings
- Order field for sorting menu items

---

### Route Structure

- `/` (GET): Main landing page with all forms as cards
- `/<path:form_name>` (GET/POST): Dynamic form page (supports nested paths)
- `/<path:form_name>/edit/<int:idx>` (GET/POST): Edit form entry
- `/<path:form_name>/delete/<int:idx>` (GET): Delete form entry

**Examples:**
- `/contatos` - Root level form
- `/financeiro/contas` - Nested form
- `/rh/departamentos/areas` - Multi-level nested form

All operations use the index position in the forms list (not a unique ID) to identify records.

---

## Development Commands

### Install dependencies
```bash
uv sync
uv run pre-commit install  # Install git hooks for code quality checks
```

### Run the application (development mode)
```bash
uv run hatch run dev
```
The server starts on `http://0.0.0.0:5000` with debug mode enabled

### Run the application (production mode with Gunicorn)
```bash
uv run hatch run serve
```
Runs with 4 workers on `http://0.0.0.0:5000`

### Run all tests
```bash
uv run hatch run test
```

### Run a specific test
```bash
uv run pytest tests/test_form.py::test_write_and_read_forms
```

### Run tests with verbose output
```bash
uv run pytest -v
```

### Format code
```bash
uv run hatch run format
```

### Check code formatting
```bash
uv run hatch run lint
```

### Run pre-commit hooks
```bash
uv run hatch run check
```

---

## Testing Approach

Tests in `tests/test_form.py` (16 total) import functions directly from `VibeCForms.py` and use pytest's `tmp_path` fixture to create temporary data files.

**Test Coverage:**
- Form read/write operations with specs
- CRUD operations (create, update, delete)
- Dynamic validation based on specs
- Spec file loading and validation
- Icon support in specs
- Folder configuration loading
- Menu generation with icons
- Hierarchical menu structure
- Sorting by order field

All tests pass without functional regressions.

---

## Extension Patterns

When extending VibeCForms, follow the convention hierarchy:

### 1. Start with Convention
Ask: "Can this be solved by existing conventions?"
- Adding a new form? → Just create a spec file (convention handles it)
- Need a relationship? → Use relationship table pattern (convention)
- Tracking states? → Use tags (convention)

### 2. Move to Configuration if Needed
Ask: "Can this be configured in JSON?"
- Custom backend? → Edit `persistence.json`
- Specific validation messages? → Add to spec
- Custom icons? → Add to spec or `_folder.json`

### 3. Write Code as Last Resort
Ask: "Is this truly unique logic?"
- Complex business rules → Write code
- External API integrations → Write code
- Custom AI agent behaviors → Write code

### Adding New Features

When working on new features:
- **Maintain backward compatibility** with existing spec format
- **Document all AI prompts** and interactions in `docs/prompts.md` (in Portuguese)
- **Add tests** for new functionality
- **Update relevant documentation** files
- **Follow the convention hierarchy** - don't write code when configuration would work

### Examples of Good Extensions

**Good (Uses Convention):**
```bash
# Adding a new form for products
# Just create the spec file - convention handles the rest
cat > src/specs/products.json << EOF
{
  "title": "Products",
  "fields": [...]
}
EOF
```

**Good (Uses Configuration):**
```json
// Need MySQL backend? Configure it, don't code it
{
  "form_mappings": {
    "products": "mysql"
  }
}
```

**Good (Code When Necessary):**
```python
# Complex business rule that can't be configured
def validate_discount(product, discount):
    if product.category == "premium" and discount > 0.15:
        return False, "Premium products cannot have >15% discount"
    return True, None
```

---

## Implementation Constraints

### Validation Rules
Validation messages are defined in each form's spec file under `validation_messages`:
- `all_empty`: Message when all required fields are empty
- `<field_name>`: Field-specific validation message

The `validate_form_data(spec, form_data)` function processes validation dynamically based on the spec.

### Data Integrity
Since records are identified by index position rather than unique IDs, concurrent edits or deletions can cause race conditions. The application is designed for single-user local use.

### Adding New Forms (Pure Convention)
To add a new form, simply:
1. Create a JSON spec file in `src/specs/` (optionally in a subfolder)
2. Include optional `icon` field for custom icon
3. The form will automatically appear in the menu and landing page
4. Data will be persisted to `<form_path_with_underscores>.txt` (or configured backend)

No code changes required - this is pure convention.

### Customizing Folders (Configuration)
To customize a folder:
1. Create `_folder.json` in the folder
2. Specify `name`, `description`, `icon`, and `order`
3. The menu will automatically use these settings

No code changes required - this is configuration.

---

## Recent Improvements

### Version 2.3.1

#### Improvement #7: Search with Autocomplete
- Added support for search fields with dynamic autocomplete from datasources
- New API endpoint `/api/search/contatos` for querying contact names
- Real-time suggestions as users type (300ms debounce for performance)
- Uses HTML5 datalist for native browser autocomplete
- Case-insensitive substring matching
- Created `search_autocomplete.html` template
- Enhanced `generate_form_field()` to detect `datasource` attribute

#### Improvement #8: Responsive Table with Horizontal Scroll
- Tables now wrapped in scrollable container (`table-wrapper`)
- Horizontal scroll appears automatically when table exceeds container width
- Minimum table width of 600px for readability
- No more layout breaking on narrow screens or forms with many columns
- Applied to `form.html` template
- Seamless experience on mobile devices

### Version 2.3

#### Improvement #6: Complete HTML5 Field Type Support
- Expanded from 8 to 20 supported field types (100% HTML5 coverage)
- Added 4 new field templates: `select.html`, `radio.html`, `color.html`, `range.html`
- Enhanced `generate_form_field()` to handle options array and min/max/step attributes
- Improved `generate_table_row()` to display labels, color swatches, and masked passwords
- All 16 existing tests continue to pass
- Zero breaking changes - fully backward compatible

### Version 2.2

#### Improvement #4: Field Template System
- Separated field rendering into individual Jinja2 templates
- Created `src/templates/fields/` directory with dedicated templates
- Complete separation of field HTML from Python logic
- Extended support to include password and date input types

#### Improvement #5: Form Layout Enhancement
- Improved form field layout with horizontal label-input alignment
- Labels with fixed width (180px) for consistent alignment
- Inputs expand to fill remaining space
- Applied consistently to both `form.html` and `edit.html` templates

### Version 2.1

#### Improvement #1: Icon Support
- Added optional `icon` field to form specs
- Eliminates hardcoded icon mappings
- Icons display consistently in menu and cards

#### Improvement #2: Folder Configuration
- Added `_folder.json` for declarative folder config
- Supports custom names, descriptions, icons, and sort order
- No code changes needed for customization

#### Improvement #3: Template System
- Separated HTML into dedicated template files
- Reduced main file from 925 to 587 lines (-36.5%)
- Better IDE support and maintainability
- Follows Flask best practices
