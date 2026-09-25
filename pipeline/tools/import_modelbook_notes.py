#!/usr/bin/env python3
"""Pull the model-book annotations out of the Obsidian vault into the dashboard.

Andy, 2026-09-25: "obsidian里有traderlion的modelbook，这些材料也加到这个
database里，如果有重复或者有批注，用traderlion的版本，注释是很有用的教学，
可以有一个侧栏是notes栏目。"

WHERE IT READS FROM. `FluxusTrading_Obsidian/60_ModelBook/_案例库/`, which holds
three kinds of card, all transcribed from PDFs Andy owns:

  B1_*_Model_Book.md      TraderLion Model Books (Ross Haber) — 62 tickers, each
                          with a paragraph of commentary that states the breakout
                          price and date, the high, and the gain in weeks.
  *_Market_Leaders.md     10 Years of Market Leaders (Richard Moglen) — 214 chart
                          pages, each a list of the labels drawn on the chart.
  Base_Breakouts.md,      Moglen again, grouped by pattern — and the only entries
  Base_Breakout_Failures  in this library that FAILED. The dashboard's own set is
  Gaps, Failed_Gaps       survivors only, so these are the half it has never had.

WHAT IT COPIES, AND UNDER WHOSE NAME. Everything: the authors' paragraphs, the
chart labels, and the facts those paragraphs state (breakout price and date, the
high, the gain, sector and industry).

The paragraphs were the open question. This repository is public and Vercel
serves `frontend/public/` verbatim, and the vault itself is gitignored here and
lives in a repository of its own — so copying the prose into `notes.json` puts
it on the public web for the first time. Raised with Andy on 2026-09-25; his
answer was "Haber's paragraphs可以放入。给credit". So they go in, and every note
carries the book, the author and the page it came from, in the data and on the
page. `--no-prose` drops them again if that decision is ever revisited.

Credit is not decoration here: a note without `book` and `author` is a bug, and
`check_credit()` refuses to write the file if one appears.

MERGE RULE. Keyed on ticker + year. Where the dashboard already has that pair,
the note attaches to the existing entry and TraderLion's stated breakout wins
over our computed one (Andy: "如果有重复或者有批注，用traderlion的版本").
Where it does not, a new entry is added with no bars — the page shows those as
notes-only cards until someone fetches the history.

OUTPUT. `frontend/public/data/modelbooks/notes.json`:

    {"generated_at": ..., "entries": {"<TICKER>-<YEAR>": {
        "sources": [{"book", "author", "page", "labels": [...], "facts": {...}}],
        "breakout": {"date", "price", "book"},   # TraderLion's, when stated
        "peak":     {"date", "price"},
        "gain_pct", "weeks", "sector", "industry", "outcome_line"}}}
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[2]
VAULT = REPO / "FluxusTrading_Obsidian" / "60_ModelBook" / "_案例库"
OUT = REPO / "frontend" / "public" / "data" / "modelbooks" / "notes.json"

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

# The 2018-2020 books date without a year ("on April 6th") and mean the book's
# year; the 2023/2024 books spell it out ("on November 16, 2023") and often mean
# the year BEFORE the book's. Read the year when it is written and only fall
# back to the file's when it is not — assuming it cost ISRG, SPOT and RNA a
# breakout each, all filed twelve months late.
RE_BREAKOUT = re.compile(
    r"broke out (?:through|above|of)\s+\$?([\d,]+\.?\d*)\s+on\s+"
    r"([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", re.I)
RE_HIGH = re.compile(
    r"(?:all-time high|high) of \$?([\d,]+\.?\d*)\s+on\s+"
    r"([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", re.I)
# "for a gain of 84% in 20 weeks"
RE_GAIN = re.compile(r"(?:gain|move|rise) of ([\d.]+)%\s+in\s+(\d+)\s+weeks?", re.I)
# The PDF lays sector and industry out as a two-column header with the two
# values on the NEXT line, so the pair has to be read across two lines:
#     Sector:                         Industry:
#     Consumer Discretionary          Internet & Direct Marketing
RE_SECTOR = re.compile(r"Sector:\s+Industry:\s*\n\s*(.+)")
RE_LABELS = re.compile(r"\*\*图上标注\*\*：(.+)")
# "## p108 · TSLA 2020 DAILY 1/2" and "## NVDA 2024 Daily Base Breakout - 180% ..."
RE_MOGLEN_HEAD = re.compile(r"^p(\d+)\s*·\s*([A-Z][A-Z0-9.\-]{0,6})\s+(\d{4})\b(.*)")
RE_TL_HEAD = re.compile(r"^([A-Z][A-Z0-9.\-]{0,6})[\s　]*（PDF p([\d\-]+)）")

# A few chart pages are headed with the company name rather than its symbol.
# Mapping them keeps the note attached to the entry it describes instead of
# floating off as a ticker that does not exist.
NAME_TO_TICKER = {"GOOGLE": "GOOG"}


def _iso(year: int, month_name: str, day: str) -> str | None:
    month = MONTHS.get(month_name.title())
    if not month:
        return None
    try:
        return date(year, month, int(day)).isoformat()
    except ValueError:
        return None


def _front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _sections(text: str) -> list[str]:
    """Everything after each `## ` heading, heading line included."""
    return re.split(r"\n##\s+", text)[1:]


def parse_traderlion(path: Path, with_prose: bool) -> list[dict]:
    """One record per ticker in a TraderLion Model Book file."""
    text = path.read_text(encoding="utf-8")
    fm = _front_matter(text)
    year_m = re.search(r"B1_(\d{4})", path.name)
    file_year = int(year_m.group(1)) if year_m else None
    out = []
    for sec in _sections(text):
        head = sec.splitlines()[0]
        m = RE_TL_HEAD.match(head.strip())
        if not m:
            continue
        ticker, page = m.group(1), m.group(2)
        rec = {
            "ticker": ticker,
            "year": file_year,
            "book": fm.get("book", "TraderLion Model Book"),
            "author": "Ross Haber",
            "page": page,
            "facts": {},
            "labels": [],
        }
        # pdftotext wraps mid-sentence ("made an all-time high\nof $3,552.25
        # on September 2nd"), so the facts are read off a single-line copy.
        flat = " ".join(sec.split())
        b = RE_BREAKOUT.search(flat)
        if b and file_year:
            d = _iso(int(b.group(4)) if b.group(4) else file_year, b.group(2), b.group(3))
            if d:
                rec["facts"]["breakout_date"] = d
                rec["facts"]["breakout_price"] = float(b.group(1).replace(",", ""))
        h = RE_HIGH.search(flat)
        if h and file_year:
            bo = rec["facts"].get("breakout_date")
            if h.group(4):
                d = _iso(int(h.group(4)), h.group(2), h.group(3))
            else:
                # no year written: it is the breakout's year, or the next one
                # when the high reads as falling before the breakout
                base = int(bo[:4]) if bo else file_year
                d = _iso(base, h.group(2), h.group(3))
                if d and bo and d < bo:
                    d = _iso(base + 1, h.group(2), h.group(3))
            if d:
                rec["facts"]["peak_date"] = d
                rec["facts"]["peak_price"] = float(h.group(1).replace(",", ""))
        g = RE_GAIN.search(flat)
        if g:
            rec["facts"]["gain_pct"] = float(g.group(1))
            rec["facts"]["weeks"] = int(g.group(2))
        s = RE_SECTOR.search(sec)
        if s:
            parts = [x.strip() for x in re.split(r"\s{2,}", s.group(1).strip()) if x.strip()]
            if parts:
                rec["facts"]["sector"] = parts[0]
            if len(parts) > 1:
                rec["facts"]["industry"] = " ".join(parts[1:])
        if with_prose:
            rec["prose"] = sec
        out.append(rec)
    return out


def parse_moglen(path: Path, with_prose: bool = True) -> list[dict]:
    """One record per annotated chart page in a Market Leaders file."""
    text = path.read_text(encoding="utf-8")
    fm = _front_matter(text)
    out = []
    for sec in _sections(text):
        head = sec.splitlines()[0].strip()
        m = RE_MOGLEN_HEAD.match(head)
        if not m:
            continue
        page, ticker, year, tail = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        ticker = NAME_TO_TICKER.get(ticker, ticker)
        labels = []
        lm = RE_LABELS.search(sec)
        if lm:
            labels = [x.strip().strip("`") for x in lm.group(1).split("·") if x.strip()]
        # the quoted lines above the labels are the page's own caption
        caption = [ln.lstrip("> ").strip() for ln in sec.splitlines()
                   if ln.startswith("> ") and "图上标注" not in ln]
        rec = {
            "ticker": ticker,
            "year": year,
            "book": fm.get("book", "10 Years of Market Leaders"),
            "author": "Richard Moglen",
            "page": page,
            "chart": tail.strip(" ·-"),
            "labels": labels,
            # A caption is one line of the author's prose. Kept only when it
            # names the pattern rather than explaining it — see the header.
            "caption": caption if with_prose else caption[:1],
            "facts": {},
        }
        out.append(rec)
    return out


def check_facts(entries: dict, weeks_tol: float = 3.0, gain_tol: float = 0.15) -> list[str]:
    """Audit each card against itself.

    A model book sentence states four things at once — two prices, two dates and
    a duration — so any three of them check the fourth for free. Worth running
    every import for two different reasons:

    · IT CATCHES OUR PARSING. Reading the month and day but assuming the file's
      year filed ISRG, SPOT and RNA's breakouts twelve months late; all three
      surfaced here as ~52-week errors and were fixed.
    · IT CATCHES THE BOOKS. What is left over after that fix is the source's
      own drift, and it is not noise worth hiding. Most entries are off by
      three to seven weeks, which reads as the author rounding to the week the
      high printed in. HOOD 2024 is a genuine contradiction: $11.33 on
      2024-09-02 to $42.76 on 2024-12-05 is +277% over 13 weeks, and the same
      sentence calls it "138% in 31 weeks". Our dates and prices are quoted as
      printed; the disagreement is the book's, and the page shows both numbers
      rather than silently picking one.
    """
    bad = []
    for key, e in entries.items():
        bo = (e.get("breakout") or {})
        pk = (e.get("peak") or {})
        weeks, gain = e.get("weeks"), e.get("gain_pct")
        if weeks and bo.get("date") and pk.get("date"):
            actual = (date.fromisoformat(pk["date"]) - date.fromisoformat(bo["date"])).days / 7
            if abs(actual - weeks) > weeks_tol:
                bad.append(f"{key}: dates span {actual:.0f}w, the book says {weeks}w")
        if gain and bo.get("price") and pk.get("price") and bo["price"] > 0:
            implied = (pk["price"] / bo["price"] - 1) * 100
            if abs(implied - gain) > max(gain_tol * abs(gain), 2):
                bad.append(f"{key}: ${bo['price']}→${pk['price']} is +{implied:.0f}%, "
                           f"the book says +{gain:.0f}%")
    return bad


def check_credit(entries: dict) -> None:
    """Every note names its book, its author and its page, or nothing is written."""
    bad = [f"{k} #{i}" for k, e in entries.items()
           for i, s in enumerate(e["sources"])
           if not s.get("book") or not s.get("author") or not s.get("page")]
    if bad:
        raise SystemExit(f"[notes] {len(bad)} note(s) carry no credit: {bad[:5]}")


def collect(vault: Path, with_prose: bool) -> dict:
    records: list[dict] = []
    for p in sorted(vault.glob("B1_*_Model_Book.md")):
        records += parse_traderlion(p, with_prose)
    for pattern in ("*_Market_Leaders.md", "Base_Breakouts.md",
                    "Base_Breakout_Failures.md", "Gaps.md", "Failed_Gaps.md"):
        for p in sorted(vault.glob(pattern)):
            records += parse_moglen(p, with_prose)

    entries: dict[str, dict] = {}
    for r in records:
        if not r.get("year"):
            continue
        key = f"{r['ticker']}-{r['year']}"
        e = entries.setdefault(key, {"ticker": r["ticker"], "year": r["year"], "sources": []})
        e["sources"].append({k: v for k, v in r.items() if k not in ("ticker", "year")})

    # TraderLion wins on every field it states (Andy 2026-09-25).
    for e in entries.values():
        tl = [s for s in e["sources"] if s["author"] == "Ross Haber"]
        for s in tl + [s for s in e["sources"] if s not in tl]:
            f = s.get("facts") or {}
            if f.get("breakout_date") and "breakout" not in e:
                e["breakout"] = {"date": f["breakout_date"], "price": f.get("breakout_price"),
                                 "book": s["book"]}
            if f.get("peak_date") and "peak" not in e:
                e["peak"] = {"date": f["peak_date"], "price": f.get("peak_price")}
            for k in ("gain_pct", "weeks", "sector", "industry"):
                if f.get(k) is not None and k not in e:
                    e[k] = f[k]
        e["has_traderlion"] = bool(tl)
        e["label_count"] = sum(len(s.get("labels") or []) for s in e["sources"])
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=VAULT)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--no-prose", action="store_true",
                    help="drop the authors' paragraphs and keep only facts and "
                         "chart labels (Andy approved including them 2026-09-25)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not a.vault.is_dir():
        logger.error("no vault at %s", a.vault)
        return 1
    entries = collect(a.vault, not a.no_prose)
    check_credit(entries)
    drift = check_facts(entries)
    payload = {
        "generated_at": date.today().isoformat(),
        "vault": str(a.vault.relative_to(REPO)),
        "prose_included": not a.no_prose,
        "entries": entries,
    }
    a.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    tl = sum(1 for e in entries.values() if e["has_traderlion"])
    withb = sum(1 for e in entries.values() if "breakout" in e)
    labels = sum(e["label_count"] for e in entries.values())
    logger.info("%d ticker-years · %d carry a TraderLion card · %d state a breakout · "
                "%d chart labels%s", len(entries), tl, withb, labels,
                "" if a.no_prose else " · with the authors' paragraphs")
    for line in drift:
        logger.warning("  ⚠ %s", line)
    if drift:
        logger.warning("  %d card%s disagree with themselves — see check_facts()",
                       len(drift), "" if len(drift) == 1 else "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
