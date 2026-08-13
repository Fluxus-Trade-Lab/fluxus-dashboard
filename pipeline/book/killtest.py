"""The kill test: a rule must beat its own control out of sample, or it dies.

His discipline, 2026-08-12:

    "Every rule in SCE had to survive a kill-test before it qualified. 17
     volatility signals died. A leverage overlay died. Eight alternative base
     assets lost to plain SPY. What was left was what beat its own control on
     out-of-sample splits — not what looked good on a backtest."

Two things in that paragraph do the work, and only one of them is the test.

**The control is the book WITHOUT that rule**, not the market. "Beat its own
control" is a much harder bar than "made money": a rule that only reproduces
what the base position already did adds cost and no information, and against
SPY it would still look fine.

**The denominator is published.** Seventeen deaths is not an aside — it is the
number that makes the survivors mean anything, and it is the number almost
nobody reports. Our own arithmetic says twenty untracked probes throw at least
one false positive 64% of the time, so a survivor from an uncounted search is
not evidence. `killlog.py` exists to keep that count.

## What a verdict may say

Never a bare boolean, and never "passed". Three outcomes:

  ``survived``     beat its control out of sample, by an interval excluding zero
  ``killed``       did not, on data it had never seen
  ``undecided``    the out-of-sample window cannot separate them either way

`undecided` is not a soft kill and must never be reported as one. It means the
question is open and the sample is too short — the same distinction
`profile.patterns` draws between failed and unmeasurable, and `events` between
no and unknown.

## The split

Time-ordered, never shuffled. A rule tuned on the first 70% of history and
tested on the last 30% has still seen the first 70%; a shuffled split lets it
see tomorrow, which is the most common way a backtest lies.
"""
from __future__ import annotations

from . import metrics as M

# Fraction of history reserved for fitting. The remainder is untouched until the
# verdict. 0.70 is conventional; it is stated here rather than buried, and the
# split index is reported with every verdict so a reader can see how many days
# the decision actually rests on.
DEFAULT_TRAIN = 0.70

# Below this many out-of-sample days a verdict is not attempted. A drawdown
# comparison over three weeks is a comparison of which week was worse.
MIN_OOS_DAYS = 60

VERDICTS = ("survived", "killed", "undecided")


def split(n: int, train: float = DEFAULT_TRAIN) -> int:
    """Index where out-of-sample begins. Time-ordered, never shuffled."""
    if not 0.0 < train < 1.0:
        raise ValueError("train fraction must be strictly between 0 and 1")
    return int(n * train)


def apply_rule(base: list[float], overlay: list[float],
               active: list[bool]) -> list[float]:
    """The book's returns: base every day, plus the overlay when the rule says so.

    `active[i]` must be decidable from information available BEFORE day i's
    return. This function cannot check that — nothing can, from the arrays alone
    — so every caller that builds an `active` series owes a comment saying which
    session's data it was computed from. Lookahead is the failure this whole
    module exists to catch and it is the one it cannot detect for you.
    """
    if not (len(base) == len(overlay) == len(active)):
        raise ValueError(
            f"base {len(base)}, overlay {len(overlay)}, active {len(active)} — "
            "all three are daily series over the same dates and must align")
    return [b + (o if a else 0.0) for b, o, a in zip(base, overlay, active)]


def kill_test(name: str, base: list[float], overlay: list[float],
              active: list[bool], train: float = DEFAULT_TRAIN,
              block: int = M.DEFAULT_BLOCK, draws: int = M.DEFAULT_DRAWS,
              seed: int = 7) -> dict:
    """Run a candidate rule against its own control, out of sample.

    The control is the same book with this rule switched off — `base` alone.
    Both curves are evaluated only on the out-of-sample tail; the in-sample
    figures are computed and reported too, precisely so a rule that looks
    wonderful in training and dies in test is visible as that rather than as a
    plain failure.
    """
    if not (len(base) == len(overlay) == len(active)):
        raise ValueError("base, overlay and active must be the same length")
    i = split(len(base), train)
    book = apply_rule(base, overlay, active)

    oos_book, oos_ctrl = book[i:], base[i:]
    n_oos = len(oos_book)
    n_fired_oos = sum(1 for a in active[i:] if a)

    result = {
        "rule": name, "n_days": len(base), "split_index": i,
        "train_fraction": train,
        "n_oos_days": n_oos, "n_fired_total": sum(active),
        "n_fired_oos": n_fired_oos,
        "in_sample": {"book": M.summary(book[:i]), "control": M.summary(base[:i])},
        "out_of_sample": {"book": M.summary(oos_book),
                          "control": M.summary(oos_ctrl)},
    }

    if n_oos < MIN_OOS_DAYS:
        return {**result, "verdict": "undecided", "advantage": None,
                "note": (f"{n_oos} out-of-sample days; {MIN_OOS_DAYS} needed "
                         f"before a drawdown comparison is a comparison rather "
                         f"than a question about which week was worse")}
    if n_fired_oos == 0:
        return {**result, "verdict": "undecided", "advantage": None,
                "note": (f"the rule never fired in the {n_oos} out-of-sample "
                         f"days — it fired {sum(active)} times in sample. There "
                         f"is nothing to test, which is not the same as failing")}

    adv = M.drawdown_advantage(oos_book, oos_ctrl, block=block, draws=draws,
                               seed=seed)
    if adv["ci_low"] > 0:
        verdict = "survived"
    elif adv["ci_high"] < 0:
        verdict = "killed"
    else:
        verdict = "undecided"
    return {**result, "verdict": verdict, "advantage": adv,
            "note": _explain(verdict, name, adv, n_fired_oos, n_oos)}


def _explain(verdict: str, name: str, adv: dict, fired: int, n: int) -> str:
    """A whole sentence per branch."""
    where = f"fired {fired} of {n} out-of-sample days"
    if verdict == "survived":
        return (f"{name} survived: {where}, drawdown advantage "
                f"{adv['advantage'] * 100:+.1f} points, interval "
                f"[{adv['ci_low'] * 100:+.1f}, {adv['ci_high'] * 100:+.1f}] "
                f"excludes zero")
    if verdict == "killed":
        return (f"{name} killed: {where} and took MORE damage than the book "
                f"without it, {adv['advantage'] * 100:+.1f} points, interval "
                f"[{adv['ci_low'] * 100:+.1f}, {adv['ci_high'] * 100:+.1f}]")
    return (f"{name} undecided: {where}, advantage "
            f"{adv['advantage'] * 100:+.1f} points but the interval "
            f"[{adv['ci_low'] * 100:+.1f}, {adv['ci_high'] * 100:+.1f}] "
            f"straddles zero — open, not failed")


def shuffled_control(name: str, base: list[float], overlay: list[float],
                     active: list[bool], seed: int = 7, **kw) -> dict:
    """The same test against a rule that fires the same number of times at random.

    A rule can beat `base` merely by being ON during a calm stretch. Holding the
    firing COUNT fixed and moving WHEN it fires asks the sharper question: does
    the timing carry anything, or only the exposure?
    """
    import random
    rng = random.Random(seed)
    k = sum(active)
    idx = set(rng.sample(range(len(active)), k)) if k else set()
    return kill_test(f"{name} [timing-shuffled]", base, overlay,
                     [i in idx for i in range(len(active))], seed=seed, **kw)
