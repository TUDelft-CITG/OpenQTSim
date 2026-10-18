import numpy as np

from openqtsim._validation import validate_seed


def create_random_streams(arrival_seed, service_seed):
    validate_seed(arrival_seed, "arrival_seed")
    validate_seed(service_seed, "service_seed")
    if arrival_seed is not None and service_seed is not None and arrival_seed == service_seed:
        raise ValueError("arrival_seed and service_seed must be different when both are specified.")
    arrivals = np.random.default_rng(np.random.SeedSequence(arrival_seed, spawn_key=(0,)))
    services = np.random.default_rng(np.random.SeedSequence(service_seed, spawn_key=(1,)))
    return arrivals, services
