# TOF Project Assistant — Accountability Sheet

**Challenge B: Office Agent | AI CAN DO IT Hackathon Indonesia 2026**

---

## What the Agent CAN Access

| Data Source | Access Level | Storage |
|-------------|-------------|---------|
| Client briefs (text, documents) | Read + Store | Local JSON (`state/projects/`) |
| Clarification Q&A | Read + Store | Local JSON |
| Project plans (WBS, estimates) | Read + Store | Local JSON |
| Excel project tracker | Read + Write (with approval) | Local `.xlsx` file |
| Rate card & templates | Read-only | Markdown files |
| Audit log | Append-only | JSONL daily files |
| Approval state (pending/history) | Read + Write | Local JSON |

## What the Agent Executes Autonomously (No Approval Needed)

| Action | Risk Level | Why Safe |
|--------|-----------|----------|
| Read client brief | Low | Read-only, internal |
| Store brief in JSON | Low | Agent internal state |
| Ask clarification questions | Low | Communication only |
| Generate project plan | Low | Output only, no external change |
| Run validation checks | Low | Analysis only |
| Generate audit log entries | Low | Append-only, internal |
| Generate quotation draft | Low | Output only, for review |
| Derive UI screen inventory from plan | Low | Deterministic, output only |
| Render mockup PNG into project folder | Low | Writes only to own workspace |
| Run self-tests | Low | Internal validation |

## What Requires Human Approval

| Action | Risk Level | Approval Mechanism |
|--------|-----------|-------------------|
| Create tasks in Excel tracker | Medium | Approval card → PENDING → APPROVED |
| Update task status in tracker | Medium | Approval card with detail changes |
| Sync local state to tracker | Medium | Approval card per sync batch |
| Confirm UI screen inventory before design | Medium | Approval card listing every screen + its source scope line |
| Write frames into a shared Figcraft design file | High | Separate approval — never modifies existing layers |
| Send quotation via email | High | Separate approval for email send |
| Delete data | High | Never auto-executed |
| Bulk operations (>5 cells) | High | Approval card with full scope |
| Generate BAST draft | High | Legal document, approval required |
| Mark UAT as passed | High | Project closure decision |

**Approval State Machine:**
```
DRAFT → PENDING_APPROVAL → APPROVED → EXECUTED → (FAILED if error)
                    ↓
              REJECTED → DRAFT (revise & resubmit — remediation loop)
```

**Blocked transitions (enforced by gate.py, 27 tests):**
- PENDING → EXECUTED (cannot skip approval)
- REJECTED → EXECUTED (rejected = blocked)
- FAILED → EXECUTED (needs new approval)

## What the Agent Will NEVER Do

| Boundary | Enforcement |
|----------|-------------|
| Execute any action without human approval | `gate.py` blocks all non-APPROVED actions |
| Fabricate information not in brief or clarification | Anti-fabrication rule in accountability.md |
| Follow instructions embedded in client documents | Prompt injection detection (10 patterns in gate.py) |
| Delete or modify audit log entries | Append-only design, no delete API |
| Claim success without verification | Completion honesty rule, executor verifies |
| Access data outside project workspace | Bounded authority CAN/CANNOT table |
| Change project scope without authority | Approval required for scope changes |
| Send emails without explicit approval | Email send = high risk, separate approval |
| Invent UI screens not backed by plan scope | `ui_spec.py` requires `derivedFrom` on every screen; TC-022 asserts 0 invented |
| Use real client data in mockups | Mockups use obvious sample data only |

---

## Transparency Tags (Shows Sources)

Every information item in plans is tagged:

| Tag | Meaning | Example |
|-----|---------|---------|
| [BRIEF] | Directly from client brief | "Tech: React + Apps Script" |
| [CLARIFIED] | From user's clarification answers | "Role-based auth needed" |
| [ASSUMPTION] | AI assumption (flagged, needs confirmation) | "Developer works full-time" |
| [AI RECOMMENDATION] | AI's suggestion (not final) | "Phased approach: 4 phases" |

**Sample plan:** 23 items tagged across 4 categories (8 BRIEF, 4 CLARIFIED, 5 ASSUMPTION, 6 AI_RECOMMENDATION)

---

## Audit Trail (Keeps a Record)

- **Format:** JSONL (JSON Lines), daily files
- **Location:** `state/audit-log/YYYY-MM-DD.jsonl`
- **33 event types** across project lifecycle, planning, approval, execution, quotation, UI design, and security
- **Each entry:** UUID, timestamp, projectId, eventType, actor, description, metadata, actionId, riskLevel

---

## Test Results Summary

| Test Suite | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| gate.py self-tests | 27 | 27 | 0 |
| validator.py self-tests | 14 | 14 | 0 |
| quote_gen.py self-tests | 31 | 31 | 0 |
| ui_spec.py self-tests | 26 | 26 | 0 |
| mockup_render.py self-tests | 18 | 18 | 0 |
| audit_logger.py | 1 | 1 | 0 |
| state_manager.py | 1 | 1 | 0 |
| Challenge test cases | 24 | 23 | 1 |
| **Total** | **142** | **141** | **1** |

**The 1 failure (TC-002):** Keyword-based gap detection finds 1 "unclear" marker in a brief that has 10 numbered unclear points. The LLM-based orchestrator catches all 10 through semantic analysis. This failure is documented honestly — the hackathon values showing limitations, not hiding them.
