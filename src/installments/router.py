"""FastAPI routers para /installments e /income-sources."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import AccountNotFound, InstallmentNotFound
from src.installments.schemas import (
    InstallmentCreate, InstallmentOut,
    IncomeSourceCreate, IncomeSourceOut,
)
from src.installments.service import IncomeSourceService, InstallmentService
from src.core.models import Installment


def _serialize(inst: Installment) -> dict:
    """Converte Installment + campos calculados para dict serializável."""
    data = {c.name: getattr(inst, c.name) for c in inst.__table__.columns}
    data.update(InstallmentService.enrich(inst))
    return data

router = APIRouter(prefix="/installments", tags=["installments"])
income_router = APIRouter(prefix="/income-sources", tags=["income-sources"])


def _svc(db: Session = Depends(get_db)) -> InstallmentService:
    return InstallmentService(db)


def _income_svc(db: Session = Depends(get_db)) -> IncomeSourceService:
    return IncomeSourceService(db)


# ── Installments ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[dict])
def list_installments(include_closed: bool = False, svc: InstallmentService = Depends(_svc)):
    items = svc.list(include_closed)
    return [
        _serialize(inst)
        for inst in items
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_installment(body: InstallmentCreate, svc: InstallmentService = Depends(_svc)):
    try:
        inst = svc.create(**body.model_dump())
        svc.db.commit()
        svc.db.refresh(inst)
        return _serialize(inst)
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/upcoming")
def upcoming(days: int = 90, svc: InstallmentService = Depends(_svc)):
    return svc.get_upcoming(days)


@router.get("/monthly-commitment")
def monthly_commitment(svc: InstallmentService = Depends(_svc)):
    return {"monthly_commitment": svc.monthly_commitment()}


@router.get("/{installment_id}")
def get_installment(installment_id: int, svc: InstallmentService = Depends(_svc)):
    try:
        inst = svc.get(installment_id)
        return _serialize(inst)
    except InstallmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{installment_id}/mark-paid")
def mark_paid(installment_id: int, svc: InstallmentService = Depends(_svc)):
    try:
        inst = svc.mark_paid(installment_id)
        svc.db.commit()
        return _serialize(inst)
    except InstallmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{installment_id}/close", status_code=status.HTTP_200_OK)
def close_installment(installment_id: int, svc: InstallmentService = Depends(_svc)):
    try:
        inst = svc.close(installment_id)
        svc.db.commit()
        return {"id": inst.id, "is_closed": inst.is_closed}
    except InstallmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Income Sources ────────────────────────────────────────────────────────────

@income_router.get("/", response_model=list[IncomeSourceOut])
def list_income_sources(include_inactive: bool = False, svc: IncomeSourceService = Depends(_income_svc)):
    return svc.list(include_inactive)


@income_router.post("/", response_model=IncomeSourceOut, status_code=status.HTTP_201_CREATED)
def create_income_source(body: IncomeSourceCreate, svc: IncomeSourceService = Depends(_income_svc)):
    try:
        src = svc.create(**body.model_dump())
        svc.db.commit()
        svc.db.refresh(src)
        return src
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@income_router.get("/total-monthly")
def total_monthly(svc: IncomeSourceService = Depends(_income_svc)):
    return {"total_monthly": svc.total_monthly()}


@income_router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_income_source(source_id: int, svc: IncomeSourceService = Depends(_income_svc)):
    try:
        svc.deactivate(source_id)
        svc.db.commit()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
