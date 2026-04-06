from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

from src.dashboard.theme import DANGER, PRIMARY, SUCCESS, SECONDARY


def metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = PRIMARY,
    icon: str | None = None,
    delta: str | None = None,
    delta_positive: bool = True,
) -> dbc.Card:
    header_parts = []
    if icon:
        header_parts.append(html.Span(icon, style={"marginRight": "6px", "fontSize": "1rem"}))
    header_parts.append(
        html.Small(title, style={"color": SECONDARY, "fontWeight": "500", "fontSize": "0.78rem", "textTransform": "uppercase", "letterSpacing": "0.05em"})
    )

    body_children = [
        html.Div(header_parts, style={"marginBottom": "8px"}),
        html.Div(
            value,
            style={
                "color": "#0f172a",
                "fontWeight": "700",
                "fontSize": "1.6rem",
                "lineHeight": "1.2",
                "fontVariantNumeric": "tabular-nums",
                "marginBottom": "6px",
            },
        ),
    ]
    if delta:
        delta_color = SUCCESS if delta_positive else DANGER
        arrow = "↑" if delta_positive else "↓"
        body_children.append(
            html.Small(
                f"{arrow} {delta}",
                style={"color": delta_color, "fontWeight": "600", "fontSize": "0.8rem"},
            )
        )
    elif subtitle:
        body_children.append(
            html.Small(subtitle, style={"color": SECONDARY})
        )

    return dbc.Card(
        dbc.CardBody(body_children, style={"padding": "20px"}),
        style={
            "borderLeft": f"4px solid {color}",
            "borderRadius": "12px",
            "backgroundColor": "#ffffff",
            "border": f"1px solid #e2e8f0",
            "borderLeft": f"4px solid {color}",
        },
        className="shadow-sm mb-3",
    )


def section_header(title: str) -> html.H5:
    return html.H5(
        title,
        style={
            "fontWeight": "600",
            "color": "#0f172a",
            "borderBottom": f"2px solid {PRIMARY}",
            "paddingBottom": "8px",
            "marginBottom": "16px",
            "fontSize": "0.95rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.05em",
        },
    )
