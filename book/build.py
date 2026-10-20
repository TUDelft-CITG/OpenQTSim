"""Build a Jupyter Book from saved outputs of the numbered example notebooks."""

import argparse
import json
from pathlib import Path
import re
import shutil

import nbformat
import plotly.io as pio
from plotly.offline import get_plotlyjs
import yaml


ROOT = Path(__file__).resolve().parents[1]


def prepare_book(root: Path) -> Path:
    """Copy book inputs and generate a numerically ordered table of contents.

    Parameters
    ----------
    root : pathlib.Path
        Repository root containing ``book`` and ``notebooks``.

    Returns
    -------
    pathlib.Path
        Generated book source directory. Original notebooks are never modified.
    """
    notebooks = sorted(
        path for path in (root / "notebooks").glob("*.ipynb")
        if re.fullmatch(r"\d{4} - .+\.ipynb", path.name)
    )
    if not notebooks:
        raise ValueError("No numbered example notebooks found.")
    numbers = [path.name[:4] for path in notebooks]
    if len(numbers) != len(set(numbers)):
        raise ValueError("Numbered example notebooks must have unique four-digit numbers.")

    source = root / "book" / "_source"
    examples = source / "notebooks"
    examples.mkdir(parents=True, exist_ok=True)
    for stale in examples.glob("*.ipynb"):
        if stale.name not in {path.name for path in notebooks}:
            stale.unlink()
    for name in ["_config.yml", "intro.md"]:
        shutil.copy2(root / "book" / name, source / name)
    shutil.copy2(root / "logo-OpenQTSim.png", source / "logo-OpenQTSim.png")
    static = source / "_static"
    static.mkdir(exist_ok=True)
    (static / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    for resource in (root / "notebooks").glob("*.xlsx"):
        shutil.copy2(resource, examples / resource.name)

    groups = {}
    captions = {
        0: "Basic queueing and shared quays",
        1: "Parallel simulations with Dask",
        2: "Queue organisation and berth planning",
    }
    for path in notebooks:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                cell.source = cell.source.replace(
                    "../../OpenTESim/",
                    "https://github.com/TUDelft-CITG/OpenTESim/blob/master/",
                )
            for output in cell.get("outputs", []):
                data = output.get("data", {})
                if "application/vnd.plotly.v1+json" in data:
                    # MyST-NB has no native Plotly renderer; convert only the book copy.
                    figure = pio.from_json(
                        json.dumps(data["application/vnd.plotly.v1+json"])
                    )
                    output["data"] = {"text/html": pio.to_html(
                        figure, include_plotlyjs=False, full_html=False,
                        config={"responsive": True},
                    )}
        nbformat.write(notebook, examples / path.name)
        series = int(path.name[:4]) // 1000
        groups.setdefault(series, []).append({
            "file": f"notebooks/{path.stem}",
        })
    toc = {
        "format": "jb-book",
        "root": "intro",
        "parts": [
            {"caption": captions.get(series, f"{series}000-series examples"), "chapters": chapters}
            for series, chapters in sorted(groups.items())
        ],
    }
    (source / "_toc.yml").write_text(yaml.safe_dump(toc, sort_keys=False), encoding="utf-8")
    return source


def main() -> None:
    """Prepare the book and run a strict HTML build with the active interpreter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="Generate sources without building HTML.")
    args = parser.parse_args()
    source = prepare_book(ROOT)
    if not args.prepare_only:
        from jupyter_book.cli.main import main as book_cli

        book_cli(["build", str(source), "--path-output", str(ROOT / "book"),
                  "--all", "--warningiserror", "--keep-going"])


if __name__ == "__main__":
    main()
