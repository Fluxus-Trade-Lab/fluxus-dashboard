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


# ------------------------------------------------------------------ L1 · page layout
# Andy 09-13 (final): 「只要除了教育和portfolio update之外的内容能够全部进入这前4页就算通过」,「教育段可以跨页」.
# So: everything except the lesson and the book lands by page 4; the book owns the last page alone; the lesson
# sits between them and may run onto page 5 — a daily is 5 pages (lesson fitted) or 6 (lesson spilled).
# The one hard line on the spill: a break may not fall inside a sentence, because X image 4 is EN page 4.
CONTENT_PAGES = 4
_SENT_END = re.compile(r"[.!?:;。！？：；”\"')）\]】…·%]$|[0-9]$|^$")
_CONT_START = re.compile(r"^[a-z(\[]|^[，。、；：）】]")


def _pages_of(text: str) -> list[str]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def _body_lines(page_text: str) -> list[str]:
    return [ln.strip() for ln in page_text.splitlines() if ln.strip() and not _CHROME.search(ln)]


def sentence_split_breaks(text: str, continued_pages: list[int]) -> list[int]:
    """Page numbers whose top continues the previous page inside a sentence (no new heading started there)."""
    pages = _pages_of(text)
    bad = []
    for p in continued_pages:
        if not 2 <= p <= len(pages):
            continue
        prev, cur = _body_lines(pages[p - 2]), _body_lines(pages[p - 1])
        if prev and cur and not _SENT_END.search(prev[-1]) and _CONT_START.search(cur[0]):
            bad.append(p)
    return bad


def check_layout(text: str, sections: list[list[str]], edu_heading: str, book_heading: str, weekly: bool = False) -> dict:
    """L1: non-lesson, non-book content ends by page CONTENT_PAGES; the book owns the last page alone;
    the lesson may span pages 4–5; no page may open mid-sentence."""
    hits, pages = [], len(sections)
    if not sections:
        return {"ok": False, "pages": 0, "hits": ["no pages"], "book_page": None, "edu_pages": []}
    if sections[-1] != [book_heading]:
        hits.append(f"last page is not the book alone: {sections[-1]}")
    if any(book_heading in s for s in sections[:-1]):
        hits.append("book appears before the last page")
    active, present = None, []
    for starts in sections:
        here = list(starts)
        if active and starts[:1] != [book_heading] and (not starts or starts[0] != active):
            here.insert(0, active)  # the section that continues onto this page (the book always starts a page)
        present.append(here)
        if starts:
            active = starts[-1]
    if not weekly:  # the weekly has no page budget; only the daily must clear pages 5+
        for i, here in enumerate(present[:-1], start=1):  # every page but the book's
            if i <= CONTENT_PAGES:
                continue
            stray = [h for h in here if h not in (edu_heading, book_heading)]
            if stray:
                hits.append(f"page {i} still carries {stray}")
        if pages not in (CONTENT_PAGES + 1, CONTENT_PAGES + 2):
            hits.append(f"{pages} pages (want {CONTENT_PAGES + 1} or {CONTENT_PAGES + 2})")
    continued = [i + 1 for i, s in enumerate(sections) if i and not s]
    split = sentence_split_breaks(text, continued)
    if split:
        hits.append(f"page(s) {split} open mid-sentence")
    return {"ok": not hits, "pages": pages, "hits": hits,
            "book_page": next((i + 1 for i, s in enumerate(sections) if book_heading in s), None),
            "edu_pages": [i + 1 for i, here in enumerate(present) if edu_heading in here]}


# ------------------------------------------------------------------ L2 · true printed size
# Chrome silently shrinks a whole page when any element is wider than the type area (09-11 EN 0.924, W37 EN
# 0.849). Line-box heights misread that twice, so L2 reads each glyph's font size from the PDF (pdfminer).
# The 12pt build fails this on purpose: the shipped size is 10.5pt body / 9.5pt tables.
BODY_FONT = {"EN": "IBMPlexSans-Regular", "ZH": "PingFangSC-Regular"}
TABLE_FONT = "IBMPlexMono-Regular"  # table figures
BODY_PT, BODY_TOL, TABLE_MIN_PT = 10.5, 0.1, 9.5  # Andy 09-13, final:「表格用9.5， 正文用10.5」


def size_tiers(pdf_path, max_pages: int = 2) -> dict:
    """{(font without subset prefix, size rounded to 0.1pt): glyph count} over the first pages."""
    import collections
    import logging

    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTChar

    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    tiers = collections.Counter()

    def walk(o):
        if isinstance(o, LTChar):
            if o.get_text().strip():
                tiers[(o.fontname.split("+")[-1], round(o.size, 1))] += 1
        elif hasattr(o, "__iter__"):
            for x in o:
                walk(x)

    for page in extract_pages(str(pdf_path), maxpages=max_pages):
        walk(page)
    return dict(tiers)


def _top_size(tiers: dict, font: str):
    sizes = {sz: n for (fn, sz), n in tiers.items() if fn == font}
    return max(sizes, key=sizes.get) if sizes else None


def check_true_size(tiers: dict, lang: str) -> dict:
    """L2: body tier (most glyphs of the body font) must be 12.0±0.1pt; table tier (most glyphs of the
    mono figures) must not be under 10.5pt."""
    body, table = _top_size(tiers, BODY_FONT[lang]), _top_size(tiers, TABLE_FONT)
    hits = []
    if body is None or abs(body - BODY_PT) > BODY_TOL:
        hits.append(f"body {body}pt (want {BODY_PT}±{BODY_TOL})")
    if table is None or table < TABLE_MIN_PT:
        hits.append(f"table {table}pt (< {TABLE_MIN_PT})")
    return {"ok": not hits, "body_pt": body, "table_pt": table, "hits": hits}


def check_true_size_pdf(pdf_path, lang: str) -> dict:
    try:
        return check_true_size(size_tiers(pdf_path), lang)
    except ImportError:  # fail closed: a missing reader must not read as a pass
        return {"ok": False, "body_pt": None, "table_pt": None, "hits": ["pdfminer.six not installed"]}


def check_margins(pdf_path, left_mm: float = 14.0, right_mm: float = 14.0, tol_pt: float = 2.0) -> dict:
    out = subprocess.run(["pdftotext", "-bbox", str(pdf_path), "-"], capture_output=True, text=True, check=True).stdout
    bad = margin_overflow(out, left_mm, right_mm, tol_pt)
    return {"ok": not bad, "count": len(bad), "overflow": bad[:12]}


# ------------------------------------------------------------------ L3 · the state row travels whole
_STATE_VOTES = re.compile(r"/\s*\d+\s*(?:votes|票)\s*$")
_STATE_ENV = re.compile(r"^\s*[A-Z]{4,}\b")


def check_state_row(layout_text: str) -> dict:
    """L3 (Visual Vera 09-14): the big state word, its score and "/ N votes" print as one row on one page.
    In pdftotext -layout that row is one line; a page break inside the flex row leaves the "/ N votes" line
    without the state word (09-11 EN: "MIXED" closed page 1, "0 / 12 votes" opened page 2)."""
    rows = [ln for ln in layout_text.splitlines() if _STATE_VOTES.search(ln)]
    split = [ln.strip() for ln in rows if not _STATE_ENV.search(ln)]
    return {"ok": bool(rows) and not split, "rows": len(rows), "split": split}
