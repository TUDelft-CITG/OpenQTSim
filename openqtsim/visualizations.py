"""Visualisations of OpenQTSim simulation logs."""

import plotly.graph_objects as go


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
