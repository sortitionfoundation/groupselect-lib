"""Example participant datasets, loaded from CSV or generated on the fly."""

from collections.abc import Mapping
from pathlib import Path
from typing import Iterable

import numpy as np

from groupselect.field_mode import FieldMode

try:
    import pandas as pd

    HAS_PANDAS: bool = True
except ImportError:
    pd = None
    HAS_PANDAS: bool = False


DATA_DIR = Path(__file__).parent / "data"


class _MissingPandasExampleData(Mapping):
    """Stand-in for the example-data dicts when pandas isn't installed.

    The example datasets are stored as CSV files and only loaded via
    pandas, so there is nothing to fall back to without it. Any lookup
    raises a clear error rather than a plain ``KeyError``.
    """

    def __getitem__(self, key):
        raise ImportError(
            f"Example dataset {key!r} is not available: pandas is not "
            "installed. Install pandas to use groupselect.examples "
            "example_data_np / example_data_pd."
        )

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0


if HAS_PANDAS:
    example_data_np = {}
    example_data_pd = {}
    for file in DATA_DIR.glob("*.csv"):
        basename = file.stem
        example_data_pd[basename] = pd.read_csv(file)
        example_data_pd[basename].set_index(
            "ID" if "ID" in example_data_pd[basename] else "name",
            inplace=True,
        )
        example_data_np[basename] = (
            example_data_pd[basename]
            .astype("category")
            .apply(lambda col: col.cat.codes)
            .to_numpy()
        )
else:
    example_data_np = _MissingPandasExampleData()
    example_data_pd = _MissingPandasExampleData()


# ---------------------------------------------------------------------------
# Synthetic dataset generation.
# ---------------------------------------------------------------------------


def generate_participants(
    n_participants: int,
    n_div_fields: int,
    n_field_features: int | Iterable[int] = 3,
    rng: np.random.Generator | int | None = None,
) -> np.ndarray:
    """Generate a synthetic array of participants for benchmarking.

    Each of the ``n_div_fields`` columns is populated independently:
    feature codes ``0 .. n_field_features - 1`` are assigned so that
    every feature occurs an (as close to) equal number of times
    within that field, then the column is randomly shuffled. Passing
    a single int for ``n_field_features`` gives every field the same
    number of features; passing a sequence of length ``n_div_fields``
    allows each field to have a different number of features.

    Returns a ``(n_participants, n_div_fields)`` array of ``int``
    feature codes, directly usable as the ``participants`` argument
    of :func:`groupselect.allocate_numpy`.
    """
    if n_participants <= 0:
        raise ValueError("n_participants must be a positive integer.")
    if n_div_fields <= 0:
        raise ValueError("n_div_fields must be a positive integer.")

    if isinstance(n_field_features, int):
        n_field_features = [n_field_features] * n_div_fields
    else:
        n_field_features = list(n_field_features)
    if len(n_field_features) != n_div_fields:
        raise ValueError(
            "n_field_features must be an int, or a sequence of "
            "length n_div_fields."
        )
    if any(n_features < 1 for n_features in n_field_features):
        raise ValueError("n_field_features must be at least 1.")

    rng = (
        rng
        if isinstance(rng, np.random.Generator)
        else np.random.default_rng(rng)
    )

    columns = []
    for n_features in n_field_features:
        # Distribute feature codes as evenly as possible over the
        # participants, then shuffle so codes aren't grouped by index.
        column = np.arange(n_participants) % n_features
        rng.shuffle(column)
        columns.append(column)

    return np.column_stack(columns).astype(int)


def generate_fields(
    n_div_fields: int, mode: FieldMode = FieldMode.Diversify
) -> dict[int, FieldMode]:
    """Return a fields dict marking columns ``0 .. n_div_fields - 1``."""
    return {field_id: mode for field_id in range(n_div_fields)}


def generate_dataset(
    n_participants: int,
    n_div_fields: int,
    n_field_features: int | Iterable[int] = 3,
    n_part_per_group: int = 6,
    n_allocations: int = 1,
    rng: np.random.Generator | int | None = None,
) -> dict:
    """Generate a full synthetic dataset ready for `allocate_numpy`.

    Returns a dict with keys ``participants``, ``fields`` and
    ``n_part_per_group``, which can be passed straight into
    :func:`groupselect.allocate_numpy` via ``**``, e.g.::

        dataset = generate_dataset(
            n_participants=60, n_div_fields=3, n_field_features=4,
            n_part_per_group=10, n_allocations=3,
        )
        result = groupselect.allocate_numpy(
            **dataset, algorithm="HERMES", settings=...,
        )
    """
    return dict(
        participants=generate_participants(
            n_participants=n_participants,
            n_div_fields=n_div_fields,
            n_field_features=n_field_features,
            rng=rng,
        ),
        fields=generate_fields(n_div_fields),
        n_part_per_group=n_allocations * [n_part_per_group],
    )


if HAS_PANDAS:

    def generate_dataset_pandas(
        n_participants: int,
        n_div_fields: int,
        n_field_features: int | Iterable[int] = 3,
        n_part_per_group: int = 6,
        n_allocations: int = 1,
        rng: np.random.Generator | int | None = None,
    ) -> dict:
        """Like `generate_dataset`, but with participants as a DataFrame.

        The DataFrame has diversity-field columns named ``"field_0"``,
        ``"field_1"``, ... and an ``"ID"``-named index, ready for
        :func:`groupselect.allocate_pandas`.
        """
        dataset = generate_dataset(
            n_participants=n_participants,
            n_div_fields=n_div_fields,
            n_field_features=n_field_features,
            n_part_per_group=n_part_per_group,
            n_allocations=n_allocations,
            rng=rng,
        )
        field_names = [f"field_{i}" for i in range(n_div_fields)]
        participants = pd.DataFrame(
            dataset["participants"], columns=field_names
        )
        participants.index.name = "ID"
        dataset["participants"] = participants
        dataset["fields"] = dict(zip(field_names, dataset["fields"].values()))
        return dataset
