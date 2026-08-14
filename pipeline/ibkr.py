"""One place to open an IBKR connection, and one reason it exists.

`ib_async.IB.connect()` defaults to `fetchFields=StartupFetch.ALL`. On every
connect it therefore issues, before returning: positions, open orders, completed
orders, executions, and account updates for **each** sub-account. This account
has four.

None of our scripts read any of that. They are market-data readers — chains,
bars, ticks, greeks. The startup fetch is pure overhead on a good day and a hang
on a bad one, and it hung on two consecutive post-close runs:

    [2026-08-13 05:30:01 JST] running GEX pull for 20260812 (post-close)
    positions request timed out
    open orders request timed out
    completed orders request timed out
    account updates for U20120333 request timed out
    ... four sub-accounts ...
    executions request timed out
    [2026-08-13 05:45:34 JST] TIMEOUT after 900s: gex_levels — killed

    [2026-08-14 05:30:02 JST] running GEX pull for 20260813 (post-close)
    [2026-08-14 05:45:36 JST] TIMEOUT after 900s: gex_levels — killed

Two sessions of settled chain lost, and with them both days' Market Profile and
the facilitation gate that depends on it. The 900s ceiling did its job twice and
was treating a symptom: **the request that hangs is one we never wanted.**

`connect()` here passes `StartupFetchNONE`. A script that genuinely needs
account state can ask for exactly the fields it needs and say why.
"""
from __future__ import annotations

# The ports we try, in order: TWS live, then the two Gateway defaults.
PORTS = (7496, 4001, 4002)


def connect(client_id: int, *, timeout: int = 10, ports=PORTS,
            fetch=None, readonly: bool = True):
    """Return a connected `IB`, or raise. No account/order/position fetch.

    `readonly` defaults True because nothing in this repo places an order, and a
    read-only session cannot be the thing that does it by accident.

    Raises rather than returning None: a caller that forgets to check a None is
    a traceback several steps away from the real problem, and every one of these
    scripts is unusable without a connection anyway.
    """
    from ib_async import IB, StartupFetchNONE

    ib = IB()
    last = None
    for port in ports:
        try:
            ib.connect("127.0.0.1", port, clientId=client_id, timeout=timeout,
                       readonly=readonly,
                       fetchFields=StartupFetchNONE if fetch is None else fetch)
            return ib
        except Exception as e:      # noqa: BLE001 - the next port is the retry
            last = e
    raise ConnectionError(
        f"no IBKR endpoint on {ports} (clientId {client_id}) — is TWS logged "
        f"in? last error: {last}")
