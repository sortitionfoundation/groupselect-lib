from enum import Enum, unique
from importlib import import_module


# Define Enum data type for different algorithms
@unique
class Algorithm(Enum):
    """Available group-allocation algorithms.

    Attributes:
        Legacy: Greedy + random-restart (Verpoort 2020).  Fast but no
            cross-round meeting awareness.  Currently has a known bug
            with ``FieldMode.Diversify`` fields — see ``algorithm_legacy``
            module for details.
        DREAM: Pareto-swap heuristic (Barrett & Gal 2024).  Processes
            rounds sequentially and maintains a running meeting count.
            Currently shares the same bug as Legacy.
        HERMES: Extension of DREAM with per-field diversity weights
            (Cowie 2026).  Recommended for production use.
    """

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
