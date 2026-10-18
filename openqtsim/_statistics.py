import numpy as np


def _occupied_time(starts, ends):
    order = np.argsort(starts, kind="stable")
    starts = starts[order]
    ends = ends[order]
    previous_ends = np.r_[0.0, np.maximum.accumulate(ends)[:-1]]
    return np.maximum(ends - np.maximum(starts, previous_ends), 0).sum()


def calculate_statistics(customers, servers=1):
    """Summarise completed customer intervals over [0, last completion]."""
    if customers.empty:
        raise ValueError("Statistics require at least one completed customer.")
    horizon = float(customers["TSE"].max())
    if not np.isfinite(horizon) or horizon <= 0:
        raise ValueError("Statistics require a positive finite observation horizon.")

    arrivals = customers["AT"].to_numpy()
    starts = customers["TSB"].to_numpy()
    ends = customers["TSE"].to_numpy()
    waiting = starts - arrivals
    service = ends - starts
    sojourn = ends - arrivals
    mean_service = float(service.mean())
    return {
        "observation_start": 0.0,
        "observation_end": horizon,
        "observation_duration": horizon,
        "customers": len(customers),
        "waiting_factor": float(waiting.mean() / mean_service) if mean_service > 0 else None,
        "Rho_system": float(_occupied_time(starts, ends) / horizon),
        "Rho_server": float(service.sum() / (servers * horizon)),
        "P_0": float(1 - _occupied_time(arrivals, ends) / horizon),
        "L_s": float(sojourn.sum() / horizon),
        "L_q": float(waiting.sum() / horizon),
        "W_s": float(sojourn.mean()),
        "W_q": float(waiting.mean()),
        "IAT": float(customers["IAT"].mean()),
        "ST": mean_service,
    }
