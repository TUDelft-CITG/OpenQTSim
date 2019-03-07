from scipy import stats
import numpy as np
import pytest

import queueing

"""
Testing the M/M/c/inf/inf/FIFO queue, in this case c = 3.
All answers are compared to the analytical solutions.
"""

@pytest.fixture
def Q():
    A = queueing.arrival_process("M", stats.poisson(1 / 0.9))
    S = queueing.service_process("M", stats.expon(0))
    c = 3

    return queueing.queue(A, S, c)


def test_utilization(Q):
    """
    Mean interarrival rate = 1.11
    Thus lambda = 1.00 / 1.11 = 0.90

    Mean service time = 1.00
    Thus mu = 1.00 / 1.00 = 1.00

    Utilization, rho = lambda / (c * mu) = 0.90 / 3.00 = 0.30
    """

    np.testing.assert_almost_equal(Q.utilization, 0.3)


def test_simulation(Q):
    """
    The mean results should be very similar to the steady state of the queue.
    Therefore simulating for a sufficiently large period of time should result in the steady state solutions.
    """

    sim = queueing.simulation(Q)
    sim.simulate(2500000)

    np.testing.assert_almost_equal(sim.environment.queue.A.arrival_rate, np.mean(sim.environment.arrivals), decimal = 3)
    np.testing.assert_almost_equal(sim.environment.queue.S.mean_service_time, np.mean(sim.environment.service_times), decimal = 3)
    np.testing.assert_almost_equal(Q.mean_waiting_time, np.mean(sim.environment.waiting_times), decimal = 1)
    np.testing.assert_almost_equal(Q.mean_queue_length, np.mean(sim.log["In Queue"]), decimal = 1)