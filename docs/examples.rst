========
Examples
========

The `notebooks`_ folder contains numbered example notebooks. They all construct their objects in the same way:
customers and service stations are composed of mixins with ``openqtsim.create_object``, and
``openqtsim.inspect_object`` shows their mandatory and optional inputs.

Basic examples
--------------

The 0000-series notebooks are best read in order:

#. **0001 - D D 1 example**: reproduces the queueing table (1 server) from the lecture slides.
#. **0002 - D D 2 (max 200 m)**: reproduces the lecture example with 2 servers and a 200 m quay
   (input from ``0002 - D D 2 (max 200 m).xlsx``).
#. **0003 - D M 2 (max 200 m)**: stochastic variation 1 (negative exponential service times).
#. **0004 - M D 2 (max 200 m)**: stochastic variation 2 (negative exponential interarrival times).
#. **0005 - M M 2 (max 200 m)**: stochastic variation 3 (both negative exponential).
#. **0006 - M M 1 - 20 arrivals**: a simple M/M/1 example.
#. **0007 - M M 1 - 1 million arrivals**: shows that a long run approaches the analytical solution.
#. **0008 - E2 E2 1 example**: Erlang 2 interarrival and service times, compared with M/M/1 and
   Kingman's approximation.

Parallel simulations with Dask
------------------------------

The 1000-series notebooks run many independent simulations in parallel with `Dask`_
(see ``openqtsim.mt_engine``). Install Dask with ``pip install -e ".[dask]"``.

#. **1001 - M M 1 using Dask**: independent replications of an M/M/1 queue (100,000 customers each),
   compared with the analytical solution.
#. **1002 - M M n - creating a queueing table**: waiting time in units of service time for 1-10 berths and
   10-90 % berth occupancy (1,000,000 customers per combination), compared with the analytical M/M/n
   (Erlang C) table of PIANC (2014).
#. **1003 - M E2 n - creating a queueing table**: the same for M/E2/n, compared with the table of
   Groenveld (2001).
#. **1004 - E2 E2 n - creating a queueing table**: the same for E2/E2/n, compared with the table of
   Groenveld (2001).

``create_tasks`` creates one task per utilisation, number of servers and replication (each with its own
reproducible seeds), and ``run_tasks(tasks, client)`` distributes them over a ``dask.distributed.Client``.
That client can be a ``LocalCluster`` on your computer or a remote (HPC or cloud) cluster:

.. code-block:: python

    from dask.distributed import Client, LocalCluster
    import openqtsim

    tasks = openqtsim.create_tasks(
        "M", "M", servers=range(1, 11), utilisations=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        nr_arr=100_000, nr_replications=10, seed=2024,
    )
    with Client(LocalCluster()) as client:
        results = openqtsim.run_tasks(tasks, client)
    table = openqtsim.waiting_time_table(tasks, results)

.. _notebooks: https://github.com/TUDelft-CITG/OpenQTSim/tree/master/notebooks
.. _Dask: https://www.dask.org
