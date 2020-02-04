import numpy as np
import openqtsim

"""
"""


def test_lookup_table_1():
    queue = openqtsim.Queue()

    utilisation = 0.9
    nr_of_servers = 1

    factor = queue.occupancy_to_waitingfactor(utilisation, nr_of_servers)
    answer = 8.998295524474928

    np.testing.assert_equal(factor, answer)

def test_lookup_table_2():
    queue = openqtsim.Queue()

    factor = 0.0870
    nr_of_servers = 4

    factor = queue.waitingfactor_to_occupancy(factor, nr_of_servers)
    answer = 0.493062176851717

    np.testing.assert_equal(factor, answer)
