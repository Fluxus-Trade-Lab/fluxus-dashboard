"""Move last month's finished sections out of night_reports/INBOX.md.

INBOX.md is an append-only mailbox that eight lines write to and several read
top to bottom every run. By 09-17 it was 3,101 lines; Andy approved moving old
months out ("非常好的想法。执行", 09-17). This tool does that move and nothing else:

- a "## " section whose heading carries a date before the cutoff month goes,
  verbatim, to INBOX_archive_<YYYY-MM>.md (appended if the file exists);
- the fixed sections at the top (up to and including "## 已裁决") never move;
- a section that still holds an open doorbell (pipeline.tools.doorbells) stays,
  so a line's fetch command keeps finding it; a later run moves it once it closes;
- undated sections stay;
- one pointer line under the title lists every archive month.

The CLI refuses to write if the open-doorbell set changes or if any line would
be lost, so a bad run fails loudly instead of quietly shrinking the mailbox.

    python3 -m pipeline.tools.inbox_archive --repo .            # cutoff = 1st of this month (UTC)
    python3 -m pipeline.tools.inbox_archive --repo . --dry-run
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

from pipeline.tools.doorbells import parse

INBOX = "data/research/night_reports/INBOX.md"
_DATE = re.compile(r"(?:(20\d\d)-)?(\d\d)-(\d\d)")
HEADER_LINES = 5


def section_month(heading: str, year: int) -> str | None:
    """First real date in a heading as YYYY-MM; a date without a year gets `year`."""
    for m in _DATE.finditer(heading):
        mm, dd = int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{m.group(1) or year}-{mm:02d}"
    return None


def _header(month: str) -> list[str]:
    return [
        f"# 夜间组收件箱 · {month} 归档（只读）",
        "",
        f"> 由 `pipeline/tools/inbox_archive.py` 从 `INBOX.md` 原样搬来，逐字未改。",
        "> 这里不再追加；新行一律写 `INBOX.md`。仍有未取门铃的节不会被搬来。",
        "",
    ]


def _pointer(months: list[str]) -> str:
    links = " · ".join(f"[`INBOX_archive_{m}.md`](INBOX_archive_{m}.md)" for m in months)
    return (f"> 📦 **归档**：{links}（每月 1 日由 `pipeline/tools/inbox_archive.py` 把上月及更早、"
            "门铃已取完的节原样搬走；Andy 09-17 批）")


def archive(text: str, cutoff: dt.date, existing: dict[str, str]):
    """Return (kept_text, archive_files, report). `existing` maps YYYY-MM to current archive content."""
    trailing = text.endswith("\n")
    lines = (text[:-1] if trailing else text).split("\n")
    cut = f"{cutoff.year}-{cutoff.month:02d}"

    heads = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    fixed_end = next((i for i in heads if lines[i].startswith("## 已裁决")), -1)
    open_rows = {b.lineno - 1 for b in parse(text, cutoff.year) if b.open}

    move: dict[str, list[tuple[int, int]]] = collections.defaultdict(list)
    kept_open = []
    for k, h in enumerate(heads):
        if h <= fixed_end:
            continue
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        month = section_month(lines[h], cutoff.year)
        if month is None:
            continue
        if not re.search(r"20\d\d-\d\d-\d\d", lines[h]) and int(month[5:]) > cutoff.month:
            month = f"{cutoff.year - 1}{month[4:]}"      # "12-30" read in January is last year
        if month >= cut:
            continue
        if any(h <= r < end for r in open_rows):
            kept_open.append(lines[h])
            continue
        move[month].append((h, end))

    gone = {i for spans in move.values() for h, end in spans for i in range(h, end)}
    kept = [ln for i, ln in enumerate(lines) if i not in gone]

    files = dict(existing)
    for month, spans in move.items():
        body = [ln for h, end in spans for ln in lines[h:end]]
        if month in files:
            base = files[month] if files[month].endswith("\n") else files[month] + "\n"
            files[month] = base + "\n".join(body) + "\n"
        else:
            files[month] = "\n".join(_header(month) + body) + "\n"

    ptr_rows = [i for i, ln in enumerate(kept[:8]) if ln.startswith("> 📦")]
    if files:
        new_ptr = _pointer(sorted(files))
        if ptr_rows:
            kept[ptr_rows[0]] = new_ptr
            for i in reversed(ptr_rows[1:]):
                del kept[i]
        else:
            kept.insert(1, new_ptr)

    report = {
        "cutoff": cut,
        "moved_sections": sum(len(s) for s in move.values()),
        "moved_lines": len(gone),
        "by_month": {m: sum(e - h for h, e in s) for m, s in sorted(move.items())},
        "kept_open": kept_open,
        "inbox_lines_after": len(kept),
        "header_lines": HEADER_LINES,
    }
    return "\n".join(kept) + ("\n" if trailing else ""), files, report


def _rows(text: str) -> collections.Counter:
    body = text[:-1] if text.endswith("\n") else text
    return collections.Counter(ln for ln in body.split("\n") if not ln.startswith("> 📦"))


def _open_set(text: str, year: int) -> collections.Counter:
    return collections.Counter((b.date, b.to, b.text) for b in parse(text, year) if b.open)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--before", help="cutoff date YYYY-MM-DD (default: 1st of the current UTC month)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    today = dt.datetime.now(dt.timezone.utc).date()
    cutoff = dt.date.fromisoformat(a.before) if a.before else today.replace(day=1)
    inbox = Path(a.repo) / INBOX
    folder = inbox.parent
    text = inbox.read_text(encoding="utf-8")
    existing = {p.stem.removeprefix("INBOX_archive_"): p.read_text(encoding="utf-8")
                for p in sorted(folder.glob("INBOX_archive_*.md"))}

    kept, files, report = archive(text, cutoff, existing)

    # Guards: same open doorbells, no line lost.
    if _open_set(text, cutoff.year) != _open_set(kept, cutoff.year):
        print("refusing: the open-doorbell set would change", file=sys.stderr)
        return 1
    added = collections.Counter()
    for m, content in files.items():
        old = existing.get(m, "")
        base = old if (not old or old.endswith("\n")) else old + "\n"
        if not content.startswith(base):
            print(f"refusing: archive {m} would be rewritten, not appended", file=sys.stderr)
            return 1
        part = content[len(base):]
        if not part:
            continue
        rows = part[:-1].split("\n")          # every write ends with exactly one "\n"
        added.update(rows[HEADER_LINES:] if not old else rows)
    removed = _rows(text) - _rows(kept)
    if removed != added:
        print(f"refusing: {sum((removed - added).values())} lines would be lost, "
              f"{sum((added - removed).values())} invented", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=1))
    if a.dry_run or report["moved_sections"] == 0 and kept == text:
        return 0
    for m, content in files.items():
        if existing.get(m) != content:
            (folder / f"INBOX_archive_{m}.md").write_text(content, encoding="utf-8")
    inbox.write_text(kept, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
