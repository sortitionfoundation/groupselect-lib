from enum import Enum, unique


@unique
class FieldMode(Enum):
    Ignore = 0
    Diversify_1 = 1
    Diversify_2 = 2
    Diversify_3 = 3
    Cluster = 4
    Keep = 5
