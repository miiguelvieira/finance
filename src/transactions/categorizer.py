"""Categorização automática de transações por regras regex.

Regras carregadas de assets/categorization_rules.yaml.
A primeira regra que bater (ordem no YAML) vence.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml


def _normalize(text: str) -> str:
    """Lowercase + remove acentos para matching mais robusto."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _load_rules(rules_path: str | Path | None = None) -> list[tuple[re.Pattern, str, str]]:
    if rules_path is None:
        # Procura o arquivo a partir da raiz do projeto
        candidate = Path(__file__).resolve().parent.parent.parent / "assets" / "categorization_rules.yaml"
        rules_path = candidate

    with open(rules_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    compiled = []
    for pattern, category, subcategory in data.get("rules", []):
        compiled.append((re.compile(pattern, re.IGNORECASE), category, subcategory))
    return compiled


class Categorizer:
    """Classifica descrições de transações em (categoria, subcategoria)."""

    def __init__(self, rules_path: str | Path | None = None):
        self._rules = _load_rules(rules_path)

    def classify(self, description: str) -> tuple[str, str | None]:
        """Retorna (categoria, subcategoria). Fallback: ('outros', None)."""
        normalized = _normalize(description)
        for pattern, category, subcategory in self._rules:
            if pattern.search(normalized):
                return category, subcategory
        return "outros", None

    def reload(self, rules_path: str | Path | None = None) -> None:
        self._rules = _load_rules(rules_path)
