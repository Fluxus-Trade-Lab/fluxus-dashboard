# pipeline/gex/engine.py
"""Orchestrator: pull → compute → derive → schema → write → render → publish."""
import argparse
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.gex import compute, derive, render, schema

OUT_DIR = Path("data/gex")
INSTR_MULT = {"SPX": 100, "QQQ": 100}


def _prior_doc(out_dir: Path, today_tag: str):
    older = sorted(p for p in out_dir.glob("gex_*.json") if today_tag not in p.name)
    if not older:
        return None
    try:
        return json.loads(older[-1].read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _convert(sym: str, tenor: dict, bases: dict) -> dict:
    lv = {k: tenor.get(k) for k in ("flip", "put_wall", "call_wall", "pin")}
    out = {}
    if sym == "SPX":
        b = bases.get("ES_minus_SPX")
        if b is not None:
            out["ES"] = {k: (v + b if v is not None else None) for k, v in lv.items()}
        out["SPY"] = {k: (round(v / 10, 1) if v is not None else None)
                      for k, v in lv.items()}
    if sym == "QQQ":
        r = bases.get("NQ_over_QQQ")
        if r is not None:
            out["NQ"] = {k: (round(v * r) if v is not None else None)
                         for k, v in lv.items()}
    return out


def _assemble(chains: dict, spots: dict, bases: dict,
              out_dir: Path, today: date) -> dict:
    today_tag = today.strftime("%Y%m%d")
    prior = _prior_doc(out_dir, today_tag)
    instruments, primary = {}, None
    for sym, tenors in chains.items():
        spot = spots[sym]
        tdocs = {}
        for tname, (expiry, df) in tenors.items():
            if df is None:
                tdocs[tname] = None
                continue
            m = compute.compute_tenor(df, spot=spot, multiplier=INSTR_MULT[sym])
            m["expiry"] = expiry
            prior_t = None
            if prior:
                prior_t = (prior.get("instruments", {}).get(sym, {})
                           .get("tenors", {}).get(tname))
            m["delta_vs_prior"] = derive.wall_migration(m, prior_t)
            m["converted"] = _convert(sym, m, bases)
            tdocs[tname] = m
        instruments[sym] = {"spot": round(spot, 2), "basis": bases,
                            "tenors": tdocs}
        if sym == "SPX" and tdocs.get("swing"):
            primary = tdocs["swing"]

    regime = derive.regime_of(primary["net_gex_mm"] if primary else None)
    opex = derive.opex_flag(today)
    plan = derive.build_plan(
        regime=regime,
        flip=primary.get("flip") if primary else None,
        put_wall=primary.get("put_wall") if primary else None,
        call_wall=primary.get("call_wall") if primary else None,
        pin=primary.get("pin") if primary else None,
        opex=opex,
        migration=primary.get("delta_vs_prior") if primary else None)
    read = {"regime": regime,
            "bull": [f"net GEX {primary['net_gex_mm']:+,.0f} $mm — dips get bought"]
                    if regime == "positive" and primary else [],
            "bear": [f"net GEX {primary['net_gex_mm']:+,.0f} $mm — moves amplify"]
                    if regime == "negative" and primary else [],
            "plan": plan}
    fit = derive.strategy_fit(regime,
                              primary.get("atm_iv") if primary else None)
    return schema.build_document(
        asof=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        stale=False, stale_reason=None, opex=opex, instruments=instruments,
        read=read, strategy_fit=fit)


def _write(doc: dict, out_dir: Path, today: date) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = today.strftime("%Y%m%d")
    (out_dir / f"gex_{tag}.json").write_text(json.dumps(doc, indent=1))
    (out_dir / "latest.json").write_text(json.dumps(doc, indent=1))
    html = render.render_brief(doc)
    (out_dir / f"brief_{tag}.html").write_text(html)
    (out_dir / "latest.html").write_text(html)


def _mark_stale(out_dir: Path, reason: str, today: date) -> None:
    latest = out_dir / "latest.json"
    if not latest.exists():
        return
    doc = json.loads(latest.read_text())
    doc["stale"], doc["stale_reason"] = True, reason
    _write(doc, out_dir, today)


def _git_publish(out_dir: Path, today: date, push: bool) -> None:
    try:
        subprocess.run(["git", "add", str(out_dir)], check=True)
        subprocess.run(["git", "commit", "-m",
                        f"chore(gex): daily gex data {today.isoformat()}"],
                       check=True)
        if push:
            subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[gex] git publish skipped/failed: {e}")  # never kill the run


def run(out_dir=OUT_DIR, offline_fixture=None, offline_spot=None,
        do_git=True, push=True) -> dict:
    out_dir = Path(out_dir)
    today = date.today()
    try:
        if offline_fixture:
            df = pd.read_csv(offline_fixture)
            expiry = "20260717"
            chains = {"SPX": {t: (expiry, df) for t in ("front", "swing", "monthly")}}
            spots = {"SPX": offline_spot}
            bases = {"ES_minus_SPX": 53.0}
        else:
            from pipeline.gex import ibkr
            ib = ibkr.connect()
            try:
                chains, spots = {}, {}
                bases = ibkr.get_bases(ib)
                for sym in ibkr.INSTRUMENTS:
                    spot = ibkr.get_spot(ib, sym)
                    if spot is None:                    # I2: skip instrument, don't kill run
                        print(f"[gex] no spot for {sym} — skipping instrument")
                        continue
                    exps, ch = ibkr.get_expirations(ib, sym)
                    tmap = derive.select_tenors(exps, today)
                    tenors = {}
                    for t, e in tmap.items():
                        if not e:
                            tenors[t] = (None, None)
                            continue
                        try:                            # I1: one tenor failing must not torch the rest
                            tenors[t] = (e, ibkr.pull_chain(ib, sym, e, spot, chain=ch))
                        except Exception as ex:         # noqa: BLE001
                            print(f"[gex] {sym} {t} ({e}) pull failed: {ex}")
                            tenors[t] = (None, None)
                    chains[sym] = tenors
                    spots[sym] = spot
                if not chains:                          # total failure → stale path
                    raise RuntimeError("no instruments pulled successfully")
            finally:
                ib.disconnect()
        doc = _assemble(chains, spots, bases, out_dir, today)
        schema.validate(doc)
        _write(doc, out_dir, today)
        if do_git:
            _git_publish(out_dir, today, push)
        return {"ok": True}
    except Exception as e:                          # noqa: BLE001
        print(f"[gex] RUN FAILED: {e}")
        _mark_stale(out_dir, f"{type(e).__name__}: {e}", today)
        if do_git:
            _git_publish(out_dir, today, push)
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--offline-fixture")
    ap.add_argument("--offline-spot", type=float)
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    result = run(out_dir=a.out, offline_fixture=a.offline_fixture,
                 offline_spot=a.offline_spot, do_git=not a.no_git,
                 push=not a.no_push)
    raise SystemExit(0 if result["ok"] else 1)
