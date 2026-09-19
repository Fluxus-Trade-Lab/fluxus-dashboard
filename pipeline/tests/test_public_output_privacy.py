"""Privacy gate for everything Vercel serves -- Andy 2026-09-13, verbatim:
「管线只做R 和%, 不写股数和美元」

Why this exists: the repo is public and vercel.json copies `data/output/`
into the site as-is, so https://fluxus-dashboard.vercel.app/data/output/...
served share counts, dollar risk and dollar P&L for every trade in the book
(389 post-mortems, 8 of them live positions), plus monthly dollar P&L on the
public Results page and a full dollar H1 report.

The rule is enforced on the OUTPUT, not on the writers: a new writer that
nobody remembers to audit is exactly how the first leak happened.

The banned names below are LITERALS on purpose. They must not be imported from
the code under test -- a gate that reads its own constant moves with the bug.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# Every directory that ends up on the public site. vercel.json copies
# data/output into frontend/public/data/output, and Vite publishes all of
# frontend/public verbatim.
PUBLIC_ROOTS = [REPO / 'data' / 'output', REPO / 'frontend' / 'public']

# Share counts and account-level dollar amounts, by exact key name.
BANNED_KEYS = {
    # share counts
    'qty', 'shares', 'original_qty', 'current_qty', 'orig_qty', 'curr_qty',
    'originalQty', 'currentQty', 'position', 'position_value', 'notional',
    # dollar risk / P&L
    'r_dollars', 'R_dollars', 'dollars', 'pl', 'pnl', 'pl_dollars',
    'realized_pl', 'unrealized_pl', 'realized_pnl', 'unrealized_pnl',
    'realizedPL', 'totalPL', 'total_pnl', 'open_pnl', 'best_pnl', 'avg_pnl',
    'profit_total', 'unrealized', 'amount', 'avg_winner', 'avg_loser',
    'expectancy',
    # account size
    'equity', 'mtm_equity', 'peak_equity', 'ending_equity', 'final_equity',
    'starting_capital', 'capital', 'cash', 'account_value', 'cost_basis',
    'market_value',
}

# Spellings nobody has written yet: snake_case tokens and camelCase humps.
BANNED_KEY_PATTERNS = [
    re.compile(r'(^|_)(qty|pnl|pl|dollars?|shares|equity|capital|notional)(_|$)'),
    re.compile(r'[a-z](Qty|Pnl|PnL|PL|Dollars?|Shares|Equity|Capital)([A-Z_]|$)'),
    re.compile(r'^(qty|pnl|shares|dollars?)[A-Z]'),
]

# Allowed, each with the reason. (file glob relative to repo, dotted-path regex)
ALLOWED_KEYS = [
    # Company fundamentals from the data vendor: the COMPANY's balance-sheet
    # cash, share count and return on equity -- public filings, not Andy's book.
    ('data/output/tickers/*.json', r'^\.info\.'),
    ('data/output/tickers/*.json', r'^\.quarterly_metrics\[\]\.cash$'),
    # A liquidity floor for the watchlist screen (min average dollar volume
    # traded in the stock by the whole market), not an account amount.
    ('data/output/watchlist.json', r'^\.gate\.min_dollar_volume$'),
    # Stockbee's liquidity column: the stock's 20-day average dollar volume
    # (whole market, close x volume) -- market data, not an account amount.
    ('data/output/universe.json', r'\.sb_avg_dollar_vol_20$'),
]

# Dollar totals and share counts hiding inside prose (the trade narrative said
# "(qty 2262) ... (1R = $3.41/sh = $7,713)"). Per-share prices like $44.41 are
# market quotes and stay legal; thousands-separated dollar figures do not.
BANNED_VALUE_PATTERNS = [
    re.compile(r'\bqty\s*[:=]?\s*\d', re.I),
    re.compile(r'\$\s?\d{1,3}(,\d{3})+'),
]

# Prose written by third parties about companies (news headlines, AI tear-sheet
# synthesis of public filings) legitimately quotes "$10,000" and "$1,200M".
ALLOWED_VALUES = [
    ('data/output/tickers/*.json', r'^\.(news|ai_synthesis)'),
]


def _rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def _allowed(rules, rel: str, path: str) -> bool:
    return any(fnmatch.fnmatch(rel, g) and re.search(rx, path) for g, rx in rules)


def _is_banned_key(k: str) -> bool:
    return k in BANNED_KEYS or any(p.search(k) for p in BANNED_KEY_PATTERNS)


def _walk(node, path, rel, hits):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f'{path}.{k}'
            if isinstance(k, str) and _is_banned_key(k) and not _allowed(ALLOWED_KEYS, rel, p):
                hits.append(f'{rel} key {p}')
            _walk(v, p, rel, hits)
    elif isinstance(node, list):
        for x in node:
            _walk(x, f'{path}[]', rel, hits)
    elif isinstance(node, str):
        if any(p.search(node) for p in BANNED_VALUE_PATTERNS) \
                and not _allowed(ALLOWED_VALUES, rel, path):
            hits.append(f'{rel} value {path}: {node[:80]!r}')


def scan(roots=PUBLIC_ROOTS) -> list[str]:
    hits: list[str] = []
    for root in roots:
        for f in sorted(root.rglob('*.json')):
            try:
                data = json.loads(f.read_text())
            except (ValueError, UnicodeDecodeError):
                continue
            _walk(data, '', _rel(f), hits)
    # One finding per (file-glob, path) keeps a 389-file leak readable.
    seen, out = set(), []
    for h in hits:
        key = re.sub(r'trades/[^ ]+\.json', 'trades/*.json', h.split(': ')[0])
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out


def test_no_share_counts_or_dollars_in_public_json():
    hits = scan()
    assert not hits, (
        '管线只做R 和% -- share counts / dollar amounts in publicly served '
        f'JSON ({len(hits)} distinct paths):\n  ' + '\n  '.join(hits))


def test_no_embedded_trade_book_in_public_html():
    """frontend/public/*.html ships verbatim too. stop-sim-report.html carried
    the March book inline (`qty:3635`) against STARTING_CAPITAL = 1000000."""
    bad = []
    for f in sorted((REPO / 'frontend' / 'public').rglob('*.html')):
        text = f.read_text(errors='replace')
        if re.search(r'\bqty\s*:\s*\d', text) or 'STARTING_CAPITAL' in text:
            bad.append(_rel(f))
    assert not bad, f'trade book embedded in public HTML: {bad}'


# ── the gate must be able to go red (positive controls) ──────────────────────

@pytest.mark.parametrize('doc, expect', [
    ({'trade': {'original_qty': 10}}, 'key .trade.original_qty'),
    ({'rows': [{'realizedPL': 1}]}, 'key .rows[].realizedPL'),
    ({'x': {'best_pnl': 1}}, 'key .x.best_pnl'),
    ({'x': {'peak_equity': 1}}, 'key .x.peak_equity'),
    ({'narrative': 'at $44.41 (qty 2262)'}, 'value .narrative'),
    ({'narrative': '1R = $3.41/sh = $7,713'}, 'value .narrative'),
])
def test_positive_controls_go_red(tmp_path, monkeypatch, doc, expect):
    monkeypatch.setattr(sys.modules[__name__], 'REPO', tmp_path)
    (tmp_path / 'data' / 'output').mkdir(parents=True)
    (tmp_path / 'data' / 'output' / 'x.json').write_text(json.dumps(doc))
    hits = scan([tmp_path / 'data' / 'output'])
    assert any(expect in h for h in hits), hits


@pytest.mark.parametrize('doc', [
    {'ticker': 'PL', 'stocks': {'PL': {}, 'CASH': {}}},       # tickers named PL / CASH
    {'trade': {'realized_R': 2.1, 'entry_price': 44.41}},    # R and a per-share quote
    {'narrative': 'Entered at $44.41 with stop $41.00 (1R = $3.41/sh = 7.7% of entry).'},
    {'rows': [{'position_in_52w_range_pct': 77}]},
])
def test_negative_controls_stay_green(tmp_path, monkeypatch, doc):
    monkeypatch.setattr(sys.modules[__name__], 'REPO', tmp_path)
    (tmp_path / 'data' / 'output').mkdir(parents=True)
    (tmp_path / 'data' / 'output' / 'x.json').write_text(json.dumps(doc))
    assert scan([tmp_path / 'data' / 'output']) == []
