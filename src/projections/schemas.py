"""Schemas Pydantic para Projections."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ProjectionPoint(BaseModel):
    month: int           # 1–12
    year: int
    label: str           # "Mai/2026"
    base: float
    optimistic: float
    pessimistic: float
    delta_base: float    # variação em relação ao mês anterior


class ProjectionResult(BaseModel):
    current_balance: float
    monthly_income: float
    avg_monthly_expenses: float
    monthly_installments: float
    variance_pct: float
    months: list[ProjectionPoint]
    trend: str           # "growing" | "shrinking" | "stable"
