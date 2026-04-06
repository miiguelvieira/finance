"""Schemas Pydantic para Investments."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class InvestmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: str = Field(..., pattern="^(renda_fixa|lci_lca|acoes|fii|crypto|other)$")
    ticker: str | None = Field(default=None, max_length=10)
    principal: float = Field(..., gt=0)
    current_value: float = Field(..., gt=0)
    purchase_date: date
    maturity_date: date | None = None
    rate_description: str | None = Field(default=None, max_length=100)
    account_id: int | None = None
    pluggy_investment_id: str | None = None


class InvestmentUpdate(BaseModel):
    name: str | None = None
    current_value: float | None = Field(default=None, gt=0)
    maturity_date: date | None = None
    rate_description: str | None = None


class InvestmentOut(BaseModel):
    id: int
    name: str
    asset_type: str
    ticker: str | None
    principal: float
    current_value: float
    purchase_date: date
    maturity_date: date | None
    rate_description: str | None
    account_id: int | None
    pluggy_investment_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvestmentEventCreate(BaseModel):
    event_type: str = Field(..., pattern="^(buy|sell|dividend|income|rebalance)$")
    amount: float = Field(..., gt=0)
    quantity: float | None = None
    price_per_unit: float | None = None
    event_date: date
    taxes_paid: float = Field(default=0.0, ge=0)
    notes: str | None = None


class InvestmentEventOut(BaseModel):
    id: int
    investment_id: int
    event_type: str
    amount: float
    quantity: float | None
    price_per_unit: float | None
    event_date: date
    taxes_paid: float
    notes: str | None

    model_config = {"from_attributes": True}


class TaxSimulationIn(BaseModel):
    asset_type: str = Field(..., pattern="^(renda_fixa|lci_lca|acoes|fii|crypto)$")
    principal: float = Field(..., gt=0)
    gross_gain: float
    purchase_date: date | None = None
    sale_date: date | None = None
    # acoes / crypto
    quarterly_sales: float = Field(default=0.0, ge=0)
    monthly_sales: float = Field(default=0.0, ge=0)
    is_day_trade: bool = False
    carryforward_loss: float = Field(default=0.0, ge=0)
    # fii
    dividend: float = Field(default=0.0, ge=0)
    capital_gain: float = Field(default=0.0, ge=0)


class TaxSimulationOut(BaseModel):
    asset_type: str
    gross_gain: float
    iof: float
    ir: float
    net_gain: float
    effective_rate: float
    details: dict
