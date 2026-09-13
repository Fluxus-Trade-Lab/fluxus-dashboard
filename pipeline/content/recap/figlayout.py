"""Label layout for the education schematics: estimated text boxes, callout avoidance, and gate F1.

Geometry mirrors recap_page.js figure(): viewBox 1000×380, x 0–100 → 40–960, y in ylim → 350–30.
Type is IBM Plex Mono 16 px (15.5 px for `.small`), so a Latin glyph is ~0.6 em wide; CJK falls back to a
full-width face, ~1 em. A text box spans baseline − 0.8 em to baseline + 0.25 em.

resolve(spec)       moves callout labels (never data, never fixed texts) until no two label boxes meet,
                    trying small vertical steps first, then horizontal; leader lines follow in the JS.
check_spec_labels   F1 on a spec (tests, pre-render).
check_svg_labels    F1 on rendered markup — the DOM Chrome actually produced.
"""
from __future__ import annotations

import html
import itertools
import re

X0, X1, YT, YB, W, H = 40.0, 960.0, 30.0, 350.0, 1000.0, 380.0


def font_size(cls: str) -> float:
    """Must match the print sizes in recap_local.css (.tell text 16.28px / .tell .small 15.02px)."""
    return 15.02 if "small" in (cls or "").split() else 16.28


def text_width(label: str, fs: float) -> float:
    return sum(fs if ord(ch) >= 0x2E80 else 0.6 * fs for ch in label)


def box(x: float, y: float, label: str, anchor: str, fs: float, pad: float = 0.0) -> tuple:
    w = text_width(label, fs)
    x0 = x if anchor == "start" else (x - w / 2 if anchor == "middle" else x - w)
    return (x0 - pad, y - 0.8 * fs - pad, x0 + w + pad, y + 0.25 * fs + pad)


def intersects(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _maps(ylim):
    y0, y1 = ylim
    X = lambda x: X0 + x / 100 * (X1 - X0)
    Y = lambda y: YB - (y - y0) / (y1 - y0) * (YB - YT)
    iX = lambda px: (px - X0) / (X1 - X0) * 100
    iY = lambda py: y0 + (YB - py) / (YB - YT) * (y1 - y0)
    return X, Y, iX, iY


def spec_label_boxes(spec: dict) -> list[tuple[str, tuple]]:
    X, Y, _, _ = _maps(spec["ylim"])
    out = []
    for it in spec["items"]:
        if it[0] == "text":
            out.append((it[4], box(X(it[2]), Y(it[3]), it[4], it[5] or "start", font_size(it[1]))))
        elif it[0] == "callout":
            out.append((it[6], box(X(it[4]), Y(it[5]), it[6], "middle", font_size(it[1]))))
    return out


def _overlaps(labels: list[tuple[str, tuple]]) -> list[tuple[str, str]]:
    return [(a[0], b[0]) for a, b in itertools.combinations(labels, 2) if intersects(a[1], b[1])]


def check_spec_labels(spec: dict) -> dict:
    ov = _overlaps(spec_label_boxes(spec))
    return {"ok": not ov, "overlaps": ov}


_TELL = re.compile(r'<svg class="tell".*?</svg>', re.S)
_TEXT = re.compile(r'<text(?: class="([^"]*)")? x="([-\d.]+)" y="([-\d.]+)" text-anchor="(\w+)">(.*?)</text>', re.S)


def check_svg_labels(markup: str) -> dict:
    """F1 over every .tell SVG in rendered markup."""
    overlaps, figures = [], 0
    for svg in _TELL.findall(markup):
        figures += 1
        labels = [(html.unescape(m.group(5)), box(float(m.group(2)), float(m.group(3)), html.unescape(m.group(5)),
                                                  m.group(4), font_size(m.group(1) or ""))) for m in _TEXT.finditer(svg)]
        overlaps += _overlaps(labels)
    return {"ok": figures > 0 and not overlaps, "figures": figures, "overlaps": overlaps}


def resolve(spec: dict, gap: float = 4.0) -> dict:
    X, Y, iX, iY = _maps(spec["ylim"])
    obstacles = []
    for it in spec["items"]:
        if it[0] == "text":
            obstacles.append(box(X(it[2]), Y(it[3]), it[4], it[5] or "start", font_size(it[1]), gap / 2))
        elif it[0] == "callout":
            cx, cy = X(it[2]), Y(it[3])
            obstacles.append((cx - 20, cy - 12, cx + 20, cy + 12))  # every marker ellipse
    steps = [(0, 0)] + [(dx, dy) for dy in (-16, 16, -32, 32, -48, 48, -64, 64) for dx in (0,)] + \
            [(dx, dy) for dy in (0, -16, 16, -32, 32) for dx in (48, -48, 96, -96)]
    for it in spec["items"]:
        if it[0] != "callout":
            continue
        fs = font_size(it[1])
        lx, ly = X(it[4]), Y(it[5])
        chosen = None
        for dx, dy in steps:
            b = box(lx + dx, ly + dy, it[6], "middle", fs, gap / 2)
            if b[0] < 2 or b[2] > W - 2 or b[1] < 2 or b[3] > H - 2:
                continue
            if any(intersects(b, o) for o in obstacles):
                continue
            chosen = (dx, dy, b)
            break
        if chosen is None:
            obstacles.append(box(lx, ly, it[6], "middle", fs, gap / 2))
            continue
        dx, dy, b = chosen
        if dx or dy:
            it[4], it[5] = round(iX(lx + dx), 2), round(iY(ly + dy), 2)
        obstacles.append(b)
    return spec
