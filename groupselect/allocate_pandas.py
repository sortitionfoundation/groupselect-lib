"""Allocate participants given as a pandas DataFrame."""

import warnings
from typing import Callable, Iterable, Hashable

from groupselect import FieldMode, Algorithm, allocate_numpy, AllocatorResult


try:
    import pandas as pd
except ImportError:
    raise ImportError(
        "Package `pandas` needs to be installed in order to use "
        "the allocate_pandas module. Please first install "
        "`pandas` via pip or similar."
    )


def allocate_pandas(
    participants: pd.DataFrame,
    fields: dict[Hashable, FieldMode],
    n_part_per_group: int | Iterable[int],
    manuals: None | dict[int, int] = None,
    algorithm: Algorithm | str = Algorithm.Legacy,
    progress_func: None | Callable[[float], None] = None,
    settings: None | dict = None,
    return_full: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame, AllocatorResult]:
    """Allocate participants of a dataframe into groups.

    `progress_func`, if given, is called repeatedly by the chosen algorithm
    with a single float in [0.0, 1.0] indicating the fraction of work done
    so far -- this is comparable across all algorithms, regardless of how
    each one internally breaks its work into steps.
    """
    # Check that the dataframe index is unique.
    if not participants.index.is_unique:
        raise Exception("Index of dataframe must be unique.")

    # Check that the specified field IDs are among the dataframe columns
    # and are unequal to predefined names 'group' and 'allocation'.
    for field_id in fields:
        if not field_id in participants:
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
    settings_numpy = (settings or {}).copy()
    if settings is not None and "pareto_probs" in settings:
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
    """Pandas ``.groupselect`` accessor for allocating a DataFrame."""

    def __init__(self, df: pd.DataFrame):
        """Bind the accessor to the DataFrame it was accessed on."""
        self._df = df

    def allocate(
        self,
        fields: dict[Hashable, FieldMode],
        n_part_per_group: int | Iterable[int],
        manuals: None | dict[int, int] = None,
        algorithm: Algorithm | str = Algorithm.Legacy,
        progress_func: None | Callable[[float], None] = None,
        settings: None | dict = None,
        return_full: bool = False,
    ) -> pd.DataFrame:
        """Allocate the bound DataFrame's participants into groups."""
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
