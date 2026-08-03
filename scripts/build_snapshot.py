#!/usr/bin/env python3
"""Build a dated daily market snapshot: GEX rails + expected move + VIX.

Assembles from the GEX JSON already written by gex_levels.py (always present)
and, when TWS is up, adds the near-term ATM-straddle expected move and the VIX
term structure. Writes data/snapshots/snapshot_<SYMBOL>_<YYYYMMDD>.{json,html}.
Degrades gracefully: no TWS -> GEX-only snapshot, clearly marked.

Usage:
    .venv/bin/python scripts/build_snapshot.py --symbol SPX
    .venv/bin/python scripts/build_snapshot.py --gex data/gex/gex_SPX_20260722.json
"""
import argparse
import glob
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference.render import render_snapshot_html, render_snapshot_md
from pipeline.reference.context import percentile_of, ranked_levels, load_history
from pipeline.gex.derive import wall_migration
from pipeline.marketcal import market_now

OUT_DIR = Path("data/snapshots")
GEX_DIR = Path("data/gex")


def _latest_gex(symbol: str) -> Path:
    files = sorted(glob.glob(str(GEX_DIR / f"gex_{symbol}_2*.json")))
    if not files:
        sys.exit(f"no GEX json found in {GEX_DIR} for {symbol} — run gex_levels.py first")
    return Path(files[-1])


def _try_live(symbol: str, spot: float):
    """Return (expected_move, vix) or (None, None) if TWS is unreachable."""
    try:
        from ib_async import IB, Index, Option
    except Exception:
        return None, None
    ib = IB()
    connected = False
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=93, timeout=6)
            connected = True
            break
        except Exception:
            continue
    if not connected:
        return None, None
    try:
        ib.reqMarketDataType(1)
        # VIX term structure
        vix = {}
        for sym, key in (("VIX", "vix"), ("VIX3M", "vix3m")):
            c = Index(sym, "CBOE"); ib.qualifyContracts(c)
            t = ib.reqMktData(c, "", False, False); ib.sleep(2)
            v = t.last if (t.last and not math.isnan(t.last)) else t.close
            if v and not math.isnan(v):
                vix[key] = round(float(v), 2)
        vix = vix if len(vix) == 2 else None

        # near-term ATM straddle expected move (0DTE + 1DTE), SPX only
        em = None
        if symbol == "SPX":
            params = ib.reqSecDefOptParams("SPX", "", "IND", ib.qualifyContracts(Index("SPX", "CBOE"))[0].conId)
            exps = sorted({e for p in params for e in p.expirations})
            today = market_now().strftime("%Y%m%d")
            fwd = [e for e in exps if e >= today][:2]
            atm = round(spot / 25) * 25
            em = []
            labels = ["0DTE", "1DTE"]
            for i, exp in enumerate(fwd):
                tc = next((p.tradingClass for p in params if exp in p.expirations), "SPXW")
                legs = {}
                for r in ("C", "P"):
                    o = Option("SPX", exp, atm, r, "CBOE", tradingClass=tc)
                    try:
                        ib.qualifyContracts(o)
                    except Exception:
                        continue
                    if not o.conId:
                        continue
                    t = ib.reqMktData(o, "", False, False); ib.sleep(1.6)
                    mid = (t.bid + t.ask) / 2 if (t.bid and t.ask and t.bid > 0 and t.ask > 0) else t.close
                    legs[r] = mid
                if legs.get("C") and legs.get("P"):
                    s = legs["C"] + legs["P"]
                    em.append({"label": labels[i] if i < len(labels) else f"exp{i}",
                               "expiry": exp, "pts": round(s, 1),
                               "pct": round(100 * s / spot, 2),
                               "low": round(spot - s), "high": round(spot + s)})
            em = em or None
        return em, vix
    finally:
        ib.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--gex", help="Explicit GEX json path (default: latest for symbol).")
    ap.add_argument("--no-live", action="store_true", help="Skip the IBKR EM/VIX pull.")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gex_path = Path(args.gex) if args.gex else _latest_gex(args.symbol)
    g = json.loads(gex_path.read_text())

    # Prior sessions, oldest->newest, for the percentile and the day-over-day walls.
    prior_docs = []
    for p in sorted(glob.glob(str(GEX_DIR / f"gex_{args.symbol}_2*.json"))):
        if Path(p) == gex_path:
            continue
        try:
            prior_docs.append(json.loads(Path(p).read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    gex_pct = percentile_of(g.get("total_gex"), load_history(prior_docs)) \
        if g.get("total_gex") is not None else None
    prior = prior_docs[-1] if prior_docs else None
    migration = wall_migration(
        {"call_wall": g.get("call_wall"), "put_wall": g.get("put_wall"),
         "flip": g.get("zero_gamma_flip")},
        {"call_wall": prior.get("call_wall"), "put_wall": prior.get("put_wall"),
         "flip": prior.get("zero_gamma_flip")} if prior else None)
    ladder = ranked_levels(
        {float(k): float(v) for k, v in (g.get("per_strike_gex") or {}).items()},
        spot=g.get("spot") or 0,
        exclude={g.get("call_wall"), g.get("put_wall"), g.get("pin_strike")},
        n=7) if g.get("per_strike_gex") and g.get("spot") else []
    g.setdefault("symbol", args.symbol)
    now = market_now()
    date_tag = now.strftime("%Y%m%d")

    em, vix = (None, None) if args.no_live else _try_live(args.symbol, g.get("spot") or 0)
    snap = {
        "symbol": args.symbol,
        "date": now.strftime("%Y-%m-%d"),
        "generated_at": now.isoformat(timespec="seconds"),
        "gex_source": str(gex_path),
        "gex": g,
        "expected_move": em,
        "vix": vix,
        "gex_percentile": gex_pct,
        "wall_migration": migration,
        "secondary_levels": ladder,
        "prior_session": prior.get("generated_at") if prior else None,
    }
    jp = OUT_DIR / f"snapshot_{args.symbol}_{date_tag}.json"
    hp = OUT_DIR / f"snapshot_{args.symbol}_{date_tag}.html"
    mp = OUT_DIR / f"snapshot_{args.symbol}_{date_tag}.md"
    jp.write_text(json.dumps(snap, indent=2))
    hp.write_text(render_snapshot_html(snap))
    mp.write_text(render_snapshot_md(snap))
    live = "live EM+VIX" if (em and vix) else ("partial" if (em or vix) else "GEX-only (TWS down)")
    print(f"snapshot [{live}]: {jp}\n                   {hp}\n                   {mp}")
    print(f"  GEX from {gex_path.name}: regime {g.get('regime')}, "
          f"call {g.get('call_wall')} / flip {g.get('zero_gamma_flip')} / put {g.get('put_wall')}")


if __name__ == "__main__":
    main()
