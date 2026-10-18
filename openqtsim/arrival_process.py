"""Arrival process of a queue (the A in Kendall's notation A/S/c/K/N/D)."""

from openqtsim._validation import validate_process

class ArrivalProcess:
    """Arrival process class for use in the OpenQTSim package.

    Parameters
    ----------
    symbol : str, default "M"
        Kendall symbol of the interarrival time distribution: "M" (negative exponential),
        "Ek" (Erlang k, with k a positive integer, e.g. "E2") or "D" (deterministic list).
    arr_rate : float or pandas.DataFrame, default 8
        For "M" and "Ek": the mean number of arrivals per hour.
        For "D": a DataFrame with an ``IAT`` column (interarrival times in hours, paired with
        customers by row position) and optionally ``name``, ``length`` and ``maxwait`` columns.

    Attributes
    ----------
    symbol : str
        Kendall symbol of the interarrival time distribution.
    arr_rate : float or pandas.DataFrame
        Mean arrival rate (per hour) or deterministic input table.
    arrival_distribution
        Set by :class:`~openqtsim.simulation.Simulation`: the frozen ``scipy.stats`` distribution the
        interarrival times are drawn from, or the deterministic input table.

    Raises
    ------
    ValueError
        If the symbol is not supported or ``arr_rate`` is not valid for the symbol.
    """

    def __init__(self, symbol='M', arr_rate=8):
        validate_process(symbol, arr_rate, "arr_rate", "IAT")
        self.symbol = symbol
        self.arr_rate = arr_rate

    def get_IAT(self, customer_nr=[]):
        """Return the next interarrival time.

        Parameters
        ----------
        customer_nr : int
            Number of customers that already arrived; for "D" it is the zero-based row of
            the input table to use. Ignored for "M" and "Ek".

        Returns
        -------
        float
            Interarrival time (hours), drawn from the distribution or read from the table.
        """

        if self.symbol == "M" or self.symbol[0] == "E":
            return self.arrival_distribution.rvs()

        elif self.symbol == "D":
            return self.arrival_distribution.iloc[customer_nr]["IAT"]
