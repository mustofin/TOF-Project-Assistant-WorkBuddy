#!/usr/bin/env python3
"""
TOF Project Assistant - UI Spec Generator

Deterministic tool: project plan (structured) -> UI screen inventory + design tokens.

This is the "structured -> visual" bridge. Given an approved project plan,
it derives which screens the app needs and a consistent design system, so the
UI mockups are derived from the plan instead of invented from nothing.

No LLM involved: same plan always produces the same spec. Testable.

Usage:
    from ui_spec import UISpecGenerator
    gen = UISpecGenerator()
    spec = gen.build(plan, client={"company": "SG Garage"})
    print(spec["screens"])      # list of screens to design
    print(spec["tokens"])       # colors, type scale, spacing
"""

import json
import re
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------- design system

BASE_TOKENS = {
    "color": {
        "primary": "#1E5EFF",
        "primaryDark": "#0B3BB8",
        "primarySoft": "#E8EFFF",
        "accent": "#00B37E",
        "accentSoft": "#E3F8F0",
        "danger": "#E5484D",
        "dangerSoft": "#FDECEC",
        "warning": "#F5A524",
        "warningSoft": "#FEF6E7",
        "ink": "#111827",
        "inkMuted": "#5B6472",
        "inkFaint": "#9AA3B2",
        "line": "#E4E8EF",
        "surface": "#FFFFFF",
        "canvas": "#F6F8FB",
    },
    "font": {
        "family": "Inter, -apple-system, 'Segoe UI', sans-serif",
        "mono": "'SF Mono', Menlo, monospace",
        "size": {"xs": 11, "sm": 12, "base": 14, "md": 16, "lg": 20, "xl": 28, "display": 36},
        "weight": {"regular": 400, "medium": 500, "semibold": 600, "bold": 700},
        "lineHeight": {"tight": 1.25, "normal": 1.5, "loose": 1.7},
    },
    "space": {"1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48},
    "radius": {"sm": 6, "md": 10, "lg": 14, "pill": 999},
    "shadow": {
        "card": "0 1px 2px rgba(17,24,39,.04), 0 4px 12px rgba(17,24,39,.06)",
        "pop": "0 8px 28px rgba(17,24,39,.14)",
    },
    "layout": {"sidebar": 232, "topbar": 60, "contentMax": 1180, "gutter": 24},
}

# ---------------------------------------------------------------- screen rules

# Each rule: keyword(s) in a scope item -> screens it implies.
# (id, title, archetype, description, key columns/fields)
SCREEN_RULES = [
    {
        "match": ["dashboard", "ringkasan", "summary"],
        "screens": [
            ("dashboard", "Dashboard", "dashboard",
             "Operational overview: KPI cards, recent activity, alerts", []),
        ],
    },
    {
        "match": ["customer", "pelanggan"],
        "screens": [
            ("customer-list", "Customer List", "list",
             "Browse and search customers",
             ["Name", "Phone", "Vehicles", "Last Visit"]),
            ("customer-form", "Add / Edit Customer", "form",
             "Create or update a customer record",
             ["Full Name", "Phone", "Email", "Address", "Notes"]),
        ],
    },
    {
        "match": ["vehicle", "kendaraan"],
        "screens": [
            ("vehicle-list", "Vehicle List", "list",
             "Vehicles registered per customer",
             ["Plate", "Model", "Year", "Owner", "Last Service"]),
            ("vehicle-form", "Add / Edit Vehicle", "form",
             "Register a vehicle under a customer",
             ["Plate Number", "Brand", "Model", "Year", "Owner", "Notes"]),
        ],
    },
    {
        "match": ["service", "transaksi", "transaction", "order"],
        "screens": [
            ("service-list", "Service Orders", "list",
             "All service transactions with status",
             ["Order #", "Customer", "Vehicle", "Status", "Total"]),
            ("service-form", "New Service Order", "form",
             "Create a service order and add line items",
             ["Customer", "Vehicle", "Complaint", "Mechanic", "Items"]),
            ("service-detail", "Service Detail", "detail",
             "Single order: status timeline, items, invoice link", []),
        ],
    },
    {
        "match": ["inventory", "stock", "stok", "suku cadang", "part"],
        "screens": [
            ("inventory-list", "Inventory", "list",
             "Parts stock levels with low-stock warnings",
             ["SKU", "Part Name", "Stock", "Min", "Price"]),
            ("stock-form", "Stock In / Out", "form",
             "Record stock movement",
             ["Part", "Movement", "Quantity", "Reference", "Date"]),
        ],
    },
    {
        "match": ["invoice", "faktur", "tagihan", "billing"],
        "screens": [
            ("invoice-list", "Invoices", "list",
             "Issued invoices and payment status",
             ["Invoice #", "Customer", "Issued", "Due", "Status", "Amount"]),
            ("invoice-preview", "Invoice Preview", "detail",
             "Printable invoice for the customer", []),
        ],
    },
    {
        "match": ["report", "laporan", "monthly"],
        "screens": [
            ("report-monthly", "Monthly Report", "dashboard",
             "Revenue and volume by period", []),
        ],
    },
    {
        "match": ["login", "auth", "role", "akses"],
        "screens": [
            ("login", "Sign In", "auth",
             "Email + password sign in with role detection", []),
        ],
    },
    {
        "match": ["user", "pengguna", "karyawan", "staff", "employee"],
        "screens": [
            ("user-list", "Users & Roles", "list",
             "Staff accounts and their access level",
             ["Name", "Email", "Role", "Status", "Last Login"]),
        ],
    },
]

# Role -> which screens they can open (derived from plan user types)
ROLE_HINTS = {
    "service advisor": ["dashboard", "customer-*", "vehicle-*", "service-*"],
    "kasir": ["dashboard", "invoice-*", "service-list"],
    "kepala bengkel": ["*"],
    "admin": ["*"],
    "owner": ["*"],
    "manager": ["*"],
}

# Which design file / page each archetype maps to in Figcraft
ARCHETYPE_PAGE = {
    "auth": "01 Auth",
    "dashboard": "02 Dashboard",
    "list": "03 Lists",
    "form": "04 Forms",
    "detail": "05 Details",
}


class UISpecGenerator:
    """Derives a UI screen inventory + design tokens from a project plan."""

    def build(self, plan, client=None, brand=None, platform="web"):
        """
        Build a UI spec from a project plan.

        Args:
            plan: project plan dict (needs scope.inScope at minimum)
            client: {"company": "...", "industry": "..."} for naming
            brand: optional {"primary": "#hex"} to override the palette
            platform: "web" | "mobile"

        Returns:
            dict: {screens, tokens, navigation, roles, meta}
        """
        client = client or {}
        scope_items = self._extract_scope(plan)
        user_types = self._extract_user_types(plan)

        screens = self._derive_screens(scope_items)
        if not screens:
            screens = self._fallback_screens(scope_items)

        tokens = self._build_tokens(brand)
        nav = self._build_nav(screens)
        roles = self._build_roles(user_types, screens)

        return {
            "meta": {
                "projectId": plan.get("projectId", ""),
                "projectName": plan.get("projectName", ""),
                "client": client.get("company", ""),
                "platform": platform,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "generator": "tof-ui-designer/ui_spec.py",
                "source": "derived from plan scope — no invented features",
            },
            "screens": screens,
            "navigation": nav,
            "roles": roles,
            "tokens": tokens,
            "stats": {
                "screenCount": len(screens),
                "archetypes": sorted({s["archetype"] for s in screens}),
                "scopeItemsUsed": len(scope_items),
                "userTypes": len(user_types),
            },
        }

    # ------------------------------------------------------------ extraction

    def _extract_scope(self, plan):
        scope = plan.get("scope", {})
        if isinstance(scope, dict):
            items = scope.get("inScope", [])
        elif isinstance(scope, list):
            items = scope
        else:
            items = []
        return [str(i) for i in items if str(i).strip()]

    def _extract_user_types(self, plan):
        """
        Pull staff roles out of brief/clarification text.

        Only lines that talk about *users* or *roles* are scanned — otherwise
        data entities ("Customer management") get mistaken for roles.
        """
        found = []
        src = plan.get("informationSources", {}) or {}
        candidates = list(src.get("fromBrief", [])) + list(src.get("fromClarification", []))

        role_context = ("user type", "user types", "role", "akses", "access level",
                        "pengguna", "hak akses")

        haystack_parts = []
        for item in candidates:
            low = str(item).lower()
            if any(ctx in low for ctx in role_context):
                haystack_parts.append(low)
        haystack = " ".join(haystack_parts)

        if not haystack:
            return []

        # Staff roles only — customers are data, not app roles.
        known = ["service advisor", "kasir", "kepala bengkel", "admin", "owner",
                 "manager", "supervisor", "staff", "mekanik", "gudang"]
        for k in known:
            if k in haystack:
                found.append(k.title())

        if not found:
            m = re.search(r"(\d+)\s+(?:user\s+types|roles?)", haystack)
            if m:
                found = [f"Role {i+1}" for i in range(int(m.group(1)))]
        return found

    # ------------------------------------------------------------ screens

    def _derive_screens(self, scope_items):
        screens = []
        seen = set()

        for item in scope_items:
            low = item.lower()
            for rule in SCREEN_RULES:
                if not any(k in low for k in rule["match"]):
                    continue
                for sid, title, archetype, desc, fields in rule["screens"]:
                    if sid in seen:
                        continue
                    seen.add(sid)
                    screens.append({
                        "id": sid,
                        "title": title,
                        "archetype": archetype,
                        "page": ARCHETYPE_PAGE.get(archetype, "09 Other"),
                        "description": desc,
                        "columns": fields if archetype in ("list",) else [],
                        "fields": fields if archetype in ("form",) else [],
                        "derivedFrom": item,
                    })

        # Always need a sign-in if there is more than one role
        if "login" not in seen and len(screens) > 2:
            screens.insert(0, {
                "id": "login", "title": "Sign In", "archetype": "auth",
                "page": ARCHETYPE_PAGE["auth"],
                "description": "Email + password sign in with role detection",
                "columns": [], "fields": [], "derivedFrom": "implicit: multi-user app",
            })

        # Dashboard first
        screens.sort(key=lambda s: (0 if s["archetype"] == "dashboard" else
                                    1 if s["archetype"] == "auth" else 2, s["id"]))
        return screens

    def _fallback_screens(self, scope_items):
        """If scope wording didn't match any rule, make a generic CRUD set."""
        base = [
            ("dashboard", "Dashboard", "dashboard", "Overview", []),
            ("records-list", "Records", "list", "Browse records",
             ["ID", "Name", "Status", "Updated"]),
            ("records-form", "Add / Edit Record", "form", "Create or edit",
             ["Name", "Description", "Status"]),
        ]
        return [{
            "id": sid, "title": title, "archetype": arch,
            "page": ARCHETYPE_PAGE.get(arch, "09 Other"),
            "description": desc,
            "columns": f if arch == "list" else [],
            "fields": f if arch == "form" else [],
            "derivedFrom": scope_items[0] if scope_items else "fallback",
        } for sid, title, arch, desc, f in base]

    def _build_nav(self, screens):
        """Group screens into a sidebar navigation."""
        groups = {}
        for s in screens:
            if s["archetype"] == "auth":
                continue
            group = s["page"].split(" ", 1)[-1]
            groups.setdefault(group, []).append({"id": s["id"], "title": s["title"]})
        return [{"group": g, "items": items} for g, items in groups.items()]

    def _build_roles(self, user_types, screens):
        """Map roles to visible screen ids."""
        all_ids = [s["id"] for s in screens]
        roles = []
        for ut in user_types:
            key = ut.lower()
            patterns = ROLE_HINTS.get(key, ["*"])
            if "*" in patterns:
                visible = all_ids
            else:
                visible = []
                for p in patterns:
                    if p.endswith("*"):
                        visible += [i for i in all_ids if i.startswith(p[:-1])]
                    elif p in all_ids:
                        visible.append(p)
            roles.append({
                "role": ut,
                "visibleScreens": sorted(set(visible)),
                "screenCount": len(set(visible)),
            })
        return roles

    def _build_tokens(self, brand):
        tokens = json.loads(json.dumps(BASE_TOKENS))  # deep copy
        if brand and brand.get("primary"):
            tokens["color"]["primary"] = brand["primary"]
        return tokens

    # ------------------------------------------------------------ checks

    def validate(self, spec):
        """Sanity-check a spec before it is used to generate designs."""
        errors, warnings = [], []

        screens = spec.get("screens", [])
        if not screens:
            errors.append("No screens derived")
        if len(screens) > 20:
            warnings.append(f"{len(screens)} screens is a lot for one MVP — consider splitting")

        ids = [s["id"] for s in screens]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            errors.append(f"Duplicate screen ids: {sorted(dupes)}")

        for s in screens:
            if s["archetype"] == "list" and not s.get("columns"):
                warnings.append(f"{s['id']}: list screen has no columns")
            if s["archetype"] == "form" and not s.get("fields"):
                warnings.append(f"{s['id']}: form screen has no fields")

        if not any(s["archetype"] == "dashboard" for s in screens):
            warnings.append("No dashboard screen derived")

        roles = spec.get("roles", [])
        for r in roles:
            if r["screenCount"] == 0:
                warnings.append(f"Role '{r['role']}' has no visible screens")

        return {"valid": not errors, "errors": errors, "warnings": warnings}


# =============================================================================
# Self-Test
# =============================================================================

def run_selftest():
    print("=" * 60)
    print("TOF Project Assistant - UI Spec Self-Test")
    print("=" * 60)

    gen = UISpecGenerator()
    passed = failed = total = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed, total
        total += 1
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} - {detail}")

    # --- 1: derives screens from SG Garage plan ---
    print("\n--- Group 1: Screen Derivation ---")
    plan = {
        "projectId": "PRJ-SGG-001",
        "projectName": "SG Garage WMS",
        "scope": {"inScope": [
            "Customer management (CRUD)",
            "Vehicle management (CRUD, linked to customer)",
            "Service transactions (create, update, status tracking)",
            "Inventory management (stock in/out, low stock alert)",
            "Invoice printing (PDF generation from service transaction)",
            "Dashboard (daily revenue, active services, stock alerts)",
            "Role-based authentication (3 roles)",
        ]},
        "informationSources": {
            "fromBrief": ["3 user types: Service Advisor, Kasir, Kepala Bengkel"],
        },
    }
    spec = gen.build(plan, client={"company": "SG Garage"})

    check("Derives screens", len(spec["screens"]) >= 8, f"got {len(spec['screens'])}")
    check("Has dashboard", any(s["archetype"] == "dashboard" for s in spec["screens"]))
    check("Has login", any(s["id"] == "login" for s in spec["screens"]))
    check("Has customer list", any(s["id"] == "customer-list" for s in spec["screens"]))
    check("Has service form", any(s["id"] == "service-form" for s in spec["screens"]))
    check("Has invoice preview", any(s["id"] == "invoice-preview" for s in spec["screens"]))
    check("Has inventory list", any(s["id"] == "inventory-list" for s in spec["screens"]))

    # --- 2: every screen traces to a scope item ---
    print("\n--- Group 2: Traceability ---")
    untraced = [s["id"] for s in spec["screens"] if not s.get("derivedFrom")]
    check("Every screen has derivedFrom", not untraced, str(untraced))

    derived = {s["derivedFrom"] for s in spec["screens"]}
    check("derivedFrom values come from plan scope",
          all(d in plan["scope"]["inScope"] or d.startswith("implicit:")
              for d in derived),
          str(derived))

    # --- 3: roles ---
    print("\n--- Group 3: Roles ---")
    check("Extracts 3 roles", len(spec["roles"]) == 3,
          f"got {[r['role'] for r in spec['roles']]}")
    ketua = next((r for r in spec["roles"] if "kepala" in r["role"].lower()), None)
    check("Kepala Bengkel sees all screens",
          ketua is not None and ketua["screenCount"] == len(spec["screens"]),
          str(ketua))
    kasir = next((r for r in spec["roles"] if r["role"].lower() == "kasir"), None)
    check("Kasir restricted to fewer screens",
          kasir is not None and kasir["screenCount"] < len(spec["screens"]),
          str(kasir))

    # --- 4: tokens ---
    print("\n--- Group 4: Design Tokens ---")
    check("Has primary color", spec["tokens"]["color"]["primary"].startswith("#"))
    check("Has type scale", "size" in spec["tokens"]["font"])
    check("Has spacing scale", len(spec["tokens"]["space"]) >= 6)
    check("Has radius scale", "md" in spec["tokens"]["radius"])

    branded = gen.build(plan, brand={"primary": "#FF5722"})
    check("Brand override applied",
          branded["tokens"]["color"]["primary"] == "#FF5722")

    # --- 5: determinism ---
    print("\n--- Group 5: Determinism ---")
    a = gen.build(plan)
    b = gen.build(plan)
    check("Same plan -> same screens", a["screens"] == b["screens"])
    check("Same plan -> same tokens", a["tokens"] == b["tokens"])

    # --- 6: validation ---
    print("\n--- Group 6: Validation ---")
    v = gen.validate(spec)
    check("Valid spec passes", v["valid"], str(v["errors"]))
    check("No duplicate ids",
          len({s['id'] for s in spec['screens']}) == len(spec['screens']))

    bad = {"screens": [{"id": "x", "title": "X", "archetype": "list", "columns": []},
                       {"id": "x", "title": "X2", "archetype": "form", "fields": []}],
           "roles": []}
    vb = gen.validate(bad)
    check("Duplicate ids rejected", not vb["valid"], str(vb["errors"]))
    check("Empty list columns warned", any("no columns" in w for w in vb["warnings"]))

    empty = gen.build({"projectId": "P", "scope": {"inScope": []}})
    check("Empty scope -> fallback screens", len(empty["screens"]) == 3,
          f"got {len(empty['screens'])}")

    # --- 7: nav ---
    print("\n--- Group 7: Navigation ---")
    check("Nav groups built", len(spec["navigation"]) >= 3,
          str([n["group"] for n in spec["navigation"]]))
    nav_ids = [i["id"] for g in spec["navigation"] for i in g["items"]]
    check("Login excluded from nav", "login" not in nav_ids)

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)
    if failed == 0:
        print("\nAll UI spec self-tests passed!")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_selftest() else 1)
