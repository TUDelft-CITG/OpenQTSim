import numpy as np
import pandas as pd
import pytest

import openqtsim


def simulate(iat, st, servers=1, assignments=None):
    services = pd.DataFrame({"ST": st})
    if assignments is not None:
        services["s_id"] = assignments
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("D", pd.DataFrame({"IAT": iat})),
        openqtsim.ServiceProcess("D", services),
        servers,
    )
    sim = openqtsim.Simulation(queue)
    sim.run(len(iat))
    return sim


def assert_state_integrals(sim, summary):
    customers, states = sim.return_log()
    times = states["t"].to_numpy()
    assert (np.diff(times) >= 0).all()
    assert times[-1] == summary["observation_end"]
    for column, statistic in [("c_s", "L_s"), ("c_q", "L_q")]:
        area = np.sum(np.diff(times) * states[column].to_numpy()[:-1])
        assert area / times[-1] == pytest.approx(summary[statistic])
    assert states.iloc[-1]["c_s"] == states.iloc[-1]["c_q"] == 0
    rate = len(customers) / summary["observation_duration"]
    assert summary["L_s"] == pytest.approx(rate * summary["W_s"])
    assert summary["L_q"] == pytest.approx(rate * summary["W_q"])


def test_single_server_statistics_include_initial_idle_and_drain(capsys):
    sim = simulate([2, 1], [4, 2])
    summary = sim.get_stats()
    expected = {
        "observation_start": 0, "observation_end": 8, "observation_duration": 8,
        "customers": 2, "waiting_factor": .5,
        "Rho_system": .75, "Rho_server": .75, "P_0": .25,
        "L_s": 9 / 8, "L_q": 3 / 8,
        "W_s": 4.5, "W_q": 1.5, "IAT": 1.5, "ST": 3,
    }
    assert summary == pytest.approx(expected)
    output = capsys.readouterr().out
    assert "Observation horizon: 0 to 8.0000 hours" in output
    assert "Rho_server: server utilisation: 0.7500" in output
    assert_state_integrals(sim, summary)


def test_multiserver_horizon_is_last_completion_not_last_arrival():
    sim = simulate([2, 1], [100, 1], servers=3)
    customers, _ = sim.return_log()
    assert customers["TSE"].iloc[-1] == 4
    summary = sim.get_stats()
    assert summary["observation_end"] == 102
    assert summary["Rho_system"] == pytest.approx(100 / 102)
    assert summary["Rho_server"] == pytest.approx(101 / (3 * 102))
    assert summary["P_0"] == pytest.approx(2 / 102)
    assert summary["L_s"] == pytest.approx(101 / 102)
    assert summary["L_q"] == 0
    assert_state_integrals(sim, summary)


def test_disjoint_and_overlapping_busy_periods():
    sim = simulate([1, 0, 9], [4, 2, 2], servers=2)
    summary = sim.get_stats()
    assert summary["observation_end"] == 12
    assert summary["Rho_system"] == pytest.approx(6 / 12)
    assert summary["Rho_server"] == pytest.approx(8 / 24)
    assert summary["P_0"] == pytest.approx(6 / 12)
    assert_state_integrals(sim, summary)


@pytest.mark.parametrize(
    "iat,st,assignments",
    [
        ([0, 0, 0, 1], [4, 2, 1, 3], None),
        ([0, 1, 1, 1], [10, 2, 3, 1], [2, 2, 1, 2]),
        ([1, 0, 0], [0, 2, 0], None),
    ],
)
def test_state_log_integrals_match_customer_intervals(iat, st, assignments):
    sim = simulate(iat, st, servers=2, assignments=assignments)
    summary = sim.get_stats()
    assert_state_integrals(sim, summary)
    for key in ["Rho_system", "Rho_server", "P_0"]:
        assert 0 <= summary[key] <= 1


def test_one_customer_interarrival_mean_has_no_division_by_zero():
    summary = simulate([2], [3]).get_stats()
    assert summary["IAT"] == 2
    assert summary["ST"] == 3
    assert summary["observation_end"] == 5


def test_zero_mean_service_has_explicit_undefined_waiting_factor(capsys):
    sim = simulate([1, 1], [0, 0])
    summary = sim.get_stats()
    assert summary["waiting_factor"] is None
    assert summary["P_0"] == 1
    assert summary["Rho_server"] == summary["Rho_system"] == 0
    assert "undefined (mean service time is zero)" in capsys.readouterr().out
    assert_state_integrals(sim, summary)


def test_zero_horizon_is_rejected():
    sim = simulate([0], [0])
    with pytest.raises(ValueError, match="positive finite observation horizon"):
        sim.get_stats()


def test_statistics_before_run_are_rejected():
    sim = openqtsim.Simulation(openqtsim.Queue())
    with pytest.raises(ValueError, match="completed customer"):
        sim.get_stats()


def test_incomplete_simulation_statistics_are_rejected():
    sim = openqtsim.Simulation(openqtsim.Queue(
        openqtsim.ArrivalProcess("D", pd.DataFrame({"IAT": [1]})),
        openqtsim.ServiceProcess("D", pd.DataFrame({"ST": [10]})),
    ), max_arr=1)
    sim.env.run(until=sim.env.now + 2)
    with pytest.raises(ValueError, match="all arrived customers"):
        sim.get_stats()


def test_fast_solver_and_simulation_statistics_agree():
    iat, st = [2, 1, 5], [4, 2, 1]
    expected = simulate(iat, st).get_stats()
    solver = openqtsim.MM1(8, 9, len(iat))
    customers = solver.calculate(iat, st)
    # The horizon must not depend on table order or recorded pre-service idle times.
    customers = customers.iloc[::-1].copy()
    customers["ITS"] = 999
    actual = solver.get_stats(customers)
    assert actual == pytest.approx(expected)


def test_fast_solver_rejects_zero_horizon():
    solver = openqtsim.MM1(8, 9, 1)
    with pytest.raises(ValueError, match="positive finite observation horizon"):
        solver.get_stats(solver.calculate([0], [0]))


@pytest.mark.parametrize("servers", [1, 3])
def test_stochastic_statistics_match_time_integrated_event_log(servers):
    queue = openqtsim.Queue(
        openqtsim.ArrivalProcess("M", 8), openqtsim.ServiceProcess("M", 9), servers,
    )
    sim = openqtsim.Simulation(queue, arrival_seed=42, service_seed=43)
    sim.run(1000)
    summary = sim.get_stats()
    assert_state_integrals(sim, summary)
    _, states = sim.return_log()
    durations = np.diff(states["t"].to_numpy())
    busy = (states["c_s"] - states["c_q"]).to_numpy()[:-1]
    horizon = summary["observation_duration"]
    assert summary["Rho_system"] == pytest.approx(np.sum(durations * (busy > 0)) / horizon)
    assert summary["Rho_server"] == pytest.approx(np.sum(durations * busy) / (servers * horizon))
    assert summary["P_0"] == pytest.approx(
        np.sum(durations * (states["c_s"].to_numpy()[:-1] == 0)) / horizon,
    )


def test_system_plot_uses_steps_without_averaging_simultaneous_events():
    sim = simulate([1, 0, 1], [4, 2, 1], servers=2)
    _, states = sim.return_log()
    figure = sim.plot_system_state()
    assert len(figure.data) == 2
    for trace, column in zip(figure.data, ["c_s", "c_q"]):
        assert trace.line.shape == "hv" and trace.showlegend is not False
        np.testing.assert_array_equal(trace.x, states["t"])
        np.testing.assert_array_equal(trace.y, states[column])


def test_system_plot_reduces_large_logs_but_keeps_peaks():
    from openqtsim.visualizations import plot_system_state

    rng = np.random.default_rng(1)
    states = pd.DataFrame({"t": np.arange(50_000.0), "c_s": rng.integers(0, 50, 50_000)})
    states.loc[31_234, "c_s"] = 999
    states["c_q"] = np.maximum(states["c_s"] - 1, 0)
    figure = plot_system_state(states, max_points=1_000)
    for trace, column in zip(figure.data, ["c_s", "c_q"]):
        assert len(trace.x) <= 1_100 and "reduced" in trace.name
        assert trace.x[0] == 0 and trace.x[-1] == 49_999
        assert max(trace.y) == states[column].max() and min(trace.y) == states[column].min()
        np.testing.assert_array_equal(trace.y, states[column].to_numpy()[np.asarray(trace.x, dtype=int)])


def test_iat_st_plot_has_mean_lines_to_top_and_legend():
    sim = simulate([1, 2, 3, 2], [0.5, 1, 1.5, 1], servers=1)
    df_cust, _ = sim.return_log()
    figure = sim.plot_IAT_ST()
    bars = [trace for trace in figure.data if trace.type == "bar"]
    means = [trace for trace in figure.data if trace.type == "scatter"]
    assert len(bars) == len(means) == 2
    for bar, mean, column, axis in zip(bars, means, ["IAT", "ST"], ["yaxis", "yaxis2"]):
        assert sum(bar.y) == df_cust[column].notna().sum()
        assert mean.x[0] == mean.x[1] == pytest.approx(df_cust[column].mean())
        assert mean.y[0] == 0 and mean.y[1] == figure.layout[axis].range[1]
        assert mean.line.color == "black" and "Mean" in mean.name
    assert figure.layout.showlegend is not False
