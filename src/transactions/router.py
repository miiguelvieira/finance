"""FastAPI router para /transactions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import AccountNotFound
from src.transactions.schemas import TransactionCreate, TransactionOut
from src.transactions.service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _svc(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    account_id: int | None = Query(None),
    category: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
    svc: TransactionService = Depends(_svc),
):
    from datetime import date
    return svc.list(
        account_id=account_id,
        category=category,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate, svc: TransactionService = Depends(_svc)):
    try:
        tx = svc.create(**body.model_dump())
        svc.db.commit()
        svc.db.refresh(tx)
        return tx
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary/{year}/{month}")
def monthly_summary(year: int, month: int, svc: TransactionService = Depends(_svc)):
    return svc.monthly_summary(year, month)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int, svc: TransactionService = Depends(_svc)):
    try:
        return svc.get(transaction_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, svc: TransactionService = Depends(_svc)):
    try:
        svc.delete(transaction_id)
        svc.db.commit()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
