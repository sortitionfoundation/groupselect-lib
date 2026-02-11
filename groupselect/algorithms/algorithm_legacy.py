import csv
import statistics
from typing import Callable

import numpy as np

from groupselect.field_mode import FieldMode
from groupselect.allocation import Allocation, ParticipantGroup, AllocationEnsemble, AllocatorResult


# Legacy algorithm
def algorithm_legacy(participants: np.ndarray[int],
                     fields: dict[int, FieldMode],
                     groups: list[(int, int)],
                     manuals: dict[int, int],
                     progress_func: None | Callable = None,
                     n_attempts: int = 100,
                     seed: None | int = None) -> AllocatorResult:

    print("hoho")

    meet1 = [0] * 10
    m_data = participants.shape[0]



    peopledata_vals_used = [{} for i in range(m_data)]
    order_cluster = [k for k, v in fields.items() if v == FieldMode.Cluster]
    order_diverse = [k for k, v in fields.items() if v == FieldMode.Diversify_1 or v == FieldMode.Diversify_2 or v == FieldMode.Diversify_3]

    lister = [None] * len(order_diverse)
    Y = participants[:, order_diverse]
    for i in range(0, len(order_diverse)):
        lister[i] = [int(item[i]) for item in Y]

        lister[i] = np.unique(lister[i])
        lister[i] = lister[i].tolist()
    order_diverse_dict = dict(zip(order_diverse, lister))

    for i in range(m_data):
        for j in order_cluster + order_diverse:
            peopledata_vals_used[i][j] = int(participants[i][j])

    # Check argument: seed
    if not (seed is None or isinstance(seed, int)):
        raise Exception('Random number seed must be integer.')

    # Try to set the random seed.
    try:
        random = np.random.default_rng(seed)
    except:
        raise Exception('Error when creating random number generator.',
                        'This may be due to an incorrect seed. Please '
                        'check your input.')

    # Check argument: n_attempts
    if not (isinstance(n_attempts, int) and n_attempts > 0):
        raise Exception('Argument n_attempts must be positive integer.')

    # Check that there is at least one diversification field defined.
    if not FieldMode.Diversify_1 in fields.values():
        raise Exception('Error: One diversification field required!',
                        'You have to set at least one field that is '
                        'used to diversify people across groups.')

    # Reindex the field values such that the index is descending w.r.t.
    # the number of occurrences of the specific field value.
    participants = participants.copy()
    for field_id in fields:
        field_vals, field_val_counts = np.unique(participants.T[field_id], return_counts=True)
        mapping_dict = dict(zip(field_vals, field_val_counts.argsort()))
        mapping_func = np.vectorize(mapping_dict.get)
        participants.T[field_id] = mapping_func(participants.T[field_id])

    # Generate AllocationEnsemble `n_attempts` times, where `n_attempts`
    # is an externally given argument.
    allocation_attempts: list[AllocationEnsemble] = [
        AllocationEnsemble()
        for _ in range(n_attempts)
    ]
    for n, ensemble in enumerate(allocation_attempts):
        if progress_func is not None:
            progress_func(n)
        for n_gr, n_ppgr in groups:
            # Shuffle participant IDs.
            shuffle = list(range(len(participants)))
            random.shuffle(shuffle)

            # Generate single allocation.
            allocation = _allocate_legacy_once(
                participants=participants[shuffle],
                fields=fields,
                n_gr=n_gr,
                n_ppgr=n_ppgr,
                manuals=manuals,
            )

            # Revert shuffle of participants IDs.
            allocation = Allocation(
                ParticipantGroup(shuffle[p_id] for p_id in group)
                for group in allocation
            )

            #distance = {}
            #index = 0
            #for table in allocation:
             #   print(index)
              #  distance[i] = evaluate_demographics(
               #      allocation, index, peopledata_vals_used, order_diverse_dict, m_data)
               # index += 1

            #print(fields)
            #print(allocation)
            #print(participants)

            #fields_diversify = [k for k, v in fields.items() if v == FieldMode.Diversify_1]

            #groups_list = [
             #   g_id
              #  for g_id, group in enumerate(allocation)
               # if len(group) <= n_ppgr
            #]
            field_val = [0,1]
            #fielders = []
            #for field_id in fields_diversify:
             #   for val in field_val:
              #      field_value_counts = {
               #         g_id: _count_categories(allocation[g_id], field_id, val, participants)
                #        for g_id in groups_list
                 #   }
                 #   field_val_counts_min = min(field_value_counts.items(), key=lambda x: x[1])[1]
                    #groups_list = [
                    #    g_id
                    #    for g_id in groups_list
                    #    if field_value_counts[g_id] == field_val_counts_min
                    #]
 #                   fielders.append(field_value_counts)


            #print("here ", distance)

            # Append allocation to ensemble.
            ensemble.append(allocation)

    # Sample `n_allocation` allocations and repeat that `n_attempts` times.
    allocation_samples: list[AllocationEnsemble] = [
        AllocationEnsemble()
        for _ in range(n_attempts)
    ]
    for a_id in range(len(groups)):
        for sample, choice in zip(allocation_samples, random.choice(n_attempts, n_attempts)):
            sample.append(allocation_attempts[choice][a_id])

    # Select the sample with maximum number of meetings.
    allocation_sample_max = max(
        allocation_samples,
        key=lambda ensemble: ensemble.calc_n_meetings_alo(),
    )

    previous_meetings = {}

    for i in range(m_data):
        for j in range( i +1, m_data):
            pair = (i ,j)
            if pair not in previous_meetings:
                previous_meetings[pair] = 0


    final = [0] * 10
    div_mean = [0] * 10
    distance = {}
    print(allocation_sample_max[0])
    for j in range(0, 10):
      print("j",j)
      for i in range(0, 11):
         print("i",i)
         distance[i] = evaluate_demographics(
           allocation_sample_max[j], i, peopledata_vals_used, order_diverse_dict, m_data)


         this = [y for x, y in distance.items()]
         this3 = [x[8] for x in this]
         # for i in range (0, len(distance)):
         # if (j == 983):
         # print(this3, "this3")
         final[j] = statistics.mean(this3)
         # print(final[0:j+1])
         div_mean[j] = statistics.mean(final[0:j + 1])

    for n in range(0, 10):
        print("n",n)
        for m in range (0, len(allocation_sample_max[n])):
            print("m",m)
            for i in range (0, len(allocation_sample_max[n][m])):

                 print(allocation_sample_max[n][m])
                 pid_1 = allocation_sample_max[n][m][i]
                 for j in range (i+1, len(allocation_sample_max[n][m])):
                     print(allocation_sample_max[n][m][j])
                     pid_2 = allocation_sample_max[n][m][j]
                     pair = (min(pid_1,pid_2), max(pid_1,pid_2))
                     previous_meetings[pair] += 1
        meet1[n] = sum(x == 1 for x in previous_meetings.values())

    print(previous_meetings)
    print(div_mean)
    print(allocation_sample_max)
    print(meet1)

    filename = ('meetsvsdiv(alloc = photo.csv')
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["round div_mean", "total_div_mean", "meet1"])
        for j in range(10):
            # writer.writerow([1,2,3,4])
            writer.writerow([final[j], div_mean[j], meet1[j]])

    # Create AllocatorResult from sample max and return
    return AllocatorResult(ensemble=allocation_sample_max)

# Actually run the calculation for given number of participants
# per groups, number of groups, and participants' data.
def _allocate_legacy_once(participants: np.ndarray[int],
                          fields: dict[int, FieldMode],
                          n_gr: int,
                          n_ppgr: int,
                          manuals: dict[int, int]) -> Allocation:

    # Generate empty allocations.
    allocation = Allocation(
        ParticipantGroup()
        for _ in range(n_gr)
    )

    # Allocate manuals
    for m_p_id, m_g_id in manuals.items():
        # Find first empty spot
        allocation[m_g_id].append(m_p_id)

    # Split fields into clustering and diversification fields. Order participant IDs
    # by clustering and diversification field values.
    fields_cluster = [k for k, v in fields.items() if v == FieldMode.Cluster]
    fields_diversify = [k for k, v in fields.items() if v == FieldMode.Diversify_1]
    p_ids_ordered = np.lexsort(participants[:, (fields_cluster + fields_diversify)[::-1]].T)

    # Loop over participants and allocate to a group.
    for p_id, p_details in zip(p_ids_ordered, participants[p_ids_ordered]):
        if p_id in manuals:
            continue
        _allocate_person(
            p_id=p_id,
            p_details=p_details,
            allocation=allocation,
            participants=participants,
            fields_cluster=fields_cluster,
            fields_diversify=fields_diversify,
            n_ppgr=n_ppgr,
        )

    return allocation

# Add a participant to a group
def _allocate_person(p_id: int,
                     p_details: np.ndarray[int],
                     allocation: Allocation,
                     participants: np.ndarray[int],
                     fields_cluster: list[int],
                     fields_diversify: list[int],
                     n_ppgr: int):
    # List of groups to choose from is initially list of non-full groups.
    groups_list = [
        g_id
        for g_id, group in enumerate(allocation)
        if len(group) < n_ppgr
    ]
    # Loop over clustering fields.
    superior_field_filters = {}
    for field_id in fields_cluster:
        field_val: int = p_details[field_id]

        # Do not constrain the groups while clustering if the respective
        # field value is the majority value (the one with highest occurrence).
        # The majority value should be equal to 0 (zero) due to the reindex
        # that happened before.
        if field_val == participants.T[field_id].max():
            continue

        # Determine how often this field value occurs across groups.
        field_value_counts = {
            g_id: _count_categories(allocation[g_id], field_id, field_val, participants)
            for g_id in groups_list
        }

        # Create a temporary list of potential groups to focus on. To begin with, this list
        # contains all groups that already contain at least one participant of the same
        # field value.
        groups_list_tmp = [
            g_id
            for g_id in groups_list
            if field_value_counts[g_id] > 0
        ]

        # Then check if the temporary list of groups is enough to accommodate all participants with
        # this specific field value. If not, then keep adding one more group, which is determined
        # from all groups from groups_list
        spaces_required = _number_of_people_filtered(participants, superior_field_filters | {field_id: field_val})
        groups_options = None
        while sum((n_ppgr - len(allocation[g_id])) for g_id in groups_list_tmp) < spaces_required:
            groups_options = groups_options or sorted(
                [g_id for g_id in groups_list if g_id not in groups_list_tmp],
                key=lambda g_id: len(allocation[g_id]),
            )
            groups_list_tmp.append(groups_options.pop(0))
        groups_list = groups_list_tmp
        superior_field_filters[field_id] = field_val


    # Loop over diversification fields.
    for field_id in fields_diversify:
        field_val = p_details[field_id]
        field_value_counts = {
            g_id: _count_categories(allocation[g_id], field_id, field_val, participants)
            for g_id in groups_list
        }
        field_val_counts_min = min(field_value_counts.items(), key=lambda x: x[1])[1]
        groups_list = [
            g_id
            for g_id in groups_list
            if field_value_counts[g_id] == field_val_counts_min
        ]

    # Select groups with least number of participants
    group_size_min = min(len(allocation[g_id]) for g_id in groups_list)
    groups_list = [
        g_id
        for g_id in groups_list
        if len(allocation[g_id]) == group_size_min
    ]

    # Add participant to first group from the list of groups that remain.
    g_id_add = groups_list[0]
    allocation[g_id_add].append(p_id)

    return

# Count number of occurrences of field value in a participant group.
def _count_categories(group: ParticipantGroup, field_id: int, field_val: int, participants: np.ndarray[int]):
    return sum(1 for p_id in group if participants[p_id][field_id] == field_val)

def _number_of_people_filtered(participants: np.ndarray[int], fields: dict[int, int]):
    return (participants.T[list(fields.keys())] == list(fields.values())).all(axis=0).sum()

def evaluate_demographics(temp_allocations,
                          table_no,
                          people,
                          cats_diverse,
                          m_data):
    table = temp_allocations[table_no]

    print("far")

    print(table)

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


    print("epis")
    return table_distances

def calculate_ideal_balance(cats_diverse,
                            m_data,
                            people):
    print("prob")
    ideal_balance = {}
    for demog in cats_diverse:
        counts = [0] * len(cats_diverse[demog])
        for row in people:
            for i, category in enumerate(cats_diverse[demog]):
                if row[demog] == category:
                    counts[i] += 1
        ideal_balance[demog] = [count / m_data for count in counts]

    print("ideal_balance")
    return ideal_balance