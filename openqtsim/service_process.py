from scipy import stats


class ServiceProcess:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats for probability distribution of service times or a deterministic list
    """

    def __init__(self, symbol='M', srv_rate=9):
        """
        srv_rate is in services per hour (corresponding to t_scale = 1)
        t_scale 1: hours, 60: minutes, 3600: seconds, etc
        select t_scale = 3600 if you want the simulation to be in seconds
        """

        self.symbol = symbol

        if self.symbol == "M":
            aver_ST = 1/srv_rate
            self.service_distribution = stats.expon(scale=aver_ST)

        elif self.symbol == "E2":
            aver_ST = 1/srv_rate
            self.service_distribution = stats.erlang(2, scale=aver_ST)

        elif self.symbol == "D":
            self.service_distribution = srv_rate

    def get_ST(self, customer_nr=[]):
        """
        Return the service time based on the service time distribution or deterministic list
        """

        if self.symbol == "M" or self.symbol == "E2":
            return self.service_distribution.rvs(), customer_nr

        elif self.symbol == "D":
            return self.service_distribution.loc[customer_nr, ['ST']].item(), \
                   self.service_distribution.loc[customer_nr, ['name']].item()
