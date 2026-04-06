"""Auto-update via GitHub Releases."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class UpdateInfo:
    version: str
    url: str
    notes: str


def get_current_version(config_path: str = "config.yaml") -> str:
    """Lê versão do config.yaml (chave app.version)."""
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("app", {}).get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def check_for_update(repo: str = "miguel/finance") -> Optional[UpdateInfo]:
    """Consulta GitHub Releases; retorna UpdateInfo se há versão mais nova, ou None."""
    try:
        import requests
        from packaging.version import parse as vparse

        url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None

        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        if not latest:
            return None

        current = get_current_version()
        if vparse(latest) <= vparse(current):
            return None

        # Procura .exe nos assets
        assets = data.get("assets", [])
        exe_url = next(
            (a["browser_download_url"] for a in assets if a["name"].endswith(".exe")),
            data.get("html_url", ""),
        )

        return UpdateInfo(
            version=latest,
            url=exe_url,
            notes=data.get("body", "")[:500],
        )
    except Exception:
        return None


def download_and_apply(url: str) -> None:
    """Baixa o novo .exe para temp e abre; encerra o processo atual."""
    try:
        import requests

        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()

        suffix = Path(url).suffix or ".exe"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in resp.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        subprocess.Popen([tmp_path])  # abre o instalador/novo exe
        sys.exit(0)
    except Exception:
        return
