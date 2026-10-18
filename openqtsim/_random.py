"""Independent, reproducible random number streams for arrivals and services."""

import numpy as np

from openqtsim._validation import validate_seed


def create_random_streams(arrival_seed, service_seed):
    """Create separate random generators for the arrival and the service process.

    Parameters
    ----------
    arrival_seed : int or None
        Seed (0 to 2**32 - 1) of the arrival stream; None gives a non-reproducible stream.
    service_seed : int or None
        Seed (0 to 2**32 - 1) of the service stream; None gives a non-reproducible stream.

    Returns
    -------
    arrivals : numpy.random.Generator
        Random generator for the interarrival times.
    services : numpy.random.Generator
        Random generator for the service times.

    Raises
    ------
    ValueError
        If a seed is invalid, or if both seeds are given and equal.
    """
    validate_seed(arrival_seed, "arrival_seed")
    validate_seed(service_seed, "service_seed")
    if arrival_seed is not None and service_seed is not None and arrival_seed == service_seed:
        raise ValueError("arrival_seed and service_seed must be different when both are specified.")
    arrivals = np.random.default_rng(np.random.SeedSequence(arrival_seed, spawn_key=(0,)))
    services = np.random.default_rng(np.random.SeedSequence(service_seed, spawn_key=(1,)))
    return arrivals, services
