from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html

from src.dashboard import theme
from src.dashboard.layout import create_layout

# Importa as páginas para que fiquem disponíveis no dispatch
import src.dashboard.pages.accounts     as page_accounts
import src.dashboard.pages.transactions as page_transactions
import src.dashboard.pages.investments  as page_investments
import src.dashboard.pages.goals        as page_goals
import src.dashboard.pages.chatbot      as page_chatbot
import src.dashboard.pages.overview     as page_overview

app = dash.Dash(
    __name__,
    external_stylesheets=[getattr(dbc.themes, theme.THEME)],
    suppress_callback_exceptions=True,
    title="Finance Personal",
)
server = app.server
app.layout = create_layout()


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: str):
    if pathname == "/":
        return page_overview.layout()
    if pathname == "/accounts":
        return page_accounts.layout()
    if pathname == "/transactions":
        return page_transactions.layout()
    if pathname == "/investments":
        return page_investments.layout()
    if pathname == "/goals":
        return page_goals.layout()
    if pathname == "/chatbot":
        return page_chatbot.layout()
    return html.H3("Página não encontrada", className="text-center mt-5")


# Registra callbacks de todas as páginas
page_accounts.register_callbacks(app)
page_transactions.register_callbacks(app)
page_investments.register_callbacks(app)
page_goals.register_callbacks(app)
page_chatbot.register_callbacks(app)
page_overview.register_callbacks(app)

if __name__ == "__main__":
    from src.core.config import get_settings
    s = get_settings()
    app.run(host=s.host, port=s.dash_port, debug=True)
