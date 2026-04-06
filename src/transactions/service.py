"""TransactionService — CRUD e consultas de transações."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.core.exceptions import AccountNotFound
from src.core.models import Account, Transaction
from src.transactions.categorizer import Categorizer

_categorizer = Categorizer()


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    # ── Criação ───────────────────────────────────────────────────────────────

    def create(
        self,
        account_id: int,
        amount: float,
        description: str,
        transaction_date: date,
        category: str | None = None,
        subcategory: str | None = None,
        competence_date: date | None = None,
        is_recurring: bool = False,
        notes: str | None = None,
        pluggy_transaction_id: str | None = None,
        installment_id: int | None = None,
    ) -> Transaction:
        # Verifica conta
        account = self.db.get(Account, account_id)
        if account is None:
            raise AccountNotFound(account_id)

        # Auto-categoriza se não informado
        if category is None:
            category, subcategory = _categorizer.classify(description)

        tx = Transaction(
            account_id=account_id,
            amount=amount,
            description=description,
            category=category,
            subcategory=subcategory,
            transaction_date=transaction_date,
            competence_date=competence_date,
            is_recurring=is_recurring,
            notes=notes,
            pluggy_transaction_id=pluggy_transaction_id,
            installment_id=installment_id,
        )
        self.db.add(tx)
        self.db.flush()
        return tx

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get(self, transaction_id: int) -> Transaction:
        tx = self.db.get(Transaction, transaction_id)
        if tx is None:
            raise KeyError(f"Transaction {transaction_id} não encontrada")
        return tx

    def list(
        self,
        account_id: int | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        search: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Transaction]:
        q = self.db.query(Transaction)

        if account_id is not None:
            q = q.filter(Transaction.account_id == account_id)
        if category is not None:
            q = q.filter(Transaction.category == category)
        if date_from is not None:
            q = q.filter(Transaction.transaction_date >= date_from)
        if date_to is not None:
            q = q.filter(Transaction.transaction_date <= date_to)
        if min_amount is not None:
            q = q.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            q = q.filter(Transaction.amount <= max_amount)
        if search is not None:
            q = q.filter(Transaction.description.ilike(f"%{search}%"))

        return q.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()

    def monthly_summary(self, year: int, month: int) -> dict:
        """Retorna totais de receitas, despesas e saldo do mês."""
        from datetime import date as dt
        date_from = dt(year, month, 1)
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        date_to = dt(year, month, last_day)

        txs = self.list(date_from=date_from, date_to=date_to, limit=10_000)

        income = sum(t.amount for t in txs if t.amount > 0 and t.category not in ("transferencia", "investimentos"))
        expenses = sum(t.amount for t in txs if t.amount < 0 and t.category not in ("transferencia", "investimentos"))
        by_category: dict[str, float] = {}
        for t in txs:
            by_category[t.category] = round(by_category.get(t.category, 0) + t.amount, 2)

        return {
            "year": year,
            "month": month,
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net": round(income + expenses, 2),
            "by_category": by_category,
        }

    def delete(self, transaction_id: int) -> None:
        tx = self.get(transaction_id)
        self.db.delete(tx)
        self.db.flush()
