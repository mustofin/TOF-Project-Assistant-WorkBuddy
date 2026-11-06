#!/usr/bin/env python3
"""
TOF Project Assistant - Validator (Deterministic Plan Validator)

Validates a project plan against 6 quality checks:
1. COMPLETENESS - All required sections filled
2. CONSISTENCY - Scope, timeline, and effort are balanced
3. FEASIBILITY - Estimates are realistic given constraints
4. BRIEF_ALIGNMENT - Plan addresses all brief requirements
5. ASSUMPTION_RISK - High-risk assumptions flagged
6. INFORMATION_TRANSPARENCY - All items properly tagged with source

Usage:
    from validator import Validator
    validator = Validator()

    report = validator.validate(plan, brief, clarifications)
    print(report["verdict"])  # PASS, PASS_WITH_WARNINGS, FAIL
"""

import json
import sys
from datetime import datetime, timezone


# Required plan sections
REQUIRED_PLAN_SECTIONS = [
    "projectId",
    "objectives",
    "scope",
    "deliverables",
    "wbs",
    "effortEstimation",
    "costEstimation",
    "risks",
    "assumptions",
    "informationSources",
]

# Required WBS task fields
REQUIRED_TASK_FIELDS = [
    "taskId",
    "title",
    "description",
    "category",
    "priority",
    "estimatedDays",
]

# Valid priority values
VALID_PRIORITIES = ["P0", "P1", "P2", "P3"]

# Valid information source tags
VALID_SOURCE_TAGS = ["BRIEF", "CLARIFIED", "ASSUMPTION", "AI_RECOMMENDATION"]

# Feasibility thresholds
MAX_EFFORT_PER_PHASE = 60  # days - flag if single phase exceeds
MIN_TASKS_PER_PROJECT = 5  # flag if fewer tasks
EFFORT_VS_TIMELINE_BUFFER = 1.2  # flag if effort exceeds timeline * buffer

# Rate card defaults (for cost validation)
DEFAULT_RATES = {
    "Junior Developer": 500000,
    "Mid Developer": 800000,
    "Senior Developer": 1200000,
    "Full-stack Developer": 1000000,
    "UI/UX Designer": 900000,
    "QA Tester": 600000,
    "Project Manager": 1100000,
}


class Validator:
    """Deterministic plan validator with 6 quality checks."""

    def validate(self, plan, brief=None, clarifications=None):
        """
        Validate a project plan.

        Args:
            plan: dict containing the project plan
            brief: dict containing the original brief (optional)
            clarifications: dict containing Q&A (optional)

        Returns:
            dict: {
                "verdict": "PASS" | "PASS_WITH_WARNINGS" | "FAIL",
                "checks": list of check results,
                "summary": str,
                "timestamp": str
            }
        """
        checks = []

        # Run all 6 checks
        checks.append(self._check_completeness(plan))
        checks.append(self._check_consistency(plan))
        checks.append(self._check_feasibility(plan))
        checks.append(self._check_brief_alignment(plan, brief))
        checks.append(self._check_assumption_risk(plan))
        checks.append(self._check_information_transparency(plan))

        # Determine verdict
        failures = [c for c in checks if c["status"] == "FAIL"]
        warnings = [c for c in checks if c["status"] == "WARNING"]

        if failures:
            verdict = "FAIL"
            summary = f"Validation FAILED: {len(failures)} check(s) failed, {len(warnings)} warning(s)."
        elif warnings:
            verdict = "PASS_WITH_WARNINGS"
            summary = f"Validation PASSED with {len(warnings)} warning(s)."
        else:
            verdict = "PASS"
            summary = "All validation checks passed."

        return {
            "verdict": verdict,
            "checks": checks,
            "summary": summary,
            "failCount": len(failures),
            "warningCount": len(warnings),
            "passCount": len(checks) - len(failures) - len(warnings),
            "totalChecks": len(checks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _check_completeness(self, plan):
        """Check 1: All required sections are present and non-empty."""
        missing_sections = []
        empty_sections = []

        for section in REQUIRED_PLAN_SECTIONS:
            if section not in plan:
                missing_sections.append(section)
            elif not plan[section]:
                empty_sections.append(section)

        # Check WBS has tasks
        wbs = plan.get("wbs", {})
        if isinstance(wbs, dict):
            phases = wbs.get("phases", [])
            if not phases:
                empty_sections.append("wbs.phases")
            else:
                # Check each task has required fields
                missing_task_fields = []
                total_tasks = 0
                for phase in phases:
                    tasks = phase.get("tasks", [])
                    total_tasks += len(tasks)
                    for task in tasks:
                        for field in REQUIRED_TASK_FIELDS:
                            if field not in task or not task[field]:
                                missing_task_fields.append(
                                    f"{task.get('taskId', 'unknown')}.{field}"
                                )

                if total_tasks < MIN_TASKS_PER_PROJECT:
                    empty_sections.append(
                        f"wbs.tasks (only {total_tasks} tasks, minimum {MIN_TASKS_PER_PROJECT})"
                    )

                if missing_task_fields:
                    return {
                        "check": "COMPLETENESS",
                        "status": "FAIL",
                        "detail": f"Missing task fields: {missing_task_fields[:5]}...",
                        "missing": missing_sections,
                        "empty": empty_sections,
                    }
        elif isinstance(wbs, list):
            if len(wbs) < MIN_TASKS_PER_PROJECT:
                empty_sections.append(f"wbs (only {len(wbs)} tasks, minimum {MIN_TASKS_PER_PROJECT})")

        if missing_sections:
            return {
                "check": "COMPLETENESS",
                "status": "FAIL",
                "detail": f"Missing required sections: {missing_sections}",
                "missing": missing_sections,
                "empty": empty_sections,
            }

        if empty_sections:
            return {
                "check": "COMPLETENESS",
                "status": "WARNING",
                "detail": f"Empty sections: {empty_sections}",
                "missing": [],
                "empty": empty_sections,
            }

        return {
            "check": "COMPLETENESS",
            "status": "PASS",
            "detail": "All required sections present and non-empty",
            "missing": [],
            "empty": [],
        }

    def _check_consistency(self, plan):
        """Check 2: Scope, timeline, and effort are balanced."""
        issues = []

        scope = plan.get("scope", {})
        in_scope = scope.get("inScope", [])
        out_scope = scope.get("outScope", [])

        wbs = plan.get("wbs", {})
        phases = wbs.get("phases", []) if isinstance(wbs, dict) else []

        effort = plan.get("effortEstimation", {})
        total_effort = effort.get("totalDays", 0)

        cost = plan.get("costEstimation", {})
        total_cost = cost.get("totalCost", 0)

        # Check: effort vs task count
        total_tasks = 0
        phase_efforts = []
        for phase in phases:
            tasks = phase.get("tasks", [])
            total_tasks += len(tasks)
            phase_effort = phase.get("estimatedDays", sum(t.get("estimatedDays", 0) for t in tasks))
            phase_efforts.append({
                "phase": phase.get("phaseName", "unknown"),
                "effort": phase_effort,
                "taskCount": len(tasks),
            })

            if phase_effort > MAX_EFFORT_PER_PHASE:
                issues.append(
                    f"Phase '{phase.get('phaseName', 'unknown')}' has {phase_effort} days "
                    f"(exceeds max {MAX_EFFORT_PER_PHASE})"
                )

        # Check: revision markers must not leak into structural fields.
        # A revision note belongs in `revisionNote` or in the task title — never
        # in a phase name, because downstream consumers (Excel tracker, quotation
        # line items, UI spec) treat the phase name as a stable identifier.
        REVISION_MARKERS = ("[REVISED]", "[REJECTED]", "[NEW]", "->", "\u2192")
        for phase in phases:
            name = phase.get("phaseName", "") or ""
            hit = [m for m in REVISION_MARKERS if m in name]
            if hit:
                issues.append(
                    f"Phase name '{name}' contains a revision marker ({hit[0]}). "
                    f"Move the note to revisionNote; the phase name must stay stable."
                )

        # Check: total effort matches sum of task efforts
        if total_effort > 0 and total_tasks > 0:
            avg_effort_per_task = total_effort / total_tasks
            if avg_effort_per_task > 10:
                issues.append(
                    f"Average effort per task is {avg_effort_per_task:.1f} days "
                    f"(high - check if tasks are too coarse)"
                )
            elif avg_effort_per_task < 0.5:
                issues.append(
                    f"Average effort per task is {avg_effort_per_task:.1f} days "
                    f"(low - tasks may be too granular)"
                )

        # Check: cost vs effort ratio
        if total_effort > 0 and total_cost > 0:
            cost_per_day = total_cost / total_effort
            if cost_per_day < 300000:
                issues.append(
                    f"Cost per day is Rp {cost_per_day:,.0f} (below junior rate of Rp 500,000)"
                )
            elif cost_per_day > 2000000:
                issues.append(
                    f"Cost per day is Rp {cost_per_day:,.0f} (above senior rate of Rp 1,200,000)"
                )

        # Check: scope items vs deliverables
        deliverables = plan.get("deliverables", [])
        if in_scope and deliverables and len(in_scope) > len(deliverables) * 3:
            issues.append(
                f"Scope has {len(in_scope)} items but only {len(deliverables)} deliverables "
                f"(scope may be too broad for deliverables)"
            )

        if issues:
            return {
                "check": "CONSISTENCY",
                "status": "WARNING",
                "detail": "; ".join(issues),
                "issues": issues,
                "phaseBreakdown": phase_efforts,
            }

        return {
            "check": "CONSISTENCY",
            "status": "PASS",
            "detail": "Scope, timeline, and effort are balanced",
            "issues": [],
            "phaseBreakdown": phase_efforts,
        }

    def _check_feasibility(self, plan):
        """Check 3: Estimates are realistic given constraints."""
        issues = []

        effort = plan.get("effortEstimation", {})
        total_effort = effort.get("totalDays", 0)

        objectives = plan.get("objectives", [])
        if isinstance(objectives, list):
            obj_timeline = None
            for obj in objectives:
                if isinstance(obj, dict):
                    timeline = obj.get("timeline", obj.get("deadline", ""))
                    if timeline:
                        obj_timeline = timeline
                        break

        wbs = plan.get("wbs", {})
        phases = wbs.get("phases", []) if isinstance(wbs, dict) else []
        total_tasks = sum(len(p.get("tasks", [])) for p in phases)

        # Check: minimum tasks
        if total_tasks < MIN_TASKS_PER_PROJECT:
            issues.append(
                f"Only {total_tasks} tasks defined (minimum {MIN_TASKS_PER_PROJECT} expected)"
            )

        # Check: effort vs timeline
        # If timeline is 4 weeks = 20 working days, effort should not exceed 20 * buffer
        # We can't always parse timeline, so check total effort reasonableness
        if total_effort > 100:
            issues.append(
                f"Total effort is {total_effort} days (very high - consider splitting project)"
            )

        # Check: each task has estimatedDays
        tasks_without_effort = 0
        for phase in phases:
            for task in phase.get("tasks", []):
                if not task.get("estimatedDays") or task.get("estimatedDays") <= 0:
                    tasks_without_effort += 1

        if tasks_without_effort > 0:
            issues.append(
                f"{tasks_without_effort} task(s) missing effort estimates"
            )

        # Check: cost estimation has rate source
        cost = plan.get("costEstimation", {})
        rate_source = cost.get("rateSource", cost.get("source", ""))
        if not rate_source:
            issues.append("Cost estimation does not specify rate source")

        # Check: risks have mitigation
        risks = plan.get("risks", [])
        risks_without_mitigation = 0
        for risk in risks:
            if isinstance(risk, dict):
                if not risk.get("mitigation"):
                    risks_without_mitigation += 1

        if risks_without_mitigation > 0:
            issues.append(
                f"{risks_without_mitigation} risk(s) without mitigation strategy"
            )

        if issues:
            return {
                "check": "FEASIBILITY",
                "status": "WARNING",
                "detail": "; ".join(issues),
                "issues": issues,
            }

        return {
            "check": "FEASIBILITY",
            "status": "PASS",
            "detail": "Estimates are realistic",
            "issues": [],
        }

    def _check_brief_alignment(self, plan, brief=None):
        """Check 4: Plan addresses all brief requirements."""
        if not brief:
            return {
                "check": "BRIEF_ALIGNMENT",
                "status": "WARNING",
                "detail": "No brief provided for alignment check",
                "covered": [],
                "missing": [],
            }

        brief_text = ""
        if isinstance(brief, dict):
            brief_text = brief.get("briefText", "")
        elif isinstance(brief, str):
            brief_text = brief

        if not brief_text:
            return {
                "check": "BRIEF_ALIGNMENT",
                "status": "WARNING",
                "detail": "Brief text is empty",
                "covered": [],
                "missing": [],
            }

        brief_lower = brief_text.lower()

        # Extract key requirements from brief
        covered = []
        missing = []

        # Check for tech stack mention
        plan_scope = json.dumps(plan.get("scope", {})).lower()
        plan_wbs = json.dumps(plan.get("wbs", {})).lower()
        plan_combined = plan_scope + " " + plan_wbs

        # Check if brief's key tech terms appear in plan
        tech_keywords = ["react", "vue", "laravel", "node", "apps script", "google sheets",
                         "mobile", "wordpress", "python", "flask", "django"]

        brief_tech = [t for t in tech_keywords if t in brief_lower]
        for tech in brief_tech:
            if tech in plan_combined:
                covered.append(f"Tech: {tech}")
            else:
                missing.append(f"Tech: {tech} (mentioned in brief but not in plan)")

        # Check user types
        if "user type" in brief_lower or "user role" in brief_lower or "tipe user" in brief_lower:
            if "auth" in plan_combined or "role" in plan_combined or "user" in plan_combined:
                covered.append("User types/roles addressed")
            else:
                missing.append("User types/roles from brief not addressed in plan")

        # Check timeline
        timeline_keywords = ["week", "minggu", "bulan", "month", "hari", "day"]
        has_timeline = any(k in brief_lower for k in timeline_keywords)
        if has_timeline:
            effort = plan.get("effortEstimation", {})
            if effort.get("totalDays"):
                covered.append(f"Timeline considered (effort: {effort['totalDays']} days)")
            else:
                missing.append("Brief mentions timeline but plan has no effort estimate")

        if missing:
            return {
                "check": "BRIEF_ALIGNMENT",
                "status": "WARNING",
                "detail": f"Potential gaps: {'; '.join(missing[:3])}",
                "covered": covered,
                "missing": missing,
            }

        return {
            "check": "BRIEF_ALIGNMENT",
            "status": "PASS",
            "detail": f"Plan addresses brief requirements ({len(covered)} items covered)",
            "covered": covered,
            "missing": [],
        }

    def _check_assumption_risk(self, plan):
        """Check 5: High-risk assumptions flagged."""
        assumptions = plan.get("assumptions", [])
        info_sources = plan.get("informationSources", {})

        high_risk = []
        unflagged = []

        # Check assumptions structure
        for assumption in assumptions:
            if isinstance(assumption, dict):
                risk_level = assumption.get("riskLevel", "").lower()
                desc = assumption.get("description", assumption.get("text", ""))

                if risk_level == "high":
                    high_risk.append(desc)
                elif not risk_level:
                    unflagged.append(desc)
            elif isinstance(assumption, str):
                unflagged.append(assumption)

        # Check for assumptions in infoSources that aren't in assumptions array
        from_assumption = info_sources.get("fromAssumption", []) if isinstance(info_sources, dict) else []
        assumption_texts = []
        for a in assumptions:
            if isinstance(a, dict):
                assumption_texts.append(a.get("description", a.get("text", "")).lower())
            elif isinstance(a, str):
                assumption_texts.append(a.lower())

        for fa in from_assumption:
            if isinstance(fa, str) and fa.lower() not in assumption_texts:
                unflagged.append(f"[infoSources] {fa}")

        issues = []
        if high_risk:
            issues.append(f"{len(high_risk)} high-risk assumption(s): {high_risk[:2]}")

        if unflagged:
            issues.append(f"{len(unflagged)} assumption(s) without risk level: {unflagged[:2]}")

        if issues:
            return {
                "check": "ASSUMPTION_RISK",
                "status": "WARNING",
                "detail": "; ".join(issues),
                "highRisk": high_risk,
                "unflagged": unflagged,
            }

        return {
            "check": "ASSUMPTION_RISK",
            "status": "PASS",
            "detail": "All assumptions have risk levels, no high-risk assumptions",
            "highRisk": [],
            "unflagged": [],
        }

    def _check_information_transparency(self, plan):
        """Check 6: All information items properly tagged with source."""
        info_sources = plan.get("informationSources", {})

        if not info_sources:
            return {
                "check": "INFORMATION_TRANSPARENCY",
                "status": "FAIL",
                "detail": "No informationSources section in plan",
                "tagged": 0,
                "untagged": 0,
            }

        if isinstance(info_sources, dict):
            from_brief = info_sources.get("fromBrief", [])
            from_clarified = info_sources.get("fromClarification", [])
            from_assumption = info_sources.get("fromAssumption", [])
            from_ai = info_sources.get("fromAIRecommendation", [])

            tagged_count = len(from_brief) + len(from_clarified) + len(from_assumption) + len(from_ai)

            # Check that WBS tasks have source tags
            wbs = plan.get("wbs", {})
            phases = wbs.get("phases", []) if isinstance(wbs, dict) else []
            untagged_tasks = []

            for phase in phases:
                for task in phase.get("tasks", []):
                    source = task.get("source", task.get("informationSource", ""))
                    if not source:
                        untagged_tasks.append(task.get("taskId", "unknown"))

            if untagged_tasks:
                return {
                    "check": "INFORMATION_TRANSPARENCY",
                    "status": "WARNING",
                    "detail": f"{len(untagged_tasks)} task(s) without source tag: {untagged_tasks[:5]}",
                    "tagged": tagged_count,
                    "untagged": len(untagged_tasks),
                    "untaggedTasks": untagged_tasks,
                }

            if tagged_count == 0:
                return {
                    "check": "INFORMATION_TRANSPARENCY",
                    "status": "FAIL",
                    "detail": "No information items tagged with source",
                    "tagged": 0,
                    "untagged": 0,
                }

            return {
                "check": "INFORMATION_TRANSPARENCY",
                "status": "PASS",
                "detail": f"All information items tagged ({tagged_count} items across 4 categories)",
                "tagged": tagged_count,
                "untagged": 0,
                "breakdown": {
                    "BRIEF": len(from_brief),
                    "CLARIFIED": len(from_clarified),
                    "ASSUMPTION": len(from_assumption),
                    "AI_RECOMMENDATION": len(from_ai),
                },
            }

        return {
            "check": "INFORMATION_TRANSPARENCY",
            "status": "WARNING",
            "detail": "informationSources has unexpected format",
            "tagged": 0,
            "untagged": 0,
        }


# =============================================================================
# Self-Test
# =============================================================================

def run_selftest():
    """Run self-tests for Validator tool."""
    print("=" * 60)
    print("TOF Project Assistant - Validator Self-Test")
    print("=" * 60)

    validator = Validator()
    tests_passed = 0
    tests_failed = 0
    total_tests = 0

    def assert_test(name, condition, detail=""):
        nonlocal tests_passed, tests_failed, total_tests
        total_tests += 1
        if condition:
            tests_passed += 1
            print(f"  [PASS] {name}")
        else:
            tests_failed += 1
            print(f"  [FAIL] {name} - {detail}")

    # --- Test 1: Valid plan passes ---
    print("\n--- Test Group 1: Valid Plan ---")

    valid_plan = {
        "projectId": "PRJ-TEST-001",
        "objectives": [
            {"description": "Build WMS for SG Garage", "timeline": "4 weeks"}
        ],
        "scope": {
            "inScope": ["Customer management", "Vehicle management", "Service transactions"],
            "outScope": ["Multi-cabang", "Mobile app"],
        },
        "deliverables": ["Web app", "Documentation", "Training"],
        "wbs": {
            "phases": [
                {
                    "phaseName": "Requirements",
                    "estimatedDays": 3,
                    "tasks": [
                        {"taskId": "TASK-001", "title": "Gather requirements", "description": "Collect all requirements", "category": "requirements", "priority": "P0", "estimatedDays": 2, "source": "BRIEF"},
                        {"taskId": "TASK-002", "title": "Create spec", "description": "Write specification document", "category": "requirements", "priority": "P0", "estimatedDays": 1, "source": "AI_RECOMMENDATION"},
                    ]
                },
                {
                    "phaseName": "Development",
                    "estimatedDays": 15,
                    "tasks": [
                        {"taskId": "TASK-003", "title": "Frontend", "description": "Build React frontend", "category": "development", "priority": "P0", "estimatedDays": 8, "source": "BRIEF"},
                        {"taskId": "TASK-004", "title": "Backend", "description": "Build Apps Script backend", "category": "development", "priority": "P0", "estimatedDays": 5, "source": "BRIEF"},
                        {"taskId": "TASK-005", "title": "Integration", "description": "Connect frontend and backend", "category": "development", "priority": "P1", "estimatedDays": 2, "source": "AI_RECOMMENDATION"},
                    ]
                },
                {
                    "phaseName": "Testing",
                    "estimatedDays": 4,
                    "tasks": [
                        {"taskId": "TASK-006", "title": "Unit tests", "description": "Write and run unit tests", "category": "testing", "priority": "P1", "estimatedDays": 2, "source": "AI_RECOMMENDATION"},
                        {"taskId": "TASK-007", "title": "UAT", "description": "User acceptance testing", "category": "testing", "priority": "P0", "estimatedDays": 2, "source": "CLARIFIED"},
                    ]
                },
            ]
        },
        "effortEstimation": {"totalDays": 22},
        "costEstimation": {"totalCost": 22000000, "rateSource": "data/rate-card.md"},
        "risks": [
            {"description": "Timeline too tight", "probability": "medium", "impact": "high", "mitigation": "Add buffer days"},
        ],
        "assumptions": [
            {"description": "Developer works full-time", "riskLevel": "low"},
            {"description": "No major scope changes", "riskLevel": "medium"},
        ],
        "informationSources": {
            "fromBrief": ["React + Apps Script", "3 user types", "4 week timeline"],
            "fromClarification": ["Role-based auth needed"],
            "fromAssumption": ["Developer works full-time", "No major scope changes"],
            "fromAIRecommendation": ["Phased approach", "Priority ordering"],
        },
    }

    result = validator.validate(valid_plan)
    assert_test(
        "Valid plan - verdict is PASS or PASS_WITH_WARNINGS",
        result["verdict"] in ("PASS", "PASS_WITH_WARNINGS"),
        f"Got {result['verdict']} - {result['summary']}",
    )

    # Check all 6 checks ran
    assert_test(
        "All 6 checks executed",
        len(result["checks"]) == 6,
        f"Got {len(result['checks'])} checks",
    )

    # --- Test 2: Missing sections fail ---
    print("\n--- Test Group 2: Missing Sections ---")

    incomplete_plan = {"projectId": "PRJ-BAD"}
    result = validator.validate(incomplete_plan)
    assert_test(
        "Incomplete plan fails",
        result["verdict"] == "FAIL",
        f"Got {result['verdict']}",
    )

    completeness = [c for c in result["checks"] if c["check"] == "COMPLETENESS"][0]
    assert_test(
        "Completeness check fails",
        completeness["status"] == "FAIL",
    )

    # --- Test 3: Empty WBS warning ---
    print("\n--- Test Group 3: Empty WBS ---")

    empty_wbs_plan = {
        **valid_plan,
        "wbs": {"phases": []},
    }
    result = validator.validate(empty_wbs_plan)
    completeness = [c for c in result["checks"] if c["check"] == "COMPLETENESS"][0]
    assert_test(
        "Empty WBS flagged",
        completeness["status"] in ("FAIL", "WARNING"),
    )

    # --- Test 4: High effort per phase warning ---
    print("\n--- Test Group 4: High Effort Phase ---")

    high_effort_plan = json.loads(json.dumps(valid_plan))
    high_effort_plan["wbs"]["phases"][1]["estimatedDays"] = 70
    result = validator.validate(high_effort_plan)
    consistency = [c for c in result["checks"] if c["check"] == "CONSISTENCY"][0]
    assert_test(
        "High effort phase flagged",
        consistency["status"] == "WARNING",
    )

    # --- Test 5: Missing information sources ---
    print("\n--- Test Group 5: Information Transparency ---")

    no_sources_plan = json.loads(json.dumps(valid_plan))
    del no_sources_plan["informationSources"]
    result = validator.validate(no_sources_plan)
    transparency = [c for c in result["checks"] if c["check"] == "INFORMATION_TRANSPARENCY"][0]
    assert_test(
        "Missing infoSources fails",
        transparency["status"] == "FAIL",
    )

    # --- Test 6: High-risk assumptions ---
    print("\n--- Test Group 6: Assumption Risk ---")

    high_risk_plan = json.loads(json.dumps(valid_plan))
    high_risk_plan["assumptions"].append({"description": "Client will pay 100% upfront", "riskLevel": "high"})
    result = validator.validate(high_risk_plan)
    assumption_check = [c for c in result["checks"] if c["check"] == "ASSUMPTION_RISK"][0]
    assert_test(
        "High-risk assumption flagged",
        assumption_check["status"] == "WARNING" and len(assumption_check["highRisk"]) > 0,
    )

    # --- Test 7: Unflagged assumptions ---
    print("\n--- Test Group 7: Unflagged Assumptions ---")

    unflagged_plan = json.loads(json.dumps(valid_plan))
    unflagged_plan["assumptions"] = ["Some assumption without risk level"]
    result = validator.validate(unflagged_plan)
    assumption_check = [c for c in result["checks"] if c["check"] == "ASSUMPTION_RISK"][0]
    assert_test(
        "Unflagged assumption detected",
        assumption_check["status"] == "WARNING" and len(assumption_check["unflagged"]) > 0,
    )

    # --- Test 8: Brief alignment ---
    print("\n--- Test Group 8: Brief Alignment ---")

    brief = {
        "briefText": "We need a web app using React and Google Apps Script with Google Sheets backend. "
        "3 user types. Timeline 4 weeks."
    }
    result = validator.validate(valid_plan, brief=brief)
    alignment = [c for c in result["checks"] if c["check"] == "BRIEF_ALIGNMENT"][0]
    assert_test(
        "Brief alignment checks tech stack",
        "react" in json.dumps(alignment).lower(),
    )

    # --- Test 9: No brief ---
    print("\n--- Test Group 9: No Brief ---")

    result = validator.validate(valid_plan, brief=None)
    alignment = [c for c in result["checks"] if c["check"] == "BRIEF_ALIGNMENT"][0]
    assert_test(
        "No brief - warning",
        alignment["status"] == "WARNING",
    )

    # --- Test 10: Cost validation ---
    print("\n--- Test Group 10: Cost Validation ---")

    low_cost_plan = json.loads(json.dumps(valid_plan))
    low_cost_plan["costEstimation"]["totalCost"] = 100000  # too low for 22 days
    result = validator.validate(low_cost_plan)
    consistency = [c for c in result["checks"] if c["check"] == "CONSISTENCY"][0]
    assert_test(
        "Low cost flagged",
        consistency["status"] == "WARNING",
    )

    # --- Test 11: Tasks without source tags ---
    print("\n--- Test Group 11: Untagged Tasks ---")

    untagged_plan = json.loads(json.dumps(valid_plan))
    for phase in untagged_plan["wbs"]["phases"]:
        for task in phase["tasks"]:
            if "source" in task:
                del task["source"]
    result = validator.validate(untagged_plan)
    transparency = [c for c in result["checks"] if c["check"] == "INFORMATION_TRANSPARENCY"][0]
    assert_test(
        "Untagged tasks flagged",
        transparency["status"] == "WARNING" and transparency["untagged"] > 0,
    )

    # --- Test 12: Risks without mitigation ---
    print("\n--- Test Group 12: Risks Without Mitigation ---")

    no_mitigation_plan = json.loads(json.dumps(valid_plan))
    no_mitigation_plan["risks"] = [
        {"description": "Big risk", "probability": "high", "impact": "high"},
    ]
    result = validator.validate(no_mitigation_plan)
    feasibility = [c for c in result["checks"] if c["check"] == "FEASIBILITY"][0]
    assert_test(
        "Risk without mitigation flagged",
        feasibility["status"] == "WARNING",
    )

    # --- Test 13: Revision marker leaking into a phase name ---
    print("\n--- Test Group 13: Revision Marker in Phase Name ---")

    polluted = json.loads(json.dumps(valid_plan))
    polluted["wbs"]["phases"][1]["phaseName"] = "[REVISED] Development (Invoice -> Phase 2)"
    result = validator.validate(polluted)
    consistency = [c for c in result["checks"] if c["check"] == "CONSISTENCY"][0]
    assert_test(
        "Phase name with [REVISED] marker is flagged",
        consistency["status"] == "WARNING"
        and any("revision marker" in i for i in consistency.get("issues", [])),
        f"status={consistency['status']} issues={consistency.get('issues')}",
    )

    arrow_only = json.loads(json.dumps(valid_plan))
    arrow_only["wbs"]["phases"][2]["phaseName"] = "Testing -> Handover"
    result = validator.validate(arrow_only)
    consistency = [c for c in result["checks"] if c["check"] == "CONSISTENCY"][0]
    assert_test(
        "Phase name with an arrow is flagged (notes leak as structure)",
        consistency["status"] == "WARNING",
    )

    clean = json.loads(json.dumps(valid_plan))
    result = validator.validate(clean)
    consistency = [c for c in result["checks"] if c["check"] == "CONSISTENCY"][0]
    assert_test(
        "Clean phase names raise no revision-marker warning",
        not any("revision marker" in i for i in consistency.get("issues", [])),
    )

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed > 0:
        return False

    print("\nAll validator self-tests passed!")
    return True


if __name__ == "__main__":
    success = run_selftest()
    sys.exit(0 if success else 1)
