import numpy as np
import openqtsim

"""
"""


def test_lookup_table():
    queue = openqtsim.Queue()

    utilisation = 0.9
    nr_of_servers = 1

    factor = queue.occupancy_to_waitingfactor(utilisation, nr_of_servers)
    answer = 8.998295524474928

    np.testing.assert_equal(factor, answer)
