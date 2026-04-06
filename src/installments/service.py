"""InstallmentService — parcelamento de cartão + fontes de renda."""

from __future__ import annotations

from datetime import date
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session

from src.core.exceptions import AccountNotFound, InstallmentNotFound
from src.core.models import Account, IncomeSource, Installment, Transaction


class InstallmentService:
    def __init__(self, db: Session):
        self.db = db

    # ── Criação ───────────────────────────────────────────────────────────────

    def create(
        self,
        account_id: int,
        description: str,
        total_amount: float,
        installment_count: int,
        start_date: date,
        category: str = "outros",
    ) -> Installment:
        """Cria o parcelamento e N transações futuras (uma por mês)."""
        if self.db.get(Account, account_id) is None:
            raise AccountNotFound(account_id)

        installment_value = round(total_amount / installment_count, 2)

        installment = Installment(
            account_id=account_id,
            description=description,
            total_amount=total_amount,
            installment_count=installment_count,
            installment_value=installment_value,
            start_date=start_date,
            category=category,
        )
        self.db.add(installment)
        self.db.flush()  # garante installment.id antes de criar transações

        for i in range(installment_count):
            due_date = start_date + relativedelta(months=i)
            tx = Transaction(
                account_id=account_id,
                amount=-installment_value,
                description=f"{description} ({i + 1}/{installment_count})",
                category=category,
                transaction_date=due_date,
                competence_date=due_date,
                installment_id=installment.id,
            )
            self.db.add(tx)

        self.db.flush()
        return installment

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get(self, installment_id: int) -> Installment:
        inst = self.db.get(Installment, installment_id)
        if inst is None:
            raise InstallmentNotFound(installment_id)
        return inst

    def list(self, include_closed: bool = False) -> list[Installment]:
        q = self.db.query(Installment)
        if not include_closed:
            q = q.filter(Installment.is_closed == False)
        return q.order_by(Installment.start_date).all()

    def get_upcoming(self, days: int = 90) -> list[dict]:
        """Parcelas com vencimento nos próximos N dias."""
        today = date.today()
        cutoff = today + relativedelta(days=days)

        txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.installment_id.isnot(None),
                Transaction.transaction_date >= today,
                Transaction.transaction_date <= cutoff,
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

        return [
            {
                "transaction_id": t.id,
                "installment_id": t.installment_id,
                "description": t.description,
                "amount": t.amount,
                "due_date": t.transaction_date,
                "account_id": t.account_id,
            }
            for t in txs
        ]

    def monthly_commitment(self) -> float:
        """Soma dos valores mensais de todos os parcelamentos ativos."""
        active = self.list(include_closed=False)
        return round(sum(i.installment_value for i in active), 2)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def mark_paid(self, installment_id: int) -> Installment:
        """Incrementa paid_count; fecha automaticamente quando todas pagas."""
        inst = self.get(installment_id)
        if inst.is_closed:
            return inst
        inst.paid_count += 1
        if inst.paid_count >= inst.installment_count:
            inst.is_closed = True
        self.db.flush()
        return inst

    def close(self, installment_id: int) -> Installment:
        inst = self.get(installment_id)
        inst.is_closed = True
        self.db.flush()
        return inst

    # ── Helpers para o schema de saída ───────────────────────────────────────

    @staticmethod
    def enrich(inst: Installment) -> dict:
        """Adiciona campos calculados que não existem na ORM."""
        remaining = inst.installment_count - inst.paid_count
        next_due = (
            inst.start_date + relativedelta(months=inst.paid_count)
            if not inst.is_closed and remaining > 0
            else None
        )
        return {
            "remaining_count": remaining,
            "remaining_amount": round(remaining * inst.installment_value, 2),
            "next_due_date": next_due,
        }


# ── IncomeSources ─────────────────────────────────────────────────────────────

class IncomeSourceService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        amount: float,
        day_of_month: int | None = None,
        account_id: int | None = None,
    ) -> IncomeSource:
        if account_id and self.db.get(Account, account_id) is None:
            raise AccountNotFound(account_id)
        source = IncomeSource(
            name=name,
            amount=amount,
            day_of_month=day_of_month,
            account_id=account_id,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def list(self, include_inactive: bool = False) -> list[IncomeSource]:
        q = self.db.query(IncomeSource)
        if not include_inactive:
            q = q.filter(IncomeSource.is_active == True)
        return q.order_by(IncomeSource.name).all()

    def get(self, source_id: int) -> IncomeSource:
        src = self.db.get(IncomeSource, source_id)
        if src is None:
            raise KeyError(f"IncomeSource {source_id} nao encontrada")
        return src

    def deactivate(self, source_id: int) -> IncomeSource:
        src = self.get(source_id)
        src.is_active = False
        self.db.flush()
        return src

    def total_monthly(self) -> float:
        """Soma de todas as fontes de renda ativas."""
        return round(sum(s.amount for s in self.list()), 2)
