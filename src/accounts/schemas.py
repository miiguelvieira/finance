"""Schemas Pydantic para Accounts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    bank_name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., pattern="^(checking|savings|credit_card|investment)$")
    currency: str = Field(default="BRL", max_length=3)
    balance: float = Field(default=0.0)
    credit_limit: float | None = None
    pluggy_account_id: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = None
    bank_name: str | None = None
    balance: float | None = None
    credit_limit: float | None = None
    is_active: bool | None = None


class AccountOut(BaseModel):
    id: int
    name: str
    bank_name: str
    account_type: str
    currency: str
    balance: float
    credit_limit: float | None
    pluggy_account_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceUpdateIn(BaseModel):
    balance: float
    source: str = Field(default="manual", pattern="^(manual|pluggy|auto)$")


class TransferIn(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0)
    description: str = Field(default="Transferência")
    date: str | None = None  # ISO date string, padrão hoje
