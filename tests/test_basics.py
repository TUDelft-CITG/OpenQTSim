import numpy as np
import openqtsim

"""
Testing the M/M/c/inf/inf/FIFO queue, in this case c = 3.
All answers are compared to the analytical solutions.
"""


def test_lookup_table():
    queue = openqtsim.Queue()

    utilisation = 0.9
    nr_of_servers = 1

    factor = queue.occupancy_to_waitingfactor(utilisation, nr_of_servers)
    answer = 8.998295524474928

    np.testing.assert_equal(factor, answer)
