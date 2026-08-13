"""The scoreboard: a paper book, a control, and a kill log with a denominator.

Built 2026-08-13 to replicate his method rather than his numbers. What is
replicable from what he has published:

  * base is plain SPY, long, because eight alternatives lost to it
  * the overlay is DEFINED RISK, and convexity comes from position structure
    rather than from a forecast -- "if a signal needed a forecast to work, we
    consistently found it didn't perform"
  * the objective is DRAWDOWN, not return
  * every rule beats its own control on an out-of-sample split or it dies, and
    the death count is published

What is NOT replicable, and must not be guessed at: his dislocation definition,
his structure selection, his sizing, and his exits. None of that is public. Any
module here that claimed to reproduce SCE's -4.9% would be fabricating the
half he kept.

So this package supplies the harness and our own candidates go through it. If
seventeen of ours die, the replication has worked.
"""
