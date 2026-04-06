"""Schemas Pydantic para respostas da API Pluggy."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PluggyAuthResponse(BaseModel):
    apiKey: str


class PluggyAccount(BaseModel):
    id: str
    itemId: str
    name: str
    number: str | None = None
    marketingName: str | None = None
    balance: float
    currencyCode: str = "BRL"
    type: str        # BANK, CREDIT
    subtype: str     # CHECKING_ACCOUNT, SAVINGS_ACCOUNT, CREDIT_CARD, etc.


class PluggyTransaction(BaseModel):
    id: str
    accountId: str
    date: datetime
    description: str
    amount: float
    currencyCode: str = "BRL"
    type: str        # CREDIT, DEBIT
    category: str | None = None


class PluggyTransactionPage(BaseModel):
    total: int
    totalPages: int
    page: int
    results: list[PluggyTransaction]


class PluggyInvestment(BaseModel):
    id: str
    itemId: str
    type: str
    name: str
    number: str | None = None
    balance: float
    currencyCode: str = "BRL"
    purchase_date: date | None = None
    annualRate: float | None = None
    lastMonthRate: float | None = None
    lastTwelveMonthsRate: float | None = None
    maturity_date: date | None = None
    issuer: str | None = None
    issuerCNPJ: str | None = None
    isinCode: str | None = None
    quantity: float | None = None
    taxes: float | None = None
    amountProfit: float | None = None
    amountWithdrawal: float | None = None


class SyncResult(BaseModel):
    accounts_created: int = 0
    accounts_updated: int = 0
    transactions_created: int = 0
    transactions_skipped: int = 0
    errors: list[str] = Field(default_factory=list)

    def merge(self, other: "SyncResult") -> None:
        self.accounts_created += other.accounts_created
        self.accounts_updated += other.accounts_updated
        self.transactions_created += other.transactions_created
        self.transactions_skipped += other.transactions_skipped
        self.errors.extend(other.errors)
