"""Validate the introductory chapters and their executable event example."""

from pathlib import Path
import re
from urllib.parse import unquote

import nbformat
import pytest


FOLDER = Path(__file__).resolve().parents[1] / "notebooks"


def test_introduction_explains_and_executes_event_logic(monkeypatch):
    monkeypatch.setattr("IPython.display.display", lambda *args, **kwargs: None)
    namespace = {}
    for filename, title in [
        ("0001 - Queueing theory.ipynb", "Queueing theory"),
        ("0002 - Simulation.ipynb", "Simulation"),
    ]:
        notebook = nbformat.read(FOLDER / filename, as_version=4)
        nbformat.validate(notebook)
        assert notebook.cells[0].source.startswith(f"# {title}\n")
        for cell in notebook.cells:
            if cell.cell_type == "code":
                exec(compile(cell.source, filename, "exec"), namespace)
            else:
                for link in re.findall(r"\]\(([^)]+\.ipynb)\)", cell.source):
                    assert (FOLDER / unquote(link)).is_file()
    table = namespace["event_table"]
    assert table["waiting"].tolist() == [0, 1, 0]
    assert table["service start"].tolist() == [0, 2, 4]
    assert table["service end"].tolist() == [2, 4, 5]
    assert table["waiting"].mean() == pytest.approx(1 / 3)


def test_numbered_chapters_and_queue_titles_are_consistent():
    notebooks = sorted(FOLDER.glob("[0-9][0-9][0-9][0-9] - *.ipynb"))
    numbers = [int(path.name[:4]) for path in notebooks]
    assert numbers == [1, 2, *range(1001, 1009), *range(2001, 2005), *range(3001, 3006)]
    expected = [
        "D/D/1 - basics of queueing", "D/D/2 (max 200 m)", "D/M/2 (max 200 m)",
        "M/D/2 (max 200 m)", "M/M/2 (max 200 m)", "M/M/1 - 20 arrivals",
        "M/M/1 - 1 million arrivals", "E2/E2/1 - 1 million arrivals",
        "M/M/1 - using Dask", "M/M/n - queueing table",
        "M/E2/n - queueing table", "E2/E2/n - queueing table",
    ]
    for path, title in zip(notebooks[2:14], expected):
        notebook = nbformat.read(path, as_version=4)
        assert notebook.cells[0].source.splitlines()[0] == f"# {title}"
