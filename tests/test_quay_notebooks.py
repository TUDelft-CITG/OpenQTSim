from pathlib import Path

import matplotlib.pyplot as plt
import nbformat
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from openqtsim.visualizations import hover_time


@pytest.mark.parametrize("number,arrival,service", [(2, "D", "D"), (3, "D", "M"), (4, "M", "D"), (5, "M", "M")])
def test_quay_notebook_executes_from_info_only(monkeypatch, number, arrival, service):
    folder = Path(__file__).resolve().parents[1] / "notebooks"
    monkeypatch.chdir(folder)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    read_excel = pd.read_excel
    sheets = []

    def read_info(*args, **kwargs):
        sheets.append(kwargs.get("sheet_name"))
        assert kwargs.get("sheet_name") == "info"
        return read_excel(*args, **kwargs)

    monkeypatch.setattr(pd, "read_excel", read_info)
    title = f"{arrival} {service} 2 (max 200 m)"
    notebook = nbformat.read(folder / f"{number:04d} - {title}.ipynb", as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    try:
        for cell in notebook.cells:
            if cell.cell_type == "code":
                exec(compile(cell.source, str(folder / title), "exec"), namespace)
        assert sheets == ["info"]
        assert notebook.cells[0].source.startswith(f"# {title}\n")
        assert namespace["arrival_distribution"] == arrival
        assert namespace["service_distribution"] == service
        assert "inspect_object(Vessel, show_parameter_table=True)" in [cell.source for cell in notebook.cells]
        assert "inspect_object(Quay, show_parameter_table=True)" in [cell.source for cell in notebook.cells]
        quay = namespace["quay"]
        assert (quay.name, quay.nr_resources, quay.length) == ("Quay", 2, 200)
        assert namespace["q"].station is quay and namespace["q"].c == 2 and namespace["q"].quay_length == 200
        assert [vessel.name for vessel in namespace["vessels"]] == namespace["info"]["name"].tolist()
        arrivals = namespace["arrival_table"]
        services = namespace["service_table"]
        log = namespace["df"]
        assert len(arrivals) == len(services) == len(log) == 20
        np.testing.assert_allclose(arrivals.IAT.cumsum(), arrivals.AT)
        np.testing.assert_allclose(log.AT, arrivals.AT, atol=1e-5)
        assert namespace["sim"].c_s == namespace["sim"].c_q == 0
        assert set(log.status) <= {"served", "reneged"}
        for time in set(log.TSB.dropna()) | set(log.departure):
            active = log[(log.TSB <= time) & (log.TSE > time)]
            assert len(active) <= 2
            assert active.length.sum() <= 200
        reneged = log[log.status == "reneged"]
        np.testing.assert_allclose(reneged.departure - reneged.AT, reneged.maxwait, atol=1e-5)
        red = next(trace for trace in namespace["fig"].data if trace.name == "Reneged")
        assert red.marker.color == "red" and red.marker.symbol == "x"
        np.testing.assert_allclose(red.x, reneged.departure)
        assert hover_time(48) == "48 h (2 days)"
    finally:
        plt.close("all")


def test_mm1_notebook_uses_lean_server_station(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "notebooks"
    monkeypatch.chdir(folder)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    notebook = nbformat.read(folder / "0006 - M M 1 - 20 arrivals.ipynb", as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    try:
        for cell in notebook.cells:
            if cell.cell_type == "code":
                source = "\n".join(line for line in cell.source.splitlines() if not line.startswith("%%"))
                exec(compile(source, "M M 1 - 20 arrivals", "exec"), namespace)
        assert "inspect_object(Server, show_parameter_table=True)" in [cell.source for cell in notebook.cells]
        server = namespace["server"]
        assert (server.name, server.nr_resources) == ("Server", 1)
        q = namespace["q"]
        assert q.station is server and q.c == 1 and q.quay_length is None
        assert q.kendall_notation.startswith("M/M/1")
        log = namespace["df"]
        assert len(log) == 20 and set(log.status) == {"served"}
        assert namespace["sim"].c_s == namespace["sim"].c_q == 0
        assert len(namespace["fig"].data) > 0
    finally:
        plt.close("all")


def test_mm1_million_notebook_compares_with_analytical_solution(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "notebooks"
    monkeypatch.chdir(folder)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    notebook = nbformat.read(folder / "0007 - M M 1 - 1 million arrivals.ipynb", as_version=4)
    nbformat.validate(notebook)
    sources = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    assert any("nr_arr = 1_000_000" in source for source in sources)
    namespace = {}
    try:
        for source in sources:
            # a shorter run keeps the test fast; the notebook itself uses 1 million arrivals
            source = source.replace("nr_arr = 1_000_000", "nr_arr = 20_000")
            source = "\n".join(line for line in source.splitlines() if not line.startswith("%%"))
            exec(compile(source, "M M 1 - 1 million arrivals", "exec"), namespace)
        assert namespace["q"].station is namespace["server"] and namespace["q"].c == 1
        comparison = namespace["comparison"]
        assert list(comparison.index) == ["IAT", "ST", "Rho_server", "P_0", "P_1", "P_10", "L_s", "L_q", "W_s", "W_q"]
        np.testing.assert_allclose(comparison.loc["L_s", "analytical"], 8)
        np.testing.assert_allclose(comparison.loc["W_q", "analytical"], 8 / 9)
        np.testing.assert_allclose(comparison.loc["P_0", "simulated"], namespace["summary"]["P_0"], atol=1e-9)
        assert comparison.notna().all().all()
        assert len(namespace["first"]) == 20 and len(namespace["df"]) == 20_000
    finally:
        plt.close("all")


def test_dd1_notebook_reproduces_lecture_queueing_table(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "notebooks"
    monkeypatch.chdir(folder)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    notebook = nbformat.read(folder / "0001 - D D 1 example.ipynb", as_version=4)
    nbformat.validate(notebook)
    namespace = {}
    for cell in notebook.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, "D D 1 example", "exec"), namespace)
    assert namespace["q"].station is namespace["server"] and namespace["q"].c == 1
    assert list(namespace["table"]["TSE"]) == [23, 31, 35, 42, 46, 54, 67, 72]
    measures = namespace["measures"]
    np.testing.assert_allclose(measures.loc[["W_s", "W_q", "L_q", "L_s"], "average over arriving customers"],
                               [74 / 8, 21 / 8, 5 / 8, 13 / 8])
    np.testing.assert_allclose(measures.loc[["W_s", "W_q", "L_q", "L_s"], "time average (sim.get_stats)"],
                               [74 / 8, 21 / 8, 21 / 72, 74 / 72])
