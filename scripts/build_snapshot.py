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
import datetime as dt
import glob
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference.render import render_snapshot_html, render_snapshot_md


def _auction_join(g: dict) -> dict:
    """Attach the auction framework, when a profile exists for a recent session.

    The newest profile no older than 5 calendar days is used — yesterday's
    auction structure is exactly what today trades against. Missing profile
    means the brief simply lacks the section; it never fabricates one.
    """
    from pipeline.profile import synthesis as SY
    empty = {"todays_business": None, "reference_map": None,
             "strongest": None, "conflicts": None, "profile_source": None}
    files = sorted(Path("data/profile").glob("profile_*.json"))
    if not files:
        return empty
    latest = files[-1]
    data_day = (g.get("generated_at") or "")[:10]
    prof_day = latest.stem.split("_")[1]
    prof_iso = f"{prof_day[:4]}-{prof_day[4:6]}-{prof_day[6:]}"
    if data_day and prof_iso:
        gap = abs((dt.date.fromisoformat(data_day)
                   - dt.date.fromisoformat(prof_iso)).days)
        if gap > 5:
            return empty
    try:
        prof = json.loads(latest.read_text())
    except (json.JSONDecodeError, OSError):
        return empty
    rows = SY.reference_map(SY.auction_levels(prof), SY.options_levels(g))
    return {"todays_business": SY.todays_business(prof, g),
            "reference_map": rows,
            "strongest": SY.strongest(rows),
            "conflicts": SY.conflicts(prof, g),
            # Conflicts without a resolution are a shrug. The precedence rule
            # says the auction is root cause and the dealer book is mechanism.
            "resolution": SY.resolve(prof, g),
            "profile_source": str(latest)}


def _transition(symbol: str) -> dict | None:
    """The GEX series read as a state move, not as a number.

    The level is what we have always published; the source's fifteen-year test
    says the level is mostly noise and the transition is the signal. This makes
    the transition visible. It does not make it tested — see the note it carries.
    """
    from pipeline.reference import levels_log as LL
    from pipeline.reference import transitions as TR
    per = LL.last_entry_per_day(LL.read(), symbol)
    ser = [(k, per[k]["total_gex"] / 1e9) for k in sorted(per)
           if per[k].get("total_gex") is not None]
    rows = TR.transitions(ser)
    if not rows:
        return None
    out = TR.summary(rows)
    out["recent"] = rows[-5:]
    return out


def _flow_ratio(g: dict) -> dict | None:
    """Today's flow against standing positioning, per strike.

    Only present when the volume-weighted series is — outside RTH the option
    volume fields are empty, and a ratio against nothing is not a zero reading.
    """
    from pipeline.gex import flow_ratio as FR
    vol = g.get("per_strike_gex_volume")
    if not vol:
        return None
    oi = {float(k): v for k, v in (g.get("per_strike_gex") or {}).items()}
    rows = FR.flow_ratio(oi, {float(k): v for k, v in vol.items()})
    if not rows:
        return None
    out = FR.summary(rows)
    out["rows"] = FR.hot_strikes(rows)[:8]
    return out


def _consistency(g: dict) -> dict | None:
    """Replicate every published number by a second route and report drift.

    Runs on every brief, not on demand: a check that has to be remembered is a
    check that fires the day nobody ran it.
    """
    from pipeline.reference import consistency as C
    checks = C.gex_checks(g)
    files = sorted(Path("data/profile").glob("profile_*.json"))
    if files:
        try:
            checks += C.profile_checks(json.loads(files[-1].read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    run = C.run(checks)
    run["checks"] = checks
    return run


def _scorecard(symbol: str) -> dict | None:
    """Our published levels, graded. Missing file is not an error — the brief
    simply omits the block rather than implying a record we have not earned."""
    p = Path("data/reference") / f"scorecard_{symbol}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text()).get("summary")
    except (json.JSONDecodeError, OSError):
        return None
from pipeline.reference.context import percentile_of, ranked_levels, load_history
from pipeline.gex.derive import wall_migration
from pipeline.reference import levels_log as LL
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
                    # Outside RTH the close itself can be NaN; NaN would ride
                    # through the sum and crash at round(). Missing is missing.
                    if mid is not None and not math.isnan(mid):
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
    ap.add_argument("--no-log", action="store_true", help="Do not append to the levels log.")
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
    # Confluence: same-signed and both loaded (mirrors the chart threshold).
    gx = {float(k): float(v) for k, v in (g.get("per_strike_gex") or {}).items()}
    ch = {float(k): float(v) for k, v in (g.get("per_strike_charm") or {}).items()}
    confluence = []
    if gx and ch:
        gm = max(abs(v) for v in gx.values()) or 1.0
        cm = max(abs(v) for v in ch.values()) or 1.0
        confluence = [k for k in gx if k in ch and gx[k] * ch[k] > 0
                      and abs(gx[k]) >= 0.4 * gm and abs(ch[k]) >= 0.4 * cm]

    g.setdefault("symbol", args.symbol)
    now = market_now()
    date_tag = now.strftime("%Y%m%d")

    # Append-only record BEFORE rendering: what we believed at this moment.
    if not args.no_log:
        LL.append(LL.entry_from(g, symbol=args.symbol, confluence=confluence))
    # Keyed on the DATA's session, not today: a brief built from Friday's chain
    # should show Friday's sequence, not an empty Monday.
    data_day = (g.get("generated_at") or now.isoformat())[:10]
    seq = LL.intraday_sequence(LL.read(), data_day, args.symbol)

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
        "confluence": sorted(confluence),
        "intraday_sequence": seq,
        "scorecard": _scorecard(args.symbol),
        "consistency": _consistency(g),
        "flow_ratio": _flow_ratio(g),
        "gex_transition": _transition(args.symbol),
        **_auction_join(g),
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
