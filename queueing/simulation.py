import simpy
import random
import pandas as pd
import numpy as np

from .queue import queue

class simulation():
    """
    A discrete event simulation that simulates the queue.
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """
    
    def __init__(self, queue, priority = False, seed = 4):
        """
        Initialization
        """
        
        random.seed(seed)
        
        self.environment = simpy.Environment()
        self.environment.queue = queue
        
        self.environment.waiting_times = []
        self.environment.service_times = []
        self.environment.system_times = []
        self.environment.arrivals = []
        
        self.environment.in_queue = 0
        self.environment.in_service = 0
        self.log = {"Time": [],
                    "In queue": [],
                    "In service": [],
                    "In system": []}
        
        if priority == False:
            self.environment.servers = simpy.Resource(self.environment, capacity = queue.c)
        else:
            self.environment.servers = simpy.PriorityResource(self.environment, capacity = queue.c)
    
    def simulate(self, time):
        """
        Simulate the queue
        """
        
        self.environment.process(self.environment.queue.A.arrival(self.environment, self))
        self.environment.run(until = time)
        
    def log_entry(self, time, in_queue, in_service):
        """
        Update the log based on the current timestamp.
        """
        
        self.log["Time"].append(time)
        self.log["In queue"].append(in_queue)
        self.log["In service"].append(in_service)
        self.log["In system"].append(in_queue + in_service)
    
    def return_log(self, to_csv = False):
        """
        Return the log in the form of a pandas dataframe.
        
        If to_csv is True, a .csv file will be saved with the name "simulation_results.csv"
        """
        
        dataframe = pd.DataFrame.from_dict(self.log)
        
        if to_csv == True:
            dataframe.to_csv("simulation_results.csv")
        
        return dataframe
    
    def get_stats(self):
        print("The arrival rate is:      {:04.2f} seconds".format(np.mean(self.environment.arrivals)))
        print("The mean waiting time is: {:04.2f} seconds".format(np.mean(self.environment.waiting_times)))
        print("The mean service time is: {:04.2f} seconds".format(np.mean(self.environment.service_times)))