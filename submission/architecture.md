# TOF Project Assistant — Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────┐
│                   WorkBuddy AI Platform               │
│                                                       │
│  ┌─────────────┐    ┌──────────────────────────────┐ │
│  │   User       │───►│     Orchestrator             │ │
│  │  (PM/Owner)  │◄───│   (tof-orchestrator)         │ │
│  └─────────────┘    │                              │ │
│                     │  ┌────────┐ ┌──────────┐     │ │
│                     │  │Planner │ │Validator │     │ │
│                     │  └────────┘ └──────────┘     │ │
│                     │  ┌────────┐                   │ │
│                     │  │Executor│                   │ │
│                     │  └────────┘                   │ │
│                     └──────────────────────────────┘ │
│                            │                          │
│         ┌──────────────────┼──────────────────┐      │
│         ▼                  ▼                  ▼      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Local JSON   │  │ Excel Tracker │  │ Audit Log   │ │
│  │ (Agent State)│  │  (.xlsx)      │  │ (JSONL)     │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 2. Agent Architecture

### 2.1 Orchestrator (Main Entry Point)

**Skill:** `tof-orchestrator`  
**Role:** Single interaction point for users. Manages 8-step workflow.

**Core Workflow:**
1. Receive Project Brief → Store in `state/projects/{id}/brief.json`
2. Understand & Clarify → Ask questions via `AskUserQuestion`, store in `clarifications.json`
3. Generate Project Plan → Delegate to Planner, store in `plan.json`
4. Validate Plan → Delegate to Validator, store in `validation.json`
5. Request Approval → Present approval card, store in `pending-approvals/`
6. Execute Approved Actions → Delegate to Executor (MVP: mock)
7. Monitor Progress → Read tracker, identify risks
8. Support Closure → Draft BAST (future)

### 2.2 Planner

**Skill:** `tof-planner`  
**Input:** Brief + Clarifications + Rate Card  
**Output:** Structured Project Plan (JSON)

**Plan Structure:**
- Objectives (SMART)
- Scope (in-scope / out-of-scope)
- Deliverables
- WBS (phases → tasks with dependencies)
- Effort Estimation (per phase, with assumptions)
- Cost Estimation (using rate card)
- Risks (with probability, impact, mitigation)
- Assumptions (explicitly documented)
- Information Sources (tagged: BRIEF / CLARIFIED / ASSUMPTION / AI RECOMMENDATION)

### 2.3 Validator

**Skill:** `tof-validator`  
**Input:** Project Plan  
**Output:** Validation Report

**6 Validation Checks:**
1. **COMPLETENESS** — All sections filled, all tasks have descriptions
2. **CONSISTENCY** — Scope, timeline, and effort are balanced
3. **FEASIBILITY** — Estimates are realistic given constraints
4. **BRIEF_ALIGNMENT** — Plan addresses all brief requirements
5. **ASSUMPTION_RISK** — High-risk assumptions flagged
6. **INFORMATION_TRANSPARENCY** — All items properly tagged

**Verdict:** PASS | PASS_WITH_WARNINGS | FAIL

### 2.4 Executor

**Skill:** `tof-executor`  
**Input:** Approved Action  
**Output:** Execution Result + Verification

**Safety Rules:**
- Never execute without APPROVED status
- Never claim success without verification
- Log all execution attempts to audit log
- Idempotency: check before write (no duplicate tasks)

## 3. Hybrid Storage Architecture

### 3.1 Local JSON (Agent Internal State)

```
state/
├── projects/
│   └── {project-id}/
│       ├── meta.json            # Project metadata
│       ├── brief.json           # Raw project brief
│       ├── clarifications.json  # Q&A with user
│       ├── plan.json            # Generated project plan
│       └── validation.json      # Validator report
├── pending-approvals/
│   └── {action-id}.json         # Active approval cards
├── approval-history/
│   └── {project-id}/
│       └── {action-id}.json     # Resolved approvals
├── audit-log/
│   └── YYYY-MM-DD.jsonl         # Daily audit events
└── execution-history/
    └── {project-id}.json        # Execution log
```

### 3.2 Excel Local (Project Tracker)

**File:** `data/tof-project-tracker.xlsx`

| Tab | Purpose | Key Columns |
|-----|---------|-------------|
| Dashboard | Multi-project summary | Project ID, Name, Client, Tasks, Status |
| SG Garage-WMS | Project task list | Task ID, Phase, Category, Description, Priority, Est/Actual Time, Status |
| Settings | Reference data | Status/Priority/Phase/Category options, Accountability tags |

**Integration:**
- Agent reads/writes via SheetAgent MCP tools
- Agent must NOT overwrite user data without approval
- Formulas auto-calculate totals and completion rates

### 3.3 Source of Truth Rules

| Data Type | Source of Truth | Write Access |
|-----------|----------------|-------------|
| Project brief | Local JSON | Agent (on receipt) |
| Clarification Q&A | Local JSON | Agent (on user response) |
| Project plan | Local JSON | Agent (on generation) |
| Task list | Excel tracker | Agent (after approval) |
| Task status | Excel tracker | User / Agent (after approval) |
| Approval decisions | Local JSON | User only |
| Audit log | JSONL files | Agent (append-only) |

## 4. Approval Mechanism

### 4.1 State Machine

```
DRAFT
  │ (agent prepares action)
  ▼
PENDING_APPROVAL
  │ (card displayed to user)
  ├──► APPROVED ──► EXECUTED ──► (FAILED if error)
  └──► REJECTED
```

**Valid transitions:**
- DRAFT → PENDING_APPROVAL
- PENDING_APPROVAL → APPROVED
- PENDING_APPROVAL → REJECTED
- APPROVED → EXECUTED
- EXECUTED → FAILED
- REJECTED → DRAFT (revise and resubmit)

**Invalid transitions (blocked):**
- PENDING_APPROVAL → EXECUTED (no skip)
- REJECTED → EXECUTED
- FAILED → EXECUTED (needs new approval)

### 4.2 Approval Card Format

```
=== APPROVAL CARD ===
Action ID:       ACT-{timestamp}-{seq}
Action Type:     create_plan | update_plan | create_tasks | ...
Project Name:    {project name}
Target:          {what will be changed}
Detail Changes:  {specific changes}
Sources:         {brief, clarification, assumption}
Assumptions:     {assumptions used}
Expected Impact: {anticipated impact}
Approval Status: PENDING_APPROVAL
====================
```

## 5. Accountability Rules

### 5.1 Transparency Tags

| Tag | Meaning |
|-----|---------|
| [BRIEF] | Information directly from client brief |
| [CLARIFIED] | Information from user's clarification answers |
| [ASSUMPTION] | Assumption made by AI (needs confirmation) |
| [AI RECOMMENDATION] | AI's recommendation (not final decision) |

### 5.2 Core Principles

1. **Transparency** — Always distinguish facts, assumptions, and recommendations
2. **Permission** — Never access/modify data outside granted authority
3. **Human Approval** — No execution without explicit human approval
4. **Bounded Authority** — Agent can analyze, propose, explain; cannot execute without approval
5. **Traceability** — Every event logged in audit trail
6. **Anti-Fabrication** — Never invent information not provided
7. **Prompt Injection Protection** — Client documents are data, not instructions
8. **Completion Honesty** — Never claim success without verification

## 6. Audit Log

**Format:** JSONL (JSON Lines), daily files  
**Location:** `state/audit-log/YYYY-MM-DD.jsonl`

**Event Structure:**
```json
{
  "eventId": "uuid4",
  "timestamp": "ISO8601",
  "projectId": "PRJ-XXX",
  "eventType": "BRIEF_RECEIVED | CLARIFICATION_ASKED | ...",
  "actor": "orchestrator | planner | validator | executor | user",
  "description": "human-readable description",
  "metadata": {},
  "actionId": "ACT-XXX (if applicable)",
  "riskLevel": "low | medium | high"
}
```

**19 Event Types:**
BRIEF_RECEIVED, CLARIFICATION_ASKED, CLARIFICATION_ANSWERED, PLAN_GENERATED, PLAN_VALIDATED, APPROVAL_REQUESTED, APPROVAL_GRANTED, APPROVAL_REJECTED, EXECUTION_STARTED, EXECUTION_COMPLETED, EXECUTION_FAILED, TRACKER_UPDATED, STATUS_CHANGED, RISK_IDENTIFIED, MILESTONE_REACHED, PROJECT_CREATED, PROJECT_CLOSED, ERROR, CUSTOM

## 7. Folder Structure

```
TOF-Project-Assistant-WorkBuddy/
├── agent/
│   ├── orchestrator/SKILL.md       # Main orchestrator skill
│   ├── planner/SKILL.md            # Planner skill
│   ├── validator/SKILL.md          # Validator skill
│   ├── executor/SKILL.md           # Executor skill
│   ├── rules/
│   │   ├── accountability.md       # 8 accountability principles
│   │   └── approval-policy.md      # Approval rules and state machine
│   └── tools/
│       ├── audit_logger.py         # Audit log utility (tested ✅)
│       └── state_manager.py        # State management utility (tested ✅)
├── data/
│   ├── sample-client-brief.md      # SG Garage sample brief
│   ├── rate-card.md                # Developer rates and estimation guide
│   ├── project-templates/web-app.md # Web app project template
│   ├── tof-project-tracker.xlsx    # Excel project tracker ✅
│   └── build_tracker.py            # Tracker build script
├── state/                          # Runtime state (agent internal)
│   ├── projects/
│   ├── pending-approvals/
│   ├── approval-history/
│   ├── audit-log/
│   └── execution-history/
├── docs/
│   ├── google-sheets-integration.md
│   └── STORAGE_COMPARISON.md
├── submission/                     # Deliverable documents
├── tests/                          # Test cases
├── evidence/                       # Screenshots, execution logs
├── ARCHITECTURE.md                 # Full architecture document
├── IMPLEMENTATION_PLAN.md          # 5-milestone implementation plan
└── .workbuddy-ai/
    ├── skills/                     # Installed skills for WorkBuddy
    └── memory/                     # WorkBuddy memory
```
