import openqtsim
import pandas as pd
import numpy as np


def get_waiting_time_service_time_table(utilisations, servers, nr_arr):
    """
    Generate a waiting time over service time ratio table
    """

    lams = utilisations * 10
    mu = 10

    df = pd.DataFrame(index=utilisations, columns=servers)

    for index, lam in enumerate(lams):
        for server in servers:
            # Create Arrival and Service processes and specify the number of servers
            A = openqtsim.ArrivalProcess("M", arr_rate=lam)
            S = openqtsim.ServiceProcess("M", srv_rate=mu)
            c = server

            # Create the queue object and use it to create a simulating object
            q = openqtsim.Queue(A, S, c)
            # q.kendall_notation

            sim = openqtsim.Simulation(q)
            sim.run(nr_arr)

            df2 = sim.return_log()

            factor = np.mean(df2["TCWQ"]) / np.mean(df2["ST"])
            df.iloc[index, server - 1] = factor

    print(sim.queue.kendall_notation)

    return df, sim
