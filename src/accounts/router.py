"""FastAPI router para /accounts."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.accounts.schemas import (
    AccountCreate, AccountOut, AccountUpdate, BalanceUpdateIn, TransferIn,
)
from src.accounts.service import AccountService
from src.core.database import get_db
from src.core.exceptions import AccountNotFound, InsufficientBalance

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _svc(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


@router.get("/", response_model=list[AccountOut])
def list_accounts(include_inactive: bool = False, svc: AccountService = Depends(_svc)):
    return svc.list(include_inactive)


@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(body: AccountCreate, svc: AccountService = Depends(_svc)):
    account = svc.create(**body.model_dump())
    svc.db.commit()
    svc.db.refresh(account)
    return account


@router.get("/net-worth")
def net_worth(svc: AccountService = Depends(_svc)):
    return {"net_worth": svc.net_worth()}


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, svc: AccountService = Depends(_svc)):
    try:
        return svc.get(account_id)
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: int, body: AccountUpdate, svc: AccountService = Depends(_svc)):
    try:
        account = svc.update(account_id, **body.model_dump(exclude_none=True))
        svc.db.commit()
        svc.db.refresh(account)
        return account
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{account_id}/balance", response_model=AccountOut)
def update_balance(account_id: int, body: BalanceUpdateIn, svc: AccountService = Depends(_svc)):
    try:
        account = svc.update_balance(account_id, body.balance, body.source)
        svc.db.commit()
        svc.db.refresh(account)
        return account
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(account_id: int, svc: AccountService = Depends(_svc)):
    try:
        svc.deactivate(account_id)
        svc.db.commit()
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/transfer", status_code=status.HTTP_201_CREATED)
def transfer(body: TransferIn, svc: AccountService = Depends(_svc)):
    try:
        transfer_date = date.fromisoformat(body.date) if body.date else None
        debit, credit = svc.transfer(
            body.from_account_id, body.to_account_id,
            body.amount, body.description, transfer_date,
        )
        svc.db.commit()
        return {"debit_id": debit.id, "credit_id": credit.id, "amount": body.amount}
    except AccountNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalance as e:
        raise HTTPException(status_code=422, detail=str(e))
