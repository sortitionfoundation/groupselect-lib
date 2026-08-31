"""GroupSelect: allocate participants into diverse groups."""

from groupselect.algorithms import Algorithm
from groupselect.field_mode import FieldMode
from groupselect.allocate_numpy import allocate_numpy
from groupselect.allocation import (
    Allocation,
    AllocationEnsemble,
    AllocatorResult,
)


try:
    import pandas
except ImportError:
    pass
else:
    from groupselect.allocate_pandas import allocate_pandas
