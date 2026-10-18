"""Utilities to compose objects from mixins and inspect their inputs (following OpenTNSim)."""

import inspect
import itertools

import pandas as pd


def create_object(name, classes):
    """Create a class called name from the given mixins, using the first valid base class order."""
    for perm in itertools.permutations(classes):
        try:
            return type(name, perm, {})
        except TypeError:
            pass
    raise TypeError("No valid base class order exists")


def _init_parameters(Class):
    for cls in Class.mro():
        if cls is object or "__init__" not in cls.__dict__:
            continue
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name == "self" or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            yield cls, name, param


def get_all_init_params(Class):
    """Return the names of all named __init__ parameters along the class' MRO."""
    return {name for _, name, _ in _init_parameters(Class)}


def inspect_object(Class, candidate_kwargs=None, show_parameter_table=False):
    """Tabulate the required and optional inputs of a (mixin-composed) class.

    candidate_kwargs: optional dict with the inputs you intend to provide; the table then marks
    each parameter as 'missing', 'added', 'optional (used)' or 'optional (unused)'.
    show_parameter_table: display the table; otherwise return (styled table, missing_parameters).
    """
    candidate_kwargs = {} if candidate_kwargs is None else candidate_kwargs

    def highlight_status(row):
        colors = {"missing": "#ffcccc", "optional (unused)": "#ffe5b4", "optional (used)": "#e8f5e9"}
        return ["background-color: {}".format(colors.get(row["status"], "#c8e6c9"))] * len(row)

    rows = []
    for cls, name, param in _init_parameters(Class):
        required = param.default is inspect.Parameter.empty
        rows.append({
            "parameter": name,
            "class": cls.__name__,
            "default": "" if required else repr(param.default),
            "required": required,
            "provided": name in candidate_kwargs,
        })

    df = pd.DataFrame(rows, columns=["parameter", "class", "default", "required", "provided"])
    df = df.drop_duplicates("parameter")
    df["missing"] = df["required"] & ~df["provided"]
    df["status"] = "optional (unused)"
    df.loc[df["missing"], "status"] = "missing"
    df.loc[df["required"] & df["provided"], "status"] = "added"
    df.loc[~df["required"] & df["provided"], "status"] = "optional (used)"
    df = df.sort_values(
        by=["missing", "required", "class", "parameter"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    missing_parameters = bool(df["missing"].any())
    df = df.drop(["missing", "required", "provided"], axis=1)
    styled = df.style.apply(highlight_status, axis=1)
    if show_parameter_table:
        try:
            from IPython.display import display
        except ImportError:
            print(df.to_string())
        else:
            display(styled)
        return None
    return styled, missing_parameters
