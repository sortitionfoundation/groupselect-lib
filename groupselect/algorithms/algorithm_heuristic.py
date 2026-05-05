import copy
import math
from itertools import product
from typing import Callable

import numpy as np

from groupselect.field_mode import FieldMode
from groupselect.allocation import Allocation, ParticipantGroup, AllocationEnsemble, AllocatorResult


def algorithm_heuristic(participants: np.ndarray[int],
                    fields: dict[int, FieldMode],
                    groups: list[(int, int)],
                    manuals: dict[int, int],
                    progress_func: None | Callable = None,
                    n_attempts: int = 3,
                    seed: None | int = None,
                    prob1: float = -1,
                    prob2: float = -1,
                    prob3: float = -1,
                    prob4: float = -1,
                    prob5: float = -1,):



    pareto_prob = [0] * 5
    pareto_prob[0] = prob1/20

    pareto_prob[1] = prob2/20

    pareto_prob[2] = prob3/20

    pareto_prob[3] = prob4/20

    pareto_prob[4] = prob5/20
    pareto_probs = {}
    i = 0
    for k, v in fields.items():
        if v == FieldMode.Diversify_1:
            pareto_probs[k] = pareto_prob[i]
            i = i + 1

    nallocations = len(groups)
    progress_bar = progress_func
    tables = groups[0][0]
    for value in groups:
        tables = value[0]
        seats = value

    order_cluster = [k for k, v in fields.items() if v == FieldMode.Cluster]
    order_diverse = [k for k, v in fields.items() if v == FieldMode.Diversify_1]#or v == FieldMode.Diversify_2 or v == FieldMode.Diversify_3]



    X = participants[:, order_cluster]

    X = np.unique(X)

    Y = participants[:, order_diverse]
    lister = [None] * len(order_diverse)

    for i in range(0, len(order_diverse)):
        lister[i] = [int(item[i]) for item in Y]

        lister[i] = np.unique(lister[i])
        lister[i] = lister[i].tolist()

    Y = np.unique(Y)

    if len(order_cluster ) >=1:
        val_cluster = X[len(X)-1]
    else:
        val_cluster = ''

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
        raise Exception("Error: One diversification field required!",
                        "You have to set at least one field that is used to diversify people across groups.")

    if len(order_cluster_dict) > 1:
        raise Exception("Error: Only one cluster field permitted. Please reduce the number of cluster fields.")

    no_cluster_agents = 0

    if len(order_cluster_dict) == 1:
        cluster_key = next(iter(order_cluster_dict))
        no_cluster_agents = sum(1 for person in peopledata_vals_used if person[cluster_key] == val_cluster)

    n_swap_loops = int(swap_rounds)
    if n_swap_loops < 1:
        raise Exception("Error: at least one round of meeting optimization must be specified (in *advanced settings*)")


    n_results, meet0, meet1, meet2, meet3, meet4, meet5 = allocate(tables, peopledata_vals_used, order_cluster_dict, order_diverse_dict, m_data, nallocations, cluster_tables, pareto_probs, n_swap_loops, progress_bar, previous_meetings, no_cluster_agents, val_cluster, manuals, random, fields)


    allocation_results = n_results
    #print(meet1)
    #meetval = (meet1[9]+(meet2[9]/2)+meet3[9]/3 +meet4[9]/4+meet5[9]/5)/ (meet0[9]+meet1[9]+meet2[9]+meet3[9]+meet4[9]+meet5[9])
    #print(meetval)
    allocations = []
    #for result in n_results[0]:
     #   allocations.append(n_results[0][result])
    print("6")
    #allocation_group_outcome = allocations
    '''
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
    '''
    # maximum links from round 0 to 1 are a function of table size and number of tables
    #allocation_group_links_pp_max = min(total_pairs, total_possible_pairs) / m_data



    # Select the sample with maximum number of meetings.
    # final_results1: list[AllocationEnsemble] = [
    #   AllocationEnsemble()
    #  for _ in range(1)
    # ]
    distance = {}

    #for i in range (0, tables):
     #   distance[i] = evaluate_demographics(i, peopledata_vals_used, order_diverse_dict, m_data, fields)

    #distances = evaluate_demographics()
    #print(distances, "di

    final = [0] * nallocations
    div_mean = [0] * nallocations
    minimum = [0] * nallocations
    maximum = [0] * nallocations
    final_results2 = max(allocation_results)
    """
    if val_cluster == '':
        it = 8
    else :
        it = 7
    for j in range(nallocations):

        for i in range (0, tables):
            distance[i] = evaluate_demographics(allocation_results[0][j], i, peopledata_vals_used, order_diverse_dict, m_data, fields, pareto_probs)

        this = [y for x,y in distance.items()]
        this2 = [x for x,y in this]
        this3 = [x[it] for x in this2]
        #this4 = [x[7] for x in this2]
        #this5 = [x[6] for x in this2]
       # print("mu")
        #for i in range (0, len(distance)):
        #if (j == 983):
            #print(this3, "this3")
      #  print("phi")
        #final3 = statistics.mean(this3)
        #final4 = statistics.mean(this4)
        #final5 = statistics.mean(this5)
        #final[j] = statistics.mean([final3, final4, final5])
        final[j] = statistics.mean(this3)
        #maximum[j] = max(this3)
        #minimum[j] = min(this3)
        #print(final[0:j+1])
       # print("omega")
        div_mean[j] = statistics.mean(final[0:j+1])

        #print(final[j])
        #print(maximum[j])
        #print(minimum[j])
    #meet_mean = statistics.mean(prev_meet_mean)
    #print("delta")
    #if pareto_prob == 0.275:
    #    rank = 2
    #elif pareto_prob == 0.5:
    #    rank = 1
    #else:
     #   rank = 3
    print(prob1)
    if pareto_prob[0] == 0.5:
      if nallocations == 10:
        name = "dreamgenraceage"
      if nallocations == 11:
        name = "dreamurbdietedu"
      if nallocations == 12:
        name = "dreamphotoaudioage"
      if nallocations == 13:
        name = "dreamracedietphoto"
      if nallocations == 14:
        name = "dreamageeduaudio"
      if nallocations == 15:
        name = "dreamgendietage"
      if nallocations == 16:
        name = "dreamraceeduaudio"
      if nallocations == 17:
        name = "dreamageurbphoto"
    if pareto_prob[0] == 0.25:
        if nallocations == 10:
            name = "heurgenraceage"
        if nallocations == 11:
            name = "heururbdietedu"
        if nallocations == 12:
            name = "heurphotoaudioage"
        if nallocations == 13:
            name = "heurracedietphoto"
        if nallocations == 14:
            name = "heurageeduaudio"
        if nallocations == 15:
            name = "heurgendietage"
        if nallocations == 16:
            name = "heurraceeduaudio"
        if nallocations == 17:
            name = "heurageurbphoto"
    if pareto_prob[0] != pareto_prob[1]:
        if nallocations == 10:
            name = "spreadgenraceage"
        if nallocations == 11:
            name = "spreadurbdietedu"
        if nallocations == 12:
            name = "spreadphotoaudioage"
        if nallocations == 13:
            name = "spreadracedietphoto"
        if nallocations == 14:
            name = "spreadageeduaudio"
        if nallocations == 15:
            name = "spreadgendietage"
        if nallocations == 16:
            name = "spreadraceeduaudio"
        if nallocations == 17:
            name = "spreadageurbphoto"

    #filename = ('mutli cats, rank =' + rank.__str__() + ')' + name + '.csv')
    filename = (name + ".csv")
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["round div_mean","total_div_mean", "meet0", "meet1", "meet2", "meet3"])
        for j in range(0, 10):
           # writer.writerow([1,2,3,4])
            writer.writerow([final[j], div_mean[j], meet0[j], meet1[j], meet2[j], meet3[j], meetval])
    """
    return AllocatorResult(final_results2)

def allocate(tables,
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
             fields):
    n_rounds = nallocations

    previous_meetings_max = [0] * nallocations
    previous_meetings_min = [0] * nallocations
    round_meetings_mean = [0] * nallocations
    total_meetings_mean = [0] * nallocations

    meet0 = [0] * nallocations
    meet1 = [0] * nallocations
    meet2 = [0] * nallocations
    meet3 = [0] * nallocations
    meet4 = [0] * nallocations
    meet5 = [0] * nallocations
    meet6 = [0] * nallocations
    meet7 = [0] * nallocations
    meet8 = [0] * nallocations
    meet9 = [0] * nallocations
    meet10 = [0] * nallocations
    pre_meeting_dist = {}
    post_meeting_dist = {}
    new_meetings_in_round = {}
    pre_balance = {}
    post_balance = {}

    allocations_list = {}

    for i in range(m_data):
        for j in range(i + 1, m_data):
            pair = (i, j)
            if pair not in previous_meetings:
                previous_meetings[pair] = 0

    # allocation_attempts : AllocationEnsemble = AllocationEnsemble()
    allocation_attempts: list[AllocationEnsemble] = [
        AllocationEnsemble()
        for _ in range(1)
    ]

    for round_no in range(n_rounds):
        if progress_bar: progress_bar(round_no + 1)

        if not (isinstance(tables, int)):
            no_tables = tables[round_no]
        else:
            no_tables = tables

        no_larger_tables = m_data % no_tables

        seats = math.ceil(m_data / no_tables)

        min_cluster_tables = math.ceil(no_cluster_agents / seats)

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
                               pareto_probs, random, fields)

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

       # print(allocation)
       # print(previous_meetings)

        values = [0] * 5

        #for key, value in previous_meetings.items():
        #    i = 0
        #    print("issue")
        #    for table in allocation:
        #
        #        print(i)
        #        for pid in table:
        #            if pid in key:
        #                print(key)
        #                values[i] = values[i] + value
        #        i = i + 1
        #print(values, "values")


       #for table in allocation:
        #    for pid in table:
         #       pid_meets = (pid in x for x in previous_meetings.keys())
          #      print(pid_meets)
           #     break
            #break
        meet0[round_no] = sum(x == 0 for x in previous_meetings.values())
        meet1[round_no] = sum(x == 1 for x in previous_meetings.values())
        meet2[round_no] = sum(x == 2 for x in previous_meetings.values())
        meet3[round_no] = sum(x == 3 for x in previous_meetings.values())
        meet4[round_no] = sum(x == 4 for x in previous_meetings.values())
        meet5[round_no] = sum(x == 5 for x in previous_meetings.values())
        #meet6[round_no] = sum(x == 6 for x in previous_meetings.values())
        #meet7[round_no] = sum(x == 7 for x in previous_meetings.values())
        #meet8[round_no] = sum(x == 8 for x in previous_meetings.values())
        #meet9[round_no] = sum(x == 9 for x in previous_meetings.values())
        #meet10[round_no] = sum(x == 10 for x in previous_meetings.values())

        #previous_meetings_max[round_no] = max(previous_meetings.values())
        #previous_meetings_min[round_no] = min(previous_meetings.values())
        #round_meetings_mean[round_no] = statistics.mean(previous_meetings.values())
        #print(round_meetings_mean[0:round_no+1])
        #print(statistics.mean(round_meetings_mean[0:round_no+1]))
        #total_meetings_mean[round_no] = statistics.mean(round_meetings_mean[0:round_no+1])

    #print(round_meetings_mean)
   # if pareto_prob == 0.3:
   #     filename = '10alloc2.csv'
   # elif pareto_prob == 0.5:
   #     filename = '10alloc.csv'
   # else:
   #     filename = '10alloc3.csv'

   # with open(filename, 'w', newline='') as csvfile:
   #     writer = csv.writer(csvfile)
   #     writer.writerow(['round_no', 'meet0', 'meet1', 'meet2', 'meet3', 'meet4', 'meet5', 'meet6', 'meet7', 'meet8', 'meet9', 'meet10'])
   #     for i in range(n_rounds):
   #         writer.writerow([i, meet0[i], meet1[i], meet2[i], meet3[i], meet4[i], meet5[i], meet6[i], meet7[i], meet8[i], meet9[i], meet10[i]])
    return allocation_attempts, meet0, meet1, meet2, meet3, meet4, meet5


def calculate_ideal_balance(cats_diverse,
                            m_data,
                            people):
    ideal_balance = {}
    for demog in cats_diverse:
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
              pareto_probs,
              random,
              fields) -> Allocation:
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
                                          cats_diverse, manual_pids, previous_meetings, m_data, pareto_probs, random, fields)
    else:
        pareto_allocations = pareto_swaps(shuffled_pids, cluster_individuals, cluster_table_index, allocations, people,
                                          cats_diverse, manual_pids, previous_meetings, m_data, pareto_probs, random, fields)
        for swap_round in range(1, n_swap_loops):
            pareto_allocations = pareto_swaps(shuffled_pids, cluster_individuals, cluster_table_index,
                                              pareto_allocations, people, cats_diverse, manual_pids, previous_meetings,
                                              m_data, pareto_probs, random, fields)

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
                 pareto_probs,
                 random,
                 fields):
    temp_allocations_update = temp_allocations.copy()

    table_meeting_evaluations = {}
    table_demog_evaluations = {}
    for index, table in enumerate(temp_allocations_update):
        table_meeting_evaluations[index] = evaluate_meetings(table, previous_meetings)
        table_demog_evaluations[index] = {}

        table_demog_evaluations[index] = evaluate_demographics(
            temp_allocations_update, index, people, cats_diverse, m_data, fields, pareto_probs)


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

        for k, v in cats_diverse.items():
            demog_total = k

        demog_scores = [[False] * (demog_total)] * m_data


        for profile in candidate_profiles:
            if pid in cluster_individuals:
                candidate_swap_tables = [x for x in table_demog_evaluations if (
                        x != table_no) and (x in cluster_table_index)]
            else:
                candidate_swap_tables = [
                    x for x in table_demog_evaluations if x != table_no]
            for candidate_table in candidate_swap_tables:
                demog_pareto = [False] * (demog_total)
                pareto_score = 0
                pareto_profile = table_demog_evaluations[candidate_table][1]
                table_valid = True
                for index, demog in enumerate(pareto_profile):
                    if pid_info[demog] in pareto_profile[demog][profile[index]]:

                        #print(fields[list(cats_diverse.keys())[list(cats_diverse.values()).index()]])
                        #diversity_val = fields[list(cats_diverse.keys())[list(cats_diverse.values()).index(cats_labels)]]
                        diversity_val = fields[demog]
                        #if diversity_val == FieldMode.Diversify_3:
                         #   pareto_score += 1
                          #  rank3_score += 1
                       # elif diversity_val == FieldMode.Diversify_2:
                        #    pareto_score += 1
                         #   rank2_score += 1
                        #else:
                        pareto_score += 1
                        demog_pareto[demog-1] = True

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

                                    for i in range(0, demog_total):
                                        if demog_pareto[i - 1] == True:
                                            demog_scores[swap_pid][i - 1] = True

                    else:
                        for swap_pid in temp_allocations_update[candidate_table]:
                            if swap_pid not in cluster_individuals:
                                if swap_pid not in manual_pids:
                                    if tuple(people[swap_pid][key] for key in people[swap_pid] if
                                             key in cats_diverse) == profile:
                                        candidate_swaps[swap_pid] = pareto_score + \
                                                                    candidate_profiles[profile]

                                        for i in range(0, demog_total):
                                            if demog_pareto[i-1] == True:
                                                demog_scores[swap_pid][i-1] = True


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
        final_swap = select_key(final_candidates, final_meetings, pareto_probs, random, demog_scores, demog_total)
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
                temp_allocations_update, index, people, cats_diverse, m_data, fields, pareto_probs)


    return temp_allocations_update


def select_key(pareto,
               meet,
               pareto_probs,
               random,
               demog_scores,
               demog_total):
    relevant_demogs = []

    k = list(pareto.keys())[0]
    for i in range (0, demog_total):
        if demog_scores[k][i] == True:

            relevant_demogs.append(pareto_probs[i+1])
    if relevant_demogs != []:
       pareto_prob_copy = max(relevant_demogs)
    else:
        pareto_prob_copy = max(pareto_probs.values())

    pareto_copy = pareto.copy()
    meet_copy = meet.copy()
    total_a = sum(pareto_copy.values())
    if random.random() < pareto_prob_copy:
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
                          m_data,
                          fields,
                          pareto_probs):
    table = temp_allocations[table_no]

    table_data = {}
    for index in table:
        table_data[index] = people[index]

    ideal_balance = calculate_ideal_balance(cats_diverse, m_data, people)

    table_balance = {}
    table_actions = {}
    table_distances = {}
    table_length = len(table)

    i = 0

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
                                                len(table), fields, cats_diverse, pareto_probs)


    return table_distances, table_actions


def evaluate_actions(ideal_dist,
                     table_dist,
                     cat_labels,
                     table_size,
                     fields,
                     cats_diverse,
                     pareto_probs):
    table_discrepancies = [y - x for y, x in zip(table_dist, ideal_dist)]

    actions = {}

    #print(list(mydict.keys())[list(mydict.values()).index(16)])
    #mydict.keys()[mydict.values().index(16)]
    diversity_val = fields[list(cats_diverse.keys())[list(cats_diverse.values()).index(cat_labels)]]

    lister = list(cats_diverse.keys())[list(cats_diverse.values()).index(cat_labels)]

    #top_prob = max(pareto_probs)
    threshold = -0.5 + pareto_probs[lister]
    #k = fields[cats_diverse[cat_labels]]
    for index, label in enumerate(cat_labels):
        actions_for_label = []
        if table_dist[index] > ideal_dist[index]:
            for a, b in zip(table_discrepancies, cat_labels):
                if diversity_val == FieldMode.Diversify_1 and a < threshold:
                    actions_for_label.append(b)
                #elif diversity_val == FieldMode.Diversify_2 and a < -0.2:
                 #      actions_for_label.append(b)
                #elif diversity_val == FieldMode.Diversify_3 and a < -0.7:
                 #      actions_for_label.append(b)
        actions[label] = actions_for_label

    #  for i in range (0,len(actions)):
    #     if len(actions[i]) != 0:
    #        for j in range (0,len(actions[i])):
    #           actions[i][j] = math.ceil(actions[i][j] * 0.5)

    return actions


