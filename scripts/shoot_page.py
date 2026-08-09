#!/usr/bin/env python3
"""Screenshot one card out of the running dev server.

The in-app browser pane can be hidden, and a hidden pane lays out at 0×0 — every
width you measure through it is a lie, and no screenshot is worth looking at. So
this drives headless Chrome instead, at a window size I choose.

Chrome's --screenshot captures the top of the viewport and gives no way to scroll
first, so the page is loaded inside a same-origin iframe on a throwaway harness
served by Vite itself. The harness scrolls the iframe until the card whose text
you named is at the top, then sizes itself to the card. What lands in the PNG is
the component, not the page around it.

    python3 scripts/shoot_page.py '#/ticker/AEHR' 'Signal history' \
        --out visuals/out/ticker_signal_history.png

Requires the fluxus-dashboard dev server to already be running on --port.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

HARNESS = """<!doctype html><meta charset=utf-8>
<style>html,body{{margin:0;padding:0;background:#fff;overflow:hidden}}
iframe{{border:0;display:block;width:{w}px;height:{h}px}}</style>
<script>
// same origin, so the app reads this on its first render — both themes are
// measured designs and both have to be shootable
localStorage.setItem('theme', {theme});
</script>
<iframe id=f src="{route}"></iframe>
<script>
const NEEDLE={needle};
const f=document.getElementById('f');
f.addEventListener('load',()=>{{
  // the SPA mounts after load and fetches its data, so poll rather than guess
  let tries=0;
  const tick=setInterval(()=>{{
    const d=f.contentDocument;
    const el=d && [...d.querySelectorAll('h1,h2,h3')].find(e=>e.textContent.includes(NEEDLE));
    if(el){{
      const card=el.parentElement.parentElement;
      const r=card.getBoundingClientRect();
      f.contentWindow.scrollBy(0,r.top-8);
      // shrink the frame to the card so the shot has no page around it
      const hh=Math.min(Math.ceil(r.height)+16,{maxh});
      f.style.height=hh+'px';
      document.title='READY '+Math.round(r.width)+'x'+hh;
      clearInterval(tick);
    }} else if(++tries>120) {{ document.title='MISSING'; clearInterval(tick); }}
  }},100);
}});
</script>"""


def shoot(route: str, needle: str, out: Path, port: int, w: int, h: int,
          theme: str = "dark") -> None:
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found: {CHROME}")
    base = f"http://localhost:{port}/"
    try:
        urllib.request.urlopen(base, timeout=5)
    except (urllib.error.URLError, OSError) as e:
        raise SystemExit(f"dev server not answering on {base} — start it first ({e})")

    harness = PUBLIC / "_shot.html"
    harness.write_text(HARNESS.format(
        route=route if route.startswith("http") else base + route.lstrip("/"),
        needle=json.dumps(needle), theme=json.dumps(theme), w=w, h=h, maxh=h))
    url = f"{base}_shot.html"
    try:
        time.sleep(0.4)  # let Vite notice the new file before Chrome asks for it
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={w},{h}", "--force-device-scale-factor=2",
             f"--screenshot={out}", "--virtual-time-budget=20000", url],
            capture_output=True, timeout=180, check=True)
    finally:
        harness.unlink(missing_ok=True)

    if not out.exists():
        raise SystemExit("Chrome produced no file")
    rel = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"{rel}  ({out.stat().st_size/1024:.0f} KB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("route", help="hash route, e.g. '#/ticker/AEHR'")
    ap.add_argument("needle", help="heading text that identifies the card")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--port", type=int, default=5173)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=1400)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    a = ap.parse_args()
    shoot(a.route, a.needle, a.out, a.port, a.width, a.height, a.theme)


if __name__ == "__main__":
    main()
