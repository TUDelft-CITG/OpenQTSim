import simpy
import random
import pandas as pd
import numpy as np
import datetime, time

class simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(self, queue, maxiter=100, priority=False, seed=4):
        """
        Initialization
        """
        self.simulation_start = datetime.datetime.now()
        self.environment = simpy.Environment(initial_time=time.mktime(self.simulation_start.timetuple()))
        self.environment.epoch = time.mktime(self.simulation_start.timetuple())

        self.queue = queue

        self.customer_nr = 0
        self.maxiter = maxiter

        self.log = {
            "c": [],  # c = customer
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
            "TCWQ": [],  # TCWQ = time customer waits in the queue
            "TSE": [],  # TSE = time service ends
            "TCSS": [],  # TCSS = time customer spends in the system
            "ITS": []}  # ITS = idle time of the server

        random.seed(seed)

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

    def run(self, maxiter=1000):
        self.maxiter = maxiter

        self.environment.run()

        print("")
        print("*** Simulation finished in {}".format(datetime.timedelta(seconds=int(self.environment.now - self.environment.epoch))))

    def log_entry(self, IAT, AT, ST, TSB, TSE):
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

        # self.log["c"].append(self.customer_nr)
        # self.log["IAT"].append(IAT)
        # self.log["ST"].append(ST)
        # self.log["AT"].append(AT - self.environment.epoch)
        # self.log["TSB"].append(TSB - self.environment.epoch)
        # self.log["TSE"].append(TSE - self.environment.epoch)
        # self.log["TCWQ"].append(TSB - AT)  # todo: check
        # self.log["TCSS"].append(TSE - AT)  # todo: check
        # self.log["ITS"].append(TSB - AT)  # todo: check

        self.log["c"].append(self.customer_nr)
        self.log["IAT"].append(IAT)
        self.log["ST"].append(ST)
        if self.customer_nr == 1:
            self.log["AT"].append(0 + IAT)
        else:
            self.log["AT"].append(self.log["AT"][-1] + IAT)

        if self.customer_nr == 1:
            self.log["TSB"].append(self.log["AT"][-1])
        else:
            self.log["TSB"].append(max([self.log["TSE"][-1], self.log["AT"][-1]]))

        self.log["TSE"].append(self.log["TSB"][-1] + ST)
        self.log["TCWQ"].append(self.log["TSB"][-1] - self.log["AT"][-1])  # todo: check
        self.log["TCSS"].append(self.log["TSE"][-1] - self.log["AT"][-1])  # todo: check
        if self.customer_nr == 1:
            self.log["ITS"].append(0)  # todo: check
        else:
            self.log["ITS"].append(max([self.log["AT"][-1] - self.log["TSE"][-2], 0]))  # todo: check

    def return_log(self, to_csv=False):
        """
        Return the log in the form of a pandas dataframe.
        
        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """

        dataframe = pd.DataFrame.from_dict(self.log)

        # if to_csv == True:
        #     dataframe.to_csv("simulation_results.csv")

        return dataframe

    def get_stats(self):
        print(
            "The arrival rate is:      {:04.2f} seconds".format(
                np.mean(self.environment.arrivals)
            )
        )
        print(
            "The mean waiting time is: {:04.2f} seconds".format(
                np.mean(self.environment.waiting_times)
            )
        )
        print(
            "The mean service time is: {:04.2f} seconds".format(
                np.mean(self.environment.service_times)
            )
        )
