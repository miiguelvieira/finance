"""Inicia FastAPI e Dash em threads de background antes de abrir a janela."""
from __future__ import annotations

import logging
import socket
import threading
import time

logger = logging.getLogger(__name__)


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.25)
    return False


def _run_api(host: str, port: int) -> None:
    import uvicorn
    from src.api.main import app
    uvicorn.run(app, host=host, port=port, log_level="warning")


def _run_dash(host: str, port: int) -> None:
    from src.core.config import get_settings
    from src.dashboard.app import app
    s = get_settings()
    app.run(host=host, port=port, debug=False, use_reloader=False)


def start_servers(api_host: str = "127.0.0.1",
                  api_port: int = 8000,
                  dash_host: str = "127.0.0.1",
                  dash_port: int = 8050) -> str:
    """Sobe FastAPI + Dash em daemons e retorna URL do dashboard."""
    if not _port_open(api_host, api_port):
        t_api = threading.Thread(
            target=_run_api, args=(api_host, api_port), daemon=True
        )
        t_api.start()

    if not _port_open(dash_host, dash_port):
        t_dash = threading.Thread(
            target=_run_dash, args=(dash_host, dash_port), daemon=True
        )
        t_dash.start()

    if not _wait_for_port(dash_host, dash_port, timeout=30):
        raise RuntimeError(
            f"Dashboard nao iniciou em {dash_host}:{dash_port} dentro de 30s"
        )

    return f"http://{dash_host}:{dash_port}"
