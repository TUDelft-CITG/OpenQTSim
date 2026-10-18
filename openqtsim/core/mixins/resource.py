"""Mixins describing the capacity of service stations and the size of customers."""

from openqtsim._validation import validate_positive_integer, validate_positive_rate


class HasResource:
    """Mixin class: the object has a number of servers (service slots).

    The simulation creates the SimPy resources itself, because a station that also has a length
    must admit customers on a free server and sufficient remaining length at the same time.

    Parameters
    ----------
    nr_resources : int, default 1
        Number of customers that can be served simultaneously (c in Kendall's notation).

    Attributes
    ----------
    nr_resources : int
        Number of servers.

    Raises
    ------
    ValueError
        If nr_resources is not a positive integer.
    """

    def __init__(self, *args, nr_resources=1, **kwargs):
        super().__init__(*args, **kwargs)
        validate_positive_integer(nr_resources, "nr_resources")
        self.nr_resources = nr_resources


class HasLength:
    """Mixin class: the object has a physical length (m).

    The occupied length of a service station is a simulation state.

    Parameters
    ----------
    length : float
        For a customer its own length (e.g. a vessel); for a service station the total length
        that customers can share (e.g. a quay wall).

    Attributes
    ----------
    length : float
        Length (m).

    Raises
    ------
    ValueError
        If length is not a finite positive number.
    """

    def __init__(self, *args, length, **kwargs):
        super().__init__(*args, **kwargs)
        validate_positive_rate(length, "length")
        self.length = length
