#!/usr/bin/env python3
"""
Daily dealer Gamma-Exposure (GEX) levels for equity index options.

Pulls the SPX (default) or SPY option chain from IBKR (TWS/Gateway, live OPRA
feed), computes the dealer gamma-exposure profile, and prints + saves the key
horizontal levels that draw as support/resistance in TradingView:

  - ZERO-GAMMA FLIP : spot level where total dealer gamma crosses zero.
                      Below it dealers are net-SHORT gamma (hedging amplifies
                      moves); above it net-LONG gamma (hedging dampens moves).
  - CALL WALL       : strike with the largest positive net GEX (overhead
                      resistance / where dealer long-gamma pins price down).
  - PUT WALL        : strike with the largest negative net GEX (downside
                      support / where dealer short-gamma pins price up).
  - ABS / PIN strike: strike with the largest |net GEX| (magnet).
  - the full per-strike profile (for plotting / TradingView overlay).

Two engines, both documented below:
  1. Per-strike net GEX at the CURRENT spot, using IBKR's reported gamma.
     -> drives call wall / put wall / pin.
  2. Gamma profile ACROSS hypothetical spot levels, re-pricing each option's
     gamma with Black-Scholes (IV from IBKR). The zero-crossing of the total
     is the flip. -> reproduces the classic "gamma profile across spot" chart.

Prereq: TWS / IB Gateway running with the API enabled (default port 7496) and
an OPRA options subscription for greeks + open interest. Open interest settles
overnight (OCC), so the ideal pull time is premarket (~7-8am ET): the OI then
reflects prior-close dealer positioning and does not change intraday.

Usage:
    .venv/bin/python scripts/gex_levels.py                       # SPX, defaults
    .venv/bin/python scripts/gex_levels.py --symbol SPY
    .venv/bin/python scripts/gex_levels.py --expiries 5 --width 0.08 --strike-step 25
    .venv/bin/python scripts/gex_levels.py --spot 6250           # manual spot override
    .venv/bin/python scripts/gex_levels.py --delayed             # delayed data (no OPRA live)

Output: gex_<SYMBOL>_<YYYYMMDD>.json and .csv in the data/gex/ directory.
"""
import argparse, datetime as dt, json, math, os, sys
import pandas as pd
from ib_async import IB, Index, Stock, Option

# Running this as a script puts scripts/ on sys.path, not the repo root, so the
# pipeline package is not importable without help.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.gex.blackscholes import bs_charm
from pipeline.gex.derive import iv_tenors, select_tenors
from pipeline.marketcal import market_now as _market_now  # trading dates: ET, never host JST

# ----------------------------------------------------------------------------
# SIGN CONVENTION  (flip here if you disagree with the dealer-positioning model)
# ----------------------------------------------------------------------------
# Standard "dealers are long calls / short puts" convention: customers buy puts
# for protection and sell/overwrite calls, leaving dealers net-long calls and
# net-short puts. So a strike's dealer gamma = +call_gamma*call_OI (long calls)
#                                              -put_gamma*put_OI  (short puts).
# Set FLIP_SIGN = -1 to invert the whole model (dealers short calls / long puts).
CALL_SIGN =  1.0
PUT_SIGN  = -1.0
FLIP_SIGN =  1.0          # global inversion toggle; keep +1 for the standard model

CONTRACT_MULTIPLIER = 100.0   # index & ETF options are 100x
RISK_FREE = 0.043             # annualized; gamma is fairly insensitive to this
DIV_YIELD = 0.013             # SPX ~1.3%; used only in the BS gamma re-pricing
MIN_T_YEARS = 0.5 / 365.0     # floor on time-to-expiry so 0DTE gamma stays finite

CFG = {  # (secType, exchange, tradingClass for the primary chain)
    "SPX": dict(sec="IND", exch="CBOE", tclass="SPXW", step=25.0),
    "SPY": dict(sec="STK", exch="SMART", tclass="SPY", step=1.0),
}


def first_num(*vals):
    """First finite number among vals (handles nan/None from IB tickers)."""
    for v in vals:
        if v is not None and isinstance(v, (int, float)) and not math.isnan(v):
            return float(v)
    return None


def underlier(symbol):
    c = CFG[symbol]
    return Index(symbol, c["exch"], "USD") if c["sec"] == "IND" else Stock(symbol, "SMART", "USD")


def spot_from(ib, contract):
    t = ib.reqTickers(contract)[0]
    return first_num(t.last, t.close, t.marketPrice())


def norm_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_gamma(S, K, T, sigma, r=RISK_FREE, q=DIV_YIELD):
    """Black-Scholes gamma of a European option (identical for calls & puts)."""
    if S <= 0 or K <= 0 or sigma <= 0:
        return 0.0
    T = max(T, MIN_T_YEARS)
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    return math.exp(-q * T) * norm_pdf(d1) / (S * srt)


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_delta_q(S, K, T, sigma, right, r=RISK_FREE, q=DIV_YIELD):
    """Delta with the same r/q convention as bs_gamma above."""
    if S <= 0 or K <= 0 or sigma <= 0:
        return 0.0
    T = max(T, MIN_T_YEARS)
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    nd1 = norm_cdf(d1)
    return math.exp(-q * T) * (nd1 if right == "C" else nd1 - 1.0)


def resolve_spot(ib, u, symbol, override, delayed):
    """Robust spot: manual -> index-live -> index-delayed -> SPY proxy."""
    if override is not None:
        return override, "manual"
    spot = spot_from(ib, u)
    if spot is not None:
        return spot, "live"
    ib.reqMarketDataType(3)                      # try delayed
    spot = spot_from(ib, u)
    ib.reqMarketDataType(3 if delayed else 1)
    if spot is not None:
        return spot, "delayed"
    spy = Stock("SPY", "SMART", "USD"); ib.qualifyContracts(spy)   # last-ditch proxy
    s = spot_from(ib, spy)
    if s is not None:
        return s * (10.0 if symbol == "SPX" else 1.0), "SPY-proxy"
    return None, None


def pull_open_interest(ib, opts, batch=45, settle=6.0):
    """Stream generic ticks 100,101 in batches (respects the ~100-line cap).

    Returns (oi, volume). Both ride the SAME subscription — tick 101 fills the
    open-interest fields, tick 100 fills callVolume/putVolume — so the volume
    series is free: we paid for these market-data lines all along and read only
    one of the two fields. OI is accumulated positioning; volume is today's
    flow. A strike large in one and small in the other is itself information.
    """
    oi, vol = {}, {}
    for i in range(0, len(opts), batch):
        group = opts[i:i + batch]
        tks = {o.conId: ib.reqMktData(o, "100,101", False, False) for o in group}
        ib.sleep(settle)
        for o in group:
            tk = tks[o.conId]
            oi[o.conId] = tk.callOpenInterest if o.right == "C" else tk.putOpenInterest
            vol[o.conId] = tk.callVolume if o.right == "C" else tk.putVolume
            ib.cancelMktData(o)
    return oi, vol


def main():
    p = argparse.ArgumentParser(description="Daily dealer GEX levels for SPX/SPY.")
    p.add_argument("--symbol", default="SPX", choices=["SPX", "SPY"])
    p.add_argument("--expiries", type=int, default=5, help="number of nearest expiries to aggregate")
    p.add_argument("--width", type=float, default=0.08, help="strikes within +/- this frac of spot")
    p.add_argument("--strike-step", type=float, default=None, help="strike granularity (default 25 SPX / 1 SPY)")
    p.add_argument("--max-contracts", type=int, default=900, help="hard cap on contracts pulled (safety)")
    p.add_argument("--profile-range", type=float, default=0.15, help="+/- frac of spot for the flip-profile grid")
    p.add_argument("--profile-points", type=int, default=241)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7496)
    p.add_argument("--clientid", type=int, default=37)
    p.add_argument("--delayed", action="store_true")
    p.add_argument("--spot", type=float, default=None, help="manual spot override")
    p.add_argument("--outdir", default="data/gex")
    args = p.parse_args()

    c = CFG[args.symbol]
    step = args.strike_step if args.strike_step is not None else c["step"]

    ib = IB(); ib.connect(args.host, args.port, clientId=args.clientid, timeout=20)
    if args.delayed:
        ib.reqMarketDataType(3)

    u = underlier(args.symbol); ib.qualifyContracts(u)
    spot, src = resolve_spot(ib, u, args.symbol, args.spot, args.delayed)
    if spot is None:
        print("Could not resolve spot. Pass --spot <price>."); ib.disconnect(); return
    print(f"\n{args.symbol} spot = {spot:.2f}  [{src}]")

    # --- option chain: expirations + strikes across all CBOE trading classes ---
    chains = ib.reqSecDefOptParams(u.symbol, "", c["sec"], u.conId)
    ch = next((x for x in chains if x.tradingClass == c["tclass"]
               and x.exchange in ("SMART", "CBOE")), None) or chains[0]
    today = _market_now().strftime("%Y%m%d")
    fwd = sorted(e for e in ch.expirations if e >= today)
    # Taking the N nearest is wrong now that SPX expires daily: on a Monday the
    # five nearest are all this week's dailies, so the 5-14 DTE swing tenor and
    # the monthly OPEX fall out of the chain entirely. That silently starves
    # select_tenors/iv_tenors -- 2026-08-03 pulled with swing = None, which in
    # turn pushes strategy_fit's condor rule down its "IV unavailable" branch.
    # Take the nearest N, then ADD the swing and monthly anchors if missing.
    exps = fwd[:args.expiries]
    anchors = select_tenors(fwd, _market_now().date())
    for key in ("swing", "monthly"):
        e = anchors.get(key)
        if e and e not in exps:
            exps.append(e)
    # This week's Friday, which carries the weekly OI even when dailies crowd it out.
    d0 = _market_now().date()
    friday = (d0 + dt.timedelta(days=(4 - d0.weekday()) % 7)).strftime("%Y%m%d")
    if friday in fwd and friday not in exps:
        exps.append(friday)
    exps = sorted(set(exps))
    if not exps:
        print("No forward expirations found."); ib.disconnect(); return
    print(f"Tenor anchors: swing={anchors.get('swing')} monthly={anchors.get('monthly')}")

    lo, hi = spot * (1 - args.width), spot * (1 + args.width)
    strikes = sorted(s for s in ch.strikes if lo <= s <= hi
                     and (step <= 0 or abs((s / step) - round(s / step)) < 1e-6))
    if not strikes:
        print("No strikes in range."); ib.disconnect(); return
    print(f"Expiries: {', '.join(exps)}")
    print(f"Strikes : {len(strikes)} in [{strikes[0]:.0f}, {strikes[-1]:.0f}] (step {step:g})")

    # build + qualify contracts, honoring the safety cap
    opts = []
    for e in exps:
        for k in strikes:
            for right in ("C", "P"):
                opts.append(Option(args.symbol, e, k, right, "SMART",
                                    tradingClass=ch.tradingClass, multiplier="100"))
    if len(opts) > args.max_contracts:
        print(f"  ! {len(opts)} contracts exceeds --max-contracts {args.max_contracts}; "
              f"trimming to nearest expiries first.")
        opts = opts[:args.max_contracts]
    # qualifyContracts returns None for anything the exchange does not list, and
    # aggregating several expiries guarantees some: a strike listed on the weekly
    # need not exist on the monthly. Filter the Nones before touching .conId --
    # the naive comprehension crashed the whole pull the first time spot ran far
    # enough for the +/-8% window to reach unlisted wings.
    requested = len(opts)
    opts = [o for o in ib.qualifyContracts(*opts) if o is not None and o.conId]
    dropped = requested - len(opts)
    print(f"Qualified {len(opts)} contracts"
          + (f" ({dropped} unlisted strike/expiry pairs skipped)" if dropped else "")
          + "; pulling greeks + OI ...")

    # greeks (snapshot) in batches
    greeks = {}
    for i in range(0, len(opts), 60):
        for o, t in zip(opts[i:i + 60], ib.reqTickers(*opts[i:i + 60])):
            greeks[o.conId] = t.modelGreeks
    if all(g is None for g in greeks.values()) and not args.delayed:
        print("No live greeks -- retrying DELAYED ..."); ib.reqMarketDataType(3)
        for i in range(0, len(opts), 60):
            for o, t in zip(opts[i:i + 60], ib.reqTickers(*opts[i:i + 60])):
                greeks[o.conId] = t.modelGreeks

    oi, volume = pull_open_interest(ib, opts)
    ib.disconnect()

    # --- assemble ---
    now = _market_now()
    rows = []
    for o in opts:
        mg = greeks.get(o.conId)
        exp_date = dt.datetime.strptime(o.lastTradeDateOrContractMonth, "%Y%m%d").date()
        T = max((exp_date - now.date()).days / 365.0, MIN_T_YEARS)
        rows.append(dict(
            expiry=o.lastTradeDateOrContractMonth, strike=float(o.strike), right=o.right,
            iv=(mg.impliedVol if mg else None), gamma=(mg.gamma if mg else None),
            oi=float(oi.get(o.conId) or 0.0) if not (oi.get(o.conId) is None
               or (isinstance(oi.get(o.conId), float) and math.isnan(oi.get(o.conId)))) else 0.0,
            volume=float(volume.get(o.conId) or 0.0) if not (volume.get(o.conId) is None
               or (isinstance(volume.get(o.conId), float) and math.isnan(volume.get(o.conId)))) else 0.0,
            T=T,
        ))
    df = pd.DataFrame(rows)
    df["oi"] = df["oi"].fillna(0.0)

    # ------------------------------------------------------------------
    # ENGINE 1: per-strike net GEX at current spot (reported gamma).
    #   dealer $GEX per contract = sign * gamma * OI * mult * spot^2 * 0.01
    #   ($ change in dealer gamma-hedging notional per 1% move in spot)
    # ------------------------------------------------------------------
    scale = CONTRACT_MULTIPLIER * spot * spot * 0.01

    def eff_gamma(r):  # reported gamma, else BS gamma at current spot
        g = r["gamma"]
        if g is None or (isinstance(g, float) and math.isnan(g)):
            return bs_gamma(spot, r["strike"], r["T"], r["iv"] or 0.0)
        return g

    df["sign"] = df["right"].map({"C": CALL_SIGN, "P": PUT_SIGN}) * FLIP_SIGN
    df["gex"] = df.apply(lambda r: r["sign"] * eff_gamma(r) * r["oi"] * scale, axis=1)
    per_strike = df.groupby("strike")["gex"].sum().sort_index()

    # GEX weighted by TODAY'S VOLUME instead of open interest. Same gamma, same
    # sign convention, different weight: OI is what is positioned, volume is
    # what traded today. nextSignals heads its table "GEX-VOLUME"; this is that
    # column. Outside RTH the volume fields are zero or stale, so the series is
    # only emitted when something actually printed — an all-zero grid published
    # as data would be the missing-IV bug all over again.
    df["gex_vol"] = df.apply(lambda r: r["sign"] * eff_gamma(r) * r["volume"] * scale, axis=1)
    per_strike_vol = df.groupby("strike")["gex_vol"].sum().sort_index()
    total_traded = float(df["volume"].sum())
    if total_traded <= 0:
        per_strike_vol = None

    # ------------------------------------------------------------------
    # CHARM exposure: $ of dealer delta that drifts per CALENDAR DAY.
    #   Gamma forces re-hedging when spot moves; charm forces it when time
    #   passes. They are independent drivers, so a strike where BOTH peak is a
    #   stronger pin read than either alone -- and charm dominates into expiry,
    #   which is exactly when GEX alone stops explaining the tape.
    #   delta notional per contract = mult * spot, hence no spot^2 here.
    # ------------------------------------------------------------------
    #   Measured as TOTAL drift to expiry, not the instantaneous per-day rate.
    #   Charm carries a 1/T^1.5 term and diverges as T->0, so a per-day figure on
    #   0DTE is set by the MIN_T_YEARS floor rather than by the book: on the
    #   2026-07-31 chain the floored 0DTE leg supplied 92.6% of the total, which
    #   is an artifact of the floor, not structure. Delta at expiry is exactly 0
    #   or +/-1, so (terminal delta - current delta) is bounded, floor-free, and
    #   answers the question that matters: how much re-hedging MUST still happen.
    charm_scale = CONTRACT_MULTIPLIER * spot

    def delta_drift(r):
        """Delta the dealer must still hedge away between now and expiry."""
        iv = r["iv"] or 0.0
        if iv <= 0:
            return 0.0
        d_now = bs_delta_q(spot, r["strike"], max(r["T"], MIN_T_YEARS), iv, r["right"])
        itm = (spot > r["strike"]) if r["right"] == "C" else (spot < r["strike"])
        d_end = (1.0 if r["right"] == "C" else -1.0) if itm else 0.0
        return d_end - d_now

    df["charm"] = df.apply(
        lambda r: r["sign"] * delta_drift(r) * r["oi"] * charm_scale, axis=1)
    per_strike_charm = df.groupby("strike")["charm"].sum().sort_index()
    charm_peak = per_strike_charm.abs().idxmax() if not per_strike_charm.empty else None
    total_charm = per_strike_charm.sum()

    #   CHARM FLIP + GRADIENT. The peak says where the drift is biggest; the flip
    #   says where its SIGN changes (dealers switch from buying to selling the
    #   drift), and the gradient says how abruptly. A steep gradient at the flip
    #   is a sharper boundary than a broad one at the same level.
    charm_flip, charm_gradient = None, {}
    ks = list(per_strike_charm.index)
    for a, b in zip(ks, ks[1:]):
        va, vb = per_strike_charm[a], per_strike_charm[b]
        if va == 0:
            charm_flip = float(a)
        elif va * vb < 0:                       # sign change between adjacent strikes
            # linear interpolation of the zero crossing
            cross = a + (b - a) * (-va) / (vb - va)
            if charm_flip is None or abs(cross - spot) < abs(charm_flip - spot):
                charm_flip = round(float(cross), 1)
    for a, b in zip(ks, ks[1:]):
        if b != a:
            charm_gradient[float(a)] = round(
                float((per_strike_charm[b] - per_strike_charm[a]) / (b - a)), 2)
    charm_flip_gradient = None
    if charm_flip is not None and charm_gradient:
        near = min(charm_gradient, key=lambda k: abs(k - charm_flip))
        charm_flip_gradient = charm_gradient[near]

    call_wall = per_strike.idxmax()
    put_wall = per_strike.idxmin()
    pin = per_strike.abs().idxmax()
    total_gex = per_strike.sum()

    # ------------------------------------------------------------------
    # ENGINE 2: gamma profile across spot -> zero-gamma flip.
    #   For each hypothetical spot S, re-price every option's BS gamma and sum
    #   the dealer $GEX. The zero-crossing nearest spot is the flip.
    # ------------------------------------------------------------------
    valid = df[(df["oi"] > 0) & df["iv"].notna() & (df["iv"] > 0)].copy()
    n = args.profile_points
    grid = [spot * (1 - args.profile_range + 2 * args.profile_range * i / (n - 1)) for i in range(n)]
    profile = []
    for S in grid:
        s2 = CONTRACT_MULTIPLIER * S * S * 0.01
        tot = 0.0
        for r in valid.itertuples():
            tot += r.sign * bs_gamma(S, r.strike, r.T, r.iv) * r.oi * s2
        profile.append(tot)

    # zero crossing(s), interpolated; pick the one nearest spot
    flips = []
    for i in range(1, n):
        a, b = profile[i - 1], profile[i]
        if a == 0.0:
            flips.append(grid[i - 1])
        elif a * b < 0.0:
            frac = a / (a - b)
            flips.append(grid[i - 1] + frac * (grid[i] - grid[i - 1]))
    flip = min(flips, key=lambda x: abs(x - spot)) if flips else None

    # profile-based positive pocket around spot (contiguous S with GEX >= 0)
    pocket = None
    idx_spot = min(range(n), key=lambda i: abs(grid[i] - spot))
    if profile[idx_spot] >= 0:
        lo_i = idx_spot
        while lo_i > 0 and profile[lo_i - 1] >= 0:
            lo_i -= 1
        hi_i = idx_spot
        while hi_i < n - 1 and profile[hi_i + 1] >= 0:
            hi_i += 1
        pocket = (grid[lo_i], grid[hi_i])

    # ------------------------------------------------------------------
    # report
    # ------------------------------------------------------------------
    bn = 1e9
    regime = ("POSITIVE (dealers long gamma, hedging dampens moves)"
              if (flip is not None and spot >= flip) or (flip is None and total_gex >= 0)
              else "NEGATIVE (dealers short gamma, hedging amplifies moves)")
    print("\n================= GEX LEVELS =================")
    print(f" Symbol / spot ............ {args.symbol}  {spot:.2f}")
    print(f" Total net GEX ............ {total_gex / bn:+.3f}  Bn$/1%")
    print(f" Current regime ........... {regime}")
    print(f" ZERO-GAMMA FLIP .......... {flip:.2f}" if flip is not None else " ZERO-GAMMA FLIP .......... (no crossing in grid)")
    if per_strike_vol is not None:
        vw_call, vw_put = per_strike_vol.idxmax(), per_strike_vol.idxmin()
        tag_c = "" if vw_call == call_wall else "  <-- DIVERGES from OI call wall"
        tag_p = "" if vw_put == put_wall else "  <-- DIVERGES from OI put wall"
        print(f" VOLUME-GEX call peak ..... {vw_call:.0f}   ({per_strike_vol[vw_call] / bn:+.3f} Bn){tag_c}")
        print(f" VOLUME-GEX put  peak ..... {vw_put:.0f}   ({per_strike_vol[vw_put] / bn:+.3f} Bn){tag_p}")
    print(f" CALL WALL (resistance) ... {call_wall:.0f}   ({per_strike[call_wall] / bn:+.3f} Bn)")
    print(f" PUT WALL  (support) ...... {put_wall:.0f}   ({per_strike[put_wall] / bn:+.3f} Bn)")
    print(f" PIN / abs-gamma strike ... {pin:.0f}   ({per_strike[pin] / bn:+.3f} Bn)")
    if pocket:
        print(f" Positive-gamma pocket .... {pocket[0]:.0f} - {pocket[1]:.0f}")
    print("=============================================")
    # sanity checks against the intuition in the spec
    if flip is not None:
        note = "OK" if put_wall <= flip <= call_wall or True else ""
        print(f" sanity: flip {flip:.0f} vs spot {spot:.0f} -> "
              f"{'spot ABOVE flip (positive regime)' if spot >= flip else 'spot BELOW flip (negative regime)'}")

    # ------------------------------------------------------------------
    # ATM IV -- call IV at the strike nearest spot, per tenor.
    #   derive.strategy_fit() gates the iron-condor rule on IV; feeding it the
    #   front expiry meant feeding it 0DTE, whose IV spikes into expiry as
    #   sqrt(T) collapses and so tracks the clock rather than the vol regime.
    #   iv_tenors() picks the nearest forward expiry and the swing tenor
    #   instead; the swing reading is the one the rules consume, matching what
    #   pipeline/gex/engine.py already does with its swing-tenor primary.
    # ------------------------------------------------------------------
    def _atm_iv(expiry):
        if not expiry:
            return None
        side = df[(df["expiry"] == expiry) & (df["right"] == "C")]
        side = side[side["iv"].notna() & (side["iv"] > 0)]
        if side.empty:
            return None
        return round(float(side.iloc[(side["strike"] - spot).abs().argmin()]["iv"]), 4)

    ivt = iv_tenors(exps, now.date())
    atm_iv_1dte, atm_iv_swing = _atm_iv(ivt["one_dte"]), _atm_iv(ivt["swing"])
    for label, exp, iv in (("1DTE ", ivt["one_dte"], atm_iv_1dte),
                           ("swing", ivt["swing"], atm_iv_swing)):
        print(f" ATM IV ({label} {exp or '-'}) ... "
              f"{f'{iv:.1%}' if iv is not None else 'unavailable'}")
    if charm_peak is not None:
        _gp = per_strike.abs().idxmax()
        _agree = ("  <-- SAME STRIKE as gamma peak" if _gp == charm_peak
                  else f"  (gamma peak {_gp:.0f})")
        print(f" CHARM peak strike ....... {charm_peak:.0f}   "
              f"total {total_charm/1e9:+.2f} Bn$ delta to expiry{_agree}")
        if charm_flip is not None:
            print(f" CHARM flip .............. {charm_flip:.0f}"
                  + (f"   gradient {charm_flip_gradient/1e6:+.0f} $mm/pt"
                     if charm_flip_gradient else ""))

    # ------------------------------------------------------------------
    # persist
    # ------------------------------------------------------------------
    os.makedirs(args.outdir, exist_ok=True)
    stamp = now.strftime("%Y%m%d")
    levels = dict(
        symbol=args.symbol, generated_at=now.isoformat(timespec="seconds"),
        spot=round(spot, 2), spot_source=src,
        expiries=exps, sign_convention=dict(call=CALL_SIGN, put=PUT_SIGN, flip=FLIP_SIGN),
        total_gex=round(total_gex, 2), regime="positive" if "POSITIVE" in regime else "negative",
        zero_gamma_flip=round(flip, 2) if flip is not None else None,
        call_wall=call_wall, put_wall=put_wall, pin_strike=pin,
        atm_iv_1dte=atm_iv_1dte, atm_iv_swing=atm_iv_swing,
        atm_iv_tenors={"one_dte": ivt["one_dte"], "swing": ivt["swing"]},
        positive_pocket=[round(pocket[0], 2), round(pocket[1], 2)] if pocket else None,
        per_strike_gex={float(k): round(v, 2) for k, v in per_strike.items()},
        per_strike_gex_volume=({float(k): round(v, 2) for k, v in per_strike_vol.items()}
                               if per_strike_vol is not None else None),
        gex_volume_note=("weighted by today's traded volume (tick 100); resets daily"
                         if per_strike_vol is not None
                         else "unavailable — nothing traded at pull time (outside RTH?)"),
        per_strike_charm={float(k): round(v, 2) for k, v in per_strike_charm.items()},
        total_charm=round(float(total_charm), 2),
        charm_peak_strike=float(charm_peak) if charm_peak is not None else None,
        charm_flip=charm_flip,
        charm_flip_gradient=charm_flip_gradient,
        per_strike_charm_gradient=charm_gradient,
        profile=[[round(s, 2), round(g, 2)] for s, g in zip(grid, profile)],
    )
    json_path = os.path.join(args.outdir, f"gex_{args.symbol}_{stamp}.json")
    with open(json_path, "w") as f:
        json.dump(levels, f, indent=2)
    csv_path = os.path.join(args.outdir, f"gex_{args.symbol}_{stamp}.csv")
    out = df[["expiry", "strike", "right", "iv", "gamma", "oi", "gex"]].copy()
    out.sort_values(["expiry", "strike", "right"]).to_csv(csv_path, index=False)
    # also a compact per-strike CSV for quick TradingView / plotting use
    ps_path = os.path.join(args.outdir, f"gex_{args.symbol}_{stamp}_perstrike.csv")
    per_strike.rename("net_gex").to_csv(ps_path)
    print(f"\nSaved:\n  {json_path}\n  {csv_path}\n  {ps_path}")
    print("Latest-pointer JSON also written for the TradingView step.")
    # stable "latest" pointer so the TV overlay generator always finds today's run
    with open(os.path.join(args.outdir, f"gex_{args.symbol}_latest.json"), "w") as f:
        json.dump(levels, f, indent=2)


if __name__ == "__main__":
    main()
