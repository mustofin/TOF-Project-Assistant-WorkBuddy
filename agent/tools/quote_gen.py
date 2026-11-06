#!/usr/bin/env python3
"""
TOF Project Assistant - Quotation Generator

Generates a quotation document from a project plan and client data.
Produces a structured JSON quotation that can be rendered into a DOCX
using the quotation template.

Usage:
    from quote_gen import QuotationGenerator
    gen = QuotationGenerator()

    quotation = gen.generate(
        project_id="PRJ-SGG-001",
        project_name="SG Garage - Workshop Management System",
        client_name="Budi Santoso",
        client_company="SG Garage",
        client_phone="0812-3456-7890",
        client_email="budi@sggarage.com",
        plan=plan_dict,
        rate_card_path="data/rate-card.md"
    )
"""

import json
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


class QuotationGenerator:
    """Generates structured quotation data from project plan."""

    # Default terms (can be overridden)
    DEFAULT_TERMS = [
        "Harga di atas sudah termasuk pajak yang berlaku.",
        "Pekerjaan akan dimulai setelah pembayaran tahap pertama diterima.",
        "Estimasi waktu pengerjaan dimulai setelah brief final disepakati.",
        "Perubahan scope di luar ketentuan awal akan dikenakan biaya tambahan.",
        "Source code menjadi milik klien setelah pelunasan.",
        "Garansi bug fix selama 30 hari setelah live.",
        "Meeting dan koordinasi via WhatsApp/Zoom.",
        "Pembayaran dilakukan via transfer bank.",
    ]

    # Default payment schedule
    DEFAULT_PAYMENT_SCHEDULE = [
        {"tahap": "Tahap 1 (DP)", "persentase": 50, "trigger": "Setelah konfirmasi dan brief final"},
        {"tahap": "Tahap 2 (Pelunasan)", "persentase": 50, "trigger": "Setelah UAT dan live"},
    ]

    def __init__(self):
        self.rate_card = {}

    def load_rate_card(self, rate_card_path):
        """Load rate card from markdown file."""
        if not rate_card_path or not Path(rate_card_path).exists():
            return self._default_rates()

        content = Path(rate_card_path).read_text(encoding="utf-8")
        rates = {}

        # Parse rate table: | Role | Rp X.000.000 | ... |
        pattern = r"\|\s*([^|]+)\s*\|\s*Rp\s*([\d.]+)\s*\|"
        matches = re.findall(pattern, content)

        for role, rate_str in matches:
            role = role.strip()
            rate = int(rate_str.replace(".", ""))
            if rate > 0:
                rates[role] = rate

        self.rate_card = rates if rates else self._default_rates()
        return self.rate_card

    def _default_rates(self):
        return {
            "Junior Developer": 500000,
            "Mid Developer": 800000,
            "Senior Developer": 1200000,
            "Full-stack Developer": 1000000,
            "UI/UX Designer": 900000,
            "QA Tester": 600000,
            "Project Manager": 1100000,
        }

    def generate_quote_number(self, project_id, date=None):
        """Generate a quotation number."""
        if date is None:
            date = datetime.now(timezone.utc)
        seq = date.strftime("%Y%m%d")
        # Use project ID suffix for uniqueness
        proj_suffix = project_id.replace("PRJ-", "").replace("-", "")[:4].upper()
        return f"QTO/{seq}/{proj_suffix}"

    def terbilang(self, amount):
        """
        Convert number to Indonesian words (terbilang).

        Args:
            amount: int - the amount in Rupiah

        Returns:
            str: amount in Indonesian words
        """
        if amount == 0:
            return "nol rupiah"

        ones = ["", "satu", "dua", "tiga", "empat", "lima", "enam",
                "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]

        def convert_below(n):
            if n < 12:
                return ones[n]
            elif n < 20:
                return convert_below(n - 10) + " belas"
            elif n < 100:
                tens = n // 10
                rest = n % 10
                return ones[tens] + " puluh" + (" " + ones[rest] if rest else "")
            elif n < 200:
                return "seratus" + (" " + convert_below(n - 100) if n - 100 else "")
            elif n < 1000:
                hundreds = n // 100
                rest = n % 100
                return ones[hundreds] + " ratus" + (" " + convert_below(rest) if rest else "")
            elif n < 2000:
                return "seribu" + (" " + convert_below(n - 1000) if n - 1000 else "")
            elif n < 1000000:
                thousands = n // 1000
                rest = n % 1000
                return convert_below(thousands) + " ribu" + (" " + convert_below(rest) if rest else "")
            elif n < 1000000000:
                millions = n // 1000000
                rest = n % 1000000
                return convert_below(millions) + " juta" + (" " + convert_below(rest) if rest else "")
            elif n < 1000000000000:
                billions = n // 1000000000
                rest = n % 1000000000
                return convert_below(billions) + " miliar" + (" " + convert_below(rest) if rest else "")
            else:
                return "angka terlalu besar"

        words = convert_below(amount)
        return words + " rupiah"

    def calculate_costs(self, plan, rate_card=None):
        """
        Calculate costs from plan's WBS and effort estimation.

        Returns:
            dict: {
                "lineItems": [...],
                "subtotal": int,
                "tax": int (0 for MVP),
                "total": int,
                "totalDays": int
            }
        """
        rates = rate_card or self.rate_card or self._default_rates()

        wbs = plan.get("wbs", {})
        phases = wbs.get("phases", []) if isinstance(wbs, dict) else []

        line_items = []
        subtotal = 0
        total_days = 0

        # Determine developer role from plan
        plan_role = plan.get("effortEstimation", {}).get("role", "Full-stack Developer")
        rate = rates.get(plan_role, rates.get("Full-stack Developer", 1000000))

        # Stack multiplier
        stack = plan.get("scope", {}).get("techStack", "")
        stack_multiplier = 1.0
        if "apps script" in stack.lower():
            stack_multiplier = 0.9
        elif "laravel" in stack.lower():
            stack_multiplier = 1.1
        elif "react native" in stack.lower():
            stack_multiplier = 1.2

        for phase in phases:
            phase_name = phase.get("phaseName", "Unknown")
            phase_days = phase.get("estimatedDays", 0)

            # Sum task days if phase days not set
            if not phase_days:
                phase_days = sum(t.get("estimatedDays", 0) for t in phase.get("tasks", []))

            if phase_days > 0:
                phase_cost = int(phase_days * rate * stack_multiplier)

                # Determine category for description
                category = "Development"
                if "requirement" in phase_name.lower():
                    category = "Analisa & Desain"
                elif "design" in phase_name.lower():
                    category = "UI/UX Design"
                elif "develop" in phase_name.lower():
                    category = "Development"
                elif "test" in phase_name.lower():
                    category = "Testing & QA"
                elif "deploy" in phase_name.lower():
                    category = "Deployment"

                line_items.append({
                    "no": len(line_items) + 1,
                    "item": phase_name,
                    "category": category,
                    "keterangan": f"{phase_days} hari kerja ({plan_role})",
                    "days": phase_days,
                    "ratePerDay": rate,
                    "biaya": phase_cost,
                })

                subtotal += phase_cost
                total_days += phase_days

        return {
            "lineItems": line_items,
            "subtotal": subtotal,
            "tax": 0,  # PPN included in price for MVP
            "total": subtotal,
            "totalDays": total_days,
            "rateUsed": plan_role,
            "ratePerDay": rate,
            "stackMultiplier": stack_multiplier,
        }

    def generate(self, project_id, project_name, client_name, client_company,
                 client_phone, client_email, plan, rate_card_path=None,
                 prepared_by="TOF Solusi Digital", valid_days=30,
                 terms=None, payment_schedule=None):
        """
        Generate a complete quotation.

        Returns:
            dict: Complete quotation data structure
        """
        # Load rates
        if rate_card_path:
            self.load_rate_card(rate_card_path)
        elif not self.rate_card:
            self.rate_card = self._default_rates()

        # Generate quote number
        now = datetime.now(timezone.utc)
        quote_number = self.generate_quote_number(project_id, now)

        # Calculate costs
        cost_calc = self.calculate_costs(plan)

        # Valid until
        valid_until = now + timedelta(days=valid_days)

        # Build quotation structure
        quotation = {
            "meta": {
                "quoteNumber": quote_number,
                "projectName": project_name,
                "projectId": project_id,
                "generatedAt": now.isoformat(),
                "generatedBy": "TOF Project Assistant - Quotation Generator",
                "validUntil": valid_until.isoformat(),
                "version": "1.0",
            },
            "company": {
                "name": "TOF Solusi Digital",
                "preparedBy": prepared_by,
            },
            "client": {
                "name": client_name,
                "company": client_company,
                "phone": client_phone,
                "email": client_email,
                "pic": client_name,
            },
            "project": {
                "name": project_name,
                "projectId": project_id,
                "timeline": plan.get("effortEstimation", {}).get("timeline", ""),
                "totalDays": cost_calc["totalDays"],
            },
            "workScope": cost_calc["lineItems"],
            "totalInvestment": {
                "subtotal": cost_calc["subtotal"],
                "tax": cost_calc["tax"],
                "total": cost_calc["total"],
                "terbilang": self.terbilang(cost_calc["total"]),
            },
            "terms": terms or self.DEFAULT_TERMS,
            "paymentSchedule": payment_schedule or self.DEFAULT_PAYMENT_SCHEDULE,
            "rateInfo": {
                "roleUsed": cost_calc["rateUsed"],
                "ratePerDay": cost_calc["ratePerDay"],
                "stackMultiplier": cost_calc["stackMultiplier"],
                "rateSource": rate_card_path or "default",
            },
            "approval": {
                "status": "DRAFT",
                "approvalRequired": True,
                "riskLevel": "medium",
                "note": "Quotation requires human review and approval before sending to client.",
            },
        }

        # Calculate payment amounts
        for payment in quotation["paymentSchedule"]:
            payment["nominal"] = int(cost_calc["total"] * payment["persentase"] / 100)

        return quotation

    def format_approval_card(self, quotation):
        """Format quotation as an approval card for user review."""
        total = quotation["totalInvestment"]["total"]
        lines = []
        lines.append("=== APPROVAL CARD: QUOTATION ===")
        lines.append(f"Action Type:     generate_quotation")
        lines.append(f"Quote Number:    {quotation['meta']['quoteNumber']}")
        lines.append(f"Project:         {quotation['project']['name']}")
        lines.append(f"Client:          {quotation['client']['name']} ({quotation['client']['company']})")
        lines.append(f"")
        lines.append(f"Work Scope:")
        for item in quotation["workScope"]:
            lines.append(f"  {item['no']}. [{item['category']}] {item['item']}")
            lines.append(f"     {item['keterangan']} - Rp {item['biaya']:,}")
        lines.append(f"")
        lines.append(f"Total Investment: Rp {total:,}")
        lines.append(f"Terbilang:        {quotation['totalInvestment']['terbilang']}")
        lines.append(f"")
        lines.append(f"Payment Schedule:")
        for p in quotation["paymentSchedule"]:
            lines.append(f"  {p['tahap']}: {p['persentase']}% = Rp {p['nominal']:,}")
        lines.append(f"")
        lines.append(f"Approval Status: {quotation['approval']['status']}")
        lines.append(f"Risk Level:      {quotation['approval']['riskLevel']}")
        lines.append(f"")
        lines.append(f"NOTE: {quotation['approval']['note']}")
        lines.append("================================")

        return "\n".join(lines)

    def validate_quotation(self, quotation):
        """
        Validate a quotation for completeness and correctness.

        Returns:
            dict: {"valid": bool, "errors": list, "warnings": list}
        """
        errors = []
        warnings = []

        # Check required fields
        if not quotation.get("meta", {}).get("quoteNumber"):
            errors.append("Missing quote number")

        if not quotation.get("client", {}).get("name"):
            errors.append("Missing client name")

        if not quotation.get("client", {}).get("email"):
            warnings.append("Missing client email")

        # Check work scope
        work_scope = quotation.get("workScope", [])
        if not work_scope:
            errors.append("No work scope items")

        # Check total
        total = quotation.get("totalInvestment", {}).get("total", 0)
        if total <= 0:
            errors.append(f"Invalid total: {total}")

        # Check payment schedule sums to 100%
        payments = quotation.get("paymentSchedule", [])
        if payments:
            total_pct = sum(p.get("persentase", 0) for p in payments)
            if total_pct != 100:
                errors.append(f"Payment schedule sums to {total_pct}% (should be 100%)")

        # Check terbilang
        terbilang = quotation.get("totalInvestment", {}).get("terbilang", "")
        if not terbilang:
            warnings.append("Missing terbilang (amount in words)")

        # Check line items sum
        if work_scope:
            items_sum = sum(item.get("biaya", 0) for item in work_scope)
            if items_sum != total:
                errors.append(f"Line items sum ({items_sum}) != total ({total})")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# =============================================================================
# Self-Test
# =============================================================================

def run_selftest():
    """Run self-tests for QuotationGenerator tool."""
    print("=" * 60)
    print("TOF Project Assistant - Quotation Generator Self-Test")
    print("=" * 60)

    gen = QuotationGenerator()
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

    # --- Test 1: Quote number generation ---
    print("\n--- Test Group 1: Quote Number ---")

    qn = gen.generate_quote_number("PRJ-SGG-001")
    assert_test(
        "Quote number has correct format",
        qn.startswith("QTO/") and "SGG0" in qn,
        f"Got: {qn}",
    )

    qn2 = gen.generate_quote_number("PRJ-ABC-002")
    assert_test(
        "Different project = different quote number",
        qn != qn2,
        f"{qn} vs {qn2}",
    )

    # --- Test 2: Terbilang ---
    print("\n--- Test Group 2: Terbilang (Amount in Words) ---")

    result = gen.terbilang(0)
    assert_test("Zero", result == "nol rupiah", f"Got: {result}")

    result = gen.terbilang(500000)
    assert_test("500000", "lima ratus ribu" in result, f"Got: {result}")

    result = gen.terbilang(1000000)
    assert_test("1000000", "satu juta" in result, f"Got: {result}")

    result = gen.terbilang(23800000)
    assert_test("23800000", "dua puluh tiga" in result and "juta" in result, f"Got: {result}")

    result = gen.terbilang(1500000)
    assert_test("1500000", "satu juta lima ratus ribu" in result, f"Got: {result}")

    # --- Test 3: Full quotation generation ---
    print("\n--- Test Group 3: Full Quotation ---")

    sample_plan = {
        "projectId": "PRJ-SGG-001",
        "projectName": "SG Garage - WMS",
        "scope": {
            "techStack": "React + Apps Script + Google Sheets",
        },
        "effortEstimation": {
            "totalDays": 22,
            "role": "Full-stack Developer",
            "timeline": "4 weeks",
        },
        "wbs": {
            "phases": [
                {
                    "phaseName": "Requirements & Design",
                    "estimatedDays": 4,
                    "tasks": [{"taskId": "T1", "estimatedDays": 4}]
                },
                {
                    "phaseName": "Development",
                    "estimatedDays": 14,
                    "tasks": [{"taskId": "T2", "estimatedDays": 14}]
                },
                {
                    "phaseName": "Testing & Deployment",
                    "estimatedDays": 4,
                    "tasks": [{"taskId": "T3", "estimatedDays": 4}]
                },
            ]
        },
    }

    quotation = gen.generate(
        project_id="PRJ-SGG-001",
        project_name="SG Garage - Workshop Management System",
        client_name="Budi Santoso",
        client_company="SG Garage",
        client_phone="0812-3456-7890",
        client_email="budi@sggarage.com",
        plan=sample_plan,
    )

    assert_test(
        "Quotation has quote number",
        bool(quotation["meta"]["quoteNumber"]),
    )

    assert_test(
        "Quotation has client info",
        quotation["client"]["name"] == "Budi Santoso",
    )

    assert_test(
        "Quotation has work scope",
        len(quotation["workScope"]) == 3,
        f"Got {len(quotation['workScope'])} items",
    )

    assert_test(
        "Quotation total > 0",
        quotation["totalInvestment"]["total"] > 0,
        f"Total: {quotation['totalInvestment']['total']}",
    )

    assert_test(
        "Quotation has terbilang",
        bool(quotation["totalInvestment"]["terbilang"]),
    )

    assert_test(
        "Quotation has terms",
        len(quotation["terms"]) >= 5,
    )

    assert_test(
        "Quotation has payment schedule",
        len(quotation["paymentSchedule"]) >= 2,
    )

    # --- Test 4: Payment schedule sums to 100% ---
    print("\n--- Test Group 4: Payment Schedule ---")

    total_pct = sum(p["persentase"] for p in quotation["paymentSchedule"])
    assert_test(
        "Payment schedule sums to 100%",
        total_pct == 100,
        f"Got: {total_pct}%",
    )

    # Check nominal sums to total
    total_nominal = sum(p["nominal"] for p in quotation["paymentSchedule"])
    assert_test(
        "Payment nominals sum to total",
        total_nominal == quotation["totalInvestment"]["total"],
        f"{total_nominal} vs {quotation['totalInvestment']['total']}",
    )

    # --- Test 5: Stack multiplier ---
    print("\n--- Test Group 5: Stack Multiplier ---")

    # Apps Script = 0.9x multiplier
    rate = gen.rate_card.get("Full-stack Developer", 1000000)
    expected_total = int(22 * rate * 0.9)  # 22 days * rate * 0.9
    assert_test(
        "Apps Script stack multiplier applied (0.9x)",
        quotation["totalInvestment"]["total"] == expected_total,
        f"Expected: {expected_total}, Got: {quotation['totalInvestment']['total']}",
    )

    # --- Test 6: Cost calculation ---
    print("\n--- Test Group 6: Cost Calculation ---")

    costs = gen.calculate_costs(sample_plan)
    assert_test(
        "Cost calculation has line items",
        len(costs["lineItems"]) == 3,
    )

    assert_test(
        "Cost calculation total days = 22",
        costs["totalDays"] == 22,
        f"Got: {costs['totalDays']}",
    )

    # Line items sum = subtotal
    items_sum = sum(item["biaya"] for item in costs["lineItems"])
    assert_test(
        "Line items sum = subtotal",
        items_sum == costs["subtotal"],
        f"{items_sum} vs {costs['subtotal']}",
    )

    # --- Test 7: Quotation validation ---
    print("\n--- Test Group 7: Quotation Validation ---")

    validation = gen.validate_quotation(quotation)
    assert_test(
        "Valid quotation passes validation",
        validation["valid"],
        f"Errors: {validation['errors']}",
    )

    # Invalid quotation
    bad_quotation = {
        "meta": {},
        "client": {},
        "workScope": [],
        "totalInvestment": {"total": 0},
        "paymentSchedule": [{"persentase": 50}],
    }
    validation = gen.validate_quotation(bad_quotation)
    assert_test(
        "Invalid quotation fails validation",
        not validation["valid"],
    )

    # --- Test 8: Approval card ---
    print("\n--- Test Group 8: Approval Card ---")

    card = gen.format_approval_card(quotation)
    assert_test(
        "Approval card has header",
        "APPROVAL CARD: QUOTATION" in card,
    )

    assert_test(
        "Approval card has total",
        "Total Investment" in card,
    )

    assert_test(
        "Approval card has risk level",
        "medium" in card.lower(),
    )

    # --- Test 9: Rate card loading ---
    print("\n--- Test Group 9: Rate Card ---")

    rates = gen.load_rate_card("data/rate-card.md")
    assert_test(
        "Rate card loaded",
        len(rates) > 0,
        f"Got {len(rates)} rates",
    )

    assert_test(
        "Full-stack Developer rate = 1,000,000",
        rates.get("Full-stack Developer") == 1000000,
        f"Got: {rates.get('Full-stack Developer')}",
    )

    # --- Test 10: Different roles ---
    print("\n--- Test Group 10: Different Developer Roles ---")

    junior_plan = json.loads(json.dumps(sample_plan))
    junior_plan["effortEstimation"]["role"] = "Junior Developer"
    junior_quote = gen.generate(
        project_id="PRJ-JUN-001",
        project_name="Test Junior",
        client_name="Test",
        client_company="Test Co",
        client_phone="0800",
        client_email="test@test.com",
        plan=junior_plan,
    )
    assert_test(
        "Junior rate cheaper than Full-stack",
        junior_quote["totalInvestment"]["total"] < quotation["totalInvestment"]["total"],
        f"Junior: {junior_quote['totalInvestment']['total']}, Full-stack: {quotation['totalInvestment']['total']}",
    )

    # --- Test 11: Custom terms ---
    print("\n--- Test Group 11: Custom Terms ---")

    custom_terms = ["Custom term 1", "Custom term 2"]
    custom_quote = gen.generate(
        project_id="PRJ-CUST-001",
        project_name="Custom",
        client_name="Test",
        client_company="Test",
        client_phone="0800",
        client_email="t@t.com",
        plan=sample_plan,
        terms=custom_terms,
    )
    assert_test(
        "Custom terms used",
        custom_quote["terms"] == custom_terms,
    )

    # --- Test 12: Empty plan ---
    print("\n--- Test Group 12: Empty Plan ---")

    empty_quote = gen.generate(
        project_id="PRJ-EMPTY-001",
        project_name="Empty",
        client_name="Test",
        client_company="Test",
        client_phone="0800",
        client_email="t@t.com",
        plan={"wbs": {"phases": []}},
    )
    assert_test(
        "Empty plan = zero total",
        empty_quote["totalInvestment"]["total"] == 0,
    )

    assert_test(
        "Empty plan = no work scope",
        len(empty_quote["workScope"]) == 0,
    )

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed > 0:
        return False

    print("\nAll quotation generator self-tests passed!")
    return True


if __name__ == "__main__":
    success = run_selftest()
    sys.exit(0 if success else 1)
