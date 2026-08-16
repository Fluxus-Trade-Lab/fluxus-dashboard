"""Pull the live trade log straight from the Google Sheet.

Why this exists
---------------
The book lived in three places and only one of them was current:

* the browser's localStorage / the Sheet — 355 trades, today
* ``data/portfolio/portfolio_*.csv`` — a hand-made export, whenever Andy
  remembered
* ``data/output/trades/_index.json`` — whatever the last hand-run of
  ``trade_postmortem`` produced, which on 2026-08-17 was 84 days old

Two manual steps in a row is not a pipeline, it is a habit, and the Trade
Journal had been showing a book that ended in May since May. This module
removes the first step: the post-mortem generator can now read the Sheet the
browser writes to, so the only copy that matters is the only copy read.

Credentials
-----------
``FLUXUS_GAS_URL`` and ``FLUXUS_SYNC_TOKEN``, from the environment — never
arguments in a shell history, never a file in the repo. The token is a bearer
credential in a query string, so nothing here logs a URL: errors quote the
status, not the request.

Agreement with the CSV reader
-----------------------------
`trade_parser.parse_csv` is the existing contract and this mirrors it field for
field, sharing its date/number primitives so there is one definition of each.

Both readers leave a blank ``initialStop`` blank. The CSV reader used to
backfill it from the *current* stop; the Apps Script stopped doing that first,
and Andy settled it on 2026-08-17 in the Apps Script's favour — he trails stops
in the tracker, so after the first trail the live stop is not the stop the
position was sized against, and substituting it divides that trade's R by the
wrong number while leaving no trace. Such trades now carry no R at all, which
every reader must render as "not measured" rather than as a zero.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Mapping, Optional, Sequence

import requests

from pipeline.portfolio.trade_parser import Trade, TrimEvent, _parse_date

logger = logging.getLogger(__name__)

ENV_URL = 'FLUXUS_GAS_URL'
ENV_TOKEN = 'FLUXUS_SYNC_TOKEN'

# The Apps Script cold-starts; the browser client allows 15s and this runs in
# CI where a retry costs a whole scheduled run, so it gets more room.
TIMEOUT_S = 45


class SheetsUnavailable(RuntimeError):
    """Raised when the Sheet cannot be read. Never carries the token."""


def _num(v: Any) -> Optional[float]:
    """JSON gives numbers, blanks give None or ''. Strings still parse."""
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v: Any) -> Optional[int]:
    f = _num(v)
    return int(f) if f is not None else None


def _as_date(v: Any) -> Optional[date]:
    if isinstance(v, date):
        return v
    return _parse_date(str(v)) if v else None


def _to_trade(obj: Mapping[str, Any], idx: int) -> tuple[Optional[Trade], bool]:
    """One pulled row → Trade. Returns (trade, backfilled_initial_stop)."""
    ticker = (obj.get('ticker') or '').strip()
    direction = (obj.get('direction') or '').strip().lower()
    entry_date = _as_date(obj.get('entryDate'))
    entry_price = _num(obj.get('entryPrice'))
    original_qty = _int(obj.get('originalQty'))

    if not ticker or entry_date is None or entry_price is None or original_qty is None:
        logger.warning('Row %d (%s): missing required fields, skipping', idx, ticker or '?')
        return None, False
    if direction not in ('long', 'short'):
        logger.warning('Row %d (%s): bad direction %r, skipping', idx, ticker, direction)
        return None, False

    stop_price = _num(obj.get('stopPrice'))
    # Same fallback the CSV reader uses when the stop cell itself is empty.
    final_stop = stop_price if stop_price is not None else entry_price * 0.95

    # Left as None when the sheet has no entry stop. Andy trails stops in the
    # tracker, so substituting the live one would divide that trade's R by a
    # number it was never sized against. The Apps Script stopped doing this
    # first; both readers now agree, and R simply goes missing where it is
    # genuinely unknown.
    initial_stop = _num(obj.get('initialStop'))
    unknown_r = initial_stop is None

    trims: list[TrimEvent] = []
    for t in (obj.get('trims') or []):
        if not isinstance(t, Mapping):
            continue
        d = _as_date(t.get('date'))
        p = _num(t.get('price'))
        q = _int(t.get('qty'))
        ttype = (t.get('type') or '').strip()
        if d and p is not None and q is not None and ttype:
            trims.append(TrimEvent(date=d, price=p, qty=q, type=ttype))
    # The sheet stores trims as written, not as ordered. Every downstream
    # reading — the ladder, the R attribution, exit_date — assumes oldest
    # first, which the CSV layout enforced by column position and a JSON array
    # does not.
    trims.sort(key=lambda t: t.date)

    return Trade(
        ticker=ticker,
        direction=direction,
        sector=(obj.get('sector') or 'Unknown').strip() or 'Unknown',
        entry_date=entry_date,
        entry_price=entry_price,
        original_qty=original_qty,
        current_qty=_int(obj.get('currentQty')) or 0,
        stop_price=final_stop,
        initial_stop=initial_stop,
        closed=bool(obj.get('isClosed')),
        trims=tuple(trims),
    ), unknown_r


def to_trades(stock_trades: Sequence[Mapping[str, Any]]) -> list[Trade]:
    """Convert a pulled ``stockTrades`` payload into Trade records."""
    out: list[Trade] = []
    no_r = 0
    for i, obj in enumerate(stock_trades, start=1):
        trade, unknown_r = _to_trade(obj, i)
        if trade is None:
            continue
        out.append(trade)
        no_r += int(unknown_r)
    if no_r:
        logger.warning(
            '%d of %d trades have no initialStop, so they carry no R. Type the '
            'entry stop into the initialStop column to restore it — it is not '
            'inferred from the live stop, which has since been trailed.',
            no_r, len(out),
        )
    logger.info('Pulled %d trades from the Sheet (%d skipped)',
                len(out), len(stock_trades) - len(out))
    return out


def _diagnose(resp: 'requests.Response', gas_url: str) -> str:
    """Name the failure shape without ever quoting the token.

    Apps Script answers a bad deployment, a login-walled deployment and a bad
    token with three different things, and all three look alike from the status
    line: a 404 page, an HTML sign-in page, and a JSON error respectively.
    """
    from urllib.parse import urlparse

    parts = urlparse(gas_url)
    notes: list[str] = []

    if not parts.path.endswith('/exec'):
        tail = parts.path.rsplit('/', 1)[-1] or '/'
        notes.append(
            f"the URL ends in {tail!r}, not 'exec' — a deployment URL ends "
            "/exec; /dev and the editor link are not callable from CI"
        )
    if resp.history:
        hosts = ' → '.join(dict.fromkeys(urlparse(r.url).netloc for r in resp.history))
        notes.append(f'redirected via {hosts}')
    if 'text/html' in resp.headers.get('content-type', ''):
        body = resp.text[:400].lower()
        if 'accounts.google.com' in body or 'sign in' in body or 'signin' in body:
            notes.append(
                'the response is a Google sign-in page: the deployment is set '
                'to "Anyone with a Google account", which a browser satisfies '
                'and a CI runner cannot. Redeploy with access "Anyone"'
            )
        else:
            notes.append('the response is an HTML page, not the API')

    return '; '.join(notes) or 'the endpoint answered, but not with the API'

def fetch_trades(gas_url: Optional[str] = None,
                 token: Optional[str] = None) -> list[Trade]:
    """Pull the live stock trades. Credentials default to the environment."""
    gas_url = gas_url or os.environ.get(ENV_URL, '').strip()
    token = token or os.environ.get(ENV_TOKEN, '').strip()
    if not gas_url or not token:
        missing = ' and '.join(
            n for n, v in ((ENV_URL, gas_url), (ENV_TOKEN, token)) if not v)
        raise SheetsUnavailable(f'{missing} not set in the environment')

    try:
        resp = requests.get(gas_url, params={'action': 'pull', 'token': token},
                            timeout=TIMEOUT_S)
    except requests.RequestException as e:
        # str(e) on a requests error can embed the full URL, token included.
        raise SheetsUnavailable(f'request failed: {type(e).__name__}') from None

    if resp.status_code != 200:
        # "HTTP 404" on its own sent one debugging session looking at the token
        # when the deployment was the problem. Apps Script fails in a handful
        # of distinguishable ways and the status code alone separates none of
        # them, so say which shape this is. Hosts and paths only — the token
        # rides in the query string, which is why nothing here prints a URL.
        raise SheetsUnavailable(f'HTTP {resp.status_code} — {_diagnose(resp, gas_url)}')

    try:
        data = resp.json()
    except ValueError:
        raise SheetsUnavailable(
            f'response was not JSON — {_diagnose(resp, gas_url)}') from None
    if not data.get('ok'):
        raise SheetsUnavailable(str(data.get('error') or 'pull rejected'))

    return to_trades(data.get('stockTrades') or [])
