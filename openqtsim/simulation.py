import simpy
import pandas as pd
import numpy as np
import datetime
import time


class MonitoredResource(simpy.Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().release(*args, **kwargs)


class Simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(self, queue, max_arr=100, IAT_tol=0.0001, ST_tol=0.0001, priority=False, seed=None, t_scale=1):
        """
        Initialization the basic time unit is hours.
        """
        self.sim_start = datetime.datetime.now()
        self.env = simpy.Environment(initial_time=time.mktime(self.sim_start.timetuple()))
        self.env.epoch = time.mktime(self.sim_start.timetuple())
        self.t_scale = t_scale
        self.queue = queue

        self.customer_nr = 0
        self.max_arr = max_arr
        self.IAT_tol = IAT_tol
        self.ST_tol = ST_tol

        self.log = {
            "c_id": [],  # c_id = customer id
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
            "TSE": [],  # TSE = time service ends
            "TCSS": [],  # TCSS = time customer spends in the system
            "TCWQ": [],  # TCWQ = time customer waits in the queue
            "ITS": [],  # ITS = idle time of the server
            "QL": []}  # QL = customers in the queue

        np.random.seed(seed)

        # set nr of servers
        if not priority:
            self.env.servers = MonitoredResource(self.env, capacity=self.queue.c)
        else:
            self.env.servers = MonitoredResource(simpy.PriorityResource(self.env, capacity=self.queue.c))

        self.env.process(self.queue.populate(self.env, self))

    def run(self, max_arr=1000, IAT_tol=0.001, ST_tol=0.001):
        self.max_arr = max_arr
        self.IAT_tol = IAT_tol
        self.ST_tol = ST_tol

        self.env.run()

    def log_entry(self, customer_id, IAT, AT, ST, TSB, TSE, QL):
        """
        # the following items are logged per customer that enters the system:
        # c = customer id
        # IAT = inter arrival time
        # ST = service time
        # AT = arrival time
        # TSB = time service begins
        # TSE = time service ends
        # TCSS = time customer spends in the system
        # TCWQ = time customer waits in the queue
        # ITS = idle time of the server
        # QL = queue length (at T = TSE)
        """

        self.log["c_id"].append(customer_id)
        self.log["IAT"].append(IAT)
        self.log["ST"].append(ST)
        self.log["AT"].append(AT)
        self.log["TSB"].append(TSB)
        self.log["TSE"].append(TSE)
        self.log["TCWQ"].append(TSB - AT)
        self.log["TCSS"].append(TSE - AT)
        if len(self.log["c_id"]) == 1:
            self.log["ITS"].append(IAT)  # the server will start idle until the first arrival
        else:
            self.log["ITS"].append(max([AT - self.log["TSE"][-2], 0]))  # todo: I don't think this works with multiple servers
        self.log["QL"].append(QL)  # this is monitored by using the custom class MonitoredResource defined above

    def return_log(self, nr_of_records_to_display=0, to_csv=False):
        """
        Return the log in the form of a pandas data frame. The input 'nr_of_records_to_display' determines
        how many records are displayed starting from 1. If set to 0 all records are displayed.

        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """

        if nr_of_records_to_display == 0:
            dataframe = pd.DataFrame.from_dict(self.log)
        else:
            dataframe = pd.DataFrame.from_dict(self.log).head(nr_of_records_to_display)

        if to_csv == True:
            dataframe.to_csv("simulation_results.csv")

        return dataframe

    def get_stats(self):

        df = self.return_log()

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
