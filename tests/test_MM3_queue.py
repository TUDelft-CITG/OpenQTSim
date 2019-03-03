"""Tests for queueing package."""

import numpy as np
import queueing

from scipy import stats

def test_MM3_queue():
    A = queueing.arrival_process("M", stats.poisson(1))
    S = queueing.service_process("M", stats.expon(1))
    c = 3

    q = queueing.queue(A, S, c)
    sim = queueing.simulation(q)

    sim.simulate(500000)

    np.testing.assert_almost_equal(sim.environment.queue.A.arrival_rate, np.mean(sim.environment.arrivals), decimal = 3)
    np.testing.assert_almost_equal(sim.environment.queue.S.mean_service_time, np.mean(sim.environment.service_times), decimal = 3)