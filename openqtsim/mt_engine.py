import openqtsim
import numpy as np
from collections import namedtuple

Task = namedtuple('Task', 'A, S, c, nr_arr, lam, mu')


def worker(task:Task):
    # calculate the appropriate service rate per server
    srv_rate = task.mu/task.c

    # create Arrival and Service processes and specify the number of servers
    A = openqtsim.ArrivalProcess(task.A, arr_rate=task.lam)
    S = openqtsim.ServiceProcess(task.S, srv_rate=srv_rate)
    c = task.c

    # create the queue object
    q = openqtsim.Queue(A, S, c)

    # use the queue object to create a simulation object and run simulation with the specified number of arrivals
    sim = openqtsim.Simulation(q)
    sim.run(task.nr_arr)

    # retrieve the logs (df1: customer log, df2: system log)
    df1, df2 = sim.return_log()

    # use the customer log to determine the average waiting time as a factor of service time 
    factor = np.mean(df1["TCWQ"]) / np.mean(df1["ST"])

    return factor
