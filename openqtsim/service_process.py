from openqtsim._validation import validate_process

class ServiceProcess:
    """
    Server process class for use in the OpenQTSim package
    """

    def __init__(self, symbol='M', srv_rate=9):
        """
        symbol: symbol of the process (M, E_k, etc.)
        srv_rate: services per hour
        """

        validate_process(symbol, srv_rate, "srv_rate", "ST")
        self.symbol = symbol
        self.srv_rate = srv_rate

    def get_ST(self, server, customer_nr=[]):
        """
        Return service time; deterministic rows follow one-based customer IDs.
        """

        if self.symbol == "M" or self.symbol[0] == "E":
            return server.service_distribution.rvs()

        elif self.symbol == "D":
            return server.service_distribution.iloc[customer_nr - 1]["ST"]
