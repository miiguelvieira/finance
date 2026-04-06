from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from src.core.database import get_engine, get_session, init_db, make_session_factory
from src.dashboard.theme import PRIMARY

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
            html.H4("🤖 Assistente Financeiro", className="mb-2"),
            html.P("Pergunte sobre seu saldo, gastos, investimentos, metas ou impostos."),
            html.Div(
                id="chat-history",
                style={
                    "height": "400px",
                    "overflowY": "auto",
                    "border": "1px solid #ddd",
                    "borderRadius": "8px",
                    "padding": "16px",
                    "backgroundColor": "white",
                    "marginBottom": "16px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Input(
                            id="chat-input",
                            placeholder="Digite sua mensagem...",
                            type="text",
                            debounce=False,
                        ),
                        width=10,
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Enviar",
                            id="chat-send-btn",
                            color="primary",
                            style={"width": "100%"},
                        ),
                        width=2,
                    ),
                ],
                className="mb-2",
            ),
            html.Div(id="chat-intent-badge", className="mb-2"),
            dcc.Store(id="chat-messages-store", data=[]),
            dcc.Interval(id="chat-interval", interval=1000, max_intervals=1),
        ],
        fluid=True,
    )


def register_callbacks(app):
    @app.callback(
        Output("chat-messages-store", "data"),
        Output("chat-input", "value"),
        Output("chat-intent-badge", "children"),
        Input("chat-send-btn", "n_clicks"),
        Input("chat-input", "n_submit"),
        State("chat-input", "value"),
        State("chat-messages-store", "data"),
        prevent_initial_call=True,
    )
    def send_message(n_clicks, n_submit, msg, messages):
        if not msg or not msg.strip():
            return dash.no_update, dash.no_update, dash.no_update

        if n_clicks is None and n_submit is None:
            return dash.no_update, dash.no_update, dash.no_update

        try:
            from src.chatbot.engine import ChatbotEngine

            with get_session(_get_factory()) as db:
                engine = ChatbotEngine(db, "assets/intents.yaml")
                intent = engine._classifier.classify(msg)
                reply = engine.reply(msg)
                db.commit()
        except Exception as exc:
            reply = f"Erro ao processar mensagem: {exc}"
            intent = "erro"

        updated = list(messages or [])
        updated.append({"user": msg, "bot": reply, "intent": intent})

        badge = dbc.Badge(
            f"Intent: {intent}",
            color="secondary",
            pill=True,
        )
        return updated, "", badge

    @app.callback(
        Output("chat-history", "children"),
        Input("chat-messages-store", "data"),
        Input("chat-interval", "n_intervals"),
    )
    def render_history(data, n_intervals):
        messages = list(data or [])

        # Se store vazio mas há histórico no banco, carrega últimas 5 mensagens
        if not messages:
            try:
                from src.core.models import ChatbotHistory

                with get_session(_get_factory()) as db:
                    history = (
                        db.query(ChatbotHistory)
                        .order_by(ChatbotHistory.created_at.desc())
                        .limit(5)
                        .all()
                    )
                    messages = [
                        {"user": h.user_message, "bot": h.bot_response, "intent": h.intent or ""}
                        for h in reversed(history)
                    ]
            except Exception:
                messages = []

        if not messages:
            return html.P("Olá! Como posso ajudar?", className="text-muted")

        bubbles = []
        for entry in messages:
            # Bolha do usuário — direita, fundo azul claro
            bubbles.append(
                html.Div(
                    html.Div(
                        entry["user"],
                        style={
                            "display": "inline-block",
                            "backgroundColor": "#e3f2fd",
                            "color": "#0d47a1",
                            "padding": "8px 14px",
                            "borderRadius": "16px 16px 4px 16px",
                            "maxWidth": "75%",
                            "wordBreak": "break-word",
                        },
                    ),
                    style={"textAlign": "right", "marginBottom": "8px"},
                )
            )
            # Bolha do bot — esquerda, fundo cinza claro, monospace
            bubbles.append(
                html.Div(
                    html.Div(
                        entry["bot"],
                        style={
                            "display": "inline-block",
                            "backgroundColor": "#f5f5f5",
                            "color": "#333",
                            "padding": "8px 14px",
                            "borderRadius": "16px 16px 16px 4px",
                            "maxWidth": "75%",
                            "fontFamily": "monospace",
                            "whiteSpace": "pre-wrap",
                            "wordBreak": "break-word",
                        },
                    ),
                    style={"textAlign": "left", "marginBottom": "8px"},
                )
            )

        return bubbles
