"""Classificacao de intencoes via keyword matching."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml


def _normalize(text: str) -> str:
    """Remove acentos e converte para minusculo."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class IntentClassifier:
    def __init__(self, yaml_path: str = "assets/intents.yaml"):
        raw = self._load(yaml_path)
        self._patterns: dict[str, list[re.Pattern]] = {}
        for intent, cfg in raw.get("intents", {}).items():
            self._patterns[intent] = [
                re.compile(r"\b" + re.escape(_normalize(p)) + r"\b")
                for p in cfg.get("patterns", [])
            ]

    @staticmethod
    def _load(path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {}
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def known_intents(self) -> list[str]:
        return list(self._patterns.keys())

    def classify(self, text: str) -> str:
        """Retorna a intent com mais matches, ou 'desconhecido'."""
        norm = _normalize(text)
        scores: dict[str, int] = {}
        for intent, patterns in self._patterns.items():
            scores[intent] = sum(1 for p in patterns if p.search(norm))

        best = max(scores, key=lambda k: scores[k]) if scores else "desconhecido"
        return best if scores.get(best, 0) > 0 else "desconhecido"
