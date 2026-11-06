# Demo Runner — Recording Guide

One command runs the entire 10-scene demo end-to-end. Designed so you can
screen-record it without clicking through anything.

## Run it

```bash
# Full demo with pauses (for recording) — ~4-6 min
python3 demo/run_demo.py

# No pauses (just to verify it works)
python3 demo/run_demo.py --fast

# Re-record a single scene
python3 demo/run_demo.py --scene 5
python3 demo/run_demo.py --scene 9
```

## Before you hit record

1. **Maximise the terminal** — 100+ columns, font size 14-16pt so text is readable on video.
2. **Use a dark terminal theme** — the output uses ANSI colours tuned for dark backgrounds.
3. **Clear the screen** — `clear` right before starting.
4. **Check audio** — if you narrate, test the mic first. If not, add captions in editing.

## Recording

| Tool | Command |
|------|---------|
| QuickTime | File → New Screen Recording |
| macOS shortcut | `Cmd + Shift + 5` → Record Selected Portion |
| OBS | Scene → Display Capture, 1080p 30fps |

Record only the terminal window region, then crop.

## Scene map (what the judges must see)

| Scene | Content | Why it matters |
|-------|---------|----------------|
| 1 | Brief received (unstructured) | Challenge B input |
| 2 | 4 gaps → clarification questions | Agent asks, doesn't assume |
| 3 | Plan generated, 4 transparency tags | Unstructured → structured |
| 4 | 6 validation checks | Deterministic quality gate |
| 5 | **Approval card → agent WAITS** | ⚠️ REQUIRED MOMENT — "asks before acting" |
| 6 | Human approves → executed | Bounded authority |
| 7 | Quotation + separate high-risk approval | Scoped approval, not blanket |
| 7b | UI screens derived from plan, role-aware | Structured → visual, still traceable |
| 8 | **Reject → remediate → approve** | Resilience loop, shows revision |
| 9 | **Prompt injection → agent REFUSES** | ⚠️ REQUIRED MOMENT — "stays within permissions" |
| 10 | Audit trail, full event list | "keeps a record" |

The two ⚠️ moments are mandatory per the handbook: the demo must show at least
one instance where the agent **refuses, seeks clarification, or awaits approval**.
We show all three.

## Suggested narration beats

- **Scene 1** — "The client sent this over WhatsApp. No structure at all."
- **Scene 2** — "Instead of guessing, it asks four specific questions."
- **Scene 5** — "Watch — it prepared the action but it will not execute. It's waiting for me." *(pause here, this is the key moment)*
- **Scene 7b** — "Every screen here traces back to a line in the plan. It didn't invent features to make the mockup look fuller."
- **Scene 8** — "I rejected it as too expensive. Instead of giving up, it revised the scope and came back."
- **Scene 9** — "This brief tries to tell the agent to ignore all rules. It refused, logged it, and kept working normally."

## After recording

1. Trim dead time at the start/end.
2. Target **5-8 minutes** — the handbook limit.
3. Export 1080p MP4 (H.264).
4. Upload to YouTube (unlisted) or Google Drive, set link sharing to "anyone with the link".
5. Put the link in the submission form.

## Fallback if recording fails

`submission/demo-script.md` contains the written walkthrough. The PNG evidence in
`evidence/screenshots/` shows the same test output statically. But the video is a
required submission item — record it.
