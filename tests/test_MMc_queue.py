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

    # Assert similarities of arrival rate and service times between simulation and analytical solutions
    np.testing.assert_almost_equal(sim.environment.queue.A.arrival_rate, np.mean(sim.environment.arrivals), decimal = 3)
    np.testing.assert_almost_equal(sim.environment.queue.S.mean_service_time, np.mean(sim.environment.service_times), decimal = 3)

    # Assert similarities of waiting times and queue lengths between simulation and analytical solutions
    assert np.isclose(Q.mean_waiting_time, np.mean(sim.environment.waiting_times), rtol = 0.001, atol = 0.1)
    assert np.isclose(Q.mean_queue_length, np.mean(sim.log["In queue"]), rtol = 0.001, atol = 0.1)

def test_analytical_solutions():
    """
    With values from https://www.win.tue.nl/~iadan/queueing.pdf
    Page 45, table 5.1
    
    The utilization is constant at 0.90
    """
    
    customers = [1, 2, 5, 10, 20]
    delay_probability = [0.90, 0.85, 0.76, 0.67, 0.55]
    mean_waiting_time = [9.00, 4.26, 1.53, 0.67, 0.28]

    for i, c in enumerate(customers):

        # Arrival process varies dependent on number of customers
        A = queueing.arrival_process("M", stats.poisson(1 / (c * 0.9)))
        
        # Mean service time is 1 unit of time
        S = queueing.service_process("M", stats.expon(0))

        # Create queue
        q = queueing.queue(A, S, c)

        # Check results
        assert np.isclose(0.9, q.utilization, rtol = 0.1, atol = 0.1)
        assert np.isclose(delay_probability[i], q.delay_probability, rtol = 0.1, atol = 0.1)
        assert np.isclose(mean_waiting_time[i], q.mean_waiting_time, rtol = 0.1, atol = 0.1)