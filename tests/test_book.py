"""Checks for preparing a static notebook book without running simulations."""

from pathlib import Path
import runpy
import shutil

import nbformat
import pytest


yaml = pytest.importorskip("yaml")
pytest.importorskip("jupyter_book")
ROOT = Path(__file__).resolve().parents[1]
prepare_book = runpy.run_path(str(ROOT / "book" / "build.py"))["prepare_book"]


@pytest.fixture
def book_root(tmp_path):
    """Create a small repository with the real book configuration."""
    (tmp_path / "book").mkdir()
    (tmp_path / "notebooks").mkdir()
    for name in ["_config.yml", "intro.md"]:
        shutil.copy2(ROOT / "book" / name, tmp_path / "book" / name)
    shutil.copy2(ROOT / "logo-OpenQTSim.png", tmp_path / "logo-OpenQTSim.png")
    return tmp_path


def write_notebook(root, name):
    """Write a notebook whose code must never be executed by the book builder."""
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            "[Source](../../OpenTESim/notebooks/example.ipynb)"
        ),
        nbformat.v4.new_code_cell(
            "raise RuntimeError('The book must not execute simulations')",
            outputs=[nbformat.v4.new_output("display_data", data={
                "application/vnd.plotly.v1+json": {
                    "data": [{"type": "sunburst", "labels": ["Terminal", "Quay"],
                              "parents": ["", "Terminal"], "values": [10, 10],
                              "branchvalues": "total"}],
                    "layout": {},
                },
            })],
        ),
    ])
    path = root / "notebooks" / name
    nbformat.write(notebook, path)
    return path


def test_book_preserves_outputs_and_generates_grouped_toc(book_root):
    paths = [write_notebook(book_root, name) for name in [
        "2005 - Costs.ipynb", "0002 - Shared quay.ipynb", "1001 - Dask.ipynb",
        "Scratch.ipynb",
    ]]
    originals = {path: path.read_bytes() for path in paths}
    (book_root / "notebooks" / "input.xlsx").write_bytes(b"test spreadsheet")
    source = prepare_book(book_root)
    toc = yaml.safe_load((source / "_toc.yml").read_text())
    chapters = [chapter["file"] for part in toc["parts"] for chapter in part["chapters"]]
    assert chapters == [
        "notebooks/0002 - Shared quay", "notebooks/1001 - Dask", "notebooks/2005 - Costs",
    ]
    assert all("title" not in chapter for part in toc["parts"] for chapter in part["chapters"])
    assert not (source / "notebooks" / "Scratch.ipynb").exists()
    assert (source / "notebooks" / "input.xlsx").read_bytes() == b"test spreadsheet"
    assert (source / "_static" / "plotly.min.js").stat().st_size > 1_000_000
    assert yaml.safe_load((source / "_config.yml").read_text())["execute"]["execute_notebooks"] == "off"
    copied = nbformat.read(source / "notebooks" / paths[0].name, as_version=4)
    assert "https://github.com/TUDelft-CITG/OpenTESim/blob/master/" in copied.cells[0].source
    assert copied.cells[1].source.startswith("raise RuntimeError")
    html = copied.cells[1].outputs[0].data["text/html"]
    assert "Plotly.newPlot" in html and "sunburst" in html
    assert "cdn.plot.ly" not in html
    assert "application/vnd.plotly.v1+json" not in copied.cells[1].outputs[0].data
    assert all(path.read_bytes() == data for path, data in originals.items())
    (source / "notebooks" / "0099 - Removed.ipynb").write_text("{}")
    prepare_book(book_root)
    assert not (source / "notebooks" / "0099 - Removed.ipynb").exists()


def test_book_rejects_empty_or_duplicate_numbering(book_root):
    with pytest.raises(ValueError, match="No numbered"):
        prepare_book(book_root)
    write_notebook(book_root, "0001 - First.ipynb")
    write_notebook(book_root, "0001 - Duplicate.ipynb")
    with pytest.raises(ValueError, match="unique"):
        prepare_book(book_root)
