

class ServiceProcess:
    """
    Class to represent the service process
    """

    def __init__(self, symbol='M', srv_rate=9):
        """
        symbol: symbol of the process (M, E_k, etc.)
        srv_rate: services per hour
        """

        self.symbol = symbol
        self.srv_rate = srv_rate
