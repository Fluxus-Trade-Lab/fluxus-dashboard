#!/usr/bin/env python3
"""Copy the day's recap cross-asset sentences to the Market State page.

Andy 2026-10-03: 「选B，搬复盘原句，先不做门禁。」 — the recap's own
`cross_assets` sentences go on the public page verbatim, minus the internal
◇ marker (it flags an outside conclusion for the recap writer, not the reader).

Reads  <root>/<YYYY-MM>/<YYYY-MM-DD>/pack/content_{EN,ZH}.json   (local only)
Writes frontend/public/data/recap_cross.json                        (public)

    python3 recap_cross.py --date 2026-10-02 [--root ~/Documents/Trading/01_Market_Reports_Daily] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / "Documents/Trading/01_Market_Reports_Daily"
OUT = Path("frontend/public/data/recap_cross.json")

# Lead noun (the recap bolds it) → the Cross-asset card it belongs to.
# Order matters: "ten-year" before "bond", "silver" with gold.
ASSETS = [
    (("ten-year", "10-year", "十年"), "10Y"),
    (("bond", "treasur", "债"), "TLT"),
    (("dollar", "美元"), "UUP"),
    (("gold", "silver", "metal", "黄金", "白银", "金属"), "GLD"),
    (("crude", "oil", "原油"), "USO"),
    (("bitcoin", "crypto", "比特币", "加密"), "IBIT"),
    (("vix", "volatility", "波动"), "VIX"),
]


def asset_of(sentence: str) -> str | None:
    m = re.search(r"<b>(.*?)</b>", sentence)
    head = (m.group(1) if m else sentence[:40]).lower()
    for keys, ticker in ASSETS:
        if any(k in head for k in keys):
            return ticker
    return None


def clean(sentence: str) -> str:
    s = re.sub(r"\s*◇", "", sentence)
    return re.sub(r"\s{2,}", " ", s).strip()


def notes(content: dict) -> list[dict]:
    return [{"ticker": asset_of(s), "text": clean(s)} for s in content.get("cross_assets") or [] if s.strip()]


def build(date: str, root: Path) -> dict:
    pack = root / date[:7] / date / "pack"
    out = {"asof": date, "notes": {}}
    for lang in ("EN", "ZH"):
        p = pack / f"content_{lang}.json"
        if p.exists():
            out["notes"][lang.lower()] = notes(json.loads(p.read_text()))
    if not out["notes"]:
        raise FileNotFoundError(f"no content_EN/ZH.json under {pack}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    doc = build(a.date, a.root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    unmapped = [n["text"][:40] for v in doc["notes"].values() for n in v if n["ticker"] is None]
    print(json.dumps({"asof": doc["asof"], "counts": {k: len(v) for k, v in doc["notes"].items()}, "unmapped": unmapped}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
