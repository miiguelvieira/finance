"""Testes Fase 4 — ProjectionEngine (100% coverage obrigatoria).

Cobre:
  1. compute() estatico com inputs conhecidos — verificacoes numericas exatas
  2. Banda: optimistic >= base >= pessimistic para todos os meses
  3. Tendencias: growing / shrinking / stable
  4. Acumulacao correta mes a mes
  5. Variancia aplicada separadamente a income e expenses
  6. Parcelas fixas (sem variancia)
  7. project() com banco real (dados injetados)
  8. _avg_monthly_expenses: fallback vazio, exclusao de categorias/parcelas
  9. Router /projections GET e POST /simulate
"""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dateutil.relativedelta import relativedelta
from src.core.database import get_db, get_engine, init_db, make_session_factory
from src.accounts.service import AccountService
from src.installments.service import IncomeSourceService, InstallmentService
from src.transactions.service import TransactionService
from src.projections.engine import ProjectionEngine, _INCOME_CATEGORIES

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


# ── 1. compute() estatico — valores numericos exatos ─────────────────────────
print("\n=== 1. compute() estatico — numerica exata ===\n")

REF_DATE = date(2026, 1, 1)

result = ProjectionEngine.compute(
    current_balance=10_000.0,
    monthly_income=5_000.0,
    avg_monthly_expenses=3_000.0,
    monthly_installments=500.0,
    variance_pct=0.10,
    months_forward=3,
    start_date=REF_DATE,
)

# base_delta = 5000 - 3000 - 500 = 1500
# opt_delta  = 5000*1.1 - 3000*0.9 - 500 = 5500 - 2700 - 500 = 2300
# pess_delta = 5000*0.9 - 3000*1.1 - 500 = 4500 - 3300 - 500 = 700

report("3 meses gerados", len(result.months) == 3)
report("mes 1 base = 11500.0", result.months[0].base == 11_500.0, f"got={result.months[0].base}")
report("mes 1 optimistic = 12300.0", result.months[0].optimistic == 12_300.0, f"got={result.months[0].optimistic}")
report("mes 1 pessimistic = 10700.0", result.months[0].pessimistic == 10_700.0, f"got={result.months[0].pessimistic}")
report("mes 2 base = 13000.0", result.months[1].base == 13_000.0, f"got={result.months[1].base}")
report("mes 3 base = 14500.0", result.months[2].base == 14_500.0, f"got={result.months[2].base}")
report("delta_base mes 1 = 1500.0", result.months[0].delta_base == 1_500.0, f"got={result.months[0].delta_base}")
report("trend = growing", result.trend == "growing", f"got={result.trend}")
report("current_balance = 10000.0", result.current_balance == 10_000.0)
report("monthly_income = 5000.0", result.monthly_income == 5_000.0)
report("avg_monthly_expenses = 3000.0", result.avg_monthly_expenses == 3_000.0)
report("monthly_installments = 500.0", result.monthly_installments == 500.0)


# ── 2. Banda: opt >= base >= pess em todos os meses ───────────────────────────
print("\n=== 2. Banda opt >= base >= pess ===\n")

result_band = ProjectionEngine.compute(
    current_balance=5_000.0,
    monthly_income=4_000.0,
    avg_monthly_expenses=2_000.0,
    monthly_installments=300.0,
    variance_pct=0.15,
    months_forward=12,
    start_date=REF_DATE,
)

all_opt_ge_base = all(m.optimistic >= m.base for m in result_band.months)
all_base_ge_pess = all(m.base >= m.pessimistic for m in result_band.months)
report("optimistic >= base em todos os 12 meses", all_opt_ge_base)
report("base >= pessimistic em todos os 12 meses", all_base_ge_pess)


# ── 3. Tendencias ─────────────────────────────────────────────────────────────
print("\n=== 3. classify_trend ===\n")

report("delta +1500 -> growing", ProjectionEngine._classify_trend(1500.0) == "growing")
report("delta -1500 -> shrinking", ProjectionEngine._classify_trend(-1500.0) == "shrinking")
report("delta +10 -> stable", ProjectionEngine._classify_trend(10.0) == "stable")
report("delta -10 -> stable", ProjectionEngine._classify_trend(-10.0) == "stable")
report("delta exato +50 -> stable", ProjectionEngine._classify_trend(50.0) == "stable")
report("delta exato -50 -> stable", ProjectionEngine._classify_trend(-50.0) == "stable")
report("delta +51 -> growing", ProjectionEngine._classify_trend(51.0) == "growing")
report("delta -51 -> shrinking", ProjectionEngine._classify_trend(-51.0) == "shrinking")


# ── 4. Acumulacao correta ─────────────────────────────────────────────────────
print("\n=== 4. Acumulacao mensal ===\n")

result_acc = ProjectionEngine.compute(
    current_balance=1_000.0,
    monthly_income=1_000.0,
    avg_monthly_expenses=0.0,
    monthly_installments=0.0,
    variance_pct=0.0,   # sem variancia para verificar acumulacao pura
    months_forward=5,
    start_date=REF_DATE,
)

# Com v=0: base=opt=pess, delta=1000 por mes
for i, m in enumerate(result_acc.months):
    expected = 1_000.0 + (i + 1) * 1_000.0
    report(f"mes {i+1} acumulado = {expected}", m.base == expected, f"got={m.base}")
    report(f"mes {i+1} opt == base com v=0", m.optimistic == m.base)
    report(f"mes {i+1} pess == base com v=0", m.pessimistic == m.base)


# ── 5. Parcelas fixas (sem variancia) ─────────────────────────────────────────
print("\n=== 5. Parcelas fixas sem variancia ===\n")

# Com income=0, expenses=0, apenas parcelas
# opt_delta = pess_delta = base_delta = -installs
result_install = ProjectionEngine.compute(
    current_balance=12_000.0,
    monthly_income=0.0,
    avg_monthly_expenses=0.0,
    monthly_installments=1_000.0,
    variance_pct=0.50,  # variancia alta — parcelas nao devem variar
    months_forward=2,
    start_date=REF_DATE,
)

report("base mes 1 com so parcelas = 11000", result_install.months[0].base == 11_000.0)
report("opt == base quando so parcelas (v alto)", result_install.months[0].optimistic == result_install.months[0].base,
       f"opt={result_install.months[0].optimistic} base={result_install.months[0].base}")
report("pess == base quando so parcelas (v alto)", result_install.months[0].pessimistic == result_install.months[0].base)


# ── 6. Cenario de shrinking ───────────────────────────────────────────────────
print("\n=== 6. Cenario shrinking ===\n")

result_shrink = ProjectionEngine.compute(
    current_balance=5_000.0,
    monthly_income=2_000.0,
    avg_monthly_expenses=3_000.0,
    monthly_installments=0.0,
    variance_pct=0.10,
    months_forward=3,
    start_date=REF_DATE,
)
# base_delta = 2000 - 3000 = -1000
report("trend = shrinking", result_shrink.trend == "shrinking")
report("saldo cai mes a mes", result_shrink.months[0].base < result_shrink.current_balance)
report("pess cai mais rapido que base", result_shrink.months[2].pessimistic < result_shrink.months[2].base)


# ── 7. Labels e datas ─────────────────────────────────────────────────────────
print("\n=== 7. Labels e datas ===\n")

result_labels = ProjectionEngine.compute(
    current_balance=0.0,
    monthly_income=1000.0,
    avg_monthly_expenses=0.0,
    monthly_installments=0.0,
    months_forward=12,
    start_date=date(2026, 1, 1),
)

report("mes 1 label = Fev/2026", result_labels.months[0].label == "Fev/2026", f"got={result_labels.months[0].label}")
report("mes 12 label = Jan/2027", result_labels.months[11].label == "Jan/2027", f"got={result_labels.months[11].label}")
report("mes 1 month=2 year=2026", result_labels.months[0].month == 2 and result_labels.months[0].year == 2026)


# ── 8. project() com banco — dados injetados ─────────────────────────────────
print("\n=== 8. project() com banco real ===\n")


def make_db():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    return factory(), eng


db, eng = make_db()
acc_svc = AccountService(db)
tx_svc = TransactionService(db)
inc_svc = IncomeSourceService(db)
inst_svc = InstallmentService(db)

acc = acc_svc.create("Corrente", "Nubank", "checking", balance=8_000.0)
db.commit()

# Injeta 3 meses de despesas (nao-parcelas)
today = date.today()
for m in range(3):
    d = today - relativedelta(months=m)
    tx_svc.create(acc.id, -2_000.0, "Aluguel e contas", d, category="moradia")
    tx_svc.create(acc.id, -500.0, "iFood pedidos", d, category="alimentacao")
db.commit()
# avg_expenses esperado: (2500 + 2500 + 2500) / 3 = 2500

inc_svc.create("Salario", 7_000.0)
db.commit()

engine = ProjectionEngine(db, months_forward=3, variance_pct=0.10)
res = engine.project()

report("current_balance = 8000.0", res.current_balance == 8_000.0, f"got={res.current_balance}")
report("monthly_income = 7000.0", res.monthly_income == 7_000.0)
report("avg_monthly_expenses = 2500.0", res.avg_monthly_expenses == 2_500.0, f"got={res.avg_monthly_expenses}")
report("monthly_installments = 0.0", res.monthly_installments == 0.0)
report("3 meses projetados", len(res.months) == 3)
# base_delta = 7000 - 2500 - 0 = 4500
report("trend = growing", res.trend == "growing")
report("mes 1 base = 12500.0", res.months[0].base == 12_500.0, f"got={res.months[0].base}")

db.close()
eng.dispose()


# ── 9. _avg_monthly_expenses — exclusoes ──────────────────────────────────────
print("\n=== 9. exclusoes no avg_monthly_expenses ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
tx_svc = TransactionService(db)
inst_svc = InstallmentService(db)

acc = acc_svc.create("CC", "Banco", "checking", balance=5_000.0)
db.commit()

today = date.today()

# Despesa real (deve entrar)
tx_svc.create(acc.id, -1_000.0, "Supermercado", today, category="alimentacao")
# Salario (categoria renda — deve ser excluido)
tx_svc.create(acc.id, 5_000.0, "Salario", today, category="salario")
# Transferencia (deve ser excluida)
tx_svc.create(acc.id, -500.0, "Ted para poupanca", today, category="transferencia")
# Investimento (deve ser excluido)
tx_svc.create(acc.id, -2_000.0, "Aporte CDB", today, category="investimentos")
db.commit()

# Cria parcelamento (transacoes de parcelas devem ser excluidas do avg)
inst = inst_svc.create(acc.id, "Notebook", 3_000.0, 3, today)
db.commit()

engine = ProjectionEngine(db, history_months=1)
avg = engine._avg_monthly_expenses()
report("avg exclui salario, transferencia, investimentos e parcelas",
       avg == 1_000.0, f"got={avg}")

# Fallback vazio
db2, eng2 = make_db()
engine2 = ProjectionEngine(db2, history_months=3)
report("avg = 0.0 com banco vazio", engine2._avg_monthly_expenses() == 0.0)
db2.close()
eng2.dispose()

# _INCOME_CATEGORIES contem as categorias corretas
for cat in ("salario", "freelance", "dividendos", "transferencia", "investimentos"):
    report(f"_INCOME_CATEGORIES contem '{cat}'", cat in _INCOME_CATEGORIES)

db.close()
eng.dispose()


# ── 10. Router GET /projections + POST /simulate ─────────────────────────────
print("\n=== 10. Routers /projections ===\n")

from fastapi.testclient import TestClient
from src.api.main import app

test_eng = get_engine("sqlite:///:memory:")
init_db(test_eng)
test_factory = make_session_factory(test_eng)


def _override():
    db = test_factory()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override

with TestClient(app) as tc:
    # Cria conta e renda para GET /projections
    tc.post("/accounts/", json={"name": "Corrente", "bank_name": "Nubank",
                                 "account_type": "checking", "balance": 5000.0})
    tc.post("/income-sources/", json={"name": "Salario", "amount": 4000.0})

    r = tc.get("/projections/")
    report("GET /projections/ retorna 200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    report("resposta contem months", "months" in data)
    report("resposta contem trend", "trend" in data)
    report("12 meses retornados", len(data["months"]) == 12, f"count={len(data.get('months', []))}")

    r = tc.get("/projections/?months=6&variance=0.20")
    report("GET /projections/?months=6 retorna 6 meses", len(r.json()["months"]) == 6)

    r = tc.post(
        "/projections/simulate"
        "?current_balance=10000"
        "&monthly_income=5000"
        "&avg_monthly_expenses=3000"
        "&monthly_installments=500"
        "&months=3"
        "&variance=0.10"
    )
    report("POST /simulate retorna 200", r.status_code == 200, f"status={r.status_code}")
    sim = r.json()
    report("simulate mes 1 base = 11500.0", sim["months"][0]["base"] == 11_500.0,
           f"got={sim['months'][0].get('base')}")
    report("simulate trend = growing", sim["trend"] == "growing")

app.dependency_overrides.clear()
test_eng.dispose()


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
