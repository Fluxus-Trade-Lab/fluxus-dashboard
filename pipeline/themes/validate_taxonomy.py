"""Is each theme a real grouping, or just a label?

81% of the taxonomy was seeded from a competitor's published list, so the
useful question is whether these groupings describe how the names actually
trade -- independent of whose judgement picked them.

**Business themes** (semiconductors, uranium, AI datacenters) make a testable
claim: these companies are driven by the same thing, so they should co-move
more than a random basket of the same size from the same pool.

**Factor themes** (Microcaps, High Beta, Value) make no such claim.  "Market
cap under $1B" is a property, not a common driver -- a microcap biotech and a
microcap miner share a number and nothing else.  Testing them for co-movement
asks the wrong question, so they are reported separately and judged on whether
the rule selects what it says it selects.

The first version of this file scored everything with ``z = excess / sd``.
That was wrong: sd of the random baskets collapses as the basket grows (0.064
at n=5 down to 0.0037 at n=985, a 17x fall), so z measured basket *size* as
much as theme quality -- High Beta Factor scored z=-12.4 on an excess of only
-0.046.  The excess itself is stable across n (random mean sits at ~0.252
everywhere), so excess is the statistic and the noise band is context.

    python -m pipeline.themes.validate_taxonomy
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.themes import taxonomy
from pipeline.themes.backtest_accel import BENCH, load_panel
from pipeline.themes.build_groups import load_universe, resolve_theme_members
from pipeline.themes.etf_holdings import load_holdings

logger = logging.getLogger(__name__)

OUT = Path("data/reference/taxonomy_validation.md")
# Machine-readable verdicts. Validation needs a 10y price panel and cannot run
# in the daily cron, so build_groups reads the stored verdict instead of
# recomputing it. Stale verdicts are worse than none, hence the timestamp.
VERDICTS = Path("data/reference/taxonomy_verdicts.json")
N_DRAWS = 60
MIN_MEMBERS = 4
SEED = 20260809
MIN_OVERLAP = 252   # a correlation needs a year of shared history to mean anything

# Excess correlation over a size-matched random basket.  Absolute thresholds,
# because the excess is comparable across basket sizes and z is not.
REAL_THRESHOLD = 0.05
WEAK_THRESHOLD = 0.02

# Random baskets are only re-drawn at these sizes; the curve is smooth so
# intermediate n interpolates. Keeps a 56-theme run to seconds, not minutes.
CALIBRATION_SIZES = (5, 8, 12, 20, 35, 60, 100, 175, 300, 500, 900)


def mean_pairwise_corr(corr: pd.DataFrame, cols: List[str]) -> float:
    """Mean off-diagonal correlation for *cols*, read off a precomputed matrix."""
    if len(cols) < 2:
        return float("nan")
    m = corr.loc[cols, cols].values
    iu = np.triu_indices_from(m, k=1)
    vals = m[iu]
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if vals.size else float("nan")


def calibrate(corr: pd.DataFrame, rng: np.random.Generator) -> Dict[int, tuple]:
    """Random-basket mean and sd at a ladder of sizes."""
    cols = list(corr.columns)
    out: Dict[int, tuple] = {}
    for size in CALIBRATION_SIZES:
        if size > len(cols):
            continue
        draws = [
            mean_pairwise_corr(corr, list(rng.choice(cols, size=size, replace=False)))
            for _ in range(N_DRAWS)
        ]
        out[size] = (float(np.nanmean(draws)), float(np.nanstd(draws)))
        logger.debug("n=%d random=%.4f sd=%.5f", size, *out[size])
    return out


def interpolate(cal: Dict[int, tuple], n: int) -> tuple:
    sizes = sorted(cal)
    nearest = min(sizes, key=lambda s: abs(s - n))
    return cal[nearest]


def run(panel: pd.DataFrame) -> List[Dict[str, Any]]:
    universe = load_universe()
    holdings = load_holdings()
    returns = panel.drop(columns=[BENCH], errors="ignore").pct_change()
    returns = returns.dropna(how="all")
    # min_periods: two names that only overlap a few weeks produce a
    # correlation that is noise. Pairs below this become NaN and are dropped
    # from the mean rather than quietly dragging it toward zero.
    corr = returns.corr(min_periods=MIN_OVERLAP)
    available = set(corr.columns)

    rng = np.random.default_rng(SEED)
    cal = calibrate(corr, rng)

    rows: List[Dict[str, Any]] = []
    for theme in taxonomy.THEMES:
        if theme.method == "proxy":
            continue  # one fund has no internal cohesion to measure

        members = [str(m["ticker"]) for m in
                   resolve_theme_members(theme, universe, holdings)
                   if m.get("ticker")]
        present = sorted(set(members) & available)
        kind = "factor" if theme.method == "rule" else "business"

        row: Dict[str, Any] = {
            "theme": theme.name, "source": theme.source, "kind": kind,
            "n": len(present), "listed": len(set(members)),
            # Coverage is reported on every row. The previous run omitted it
            # and reported verdicts computed on a median ~50% of each theme's
            # members -- a theme of recent listings was judged on its oldest
            # survivors.
            "coverage": len(present) / max(len(set(members)), 1),
            "within": None, "random": None,
            "excess": None, "noise": None, "verdict": None,
        }

        if len(present) < MIN_MEMBERS:
            row["verdict"] = "too few in panel"
            rows.append(row)
            continue

        within = mean_pairwise_corr(corr, present)
        rnd, sd = interpolate(cal, len(present))
        excess = within - rnd
        row.update({"within": within, "random": rnd, "excess": excess, "noise": sd})

        if kind == "factor":
            # Definitional grouping -- co-movement is not the claim it makes.
            row["verdict"] = "definitional"
        elif excess >= REAL_THRESHOLD:
            row["verdict"] = "real"
        elif excess >= WEAK_THRESHOLD:
            row["verdict"] = "weak"
        else:
            row["verdict"] = "label"
        rows.append(row)

    rows.sort(key=lambda r: (r["excess"] is None, -(r["excess"] or -9)))
    return rows


def render(rows: List[Dict[str, Any]]) -> str:
    biz = [r for r in rows if r["kind"] == "business" and r["excess"] is not None]
    fac = [r for r in rows if r["kind"] == "factor" and r["excess"] is not None]
    thin = [r for r in rows if r["excess"] is None]
    real = [r for r in biz if r["verdict"] == "real"]
    weak = [r for r in biz if r["verdict"] == "weak"]
    label = [r for r in biz if r["verdict"] == "label"]

    out = [
        "# Taxonomy validation — is each theme a real grouping?",
        "",
        "A business theme claims its members share a driver, so they should "
        "co-move more than a size-matched random basket from the same pool. "
        "`excess` is that difference in mean pairwise correlation.",
        "",
        f"**Business themes: {len(real)} real · {len(weak)} weak · "
        f"{len(label)} label** (thresholds: real >= +{REAL_THRESHOLD:.2f}, "
        f"weak >= +{WEAK_THRESHOLD:.2f})",
        "",
        f"Factor themes ({len(fac)}) are reported but not scored — see below. "
        f"{len(thin)} themes had too few names in the panel.",
        "",
        "**`cov` is the share of a theme's members present in the price panel.** "
        "A verdict computed on half a theme is a verdict on half a theme; "
        "rows below 75% are flagged and should be read as provisional.",
        "",
        "## Business themes",
        "",
        "| Theme | src | n | cov | within | random | **excess** | noise | verdict |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in biz:
        flag = " ⚠️" if r["coverage"] < 0.75 else ""
        out.append(f"| {r['theme']} | {r['source']} | {r['n']}/{r['listed']} | "
                   f"{100*r['coverage']:.0f}%{flag} | {r['within']:.3f} | "
                   f"{r['random']:.3f} | **{r['excess']:+.3f}** | ±{r['noise']:.3f} | "
                   f"{r['verdict']} |")

    out += [
        "", "## Factor themes — not scored, and why", "",
        "These group names by a *property*, not a shared driver. A microcap "
        "biotech and a microcap miner have a number in common and nothing "
        "else, so low internal correlation is the expected result, not a "
        "failure. The rule either selects what it says it selects — which the "
        "unit tests check — or it does not.",
        "",
        "| Theme | src | n | within | random | excess |",
        "|---|---|---|---|---|---|",
    ]
    for r in fac:
        out.append(f"| {r['theme']} | {r['source']} | {r['n']} | {r['within']:.3f} | "
                   f"{r['random']:.3f} | {r['excess']:+.3f} |")

    if label:
        out += ["", "## Business themes that failed", "",
                "These group names that do not co-move. Either the membership "
                "is wrong, or the market does not trade the concept as a unit.",
                ""]
        for r in label:
            out.append(f"- **{r['theme']}** ({r['source']}, n={r['n']}, "
                       f"excess {r['excess']:+.3f})")

    out += ["", "## Method note", "",
            "An earlier version scored everything as `z = excess / sd`. The sd "
            "of random baskets falls from 0.064 at n=5 to 0.0037 at n=985, so "
            "z rewarded small themes and punished large ones regardless of "
            "quality — High Beta Factor scored z=-12.4 on an excess of only "
            "-0.046. The random mean is flat at ~0.252 across every size, so "
            "the excess is comparable and z was not."]
    return "\n".join(out)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    argparse.ArgumentParser(description=__doc__).parse_args()

    panel = load_panel()
    rows = run(panel)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(rows))

    VERDICTS.write_text(json.dumps({
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "panel": {
            "sessions": int(panel.shape[0]),
            "tickers": int(panel.shape[1]),
            "first": str(panel.index[0].date()),
            "last": str(panel.index[-1].date()),
        },
        "thresholds": {"real": REAL_THRESHOLD, "weak": WEAK_THRESHOLD},
        "themes": {
            r["theme"]: {
                "verdict": r["verdict"], "kind": r["kind"],
                "excess": None if r["excess"] is None else round(r["excess"], 4),
                "n": r["n"], "coverage": round(r["coverage"], 3),
            } for r in rows
        },
    }, indent=2))
    logger.info("wrote %s", VERDICTS)

    biz = [r for r in rows if r["kind"] == "business" and r["excess"] is not None]
    for v in ("real", "weak", "label"):
        logger.info("%-6s %d", v, sum(1 for r in biz if r["verdict"] == v))
    logger.info("wrote %s", OUT)


if __name__ == "__main__":
    main()
