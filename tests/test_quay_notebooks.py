from pathlib import Path

import matplotlib.pyplot as plt
import nbformat
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from openqtsim.visualizations import hover_time


@pytest.mark.parametrize("arrival,service", [("D", "D"), ("D", "M"), ("M", "D"), ("M", "M")])
def test_quay_notebook_executes_from_info_only(monkeypatch, arrival, service):
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
    notebook = nbformat.read(folder / f"OpenQTSim - {title}.ipynb", as_version=4)
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
