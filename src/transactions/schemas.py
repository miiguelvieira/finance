"""Schemas Pydantic para Transactions."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    account_id: int
    amount: float  # positivo=crédito, negativo=débito
    description: str = Field(..., min_length=1, max_length=255)
    category: str | None = None       # se None, categorizer tenta classificar
    subcategory: str | None = None
    transaction_date: date
    competence_date: date | None = None
    is_recurring: bool = False
    notes: str | None = None
    pluggy_transaction_id: str | None = None


class TransactionOut(BaseModel):
    id: int
    account_id: int
    amount: float
    description: str
    category: str
    subcategory: str | None
    transaction_date: date
    competence_date: date | None
    is_recurring: bool
    installment_id: int | None
    transfer_ref: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionFilter(BaseModel):
    account_id: int | None = None
    category: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    search: str | None = None
