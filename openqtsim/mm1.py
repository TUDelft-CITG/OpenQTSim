from scipy import stats
import numpy as np
import pandas as pd


class MM1:
    """
    A simple simulation method for MM1 queues
    - MM1.get_IAT_and_ST: generates lists of IAT's and ST's drawn from exponential distributions
    - MM1.calculate: values for AT, TSB, TSE, TCSS, TCWG and ITS are calculated per arrival
    - MM1.get_stats: print basic statistics based on the simulation results
    """
    def __init__(self, lam, mu, nr_arr, seed=None):
        """
        Initialization the basic time unit is hours.
        """

        # todo: consider to remove seed
        self.lam = lam  # arrivals per hour
        self.mu = mu  # departures per hour
        self.nr_arr = nr_arr  # nr of customers

        np.random.seed(seed)

    def get_IAT_and_ST(self):  # generate list of inter arrival times
        """
        Generate lists of IAT's and ST's drawn from exponential distributions.
        """

        rv_iat = stats.expon(scale=1 / self.lam)
        rv_st = stats.expon(scale=1 / self.mu)

        # generate list of inter arrival times
        IAT = rv_iat.rvs(self.nr_arr)

        # generate list of service times
        ST = rv_st.rvs(self.nr_arr)

        return IAT, ST

    def calculate(self, IAT, ST):
        """
        Values for AT, TSB, TSE, TCSS, TCWG and ITS are calculated per arrival
        """

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
        Generate lists of IAT's and ST's drawn from exponential distributions.
        """

        value = np.mean(df_cust["TCWQ"]) / np.mean(df_cust["ST"])
        print('Waiting time over service time: {:.4f}'.format(value))
        print('')

        value = (df_cust["TSE"].iloc[-1] - np.sum(df_cust["ITS"])) / df_cust["TSE"].iloc[-1]
        print('Rho: system utilisation: {:.4f}'.format(value))
        print('')

        value = np.sum(df_cust["ITS"]) / df_cust["TSE"].iloc[-1]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))

        value = np.mean(df_cust["TCSS"])
        print('W_s: the long term average time spent in the system: {:.4f}'.format(value))

        value = np.mean(df_cust["TCWQ"])
        print('W_q: the long term average time spent in the queue: {:.4f}'.format(value))

        value = df_cust["AT"].iloc[-1]/(len(df_cust["ST"])-1)
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = np.sum(df_cust["ST"])/(len(df_cust["ST"]))
        print('ST: average service time: {:.4f}'.format(value))
        print('')
