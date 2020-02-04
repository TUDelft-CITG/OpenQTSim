from scipy import stats


class ArrivalProcess:
    """
    Class to represent the arrival process:
    - symbol is the symbol of the process (M, E_k, etc.)
    - scipy.stats probility distribution of arrival times
    """

    def __init__(self, symbol='M', arr_rate=8, t_scale=1):
        """
        arr_rate is in arrivals per hour (corresponding to t_scale = 1)
        t_scale 1: hours, 60: minutes, 3600: seconds, etc
        select t_scale = 3600 if you want the simulation to be in seconds
         """

        self.symbol = symbol
        self.t_scale = t_scale

        if self.symbol == "M":
            aver_IAT_in_t_scale = (1 * self.t_scale)/arr_rate
            self.arrival_distribution = stats.expon(scale=aver_IAT_in_t_scale)

        elif self.symbol == "D":
            self.arrival_distribution = arr_rate

    def get_IAT(self, customer_nr=[]):
        """
        Return the service time based on the service time distribution.
        """

        if self.symbol == "M":
            return self.arrival_distribution.rvs()

        elif self.symbol == "D":
            return self.arrival_distribution.loc[customer_nr, ['IAT']].item()
