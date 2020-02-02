import simpy
import random
import pandas as pd
import numpy as np
import datetime
import time


class simulation:
    """ A discrete event simulation that simulates the queue.
    
    - queue is a queue based on the queue class
    - seed is a random seed to have retraceable simulations
    """

    def __init__(
        self,
        queue,
        simulation_start=datetime.datetime.now(),
        type="probabilistic",
        priority=False,
        seed=4,
    ):
        """
        Initialization
        """
        self.simulation_start = simulation_start
        self.environment = simpy.Environment(
            initial_time=time.mktime(self.simulation_start.timetuple())
        )
        self.environment.epoch = time.mktime(self.simulation_start.timetuple())

        self.queue = queue
        self.customer_nr = 0

        np.random.seed(seed)

        self.log = {
            "c": [],  # c = customer
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
            "TCWQ": [],  # TCWQ = time customer waits in the queue
            "TSE": [],  # TSE = time service ends
            "TCSS": [],  # TCSS = time customer spends in the system
            "ITS": [],  # ITS = idle time of the server
        }

        # set nr of servers
        if priority == False:
            self.environment.servers = simpy.Resource(
                self.environment, capacity=queue.c
            )
        else:
            self.environment.servers = simpy.PriorityResource(
                self.environment, capacity=queue.c
            )

        # arrival_process = self.queue.A
        self.environment.process(self.queue.A.arrival(self.environment, self))

    def run(self, duration=None, max_arrivals=None):
        """ Run a simulation of the queueuing system """

        assert (
            time != None or max_arrivals != None
        ), "Specify the end of the simulation by maximizing either the time or the number of customers."

        self.max_arrivals = max_arrivals

        if duration:
            self.time = duration + self.environment.epoch
            self.environment.run(until=self.time)
        else:
            self.environment.run()

        print(
            "Simulation finished in {}".format(
                datetime.timedelta(
                    seconds=int(self.environment.now - self.environment.epoch)
                )
            )
        )

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

    def return_log(self, filename=None):
        """Return the log in the form of a pandas dataframe.
        
        If a filename is specified, the results will be saved in the working folder as a .csv file.
        """

        dataframe = pd.DataFrame.from_dict(self.log).set_index("c")

        if filename:
            if ".csv" not in filename:
                filename += ".csv"

            dataframe.to_csv(filename)

        return dataframe

    def get_stats(self):
        """ Return the statistics of the simulation """

        print(
            "The arrival rate is:      {:04.2f} seconds".format(
                np.mean(self.log["IAT"])
            )
        )
        print(
            "The mean waiting time is: {:04.2f} seconds".format(
                np.mean(self.log["TCWQ"])
            )
        )
        print(
            "The mean service time is: {:04.2f} seconds".format(np.mean(self.log["ST"]))
        )
