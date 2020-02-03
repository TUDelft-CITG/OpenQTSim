import simpy
import random
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
            "c_id": [],  # c_id = customer id
            "IAT": [],  # IAT = inter arrival time
            "ST": [],  # ST = service time
            "AT": [],  # AT = now + IAT
            "TSB": [],  # TSB = time service begins
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
        self.log["TCWQ"].append(TSB - AT)
        self.log["TCSS"].append(TSE - AT)
        if len(self.log["c_id"]) == 1:
            self.log["ITS"].append(
                IAT
            )  # the server will start idle until the first arrival
        else:
            self.log["ITS"].append(
                max([AT - self.log["TSE"][-2], 0])
            )  # todo: I don't think this works with multiple servers
        self.log["QL"].append(
            QL
        )  # this is monitored by using the custom class MonitoredResource defined above

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

    def get_queue_info(self):
        """ Determine additional info on the queue.
        
        Based on the logs per customer, define the number of customers 
        in the queue and in the systems at any time.
        """

        assert (
            self.environment.now != self.environment.epoch
        ), "Simulation has not started yet."

        for time in self.env.now - self.environment.epoch:
            return 0

    def get_stats(self):
        # https://www.youtube.com/watch?v=nDXD8oVelo4
        # https: // www.youtube.com / watch?v = QppldN - t4pQ
        # https: // www.supositorio.com / rcalc / rcalclite.htm
        print(
            "Average IAT: {:.2f} [seconds]".format(
                np.sum(self.log["IAT"]) / (len(self.log["c_id"]) - 1)
            )
        )
        print(
            "Average ST: {:.2f} [seconds]".format(
                np.sum(self.log["ST"]) / (len(self.log["c_id"]))
            )
        )
        print("")
        print("Total number of customers: {:.2f}".format((len(self.log["c_id"]))))
        av_arr = 3600 / (np.sum(self.log["IAT"]) / ((len(self.log["c_id"]) - 1)))
        av_ser = 3600 / (np.sum(self.log["ST"]) / ((len(self.log["c_id"]) - 1)))
        print("Average nr arrivals: {:.2f} [# per hour]".format(av_arr))
        print("Average nr services: {:.2f} [# per hour]".format(av_ser))
        # print('Average nr people in the system: {:.2f}'.format(av_arr*(np.mean(self.log["TCSS"])/3600)))

        print("")
        print("Total waiting time: {:.2f} [seconds]".format(np.sum(self.log["TCWQ"])))
        print(
            "Average waiting time of all customers: {:.2f} [seconds]".format(
                np.sum(self.log["TCWQ"]) / (len(self.log["c_id"]))
            )
        )
        print(
            "Average waiting time of customers that waited: {:.2f} [seconds]".format(
                np.sum(self.log["TCWQ"]) / np.sum(np.array(self.log["TCWQ"]) != 0)
            )
        )

        print("")
        print(
            "Probability of idle server (nobody in the system): {:.4f}".format(
                np.sum(self.log["ITS"]) / self.log["TSE"][-1]
            )
        )
        print(
            "Probability that somebody is waiting: {:.4f}".format(
                np.sum(np.array(self.log["QL"]) != 0) / (len(self.log["c_id"]))
            )
        )
        print(
            "Probability that nobody is waiting: {:.4f}".format(
                np.sum(np.array(self.log["QL"]) == 0) / (len(self.log["c_id"]))
            )
        )
        print(
            "Probability that 1 person is waiting: {:.4f}".format(
                np.sum(np.array(self.log["QL"]) == 1) / (len(self.log["c_id"]))
            )
        )
        print(
            "Probability that 2 persons are waiting: {:.4f}".format(
                np.sum(np.array(self.log["QL"]) == 2) / (len(self.log["c_id"]))
            )
        )
        print(
            "Probability that 3 persons are waiting: {:.4f}".format(
                np.sum(np.array(self.log["QL"]) == 3) / (len(self.log["c_id"]))
            )
        )
        print(
            "Probability that 9 persons are waiting (10 in system): {:.4f}".format(
                np.sum(np.array(self.log["QL"]) == 9) / (len(self.log["c_id"]))
            )
        )
        print("")
        print("Total service time: {:.2f} [seconds]".format(np.sum(self.log["ST"])))
        print(
            "Average total time a customer spent in the system: {:.2f} [seconds]".format(
                np.sum(self.log["TCSS"]) / (len(self.log["c_id"]))
            )
        )
        print(
            "Average waiting time as a fraction of ST: {:.2f}".format(
                np.mean(np.array(self.log["TCWQ"])) / np.mean(np.array(self.log["ST"]))
            )
        )
        print("")
        print(
            "System utilisation: {:.4f}".format(
                (
                    (
                        (self.log["TSE"][-1] - np.sum(self.log["ITS"]))
                        / self.log["TSE"][-1]
                    )
                )
            )
        )
