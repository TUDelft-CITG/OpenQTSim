"""Service process of a queue (the S in Kendall's notation A/S/c/K/N/D)."""

from openqtsim._validation import validate_process

class ServiceProcess:
    """Service process class for use in the OpenQTSim package.

    Parameters
    ----------
    symbol : str, default "M"
        Kendall symbol of the service time distribution: "M" (negative exponential),
        "Ek" (Erlang k, with k a positive integer, e.g. "E2") or "D" (deterministic list).
    srv_rate : float or pandas.DataFrame, default 9
        For "M" and "Ek": the mean number of services completed per hour per server.
        For "D": a DataFrame with an ``ST`` column (service times in hours, paired with
        customers by row position) and optionally ``name``, ``s_id`` (assigned server, 1 to c),
        ``length`` and ``maxwait`` columns.

    Attributes
    ----------
    symbol : str
        Kendall symbol of the service time distribution.
    srv_rate : float or pandas.DataFrame
        Mean service rate (per hour per server) or deterministic input table.

    Raises
    ------
    ValueError
        If the symbol is not supported or ``srv_rate`` is not valid for the symbol.
    """

    def __init__(self, symbol='M', srv_rate=9):
        validate_process(symbol, srv_rate, "srv_rate", "ST")
        self.symbol = symbol
        self.srv_rate = srv_rate

    def get_ST(self, server, customer_nr=[]):
        """Return the service time of a customer.

        Parameters
        ----------
        server : Server
            The server (namedtuple created by :class:`~openqtsim.simulation.Simulation`) that serves the
            customer; its ``service_distribution`` is used.
        customer_nr : int
            One-based customer ID; for "D" it selects the row of the input table.
            Ignored for "M" and "Ek".

        Returns
        -------
        float
            Service time (hours), drawn from the distribution or read from the table.
        """

        if self.symbol == "M" or self.symbol[0] == "E":
            return server.service_distribution.rvs()

        elif self.symbol == "D":
            return server.service_distribution.iloc[customer_nr - 1]["ST"]
