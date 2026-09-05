"""Naming collisions between our field names and standard vocabulary
(pipeline/tools/audit_metric_names.py).

Three times, a self-invented field wore a standard's own name: `wk_tight_3`
(now `wk_band_3`) borrowed IBD's "3 Tight Closes" for a 1.5%-band rule that
is entirely ours; `rs_ibd` (now `rs_rating`) borrowed IBD's RS Rating for a
community reconstruction that IBD never published. The 2026-09-06
vocabulary sweep (`data/research/ops/recap_vocab_sources_2026-09-06.md`)
found the same shape twice more, this time without a rename ever happening:
`sp_phase` (oratnek Structure Pivot's internal 1/2/3 state) reads like
Weinstein's "stage", and `vcs` (oratnek's Volatility Contraction Score)
reads like Minervini's VCP -- both already published, both never renamed,
because nothing had ever asked "does this name already mean something
else." Andy, 2026-09-06, verbatim: 「候选行批了，Power Trend 改判定对齐
Webster，撞名立机制。」Three occurrences was already the repeated shape in
`pitfall_invented_a_metric_that_already_had_a_standard.md`; a fourth makes
it a mechanism, not another one-off rename.

WHAT THIS CHECKS: `data/reference/METRIC_SOURCES.md`'s 登记表 (the `| 我们发的
| 标准名 | 标准口径 | 状态 |` table). For every row whose 状态 column contains
自造 or 冒充 -- we are ourselves declaring the value self-invented, or
admitting a past name impersonated a standard -- the 我们发的 field name must
NOT normalize to the same token as a proper-noun span quoted in 标准名
(a `**bold**` span, or a short acronym in parens inside one, e.g. "(VCP)").
A row that carries the giveaway word and STILL wears the standard's own
name is the exact shape of the bug: a self-invented number, dressed in a
name a reader will mistake for the standard reading.

RATCHET, not a rewrite of history: ALLOWLIST below holds 我们发的 raw cell
text for rows that predate this check and have not been renamed yet -- none
are seeded today (the four historical precedents above no longer collide
under this check; see the test suite for the replay that proves it). An
allowlisted row still prints, as a warning, never silently invisible -- it
just does not fail the exit code. Anything NOT on the allowlist that
collides is a violation. The job is to catch the *next* one, not relitigate
names already shipped before 2026-09-06.

A missing file, a missing `## 登记表` heading, a header row that doesn't
match the expected four columns, or a data row with the wrong cell count is
a LOUD error -- it lands in violations and fails the exit code exactly like
a real naming collision. An audit that cannot find its own table must never
report clean.

    python -m pipeline.tools.audit_metric_names
    python -m pipeline.tools.audit_metric_names --file path/to/METRIC_SOURCES.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

METRIC_SOURCES = Path("data/reference/METRIC_SOURCES.md")

# 我们发的 raw cell text (verbatim, as written in the live table) for rows
# grandfathered in before this check existed. Empty today -- see the module
# docstring; nothing in the current file needs an exemption. Do not add to
# this without a rename plan: an allowlist entry is a debt, not a pardon.
ALLOWLIST: Set[str] = set()

TABLE_HEADING = "## 登记表"
EXPECTED_HEADER = ["我们发的", "标准名", "标准口径", "状态"]
FLAG_WORDS = ("自造", "冒充")

_NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)
_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
_DIVIDER_CELL_RE = re.compile(r"^:?-{2,}:?$")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_PAREN_ACRONYM_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9]{1,12})\)")
_IDENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_]*$")


def _normalize(s: str) -> str:
    """lowercase; strip spaces/hyphens/underscores and the markdown
    emphasis/code punctuation that wraps names in this table, down to a
    bare comparable token."""
    s = s.strip().lower()
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"[\s\-_/]", "", s)
    return s


def _split_row(line: str) -> List[str]:
    m = _ROW_RE.match(line.strip())
    if not m:
        return []
    return [c.strip() for c in m.group(1).split("|")]


def _is_divider(cells: List[str]) -> bool:
    return bool(cells) and all(_DIVIDER_CELL_RE.match(c) for c in cells)


def _extract_field_token(cell: str) -> str:
    """The first backtick-quoted identifier in 我们发的 -- the actual field
    name, not a companion filename (those contain a dot and are skipped) or
    a second/alias field. A placeholder cell (`—`, `*(未发)*`, no backticks
    at all) yields "" -- nothing published yet, nothing to check."""
    for tok in _BACKTICK_RE.findall(cell):
        if _IDENT_RE.match(tok):
            return _normalize(tok)
    return ""


def _extract_canonical_tokens(cell: str) -> Set[str]:
    """Every bold span in 标准名, plus any short parenthetical acronym found
    inside one -- the proper-noun surface a reader would recognize as THE
    standard's own name (e.g. "Volatility Contraction Pattern (VCP)" yields
    both the full phrase and "VCP")."""
    tokens: Set[str] = set()
    for span in _BOLD_RE.findall(cell):
        norm = _normalize(span)
        if norm:
            tokens.add(norm)
        for acro in _PAREN_ACRONYM_RE.findall(span):
            tokens.add(_normalize(acro))
    return tokens


def parse_table(text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """Return (rows, errors) for the `## 登记表` table. Each row is a dict
    with keys 我们发的/标准名/标准口径/状态 holding the raw (un-normalized)
    cell text."""
    errors: List[str] = []
    idx = text.find(TABLE_HEADING)
    if idx == -1:
        errors.append(f"'{TABLE_HEADING}' heading not found -- table is unparsable")
        return [], errors

    rest = text[idx + len(TABLE_HEADING):]
    nxt = _NEXT_HEADING_RE.search(rest)
    section = rest[:nxt.start()] if nxt else rest

    lines = [ln for ln in section.splitlines() if ln.strip().startswith("|")]
    if not lines:
        errors.append(f"no '|' table rows found under '{TABLE_HEADING}'")
        return [], errors

    header_cells = _split_row(lines[0])
    if header_cells != EXPECTED_HEADER:
        errors.append(f"table header {header_cells!r} != expected {EXPECTED_HEADER!r}")
        return [], errors

    rows: List[Dict[str, str]] = []
    for line in lines[1:]:
        cells = _split_row(line)
        if not cells or _is_divider(cells):
            continue
        if len(cells) != len(EXPECTED_HEADER):
            errors.append(f"row has {len(cells)} cells, expected {len(EXPECTED_HEADER)}: {line[:80]!r}")
            continue
        rows.append(dict(zip(EXPECTED_HEADER, cells)))
    return rows, errors


def check(text: str) -> Dict[str, object]:
    """Run the naming-collision check over already-loaded table text."""
    rows, errors = parse_table(text)
    out: Dict[str, object] = {"violations": list(errors), "warnings": [], "checked_rows": 0, "ok": True}
    if errors:
        out["ok"] = False
        return out

    for row in rows:
        status = row["状态"]
        if not any(w in status for w in FLAG_WORDS):
            continue
        field_tok = _extract_field_token(row["我们发的"])
        if not field_tok:
            continue
        canon = _extract_canonical_tokens(row["标准名"])
        if field_tok not in canon:
            continue
        out["checked_rows"] = int(out["checked_rows"]) + 1
        msg = (f"`{row['我们发的']}` reuses a standard token from 标准名={row['标准名'][:60]!r} "
               f"while 状态 declares 自造/冒充: {status[:60]!r}")
        if row["我们发的"] in ALLOWLIST:
            out["warnings"].append(f"(grandfathered) {msg}")
        else:
            out["violations"].append(msg)

    out["ok"] = not out["violations"]
    return out


def run(path: Path = METRIC_SOURCES) -> Dict[str, object]:
    if not path.exists():
        return {"ok": False, "violations": [f"{path} not found"], "warnings": [], "checked_rows": 0}
    return check(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=str(METRIC_SOURCES))
    args = ap.parse_args(argv)
    out = run(Path(args.file))

    for w in out["warnings"]:
        print(f"    {w}")
    for v in out["violations"]:
        print(f"BAD {v}")
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: {len(out['violations'])} violation(s), "
          f"{len(out['warnings'])} warning(s) over {out['checked_rows']} flagged row(s)")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
