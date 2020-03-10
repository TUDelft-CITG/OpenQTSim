import simpy
import pandas as pd
import numpy as np
import datetime
import time
from scipy import stats
from collections import namedtuple


class Simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(self, queue, max_arr=100, priority=False, seed=None):
        """
        Initialization (the basic time unit is hours)
        """
        self.queue = queue
        self.max_arr = max_arr

        # set simulation time and epoch
        self.sim_start = datetime.datetime.now()
        self.env = simpy.Environment(initial_time=time.mktime(self.sim_start.timetuple()))
        self.env.epoch = time.mktime(self.sim_start.timetuple())

        # initialise counters and logs
        self.customer_nr = 0
        self.t = [0]
        self.t_c_s = [0]
        self.t_c_q = [0]
        self.system_state = pd.DataFrame(columns=['t', 'c_s', 'c_q'])
        self.c_s = 0  # people in the system
        self.c_q = 0  # people in the queue
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
            "s_id": []}  # s_id = server id

        # activate random seed
        np.random.seed(seed)

        # set nr of servers
        if not priority:

            # arrival distribution
            aver_IAT = 1 / self.queue.A.arr_rate
            if self.queue.A.symbol == "M":
                self.queue.A.arrival_distribution = stats.expon(scale=aver_IAT)
            elif self.queue.A.symbol == "E2":
                self.queue.A.arrival_distribution = stats.erlang(2, scale=aver_IAT)

            # service distribution
            self.env.servers = simpy.FilterStore(self.env, capacity=self.queue.c)
            self.env.servers.items = []
            self.env.server_info = {}
            Server = namedtuple('Server', 'service_distribution, last_active, id')
            aver_ST = 1 / self.queue.S.srv_rate
            if self.queue.S.symbol == "M":
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(stats.expon(scale=aver_ST), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})
            elif self.queue.S.symbol == "E2":
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(stats.erlang(2, scale=aver_ST), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

        else:
            pass

        # initiate queue populating process
        self.env.process(self.queue.populate(self.env, self))

    def run(self, max_arr=1000):
        self.max_arr = max_arr

        self.env.run()

    def log_entry(self, customer_id, IAT, AT, ST, TSB, TSE, ITS, s_id):
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
        self.log["ITS"].append(ITS)
        self.log["s_id"].append(s_id)

    def return_log(self):
        """
        Return the log in the form of a pandas data frame.
        The input 'nr_of_records_to_display' determines how many records are displayed starting from 1. If set to 0 all
        records are displayed.
        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """

        df = pd.DataFrame.from_dict(self.log)

        df_sys = pd.DataFrame(columns=['t', 'c_s', 'c_q'])
        df_sys['t'] = self.t
        df_sys['c_s'] = self.t_c_s
        df_sys['c_q'] = self.t_c_q
        df_sys = df_sys.sort_values(by=['t'], ascending=[True])

        return df, df_sys

    def get_stats(self):

        df, df_sys = self.return_log()

        value = np.mean(df["TCWQ"]) / np.mean(df["ST"])
        # value = np.mean(df[df["TCWQ"] != 0]["TCWQ"]) / np.mean(df["ST"])
        print('Waiting time over service time: {:.4f}'.format(value))
        print('')

        value = (df["TSE"].iloc[-1] - (np.sum(df["ITS"])/self.queue.c)) / df["TSE"].iloc[-1]
        print('Rho: server utilisation: {:.4f}'.format(value))

        value = np.sum(df["ITS"]) / df["TSE"].iloc[-1]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))
        print('')

        value = np.mean(df_sys['c_s'])
        print('L_s: average nr of customers in the system: {}'.format(value))
        value = np.mean(df_sys['c_q'])
        print('L_q: average nr of customers in the queue: {}'.format(value))
        value = np.mean(df["TCSS"])
        print('W_s: the long term average time spent in the system: {:.4f}'.format(value))
        value = np.mean(df["TCWQ"])
        print('W_q: the long term average time spent in the queue: {:.4f}'.format(value))
        print('')

        value = df["AT"].iloc[-1]/(len(df["ST"])-1)
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = np.sum(df["ST"])/(len(df["ST"]))
        print('ST: average service time: {:.4f}'.format(value))
        print('')

