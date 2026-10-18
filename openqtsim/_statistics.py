"""Statistics of a simulated customer log (utilisation, queue lengths, waiting times)."""

import numpy as np


def _occupied_time(starts, ends):
    """Return the total length of the union of the intervals [starts, ends).

    Parameters
    ----------
    starts : numpy.ndarray
        Start times of the intervals.
    ends : numpy.ndarray
        End times of the intervals.

    Returns
    -------
    float
        Total time covered by at least one interval.
    """
    if len(starts) == 0:
        return 0.0
    order = np.argsort(starts, kind="stable")
    starts = starts[order]
    ends = ends[order]
    previous_ends = np.r_[0.0, np.maximum.accumulate(ends)[:-1]]
    return np.maximum(ends - np.maximum(starts, previous_ends), 0).sum()


def calculate_statistics(customers, servers=1):
    """Summarise a customer log, including customers that reneged (abandoned the queue).

    Time averages are taken over the observation horizon from time 0 to the last departure.

    Parameters
    ----------
    customers : pandas.DataFrame
        Customer log (e.g. from :meth:`~openqtsim.simulation.Simulation.return_log` or
        :meth:`~openqtsim.mm1.MM1.calculate`) with at least the columns ``IAT``, ``AT``, ``TSB`` and
        ``TSE``, and optionally ``TCWQ``, ``departure``, ``status`` and ``maxwait``.
    servers : int, default 1
        Number of servers (c), used for the server utilisation.

    Returns
    -------
    dict
        Observation horizon (``observation_start``, ``observation_end``, ``observation_duration``),
        number of ``customers``, ``waiting_factor`` (mean waiting time / mean service time, None if
        the mean service time is zero), ``Rho_system`` (fraction of time at least one server is
        busy), ``Rho_server`` (server utilisation), ``P_0`` (probability that the system is empty),
        ``L_s`` and ``L_q`` (mean number of customers in the system and in the queue),
        ``W_s`` and ``W_q`` (mean time in the system and in the queue) and the mean ``IAT`` and ``ST``.
        If customers have a ``maxwait``, also the number of customers ``served`` and ``reneged``.

    Raises
    ------
    ValueError
        If the log is empty or the observation horizon is not positive and finite.
    """
    if customers.empty:
        raise ValueError("Statistics require at least one completed customer.")
    departures = customers["departure"] if "departure" in customers else customers["TSE"]
    horizon = float(departures.max())
    if not np.isfinite(horizon) or horizon <= 0:
        raise ValueError("Statistics require a positive finite observation horizon.")

    arrivals = customers["AT"].to_numpy()
    served = customers if "status" not in customers else customers[customers["status"] == "served"]
    starts = served["TSB"].to_numpy(dtype=float)
    ends = served["TSE"].to_numpy(dtype=float)
    waiting = customers["TCWQ"].to_numpy() if "TCWQ" in customers else starts - arrivals
    service = ends - starts
    sojourn = departures.to_numpy() - arrivals
    mean_service = float(service.mean()) if len(service) else 0.0
    summary = {
        "observation_start": 0.0,
        "observation_end": horizon,
        "observation_duration": horizon,
        "customers": len(customers),
        "waiting_factor": float(waiting.mean() / mean_service) if mean_service > 0 else None,
        "Rho_system": float(_occupied_time(starts, ends) / horizon),
        "Rho_server": float(service.sum() / (servers * horizon)),
        "P_0": float(1 - _occupied_time(arrivals, departures.to_numpy()) / horizon),
        "L_s": float(sojourn.sum() / horizon),
        "L_q": float(waiting.sum() / horizon),
        "W_s": float(sojourn.mean()),
        "W_q": float(waiting.mean()),
        "IAT": float(customers["IAT"].mean()),
        "ST": mean_service,
    }
    if "maxwait" in customers and customers["maxwait"].notna().any():
        summary.update(served=len(served), reneged=len(customers) - len(served))
    return summary
