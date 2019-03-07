from scipy import stats
import numpy as np
import pytest

import queueing

"""
Testing the M/M/1/inf/inf/FIFO queue.
All answers are compared to the analytical solutions.
"""


@pytest.fixture
def Q():
    A = queueing.arrival_process("M", stats.poisson(1 / 0.9))
    S = queueing.service_process("M", stats.expon(0))
    c = 1

    return queueing.queue(A, S, c)
    

def test_utilization(Q):
    """
    Mean interarrival rate = 1.11
    Thus lambda = 1.00 / 1.11 = 0.90

    Mean service time = 1.00
    Thus mu = 1.00 / 1.00 = 1.00

    Utilization, rho = lambda / mu = 0.90 / 1.00 = 0.90
    """

    np.testing.assert_almost_equal(Q.utilization, 0.9)


def test_mean_queue_length(Q):
    """
    For M/M/1 queue the mean queue length, Lq, has an analytical solution.
    The analytical solution is equal to the average arrival rate (lambda)
    multiplied with the average waiting time (Wq).

    Or the utilization squared diveded by 1 minus the utilization.
    The utilization was 0.9, thus the mean queue length should be 8.1
    """

    np.testing.assert_almost_equal(Q.mean_queue_length, (0.9 ** 2) / (1 - 0.9))


def test_mean_waiting_time(Q):
    """
    For M/M/1 queue the mean waiting time, Wq, has an analytical solution.
    The analytical solution is equal to the mean queue length (Ls) divided
    by the average arrival rate (lambda).

    Or the utilization squared diveded by 1 minus the utilization, divided by lambda.
    The utilization was 0.9, lambda was 0.9 thus the mean queue length should be 9.00
    """

    np.testing.assert_almost_equal(Q.mean_waiting_time, ((0.9 ** 2) / (1 - 0.9) / 0.9))


def test_simulation(Q):
    """
    The mean results should be very similar to the steady state of the queue.
    Therefore simulating for a sufficiently large period of time should result in the steady state solutions.
    """

    sim = queueing.simulation(Q)
    sim.simulate(2500000)

    # Assert similarities of arrival rate and service times between simulation and analytical solutions
    np.testing.assert_almost_equal(sim.environment.queue.A.arrival_rate, np.mean(sim.environment.arrivals), decimal = 3)
    np.testing.assert_almost_equal(sim.environment.queue.S.mean_service_time, np.mean(sim.environment.service_times), decimal = 3)

    # Assert similarities of waiting times and queue lengths between simulation and analytical solutions
    assert np.isclose(Q.mean_waiting_time, np.mean(sim.environment.waiting_times), rtol = 0.001, atol = 0.1)
    assert np.isclose(Q.mean_queue_length, np.mean(sim.log["In queue"]), rtol = 0.001, atol = 0.1)