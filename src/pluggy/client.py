"""PluggyClient — wrapper HTTP para a API Pluggy (Open Banking BR)."""

from __future__ import annotations

import httpx

from src.core.exceptions import PluggyAuthError
from src.pluggy.schemas import (
    PluggyAccount, PluggyAuthResponse,
    PluggyInvestment, PluggyTransactionPage,
)

_BASE_URL = "https://api.pluggy.ai"


class PluggyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = _BASE_URL,
        timeout: float = 15.0,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._api_key: str | None = None

    # ── Autenticação ──────────────────────────────────────────────────────────

    def authenticate(self) -> str:
        """POST /auth — obtém API key de curta duração."""
        resp = httpx.post(
            f"{self._base_url}/auth",
            json={"clientId": self._client_id, "clientSecret": self._client_secret},
            timeout=self._timeout,
        )
        if resp.status_code != 200:
            raise PluggyAuthError(
                f"Falha de autenticacao Pluggy: {resp.status_code} {resp.text[:200]}"
            )
        self._api_key = PluggyAuthResponse(**resp.json()).apiKey
        return self._api_key

    @property
    def is_authenticated(self) -> bool:
        return self._api_key is not None

    def _headers(self) -> dict:
        if not self._api_key:
            raise PluggyAuthError("Nao autenticado. Chame authenticate() primeiro.")
        return {"X-API-KEY": self._api_key, "Content-Type": "application/json"}

    # ── Contas ────────────────────────────────────────────────────────────────

    def get_accounts(self, item_id: str) -> list[PluggyAccount]:
        resp = httpx.get(
            f"{self._base_url}/accounts",
            params={"itemId": item_id},
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return [PluggyAccount(**a) for a in resp.json().get("results", [])]

    # ── Transações ────────────────────────────────────────────────────────────

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int = 1,
        page_size: int = 500,
    ) -> PluggyTransactionPage:
        params: dict = {"accountId": account_id, "page": page, "pageSize": page_size}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        resp = httpx.get(
            f"{self._base_url}/transactions",
            params=params,
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return PluggyTransactionPage(**resp.json())

    def get_all_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list:
        """Busca todas as paginas de transacoes."""
        page = 1
        all_txs = []
        while True:
            result = self.get_transactions(account_id, from_date, to_date, page=page)
            all_txs.extend(result.results)
            if page >= result.totalPages:
                break
            page += 1
        return all_txs

    # ── Investimentos ─────────────────────────────────────────────────────────

    def get_investments(self, item_id: str) -> list[PluggyInvestment]:
        resp = httpx.get(
            f"{self._base_url}/investments",
            params={"itemId": item_id},
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return [PluggyInvestment(**i) for i in resp.json().get("results", [])]
