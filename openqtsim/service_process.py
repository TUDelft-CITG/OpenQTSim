

class ServiceProcess:
    """
    Server process class for use in the OpenQTSim package
    """

    def __init__(self, symbol='M', srv_rate=9):
        """
        symbol: symbol of the process (M, E_k, etc.)
        srv_rate: services per hour
        """

        self.symbol = symbol
        self.srv_rate = srv_rate

    def get_ST(self, server, customer_nr=[]):
        """
        Return the inter arrival time based on the inter arrival time distribution or deterministic list
        """

        if self.symbol == "M" or self.symbol == "E2":
            return server.service_distribution.rvs()

        elif self.symbol == "D":
            return server.service_distribution.loc[customer_nr, ['ST']].item()
