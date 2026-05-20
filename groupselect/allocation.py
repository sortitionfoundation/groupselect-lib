from collections import Counter
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd


class ParticipantGroup(list[int]):
    pass


class Allocation(list[ParticipantGroup]):
    pass


class AllocationEnsemble(list[Allocation]):
    def get_pids(self):
        return {
            p_id
            for allocation in self
            for group in allocation
            for p_id in group
            if p_id == p_id
        }

    def calc_total_number_pairs(self):
        pids = self.get_pids()
        return comb(len(pids), 2)

    def calc_pair_counts(self) -> Counter:
        pair_counts = Counter()
        for allocation in self:
            for group in allocation:
                for pair in combinations(group, 2):
                    pair_counts[frozenset(pair)] += 1
        return pair_counts

    def calc_pair_occurrences(self) -> Counter:
        # Calculate occurrences from pair counter.
        pair_counts = self.calc_pair_counts()
        occurrences = Counter(pair_counts.values())

        # Add entry on non-observed pairs.
        total_pairs = self.calc_total_number_pairs()
        observed_pairs = len(pair_counts)
        occurrences[0] = total_pairs - observed_pairs

        return occurrences

    def calc_meeting_rel_score(self) -> float:
        occurrences = self.calc_pair_occurrences()
        return 1 - occurrences[0] / sum(occurrences.values())

    def calc_meeting_norm_score(self) -> float:
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
        return sum(
            len(p_stats) for p_id, p_stats in self.calc_meetings().items()
        )

    def calc_meetings(self) -> dict[int, dict[int, int]]:
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
    def __init__(self, ensemble: None | AllocationEnsemble = None):
        self.ensemble = ensemble
