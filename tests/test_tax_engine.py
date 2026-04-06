"""Testes do Tax Engine BR 2026 — cobertura 100% obrigatória."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.investments.tax_engine import (
    _iof_rate,
    calc_renda_fixa,
    calc_lci_lca,
    calc_acoes,
    calc_fii,
    calc_crypto,
    carryforward_remaining,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, passed))


def approx(a, b, tol=0.01):
    return abs(a - b) <= tol


# ── _iof_rate ─────────────────────────────────────────────────────────────────
print("\n=== 1. _iof_rate ===\n")

report("dia 0 = 96%",   _iof_rate(0)  == 0.96)
report("dia -1 = 96%",  _iof_rate(-1) == 0.96)
report("dia 1 = 96%",   _iof_rate(1)  == 0.96)
report("dia 15 = 50%",  _iof_rate(15) == 0.50)
report("dia 29 = 3%",   _iof_rate(29) == 0.03)
report("dia 30 = 0%",   _iof_rate(30) == 0.0)
report("dia 60 = 0%",   _iof_rate(60) == 0.0)


# ── calc_renda_fixa ───────────────────────────────────────────────────────────
print("\n=== 2. calc_renda_fixa ===\n")

BASE = date(2026, 1, 1)

r = calc_renda_fixa(1000.0, 100.0, BASE, date(2026, 4, 1))  # >30 dias
report("sem IOF quando >30 dias", r.iof == 0.0)
report("IR 17.5% sobre ganho",    approx(r.ir, 17.5))
report("net_gain correto",         approx(r.net_gain, 82.5))
report("details tem ir_rate_pct", r.details["ir_rate_pct"] == 17.5)

r2 = calc_renda_fixa(1000.0, 100.0, BASE, date(2026, 1, 2))  # 1 dia
report("IOF dia 1 = 96% do ganho", approx(r2.iof, 96.0))
report("IR sobre ganho pós-IOF",   approx(r2.ir, 0.70))
report("net_gain com IOF+IR",      approx(r2.net_gain, 3.30))

r3 = calc_renda_fixa(1000.0, 0.0, BASE, date(2026, 3, 15))
report("ganho zero sem imposto",     r3.ir == 0.0 and r3.effective_rate == 0.0)

r4 = calc_renda_fixa(1000.0, 50.0, BASE, date(2026, 2, 1))
report("details days_held = 31",    r4.details["days_held"] == 31)

r5 = calc_renda_fixa(1000.0, 100.0, BASE, date(2026, 4, 1))
report("effective_rate ~17.5%",     approx(r5.effective_rate, 17.5, tol=0.5))


# ── calc_lci_lca ──────────────────────────────────────────────────────────────
print("\n=== 3. calc_lci_lca ===\n")

r = calc_lci_lca(5000.0, 200.0)
report("IR = 5% sobre ganho",      approx(r.ir, 10.0))
report("net_gain correto",          approx(r.net_gain, 190.0))
report("sem IOF",                   r.iof == 0.0)
report("effective_rate = 5%",       approx(r.effective_rate, 5.0))

r2 = calc_lci_lca(5000.0, 0.0)
report("ganho zero -> IR zero",     r2.ir == 0.0 and r2.effective_rate == 0.0)

r3 = calc_lci_lca(1000.0, 50.0)
report("details menciona reforma", "reforma" in r3.details["note"].lower())


# ── calc_acoes ────────────────────────────────────────────────────────────────
print("\n=== 4. calc_acoes ===\n")

r = calc_acoes(500.0, quarterly_sales=30_000.0)
report("isento abaixo de R$60k",   r.ir == 0.0 and r.details["exempt"] is True)

r2 = calc_acoes(500.0, quarterly_sales=60_000.0)
report("isento exatamente R$60k",  r2.ir == 0.0)

r3 = calc_acoes(1000.0, quarterly_sales=70_000.0)
report("tributado acima R$60k",    approx(r3.ir, 175.0) and r3.details["exempt"] is False)

r4 = calc_acoes(1000.0, quarterly_sales=10_000.0, is_day_trade=True)
report("day trade -> 20%",          approx(r4.ir, 200.0) and r4.details["ir_rate_pct"] == 20.0)

r5 = calc_acoes(1000.0, quarterly_sales=80_000.0, carryforward_loss=400.0)
report("carryforward reduz base",  approx(r5.ir, 105.0))

r6 = calc_acoes(300.0, quarterly_sales=80_000.0, carryforward_loss=500.0)
report("carryforward >= ganho -> IR zero",  r6.ir == 0.0)
report("carryforward_used não excede ganho", approx(r6.details["carryforward_used"], 300.0))

r7 = calc_acoes(500.0, quarterly_sales=10_000.0, is_day_trade=True)
report("day trade não isento abaixo R$60k", approx(r7.ir, 100.0))


# ── calc_fii ──────────────────────────────────────────────────────────────────
print("\n=== 5. calc_fii ===\n")

r = calc_fii(dividend=200.0, capital_gain=300.0)
report("dividendo 5%",              approx(r.details["ir_dividend"], 10.0))
report("ganho capital 17.5%",       approx(r.details["ir_capital"], 52.5))
report("IR total correto",          approx(r.ir, 62.5))
report("net_gain = gross - ir",     approx(r.net_gain, r.gross_gain - r.ir))

r2 = calc_fii(dividend=0.0, capital_gain=1000.0, carryforward_loss=400.0)
report("carryforward reduz ganho capital",  approx(r2.details["ir_capital"], 105.0))

r3 = calc_fii(dividend=500.0, capital_gain=0.0)
report("apenas dividendo",          approx(r3.ir, 25.0) and approx(r3.effective_rate, 5.0))

r4 = calc_fii(dividend=0.0, capital_gain=0.0)
report("sem ganho -> effective_rate 0", r4.effective_rate == 0.0)


# ── calc_crypto ───────────────────────────────────────────────────────────────
print("\n=== 6. calc_crypto ===\n")

r = calc_crypto(500.0, monthly_sales=20_000.0)
report("isento abaixo R$35k",      r.ir == 0.0 and r.details["exempt"] is True)

r2 = calc_crypto(500.0, monthly_sales=35_000.0)
report("isento exatamente R$35k",  r2.ir == 0.0)

r3 = calc_crypto(1000.0, monthly_sales=40_000.0)
report("tributado acima R$35k",    approx(r3.ir, 175.0) and r3.details["exempt"] is False)

r4 = calc_crypto(1000.0, monthly_sales=40_000.0, carryforward_loss=500.0)
report("carryforward reduz base",  approx(r4.ir, 87.5))

r5 = calc_crypto(200.0, monthly_sales=40_000.0, carryforward_loss=500.0)
report("carryforward >= ganho -> IR zero", r5.ir == 0.0)


# ── carryforward_remaining ────────────────────────────────────────────────────
print("\n=== 7. carryforward_remaining ===\n")

ref = date(2026, 1, 1)

r = carryforward_remaining([(date(2023, 1, 1), 1000.0)], ref)
report("prejuízo dentro de 5 anos válido",  approx(r, 1000.0))

r2 = carryforward_remaining([(date(2020, 1, 1), 1000.0)], ref)
report("prejuízo >5 anos excluído",          approx(r2, 0.0))

r3 = carryforward_remaining([
    (date(2023, 6, 1), 500.0),
    (date(2025, 3, 1), 300.0),
    (date(2019, 1, 1), 999.0),   # expirado
], ref)
report("múltiplos prejuízos somados",        approx(r3, 800.0))

r4 = carryforward_remaining([], ref)
report("lista vazia retorna 0",              r4 == 0.0)

# max_years customizável: loss de 6 meses atrás
r5 = carryforward_remaining([(date(2025, 6, 1), 500.0)], ref, max_years=1)
report("max_years=1 inclui loss de 0.6 anos", approx(r5, 500.0))

r6 = carryforward_remaining([(date(2024, 1, 1), 500.0)], ref, max_years=1)
report("max_years=1 exclui loss de 2 anos",   approx(r6, 0.0))


# ── Resumo ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
print(f"  TOTAL: {passed} passed / {failed} failed / {len(results)} tests")
if failed:
    print("\n  Falhas:")
    for name, ok in results:
        if not ok:
            print(f"    - {name}")
print("=" * 55)

sys.exit(0 if failed == 0 else 1)
