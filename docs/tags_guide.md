# Tags as State - User Guide

## Overview

VibeCForms implements **Convention #4: Tags as State**, a powerful system for tracking object states through workflows. Instead of using status fields or enum columns, VibeCForms uses **tags** to represent states, enabling flexible multi-state workflows with full audit trails.

## What are Tags?

Tags are **labels** attached to records that represent their current state in a workflow. Think of them as sticky notes you can add or remove from a record.

### Example: Sales Pipeline

A deal might move through these states:

```
lead → qualified → proposal → negotiation → won
                                         → lost
```

In VibeCForms, each state is a **tag**:

```python
# New lead comes in
add_tag(deal_id, 'lead')

# Sales rep qualifies the lead
remove_tag(deal_id, 'lead')
add_tag(deal_id, 'qualified')

# Send proposal
remove_tag(deal_id, 'qualified')
add_tag(deal_id, 'proposal')
```

## Key Concepts

### 1. Tags Represent States

Instead of a single `status` field, objects can have multiple tags simultaneously:

```
Deal #1: ['qualified', 'priority', 'enterprise']
Deal #2: ['proposal', 'needs_followup']
Deal #3: ['won', 'recurring_revenue']
```

### 2. Multiple Tags Per Object

Objects can have multiple tags at the same time, allowing rich state representation:

```python
# A deal can be both qualified AND priority
add_tag(deal_id, 'qualified')
add_tag(deal_id, 'priority')
add_tag(deal_id, 'enterprise')

# Check for combinations
if has_all_tags(deal_id, ['qualified', 'priority']):
    notify_sales_manager(deal_id)
```

### 3. Complete Audit Trail

Every tag application and removal is tracked:

- **When** was it added/removed?
- **Who** added/removed it? (user, AI agent, system)
- **Why** (optional metadata)

### 4. Multi-Actor Collaboration

Tags enable seamless collaboration between:

- **Humans** - Sales reps, managers (via Kanban boards)
- **AI Agents** - Automated qualification, lead scoring
- **Systems** - Email monitoring, data enrichment, notifications

All actors use the **same interface** to read and modify tags.

## Using Tags in VibeCForms

### Basic Tag Operations

#### Adding Tags

```python
from services.tag_service import get_tag_service

tag_service = get_tag_service()

# Add a tag
success = tag_service.add_tag(
    object_type='deals',           # Form path
    object_id='3HNMQR8PJSG0C9VW',  # 27-char Crockford ID
    tag='qualified',                # Tag name
    applied_by='user123',           # Who applied it
    metadata={'score': 85}          # Optional metadata
)
```

#### Checking Tags

```python
# Check if object has a specific tag
if tag_service.has_tag('deals', deal_id, 'qualified'):
    print("Deal is qualified!")

# Check if object has ANY of several tags
if tag_service.has_any_tag('deals', deal_id, ['qualified', 'proposal']):
    print("Deal is in active pipeline")

# Check if object has ALL specified tags
if tag_service.has_all_tags('deals', deal_id, ['qualified', 'priority']):
    notify_sales_manager(deal_id)
```

#### Getting Tags

```python
# Get all active tags for an object
tags = tag_service.get_tags('deals', deal_id)
# [
#     {
#         'tag': 'qualified',
#         'applied_at': '2025-01-14T10:30:00Z',
#         'applied_by': 'user123',
#         'metadata': {'score': 85},
#         'removed_at': None,
#         'removed_by': None
#     }
# ]

# Get just tag names (without metadata)
tag_names = tag_service.get_tag_names('deals', deal_id)
# ['qualified', 'priority', 'enterprise']
```

#### Removing Tags

```python
# Remove a specific tag
success = tag_service.remove_tag(
    object_type='deals',
    object_id=deal_id,
    tag='qualified',
    removed_by='user123'
)

# Remove all tags (reset state)
count = tag_service.remove_all_tags(
    object_type='deals',
    object_id=deal_id,
    removed_by='user123'
)
print(f"Removed {count} tags")
```

### State Transitions

The most common pattern is transitioning from one state to another:

```python
# Transition from 'qualified' to 'proposal'
success = tag_service.transition(
    object_type='deals',
    object_id=deal_id,
    from_tag='qualified',
    to_tag='proposal',
    actor='user123',
    metadata={'proposal_sent_at': '2025-01-14T15:30:00Z'}
)
```

This is equivalent to:
```python
tag_service.remove_tag('deals', deal_id, 'qualified', 'user123')
tag_service.add_tag('deals', deal_id, 'proposal', 'user123', metadata)
```

### Querying by Tag

Find all objects in a specific state:

```python
# Get all qualified deals
qualified_deals = tag_service.get_objects_with_tag('deals', 'qualified')
# ['3HNMQR8PJSG0C9VW', '7KMPQR9PJSG0C9VW', ...]

# Process each qualified deal
for deal_id in qualified_deals:
    deal = repo.read_by_id('deals', spec, deal_id)
    process_qualified_deal(deal)
```

## Tag Naming Conventions

Tags should follow these rules:

✅ **Lowercase only**: `qualified` not `Qualified`
✅ **Alphanumeric + underscores**: `needs_followup` not `needs-followup`
✅ **Descriptive**: `qualified` not `q`
✅ **Consistent**: Use the same tag names across your workflow

### Good Tag Names

```
lead
qualified
proposal
negotiation
won
lost
priority
needs_followup
high_value
enterprise
recurring_revenue
```

### Bad Tag Names

```
Qualified          # uppercase
needs-followup     # hyphen instead of underscore
q                  # too short, not descriptive
URGENT!!!          # uppercase, special chars
qualified lead     # spaces not allowed
```

## Tag History and Audit Trail

### Viewing Tag History

```python
# Get full history for an object
history = repo.get_tag_history('deals', deal_id)
# [
#     {
#         'tag': 'lead',
#         'event': 'applied',
#         'timestamp': '2025-01-10T09:00:00Z',
#         'actor': 'system',
#         'metadata': {'source': 'web_form'}
#     },
#     {
#         'tag': 'lead',
#         'event': 'removed',
#         'timestamp': '2025-01-12T14:30:00Z',
#         'actor': 'user123',
#         'metadata': None
#     },
#     {
#         'tag': 'qualified',
#         'event': 'applied',
#         'timestamp': '2025-01-12T14:30:00Z',
#         'actor': 'user123',
#         'metadata': {'score': 85}
#     }
# ]

# Get history for a specific tag
qualified_history = repo.get_tag_history('deals', deal_id, tag='qualified')
```

### Tag Statistics

```python
# Get tag usage statistics for a form
stats = repo.get_tag_statistics('deals')
# {
#     'lead': 45,
#     'qualified': 23,
#     'proposal': 12,
#     'negotiation': 8,
#     'won': 15,
#     'lost': 22
# }

# Use for reporting
total_pipeline = stats['qualified'] + stats['proposal'] + stats['negotiation']
win_rate = stats['won'] / (stats['won'] + stats['lost']) * 100
```

## Use Cases

### 1. Sales Pipeline

Track deals through sales stages:

```python
# New lead from website
add_tag(deal_id, 'lead', 'system', {'source': 'contact_form'})

# Sales rep qualifies
transition(deal_id, 'lead', 'qualified', 'sales_rep_1')

# Send proposal
transition(deal_id, 'qualified', 'proposal', 'sales_rep_1')

# Enter negotiation
transition(deal_id, 'proposal', 'negotiation', 'sales_rep_1')

# Win the deal!
transition(deal_id, 'negotiation', 'won', 'sales_rep_1',
          {'value': 50000, 'close_date': '2025-01-30'})
```

### 2. Case Management

Track support tickets or legal cases:

```python
# New ticket arrives
add_tag(ticket_id, 'open', 'system')
add_tag(ticket_id, 'priority_medium', 'system')

# Assign to engineer
add_tag(ticket_id, 'assigned', 'system', {'assigned_to': 'eng_42'})

# Engineer starts work
transition(ticket_id, 'open', 'in_progress', 'eng_42')

# Issue resolved
transition(ticket_id, 'in_progress', 'resolved', 'eng_42',
          {'resolution': 'Updated config file'})

# Customer confirms
transition(ticket_id, 'resolved', 'closed', 'customer_123')
```

### 3. Laboratory Workflow

Track samples through analysis stages:

```python
# Sample received
add_tag(sample_id, 'received', 'lab_tech_1',
       {'received_at': '2025-01-14T08:00:00Z'})

# Preparation
transition(sample_id, 'received', 'preparing', 'lab_tech_1')

# Analysis
transition(sample_id, 'preparing', 'analyzing', 'lab_tech_2',
          {'instrument': 'mass_spec_3'})

# Quality control
transition(sample_id, 'analyzing', 'qc_review', 'lab_supervisor')

# Results approved
transition(sample_id, 'qc_review', 'approved', 'lab_supervisor',
          {'results_url': '/reports/sample_12345.pdf'})
```

### 4. Multi-Actor Collaboration

Human, AI, and system working together:

```python
# System creates lead from web form
add_tag(deal_id, 'lead', 'system', {'source': 'website'})

# AI agent enriches and scores lead
add_tag(deal_id, 'ai_scored', 'ai_agent',
       {'score': 92, 'company_size': 500, 'industry': 'SaaS'})

# AI recommends qualification
if ai_score > 80:
    add_tag(deal_id, 'ai_recommended', 'ai_agent')

# Human reviews and qualifies
if has_tag(deal_id, 'ai_recommended'):
    transition(deal_id, 'lead', 'qualified', 'sales_rep_1')

# Email system monitors for responses
def email_monitor():
    proposal_deals = get_objects_with_tag('deals', 'proposal')
    for deal_id in proposal_deals:
        if days_since_email(deal_id) > 3:
            add_tag(deal_id, 'needs_followup', 'email_system')
            notify_sales_rep(deal_id)
```

## Storage Backends

Tags work identically across all backends:

### TXT Files

Tags are stored in `<form>_tags.txt`:

```
3HNMQR8PJSG0C9VW;qualified;2025-01-14T10:30:00Z;user123;{"score":85};;;
7KMPQR9PJSG0C9VW;proposal;2025-01-14T11:00:00Z;user456;{};;;
3HNMQR8PJSG0C9VW;priority;2025-01-14T12:00:00Z;manager1;{};;;
```

Format: `object_id;tag;applied_at;applied_by;metadata;removed_at;removed_by;`

### SQLite Database

Tags stored in global `tags` table:

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT NOT NULL,
    object_id VARCHAR(27) NOT NULL,
    tag TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    applied_by TEXT NOT NULL,
    removed_at TEXT,
    removed_by TEXT,
    metadata TEXT
);

CREATE INDEX idx_tags_object_id ON tags(object_id);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_tags_object_type_tag ON tags(object_type, tag);
```

## Configuration

### Enabling Tags

Tags are enabled by default for all forms. To customize per form:

**Form Spec** (`src/specs/deals.json`):

```json
{
  "title": "Deals",
  "fields": [...],
  "tags": {
    "enabled": true,
    "allow_multiple": true,
    "predefined_tags": ["lead", "qualified", "proposal", "won", "lost"]
  }
}
```

**Global Config** (`src/config/persistence.json`):

```json
{
  "default_backend": "sqlite",
  "tags": {
    "enabled_by_default": true,
    "storage_mode": "dedicated"
  }
}
```

### Predefined Tags

Specify allowed tags in form spec:

```json
{
  "tags": {
    "predefined_tags": [
      "lead",
      "qualified",
      "proposal",
      "negotiation",
      "won",
      "lost"
    ]
  }
}
```

When predefined tags are specified, only those tags can be applied to records.

## API Endpoints

VibeCForms provides REST API endpoints for tag operations:

### Add Tag

```http
POST /api/deals/tags/3HNMQR8PJSG0C9VW
Content-Type: application/json

{
  "tag": "qualified",
  "applied_by": "user123",
  "metadata": {"score": 85}
}
```

### Remove Tag

```http
DELETE /api/deals/tags/3HNMQR8PJSG0C9VW/qualified
```

### Get Tags

```http
GET /api/deals/tags/3HNMQR8PJSG0C9VW
```

Response:
```json
[
  {
    "tag": "qualified",
    "applied_at": "2025-01-14T10:30:00Z",
    "applied_by": "user123",
    "metadata": {"score": 85},
    "removed_at": null,
    "removed_by": null
  }
]
```

### Search by Tag

```http
GET /api/deals/search/tags?tag=qualified
```

Response:
```json
{
  "object_type": "deals",
  "tag": "qualified",
  "objects": [
    "3HNMQR8PJSG0C9VW",
    "7KMPQR9PJSG0C9VW"
  ]
}
```

### State Transition

```http
PUT /api/deals/tags/3HNMQR8PJSG0C9VW/transition
Content-Type: application/json

{
  "from": "qualified",
  "to": "proposal",
  "actor": "user123",
  "metadata": {"proposal_sent": true}
}
```

## Kanban Boards

Kanban boards provide visual interface for tag-based workflows (Convention #5).

### Board Configuration

**File:** `examples/demo/config/kanban_boards.json`

```json
{
  "sales_pipeline": {
    "title": "Sales Pipeline",
    "object_type": "deals",
    "columns": [
      {"tag": "lead", "label": "Leads", "color": "#gray"},
      {"tag": "qualified", "label": "Qualified", "color": "#blue"},
      {"tag": "proposal", "label": "Proposal", "color": "#yellow"},
      {"tag": "negotiation", "label": "Negotiation", "color": "#orange"},
      {"tag": "won", "label": "Won", "color": "#green"},
      {"tag": "lost", "label": "Lost", "color": "#red"}
    ]
  }
}
```

### Using Kanban

1. Navigate to `/kanban/sales_pipeline`
2. See deals organized by state (tag)
3. Drag cards between columns to change state
4. Dragging automatically removes old tag and adds new tag

**Behind the scenes:**
```python
# When user drags deal from "qualified" to "proposal"
kanban.move_card(deal_id, from_column='qualified', to_column='proposal')
  # Calls:
  remove_tag(deal_id, 'qualified', user_id)
  add_tag(deal_id, 'proposal', user_id)
```

## Best Practices

### DO

✅ **Use descriptive tag names** that clearly indicate state
✅ **Track who and when** for audit trail
✅ **Use metadata** to provide context (scores, reasons, etc.)
✅ **Query by tag** for workflow filtering
✅ **Check combinations** for complex logic (has_all_tags, has_any_tag)
✅ **Use transitions** for common state changes
✅ **Monitor tag history** for analytics and debugging

### DON'T

❌ **Don't use tags for data** (use fields instead)
  - Bad: `add_tag(record_id, 'priority_5')`
  - Good: `add_tag(record_id, 'priority', metadata={'level': 5})`

❌ **Don't create too many tags** (prefer metadata)
  - Bad: `high_priority`, `medium_priority`, `low_priority`
  - Good: `priority` with metadata `{'level': 'high'}`

❌ **Don't assume tag order** (tags are unordered)
❌ **Don't duplicate data in tags** that exists in fields
❌ **Don't skip the `applied_by` parameter** (important for audit)

## Performance Tips

### Indexing

For high-volume systems, ensure proper indexes:

```sql
-- SQLite automatically creates these for optimal tag queries
CREATE INDEX idx_tags_object_id ON tags(object_id);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_tags_object_type_tag ON tags(object_type, tag);
```

### Batch Operations

When processing many objects, cache tag queries:

```python
# SLOW: Query for each object
for deal_id in deal_ids:
    if has_tag('deals', deal_id, 'qualified'):
        process_deal(deal_id)

# FAST: Single query
qualified_deals = get_objects_with_tag('deals', 'qualified')
qualified_set = set(qualified_deals)

for deal_id in deal_ids:
    if deal_id in qualified_set:
        process_deal(deal_id)
```

### Active vs Historical Tags

By default, queries return only **active** tags. For better performance:

```python
# Only active tags (fast)
tags = get_tags('deals', deal_id, active_only=True)

# All tags including removed (slower, use for audit only)
all_tags = get_tags('deals', deal_id, active_only=False)
```

## Troubleshooting

### Tag Not Applied

**Problem:** `add_tag()` returns `False`

**Solutions:**
1. Check tag name format (lowercase, alphanumeric, underscores only)
2. Verify object ID exists and is valid
3. Check if tag already exists (can't add duplicate active tag)
4. Verify form has tags enabled

### Can't Find Objects by Tag

**Problem:** `get_objects_with_tag()` returns empty list

**Solutions:**
1. Verify tag name is correct (case-sensitive)
2. Check if tags were removed (use `active_only=False` to see all)
3. Verify object_type matches form path
4. Check backend configuration

### Tag History Missing

**Problem:** Tag history doesn't show expected events

**Solutions:**
1. Ensure tags were removed properly (not deleted)
2. Check if using correct object ID
3. Verify backend properly stores tag history
4. For TXT backend, check `.tags.txt` file exists

## Examples

### Complete Sales Workflow

```python
from services.tag_service import get_tag_service

tag_service = get_tag_service()

# 1. New lead created by web form
deal_id = repo.create('deals', spec, {'name': 'Acme Corp', 'value': 50000})
tag_service.add_tag('deals', deal_id, 'lead', 'system',
                    {'source': 'website', 'form_id': 'contact_us'})

# 2. AI agent scores the lead
ai_score = ai_score_lead(deal_id)
tag_service.add_tag('deals', deal_id, 'ai_scored', 'ai_agent',
                    {'score': ai_score, 'model': 'lead_scorer_v2'})

if ai_score > 80:
    tag_service.add_tag('deals', deal_id, 'priority', 'ai_agent')

# 3. Sales rep qualifies the lead
tag_service.transition('deals', deal_id, 'lead', 'qualified', 'sales_rep_1',
                      {'notes': 'Strong fit for Enterprise plan'})

# 4. Send proposal
send_proposal_email(deal_id)
tag_service.transition('deals', deal_id, 'qualified', 'proposal', 'sales_rep_1',
                      {'proposal_sent_at': datetime.now().isoformat()})

# 5. Monitor for response
def check_proposal_responses():
    proposal_deals = tag_service.get_objects_with_tag('deals', 'proposal')

    for deal_id in proposal_deals:
        tags = tag_service.get_tags('deals', deal_id)
        proposal_tag = next(t for t in tags if t['tag'] == 'proposal')
        sent_at = datetime.fromisoformat(proposal_tag['metadata']['proposal_sent_at'])

        if (datetime.now() - sent_at).days > 3:
            tag_service.add_tag('deals', deal_id, 'needs_followup', 'system',
                               {'days_waiting': (datetime.now() - sent_at).days})

# 6. Deal won!
tag_service.transition('deals', deal_id, 'proposal', 'won', 'sales_rep_1',
                      {'close_date': datetime.now().isoformat(),
                       'final_value': 55000})
```

## See Also

- [Crockford IDs](crockford_ids.md) - Understanding VibeCForms ID system
- [CLAUDE.md](../CLAUDE.md) - VibeCForms conventions and architecture
- [Kanban Workflow Skill](../.claude/skills/workflow_kanban/) - Kanban board implementation
