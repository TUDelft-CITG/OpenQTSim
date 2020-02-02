import numpy as np
import openqtsim

"""
Testing the M/M/c/inf/inf/FIFO queue, in this case c = 3.
All answers are compared to the analytical solutions.
"""


def test_lookup_table():
    factor = openqtsim.lookup_tables.occupancy_to_waitingfactor(
        utilisation=.3,
        nr_of_servers_to_chk=1,
        poly_order=6, kendall='E2/E2/n')

    np.testing.assert_approx_equal(factor, 0.1310, significant=1)
