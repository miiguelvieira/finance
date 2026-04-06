"""Testes E2E com Playwright — requer `-m e2e` para rodar."""

import sys
import threading
import time
from pathlib import Path

import pytest

# Skip gracefully se playwright não estiver instalado
playwright = pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DASH_PORT = 8051
API_PORT = 8001
DASH_URL = f"http://127.0.0.1:{DASH_PORT}"
API_URL = f"http://127.0.0.1:{API_PORT}"


# ---------------------------------------------------------------------------
# Fixtures de sessão — ssobem os servidores uma vez por sessão
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _api_server():
    """Sobe FastAPI em :8001 numa thread daemon."""
    import uvicorn
    from src.api.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host="127.0.0.1",
        port=API_PORT,
        log_level="error",
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)
    yield
    server.should_exit = True


@pytest.fixture(scope="session")
def _dash_server(_api_server):
    """Sobe Dash em :8051 numa thread daemon (depende da API estar no ar)."""
    from src.dashboard.app import app as dash_app

    t = threading.Thread(
        target=dash_app.run,
        kwargs={"host": "127.0.0.1", "port": DASH_PORT, "debug": False},
        daemon=True,
    )
    t.start()
    time.sleep(2)
    yield


@pytest.fixture(scope="session")
def browser_page(_dash_server):
    """Página Chromium headless reutilizada em todos os testes da sessão."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


# ---------------------------------------------------------------------------
# Testes de navegação básica
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_overview_page_loads(browser_page):
    """Página inicial carrega e exibe ao menos um elemento KPI."""
    browser_page.goto(DASH_URL + "/", wait_until="networkidle")
    # Aguarda o callback popular o conteúdo
    browser_page.wait_for_selector("#page-content", timeout=10_000)
    content = browser_page.inner_text("#page-content")
    assert content.strip() != "", "page-content está vazio"


@pytest.mark.e2e
def test_sidebar_navigation(browser_page):
    """Clicar em 'Contas' na sidebar navega para /accounts."""
    browser_page.goto(DASH_URL + "/", wait_until="networkidle")
    browser_page.wait_for_selector("#sidebar", timeout=10_000)
    # Clica no link de Contas pelo href
    browser_page.click("a[href='/accounts']")
    browser_page.wait_for_url("**/accounts", timeout=8_000)
    assert "/accounts" in browser_page.url


@pytest.mark.e2e
def test_accounts_page_loads(browser_page):
    """Página /accounts renderiza sem erro — div de contas ou card presente."""
    browser_page.goto(DASH_URL + "/accounts", wait_until="networkidle")
    browser_page.wait_for_selector("#accounts-table", timeout=10_000)
    # Verifica que o contêiner principal da página foi renderizado
    assert browser_page.is_visible("#accounts-table")


# ---------------------------------------------------------------------------
# Testes de interações
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_chatbot_page_loads(browser_page):
    """Página /chatbot carrega e exibe o campo de input de texto."""
    browser_page.goto(DASH_URL + "/chatbot", wait_until="networkidle")
    browser_page.wait_for_selector("#chat-input", timeout=10_000)
    assert browser_page.is_visible("#chat-input")


@pytest.mark.e2e
def test_investments_page_loads(browser_page):
    """Página /investimentos carrega sem retornar erro 500."""
    response = browser_page.goto(DASH_URL + "/investments", wait_until="networkidle")
    # Verifica que o Dash não exibiu tela de erro (status sempre 200 no Dash SPA)
    assert response.status == 200
    browser_page.wait_for_selector("#page-content", timeout=10_000)
    content = browser_page.inner_text("#page-content")
    # Se houve erro 500 interno, Dash exibe "Internal Server Error"
    assert "Internal Server Error" not in content
