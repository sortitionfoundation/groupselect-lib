# Legacy Algorithm

`Algorithm.Legacy` — developed by P.C. Verpoort (2020).

!!! warning "Known bug"
    This algorithm currently references `FieldMode.Diversify_1`,
    `Diversify_2`, and `Diversify_3`, which do not exist in the current
    `FieldMode` enum. Calling it with any `Diversify` fields raises
    `AttributeError`. This is a regression introduced during a later edit.
    The fix is to replace these references with `FieldMode.Diversify`.

## How it works

1. **Re-index field values** by frequency (most common value → index 0).
2. **Sort participants** using `numpy.lexsort` on the combined list of
   Cluster and Diversify fields.
3. **Greedy placement**: iterate over participants in sorted order; for each
   participant, find the group (from non-full groups) that currently has the
   fewest members with their specific field value. Ties broken by choosing
   the emptiest group.
4. **Random restart**: the above process is seeded with a shuffled
   participant order. Repeat `n_attempts` times.
5. **Ensemble selection**: randomly sample `n_allocation_rounds` allocations
   (one per requested group size) from the set of attempts, repeat
   `n_attempts` times, and return the sample with the most total unique
   pairwise meetings.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_attempts` | int | 100 | Number of random-restart attempts |
| `seed` | int or None | None | Random seed for reproducibility |

## Clustering

When a Cluster field is present, participants sharing the target field
value are preferentially placed in the same groups. The algorithm tracks
whether there is enough capacity in the "cluster groups" to accommodate
all clustering participants, expanding the eligible group set only when
necessary.

## Strengths and limitations

- Simple and fast.
- No cross-round meeting awareness (each allocation is independent).
- The greedy approach guarantees diversity within a single allocation but
  does not optimise meeting uniqueness across rounds.
- Currently non-functional for Diversify fields (see warning above).
