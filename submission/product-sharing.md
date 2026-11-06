# TOF Project Assistant — Product Sharing

**Challenge B: Office Agent | AI CAN DO IT Hackathon Indonesia 2026**

---

## The Problem

At TOF Solusi Digital, we noticed that software project management has a accountability crisis:

1. **AI tools execute without permission** — Modern AI can generate plans, but they also create tasks, modify timelines, and send emails without asking. When the AI is wrong (and it often is), the damage is already done.

2. **Assumptions are invisible** — Project plans silently embed assumptions like "developer works full-time" or "no scope changes." These assumptions aren't labeled, so stakeholders don't know what's fact vs. guess.

3. **No paper trail** — When a project fails, the question "who approved this?" has no answer. Decisions happen in chat, in heads, in assumptions — nowhere traceable.

4. **Briefs are messy** — Clients say "I need a web app for my bengkel" and expect a full project plan. The gap between what they say and what the developer needs is enormous.

---

## Our Approach

We built TOF Project Assistant as an **accountable** AI that follows 5 rules:

1. **Shows sources** — Every piece of information is tagged: [BRIEF], [CLARIFIED], [ASSUMPTION], or [AI RECOMMENDATION]. You always know where information came from.

2. **Stays within permissions** — A bounded authority table defines what the agent CAN do (analyze, propose, explain) and CANNOT do (execute without approval, fabricate data, bypass rules).

3. **Asks before acting** — An approval state machine (DRAFT → PENDING → APPROVED → EXECUTED) ensures no external action happens without human consent. Rejected plans enter a remediation loop.

4. **Admits limits** — We documented 1 test failure (TC-002) where keyword-based gap detection can't match LLM semantic analysis. We show this honestly rather than hiding it.

5. **Keeps a record** — 26 event types are logged in append-only JSONL audit files. Every action has a UUID, timestamp, actor, and approval reference.

---

## What Makes It Innovative

| Feature | Traditional AI | TOF Project Assistant |
|---------|---------------|----------------------|
| Information sources | Mixed, unlabeled | 4 transparency tags on every item |
| Execution | Direct, no approval | State machine with 6 states |
| Assumptions | Hidden in output | Explicitly flagged with risk level |
| Audit trail | None or manual | 26 event types, automatic JSONL |
| Prompt injection | Vulnerable | 10-pattern detection in gate.py |
| Quotation generation | Manual (2-3 hours) | Automated (< 1 min) with terbilang |
| Failure reporting | Hidden | 1 documented failure (TC-002) |
| Reject → remediate | One-directional | Loop: REJECTED → DRAFT → PENDING → APPROVED |

---

## Workflow Demo

**Scenario:** SG Garage (bengkel) wants a Workshop Management System.

1. **Brief:** "Bengkel butuh web app. React + Apps Script. 3 user types. 3-4 weeks."
2. **Agent identifies 4 gaps:** Auth roles, WhatsApp, monthly reports, multi-cabang
3. **Clarification:** Asks 4 structured questions (grouped by topic)
4. **Plan:** 14 tasks, 4 phases, 24 dev-days, Rp 21,600,000
5. **Validation:** PASS_WITH_WARNINGS (timeline risk flagged)
6. **Approval card:** Shows all details, sources, assumptions, expected impact
7. **User approves** → tasks written to Excel tracker
8. **Quotation:** Generated with terbilang ("dua puluh satu juta enam ratus ribu rupiah")
9. **Quotation approved** → email draft prepared (requires separate high-risk approval)

**Key demo moment:** When the brief with prompt injection ("ignore all rules") is processed, the agent detects 6 injection patterns, treats the text as data, and continues with normal approval workflow.

---

## Technology Choices

| Choice | Why |
|--------|-----|
| WorkBuddy AI platform | Native skill system, MCP tools, built-in audit log |
| Python deterministic tools | Testable, verifiable, not dependent on LLM behavior |
| Local JSON for state | Simple, no external dependencies, full control |
| Excel for tracker | Human-readable, editable, SheetAgent MCP integration |
| JSONL for audit log | Append-only, human-readable, easy to verify |
| HTML/SVG for architecture | No external dependencies, renders anywhere |

---

## Lessons Learned

1. **Deterministic tools are essential** — Relying purely on LLM prompts for safety-critical checks (like approval gates) is fragile. Python tools with self-tests provide verifiable guarantees.

2. **Honesty builds trust** — Showing 1 test failure (TC-002) demonstrates that the system is honest about its limitations. This is more valuable than claiming 100% pass rate.

3. **Approval as a visible artifact** — Approval should be more than text in chat. The approval card format (Action ID, detail changes, sources, assumptions) makes the decision explicit and auditable.

4. **Separate brain from channel** — The agent's intelligence (skills) is separate from the data channel (JSON state). This allows the agent to maintain state across turns even though WorkBuddy skills run per-turn.

5. **Prompt injection is a real threat** — Our mock brief 3 contains 6 injection patterns. Without detection, these could bypass approval gates. The gate.py detection is a first line of defense.

---

## What's Next

- **M2:** Full executor implementation (Excel write-back with idempotency)
- **M3:** Progress monitoring and risk alerts
- **M4:** Multi-project dashboard with Cloud Service DB
- **M5:** Closure support (UAT tracking, BAST generation)
- **Future:** Integration with email (Gmail MCP), calendar scheduling, team collaboration

---

## Team

**TOF Solusi Digital** — Software development company based in Indonesia, building accountable AI tools for project management.

Built on WorkBuddy AI platform for AI CAN DO IT Tencent Cloud Hackathon Indonesia 2026.
