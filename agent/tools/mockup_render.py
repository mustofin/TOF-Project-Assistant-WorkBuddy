#!/usr/bin/env python3
"""
TOF Project Assistant - Mockup Renderer

Turns a UI spec (from ui_spec.py) into HTML wireframe/mockup pages,
then renders them to PNG with headless Chrome.

This is the fallback/offline path. When the Figcraft app is running, the
tof-ui-designer skill uses Figcraft MCP instead and exports from there.
Both paths consume the SAME spec, so output is consistent.

Usage:
    from mockup_render import MockupRenderer
    r = MockupRenderer()
    paths = r.render_all(spec, out_dir="state/projects/PRJ-001/ui-design")
"""

import json
import subprocess
import sys
from pathlib import Path

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    return None


class MockupRenderer:
    def __init__(self, width=1440, height=900):
        self.width = width
        self.height = height
        self.chrome = find_chrome()

    # Viewport height per archetype — short screens don't need a full frame
    HEIGHTS = {"auth": 640, "form": 780, "detail": 720, "list": 880, "dashboard": 880}

    def height_for(self, screen):
        return self.HEIGHTS.get(screen.get("archetype"), self.height)

    # ------------------------------------------------------------- shell

    def _shell(self, spec, screen, body_html, active_nav=None):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        frame_h = self.height_for(screen)
        nav_html = ""
        for group in spec.get("navigation", []):
            items = ""
            for it in group["items"]:
                active = (active_nav == it["id"])
                bg = c["primarySoft"] if active else "transparent"
                fg = c["primary"] if active else c["inkMuted"]
                weight = f["weight"]["semibold"] if active else f["weight"]["regular"]
                items += (
                    f'<div class="nav-item" style="background:{bg};color:{fg};'
                    f'font-weight:{weight}">{it["title"]}</div>'
                )
            nav_html += (
                f'<div class="nav-group"><div class="nav-label">{group["group"]}</div>'
                f'{items}</div>'
            )

        company = spec["meta"].get("client") or spec["meta"].get("projectName", "App")
        initials = "".join(w[0] for w in company.split()[:2]).upper() or "AP"
        proj = spec["meta"].get("projectName", "")
        proj_short = proj if len(proj) <= 24 else proj[:23].rstrip() + "…"

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{screen['title']}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:{f['family']};background:{c['canvas']};color:{c['ink']};
        -webkit-font-smoothing:antialiased}}
  .app{{display:flex;min-height:{frame_h}px}}
  .sidebar{{width:{t['layout']['sidebar']}px;background:{c['surface']};
            border-right:1px solid {c['line']};padding:{sp['4']}px 0;flex-shrink:0;
            display:flex;flex-direction:column}}
  .brand{{display:flex;align-items:center;gap:{sp['3']}px;padding:0 {sp['4']}px {sp['5']}px}}
  .brand-mark{{width:34px;height:34px;border-radius:{t['radius']['md']}px;
               background:{c['primary']};color:#fff;display:flex;align-items:center;
               justify-content:center;font-weight:{f['weight']['bold']};
               font-size:{f['size']['sm']}px;letter-spacing:.4px}}
  .brand-name{{font-size:{f['size']['base']}px;font-weight:{f['weight']['semibold']}}}
  .brand-sub{{font-size:{f['size']['xs']}px;color:{c['inkFaint']}}}
  .nav-group{{margin-bottom:{sp['5']}px}}
  .nav-label{{font-size:10px;text-transform:uppercase;letter-spacing:.8px;
              color:{c['inkFaint']};padding:0 {sp['4']}px {sp['2']}px;
              font-weight:{f['weight']['semibold']}}}
  .nav-item{{padding:{sp['2']}px {sp['4']}px;margin:1px {sp['2']}px;
             border-radius:{t['radius']['sm']}px;font-size:{f['size']['sm']}px;cursor:default}}
  .main{{flex:1;display:flex;flex-direction:column;min-width:0}}
  .topbar{{height:{t['layout']['topbar']}px;background:{c['surface']};
           border-bottom:1px solid {c['line']};display:flex;align-items:center;
           justify-content:space-between;padding:0 {sp['6']}px;flex-shrink:0}}
  .crumb{{font-size:{f['size']['sm']}px;color:{c['inkMuted']}}}
  .crumb b{{color:{c['ink']};font-weight:{f['weight']['semibold']}}}
  .user{{display:flex;align-items:center;gap:{sp['2']}px}}
  .avatar{{width:30px;height:30px;border-radius:{t['radius']['pill']}px;
           background:{c['primarySoft']};color:{c['primary']};display:flex;
           align-items:center;justify-content:center;font-size:{f['size']['xs']}px;
           font-weight:{f['weight']['bold']}}}
  .content{{padding:{sp['6']}px;flex:1;overflow:hidden}}
  .page-head{{display:flex;align-items:flex-start;justify-content:space-between;
              margin-bottom:{sp['5']}px}}
  .page-title{{font-size:{f['size']['xl']}px;font-weight:{f['weight']['bold']};
               letter-spacing:-.4px}}
  .page-desc{{font-size:{f['size']['sm']}px;color:{c['inkMuted']};margin-top:4px}}
  .btn{{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;
        border-radius:{t['radius']['sm']}px;font-size:{f['size']['sm']}px;
        font-weight:{f['weight']['semibold']};border:none;cursor:default}}
  .btn-primary{{background:{c['primary']};color:#fff}}
  .btn-ghost{{background:{c['surface']};color:{c['inkMuted']};
              border:1px solid {c['line']}}}
  .card{{background:{c['surface']};border:1px solid {c['line']};
         border-radius:{t['radius']['lg']}px;box-shadow:{t['shadow']['card']}}}
  table{{width:100%;border-collapse:collapse;font-size:{f['size']['sm']}px}}
  th{{text-align:left;padding:11px {sp['4']}px;font-size:10px;text-transform:uppercase;
      letter-spacing:.7px;color:{c['inkFaint']};border-bottom:1px solid {c['line']};
      font-weight:{f['weight']['semibold']};background:{c['canvas']}}}
  td{{padding:13px {sp['4']}px;border-bottom:1px solid {c['line']};color:{c['inkMuted']}}}
  td:first-child{{color:{c['ink']};font-weight:{f['weight']['medium']}}}
  tr:last-child td{{border-bottom:none}}
  .pill{{display:inline-block;padding:3px 10px;border-radius:{t['radius']['pill']}px;
         font-size:10px;font-weight:{f['weight']['semibold']}}}
  .field{{margin-bottom:{sp['4']}px}}
  .label{{display:block;font-size:{f['size']['xs']}px;font-weight:{f['weight']['semibold']};
          color:{c['ink']};margin-bottom:6px}}
  .input{{width:100%;padding:10px 12px;border:1px solid {c['line']};
          border-radius:{t['radius']['sm']}px;font-size:{f['size']['sm']}px;
          color:{c['inkFaint']};background:{c['surface']}}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:{sp['4']}px;
             margin-bottom:{sp['5']}px}}
  .kpi{{padding:{sp['4']}px {sp['5']}px}}
  .kpi-label{{font-size:10px;text-transform:uppercase;letter-spacing:.7px;
              color:{c['inkFaint']};font-weight:{f['weight']['semibold']}}}
  .kpi-value{{font-size:{f['size']['xl']}px;font-weight:{f['weight']['bold']};
              margin-top:8px;letter-spacing:-.5px}}
  .kpi-delta{{font-size:{f['size']['xs']}px;margin-top:4px}}
  .note{{font-size:11px;color:{c['inkFaint']};margin-top:{sp['3']}px}}
</style></head>
<body><div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">{initials}</div>
      <div><div class="brand-name">{company}</div>
      <div class="brand-sub">{proj_short}</div></div>
    </div>
    {nav_html}
  </aside>
  <div class="main">
    <div class="topbar">
      <div class="crumb">Home &nbsp;/&nbsp; <b>{screen['title']}</b></div>
      <div class="user"><span class="crumb">Kepala Bengkel</span>
        <div class="avatar">KB</div></div>
    </div>
    <div class="content">{body_html}</div>
  </div>
</div></body></html>"""

    # ------------------------------------------------------------- archetypes

    def _head(self, screen, action=None):
        btn = f'<button class="btn btn-primary">{action}</button>' if action else ""
        return (f'<div class="page-head"><div>'
                f'<div class="page-title">{screen["title"]}</div>'
                f'<div class="page-desc">{screen["description"]}</div>'
                f'</div>{btn}</div>')

    def _list_body(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        cols = screen.get("columns") or ["Name", "Status", "Updated"]
        head = "".join(f"<th>{x}</th>" for x in cols)

        pills = [
            (c["accentSoft"], c["accent"], "Active"),
            (c["warningSoft"], c["warning"], "Pending"),
            (c["dangerSoft"], c["danger"], "Overdue"),
        ]
        rows = ""
        for i in range(7):
            cells = ""
            for j, col in enumerate(cols):
                if j == 0:
                    cells += f"<td>Sample {i+1:02d}</td>"
                elif j == len(cols) - 1:
                    bg, fg, label = pills[i % 3]
                    cells += (f'<td><span class="pill" style="background:{bg};'
                              f'color:{fg}">{label}</span></td>')
                else:
                    cells += f"<td>—</td>"
            rows += f"<tr>{cells}</tr>"

        return (self._head(screen, "+ Add New") +
                f'<div class="card"><table><thead><tr>{head}</tr></thead>'
                f'<tbody>{rows}</tbody></table></div>'
                f'<div class="note">{len(cols)} columns · derived from plan scope</div>')

    def _form_body(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        fields = screen.get("fields") or ["Name", "Description", "Status"]
        html = ""
        for fld in fields:
            html += (f'<div class="field"><label class="label">{fld}</label>'
                     f'<div class="input">Enter {fld.lower()}…</div></div>')
        return (self._head(screen) +
                f'<div style="display:grid;grid-template-columns:1.6fr .9fr;'
                f'gap:{sp["5"]}px;align-items:start">'
                f'<div class="card" style="padding:{sp["6"]}px">{html}</div>'
                f'<div class="card" style="padding:{sp["5"]}px">'
                f'<div style="font-size:{f["size"]["sm"]}px;font-weight:600;'
                f'margin-bottom:10px">Guidance</div>'
                f'<div style="font-size:{f["size"]["sm"]}px;color:{c["inkMuted"]};'
                f'line-height:1.6">Required fields must be filled before saving. '
                f'Changes are logged to the audit trail.</div>'
                f'<div style="margin-top:{sp["4"]}px;display:flex;gap:8px">'
                f'<button class="btn btn-primary">Save</button>'
                f'<button class="btn btn-ghost">Cancel</button></div>'
                f'</div></div>')

    def _dashboard_body(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        kpis = [("Revenue Today", "Rp 4.250.000", "+12.4%", c["accent"]),
                ("Active Services", "18", "+3", c["accent"]),
                ("Low Stock Items", "5", "needs reorder", c["warning"]),
                ("Completed Today", "11", "+2", c["accent"])]
        kpi_html = ""
        for label, val, delta, dcolor in kpis:
            kpi_html += (f'<div class="card kpi">'
                         f'<div class="kpi-label">{label}</div>'
                         f'<div class="kpi-value">{val}</div>'
                         f'<div class="kpi-delta" style="color:{dcolor}">{delta}</div>'
                         f'</div>')

        cols = ["Order #", "Customer", "Vehicle", "Status", "Total"]
        head = "".join(f"<th>{x}</th>" for x in cols)
        rows = ""
        for i in range(5):
            rows += (f"<tr><td>SO-{1001+i}</td><td>Sample Customer {i+1}</td>"
                     f"<td>B 1234 XY</td>"
                     f'<td><span class="pill" style="background:{c["primarySoft"]};'
                     f'color:{c["primary"]}">In Progress</span></td>'
                     f"<td>Rp {(750000 + i*215000):,}</td></tr>")

        return (self._head(screen, "New Service Order") +
                f'<div class="kpi-grid">{kpi_html}</div>'
                f'<div class="card"><div style="padding:{sp["4"]}px {sp["4"]}px 0;'
                f'font-size:{f["size"]["sm"]}px;font-weight:600">Recent Service Orders</div>'
                f'<table style="margin-top:8px"><thead><tr>{head}</tr></thead>'
                f'<tbody>{rows}</tbody></table></div>')

    def _detail_body(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        steps = [("Received", True), ("In Progress", True), ("Waiting Parts", False),
                 ("Completed", False), ("Invoiced", False)]
        timeline = ""
        for label, done in steps:
            bg = c["primary"] if done else c["line"]
            fg = c["ink"] if done else c["inkFaint"]
            timeline += (f'<div style="display:flex;align-items:center;gap:10px;'
                         f'margin-bottom:14px">'
                         f'<div style="width:10px;height:10px;border-radius:50%;'
                         f'background:{bg}"></div>'
                         f'<div style="font-size:{f["size"]["sm"]}px;color:{fg};'
                         f'font-weight:{f["weight"]["medium"] if done else f["weight"]["regular"]}">'
                         f'{label}</div></div>')
        return (self._head(screen, "Print") +
                f'<div style="display:grid;grid-template-columns:1.7fr 1fr;'
                f'gap:{sp["5"]}px;align-items:start">'
                f'<div class="card" style="padding:{sp["6"]}px">'
                f'<div style="font-size:{f["size"]["md"]}px;font-weight:600;'
                f'margin-bottom:16px">Detail</div>'
                f'<div style="font-size:{f["size"]["sm"]}px;color:{c["inkMuted"]};'
                f'line-height:1.8">Customer · Vehicle · Items · Totals appear here, '
                f'populated from the service order record.</div></div>'
                f'<div class="card" style="padding:{sp["5"]}px">'
                f'<div style="font-size:{f["size"]["sm"]}px;font-weight:600;'
                f'margin-bottom:16px">Status Timeline</div>{timeline}</div></div>')

    def _auth_body(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        return (f'<div style="display:flex;align-items:center;justify-content:center;'
                f'min-height:{self.height_for(screen) - 40}px">'
                f'<div class="card" style="width:380px;padding:{sp["8"]}px">'
                f'<div style="font-size:{f["size"]["lg"]}px;font-weight:700;'
                f'margin-bottom:6px">Sign in</div>'
                f'<div style="font-size:{f["size"]["sm"]}px;color:{c["inkMuted"]};'
                f'margin-bottom:{sp["6"]}px">Use your work account</div>'
                f'<div class="field"><label class="label">Email</label>'
                f'<div class="input">name@company.com</div></div>'
                f'<div class="field"><label class="label">Password</label>'
                f'<div class="input">••••••••</div></div>'
                f'<button class="btn btn-primary" style="width:100%;'
                f'justify-content:center;margin-top:8px">Sign in</button>'
                f'<div style="font-size:11px;color:{c["inkFaint"]};margin-top:14px;'
                f'text-align:center">Role is detected from your account</div>'
                f'</div></div>')

    # ------------------------------------------------------------- render

    def build_html(self, spec, screen):
        arch = screen["archetype"]
        if arch == "list":
            body = self._list_body(spec, screen)
        elif arch == "form":
            body = self._form_body(spec, screen)
        elif arch == "dashboard":
            body = self._dashboard_body(spec, screen)
        elif arch == "detail":
            body = self._detail_body(spec, screen)
        elif arch == "auth":
            return self._auth_body_page(spec, screen)
        else:
            body = self._list_body(spec, screen)
        return self._shell(spec, screen, body, active_nav=screen["id"])

    def _auth_body_page(self, spec, screen):
        t = spec["tokens"]
        c, f, sp = t["color"], t["font"], t["space"]
        inner = self._auth_body(spec, screen)
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{screen['title']}</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:{f['family']};background:{c['canvas']};color:{c['ink']};
      -webkit-font-smoothing:antialiased}}
.field{{margin-bottom:{sp['4']}px}}
.label{{display:block;font-size:{f['size']['xs']}px;font-weight:600;
        margin-bottom:6px}}
.input{{width:100%;padding:10px 12px;border:1px solid {c['line']};
        border-radius:{t['radius']['sm']}px;font-size:{f['size']['sm']}px;
        color:{c['inkFaint']};background:{c['surface']}}}
.btn{{padding:10px 16px;border-radius:{t['radius']['sm']}px;
      font-size:{f['size']['sm']}px;font-weight:600;border:none;
      display:inline-flex}}
.btn-primary{{background:{c['primary']};color:#fff}}
.card{{background:{c['surface']};border:1px solid {c['line']};
       border-radius:{t['radius']['lg']}px;box-shadow:{t['shadow']['card']}}}
</style></head><body>{inner}</body></html>"""

    def render_all(self, spec, out_dir, scale=1):
        """Render every screen in the spec to PNG. Returns list of paths."""
        if not self.chrome:
            raise RuntimeError(
                "No headless browser found. Install Google Chrome or Chromium.")

        out = Path(out_dir).resolve()
        html_dir = out / "html"
        png_dir = out / "screens"
        html_dir.mkdir(parents=True, exist_ok=True)
        png_dir.mkdir(parents=True, exist_ok=True)

        # Persist the spec next to the output for traceability
        (out / "ui-spec.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        written = []
        for screen in spec["screens"]:
            html = self.build_html(spec, screen)
            hp = (html_dir / f"{screen['id']}.html").resolve()
            hp.write_text(html, encoding="utf-8")

            pp = (png_dir / f"{screen['id']}.png").resolve()
            h = self.height_for(screen)

            # Chrome's own sandbox cannot always initialise — inside a
            # container, a nested sandbox, or a hardened shell it fails with
            # "sandbox initialization failed: Operation not permitted" and
            # writes nothing. Retry once with the sandbox disabled rather than
            # aborting a demo half-way through; only report failure if both
            # attempts produce no file.
            base = [
                self.chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                f"--window-size={self.width},{h}",
                f"--screenshot={pp}", f"file://{hp}",
            ]
            attempts = [
                base,
                base[:2] + ["--no-sandbox", "--disable-dev-shm-usage"] + base[2:],
            ]

            last_err = ""
            for args in attempts:
                proc = subprocess.run(args, capture_output=True, text=True)
                if pp.exists():
                    break
                last_err = (proc.stderr or proc.stdout or "").strip()
            else:
                raise RuntimeError(
                    f"Chrome failed to write {pp.name} after 2 attempts "
                    f"(sandboxed, then --no-sandbox).\n"
                    f"Chrome said: {last_err[:300]}\n"
                    f"Fix: run this outside a container/IDE sandbox, or open "
                    f"{hp} in a browser and take the screenshot manually.")
            written.append(str(pp))

        return written


# =============================================================================
# Self-Test
# =============================================================================

def run_selftest():
    print("=" * 60)
    print("TOF Project Assistant - Mockup Renderer Self-Test")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent))
    from ui_spec import UISpecGenerator

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

    r = MockupRenderer()
    check("Headless browser found", r.chrome is not None, str(r.chrome))

    plan = {
        "projectId": "PRJ-T", "projectName": "Test App",
        "scope": {"inScope": ["Customer management", "Dashboard",
                              "Service transactions", "Invoice printing"]},
        "informationSources": {"fromBrief": ["Kasir"]},
    }
    spec = UISpecGenerator().build(plan, client={"company": "Test Co"})

    # --- HTML generation per archetype ---
    print("\n--- Group 1: HTML per archetype ---")
    arch_seen = set()
    for s in spec["screens"]:
        html = r.build_html(spec, s)
        arch_seen.add(s["archetype"])
        check(f"{s['id']} ({s['archetype']}) produces HTML",
              html.startswith("<!DOCTYPE html>") and len(html) > 800,
              f"{len(html)} chars")

    check("Covers >=4 archetypes", len(arch_seen) >= 4, str(sorted(arch_seen)))

    # --- tokens actually applied ---
    print("\n--- Group 2: Tokens applied ---")
    primary = spec["tokens"]["color"]["primary"]
    list_screen = next((s for s in spec["screens"] if s["archetype"] == "list"), None)
    if list_screen:
        html = r.build_html(spec, list_screen)
        check("Primary colour present in HTML", primary in html)
        check("Sidebar width from tokens",
              str(spec["tokens"]["layout"]["sidebar"]) in html)

    # --- real render ---
    print("\n--- Group 3: Actual PNG render ---")
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="tof-mockup-")
    try:
        paths = r.render_all(spec, tmp)
        check("Rendered one PNG per screen",
              len(paths) == len(spec["screens"]),
              f"{len(paths)} vs {len(spec['screens'])}")

        p = Path(paths[0])
        check("PNG exists and is non-trivial",
              p.exists() and p.stat().st_size > 8000,
              f"{p.stat().st_size if p.exists() else 0} bytes")

        check("Spec persisted to ui-spec.json",
              (Path(tmp) / "ui-spec.json").exists())

        check("HTML sources kept",
              len(list((Path(tmp) / "html").glob("*.html"))) == len(spec["screens"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # --- missing browser handled ---
    print("\n--- Group 4: Error handling ---")
    bad = MockupRenderer()
    bad.chrome = None
    try:
        bad.render_all(spec, "/tmp/should-not-write")
        check("Raises when no browser", False, "no exception")
    except RuntimeError as e:
        check("Raises clear error when no browser", "browser" in str(e).lower())

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)
    if failed == 0:
        print("\nAll mockup renderer self-tests passed!")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_selftest() else 1)
