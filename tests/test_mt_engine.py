import math
from pathlib import Path

import nbformat
import numpy as np
import plotly.graph_objects as go
import pytest

from openqtsim.mt_engine import (
    Task, create_tasks, mmc_waiting_time_factor, run_tasks, statistics_worker, waiting_time_table, worker,
)


def test_task_keeps_positional_backward_compatibility():
    task = Task("M", "M", 1, 100, 5, 10)
    assert task.replication == 0 and task.arrival_seed is None and task.service_seed is None


def test_create_tasks_gives_reproducible_independent_seeds():
    tasks = create_tasks("M", "M", [1, 2], [0.5, 0.8], 100, mu=10, nr_replications=3, seed=1)
    assert len(tasks) == 12
    assert tasks == create_tasks("M", "M", [1, 2], [0.5, 0.8], 100, mu=10, nr_replications=3, seed=1)
    seeds = [s for task in tasks for s in (task.arrival_seed, task.service_seed)]
    assert len(set(seeds)) == len(seeds)
    assert {(task.lam, task.c) for task in tasks} == {(5.0, 1), (5.0, 2), (8.0, 1), (8.0, 2)}


def test_seeded_worker_is_reproducible():
    task = create_tasks("M", "M", [2], [0.6], 500, seed=3)[0]
    assert worker(task) == worker(task)


def test_mmc_waiting_time_factor_matches_known_values():
    for rho in (0.1, 0.5, 0.9):
        assert math.isclose(mmc_waiting_time_factor(1, rho), rho / (1 - rho))
    assert math.isclose(mmc_waiting_time_factor(2, 0.5), 1 / 3)
    assert mmc_waiting_time_factor(1, 1.0) == math.inf


def test_waiting_time_table_averages_replications():
    tasks = create_tasks("M", "M", [1, 2], [0.5], 10, nr_replications=2, seed=0)
    table = waiting_time_table(tasks, [1.0, 3.0, 10.0, 20.0])
    assert list(table.index) == [0.5] and list(table.columns) == [1, 2]
    assert table.loc[0.5, 1] == 2.0 and table.loc[0.5, 2] == 15.0


def test_run_tasks_with_dask_matches_serial_run():
    distributed = pytest.importorskip("dask.distributed")
    tasks = create_tasks("M", "E2", [1, 2], [0.5], 300, nr_replications=2, seed=5)
    # identical unseeded tasks must not be deduplicated by dask
    unseeded = [Task("M", "M", 1, 300, 5, 10)] * 2
    with distributed.Client(processes=False, n_workers=2, threads_per_worker=1, dashboard_address=":0") as client:
        assert run_tasks(tasks, client) == run_tasks(tasks)
        first, second = run_tasks(unseeded, client)
    assert first != second


def test_statistics_worker_returns_task_and_simulation_statistics():
    task = create_tasks("M", "M", [2], [0.5], 2_000, mu=10, seed=4)[0]
    summary = statistics_worker(task)
    assert summary["c"] == 2 and summary["customers"] == 2_000
    np.testing.assert_allclose(summary["waiting_factor"], worker(task), rtol=1e-6)
    assert run_tasks([task], func=statistics_worker) == [summary]


def _execute_notebook(monkeypatch, name, replacements):
    pytest.importorskip("dask.distributed")
    folder = Path(__file__).resolve().parents[1] / "notebooks"
    monkeypatch.chdir(folder)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    notebook = nbformat.read(folder / name, as_version=4)
    nbformat.validate(notebook)
    sources = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    replacements = {
        **replacements,
        "n_workers = os.cpu_count()": "n_workers = 2",
        "processes=True": "processes=False, dashboard_address=':0'",
    }
    for old in replacements:
        assert any(old in source for source in sources), old
    namespace = {"display": lambda *args, **kwargs: None}
    for source in sources:
        for old, new in replacements.items():
            source = source.replace(old, new)
        source = "\n".join(line for line in source.splitlines() if not line.startswith("%%"))
        exec(compile(source, name, "exec"), namespace)
    assert namespace["client"].status == "closed"
    return namespace


def test_mm1_dask_notebook_executes(monkeypatch):
    namespace = _execute_notebook(
        monkeypatch, "1001 - M M 1 using Dask.ipynb",
        {"nr_arr = 100_000": "nr_arr = 500", "nr_replications = 24": "nr_replications = 3"},
    )
    comparison = namespace["comparison"]
    assert len(namespace["results"]) == 3 and comparison.notna().all().all()
    np.testing.assert_allclose(comparison.loc["W_q", "analytical"], 8 / 9)
    np.testing.assert_allclose(comparison.loc["waiting_factor", "analytical"], 8)


@pytest.mark.parametrize("number,A,S,reference_value", [
    (1002, "M", "M", 0.6687),     # PIANC (2014) M/M/n table, n = 10 at 90 %
    (1003, "M", "E2", 0.65),      # Groenveld (2001) M/E2/n table, n = 8 at 90 %
    (1004, "E2", "E2", 0.4000),   # Groenveld (2001) E2/E2/n table, n = 8 at 90 %
])
def test_queueing_table_notebooks_execute(monkeypatch, number, A, S, reference_value):
    name = f"{number} - {A} {S} n - creating a queueing table.ipynb"
    namespace = _execute_notebook(
        monkeypatch, name,
        {"customers_per_cell = 1_000_000": "customers_per_cell = 600", "nr_arr = 100_000": "nr_arr = 300"},
    )
    assert (namespace["A"], namespace["S"]) == (A, S)
    table, reference = namespace["table"], namespace["reference"]
    assert len(namespace["tasks"]) == 9 * 10 * 2
    assert table.shape == (9, 10) and table.notna().all().all()
    n = 10 if number == 1002 else 8
    np.testing.assert_allclose(reference.loc[0.9, n], reference_value, atol=1e-4)
    assert namespace["difference"].shape == table.shape
    assert list(namespace["pianc_layout"](table).index[[0, -1]]) == ["10%", "90%"]
