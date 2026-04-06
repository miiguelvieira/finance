"""Testes Fase 2 — AccountService + router."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.database import get_engine, init_db, make_session_factory
from src.core.exceptions import AccountNotFound, InsufficientBalance
from src.accounts.service import AccountService
from src.core.models import BalanceHistory, Transaction

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


def make_svc():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    db = factory()
    return AccountService(db), eng


# ── 1. CRUD básico ────────────────────────────────────────────────────────────
print("\n=== 1. AccountService — CRUD ===\n")

svc, eng = make_svc()

acc = svc.create("Nubank Conta", "Nubank", "checking", balance=1000.0)
svc.db.commit()

report("create retorna Account", acc.id is not None, f"id={acc.id}")
report("balance inicial correto", acc.balance == 1000.0)
report("is_active=True por padrão", acc.is_active is True)

acc2 = svc.get(acc.id)
report("get retorna a conta criada", acc2.name == "Nubank Conta")

accounts = svc.list()
report("list retorna contas ativas", len(accounts) == 1)

svc.update(acc.id, name="Nubank CC")
svc.db.commit()
report("update altera o nome", svc.get(acc.id).name == "Nubank CC")

svc.deactivate(acc.id)
svc.db.commit()
report("deactivate remove da listagem padrão", len(svc.list()) == 0)
report("deactivate não apaga (include_inactive)", len(svc.list(include_inactive=True)) == 1)

try:
    svc.get(9999)
    report("get conta inexistente lança AccountNotFound", False)
except AccountNotFound:
    report("get conta inexistente lança AccountNotFound", True)

svc.db.close()
eng.dispose()


# ── 2. Saldo e BalanceHistory ─────────────────────────────────────────────────
print("\n=== 2. update_balance + BalanceHistory ===\n")

svc, eng = make_svc()
acc = svc.create("Itaú", "Itaú", "savings", balance=500.0)
svc.db.commit()

svc.update_balance(acc.id, 750.0, source="manual")
svc.db.commit()

report("balance atualizado", svc.get(acc.id).balance == 750.0)

history = svc.db.query(BalanceHistory).filter(BalanceHistory.account_id == acc.id).all()
report("BalanceHistory tem 2 registros (create + update)", len(history) == 2, f"count={len(history)}")
report("último registro é 750.0", history[-1].balance == 750.0)
report("source registrado como 'manual'", history[-1].source == "manual")

svc.db.close()
eng.dispose()


# ── 3. Net worth ──────────────────────────────────────────────────────────────
print("\n=== 3. net_worth ===\n")

svc, eng = make_svc()
svc.create("Banco A", "A", "checking", balance=1000.0)
svc.create("Banco B", "B", "savings", balance=500.0)
svc.create("Banco C", "C", "checking", balance=250.0)
svc.db.commit()

nw = svc.net_worth()
report("net_worth soma todos os saldos", nw == 1750.0, f"net_worth={nw}")

svc.db.close()
eng.dispose()


# ── 4. Transferência ──────────────────────────────────────────────────────────
print("\n=== 4. transfer ===\n")

svc, eng = make_svc()
origem = svc.create("Origem", "X", "checking", balance=1000.0)
destino = svc.create("Destino", "Y", "checking", balance=200.0)
svc.db.commit()

debit, credit = svc.transfer(origem.id, destino.id, 300.0)
svc.db.commit()

report("debit amount é negativo", debit.amount == -300.0, f"debit.amount={debit.amount}")
report("credit amount é positivo", credit.amount == 300.0)
report("transfer_ref igual nos dois lados", debit.transfer_ref == credit.transfer_ref)
report("saldo origem decrementou", svc.get(origem.id).balance == 700.0)
report("saldo destino incrementou", svc.get(destino.id).balance == 500.0)
report("categoria é 'transferencia'", debit.category == "transferencia")

# Saldo insuficiente
try:
    svc.transfer(origem.id, destino.id, 9999.0)
    report("InsufficientBalance lançado", False)
except InsufficientBalance:
    report("InsufficientBalance lançado", True)

svc.db.close()
eng.dispose()


# ── 5. Router /accounts ───────────────────────────────────────────────────────
print("\n=== 5. Router /accounts ===\n")

from fastapi.testclient import TestClient
from src.api.main import app
from src.core.database import get_db

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
    r = tc.post("/accounts/", json={"name": "NuConta", "bank_name": "Nubank",
                                     "account_type": "checking", "balance": 500.0})
    report("POST /accounts/ retorna 201", r.status_code == 201, f"status={r.status_code}")
    acc_id = r.json()["id"]

    # Lista
    r = tc.get("/accounts/")
    report("GET /accounts/ retorna lista", r.status_code == 200 and len(r.json()) == 1)

    # Net worth
    r = tc.get("/accounts/net-worth")
    report("GET /accounts/net-worth retorna 500.0", r.json()["net_worth"] == 500.0)

    # Atualiza saldo
    r = tc.patch(f"/accounts/{acc_id}/balance", json={"balance": 800.0})
    report("PATCH /balance retorna 200", r.status_code == 200)
    report("balance atualizado via API", r.json()["balance"] == 800.0)

    # 404
    r = tc.get("/accounts/9999")
    report("GET conta inexistente retorna 404", r.status_code == 404)

    # Transferência
    r2 = tc.post("/accounts/", json={"name": "Poupança", "bank_name": "Itaú",
                                      "account_type": "savings", "balance": 100.0})
    acc2_id = r2.json()["id"]
    r = tc.post("/accounts/transfer", json={"from_account_id": acc_id,
                                             "to_account_id": acc2_id, "amount": 200.0})
    report("POST /transfer retorna 201", r.status_code == 201)

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

import sys
sys.exit(0 if failed == 0 else 1)
