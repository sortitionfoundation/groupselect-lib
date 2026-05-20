from inspect import signature
from math import ceil
from typing import Callable, Iterable

import numpy as np

from groupselect.algorithms import Algorithm, algorithm_funcs
from groupselect.allocation import AllocatorResult
from groupselect.field_mode import FieldMode


# Generic function for allocations.
def allocate_numpy(
    participants: np.ndarray[int],
    fields: dict[int, FieldMode],
    n_part_per_group: int | Iterable[int],
    manuals: None | dict[int, int] = None,
    algorithm: Algorithm | str = Algorithm.Legacy,
    progress_func: None | Callable = None,
    settings: None | dict = None,
) -> AllocatorResult:
    """Partition participants into groups using a specified algorithm.

    Args:
        participants: 2-D integer array of shape
            ``(n_participants, n_fields)``.  Each row is one participant;
            each column is one categorical field encoded as non-negative
            consecutive integers.
        fields: Mapping from column index to :class:`~groupselect.FieldMode`.
            Columns not listed default to ``FieldMode.Ignore``.
            String values are accepted and matched case-insensitively.
        n_part_per_group: Target group size.  An integer applies the same
            size to all allocation rounds; a list of integers produces one
            round per entry (list length == number of rounds in output).
            Actual groups may be one smaller when ``n_participants`` is not
            evenly divisible.
        manuals: Optional ``{participant_index: group_index}`` mapping of
            forced pre-assignments.  The algorithm fills the remaining
            seats around them.
        algorithm: Which algorithm to use.  Accepts an
            :class:`~groupselect.Algorithm` member or a case-insensitive
            string name.  Defaults to ``Algorithm.Legacy``.
        progress_func: Optional callback called with the current iteration
            count (integer).  Used by the GUI to update a progress bar.
        settings: Algorithm-specific keyword arguments forwarded by name
            to the underlying algorithm function.  Unknown keys are silently
            ignored.

    Returns:
        :class:`~groupselect.AllocatorResult` whose ``.ensemble`` attribute
        is an :class:`~groupselect.AllocationEnsemble` containing one
        :class:`~groupselect.Allocation` per entry in ``n_part_per_group``.

    Raises:
        Exception: If any argument fails validation (wrong shape, out-of-range
            indices, unknown algorithm name, etc.).
    """

    # Check arguments: participants.
    if not np.issubdtype(participants.dtype, np.integer):
        raise Exception("Argument participants must only contain integers.")
    if not participants.ndim == 2:
        raise Exception("Argument participants must be 2-dimensional array.")

    # Define constants from participants' data.
    n_participants = participants.shape[0]
    n_fields = participants.shape[1]

    # Check argument n_part_per_group
    if not (
        (
            isinstance(n_part_per_group, int)
            and 0 < n_part_per_group <= n_participants
        )
        or (
            isinstance(n_part_per_group, Iterable)
            and all(
                isinstance(n, int) and 0 < n <= n_participants
                for n in n_part_per_group
            )
        )
    ):
        raise Exception(
            "Number of participants per group must be a positive integer less"
            "than the total number of participants or a list of such integers."
        )
    n_part_per_group = (
        [n_part_per_group]
        if isinstance(n_part_per_group, int)
        else list(n_part_per_group)
    )

    # Compute number of groups per allocation from number of participants per
    # group.
    groups = [
        (ceil(n_participants / n_ppgr), n_ppgr) for n_ppgr in n_part_per_group
    ]

    # Check arguments: manuals
    if manuals is not None:
        if not all(
            isinstance(m_p_id, int) and 0 <= m_p_id < n_participants
            for m_p_id in manuals
        ):
            raise Exception(
                "IDs of manually allocated participants must be integers "
                "within range of number of participants."
            )
        if not all(
            isinstance(m_g_id, int) and 0 <= m_g_id < n_gr
            for n_gr, n_ppgr in groups
            for m_g_id in manuals.values()
        ):
            raise Exception(
                "Group IDs of manual allocations must be within range of "
                "requested group sizes."
            )
    else:
        manuals = {}

    # Check arguments: fields
    for f_id, f_usage in fields.items():
        if not (isinstance(f_id, int) and 0 <= f_id < n_fields):
            raise Exception(
                "Keys of dict containing field usage modes must be positive "
                "integers and less than the number of fields provided for "
                "participants."
            )
        if isinstance(f_usage, str):
            try:
                fields[f_id] = next(
                    f
                    for f in FieldMode
                    if f.name.casefold() == f_usage.casefold()
                )
            except StopIteration:
                raise Exception(f"Unknown field usage type: {f_usage}")
    if not all(isinstance(f_usage, FieldMode) for f_usage in fields.values()):
        raise Exception("Field usage must be valid usage type.")
    for f_id in range(n_fields):
        if f_id not in fields:
            fields[f_id] = FieldMode.Ignore

    # Check arguments: algorithm
    if isinstance(algorithm, str):
        try:
            algorithm = next(
                a
                for a in Algorithm
                if a.name.casefold() == algorithm.casefold()
            )
        except StopIteration:
            raise Exception(
                f"Unknown algorithm type: {algorithm}. Please "
                "choose from: " + ", ".join(a.name for a in Algorithm)
            )
    if not (isinstance(algorithm, Algorithm)):
        raise Exception(
            "Argument algorithm must be a valid algorithm. Please choose "
            "from: " + ", ".join(a.name for a in Algorithm)
        )

    # Initialise empty settings dict.
    if settings is None:
        settings = {}

    # TODO: Check that arguments in the algorithm_func without default are
    #       contained in the settings dict.

    # Call specific algorithm function.
    algorithm_func = algorithm_funcs[algorithm]
    algorithm_func_args = list(signature(algorithm_func).parameters)
    result = algorithm_func(
        participants=participants,
        fields=fields,
        groups=groups,
        manuals=manuals,
        progress_func=progress_func,
        **{k: v for k, v in settings.items() if k in algorithm_func_args},
    )

    return result
