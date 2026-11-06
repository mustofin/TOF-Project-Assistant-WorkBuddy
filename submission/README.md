# TOF Project Assistant — Submission Package

**Challenge B: Office Agent | AI CAN DO IT - Tencent Cloud Hackathon Indonesia 2026**

---

## Quick Start

```bash
# 1. Run self-tests (5 modules, 72 tests)
python3 agent/tools/selftest.py

# 2. Run challenge test cases (20 tests)
python3 tests/test_cases.py

# 3. View architecture diagram
open submission/architecture-diagram.html
```

---

## Submission Items Checklist

| # | Item | File | Status |
|---|------|------|--------|
| 1 | Project title | "TOF Project Assistant" | ✅ |
| 2 | Short blurb (<10 words) | `submission/short-blurb.md` | ✅ |
| 3 | Project description | `submission/project-description.md` | ✅ |
| 4 | Accountability sheet (1 page) | `submission/accountability-sheet.md` | ✅ |
| 5 | Test results with screenshots | `submission/test-cases.md` + `evidence/screenshots/` | ✅ |
| 6 | Architecture diagram | `submission/architecture-diagram.png` | ✅ |
| 7 | Demo video (5-8 min) | `submission/demo-script.md` + `demo/run_demo.py` | ⏳ Record |
| 8 | Product sharing | `submission/product-sharing.md` | ✅ |
| 9 | Source code | `https://github.com/mustofin/TOF-Project-Assistant-WorkBuddy` | ⏳ Push |

**Bonus (bukan item wajib, tapi memperkuat submission):**
`submission/ui-mockups/gallery.html` — 14 layar UI hasil turunan plan, lengkap dengan
role matrix dan design tokens.

---

## Project Structure

```
TOF-Project-Assistant-WorkBuddy/
├── agent/
│   ├── orchestrator/SKILL.md       # Main orchestrator (8-step workflow)
│   ├── planner/SKILL.md            # Brief → WBS plan generator
│   ├── validator/SKILL.md          # 6-check plan validator skill
│   ├── executor/SKILL.md           # Approved action executor
│   ├── quotation/SKILL.md          # Quotation document generator
│   ├── ui-designer/SKILL.md        # Plan → UI screens + mockups
│   ├── rules/
│   │   ├── accountability.md       # 8 accountability principles
│   │   └── approval-policy.md      # State machine + remediation loop
│   └── tools/
│       ├── gate.py                 # Approval gate + injection detection (27 tests)
│       ├── validator.py            # Plan validator (14 tests)
│       ├── quote_gen.py            # Quotation generator (31 tests)
│       ├── ui_spec.py              # Plan → screen inventory (26 tests)
│       ├── mockup_render.py        # Spec → HTML → PNG (18 tests)
│       ├── audit_logger.py         # JSONL audit log (33 event types)
│       ├── state_manager.py        # State management + remediation loop
│       └── selftest.py             # Master test runner
├── data/
│   ├── mock-dataset/               # 3 briefs, client profiles, quotation scenarios
│   ├── rate-card.md                # Developer rates for cost estimation
│   ├── sample-client-brief.md      # SG Garage sample brief
│   ├── project-templates/web-app.md
│   ├── templates/Quotation_Template_Dummy.docx
│   └── tof-project-tracker.xlsx    # Excel tracker (3 tabs, 15 tasks)
├── tests/
│   └── test_cases.py               # 20 challenge test cases
├── evidence/
│   ├── test-results.json           # Full test results in JSON
│   └── selftest-results.txt        # Self-test output log
├── submission/                     # Hackathon deliverables
│   ├── short-blurb.md
│   ├── project-description.md
│   ├── accountability-sheet.md
│   ├── test-cases.md
│   ├── architecture.md
│   ├── architecture-diagram.html
│   ├── demo-script.md
│   ├── product-sharing.md
│   └── README.md (this file)
├── ARCHITECTURE.md                 # Full architecture document
└── IMPLEMENTATION_PLAN.md          # 5-milestone roadmap
```

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Agent Skills | 6 (Orchestrator, Planner, Validator, Executor, Quotation Gen, UI Designer) |
| Deterministic Tools | 7 Python modules |
| Self-Tests | 95 tests, 100% pass |
| Challenge Test Cases | 24 tests, 96% pass (23/24) |
| Audit Event Types | 33 |
| Transparency Tags | 4 (BRIEF, CLARIFIED, ASSUMPTION, AI_RECOMMENDATION) |
| Approval States | 6 (DRAFT, PENDING, APPROVED, REJECTED, EXECUTED, FAILED) |
| Prompt Injection Patterns | 10 |
| Mock Briefs | 3 (complete, with gaps, with injection) |
| Sample Plan Tasks | 14 across 4 phases |
| UI Screens Generated | 14 from plan scope (all traceable) |

---

## Accountability Compliance

| Rule | Implementation | Evidence |
|------|---------------|----------|
| Shows sources | 4 transparency tags | 23 tagged items in sample plan |
| Within permissions | Bounded authority CAN/CANNOT table | gate.py enforces (27 tests) |
| Asks before acting | Approval state machine | 4 blocked transitions tested |
| Admits limits | 1 test failure documented | TC-002 (keyword vs semantic) |
| Keeps a record | JSONL audit log | 26 event types, append-only |
