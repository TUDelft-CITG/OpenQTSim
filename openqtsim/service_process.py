from scipy import stats


class ServiceProcess:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats probility distribution of service times
    """

    def __init__(self, symbol, srv_rate, t_scale=3600):
        """
        srv_rate is in services per hour
        """

        self.symbol = symbol
        self.t_scale = t_scale

        if self.symbol == "M":
            aver_ST_in_t_scale = (1 * self.t_scale)/srv_rate
            self.service_distribution = stats.expon(scale=aver_ST_in_t_scale)

    def get_ST(self):
        """
        Return the service time based on the service time distribution.
        """

        return self.service_distribution.rvs()
