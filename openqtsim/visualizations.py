"""Visualisations of OpenQTSim simulation logs."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _decimate_steps(t, y, max_points):
    """Reduce a step series to at most about max_points points.

    Each bin keeps its first, last, minimum and maximum point, so peaks and the step structure stay visible.
    Returns (t, y, decimated).
    """
    n = len(y)
    if max_points is None or n <= max_points:
        return t, y, False
    bins = np.arange(n) // int(np.ceil(4 * n / max_points))
    groups = pd.Series(y).groupby(bins)
    index = np.unique(np.concatenate([
        groups.idxmin().to_numpy(), groups.idxmax().to_numpy(),
        groups.head(1).index.to_numpy(), groups.tail(1).index.to_numpy(),
    ]))
    return t[index], y[index], True


def plot_system_state(system_state, max_points=100_000, height=500):
    """Step plot of the number of customers in the system and in the queue over time.

    system_state: system log from Simulation.return_log() (columns t, c_s, c_q).
    max_points: larger traces are reduced (per bin: first, last, minimum and maximum); None plots all points.
    Returns the plotly figure.
    """
    t = system_state["t"].to_numpy()
    fig = go.Figure()
    for column, label, color in [("c_s", "Nr. of customers in system", "#0072B2"),
                                 ("c_q", "Nr. of customers in queue", "#D55E00")]:
        x, y, decimated = _decimate_steps(t, system_state[column].to_numpy(), max_points)
        Scatter = go.Scattergl if len(x) > 10_000 else go.Scatter
        fig.add_trace(Scatter(
            x=x, y=y, mode="lines", line=dict(shape="hv", color=color),
            name=label + (" (reduced: min/max per bin)" if decimated else ""),
            hovertemplate="Time: %{x:.2f} h<br>" + label + ": %{y}<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_white", height=height, legend_title_text="System state",
        xaxis_title="Time (hours)", yaxis_title="Nr. of customers",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def plot_IAT_ST(customer_log, bins="auto", height=500):
    """Histograms of the interarrival times (IAT) and service times (ST), with their means.

    customer_log: customer log from Simulation.return_log(); reneged customers (no ST) are skipped.
    The vertical mean lines run over the full height of each panel. Returns the plotly figure.
    """
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08,
                        subplot_titles=("Interarrival times", "Service times"))
    for col, column, label, color in [(1, "IAT", "interarrival time", "#0072B2"),
                                      (2, "ST", "service time", "#009E73")]:
        values = customer_log[column].dropna().to_numpy(dtype=float)
        if len(values) == 0:
            continue
        counts, edges = np.histogram(values, bins=bins)
        fig.add_trace(go.Bar(
            x=(edges[:-1] + edges[1:]) / 2, y=counts, width=np.diff(edges), marker_color=color, marker_line_width=0,
            name=f"{column}: nr. of customers", customdata=np.column_stack([edges[:-1], edges[1:]]),
            hovertemplate="%{customdata[0]:.4f} - %{customdata[1]:.4f} h<br>Nr. of customers: %{y}<extra></extra>",
        ), row=1, col=col)
        top = counts.max() * 1.05
        mean = values.mean()
        fig.add_trace(go.Scatter(
            x=[mean, mean], y=[0, top], mode="lines", line=dict(color="black", width=3),
            name=f"Mean {label}: {mean:.4f} h",
            hovertemplate=f"Mean {label}: {mean:.4f} h<extra></extra>",
        ), row=1, col=col)
        fig.update_yaxes(range=[0, top], title_text="Nr. of customers", row=1, col=col)
        fig.update_xaxes(title_text=f"{column} (hours)", row=1, col=col)
    fig.update_layout(template="plotly_white", height=height, bargap=0,
                      legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="left", x=0))
    return fig


def hover_time(hours):
    """Format a time in hours with at most two decimals, followed by the time in days."""
    hours_text = f"{hours:.2f}".rstrip("0").rstrip(".")
    days_text = f"{hours / 24:.2f}".rstrip("0").rstrip(".")
    return f"{hours_text} h ({days_text} days)"


def plot_gantt(log, title=None, height=750):
    """Gantt chart of arrival, waiting, service, departure and reneging per customer visit.

    log: customer log from Simulation.return_log(); one row per visit, labelled by name when available.
    Returns the plotly figure.
    """
    customers = log.sort_values(["AT", "c_id"]).copy()
    customers["wait_end"] = customers["TSB"].fillna(customers["departure"])
    customer_rows = "Customer " + customers["c_id"].astype(str)
    customer_labels = customer_rows.copy()
    if "name" in customers.columns:
        names = customers["name"].fillna("").astype(str).str.strip()
        customer_labels = names.where(names.ne(""), customer_rows)

    fig = go.Figure()
    for phase, start, end, color in [
        ("Waiting", "AT", "wait_end", "#E69F00"),
        ("Service", "TSB", "TSE", "#0072B2"),
    ]:
        mask = customers[start].notna() & customers[end].notna()
        duration = customers.loc[mask, end] - customers.loc[mask, start]
        fig.add_trace(go.Bar(
            name=phase, y=customer_rows[mask], text=customer_labels[mask], textposition="none",
            x=duration, base=customers.loc[mask, start], orientation="h", marker_color=color,
            customdata=list(zip(
                customers.loc[mask, start].map(hover_time),
                customers.loc[mask, end].map(hover_time),
                duration.map(hover_time),
            )),
            hovertemplate=("%{text}<br>Start: %{customdata[0]}"
                           "<br>End: %{customdata[1]}"
                           "<br>Duration: %{customdata[2]}<extra>%{fullData.name}</extra>"),
        ))

    for event, column, symbol, color, size, status in [
        ("Arrival", "AT", "circle-open", "#333333", 12, None),
        ("Departure", "TSE", "x", "#009E73", 9, "served"),
        ("Service start", "TSB", "diamond", "#CC79A7", 6, "served"),
        ("Reneged", "departure", "x", "red", 12, "reneged"),
    ]:
        mask = customers[column].notna()
        if status is not None:
            mask &= customers["status"].eq(status)
        fig.add_trace(go.Scatter(
            name=event, x=customers.loc[mask, column], y=customer_rows[mask], text=customer_labels[mask],
            mode="markers", marker=dict(symbol=symbol, color=color, size=size),
            customdata=customers.loc[mask, column].map(hover_time),
            hovertemplate="%{text}<br>Time: %{customdata}<extra>%{fullData.name}</extra>",
        ))

    fig.update_layout(
        title=title if title is not None else f"{len(customers)} customer arrivals",
        barmode="overlay", template="plotly_white", height=height,
        xaxis_title="Time since simulation start (hours)",
        yaxis_title="Customer (arrival order)", legend_title_text="Phase / event",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=customer_rows.tolist(), autorange="reversed",
                     tickmode="array", tickvals=customer_rows.tolist(), ticktext=customer_labels.tolist())
    fig.update_xaxes(range=[0, customers["departure"].max() * 1.03])
    return fig
