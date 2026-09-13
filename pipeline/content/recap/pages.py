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


def _spaced(term: str) -> str:
    """Regex for a label as pdftotext may emit it: letter-spaced headings can gain single spaces."""
    return r"\s?".join(re.escape(ch) if ch != " " else r"\s{1,3}" for ch in term)


# X posts carry pages 1–4 of the EN PDF: none of those pages may show the book.
X_STRONG = {"EN": [("Portfolio Update", re.I), ("OPEN R", 0), ("REALIZED R", 0), ("Open position", re.I)],
            "ZH": [("组合更新", 0), ("浮动 R", 0), ("已实现 R", 0)]}
X_CELLS = {"EN": ("RETURN", "CASH"), "ZH": ("收益", "现金", "持仓")}  # only as a stand-alone cell, never inside prose


def x_page_hits(page_text: str, lang: str, book_tickers=()) -> list[str]:
    hits = []
    for term, flags in X_STRONG[lang]:
        tail = r"(?![A-Za-z])" if term.endswith(" R") else ""
        if re.search(_spaced(term) + tail, page_text, flags):
            hits.append(term)
    for line in page_text.splitlines():
        cells = [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]
        for term in X_CELLS[lang]:
            if term in cells:
                hits.append(f"cell:{term}")
        for tk in book_tickers:
            if re.match(rf"^\s*{re.escape(tk)}\s{{2,}}(long|short|多|空)(\s|$)", line):
                hits.append(f"book row:{tk}")
    return hits


def check_x_pages(text: str, lang: str, book_tickers=(), first_n: int = 4, min_pages: int = 4) -> dict:
    """X1: pages 1..first_n carry no portfolio content. X2: the PDF has at least min_pages pages."""
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    x1 = {i + 1: h for i, p in enumerate(pages[:first_n]) if (h := x_page_hits(p, lang, book_tickers))}
    return {"pages": len(pages), "x1_hits": x1, "x1_ok": not x1, "x2_ok": len(pages) >= min_pages,
            "ok": not x1 and len(pages) >= min_pages}


def page_sections(text: str, headings: list[str]) -> list[list[str]]:
    """For each page, the section headings that start on it (letter-spacing and case tolerant)."""
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    squash = lambda s: re.sub(r"\s+", "", s).upper()
    out = []
    for p in pages:
        sp = squash(p)
        out.append([h for h in headings if h and squash(h) in sp])
    return out


def check_margins(pdf_path, left_mm: float = 14.0, right_mm: float = 14.0, tol_pt: float = 2.0) -> dict:
    out = subprocess.run(["pdftotext", "-bbox", str(pdf_path), "-"], capture_output=True, text=True, check=True).stdout
    bad = margin_overflow(out, left_mm, right_mm, tol_pt)
    return {"ok": not bad, "count": len(bad), "overflow": bad[:12]}
