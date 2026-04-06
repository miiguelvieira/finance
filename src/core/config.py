"""Configuração centralizada via Pydantic Settings + config.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(default="sqlite:///data/finance.db")

    # Pluggy Open Banking
    pluggy_api_key: str = Field(default="")
    pluggy_client_secret: str = Field(default="")
    pluggy_sandbox: bool = Field(default=True)

    # Server
    dash_port: int = Field(default=8050)
    api_port: int = Field(default=8000)
    host: str = Field(default="127.0.0.1")

    # Runtime (populated from config.yaml at startup)
    _yaml: dict = {}

    def yaml(self) -> dict:
        return self._yaml

    def get(self, *keys: str, default=None):
        """Acessa valores aninhados do config.yaml: settings.get('tax', 'renda_fixa_rate')."""
        node = self._yaml
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k, default)
        return node


@lru_cache(maxsize=1)
def get_settings(config_path: str = "config.yaml") -> Settings:
    settings = Settings()
    yaml_data = _load_yaml(Path(config_path))
    settings._yaml = yaml_data

    # Override server fields from yaml if not set via env
    srv = yaml_data.get("server", {})
    if srv.get("dash_port"):
        object.__setattr__(settings, "dash_port", srv["dash_port"])
    if srv.get("api_port"):
        object.__setattr__(settings, "api_port", srv["api_port"])
    if srv.get("host"):
        object.__setattr__(settings, "host", srv["host"])

    db = yaml_data.get("database", {})
    if db.get("path") and settings.database_url == "sqlite:///data/finance.db":
        object.__setattr__(settings, "database_url", f"sqlite:///{db['path']}")

    return settings
