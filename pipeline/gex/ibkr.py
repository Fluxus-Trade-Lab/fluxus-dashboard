# pipeline/gex/ibkr.py
"""All IBKR I/O for the GEX engine. Rules encoded here:
- LOW clientIds only (high IDs hang TWS after repeated sessions).
- Ports tried in order: IB Gateway live (4001), paper (4002), TWS (7496).
- SPX spot falls back to SPY*10 when the CBOE index quote is missing.
- QQQ: only request strikes that qualify (chain lists phantom .5 strikes).
"""
import math
import pandas as pd
from ib_async import IB, Stock, Index, Option, ContFuture

PORTS = (4001, 4002, 7496)
CLIENT_ID = 9
CHAIN_WIDTH = 0.025          # +/-2.5% of spot: keeps a tenor under ~200 contracts
# so successive tenors' reqMktData subscriptions stay within IBKR's per-session
# pacing envelope. Above ~200 contracts per tenor, greek coverage on the
# 2nd+ tenor drops from ~100% to <30% and never recovers within our settle
# windows. Meaningful walls almost always cluster within +/-1% of spot anyway.
# OI ticks stream over 10-15s in LIVE mode; give them time to arrive.
OI_SETTLE_SECONDS = 15
GREEKS_SETTLE_SECONDS = 5
# Market-data type: 1=live (RTH only), 2=frozen (last settle — works pre-open),
# 3=delayed, 4=delayed-frozen. Neither mode alone gives both fields off-hours:
# LIVE delivers OI (static clearing data, 60/60 verified weekend) but greeks are
# dark; FROZEN delivers greeks/IV/price snapshot (60/60) but OI ticks stall at
# ~2/60. So pull_chain requests both — LIVE first for OI, then FROZEN for greeks.
MDT_LIVE, MDT_FROZEN = 1, 2

INSTRUMENTS = {
    "SPX": dict(kind="index", exch="CBOE", tclass="SPXW", strike_step=5,
                multiplier=100),
    "QQQ": dict(kind="stock", exch="SMART", tclass="QQQ", strike_step=1,
                multiplier=100),
}


def _num(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _first(*vals):
    for v in vals:
        if _num(v) is not None:
            return float(v)
    return None


def connect(client_id: int = CLIENT_ID, market_data_type: int = MDT_FROZEN) -> IB:
    """Connect and set the market-data type.

    Default is FROZEN (2) so the 8am ET run gets the prior settle's greeks/IV
    even before the options market opens. Pass `market_data_type=MDT_LIVE` for
    intraday pulls when live quotes are desired.
    """
    last = None
    for port in PORTS:
        try:
            ib = IB()
            ib.connect("127.0.0.1", port, clientId=client_id, timeout=15)
            ib.reqMarketDataType(market_data_type)
            return ib
        except Exception as e:      # noqa: BLE001 — try next port
            last = e
    raise ConnectionError(f"no IBKR endpoint on ports {PORTS}: {last}")


def underlier(symbol: str):
    cfg = INSTRUMENTS[symbol]
    return (Index(symbol, cfg["exch"], "USD") if cfg["kind"] == "index"
            else Stock(symbol, "SMART", "USD"))


def get_spot(ib: IB, symbol: str) -> float | None:
    u = underlier(symbol)
    ib.qualifyContracts(u)
    t = ib.reqTickers(u)[0]
    spot = _first(t.last, t.marketPrice(), t.close)
    if spot is None and symbol == "SPX":          # no CBOE index sub
        spy = Stock("SPY", "SMART", "USD")
        ib.qualifyContracts(spy)
        ts = ib.reqTickers(spy)[0]
        s = _first(ts.last, ts.marketPrice(), ts.close)
        spot = s * 10 if s else None
    return spot


def get_bases(ib: IB) -> dict:
    """Live conversion anchors: ES-SPX basis and NQ/QQQ ratio."""
    out = {}
    try:
        es = ContFuture("ES", "CME"); ib.qualifyContracts(es)
        spx = get_spot(ib, "SPX")
        t = ib.reqTickers(es)[0]
        esp = _first(t.last, t.marketPrice(), t.close)
        if esp and spx:
            out["ES_minus_SPX"] = round(esp - spx, 1)
    except Exception:                               # noqa: BLE001
        pass
    try:
        nq = ContFuture("NQ", "CME"); ib.qualifyContracts(nq)
        t = ib.reqTickers(nq)[0]
        nqp = _first(t.last, t.marketPrice(), t.close)
        qq = get_spot(ib, "QQQ")
        if nqp and qq:
            out["NQ_over_QQQ"] = round(nqp / qq, 3)
    except Exception:                               # noqa: BLE001
        pass
    return out


def get_expirations(ib: IB, symbol: str) -> list[str]:
    cfg = INSTRUMENTS[symbol]
    u = underlier(symbol)
    ib.qualifyContracts(u)
    sec = "IND" if cfg["kind"] == "index" else "STK"
    chains = ib.reqSecDefOptParams(u.symbol, "", sec, u.conId)
    ch = next((c for c in chains
               if c.tradingClass == cfg["tclass"]
               and c.exchange in ("SMART", cfg["exch"])), chains[0])
    return sorted(ch.expirations), ch


def pull_chain(ib: IB, symbol: str, expiry: str, spot: float, chain=None) -> pd.DataFrame:
    cfg = INSTRUMENTS[symbol]
    ch = chain if chain is not None else get_expirations(ib, symbol)[1]  # reuse if caller has it
    lo, hi = spot * (1 - CHAIN_WIDTH), spot * (1 + CHAIN_WIDTH)
    step = cfg["strike_step"]
    strikes = sorted(k for k in ch.strikes
                     if lo <= k <= hi and float(k) == float(int(k // step) * step))
    opts = [Option(symbol, expiry, k, r, "SMART", tradingClass=cfg["tclass"])
            for k in strikes for r in ("C", "P")]
    opts = [o for o in ib.qualifyContracts(*opts) if getattr(o, "conId", None)]
    # Two-phase pull through a SINGLE reqMktData stream per contract:
    #   phase 1: LIVE mode  -> stream delivers OI ticks (100/101)
    #   phase 2: FROZEN     -> same stream delivers last-settle modelGreeks + price
    # A separate reqTickers call would open a second (snapshot) subscription per
    # contract; across 6 tenors x 200 contracts that piles up faster than
    # cancelMktData clears, causing greek coverage to degrade monotonically.
    ib.reqMarketDataType(MDT_LIVE)
    handles = [ib.reqMktData(o, "100,101", False, False) for o in opts]
    try:
        ib.sleep(OI_SETTLE_SECONDS)                     # ~15s: OI populates
        ib.reqMarketDataType(MDT_FROZEN)                # same streams now → frozen
        ib.sleep(GREEKS_SETTLE_SECONDS)                 # ~5s: greeks + close populate
        rows = []
        for o, t in zip(opts, handles):
            mg = t.modelGreeks
            rows.append(dict(
                strike=float(o.strike), right=o.right,
                gamma=_num(mg.gamma) if mg else None,
                iv=_num(mg.impliedVol) if mg else None,
                mid=_num(t.marketPrice()) or _num(t.close),   # close fallback pre-open
                oi=_num(t.callOpenInterest if o.right == "C" else t.putOpenInterest),
            ))
    finally:                                            # M1: never leak market-data lines
        for o in opts:
            ib.cancelMktData(o)
    return pd.DataFrame(rows)


if __name__ == "__main__":                          # manual smoke: needs IBKR up
    ib = connect()
    for sym in INSTRUMENTS:
        spot = get_spot(ib, sym)
        exps, _ = get_expirations(ib, sym)
        print(f"{sym}: spot={spot} expiries[:3]={exps[:3]}")
    print("bases:", get_bases(ib))
    ib.disconnect()
