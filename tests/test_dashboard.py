"""Testes Fase 7 — Dashboard Dash (theme, components, layout, pages)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, passed))


def find_id(component, target_id):
    """Busca recursiva de componente Dash por id."""
    if hasattr(component, "id") and component.id == target_id:
        return True
    children = getattr(component, "children", None)
    if children is None:
        return False
    if isinstance(children, list):
        return any(find_id(c, target_id) for c in children)
    return find_id(children, target_id)


# ── 1. theme.py ───────────────────────────────────────────────────────────────
print("\n=== 1. theme.py ===\n")

from src.dashboard.theme import (
    DANGER, FONT_FAMILY, PRIMARY, SIDEBAR_BG, SIDEBAR_WIDTH, SUCCESS, THEME, WARNING,
)

report("THEME e string nao-vazia",        isinstance(THEME, str) and len(THEME) > 0)
report("PRIMARY comeca com #",            PRIMARY.startswith("#"))
report("SUCCESS comeca com #",            SUCCESS.startswith("#"))
report("DANGER comeca com #",             DANGER.startswith("#"))
report("WARNING comeca com #",            WARNING.startswith("#"))
report("SIDEBAR_BG comeca com #",         SIDEBAR_BG.startswith("#"))
report("SIDEBAR_WIDTH termina com px",    SIDEBAR_WIDTH.endswith("px"))
report("FONT_FAMILY e string nao-vazia",  isinstance(FONT_FAMILY, str) and len(FONT_FAMILY) > 0)


# ── 2. components/charts.py ──────────────────────────────────────────────────
print("\n=== 2. components/charts.py ===\n")

import plotly.graph_objects as go
from src.dashboard.components.charts import bar_chart, line_chart, pie_chart

fig_bar = bar_chart([1, 2, 3], [4, 5, 6], "Teste Bar")
report("bar_chart retorna go.Figure",     isinstance(fig_bar, go.Figure))
report("bar_chart tem >= 1 trace",        len(fig_bar.data) >= 1)
report("bar_chart layout.margin.l = 10", fig_bar.layout.margin.l == 10)
report("bar_chart titulo correto",        fig_bar.layout.title.text == "Teste Bar")

fig_pie = pie_chart(["A", "B"], [10, 20], "Teste Pie")
report("pie_chart retorna go.Figure",     isinstance(fig_pie, go.Figure))
report("pie_chart tem >= 1 trace",        len(fig_pie.data) >= 1)

fig_line = line_chart([1, 2, 3], [10, 20, 15], "Teste Line")
report("line_chart retorna go.Figure",    isinstance(fig_line, go.Figure))
report("line_chart tem >= 1 trace",       len(fig_line.data) >= 1)

# Cor customizada
fig_c = bar_chart([1], [1], "X", color="#ff0000")
report("bar_chart aceita cor customizada", isinstance(fig_c, go.Figure))


# ── 3. components/cards.py ───────────────────────────────────────────────────
print("\n=== 3. components/cards.py ===\n")

import dash_bootstrap_components as dbc
from dash import html
from src.dashboard.components.cards import metric_card, section_header

try:
    card = metric_card("Titulo", "R$ 100,00")
    report("metric_card retorna dbc.Card",    isinstance(card, dbc.Card))
except Exception as e:
    report("metric_card retorna dbc.Card",    False, str(e))

try:
    card_icon = metric_card("Titulo", "100", icon="x")
    report("metric_card com icon nao lanca",  True)
except Exception as e:
    report("metric_card com icon nao lanca",  False, str(e))

try:
    card_sub = metric_card("Titulo", "100", subtitle="Sub")
    report("metric_card com subtitle nao lanca", True)
except Exception as e:
    report("metric_card com subtitle nao lanca", False, str(e))

try:
    hdr = section_header("Secao Teste")
    report("section_header retorna html.H5",  isinstance(hdr, html.H5))
    report("section_header contem texto",      "Secao Teste" in str(hdr.children))
except Exception as e:
    report("section_header retorna html.H5",  False, str(e))
    report("section_header contem texto",      False, str(e))


# ── 4. layout.py ─────────────────────────────────────────────────────────────
print("\n=== 4. layout.py ===\n")

try:
    from src.dashboard.layout import create_layout
    layout_root = create_layout()
    report("create_layout nao lanca excecao",  True)
    report("create_layout retorna html.Div",   isinstance(layout_root, html.Div))
    report("layout tem id=sidebar",            find_id(layout_root, "sidebar"))
    report("layout tem id=page-content",       find_id(layout_root, "page-content"))
    report("layout tem id=url",                find_id(layout_root, "url"))
except Exception as e:
    for name in [
        "create_layout nao lanca excecao",
        "create_layout retorna html.Div",
        "layout tem id=sidebar",
        "layout tem id=page-content",
        "layout tem id=url",
    ]:
        report(name, False, str(e))


# ── 5. pages/accounts.py ─────────────────────────────────────────────────────
print("\n=== 5. pages/accounts.py ===\n")

try:
    from src.dashboard.pages.accounts import fmt_brl as acc_fmt_brl
    from src.dashboard.pages.accounts import layout as accounts_layout

    report("fmt_brl(1234.56) correto",    acc_fmt_brl(1234.56) == "R$ 1.234,56")
    report("fmt_brl(0.0) correto",        acc_fmt_brl(0.0) == "R$ 0,00")
    report("fmt_brl(1000.0) correto",     acc_fmt_brl(1000.0) == "R$ 1.000,00")
    report("fmt_brl negativo nao lanca",  isinstance(acc_fmt_brl(-500.0), str))

    pg = accounts_layout()
    report("accounts layout() nao lanca",   True)
    report("accounts layout() tem children", hasattr(pg, "children"))
    report("accounts tem id accounts-interval", find_id(pg, "accounts-interval"))
    report("accounts tem id accounts-table",    find_id(pg, "accounts-table"))
    report("accounts tem id accounts-pie-chart", find_id(pg, "accounts-pie-chart"))
except Exception as e:
    for name in [
        "fmt_brl(1234.56) correto", "fmt_brl(0.0) correto",
        "fmt_brl(1000.0) correto", "fmt_brl negativo nao lanca",
        "accounts layout() nao lanca", "accounts layout() tem children",
        "accounts tem id accounts-interval", "accounts tem id accounts-table",
        "accounts tem id accounts-pie-chart",
    ]:
        report(name, False, str(e))


# ── 6. pages/transactions.py ─────────────────────────────────────────────────
print("\n=== 6. pages/transactions.py ===\n")

try:
    from src.dashboard.pages.transactions import layout as transactions_layout

    pg = transactions_layout()
    report("transactions layout() nao lanca",    True)
    report("transactions layout() tem children", hasattr(pg, "children"))
    report("transactions tem id tx-account-filter", find_id(pg, "tx-account-filter"))
    report("transactions tem id tx-filter-btn",     find_id(pg, "tx-filter-btn"))
    report("transactions tem id tx-table",          find_id(pg, "tx-table"))
    report("transactions tem id tx-category-pie",   find_id(pg, "tx-category-pie"))
except Exception as e:
    for name in [
        "transactions layout() nao lanca", "transactions layout() tem children",
        "transactions tem id tx-account-filter", "transactions tem id tx-filter-btn",
        "transactions tem id tx-table", "transactions tem id tx-category-pie",
    ]:
        report(name, False, str(e))


# ── 7. pages/investments.py ──────────────────────────────────────────────────
print("\n=== 7. pages/investments.py ===\n")

try:
    from src.dashboard.pages.investments import layout as investments_layout

    pg = investments_layout()
    report("investments layout() nao lanca",    True)
    report("investments layout() tem children", hasattr(pg, "children"))
    report("investments tem id inv-principal",       find_id(pg, "inv-principal"))
    report("investments tem id inv-current",         find_id(pg, "inv-current"))
    report("investments tem id inv-gain",            find_id(pg, "inv-gain"))
    report("investments tem id inv-allocation-pie",  find_id(pg, "inv-allocation-pie"))
    report("investments tem id inv-table",           find_id(pg, "inv-table"))
except Exception as e:
    for name in [
        "investments layout() nao lanca", "investments layout() tem children",
        "investments tem id inv-principal", "investments tem id inv-current",
        "investments tem id inv-gain", "investments tem id inv-allocation-pie",
        "investments tem id inv-table",
    ]:
        report(name, False, str(e))


# ── 8. pages/goals.py ────────────────────────────────────────────────────────
print("\n=== 8. pages/goals.py ===\n")

try:
    from src.dashboard.pages.goals import layout as goals_layout

    pg = goals_layout()
    report("goals layout() nao lanca",    True)
    report("goals layout() tem children", hasattr(pg, "children"))
    report("goals tem id goals-active-count",   find_id(pg, "goals-active-count"))
    report("goals tem id goals-achieved-count", find_id(pg, "goals-achieved-count"))
    report("goals tem id goals-list",           find_id(pg, "goals-list"))
    report("goals tem id goal-add-btn",         find_id(pg, "goal-add-btn"))
except Exception as e:
    for name in [
        "goals layout() nao lanca", "goals layout() tem children",
        "goals tem id goals-active-count", "goals tem id goals-achieved-count",
        "goals tem id goals-list", "goals tem id goal-add-btn",
    ]:
        report(name, False, str(e))


# ── 9. pages/chatbot.py ──────────────────────────────────────────────────────
print("\n=== 9. pages/chatbot.py ===\n")

try:
    from src.dashboard.pages.chatbot import layout as chatbot_layout

    pg = chatbot_layout()
    report("chatbot layout() nao lanca",    True)
    report("chatbot layout() tem children", hasattr(pg, "children"))
    report("chatbot tem id chat-history",       find_id(pg, "chat-history"))
    report("chatbot tem id chat-input",         find_id(pg, "chat-input"))
    report("chatbot tem id chat-send-btn",      find_id(pg, "chat-send-btn"))
    report("chatbot tem id chat-messages-store", find_id(pg, "chat-messages-store"))
    report("chatbot tem id chat-intent-badge",  find_id(pg, "chat-intent-badge"))
except Exception as e:
    for name in [
        "chatbot layout() nao lanca", "chatbot layout() tem children",
        "chatbot tem id chat-history", "chatbot tem id chat-input",
        "chatbot tem id chat-send-btn", "chatbot tem id chat-messages-store",
        "chatbot tem id chat-intent-badge",
    ]:
        report(name, False, str(e))


# ── 10. pages/overview.py ────────────────────────────────────────────────────
print("\n=== 10. pages/overview.py ===\n")

try:
    from src.dashboard.pages.overview import layout as overview_layout

    pg = overview_layout()
    report("overview layout() nao lanca",    True)
    report("overview layout() tem children", hasattr(pg, "children"))
    report("overview tem id overview-interval",       find_id(pg, "overview-interval"))
    report("overview tem id overview-net-worth",      find_id(pg, "overview-net-worth"))
    report("overview tem id overview-income",         find_id(pg, "overview-income"))
    report("overview tem id overview-expenses",       find_id(pg, "overview-expenses"))
    report("overview tem id overview-yield",          find_id(pg, "overview-yield"))
    report("overview tem id overview-balance-chart",  find_id(pg, "overview-balance-chart"))
    report("overview tem id overview-allocation-pie", find_id(pg, "overview-allocation-pie"))
    report("overview tem id overview-alerts",         find_id(pg, "overview-alerts"))
except Exception as e:
    for name in [
        "overview layout() nao lanca", "overview layout() tem children",
        "overview tem id overview-interval", "overview tem id overview-net-worth",
        "overview tem id overview-income", "overview tem id overview-expenses",
        "overview tem id overview-yield", "overview tem id overview-balance-chart",
        "overview tem id overview-allocation-pie", "overview tem id overview-alerts",
    ]:
        report(name, False, str(e))


# ── 11. theme.py novos tokens ─────────────────────────────────────────────────
print("\n=== 11. theme.py tokens adicionais ===\n")

try:
    from src.dashboard.theme import INFO, PAGE_BG, SECONDARY
    report("SECONDARY comeca com #", SECONDARY.startswith("#"))
    report("INFO comeca com #",      INFO.startswith("#"))
    report("PAGE_BG comeca com #",   PAGE_BG.startswith("#"))
except ImportError as e:
    report("SECONDARY comeca com #", False, str(e))
    report("INFO comeca com #",      False, str(e))
    report("PAGE_BG comeca com #",   False, str(e))


# ── 12. metric_card com delta ────────────────────────────────────────────────
print("\n=== 12. metric_card delta ===\n")

try:
    from src.dashboard.components.cards import metric_card as mc
    card_delta = mc("Titulo", "R$ 100", delta="+5% este mes", delta_positive=True)
    report("metric_card com delta nao lanca", True)
    report("metric_card delta retorna dbc.Card", isinstance(card_delta, dbc.Card))
    card_neg = mc("Titulo", "R$ 100", delta="-2% este mes", delta_positive=False)
    report("metric_card delta negativo nao lanca", True)
except Exception as e:
    report("metric_card com delta nao lanca",      False, str(e))
    report("metric_card delta retorna dbc.Card",   False, str(e))
    report("metric_card delta negativo nao lanca", False, str(e))


# ── Resumo ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
print(f"  TOTAL: {passed} passed / {failed} failed / {len(results)} tests")
if failed:
    print("\n  Falhas:")
    for name, ok in results:
        if not ok:
            print(f"    - {name}")
print("=" * 55)

sys.exit(0 if failed == 0 else 1)
