from scipy import stats


class service_process:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats probility distribution of service times
    """

    def __init__(self, symbol, service_distribution):
        """
        Initialization
        """

        self.symbol = symbol
        self.service_distribution = service_distribution
        self.service_rate = 1. / self.service_distribution.mean()
        self.mean_service_time = self.service_distribution.mean()

    def service(self):
        """
        Return the service time based on the service time distribution.
        """
        
        return self.service_distribution.rvs()
