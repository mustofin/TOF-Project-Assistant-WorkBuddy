# Project Description — Form Version

Structured to match the four headings the submission form asks for, in order.
Every number here is verifiable from the repository.

---

## 1. Project Overview

**TOF Project Assistant** is an accountable AI project manager for a small software
consultancy. It turns an unstructured client brief into a validated project plan, a
quotation, and a UI screen inventory — and stops for human approval before anything is
written to a shared file or sent to a client. Built on WorkBuddy AI; submission for
Challenge B: The Office Agent.

**Target scenarios.** A brief arrives as a forwarded WhatsApp message: no headings, no
feature list, sometimes two requirements that cannot both be satisfied. A developer must
turn it into a plan, a price, and a delivery schedule within a day, while the client waits.

**Users.** The primary user is the PM / business owner at a 2–10 person software house —
someone who does the estimating and the client conversation personally, and who cannot
afford an AI that quietly invents the client's user count or the deadline. Secondary users
are the roles named in the plan itself: in the sample project, a service advisor, a cashier
and a workshop head, each of whom sees only the screens their role allows.

**Value proposition.** A general-purpose assistant will produce a confident plan from an
incomplete brief. This one produces a plan you can defend: every line says where it came
from, every assumption is labelled, nothing external happens without a recorded approval,
and the whole session is auditable afterwards.

---

## 2. Sources of Pain Points

**Target audience.** Small software consultancies and freelance development teams in
Indonesia that take client work without a dedicated PMO — the segment where "the plan" is
one person's judgement and "the quote" is a spreadsheet rebuilt from scratch each time.

**Core problem statement.** The gap between what a client says and what a developer needs
is where projects fail, and it is currently bridged by silent assumption. Three specific
symptoms, observed directly at TOF Solusi Digital:

1. **Assumptions are invisible.** A plan silently embeds "developer works full-time" or
   "no scope changes". Nobody sees them until they cause a dispute.
2. **AI acts without permission.** Most AI tooling writes changes immediately — creates
   tasks, edits timelines, sends email. When the model is wrong, the damage is already done
   and there is no step at which a human could have stopped it.
3. **No paper trail.** "Who approved adding five tasks?" is unanswerable, because decisions
   live in chat and in people's heads.

Each symptom maps to one of the hackathon's five accountability rules, which is why the
product is built around the rules rather than decorated with them.

---

## 3. Solution & Superiority

**Comprehensive design.** Six WorkBuddy skills (orchestrator, planner, validator, executor,
quotation generator, UI designer) drive eight deterministic Python modules. The split is
deliberate: judgement is done by the model, and anything safety-critical — approval state,
quality checks, cost arithmetic, screen derivation — is done by testable code. The agent
reads its state from disk each turn, so a session can be audited and resumed rather than
trusted from memory.

**Business and technical architecture.** Five layers: WorkBuddy chat → skills →
deterministic tools → hybrid storage (local JSON for agent state, Excel tracker for humans,
append-only JSONL for audit) → accountability layer. The approval state machine
(`DRAFT → PENDING_APPROVAL → APPROVED → EXECUTED`, with `REJECTED → DRAFT` as a remediation
loop) is enforced in `gate.py`, not in a prompt: `PENDING → EXECUTED`, `REJECTED →
EXECUTED` and `FAILED → EXECUTED` are blocked transitions, covered by tests.

**How it drives AI generation.** The model is not asked to be careful; it is given no room
to be careless. Every generated line must carry a provenance tag (`[BRIEF]`, `[CLARIFIED]`,
`[ASSUMPTION]`, `[AI RECOMMENDATION]`). The validator runs six checks before a human sees
the plan. The UI designer can only emit a screen that maps to a scope line — each screen
carries a `derivedFrom` pointer, so an invented screen is a visible defect rather than a
plausible extra. And when the model does get something wrong, the correction goes through
the same gate: rejection records a reason, the plan is revised rather than restarted, and a
new approval card is issued because the old approval ID cannot be reused.

**Superiority, stated narrowly.** The differentiator is not that it produces plans — many
tools do. It is that the output is falsifiable: 157 assertions across 8 modules, 24
challenge test cases, and one test that fails on purpose and is documented (TC-002:
keyword-based gap detection cannot match a model's semantic reading of a brief). A suite
that always reports 100% is not measuring anything.

---

## 4. Business Value

**Quantifiable metrics** (measured on the two sample projects in the repository):

| Activity | Before | With the agent |
|---|---|---|
| Brief analysis and gap finding | 30–60 min, manual | under 5 min, gaps listed explicitly |
| Plan + effort + cost | 1–2 hours | generated, then validated by 6 checks |
| Quotation | 2–3 hours | under 1 min, with *terbilang* |
| UI screen inventory | 1–2 days | under 2 min (14 screens, all traceable) |
| Approval traceability | none | 33 audit event types, append-only |

**Clearly defined impact.** Three effects matter more than the time saved. First, a wrong
estimate is caught at the approval card instead of at delivery — in the catering sample, the
first honest plan came in at Rp 14.4M against a Rp 12M budget, the client rejected it, and
the revision landed at Rp 11.7M before any code was written. Second, scope is bounded by
construction: the plan's role matrix gives the courier 2 of 16 screens and hides prices from
the kitchen, because the plan said so. Third, the audit trail answers "who approved this?"
with a record rather than a recollection — which is the difference between an AI that helps
and an AI you can hand a client's project to.

---

*Full detail: `submission/project-description.md` · Evidence: `submission/test-cases.md`,
`evidence/screenshots/` · Live showcase: see Project Link in the form.*
