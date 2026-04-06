from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from src.core.database import get_engine, get_session, init_db, make_session_factory
from src.dashboard.components.cards import metric_card, section_header
from src.dashboard.theme import PRIMARY, SUCCESS

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
            html.H4("🎯 Metas", className="mb-4"),
            dcc.Interval(id="goals-interval", interval=30_000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="goals-active-count"), md=6),
                    dbc.Col(html.Div(id="goals-achieved-count"), md=6),
                ],
                className="mb-3",
            ),
            html.Div(id="goals-list", className="mb-4"),
            section_header("Adicionar Meta"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Input(id="goal-name-input", placeholder="Nome da meta"),
                        md=4,
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="goal-target-input",
                            placeholder="Valor alvo (R$)",
                            type="number",
                            min=0,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="goal-current-input",
                            placeholder="Valor atual (R$)",
                            type="number",
                            min=0,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Button("Adicionar Meta", id="goal-add-btn", color="success"),
                        md=2,
                    ),
                ],
                className="mb-2",
            ),
            html.Div(id="goal-add-feedback"),
        ],
        fluid=True,
    )


def register_callbacks(app):
    @app.callback(
        Output("goals-active-count", "children"),
        Output("goals-achieved-count", "children"),
        Output("goals-list", "children"),
        Input("goals-interval", "n_intervals"),
        Input("goal-add-btn", "n_clicks"),
    )
    def update_goals(n_intervals, n_clicks):
        from src.core.models import Goal

        try:
            with get_session(_get_factory()) as db:
                goals = db.query(Goal).order_by(Goal.created_at.desc()).all()
        except Exception:
            err = html.Div("Erro ao carregar metas.")
            return err, err, err

        active = [g for g in goals if not g.is_achieved]
        achieved = [g for g in goals if g.is_achieved]

        card_active = metric_card("Metas Ativas", str(len(active)), color=PRIMARY, icon="🎯")
        card_achieved = metric_card("Metas Atingidas", str(len(achieved)), color=SUCCESS, icon="✅")

        if not goals:
            goals_ui = html.P("Nenhuma meta cadastrada.", className="text-muted")
        else:
            cards = []
            for g in goals:
                pct = min((g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0.0, 100.0)
                bar_color = "success" if g.is_achieved else "primary"
                cards.append(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Strong(g.name),
                                        html.Span(
                                            f"  {fmt_brl(g.current_amount)} / {fmt_brl(g.target_amount)}",
                                            className="text-muted ms-2",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                dbc.Progress(
                                    value=pct,
                                    label=f"{pct:.0f}%",
                                    color=bar_color,
                                    style={"height": "20px"},
                                ),
                            ]
                        ),
                        className="mb-2 shadow-sm",
                    )
                )
            goals_ui = html.Div(cards)

        return card_active, card_achieved, goals_ui

    @app.callback(
        Output("goal-add-feedback", "children"),
        Input("goal-add-btn", "n_clicks"),
        State("goal-name-input", "value"),
        State("goal-target-input", "value"),
        State("goal-current-input", "value"),
        prevent_initial_call=True,
    )
    def add_goal(n_clicks, name, target, current):
        from src.core.models import Goal

        if not n_clicks:
            return dash.no_update

        if not name or target is None:
            return dbc.Alert("Nome e valor alvo são obrigatórios.", color="warning", dismissable=True)

        try:
            target_f = float(target)
            current_f = float(current) if current is not None else 0.0
            new_goal = Goal(
                name=name,
                target_amount=target_f,
                current_amount=current_f,
                is_achieved=(current_f >= target_f),
            )
            with get_session(_get_factory()) as db:
                db.add(new_goal)
                db.commit()
        except Exception as exc:
            return dbc.Alert(f"Erro ao salvar meta: {exc}", color="danger", dismissable=True)

        return dbc.Alert(f"Meta '{name}' adicionada com sucesso!", color="success", dismissable=True)
