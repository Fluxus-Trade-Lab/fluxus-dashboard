"""Page-fill check on pdftotext output: no page may be header + footer + a line or two.

pdftotext separates pages with form feeds. Header/footer lines are the running
margin boxes ("FLUXUS CAPITAL … DAILY MARKET RECAP", "FLUXUS CAPITAL · CONFIDENTIAL · n / m").
Everything else that is non-blank counts as body.
"""
from __future__ import annotations

import re

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
