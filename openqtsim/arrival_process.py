from scipy import stats


class ArrivalProcess:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats probility distribution of arrival times
    """

    def __init__(self, symbol, arr_rate, t_scale=3600):
        """
        arr_rate is in arrivals per hour
        """

        self.symbol = symbol
        self.t_scale = t_scale

        if self.symbol == "M":
            aver_IAT_in_t_scale = (1 * self.t_scale)/arr_rate
            self.arrival_distribution = stats.expon(scale=aver_IAT_in_t_scale)

    def get_IAT(self):
        """
        Return the service time based on the service time distribution.
        """

        return self.arrival_distribution.rvs()
