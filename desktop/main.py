"""Ponto de entrada do executável desktop — splash screen + pywebview."""
from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

SPLASH_PATH = Path(__file__).resolve().parent / "splash.html"
SPLASH_URL  = SPLASH_PATH.as_uri()


def main() -> None:
    import webview

    # Abre a janela imediatamente com a splash screen
    window = webview.create_window(
        title="Finance Personal",
        url=SPLASH_URL,
        width=1280,
        height=800,
        min_size=(900, 600),
        text_select=True,
        background_color="#0f172a",
    )

    def _boot(win):
        """Sobe servidores em background e redireciona quando prontos."""
        try:
            from desktop.launcher import start_servers
            logger.info("Iniciando servidores...")
            url = start_servers()
            logger.info("Dashboard disponivel em %s", url)
            win.load_url(url)
        except Exception as exc:
            logger.exception("Falha ao iniciar servidores: %s", exc)
            # Mostra erro na splash em vez de fechar silenciosamente
            win.evaluate_js(
                f"document.querySelector('.status').textContent = 'Erro: {exc!s:.80}';"
            )

    try:
        webview.start(_boot, window, debug=False)
    except Exception as exc:
        logger.exception("Falha ao abrir janela: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
