from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard.theme import PRIMARY, SIDEBAR_BG, SIDEBAR_WIDTH

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": SIDEBAR_WIDTH,
    "padding": "0",
    "backgroundColor": SIDEBAR_BG,
    "color": "white",
    "overflowY": "auto",
    "zIndex": "100",
    "display": "flex",
    "flexDirection": "column",
}

CONTENT_STYLE = {
    "marginLeft": SIDEBAR_WIDTH,
    "padding": "28px 32px",
    "backgroundColor": "#f1f5f9",
    "minHeight": "100vh",
}

_NAV_LINKS = [
    {"label": "🏠 Visão Geral",    "href": "/"},
    {"label": "🏦 Contas",          "href": "/accounts"},
    {"label": "💳 Transações",      "href": "/transactions"},
    {"label": "📈 Investimentos",   "href": "/investments"},
    {"label": "🎯 Metas",           "href": "/goals"},
    {"label": "🤖 Chatbot",         "href": "/chatbot"},
]

_LINK_STYLE = {
    "color": "rgba(255,255,255,0.65)",
    "padding": "10px 20px",
    "borderRadius": "8px",
    "margin": "2px 12px",
    "fontSize": "0.875rem",
    "fontWeight": "500",
    "transition": "all 0.15s ease",
}


def _sidebar() -> html.Div:
    nav_items = [
        dbc.NavItem(
            dbc.NavLink(
                link["label"],
                href=link["href"],
                active="exact",
                style=_LINK_STYLE,
            )
        )
        for link in _NAV_LINKS
    ]

    logo_area = html.Div(
        [
            html.Div(
                "💰",
                style={"fontSize": "1.5rem", "marginBottom": "4px"},
            ),
            html.Div(
                "Finance",
                style={"fontSize": "1.1rem", "fontWeight": "700", "letterSpacing": "0.5px"},
            ),
            html.Div(
                "Personal",
                style={"fontSize": "0.7rem", "color": "rgba(255,255,255,0.4)", "textTransform": "uppercase", "letterSpacing": "2px"},
            ),
        ],
        style={
            "padding": "24px 24px 20px",
            "borderBottom": "1px solid rgba(255,255,255,0.08)",
            "marginBottom": "8px",
        },
    )

    footer = html.Div(
        [
            html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "margin": "0 0 12px"}),
            html.Div(
                "v1.0 · 2026",
                style={"color": "rgba(255,255,255,0.25)", "fontSize": "0.7rem", "padding": "0 24px 16px"},
            ),
        ],
        style={"marginTop": "auto"},
    )

    return html.Div(
        [
            logo_area,
            dbc.Nav(nav_items, vertical=True, pills=True, style={"flex": "1"}),
            footer,
        ],
        style=SIDEBAR_STYLE,
        id="sidebar",
    )


def create_layout() -> html.Div:
    return html.Div(
        [
            _sidebar(),
            html.Div(
                [
                    dcc.Location(id="url", refresh=False),
                    html.Div(id="page-content"),
                ],
                style=CONTENT_STYLE,
            ),
        ]
    )
