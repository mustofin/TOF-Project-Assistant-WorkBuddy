# TOF Project Assistant — Project Description

**Challenge B: Office Agent — Unstructured to Structured with Approval Gates**

---

## Overview

TOF Project Assistant is an accountable AI project management assistant that transforms unstructured client briefs into validated, structured project plans — with mandatory human approval before any action is taken. Built on the WorkBuddy AI platform, it serves as a digital project manager for TOF Solusi Digital, a software development company.

The agent accepts raw client briefs (free-form text), identifies information gaps, asks structured clarification questions, generates a Work Breakdown Structure (WBS) with effort and cost estimates, validates the plan against 6 quality checks, and presents an approval card before executing anything. It also generates professional quotation documents from approved plans.

**What makes it an Office Agent (Challenge B):**
- **Unstructured input:** Client briefs arrive as free-form text/documents
- **Structured output:** Project plans (JSON), Excel tracker tasks, quotation documents (DOCX)
- **Approval gates:** Every external action requires human approval via a state machine
- **Audit trail:** All 33 event types logged with timestamp, actor, and metadata

---

## Real-World Insight

At TOF Solusi Digital, we observed four recurring problems in software project management:

1. **Unstructured briefs** — Client requirements arrive via WhatsApp, email, or verbal communication. A typical brief says "I need a web app for my bengkel" with minimal detail about features, users, or constraints.

2. **Hidden assumptions** — Project plans silently embed assumptions ("developer works full-time", "no scope changes") that later cause disputes. Nobody flags them until it's too late.

3. **No approval gates** — When AI tools generate plans, they often execute changes directly (creating tasks, modifying timelines) without human oversight. This creates risk when the AI's assumptions are wrong.

4. **No traceability** — When something goes wrong, there's no record of who decided what and why. "Who approved adding 5 extra tasks?" is an unanswerable question.

These problems map directly to the hackathon's 5 accountability rules: show sources, stay within permissions, ask before acting, admit limits, and keep a record.

---

## Solution Design

### Architecture

The system has 5 layers:

1. **User Interface** — WorkBuddy AI chat (user = PM/Business Owner)
2. **Agent Layer** — 6 WorkBuddy skills:
   - **Orchestrator** (main entry, 8-step workflow)
   - **Planner** (brief → WBS with effort/cost/risk)
   - **Validator** (6 quality checks)
   - **Executor** (approved actions → Excel tracker)
   - **Quotation Generator** (plan → quotation document)
   - **UI Designer** (plan → screen inventory → mockups)
3. **Deterministic Tools** — 7 Python modules (118 assertions):
   - `gate.py` — Approval state machine + prompt injection detection (27 tests)
   - `validator.py` — Plan quality validator (14 tests)
   - `quote_gen.py` — Quotation calculator with terbilang (31 tests)
   - `ui_spec.py` — Plan → screen inventory + design tokens (26 tests)
   - `mockup_render.py` — Spec → HTML → PNG mockups (18 tests)
   - `audit_logger.py` — JSONL audit log, 33 event types
   - `state_manager.py` — Project state lifecycle management
4. **Hybrid Storage:**
   - Local JSON — Agent internal state (briefs, plans, approvals)
   - Excel (.xlsx) — Human-facing project tracker (3 tabs, 15 sample tasks)
   - Audit Log — JSONL daily files, append-only
   - UI design artifacts — spec JSON + HTML source + PNG per screen
5. **Accountability Layer** — 8 principles enforced:
   - Transparency tags: [BRIEF], [CLARIFIED], [ASSUMPTION], [AI RECOMMENDATION]
   - Approval state machine: DRAFT → PENDING → APPROVED → EXECUTED
   - Reject → Remediate → Approve loop
   - Prompt injection detection (10 patterns)
   - Bounded authority (CAN/CANNOT table)

### Approval State Machine

```
DRAFT → PENDING_APPROVAL → APPROVED → EXECUTED → (FAILED if error)
                    ↓
              REJECTED → DRAFT (revise and resubmit)
```

**Blocked transitions (enforced by gate.py):**
- PENDING_APPROVAL → EXECUTED (cannot skip approval)
- REJECTED → EXECUTED (rejected = no execution)
- FAILED → EXECUTED (must get new approval for retry)

### Mock Dataset

3 sample briefs for testing:
1. **Complete brief** (SG Garage WMS) — Full requirements, 4 unclear points
2. **Brief with gaps** (Kopi Nusantara POS) — 10 missing items requiring clarification
3. **Brief with prompt injection** (Toko Maju Jaya) — Contains "ignore all rules" injection attempt

### Test Results

- **Self-tests:** 7 modules, 95 tests, all passed
- **Challenge test cases:** 24 tests, 23 passed, 1 failed
  - The 1 failure (TC-002) is an intentional demonstration of honest reporting: keyword-based gap detection cannot match LLM-based semantic analysis. This limitation is documented, not hidden.

---

## Business Value

### For TOF Solusi Digital

| Metric | Before | After |
|--------|--------|-------|
| Brief analysis time | 30-60 min (manual) | < 5 min (automated) |
| Hidden assumptions | Undetected | Tagged with risk level |
| Approval traceability | None | Full audit trail (33 event types) |
| Quotation generation | 2-3 hours (manual) | < 1 min (automated) |
| UI mockup production | 1-2 days (manual) | < 2 min (14 screens from plan) |
| Plan quality checks | Ad hoc | 6 systematic checks |

### Scalability

- Current: Single project (SG Garage WMS)
- Next: Multi-project dashboard (M4 milestone)
- Future: Cloud Service DB for team collaboration (M5 milestone)

### Accountability Compliance

All 5 hackathon accountability rules are enforced:

| Rule | How Enforced | Evidence |
|------|-------------|----------|
| Shows sources | 4 transparency tags on every information item | 23 tagged items in sample plan |
| Within permissions | Bounded authority CAN/CANNOT table | gate.py enforces (27 tests) |
| Asks before acting | Approval state machine blocks execution | 4 blocked transitions tested |
| Admits limits | 1 test failure documented honestly | TC-002 (keyword vs semantic gap detection) |
| Keeps a record | JSONL audit log, 33 event types | audit_logger.py (tested) |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI Platform | WorkBuddy AI v5.9.4 |
| Agent Skills | WorkBuddy SKILL.md (YAML frontmatter) |
| Deterministic Tools | Python 3.13 (gate.py, validator.py, quote_gen.py, audit_logger.py, state_manager.py) |
| State Storage | Local JSON files |
| Project Tracker | Excel (.xlsx) via openpyxl |
| Audit Log | JSONL files (daily rotation) |
| Reference Data | Markdown files (rate card, templates) |
| Quotation Template | DOCX (Arunika Digital template) |

---

## Sample Use Case

**Client:** SG Garage (Budi Santoso, Surabaya)
**Project:** Workshop Management System (WMS)

1. **Brief received:** "Bengkel mobil butuh web app. React + Apps Script + Google Sheets. 3 user types. 3-4 weeks."
2. **Agent identifies 4 gaps:** Auth roles, WhatsApp, monthly reports, multi-cabang
3. **Clarification questions asked** (grouped: scope, features, technical)
4. **Plan generated:** 14 tasks across 4 phases, 24 dev-days, Rp 21,600,000
5. **Validated:** PASS_WITH_WARNINGS (1 assumption risk flagged)
6. **Approval card presented** with all details and sources
7. **User approves** → tasks created in Excel tracker
8. **Quotation generated:** QTO/20261106/SGG0, Rp 21,600,000, terbilang: "dua puluh satu juta enam ratus ribu rupiah"
9. **Quotation approved** → email draft prepared for client

---

## Roadmap

| Milestone | Scope | Status |
|-----------|-------|--------|
| M1: Foundation | Brief → Plan → Validate → Approval | ✅ Complete |
| M2: Execution | Execute approved actions to Excel tracker | ✅ Tools ready |
| M3: Monitoring | Progress tracking, blocker identification | Planned |
| M4: Multi-Project | Dashboard, cloud DB integration | Planned |
| M5: Closure | UAT support, BAST draft generation | Planned |
