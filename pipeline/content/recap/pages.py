"""Page-fill check on pdftotext output: no page may be header + footer + a line or two.

pdftotext separates pages with form feeds. Header/footer lines are the running
margin boxes ("FLUXUS CAPITAL … DAILY MARKET RECAP", "FLUXUS CAPITAL · CONFIDENTIAL · n / m").
Everything else that is non-blank counts as body.
"""
from __future__ import annotations

import html
import re
import subprocess

MIN_BODY_LINES = 3
_CHROME = re.compile(r"FLUXUS\s+CAPITAL|DAILY\s+MARKET\s+RECAP|WEEKLY\s+MARKET\s+RECAP|CONFIDENTIAL")


def body_lines_per_page(text: str) -> list[int]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return [sum(1 for ln in p.splitlines() if ln.strip() and not _CHROME.search(ln)) for p in pages]


def check_pages(text: str, min_body: int = MIN_BODY_LINES) -> dict:
    counts = body_lines_per_page(text)
    thin = [i + 1 for i, n in enumerate(counts) if n < min_body]
    return {"pages": len(counts), "body_lines": counts, "thin_pages": thin, "ok": bool(counts) and not thin}


# ------------------------------------------------------------------ text inside the type area
PT_PER_MM = 72 / 25.4
_BBOX = re.compile(r'<page width="([\d.]+)" height="[\d.]+">|<word xMin="([\d.]+)" yMin="[\d.]+" xMax="([\d.]+)" yMax="[\d.]+">(.*?)</word>')


def margin_overflow(bbox_html: str, left_mm: float, right_mm: float, tol_pt: float = 2.0) -> list[dict]:
    """Words whose box leaves the horizontal type area, from `pdftotext -bbox` output.
    A table that runs past the right margin prints its tail into the margin (or off the sheet);
    either way the word box crosses the limit, so a truncated column is caught even when the
    visible text looks plausible ("多空线 / bu")."""
    bad, page, lo, hi = [], 0, 0.0, 0.0
    for m in _BBOX.finditer(bbox_html):
        if m.group(1):
            page += 1
            width = float(m.group(1))
            lo, hi = left_mm * PT_PER_MM - tol_pt, width - right_mm * PT_PER_MM + tol_pt
            continue
        x0, x1 = float(m.group(2)), float(m.group(3))
        if x0 < lo or x1 > hi:
            bad.append({"page": page, "word": html.unescape(m.group(4)), "xMin": x0, "xMax": x1,
                        "limits": [round(lo, 1), round(hi, 1)]})
    return bad


def check_margins(pdf_path, left_mm: float = 14.0, right_mm: float = 14.0, tol_pt: float = 2.0) -> dict:
    out = subprocess.run(["pdftotext", "-bbox", str(pdf_path), "-"], capture_output=True, text=True, check=True).stdout
    bad = margin_overflow(out, left_mm, right_mm, tol_pt)
    return {"ok": not bad, "count": len(bad), "overflow": bad[:12]}
