"""Open doorbells in INBOX.md -- the ones nobody has taken yet.

The constitution's fetch command is `grep "🔔.*→ *<line>.*pending"`. A doorbell
line is append-only, so it keeps saying `pending` after it is handled; the
receipt is an indented `↳ ✅ <line> 已取` line written under it. The grep alone
therefore returns handled and unhandled doorbells alike: on 09-16 the daily
page showed "OPS 名下 9 条滞留" when 6 of OPS's 10 pending lines already had
receipts (X 日调研 reported the same shape on 09-12).

A doorbell is open until a `↳ ✅` line in the block under it closes it. A ✅
line closes it unless it is signed by another line only: on 09-16 Plumber Joe's
unrelated `↳ ✅ Plumber Joe …` note landed under an OPS doorbell. Unsigned
receipts (`↳ ✅ 已执行（09-13 · <commit>）`) do close — most lines write them that way.

    python3 -m pipeline.tools.doorbells --to OPS --older-than-hours 48
    git -C <repo> show origin/main:pipeline/tools/doorbells.py | python3 - --repo <repo> --to Joe

The second form is the constitution's fetch command: it needs nothing from the checkout it runs in,
so a task sitting on an old branch still runs the current tool against the current INBOX.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass


INBOX = "data/research/night_reports/INBOX.md"
_BELL = re.compile(r"^🔔\s*\[(\d{2})-(\d{2})\]\s*→\s*([^:：]+)[:：]\s*(.*)$")
_GENERIC = {"line", "data", "marketing", "visual", "studio", "writer", "plumber", "nighty", "growth", "rnd", "ui"}


@dataclass
class Bell:
    lineno: int
    date: dt.date
    to: str
    text: str
    receipts: list[str]
    open: bool = True


def _keys(to: str) -> list[str]:
    head = re.split(r"\s*·\s*", to.strip())[0]
    words = [w for w in re.split(r"\s+", head) if len(w) >= 3]
    specific = [w for w in words if w.lower() not in _GENERIC]
    return specific or words


def _signed(keys: list[str], receipt: str) -> bool:
    low = receipt.lower()
    return any(k.lower() in low for k in keys)


def closes(to: str, receipt: str, roster: set[str]) -> bool:
    """A ✅ receipt closes the doorbell unless it names some other line and not the addressee."""
    if "✅" not in receipt:
        return False
    own = _keys(to)
    if _signed(own, receipt):
        return True
    others = [k for k in roster if k.lower() not in {o.lower() for o in own}]
    return not _signed(others, receipt)


def parse(text: str, year: int) -> list[Bell]:
    lines = text.splitlines()
    bells = []
    for i, ln in enumerate(lines):
        m = _BELL.match(ln)
        if not m or "pending" not in ln:
            continue
        receipts = []
        j = i + 1
        while j < len(lines) and lines[j].lstrip().startswith("↳"):
            receipts.append(lines[j].strip())
            j += 1
        bells.append(Bell(i + 1, dt.date(year, int(m.group(1)), int(m.group(2))), m.group(3).strip(), m.group(4).strip(), receipts))
    roster = {k for b in bells for k in _keys(b.to)}
    for b in bells:
        b.open = not any(closes(b.to, r, roster) for r in b.receipts)
    return bells


def open_bells(text: str, to: str | None, now: dt.datetime, older_than_hours: float = 0) -> list[Bell]:
    out = []
    for b in parse(text, now.year):
        if not b.open:
            continue
        if to and to.lower() not in b.to.lower():
            continue
        age_h = (now.replace(tzinfo=None) - dt.datetime.combine(b.date, dt.time())).total_seconds() / 3600
        if age_h >= older_than_hours:
            out.append(b)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--to", help="addressee substring, e.g. OPS / Joe / Steve")
    ap.add_argument("--older-than-hours", type=float, default=0)
    ap.add_argument("--file", help="read a local file instead of origin/main")
    ap.add_argument("--repo", default=".", help="repository to read origin/main from")
    a = ap.parse_args(argv)
    if a.file:
        text = open(a.file, encoding="utf-8").read()
    else:
        r = subprocess.run(["git", "-C", a.repo, "show", f"origin/main:{INBOX}"], capture_output=True, text=True)
        if r.returncode:
            print(f"cannot read origin/main:{INBOX}: {r.stderr.strip()}", file=sys.stderr)
            return 2
        text = r.stdout
    bells = open_bells(text, a.to, dt.datetime.now(), a.older_than_hours)
    for b in bells:
        print(f"L{b.lineno} [{b.date:%m-%d}] → {b.to}: {b.text[:160]}")
    print(f"open: {len(bells)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
