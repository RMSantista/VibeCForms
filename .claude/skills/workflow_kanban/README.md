# Workflow Kanban Skill - Installation Guide

## Overview

This skill provides comprehensive knowledge and tools for developing the Kanban-Workflow system in VibeCForms v4.0.

**Package Contents:**
- 5 progressive knowledge levels (fundamentals → implementation)
- 3 functional Python scripts (validator, template generator, implementation assistant)
- 2 pre-configured kanban templates
- Complete documentation (4,520+ lines)

**Package Size:** ~200KB

**Dependencies:** None (uses Python standard library only)

---

## Installation

### Option 1: Manual Installation (Recommended)

1. **Extract the package:**
   ```bash
   unzip workflow_kanban.zip -d ~/.claude/skills/
   ```

2. **Verify installation:**
   ```bash
   ls ~/.claude/skills/workflow_kanban/
   ```

   You should see:
   ```
   SKILL.md
   README.md
   assets/
   references/
   scripts/
   ```

3. **Test the scripts:**
   ```bash
   # Test validator
   python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py --help

   # Test template generator
   python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py --list

   # Test implementation assistant
   python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py
   ```

### Option 2: Direct Download

If you're already in the VibeCForms project:

```bash
# The skill is already present at:
.claude/skills/workflow_kanban/

# No installation needed, just use it!
```

---

## Quick Start

### 1. Learn the System

Start with Level 1 fundamentals:

```bash
cat ~/.claude/skills/workflow_kanban/references/level_1_fundamentals.md
```

Progress through levels 2-5 as needed.

### 2. Generate Your First Kanban

```bash
# Generate from template
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py \
  --template order_flow \
  --output my_first_kanban.json

# Validate it
python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py \
  my_first_kanban.json
```

### 3. Plan Implementation

```bash
# View roadmap
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py

# View Phase 1 checklist
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --phase 1
```

---

## Skill Structure

```
workflow_kanban/
├── SKILL.md                          # Main skill definition
├── README.md                         # This file
│
├── references/                       # Progressive documentation
│   ├── level_1_fundamentals.md      # Core concepts (Novice)
│   ├── level_2_engine.md            # AutoTransition, AI (Competent)
│   ├── level_3_interface.md         # Visual Editor, Dashboard (Proficient)
│   ├── level_4_architecture.md      # Complete architecture (Advanced)
│   └── level_5_implementation.md    # 5 phases, 50 days, 150 tests (Master)
│
├── scripts/                          # Functional tools
│   ├── kanban_validator.py          # Validate kanban JSON files
│   ├── template_generator.py        # Generate kanban templates
│   └── implementation_assistant.py  # Implementation phase guide
│
└── assets/
    └── templates/                    # Pre-configured templates
        ├── order_flow.json           # Order workflow template
        └── support_ticket.json       # Support ticket template
```

---

## Usage in Claude Code

Once installed, the skill appears in Claude Code's skill list:

```
/skills
```

You'll see:

```
workflow_kanban - Provides comprehensive knowledge and practical tools
for developing the Kanban-Workflow system in VibeCForms v4.0.
```

### Activate the Skill

In Claude Code, simply mention workflow-related tasks:

```
"Help me implement the AutoTransitionEngine for the kanban workflow"
```

Or explicitly invoke:

```
Use the workflow_kanban skill to plan Phase 2 implementation
```

---

## Common Workflows

### Workflow A: Create New Kanban

```bash
# 1. Generate template
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py \
  --template order_flow --output kanban.json

# 2. Edit kanban.json as needed

# 3. Validate
python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py kanban.json

# 4. Deploy
cp kanban.json /path/to/VibeCForms/src/config/kanbans/
```

### Workflow B: Plan Implementation

```bash
# View overall roadmap
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py

# Deep dive into specific phase
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --phase 2

# Check progress regularly
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --check
```

### Workflow C: Validate Existing Kanban

```bash
python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py \
  /path/to/existing/kanban.json
```

---

## Available Templates

### 1. Order Flow (`order_flow`)
Complete order processing workflow:
- States: Orçamento → Pedido → Em Entrega → Concluído
- AI Agents: OrcamentoAgent, PedidoAgent, EntregaAgent
- Prerequisites: Payment validation, time checks

### 2. Support Ticket (`support_ticket`)
Support ticket management:
- States: Novo → Em Análise → Resolvido
- Prerequisites: Priority assignment, response time

---

## Scripts Reference

### kanban_validator.py

**Purpose:** Validate kanban JSON files for correctness

**Usage:**
```bash
python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py <kanban.json>
```

**Validates:**
- JSON schema correctness
- Required fields (id, name, states, transitions)
- Transition consistency (from/to states exist)
- Prerequisite types (4 valid types)
- Infinite cycle detection
- Generates detailed error/warning report

### template_generator.py

**Purpose:** Generate pre-configured kanban templates

**Usage:**
```bash
# List templates
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py --list

# Generate template
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py \
  --template order_flow --output kanban.json
```

**Available Templates:**
- `order_flow` - Order processing (4 states)
- `support_ticket` - Support management (3 states)
- `hiring` - Hiring process (coming soon)
- `approval` - Approval flow (coming soon)

### implementation_assistant.py

**Purpose:** Guide implementation phase by phase

**Usage:**
```bash
# Overview
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py

# Phase details
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --phase 1

# Check progress
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --check
```

**Shows:**
- 5 implementation phases (50 days total)
- Daily checklists per phase
- Test count targets
- File deliverables
- Progress tracking

---

## Knowledge Levels Guide

### Level 1: Fundamentals (Start Here)
- **Target:** Developers new to the project
- **Topics:** Core concepts, Kanban-Form architecture, pluggable persistence
- **When to read:** Understanding project basics, first time on the project

### Level 2: Engine
- **Target:** Developers implementing core features
- **Topics:** AutoTransitionEngine, AI Agents, PatternAnalyzer
- **When to read:** Implementing transitions, automation, pattern analysis

### Level 3: Interface
- **Target:** Developers working on UI/UX
- **Topics:** Visual Editor, Analytics Dashboard, Exports, Audit Interface
- **When to read:** Building visual interfaces, dashboards, user-facing features

### Level 4: Architecture
- **Target:** Architects and tech leads
- **Topics:** Complete technical architecture, component diagrams
- **When to read:** Planning architecture, reviewing technical decisions

### Level 5: Implementation
- **Target:** Project managers and implementers
- **Topics:** 5 implementation phases, 50 days roadmap, 150+ tests
- **When to read:** Planning implementation, defining schedules, creating tests

---

## System Requirements

- **Python:** 3.7+ (no external dependencies)
- **Claude Code:** Latest version
- **VibeCForms:** v3.0+ (with pluggable persistence system)

---

## Core Principles

**"Warn, Not Block" Philosophy:**
Prerequisites NEVER block transitions. They warn users and require justification for forced transitions, but maintain user autonomy.

**Key Concepts:**
- **Kanban = Workflow Definition**: Kanbans define business rules and workflow logic
- **1:N Kanban-Form Relationship**: One kanban can generate processes from multiple forms
- **Automatic Process Generation**: Saving a form automatically creates a workflow process
- **3 Transition Types**: Manual (user), System (automatic), Agent (AI-suggested)
- **Pluggable Persistence**: TXT (default), SQLite, MySQL, PostgreSQL, MongoDB

---

## Implementation Phases Summary

| Phase | Duration | Focus | Tests |
|-------|----------|-------|-------|
| **1** | 10 days | Core Kanban-Form Integration | 30 |
| **2** | 10 days | AutoTransitionEngine | 40 |
| **3** | 10 days | Basic AI (Pattern Analysis) | 40 |
| **4** | 10 days | Visual Editor + Dashboard | 30 |
| **5** | 10 days | Advanced Features (Audit, Export) | 10 |
| **Total** | **50 days** | **Complete v4.0 System** | **150** |

---

## Troubleshooting

### Script doesn't run
```bash
# Check Python version
python3 --version  # Should be 3.7+

# Make scripts executable
chmod +x ~/.claude/skills/workflow_kanban/scripts/*.py
```

### Skill not appearing in Claude Code
```bash
# Verify installation path
ls ~/.claude/skills/workflow_kanban/SKILL.md

# Restart Claude Code
```

### Validation errors
Consult Level 1 documentation for correct kanban structure:
```bash
cat ~/.claude/skills/workflow_kanban/references/level_1_fundamentals.md
```

---

## Support & Contribution

**Documentation Source:** `/docs/planning/workflow/workflow_kanban_planejamento_v4_parte*.md`

**Project:** VibeCForms v4.0 - Kanban Workflow System

**Created by:** Rodrigo Santista

**Last Updated:** October 2025

---

## Quick Reference Card

```bash
# Most Common Commands
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py --list
python3 ~/.claude/skills/workflow_kanban/scripts/template_generator.py --template order_flow --output k.json
python3 ~/.claude/skills/workflow_kanban/scripts/kanban_validator.py k.json
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py
python3 ~/.claude/skills/workflow_kanban/scripts/implementation_assistant.py --phase 1

# Documentation
cat ~/.claude/skills/workflow_kanban/references/level_1_fundamentals.md
cat ~/.claude/skills/workflow_kanban/references/level_5_implementation.md
```

---

**Ready to start? Begin with Level 1 fundamentals!** 🚀
