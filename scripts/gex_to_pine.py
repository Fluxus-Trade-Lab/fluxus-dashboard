#!/usr/bin/env python3
"""
Generate a TradingView Pine v6 overlay from a gex_levels.py run.

Reads data/gex/gex_<SYMBOL>_latest.json (or a path passed as arg) and emits a
Pine script that draws the GEX levels as extended support/resistance lines with
on-chart labels:
    - Zero-gamma flip (dashed yellow)
    - Call wall       (red, resistance)
    - Put wall        (green, support)
    - Pin / abs-gamma strike (orange, only if distinct from the walls)
    - Positive-gamma pocket (faint shaded band)

For SPX, the overlay includes a "This chart is: SPX / ES" toggle so the same
SPX-cash levels can be used on an ES futures chart. In ES mode it shifts every
level by the SPX->ES basis; the default Auto source computes the basis live from
daily closes (ES close - SPX close), which self-corrects through contract roll
and basis decay. A Manual fixed-points override is also provided.

Writes the .pine next to the JSON and prints the source to stdout so it can be
piped straight into the TradingView MCP (pine_set_source + pine_smart_compile
+ pine_save). Regenerate daily so the levels persist on the chart.

Usage:
    .venv/bin/python scripts/gex_to_pine.py                 # SPX latest
    .venv/bin/python scripts/gex_to_pine.py --symbol SPY
    .venv/bin/python scripts/gex_to_pine.py path/to/gex.json
"""
import argparse, json, os

TEMPLATE = '''//@version=6
indicator("GEX Levels {symbol} {date}", overlay=true, max_labels_count=50, max_lines_count=20)

// --- Dealer gamma-exposure levels (generated {generated_at}) ---
// spot at pull: {spot}   regime: {regime}   total net GEX: {total_gex_bn} Bn$/1%
FLIP      = {flip}
CALL_WALL = {call_wall}
PUT_WALL  = {put_wall}
PIN       = {pin}
POCKET_LO = {pocket_lo}
POCKET_HI = {pocket_hi}

show_pocket = input.bool(true, "Show positive-gamma pocket")

{basis_block}

// Levels are drawn as extended lines (so the live basis can shift them on an ES
// chart) with a label at each. Lines + labels are rebuilt on the last bar so
// nothing duplicates.
var line lnFlip = na
var line lnCall = na
var line lnPut  = na
var line lnPin  = na
var label lFlip = na
var label lCall = na
var label lPut  = na
var label lPin  = na
lbl(_name, _p) => _name + " " + str.tostring(_p, format.mintick) + (basis != 0 ? " ⇒ " + str.tostring(adj(_p), format.mintick) : "")
if barstate.islast
    line.delete(lnFlip), line.delete(lnCall), line.delete(lnPut), line.delete(lnPin)
    label.delete(lFlip), label.delete(lCall), label.delete(lPut), label.delete(lPin)
    x1 = bar_index - 1
    x2 = bar_index
    {flip_draw}
    lnCall := line.new(x1, adj(CALL_WALL), x2, adj(CALL_WALL), extend=extend.both, color=color.new(color.red, 0), width=2)
    lCall := label.new(x2, adj(CALL_WALL), lbl("Call Wall", CALL_WALL), style=label.style_label_left, color=color.new(color.red, 20), textcolor=color.white, size=size.small)
    lnPut := line.new(x1, adj(PUT_WALL), x2, adj(PUT_WALL), extend=extend.both, color=color.new(color.green, 0), width=2)
    lPut := label.new(x2, adj(PUT_WALL), lbl("Put Wall", PUT_WALL), style=label.style_label_left, color=color.new(color.green, 20), textcolor=color.white, size=size.small)
    {pin_draw}

// shaded positive-gamma pocket (bounds shifted by basis too)
bgcolor(show_pocket and not na(POCKET_LO) and close >= adj(POCKET_LO) and close <= adj(POCKET_HI) ? color.new(color.teal, 90) : na)
'''

BASIS_BLOCK_SPX = '''// --- SPX <-> ES basis toggle (levels are SPX cash strikes) ---
chartIs   = input.string("SPX", "This chart is", options=["SPX", "ES"], tooltip="Set to ES to shift the SPX levels onto an ES futures chart.")
basisMode = input.string("Auto", "ES basis source", options=["Auto", "Manual"], tooltip="Auto = live daily (ES close - SPX close); tracks contract roll + basis decay. Manual = fixed points.")
manualPts = input.float(0.0, "Manual ES basis (ES - SPX, pts)")
spxDClose = request.security("SP:SPX", "D", close)
chtDClose = request.security(syminfo.tickerid, "D", close)
autoBasis = chtDClose - spxDClose
basis = chartIs == "ES" ? (basisMode == "Auto" ? autoBasis : manualPts) : 0.0
adj(_p) => _p + basis'''

BASIS_BLOCK_PLAIN = '''// levels are {symbol} prices; no futures-basis adjustment
basis = 0.0
adj(_p) => _p'''


def fmt(v):
    return "na" if v is None else f"{float(v):.2f}"


def build(levels):
    sym = levels["symbol"]
    flip = levels.get("zero_gamma_flip")
    call_wall = levels["call_wall"]
    put_wall = levels["put_wall"]
    pin = levels["pin_strike"]
    pocket = levels.get("positive_pocket") or [None, None]

    # flip line + label (inside the barstate.islast block; 4-space indent)
    if flip is not None:
        flip_draw = (
            'lnFlip := line.new(x1, adj(FLIP), x2, adj(FLIP), extend=extend.both, '
            'color=color.new(color.yellow, 0), style=line.style_dashed, width=2)\n'
            '    lFlip := label.new(x2, adj(FLIP), lbl("Flip", FLIP), style=label.style_label_left, '
            'color=color.new(color.yellow, 20), textcolor=color.black, size=size.small)'
        )
    else:
        flip_draw = "// no zero-gamma crossing found in the profile grid"

    distinct_pin = pin not in (call_wall, put_wall)
    if distinct_pin:
        pin_draw = (
            'lnPin := line.new(x1, adj(PIN), x2, adj(PIN), extend=extend.both, '
            'color=color.new(color.orange, 0), width=1)\n'
            '    lPin := label.new(x2, adj(PIN), lbl("Pin", PIN), style=label.style_label_left, '
            'color=color.new(color.orange, 20), textcolor=color.white, size=size.small)'
        )
    else:
        pin_draw = "// pin coincides with a wall (not drawn separately)"

    basis_block = BASIS_BLOCK_SPX if sym == "SPX" else BASIS_BLOCK_PLAIN.format(symbol=sym)

    return TEMPLATE.format(
        symbol=sym, date=levels["generated_at"][:10], generated_at=levels["generated_at"],
        spot=levels["spot"], regime=levels.get("regime", "?"),
        total_gex_bn=f'{levels["total_gex"]/1e9:+.2f}',
        flip=fmt(flip), call_wall=fmt(call_wall), put_wall=fmt(put_wall), pin=fmt(pin),
        pocket_lo=fmt(pocket[0]), pocket_hi=fmt(pocket[1]),
        basis_block=basis_block, flip_draw=flip_draw, pin_draw=pin_draw,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json", nargs="?", default=None, help="path to a gex JSON (default: latest)")
    p.add_argument("--symbol", default="SPX")
    p.add_argument("--outdir", default="data/gex")
    args = p.parse_args()

    path = args.json or os.path.join(args.outdir, f"gex_{args.symbol}_latest.json")
    with open(path) as f:
        levels = json.load(f)
    src = build(levels)

    pine_path = os.path.splitext(path)[0] + ".pine"
    with open(pine_path, "w") as f:
        f.write(src)
    # stable pointer for the daily TV push
    with open(os.path.join(args.outdir, f"gex_{levels['symbol']}_latest.pine"), "w") as f:
        f.write(src)
    print(src)


if __name__ == "__main__":
    main()
