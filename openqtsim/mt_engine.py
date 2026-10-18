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


def _simulate(task: Task):
    A = openqtsim.ArrivalProcess(task.A, arr_rate=task.lam)
    S = openqtsim.ServiceProcess(task.S, srv_rate=task.mu / task.c)
    q = openqtsim.Queue(A, S, task.c)

    sim = openqtsim.Simulation(q, arrival_seed=task.arrival_seed, service_seed=task.service_seed)
    sim.run(task.nr_arr)
    df_cust, _ = sim.return_log()
    return df_cust


def worker(task: Task):
    """Simulate one task and return mean waiting time / mean service time."""
    df_cust = _simulate(task)
    return float(np.mean(df_cust["TCWQ"]) / np.mean(df_cust["ST"]))


def statistics_worker(task: Task):
    """Simulate one task and return its statistics (as ``Simulation.get_stats``, without printing)."""
    summary = calculate_statistics(_simulate(task), task.c)
    summary.update(task._asdict())
    return summary


def create_tasks(A, S, servers, utilisations, nr_arr, mu=10, nr_replications=1, seed=None):
    """Create one task per (utilisation, number of servers, replication).

    With an integer ``seed`` every task gets its own reproducible, independent pair
    of arrival and service seeds, so results do not depend on how tasks are scheduled.
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
    """Run ``func`` (default :func:`worker`) on all tasks.

    Uses a ``dask.distributed.Client`` when given, otherwise runs serially.
    """
    if client is None:
        return [func(task) for task in tasks]
    # pure=False: identical unseeded tasks must be simulated separately, not deduplicated
    futures = client.map(func, tasks, pure=False)
    return client.gather(futures)


def waiting_time_table(tasks, results, aggfunc="mean"):
    """Pivot results into a table: rows utilisation, columns number of servers."""
    df = pd.DataFrame(tasks)
    df["result"] = list(results)
    df["utilisation"] = (df["lam"] / df["mu"]).round(10)
    return df.pivot_table(index="utilisation", columns="c", values="result", aggfunc=aggfunc)


def mmc_waiting_time_factor(c, utilisation):
    """Analytical M/M/c mean waiting time in units of mean service time (Erlang C)."""
    if not 0 <= utilisation < 1:
        return math.inf
    a = c * utilisation
    term = a**c / math.factorial(c) / (1 - utilisation)
    erlang_c = term / (sum(a**k / math.factorial(k) for k in range(c)) + term)
    return erlang_c / (c * (1 - utilisation))
