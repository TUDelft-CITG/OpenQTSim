import numpy as np
import pandas as pd
import pytest

import openqtsim


@pytest.mark.parametrize("process", [openqtsim.ArrivalProcess, openqtsim.ServiceProcess])
@pytest.mark.parametrize("symbol", ["G", "", "E", "E0", "E-1", "E2.5", "E02", "m", None, 2])
def test_unsupported_distribution_is_rejected(process, symbol):
    with pytest.raises(ValueError, match="distribution"):
        process(symbol)


@pytest.mark.parametrize("process", [openqtsim.ArrivalProcess, openqtsim.ServiceProcess])
@pytest.mark.parametrize("rate", [0, -1, np.nan, np.inf, -np.inf, True, "8", None, [8], 1j])
def test_invalid_rate_is_rejected(process, rate):
    with pytest.raises(ValueError, match="finite positive"):
        process("M", rate)


@pytest.mark.parametrize("field", ["K", "N"])
@pytest.mark.parametrize("value", [1, 0, -1, -np.inf, np.nan, None, "inf", [np.inf], True])
def test_unsupported_capacity_and_population_are_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        openqtsim.Queue(**{field: value})


@pytest.mark.parametrize("discipline", ["LIFO", "priority", "fifo", None, 1])
def test_unsupported_discipline_is_rejected(discipline):
    with pytest.raises(ValueError, match="FIFO"):
        openqtsim.Queue(D=discipline)


@pytest.mark.parametrize("count", [0, -1, 2.5, np.nan, np.inf, True, "2", None])
def test_invalid_server_and_arrival_counts_are_rejected(count):
    with pytest.raises(ValueError, match="c must"):
        openqtsim.Queue(c=count)
    with pytest.raises(ValueError, match="max_arr"):
        openqtsim.Simulation(openqtsim.Queue(), max_arr=count)
    sim = openqtsim.Simulation(openqtsim.Queue())
    with pytest.raises(ValueError, match="max_arr"):
        sim.run(count)
    assert sim.customer_nr == 0


@pytest.mark.parametrize("priority", [True, 1, "False", None])
def test_priority_is_rejected(priority):
    with pytest.raises(ValueError, match="priority"):
        openqtsim.Simulation(openqtsim.Queue(), priority=priority)


@pytest.mark.parametrize("seed", [-1, 2**32, 1.5, True, "42", [42]])
def test_invalid_seed_is_rejected(seed):
    with pytest.raises(ValueError, match="seed"):
        openqtsim.Simulation(openqtsim.Queue(), seed=seed)


@pytest.mark.parametrize("seed", [None, 0, 2**32 - 1])
def test_valid_seed_boundaries_are_accepted(seed):
    sim = openqtsim.Simulation(openqtsim.Queue(), seed=seed)
    sim.run(2)
    assert len(sim.return_log()[0]) == 2


def test_wrong_queue_and_process_types_are_rejected():
    with pytest.raises(ValueError, match="queue must"):
        openqtsim.Simulation(None)
    with pytest.raises(ValueError, match="A and S"):
        openqtsim.Queue(A=None)
    with pytest.raises(ValueError, match="A and S"):
        openqtsim.Queue(S=None)


@pytest.mark.parametrize("assignment", [True, False, np.inf])
def test_invalid_assignment_values_are_rejected(assignment):
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", pd.DataFrame({"IAT": [0]})),
        openqtsim.ServiceProcess("D", pd.DataFrame({"ST": [1], "s_id": [assignment]})),
    )
    sim = openqtsim.Simulation(queue)
    with pytest.raises(ValueError, match="s_id"):
        sim.run(1)
    assert sim.customer_nr == 0


@pytest.mark.parametrize("column", ["IAT", "ST"])
def test_mutated_deterministic_duration_fails_before_arrivals(column):
    arrivals = pd.DataFrame({"IAT": [0., 1.]})
    services = pd.DataFrame({"ST": [1., 2.]})
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services),
    )
    sim = openqtsim.Simulation(queue)
    table = arrivals if column == "IAT" else services
    table.loc[1, column] = -1
    with pytest.raises(ValueError, match=column):
        sim.run(2)
    assert sim.customer_nr == 0


@pytest.mark.parametrize(
    "process,column",
    [(openqtsim.ArrivalProcess, "IAT"), (openqtsim.ServiceProcess, "ST")],
)
@pytest.mark.parametrize("duration", [-1, np.inf, np.nan, None, "1", True, 1j])
def test_invalid_deterministic_duration_is_rejected(process, column, duration):
    with pytest.raises(ValueError, match=column):
        process("D", pd.DataFrame({column: [duration]}))


@pytest.mark.parametrize(
    "process,column",
    [(openqtsim.ArrivalProcess, "IAT"), (openqtsim.ServiceProcess, "ST")],
)
def test_invalid_deterministic_schema_is_rejected(process, column):
    for table in [1, [], pd.DataFrame({"wrong": [1]})]:
        with pytest.raises(ValueError, match=column):
            process("D", table)
    with pytest.raises(ValueError, match="unique column"):
        process("D", pd.DataFrame([[1, 2]], columns=[column, column]))


@pytest.mark.parametrize("field,value", [("K", 1), ("N", 1), ("D", "LIFO"), ("c", 0)])
def test_mutated_queue_is_validated_again_before_running(field, value):
    sim = openqtsim.Simulation(openqtsim.Queue())
    setattr(sim.queue, field, value)
    with pytest.raises(ValueError):
        sim.run(2)
    assert sim.customer_nr == 0


def test_mutated_process_is_validated_before_running():
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("M", 8), openqtsim.ServiceProcess("M", 9),
    )
    sim = openqtsim.Simulation(queue)
    queue.S.symbol = "G"
    with pytest.raises(ValueError, match="distribution"):
        sim.run(2)
    assert sim.customer_nr == 0


@pytest.mark.parametrize("symbol", ["M", "E1", "E2", "E4"])
def test_valid_stochastic_configuration_completes(symbol):
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess(symbol, np.float64(8)),
        openqtsim.ServiceProcess(symbol, 9),
        c=np.int64(2),
    )
    sim = openqtsim.Simulation(queue, seed=np.int64(42))
    sim.run(np.int64(20))
    assert len(sim.return_log()[0]) == 20


def test_zero_durations_and_integral_float_assignments_remain_valid():
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", pd.DataFrame({"IAT": [0, 0]})),
        openqtsim.ServiceProcess("D", pd.DataFrame({"ST": [0, 0], "s_id": [1., 1.]})),
    )
    sim = openqtsim.Simulation(queue)
    sim.run(2)
    assert len(sim.return_log()[0]) == 2


def test_overloaded_finite_run_is_allowed():
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("M", 20), openqtsim.ServiceProcess("M", 1),
    )
    sim = openqtsim.Simulation(queue, seed=42)
    sim.run(20)
    assert len(sim.return_log()[0]) == 20


@pytest.mark.parametrize("field,value", [("lam", 0), ("mu", np.inf), ("nr_arr", 2.5), ("seed", -1)])
def test_fast_solver_validates_configuration(field, value):
    parameters = dict(lam=8, mu=9, nr_arr=2, seed=42)
    parameters[field] = value
    with pytest.raises(ValueError, match=field):
        openqtsim.MM1(**parameters)


@pytest.mark.parametrize("iat,st", [([1], [1, 2]), ([1, 2], [-1, 2]), ([[1, 2]], [1, 2])])
def test_fast_solver_validates_customer_inputs(iat, st):
    solver = openqtsim.MM1(8, 9, 2)
    with pytest.raises(ValueError):
        solver.calculate(iat, st)


def test_fast_solver_valid_inputs_remain_supported():
    solver = openqtsim.MM1(8, 9, 3, seed=42)
    iat, st = solver.get_IAT_and_ST()
    result = solver.calculate(iat, st)
    assert len(result) == 3
    assert (result["TCWQ"] >= 0).all()


@pytest.mark.parametrize("method", ["occupancy_to_waitingfactor", "waitingfactor_to_occupancy"])
def test_lookup_rejects_unsupported_distribution_pair(method):
    queue = openqtsim.Queue(openqtsim.ArrivalProcess("E3"), openqtsim.ServiceProcess())
    with pytest.raises(ValueError, match="lookup only supports"):
        getattr(queue, method)()


def test_m_erlang_lookup_is_reachable():
    queue = openqtsim.Queue(openqtsim.ArrivalProcess("M"), openqtsim.ServiceProcess("E2"))
    assert np.isfinite(queue.occupancy_to_waitingfactor(.5, 1))
    assert np.isfinite(queue.waitingfactor_to_occupancy(.75, 1))
