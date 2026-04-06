from __future__ import annotations

from datetime import date

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from src.core.database import get_engine, get_session, init_db, make_session_factory
from src.dashboard.components.cards import metric_card, section_header
from src.dashboard.components.charts import pie_chart
from src.dashboard.theme import DANGER, PRIMARY, SUCCESS, WARNING

_CATEGORIES = [
    "moradia", "alimentacao", "transporte", "saude", "educacao",
    "lazer", "vestuario", "assinaturas", "investimentos",
    "transferencia", "salario", "freelance", "dividendos", "outros",
]

_MONTHS = [
    (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"), (5, "Mai"), (6, "Jun"),
    (7, "Jul"), (8, "Ago"), (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
]

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
            html.H4("💳 Transações", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            id="tx-account-filter",
                            placeholder="Todas as contas",
                            clearable=True,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="tx-month-filter",
                            options=[{"label": m, "value": i} for i, m in _MONTHS],
                            placeholder="Mês",
                            clearable=True,
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="tx-year-filter",
                            options=[{"label": str(y), "value": y} for y in range(2023, 2027)],
                            placeholder="Ano",
                            clearable=True,
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="tx-category-filter",
                            options=[{"label": c, "value": c} for c in _CATEGORIES],
                            placeholder="Categoria",
                            clearable=True,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Button("Filtrar", id="tx-filter-btn", color="primary", size="sm"),
                        md=2,
                        className="d-flex align-items-center",
                    ),
                ],
                className="mb-3 g-2",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="tx-income"), md=4),
                    dbc.Col(html.Div(id="tx-expenses"), md=4),
                    dbc.Col(html.Div(id="tx-net"), md=4),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [section_header("Transações"), html.Div(id="tx-table")],
                        md=8,
                    ),
                    dbc.Col(
                        [section_header("Por Categoria"), dcc.Graph(id="tx-category-pie")],
                        md=4,
                    ),
                ],
            ),
            dcc.Store(id="tx-store"),
        ],
        fluid=True,
    )


def register_callbacks(app):
    # Callback 1 — popula dropdown de contas
    @app.callback(
        Output("tx-account-filter", "options"),
        Input("tx-filter-btn", "n_clicks"),
        prevent_initial_call=False,
    )
    def populate_accounts(_):
        from src.accounts.service import AccountService
        try:
            with get_session(_get_factory()) as db:
                accounts = AccountService(db).list(include_inactive=False)
            return [{"label": a.name, "value": a.id} for a in accounts]
        except Exception:
            return []

    # Callback 2 — filtra e renderiza transações
    @app.callback(
        Output("tx-income", "children"),
        Output("tx-expenses", "children"),
        Output("tx-net", "children"),
        Output("tx-table", "children"),
        Output("tx-category-pie", "figure"),
        Input("tx-filter-btn", "n_clicks"),
        State("tx-account-filter", "value"),
        State("tx-month-filter", "value"),
        State("tx-year-filter", "value"),
        State("tx-category-filter", "value"),
        prevent_initial_call=False,
    )
    def filter_transactions(_, account_id, month, year, category):
        from src.transactions.service import TransactionService

        # Build date range from year/month filters
        date_from: date | None = None
        date_to: date | None = None
        if year and month:
            import calendar
            date_from = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            date_to = date(year, month, last_day)
        elif year:
            date_from = date(year, 1, 1)
            date_to = date(year, 12, 31)

        try:
            with get_session(_get_factory()) as db:
                txs = TransactionService(db).list(
                    account_id=account_id,
                    category=category,
                    date_from=date_from,
                    date_to=date_to,
                    limit=200,
                )
        except Exception:
            empty_fig = go.Figure()
            err = html.Div("Erro ao carregar transações.")
            return (
                metric_card("Receitas", "Erro", color=SUCCESS),
                metric_card("Despesas", "Erro", color=DANGER),
                metric_card("Saldo do Mês", "Erro", color=PRIMARY),
                err,
                empty_fig,
            )

        income = sum(t.amount for t in txs if t.amount > 0)
        expenses = sum(t.amount for t in txs if t.amount < 0)
        net = income + expenses

        net_color = SUCCESS if net >= 0 else DANGER
        card_income = metric_card("Receitas", fmt_brl(income), color=SUCCESS)
        card_expenses = metric_card("Despesas", fmt_brl(abs(expenses)), color=DANGER)
        card_net = metric_card("Saldo do Mês", fmt_brl(net), color=net_color)

        # Table
        rows = []
        for tx in txs:
            amount_color = SUCCESS if tx.amount > 0 else DANGER
            desc = (tx.description or "")[:30]
            tx_date = tx.transaction_date.strftime("%d/%m/%Y") if tx.transaction_date else "—"
            rows.append(
                html.Tr(
                    [
                        html.Td(tx_date),
                        html.Td(desc),
                        html.Td(tx.category or "—"),
                        html.Td(
                            fmt_brl(tx.amount),
                            style={"color": amount_color, "fontWeight": "600"},
                        ),
                    ]
                )
            )

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr([html.Th("Data"), html.Th("Descrição"), html.Th("Categoria"), html.Th("Valor")])
                ),
                html.Tbody(rows if rows else [html.Tr([html.Td("Nenhuma transação encontrada.", colSpan=4)])]),
            ],
            striped=True,
            hover=True,
            responsive=True,
            size="sm",
        )

        # Pie — only expense categories (amount < 0)
        cat_totals: dict[str, float] = {}
        for tx in txs:
            if tx.amount < 0:
                cat = tx.category or "outros"
                cat_totals[cat] = cat_totals.get(cat, 0) + tx.amount

        if cat_totals:
            labels = list(cat_totals.keys())
            values = [abs(v) for v in cat_totals.values()]
            fig = pie_chart(labels, values, "Despesas por Categoria")
        else:
            fig = go.Figure()
            fig.update_layout(title="Sem despesas no período")

        return card_income, card_expenses, card_net, table, fig
