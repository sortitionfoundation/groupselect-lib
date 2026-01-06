from enum import Enum, unique
from importlib import import_module

from groupselect.algorithms.algorithm_legacy import algorithm_legacy


# Define Enum data type for different algorithms
@unique
class Algorithm(Enum):
    Legacy = 0
    Dream = 1
    Heuristic = 2
    # Heuristic = 1  # TODO: Add heuristic algorithm

# Define functions of algorithms.
algorithm_funcs = {
    algorithm: getattr(
        import_module('groupselect.algorithms.algorithm_' + algorithm.name.lower()),
        'algorithm_' + algorithm.name.lower()
    )
    for algorithm in Algorithm
}
