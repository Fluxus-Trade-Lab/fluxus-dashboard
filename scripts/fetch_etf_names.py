"""Fetch display names for the dashboard's ETFs, once, into a static file.

The cards want "GDX / Gold Miners", not "GDX" on its own, and the names were
the one piece of that not already on disk. They are also the kind of thing that
should never be typed from memory: a wrong fund name is invisible in review and
wrong forever.

Output: frontend/src/lib/etfNames.json  (ticker -> short display name)

Run when the ETF lists in frontend/src/lib/etfGroups.js change:

    python -m scripts.fetch_etf_names

Names are shortened from the vendor's — "VanEck Gold Miners ETF" is the fund,
"Gold Miners" is the exposure, and the card has room for the exposure. The
trimming is mechanical (drop the issuer prefix and the ETF/Fund suffix) and
whatever survives is kept verbatim; anything that trims to nothing keeps the
vendor string, and anything that cannot be fetched is simply absent so the UI
falls back to the ticker rather than inventing a label.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS_JS = ROOT / "frontend" / "src" / "lib" / "etfGroups.js"
OUT = ROOT / "frontend" / "src" / "lib" / "etfNames.json"

# Issuer prefixes carry no information on a card where every row is an ETF.
_ISSUERS = (
    "State Street", "VanEck", "iShares", "SPDR", "Invesco", "Global X",
    "First Trust", "ARK", "Amplify", "ProShares", "Direxion", "Vanguard",
    "Schwab", "United States", "Sprott", "KraneShares", "Defiance",
    "Roundhill", "AdvisorShares", "Simplify", "Themes", "Tema", "abrdn",
    "Grayscale", "Fidelity", "Franklin", "Pacer", "WisdomTree", "Alerian",
    "Bitwise", "CoinShares", "SonicShares", "Virtus", "U.S. Global",
    "USCF", "Hashdex", "Valkyrie",
)

# Branding that survives in the middle of a name rather than at either end.
# Index families are NOT here: "Dow Jones" and "Nasdaq" are what the fund
# tracks, not who sells it, and stripping them left DIA reading "Industrial
# Average".
_INFIXES = ("SPDR", "S&P", "DB", "Reaves")

_SUFFIXES = (
    "Select Sector SPDR", "Select Sector", "Index Tracking", "Trust Series I",
    "ETF", "Fund, LP", "Fund", "Trust", "Shares", "Index", "Portfolio", "ETV",
    "LP", "Inc.", "Inc",
)


def shorten(name: str) -> str:
    """Issuer and branding out, exposure kept verbatim.

    Applied repeatedly because the layers nest: "State Street SPDR S&P Oil &
    Gas Exploration" needs three passes to become "Oil & Gas Exploration", and
    a single pass would leave the fund half-named, which is worse than not
    trimming at all.
    """
    out = name
    for _ in range(4):
        before = out
        for issuer in _ISSUERS:
            out = re.sub(rf"^{re.escape(issuer)}\b[\s'’]*", "", out, flags=re.I)
        for suffix in _SUFFIXES:
            out = re.sub(rf"[\s,]+{re.escape(suffix)}$", "", out, flags=re.I)
        for infix in _INFIXES:
            out = re.sub(rf"^{re.escape(infix)}\b\s*", "", out, flags=re.I)
        out = re.sub(r"\s+", " ", out).strip(" -–—,")
        if out == before:
            break
    return out or name


def tickers_from_groups(path: Path) -> list[str]:
    src = path.read_text()
    seen: dict[str, None] = {}
    for group in ("Industries", "Sel Sectors", "Indices", "S&P Style"):
        m = re.search(rf"'?{re.escape(group)}'?:\s*\[(.*?)\]", src, re.S)
        if not m:
            continue
        for t in re.findall(r"'([A-Z]+)'", m.group(1)):
            seen.setdefault(t, None)
    return list(seen)


def main() -> int:
    import yfinance as yf

    tickers = tickers_from_groups(GROUPS_JS)
    print(f"{len(tickers)} tickers from {GROUPS_JS.name}")

    names: dict[str, str] = {}
    missing: list[str] = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info or {}
        except Exception as exc:                      # noqa: BLE001 - report, continue
            print(f"  {t}: {type(exc).__name__}")
            missing.append(t)
            continue
        raw = info.get("longName") or info.get("shortName")
        if not raw:
            missing.append(t)
            continue
        names[t] = shorten(str(raw))

    OUT.write_text(json.dumps(dict(sorted(names.items())), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(names)} names -> {OUT.relative_to(ROOT)}")
    if missing:
        # Absent, not guessed: the UI falls back to the ticker.
        print(f"no name for {len(missing)}: {' '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
