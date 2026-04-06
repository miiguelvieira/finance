"""Motor de projeção de saldo — 12 meses com banda de confiança.

Modelo:
  base_delta   = income - abs(avg_expenses) - monthly_installments
  opt_delta    = income*(1+v) - abs(avg_expenses)*(1-v) - monthly_installments
  pess_delta   = income*(1-v) - abs(avg_expenses)*(1+v) - monthly_installments

  balance[i] = balance[i-1] + delta[i]

Notas:
  - avg_expenses: média dos últimos N meses de transações com amount < 0,
    excluindo parcelas (installment_id IS NOT NULL) e categorias de renda
    (salario, freelance, dividendos, transferencia, investimentos).
  - monthly_installments: soma dos installment_value dos parcelamentos ativos.
    Separado do avg_expenses para capturar novos parcelamentos não refletidos
    no histórico.
  - Parcelas têm valor fixo (sem variância), pois são obrigações conhecidas.
  - Fallback para histórico vazio: avg_expenses = 0.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from src.core.models import Account, IncomeSource, Installment, Transaction

# Categorias que NÃO são despesas (não entram no avg_expenses)
_INCOME_CATEGORIES = frozenset(
    {"salario", "freelance", "dividendos", "transferencia", "investimentos"}
)

# Meses em português
_MONTHS_PT = (
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
)


@dataclass
class ProjectionPoint:
    month: int
    year: int
    label: str
    base: float
    optimistic: float
    pessimistic: float
    delta_base: float


@dataclass
class ProjectionResult:
    current_balance: float
    monthly_income: float
    avg_monthly_expenses: float
    monthly_installments: float
    variance_pct: float
    months: list[ProjectionPoint]
    trend: str


class ProjectionEngine:
    """Calcula projeção de saldo para os próximos N meses."""

    def __init__(
        self,
        db: Session,
        months_forward: int = 12,
        variance_pct: float = 0.15,
        history_months: int = 3,
    ):
        self.db = db
        self.months_forward = months_forward
        self.variance_pct = variance_pct
        self.history_months = history_months

    # ── API pública ───────────────────────────────────────────────────────────

    def project(self) -> ProjectionResult:
        current_balance = self._current_balance()
        monthly_income = self._monthly_income()
        avg_expenses = self._avg_monthly_expenses()
        monthly_install = self._monthly_installments()
        v = self.variance_pct

        base_delta = monthly_income - avg_expenses - monthly_install
        opt_delta = monthly_income * (1 + v) - avg_expenses * (1 - v) - monthly_install
        pess_delta = monthly_income * (1 - v) - avg_expenses * (1 + v) - monthly_install

        points: list[ProjectionPoint] = []
        bal_base = current_balance
        bal_opt = current_balance
        bal_pess = current_balance
        today = date.today()

        for i in range(1, self.months_forward + 1):
            target = today + relativedelta(months=i)
            prev_base = bal_base

            bal_base = round(bal_base + base_delta, 2)
            bal_opt = round(bal_opt + opt_delta, 2)
            bal_pess = round(bal_pess + pess_delta, 2)

            points.append(ProjectionPoint(
                month=target.month,
                year=target.year,
                label=f"{_MONTHS_PT[target.month]}/{target.year}",
                base=bal_base,
                optimistic=bal_opt,
                pessimistic=bal_pess,
                delta_base=round(bal_base - prev_base, 2),
            ))

        trend = self._classify_trend(base_delta)

        return ProjectionResult(
            current_balance=round(current_balance, 2),
            monthly_income=round(monthly_income, 2),
            avg_monthly_expenses=round(avg_expenses, 2),
            monthly_installments=round(monthly_install, 2),
            variance_pct=v,
            months=points,
            trend=trend,
        )

    # ── Coleta de dados ───────────────────────────────────────────────────────

    def _current_balance(self) -> float:
        rows = self.db.query(Account.balance).filter(Account.is_active == True).all()
        return sum(r.balance for r in rows)

    def _monthly_income(self) -> float:
        rows = self.db.query(IncomeSource.amount).filter(IncomeSource.is_active == True).all()
        return sum(r.amount for r in rows)

    def _avg_monthly_expenses(self) -> float:
        """Média mensal de despesas reais dos últimos history_months meses.

        Exclui:
          - Transações de parcelas (installment_id IS NOT NULL) — contadas em monthly_installments
          - Categorias de renda e transferências
          - Transações com amount >= 0 (créditos)
        """
        today = date.today()
        cutoff = today - relativedelta(months=self.history_months)

        rows = (
            self.db.query(Transaction.amount, Transaction.transaction_date)
            .filter(
                Transaction.amount < 0,
                Transaction.transaction_date >= cutoff,
                Transaction.transaction_date <= today,
                Transaction.installment_id.is_(None),
                Transaction.category.notin_(_INCOME_CATEGORIES),
            )
            .all()
        )

        if not rows:
            return 0.0

        # Agrupa por mês para calcular média mensal
        monthly: dict[tuple[int, int], float] = {}
        for amount, tx_date in rows:
            key = (tx_date.year, tx_date.month)
            monthly[key] = monthly.get(key, 0.0) + abs(amount)

        return sum(monthly.values()) / len(monthly) if monthly else 0.0

    def _monthly_installments(self) -> float:
        rows = (
            self.db.query(Installment.installment_value)
            .filter(Installment.is_closed == False)
            .all()
        )
        return sum(r.installment_value for r in rows)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_trend(base_delta: float, threshold: float = 50.0) -> str:
        if base_delta > threshold:
            return "growing"
        if base_delta < -threshold:
            return "shrinking"
        return "stable"

    # ── Método estático para uso direto com inputs conhecidos (testável) ──────

    @staticmethod
    def compute(
        current_balance: float,
        monthly_income: float,
        avg_monthly_expenses: float,
        monthly_installments: float,
        variance_pct: float = 0.15,
        months_forward: int = 12,
        start_date: date | None = None,
    ) -> ProjectionResult:
        """Projeção a partir de valores explícitos — sem acesso ao banco.

        Útil para testes e para o endpoint que recebe parâmetros customizados.
        """
        v = variance_pct
        base_delta = monthly_income - avg_monthly_expenses - monthly_installments
        opt_delta = monthly_income * (1 + v) - avg_monthly_expenses * (1 - v) - monthly_installments
        pess_delta = monthly_income * (1 - v) - avg_monthly_expenses * (1 + v) - monthly_installments

        today = start_date or date.today()
        points: list[ProjectionPoint] = []
        bal_base = current_balance
        bal_opt = current_balance
        bal_pess = current_balance

        for i in range(1, months_forward + 1):
            target = today + relativedelta(months=i)
            prev_base = bal_base
            bal_base = round(bal_base + base_delta, 2)
            bal_opt = round(bal_opt + opt_delta, 2)
            bal_pess = round(bal_pess + pess_delta, 2)

            points.append(ProjectionPoint(
                month=target.month,
                year=target.year,
                label=f"{_MONTHS_PT[target.month]}/{target.year}",
                base=bal_base,
                optimistic=bal_opt,
                pessimistic=bal_pess,
                delta_base=round(bal_base - prev_base, 2),
            ))

        return ProjectionResult(
            current_balance=round(current_balance, 2),
            monthly_income=round(monthly_income, 2),
            avg_monthly_expenses=round(avg_monthly_expenses, 2),
            monthly_installments=round(monthly_installments, 2),
            variance_pct=v,
            months=points,
            trend=ProjectionEngine._classify_trend(base_delta),
        )
