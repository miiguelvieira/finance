"""Testes Fase 8 — Desktop launcher (sem iniciar servidores reais)."""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ── 1. Importacoes ────────────────────────────────────────────────────────────
print("\n=== 1. Imports ===\n")

try:
    from desktop.launcher import _port_open, _wait_for_port, start_servers
    report("desktop.launcher importavel", True)
except Exception as e:
    report("desktop.launcher importavel", False, str(e))

try:
    import desktop.main as desktop_main
    report("desktop.main importavel", True)
except Exception as e:
    report("desktop.main importavel", False, str(e))


# ── 2. _port_open ─────────────────────────────────────────────────────────────
print("\n=== 2. _port_open ===\n")

try:
    result_closed = not _port_open("127.0.0.1", 19999)
    report("_port_open porta fechada retorna False", result_closed)
except Exception as e:
    report("_port_open porta fechada retorna False", False, str(e))


# ── 3. _wait_for_port timeout ─────────────────────────────────────────────────
print("\n=== 3. _wait_for_port ===\n")

try:
    t0 = time.monotonic()
    result_timeout = not _wait_for_port("127.0.0.1", 19998, timeout=0.6)
    elapsed = time.monotonic() - t0
    report("_wait_for_port retorna False em porta fechada", result_timeout)
    report("_wait_for_port respeita timeout (~0.6s)", 0.5 <= elapsed <= 2.0,
           f"elapsed={elapsed:.2f}s")
except Exception as e:
    report("_wait_for_port retorna False em porta fechada", False, str(e))
    report("_wait_for_port respeita timeout (~0.6s)", False, str(e))


# ── 4. _wait_for_port sucesso ─────────────────────────────────────────────────
print("\n=== 4. _wait_for_port sucesso ===\n")

import socket


def _open_server(port: int, ready_event: threading.Event):
    """Sobe um TCP listener temporario na porta dada."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        ready_event.set()
        s.settimeout(3.0)
        try:
            s.accept()
        except Exception:
            pass


try:
    port = 19997
    ready = threading.Event()
    t = threading.Thread(target=_open_server, args=(port, ready), daemon=True)
    t.start()
    ready.wait(timeout=2.0)
    found = _wait_for_port("127.0.0.1", port, timeout=3.0)
    report("_wait_for_port detecta porta aberta", found)
except Exception as e:
    report("_wait_for_port detecta porta aberta", False, str(e))


# ── 5. start_servers (mocked) ─────────────────────────────────────────────────
print("\n=== 5. start_servers (mocked) ===\n")

try:
    with patch("desktop.launcher._port_open", return_value=True), \
         patch("desktop.launcher._wait_for_port", return_value=True):
        url = start_servers(api_host="127.0.0.1", api_port=8000,
                            dash_host="127.0.0.1", dash_port=8050)
        report("start_servers retorna URL", isinstance(url, str) and url.startswith("http"))
        report("start_servers URL contem porta 8050", ":8050" in url)
except Exception as e:
    report("start_servers retorna URL", False, str(e))
    report("start_servers URL contem porta 8050", False, str(e))


# ── 6. start_servers lanca se dash nao sobe ───────────────────────────────────
print("\n=== 6. start_servers falha graciosamente ===\n")

try:
    with patch("desktop.launcher._port_open", return_value=False), \
         patch("desktop.launcher._wait_for_port", return_value=False), \
         patch("desktop.launcher.threading.Thread") as mock_thread:
        mock_thread.return_value.start = MagicMock()
        try:
            start_servers()
            report("start_servers lanca RuntimeError se dash nao sobe", False,
                   "deveria ter lancado")
        except RuntimeError as exc:
            report("start_servers lanca RuntimeError se dash nao sobe", True,
                   str(exc)[:60])
except Exception as e:
    report("start_servers lanca RuntimeError se dash nao sobe", False, str(e))


# ── 7. desktop/main.py tem funcao main() ──────────────────────────────────────
print("\n=== 7. desktop.main estrutura ===\n")

try:
    report("desktop.main tem funcao main()", callable(getattr(desktop_main, "main", None)))
except Exception as e:
    report("desktop.main tem funcao main()", False, str(e))


# ── 8. build.spec existe ──────────────────────────────────────────────────────
print("\n=== 8. Artefatos ===\n")

spec_path = ROOT / "desktop" / "build.spec"
launcher_path = ROOT / "desktop" / "launcher.py"
main_path = ROOT / "desktop" / "main.py"

report("desktop/build.spec existe",  spec_path.exists())
report("desktop/launcher.py existe", launcher_path.exists())
report("desktop/main.py existe",     main_path.exists())

spec_content = spec_path.read_text(encoding="utf-8")
report("build.spec menciona console=False", "console=False" in spec_content)
report("build.spec inclui assets/",         "assets" in spec_content)
report("build.spec inclui hiddenimports",   "hiddenimports" in spec_content)


# ── 9. Splash screen ──────────────────────────────────────────────────────────
print("\n=== 9. Splash screen ===\n")

splash_path = ROOT / "desktop" / "splash.html"
report("desktop/splash.html existe", splash_path.exists())

if splash_path.exists():
    splash_content = splash_path.read_text(encoding="utf-8")
    report("splash tem spinner animado",  "animation" in splash_content or "spinner" in splash_content)
    report("splash tem fundo escuro",     "#0f172a" in splash_content or "0f172a" in splash_content)
    report("splash menciona Finance",     "Finance" in splash_content)

main_content = main_path.read_text(encoding="utf-8")
report("main.py usa splash.html",       "splash.html" in main_content or "SPLASH" in main_content)
report("main.py tem load_url",          "load_url" in main_content)


# ── 10. CI/CD ─────────────────────────────────────────────────────────────────
print("\n=== 10. CI/CD ===\n")

ci_path = ROOT / ".github" / "workflows" / "ci.yml"
report(".github/workflows/ci.yml existe", ci_path.exists())

if ci_path.exists():
    ci_content = ci_path.read_text(encoding="utf-8")
    report("CI roda em windows-latest",      "windows-latest" in ci_content)
    report("CI executa test_dashboard.py",   "test_dashboard" in ci_content)
    report("CI tem job build-exe",           "build-exe" in ci_content)
    report("CI tem job release",             "release" in ci_content)


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
