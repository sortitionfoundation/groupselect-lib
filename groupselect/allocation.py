from collections import Counter
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd


class ParticipantGroup(list[int]):
    """A single group of participants within one allocation.

    Stores participant row-indices (integers) from the original input array.
    """


class Allocation(list[ParticipantGroup]):
    """One full partition of participants into groups for a single round.

    A list of :class:`ParticipantGroup` objects covering all participants.
    """


class AllocationEnsemble(list[Allocation]):
    """A sequence of allocations covering multiple rounds of a CA.

    Provides scoring methods that measure diversity and meeting
    uniqueness across all contained allocations.
    """

    def get_pids(self):
        """Return the set of all participant IDs across the ensemble."""
        return {
            p_id
            for allocation in self
            for group in allocation
            for p_id in group
            if p_id == p_id
        }

    def calc_total_number_pairs(self):
        """Return the total number of possible participant pairs."""
        pids = self.get_pids()
        return comb(len(pids), 2)

    def calc_pair_counts(self) -> Counter:
        """Count how many times each participant pair appeared in the same group.

        Returns:
            Counter mapping ``frozenset({pid_a, pid_b})`` to the number
            of times that pair shared a group across all allocations.
        """
        pair_counts = Counter()
        for allocation in self:
            for group in allocation:
                for pair in combinations(group, 2):
                    pair_counts[frozenset(pair)] += 1
        return pair_counts

    def calc_pair_occurrences(self) -> Counter:
        """Return a frequency distribution of pair-meeting counts.

        Returns:
            Counter mapping meeting-count to the number of pairs with
            that count.  The key ``0`` covers pairs that never met.

        Example:
            ``{0: 200, 1: 50, 2: 10}`` means 200 pairs never met,
            50 pairs met exactly once, and 10 pairs met twice.
        """
        # Calculate occurrences from pair counter.
        pair_counts = self.calc_pair_counts()
        occurrences = Counter(pair_counts.values())

        # Add entry on non-observed pairs.
        total_pairs = self.calc_total_number_pairs()
        observed_pairs = len(pair_counts)
        occurrences[0] = total_pairs - observed_pairs

        return occurrences

    def calc_meeting_rel_score(self) -> float:
        """Return the fraction of all participant pairs that met at least once.

        Returns:
            Float in ``[0.0, 1.0]``.  ``1.0`` means every possible pair
            shared a group in at least one allocation round.
        """
        occurrences = self.calc_pair_occurrences()
        return 1 - occurrences[0] / sum(occurrences.values())

    def calc_meeting_norm_score(self) -> float:
        """Return a normalised meeting-uniqueness score.

        The score is normalised between two theoretical extremes:

        - ``0.0`` (worst): all allocation rounds assign the same groups,
          so unique pairs = pairs in a single round.
        - ``1.0`` (best): every round has fully disjoint group pairings,
          so unique pairs = sum of pairs across all rounds.

        Returns:
            Float in ``[0.0, 1.0]``, or ``1.0`` if all rounds are
            identical in size (degenerate case).
        """
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
        """Return the total number of unique meetings across all participants.

        Counts each directed pair (A met B) separately, so the result
        is twice the number of unique unordered pairs that met at least once.
        """
        return sum(
            len(p_stats) for p_id, p_stats in self.calc_meetings().items()
        )

    def calc_meetings(self) -> dict[int, dict[int, int]]:
        """Return a nested dict of meeting counts between all participant pairs.

        Returns:
            ``{pid: {other_pid: n_times_met}}`` for every participant.
        """
        p_ids = {
            p_id
            for allocation in self
            for group in allocation
            for p_id in group
            if p_id
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
        """Return a diversity score across all allocations and fields.

        For each field and each allocation, the per-group L1 deviation
        from the ideal (population-level) category distribution is computed
        and averaged across groups.  The results are summed across fields
        and allocations.  Lower values indicate better diversity.

        Args:
            participants_data: 2-D integer array of shape
                ``(n_participants, n_fields)`` or a pandas DataFrame.
                Only the columns corresponding to diversification fields
                need be included.

        Returns:
            Non-negative float.  ``0.0`` means every group perfectly
            mirrors the population distribution for every field.
        """
        if isinstance(participants_data, pd.DataFrame):
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
    """Container returned by all allocator functions.

    Attributes:
        ensemble: The computed :class:`AllocationEnsemble`, or ``None``
            if allocation has not yet been performed.
    """

    def __init__(self, ensemble: None | AllocationEnsemble = None):
        self.ensemble = ensemble
