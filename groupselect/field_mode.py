from enum import Enum, unique


@unique
class FieldMode(Enum):
    Ignore = 0
    Diversify = 1
    Cluster = 2
    Keep = 3
