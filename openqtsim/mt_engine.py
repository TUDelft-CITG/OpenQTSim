"""Run many independent queue simulations in parallel (e.g. with Dask).

Each :class:`Task` describes one simulation; :func:`worker` runs it and returns
the average waiting time in units of the average service time. The tasks are
independent, so they can be distributed over processes or a cluster with
:func:`run_tasks` and a ``dask.distributed.Client``.
"""
import math
from collections import namedtuple

import numpy as np
import pandas as pd

import openqtsim
from openqtsim._statistics import calculate_statistics

# mu is the total service capacity of the system (customers per time unit); each of
# the c servers serves at mu / c, so the utilisation is lam / mu.
Task = namedtuple(
    "Task",
    "A, S, c, nr_arr, lam, mu, replication, arrival_seed, service_seed",
    defaults=(0, None, None),
)
Task.__doc__ = """One independent queue simulation.

Parameters
----------
A : str
    Symbol of the arrival process ("M" or "Ek").
S : str
    Symbol of the service process ("M" or "Ek").
c : int
    Number of servers.
nr_arr : int
    Number of customers to simulate.
lam : float
    Arrival rate (customers per time unit).
mu : float
    Total service capacity of the system (customers per time unit); each server serves at
    mu / c, so the utilisation is lam / mu.
replication : int, default 0
    Replication number.
arrival_seed : int, optional
    Seed of the arrival stream.
service_seed : int, optional
    Seed of the service stream.
"""


def _simulate(task: Task):
    """Simulate one task and return the customer log (see :meth:`~openqtsim.simulation.Simulation.return_log`)."""
    A = openqtsim.ArrivalProcess(task.A, arr_rate=task.lam)
    S = openqtsim.ServiceProcess(task.S, srv_rate=task.mu / task.c)
    q = openqtsim.Queue(A, S, task.c)

    sim = openqtsim.Simulation(q, arrival_seed=task.arrival_seed, service_seed=task.service_seed)
    sim.run(task.nr_arr)
    df_cust, _ = sim.return_log()
    return df_cust


def worker(task: Task):
    """Simulate one task and return the waiting time factor.

    Parameters
    ----------
    task : Task
        The simulation to run.

    Returns
    -------
    float
        Mean waiting time / mean service time.
    """
    df_cust = _simulate(task)
    return float(np.mean(df_cust["TCWQ"]) / np.mean(df_cust["ST"]))


def statistics_worker(task: Task):
    """Simulate one task and return its statistics.

    Parameters
    ----------
    task : Task
        The simulation to run.

    Returns
    -------
    dict
        Statistics as returned by :meth:`~openqtsim.simulation.Simulation.get_stats` (without printing),
        together with the task fields.
    """
    summary = calculate_statistics(_simulate(task), task.c)
    summary.update(task._asdict())
    return summary


def create_tasks(A, S, servers, utilisations, nr_arr, mu=10, nr_replications=1, seed=None):
    """Create one task per (utilisation, number of servers, replication).

    Parameters
    ----------
    A : str
        Symbol of the arrival process ("M" or "Ek").
    S : str
        Symbol of the service process ("M" or "Ek").
    servers : iterable of int
        Numbers of servers.
    utilisations : iterable of float
        Server utilisations (lam / mu).
    nr_arr : int
        Number of customers per simulation.
    mu : float, default 10
        Total service capacity of the system (customers per time unit).
    nr_replications : int, default 1
        Number of replications per combination.
    seed : int, optional
        With an integer seed every task gets its own reproducible, independent pair of
        arrival and service seeds, so results do not depend on how tasks are scheduled.

    Returns
    -------
    list of Task
        The tasks.
    """
    combinations = [
        (u, c, r) for u in utilisations for c in servers for r in range(nr_replications)
    ]
    if seed is None:
        seeds = [(None, None)] * len(combinations)
    else:
        seeds = [
            tuple(int(s) for s in child.generate_state(2))
            for child in np.random.SeedSequence(seed).spawn(len(combinations))
        ]
        seeds = [(a, s if s != a else (s + 1) % 2**32) for a, s in seeds]
    return [
        Task(A, S, int(c), int(nr_arr), float(u) * mu, mu, r, arrival_seed, service_seed)
        for (u, c, r), (arrival_seed, service_seed) in zip(combinations, seeds)
    ]


def run_tasks(tasks, client=None, func=worker):
    """Run ``func`` on all tasks.

    Parameters
    ----------
    tasks : list of Task
        The tasks to run.
    client : dask.distributed.Client, optional
        Client to distribute the tasks over; without a client the tasks run serially.
    func : callable, default worker
        Function applied to each task, e.g. :func:`worker` or :func:`statistics_worker`.

    Returns
    -------
    list
        The results, in the order of the tasks.
    """
    if client is None:
        return [func(task) for task in tasks]
    # pure=False: identical unseeded tasks must be simulated separately, not deduplicated
    futures = client.map(func, tasks, pure=False)
    return client.gather(futures)


def waiting_time_table(tasks, results, aggfunc="mean"):
    """Pivot results into a table: rows utilisation, columns number of servers.

    Parameters
    ----------
    tasks : list of Task
        The tasks.
    results : iterable
        One result per task (e.g. from :func:`run_tasks`).
    aggfunc : str or callable, default "mean"
        Aggregation of the replications per combination.

    Returns
    -------
    pandas.DataFrame
        Table with the utilisations as index and the numbers of servers as columns.
    """
    df = pd.DataFrame(tasks)
    df["result"] = list(results)
    df["utilisation"] = (df["lam"] / df["mu"]).round(10)
    return df.pivot_table(index="utilisation", columns="c", values="result", aggfunc=aggfunc)


def mmc_waiting_time_factor(c, utilisation):
    """Analytical M/M/c mean waiting time in units of mean service time (Erlang C).

    Parameters
    ----------
    c : int
        Number of servers.
    utilisation : float
        Server utilisation.

    Returns
    -------
    float
        Waiting time factor; infinity if the utilisation is not between 0 and 1.
    """
    if not 0 <= utilisation < 1:
        return math.inf
    a = c * utilisation
    term = a**c / math.factorial(c) / (1 - utilisation)
    erlang_c = term / (sum(a**k / math.factorial(k) for k in range(c)) + term)
    return erlang_c / (c * (1 - utilisation))
