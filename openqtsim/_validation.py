"""Input validation shared by the OpenQTSim classes and functions.

All validators raise a ``ValueError`` with a descriptive message when the value is invalid.
"""

from numbers import Integral, Real
import re

import numpy as np
import pandas as pd


def validate_positive_integer(value, name):
    """Check that value is a positive integer (booleans are rejected).

    Parameters
    ----------
    value : object
        Value to check.
    name : str
        Name of the value, used in the error message.

    Raises
    ------
    ValueError
        If the value is invalid.
    """
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value <= 0:
        raise ValueError("{} must be a positive integer.".format(name))


def validate_positive_rate(value, name):
    """Check that value is a finite positive real number (booleans are rejected).

    Parameters
    ----------
    value : object
        Value to check.
    name : str
        Name of the value, used in the error message.

    Raises
    ------
    ValueError
        If the value is invalid.
    """
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or value <= 0):
        raise ValueError("{} must be a finite positive number.".format(name))


def validate_nonnegative_number(value, name):
    """Check that value is a finite nonnegative real number (booleans are rejected).

    Parameters
    ----------
    value : object
        Value to check.
    name : str
        Name of the value, used in the error message.

    Raises
    ------
    ValueError
        If the value is invalid.
    """
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or value < 0):
        raise ValueError("{} must be a finite nonnegative number.".format(name))


def validate_seed(seed, name="seed"):
    """Check that seed is None or an integer between 0 and 2**32 - 1.

    Parameters
    ----------
    seed : object
        Seed to check.
    name : str, default "seed"
        Name of the seed, used in the error message.

    Raises
    ------
    ValueError
        If the seed is invalid.
    """
    if seed is not None and (
        isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral)
        or not 0 <= seed < 2**32
    ):
        raise ValueError("{} must be None or an integer between 0 and 2**32 - 1.".format(name))


def validate_process(symbol, rate, rate_name, column):
    """Check the symbol and rate (or deterministic table) of an arrival or service process.

    Parameters
    ----------
    symbol : str
        Kendall symbol: "M", "D" or "Ek" (with k a positive integer).
    rate : float or pandas.DataFrame
        For "M" and "Ek" a finite positive rate; for "D" a DataFrame with unique column names
        and a ``column`` column containing finite nonnegative numbers.
    rate_name : str
        Name of the rate, used in the error message.
    column : str
        Required column of a deterministic table ("IAT" or "ST").

    Raises
    ------
    ValueError
        If the symbol or rate is invalid.
    """
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
