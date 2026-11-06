#!/usr/bin/env python3
"""
tracker_sync.py — Deterministic plan.json -> Excel tracker writer.

WHY THIS EXISTS
---------------
Before this module, the executor wrote the Excel tracker by hand (LLM-driven
openpyxl calls). During a live run on 2026-11-06 that produced three defects
in the submitted tracker:

  1. Dashboard said SG Garage had 0 tasks (the sheet had 15).
  2. A phase name was overwritten with a revision note:
     "[REVISED] Stok (Invoice -> Fase 2)" instead of "Modul Inti".
  3. The sheet kept a template row (TASK-015) that was not in plan.json.

All three are drift between a plan and a spreadsheet. Drift is exactly what
this project claims to prevent, so the write path must not be left to the LLM.
plan.json is the single source of truth; this module renders it.

PUBLIC API
----------
    create_tracker(path)                          -> blank tracker workbook
    sync_project(path, plan, sheet_name=None, client=None, project_status="Active")
    recompute_dashboard(path)
    verify(path, plan, sheet_name=None)           -> list[str] of issues
    run_selftest()                                -> bool

CLI
---
    python3 agent/tools/tracker_sync.py --selftest
    python3 agent/tools/tracker_sync.py --sync state/projects/PRJ-X/plan.json data/tof-project-tracker.xlsx
    python3 agent/tools/tracker_sync.py --verify state/projects/PRJ-X/plan.json data/tof-project-tracker.xlsx
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    print("openpyxl is required: pip install openpyxl")
    raise

# ---------------------------------------------------------------------------
# Layout constants — one place, so the writer and the verifier cannot disagree
# ---------------------------------------------------------------------------

SHEET_TITLE_ROW = 1
META_ROW = 2
HEADER_ROW = 4
DATA_START_ROW = 5

COLUMNS = [
    ("Task ID", 14),
    ("Phase", 26),
    ("Category", 20),
    ("Task Description", 46),
    ("Technical Reason", 44),
    ("Priority", 12),
    ("Est. Time (days)", 16),
    ("Actual Time (days)", 18),
    ("Status", 14),
    ("Notes", 34),
]

DASH_TITLE_ROW = 1
DASH_SECTION_ROW = 6
DASH_HEADER_ROW = 7
DASH_FIRST_PROJECT_ROW = 8
DASH_LAST_PROJECT_ROW = 12
DASH_TOTAL_ROW = 13

# Tracker's Settings sheet defines these vocabularies; map plan values onto them.
CATEGORY_MAP = {
    "requirements": "Requirements/Design",
    "design": "Requirements/Design",
    "development": "Development",
    "testing": "Testing/QA",
    "qa": "Testing/QA",
    "deployment": "Deployment/Handover",
    "handover": "Deployment/Handover",
    "access": "Access & Reporting",
    "reporting": "Access & Reporting",
}

PRIORITY_MAP = {"P0": "High", "P1": "Medium", "P2": "Low"}

DONE_STATUSES = {"done", "completed", "complete", "selesai"}

HEADER_FILL = PatternFill("solid", fgColor="E2EFDA")
TITLE_FONT = Font(bold=True, size=13)
HEADER_FONT = Font(bold=True, size=10, color="1F3864")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_sheet_name(name: str) -> str:
    """Excel sheet names: max 31 chars, cannot contain []:*?/\\ or lead with '."""
    clean = re.sub(r"[\[\]:*?/\\]", "-", str(name)).strip().strip("'")
    clean = re.sub(r"\s+", " ", clean)
    return (clean or "Project")[:31]


def phase_name(phase: dict) -> str:
    return phase.get("phaseName") or phase.get("name") or "Unnamed Phase"


def normalize_category(raw: str | None) -> str:
    if not raw:
        return "Development"
    key = str(raw).strip().lower()
    return CATEGORY_MAP.get(key, str(raw).strip())


def normalize_priority(raw: str | None) -> str:
    if not raw:
        return "Medium"
    token = str(raw).strip()
    return PRIORITY_MAP.get(token.upper(), token)


def plan_tasks(plan: dict) -> list[dict]:
    """Flatten wbs.phases[].tasks[] into one ordered list with phase attached."""
    rows: list[dict] = []
    for phase_index, phase in enumerate(plan.get("wbs", {}).get("phases", [])):
        pname = phase_name(phase)
        for task_index, task in enumerate(phase.get("tasks", [])):
            rows.append({
                "taskId": task.get("taskId", f"TASK-{len(rows) + 1:03d}"),
                "phase": pname,
                "category": normalize_category(task.get("category")),
                "title": task.get("title", ""),
                "reason": task.get("technicalReason") or task.get("description") or "",
                "priority": normalize_priority(task.get("priority")),
                "days": task.get("estimatedDays", 0),
                "source": task.get("source", ""),
                "trace": f"plan.json#wbs.phases[{phase_index}].tasks[{task_index}]",
            })
    return rows


def _find_project_sheet(wb, project_id: str, sheet_name: str | None):
    if sheet_name and sheet_name in wb.sheetnames:
        return wb[sheet_name]
    for ws in wb.worksheets:
        if str(ws.cell(META_ROW, 2).value or "").strip() == project_id:
            return ws
    return None


def _style_header(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row, col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.border = BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=True)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_tracker(path: str | Path) -> Path:
    """Create an empty tracker with Dashboard + Settings sheets."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()

    dash = wb.active
    dash.title = "Dashboard"
    dash["A1"] = "TOF Project Assistant — Project Tracker"
    dash["A1"].font = TITLE_FONT
    dash.cell(DASH_SECTION_ROW, 1, "Project Summary").font = Font(bold=True, size=11)
    headers = ["Project ID", "Project Name", "Client", "Total Tasks",
               "Completed Tasks", "Status"]
    for i, h in enumerate(headers, start=1):
        dash.cell(DASH_HEADER_ROW, i, h)
    _style_header(dash, DASH_HEADER_ROW, len(headers))
    dash.cell(DASH_TOTAL_ROW, 1, "TOTAL").font = Font(bold=True)
    dash.cell(DASH_TOTAL_ROW, 4, f"=SUM(D{DASH_FIRST_PROJECT_ROW}:D{DASH_LAST_PROJECT_ROW})")
    dash.cell(DASH_TOTAL_ROW, 5, f"=SUM(E{DASH_FIRST_PROJECT_ROW}:E{DASH_LAST_PROJECT_ROW})")
    for col, width in zip("ABCDEF", (18, 42, 32, 14, 18, 12)):
        dash.column_dimensions[col].width = width

    settings = wb.create_sheet("Settings")
    settings["A1"] = "Settings & Reference Data"
    settings["A1"].font = TITLE_FONT
    vocab = {
        "Status Options": ["Not Started", "In Progress", "Blocked", "Done"],
        "Priority Options": ["High", "Medium", "Low"],
        "Phase Options": ["Requirements & Design", "Development", "Testing/QA",
                          "Deployment/Handover"],
        "Category Options": ["Requirements/Design", "Development", "Testing/QA",
                             "Access & Reporting", "Deployment/Handover"],
    }
    for i, (heading, values) in enumerate(vocab.items(), start=1):
        col = get_column_letter(i)
        settings.cell(3, i, heading).font = Font(bold=True)
        for j, value in enumerate(values, start=4):
            settings.cell(j, i, value)
        settings.column_dimensions[col].width = 24

    wb.save(path)
    return path


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_project(
    tracker_path: str | Path,
    plan: dict,
    sheet_name: str | None = None,
    client: str | None = None,
    project_status: str = "Active",
) -> dict:
    """Render plan.json into a project sheet, then refresh the Dashboard.

    Deterministic: same plan in, same sheet out. Task rows are cleared and
    rewritten from the plan, so stale template rows cannot survive.
    """
    tracker_path = Path(tracker_path)
    if not tracker_path.exists():
        create_tracker(tracker_path)

    wb = openpyxl.load_workbook(tracker_path)
    project_id = plan.get("projectId", "PRJ-UNKNOWN")
    project_name = plan.get("projectName", project_id)

    ws = _find_project_sheet(wb, project_id, sheet_name)
    if ws is None:
        ws = wb.create_sheet(sanitize_sheet_name(sheet_name or project_name))
    else:
        if sheet_name and ws.title != sheet_name and sheet_name not in wb.sheetnames:
            ws.title = sanitize_sheet_name(sheet_name)

    # Title + meta block
    ws.cell(SHEET_TITLE_ROW, 1, f"{project_name} ({project_id})").font = TITLE_FONT
    ws.cell(META_ROW, 1, "Project ID:")
    ws.cell(META_ROW, 2, project_id)
    ws.cell(META_ROW, 4, "Client:")
    ws.cell(META_ROW, 5, client or plan.get("client", {}).get("company", "") or "")
    ws.cell(META_ROW, 7, "Overall Status:")
    ws.cell(META_ROW, 8, project_status)

    # Clear every row below the header so removed tasks really disappear.
    if ws.max_row >= DATA_START_ROW:
        ws.delete_rows(DATA_START_ROW, ws.max_row - DATA_START_ROW + 1)

    for col, (heading, width) in enumerate(COLUMNS, start=1):
        ws.cell(HEADER_ROW, col, heading)
        ws.column_dimensions[get_column_letter(col)].width = width
    _style_header(ws, HEADER_ROW, len(COLUMNS))

    rows = plan_tasks(plan)
    for offset, task in enumerate(rows):
        r = DATA_START_ROW + offset
        values = [
            task["taskId"],
            task["phase"],
            task["category"],
            task["title"],
            task["reason"],
            task["priority"],
            task["days"],
            None,
            "Not Started",
            f"{task['trace']} | {task['source']}".strip(" |"),
        ]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(r, col, value)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=col in (2, 4, 5, 10))

    ws.freeze_panes = f"B{DATA_START_ROW}"
    wb.save(tracker_path)
    recompute_dashboard(tracker_path)

    return {
        "projectId": project_id,
        "sheet": ws.title,
        "tasksWritten": len(rows),
        "totalDays": sum(t["days"] for t in rows),
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def recompute_dashboard(tracker_path: str | Path) -> list[dict]:
    """Rebuild the Dashboard project table from the actual project sheets.

    Counts are read from the sheets themselves, so the summary cannot claim a
    number the detail does not contain.
    """
    tracker_path = Path(tracker_path)
    wb = openpyxl.load_workbook(tracker_path)
    if "Dashboard" not in wb.sheetnames:
        return []

    projects = []
    for ws in wb.worksheets:
        if ws.title == "Dashboard":
            continue
        if str(ws.cell(META_ROW, 1).value or "").strip() != "Project ID:":
            continue
        pid = str(ws.cell(META_ROW, 2).value or "").strip()
        if not pid:
            continue
        total = 0
        done = 0
        for r in range(DATA_START_ROW, ws.max_row + 1):
            tid = str(ws.cell(r, 1).value or "").strip()
            if not tid.upper().startswith("TASK"):
                continue
            total += 1
            if str(ws.cell(r, 9).value or "").strip().lower() in DONE_STATUSES:
                done += 1
        projects.append({
            "projectId": pid,
            "projectName": str(ws.cell(SHEET_TITLE_ROW, 1).value or "").strip(),
            "client": str(ws.cell(META_ROW, 5).value or "").strip(),
            "total": total,
            "done": done,
            "status": str(ws.cell(META_ROW, 8).value or "Active").strip(),
        })

    dash = wb["Dashboard"]
    if dash.max_row >= DASH_FIRST_PROJECT_ROW:
        dash.delete_rows(DASH_FIRST_PROJECT_ROW,
                         max(dash.max_row - DASH_FIRST_PROJECT_ROW + 1, 1))

    for offset, proj in enumerate(projects[:DASH_LAST_PROJECT_ROW - DASH_FIRST_PROJECT_ROW + 1]):
        r = DASH_FIRST_PROJECT_ROW + offset
        dash.cell(r, 1, proj["projectId"])
        dash.cell(r, 2, proj["projectName"])
        dash.cell(r, 3, proj["client"])
        dash.cell(r, 4, proj["total"])
        dash.cell(r, 5, proj["done"])
        dash.cell(r, 6, proj["status"])

    total_row = DASH_FIRST_PROJECT_ROW + max(len(projects), 1)
    dash.cell(total_row, 1, "TOTAL").font = Font(bold=True)
    dash.cell(total_row, 4, f"=SUM(D{DASH_FIRST_PROJECT_ROW}:D{total_row - 1})")
    dash.cell(total_row, 5, f"=SUM(E{DASH_FIRST_PROJECT_ROW}:E{total_row - 1})")

    wb.save(tracker_path)
    return projects


# ---------------------------------------------------------------------------
# Verify — the accountability check
# ---------------------------------------------------------------------------

def verify(tracker_path: str | Path, plan: dict, sheet_name: str | None = None) -> list[str]:
    """Cross-check a tracker sheet against plan.json. Returns human-readable issues."""
    tracker_path = Path(tracker_path)
    issues: list[str] = []
    if not tracker_path.exists():
        return [f"tracker not found: {tracker_path}"]

    wb = openpyxl.load_workbook(tracker_path)
    project_id = plan.get("projectId", "")
    ws = _find_project_sheet(wb, project_id, sheet_name)
    if ws is None:
        return [f"no sheet for project {project_id} in {tracker_path.name}"]

    expected = plan_tasks(plan)
    expected_ids = [t["taskId"] for t in expected]
    expected_phase = {t["taskId"]: t["phase"] for t in expected}
    expected_days = {t["taskId"]: t["days"] for t in expected}

    actual_ids: list[str] = []
    for r in range(DATA_START_ROW, ws.max_row + 1):
        tid = str(ws.cell(r, 1).value or "").strip()
        if not tid.upper().startswith("TASK"):
            continue
        actual_ids.append(tid)

        # 1. phase must match the plan exactly (catches revision notes leaking in)
        sheet_phase = str(ws.cell(r, 2).value or "").strip()
        if tid in expected_phase and sheet_phase != expected_phase[tid]:
            issues.append(
                f"{tid}: phase mismatch — sheet '{sheet_phase}' vs plan '{expected_phase[tid]}'"
            )

        # 2. effort must match
        sheet_days = ws.cell(r, 7).value
        if tid in expected_days and sheet_days != expected_days[tid]:
            issues.append(
                f"{tid}: est. days mismatch — sheet {sheet_days} vs plan {expected_days[tid]}"
            )

        # 3. a [REVISED] marker belongs in the title, never in the phase column
        if "[REVISED]" in sheet_phase:
            issues.append(f"{tid}: revision marker found in Phase column")

    missing = [t for t in expected_ids if t not in actual_ids]
    extra = [t for t in actual_ids if t not in expected_ids]
    if missing:
        issues.append(f"tasks in plan but not in sheet: {', '.join(missing)}")
    if extra:
        issues.append(f"tasks in sheet but not in plan (stale rows): {', '.join(extra)}")

    # 4. Dashboard total must equal the number of rows actually written
    dash = wb["Dashboard"] if "Dashboard" in wb.sheetnames else None
    if dash is not None:
        dash_total = None
        for r in range(DASH_FIRST_PROJECT_ROW, dash.max_row + 1):
            if str(dash.cell(r, 1).value or "").strip() == project_id:
                dash_total = dash.cell(r, 4).value
                break
        if dash_total is None:
            issues.append(f"Dashboard has no row for {project_id}")
        elif dash_total != len(actual_ids):
            issues.append(
                f"Dashboard total for {project_id} is {dash_total}, sheet has {len(actual_ids)}"
            )

    # 5. effort total must match the plan's own totalDays
    plan_days = plan.get("effortEstimation", {}).get("totalDays")
    sheet_days_total = sum(
        ws.cell(r, 7).value for r in range(DATA_START_ROW, ws.max_row + 1)
        if str(ws.cell(r, 1).value or "").upper().startswith("TASK")
        and isinstance(ws.cell(r, 7).value, (int, float))
    )
    if isinstance(plan_days, (int, float)) and sheet_days_total != plan_days:
        issues.append(
            f"effort total mismatch — sheet sums to {sheet_days_total} days, plan says {plan_days}"
        )

    return issues


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _sample_plan() -> dict:
    return {
        "projectId": "PRJ-TEST-001",
        "projectName": "Test Project With A Very Long Name That Exceeds Thirty One Chars",
        "client": {"company": "Test Client"},
        "effortEstimation": {"totalDays": 5},
        "wbs": {
            "phases": [
                {
                    "phaseName": "Requirements & Design",
                    "tasks": [
                        {"taskId": "TASK-001", "title": "Gather", "category": "requirements",
                         "priority": "P0", "estimatedDays": 2, "source": "BRIEF"},
                        {"taskId": "TASK-002", "title": "Wireframe", "category": "design",
                         "priority": "P1", "estimatedDays": 1, "source": "CLARIFIED"},
                    ],
                },
                {
                    "phaseName": "Development",
                    "tasks": [
                        {"taskId": "TASK-003", "title": "Build", "category": "development",
                         "priority": "P0", "estimatedDays": 2, "source": "BRIEF"},
                    ],
                },
            ]
        },
    }


def run_selftest() -> bool:
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))

    print("\n" + "=" * 60)
    print("TRACKER SYNC — SELF TEST")
    print("=" * 60)

    tmp = Path(tempfile.mkdtemp(prefix="tof-tracker-test-"))
    tracker = tmp / "tracker.xlsx"
    plan = _sample_plan()

    # Group 1 — helpers
    print("\n--- Group 1: helpers ---")
    check("sanitize truncates to 31 chars",
          len(sanitize_sheet_name(plan["projectName"])) == 31)
    check("sanitize strips forbidden chars",
          "/" not in sanitize_sheet_name("a/b:c*d"))
    check("P0 maps to High", normalize_priority("P0") == "High")
    check("unknown priority passes through", normalize_priority("Medium") == "Medium")
    check("requirements maps to Requirements/Design",
          normalize_category("requirements") == "Requirements/Design")
    check("plan_tasks flattens 3 tasks", len(plan_tasks(plan)) == 3)
    check("plan_tasks carries phase name",
          plan_tasks(plan)[0]["phase"] == "Requirements & Design")

    # Group 2 — create + sync
    print("\n--- Group 2: create and sync ---")
    create_tracker(tracker)
    check("tracker file created", tracker.exists())
    result = sync_project(tracker, plan, sheet_name="PRJ-TEST-001", client="Test Client")
    check("sync reports 3 tasks written", result["tasksWritten"] == 3)
    check("sync reports 5 total days", result["totalDays"] == 5)

    wb = openpyxl.load_workbook(tracker)
    check("project sheet exists", "PRJ-TEST-001" in wb.sheetnames)
    ws = wb["PRJ-TEST-001"]
    check("header written", ws.cell(HEADER_ROW, 1).value == "Task ID")
    check("first task id", ws.cell(DATA_START_ROW, 1).value == "TASK-001")
    check("first task phase", ws.cell(DATA_START_ROW, 2).value == "Requirements & Design")
    check("status defaults to Not Started",
          ws.cell(DATA_START_ROW, 9).value == "Not Started")
    check("traceability note recorded",
          "plan.json#wbs.phases[0].tasks[0]" in str(ws.cell(DATA_START_ROW, 10).value))

    # Group 3 — dashboard
    print("\n--- Group 3: dashboard ---")
    dash = wb["Dashboard"]
    check("dashboard has project row", dash.cell(DASH_FIRST_PROJECT_ROW, 1).value == "PRJ-TEST-001")
    check("dashboard total tasks is 3", dash.cell(DASH_FIRST_PROJECT_ROW, 4).value == 3)
    check("dashboard completed is 0", dash.cell(DASH_FIRST_PROJECT_ROW, 5).value == 0)

    # Group 4 — verify passes on a clean sync
    print("\n--- Group 4: verify on clean data ---")
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("clean sync produces no issues", issues == [], str(issues))

    # Group 5 — verify catches each defect class we actually hit
    print("\n--- Group 5: verify catches real defect classes ---")

    # 5a. phase pollution (the bug that shipped)
    wb = openpyxl.load_workbook(tracker)
    wb["PRJ-TEST-001"].cell(DATA_START_ROW, 2, "[REVISED] Stok (Invoice -> Fase 2)")
    wb.save(tracker)
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("detects phase pollution", any("phase mismatch" in i for i in issues), str(issues))
    check("detects revision marker in phase",
          any("revision marker" in i for i in issues), str(issues))
    sync_project(tracker, plan, sheet_name="PRJ-TEST-001")

    # 5b. stale extra row (the TASK-015 bug)
    wb = openpyxl.load_workbook(tracker)
    wb["PRJ-TEST-001"].cell(DATA_START_ROW + 3, 1, "TASK-999")
    wb.save(tracker)
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("detects stale row", any("stale rows" in i for i in issues), str(issues))
    sync_project(tracker, plan, sheet_name="PRJ-TEST-001")

    # 5c. dashboard under-reporting (the "0 tasks" bug)
    wb = openpyxl.load_workbook(tracker)
    wb["Dashboard"].cell(DASH_FIRST_PROJECT_ROW, 4, 0)
    wb.save(tracker)
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("detects dashboard undercount",
          any("Dashboard total" in i for i in issues), str(issues))
    recompute_dashboard(tracker)

    # 5d. effort drift
    wb = openpyxl.load_workbook(tracker)
    wb["PRJ-TEST-001"].cell(DATA_START_ROW, 7, 9)
    wb.save(tracker)
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("detects est-days mismatch", any("est. days mismatch" in i for i in issues), str(issues))
    sync_project(tracker, plan, sheet_name="PRJ-TEST-001")

    # Group 6 — idempotency and task removal
    print("\n--- Group 6: idempotency and removal ---")
    sync_project(tracker, plan, sheet_name="PRJ-TEST-001")
    issues = verify(tracker, plan, sheet_name="PRJ-TEST-001")
    check("re-sync is idempotent", issues == [], str(issues))

    trimmed = json.loads(json.dumps(plan))
    trimmed["wbs"]["phases"][1]["tasks"] = []
    trimmed["effortEstimation"]["totalDays"] = 3
    sync_project(tracker, trimmed, sheet_name="PRJ-TEST-001")
    issues = verify(tracker, trimmed, sheet_name="PRJ-TEST-001")
    check("removed task leaves no stale row", issues == [], str(issues))
    wb = openpyxl.load_workbook(tracker)
    check("sheet now has 2 task rows",
          wb["PRJ-TEST-001"].cell(DATA_START_ROW + 2, 1).value in (None, ""))
    check("dashboard follows removal",
          wb["Dashboard"].cell(DASH_FIRST_PROJECT_ROW, 4).value == 2)

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv or len(sys.argv) == 1:
        sys.exit(0 if run_selftest() else 1)

    if "--sync" in sys.argv:
        i = sys.argv.index("--sync")
        plan_path, tracker_path = sys.argv[i + 1], sys.argv[i + 2]
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        out = sync_project(tracker_path, plan)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(0)

    if "--verify" in sys.argv:
        i = sys.argv.index("--verify")
        plan_path, tracker_path = sys.argv[i + 1], sys.argv[i + 2]
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        problems = verify(tracker_path, plan)
        if problems:
            print("ISSUES:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        print("OK: tracker matches plan.json")
        sys.exit(0)

    print(__doc__)
