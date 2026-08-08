"""The centaur layer: a machine view, a human view, and a bounded merge.

Built 2026-08-09 after reading Saghafian & Idan, "Effective Generative AI: The
Human-Algorithm Centaur" (HDSR 2024 / arXiv 2406.10942) — the paper
@TailThatWagsDog cites under every chart he publishes.

The paper names our previous arrangement as an anti-pattern. In its taxonomy,
human input that is "used orthogonally to the AI model … by working on a
different set of records than the machine" is **workload partitioning**, which
it distinguishes from centaurs. "I compute, you decide" is exactly that: the
machine emits numbers, the human decides, and the decision evaporates. Nothing
learns.

A centaur requires **symbiotic learning**, which the paper defines by three
properties:

1. Learning uses MULTIPLE inputs, at least one of which is a record of human
   *subjective* judgement — preferences, opinions, decisions — not ground truth.
2. That human input enters the combined estimate directly, not beside it.
3. Its influence is **constrained** by measured expertise and feedback quality,
   rather than assumed.

Property 1 is `log.py` — the dataset of Andy's calls that has never existed.
Property 2 is `blend.py`. Property 3 is `skill.py`, which measures rather than
assumes, because the empirical result that motivates all of this is
counter-intuitive: in the paper's Mayo Clinic experiment the ranking was
**centaur > algorithm > human experts**. The human was *worse than the algorithm
alone* and still improved it. A merge that assumed the human was better would
have destroyed that gain; so would one that ignored him.

A note on what a "view" is here. The machine states a **prediction**, which gets
scored. It never states a recommendation, which would get followed. That
distinction is what keeps this consistent with the standing rule that this
system calculates and Andy decides — the merge informs his decision, it does not
replace it, and no output of this package sizes a position.
"""
