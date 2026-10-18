from numbers import Integral, Real
import re

import numpy as np
import pandas as pd


def validate_positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value <= 0:
        raise ValueError("{} must be a positive integer.".format(name))


def validate_positive_rate(value, name):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or value <= 0):
        raise ValueError("{} must be a finite positive number.".format(name))


def validate_seed(seed):
    if seed is not None and (
        isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral)
        or not 0 <= seed < 2**32
    ):
        raise ValueError("seed must be None or an integer between 0 and 2**32 - 1.")


def validate_process(symbol, rate, rate_name, column):
    if not isinstance(symbol, str) or not (
        symbol in ("M", "D") or re.fullmatch(r"E[1-9][0-9]*", symbol)
    ):
        raise ValueError("Unsupported distribution {!r}; use 'M', 'D', or 'Ek' with a positive integer k.".format(
            symbol))
    if symbol != "D":
        validate_positive_rate(rate, rate_name)
        return
    if not isinstance(rate, pd.DataFrame) or column not in rate.columns:
        raise ValueError("Deterministic input must be a DataFrame with a '{}' column.".format(column))
    if not rate.columns.is_unique:
        raise ValueError("Deterministic input must have unique column names.")
    values = rate[column]
    if not values.map(
        lambda value: isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
        and np.isfinite(value) and value >= 0
    ).all():
        raise ValueError("Deterministic '{}' values must be finite nonnegative numbers.".format(column))
