import simpy
import random
import pandas as pd
import numpy as np

from .queue import queue


class simulation:
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(self, queue, priority=False, seed=4):
        """
        Initialization
        """

        random.seed(seed)

        self.environment = simpy.Environment()
        self.environment.queue = queue
        
        self.environment.IAT = []
        self.environment.ST = []

        self.environment.waiting_times = []
        self.environment.service_times = []
        self.environment.system_times = []
        self.environment.arrivals = []

        self.environment.in_queue = 0
        self.environment.in_service = 0
        
        # c = customer
	# IAT = inter arrival time
	# AT = now + IAT
	# ST = service time
	# TSB = time service begins
	# TCWQ = time customer waits in the queue
	# TSE = time service ends
	# TCSS = time customer spends in the system
        # ITS = idle time of the server
        self.log = {
            "c": [], 
            "IAT": [], 
            "AT": [],
	    "ST": [],
	    "TSB": [],
	    "TCWQ": [],
	    "TSE": [],
	    "TCSS": [],
	    "ITS": []}
 
#        self.log = {"Time": [], "In queue": [], "In service": [], "In system": []}

        if priority == False:
            self.environment.servers = simpy.Resource(
                self.environment, capacity=queue.c
            )
        else:
            self.environment.servers = simpy.PriorityResource(
                self.environment, capacity=queue.c
            )

    def simulate(self, time):
        """
        Simulate the queue
        """

        self.environment.process(
            self.environment.queue.A.arrival(self.environment, self)
        )
        self.environment.process(self.log_entry())
        self.environment.run(until=time)

    def log_entry(self):
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

        while True:
            self.log["c"].append(self.environment.now + 1)
            
            self.log["IAT"].append(self.environment.IAT)
            
            if self.environment.now == 0:
               # time starts at 0, but the first customer does not have to arrive a t=0
               self.log["AT"].append(0 + self.environment.IAT)
            else:
               self.log["AT"].append(self.log["AT"][-1] + self.environment.IAT)
            
            self.log["ST"].append(self.environment.ST)
            
            if self.environment.now == 0:
               self.log["TSB"].append(0 + self.environment.IAT)
            else:
               self.log["TSB"].append(max([self.log["AT"][-1],self.log["TSE"][-1]]))
            
            self.log["TCWQ"].append(self.log["TSB"][-1] - self.log["AT"][-1])
            
            self.log["TSE"].append(self.log["TSB"][-1] + self.log["ST"][-1])
            
            self.log["TCSS"].append(self.log["TSE"][-1] - self.log["AT"][-1])
            
            self.log["ITS"].append(self.log["TSB"][-1] - self.log["AT"][-1])
 
            
            # self.log["In queue"].append(self.environment.in_queue)
            # self.log["In service"].append(self.environment.in_service)
            # self.log["In system"].append(
            #    self.environment.in_queue + self.environment.in_service
            #)

            yield self.environment.timeout(1)


        # while True:
        #    self.log["Time"].append(self.environment.now)
        #    self.log["In queue"].append(self.environment.in_queue)
        #    self.log["In service"].append(self.environment.in_service)
        #    self.log["In system"].append(
        #        self.environment.in_queue + self.environment.in_service
        #    )
        # 
        #    yield self.environment.timeout(1)

    def return_log(self, to_csv=False):
        """
        Return the log in the form of a pandas dataframe.
        
        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """

        dataframe = pd.DataFrame.from_dict(self.log)

        if to_csv == True:
            dataframe.to_csv("simulation_results.csv")

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
