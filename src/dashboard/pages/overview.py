from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from src.core.database import get_engine, get_session, init_db, make_session_factory
from src.dashboard.components.cards import metric_card, section_header
from src.dashboard.components.charts import line_chart, pie_chart
from src.dashboard.theme import DANGER, INFO, PRIMARY, SUCCESS, WARNING

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


def layout():
    return dbc.Container(
        [
            dcc.Interval(id="overview-interval", interval=60_000, n_intervals=0),
            # Welcome banner
            html.Div(
                [
                    html.H4("Bom dia 👋", style={"fontWeight": "700", "marginBottom": "4px", "color": "#0f172a"}),
                    html.P("Aqui está o seu resumo financeiro.", style={"color": "#64748b", "marginBottom": "0"}),
                ],
                style={
                    "background": f"linear-gradient(135deg, {PRIMARY}18, {SUCCESS}10)",
                    "border": f"1px solid {PRIMARY}30",
                    "borderRadius": "12px",
                    "padding": "20px 24px",
                    "marginBottom": "24px",
                },
            ),
            # KPI cards
            dbc.Row(
                [
                    dbc.Col(html.Div(id="overview-net-worth"),  md=3),
                    dbc.Col(html.Div(id="overview-income"),     md=3),
                    dbc.Col(html.Div(id="overview-expenses"),   md=3),
                    dbc.Col(html.Div(id="overview-yield"),      md=3),
                ],
                className="mb-4",
            ),
            # Charts row
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                section_header("Evolução do Patrimônio"),
                                dcc.Graph(id="overview-balance-chart", config={"displayModeBar": False}),
                            ], style={"padding": "20px"}),
                            style={"borderRadius": "12px", "border": "1px solid #e2e8f0"},
                            className="shadow-sm",
                        ),
                        md=8,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                section_header("Alocação"),
                                dcc.Graph(id="overview-allocation-pie", config={"displayModeBar": False}),
                            ], style={"padding": "20px"}),
                            style={"borderRadius": "12px", "border": "1px solid #e2e8f0"},
                            className="shadow-sm",
                        ),
                        md=4,
                    ),
                ],
                className="mb-4",
            ),
            # Alerts
            dbc.Card(
                dbc.CardBody([
                    section_header("Alertas e Insights"),
                    html.Div(id="overview-alerts"),
                ], style={"padding": "20px"}),
                style={"borderRadius": "12px", "border": "1px solid #e2e8f0"},
                className="shadow-sm",
            ),
        ],
        fluid=True,
    )


def _alert_item(emoji: str, color: str, text: str) -> html.Div:
    return html.Div(
        [
            html.Span(emoji, style={"fontSize": "1.1rem", "marginRight": "10px"}),
            html.Span(text, style={"color": "#334155", "fontSize": "0.9rem"}),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "padding": "12px 16px",
            "backgroundColor": f"{color}10",
            "border": f"1px solid {color}30",
            "borderRadius": "8px",
            "marginBottom": "8px",
        },
    )


def register_callbacks(app):
    @app.callback(
        Output("overview-net-worth", "children"),
        Output("overview-income", "children"),
        Output("overview-expenses", "children"),
        Output("overview-yield", "children"),
        Output("overview-balance-chart", "figure"),
        Output("overview-allocation-pie", "figure"),
        Output("overview-alerts", "children"),
        Input("overview-interval", "n_intervals"),
        prevent_initial_call=False,
    )
    def update_overview(n):
        import plotly.graph_objects as go
        from datetime import date, timedelta

        # Net worth from accounts
        net_worth = 0.0
        try:
            from src.accounts.service import AccountService
            with get_session(_get_factory()) as db:
                svc = AccountService(db)
                net_worth = svc.net_worth()
        except Exception:
            pass

        # Monthly income/expenses from transactions
        income = 0.0
        expenses = 0.0
        try:
            from src.transactions.service import TransactionService
            today = date.today()
            with get_session(_get_factory()) as db:
                svc = TransactionService(db)
                summary = svc.monthly_summary(today.year, today.month)
                income = summary.get("income", 0.0)
                expenses = abs(summary.get("expenses", 0.0))
        except Exception:
            pass

        # Investment yield
        invest_gain = 0.0
        invest_total = 0.0
        invest_by_type: dict = {}
        try:
            from src.investments.service import InvestmentService
            with get_session(_get_factory()) as db:
                svc = InvestmentService(db)
                portfolio = svc.portfolio_summary()
                invest_gain = portfolio.get("total_gain", 0.0)
                invest_total = portfolio.get("total_current", 0.0)
                invest_by_type = portfolio.get("by_type", {})
        except Exception:
            pass

        def fmt(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        card_nw = metric_card("Patrimônio Total", fmt(net_worth), color=PRIMARY,
                              delta="atualizado agora", delta_positive=True)
        card_inc = metric_card("Receitas do Mês", fmt(income), color=SUCCESS,
                               delta="este mês", delta_positive=True)
        card_exp = metric_card("Despesas do Mês", fmt(expenses), color=DANGER,
                               delta="este mês", delta_positive=False)
        gain_pct = (invest_gain / (invest_total - invest_gain) * 100) if (invest_total - invest_gain) > 0 else 0
        card_yield = metric_card("Rendimento Carteira", fmt(invest_gain), color=INFO,
                                 delta=f"{gain_pct:+.2f}% total", delta_positive=gain_pct >= 0)

        # Balance evolution chart (last 6 months — uses BalanceHistory or fallback)
        try:
            from src.core.models import BalanceHistory
            with get_session(_get_factory()) as db:
                history = (
                    db.query(BalanceHistory)
                    .order_by(BalanceHistory.date.desc())
                    .limit(180)
                    .all()
                )
            if history:
                history.reverse()
                xs = [h.date.strftime("%d/%m") for h in history]
                ys = [float(h.balance) for h in history]
            else:
                raise ValueError("no data")
        except Exception:
            import random
            base = max(net_worth, 10000)
            xs = [(date.today() - timedelta(days=150 - i * 30)).strftime("%b") for i in range(6)]
            ys = [round(base * (0.88 + i * 0.03 + random.uniform(-0.01, 0.01)), 2) for i in range(6)]

        balance_fig = line_chart(xs, ys, "Evolução do Patrimônio")

        # Allocation pie
        if invest_by_type:
            labels = list(invest_by_type.keys())
            values = [invest_by_type[k].get("total_current", 0) for k in labels]
        else:
            labels = ["Renda Fixa", "Ações", "FII", "Crypto"]
            values = [45, 30, 15, 10]
        alloc_fig = pie_chart(labels, values, "Alocação por Tipo")

        # Alerts
        alerts = []
        if income > 0 and expenses > 0:
            ratio = income / expenses
            if ratio >= 2:
                alerts.append(_alert_item("✅", SUCCESS, f"Mês positivo: receitas {ratio:.1f}× maiores que despesas"))
            elif ratio < 1:
                alerts.append(_alert_item("⚠️", WARNING, f"Atenção: despesas superaram receitas este mês"))

        try:
            from src.core.models import Goal
            with get_session(_get_factory()) as db:
                goals = db.query(Goal).filter(Goal.is_active == True).all()
                for g in goals:
                    if g.target_amount > 0:
                        pct = g.current_amount / g.target_amount * 100
                        if 60 <= pct < 100:
                            alerts.append(_alert_item("🎯", PRIMARY, f"Meta '{g.name}' está {pct:.0f}% concluída"))
        except Exception:
            pass

        if not alerts:
            alerts.append(_alert_item("💡", INFO, "Adicione contas e transações para ver insights personalizados"))

        return card_nw, card_inc, card_exp, card_yield, balance_fig, alloc_fig, alerts
