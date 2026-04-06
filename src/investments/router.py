"""FastAPI router para /investments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import AccountNotFound
from src.investments.flashcards import get_all, get_by_id, get_by_tag
from src.investments.schemas import (
    InvestmentCreate, InvestmentEventCreate, InvestmentEventOut,
    InvestmentOut, InvestmentUpdate, TaxSimulationIn, TaxSimulationOut,
)
from src.investments.service import InvestmentNotFound, InvestmentService

router = APIRouter(prefix="/investments", tags=["investments"])


def _svc(db: Session = Depends(get_db)) -> InvestmentService:
    return InvestmentService(db)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[InvestmentOut])
def list_investments(
    asset_type: str | None = None,
    account_id: int | None = None,
    svc: InvestmentService = Depends(_svc),
):
    return svc.list(asset_type=asset_type, account_id=account_id)


@router.post("/", response_model=InvestmentOut, status_code=status.HTTP_201_CREATED)
def create_investment(body: InvestmentCreate, svc: InvestmentService = Depends(_svc)):
    try:
        inv = svc.create(**body.model_dump())
        svc.db.commit()
        svc.db.refresh(inv)
        return inv
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portfolio")
def portfolio_summary(svc: InvestmentService = Depends(_svc)):
    return svc.portfolio_summary()


@router.get("/{inv_id}", response_model=InvestmentOut)
def get_investment(inv_id: int, svc: InvestmentService = Depends(_svc)):
    try:
        return svc.get(inv_id)
    except InvestmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{inv_id}", response_model=InvestmentOut)
def update_investment(inv_id: int, body: InvestmentUpdate, svc: InvestmentService = Depends(_svc)):
    try:
        inv = svc.update(inv_id, **body.model_dump(exclude_none=True))
        svc.db.commit()
        svc.db.refresh(inv)
        return inv
    except InvestmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(inv_id: int, svc: InvestmentService = Depends(_svc)):
    try:
        svc.delete(inv_id)
        svc.db.commit()
    except InvestmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Eventos ───────────────────────────────────────────────────────────────────

@router.post("/{inv_id}/events", response_model=InvestmentEventOut, status_code=status.HTTP_201_CREATED)
def add_event(inv_id: int, body: InvestmentEventCreate, svc: InvestmentService = Depends(_svc)):
    try:
        evt = svc.add_event(inv_id, **body.model_dump())
        svc.db.commit()
        svc.db.refresh(evt)
        return evt
    except InvestmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{inv_id}/events", response_model=list[InvestmentEventOut])
def list_events(inv_id: int, svc: InvestmentService = Depends(_svc)):
    try:
        return svc.list_events(inv_id)
    except InvestmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Simulação de Impostos ─────────────────────────────────────────────────────

@router.post("/tax/simulate", response_model=TaxSimulationOut)
def simulate_tax(body: TaxSimulationIn, svc: InvestmentService = Depends(_svc)):
    result = svc.simulate_tax(
        asset_type=body.asset_type,
        principal=body.principal,
        gross_gain=body.gross_gain,
        purchase_date=body.purchase_date,
        sale_date=body.sale_date,
        quarterly_sales=body.quarterly_sales,
        monthly_sales=body.monthly_sales,
        is_day_trade=body.is_day_trade,
        carryforward_loss=body.carryforward_loss,
        dividend=body.dividend,
        capital_gain=body.capital_gain,
    )
    return TaxSimulationOut(
        asset_type=body.asset_type,
        gross_gain=result.gross_gain,
        iof=result.iof,
        ir=result.ir,
        net_gain=result.net_gain,
        effective_rate=result.effective_rate,
        details=result.details,
    )


# ── Flashcards ────────────────────────────────────────────────────────────────

@router.get("/flashcards/all")
def flashcards_all():
    return [vars(c) for c in get_all()]


@router.get("/flashcards/tag/{tag}")
def flashcards_by_tag(tag: str):
    return [vars(c) for c in get_by_tag(tag)]


@router.get("/flashcards/{flashcard_id}")
def flashcard_detail(flashcard_id: int):
    card = get_by_id(flashcard_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Flashcard {flashcard_id} não encontrado")
    return vars(card)
