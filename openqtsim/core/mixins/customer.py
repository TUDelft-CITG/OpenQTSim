"""Mixins describing when customers arrive, how long they are served and how long they wait.

Times are stored in the unit they are given in; generate_vessel_tables expects days.
"""

from openqtsim._validation import validate_nonnegative_number, validate_positive_rate


class HasArrivalSchedule:
    """Mixin class: the customer arrives repeatedly.

    AT: (mean) time of the first arrival
    IAT: (mean) interval between subsequent arrivals of the same customer
    """

    def __init__(self, *args, AT, IAT, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(AT, "AT")
        validate_positive_rate(IAT, "IAT")
        self.AT = AT
        self.IAT = IAT


class HasHandlingTimes:
    """Mixin class: the customer's (mean) service time is unloading + loading.

    unloading: (mean) unloading time
    loading: (mean) loading time
    """

    def __init__(self, *args, unloading=0, loading=0, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(unloading, "unloading")
        validate_nonnegative_number(loading, "loading")
        self.unloading = unloading
        self.loading = loading

    @property
    def service_time(self):
        return self.unloading + self.loading


class HasMaxWait:
    """Mixin class: the customer reneges when it cannot start service within maxwait.

    maxwait: maximum waiting time; 0 allows immediate service only
    """

    def __init__(self, *args, maxwait, **kwargs):
        super().__init__(*args, **kwargs)
        validate_nonnegative_number(maxwait, "maxwait")
        self.maxwait = maxwait
