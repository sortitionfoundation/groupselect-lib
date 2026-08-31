"""Allocate participants given as a plain numpy array."""

from typing import Callable, Iterable
from inspect import signature
from math import ceil

import numpy as np

from groupselect.allocation import AllocatorResult
from groupselect.algorithms import Algorithm, algorithm_funcs
from groupselect.field_mode import FieldMode


# Generic function for allocations.
def allocate_numpy(
    participants: np.ndarray[int],
    fields: dict[int, FieldMode],
    n_part_per_group: int | Iterable[int],
    manuals: None | dict[int, int] = None,
    algorithm: Algorithm | str = Algorithm.Legacy,
    progress_func: None | Callable[[float], None] = None,
    settings: None | dict = None,
) -> AllocatorResult:
    """Allocate participants into groups using the chosen algorithm.

    `progress_func`, if given, is called repeatedly by the chosen algorithm
    with a single float in [0.0, 1.0] indicating the fraction of work done
    so far -- this is comparable across all algorithms, regardless of how
    each one internally breaks its work into steps.
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
            "Number of participants per group must be a positive integer "
            "less than the total number of participants or a list of "
            "such integers."
        )
    n_part_per_group = (
        [n_part_per_group]
        if isinstance(n_part_per_group, int)
        else list(n_part_per_group)
    )

    # Compute number of groups per allocation from number of
    # participants per group.
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
                "IDs of manually allocated participants must "
                "be integers within range of number of "
                "participants."
            )
        if not all(
            isinstance(m_g_id, int) and 0 <= m_g_id < n_gr
            for n_gr, n_ppgr in groups
            for m_g_id in manuals.values()
        ):
            raise Exception(
                "Group IDs of manual allocations must be "
                "within range of requested group sizes."
            )
    else:
        manuals = {}

    # Check arguments: fields
    for f_id, f_usage in fields.items():
        if not (isinstance(f_id, int) and 0 <= f_id < n_fields):
            raise Exception(
                "Keys of dict containing field usage modes "
                "must be positive integers and less than the "
                "number of fields provided for participants."
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
            "Argument algorithm must be a valid "
            "algorithm. Please choose from: "
            + ", ".join(a.name for a in Algorithm)
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
