from scipy import stats
import numpy as np
import pandas as pd
from openqtsim._validation import (
    validate_positive_integer, validate_positive_rate, validate_process,
)
from openqtsim._random import create_random_streams
from openqtsim._statistics import calculate_statistics


class MM1:
    """
    A simple simulation method for MM1 queues
    - MM1.get_IAT_and_ST: generates lists of IAT's and ST's drawn from exponential distributions
    - MM1.calculate: values for AT, TSB, TSE, TCSS, TCWG and ITS are calculated per arrival
    - MM1.get_stats: print basic statistics based on the simulation results
    """
    def __init__(self, lam, mu, nr_arr, *, arrival_seed=None, service_seed=None):
        """
        Initialization the basic time unit is hours.
        """

        validate_positive_rate(lam, "lam")
        validate_positive_rate(mu, "mu")
        validate_positive_integer(nr_arr, "nr_arr")
        self.arrival_rng, self.service_rng = create_random_streams(arrival_seed, service_seed)
        self.lam = lam  # arrivals per hour
        self.mu = mu  # departures per hour
        self.nr_arr = nr_arr  # nr of customers

    def get_IAT_and_ST(self):  # generate list of inter arrival times
        """
        Generate lists of IAT's and ST's drawn from exponential distributions.
        """

        rv_iat = stats.expon(scale=1 / self.lam)
        rv_st = stats.expon(scale=1 / self.mu)

        # generate list of inter arrival times
        IAT = rv_iat.rvs(self.nr_arr, random_state=self.arrival_rng)

        # generate list of service times
        ST = rv_st.rvs(self.nr_arr, random_state=self.service_rng)

        return IAT, ST

    def calculate(self, IAT, ST):
        """
        Values for AT, TSB, TSE, TCSS, TCWG and ITS are calculated per arrival
        """

        for values, name in [(IAT, "IAT"), (ST, "ST")]:
            if np.ndim(values) != 1 or len(values) != self.nr_arr:
                raise ValueError("{} must be a one-dimensional sequence with nr_arr values.".format(name))
            validate_process("D", pd.DataFrame({name: values}), name, name)

        df_cust = pd.DataFrame()
        AT = []
        TSB = []
        TSE = []
        TCSS = []
        TCWQ = []
        ITS = []

        for i in range(len(IAT)):
            # AT
            if i == 0:
                AT.append(IAT[i])  # time starts at 0 and the first arrival arrives at 0 + IAT
            else:
                AT.append(AT[i - 1] + IAT[i])  # next arrivals start at the previous arrival AT[i-1] + IAT

            # TSB
            if i == 0:
                TSB.append(AT[i])  # first arrival the queue is empty so service begins as soon as customer arrives
            else:
                TSB.append(np.max([AT[i], TSE[i - 1]]))

            # TSE
            TSE.append(TSB[i] + ST[i])  # moment service begins plus service time

            # TCSS
            TCSS.append(TSE[i] - AT[i])  # moment of arrival until service ends

            # TCWQ
            TCWQ.append(TSB[i] - AT[i])  # moment of arrival until service begins

            # ITS
            if i == 0:
                ITS.append(IAT[i])  # the server will start idle until the first arrival
            else:
                ITS.append(np.max([AT[i] - TSE[i - 1], 0]))

        # Add lists to dataframe
        df_cust["IAT"] = IAT
        df_cust["ST"] = ST
        df_cust["AT"] = AT
        df_cust["TSB"] = TSB
        df_cust["TSE"] = TSE
        df_cust["TCSS"] = TCSS
        df_cust["TCWQ"] = TCWQ
        df_cust["ITS"] = ITS

        return df_cust

    def get_stats(self, df_cust):
        """
        Print and return statistics over time 0 through the last completion.
        """

        summary = calculate_statistics(df_cust)
        value = summary["waiting_factor"]
        print('Waiting time over service time: {}'.format(
            "{:.4f}".format(value) if value is not None else "undefined (mean service time is zero)"))
        print('Observation horizon: 0 to {:.4f} hours'.format(summary["observation_end"]))
        print('')

        value = summary["Rho_system"]
        print('Rho: system utilisation: {:.4f}'.format(value))
        print('')

        value = summary["P_0"]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))

        value = summary["W_s"]
        print('W_s: average time spent in the system: {:.4f}'.format(value))

        value = summary["W_q"]
        print('W_q: average time spent in the queue: {:.4f}'.format(value))

        value = summary["IAT"]
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = summary["ST"]
        print('ST: average service time: {:.4f}'.format(value))
        print('')
        return summary
