"""Tests for the pandas ``.groupselect`` accessor."""

import pytest

import pandas as pd

from groupselect.examples import example_data_pd


def test_philipps_example_data():
    """Allocate Philipp's example dataset and print the result."""
    df = example_data_pd["default"]
    for fields in (
        {
            "age": "diversify",
            "gender": "diversify",
            "photo consent": "cluster",
        },
    ):
        for n_part_per_group in (
            3 * [6],
            4 * [8],
        ):
            res = df.groupselect.allocate(
                fields=fields,
                n_part_per_group=n_part_per_group,
            )
            with pd.option_context(
                "display.max_rows", None, "display.max_columns", None
            ):
                print(res)


@pytest.mark.parametrize("algorithm", ["DREAM", "HERMES"])
def test_dream_hermes_without_diversify_field(algorithm):
    """DREAM/HERMES must allocate even with no diversify field defined.

    Unlike LEGACY (see ``test_legacy_requires_diversify_field`` below),
    DREAM and HERMES do not need a diversify field: their swap machinery
    degrades to optimising only for unique meetings when no diversity
    fields are configured -- see `algorithm_dream.py`/`algorithm_hermes.py`
    for how this is handled.
    """
    df = example_data_pd["default"]
    settings = {"pareto_prob": 0.4} if algorithm == "DREAM" else {}
    res = df.groupselect.allocate(
        fields={"photo consent": "cluster"},
        n_part_per_group=6,
        algorithm=algorithm,
        settings=settings,
    )
    assert len(res) == len(df)


def test_legacy_requires_diversify_field():
    """LEGACY, unlike DREAM/HERMES, still requires a diversify field."""
    df = example_data_pd["default"]
    with pytest.raises(Exception, match="diversification field required"):
        df.groupselect.allocate(
            fields={"photo consent": "cluster"},
            n_part_per_group=3 * [6],
            algorithm="Legacy",
        )


@pytest.mark.parametrize("algorithm", ["DREAM", "HERMES"])
def test_dream_hermes_with_no_fields_at_all(algorithm):
    """DREAM/HERMES must allocate with an entirely empty `fields` dict.

    `participants[[]].apply(...)` returns a zero-column DataFrame that
    pandas defaults to dtype float64 (there are no columns to infer a
    dtype from), which used to fail `allocate_numpy`'s integer-dtype
    check -- see `allocate_pandas()`'s explicit `fields`-empty branch.
    """
    df = example_data_pd["default"]
    settings = {"pareto_prob": 0.4} if algorithm == "DREAM" else {}
    res = df.groupselect.allocate(
        fields={},
        n_part_per_group=6,
        algorithm=algorithm,
        settings=settings,
    )
    assert len(res) == len(df)


def test_legacy_requires_diversify_field_with_no_fields_at_all():
    """LEGACY must still reject an entirely empty `fields` dict too."""
    df = example_data_pd["default"]
    with pytest.raises(Exception, match="diversification field required"):
        df.groupselect.allocate(
            fields={},
            n_part_per_group=6,
            algorithm="Legacy",
        )
