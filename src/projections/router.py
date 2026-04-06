"""FastAPI router para /projections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
from src.projections.engine import ProjectionEngine

router = APIRouter(prefix="/projections", tags=["projections"])


@router.get("/")
def get_projection(
    months: int = Query(default=12, ge=1, le=24),
    variance: float = Query(default=None),
    db: Session = Depends(get_db),
):
    """Projeção de saldo usando dados reais do banco."""
    cfg = get_settings()
    v = variance if variance is not None else cfg.get("projection", "variance_pct", default=0.15)
    m = months or cfg.get("projection", "months_forward", default=12)

    engine = ProjectionEngine(db, months_forward=m, variance_pct=v)
    result = engine.project()
    return result


@router.post("/simulate")
def simulate_projection(
    current_balance: float = Query(...),
    monthly_income: float = Query(...),
    avg_monthly_expenses: float = Query(...),
    monthly_installments: float = Query(default=0.0),
    months: int = Query(default=12, ge=1, le=24),
    variance: float = Query(default=0.15),
):
    """Simulação com valores customizados — não usa o banco."""
    result = ProjectionEngine.compute(
        current_balance=current_balance,
        monthly_income=monthly_income,
        avg_monthly_expenses=avg_monthly_expenses,
        monthly_installments=monthly_installments,
        variance_pct=variance,
        months_forward=months,
    )
    return result
