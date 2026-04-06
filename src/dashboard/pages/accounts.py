from __future__ import annotations

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

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
            html.H4("🏦 Contas", className="mb-4"),
            dcc.Interval(id="accounts-interval", interval=30_000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(metric_card("Patrimônio Total", "Carregando...", color=PRIMARY), md=4, id="accounts-net-worth"),
                    dbc.Col(metric_card("Contas Ativas", "Carregando...", color=SUCCESS), md=4, id="accounts-count"),
                    dbc.Col(metric_card("Saldo Médio", "Carregando...", color=PRIMARY), md=4, id="accounts-avg-balance"),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [section_header("Contas"), html.Div(id="accounts-table")],
                        md=8,
                    ),
                    dbc.Col(
                        [section_header("Distribuição"), dcc.Graph(id="accounts-pie-chart")],
                        md=4,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Button("↻ Atualizar", id="accounts-refresh-btn", color="primary", size="sm"),
        ],
        fluid=True,
    )


def register_callbacks(app):
    @app.callback(
        Output("accounts-net-worth", "children"),
        Output("accounts-count", "children"),
        Output("accounts-avg-balance", "children"),
        Output("accounts-table", "children"),
        Output("accounts-pie-chart", "figure"),
        Input("accounts-interval", "n_intervals"),
        Input("accounts-refresh-btn", "n_clicks"),
        prevent_initial_call=False,
    )
    def update_accounts(n_intervals, n_clicks):
        from src.accounts.service import AccountService

        try:
            with get_session(_get_factory()) as db:
                svc = AccountService(db)
                accounts = svc.list(include_inactive=False)
                net_worth = svc.net_worth()
        except Exception:
            empty_fig = go.Figure()
            return "Erro", "Erro", "Erro", html.Div("Erro ao carregar contas."), empty_fig

        count = len(accounts)
        avg = net_worth / count if count > 0 else 0.0

        # Metric cards
        card_nw = metric_card("Patrimônio Total", fmt_brl(net_worth), color=PRIMARY)
        card_count = metric_card("Contas Ativas", str(count), color=SUCCESS)
        card_avg = metric_card("Saldo Médio", fmt_brl(avg), color=PRIMARY)

        # Table
        rows = []
        for acc in accounts:
            color = SUCCESS if acc.balance > 0 else (DANGER if acc.balance < 0 else "#333")
            rows.append(
                html.Tr(
                    [
                        html.Td(acc.name),
                        html.Td(acc.bank_name or "—"),
                        html.Td(acc.account_type or "—"),
                        html.Td(fmt_brl(acc.balance), style={"color": color, "fontWeight": "600"}),
                    ]
                )
            )
        table = dbc.Table(
            [
                html.Thead(html.Tr([html.Th("Nome"), html.Th("Banco"), html.Th("Tipo"), html.Th("Saldo")])),
                html.Tbody(rows),
            ],
            striped=True,
            hover=True,
            responsive=True,
            size="sm",
        )

        # Pie chart — only positive balances
        pos = [(a.name, a.balance) for a in accounts if a.balance > 0]
        if pos:
            labels, values = zip(*pos)
            fig = pie_chart(list(labels), list(values), "Distribuição de Saldo")
        else:
            fig = go.Figure()
            fig.update_layout(title="Sem saldos positivos")

        return card_nw, card_count, card_avg, table, fig
