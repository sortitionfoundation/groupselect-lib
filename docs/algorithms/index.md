# Algorithms

GroupSelect provides three algorithms, selectable via the `Algorithm` enum.

## Comparison

| Algorithm | Diversity control | Meeting optimisation | Multi-round aware | Notes |
|-----------|------------------|---------------------|-------------------|-------|
| Legacy | Per-field (binary) | Basic (random restart) | No | ⚠ Broken |
| DREAM | Uniform (Pareto swap) | Pareto swap | Yes | Stable |
| HERMES | Per-field weighted | Pareto swap | Yes | Recommended |

## Common concepts

### Allocation rounds

All algorithms accept `n_part_per_group` as a list. Each entry in the list
produces one `Allocation` (one session/round). The list length is therefore
the number of rounds.

### Random seed

Pass `seed` in `settings` for reproducible results. The same seed and
participants produce identical output.

### Manual allocations

The `manuals` argument (`{participant_index: group_index}`) forces specific
participants into specific groups before the algorithm runs. The algorithm
fills the remaining seats around them.

### Progress callback

Pass `progress_func` to receive integer call-backs with the current
iteration count. Used by the app's progress bar.

---

See the individual algorithm pages for details:

- [Legacy](legacy.md)
- [DREAM](dream.md)
- [HERMES](hermes.md) ← recommended
