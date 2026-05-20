# DREAM Algorithm

`Algorithm.DREAM` — based on Barrett & Gal (2024).

**Reference:** J. Barrett and K. Gal, "DREAM: A Heuristic for Group
Allocation in Deliberative Democracy Events", arXiv:2410.21451.

## How it works

DREAM processes allocation rounds sequentially, maintaining a
`previous_meetings` dictionary that tracks how many times each participant
pair has been in the same group. This makes meeting optimisation cumulative
across rounds.

**Per round:**

1. **Random shuffle** all participant indices.
2. **Greedy seat assignment**: place participants in a round-robin manner
   across groups, filling cluster participants first if a Cluster field is
   present.
3. **Pareto swap phase** (one or more iterations):
   - For each participant in shuffled order, identify candidate swap
     partners in other groups.
   - A candidate swap is *Pareto-improving* if it does not worsen either
     the diversity score or the meeting score relative to the current state
     (and improves at least one).
   - Among valid candidates, select the swap using a probabilistic
     `pareto_prob` parameter: with probability `pareto_prob` choose the
     swap maximising diversity; with probability `1 - pareto_prob` choose
     the swap maximising meeting uniqueness.
   - Execute the selected swap and update cached evaluations.

The swap phase can be repeated multiple times per round (`swap_rounds`,
currently hard-coded to 1 in the entry function).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_attempts` | int | 3 | Number of independent ensemble candidates |
| `seed` | int or None | None | Random seed |

Note: `pareto_prob` is currently hard-coded to `0.5` inside the algorithm
and is not exposed via the public API. Use `Algorithm.HERMES` for
user-configurable weights.

## Diversity evaluation

For each group and each Diversify field, the algorithm computes:

- The *ideal distribution* of each category value across all participants.
- The *current distribution* in the group.
- For each overrepresented category value, it identifies which other values
  are underrepresented; these define candidate *swap actions*.

A swap is considered diversity-improving if it moves the table distribution
closer to the ideal.

## Strengths and limitations

- Cross-round meeting awareness via `previous_meetings`.
- Pareto swap phase effectively balances diversity and uniqueness.
- `pareto_prob` is fixed at 0.5 — no per-field user control.
- Currently non-functional for Diversify fields (see warning above).
- Use `Algorithm.HERMES` for production use.
