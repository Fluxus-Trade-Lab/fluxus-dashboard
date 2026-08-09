#!/usr/bin/env python3
"""Render one card out of an exploration page to a print-ready PNG.

`make_poster.py` owns the wall-label frame (borrowed image + measurement line).
The level-4 pieces are a different layout entirely — built and reviewed inside
`Fluxus_Brand/visual/explorations/**/*.html` — so this shoots a single `.piece`
element from one of those pages at export scale.

    python3 scripts/render_piece.py loud2.html nullres --out visuals/out/null_result.png

Uses the same headless Chrome as make_poster.py; no extra dependency. Fonts are
loaded by the page itself from its own `fonts/` directory, and the script waits
on `document.fonts.ready` so nothing ships in a substitute face.
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORE = ROOT / "Fluxus_Brand" / "visual" / "explorations" / "2026-08-08"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 432×540 in the exploration pages is exactly 1080×1350 at 2.5×
DEFAULT_SCALE = 2.5


def render(page: str, element_id: str, out: Path, scale: float) -> None:
    src = EXPLORE / page
    if not src.exists():
        raise SystemExit(f"no such page: {src}")
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found: {CHROME}")

    # Serve from the page's own directory so its relative font URLs resolve.
    # A file:// load would hit CORS on the woff2 and silently substitute.
    shim = f"""
    <script>
    window.addEventListener('load', async () => {{
      await document.fonts.ready;
      const el = document.getElementById({json.dumps(element_id)});
      if (!el) {{ document.title = 'MISSING'; return; }}
      // strip everything except the piece, then size the viewport to it
      const w = el.offsetWidth, h = el.offsetHeight;
      document.body.innerHTML = '';
      document.body.style.cssText =
        'margin:0;padding:0;background:transparent;width:' + w + 'px;height:' + h + 'px';
      document.documentElement.style.cssText = document.body.style.cssText;
      // keep `relative` — the meta bar is absolutely positioned against it,
      // and switching to static pushed the mark off the right edge
      el.style.position = 'relative';
      el.style.margin = '0';
      document.body.appendChild(el);
      document.title = 'READY ' + w + 'x' + h;
    }});
    </script>"""
    html = src.read_text()
    assert "</body>" in html, "unexpected page shape"
    tmp = src.parent / f".render_{element_id}.html"
    tmp.write_text(html.replace("</body>", shim + "\n</body>"))

    try:
        # measure first so the shot is exactly the element, not a padded page
        probe = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--dump-dom",
             "--virtual-time-budget=8000", tmp.as_uri()],
            capture_output=True, text=True, timeout=120)
        dom = probe.stdout
        if "MISSING" in dom[:4000]:
            raise SystemExit(f"element #{element_id} not found in {page}")

        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--force-device-scale-factor={scale}",
             "--window-size=432,540",
             "--default-background-color=00000000",
             f"--screenshot={out}", "--virtual-time-budget=8000",
             tmp.as_uri()],
            capture_output=True, timeout=180, check=True)
    finally:
        tmp.unlink(missing_ok=True)

    if not out.exists():
        raise SystemExit("Chrome produced no file")
    print(f"{out}  ({out.stat().st_size/1024:.0f} KB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("page", help="file name inside the explorations folder, e.g. loud2.html")
    ap.add_argument("element", help="id of the .piece element, e.g. nullres")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                    help="device scale factor; 2.5 gives 1080×1350 from a 432×540 piece")
    a = ap.parse_args()
    render(a.page, a.element, a.out, a.scale)


if __name__ == "__main__":
    main()
