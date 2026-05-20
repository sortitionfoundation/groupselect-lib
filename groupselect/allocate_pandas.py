import warnings
from typing import Callable, Hashable, Iterable

from groupselect import Algorithm, AllocatorResult, FieldMode, allocate_numpy

try:
    import pandas as pd
except ImportError:
    ImportError(
        "Package `pandas` needs to be installed in order to use the "
        "allocate_pandas module. Please first install `pandas` via pip or "
        "similar."
    )


def allocate_pandas(
    participants: pd.DataFrame,
    fields: dict[Hashable, FieldMode],
    n_part_per_group: int | Iterable[int],
    manuals: None | dict[int, int] = None,
    algorithm: Algorithm | str = Algorithm.Legacy,
    progress_func: None | Callable = None,
    settings: None | dict = None,
    return_full: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame, AllocatorResult]:
    """Partition participants into groups, accepting a pandas DataFrame.

    Wraps :func:`allocate_numpy` with automatic integer encoding of
    categorical columns and a pandas-native result format.

    Args:
        participants: DataFrame where each row is one participant.  The
            index must be unique.
        fields: Mapping from DataFrame column label to
            :class:`~groupselect.FieldMode`.  All listed columns are
            cast to pandas ``category`` dtype for encoding.
        n_part_per_group: Target group size.  Same semantics as in
            :func:`allocate_numpy`.
        manuals: Optional ``{participant_index: group_index}`` mapping.
            Uses integer row positions (not index labels).
        algorithm: Algorithm to use.
        progress_func: Optional progress callback.
        settings: Algorithm-specific kwargs.  When using
            ``Algorithm.HERMES``, the ``"pareto_probs"`` entry should
            use column labels as keys; they are automatically translated
            to integer field indices before being forwarded.
        return_full: If ``False`` (default), returns only the participants
            DataFrame with allocation and group columns prepended.  If
            ``True``, returns a three-tuple.

    Returns:
        If ``return_full=False``: a DataFrame with columns
        ``["allocation", "group", <original columns>]``, one row per
        participant per allocation round.

        If ``return_full=True``: a tuple
        ``(participants_df, groups_df, AllocatorResult)`` where
        ``groups_df`` has columns ``["allocation", "group", "participant"]``
        and ``AllocatorResult`` contains the full
        :class:`~groupselect.AllocationEnsemble`.

    Raises:
        Exception: If the DataFrame index is not unique or a field label
            is not found as a column.
    """
    # Check that the dataframe index is unique.
    print("enough")
    if not participants.index.is_unique:
        raise Exception("Index of dataframe must be unique.")

    # Check that the specified field IDs are among the dataframe columns
    # and are unequal to predefined names 'group' and 'allocation'.
    for field_id in fields:
        if field_id not in participants:
            raise Exception(f"Field not found as dataframe column: {field_id}")
        if field_id in ("group", "allocation"):
            warnings.warn(
                "The column labels 'group' and 'allocation' will be "
                "overwritten in the returned allocation result."
            )

    # Turn fields into categories.
    participants = participants.astype(
        {field_id: "category" for field_id in fields}
    )

    # Obtain codes for participants' data from pandas.
    participants_codes = participants[list(fields.keys())].apply(
        lambda col: col.cat.codes
    )
    participants_numpy = participants_codes.to_numpy()
    fields_numpy = {
        participants_codes.columns.tolist().index(k): v
        for k, v in fields.items()
    }
    settings_numpy = settings.copy()
    if "pareto_probs" in settings:
        settings_numpy["pareto_probs"] = {
            participants_codes.columns.tolist().index(k): v
            for k, v in settings_numpy["pareto_probs"].items()
        }

    # Run allocation with numpy arrays.
    result: AllocatorResult = allocate_numpy(
        participants=participants_numpy,
        fields=fields_numpy,
        n_part_per_group=n_part_per_group,
        manuals=manuals,
        algorithm=algorithm,
        progress_func=progress_func,
        settings=settings_numpy,
    )

    # Generate pandas dataframe based on numpy results and return.
    ret_part = pd.concat(
        [
            # This is just to ensure that the two columns allocation
            # and group will be the first columns of the dataframe.
            pd.DataFrame(columns=["allocation", "group"])
        ]
        + [
            participants.loc[participants.index[group]]
            .reset_index(
                names=[f"participant {l}" for l in participants.index.names]
                if participants.index.nlevels > 1
                else "participant"
            )
            .assign(
                allocation=al_id,
                group=gr_id,
            )
            for al_id, allocation in enumerate(result.ensemble)
            for gr_id, group in enumerate(allocation)
        ],
        ignore_index=True,
    )
    if not return_full:
        return ret_part
    ret_groups = pd.DataFrame.from_records(
        [
            pd.Series(
                {
                    "allocation": al_id,
                    "group": gr_id,
                    "participant": participants.index[group].tolist(),
                }
            )
            for al_id, allocation in enumerate(result.ensemble)
            for gr_id, group in enumerate(allocation)
        ]
    )
    return ret_part, ret_groups, result


@pd.api.extensions.register_dataframe_accessor("groupselect")
class GroupSelectAccessor:
    """Pandas DataFrame accessor that exposes GroupSelect allocation.

    Registered under the ``groupselect`` namespace so that any DataFrame
    can call ``df.groupselect.allocate(...)``.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def allocate(
        self,
        fields: dict[Hashable, FieldMode],
        n_part_per_group: int | Iterable[int],
        manuals: None | dict[int, int] = None,
        algorithm: Algorithm | str = Algorithm.Legacy,
        progress_func: None | Callable = None,
        settings: None | dict = None,
        return_full: bool = False,
    ) -> pd.DataFrame:
        return allocate_pandas(
            participants=self._df,
            fields=fields,
            n_part_per_group=n_part_per_group,
            manuals=manuals,
            algorithm=algorithm,
            progress_func=progress_func,
            settings=settings,
            return_full=return_full,
        )
