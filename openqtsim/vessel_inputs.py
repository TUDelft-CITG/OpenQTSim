"""Expand vessel definitions in days into chronological simulation inputs in hours."""

import heapq
from numbers import Real

import numpy as np
import pandas as pd

from ._random import create_random_streams
from ._validation import validate_positive_integer, validate_positive_rate


def generate_vessel_tables(info, *, nr_arrivals=None, max_duration_days=None,
                           arrival_distribution="D", service_distribution="D",
                           arrival_seed=None, service_seed=None):
    """Generate visits from info-sheet rows; specify exactly one stopping limit.

    All input times and the duration limit are in days; returned times are hours.
    For exponential arrivals, AT is the mean first-arrival time and IAT is the
    mean return interval of each vessel's independent renewal process.
    Service durations are fixed or exponential with mean loading + unloading.
    The duration cutoff includes arrivals at the boundary, not service completion.
    Ties are ordered by info-sheet row position. Visits recur even after reneging.
    """
    if not isinstance(info, pd.DataFrame) or info.empty or not info.columns.is_unique:
        raise ValueError("info must be a nonempty DataFrame with unique columns.")
    required = ["name", "IAT", "AT", "length", "maxwait", "unloading", "loading"]
    missing = [column for column in required if column not in info]
    if missing:
        raise ValueError("info is missing columns: {}.".format(", ".join(missing)))
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
    for column in required[1:]:
        if not info[column].map(
            lambda value: isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
            and np.isfinite(value) and value >= 0
        ).all():
            raise ValueError("{} must contain finite nonnegative numbers.".format(column))
    for column in ("IAT", "length"):
        if (info[column] <= 0).any():
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
        arrivals.append({
            "name": row["name"], "vessel_id": vessel + 1, "visit": visit,
            "IAT": (time - previous) * 24, "AT": time * 24,
            "length": row["length"], "maxwait": row["maxwait"] * 24,
        })
        services.append({"name": row["name"], "ST": duration * 24})
        previous = time
        interval = arrival_rng.exponential(row["IAT"]) if arrival_distribution == "M" else row["IAT"]
        following = time + interval
        if not np.isfinite(following) or following <= time:
            raise ValueError("Return intervals must advance arrival time by a finite positive amount.")
        heapq.heappush(pending, (following, vessel, visit + 1))
    arrival_table = pd.DataFrame(arrivals, columns=[
        "name", "vessel_id", "visit", "IAT", "AT", "length", "maxwait"])
    service_table = pd.DataFrame(services, columns=["name", "ST"])
    if not arrival_table.empty:
        times = arrival_table[["IAT", "AT", "maxwait"]].to_numpy()
        if not np.isfinite(times).all() or not np.isfinite(service_table["ST"]).all():
            raise ValueError("Generated time values overflowed when converted to hours.")
    return arrival_table, service_table
