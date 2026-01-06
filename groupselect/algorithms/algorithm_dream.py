
import copy
import math
from itertools import product
from typing import Callable

import numpy as np


from groupselect.field_mode import FieldMode
from groupselect.allocation import Allocation, ParticipantGroup, AllocationEnsemble, AllocatorResult


def algorithm_dream(participants: np.ndarray[int],
                    fields: dict[int, FieldMode],
                    groups: list[(int, int)],
                    manuals: dict[int, int],
                    progress_func: None | Callable = None,
                    n_attempts: int = 3,
                    seed: None | int = None):


    nallocations = len(groups)
    progress_bar = progress_func
    tables = groups[0][0]
    for value in groups:
        tables = value[0]
        seats = value

    order_cluster = [k for k, v in fields.items() if v == FieldMode.Cluster]
    order_diverse = [k for k, v in fields.items() if v == FieldMode.Diversify_1 or v == FieldMode.Diversify_2 or v == FieldMode.Diversify_3]


    if len(order_cluster ) >=1:
        val_cluster = 'cluster'
    else:
        val_cluster = ''

    X = participants[:, order_cluster]
    X = np.unique(X)

    Y = participants[:, order_diverse]

    lister = [None] * len(order_diverse)

    for i in range(0, len(order_diverse)):

       lister[i] =[int(item[i]) for item in Y]

       lister[i] = np.unique(lister[i])
       lister[i] = lister[i].tolist()


    order_cluster_dict = dict(zip(order_cluster, [list(X)]))
    order_diverse_dict = dict(zip(order_diverse, lister))


    swap_rounds = 1

    cluster_tables = 2

    m_data = participants.shape[0]

    pareto_prob = 0.5


    '''
    cluster_tables: int,
    m_data: int,
    pareto_prob: float,
    swap_rounds: int,

    progress_bar: any == None'''

    seats = math.ceil(m_data /tables)
    previous_meetings = {}

    try:
        random = np.random.default_rng(seed)
    except:
        raise Exception("Error: Random seed incorrect!", "There was a problem setting the random seed. Please check your input!")

    if (nallocations < 1):
        raise Exception("Error: Wrong allocation number!", "The number of computed allocations must at least be 1!")

    # if len(tables)>1: do this bit

    peopledata_vals_used = [{} for i in range(m_data)]

    for i in range(m_data):
        for j in order_cluster + order_diverse:
            peopledata_vals_used[i][j] = int(participants[i][j])

    # order_cluster_dict = get_field_cluster_dict()
    # order_diverse_dict = get_field_diverse_dict()


    if not order_diverse_dict:
        raise Exception("Error: One diversification field required!", "You have to set at least one field that is used to diversify people across groups.")

    if len(order_cluster_dict ) >1:
        raise Exception("Error: Only one cluster field permitted. Please reduce the number of cluster fields.")

    no_cluster_agents = 0


    if len(order_cluster_dict ) ==1:
        cluster_key = next(iter(order_cluster_dict))
        no_cluster_agents = sum(1 for person in peopledata_vals_used if person[cluster_key] == val_cluster)


    n_swap_loops = int(swap_rounds)
    if n_swap_loops < 1:
        raise Exception("Error: at least one round of meeting optimization must be specified (in *advanced settings*)")

    n_results = allocate(tables, peopledata_vals_used, order_cluster_dict, order_diverse_dict, m_data, nallocations, cluster_tables, pareto_prob, n_swap_loops, progress_bar, previous_meetings, no_cluster_agents, val_cluster, manuals, random)

    allocation_results = n_results
    ''' allocations = []
    for result in n_results[0]:
        allocations.append(n_results[0][result])

    allocation_group_outcome = allocations

    d_mult = m_data// (tables**2)
    L_R = ((tables**2) * 8.5 * d_mult * (d_mult-1)) + d_mult * (m_data % (tables**2))
    min_duplicates = max(0, L_R)

    optimal_pairs = 0
    for table in allocations[0]:
        n = len(table)
        optimal_pairs += n * (n - 1) // 2

    total_possible_pairs = 0
    for round_no in range(nallocations):
        if round_no == 0:
            # no restrictions on repeating pairs
            total_possible_pairs += optimal_pairs
        else:
            total_possible_pairs += optimal_pairs - min_duplicates
    # calculate total pairs in sample
    total_pairs = m_data * (m_data - 1) // 2

    if 0 in n_results[1][nallocations - 1]:
        allocation_group_links_pp = (total_pairs - n_results[2][nallocations - 1][0]) / m_data
    else:
        # all pairs have met
        allocation_group_links_pp = total_pairs

    # maximum links from round 0 to 1 are a function of table size and number of tables
    allocation_group_links_pp_max = min(total_pairs, total_possible_pairs) / m_data

    '''

    # Select the sample with maximum number of meetings.
    # final_results1: list[AllocationEnsemble] = [
    #   AllocationEnsemble()
    #  for _ in range(1)
    # ]


    final_results2 = max(allocation_results)

    return AllocatorResult(final_results2)

def allocate(tables,
             peopledata_vals_used,
             order_cluster_dict,
             order_diverse_dict,
             m_data,
             nallocations,
             cluster_tables,
             pareto_prob,
             n_swap_loops,
             progress_bar,
             previous_meetings,
             no_cluster_agents,
             val_cluster,
             manuals,
             random):
    n_rounds = nallocations
    pre_meeting_dist = {}
    post_meeting_dist = {}
    new_meetings_in_round = {}
    pre_balance = {}
    post_balance = {}

    allocations_list = {}

    for i in range(m_data):
        for j in range( i +1, m_data):
            pair = (i ,j)
            if pair not in previous_meetings:
                previous_meetings[pair] = 0

    # allocation_attempts : AllocationEnsemble = AllocationEnsemble()
    allocation_attempts: list[AllocationEnsemble] = [
        AllocationEnsemble()
        for _ in range(1)
    ]


    for round_no in range(n_rounds):
        if progress_bar: progress_bar(round_no +1)


        if not(isinstance(tables, int)):
            no_tables = tables[round_no]
        else:
            no_tables = tables

        no_larger_tables = m_data % no_tables

        seats = math.ceil(m_data / no_tables)

        min_cluster_tables = math.ceil(no_cluster_agents /seats)

        n_cluster_tables = min(min_cluster_tables + cluster_tables, tables)
        no_smaller_tables = no_tables - no_larger_tables

        if no_larger_tables == 0:
            template = [[None for s in range(seats)] for r in range(no_smaller_tables)]
        else:
            template = [[None for s in range(seats)] for r in range(no_larger_tables)] + \
                [[None for s in range(seats - 1)] for r in range(no_smaller_tables)]

        meetings_previous_round = previous_meetings.copy()

        '''round_assign_pre, round_assign_swap, meetings_pre, '''
        allocation = run_round(template, n_swap_loops, seats, m_data, manuals, n_cluster_tables, order_cluster_dict,
                               order_diverse_dict, peopledata_vals_used, val_cluster, no_tables, previous_meetings,
                               pareto_prob, random)

        allocation = Allocation(
            ParticipantGroup(p_id for p_id in group)
            for group in allocation
        )
        for n, ensemble in enumerate(allocation_attempts):
            ensemble.append(allocation)

        '''pre_occurences = {}
        for value in meetings_pre.values():
           pre_occurences[value] = pre_occurences.get(value, 0) + 1
        pre_meeting_dist[round_no] = pre_occurences
        occurences = {}
        for value in previous_meetings.values():
            occurences[value] = occurences.get(value, 0) + 1
        post_meeting_dist[round_no] = occurences

        new_meetings = {}
        for pair in previous_meetings:
            if previous_meetings[pair]-meetings_previous_round[pair] == 1:
               new_meetings[pair] = previous_meetings[pair]
        round_meetings = {}
        for value in new_meetings.values():
            round_meetings[value] = round_meetings.get(value, 0) + 1
        new_meetings_in_round[round_no] = round_meetings

        pre_demog_evaluations = {}
        for index, table in enumerate(round_assign_pre):
            pre_demog_evaluations[index] = {}
            pre_demog_evaluations[index] = evaluate_demographics(round_assign_pre, index, peopledata_vals_used, order_diverse_dict, m_data)[0]
        pre_balance[round_no] = averages_from_evals(pre_demog_evaluations)
        post_demog_evaluations = {}
        for index, table in enumerate(round_assign_swap):
            post_demog_evaluations[index] = {}
            post_demog_evaluations[index] = evaluate_demographics(round_assign_swap, index, peopledata_vals_used, order_diverse_dict, m_data)[0]
        post_balance[round_no] = averages_from_evals(post_demog_evaluations)

        allocations_list[round_no] = round_assign_swap

        allocations_list, pre_meeting_dist, post_meeting_dist, new_meetings_in_round, pre_balance, post_balance, 
        '''

    return allocation_attempts


def calculate_ideal_balance(cats_diverse,
                            m_data,
                            people):
    ideal_balance = {}

    i = 0
    for demog in cats_diverse:
        i += 1
        counts = [0] * len(cats_diverse[demog])
        for row in people:
            for i, category in enumerate(cats_diverse[demog]):
                if row[demog] == category:
                    counts[i] += 1
        ideal_balance[demog] = [count / m_data for count in counts]

    return ideal_balance


def averages_from_evals(evaluations: dict):
    values_per_key = {}

    for nested_dict in evaluations.values():
        for key, value in nested_dict.items():
            if key not in values_per_key:
                values_per_key[key] = []
            values_per_key[key].append(value)
    averages = {}
    for key in values_per_key:
        lst = values_per_key[key]
        averages[key] = sum(lst) / len(lst)
    return averages


def run_round(template,
              n_swap_loops,
              seats,
              m_data,
              manual_pids,
              n_cluster_tables,
              cats_cluster,
              cats_diverse,
              people,
              val_cluster,
              no_tables,
              previous_meetings,
              pareto_prob,
              random) -> Allocation:
    allocations = copy.deepcopy(template)

    all_pids = list(range(m_data))

    shuffled_pids = all_pids.copy()

    random.shuffle(shuffled_pids)

    shuffled_pids = [x for x in shuffled_pids if x not in manual_pids]

    cluster_table_index = list(range(n_cluster_tables))


    if len(cats_cluster) == 1:
        cluster_individuals = []
        for index, person in enumerate(people):
            if person[next(iter(cats_cluster))] == val_cluster:
                cluster_individuals.append(index)
        cluster_individuals = [x for x in cluster_individuals if x not in manual_pids]

        chosen_chair = 0

        total_clustering_spaces = sum(allocations[index].count(None) for index in cluster_table_index)

        if len(cluster_individuals) > total_clustering_spaces:
            raise ValueError("Too many manual allocations to clustering tables: please reduce manual allocations.")
        for agent in cluster_individuals:
            agent_assigned = 0
            while (agent_assigned == 0):
                table_no = chosen_chair % len(cluster_table_index)
                seat_no = math.floor(
                    chosen_chair / len(cluster_table_index) % seats)
                if allocations[table_no][seat_no] is None:
                    allocations[table_no][seat_no] = agent
                    agent_assigned = 1
                chosen_chair += 1
    else:
        cluster_individuals = []

    non_cluster_individuals = [x for x in shuffled_pids if x not in cluster_individuals]
    chosen_chair = 0

    for agent in non_cluster_individuals:
        agent_assigned = 0
        while (agent_assigned == 0):
            table_no = chosen_chair % no_tables
            seat_no = math.floor(chosen_chair / no_tables % seats)
            if allocations[table_no][seat_no] is None:
                allocations[table_no][seat_no] = agent
                agent_assigned = 1
            chosen_chair += 1

    if n_swap_loops == 1:
        pareto_allocations = pareto_swaps(shuffled_pids, cluster_individuals, cluster_table_index, allocations, people,
                                          cats_diverse, manual_pids, previous_meetings, m_data, pareto_prob, random)
    else:
        pareto_allocations = pareto_swaps(shuffled_pids, cluster_individuals, cluster_table_index, allocations, people,
                                          cats_diverse, manual_pids, previous_meetings, m_data, pareto_prob, random)
        for swap_round in range(1, n_swap_loops):
            pareto_allocations = pareto_swaps(shuffled_pids, cluster_individuals, cluster_table_index,
                                              pareto_allocations, people, cats_diverse, manual_pids, previous_meetings,
                                              m_data, pareto_prob, random)

    raw_meetings = previous_meetings.copy()

    for sublist in pareto_allocations:

        for i in range(len(sublist)):

            for j in range(i + 1, len(sublist)):
                pair = (min(sublist[i], sublist[j]),
                        max(sublist[i], sublist[j]))

                previous_meetings[pair] += 1

    for sublist in allocations:
        for i in range(len(sublist)):
            for j in range(i + 1, len(sublist)):
                pair = (min(sublist[i], sublist[j]),
                        max(sublist[i], sublist[j]))
                # Increment count for the pair in the dictionary
                raw_meetings[pair] += 1

    this_alloc = Allocation(
        ParticipantGroup(list)
        for list in pareto_allocations
    )

    '''allocations, pareto_allocations, raw_meetings, '''

    return this_alloc


def pareto_swaps(shuffled_pids,
                 cluster_individuals,
                 cluster_table_index,
                 temp_allocations,
                 people,
                 cats_diverse,
                 manual_pids,
                 previous_meetings,
                 m_data,
                 pareto_prob,
                 random):
    temp_allocations_update = temp_allocations.copy()


    table_meeting_evaluations = {}
    table_demog_evaluations = {}
    for index, table in enumerate(temp_allocations_update):
        table_meeting_evaluations[index] = evaluate_meetings(table, previous_meetings)
        table_demog_evaluations[index] = {}
        table_demog_evaluations[index] = evaluate_demographics(
            temp_allocations_update, index, people, cats_diverse, m_data)

    for pid in shuffled_pids:
        for index, table in enumerate(temp_allocations_update):
            if pid in table:
                table_no = index

        pid_info = {key: people[pid][key]
                    for key in people[pid] if key in cats_diverse}

        candidate_demogs = {}

        for demog in cats_diverse:
            candidate_demogs[demog] = table_demog_evaluations[table_no][1][demog][pid_info[demog]]

        candidate_profiles = generate_combinations(candidate_demogs, pid_info)
        candidate_swaps = {}

        for profile in candidate_profiles:
            if pid in cluster_individuals:
                candidate_swap_tables = [x for x in table_demog_evaluations if (
                        x != table_no) and (x in cluster_table_index)]
            else:
                candidate_swap_tables = [
                    x for x in table_demog_evaluations if x != table_no]
            for candidate_table in candidate_swap_tables:
                pareto_score = 0
                pareto_profile = table_demog_evaluations[candidate_table][1]
                table_valid = True
                for index, demog in enumerate(pareto_profile):

                    if pid_info[demog] in pareto_profile[demog][profile[index]]:
                        pareto_score += 1
                    elif pid_info[demog] != profile[index]:
                        table_valid = False
                        break
                if table_valid:
                    if pid in cluster_individuals:
                        for swap_pid in temp_allocations_update[candidate_table]:
                            if swap_pid not in manual_pids:
                                if tuple(people[swap_pid][key] for key in people[swap_pid] if
                                         key in cats_diverse) == profile:
                                    candidate_swaps[swap_pid] = pareto_score + \
                                                                candidate_profiles[profile]
                    else:
                        for swap_pid in temp_allocations_update[candidate_table]:
                            if swap_pid not in cluster_individuals:
                                if swap_pid not in manual_pids:
                                    if tuple(people[swap_pid][key] for key in people[swap_pid] if
                                             key in cats_diverse) == profile:
                                        candidate_swaps[swap_pid] = pareto_score + \
                                                                    candidate_profiles[profile]

        if len(candidate_swaps) == 0:
            continue

        candidate_meetings = {}
        for swap in candidate_swaps:
            candidate_meetings[swap] = evaluate_swap(pid, swap, temp_allocations_update, table_meeting_evaluations,
                                                     previous_meetings)

        candidate_swaps = {key: value for key, value in candidate_swaps.items() if (
                candidate_swaps[key] > 0) or (candidate_swaps[key] == 0 and candidate_meetings[key] > 0)}
        if len(candidate_swaps) == 0:
            continue

        distinct_candidates = {}
        for distinct_value in {value for value in candidate_swaps.values()}:
            distinct_keys = {
                key for key, value in candidate_swaps.items() if value == distinct_value}
            max_meetings = max(
                value for key, value in candidate_meetings.items() if key in distinct_keys)
            distinct_candidates.update({key: value for key, value in candidate_swaps.items(
            ) if (value == distinct_value) and (candidate_meetings[key] == max_meetings)})
        distinct_meetings = {key: value for key, value in candidate_meetings.items(
        ) if key in distinct_candidates}

        reverse_mapping = {}
        for key, value in distinct_candidates.items():
            if value not in reverse_mapping:
                reverse_mapping[value] = []
            reverse_mapping[value].append(key)

        final_candidates = {}
        for value, keys in reverse_mapping.items():
            final_candidates[random.choice(keys)] = value
        final_meetings = {
            key: value for key, value in distinct_meetings.items() if key in final_candidates}

        keys_to_remove = set()

        for key in final_meetings.keys():
            if any(final_meetings[other_key] >= final_meetings[key] and final_candidates[other_key] > final_candidates[
                key] for other_key in final_meetings.keys() if other_key != key):
                keys_to_remove.add(key)
        for key in keys_to_remove:
            del final_meetings[key]
            del final_candidates[key]

        final_swap = select_key(final_candidates, final_meetings, pareto_prob, random)
        if final_swap == None:
            continue

        for index, table in enumerate(temp_allocations_update):
            if final_swap in table:
                swap_table = index

        temp_allocations_update[table_no] = [
            final_swap if x == pid else x for x in temp_allocations_update[table_no]]
        temp_allocations_update[swap_table] = [
            pid if x == final_swap else x for x in temp_allocations_update[swap_table]]

        for index in [table_no, swap_table]:
            table_meeting_evaluations[index] = evaluate_meetings(
                temp_allocations_update[index], previous_meetings)
            table_demog_evaluations[index] = {}
            table_demog_evaluations[index] = evaluate_demographics(
                temp_allocations_update, index, people, cats_diverse, m_data)

    return temp_allocations_update


def select_key(pareto,
               meet,
               pareto_prob,
               random):
    pareto_copy = pareto.copy()
    meet_copy = meet.copy()
    total_a = sum(pareto_copy.values())

    if random.random() < pareto_prob:
        if len(pareto_copy) == 1:
            return next(iter(pareto_copy.keys()))

        cumulative_prob_a = {}
        cumulative_sum = 0
        for key, value in pareto_copy.items():
            cumulative_sum += value / total_a
            cumulative_prob_a[key] = cumulative_sum

        rand_num = random.random()
        for key, prob in cumulative_prob_a.items():
            if rand_num <= prob:
                return key
    else:
        meet_copy = {key: value for key, value in meet_copy.items() if meet_copy[key] >= 0}
        if len(meet_copy) == 0:
            return None
        if len(meet_copy) == 1:
            return next(iter(meet_copy.keys()))

        total_b = sum(meet_copy.values())
        cumulative_prob_b = {}
        cumulative_sum = 0
        for key, value in meet_copy.items():
            cumulative_sum += value / total_b
            cumulative_prob_b[key] = cumulative_sum
        rand_num = random.random()

        for key, prob in cumulative_prob_b.items():
            if rand_num <= prob:
                return key


def evaluate_swap(original_id,
                  swap_id,
                  allocations,
                  table_meeting_evaluations,
                  previous_meetings):
    for index, table in enumerate(allocations):
        if swap_id in table:
            swap_table = index
        if original_id in table:
            table_no = index

    original_meetings = sum(x for x in table_meeting_evaluations[table_no].values()) + sum(
        x for x in table_meeting_evaluations[swap_table].values())
    original_table = allocations[table_no]
    swap_table = allocations[swap_table]
    original_table_2 = [swap_id if x == original_id else x for x in original_table]
    swap_table_2 = [original_id if x == swap_id else x for x in swap_table]
    meetings_1 = evaluate_meetings(original_table_2, previous_meetings)
    meetings_2 = evaluate_meetings(swap_table_2, previous_meetings)

    new_meetings = sum(x for x in meetings_1.values()) + sum(x for x in meetings_2.values())

    return original_meetings - new_meetings


def generate_combinations(demogs,
                          info):
    demographics = list(demogs.keys())

    combinations_count = {}

    for values in product(*[demogs[demographic] + [info[demographic]] for demographic in demographics]):
        combination = tuple(values)
        count = len(demogs) - \
                sum(1 for v in combination if v in info.values())
        combinations_count[combination] = count
    return combinations_count


def evaluate_meetings(table,
                      previous_meetings):

    total_meetings = {}
    for i in range(len(table)):
        for j in range(i + 1, len(table)):
            agent1, agent2 = min(table[i], table[j]), max(
                table[i], table[j])
            # Sum the values from pairs_dict for the pair of agents
            total_meetings[agent1] = total_meetings.get(
                agent1, 0) + previous_meetings.get((agent1, agent2), 0)
            total_meetings[agent2] = total_meetings.get(
                agent2, 0) + previous_meetings.get((agent1, agent2), 0)

    return (total_meetings)


def evaluate_demographics(temp_allocations,
                          table_no,
                          people,
                          cats_diverse,
                          m_data):
    table = temp_allocations[table_no]


    table_data = {}
    for index in table:
        table_data[index] = people[index]

    ideal_balance = calculate_ideal_balance(cats_diverse, m_data, people)

    table_balance = {}
    table_actions = {}
    table_distances = {}
    table_length = len(table)
    for demog in cats_diverse:
        counts = [0] * len(cats_diverse[demog])
        for person in table_data.values():
            for i, category in enumerate(cats_diverse[demog]):
                if person.get(demog) == category:
                    counts[i] += 1
        table_balance[demog] = [count / table_length for count in counts]

        table_distances[demog] = sum([abs(x - y) for x, y in zip(
            ideal_balance[demog], table_balance[demog])]) / len(ideal_balance[demog])

        table_actions[demog] = evaluate_actions(ideal_balance[demog], table_balance[demog], cats_diverse[demog],
                                                len(table))

    return table_distances, table_actions


def evaluate_actions(ideal_dist,
                     table_dist,
                     cat_labels):
    table_discrepancies = [y - x for y, x in zip(table_dist, ideal_dist)]
    actions = {}

    for index, label in enumerate(cat_labels):
        actions_for_label = []
        if table_dist[index] > ideal_dist[index]:
            for a, b in zip(table_discrepancies, cat_labels):
                if a < 0:
                    actions_for_label.append(b)
        actions[label] = actions_for_label
    return actions


