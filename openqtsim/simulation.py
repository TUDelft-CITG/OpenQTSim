import simpy
import pandas as pd
import numpy as np
import datetime
import time
from scipy import stats
from collections import namedtuple
import matplotlib.pyplot as plt


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
        self.c_s = 0  # people in the system
        self.c_q = 0  # people in the queue
        self.system_state = {
            "t": [0],
            "c_s": [0],
            "c_q": [0]}

        self.customer_nr = 0
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

        # define arrival and service processes
        if not priority:

            # --- arrival distribution ---
            if self.queue.A.symbol == "M":
                # define the average inter arrival time and add distribution with appropriate scaling
                aver_IAT = 1 / self.queue.A.arr_rate
                self.queue.A.arrival_distribution = stats.expon(scale=aver_IAT)

            elif self.queue.A.symbol == "E2":
                # define the average inter arrival time and add distribution with appropriate scaling
                aver_IAT = 1 / self.queue.A.arr_rate
                self.queue.A.arrival_distribution = stats.erlang(2, scale=aver_IAT)

            elif self.queue.A.symbol == "D":
                # the deterministic type expects arr_rate to contain a dataframe with columns ["name","IAT","AT"]
                self.queue.A.arrival_distribution = self.queue.A.arr_rate

            # --- service distribution ---
            self.env.servers = simpy.FilterStore(self.env, capacity=self.queue.c)
            self.env.servers.items = []  # to be filled in the next steps depending on S.symbol
            self.env.server_info = {}  # to be filled in the next steps depending on S.symbol
            Server = namedtuple('Server', 'service_distribution, last_active, id')

            if self.queue.S.symbol == "M":
                # define the average service time and add distribution with appropriate scaling for each server
                aver_ST = 1 / self.queue.S.srv_rate
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(stats.expon(scale=aver_ST), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

            elif self.queue.S.symbol == "E2":
                # define the average service time and add distribution with appropriate scaling for each server
                aver_ST = 1 / self.queue.S.srv_rate
                for i in range(1, self.queue.c + 1):
                    self.env.servers.items.append(Server(stats.erlang(2, scale=aver_ST), self.env.now, i))
                    self.env.server_info.update({i: {'last_active': self.env.now}})

            elif self.queue.A.symbol == "D":
                if self.queue.c == 1:
                    # for 1 server the deterministic type expects srv_rate to contain a dataframe
                    # with columns: ["name","ST"]
                    self.env.servers.items.append(Server(self.queue.S.srv_rate, self.env.now, 1))
                    self.env.server_info.update({1: {'last_active': self.env.now}})
                else:
                    # for n servers the deterministic type expects srv_rate to contain a dataframe
                    # with columns: ["name","ST","s_id"]
                    for i in range(1, self.queue.c + 1):
                        self.env.servers.items.append(Server(self.queue.S.srv_rate[self.queue.S.srv_rate["s_id"] == i],
                                                             self.env.now, i))
                        self.env.server_info.update({i: {'last_active': self.env.now}})

        else:
            pass
            # Todo: add the option of having priority arrivals?

        # initiate queue populating process
        self.env.process(self.queue.populate(self.env, self))

    def run(self, max_arr=1000):
        """
        Run simulation
        """

        self.max_arr = max_arr

        self.env.run()

    def log_customer_state(self, customer_id, IAT, AT, ST, TSB, TSE, ITS, s_id):
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
        # s_id = id of server assigned to customer
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

    def log_system_state(self, t, c_s, c_q):
        """
        # the following items are logged for the state of the system:
        # t = time (from start of simulation)
        # c_s = number of customers in the system
        # c_q = number of customers in the queue
        """

        self.system_state["t"].append(t)
        self.system_state["c_s"].append(c_s)
        self.system_state["c_q"].append(c_q)

    def return_log(self):
        """
        Return the log in the form of a pandas data frame.
        """

        # convert self.log to dataframe
        df_cust = pd.DataFrame.from_dict(self.log)
        df_cust = df_cust.sort_values(by=['AT'], ascending=[True])

        # convert self.system_state to dataframe
        df_sys = pd.DataFrame.from_dict(self.system_state)
        df_sys = df_sys.sort_values(by=['t'], ascending=[True])

        return df_cust, df_sys

    def get_stats(self):
        """
        Post processing of logs to print basic simulation statistics
        """

        df_cust, df_sys = self.return_log()

        value = np.mean(df_cust["TCWQ"]) / np.mean(df_cust["ST"])
        print('Waiting time over service time: {:.4f}'.format(value))
        print('')

        value = (df_cust["TSE"].iloc[-1] - np.sum(df_cust["ITS"])) / df_cust["TSE"].iloc[-1]
        print('Rho_system: system utilisation: {:.4f}'.format(value))
        value = (df_cust["TSE"].iloc[-1] - (np.sum(df_cust["ITS"])/self.queue.c)) / df_cust["TSE"].iloc[-1]
        print('Rho_server: server utilisation: {:.4f}'.format(value))

        value = np.sum(df_cust["ITS"]) / df_cust["TSE"].iloc[-1]
        print('P_0: probability nobody in the system: {:.4f}'.format(value))
        print('')

        value = np.mean(df_sys['c_s'])
        print('L_s: average nr of customers in the system: {}'.format(value))
        value = np.mean(df_sys['c_q'])

        print('L_q: average nr of customers in the queue: {}'.format(value))
        value = np.mean(df_cust["TCSS"])
        print('W_s: the long term average time spent in the system: {:.4f}'.format(value))
        value = np.mean(df_cust["TCWQ"])
        print('W_q: the long term average time spent in the queue: {:.4f}'.format(value))
        print('')

        value = df_cust["AT"].iloc[-1]/(len(df_cust["ST"])-1)
        print('IAT: average inter arrival time: {:.4f}'.format(value))

        value = np.sum(df_cust["ST"])/(len(df_cust["ST"]))
        print('ST: average service time: {:.4f}'.format(value))
        print('')

    def plot_system_state(self, fontsize=20):
        """
        Plot number of customers in the system and in the queue as a function of time
        """

        df_cust, df_sys = self.return_log()

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(df_sys['t'].values, df_sys['c_s'].values, '-bo', markersize=.1, label='c_s')
        ax.plot(df_sys['t'].values, df_sys['c_q'].values, '-ro', markersize=.1, label='c_q')

        ax.set_xlabel('Time [hours]', fontsize=fontsize)
        ax.set_ylabel('nr of customers', fontsize=fontsize)
        ax.set_title('System state: {}'.format(self.queue.kendall_notation), fontsize=fontsize)
        ax.legend(loc='upper right', fontsize=fontsize)

