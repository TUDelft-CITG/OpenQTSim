"""Mixins describing when customers arrive, how long they are served and how long they wait.

Times are stored in the unit they are given in; generate_vessel_tables expects days.
"""

from openqtsim._validation import validate_nonnegative_number, validate_positive_rate


class HasArrivalSchedule:
    """Mixin class: the customer arrives repeatedly.

    Parameters
    ----------
    AT : float
        (Mean) time of the first arrival.
    IAT : float
        (Mean) interval between subsequent arrivals of the same customer.

    Attributes
    ----------
    AT, IAT : float
        The inputs.

    Raises
    ------
    ValueError
        If AT is negative or IAT is not positive (or either is not finite).
    """

    def __init__(self, *args, AT, IAT, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(AT, "AT")
        validate_positive_rate(IAT, "IAT")
        self.AT = AT
        self.IAT = IAT


class HasHandlingTimes:
    """Mixin class: the customer's (mean) service time is unloading + loading.

    Parameters
    ----------
    unloading : float, default 0
        (Mean) unloading time.
    loading : float, default 0
        (Mean) loading time.

    Attributes
    ----------
    unloading, loading : float
        The inputs.

    Raises
    ------
    ValueError
        If unloading or loading is not a finite nonnegative number.
    """

    def __init__(self, *args, unloading=0, loading=0, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(unloading, "unloading")
        validate_nonnegative_number(loading, "loading")
        self.unloading = unloading
        self.loading = loading

    @property
    def service_time(self):
        """float: (Mean) service time, unloading + loading."""
        return self.unloading + self.loading


class HasMaxWait:
    """Mixin class: the customer reneges when it cannot start service within maxwait.

    Parameters
    ----------
    maxwait : float
        Maximum waiting time; 0 allows immediate service only.

    Attributes
    ----------
    maxwait : float
        Maximum waiting time.

    Raises
    ------
    ValueError
        If maxwait is not a finite nonnegative number.
    """

    def __init__(self, *args, maxwait, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(maxwait, "maxwait")
        self.maxwait = maxwait
