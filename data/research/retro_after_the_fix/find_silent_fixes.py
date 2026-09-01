"""List the commits that fixed a *silent* failure -- and say so reproducibly.

2026-09-01 I wrote "17 conditions, grepped from commit titles, trustworthy."
Running the grep as described gives 9, and none of the six commits that report
names them. Two reasons, both worth pinning in code instead of prose:

  1. This repo's commits are bilingual. `4f223879` says "three layers that
     would never have run again"; a Chinese-only pattern cannot see it.
  2. The symptom is often in the BODY, not the title. `2f782b53` is titled
     "feat(groups): a theme layer" -- the M-to-Z loss is three lines down.

So the number depended on a pattern and a scope that the prose did not state.
This script states both. Prose quotes what it prints; nothing is hand-typed.

    python3 data/research/retro_after_the_fix/find_silent_fixes.py --since '3 months ago'
"""
from __future__ import annotations

import argparse
import re
import subprocess

# Words that claim a failure ran unnoticed. Split into two tiers because the
# broad tier's recall costs precision: "一直" and "never" appear in plenty of
# commits that are not about silent failure at all.
NARROW = [r"静默", r"silent", r"没人发现", r"nobody noticed", r"unnoticed",
          r"从没", r"从未", r"was never", r"were never", r"never (?:been )?(?:written|run|computed|in the)",
          r"would never", r"再也不会"]
BROAD = NARROW + [r"一直", r"\bnever\b"]

SEP = "\x1e"


def commits(since: str, scope: str):
    fmt = f"%h{SEP}%ad{SEP}%s{SEP}%b{SEP}"
    out = subprocess.run(
        ["git", "log", "origin/main", f"--since={since}", f"--pretty=format:{fmt}%x00",
         "--date=short"],
        capture_output=True, text=True, check=True).stdout
    for rec in out.split("\x00"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, date, subject, body = (rec.split(SEP) + ["", "", "", ""])[:4]
        yield sha, date, subject, (subject if scope == "title" else subject + "\n" + body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="3 months ago")
    ap.add_argument("--scope", choices=["title", "full"], default="full")
    ap.add_argument("--tier", choices=["narrow", "broad"], default="narrow")
    a = ap.parse_args()

    pats = [re.compile(p, re.I) for p in (NARROW if a.tier == "narrow" else BROAD)]
    hits = []
    for sha, date, subject, hay in commits(a.since, a.scope):
        matched = sorted({p.pattern for p in pats if p.search(hay)})
        if matched:
            hits.append((sha, date, subject, matched))

    for sha, date, subject, matched in hits:
        print(f"{sha} {date} {subject[:96]}")
        print(f"{'':9}matched: {', '.join(matched)}")
    print(f"\n{len(hits)} commits  (since={a.since!r} scope={a.scope} tier={a.tier})")


if __name__ == "__main__":
    main()
