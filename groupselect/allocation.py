"""Data structures for allocations and metrics computed over them."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from functools import lru_cache
from itertools import combinations
from math import comb

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None


def _encode_participants_data(
    participants_data: np.ndarray[int] | pd.DataFrame,
) -> np.ndarray:
    """Convert a participants-data table to an integer-coded ndarray.

    Passes plain ndarrays through unchanged; category-encodes a DataFrame's
    columns (each column becomes its `pandas` category codes).
    """
    if pd is not None and isinstance(participants_data, pd.DataFrame):
        return (
            participants_data.astype("category")
            .apply(lambda col: col.cat.codes)
            .to_numpy()
        )
    return participants_data


def _prepare_field_stats(
    values_field: np.ndarray,
) -> tuple[np.ndarray, int, np.ndarray]:
    """Encode one field's population-wide values for the diversity score.

    Returns `(inverse, n_values, share_full)`: `inverse` maps each participant
    ID (by position) to a category code, `n_values` is the number of distinct
    categories, and `share_full` is the population-wide share of each
    category. Computing this once per field and threading it down through
    `Allocation`/`ParticipantGroup` avoids re-deriving it for every group.
    """
    values, inverse = np.unique(values_field, return_inverse=True)
    counts_full = np.bincount(inverse)
    share_full = counts_full / len(values_field)
    return inverse, len(values), share_full


def _mean_over_fields(
    participants_data: np.ndarray[int] | pd.DataFrame,
    single_field_score: Callable[[np.ndarray], float],
) -> float:
    """Return the mean of `single_field_score` over every field's population column."""
    participants_data = _encode_participants_data(participants_data)
    fields = list(participants_data.T)
    if not fields:
        return 0.0
    return sum(single_field_score(col) for col in fields) / len(fields)


@lru_cache(maxsize=None)
def _chance_deviation_single_field(
    counts_full: tuple[int, ...],
    group_size: int,
    n_samples: int = 2000,
    seed: int = 0,
) -> float:
    """Estimate a random group's expected L1 deviation from population shares.

    Draws `n_samples` random groups of `group_size` via multivariate
    hypergeometric sampling (without replacement) from a population with
    the given per-category counts, and returns the average raw deviation —
    i.e. how far off a *uniformly random* group of this size would
    typically be. Used as the "0%" (chance) reference for
    `calc_diversity_norm_score`, in place of an adversarial worst case: the
    adversarial version is dominated by however small the rarest category
    happens to be, and jumps sharply whenever a category's count crosses a
    group-size multiple — this is smooth in the population's shares
    instead, so a near-singleton category barely moves it.

    Memoized on `(counts_full, group_size)`: this only depends on the
    population's per-category counts for a field and the group size, not
    on which participants are actually in any particular group, so every
    group of the same size (the common case within one allocation, or
    across a whole ensemble) shares one cached estimate rather than each
    re-simulating it. 2000 samples is already stable to within ~1-2% of
    the estimate; the fixed default seed keeps repeated calls deterministic.
    """
    counts = np.array(counts_full)
    share_full = counts / counts.sum()
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_hypergeometric(counts, group_size, size=n_samples)
    shares = draws / group_size
    return float(np.abs(shares - share_full).sum(axis=1).mean())


def _normalize_diversity_score(score: float, best: float, worst: float) -> float:
    """Rescale a raw diversity deviation against a best case and a chance baseline.

    Mirrors `AllocationEnsemble.calc_meeting_norm_score`'s min/max rescaling,
    flipped since a *lower* raw deviation is better here: `best` (the
    lowest achievable deviation) maps to 1.0. `worst` is a chance
    baseline — the expected deviation of a uniformly random allocation, not
    a hard ceiling — so a result below it (worse than chance) is a
    meaningful, valid outcome and is deliberately *not* clipped to 0; only
    the top is clipped to 1.0, since `best` is itself an estimated (and for
    `Allocation`/`AllocationEnsemble`, possibly loose) bound.
    """
    if worst <= best:
        return 1.0
    return float(min((worst - score) / (worst - best), 1.0))


class ParticipantGroup(list[int]):
    """A single group of participant IDs."""

    def calc_diversity_score_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return this group's L1 distance from the population shares, for one field.

        `inverse`, `n_values`, and `share_full` are the population-wide
        encoding of a single field, as produced by `_prepare_field_stats`.
        This is the innermost term of the diversity score (DREAM's ∆_{j,d})
        and needs no further normalisation — a single group has nothing to
        average over.
        """
        counts_group = np.bincount(inverse[self], minlength=n_values)
        share_group = counts_group / len(self)
        return np.abs(share_full - share_group).sum()

    def calc_diversity_score_best_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return the best a group this size could do, for one field.

        Rounds the population shares to the nearest integer composition
        reachable by a group of this size, via the largest-remainder
        (Hamilton) apportionment method — provably the integer composition
        closest (in L1) to the population shares, i.e. the "100%" reference
        used by `calc_diversity_norm_score`. Depends only on this group's
        size, not on which participants are actually in it.
        """
        n = len(self)
        ideal = share_full * n
        base = np.floor(ideal).astype(int)
        remainder = n - base.sum()
        if remainder > 0:
            # Give the leftover slots to the categories with the largest
            # fractional remainders (largest-remainder method).
            order = np.argsort(-(ideal - base))
            base[order[:remainder]] += 1
        share_best = base / n
        return np.abs(share_full - share_best).sum()

    def calc_diversity_score_worst_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return a random group's expected deviation, for one field (chance baseline).

        The "0%" reference used by `calc_diversity_norm_score`: how far off
        a *uniformly random* group of this size would typically be from the
        population shares, not an adversarial worst case. See
        `_chance_deviation_single_field` for why, and for the caching that
        keeps this cheap. Depends only on this group's size and the
        population's per-category counts, not on which participants are
        actually in it.
        """
        counts_full = tuple(np.bincount(inverse, minlength=n_values).tolist())
        return _chance_deviation_single_field(counts_full, len(self))

    def calc_diversity_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this group's diversity score, meaned across all fields.

        `participants_data` covers the whole population, indexed by
        participant ID, same as `AllocationEnsemble.calc_diversity_score` —
        only the rows for this group's own participants end up used.
        """
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_score_best(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the best this group's size could do, meaned across fields."""
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_best_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_score_worst(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return a random group's expected deviation, meaned across fields."""
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_worst_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_norm_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this group's diversity score normalised to its estimated range.

        1.0 = at (or beyond) the best a group this size could do; 0.0 = no
        better than a uniformly random group of the same size (chance
        baseline) — a negative result means worse than chance, which is a
        meaningful outcome, not an error. See `calc_diversity_score_best`/
        `_worst` for how those references are estimated.
        """
        return _normalize_diversity_score(
            self.calc_diversity_score(participants_data),
            self.calc_diversity_score_best(participants_data),
            self.calc_diversity_score_worst(participants_data),
        )


class Allocation(list[ParticipantGroup]):
    """A full allocation of participants into groups."""

    def calc_diversity_score_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return the mean per-group diversity deviation, for one field.

        See `ParticipantGroup.calc_diversity_score_single_field` for the
        arguments. This is DREAM's mean_j(∆_{j,d}) for a fixed field d.
        """
        return sum(
            group.calc_diversity_score_single_field(inverse, n_values, share_full)
            for group in self
        ) / len(self)

    def calc_diversity_score_best_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return the mean best-case deviation across this allocation's groups.

        See `ParticipantGroup.calc_diversity_score_best_single_field`.
        """
        return sum(
            group.calc_diversity_score_best_single_field(inverse, n_values, share_full)
            for group in self
        ) / len(self)

    def calc_diversity_score_worst_single_field(
        self,
        inverse: np.ndarray,
        n_values: int,
        share_full: np.ndarray,
    ) -> float:
        """Return the mean chance-baseline deviation across this allocation's groups.

        See `ParticipantGroup.calc_diversity_score_worst_single_field`.
        """
        return sum(
            group.calc_diversity_score_worst_single_field(inverse, n_values, share_full)
            for group in self
        ) / len(self)

    def calc_diversity_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this allocation's diversity score, meaned across all fields.

        `participants_data` covers the whole population, indexed by
        participant ID, same as `AllocationEnsemble.calc_diversity_score`.
        """
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_score_best(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the best this allocation's groups could do, meaned across fields."""
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_best_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_score_worst(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this allocation's chance-baseline deviation, meaned across fields."""
        return _mean_over_fields(
            participants_data,
            lambda col: self.calc_diversity_score_worst_single_field(
                *_prepare_field_stats(col)
            ),
        )

    def calc_diversity_norm_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this allocation's diversity score normalised to its estimated range.

        1.0 = at (or beyond) the best this allocation's groups could do;
        0.0 = no better than a uniformly random allocation of the same
        shape (chance baseline) — a negative result means worse than
        chance, which is a meaningful outcome, not an error. See
        `calc_diversity_score_best`/`_worst` for how those references are
        estimated.
        """
        return _normalize_diversity_score(
            self.calc_diversity_score(participants_data),
            self.calc_diversity_score_best(participants_data),
            self.calc_diversity_score_worst(participants_data),
        )


class AllocationEnsemble(list[Allocation]):
    """A collection of allocations, e.g. produced over multiple rounds."""

    def get_pids(self):
        """Return the set of all participant IDs across all allocations."""
        return {
            p_id
            for allocation in self
            for group in allocation
            for p_id in group
            if p_id == p_id
        }

    def calc_total_number_pairs(self):
        """Return the number of possible participant pairs."""
        pids = self.get_pids()
        return comb(len(pids), 2)

    def calc_pair_counts(self) -> Counter:
        """Count how often each pair of participants shares a group."""
        pair_counts = Counter()
        for allocation in self:
            for group in allocation:
                for pair in combinations(group, 2):
                    pair_counts[frozenset(pair)] += 1
        return pair_counts

    def calc_pair_occurrences(self) -> Counter:
        """Count how many pairs meet 0, 1, 2, ... times across allocations."""
        # Calculate occurrences from pair counter.
        pair_counts = self.calc_pair_counts()
        occurrences = Counter(pair_counts.values())

        # Add entry on non-observed pairs.
        total_pairs = self.calc_total_number_pairs()
        observed_pairs = len(pair_counts)
        occurrences[0] = total_pairs - observed_pairs

        return occurrences

    def calc_meeting_rel_score(self) -> float:
        """Return the share of participant pairs that meet at least once."""
        occurrences = self.calc_pair_occurrences()
        return 1 - occurrences[0] / sum(occurrences.values())

    def calc_meeting_norm_score(self) -> float:
        """Return the meeting score normalised to its achievable range."""
        occurrences = self.calc_pair_occurrences()
        rel_score = sum(v for k, v in occurrences.items() if k)

        number_pairs_per_allocation = [
            sum(comb(len(group), 2) for group in allocation)
            for allocation in self
        ]
        min_score = max(number_pairs_per_allocation)
        max_score = sum(number_pairs_per_allocation)

        return (
            ((rel_score - min_score) / (max_score - min_score))
            if max_score > min_score
            else 1.0
        )

    def calc_n_meetings_alo(self) -> int:
        """Return the total number of distinct meeting partners, summed."""
        return sum(
            len(p_stats) for p_id, p_stats in self.calc_meetings().items()
        )

    def calc_meetings(self) -> dict[int, dict[int, int]]:
        """Return how often each participant met every other one."""
        p_ids = {
            p_id
            for allocation in self
            for group in allocation
            for p_id in group
            if p_id == p_id
        }

        meetings = {}
        for p_id in p_ids:
            meetings[p_id] = {}
            for allocation in self:
                for group in allocation:
                    for p_id_other in group:
                        if p_id == p_id_other:
                            continue
                        if p_id_other not in meetings[p_id]:
                            meetings[p_id][p_id_other] = 1
                        meetings[p_id][p_id_other] += 1

        return meetings

    def calc_diversity_score_single_field(self, values_field: np.ndarray) -> float:
        """Return the mean per-allocation diversity deviation, for one field.

        Unlike `Allocation`/`ParticipantGroup`'s methods of the same name,
        this one takes the raw population column for the field (not a
        pre-encoded `(inverse, n_values, share_full)` triple) — it encodes it
        once here and threads the result down to every allocation, rather
        than each allocation re-deriving it.

        Built on `Allocation.calc_diversity_score_single_field`: this is
        DREAM's mean_k(mean_j(∆_{j,d,k})) for a fixed field d, i.e. the
        per-allocation score averaged over allocations (rounds).
        """
        inverse, n_values, share_full = _prepare_field_stats(values_field)

        return sum(
            allocation.calc_diversity_score_single_field(
                inverse, n_values, share_full
            )
            for allocation in self
        ) / len(self)

    def calc_diversity_score_best_single_field(self, values_field: np.ndarray) -> float:
        """Return the mean per-allocation best-case deviation, for one field.

        See `Allocation.calc_diversity_score_best_single_field`.
        """
        inverse, n_values, share_full = _prepare_field_stats(values_field)

        return sum(
            allocation.calc_diversity_score_best_single_field(
                inverse, n_values, share_full
            )
            for allocation in self
        ) / len(self)

    def calc_diversity_score_worst_single_field(self, values_field: np.ndarray) -> float:
        """Return the mean per-allocation chance-baseline deviation, for one field.

        See `Allocation.calc_diversity_score_worst_single_field`.
        """
        inverse, n_values, share_full = _prepare_field_stats(values_field)

        return sum(
            allocation.calc_diversity_score_worst_single_field(
                inverse, n_values, share_full
            )
            for allocation in self
        ) / len(self)

    def calc_diversity_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the diversity score, meaned across all fields.

        Built up hierarchically: `ParticipantGroup` computes the raw
        per-group, per-field deviation; `Allocation` means that over its
        groups; this ensemble means that over its allocations, then over
        fields — matching DREAM's mean_{j,d,k}(∆_{j,d,k}) aggregate. Meaning
        (rather than summing) over fields keeps the metric from growing just
        because more fields are accounted for.
        """
        return _mean_over_fields(
            participants_data, self.calc_diversity_score_single_field
        )

    def calc_diversity_score_best(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the best this ensemble's allocations could do, meaned across fields.

        See `ParticipantGroup.calc_diversity_score_best_single_field` for
        how the per-group best case is estimated; this means it over
        groups, then allocations, then fields, same as `calc_diversity_score`.
        """
        return _mean_over_fields(
            participants_data, self.calc_diversity_score_best_single_field
        )

    def calc_diversity_score_worst(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return this ensemble's chance-baseline deviation, meaned across fields.

        See `ParticipantGroup.calc_diversity_score_worst_single_field` for
        how the per-group chance baseline is estimated; this means it over
        groups, then allocations, then fields, same as `calc_diversity_score`.
        """
        return _mean_over_fields(
            participants_data, self.calc_diversity_score_worst_single_field
        )

    def calc_diversity_norm_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the diversity score normalised to its estimated achievable range.

        Mirrors `calc_meeting_norm_score`, but for diversity: 1.0 = at (or
        beyond) the best this ensemble's allocations could do; 0.0 = no
        better than a uniformly random allocation of the same shape (chance
        baseline) — as in Adjusted Rand Index / Cohen's kappa, a negative
        result (worse than chance) is a meaningful outcome, not an error.

        `calc_diversity_score_best` (largest-remainder apportionment, meaned
        up per group) is not guaranteed globally tight, since achieving
        every group's own local optimum simultaneously isn't always jointly
        possible across a shared, finite population — so the top is clipped
        to 1.0. `calc_diversity_score_worst` doesn't have that looseness:
        because expectation is linear regardless of dependence between
        groups, the mean of each group's independently-estimated chance
        baseline equals the expected deviation of a genuine random *joint*
        partition into groups of these sizes — so the bottom is left
        unclipped.
        """
        return _normalize_diversity_score(
            self.calc_diversity_score(participants_data),
            self.calc_diversity_score_best(participants_data),
            self.calc_diversity_score_worst(participants_data),
        )


class AllocatorResult:
    """Result of an allocator run, wrapping the resulting ensemble."""

    def __init__(self, ensemble: None | AllocationEnsemble = None):
        """Store the allocation ensemble produced by the allocator."""
        self.ensemble = ensemble
