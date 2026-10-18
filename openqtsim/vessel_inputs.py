"""Expand vessel definitions in days into chronological simulation inputs in hours."""

import heapq
from numbers import Real

import numpy as np
import pandas as pd

from ._random import create_random_streams
from ._validation import validate_positive_integer, validate_positive_rate
from .core.mixins import HasArrivalSchedule, HasHandlingTimes, HasLength, HasMaxWait, Identifiable


def _customers_to_info(customers):
    """Convert mixin-composed customer objects to an info-sheet DataFrame.

    Parameters
    ----------
    customers : list
        Customer objects composed of Identifiable, HasArrivalSchedule and HasHandlingTimes,
        and optionally (all or none) HasLength and HasMaxWait.

    Returns
    -------
    pandas.DataFrame
        Info sheet with the columns name, IAT, AT, unloading, loading (and length, maxwait).

    Raises
    ------
    ValueError
        If a customer misses a required mixin or the optional mixins are mixed.
    """
    rows = []
    for customer in customers:
        missing = [mixin.__name__ for mixin in (Identifiable, HasArrivalSchedule, HasHandlingTimes)
                   if not isinstance(customer, mixin)]
        if missing:
            raise ValueError("Customer objects must include the mixins: {}.".format(", ".join(missing)))
        row = {"name": customer.name, "IAT": customer.IAT, "AT": customer.AT,
               "unloading": customer.unloading, "loading": customer.loading}
        if isinstance(customer, HasLength):
            row["length"] = customer.length
        if isinstance(customer, HasMaxWait):
            row["maxwait"] = customer.maxwait
        rows.append(row)
    if any(row.keys() != rows[0].keys() for row in rows):
        raise ValueError("Either all or none of the customers must include HasLength (and HasMaxWait).")
    return pd.DataFrame(rows)


def generate_vessel_tables(info, *, nr_arrivals=None, max_duration_days=None,
                           arrival_distribution="D", service_distribution="D",
                           arrival_seed=None, service_seed=None):
    """Generate chronological vessel visits from info-sheet rows.

    Every vessel first arrives at AT and then returns every IAT. All input times and the
    duration limit are in days; returned times are in hours. Specify exactly one stopping limit
    (nr_arrivals or max_duration_days). The duration cutoff includes arrivals at the boundary,
    not service completion. Ties are ordered by info-sheet row position. Visits recur even
    after reneging.

    Parameters
    ----------
    info : pandas.DataFrame or list
        Info sheet with the columns name, IAT, AT, unloading and loading, and optionally length
        and maxwait; or a list of customer objects composed of the mixins
        :class:`~openqtsim.core.mixins.misc.Identifiable`, :class:`~openqtsim.core.mixins.customer.HasArrivalSchedule` and
        :class:`~openqtsim.core.mixins.customer.HasHandlingTimes`, optionally with
        :class:`~openqtsim.core.mixins.resource.HasLength` and :class:`~openqtsim.core.mixins.customer.HasMaxWait`.
    nr_arrivals : int, optional
        Number of visits to generate (keyword-only).
    max_duration_days : float, optional
        Generate all visits arriving up to and including this time (days, keyword-only).
    arrival_distribution : {"D", "M"}, default "D"
        Deterministic arrivals, or exponential arrivals in which AT is the mean first-arrival
        time and IAT the mean return interval of each vessel's independent renewal process.
    service_distribution : {"D", "M"}, default "D"
        Fixed or exponential service durations with mean loading + unloading.
    arrival_seed : int, optional
        Seed of the arrival stream (keyword-only).
    service_seed : int, optional
        Seed of the service stream (keyword-only); must differ from arrival_seed.

    Returns
    -------
    arrival_table : pandas.DataFrame
        One row per visit with the columns name, vessel_id, visit, IAT and AT (hours), and length
        and maxwait (hours) when given; input for a deterministic arrival process.
    service_table : pandas.DataFrame
        One row per visit with the columns name and ST (hours); input for a deterministic
        service process.

    Raises
    ------
    ValueError
        If an input is invalid.
    """
    if isinstance(info, (list, tuple)) and info:
        info = _customers_to_info(info)
    if not isinstance(info, pd.DataFrame) or info.empty or not info.columns.is_unique:
        raise ValueError("info must be a nonempty DataFrame (or list of customer objects) with unique columns.")
    required = ["name", "IAT", "AT", "unloading", "loading"]
    missing = [column for column in required if column not in info]
    if missing:
        raise ValueError("info is missing columns: {}.".format(", ".join(missing)))
    optional = [column for column in ("length", "maxwait") if column in info]
    for symbol, label in [(arrival_distribution, "arrival"), (service_distribution, "service")]:
        if symbol not in ("D", "M"):
            raise ValueError("{} distribution must be 'D' or 'M'.".format(label))
    if (nr_arrivals is None) == (max_duration_days is None):
        raise ValueError("Specify exactly one of nr_arrivals or max_duration_days.")
    if nr_arrivals is not None:
        validate_positive_integer(nr_arrivals, "nr_arrivals")
    else:
        validate_positive_rate(max_duration_days, "max_duration_days")
    if not info["name"].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
        raise ValueError("Vessel names must be nonempty strings.")
    for column in required[1:] + optional:
        if not info[column].map(
            lambda value: isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
            and np.isfinite(value) and value >= 0
        ).all():
            raise ValueError("{} must contain finite nonnegative numbers.".format(column))
    for column in ("IAT", "length"):
        if column in info and (info[column] <= 0).any():
            raise ValueError("{} must contain positive numbers.".format(column))
    means = info["unloading"].to_numpy(dtype=float) + info["loading"].to_numpy(dtype=float)
    if not np.isfinite(means).all() or (service_distribution == "M" and (means <= 0).any()):
        raise ValueError("loading + unloading must be finite and positive for exponential service.")

    arrival_rng, service_rng = create_random_streams(arrival_seed, service_seed)
    rows = info.to_dict("records")
    pending = []
    for vessel, row in enumerate(rows):
        first = arrival_rng.exponential(row["AT"]) if arrival_distribution == "M" else row["AT"]
        heapq.heappush(pending, (float(first), vessel, 1))
    arrivals = []
    services = []
    previous = 0.0
    while nr_arrivals is None or len(arrivals) < nr_arrivals:
        time, vessel, visit = heapq.heappop(pending)
        if max_duration_days is not None and time > max_duration_days:
            break
        row = rows[vessel]
        duration = service_rng.exponential(means[vessel]) if service_distribution == "M" else means[vessel]
        arrival = {
            "name": row["name"], "vessel_id": vessel + 1, "visit": visit,
            "IAT": (time - previous) * 24, "AT": time * 24,
        }
        if "length" in optional:
            arrival["length"] = row["length"]
        if "maxwait" in optional:
            arrival["maxwait"] = row["maxwait"] * 24
        arrivals.append(arrival)
        services.append({"name": row["name"], "ST": duration * 24})
        previous = time
        interval = arrival_rng.exponential(row["IAT"]) if arrival_distribution == "M" else row["IAT"]
        following = time + interval
        if not np.isfinite(following) or following <= time:
            raise ValueError("Return intervals must advance arrival time by a finite positive amount.")
        heapq.heappush(pending, (following, vessel, visit + 1))
    arrival_table = pd.DataFrame(arrivals, columns=[
        "name", "vessel_id", "visit", "IAT", "AT", *optional])
    service_table = pd.DataFrame(services, columns=["name", "ST"])
    if not arrival_table.empty:
        times = arrival_table[["IAT", "AT", *(["maxwait"] if "maxwait" in optional else [])]].to_numpy()
        if not np.isfinite(times).all() or not np.isfinite(service_table["ST"]).all():
            raise ValueError("Generated time values overflowed when converted to hours.")
    return arrival_table, service_table
