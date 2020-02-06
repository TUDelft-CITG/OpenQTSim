from scipy import stats
import numpy as np
import pandas as pd


class MM1:
    def __init__(self, lam, mu, nr_arr, seed=None):
        """
        Initialization the basic time unit is hours. Timescaling multiplies
        """
        self.lam = lam
        self.mu = mu
        self.nr_arr = nr_arr
        self.seed = seed

    def get_IAT_and_ST(self):  # generate list of inter arrival times

        rv_iat = stats.expon(scale=1 / self.lam)
        rv_st = stats.expon(scale=1 / self.mu)

        # generate list of inter arrival times
        np.random.seed(self.seed)
        IAT = rv_iat.rvs(self.nr_arr)

        # generate list of service times
        ST = rv_st.rvs(self.nr_arr)

        return IAT, ST

    def calculate_MM1(self, IAT, ST):
        df = pd.DataFrame()
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
                ITS.append(np.max([AT[i] - TSE[i - 1], 0]))  # todo: I don't think this works with multiple servers

        # Add lists to dataframe
        df["IAT"] = IAT
        df["ST"] = ST
        df["AT"] = AT
        df["TSB"] = TSB
        df["TSE"] = TSE
        df["TCSS"] = TCSS
        df["TCWQ"] = TCWQ
        df["ITS"] = ITS

        return df

    def get_stats(self, df):
        value = np.mean(df["TCWQ"]) / np.mean(df["ST"])
        print('Waiting time over service time: {:.4f}'.format(value))
        print('')

        value = (df["TSE"].iloc[-1] - np.sum(df["ITS"])) / df["TSE"].iloc[-1]
        print('Rho: system utilisation: {:.4f}'.format(value))
        print('')

        value = np.sum(df["ITS"]) / df["TSE"].iloc[-1]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))

        value = np.mean(df["TCSS"])
        print('W_s: the long term average time spent in the system: {:.4f}'.format(value))

        value = np.mean(df["TCWQ"])
        print('W_q: the long term average time spent in the queue: {:.4f}'.format(value))

        value = df["AT"].iloc[-1]/(len(df["ST"])-1)
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = np.sum(df["ST"])/(len(df["ST"]))
        print('ST: average service time: {:.4f}'.format(value))
        print('')
