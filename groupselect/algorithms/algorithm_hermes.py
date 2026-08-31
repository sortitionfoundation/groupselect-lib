"""HERMES allocation algorithm, built on top of DREAM's swap machinery."""

import functools
import math
from typing import Callable

import numpy as np


from groupselect.field_mode import FieldMode
from groupselect.allocation import AllocatorResult
from groupselect.algorithms.algorithm_dream import (
    allocate,
    run_round,
    evaluate_demographics,
    select_key,
    evaluate_meetings,
    generate_combinations,
    evaluate_swap,
)


def algorithm_hermes(
    participants: np.ndarray[int],
    fields: dict[int, FieldMode],
    groups: list[(int, int)],
    manuals: dict[int, int],
    progress_func: None | Callable[[float], None] = None,
    seed: None | int = None,
    pareto_probs: dict[int, float] = None,
    swap_rounds: int = 1,
    cluster_tables: int = 2,
):
    """Allocate participants into groups using the HERMES algorithm."""
    pareto_probs = pareto_probs or {}
    for field_id in fields:
        if fields[field_id] == FieldMode.Diversify:
            if field_id not in pareto_probs:
                raise Exception(
                    f"Algorithm HERMES requires pareto probability to be "
                    f"passed for diversity fields, but none found for "
                    f"field {field_id}."
                )
            if not (
                isinstance(pareto_probs[field_id], float)
                and 0.0 <= pareto_probs[field_id] <= 0.5
            ):
                raise Exception(
                    f"Pareto probability must be float in range "
                    f"[0.0, 0.5] but found: {pareto_probs[field_id]}"
                )

    nallocations = len(groups)
    progress_bar = progress_func
    tables = groups[0][0]
    for value in groups:
        tables = value[0]
        seats = value

    order_cluster = [k for k, v in fields.items() if v == FieldMode.Cluster]
    order_diverse = [k for k, v in fields.items() if v == FieldMode.Diversify]

    X = participants[:, order_cluster]

    X = np.unique(X)

    Y = participants[:, order_diverse]
    lister = [None] * len(order_diverse)

    for i in range(0, len(order_diverse)):
        lister[i] = [int(item[i]) for item in Y]

        lister[i] = np.unique(lister[i])
        lister[i] = lister[i].tolist()

    if len(order_cluster) >= 1:
        val_cluster = X[len(X) - 1]
    else:
        val_cluster = ""

    order_cluster_dict = dict(zip(order_cluster, [list(X)]))
    order_diverse_dict = dict(zip(order_diverse, lister))

    m_data = participants.shape[0]

    seats = math.ceil(m_data / tables)
    previous_meetings = {}
    try:
        random = np.random.default_rng(seed)
    except:
        raise Exception(
            "Error: Random seed incorrect!",
            "There was a problem setting the random seed. Please check "
            "your input!",
        )

    if nallocations < 1:
        raise Exception(
            "Error: Wrong allocation number!",
            "The number of computed allocations must at least be 1!",
        )

    peopledata_vals_used = [{} for i in range(m_data)]

    for i in range(m_data):
        for j in order_cluster + order_diverse:
            peopledata_vals_used[i][j] = int(participants[i][j])

    # No diversification field is required: with `order_diverse_dict`
    # empty, `cats_diverse` is empty throughout the swap machinery below
    # (see `pareto_swaps` in this module), so HERMES then behaves as a
    # meeting-optimisation-only allocator, same as DREAM in that case.

    if len(order_cluster_dict) > 1:
        raise Exception(
            "Error: Only one cluster field permitted. Please reduce "
            "the number of cluster fields."
        )

    no_cluster_agents = 0

    if len(order_cluster_dict) == 1:
        cluster_key = next(iter(order_cluster_dict))
        no_cluster_agents = sum(
            1
            for person in peopledata_vals_used
            if person[cluster_key] == val_cluster
        )

    n_swap_loops = int(swap_rounds)
    if n_swap_loops < 1:
        raise Exception(
            "Error: at least one round of meeting optimization must be "
            "specified (in *advanced settings*)"
        )

    # HERMES reuses DREAM's allocation scaffolding (allocate -> run_round)
    # unchanged, overriding only the swap-selection step (pareto_swaps
    # below) so each diversity field's swap-acceptance probability is
    # weighed individually instead of using one fixed probability/threshold
    # for every field.
    allocation_results = allocate(
        tables,
        peopledata_vals_used,
        order_cluster_dict,
        order_diverse_dict,
        m_data,
        nallocations,
        cluster_tables,
        pareto_probs,
        n_swap_loops,
        progress_bar,
        previous_meetings,
        no_cluster_agents,
        val_cluster,
        manuals,
        random,
        run_round=functools.partial(run_round, pareto_swaps=pareto_swaps),
    )

    final_results2 = max(allocation_results)

    return AllocatorResult(final_results2)


def pareto_swaps(
    shuffled_pids,
    cluster_individuals,
    cluster_table_index,
    temp_allocations,
    people,
    cats_diverse,
    manual_pids,
    previous_meetings,
    m_data,
    pareto_probs,
    random,
):
    """Select the best swap for a round using HERMES's field thresholds."""
    # HERMES's per-field threshold: how far a table's demographic balance
    # may deviate from the panel-wide ideal before a swap is considered for
    # that field, controlled by the field's own pareto probability (DREAM
    # uses a fixed threshold of 0 for every field instead). Keyed directly
    # by the field's own ID -- earlier code instead reverse-looked-up the
    # field from its category-value list, which silently resolved to the
    # wrong field whenever two diversity fields shared an identical set of
    # category values.
    threshold_func = lambda demog: -0.5 + pareto_probs[demog]

    temp_allocations_update = temp_allocations.copy()

    table_meeting_evaluations = {}
    table_demog_evaluations = {}
    for index, table in enumerate(temp_allocations_update):
        table_meeting_evaluations[index] = evaluate_meetings(
            table, previous_meetings
        )
        table_demog_evaluations[index] = evaluate_demographics(
            temp_allocations_update,
            index,
            people,
            cats_diverse,
            m_data,
            threshold_func=threshold_func,
        )

    for pid in shuffled_pids:
        for index, table in enumerate(temp_allocations_update):
            if pid in table:
                table_no = index

        pid_info = {
            key: people[pid][key] for key in people[pid] if key in cats_diverse
        }

        candidate_demogs = {}

        for demog in cats_diverse:
            candidate_demogs[demog] = table_demog_evaluations[table_no][1][
                demog
            ][pid_info[demog]]

        candidate_profiles = generate_combinations(candidate_demogs, pid_info)
        candidate_swaps = {}

        # Per swap-candidate record of which diversity fields (keyed by
        # their field ID) that specific swap would pareto-improve.
        demog_scores: dict[int, set[int]] = {}

        for profile in candidate_profiles:
            if pid in cluster_individuals:
                candidate_swap_tables = [
                    x
                    for x in table_demog_evaluations
                    if (x != table_no) and (x in cluster_table_index)
                ]
            else:
                candidate_swap_tables = [
                    x for x in table_demog_evaluations if x != table_no
                ]
            for candidate_table in candidate_swap_tables:
                demog_pareto_fields = set()
                pareto_score = 0
                pareto_profile = table_demog_evaluations[candidate_table][1]
                table_valid = True
                for index, demog in enumerate(pareto_profile):
                    if (
                        pid_info[demog]
                        in pareto_profile[demog][profile[index]]
                    ):
                        pareto_score += 1
                        demog_pareto_fields.add(demog)

                    elif pid_info[demog] != profile[index]:
                        table_valid = False
                        break
                if table_valid:
                    if pid in cluster_individuals:
                        for swap_pid in temp_allocations_update[
                            candidate_table
                        ]:
                            if swap_pid not in manual_pids:
                                if (
                                    tuple(
                                        people[swap_pid][key]
                                        for key in people[swap_pid]
                                        if key in cats_diverse
                                    )
                                    == profile
                                ):
                                    candidate_swaps[swap_pid] = (
                                        pareto_score
                                        + candidate_profiles[profile]
                                    )

                                    demog_scores.setdefault(
                                        swap_pid, set()
                                    ).update(demog_pareto_fields)

                    else:
                        for swap_pid in temp_allocations_update[
                            candidate_table
                        ]:
                            if swap_pid not in cluster_individuals:
                                if swap_pid not in manual_pids:
                                    if (
                                        tuple(
                                            people[swap_pid][key]
                                            for key in people[swap_pid]
                                            if key in cats_diverse
                                        )
                                        == profile
                                    ):
                                        candidate_swaps[swap_pid] = (
                                            pareto_score
                                            + candidate_profiles[profile]
                                        )

                                        demog_scores.setdefault(
                                            swap_pid, set()
                                        ).update(demog_pareto_fields)

        if len(candidate_swaps) == 0:
            continue
        candidate_meetings = {}
        for swap in candidate_swaps:
            candidate_meetings[swap] = evaluate_swap(
                pid,
                swap,
                temp_allocations_update,
                table_meeting_evaluations,
                previous_meetings,
            )

        candidate_swaps = {
            key: value
            for key, value in candidate_swaps.items()
            if (candidate_swaps[key] > 0)
            or (candidate_swaps[key] == 0 and candidate_meetings[key] > 0)
        }

        if len(candidate_swaps) == 0:
            continue

        distinct_candidates = {}
        for distinct_value in {value for value in candidate_swaps.values()}:
            distinct_keys = {
                key
                for key, value in candidate_swaps.items()
                if value == distinct_value
            }
            max_meetings = max(
                value
                for key, value in candidate_meetings.items()
                if key in distinct_keys
            )

            distinct_candidates.update(
                {
                    key: value
                    for key, value in candidate_swaps.items()
                    if (value == distinct_value)
                    and (candidate_meetings[key] == max_meetings)
                }
            )
        distinct_meetings = {
            key: value
            for key, value in candidate_meetings.items()
            if key in distinct_candidates
        }
        reverse_mapping = {}
        for key, value in distinct_candidates.items():
            if value not in reverse_mapping:
                reverse_mapping[value] = []
            reverse_mapping[value].append(key)
        final_candidates = {}
        for value, keys in reverse_mapping.items():
            final_candidates[random.choice(keys)] = value
        final_meetings = {
            key: value
            for key, value in distinct_meetings.items()
            if key in final_candidates
        }

        keys_to_remove = set()
        for key in final_meetings.keys():
            if any(
                final_meetings[other_key] >= final_meetings[key]
                and final_candidates[other_key] > final_candidates[key]
                for other_key in final_meetings.keys()
                if other_key != key
            ):
                keys_to_remove.add(key)
        for key in keys_to_remove:
            del final_meetings[key]
            del final_candidates[key]

        # Use the highest configured probability among the diversity
        # fields the chosen candidate actually pareto-improves (falling
        # back to the overall maximum if it improves none, e.g. it was
        # accepted purely for its meeting-uniqueness score). With no
        # diversity fields configured at all, `pareto_probs` is empty and
        # no candidate ever pareto-improves a field, so fall back to 0.0
        # instead of `max()`-ing an empty sequence -- `select_key` then
        # always takes its meeting-uniqueness branch, matching DREAM's
        # own degenerate no-diversify-field behaviour.
        def pareto_prob_for(k):
            relevant = [
                pareto_probs[field_id] for field_id in demog_scores.get(k, ())
            ]
            if relevant:
                return max(relevant)
            return max(pareto_probs.values()) if pareto_probs else 0.0

        final_swap = select_key(
            final_candidates, final_meetings, pareto_prob_for, random
        )
        if final_swap == None:
            continue

        for index, table in enumerate(temp_allocations_update):
            if final_swap in table:
                swap_table = index

        temp_allocations_update[table_no] = [
            final_swap if x == pid else x
            for x in temp_allocations_update[table_no]
        ]
        temp_allocations_update[swap_table] = [
            pid if x == final_swap else x
            for x in temp_allocations_update[swap_table]
        ]

        for index in [table_no, swap_table]:
            table_meeting_evaluations[index] = evaluate_meetings(
                temp_allocations_update[index], previous_meetings
            )
            table_demog_evaluations[index] = evaluate_demographics(
                temp_allocations_update,
                index,
                people,
                cats_diverse,
                m_data,
                threshold_func=threshold_func,
            )

    return temp_allocations_update
