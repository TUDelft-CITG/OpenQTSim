import openqtsim
import pandas as pd
import numpy as np
from collections import namedtuple
Task = namedtuple('Task','lam, mu, server, nr_arr')

def worker(task:Task):
    # create Arrival and Service processes and specify the number of servers
    A = openqtsim.ArrivalProcess("M", arr_rate=task.lam)
    srv_rate = task.mu/task.server
    S = openqtsim.ServiceProcess("M", srv_rate=srv_rate)
    c = task.server

    # create the queue object and use it to create a simulating object
    q = openqtsim.Queue(A, S, c)

    # create simulation object and run simulation
    sim = openqtsim.Simulation(q)
    sim.run(task.nr_arr)

    # retrieve the logs
    df1, df2 = sim.return_log()

    # determine waiting time as a factor of service time 
    factor = np.mean(df1["TCWQ"]) / np.mean(df1["ST"])

    return factor
    