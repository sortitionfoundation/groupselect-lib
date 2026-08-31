"""Modes controlling how a participant field is treated during allocation."""

from enum import Enum, unique


@unique
class FieldMode(Enum):
    """How a participant field should be used when forming groups."""

    Ignore = 0
    Diversify = 1
    Cluster = 2
    Keep = 3
