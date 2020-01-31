import simpy
import random
import pandas as pd
import numpy as np
import datetime
import time


class simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(self, queue, type='probabilistic', maxarrivals=100, priority=False, seed=4):
        """
        Initialization
        """
        self.simulation_start = datetime.datetime.now()
        self.environment = simpy.Environment(initial_time=time.mktime(self.simulation_start.timetuple()))
        self.environment.epoch = time.mktime(self.simulation_start.timetuple())

        self.queue = queue

        self.customer_nr = 0
        self.maxarrivals = maxarrivals

        self.type = type

        self.log = {
            "c": [],  # c = customer
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
            "TSE": [],  # TSE = time service ends
            "TCSS": [],  # TCSS = time customer spends in the system
            "TCWQ": [],  # TCWQ = time customer waits in the queue
            "ITS": []}  # ITS = idle time of the server
        self.seed = seed

        # set nr of servers
        if priority == False:
            self.environment.servers = simpy.Resource(self.environment, capacity=queue.c)
        else:
            self.environment.servers = simpy.PriorityResource(self.environment, capacity=queue.c)

        """
        Simulate the queue
        q = queueing.queue(A, S, c)
        sim = queueing.simulation(q)
        sim.simulate(5)
        """

        # arrival_process = self.queue.A
        self.environment.process(self.queue.A.arrival(self.environment, self))

    def run(self, maxarrivals=1000):
        self.maxarrivals = maxarrivals

        self.environment.run()

        print("")
        print("*** Simulation finished in {}".format(datetime.timedelta(seconds=int(self.environment.now - self.environment.epoch))))

    def log_entry(self, customer_nr, IAT, AT, ST, TSB, TSE):
        """
        Update the log based on the current timestamp.
        # c = customer
        # IAT = inter arrival time
        # AT = now + IAT
        # ST = service time
        # TSB = time service begins
        # TCWQ = time customer waits in the queue
        # TSE = time service ends
        # TCSS = time customer spends in the system
        # ITS = idle time of the server   
        """

        self.log["c"].append(customer_nr)
        self.log["IAT"].append(IAT)
        self.log["ST"].append(ST)
        self.log["AT"].append(AT)
        self.log["TSB"].append(TSB)
        self.log["TSE"].append(TSE)
        self.log["TCWQ"].append(TSB - AT)  # todo: check
        self.log["TCSS"].append(TSE - AT)  # todo: check
        if len(self.log["c"]) == 1:
            self.log["ITS"].append(0)  # todo: check
        else:
            self.log["ITS"].append(max([AT - self.log["TSE"][-2], 0]))  # todo: check

        # self.log["c"].append(self.customer_nr)
        # self.log["IAT"].append(IAT)
        # self.log["ST"].append(ST)
        # if self.customer_nr == 1:
        #     self.log["AT"].append(0 + IAT)
        # else:
        #     self.log["AT"].append(self.log["AT"][-1] + IAT)
        #
        # if self.customer_nr == 1:
        #     self.log["TSB"].append(self.log["AT"][-1])
        # else:
        #     self.log["TSB"].append(max([self.log["TSE"][-1], self.log["AT"][-1]]))
        #
        # self.log["TSE"].append(self.log["TSB"][-1] + ST)
        # self.log["TCWQ"].append(self.log["TSB"][-1] - self.log["AT"][-1])  # todo: check
        # self.log["TCSS"].append(self.log["TSE"][-1] - self.log["AT"][-1])  # todo: check
        # if self.customer_nr == 1:
        #     self.log["ITS"].append(0)  # todo: check
        # else:
        #     self.log["ITS"].append(max([self.log["AT"][-1] - self.log["TSE"][-2], 0]))  # todo: check

    def return_log(self, to_csv=False):
        """
        Return the log in the form of a pandas data frame.
        
        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """

        dataframe = pd.DataFrame.from_dict(self.log)

        if to_csv == True:
            dataframe.to_csv("simulation_results.csv")

        return dataframe

    def get_stats(self):
        # https://www.youtube.com/watch?v=nDXD8oVelo4
        print('Total number of customers: {:.2f}'.format(self.log["c"][-1]))
        print('Average time between arrivals: {:.2f}'.format(np.sum(self.log["IAT"]) / (self.log["c"][-1] - 1)))
        print('Average service time: {:.2f}'.format(np.sum(self.log["ST"]) / self.log["c"][-1]))
        print('')
        print('Total waiting time: {:.2f}'.format(np.sum(self.log["TCWQ"])))
        print('Average waiting time of all customers: {:.2f}'.format(np.sum(self.log["TCWQ"]) / self.log["c"][-1]))
        print('Average waiting time of customers that waited: {:.2f}'.format(np.sum(self.log["TCWQ"]) / np.sum(np.array(self.log["TCWQ"]) != 0)))
        print('Probability that customers are waiting: {:.2f}'.format(np.sum(np.array(self.log["TCWQ"]) != 0) / self.log["c"][-1]))
        print('')
        print('Total service time: {:.2f}'.format(np.sum(self.log["ST"])))
        print('Average total time a customer spent in the system: {:.2f}'.\
              format(np.sum(self.log["TCSS"]) / self.log["c"][-1]))
        print('Probability of idle server: {:.2f}'.format(np.sum(self.log["ITS"]) / self.log["TSE"][-1]))

        # deze klopt niet helemaal lijkt het
        print('')
        print('Server utilisation (%):', (np.sum(self.log["ITS"]) / np.sum(self.log["TCSS"]) / self.log["c"][-1]) * 100)

