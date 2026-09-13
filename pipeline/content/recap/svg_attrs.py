"""Presentation attributes for the recap's inline SVG, so print renderers get the right paint.

Browsers colour these SVGs from the Visual CSS (classes + CSS variables), and CSS beats presentation
attributes, so the page keeps its light/dark theming. WeasyPrint does not apply document CSS to inline
SVG — without attributes every path fills black. The literal values below are the Visual CSS light
palette (:root in visual_assets/recap_visual.css); nothing new is introduced.
"""
from __future__ import annotations

import re

INK, MUTED, RULE, ACCENT, UP, DN, BAR = "#1A1917", "#8A857A", "#D9D6CD", "#D1600F", "#3F6B4A", "#A8402F", "#BDB8AC"
MONO = "IBM Plex Mono, Menlo, Hiragino Sans GB, monospace"

_SVG = re.compile(r'<svg class="([^"]+)"(.*?)</svg>', re.S)
_EL = re.compile(r"<(path|rect|line|text|ellipse|circle)\b([^>]*?)(/?)>")


def _paint(root: str, root_cls: set, tag: str, c: set) -> dict:
    if root == "drop":
        return {"fill": "none", "stroke": MUTED if "fmark" in root_cls else ACCENT,
                "stroke-linecap": "round", "stroke-linejoin": "round"} if tag == "path" else {}
    if root == "chart":
        if tag == "rect":
            return {"fill": INK if "now" in c else BAR}
        if tag == "line":
            return {"stroke": RULE, "stroke-width": "1", **({"stroke-dasharray": "3 3"} if "mid" in c else {})}
        if tag == "text":
            now = "nowlab" in c
            return {"fill": INK if now else MUTED, "font-size": "13" if now else "10", "font-family": MONO,
                    **({"font-weight": "600"} if now else {})}
        return {}
    if root == "tell":
        if tag == "path":
            stroke = next((v for k, v in (("trend", INK), ("upb", UP), ("dnb", DN), ("evt", MUTED), ("ma2", MUTED), ("ma", ACCENT)) if k in c), INK)
            evt = "evt" in c
            return {"fill": "none", "stroke": stroke, "stroke-width": "1.5" if evt else "3", "stroke-linecap": "round",
                    "stroke-linejoin": "round", **({"stroke-dasharray": "6 6"} if evt else {})}
        if tag == "line":
            if "lvl" in c:
                return {"stroke": ACCENT, "stroke-width": "2"}
            if "guide" in c:
                return {"stroke": RULE, "stroke-width": "1.2", "stroke-dasharray": "4 4"}
            if "lead" in c:
                return {"stroke": MUTED, "stroke-width": "1"}
            return {"stroke": MUTED, "stroke-width": "1.5", "stroke-dasharray": "6 6"}
        if tag == "ellipse":
            return {"fill": "none", "stroke": MUTED, "stroke-width": "1.4"}
        if tag == "circle":
            return {"fill": INK}
        if tag == "rect":
            if "zone-up" in c:
                return {"fill": UP, "fill-opacity": "0.07"}
            if "zone-dn" in c:
                return {"fill": DN, "fill-opacity": "0.07"}
            return {}
        if tag == "text":
            fill = next((v for k, v in (("lab-up", UP), ("lab-dn", DN), ("lab-acc", ACCENT)) if k in c), MUTED)
            lab = any(k in c for k in ("lab-up", "lab-dn", "lab-acc"))
            return {"fill": fill, "font-family": MONO, "font-size": "12" if "small" in c else "13",
                    **({"font-weight": "600"} if lab else {})}
    return {}


def presentational(markup: str) -> str:
    """Add presentation attributes to every element of .drop / .chart / .tell SVGs in `markup`."""
    def fix_svg(m):
        root_cls = set(m.group(1).split())
        root = next((r for r in ("drop", "chart", "tell") if r in root_cls), None)
        if root is None:
            return m.group(0)

        def fix_el(em):
            tag, attrs, close = em.group(1), em.group(2), em.group(3)
            cm = re.search(r'class="([^"]*)"', attrs)
            paint = _paint(root, root_cls, tag, set(cm.group(1).split()) if cm else set())
            add = "".join(f' {k}="{v}"' for k, v in paint.items() if f"{k}=" not in attrs)
            return f"<{tag}{attrs}{add}{close}>"
        return f'<svg class="{m.group(1)}"' + _EL.sub(fix_el, m.group(2)) + "</svg>"
    return _SVG.sub(fix_svg, markup)
