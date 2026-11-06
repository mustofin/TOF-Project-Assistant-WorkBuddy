# Form Submission — Copy-Paste Answers

Everything below is ready to paste into the submission form. Values are taken from
the files named next to them, so nothing here is invented.

---

## 1. Project title

```
TOF Project Assistant
```

## 2. Short blurb (must be under 10 words)

```
Turns messy client briefs into validated, human-approved project plans.
```

> 9 words. Do not add a period-counted sentence — the limit is strict.

## 3. Project description

Paste the contents of **`submission/project-description.md`** (1,237 words).

If the form has a character limit, paste the first section ("Problem" through
"How it works") and link the rest:

```
https://github.com/mustofin/TOF-Project-Assistant-WorkBuddy/blob/main/submission/project-description.md
```

## 4. Accountability sheet

Paste the contents of **`submission/accountability-sheet.md`** (915 words — one page).

It covers the five rules with the exact file that enforces each one.

## 5. Test results with screenshots

Summary line to paste:

```
8 deterministic modules, 154/154 assertions pass.
24 challenge test cases, 23 pass, 1 fails by design (TC-002, keyword-based
gap detection — documented rather than hidden).
Full detail: submission/test-cases.md
```

Upload these five files from `evidence/screenshots/`:

| File | Shows |
|---|---|
| `01a-selftest-part1.png` | gate.py (27), validator.py (14) |
| `01b-selftest-part2.png` | quote_gen.py (31), ui_spec.py (33) |
| `01c-selftest-part3.png` | mockup_render.py (18), tracker_sync.py (29), audit_logger |
| `01d-selftest-part4.png` | state_manager + **ALL 8 MODULES PASSED (154/154)** |
| `02-test-cases.png` | 24 challenge tests, 23 pass / 1 fail |

## 6. Architecture diagram

Upload **`submission/architecture-diagram.png`** (1280×1820, ~795 KB).

## 7. Demo video (5–8 minutes)

```
<paste your video link here>
```

Recording order that shows every required moment — the agent asking, waiting,
refusing, and revising — is in **`submission/demo-script.md`**. Recommended scene
order: Turn 1 → Turn 2 → Turn 8 (refusal) → Turn 7 (revision) → Turn 6 (UI).

## 8. Product sharing

Paste the contents of **`submission/product-sharing.md`** (899 words).

## 9. Source code

```
https://github.com/mustofin/TOF-Project-Assistant-WorkBuddy
```

---

## Before you hit submit

Run the readiness check one last time:

```bash
python3 verify_submission.py
```

It re-runs the test suites, re-reads the Excel tracker against `plan.json`, counts
the blurb, and asks git whether the code is actually pushed. It must print
**VERDICT: READY TO SUBMIT**.

The only expected warning is item 7 (video), because a video cannot be verified
from disk.

---

## If the form asks for something not listed here

The nine items above are the checklist this project was built against. If the live
form has extra fields (team members, university, phone number, challenge track),
answer them directly — nothing in this repository depends on them.
