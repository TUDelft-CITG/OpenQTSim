import numpy as np
import pandas as pd
import pytest

import openqtsim


def make_simulation(iat, st, lengths, c=2, capacity=200, assignments=None):
    arrivals = pd.DataFrame({"IAT": iat})
    services = pd.DataFrame({"ST": st})
    if lengths is not None:
        arrivals["length"] = lengths
    if assignments is not None:
        services["s_id"] = assignments
    return openqtsim.Simulation(openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services), c, quay_length=capacity,
    ))


def run_and_check(sim, count):
    sim.run(count)
    log, states = sim.return_log()
    log = log.sort_values("c_id")
    assert len(log) == count
    assert sim.c_s == sim.c_q == 0
    assert sim.quay_occupied == 0
    for time in sorted(set(log["TSB"]) | set(log["TSE"])):
        active = log[(log["TSB"] <= time) & (log["TSE"] > time)]
        assert len(active) <= sim.queue.c
        assert active["length"].sum() <= sim.queue.quay_length + 1e-10
    durations = np.diff(states["t"])
    assert np.sum(durations * states["c_q"].to_numpy()[:-1]) == pytest.approx(log["TCWQ"].sum())
    return log


def test_length_can_block_vessel_despite_available_slot():
    sim = make_simulation([0, 1], [5, 2], [160, 80])
    log = run_and_check(sim, 2)
    np.testing.assert_array_equal(log["TSB"], [0, 5])
    np.testing.assert_array_equal(log["TCWQ"], [0, 4])


def test_two_vessels_can_fill_quay_exactly():
    log = run_and_check(make_simulation([0, 0, 1], [5, 2, 1], [120, 80, 80]), 3)
    np.testing.assert_array_equal(log["TSB"], [0, 0, 2])


def test_server_count_limits_admission_even_with_spare_length():
    log = run_and_check(make_simulation([0, 0, 0], [5, 2, 1], [20, 20, 20]), 3)
    np.testing.assert_array_equal(log["TSB"], [0, 0, 2])


def test_fifo_prevents_shorter_vessel_bypassing_waiter():
    log = run_and_check(make_simulation([0, 1, 1], [5, 3, 1], [120, 100, 50]), 3)
    np.testing.assert_array_equal(log["TSB"], [0, 5, 5])
    np.testing.assert_array_equal(log["TCWQ"], [0, 4, 3])


def test_assignments_and_quay_capacity_are_both_respected():
    log = run_and_check(make_simulation(
        [0, 1, 1], [5, 2, 1], [100, 50, 50], assignments=[2, 2, 1],
    ), 3)
    np.testing.assert_array_equal(log["s_id"], [2, 2, 1])
    np.testing.assert_array_equal(log["TSB"], [0, 5, 5])


@pytest.mark.parametrize("capacity", [0, -1, np.nan, np.inf, True, "200"])
def test_invalid_quay_capacity(capacity):
    with pytest.raises(ValueError, match="quay_length"):
        openqtsim.Queue(quay_length=capacity)


@pytest.mark.parametrize("length", [0, -1, 201, np.nan, np.inf, True, "80"])
def test_invalid_or_oversized_vessel_fails_before_arrivals(length):
    sim = make_simulation([0], [1], [length])
    with pytest.raises(ValueError, match="[Ll]ength"):
        sim.run(1)
    assert sim.customer_nr == 0


def test_missing_length_fails_before_arrivals():
    sim = make_simulation([0], [1], None)
    with pytest.raises(ValueError, match="length"):
        sim.run(1)
    assert sim.customer_nr == 0


def test_service_table_can_supply_lengths_with_stochastic_arrivals():
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("M", 8),
        openqtsim.ServiceProcess("D", pd.DataFrame({"ST": [2, 2], "length": [160, 80]})),
        c=2, quay_length=200,
    )
    sim = openqtsim.Simulation(queue, arrival_seed=42, service_seed=43)
    log = run_and_check(sim, 2)
    assert log.iloc[1]["TSB"] >= log.iloc[0]["TSE"]


def test_fractional_lengths_and_zero_service_release_capacity():
    sim = make_simulation([0, 0, 0, 1], [1, 0, 1, 1], [.1, .2, .2, .3], capacity=.3)
    run_and_check(sim, 4)


def test_example_first_delay_is_united_on_day_18():
    sim = make_simulation(
        [2, 0, 3, 4, 0, 3, 4, 2, 1, 4, 0, 1],
        [3, 5, 2, 3, 6, 7, 3, 5, 6, 3, 2, 4],
        [80, 80, 100, 80, 90, 100, 80, 80, 90, 80, 100, 160],
    )
    log = run_and_check(sim, 12)
    np.testing.assert_array_equal(log["TSB"], [2, 2, 5, 9, 9, 12, 16, 19, 19, 24, 25, 27])
    first_waiter = log[log["TCWQ"] > 0].iloc[0]
    assert first_waiter["c_id"] == 8
    assert first_waiter["AT"] == 18
    assert first_waiter["TCWQ"] == 1


def test_without_quay_capacity_existing_scheduling_is_unchanged():
    sim = make_simulation([0, 1], [5, 2], [160, 80], capacity=None)
    sim.run(2)
    log, _ = sim.return_log()
    np.testing.assert_array_equal(log["TSB"], [0, 1])
