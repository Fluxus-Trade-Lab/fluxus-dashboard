"""Verify every hand-written theme member against what the company actually does.

``audit_taxonomy`` proves a ticker *resolves*.  It cannot prove the company
*belongs* -- and a wrong large-cap does real damage, because it drags the
theme's reading toward a business that has nothing to do with the theme.

This pulls each name's business description from yfinance and checks it
against a keyword profile for its theme.  Three outcomes:

``PASS``    the description clearly matches the theme
``FLAG``    no match found -- needs a human or a web check
``UNKNOWN`` no description available

Nothing here decides anything on its own.  It sorts 87 names into "obviously
fine" and "look at this", so the manual pass is spent where it matters.

    python -m pipeline.themes.verify_members
    python -m pipeline.themes.verify_members --refresh   # re-pull descriptions
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.themes import taxonomy

logger = logging.getLogger(__name__)

CACHE = Path(".cache/company_profiles.json")
UNIVERSE = Path("data/output/universe.json")
OUT = Path("data/reference/theme_verification.md")

# Market-cap tier above which an error is treated as unacceptable.
BIG_CAP = 1e10

# What each theme's members should demonstrably be about.  Deliberately
# generous -- the goal is to surface names needing a look, not to auto-reject.
KEYWORDS: Dict[str, List[str]] = {
    "AI - Datacenters": [
        "data cent", "datacent", "hyperscal", "cloud infrastructur", "colocation",
        "server", "gpu", "networking", "interconnect", "power", "electrical",
        "cooling", "thermal management", "transmission", "grid", "nuclear",
        "electricity", "fiber", "optical", "switch",
    ],
    "Cybersecurity": [
        "cybersecur", "security", "threat", "endpoint", "firewall", "identity",
        "zero trust", "vulnerabilit", "malware", "siem",
    ],
    "Space": [
        "space", "satellite", "launch", "orbit", "spacecraft", "rocket",
        "geospatial", "earth observation",
    ],
    "Drones": [
        "drone", "unmanned", "uav", "autonomous system", "counter-uas",
        "robotic", "aerial",
    ],
    "Lithium & Battery Tech": [
        "lithium", "batter", "energy storage", "cathode", "anode",
        "electrochemical", "cell manufactur",
    ],
    "Rare Earth Metals": [
        "rare earth", "critical mineral", "neodymium", "magnet", "uranium",
        "vanadium", "titanium", "mineral", "mining",
    ],
    "Crypto Equities": [
        "bitcoin", "crypto", "digital asset", "blockchain", "mining",
        "exchange", "stablecoin", "ethereum", "web3",
    ],
    "Bitcoin": [
        "bitcoin", "crypto", "digital asset", "blockchain", "mining",
    ],
    "Memory & Storage": [
        "memory", "storage", "nand", "dram", "flash", "hard disk",
        "solid state", "data storage", "semiconductor",
    ],
    "Quantum Computing": [
        "quantum", "qubit", "photonic", "cryogenic",
    ],
    # Tightened 2026-08-09: "cortisol", "diabet" and "metabolic" let CORT
    # (Cushing's syndrome, oncology) pass as an obesity name. Keywords must
    # name the mechanism or the indication, not an adjacent biology.
    "GLP-1 - Clinical Stage": [
        "glp-1", "glp1", "glucagon-like", "obesity", "weight loss",
        "weight management", "incretin", "amylin", "gipr",
    ],
    "GLP-1 - Commercial": [
        "glp-1", "glp1", "glucagon-like", "obesity", "weight loss",
        "weight management", "semaglutide", "tirzepatide",
    ],
    "Drones": [
        "drone", "unmanned", "uav", "uas", "counter-uas", "aerial",
        "autonomous system", "robotic",
    ],
    "_retired GLP-1 / Obesity": [
        "glp-1", "glp1", "glucagon-like", "obesity", "weight loss",
        "weight management", "incretin", "semaglutide", "tirzepatide",
        "gipr", "amylin",
    ],
}


def load_universe() -> Dict[str, Dict[str, Any]]:
    rows = json.loads(UNIVERSE.read_text())["rows"]
    return {str(r["ticker"]): r for r in rows if r.get("ticker")}


def fetch_profiles(tickers: List[str]) -> Dict[str, Dict[str, str]]:
    import yfinance as yf
    out: Dict[str, Dict[str, str]] = {}
    for i, t in enumerate(tickers, 1):
        try:
            info = yf.Ticker(t).info
            out[t] = {
                "name": info.get("longName") or info.get("shortName") or "",
                "summary": (info.get("longBusinessSummary") or "")[:1200],
                "sector": info.get("sector") or "",
                "industry": info.get("industry") or "",
            }
            logger.info("%3d/%d %-7s %s", i, len(tickers), t, out[t]["name"][:50])
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s profile unavailable: %s", t, exc)
            out[t] = {"name": "", "summary": "", "sector": "", "industry": ""}
    return out


def load_profiles(tickers: List[str], refresh: bool = False) -> Dict[str, Dict[str, str]]:
    cached: Dict[str, Dict[str, str]] = {}
    if CACHE.exists() and not refresh:
        cached = json.loads(CACHE.read_text())
    missing = [t for t in tickers if t not in cached]
    if missing:
        cached.update(fetch_profiles(missing))
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cached, indent=2))
    return cached


def check(theme: str, profile: Dict[str, str]) -> tuple[str, List[str]]:
    """Return (verdict, matched keywords)."""
    words = KEYWORDS.get(theme)
    blob = " ".join([profile.get("summary", ""), profile.get("name", ""),
                     profile.get("industry", "")]).lower()
    if not blob.strip():
        return "UNKNOWN", []
    if not words:
        return "NO-PROFILE-DEFINED", []
    hits = [w for w in words if re.search(re.escape(w), blob)]
    return ("PASS" if hits else "FLAG"), hits


def run() -> List[Dict[str, Any]]:
    uni = load_universe()
    pairs = [(t.name, k) for t in taxonomy.THEMES for k in t.extra]
    profiles = load_profiles(sorted({k for _, k in pairs}))

    rows: List[Dict[str, Any]] = []
    for theme, ticker in pairs:
        p = profiles.get(ticker, {})
        verdict, hits = check(theme, p)
        cap = (uni.get(ticker, {}).get("market_cap") or 0)
        rows.append({
            "theme": theme, "ticker": ticker, "name": p.get("name", ""),
            "cap_b": cap / 1e9, "big": cap >= BIG_CAP,
            "industry": uni.get(ticker, {}).get("industry", ""),
            "verdict": verdict, "hits": hits,
            "summary": p.get("summary", ""),
        })
    return rows


def render(rows: List[Dict[str, Any]]) -> str:
    flagged = [r for r in rows if r["verdict"] != "PASS"]
    big_flagged = [r for r in flagged if r["big"]]

    out = [
        "# Theme member verification",
        "",
        f"{len(rows)} hand-written members across "
        f"{len({r['theme'] for r in rows})} themes. "
        f"**{sum(1 for r in rows if r['big'])}** are >= $10B market cap.",
        "",
        f"- PASS: {sum(1 for r in rows if r['verdict'] == 'PASS')}",
        f"- FLAG: {sum(1 for r in rows if r['verdict'] == 'FLAG')}",
        f"- UNKNOWN: {sum(1 for r in rows if r['verdict'] == 'UNKNOWN')}",
        "",
        "A FLAG means the company's own business description contains none of "
        "the theme's keywords. That is a prompt to look, not a verdict.",
        "",
    ]

    if big_flagged:
        out += ["## ⚠️ Flagged AND large cap — check these first", ""]
        for r in sorted(big_flagged, key=lambda x: -x["cap_b"]):
            out += [f"### {r['ticker']} · {r['name']} · ${r['cap_b']:.1f}B",
                    f"*theme:* **{r['theme']}** · *industry:* {r['industry']}", "",
                    (r["summary"][:400] + "...") if r["summary"] else "*no description*",
                    ""]

    small_flagged = [r for r in flagged if not r["big"]]
    if small_flagged:
        out += ["## Flagged, smaller cap", "",
                "| Ticker | Name | $B | Theme | Industry |", "|---|---|---|---|---|"]
        for r in sorted(small_flagged, key=lambda x: -x["cap_b"]):
            out.append(f"| {r['ticker']} | {r['name'][:34]} | {r['cap_b']:.1f} | "
                       f"{r['theme']} | {r['industry']} |")
        out.append("")

    out += ["## Passed", "",
            "| Ticker | Name | $B | Theme | Matched on |", "|---|---|---|---|---|"]
    for r in sorted([r for r in rows if r["verdict"] == "PASS"],
                    key=lambda x: (x["theme"], -x["cap_b"])):
        out.append(f"| {r['ticker']} | {r['name'][:32]} | {r['cap_b']:.1f} | "
                   f"{r['theme']} | {', '.join(r['hits'][:3])} |")

    return "\n".join(out)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    rows = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(rows))

    flagged = [r for r in rows if r["verdict"] != "PASS"]
    logger.info("%d members | %d flagged (%d of them >= $10B)",
                len(rows), len(flagged), sum(1 for r in flagged if r["big"]))
    for r in sorted(flagged, key=lambda x: -x["cap_b"]):
        logger.info("  %-7s $%7.1fB  %-26s %s", r["ticker"], r["cap_b"],
                    r["theme"], r["name"][:40])
    logger.info("Wrote %s", OUT)


if __name__ == "__main__":
    main()
