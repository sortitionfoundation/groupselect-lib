# Quick Start

## With numpy

```python
import numpy as np
from groupselect import allocate_numpy, FieldMode, Algorithm

# Encode participants as a 2-D integer array.
# Rows = participants, columns = demographic fields.
# Here: 60 participants, 2 fields (gender: 0/1, age bracket: 0/1/2/3).
rng = np.random.default_rng(42)
participants = np.column_stack([
    rng.integers(0, 2, size=60),   # gender (2 categories)
    rng.integers(0, 4, size=60),   # age bracket (4 categories)
])

result = allocate_numpy(
    participants=participants,
    fields={
        0: FieldMode.Diversify,
        1: FieldMode.Diversify,
    },
    # 3 allocation rounds, groups of 6
    n_part_per_group=[6, 6, 6],
    algorithm=Algorithm.HERMES,
    settings={
        "pareto_probs": {
            0: 0.5,  # gender: strict diversity
            1: 0.3,  # age: moderate diversity weight
        },
        "seed": 42,
    },
)

ensemble = result.ensemble
print(f"Meeting score:   {ensemble.calc_meeting_norm_score():.1%}")
print(f"Diversity score: {ensemble.calc_diversity_score(participants):.3f}")
```

## With pandas

```python
import pandas as pd
from groupselect import allocate_pandas, FieldMode, Algorithm

df = pd.read_csv("participants.csv")

result_df = allocate_pandas(
    participants=df,
    fields={
        "gender":     FieldMode.Diversify,
        "age_bucket": FieldMode.Diversify,
        "audio_need": FieldMode.Cluster,
    },
    n_part_per_group=[8, 8, 8],
    algorithm=Algorithm.HERMES,
    settings={
        "pareto_probs": {"gender": 0.5, "age_bucket": 0.4},
        "seed": 0,
    },
)

# result_df is a DataFrame with columns: allocation, group, + original columns
print(result_df.head())
```

Or using the DataFrame accessor:

```python
result_df = df.groupselect.allocate(
    fields={"gender": FieldMode.Diversify, "age_bucket": FieldMode.Diversify},
    n_part_per_group=[8, 8, 8],
    algorithm=Algorithm.HERMES,
    settings={"pareto_probs": {"gender": 0.5, "age_bucket": 0.4}},
)
```

## Using `return_full=True`

```python
ret_part, ret_groups, alloc_result = allocate_pandas(
    participants=df,
    fields={"gender": FieldMode.Diversify},
    n_part_per_group=[8, 8],
    return_full=True,
)
# ret_part: one row per participant per allocation, with 'allocation' and 'group' columns
# ret_groups: one row per group, with list of participants
# alloc_result: AllocatorResult with the full AllocationEnsemble
ensemble = alloc_result.ensemble
```

## Manual allocations

Pre-assign specific participants to specific groups:

```python
result = allocate_numpy(
    participants=participants,
    fields={0: FieldMode.Diversify},
    n_part_per_group=[6],
    manuals={
        5: 0,   # participant 5 always in group 0
        12: 2,  # participant 12 always in group 2
    },
)
```

## Choosing an algorithm

| Algorithm | Best for | Notes |
|-----------|----------|-------|
| `Algorithm.HERMES` | Most use cases | Per-field weights; recommended |
| `Algorithm.DREAM` | Baseline comparison | Uniform 50/50 diversity weight |
| `Algorithm.Legacy` | Legacy compatibility | ⚠ Currently broken for Diversify fields |

## HERMES weight guide

The `pareto_probs` dict maps each `Diversify` field index (numpy) or column
label (pandas) to a float in `[0.0, 0.5]`:

| Value | Effect |
|-------|--------|
| `0.5` | Strict diversity — equivalent to DREAM; swaps only accepted if they maintain or improve demographic balance |
| `0.25` | Balanced — moderate diversity, more meeting optimisation |
| `0.0` | Meetings-first — diversity for this field effectively ignored |

For fields listed as `Cluster` or `Ignore`, no entry in `pareto_probs` is
needed.
