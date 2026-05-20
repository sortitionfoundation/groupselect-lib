# HERMES Algorithm

`Algorithm.HERMES` — developed by Matthew Cowie (2026).

**Reference:** M. Cowie, "Improving Allocation Algorithms for Citizens
Assemblies", 4th Year Project Report, School of Informatics,
University of Edinburgh, 2026.

This is the **recommended algorithm** and the default in the GroupSelect App.

## Overview

HERMES extends DREAM by giving the user **per-field control** over the
diversity/uniqueness trade-off. Rather than a single global `pareto_prob`,
each `Diversify` field has its own weight (`pareto_prob` value in
`[0.0, 0.5]`), letting practitioners decide how strictly to enforce each
demographic criterion.

## Motivation

In a Citizens' Assembly, not all demographic fields carry equal importance.
An organiser might want strict gender balance but be willing to tolerate
some age imbalance in order to ensure participants meet more new people.
HERMES makes this optionality explicit and quantitative.

## How it works

The core structure is identical to DREAM (see [DREAM](dream.md) for the
base algorithm). The key differences are:

### Per-field diversity threshold

Inside `evaluate_actions`, for each `Diversify` field, a threshold is
computed:

```
μ = -0.5 + pareto_probs[field_id]
```

A swap action for a given category value is only added to the candidate set
if the current table distribution discrepancy for that value falls below
`μ`. This means:

- `pareto_probs = 0.5` → `μ = 0.0`: any positive discrepancy triggers a
  swap action (strict diversity, equivalent to DREAM).
- `pareto_probs = 0.0` → `μ = -0.5`: only extreme over-representation
  triggers swaps (diversity effectively ignored, meetings prioritised).

### Per-field swap selection

The `select_key` function uses the maximum `pareto_prob` across the
*relevant* diversity fields for the candidate swap (i.e. the fields where
a swap improvement is possible). This prevents lower-weighted fields from
diluting the influence of higher-weighted ones.

The selection probability `γ = max(relevant pareto_probs)` controls
whether a diversity swap or a meetings swap is chosen:

- With probability `γ`: choose the swap with the best diversity score.
- With probability `1 - γ`: choose the swap with the best meeting score.

## Required parameter: `pareto_probs`

Every `Diversify` field must have an entry in `pareto_probs`. The algorithm
raises an exception if any are missing.

```python
settings = {
    "pareto_probs": {
        0: 0.5,   # field index 0: strict diversity
        1: 0.25,  # field index 1: moderate weight
    }
}
```

When using `allocate_pandas`, the keys are **field indices** (integer
column positions in the numpy representation), not column labels. The
`allocate_pandas` function translates column labels to indices internally.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_attempts` | int | 3 | Number of independent candidates |
| `seed` | int or None | None | Random seed |
| `pareto_probs` | dict[int, float] | required | Per-field weights in [0.0, 0.5] |

## Weight guide

| `pareto_prob` | Diversity behaviour | Meeting behaviour |
|---------------|--------------------|--------------------|
| `0.5` | Strict — enforced like DREAM | Reduced (50% of swaps diversity-driven) |
| `0.4` | Strong | Moderate |
| `0.25` | Moderate | Good |
| `0.1` | Lenient | Strong |
| `0.0` | Ignored | Maximised |

!!! note "Implementation note"
    The current implementation contains debug `print()` statements and
    large commented-out blocks from the development phase. These do not
    affect the output but produce console noise. A code cleanup is planned.
