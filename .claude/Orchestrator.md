# Orchestrator - VibeCForms Development Workflow

**Based on**: [The Orchestrator Pattern: Managing AI Work at Scale](https://ronie.medium.com/the-orchestrator-pattern-managing-ai-work-at-scale-a0f798d7d0fb) - Ronie Uliana, Jan 2026

---

## Fundamental Concepts

> "The bottleneck is not the model's capability - it's the human operator"

The Orchestrator acts as a **Tech Lead who refuses to write code**:
- Coordinates specialized agents
- Defines clear goals per stage
- Establishes explicit success criteria
- Validates results before proceeding

### What makes the pattern work

1. **Clear goals** - Each stage knows exactly what to deliver
2. **Explicit stopping conditions** - Objective criteria for "done"
3. **Verification at each stage** - Validation before advancing

### Two pitfalls the pattern avoids

1. ❌ Single agent doing planning + execution + validation as continuous blob
2. ❌ Success criteria not explicit

---

## Execution Mode

For autonomous work without unnecessary interruptions:

```bash
claude --allow-dangerously-skip-permissions
```

**Practical benefit**: Let Claude Code work 20-40 minutes without babysitting.

---

## Initial Setup

Before starting any development, ask the user:

### What is the desired interaction level?

| Level | When to Approve | Ideal For |
|-------|-----------------|-----------|
| **Low** | Only at end of complete development | Large features, extensive refactoring |
| **Medium** | At each completed phase | Typical development |
| **High** | At each completed step | Critical features, learning |

---

## Available Agents

| Agent | Role | Model | Color |
|-------|------|-------|-------|
| **rex** | Project documentation specialist | haiku | purple |
| **gus** | Pragmatic Python/Flask implementer | sonnet | orange |
| **tir** | Production code reviewer | sonnet | yellow |

---

## Development Workflow

### Phase 1: Understanding

**Responsible**: rex (haiku)
**Goal**: Understand requirements and project context

| Step | Action | Verification |
|------|--------|--------------|
| 1.1 | Analyze user requirements | Scope documented |
| 1.2 | Identify applicable VibeCForms conventions | Conventions listed |
| 1.3 | Map relevant existing files | Files identified |

**✓ Success Criteria**: Clear scope and conventions identified

**→ Approval**: If level = High

---

### Phase 2: Planning

**Responsible**: Orchestrator
**Goal**: Design technical solution

| Step | Action | Verification |
|------|--------|--------------|
| 2.1 | Define technical scope | Scope documented |
| 2.2 | List files to create/modify | Complete list |
| 2.3 | Define success criteria per stage | Objective criteria |

**✓ Success Criteria**: Written and structured plan

**→ Approval**: If level = High

---

### Phase 3: Implementation

**Responsible**: gus (sonnet)
**Goal**: Code following conventions

| Step | Action | Verification |
|------|--------|--------------|
| 3.1 | Implement code following conventions | Code written |
| 3.2 | Write tests for functionality | Tests created |
| 3.3 | Run tests: `uv run pytest` | All passing |

**✓ Success Criteria**: All tests passing

**→ Approval**: If level = High

---

### Phase 4: Review

**Responsible**: tir (sonnet)
**Goal**: Review code for production

| Step | Action | Verification |
|------|--------|--------------|
| 4.1 | Review implemented code | Full review complete |
| 4.2 | Verify adherence to 8 conventions | Conventions followed |
| 4.3 | Identify dead code and duplication | Issues documented |

**✓ Success Criteria**: Status = ACCEPTABLE

**→ Approval**: If level = Medium or High

---

### Phase 5: Validation

**Responsible**: gus (sonnet)
**Goal**: Fix issues and validate quality

| Step | Action | Verification |
|------|--------|--------------|
| 5.1 | Fix review issues (if any) | Issues resolved |
| 5.2 | Run all tests: `uv run hatch run test` | All passing |
| 5.3 | Format code: `uv run hatch run format` | Formatted |
| 5.4 | Check linting: `uv run hatch run lint` | 0 errors, 0 warnings |

**✓ Success Criteria**: 0 errors, 0 warnings, all tests passing

**→ Approval**: If level = High

---

### Phase 6: Finalization

**Responsible**: Orchestrator
**Goal**: Document and commit

| Step | Action | Verification |
|------|--------|--------------|
| 6.1 | Update relevant documentation | Docs updated |
| 6.2 | Create commit with descriptive message | Commit created |

**✓ Success Criteria**: Commit created successfully

**→ HUMAN APPROVAL**: Always (all levels)

---

## Transition Rules

### Between Steps
- Only advance when current step verification passes
- If it fails, fix before proceeding
- Document blockers and solutions

### Between Phases
- Phase only completes when ALL steps pass
- Human approval per configured level
- If rejected, return to appropriate phase

### Correction Loops

```
Phase 4 (Review) → Status NOT ACCEPTABLE → Return to Phase 3 (Implementation)
Phase 5 (Validation) → Tests failing → Return to Phase 3 (Implementation)
Phase 6 (Finalization) → Human rejects → Return per feedback
```

---

## Communication Model

### During Autonomous Execution
- Agent reports start of each phase
- Agent reports completion of each step
- Agent reports blockers immediately

### At Approval Points
- Summary of what was done
- Evidence of success (tests, lint, review)
- Next planned steps
- Await explicit approval

---

## Execution Example

```
[Orchestrator] Starting feature X development
[Orchestrator] Interaction level: Medium

--- Phase 1: Understanding (rex) ---
[rex] Analyzing requirements...
[rex] Applicable conventions: 1:1 CRUD, Shared Metadata
[rex] Relevant files: src/persistence/base.py, src/services/tag_service.py
[rex] ✓ Phase 1 complete

--- Phase 2: Planning (Orchestrator) ---
[Orchestrator] Scope: Add archive_old_deals method to TagService
[Orchestrator] Files: src/services/tag_service.py, tests/test_tag_service.py
[Orchestrator] ✓ Phase 2 complete

--- Phase 3: Implementation (gus) ---
[gus] Implementing archive_old_deals...
[gus] Writing tests...
[gus] Running pytest... 15/15 passed
[gus] ✓ Phase 3 complete

--- Phase 4: Review (tir) ---
[tir] Reviewing implementation...
[tir] Status: ACCEPTABLE
[tir] ✓ Phase 4 complete

→ APPROVAL (Medium level): Awaiting human approval...

[Human] Approved!

--- Phase 5: Validation (gus) ---
[gus] Running complete test suite...
[gus] Formatting code...
[gus] Checking lint...
[gus] ✓ Phase 5 complete

--- Phase 6: Finalization ---
[Orchestrator] Updating documentation...
[Orchestrator] Creating commit...
[Orchestrator] ✓ Phase 6 complete

→ FINAL APPROVAL: Awaiting human approval...
```

---

## Workflow Verification Checklist

Use this checklist to ensure the workflow is being followed:

- [ ] Interaction level defined at start
- [ ] Each step has clear success criteria
- [ ] Verifications executed before advancing
- [ ] Correct agent for each phase
- [ ] Approval at correct points
- [ ] Tests passing before commit
- [ ] Lint and format executed
- [ ] Documentation updated

---

## Quick Command Reference

```bash
# Development
uv run app examples/<business-case>     # Run application
uv run pytest                           # Run tests
uv run pytest tests/test_x.py::test_y   # Run specific test

# Quality
uv run hatch run test                   # Complete test suite
uv run hatch run format                 # Format code
uv run hatch run lint                   # Check linting
uv run hatch run check                  # Pre-commit hooks

# Installation
uv sync                                 # Install dependencies
uv run pre-commit install               # Install git hooks
```

---

## The 8 VibeCForms Conventions

Quick reference for reviews:

1. **1:1 CRUD-to-Table Mapping** - Each form maps to one table
2. **Shared Metadata** - UI and DB use same JSON spec
3. **Relationship Tables** - All relationships via intermediate tables
4. **Tags as State** - States represented by tags
5. **Kanbans for State Transitions** - Visual boards for transitions
6. **Uniform Actor Interface** - Humans, AI and code use same interface
7. **Tag-Based Notifications** - Events based on tag changes
8. **Convention→Configuration→Code** - Preference hierarchy
