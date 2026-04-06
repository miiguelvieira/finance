"""Tax Engine BR 2026 — cálculo de impostos sobre investimentos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# IOF regressivo: índice 0 = dia 1 ... índice 29 = dia 30 (percentual sobre o ganho)
_IOF_TABLE = [
    96, 93, 90, 86, 83, 80, 76, 73, 70, 66,
    63, 60, 56, 53, 50, 46, 43, 40, 36, 33,
    30, 26, 23, 20, 16, 13, 10,  6,  3,  0,
]


@dataclass
class TaxResult:
    gross_gain: float
    iof: float
    ir: float
    net_gain: float
    effective_rate: float   # alíquota efetiva total (%)
    details: dict = field(default_factory=dict)


def _iof_rate(days_held: int) -> float:
    """Alíquota IOF (0-1). Zero para >= 30 dias."""
    if days_held <= 0:
        return 0.96
    if days_held >= 30:
        return 0.0
    return _IOF_TABLE[days_held - 1] / 100


def calc_renda_fixa(
    principal: float,
    gross_gain: float,
    purchase_date: date,
    sale_date: date,
) -> TaxResult:
    """CDB, Tesouro Direto — 17.5% IR + IOF se < 30 dias (BR 2026)."""
    days = (sale_date - purchase_date).days

    iof_rate = _iof_rate(days)
    iof = round(gross_gain * iof_rate, 2)
    gain_after_iof = max(round(gross_gain - iof, 10), 0.0)

    ir = round(gain_after_iof * 0.175, 2)
    net_gain = round(gain_after_iof - ir, 2)
    effective = round((iof + ir) / gross_gain * 100, 4) if gross_gain > 0 else 0.0

    return TaxResult(
        gross_gain=round(gross_gain, 2),
        iof=iof,
        ir=ir,
        net_gain=net_gain,
        effective_rate=effective,
        details={
            "days_held": days,
            "iof_rate_pct": round(iof_rate * 100, 2),
            "ir_rate_pct": 17.5,
            "principal": round(principal, 2),
        },
    )


def calc_lci_lca(
    principal: float,
    gross_gain: float,
) -> TaxResult:
    """LCI/LCA pós-reforma 2026 — 5% sobre o ganho."""
    ir = round(gross_gain * 0.05, 2)
    net_gain = round(gross_gain - ir, 2)
    effective = 5.0 if gross_gain > 0 else 0.0

    return TaxResult(
        gross_gain=round(gross_gain, 2),
        iof=0.0,
        ir=ir,
        net_gain=net_gain,
        effective_rate=effective,
        details={
            "ir_rate_pct": 5.0,
            "principal": round(principal, 2),
            "note": "nova emissao pos-reforma 2026",
        },
    )


def calc_acoes(
    gross_gain: float,
    quarterly_sales: float,
    is_day_trade: bool = False,
    carryforward_loss: float = 0.0,
) -> TaxResult:
    """Ações — 17.5% / 20% day trade / isento se vendas trimestrais <= R$60k."""
    EXEMPTION_LIMIT = 60_000.0

    carryforward_used = min(carryforward_loss, max(gross_gain, 0.0))
    gain_after_carryforward = max(round(gross_gain - carryforward_used, 10), 0.0)

    if not is_day_trade and quarterly_sales <= EXEMPTION_LIMIT:
        return TaxResult(
            gross_gain=round(gross_gain, 2),
            iof=0.0,
            ir=0.0,
            net_gain=round(gross_gain, 2),
            effective_rate=0.0,
            details={
                "exempt": True,
                "quarterly_sales": round(quarterly_sales, 2),
                "limit": EXEMPTION_LIMIT,
            },
        )

    ir_rate = 0.20 if is_day_trade else 0.175
    ir = round(gain_after_carryforward * ir_rate, 2)
    net_gain = round(gross_gain - ir, 2)
    effective = round(ir / gross_gain * 100, 4) if gross_gain > 0 else 0.0

    return TaxResult(
        gross_gain=round(gross_gain, 2),
        iof=0.0,
        ir=ir,
        net_gain=net_gain,
        effective_rate=effective,
        details={
            "is_day_trade": is_day_trade,
            "ir_rate_pct": round(ir_rate * 100, 2),
            "carryforward_used": round(carryforward_used, 2),
            "quarterly_sales": round(quarterly_sales, 2),
            "exempt": False,
        },
    )


def calc_fii(
    dividend: float,
    capital_gain: float,
    carryforward_loss: float = 0.0,
) -> TaxResult:
    """FII — 5% dividendos + 17.5% ganho de capital."""
    ir_dividend = round(dividend * 0.05, 2)

    carryforward_used = min(carryforward_loss, max(capital_gain, 0.0))
    gain_after_carryforward = max(round(capital_gain - carryforward_used, 10), 0.0)
    ir_capital = round(gain_after_carryforward * 0.175, 2)

    total_ir = round(ir_dividend + ir_capital, 2)
    gross_total = round(dividend + capital_gain, 2)
    net_gain = round(gross_total - total_ir, 2)
    effective = round(total_ir / gross_total * 100, 4) if gross_total > 0 else 0.0

    return TaxResult(
        gross_gain=gross_total,
        iof=0.0,
        ir=total_ir,
        net_gain=net_gain,
        effective_rate=effective,
        details={
            "ir_dividend": ir_dividend,
            "ir_capital": ir_capital,
            "dividend_rate_pct": 5.0,
            "capital_gain_rate_pct": 17.5,
            "carryforward_used": round(carryforward_used, 2),
        },
    )


def calc_crypto(
    gross_gain: float,
    monthly_sales: float,
    carryforward_loss: float = 0.0,
) -> TaxResult:
    """Crypto — 17.5% / isento se vendas mensais <= R$35k."""
    EXEMPTION_LIMIT = 35_000.0

    carryforward_used = min(carryforward_loss, max(gross_gain, 0.0))
    gain_after_carryforward = max(round(gross_gain - carryforward_used, 10), 0.0)

    if monthly_sales <= EXEMPTION_LIMIT:
        return TaxResult(
            gross_gain=round(gross_gain, 2),
            iof=0.0,
            ir=0.0,
            net_gain=round(gross_gain, 2),
            effective_rate=0.0,
            details={
                "exempt": True,
                "monthly_sales": round(monthly_sales, 2),
                "limit": EXEMPTION_LIMIT,
            },
        )

    ir = round(gain_after_carryforward * 0.175, 2)
    net_gain = round(gross_gain - ir, 2)
    effective = round(ir / gross_gain * 100, 4) if gross_gain > 0 else 0.0

    return TaxResult(
        gross_gain=round(gross_gain, 2),
        iof=0.0,
        ir=ir,
        net_gain=net_gain,
        effective_rate=effective,
        details={
            "ir_rate_pct": 17.5,
            "carryforward_used": round(carryforward_used, 2),
            "monthly_sales": round(monthly_sales, 2),
            "exempt": False,
        },
    )


def carryforward_remaining(
    losses: list[tuple[date, float]],
    reference_date: date,
    max_years: int = 5,
) -> float:
    """Soma prejuízos ainda válidos para carryforward (dentro de max_years anos)."""
    total = 0.0
    for loss_date, loss_amount in losses:
        years_ago = (reference_date - loss_date).days / 365.25
        if 0 <= years_ago <= max_years:
            total += loss_amount
    return round(total, 2)
