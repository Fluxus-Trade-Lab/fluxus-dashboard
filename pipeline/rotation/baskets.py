"""Style baskets and the risk axis they sit on.

**Why style, not sector.** A sector rotation table tells you money moved from
industrials into utilities. It cannot tell you whether the market is paying for
risk, because sectors are not ordered on risk -- a sector table has no top and
no bottom. Style baskets do: growth over value, high beta over low volatility,
IPOs and microcaps over staples. Each pair is the same question asked with
different instruments, which is what makes a one-line verdict possible at the
end. "Three different cuts, same answer" is a sentence a sector table can
never produce.

Each basket is one liquid ETF, deliberately. A hand-curated constituent list
would need the whole validation apparatus in `pipeline/themes/` and would still
drift; the ETF is what the market itself is pricing, and it needs no
maintenance.

`side` is the basket's position on the risk axis, not a judgment. `risk_on`
means the basket outperforms when the market is paying for risk. A basket that
does not belong on the axis carries `side=None` and is drawn but never voted.
"""

from __future__ import annotations

from typing import Dict, List

RISK_ON, RISK_OFF = "risk_on", "risk_off"

# ticker -> (display name, side)
BASKETS: Dict[str, Dict[str, str | None]] = {
    "IVW":  {"name": "Growth Factor",     "side": RISK_ON},
    "IVE":  {"name": "Value Factor",      "side": RISK_OFF},
    "SPHB": {"name": "High Beta Factor",  "side": RISK_ON},
    "SPLV": {"name": "Low Volatility",    "side": RISK_OFF},
    "ARKK": {"name": "Speculative Tech",  "side": RISK_ON},
    "WCLD": {"name": "Cloud Software",    "side": RISK_ON},
    "IPO":  {"name": "IPOs",              "side": RISK_ON},
    "IWC":  {"name": "Microcaps",         "side": RISK_ON},
    "IWM":  {"name": "Small Caps",        "side": RISK_ON},
    "XLV":  {"name": "Healthcare",        "side": RISK_OFF},
    "XLP":  {"name": "Consumer Staples",  "side": RISK_OFF},
}

BENCHMARK = "SPY"

# The three cuts. Each is one long side against one short side, and each uses
# instruments the others do not, so agreement between them is evidence rather
# than the same measurement counted three times.
#
# That independence is the whole point and also the fragile part: IVW and SPHB
# share large-cap tech names, so cut A and cut B are correlated even though
# their tickers differ. Treated as three votes, never as three independent
# samples -- see `verdict()`, which reports the count and never a p-value.
CUTS: List[Dict[str, object]] = [
    {
        "key": "volatility",
        "label": "Volatility appetite",
        "long": ["SPHB"],
        "short": ["SPLV"],
        "question": "is the market paying for beta, or hiding from it",
    },
    {
        "key": "style",
        "label": "Style",
        "long": ["IVW"],
        "short": ["IVE"],
        "question": "growth over value, or the reverse",
    },
    {
        "key": "speculation",
        "label": "Speculation",
        "long": ["IPO", "IWC", "ARKK"],
        "short": ["XLV", "XLP"],
        "question": "the speculative end against the defensive end",
    },
]

# Every ticker any of the above needs, benchmark included.
REQUIRED: List[str] = sorted({BENCHMARK, *BASKETS} | {
    t for c in CUTS for side in ("long", "short") for t in c[side]  # type: ignore[index]
})
