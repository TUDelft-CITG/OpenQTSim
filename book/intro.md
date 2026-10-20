# OpenQTSim examples

**OpenQTSim** is an open-source discrete-event simulator for queues described by
Kendall notation. This book brings together the numbered example notebooks.

Start with the basic queueing and shared-quay examples, then explore parallel
simulation with Dask and the berth-planning applications.

## Reading and running the examples

The book displays **saved notebook outputs**. Building it does not run any
simulations, start Dask workers or require OpenTESim. Interactive Plotly figures
support hovering, zooming and, for sunbursts, clicking sectors to explore detail.
Notebooks without saved outputs show their explanations and code only.

Download a notebook using the page's download menu, or obtain the complete
[repository](https://github.com/TUDelft-CITG/OpenQTSim). To run examples locally,
install OpenQTSim into your existing Python environment:

```bash
pip install -e .
```

The shared-quay examples also need the Excel input next to the notebook:
[0002 - D D 2 (max 200 m).xlsx](notebooks/0002%20-%20D%20D%202%20%28max%20200%20m%29.xlsx).

The 1000-series uses optional Dask dependencies:

```bash
pip install -e ".[dask]"
```

The 2000-series normally runs serially. Example 2005 additionally requires a
compatible OpenTESim installation; for sibling checkouts, run
`pip install -e ../OpenTESim` from the OpenQTSim repository root.

## Scope

Simulation estimates have sampling uncertainty and can include empty-system
start-up effects. Terminal costs and demand assumptions are illustrative.
The planning examples explain their differing workload, service-level and
financial conventions; their conclusions are not interchangeable.

The [API documentation](https://openqtsim.readthedocs.io) complements this
notebook-based book.
