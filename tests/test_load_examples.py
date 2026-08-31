"""Tests for loading the example datasets."""

import pytest


def test_load_examples():
    """Check that the examples package can be imported without error."""
    try:
        import groupselect.examples
    except Exception as ex:
        raise ex
