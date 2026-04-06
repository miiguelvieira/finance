"""Testes Fase 3 — InstallmentService + IncomeSourceService + routers."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dateutil.relativedelta import relativedelta
from src.core.database import get_engine, get_db, init_db, make_session_factory
from src.core.exceptions import AccountNotFound, InstallmentNotFound
from src.accounts.service import AccountService
from src.installments.service import IncomeSourceService, InstallmentService
from src.core.models import Transaction

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


def make_db():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    db = factory()
    return db, eng


# ── 1. InstallmentService — criação ──────────────────────────────────────────
print("\n=== 1. InstallmentService — criacao ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
svc = InstallmentService(db)

acc = acc_svc.create("Cartao Nubank", "Nubank", "credit_card", balance=0.0)
db.commit()

START = date(2026, 1, 10)
inst = svc.create(
    account_id=acc.id,
    description="iPhone 15",
    total_amount=6000.0,
    installment_count=12,
    start_date=START,
    category="vestuario",
)
db.commit()

report("create retorna Installment", inst.id is not None)
report("installment_value = 500.0", inst.installment_value == 500.0, f"val={inst.installment_value}")
report("paid_count = 0", inst.paid_count == 0)
report("is_closed = False", inst.is_closed is False)

# 12 transações criadas
txs = db.query(Transaction).filter(Transaction.installment_id == inst.id).all()
report("12 transacoes criadas", len(txs) == 12, f"count={len(txs)}")
report("primeira transacao em 2026-01-10", txs[0].transaction_date == START, f"date={txs[0].transaction_date}")
report("ultima transacao em 2026-12-10", txs[-1].transaction_date == date(2026, 12, 10),
       f"date={txs[-1].transaction_date}")
report("amount de cada tx = -500.0", all(t.amount == -500.0 for t in txs))
report("descricao tem numeracao (1/12)", "1/12" in txs[0].description, f"desc={txs[0].description}")
report("categoria propagada", all(t.category == "vestuario" for t in txs))

db.close()
eng.dispose()


# ── 2. mark_paid + fechamento automático ─────────────────────────────────────
print("\n=== 2. mark_paid + fechamento automatico ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
svc = InstallmentService(db)

acc = acc_svc.create("CC", "Banco", "credit_card")
db.commit()
inst = svc.create(acc.id, "Notebook", 3000.0, 3, date(2026, 1, 1))
db.commit()

inst = svc.mark_paid(inst.id)
db.commit()
report("mark_paid incrementa paid_count", inst.paid_count == 1)
report("nao fecha com 1/3 pago", inst.is_closed is False)

svc.mark_paid(inst.id)
inst = svc.mark_paid(inst.id)
db.commit()
report("fecha ao atingir installment_count", inst.is_closed is True, f"paid={inst.paid_count}")

# enrich
enriched = InstallmentService.enrich(inst)
report("enrich remaining_count=0 quando fechado", enriched["remaining_count"] == 0)
report("enrich next_due_date=None quando fechado", enriched["next_due_date"] is None)

# AccountNotFound
try:
    svc.create(9999, "X", 100.0, 2, date.today())
    report("AccountNotFound na conta inexistente", False)
except AccountNotFound:
    report("AccountNotFound na conta inexistente", True)

# InstallmentNotFound
try:
    svc.mark_paid(9999)
    report("InstallmentNotFound em id inexistente", False)
except InstallmentNotFound:
    report("InstallmentNotFound em id inexistente", True)

db.close()
eng.dispose()


# ── 3. get_upcoming + monthly_commitment ─────────────────────────────────────
print("\n=== 3. get_upcoming + monthly_commitment ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
svc = InstallmentService(db)

acc = acc_svc.create("CC", "Banco", "credit_card")
db.commit()

today = date.today()
inst1 = svc.create(acc.id, "TV", 2400.0, 12, today)          # 12 parcelas a partir de hoje
inst2 = svc.create(acc.id, "Geladeira", 1800.0, 6, today)    # 6 parcelas
db.commit()

upcoming = svc.get_upcoming(days=60)
report("get_upcoming retorna parcelas nos proximos 60 dias",
       len(upcoming) >= 2, f"count={len(upcoming)}")
report("upcoming tem due_date", all("due_date" in u for u in upcoming))
report("upcoming tem amount negativo", all(u["amount"] < 0 for u in upcoming))

commitment = svc.monthly_commitment()
report("monthly_commitment = 500.0 (200+300)", commitment == 500.0, f"val={commitment}")

# list exclui fechados por padrão
svc.close(inst1.id)
db.commit()
open_list = svc.list()
report("list exclui fechados por padrao", len(open_list) == 1, f"count={len(open_list)}")
all_list = svc.list(include_closed=True)
report("list(include_closed=True) inclui todos", len(all_list) == 2, f"count={len(all_list)}")

db.close()
eng.dispose()


# ── 4. IncomeSourceService ────────────────────────────────────────────────────
print("\n=== 4. IncomeSourceService ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
inc_svc = IncomeSourceService(db)

acc = acc_svc.create("Corrente", "Nubank", "checking")
db.commit()

s1 = inc_svc.create("Salario CLT", 8000.0, day_of_month=5, account_id=acc.id)
s2 = inc_svc.create("Freela Mensal", 2000.0, day_of_month=15)
db.commit()

report("create IncomeSource com account_id", s1.id is not None)
report("create IncomeSource sem account_id", s2.account_id is None)

sources = inc_svc.list()
report("list retorna 2 fontes ativas", len(sources) == 2, f"count={len(sources)}")

total = inc_svc.total_monthly()
report("total_monthly = 10000.0", total == 10000.0, f"val={total}")

inc_svc.deactivate(s2.id)
db.commit()
report("deactivate remove da listagem", len(inc_svc.list()) == 1)
report("total_monthly apos deactivate = 8000.0", inc_svc.total_monthly() == 8000.0)

db.close()
eng.dispose()


# ── 5. Routers /installments + /income-sources ───────────────────────────────
print("\n=== 5. Routers /installments e /income-sources ===\n")

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
    # Cria conta
    r = tc.post("/accounts/", json={"name": "CC Visa", "bank_name": "Bradesco",
                                     "account_type": "credit_card", "balance": 0.0})
    acc_id = r.json()["id"]

    # Cria parcelamento
    r = tc.post("/installments/", json={
        "account_id": acc_id,
        "description": "MacBook Pro",
        "total_amount": 15000.0,
        "installment_count": 10,
        "start_date": str(date.today()),
        "category": "educacao",
    })
    report("POST /installments/ retorna 201", r.status_code == 201, f"status={r.status_code}")
    inst_id = r.json()["id"]
    report("installment_value = 1500.0", r.json()["installment_value"] == 1500.0)
    report("remaining_count = 10", r.json()["remaining_count"] == 10)

    # Lista
    r = tc.get("/installments/")
    report("GET /installments/ retorna lista", r.status_code == 200 and len(r.json()) == 1)

    # Mark paid
    r = tc.post(f"/installments/{inst_id}/mark-paid")
    report("POST /mark-paid retorna 200", r.status_code == 200)
    report("paid_count = 1 apos mark-paid", r.json()["paid_count"] == 1)
    report("remaining_count = 9 apos mark-paid", r.json()["remaining_count"] == 9)

    # Upcoming
    r = tc.get("/installments/upcoming?days=60")
    report("GET /upcoming retorna 200", r.status_code == 200)

    # Monthly commitment
    r = tc.get("/installments/monthly-commitment")
    report("GET /monthly-commitment retorna 200", r.status_code == 200)
    report("monthly_commitment = 1500.0", r.json()["monthly_commitment"] == 1500.0)

    # Income sources
    r = tc.post("/income-sources/", json={"name": "Salario", "amount": 7000.0, "day_of_month": 5})
    report("POST /income-sources/ retorna 201", r.status_code == 201, f"status={r.status_code}")
    src_id = r.json()["id"]

    r = tc.get("/income-sources/total-monthly")
    report("GET /income-sources/total-monthly = 7000.0", r.json()["total_monthly"] == 7000.0)

    r = tc.delete(f"/income-sources/{src_id}")
    report("DELETE /income-sources/ retorna 204", r.status_code == 204)
    report("total_monthly = 0 apos deactivate", tc.get("/income-sources/total-monthly").json()["total_monthly"] == 0.0)

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
