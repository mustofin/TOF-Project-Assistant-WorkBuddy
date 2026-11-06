#!/usr/bin/env python3
"""
TOF Project Assistant - State Inspector

Shows what the agent ACTUALLY produced on disk, so you can verify its claims
instead of trusting the chat response.

Usage:
    python3 demo/check_state.py              # summary of everything
    python3 demo/check_state.py PRJ-SGG-001  # one project in detail
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
STATE = ROOT / "state"

C = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
    "cyan": "\033[96m", "blue": "\033[94m", "mag": "\033[95m",
}


def h(text, ch="─"):
    print(f"{C['dim']}{ch * 72}{C['reset']}")
    print(f"{C['bold']}{text}{C['reset']}")
    print(f"{C['dim']}{ch * 72}{C['reset']}")


def ok(t):
    print(f"  {C['green']}✓{C['reset']} {t}")


def no(t):
    print(f"  {C['dim']}·{C['reset']} {C['dim']}{t}{C['reset']}")


def warn(t):
    print(f"  {C['yellow']}!{C['reset']} {t}")


def read_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_project(pid, detail=False):
    pdir = STATE / "projects" / pid
    if not pdir.exists():
        print(f"  {C['red']}✗{C['reset']} {pid} — folder tidak ada")
        return

    meta = read_json(pdir / "meta.json") or {}
    print(f"\n  {C['cyan']}{C['bold']}{pid}{C['reset']}  "
          f"{meta.get('projectName', '?')}")
    print(f"  {C['dim']}status: {meta.get('status', '?')}  ·  "
          f"step: {meta.get('currentStep', '?')}{C['reset']}")

    # The 5 lifecycle artifacts, in order
    steps = [
        ("brief.json", "Brief diterima"),
        ("clarifications.json", "Klarifikasi dijawab"),
        ("plan.json", "Plan disusun"),
        ("validation.json", "Plan divalidasi"),
    ]
    for fname, label in steps:
        p = pdir / fname
        if p.exists():
            data = read_json(p)
            extra = ""
            if fname == "plan.json" and data:
                phases = data.get("wbs", {}).get("phases", [])
                n = sum(len(x.get("tasks", [])) for x in phases)
                eff = data.get("effortEstimation", {}).get("totalDays")
                cost = data.get("costEstimation", {}).get("totalCost")
                extra = f" — {n} task, {eff} hari"
                if cost:
                    extra += f", Rp {cost:,}"
            elif fname == "validation.json" and data:
                extra = f" — verdict {data.get('verdict', '?')}"
            elif fname == "clarifications.json" and data:
                extra = f" — {len(data.get('qa', []))} Q&A"
            elif fname == "brief.json" and data:
                extra = f" — {len(data.get('briefText', '')):,} char"
            ok(f"{label}{C['dim']}{extra}{C['reset']}")
        else:
            no(f"{label} — {fname} belum ada")

    # Quotation
    qdir = pdir / "quotation"
    qs = sorted(qdir.glob("*.json")) if qdir.exists() else []
    docs = sorted(qdir.glob("*.docx")) if qdir.exists() else []
    if qs or docs:
        ok(f"Quotation — {len(qs)} json, {len(docs)} docx")
    else:
        no("Quotation — belum ada")

    # UI design
    udir = pdir / "ui-design"
    spec = read_json(udir / "ui-spec.json") if udir.exists() else None
    shots = sorted((udir / "screens").glob("*.png")) if (udir / "screens").exists() else []
    if spec:
        ok(f"UI spec — {len(spec.get('screens', []))} layar diturunkan dari plan")
        if shots:
            ok(f"UI mockup — {len(shots)} PNG")
        else:
            no("UI mockup — spec ada, PNG belum dirender")
    else:
        no("UI design — belum ada")

    # Rejection feedback
    fb = read_json(pdir / "rejection-feedback.json")
    if fb:
        n = len(fb) if isinstance(fb, list) else 1
        warn(f"Remediation — {n} penolakan tercatat (loop pernah jalan)")

    if not detail:
        return

    # Detail: plan breakdown
    plan = read_json(pdir / "plan.json")
    if plan:
        print(f"\n  {C['bold']}WBS{C['reset']}")
        for ph in plan.get("wbs", {}).get("phases", []):
            print(f"    {ph.get('phaseName', '?'):<28} "
                  f"{len(ph.get('tasks', [])):>2} task  "
                  f"{ph.get('estimatedDays', 0):>3} hari")

        src = plan.get("informationSources", {})
        print(f"\n  {C['bold']}Tag sumber{C['reset']}")
        for k, label in [("fromBrief", "BRIEF"), ("fromClarification", "CLARIFIED"),
                         ("fromAssumption", "ASSUMPTION"),
                         ("fromAIRecommendation", "AI_RECOMMENDATION")]:
            print(f"    {label:<20} {len(src.get(k, [])):>2} item")

    val = read_json(pdir / "validation.json")
    if val:
        print(f"\n  {C['bold']}Validasi{C['reset']}")
        for c in val.get("checks", []):
            st = c.get("status")
            mark = (f"{C['green']}PASS{C['reset']}" if st == "PASS"
                    else f"{C['yellow']}WARN{C['reset']}" if st == "WARNING"
                    else f"{C['red']}FAIL{C['reset']}")
            print(f"    {mark}  {c.get('check', '?'):<24} "
                  f"{C['dim']}{str(c.get('detail', ''))[:34]}{C['reset']}")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"\n{C['bold']}{C['blue']}TOF Project Assistant — State Inspector{C['reset']}")
    print(f"{C['dim']}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  {STATE}{C['reset']}")

    if not STATE.exists():
        print(f"\n{C['red']}Folder state/ belum ada — agent belum pernah jalan.{C['reset']}\n")
        return

    # Projects
    h("PROJECTS")
    pdirs = sorted(p for p in (STATE / "projects").glob("*") if p.is_dir()) \
        if (STATE / "projects").exists() else []
    if target:
        check_project(target, detail=True)
    elif pdirs:
        for p in pdirs:
            check_project(p.name)
    else:
        no("Belum ada project. Mulai dengan memberi brief ke agent.")

    # Approvals
    h("PENDING APPROVALS")
    pend = sorted((STATE / "pending-approvals").glob("*.json")) \
        if (STATE / "pending-approvals").exists() else []
    if pend:
        for p in pend:
            a = read_json(p) or {}
            print(f"  {C['yellow']}●{C['reset']} {a.get('actionId', p.stem)}")
            print(f"    {C['dim']}type={a.get('actionType')}  "
                  f"status={a.get('approvalStatus')}  "
                  f"project={a.get('projectId')}{C['reset']}")
        print(f"\n  {C['dim']}→ Agent menunggu keputusanmu. Balas "
              f"\"Setuju, lanjutkan\" atau \"Tolak, alasan: ...\"{C['reset']}")
    else:
        no("Tidak ada yang menunggu approval")

    # Approval history
    h("APPROVAL HISTORY")
    hist = []
    if (STATE / "approval-history").exists():
        for p in (STATE / "approval-history").glob("*/*.json"):
            a = read_json(p) or {}
            hist.append(a)
    if hist:
        for a in sorted(hist, key=lambda x: x.get("createdAt", "")):
            st = a.get("approvalStatus", "?")
            color = {"APPROVED": "green", "EXECUTED": "green",
                     "REJECTED": "red", "FAILED": "red"}.get(st, "yellow")
            print(f"  {C[color]}{st:<10}{C['reset']} "
                  f"{a.get('actionType', '?'):<20} "
                  f"{C['dim']}{a.get('projectId', '?')}{C['reset']}")
    else:
        no("Belum ada approval yang diputuskan")

    # Audit log
    h("AUDIT LOG")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log = STATE / "audit-log" / f"{today}.jsonl"
    if log.exists():
        lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"  {len(lines)} event hari ini ({log.name})")
        counts = {}
        for l in lines:
            try:
                counts[json.loads(l).get("eventType", "?")] = \
                    counts.get(json.loads(l).get("eventType", "?"), 0) + 1
            except Exception:
                pass
        for et, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {et:<32} {n:>2}×")
        print(f"\n  {C['dim']}→ Bukti agent tidak mengklaim tanpa jejak.{C['reset']}")
    else:
        no(f"Belum ada event untuk {today}")

    print()


if __name__ == "__main__":
    main()
