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
