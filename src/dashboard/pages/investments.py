from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from src.core.database import get_engine, get_session, init_db, make_session_factory
from src.dashboard.components.cards import metric_card, section_header
from src.dashboard.components.charts import pie_chart
from src.dashboard.theme import DANGER, PRIMARY, SUCCESS

_eng = None
_factory = None


def _get_factory():
    global _eng, _factory
    if _factory is None:
        from src.core.config import get_settings
        s = get_settings()
        _eng = get_engine(s.database_url)
        init_db(_eng)
        _factory = make_session_factory(_eng)
    return _factory


def fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def layout():
    return dbc.Container(
        [
            html.H4("📈 Investimentos", className="mb-4"),
            dcc.Interval(id="inv-interval", interval=60_000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="inv-principal"), md=4),
                    dbc.Col(html.Div(id="inv-current"), md=4),
                    dbc.Col(html.Div(id="inv-gain"), md=4),
                ],
                className="mb-3",
            ),
            dcc.Dropdown(
                id="inv-type-filter",
                options=[
                    {"label": t, "value": t}
                    for t in ["renda_fixa", "lci_lca", "acoes", "fii", "crypto", "other"]
                ],
                placeholder="Tipo de ativo",
                clearable=True,
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="inv-allocation-pie"), md=5),
                    dbc.Col(html.Div(id="inv-table"), md=7),
                ],
            ),
        ],
        fluid=True,
    )


def register_callbacks(app):
    @app.callback(
        Output("inv-principal", "children"),
        Output("inv-current", "children"),
        Output("inv-gain", "children"),
        Output("inv-allocation-pie", "figure"),
        Output("inv-table", "children"),
        Input("inv-interval", "n_intervals"),
        Input("inv-type-filter", "value"),
    )
    def update_investments(n_intervals, asset_type_filter):
        from src.investments.service import InvestmentService

        try:
            with get_session(_get_factory()) as db:
                svc = InvestmentService(db)
                summary = svc.portfolio_summary()
                investments = svc.list(asset_type=asset_type_filter)
        except Exception:
            empty_fig = go.Figure()
            err = html.Div("Erro ao carregar investimentos.")
            return err, err, err, empty_fig, err

        gain = summary["total_gain"]
        gain_color = SUCCESS if gain >= 0 else DANGER
        gain_pct = summary["gain_pct"]

        card_principal = metric_card(
            "Total Aplicado", fmt_brl(summary["total_principal"]), color=PRIMARY, icon="💰"
        )
        card_current = metric_card(
            "Valor Atual", fmt_brl(summary["total_current"]), color=PRIMARY, icon="📊"
        )
        card_gain = metric_card(
            "Rendimento",
            f"{fmt_brl(gain)} ({gain_pct:+.2f}%)",
            color=gain_color,
            icon="📈" if gain >= 0 else "📉",
        )

        # Pie chart — alocação por tipo
        by_type = summary["by_type"]
        if by_type and summary["count"] > 0:
            labels = list(by_type.keys())
            values = [by_type[t]["current"] for t in labels]
            fig = pie_chart(labels, values, "Alocação por Tipo")
        else:
            fig = go.Figure()
            fig.update_layout(title="Sem investimentos")

        # Table
        rows = []
        for inv in investments:
            raw_gain = inv.current_value - inv.principal
            raw_pct = (raw_gain / inv.principal * 100) if inv.principal > 0 else 0.0
            color = SUCCESS if raw_gain >= 0 else DANGER
            rows.append(
                html.Tr(
                    [
                        html.Td(inv.name),
                        html.Td(inv.asset_type),
                        html.Td(fmt_brl(inv.principal)),
                        html.Td(fmt_brl(inv.current_value)),
                        html.Td(
                            fmt_brl(raw_gain),
                            style={"color": color, "fontWeight": "600"},
                        ),
                        html.Td(
                            f"{raw_pct:+.2f}%",
                            style={"color": color, "fontWeight": "600"},
                        ),
                    ]
                )
            )

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Nome"),
                            html.Th("Tipo"),
                            html.Th("Aplicado"),
                            html.Th("Atual"),
                            html.Th("Ganho (R$)"),
                            html.Th("Ganho (%)"),
                        ]
                    )
                ),
                html.Tbody(rows if rows else [html.Tr([html.Td("Nenhum investimento.", colSpan=6)])]),
            ],
            striped=True,
            hover=True,
            responsive=True,
            size="sm",
        )

        return card_principal, card_current, card_gain, fig, table
