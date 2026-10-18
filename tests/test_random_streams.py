import numpy as np
import pytest

import openqtsim


def queue(arrival="M", service="M", servers=1):
    return openqtsim.Queue(
        openqtsim.ArrivalProcess(arrival, 8),
        openqtsim.ServiceProcess(service, 9),
        servers,
    )


def run(arrival_seed=42, service_seed=43, arrival="M", service="M", servers=1):
    sim = openqtsim.Simulation(
        queue(arrival, service, servers),
        arrival_seed=arrival_seed, service_seed=service_seed,
    )
    sim.run(100)
    return sim.return_log()[0].sort_values("c_id")


def test_reproducible_separate_seeds():
    first, second = run(), run()
    np.testing.assert_array_equal(first["IAT"], second["IAT"])
    np.testing.assert_array_equal(first["ST"], second["ST"])
    np.testing.assert_array_equal(first["TSB"], second["TSB"])


def test_changing_service_seed_preserves_arrivals():
    first, second = run(), run(service_seed=44)
    np.testing.assert_array_equal(first["IAT"], second["IAT"])
    assert not np.array_equal(first["ST"], second["ST"])


def test_changing_arrival_seed_preserves_service_draws():
    first, second = run(), run(arrival_seed=44)
    np.testing.assert_array_equal(first["ST"], second["ST"])
    assert not np.array_equal(first["IAT"], second["IAT"])


@pytest.mark.parametrize("service,servers", [("M", 3), ("E2", 1), ("E4", 3)])
def test_service_configuration_does_not_change_arrival_draws(service, servers):
    np.testing.assert_array_equal(run()["IAT"], run(service=service, servers=servers)["IAT"])


@pytest.mark.parametrize("arrival", ["E2", "E4"])
def test_arrival_distribution_does_not_change_service_draws(arrival):
    np.testing.assert_array_equal(run()["ST"], run(arrival=arrival)["ST"])


@pytest.mark.parametrize("seed", [0, 42, np.int64(42), 2**32 - 1])
@pytest.mark.parametrize("solver", ["simulation", "mm1"])
def test_equal_explicit_seeds_are_rejected(seed, solver):
    with pytest.raises(ValueError, match="arrival_seed and service_seed must be different"):
        if solver == "simulation":
            openqtsim.Simulation(queue(), arrival_seed=seed, service_seed=seed)
        else:
            openqtsim.MM1(8, 9, 100, arrival_seed=seed, service_seed=seed)


@pytest.mark.parametrize("arrival_seed,service_seed", [(None, None), (42, None), (None, 42), (42, 43)])
def test_unspecified_or_different_seeds_are_accepted(arrival_seed, service_seed):
    sim = openqtsim.Simulation(
        queue(), arrival_seed=arrival_seed, service_seed=service_seed,
    )
    sim.run(2)
    assert len(sim.return_log()[0]) == 2
    solver = openqtsim.MM1(8, 9, 2, arrival_seed=arrival_seed, service_seed=service_seed)
    iat, st = solver.get_IAT_and_ST()
    assert len(iat) == len(st) == 2


def test_global_random_state_is_untouched_and_cannot_interfere():
    original = np.random.get_state()
    try:
        np.random.seed(123)
        expected = np.random.random(10)
        np.random.seed(123)
        first = run()
        np.testing.assert_array_equal(np.random.random(10), expected)
        np.random.random(500)
        sim = openqtsim.Simulation(queue(), arrival_seed=42, service_seed=43)
        np.random.random(500)
        sim.run(100)
        second = sim.return_log()[0].sort_values("c_id")
        np.testing.assert_array_equal(first["ST"], second["ST"])
        np.testing.assert_array_equal(first["IAT"], second["IAT"])
    finally:
        np.random.set_state(original)


def test_interleaved_simulations_sharing_queue_are_isolated():
    shared = queue()
    first = openqtsim.Simulation(shared, arrival_seed=42, service_seed=43)
    first.env.run(until=first.env.now + .5)
    other = openqtsim.Simulation(shared, arrival_seed=12, service_seed=13)
    other.run(100)
    first.run(100)
    result = first.return_log()[0].sort_values("c_id")
    reference = run()
    np.testing.assert_array_equal(result["IAT"], reference["IAT"])
    np.testing.assert_array_equal(result["ST"], reference["ST"])
    assert first.queue.A is not shared.A
    assert first.queue.S is not other.queue.S


def test_fast_solver_streams_are_independently_reproducible():
    def draw(a, s):
        return openqtsim.MM1(8, 9, 100, arrival_seed=a, service_seed=s).get_IAT_and_ST()
    iat, st = draw(42, 43)
    other_iat, other_st = draw(42, 44)
    np.testing.assert_array_equal(iat, other_iat)
    assert not np.array_equal(st, other_st)
    other_iat, other_st = draw(44, 43)
    np.testing.assert_array_equal(st, other_st)
    assert not np.array_equal(iat, other_iat)


def test_old_seed_api_is_rejected():
    with pytest.raises(TypeError, match="seed"):
        openqtsim.Simulation(queue(), seed=42)
    with pytest.raises(TypeError, match="seed"):
        openqtsim.MM1(8, 9, 100, seed=42)
    with pytest.raises(TypeError):
        openqtsim.MM1(8, 9, 100, 42)
