import numpy as np
import pandas as pd
import pytest

import openqtsim


def make_simulation(iat, service_times, servers=1, assignments=None, index=None):
    arrivals = pd.DataFrame({"IAT": iat}, index=index)
    services = pd.DataFrame({"ST": service_times}, index=index)
    if assignments is not None:
        services["s_id"] = assignments
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services),
        servers,
    )
    return openqtsim.Simulation(queue)


@pytest.mark.parametrize("index", [None, [1, 2, 3], [7, 7, 4], ["a", "b", "c"]])
def test_customer_rows_are_paired_by_position(index):
    sim = make_simulation([0, 1, 1], [10, 20, 30], index=index)
    sim.run(3)
    customers, _ = sim.return_log()
    customers = customers.sort_values("c_id")
    np.testing.assert_array_equal(customers["AT"], [0, 1, 2])
    np.testing.assert_array_equal(customers["ST"], [10, 20, 30])
    np.testing.assert_array_equal(customers["TSB"], [0, 10, 30])
    np.testing.assert_array_equal(customers["TSE"], [10, 30, 60])
    np.testing.assert_array_equal(customers["TCWQ"], [0, 9, 28])
    assert sim.c_s == sim.c_q == 0


def test_unassigned_customers_use_available_servers():
    sim = make_simulation([0, 1, 1], [10, 2, 1], servers=2)
    sim.run(3)
    customers, _ = sim.return_log()
    customers = customers.sort_values("c_id")
    np.testing.assert_array_equal(customers["s_id"], [1, 2, 2])
    np.testing.assert_array_equal(customers["TSB"], [0, 1, 3])
    np.testing.assert_array_equal(customers["TSE"], [10, 3, 4])


@pytest.mark.parametrize(
    "assignments,expected_servers,expected_starts,expected_ends",
    [
        (None, [1, 2, 2, 2], [0, 0, 2, 3], [4, 2, 3, 6]),
        ([2, 2, 1, 1], [2, 2, 1, 1], [0, 4, 0, 1], [4, 6, 1, 4]),
    ],
)
def test_simultaneous_arrivals_with_independent_table_indices(
    assignments, expected_servers, expected_starts, expected_ends,
):
    arrivals = pd.DataFrame({"IAT": [0, 0, 0, 1]}, index=[10, 20, 30, 40])
    services = pd.DataFrame({"ST": [4, 2, 1, 3]}, index=["d", "c", "b", "a"])
    if assignments is not None:
        services["s_id"] = assignments
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services),
        c=2,
    )
    sim = openqtsim.Simulation(queue)
    sim.run(len(arrivals))
    customers, _ = sim.return_log()
    customers = customers.sort_values("c_id")

    assert len(customers) == len(arrivals)
    np.testing.assert_array_equal(customers["c_id"], [1, 2, 3, 4])
    np.testing.assert_array_equal(customers["AT"], [0, 0, 0, 1])
    np.testing.assert_array_equal(customers["ST"], [4, 2, 1, 3])
    np.testing.assert_array_equal(customers["s_id"], expected_servers)
    np.testing.assert_array_equal(customers["TSB"], expected_starts)
    np.testing.assert_array_equal(customers["TSE"], expected_ends)
    np.testing.assert_array_equal(
        customers["TCWQ"], np.array(expected_starts) - customers["AT"].to_numpy(),
    )
    assert sim.c_s == sim.c_q == 0


def test_assigned_customers_wait_for_their_server_without_blocking_others():
    sim = make_simulation(
        [0, 1, 1, 1], [10, 2, 3, 1], servers=2,
        assignments=[2, 2, 1, 2],
    )
    sim.run(4)
    customers, _ = sim.return_log()
    customers = customers.sort_values("c_id")
    np.testing.assert_array_equal(customers["s_id"], [2, 2, 1, 2])
    np.testing.assert_array_equal(customers["TSB"], [0, 10, 2, 12])
    np.testing.assert_array_equal(customers["TSE"], [10, 12, 5, 13])
    np.testing.assert_array_equal(customers["TCWQ"], [0, 9, 0, 9])
    assert sim.c_s == sim.c_q == 0


@pytest.mark.parametrize("assignment", [0, 3, 1.5, np.nan, "1"])
def test_invalid_assignment_fails_before_arrivals(assignment):
    sim = make_simulation([0], [1], servers=2, assignments=[assignment])
    with pytest.raises(ValueError, match="s_id"):
        sim.run(1)
    assert sim.customer_nr == 0


@pytest.mark.parametrize("process,column", [("A", "IAT"), ("S", "ST")])
def test_short_input_fails_before_arrivals(process, column):
    sim = make_simulation([0, 1], [2, 3])
    if process == "A":
        sim.queue.A.arr_rate = sim.queue.A.arr_rate.iloc[:1]
    else:
        sim.queue.S.srv_rate = sim.queue.S.srv_rate.iloc[:1]
    with pytest.raises(ValueError, match=column):
        sim.run(2)
    assert sim.customer_nr == 0


@pytest.mark.parametrize("process,column", [("A", "IAT"), ("S", "ST")])
def test_missing_column_fails_before_arrivals(process, column):
    sim = make_simulation([0, 1], [2, 3])
    if process == "A":
        sim.queue.A.arr_rate = sim.queue.A.arr_rate.drop(columns=column)
    else:
        sim.queue.S.srv_rate = sim.queue.S.srv_rate.drop(columns=column)
    with pytest.raises(ValueError, match=column):
        sim.run(2)
    assert sim.customer_nr == 0


def test_single_server_accepts_explicit_assignment():
    sim = make_simulation([0, 1], [3, 2], assignments=[1, 1])
    sim.run(2)
    customers, _ = sim.return_log()
    np.testing.assert_array_equal(customers["TSB"], [0, 3])


@pytest.mark.parametrize("deterministic_arrivals", [True, False])
def test_deterministic_and_stochastic_processes_can_be_combined(deterministic_arrivals):
    if deterministic_arrivals:
        arrival = openqtsim.ArrivalProcess("D", pd.DataFrame({"IAT": [0, 1, 1]}))
        service = openqtsim.ServiceProcess("M", 9)
    else:
        arrival = openqtsim.ArrivalProcess("M", 8)
        service = openqtsim.ServiceProcess("D", pd.DataFrame({"ST": [1, 2, 3]}))
    sim = openqtsim.Simulation(openqtsim.Queue(arrival, service, 2), arrival_seed=42, service_seed=43)
    sim.run(3)
    customers, _ = sim.return_log()
    assert len(customers) == 3
    assert (customers["TCWQ"] >= 0).all()
    if not deterministic_arrivals:
        np.testing.assert_array_equal(customers.sort_values("c_id")["ST"], [1, 2, 3])


@pytest.mark.parametrize(
    "arrival_names,service_names,expected",
    [
        (["Ship", "Ship", "Third"], None, ["Ship", "Ship", "Third"]),
        (None, ["First", "Second", "Third"], ["First", "Second", "Third"]),
        (["Arrival", None, " "], ["Service", "Fallback", "Last"], ["Arrival", "Fallback", "Last"]),
        ([None, np.nan, ""], None, [None, None, None]),
        (None, None, [None, None, None]),
    ],
)
def test_customer_names_follow_rows_even_when_completion_order_differs(
    arrival_names, service_names, expected,
):
    arrivals = pd.DataFrame({"IAT": [0, 1, 1]}, index=["c", "a", "b"])
    services = pd.DataFrame({"ST": [10, 2, 1]}, index=[8, 4, 6])
    if arrival_names is not None:
        arrivals["name"] = arrival_names
    if service_names is not None:
        services["name"] = service_names
    sim = openqtsim.Simulation(openqtsim.Queue(
        openqtsim.ArrivalProcess("D", arrivals),
        openqtsim.ServiceProcess("D", services),
        c=2,
    ))
    sim.run(3)
    customers, _ = sim.return_log()
    assert sim.log["c_id"][0] == 2
    assert customers.sort_values("c_id")["name"].tolist() == expected
