"""AccountService — CRUD de contas, saldo, transferências e net worth."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from src.core.exceptions import AccountNotFound, InsufficientBalance
from src.core.models import Account, BalanceHistory, Transaction


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create(
        self,
        name: str,
        bank_name: str,
        account_type: str,
        balance: float = 0.0,
        currency: str = "BRL",
        credit_limit: float | None = None,
        pluggy_account_id: str | None = None,
    ) -> Account:
        account = Account(
            name=name,
            bank_name=bank_name,
            account_type=account_type,
            balance=balance,
            currency=currency,
            credit_limit=credit_limit,
            pluggy_account_id=pluggy_account_id,
        )
        self.db.add(account)
        self.db.flush()
        self._record_balance(account.id, balance, source="manual")
        return account

    def get(self, account_id: int) -> Account:
        account = self.db.get(Account, account_id)
        if account is None:
            raise AccountNotFound(account_id)
        return account

    def list(self, include_inactive: bool = False) -> list[Account]:
        q = self.db.query(Account)
        if not include_inactive:
            q = q.filter(Account.is_active == True)
        return q.order_by(Account.name).all()

    def update(self, account_id: int, **kwargs) -> Account:
        account = self.get(account_id)
        for key, val in kwargs.items():
            if val is not None and hasattr(account, key):
                setattr(account, key, val)
        self.db.flush()
        return account

    def deactivate(self, account_id: int) -> Account:
        account = self.get(account_id)
        account.is_active = False
        self.db.flush()
        return account

    # ── Saldo ─────────────────────────────────────────────────────────────────

    def update_balance(
        self,
        account_id: int,
        new_balance: float,
        source: str = "manual",
    ) -> Account:
        account = self.get(account_id)
        account.balance = new_balance
        self.db.flush()
        self._record_balance(account_id, new_balance, source)
        return account

    def net_worth(self) -> float:
        """Soma dos saldos de todas as contas ativas."""
        accounts = self.list()
        return round(sum(a.balance for a in accounts), 2)

    # ── Transferência ─────────────────────────────────────────────────────────

    def transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: float,
        description: str = "Transferência",
        transfer_date: date | None = None,
    ) -> tuple[Transaction, Transaction]:
        """Cria duas transações vinculadas por transfer_ref UUID."""
        origin = self.get(from_account_id)
        destination = self.get(to_account_id)

        if origin.balance < amount:
            raise InsufficientBalance(origin.balance, amount)

        ref = str(uuid.uuid4())
        today = transfer_date or date.today()

        debit = Transaction(
            account_id=from_account_id,
            amount=-abs(amount),
            description=description,
            category="transferencia",
            transaction_date=today,
            transfer_ref=ref,
        )
        credit = Transaction(
            account_id=to_account_id,
            amount=abs(amount),
            description=description,
            category="transferencia",
            transaction_date=today,
            transfer_ref=ref,
        )

        origin.balance = round(origin.balance - amount, 2)
        destination.balance = round(destination.balance + amount, 2)

        self.db.add(debit)
        self.db.add(credit)
        self.db.flush()
        return debit, credit

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _record_balance(self, account_id: int, balance: float, source: str) -> None:
        history = BalanceHistory(
            account_id=account_id,
            balance=balance,
            snapshot_date=date.today(),
            source=source,
        )
        self.db.add(history)
        self.db.flush()
