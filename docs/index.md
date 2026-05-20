# GroupSelect Library

`groupselect` is a Python library for partitioning the participants of a
Citizens' Assembly (CA) or other deliberative mini-public into discussion
subgroups. It is the algorithmic backbone of the
[GroupSelect App](https://github.com/sortitionfoundation/groupselect-app).

## What it does

Given a dataset of participants and their demographic attributes, the library
produces a set of *allocations* — partitions of the participants into
fixed-size groups. Each allocation represents one session or round of the
assembly. The library simultaneously optimises two objectives:

- **Diversity**: each group mirrors the full-population demographic
  distribution across the selected fields (e.g. equal gender split, correct
  age-bracket proportions).
- **Uniqueness**: across multiple allocation rounds, participants are paired
  with as many *different* people as possible.

See [Concepts](concepts.md) for a deeper explanation of these objectives and
their trade-off.

## Installation

```bash
pip install groupselect
```

pandas is an optional dependency. Install it to use `allocate_pandas`:

```bash
pip install groupselect pandas
```

## Quick start

```python
import numpy as np
from groupselect import allocate_numpy, FieldMode, Algorithm

# 100 participants, 3 demographic fields (encoded as integers)
participants = np.random.randint(0, 3, size=(100, 3))

result = allocate_numpy(
    participants=participants,
    fields={
        0: FieldMode.Diversify,  # field 0: spread proportionally
        1: FieldMode.Diversify,  # field 1: spread proportionally
        2: FieldMode.Cluster,    # field 2: cluster in same groups
    },
    n_part_per_group=[8, 8, 8],  # 3 allocation rounds, groups of 8
    algorithm=Algorithm.HERMES,
    settings={"pareto_probs": {0: 0.5, 1: 0.3}},
)

print(result.ensemble.calc_meeting_norm_score())
print(result.ensemble.calc_diversity_score(participants[:, :2]))
```

See [Quick Start](quickstart.md) for a more detailed walkthrough.

## Available algorithms

| Algorithm | Description |
|-----------|-------------|
| `Algorithm.Legacy` | Greedy + random-restart (Verpoort 2020) |
| `Algorithm.DREAM` | Pareto-swap heuristic (Barrett & Gal 2024) |
| `Algorithm.HERMES` | DREAM with per-field diversity weights (Cowie 2026) |

See [Algorithms](algorithms/index.md) for details.
