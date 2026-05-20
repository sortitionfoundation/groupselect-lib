# GroupSelect Library — LLM context

## Purpose

`groupselect` is a Python library for partitioning the participants of a
Citizens' Assembly (CA) or other deliberative mini-public into discussion
subgroups. It optimises two competing objectives:

1. **Diversity** — each subgroup should demographically mirror the full
   population across user-chosen fields (e.g. gender, age bracket).
2. **Uniqueness** — across multiple allocation rounds, maximise the number
   of distinct participant-pair meetings.

This library is consumed by `groupselect-app` (PySide6 desktop GUI) and
can also be used directly by researchers or custom tooling.

## Package structure

```
groupselect/
├── __init__.py           # Public re-exports
├── field_mode.py         # FieldMode enum
├── allocation.py         # Core data types + scoring
├── allocate_numpy.py     # Main numpy entry point
├── allocate_pandas.py    # Pandas wrapper + DataFrame accessor
└── algorithms/
    ├── __init__.py       # Algorithm enum + dispatch table
    ├── algorithm_legacy.py
    ├── algorithm_dream.py
    └── algorithm_hermes.py
```

## Key types

| Type | Description |
|------|-------------|
| `FieldMode` | `Ignore`, `Diversify`, `Cluster`, `Keep` (reserved) |
| `Algorithm` | `Legacy`, `DREAM`, `HERMES` |
| `ParticipantGroup` | `list[int]` of participant row-indices in one group |
| `Allocation` | `list[ParticipantGroup]` — one full round of groups |
| `AllocationEnsemble` | `list[Allocation]` — multiple rounds |
| `AllocatorResult` | Wraps an `AllocationEnsemble` in `.ensemble` |

## Public API

### `allocate_numpy`
```python
allocate_numpy(
    participants: np.ndarray[int],  # shape (n_participants, n_fields)
    fields: dict[int, FieldMode],   # col_index → FieldMode
    n_part_per_group: int | Iterable[int],
    manuals: dict[int, int] | None = None,
    algorithm: Algorithm | str = Algorithm.Legacy,
    progress_func: Callable | None = None,
    settings: dict | None = None,
) -> AllocatorResult
```

`n_part_per_group` as a list means one allocation per entry (the list
length equals the number of allocation rounds in the output ensemble).

### `allocate_pandas`
```python
allocate_pandas(
    participants: pd.DataFrame,
    fields: dict[Hashable, FieldMode],
    n_part_per_group: int | Iterable[int],
    ...
    return_full: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame, AllocatorResult]
```

`return_full=True` returns `(participants_df, groups_df, AllocatorResult)`.

### `df.groupselect.allocate(...)` — pandas accessor forwarding to the above.

## Algorithms

### Legacy (`Algorithm.Legacy`)

Greedy deterministic with random restarts. Sorts participants by
clustering/diversity field values, then places each participant into the
group with the smallest current count of their feature value. Runs
`n_attempts` random shuffles; selects the resulting ensemble with the most
unique pairwise meetings.

**Settings:** `n_attempts=100`, `seed=None`


### DREAM (`Algorithm.DREAM`)

Based on Barrett & Gal (2024), https://arxiv.org/pdf/2410.21451.
For each allocation round: random shuffle → greedy seat assignment →
Pareto swap phase. The swap phase iterates over each participant and
proposes swaps with participants in other groups; a swap is accepted if it
is Pareto-improving on diversity and/or meeting uniqueness. A
`pareto_prob=0.5` float (hard-coded) controls which objective takes
priority stochastically. The `previous_meetings` dict persists across
rounds so diversity/meeting optimisation is cumulative.

**Settings:** `n_attempts=3`, `seed=None`

### HERMES (`Algorithm.HERMES`) — recommended; default in groupselect-app

Developed by Matthew Cowie (2026 MSc thesis, Univ. of Edinburgh) as an
extension of DREAM. The key addition is **per-field diversity weights**:
each `Diversify` field has its own `pareto_prob` float in `[0.0, 0.5]`.

- `0.5` → strict diversity enforcement (equivalent to DREAM at 0.5)
- `0.0` → diversity effectively ignored; meetings maximised

The weight controls a threshold `μ = -0.5 + pareto_prob` used inside
`evaluate_actions`. A table distribution discrepancy must exceed `μ` to
trigger a corrective swap action; lower weight = higher tolerance = more
freedom for meeting optimisation.

**Settings:** `n_attempts=3`, `seed=None`,
`pareto_probs: dict[int, float]` (required for all `Diversify` fields)

**⚠ Note:** Implementation contains debug `print()` statements and large
commented-out blocks left from the development phase. A code cleanup is
planned.

## FieldMode values

| Mode | Behaviour |
|------|-----------|
| `Ignore` | Field ignored during allocation |
| `Diversify` | Proportional distribution across groups (mirror population) |
| `Cluster` | Keep participants with the target value in the same groups |
| `Keep` | Reserved for future use; not implemented |

## AllocationEnsemble scoring

| Method | Returns | Description |
|--------|---------|-------------|
| `calc_meeting_rel_score()` | float | Fraction of all pairs that met ≥ once |
| `calc_meeting_norm_score()` | float [0,1] | Normalised uniqueness score |
| `calc_diversity_score(data)` | float | Sum of per-field L1 deviations (lower = better) |
| `calc_pair_occurrences()` | Counter | `{n_meetings: n_pairs}` |
| `calc_meetings()` | dict | `{pid: {other_pid: n_times_met}}` |

`calc_meeting_norm_score` normalises between the worst case (all rounds
assign identical groups — only `max(pairs_per_round)` unique pairs) and
the best case (all rounds have fully distinct groups — `sum(pairs_per_round)`
unique pairs).

## Known issues

1. **`allocate_pandas.py:27`:** Stray `print("enough")` debug line.
2. **`algorithm_hermes.py`:** Debug `print("6")` (~line 185) and
   `print(meet0, ...)` (~line 340).
3. **`FieldMode.Keep`:** Defined but not implemented in any algorithm.
4. **`analysis/notebook.py`:** Uses outdated API names (`"heuristic"`,
   `FieldMode.Diversify`).
5. **`algorithm_legacy.py`:** Large commented-out blocks are
   student-introduced and can be cleaned up.
