from enum import Enum, unique


@unique
class FieldMode(Enum):
    """How a participant feature field is used during group allocation.

    Attributes:
        Ignore: Field is not considered during allocation.
        Diversify: Spread participants proportionally so each group mirrors
            the full-population distribution for this field.
        Cluster: Keep participants sharing the target field value together
            in a designated subset of groups.
        Keep: Reserved for future use; not implemented by any current
            algorithm.
    """

    Ignore = 0
    Diversify = 1
    Cluster = 2
    Keep = 3
