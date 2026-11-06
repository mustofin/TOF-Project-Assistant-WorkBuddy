# Form Submission — Copy-Paste Answers

Mapped field by field to the live Google Form, in the order the form asks.
Values come from the file named next to each one, so nothing here is invented.

Status legend: **[READY]** nothing to do · **[YOU]** only you can do this · **[NEW]** produced in this pass

---

# Part 1 — Team details (form page 1)

| # | Field | What to enter | Status |
|---|---|---|---|
| 1 | Team Name * | your team's name | **[YOU]** |
| 2 | Team Captain Name * | your full name | **[YOU]** |
| 3 | Job Title / Field of Study * | your job title or field of study | **[YOU]** |
| 4 | Company / Institution * | `TOF Solusi Digital` | **[READY]** |
| 5 | Team Captain Email * | your email (the one you monitor) | **[YOU]** |
| 6 | Team Captain Phone Number * | your WhatsApp number | **[YOU]** |
| 7–9 | Team Member 1–3 (name + email) | leave empty if you are submitting solo | **[YOU]** |
| 10 | Which Challenge/Problem Statement * | select **`The Office Agent`** | **[READY]** |

> The challenge radio has three options: The Workflow Brain / **The Office Agent** /
> The Creator Agent. This project is The Office Agent — unstructured input (client brief)
> turned into structured output (plan, quotation, screen inventory) with approval gates.
> Do not pick "The Workflow Brain": that is a different problem statement.

---

# Part 2 — Project details (form page 2)

## 11. Project Title *

```
TOF Project Assistant
```

## 12. Short Blurb * — hard limit under 10 words

```
Turns messy client briefs into validated, human-approved project plans.
```

9 words. Do not add a second sentence — the limit is strict.

## 13. Project Description *

Paste **`submission/project-description-form.md`** — it is already restructured to the
four headings the form asks for, in this order:

1. **Project Overview** → target scenarios, users, value proposition
2. **Sources of Pain Points** → target audience, core problem statement
3. **Solution & Superiority** → comprehensive design, business and technical architecture,
   how it drives AI generation
4. **Business Value** → quantified before/after table, plus the impact that is not time

`submission/project-description.md` is the longer version; use it only if the form has no
character limit.

## 14. Cover Image * — 16:9, min 300×216px, max 10MB

Upload **`submission/cover-image.png`** — **[NEW]**

2560×1440 (exactly 16:9), 2.0 MB. Contains the title, the one-line proposition, the
Challenge B label, and the five accountability rules.

## 15. Project Link * — live URL or demo link

```
https://tof-project-assistant.apps.workbuddy.host/?sharecode=QJRYZAPOGO
```

**[READY]** Published and verified reachable. The page is self-contained (14 screenshots,
1.0 MB) and states plainly that the agent itself runs in WorkBuddy, so nobody mistakes the
page for the product.

Source of the page: `submission/site/`. Rebuild with `python3 submission/site/build_site.py`
if you change anything — it reads the screenshots and numbers from the repo, so the page
cannot drift from the code.

## 16. Demo Video Link * — browser-accessible URL

```
<paste your unlisted YouTube / Drive link here>
```

**[YOU]** Not recorded yet. The script is written: `submission/demo-script.md`, 5–8 minutes.
Recommended scene order — Turn 1 (asks) → Turn 2 (waits) → Turn 8 (refuses) → Turn 7
(rejects and revises) → Turn 6 (UI). That sequence shows all four required moments.
Upload as **unlisted**, not private — a private link cannot be opened by a judge.

## 17. WorkBuddy / CodeBuddy Conversation History * — min 3 screenshots, max 10 files

**[YOU]** You already have this material: the case-study-2 session you just ran.

Capture 3–5 screenshots from that conversation, in this order:

| # | Capture | Why this one |
|---|---|---|
| 1 | Turn 1 — the agent listing the gaps and asking, instead of planning | the agent stops before acting |
| 2 | Turn 2 — the approval card with plan, cost and sources | structured output + gate |
| 3 | Turn 3 — you rejecting, and the agent returning a `[REVISED]` card | the remediation loop |
| 4 | Turn 6 — the screen inventory with `derivedFrom` per screen | no invented screens |
| 5 | Turn 7 — the agent refusing the "ignore the rules" instruction | bounded authority |

Keep each file under 10 MB. Crop to the conversation panel; no need to show your whole
desktop.

## 18. Architecture Diagram PPT * — 1 file, PDF or presentation, max 10MB

Upload **`submission/architecture-diagram.pdf`** — **[NEW]**

One page, 0.25 MB, sized to the diagram so nothing splits across pages.
`submission/architecture-diagram.png` is the same image if you would rather build a slide
from it — but the form accepts **PDF or PPT, not PNG**, so upload the PDF.

The diagram shows: platform → 6 skills → 8 deterministic tools → hybrid storage → the five
accountability rules → the approval state machine.

## 19. Source Code — GitHub repository URL *

```
https://github.com/mustofin/TOF-Project-Assistant-WorkBuddy
```

**[YOU]** The repository must be **public** and **pushed**. Right now it is neither:
the local branch is 8 commits ahead of `origin/main`.

```bash
cd ~/Documents/Github/TOF-Project-Assistant-WorkBuddy
git push origin main
```

Then confirm in the browser that the link opens without logging in. A judge who hits a 404
or a login wall scores the source code as missing.

## 20. Social Media Post Link * — must carry the hashtags

**[YOU]** Publish on YouTube, X, Threads, LinkedIn or similar with:

```
#WorkBuddy #AIforGood #TencentCloudHackathon
```

Suggested post text is in `submission/product-sharing.md`. The link must open publicly —
a post visible only to your followers does not count.

---

# Before you hit Submit

```bash
python3 verify_submission.py
```

It re-runs both test suites, re-reads the Excel tracker against `plan.json`, counts the
blurb, and asks git whether the code is actually pushed. It must print
**VERDICT: READY TO SUBMIT**.

Current state: **13 passed · 1 warning · 1 blocker** — the only blocker is the unpushed
repository. The warning is item 16 (video), which cannot be verified from disk.

---

# The short version — what is actually left

| # | Task | Owner | Blocks submit? |
|---|---|---|---|
| 1 | `git push origin main`, then make the repo public | you | **yes** |
| 2 | Record the 5–8 min demo video, upload unlisted | you | **yes** |
| 3 | Screenshot 3–5 turns of your chat history | you | **yes** |
| 4 | Publish the social media post with the 3 hashtags | you | **yes** |
| 5 | ~~Decide the Project Link~~ — published, paste the URL above | done | no |
| 6 | Fill team name, captain, email, phone | you | **yes** |
| 7 | Cover image, PDF, description, blurb, project link | done | no |
| 8 | Select "The Office Agent" | done | no |

Everything in rows 7–8 is on disk and verified. Rows 1–6 cannot be done from here —
they need your account, your voice, or your chat history.
