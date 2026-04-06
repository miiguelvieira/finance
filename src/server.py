"""Entry point para deploy em cloud (Render, Railway, etc.).
Sobe FastAPI em thread daemon e roda Dash no processo principal.
"""
from __future__ import annotations

import os
import threading
import uvicorn


def _run_api(host: str, port: int) -> None:
    from src.api.main import app
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    api_port = int(os.environ.get("API_PORT", "8000"))
    dash_port = int(os.environ.get("DASH_PORT", "8050"))
    host = os.environ.get("HOST", "0.0.0.0")

    t = threading.Thread(target=_run_api, args=(host, api_port), daemon=True)
    t.start()

    from src.core.config import get_settings
    from src.dashboard.app import app as dash_app
    dash_app.run(host=host, port=dash_port, debug=False, use_reloader=False)
