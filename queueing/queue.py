import numpy as np
import pandas as pd


class queue:
    """
    Queueing node based on Kendall's notation, in which:
    - A is the arrival process
    - S is the service time distribution
    - c is the number of servers
    - K is the number of places in the system
    - N is the calling population
    - D is the queue discipline
    """

    def __init__(self, A, S, c, K=np.inf, N=np.inf, D="FIFO", customers=[]):
        """
        Initialization
        The first six inputs are the typical Kendall inputs.
        In case the simulation type is 'stochastic' A and S should be distributions from which separate instances can
        be drawn. When the simulation type is 'deterministic' A and S should be equal length lists with values for
        inter arrival times and service times. These will then one by one be picked in the simulation. Optional is to
        add a corresponding list of customer ids or names. This will not influence statistics but may make inspection
        of the simulation outputs easier.
        """

        self.A = A
        self.S = S
        self.c = c
        self.K = K
        self.N = N
        self.D = D
        self.customers = customers

        # if 1 < self.utilization:
        #     raise AssertionError(
        #         "1 < Utilization. \nIf the utilization is larger than the number of servers the queue length will become infinitely long"
        #     )

    @property
    def kendall_notation(self):
        """
        Return queue according to the kendall notation.
        """

        return "{}/{}/{}/{}/{}/{}".format(
            self.A.symbol, self.S.symbol, str(self.c), str(self.K), str(self.N), self.D
        )

    # @property
    # def utilization(self):
    #     """
    #     Returns the utilization.
    #
    #     If the utilization is larger than c the queue length will explode,
    #     become infinitely long.
    #
    #     For an M/M/c queue:
    #     The queue utilazation (rho) is equal to arrival rate (lambda)
    #     multiplied with the mean service time (E(S)).
    #     """
    #
    #     if (
    #         self.kendall_notation[:3] == "M/M"
    #         and self.kendall_notation[-12:] == "inf/inf/FIFO"
    #     ):
    #         return (self.A.arrival_rate) / ((self.S.service_rate) * self.c)
    #
    # @property
    # def delay_probability(self):
    #     """
    #     Returns the delay probability
    #     """
    #     # Try to vectorize this
    #     part_1 = ((self.c * self.utilization) ** self.c) / np.math.factorial(self.c)
    #
    #     part_2 = 0
    #     for n in range(self.c):
    #         part_2 += ((self.c * self.utilization) ** n) / np.math.factorial(n)
    #
    #     part_3 = ((self.c * self.utilization) ** self.c) / np.math.factorial(self.c)
    #
    #     return part_1 / ((1 - self.utilization) * part_2 + part_3)
    #
    #
    # @property
    # def mean_queue_length(self):
    #     """
    #     Returns the mean queue length, E(L).
    #
    #     For an M/M/c queue:
    #
    #     """
    #
    #     if (
    #         self.kendall_notation[:3] == "M/M"
    #         and self.kendall_notation[-12:] == "inf/inf/FIFO"
    #     ):
    #         return self.delay_probability * (self.utilization / (1 - self.utilization))
    #
    # @property
    # def mean_waiting_time(self):
    #     """
    #     Returns the mean waiting time, E(W).
    #
    #     For an M/M/c queue:
    #
    #     """
    #
    #     if (
    #         self.kendall_notation[:3] == "M/M"
    #         and self.kendall_notation[-12:] == "inf/inf/FIFO"
    #     ):
    #         return (
    #             self.delay_probability
    #             * (1 / (1 - self.utilization))
    #             * (1 / (self.c * (self.S.service_rate)))
    #         )
    #
    # def steady_state_stats(self):
    #     """
    #     Return the steady state solutions.
    #     """
    #
    #     return pd.DataFrame.from_dict(
    #         {
    #             "Mean queue length": self.mean_queue_length,
    #             "Mean waiting time": self.mean_waiting_time,
    #         }
    #     )
