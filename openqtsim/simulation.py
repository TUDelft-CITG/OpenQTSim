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

    def __init__(self, queue, max_arr=100, IAT_tol=0.001, ST_tol=0.001, priority=False, seed=4, t_scale=1):
        """
        Initialization the basic time unit is hours. Timescaling multiplies
        """
        self.sim_start = datetime.datetime.now()
        self.env = simpy.Environment(initial_time=time.mktime(self.sim_start.timetuple()))
        self.env.epoch = time.mktime(self.sim_start.timetuple())
        self.t_scale = t_scale
        self.queue = queue

        self.customer_nr = 0
        self.IAT_tot = 0
        self.ST_tot = 0
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

        """
        Simulate the queue
        q = queueing.queue(A, S, c)
        sim = queueing.simulation(q)
        sim.simulate(5)
        """

        # arrival_process = self.queue.A
        self.env.process(self.queue.populate(self.env, self))

        # self.environment.process(self.queue.A.arrival(self.environment, self))

    def run(self, max_arr=1000, IAT_tol=0.001, ST_tol=0.001):
        self.max_arr = max_arr
        self.IAT_tol = IAT_tol
        self.ST_tol = ST_tol

        self.env.run()

    def log_entry(self, customer_id, IAT, AT, ST, TSB, TSE, QL):
        """
        # the following items are logged per customer that enters the system:
        # c = customer
        # IAT = inter arrival time
        # AT = arrival time
        # ST = service time
        # TSB = time service begins
        # TCWQ = time customer waits in the queue
        # TSE = time service ends
        # TCSS = time customer spends in the system
        # ITS = idle time of the server   
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
        # https://www.youtube.com/watch?v=nDXD8oVelo4
        # https: // www.youtube.com / watch?v = QppldN - t4pQ
        # https: // www.supositorio.com / rcalc / rcalclite.htm
        print('Average IAT: {:.4f} [hours]'.format((np.sum(self.log["IAT"])/self.t_scale)/(len(self.log["c_id"]))))
        print('Average ST: {:.4f} [hours]'.format((np.sum(self.log["ST"])/self.t_scale)/(len(self.log["c_id"]))))
        print('Rho: System utilisation: {:.4f}'.format((((self.log["TSE"][-1] - np.sum(self.log["ITS"])) / self.log["TSE"][-1]))))
        print('')
        print('Total number of customers: {:.2f}'.format((len(self.log["c_id"]))))
        print('')
        print('W_s: Average time spent in the system: {:.2f} [hours]'.format((np.mean(self.log["TCSS"])/self.t_scale)))
        print('W_q: Average time spent in the queue: {:.2f} [hours]'.format((np.mean(self.log["TCWQ"])/self.t_scale)))

        av_arr = self.t_scale/(np.sum(self.log["IAT"]) / (len(self.log["c_id"]) - 1))
        av_ser = self.t_scale/(np.sum(self.log["ST"]) / (len(self.log["c_id"]) - 1))
        print('Average nr arrivals: {:.2f} [# per hour]'.format(av_arr))
        print('Average nr services: {:.2f} [# per hour]'.format(av_ser))
        # print('Average nr people in the system: {:.2f}'.format(av_arr*(np.mean(self.log["TCSS"])/3600)))

        print('')
        print('Total waiting time: {:.4f} [hours]'.format(np.sum(self.log["TCWQ"])/self.t_scale))
        print('Average waiting time of all customers: {:.2f} [hours]'.format((np.sum(self.log["TCWQ"])/self.t_scale) / (len(self.log["c_id"]))))
        print('Average waiting time of customers that waited: {:.2f} [hours]'.format((np.sum(self.log["TCWQ"])/self.t_scale) / np.sum(np.array(self.log["TCWQ"]) != 0)))

        print('')
        print('P_0: Probability of idle server (nobody in the system): {:.4f}'.format(np.sum(self.log["ITS"]) / self.log["TSE"][-1]))
        print('Probability that somebody is waiting: {:.4f}'.format(np.sum(np.array(self.log["QL"]) != 0) / (len(self.log["c_id"]))))
        print('Probability that nobody is waiting: {:.4f}'.format(np.sum(np.array(self.log["QL"]) == 0) / (len(self.log["c_id"]))))
        print('P_2: Probability that 1 person is waiting: {:.4f}'.format(np.sum(np.array(self.log["QL"]) == 1) / (len(self.log["c_id"]))))
        print('P_3: Probability that 2 persons are waiting: {:.4f}'.format(np.sum(np.array(self.log["QL"]) == 2) / (len(self.log["c_id"]))))
        print('P_4: Probability that 3 persons are waiting: {:.4f}'.format(np.sum(np.array(self.log["QL"]) == 3) / (len(self.log["c_id"]))))
        print('P_10: Probability that 9 persons are waiting (10 in system): {:.4f}'.format(np.sum(np.array(self.log["QL"]) == 9) / (len(self.log["c_id"]))))
        print('')
        # print('Total service time: {:.2f} [seconds]'.format(np.sum(self.log["ST"])))
        # print('Average total time a customer spent in the system: {:.2f} [seconds]'.\
        #       format(np.sum(self.log["TCSS"]) / (len(self.log["c_id"]))))
        print('Average waiting time as a fraction of ST: {:.2f}'.format(np.mean(np.array(self.log["TCWQ"]))/np.mean(np.array(self.log["ST"]))))
        print('')

