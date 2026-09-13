"""Education schematics as data specs, drawn by the page JS in the Visual `.tell` style.

Every builder encodes spec §5's three checks as asserts on its own data, so a wrong drawing fails
the build instead of shipping:
  (1) price really performs the move the concept names,
  (2) the structural relationship is right (support below / resistance above / who leads),
  (3) every label is computed from, or placed on, the thing it names.
A spec is {"ylim", "aria", "items"}; x runs 0–100, y in ylim. Item kinds: path (flat x,y list),
hline, vline, band, rect, seg, text, callout. Colours come only from CSS classes on the page.
The figure name doubles as the education concept tag in the topic ledger (dedupe.py).
"""
from __future__ import annotations


def _r(v):
    return None if v is None else round(float(v), 2)


class Canvas:
    def __init__(self, ylim=(0, 60)):
        self.ylim, self.items = [ylim[0], ylim[1]], []

    def path(self, xs, ys, cls):
        flat = []
        for x, y in zip(xs, ys):
            flat += [_r(x), _r(y)]
        self.items.append(["path", cls, flat])

    def hline(self, y, cls, x_from=None, x_to=None):
        self.items.append(["hline", cls, _r(y), _r(x_from), _r(x_to)])

    def vline(self, x, cls):
        self.items.append(["vline", cls, _r(x)])

    def band(self, y0, y1, cls):
        self.items.append(["band", cls, _r(y0), _r(y1)])

    def rect(self, x0, y0, x1, y1, cls):
        self.items.append(["rect", cls, _r(x0), _r(y0), _r(x1), _r(y1)])

    def seg(self, x0, y0, x1, y1, cls):
        self.items.append(["seg", cls, _r(x0), _r(y0), _r(x1), _r(y1)])

    def text(self, x, y, s, cls="", anchor="start"):
        self.items.append(["text", cls, _r(x), _r(y), s, anchor])

    def callout(self, x, y, tx, ty, label, cls=""):
        self.items.append(["callout", cls, _r(x), _r(y), _r(tx), _r(ty), label])

    def svg(self, aria):
        return {"ylim": self.ylim, "aria": aria, "items": self.items}


def _lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ================================================================== A topics (samples)
def left_side_of_v(lang):
    T = {"EN": ["20 EMA · falling", "50 SMA", "pop sold at the 20", "lower high, sold again",
                "averages coil · range tightens", "right side of the V", "LEFT SIDE"],
         "ZH": ["20 EMA · 向下", "50 SMA", "反弹在 20 线被卖", "高点更低，又被卖", "均线收拢 · 区间收窄", "V 字右边", "左边"]}[lang]
    import math
    px = [2, 7, 11, 16, 20, 25, 29, 34, 38, 43, 47, 52, 56, 60, 64, 68, 72, 76, 80, 86, 92, 97]
    py = [50, 41, 45.5, 36, 39.3, 31, 35.2, 27.5, 30.6, 26.2, 29.3, 26.6, 28.9, 27.0, 28.6, 27.4, 28.8, 31.8, 30.6, 38.5, 36.8, 45]
    xs = _lin(6, 97, 80)
    ema = lambda x: 28.8 + 27.4 * math.exp(-(x - 2) / 20.6) + 0.017 * max(x - 74, 0) ** 2
    sma = lambda x: 28.4 + 2.5 * math.exp(-(x - 2) / 40.0) - 0.008 * (x - 2) + 0.003 * max(x - 82, 0) ** 2
    for hx, hy in ((11, 45.5), (20, 39.3), (29, 35.2)):
        assert ema(hx) - 3.0 <= hy <= ema(hx) + 0.3, (hx, hy)
    assert all(py[i] < ema(px[i]) for i in range(1, 17)), "left side: price under the 20"
    assert ema(11) - sma(11) > 10 and ema(68) - sma(68) < 2.5, "averages must coil"
    assert ema(20) < ema(11) and ema(40) < ema(29), "20 falling on the left"
    assert py[-1] > ema(97) and py[-1] > sma(97), "breakout clears both"
    c = Canvas(ylim=(10, 60))
    c.path(xs, [sma(x) for x in xs], "ma2")
    c.path(xs, [ema(x) for x in xs], "ma")
    c.path(px, py, "trend")
    c.text(8, 53.5, T[0], "lab-acc")
    c.text(36, 24.2, T[1])
    c.callout(20, 39.3, 26, 52, T[2])
    c.callout(29, 35.2, 42, 45, T[3])
    c.callout(62, 28.0, 60, 17, T[4], "lab-acc")
    c.callout(86, 38.5, 80, 52, T[5], "lab-up")
    c.text(3, 12.5, T[6], "small")
    return c.svg(T[5])


def rs_before_price(lang):
    T = {"EN": ["stock's high", "index · lower lows", "RS LINE = STOCK ÷ INDEX", "RS new high first", "price still under its high"],
         "ZH": ["个股前高", "指数 · 低点更低", "RS 线 = 个股 ÷ 指数", "RS 先创新高", "价格仍在前高下方"]}[lang]
    x = _lin(4, 96, 24)
    idx = [100, 99, 100.5, 98.5, 99.2, 97.3, 98, 96.2, 96.8, 95, 95.9, 94.2, 94.8, 93.1, 94, 92.4, 93.2, 91.6, 92.5, 91, 91.8, 90.4, 91.3, 90.2]
    stk = [100, 102, 104.5, 106, 104, 101.5, 102.5, 101, 102.8, 101.8, 103.2, 102.3, 103.6, 102.6, 104, 103.2, 104.4, 103.6, 104.8, 104.2, 105.2, 104.6, 105.5, 105.0]
    rs = [s / i for s, i in zip(stk, idx)]
    k = stk.index(max(stk))
    rs_prior = max(rs[: k + 1])
    j = next(i for i in range(k + 1, len(rs)) if rs[i] > rs_prior)
    lows = [idx[i] for i in range(1, len(idx) - 1) if idx[i] < idx[i - 1] and idx[i] < idx[i + 1]]
    assert all(b < a for a, b in zip(lows, lows[1:])), "index lower lows"
    assert max(stk[k + 1:]) < stk[k], "price stays under its high"
    assert stk[j] < stk[k] and rs[-1] > rs_prior, "RS new high before price"
    py = [40 + (s - 100) * 2.2 for s in stk]
    iy = [40 + (v - 100) * 1.2 for v in idx]
    ry = [6 + (r - 1.0) * 80 for r in rs]
    c = Canvas()
    c.hline(24.5, "guide")
    c.hline(py[k], "guide", 8, 100)
    c.hline(6 + (rs_prior - 1) * 80, "guide", 8, 100)
    c.path(x, iy, "evt")
    c.path(x, py, "trend")
    c.path(x, ry, "ma")
    c.text(99, py[k] + 1.3, T[0], "small", "end")
    c.text(x[-1], iy[-1] - 3.6, T[1], "small", "end")
    c.text(4, 21, T[2], "lab-acc small")
    c.callout(x[j], ry[j], x[j] + 6, 1.5, T[3], "lab-acc")
    c.callout(x[j], py[j], x[j] - 10, 57, T[4])
    return c.svg(T[3])


def bull_bear_line(lang):
    T = {"EN": ["bull / bear line", "ABOVE · long bias", "BELOW · defense, cash is a position", "loses the line", "reclaims it"],
         "ZH": ["多空线", "线上 · 偏多", "线下 · 偏守，现金也是仓位", "跌破这条线", "收回来"]}[lang]
    L = 30.0
    px = _lin(3, 97, 20)
    py = [40, 36, 38.5, 33.5, 35.5, 31.5, 33, 27.5, 29.5, 25, 27.8, 24.2, 28.6, 26.2, 31.8, 30.6, 34.5, 32.4, 37, 35.5]
    lose = next(i for i in range(1, len(py)) if py[i - 1] >= L > py[i])
    back = next(i for i in range(lose + 1, len(py)) if py[i - 1] < L <= py[i])
    assert all(p >= L for p in py[:lose]) and all(p < L for p in py[lose:back]), "below between loss and reclaim"
    assert all(p >= L for p in py[back:]), "above after the reclaim"
    c = Canvas()
    c.band(L, 58, "zone-up")
    c.band(4, L, "zone-dn")
    c.hline(L, "lvl")
    c.path(px, py, "trend")
    c.text(2, L + 1.2, T[0], "lab-acc")
    c.text(2, 54.5, T[1], "lab-up small")
    c.text(2, 6, T[2], "lab-dn small")
    c.callout(px[lose], py[lose], px[lose] + 5, 14, T[3], "lab-dn")
    c.callout(px[back], py[back], px[back] - 2, 49, T[4], "lab-up")
    return c.svg(T[0])


def equal_weight_split(lang):
    T = {"EN": ["CAP-WEIGHTED", "EQUAL-WEIGHT", "50-day", "held above", "first close under the 50-day"],
         "ZH": ["市值加权", "等权", "50 日线", "守在线上", "首次收在 50 日线下"]}[lang]
    xl = _lin(4, 45, 14)
    mal = [22 + 0.25 * (x - 3) for x in xl]
    pl = [m + o for m, o in zip(mal, [8, 10, 9, 12, 10.5, 13, 11, 12.5, 10, 11.5, 9, 10.5, 8.5, 9.5])]
    xr = _lin(55, 96, 14)
    mar = [26 + 0.12 * (x - 54) - 0.0035 * (x - 54) ** 2 for x in xr]
    pr = [m + o for m, o in zip(mar, [7, 8.5, 6, 7.5, 4.5, 6, 3, 4, 1.5, 2.5, -1, 0.5, -2.5, -3.5])]
    fb = next(i for i in range(len(pr)) if pr[i] < mar[i])
    assert all(p > m for p, m in zip(pl, mal)), "cap-weighted stays above its 50-day"
    assert all(pr[i] > mar[i] for i in range(fb)) and pr[-1] < mar[-1], "equal weight was above, then breaks"
    assert mal[-1] > mal[0], "cap-weighted 50-day rising"
    c = Canvas(ylim=(10, 60))
    c.vline(50, "guide")
    for xs, ma, p in ((xl, mal, pl), (xr, mar, pr)):
        c.path(xs, ma, "ma")
        c.path(xs, p, "trend")
    c.text(4, 56, T[0], "small")
    c.text(55, 56, T[1], "small")
    c.text(xl[-1], mal[-1] - 3.4, T[2], "lab-acc small", "end")
    c.text(xr[-1], mar[-1] + 1.6, T[2], "lab-acc small", "end")
    c.callout(xl[-1], pl[-1], 30, 51, T[3], "lab-up")
    c.callout(xr[fb], pr[fb], xr[fb] - 6, 13, T[4], "lab-dn")
    return c.svg(T[4])


def shallow_pullback(lang):
    xa = [3, 10, 16, 22, 28, 35, 42, 49, 56, 63, 70, 77, 84, 91, 97]
    va = [92, 100, 93, 95, 84, 73, 80, 78, 86, 90, 100.5, 99, 104, 103, 108]
    xb = [3, 10, 17, 24, 31, 38, 45, 52, 59, 66, 73, 80, 87, 94, 97]
    vb = [92, 100, 88, 90, 72, 60, 40, 48, 45, 55, 52, 62, 60, 68, 70]
    HIGH = 100.0
    da, db = 1 - min(va) / HIGH, 1 - min(vb) / HIGH
    ia, ib = va.index(min(va)), vb.index(min(vb))
    back_a = next(xa[i] for i in range(ia, len(va)) if va[i] > HIGH)
    back_b = next((xb[i] for i in range(ib, len(vb)) if vb[i] > HIGH), None)
    assert da < db, "A is the shallow one"
    assert back_b is None or back_a < back_b, "the shallow one regains the high first"
    T = {"EN": ["prior high", f"−{da:.0%} pullback", f"−{db:.0%} pullback", "first back to the high", "still repairing"],
         "ZH": ["前高", f"回撤 −{da:.0%}", f"回撤 −{db:.0%}", "最先回到前高", "还在修复"]}[lang]
    y = lambda v: 5 + v * 0.48
    c = Canvas()
    c.hline(y(HIGH), "guide")
    c.path(xb, [y(v) for v in vb], "ma")
    c.path(xa, [y(v) for v in va], "trend")
    c.text(3, y(HIGH) + 1.4, T[0], "small")
    c.callout(xa[ia], y(va[ia]), xa[ia] - 10, 30, T[1])
    c.callout(xb[ib], y(vb[ib]), xb[ib] + 13, 12, T[2], "lab-acc")
    c.callout(back_a, y(HIGH), back_a - 4, 58, T[3], "lab-up")
    c.text(97, y(min(vb)) + 4, T[4], "lab-acc", "end")
    return c.svg(T[3])


# ================================================================== B topics (samples)
def low_volume_breakout(lang):
    T = {"EN": ["pivot", "breakout on light volume", "back under the pivot", "VOLUME", "average", "breakout bar under average"],
         "ZH": ["突破位", "缩量突破", "又跌回突破位下", "成交量", "均量", "突破日量低于均量"]}[lang]
    PIV = 44.0
    px = _lin(4, 96, 16)
    py = [36, 40, 38, 42.5, 39.5, 43, 40.5, 43.4, 41, 43.2, 46.2, 44.6, 42.5, 41, 39.5, 38.2]
    vol = [9, 8, 7.5, 7, 6.5, 7, 6, 6.5, 5.5, 6, 5.2, 5.0, 8.5, 9.5, 10, 9]
    avg = sum(vol[:10]) / 10
    b = next(i for i in range(1, len(py)) if py[i - 1] < PIV <= py[i])
    back = next(i for i in range(b + 1, len(py)) if py[i] < PIV)
    assert all(p < PIV for p in py[:b]), "base stays under the pivot before the breakout"
    assert vol[b] < avg, "breakout volume under its average"
    assert all(p < PIV for p in py[back:]), "fails back under the pivot and stays there"
    c = Canvas(ylim=(0, 60))
    c.hline(PIV, "lvl")
    for i, (x, v) in enumerate(zip(px, vol)):
        c.rect(x - 2.0, 2, x + 2.0, 2 + v, "volbar hi" if i == b else "volbar")
    c.hline(2 + avg, "guide")
    c.path(px, py, "trend")
    c.text(2, PIV + 1.2, T[0], "lab-acc")
    c.text(2, 15, T[3], "small")
    c.text(99, 2 + avg + 1, T[4], "small", "end")
    c.callout(px[b], py[b], px[b] - 8, 56, T[1])
    c.callout(px[back + 1], py[back + 1], px[back + 1] + 3, 30, T[2], "lab-dn")
    c.callout(px[b], 2 + vol[b], px[b] - 14, 21, T[5], "lab-acc")
    return c.svg(T[1])


def gap_down_first_bar(lang):
    T = {"EN": ["prior close", "gap down", "first 15-min bar", "stop under its low", "low holds, price recovers"],
         "ZH": ["前收", "跳空低开", "第一根 15 分钟线", "止损放在它的低点下", "低点守住，价格回升"]}[lang]
    PRIOR, BAR_HI, BAR_LO, STOP = 46.0, 40.5, 36.0, 34.0
    prev_x, prev_y = [2, 8, 14, 20], [44.0, 45.5, 44.8, PRIOR]
    px = [24, 27, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96]
    py = [39.0, 37.2, 40.2, 38.3, 39.6, 37.4, 38.9, 41.2, 40.1, 42.6, 41.8, 43.9, 43.1, 44.8]
    assert py[0] < PRIOR, "opens below the prior close"
    assert BAR_LO <= min(py[:3]) and max(py[:3]) <= BAR_HI, "first bar box contains the first 15 minutes"
    assert STOP < BAR_LO, "stop sits under the first bar's low"
    assert min(py[3:]) > BAR_LO and py[-1] > BAR_HI, "low holds, then price clears the bar"
    c = Canvas(ylim=(24, 54))
    c.hline(PRIOR, "guide", 20, 100)
    c.path(prev_x, prev_y, "trend")
    c.seg(20, PRIOR, 24, py[0], "evt")
    c.rect(22.5, BAR_LO, 31.5, BAR_HI, "barbox")
    c.hline(STOP, "stop", 22, 100)
    c.path(px, py, "trend")
    c.text(99, PRIOR + 0.8, T[0], "small", "end")
    c.callout(22, 42.5, 12, 30, T[1], "lab-dn")
    c.text(22.5, BAR_HI + 1.0, T[2], "small")
    c.text(99, STOP - 2.2, T[3], "lab-dn small", "end")
    c.callout(px[5], py[5], px[5] + 16, 30, T[4], "lab-up")
    return c.svg(T[2])


def low_vix_not_risk_on(lang):
    T = {"EN": ["index · lower highs", "VIX", "VIX stays near its lows", "calm is not demand"],
         "ZH": ["指数 · 高点更低", "VIX", "VIX 一直贴着低位", "平静不等于买盘"]}[lang]
    xi = _lin(4, 96, 14)
    idx = [52, 48, 50.5, 46.5, 48.8, 45, 47, 43.5, 45.4, 42, 44, 40.6, 42.2, 39.5]
    vix = [8.5, 9.0, 8.8, 9.4, 9.1, 9.6, 9.2, 9.8, 9.5, 10.1, 9.7, 10.4, 10.0, 10.6]
    LOW_BAND = 12.0
    highs = [idx[i] for i in range(1, len(idx) - 1) if idx[i] > idx[i - 1] and idx[i] > idx[i + 1]]
    assert len(highs) >= 3 and all(b < a for a, b in zip(highs, highs[1:])), "index makes lower highs"
    assert idx[-1] < idx[0], "index ends lower"
    assert max(vix) < LOW_BAND and max(vix) - min(vix) < 3, "VIX stays low and flat"
    c = Canvas(ylim=(0, 60))
    c.band(3, LOW_BAND, "zone-up")
    c.hline(22, "guide")
    c.path(xi, idx, "trend")
    c.path(xi, vix, "ma")
    c.text(xi[-1], idx[-1] - 3.5, T[0], "small", "end")
    c.text(2, 14, T[1], "lab-acc small")
    c.callout(xi[9], vix[9], xi[9] - 6, 17.5, T[2], "lab-acc")
    c.text(50, 30, T[3], "", "middle")
    return c.svg(T[3])


def open_equals_high(lang):
    T = {"EN": ["open = high of day", "rallies sold under the open", "close near the low"],
         "ZH": ["开盘即全天最高", "反弹都在开盘价下被卖", "收在低点附近"]}[lang]
    px = _lin(4, 96, 20)
    py = [48, 45, 46.8, 43, 44.9, 41.5, 43.8, 40.2, 42, 38.6, 41.2, 37.5, 39.4, 36.2, 38.1, 35.0, 36.4, 33.6, 34.8, 33.0]
    OPEN, lo, hi = py[0], min(py), max(py)
    assert hi == OPEN and all(p < OPEN for p in py[1:]), "the open is the high"
    assert py[-1] <= lo + (hi - lo) / 3, "close in the lower third of the range"
    c = Canvas(ylim=(20, 56))
    c.hline(OPEN, "guide")
    c.path(px, py, "trend")
    c.callout(px[0], OPEN, 16, 54, T[0], "lab-dn")
    c.callout(px[6], py[6], px[6] + 14, 51, T[1])
    c.callout(px[-1], py[-1], px[-1] - 8, 24, T[2], "lab-dn")
    return c.svg(T[0])


def weekly_close(lang):
    T = {"EN": ["50-day", "Thu: close under the 50-day", "Fri: takes it back", "WEEKLY BAR", "week closes back above the line"],
         "ZH": ["50 日线", "周四：收在 50 日线下", "周五：收回来", "周线", "周收回到线上方"]}[lang]
    ma = lambda x: 30 + 0.02 * x
    xd = [4, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 70]
    yd = [36.0, 34.4, 35.2, 33.6, 32.5, 31.8, 30.9, 29.4, 29.6, 31.5, 32.8, 33.4]
    closes = {"Tue": 2, "Wed": 5, "Thu": 8, "Fri": 11}
    wk_open, wk_close, wk_low, wk_high = yd[0], yd[-1], min(yd), max(yd)
    CX = 86
    assert yd[closes["Wed"]] > ma(xd[closes["Wed"]]), "Wednesday still closes above the 50-day"
    assert yd[closes["Thu"]] < ma(xd[closes["Thu"]]), "Thursday closes under it"
    assert yd[closes["Fri"]] > ma(xd[closes["Fri"]]), "Friday takes it back"
    assert wk_low < ma(CX) < wk_close < wk_open, "weekly bar: low under the line, down week closing above it"
    c = Canvas(ylim=(20, 44))
    c.path([2, 98], [ma(2), ma(98)], "ma")
    c.vline(78, "guide")
    c.path(xd, yd, "trend")
    c.seg(CX, wk_low, CX, wk_high, "wick")
    c.rect(CX - 3, wk_close, CX + 3, wk_open, "body-dn")
    c.text(76, ma(76) - 1.6, T[0], "lab-acc small", "end")
    c.callout(xd[closes["Thu"]], yd[closes["Thu"]], 40, 23, T[1], "lab-dn")
    c.callout(xd[closes["Fri"]], yd[closes["Fri"]], 60, 41, T[2], "lab-up")
    c.text(80, 42.5, T[3], "small")
    c.text(99, 22.5, T[4], "small", "end")
    return c.svg(T[4])


FIGS = {
    "left_side_of_v": left_side_of_v,
    "rs_before_price": rs_before_price,
    "bull_bear_line": bull_bear_line,
    "equal_weight_split": equal_weight_split,
    "shallow_pullback": shallow_pullback,
    "low_volume_breakout": low_volume_breakout,
    "gap_down_first_bar": gap_down_first_bar,
    "low_vix_not_risk_on": low_vix_not_risk_on,
    "open_equals_high": open_equals_high,
    "weekly_close": weekly_close,
}
