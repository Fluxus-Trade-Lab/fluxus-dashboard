"""Number gate for the per-candidate sentences on the Screener funnel preview.

Every number in a sentence must appear in that ticker's own fact card
(rounded to 0/1/2 dp). Rule names (21EMA, 50SMA, 52-week, §11.1's 25% line,
the 4-ATR band edge) are allowed constants. Comparisons across tickers
("lowest of the four refiners") are NOT checked here -- verify by hand.

Positive control 2026-10-01: STX 0.84->0.48, RNG -33.6->-3.6, and MPC's
sentence on VLO's card all flagged.

usage: python3 check_notes.py fact_cards_<date>.json notes_zh_<date>.json
"""
import json, re, sys

ALLOWED = {25, 4, 21, 50, 52, 1, 0, 3}


def numbers_in(card):
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            for d in (0, 1, 2):
                out.add(round(abs(x), d))

    walk(card)
    return out


def check(cards, notes):
    bad = []
    for t, s in notes.items():
        if t.startswith('_'):
            continue
        have = numbers_in(cards[t])
        for m in re.findall(r'\d+(?:\.\d+)?', s.replace('§11.1', '')):
            v = float(m)
            if v not in ALLOWED and v not in have:
                bad.append((t, m))
    return bad


if __name__ == '__main__':
    D = json.load(open(sys.argv[1]))
    cards = {r['t']: r for k in D['setups'] for r in D['setups'][k]['rows']}
    bad = check(cards, json.load(open(sys.argv[2])))
    print('unsupported numbers:', bad)
    sys.exit(1 if bad else 0)
