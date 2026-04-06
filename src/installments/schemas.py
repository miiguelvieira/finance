"""Schemas Pydantic para Installments e IncomeSources."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Installments ──────────────────────────────────────────────────────────────

class InstallmentCreate(BaseModel):
    account_id: int
    description: str = Field(..., min_length=1, max_length=255)
    total_amount: float = Field(..., gt=0)
    installment_count: int = Field(..., ge=2, le=120)
    start_date: date
    category: str = "outros"


class InstallmentOut(BaseModel):
    id: int
    account_id: int
    description: str
    total_amount: float
    installment_count: int
    installment_value: float
    start_date: date
    paid_count: int
    category: str
    is_closed: bool
    remaining_count: int
    remaining_amount: float
    next_due_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── IncomeSources ─────────────────────────────────────────────────────────────

class IncomeSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    account_id: int | None = None


class IncomeSourceOut(BaseModel):
    id: int
    name: str
    amount: float
    day_of_month: int | None
    account_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}
