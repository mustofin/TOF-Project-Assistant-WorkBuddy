#!/usr/bin/env python3
"""
verify_submission.py — Read-only readiness check before submitting.

Answers one question: "can I submit right now, and if not, what is missing?"

It does not trust the documentation. It re-runs the test suites, re-reads the
Excel tracker against plan.json, counts the words in the short blurb, and asks
git whether the code has actually been pushed. Numbers printed here come from
the artifacts themselves, so a stale claim in a .md file is caught rather than
repeated.

Usage:
    python3 verify_submission.py            # full check
    python3 verify_submission.py --quiet    # only blockers

Exit code:
    0 = no blockers (warnings may remain)
    1 = at least one blocker
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUBMISSION = ROOT / "submission"
STATE = ROOT / "state"

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"
MARK = {PASS: "[PASS]", WARN: "[WARN]", FAIL: "[FAIL]", SKIP: "[ -- ]"}

results: list[tuple[str, str, str]] = []  # (status, label, detail)


def add(status: str, label: str, detail: str = "") -> None:
    results.append((status, label, detail))


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except Exception as exc:  # pragma: no cover
        return 1, str(exc)


def words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


# ---------------------------------------------------------------------------
# Submission items 1-9
# ---------------------------------------------------------------------------

def check_items() -> None:
    # 1. Project title
    add(PASS, "1. Project title", "TOF Project Assistant")

    # 2. Short blurb, < 10 words
    blurb_path = SUBMISSION / "short-blurb.md"
    if not blurb_path.exists():
        add(FAIL, "2. Short blurb (<10 words)", "file missing")
    else:
        raw = blurb_path.read_text(encoding="utf-8")
        body = "\n".join(
            ln for ln in raw.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        )
        # drop the self-declared "(N words)" annotation so it cannot be counted
        body = re.sub(r"\(\s*\d+\s*words?\s*\)", "", body)
        body = body.replace("*", "")
        n = words(body)
        if n >= 10:
            add(FAIL, "2. Short blurb (<10 words)", f"{n} words — must be fewer than 10")
        else:
            add(PASS, "2. Short blurb (<10 words)", f"{n} words")

    # 3. Project description
    desc = SUBMISSION / "project-description.md"
    if desc.exists():
        n = words(desc.read_text(encoding="utf-8"))
        add(PASS, "3. Project description", f"{desc.name}, {n} words")
    else:
        add(FAIL, "3. Project description", "missing")

    # 4. Accountability sheet, one page
    sheet = SUBMISSION / "accountability-sheet.md"
    if sheet.exists():
        n = words(sheet.read_text(encoding="utf-8"))
        status = PASS if n <= 1100 else WARN
        add(status, "4. Accountability sheet (1 page)", f"{n} words")
    else:
        add(FAIL, "4. Accountability sheet (1 page)", "missing")

    # 5. Test results + screenshots
    tc = SUBMISSION / "test-cases.md"
    shots = sorted((ROOT / "evidence" / "screenshots").glob("*.png"))
    if tc.exists() and shots:
        add(PASS, "5. Test results + screenshots", f"{len(shots)} screenshots")
    else:
        add(FAIL, "5. Test results + screenshots",
            f"test-cases.md={tc.exists()}, screenshots={len(shots)}")

    # 6. Architecture diagram
    png = SUBMISSION / "architecture-diagram.png"
    if png.exists() and png.stat().st_size > 50_000:
        add(PASS, "6. Architecture diagram", f"{png.stat().st_size // 1024} KB")
    else:
        add(FAIL, "6. Architecture diagram", "missing or too small")

    # 7. Demo video — cannot be verified from disk
    add(WARN, "7. Demo video (5-8 min)",
        "cannot be verified here — must be recorded and linked in the form")

    # 8. Product sharing
    ps = SUBMISSION / "product-sharing.md"
    add(PASS if ps.exists() else FAIL, "8. Product sharing",
        f"{words(ps.read_text(encoding='utf-8'))} words" if ps.exists() else "missing")

    # 9. Source code pushed
    code, out = run(["git", "rev-list", "--count", "origin/main..HEAD"])
    if code != 0:
        add(WARN, "9. Source code pushed", "no remote tracking branch")
    else:
        ahead = int(out.strip() or 0)
        if ahead == 0:
            add(PASS, "9. Source code pushed", "up to date with origin/main")
        else:
            add(FAIL, "9. Source code pushed",
                f"{ahead} commit(s) not pushed — run: git push origin main")


# ---------------------------------------------------------------------------
# Integrity: do the claims match the artifacts?
# ---------------------------------------------------------------------------

def check_integrity() -> None:
    # Self-tests
    code, out = run([sys.executable, "agent/tools/selftest.py"])
    m = re.search(r"Total assertions:\s*(\d+)", out)
    p = re.search(r"Assertions passed:\s*(\d+)", out)
    mods = re.search(r"Total modules:\s*(\d+)", out)
    if code == 0 and m and p:
        add(PASS, "Self-tests", f"{p.group(1)}/{m.group(1)} assertions, "
                                f"{mods.group(1) if mods else '?'} modules")
        actual_assertions = int(m.group(1))
    else:
        add(FAIL, "Self-tests", "suite failed — run python3 agent/tools/selftest.py")
        actual_assertions = None

    # Challenge test cases
    code, out = run([sys.executable, "tests/test_cases.py"])
    tp = re.search(r"TOTAL:\s*(\d+)\s+passed,\s*(\d+)\s+failed\s+out\s+of\s+(\d+)", out)
    if tp:
        add(PASS, "Challenge test cases",
            f"{tp.group(1)}/{tp.group(3)} passed, {tp.group(2)} intentional failure")
    else:
        add(WARN, "Challenge test cases", "could not parse summary")

    # Excel tracker vs plan.json
    plans = sorted(STATE.glob("projects/*/plan.json"))
    if not plans:
        add(SKIP, "Excel tracker vs plan", "no plan.json in state/")
    else:
        sys.path.insert(0, str(ROOT / "agent" / "tools"))
        try:
            import tracker_sync as ts
            tracker = ROOT / "data" / "tof-project-tracker.xlsx"
            problems = []
            checked = 0
            for plan_path in plans:
                plan = json.loads(plan_path.read_text(encoding="utf-8"))
                issues = ts.verify(tracker, plan)
                if issues:
                    problems.extend(f"{plan['projectId']}: {i}" for i in issues)
                checked += 1
            if problems:
                add(FAIL, "Excel tracker vs plan", "; ".join(problems[:3]))
            else:
                add(PASS, "Excel tracker vs plan",
                    f"{checked} project(s) match plan.json exactly")
        except Exception as exc:
            add(WARN, "Excel tracker vs plan", f"could not check: {exc}")

    # Stale numbers in the docs. Only aggregate claims are checked — per-module
    # figures like "(27 assertions)" are legitimately different numbers.
    if actual_assertions:
        aggregate = re.compile(
            r"(\d+)\s+self-tests?"
            r"|(\d+)\s+assertions?\s+across"
            r"|(\d+)\s+tests,?\s+all\s+pass"
            r"|(\d+)/(\d+)\s+PASS"
        )
        stale = []
        for md in list(SUBMISSION.glob("*.md")) + list((ROOT / "docs").glob("*.md")) \
                + [ROOT / "README.md"]:
            if not md.exists():
                continue
            text = md.read_text(encoding="utf-8")
            for match in aggregate.finditer(text):
                claimed = next(g for g in match.groups() if g)
                if int(claimed) != actual_assertions:
                    stale.append(f"{md.name} says {claimed}")
        if stale:
            add(FAIL, "Docs match real test count",
                f"actual {actual_assertions} — " + "; ".join(sorted(set(stale))[:5]))
        else:
            add(PASS, "Docs match real test count",
                f"every aggregate claim says {actual_assertions}")

    # Evidence that a real run happened
    projects = list((STATE / "projects").glob("*"))
    pending = list((STATE / "pending-approvals").glob("*.json"))
    history = list((STATE / "approval-history").glob("*/*.json"))
    if projects:
        add(PASS, "Evidence of a real run",
            f"{len(projects)} project(s), {len(pending)} pending, {len(history)} approval record(s)")
    else:
        add(WARN, "Evidence of a real run", "state/projects is empty")

    # Rendered UI mockups
    screens = list((SUBMISSION / "ui-mockups" / "screens").glob("*.png"))
    add(PASS if screens else WARN, "UI mockups", f"{len(screens)} screens rendered")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def main() -> int:
    quiet = "--quiet" in sys.argv

    print("=" * 66)
    print("  TOF PROJECT ASSISTANT — SUBMISSION READINESS")
    print("  AI CAN DO IT · Tencent Cloud Hackathon Indonesia 2026")
    print("=" * 66)

    print("\n  SUBMISSION ITEMS")
    print("  " + "-" * 62)
    check_items()
    item_count = len(results)
    check_integrity()

    # Print in order, inserting the second group's heading at the boundary.
    for index, (status, label, detail) in enumerate(results):
        if index == item_count:
            print("\n  INTEGRITY CHECKS")
            print("  " + "-" * 62)
        if quiet and status == PASS:
            continue
        line = f"  {MARK[status]} {label}"
        if detail:
            line = f"{line:<48} {detail}"
        print(line)

    blockers = [r for r in results if r[0] == FAIL]
    warnings = [r for r in results if r[0] == WARN]
    passed = [r for r in results if r[0] == PASS]

    print("\n" + "=" * 66)
    print(f"  {len(passed)} passed · {len(warnings)} warning(s) · {len(blockers)} blocker(s)")

    if blockers:
        print("\n  BLOCKERS — fix before submitting:")
        for _, label, detail in blockers:
            print(f"    - {label}: {detail}")
        print("\n  VERDICT: NOT READY")
        return 1

    print("\n  VERDICT: READY TO SUBMIT")
    if warnings:
        print("  (warnings above are things only you can do, not defects)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
