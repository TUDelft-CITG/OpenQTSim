from pathlib import Path

import nbformat
import numpy as np
import plotly.graph_objects as go
import pytest


FOLDER = Path(__file__).resolve().parents[1] / "notebooks"


def execute_notebook(monkeypatch, name, **overrides):
    monkeypatch.chdir(FOLDER)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    notebook = nbformat.read(FOLDER / name, as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    for cell in notebook.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, name, "exec"), namespace)
            if cell.id == "parameters":
                defaults = {"2002": (100_000, 8), "2004": (30_000, 4), "2005": (30_000, 4)}
                expected = defaults.get(name[:4], (50_000, 4))
                assert (namespace["nr_arr"], namespace["nr_replications"]) == expected
                namespace.update(nr_arr=5_000, nr_replications=3)
                namespace.update(overrides)
    return namespace


def test_dedicated_and_shared_notebook_keeps_traffic_and_capacity_equal(monkeypatch):
    ns = execute_notebook(monkeypatch, "2001 - Dedicated versus shared berths.ipynb")
    dedicated, pooled = ns["dedicated_tasks"], ns["pooled_tasks"]
    n, runs = ns["nr_berths"], ns["nr_replications"]
    assert len(dedicated) == n * runs and len(pooled) == runs
    for task in dedicated:
        assert task.c == 1
        assert task.lam * n == pytest.approx(ns["arrival_rate"])
        assert task.mu == ns["mu_server"]
    for task in pooled:
        assert task.c == n
        assert task.lam == ns["arrival_rate"]
        assert task.mu / n == ns["mu_server"]
    assert sum(task.nr_arr for task in dedicated) == sum(task.nr_arr for task in pooled)
    seeds = [seed for task in dedicated + pooled for seed in (task.arrival_seed, task.service_seed)]
    assert len(set(seeds)) == len(seeds)
    comparison = ns["comparison"]
    np.testing.assert_allclose(comparison["analytical W_q (hours)"], [4, 16 / 9])
    np.testing.assert_allclose(
        comparison["standard error (hours)"], ns["replications"].std(ddof=1) / np.sqrt(runs)
    )
    assert comparison.loc["Shared", "simulated W_q (hours)"] < comparison.loc["Dedicated", "simulated W_q (hours)"]
    assert ns["reduction"] == pytest.approx(5 / 9)
    assert len(ns["fig"].data) == 2


def test_occupancy_notebook_preserves_service_rate_per_berth(monkeypatch):
    ns = execute_notebook(monkeypatch, "2002 - Berth occupancy and waiting time.ipynb")
    assert len(ns["tasks"]) == len(ns["servers"]) * len(ns["utilisations"]) * ns["nr_replications"]
    for task in ns["tasks"]:
        assert task.mu / task.c == ns["mu_server"]
        assert any(np.isclose(task.lam / task.mu, rho) for rho in ns["utilisations"])
    points = ns["points"]
    assert (points["count"] == ns["nr_replications"]).all()
    assert np.isfinite(points.to_numpy()).all()
    assert (points["standard error"] >= 0).all()
    for n in ns["servers"]:
        assert points.xs(n)["analytical"].is_monotonic_increasing
    assert points.loc[(1, 0.5), "analytical"] == pytest.approx(1)
    assert points.loc[(1, 0.9), "analytical"] == pytest.approx(9)
    fixed = ns["fixed_traffic"]
    np.testing.assert_allclose(fixed["occupancy"] * fixed.index * ns["mu_server"], ns["fixed_arrival_rate"])
    assert fixed["analytical W_q (hours)"].is_monotonic_decreasing
    assert len(ns["fig"].data) == 2 * len(ns["servers"])


def test_cost_notebook_excludes_unstable_candidates_and_scales_annual_costs(monkeypatch):
    ns = execute_notebook(monkeypatch, "2003 - Berth planning by cost.ipynb")
    planning = ns["planning"]
    assert ns["stable_servers"] == [3, 4, 5, 6, 7, 8]
    assert np.isinf(planning.loc[[1, 2], "analytical total cost (EUR/year)"]).all()
    assert planning.loc[[1, 2], "simulated W_q (hours)"].isna().all()
    assert len(ns["tasks"]) == len(ns["stable_servers"]) * ns["nr_replications"]
    for task in ns["tasks"]:
        assert task.c in ns["stable_servers"]
        assert task.lam == pytest.approx(ns["arrival_rate"])
        assert task.mu / task.c == ns["mu_server"]
    stable = ns["stable"]
    factor = ns["arrival_rate"] * ns["hours_per_year"] * ns["waiting_cost_per_vessel_hour"]
    np.testing.assert_allclose(stable["analytical waiting cost (EUR/year)"], factor * stable["analytical W_q (hours)"])
    np.testing.assert_allclose(stable["simulated waiting cost (EUR/year)"], factor * stable["simulated W_q (hours)"])
    np.testing.assert_allclose(stable["total cost standard error (EUR/year)"], factor * stable["W_q standard error (hours)"])
    np.testing.assert_allclose(
        stable["simulated total cost (EUR/year)"],
        stable.index * ns["annual_berth_cost"] + stable["simulated waiting cost (EUR/year)"],
    )
    assert ns["analytical_optimum"] == 5
    assert ns["simulated_optimum"] in ns["stable_servers"]
    assert np.isfinite(stable.to_numpy(dtype=float)).all()
    assert len(ns["fig"].data) == 4


def test_cost_notebook_reports_when_no_candidate_is_stable(monkeypatch):
    with pytest.raises(ValueError, match="No candidate is stable"):
        execute_notebook(monkeypatch, "2003 - Berth planning by cost.ipynb", arrival_rate=20)


def test_container_terminal_notebook_reconstructs_book_and_separates_extension(monkeypatch):
    ns = execute_notebook(monkeypatch, "2004 - Container terminal design and costs.ipynb")
    assert ns["fleet"]["annual calls"].tolist() == [563, 228, 152]
    assert ns["annual_calls"] == 943
    assert ns["peak_workload_hours"] == 49_200
    assert ns["average_length"] == pytest.approx(339.57158, abs=1e-5)
    book = ns["book_design"]
    assert (book["berths"], book["cranes"]) == (4, 14)
    assert book["book occupancy"] == pytest.approx((49_200 / 14 + 943 * 2) / 8592)
    assert book["table waiting factor"] == pytest.approx(0.0868, abs=5e-5)
    previous = ns["book_path"].iloc[-2]
    assert (previous["berths"], previous["cranes"]) == (4, 13)
    assert previous["table waiting factor"] > ns["max_waiting_factor"]
    assert not ns["book_path"].iloc[:-1]["meets target"].any()
    designs = ns["designs"]
    ref = designs.loc[(4, 14)]
    assert ref["quay length (m)"] == pytest.approx(1600.1, abs=0.1)
    assert ref["occupancy"] == pytest.approx(
        ns["peak_workload_hours"] / (14 * ns["operating_hours"])
        + ns["peak_factor"] * ns["annual_calls"] * ns["overhead"] / (4 * ns["operating_hours"])
    )
    assert ref["occupancy"] == pytest.approx(0.47487, abs=1e-5)
    assert ref["occupancy"] != pytest.approx(book["book occupancy"])
    assert len(ns["tasks"]) == int(designs["stable"].sum()) * ns["nr_replications"]
    seeds = [seed for task in ns["tasks"] for seed in (task.arrival_seed, task.service_seed)]
    assert len(seeds) == len(set(seeds))
    for task, (n, k) in zip(ns["tasks"], ns["task_designs"]):
        assert task.A == task.S == "E2"
        assert task.lam == pytest.approx(ns["peak_arrival_rate"])
        assert task.c == n
        assert task.mu / n == pytest.approx(1 / designs.loc[(n, k), "mean service (hours)"])
    stable = designs[designs["stable"]]
    np.testing.assert_allclose(stable["waiting factor"], stable["mean wait (hours)"] / stable["mean service (hours)"])
    np.testing.assert_allclose(
        stable["factor upper bound"],
        stable["waiting factor"] + ns["critical_value"] * stable["factor standard error"],
    )
    assert (ns["qualified"]["factor upper bound"] <= ns["max_waiting_factor"]).all()
    assert ns["selected"] == ns["qualified"]["total cost (EUR/year)"].idxmin()
    np.testing.assert_allclose(stable["total cost (EUR/year)"], stable[ns["cost_columns"]].sum(axis=1))
    factor = ns["annual_calls"] * ns["vessel_cost_per_hour"]
    np.testing.assert_allclose(stable["vessel waiting cost (EUR/year)"], factor * stable["mean wait (hours)"])
    np.testing.assert_allclose(stable["vessel service cost (EUR/year)"], factor * stable["mean service (hours)"])
    np.testing.assert_allclose(stable["cost standard error (EUR/year)"], factor * stable["wait standard error (hours)"])
    assert np.isinf(designs.loc[~designs["stable"], "total cost (EUR/year)"]).all()
    assert designs.loc[~designs["stable"], "mean wait (hours)"].isna().all()
    assert ns["capital_recovery_factor"](0, 20) == 0.05
    assert ns["capital_recovery_factor"](0.05, 25) == pytest.approx(0.07095246)
    assert len(ns["cost_fig"].data) == 5
    assert len(ns["service_fig"].data) == len(ns["berth_candidates"]) + 1


def test_opentesim_lifecycle_notebook_reconciles_assets_and_discounted_flows(monkeypatch):
    pytest.importorskip("opentesim")
    ns = execute_notebook(
        monkeypatch, "2005 - Container terminal lifecycle costs with OpenTESim.ipynb",
        tariff_per_teu=25.0,
    )
    assert ns["annual_calls"] == 943
    assert ns["terminal_throughput"] == 1_611_300
    assert ns["cargo"]["stacks"].tolist() == [15, 18, 3, 5]
    assert ns["operational_start"] == 2026 and ns["end_year"] == 2072
    assert len(ns["tasks"]) == len(ns["candidates"]) * ns["nr_replications"]
    for task, (n, k) in zip(ns["tasks"], ns["task_designs"]):
        assert task.lam == pytest.approx(ns["peak_arrival_rate"])
        assert task.mu / n == pytest.approx(1 / ns["designs"].loc[(n, k), "service hours"])
    for key, engine in ns["engine_cashflows"].items():
        n, k = key
        frame = ns["cashflows"][key]
        inventory = ns["inventories"][key]
        assert len(engine) == ns["project_years"]
        assert engine.index.tolist() == list(range(2023, 2073))
        np.testing.assert_allclose(frame["discount factor"], 1.07 ** (frame.index.to_numpy() - 2023))
        np.testing.assert_allclose(
            engine["net_cashflow"], engine["total_capex"] + engine["total_opex"] + engine["total_revenue"]
        )
        np.testing.assert_allclose(engine["npv"], engine["net_cashflow"] / frame["discount factor"])
        assert frame.loc[:2025, "handling revenue"].eq(0).all()
        assert frame.loc[2026:, "handling revenue"].eq(25 * ns["throughput_teu"]).all()
        assert frame.loc[:2025, "vessel time cost"].eq(0).all()
        assert frame.loc[2026:, "vessel time cost"].lt(0).all()
        np.testing.assert_allclose(
            frame["operator discounted"],
            engine["npv"] + frame["handling revenue"] / frame["discount factor"],
        )
        np.testing.assert_allclose(frame["extended net"], frame["operator net"] + frame["vessel time cost"])
        np.testing.assert_allclose(frame["operator cumulative NPV"], frame["operator discounted"].cumsum())
        np.testing.assert_allclose(frame["extended cumulative NPV"], frame["extended discounted"].cumsum())
        quay_capex = inventory.loc["Quay", "initial CAPEX USD"]
        np.testing.assert_allclose(engine.loc[[2023, 2024], "capex_construction"], [-0.2 * quay_capex, -0.4 * quay_capex])
        assert engine.loc[2025, "capex_construction"] == pytest.approx(
            -(inventory["initial CAPEX USD"].sum() - 0.6 * quay_capex)
        )
        np.testing.assert_allclose(engine.loc[[2053, 2054, 2055], "capex_construction"], -quay_capex * np.array([0.2, 0.4, 0.4]))
        assert engine.loc[2065, "capex_construction"] == -k * ns["crane_template"]["capex_unit"]
        assert engine.loc[2026, "total_opex"] == pytest.approx(
            -(0.035 * quay_capex + 0.04 * (inventory["initial CAPEX USD"].sum() - quay_capex))
        )
        assert engine.loc[2072, "capex_divestment"] > 0
        assert engine.loc[2072, "opex_decommissioning"] < 0
        assert inventory.loc["STS fleet", "quantity"] == k
        assert inventory.loc["Tractor-trailer fleet", "quantity"] == 5 * k
        design = ns["designs"].loc[key]
        pv_teu = (ns["throughput_teu"] / frame.loc[2026:, "discount factor"]).sum()
        assert design["break-even tariff USD/TEU"] * pv_teu == pytest.approx(design["PV terminal cost USD"])
        assert design["operator NPV USD"] == pytest.approx(25 * pv_teu - design["PV terminal cost USD"])
        assert design["extended NPV USD"] == pytest.approx(design["operator NPV USD"] - design["PV vessel time USD"])
    qualified = ns["qualified"]
    assert (qualified["factor upper bound"] <= ns["max_waiting_factor"]).all()
    assert ns["operator_choice"] == qualified["operator NPV USD"].idxmax()
    assert ns["economic_choice"] == qualified["extended NPV USD"].idxmax()
    detailed_traces = ns["cashflow_fig"].data[:-4]
    for axis in [ns["cashflow_fig"].layout.yaxis, ns["cashflow_fig"].layout.yaxis2]:
        lower, upper = axis.range
        assert lower < 0 < upper
        assert -lower / (upper - lower) == pytest.approx(0.5)
    bars = np.array([trace.y for trace in ns["cashflow_fig"].data if trace.type == "bar"])
    assert np.maximum(bars, 0).sum(axis=0).max() < ns["cashflow_fig"].layout.yaxis.range[1]
    assert np.minimum(bars, 0).sum(axis=0).min() > ns["cashflow_fig"].layout.yaxis.range[0]
    assert ns["selected_cashflow"][["operator cumulative NPV", "extended cumulative NPV"]].abs().to_numpy().max() / 1e6 < ns["cashflow_fig"].layout.yaxis2.range[1]
    assert len(detailed_traces) > 20
    np.testing.assert_allclose(
        np.array([trace.y for trace in detailed_traces]).sum(axis=0) * 1e6,
        ns["selected_engine"]["net_cashflow"], atol=1e-6,
    )
    for path, ledger in ns["generation_ledgers"].items():
        generation = " / ".join(path[1:]) if len(path) > 1 else "Initial generation"
        for column in ns["component_columns"]:
            if ledger[column].ne(0).any():
                trace = next(t for t in detailed_traces if t.name == f"{path[0]} / {generation} / {column}")
                np.testing.assert_allclose(np.array(trace.y) * 1e6, ledger[column], atol=1e-6)
    assert len(ns["comparison_fig"].data) == 3
    selected_inventory = ns["inventories"][ns["selected"]]
    assert ns["investment_values"][0] == pytest.approx(selected_inventory["initial CAPEX USD"].sum())
    for prefix in ["investment", "lifecycle"]:
        trace = ns[f"{prefix}_sunburst"].data[0]
        assert trace.type == "sunburst"
        assert trace.branchvalues == "total"
        assert len(trace.ids) == len(set(trace.ids))
        assert np.isfinite(trace.values).all()
        assert (np.array(trace.values) >= 0).all()
        values = dict(zip(trace.ids, trace.values))
        for parent in set(trace.parents) - {""}:
            assert values[parent] == pytest.approx(
                sum(value for value, p in zip(trace.values, trace.parents) if p == parent)
            )
    assert ns["lifecycle_values"][0] == pytest.approx(ns["gross_lifecycle_cost"] + ns["terminal_credit_pv"])
    assert ns["residual_credit_pv"] > 0
    assert ns["gross_lifecycle_cost"] - ns["residual_credit_pv"] == pytest.approx(
        ns["designs"].loc[ns["selected"], "PV terminal cost USD"]
    )
    assert {path[0] for path in ns["generation_ledgers"]} == set(selected_inventory.index)
    assert any(len(path) > 1 for path in ns["generation_ledgers"])
    assert any("opex_decommissioning" not in leaf.df.columns
               for group in ns["projects"][ns["selected"]].children
               for leaf in getattr(group, "children", []))
    assert "capex_divestment" in ns["lifecycle_labels"]
    assert "2053" in ns["lifecycle_labels"]
    assert ns["lifecycle_labels"].count("Cost outflows") == 1
    assert ns["lifecycle_labels"].count("Credits") == 1
    assert ns["lifecycle_signed"][0] == pytest.approx(-ns["designs"].loc[ns["selected"], "PV terminal cost USD"])
    leaf_indices = [i for i, node in enumerate(ns["lifecycle_ids"]) if node not in ns["lifecycle_parents"]]
    assert len(leaf_indices) == len(ns["posted_detail"])
    np.testing.assert_allclose(
        sorted(ns["lifecycle_signed"][i] for i in leaf_indices),
        sorted(ns["posted_detail"]["PV USD"]), atol=1e-6,
    )


def test_opentesim_notebook_rejects_unstable_shortlist(monkeypatch):
    pytest.importorskip("opentesim")
    with pytest.raises(ValueError, match="No stable design"):
        execute_notebook(
            monkeypatch, "2005 - Container terminal lifecycle costs with OpenTESim.ipynb",
            candidates=[(1, 1)],
        )
