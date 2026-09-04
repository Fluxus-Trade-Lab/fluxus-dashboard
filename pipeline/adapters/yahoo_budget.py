"""One vendor, one budget: the shared throttle state for every Yahoo caller.

The pipeline talks to Yahoo from at least six places in a night -- the
universe enrichment sweep, the fundamentals store, the ticker fetcher, the
Delayed-EP scan, asset signals, name cards. Until now each one carried its own
retry loop and its own idea of how bad things were, so the fundamentals store
could detect a wall (40 consecutive failures, `walled: true`) while the OHLC
sweep, blind to that, kept hammering the same host at full speed. Yahoo does
not see six modules. It sees one IP.

What this module adds is small on purpose:

  * a **shared** backoff clock -- whoever notices the throttle sets it, and
    every other caller waits it out before its next batch;
  * **exponential** waiting, because the measured throttle window outlasts a
    linear one (2026-08-18: 20s and 40s were not enough, every batch of the
    third round came back 429);
  * a name for what happened. `yf.download` swallows HTTP status and hands
    back an empty frame, so "throttled" and "this ticker was delisted in 2019"
    arrive looking identical. A batch that returns *nothing at all* is the
    signature of a refusal, not of five thousand simultaneous delistings, and
    the ledger deserves to say which one it saw.

This is deliberately NOT a token bucket. A bucket needs a rate we do not know
-- Yahoo publishes none, and the wall moves with the hour and the IP. What we
do know is what a refusal looks like after the fact, so this reacts rather
than predicts.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Substrings that appear in a vendor refusal. Matched case-insensitively
# against the exception text, because that is the only channel yfinance
# leaves open: it raises no typed error for a 429 and returns no status code.
THROTTLE_MARKERS = (
    "429",
    "too many requests",
    "rate limit",
    "ratelimit",
    "invalid crumb",
    "401",
    "unauthorized",
)

# Waits, in seconds, for the 1st, 2nd, 3rd... refusal in a row. Capped rather
# than doubling forever: past ~10 minutes the night's window is gone anyway
# and a run that reports failure early is worth more than one that sleeps
# through its slot.
_BACKOFF_LADDER = (30, 60, 120, 300, 600)

# A batch is judged "refused" when this share or more of it came back empty.
# Below it, misses are ordinary dataless names (delisted, halted, too new);
# the healthy floor is ~2% of the universe.
_REFUSAL_SHARE = 0.50


def looks_like_throttle(err: object) -> bool:
    """Does this exception read as a vendor refusal rather than missing data?"""
    if err is None:
        return False
    text = str(err).lower()
    return any(m in text for m in THROTTLE_MARKERS)


class YahooBudget:
    """Shared, process-wide backoff state. Thread-safe; never raises."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._backoff_until = 0.0
        self._streak = 0          # consecutive refusals, drives the ladder
        self._refusals = 0        # total, for the ledger
        self._waited_s = 0.0      # total time spent waiting, for the ledger

    # -- reporting ------------------------------------------------------

    def state(self) -> dict:
        """A snapshot for the run ledger. A night that waited should say so."""
        with self._lock:
            return {
                "refusals": self._refusals,
                "waited_s": round(self._waited_s, 1),
                "backing_off": self._backoff_until > time.time(),
            }

    # -- the two calls every Yahoo caller makes -------------------------

    def before_batch(self, label: str = "") -> float:
        """Wait out any backoff another caller set. Returns seconds waited.

        The remaining time is decremented rather than re-read from the clock
        each round: a sleep that returns early (a signal, a patched clock in a
        test) would otherwise turn this into a busy-loop that never exits.
        A backoff another thread extends mid-wait is caught on the next batch,
        which is soon enough -- this is a brake, not a barrier.
        """
        with self._lock:
            remaining = self._backoff_until - time.time()
        if remaining <= 0:
            return 0.0
        logger.warning(
            "yahoo budget: %s holding %.0fs -- another caller hit the wall",
            label or "batch", remaining)
        waited = 0.0
        while remaining > 0:
            chunk = min(remaining, 30.0)
            time.sleep(chunk)
            remaining -= chunk
            waited += chunk
        with self._lock:
            self._waited_s += waited
        return waited

    def note_batch(self, requested: int, returned: int,
                   err: Optional[BaseException] = None,
                   label: str = "") -> bool:
        """Record how a batch went. Returns True if it read as a refusal.

        Two signatures count as refusal: an exception carrying a throttle
        marker, or a batch that came back all but empty. Anything else counts
        as contact with the vendor and clears the streak -- a partially
        successful batch means the host is answering us.
        """
        refused = False
        if err is not None and looks_like_throttle(err):
            refused = True
        elif requested > 0 and returned <= requested * (1 - _REFUSAL_SHARE):
            refused = True

        with self._lock:
            if not refused:
                self._streak = 0
                return False
            self._refusals += 1
            self._streak += 1
            wait = _BACKOFF_LADDER[min(self._streak, len(_BACKOFF_LADDER)) - 1]
            self._backoff_until = max(self._backoff_until, time.time() + wait)

        logger.warning(
            "yahoo budget: %s refused (%d/%d returned%s) -- backing off %ds "
            "(refusal #%d in a row, applies to every Yahoo caller)",
            label or "batch", returned, requested,
            f", {type(err).__name__}" if err is not None else "",
            wait, self._streak)
        return True

    # -- test/ops seam --------------------------------------------------

    def reset(self) -> None:
        with self._lock:
            self._backoff_until = 0.0
            self._streak = 0
            self._refusals = 0
            self._waited_s = 0.0


#: The one budget. Import this, do not build your own -- a second instance is
#: a second opinion about a host that only has one.
BUDGET = YahooBudget()
