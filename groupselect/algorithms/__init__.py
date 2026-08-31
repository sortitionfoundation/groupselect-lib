"""Available allocation algorithms and lookup of their implementations."""

from enum import Enum, unique
from importlib import import_module

from groupselect.algorithms.algorithm_legacy import algorithm_legacy


# Define Enum data type for different algorithms
@unique
class Algorithm(Enum):
    """Identifier for a supported allocation algorithm."""

    Legacy = 0
    DREAM = 1
    HERMES = 2


# Define functions of algorithms.
algorithm_funcs = {
    algorithm: getattr(
        import_module(
            "groupselect.algorithms.algorithm_" + algorithm.name.lower()
        ),
        "algorithm_" + algorithm.name.lower(),
    )
    for algorithm in Algorithm
}
