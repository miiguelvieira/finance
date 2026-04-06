"""InvestmentService — CRUD, eventos e resumo de carteira."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from src.core.exceptions import AccountNotFound
from src.core.models import Account, Investment, InvestmentEvent
from src.investments import tax_engine


class InvestmentNotFound(Exception):
    def __init__(self, inv_id: int):
        super().__init__(f"Investment {inv_id} não encontrado")


class InvestmentService:
    def __init__(self, db: Session):
        self.db = db

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create(
        self,
        name: str,
        asset_type: str,
        principal: float,
        current_value: float,
        purchase_date: date,
        ticker: str | None = None,
        maturity_date: date | None = None,
        rate_description: str | None = None,
        account_id: int | None = None,
        pluggy_investment_id: str | None = None,
    ) -> Investment:
        if account_id is not None and self.db.get(Account, account_id) is None:
            raise AccountNotFound(account_id)

        inv = Investment(
            name=name,
            asset_type=asset_type,
            principal=principal,
            current_value=current_value,
            purchase_date=purchase_date,
            ticker=ticker,
            maturity_date=maturity_date,
            rate_description=rate_description,
            account_id=account_id,
            pluggy_investment_id=pluggy_investment_id,
        )
        self.db.add(inv)
        self.db.flush()
        return inv

    def get(self, inv_id: int) -> Investment:
        inv = self.db.get(Investment, inv_id)
        if inv is None:
            raise InvestmentNotFound(inv_id)
        return inv

    def list(
        self,
        asset_type: str | None = None,
        account_id: int | None = None,
    ) -> list[Investment]:
        q = self.db.query(Investment)
        if asset_type:
            q = q.filter(Investment.asset_type == asset_type)
        if account_id is not None:
            q = q.filter(Investment.account_id == account_id)
        return q.order_by(Investment.purchase_date.desc()).all()

    def update(self, inv_id: int, **kwargs) -> Investment:
        inv = self.get(inv_id)
        for k, v in kwargs.items():
            if v is not None and hasattr(inv, k):
                setattr(inv, k, v)
        self.db.flush()
        return inv

    def delete(self, inv_id: int) -> None:
        inv = self.get(inv_id)
        self.db.delete(inv)
        self.db.flush()

    # ── Eventos ───────────────────────────────────────────────────────────────

    def add_event(
        self,
        inv_id: int,
        event_type: str,
        amount: float,
        event_date: date,
        quantity: float | None = None,
        price_per_unit: float | None = None,
        taxes_paid: float = 0.0,
        notes: str | None = None,
    ) -> InvestmentEvent:
        inv = self.get(inv_id)

        evt = InvestmentEvent(
            investment_id=inv.id,
            event_type=event_type,
            amount=amount,
            quantity=quantity,
            price_per_unit=price_per_unit,
            event_date=event_date,
            taxes_paid=taxes_paid,
            notes=notes,
        )
        self.db.add(evt)
        self.db.flush()
        return evt

    def list_events(self, inv_id: int) -> list[InvestmentEvent]:
        self.get(inv_id)  # valida existência
        return (
            self.db.query(InvestmentEvent)
            .filter(InvestmentEvent.investment_id == inv_id)
            .order_by(InvestmentEvent.event_date.desc())
            .all()
        )

    # ── Carteira ──────────────────────────────────────────────────────────────

    def portfolio_summary(self) -> dict:
        """Retorna resumo da carteira: totais por tipo, ganho bruto e alocação."""
        investments = self.list()
        if not investments:
            return {
                "total_principal": 0.0,
                "total_current": 0.0,
                "total_gain": 0.0,
                "gain_pct": 0.0,
                "by_type": {},
                "count": 0,
            }

        by_type: dict[str, dict] = {}
        total_principal = 0.0
        total_current = 0.0

        for inv in investments:
            t = inv.asset_type
            if t not in by_type:
                by_type[t] = {"principal": 0.0, "current": 0.0, "count": 0}
            by_type[t]["principal"] = round(by_type[t]["principal"] + inv.principal, 2)
            by_type[t]["current"] = round(by_type[t]["current"] + inv.current_value, 2)
            by_type[t]["count"] += 1
            total_principal += inv.principal
            total_current += inv.current_value

        total_principal = round(total_principal, 2)
        total_current = round(total_current, 2)
        total_gain = round(total_current - total_principal, 2)
        gain_pct = round(total_gain / total_principal * 100, 4) if total_principal > 0 else 0.0

        # Adiciona ganho e alocação por tipo
        for t, data in by_type.items():
            data["gain"] = round(data["current"] - data["principal"], 2)
            data["allocation_pct"] = round(data["current"] / total_current * 100, 2) if total_current > 0 else 0.0

        return {
            "total_principal": total_principal,
            "total_current": total_current,
            "total_gain": total_gain,
            "gain_pct": gain_pct,
            "by_type": by_type,
            "count": len(investments),
        }

    # ── Simulação de Imposto ──────────────────────────────────────────────────

    def simulate_tax(
        self,
        asset_type: str,
        principal: float,
        gross_gain: float,
        purchase_date: date | None = None,
        sale_date: date | None = None,
        quarterly_sales: float = 0.0,
        monthly_sales: float = 0.0,
        is_day_trade: bool = False,
        carryforward_loss: float = 0.0,
        dividend: float = 0.0,
        capital_gain: float = 0.0,
    ) -> tax_engine.TaxResult:
        today = date.today()

        if asset_type == "renda_fixa":
            return tax_engine.calc_renda_fixa(
                principal=principal,
                gross_gain=gross_gain,
                purchase_date=purchase_date or today,
                sale_date=sale_date or today,
            )
        if asset_type == "lci_lca":
            return tax_engine.calc_lci_lca(principal=principal, gross_gain=gross_gain)
        if asset_type == "acoes":
            return tax_engine.calc_acoes(
                gross_gain=gross_gain,
                quarterly_sales=quarterly_sales,
                is_day_trade=is_day_trade,
                carryforward_loss=carryforward_loss,
            )
        if asset_type == "fii":
            return tax_engine.calc_fii(
                dividend=dividend,
                capital_gain=capital_gain,
                carryforward_loss=carryforward_loss,
            )
        if asset_type == "crypto":
            return tax_engine.calc_crypto(
                gross_gain=gross_gain,
                monthly_sales=monthly_sales,
                carryforward_loss=carryforward_loss,
            )
        raise ValueError(f"asset_type desconhecido: {asset_type}")
