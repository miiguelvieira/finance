from __future__ import annotations

import plotly.graph_objects as go

from src.dashboard.theme import FONT_FAMILY, PRIMARY

_COLOR_SEQ = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#f97316", "#64748b",
]


def _base_layout(title: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=13, color="#0f172a", family=FONT_FAMILY)),
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color="#64748b"),
        xaxis=dict(showgrid=False, showline=False, zeroline=False),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False),
        legend=dict(font=dict(size=11)),
    )


def bar_chart(x: list, y: list, title: str, color: str = PRIMARY) -> go.Figure:
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=color, marker_line_width=0))
    fig.update_layout(**_base_layout(title))
    return fig


def pie_chart(labels: list, values: list, title: str) -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            textinfo="percent",
            hoverinfo="label+percent+value",
            marker=dict(colors=_COLOR_SEQ, line=dict(color="white", width=2)),
        )
    )
    layout = _base_layout(title)
    layout.pop("xaxis", None)
    layout.pop("yaxis", None)
    fig.update_layout(**layout)
    return fig


def line_chart(x: list, y: list, title: str, color: str = PRIMARY) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=x, y=y,
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline"),
            marker=dict(size=6, color=color),
            fill="tozeroy",
            fillcolor=f"rgba(59,130,246,0.08)",
        )
    )
    fig.update_layout(**_base_layout(title))
    return fig
