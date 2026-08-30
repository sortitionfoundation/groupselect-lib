"""Data structures for allocations and metrics computed over them."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import comb

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None


class ParticipantGroup(list[int]):
    """A single group of participant IDs."""

    pass


class Allocation(list[ParticipantGroup]):
    """A full allocation of participants into groups."""

    pass


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

    def _calc_diversity_score_single_field(self, values_field: np.array):
        values, inverse = np.unique(values_field, return_inverse=True)

        counts_full = np.bincount(inverse)
        share_full = counts_full / len(values_field)

        ret = 0.0
        for allocation in self:
            for group in allocation:
                group_codes = inverse[group]

                counts_group = np.bincount(
                    group_codes,
                    minlength=len(values),
                )

                share_group = counts_group / len(group)

                ret += np.abs(share_full - share_group).sum()
            ret /= len(allocation)

        return ret / len(self)

    def calc_diversity_score(
        self, participants_data: np.ndarray[int] | pd.DataFrame
    ) -> float:
        """Return the summed diversity score across all fields."""
        if pd is not None and isinstance(participants_data, pd.DataFrame):
            participants_data = (
                participants_data.astype("category")
                .apply(lambda col: col.cat.codes)
                .to_numpy()
            )

        # Sum over fields.
        return sum(
            self._calc_diversity_score_single_field(col)
            for col in participants_data.T
        )


class AllocatorResult:
    """Result of an allocator run, wrapping the resulting ensemble."""

    def __init__(self, ensemble: None | AllocationEnsemble = None):
        """Store the allocation ensemble produced by the allocator."""
        self.ensemble = ensemble
