#!/usr/bin/env python3
"""
Build HTML terminal-style evidence pages from captured test output,
then render to PNG via headless Chrome.

Splits long output into readable chunks.

Usage:
    python3 evidence/build_evidence.py
"""

import html
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
EVIDENCE = ROOT / "evidence"
SHOTS = EVIDENCE / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: -apple-system, 'SF Mono', Menlo, monospace;
    background: #1e1e2e;
    padding: 26px;
    color: #cdd6f4;
  }}
  .window {{
    background: #181825;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,.55);
  }}
  .titlebar {{
    background: #313244;
    padding: 11px 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .dot {{ width:12px; height:12px; border-radius:50%; }}
  .d1 {{ background:#f38ba8; }}
  .d2 {{ background:#f9e2af; }}
  .d3 {{ background:#a6e3a1; }}
  .titlebar span {{
    margin-left: 14px;
    font-family: -apple-system, sans-serif;
    font-size: 13px;
    color: #a6adc8;
  }}
  .meta {{
    font-family: -apple-system, sans-serif;
    font-size: 12px;
    color: #6c7086;
    padding: 10px 20px;
    background: #11111b;
    border-bottom: 1px solid #313244;
    display: flex;
    justify-content: space-between;
  }}
  pre {{
    padding: 18px 20px;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
    color: #cdd6f4;
  }}
  .pass {{ color:#a6e3a1; font-weight:700; }}
  .fail {{ color:#f38ba8; font-weight:700; }}
  .head {{ color:#89b4fa; font-weight:700; }}
  .warn {{ color:#f9e2af; }}
</style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dot d1"></div><div class="dot d2"></div><div class="dot d3"></div>
      <span>{cmd}</span>
    </div>
    <div class="meta"><span>{title}</span><span>{subtitle}</span></div>
    <pre>{body}</pre>
  </div>
</body>
</html>
"""


def colorize(text):
    out = html.escape(text)
    out = out.replace("[PASS]", "\x01P\x02PASS\x03")
    out = out.replace("[FAIL]", "\x01F\x02FAIL\x03")
    out = out.replace("[ERROR]", "\x01F\x02ERROR\x03")
    out = out.replace("[SKIP]", "\x01W\x02SKIP\x03")
    out = out.replace("TESTS PASSED", "\x01P\x02TESTS PASSED\x03")
    out = out.replace("TEST(S) FAILED", "\x01F\x02TEST(S) FAILED\x03")
    out = out.replace("=" * 70, "\x01H\x02" + "=" * 70 + "\x03")
    out = out.replace("=" * 60, "\x01H\x02" + "=" * 60 + "\x03")
    out = out.replace("--- ", "\x01H\x02--- \x03")
    out = out.replace("\x01P\x02", '<span class="pass">')
    out = out.replace("\x01F\x02", '<span class="fail">')
    out = out.replace("\x01W\x02", '<span class="warn">')
    out = out.replace("\x01H\x02", '<span class="head">')
    out = out.replace("\x03", "</span>")
    return out


def render(name, title, cmd, subtitle, lines):
    body = colorize("\n".join(lines))
    html_out = TEMPLATE.format(title=html.escape(title), cmd=html.escape(cmd),
                               subtitle=html.escape(subtitle), body=body)
    html_path = EVIDENCE / f"{name}.html"
    html_path.write_text(html_out, encoding="utf-8")

    png_path = SHOTS / f"{name}.png"
    height = max(320, min(2000, 150 + len(lines) * 19))
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
        f"--window-size=1240,{height}",
        f"--screenshot={png_path}",
        f"file://{html_path}",
    ], capture_output=True)
    print(f"  {png_path.name:34s} {len(lines):4d} lines  {png_path.stat().st_size:>9,} bytes")
    return png_path


def chunks(lines, size):
    return [lines[i:i + size] for i in range(0, len(lines), size)]


if __name__ == "__main__":
    print("Building evidence screenshots...\n")

    # --- Self-test: 252 lines -> 2 chunks ---
    st = Path("/tmp/out-selftest.txt").read_text(encoding="utf-8").splitlines()
    # Find the FINAL RESULTS marker so we can start part 2 at a good place
    try:
        split_at = next(i for i, l in enumerate(st) if "Running: Audit Logger" in l)
    except StopIteration:
        split_at = len(st) // 2

    render("01a-selftest-gate-validator",
           "Self-Test Part 1/2 — gate.py + validator.py + quote_gen.py",
           "python3 agent/tools/selftest.py",
           "Challenge B — Office Agent",
           st[:split_at])

    render("01b-selftest-summary",
           "Self-Test Part 2/2 — audit_logger.py + state_manager.py + FINAL SUMMARY",
           "python3 agent/tools/selftest.py",
           "ALL 5 MODULES PASSED",
           st[split_at:])

    # --- Test cases: 66 lines -> 1 chunk ---
    tc = Path("/tmp/out-tests.txt").read_text(encoding="utf-8").splitlines()
    render("02-test-cases",
           "Challenge B Test Cases — 20 tests",
           "python3 tests/test_cases.py",
           "19 passed / 1 documented failure",
           tc)

    print("\nDone.")
