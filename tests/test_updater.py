"""Testes Fase 10 — Auto-update via GitHub Releases."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def report(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, passed))


# ── Importação ────────────────────────────────────────────────────────────────
print("\n=== 1. Imports ===\n")

try:
    from src.core.updater import (
        UpdateInfo,
        check_for_update,
        download_and_apply,
        get_current_version,
    )
    report("src.core.updater importavel", True)
except Exception as e:
    report("src.core.updater importavel", False, str(e))
    print("Abortando — modulo nao importavel.")
    sys.exit(1)


# ── get_current_version ───────────────────────────────────────────────────────
print("\n=== 2. get_current_version ===\n")

try:
    version = get_current_version("config.yaml")
    report("get_current_version le config.yaml", isinstance(version, str) and version != "")
    report("get_current_version retorna semver valido", len(version.split(".")) == 3,
           f"version={version}")
except Exception as e:
    report("get_current_version le config.yaml", False, str(e))
    report("get_current_version retorna semver valido", False, str(e))

try:
    # Arquivo inexistente → fallback "0.0.0"
    v_fallback = get_current_version("nao_existe.yaml")
    report("get_current_version fallback em arquivo inexistente", v_fallback == "0.0.0",
           f"retornou={v_fallback}")
except Exception as e:
    report("get_current_version fallback em arquivo inexistente", False, str(e))


# ── check_for_update: sem update ─────────────────────────────────────────────
print("\n=== 3. check_for_update — sem update ===\n")

_mock_response_same = MagicMock()
_mock_response_same.status_code = 200
_mock_response_same.json.return_value = {
    "tag_name": "v1.0.0",
    "body": "Sem mudancas.",
    "html_url": "https://github.com/miguel/finance/releases/tag/v1.0.0",
    "assets": [],
}

try:
    with patch("src.core.updater.get_current_version", return_value="1.0.0"), \
         patch("requests.get", return_value=_mock_response_same):
        result = check_for_update("miguel/finance")
        report("sem update retorna None (versao igual)", result is None)
except Exception as e:
    report("sem update retorna None (versao igual)", False, str(e))

_mock_response_older = MagicMock()
_mock_response_older.status_code = 200
_mock_response_older.json.return_value = {
    "tag_name": "v0.9.0",
    "body": "Versao antiga.",
    "html_url": "https://github.com/miguel/finance/releases/tag/v0.9.0",
    "assets": [],
}

try:
    with patch("src.core.updater.get_current_version", return_value="1.0.0"), \
         patch("requests.get", return_value=_mock_response_older):
        result = check_for_update("miguel/finance")
        report("sem update retorna None (versao remota menor)", result is None)
except Exception as e:
    report("sem update retorna None (versao remota menor)", False, str(e))


# ── check_for_update: com update ─────────────────────────────────────────────
print("\n=== 4. check_for_update — com update ===\n")

_mock_response_new = MagicMock()
_mock_response_new.status_code = 200
_mock_response_new.json.return_value = {
    "tag_name": "v2.0.0",
    "body": "Nova versao com melhorias.",
    "html_url": "https://github.com/miguel/finance/releases/tag/v2.0.0",
    "assets": [
        {
            "name": "finance.exe",
            "browser_download_url": "https://github.com/miguel/finance/releases/download/v2.0.0/finance.exe",
        }
    ],
}

try:
    with patch("src.core.updater.get_current_version", return_value="1.0.0"), \
         patch("requests.get", return_value=_mock_response_new):
        result = check_for_update("miguel/finance")
        report("com update retorna UpdateInfo", isinstance(result, UpdateInfo))
        if isinstance(result, UpdateInfo):
            report("UpdateInfo.version correto", result.version == "2.0.0",
                   f"version={result.version}")
            report("UpdateInfo.url aponta para .exe",
                   result.url.endswith(".exe"), f"url={result.url}")
            report("UpdateInfo.notes nao vazio", bool(result.notes))
except Exception as e:
    report("com update retorna UpdateInfo", False, str(e))
    report("UpdateInfo.version correto", False, str(e))
    report("UpdateInfo.url aponta para .exe", False, str(e))
    report("UpdateInfo.notes nao vazio", False, str(e))


# ── check_for_update: falha de rede ──────────────────────────────────────────
print("\n=== 5. check_for_update — falha de rede ===\n")

import requests as _requests_mod

try:
    with patch("requests.get", side_effect=_requests_mod.exceptions.ConnectionError("timeout")):
        result = check_for_update("miguel/finance")
        report("falha de rede retorna None", result is None)
        report("falha de rede nao lanca excecao", True)
except Exception as e:
    report("falha de rede retorna None", False, str(e))
    report("falha de rede nao lanca excecao", False, str(e))

try:
    _mock_404 = MagicMock()
    _mock_404.status_code = 404
    with patch("requests.get", return_value=_mock_404):
        result = check_for_update("miguel/finance")
        report("resposta 404 retorna None", result is None)
except Exception as e:
    report("resposta 404 retorna None", False, str(e))


# ── download_and_apply: falha silenciosa ──────────────────────────────────────
print("\n=== 6. download_and_apply — falha silenciosa ===\n")

try:
    with patch("requests.get", side_effect=Exception("erro de rede")):
        download_and_apply("https://example.com/finance.exe")
        report("download_and_apply falha silenciosamente", True)
except SystemExit:
    # sys.exit(0) é esperado se download funcionar — não deve ocorrer aqui
    report("download_and_apply falha silenciosamente", False, "sys.exit chamado inesperadamente")
except Exception as e:
    report("download_and_apply falha silenciosamente", False, str(e))


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
