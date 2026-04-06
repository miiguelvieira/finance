"""Testes Fase 2 — Categorizer + TransactionService + router."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.database import get_engine, init_db, make_session_factory
from src.core.exceptions import AccountNotFound
from src.accounts.service import AccountService
from src.transactions.categorizer import Categorizer
from src.transactions.service import TransactionService

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


def make_services():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    db = factory()
    return AccountService(db), TransactionService(db), eng


# ── 1. Categorizer — regras regex ─────────────────────────────────────────────
print("\n=== 1. Categorizer — classificação automática ===\n")

cat = Categorizer()

FIXTURES = [
    ("Pagamento salário referência março", "salario"),
    ("iFood pedido #12345", "alimentacao"),
    ("Uber corrida zona sul", "transporte"),
    ("Netflix assinatura mensal", "lazer"),
    ("Supermercado Carrefour", "alimentacao"),
    ("Farmácia Drogasil compra", "saude"),
    ("Aluguel apartamento março", "moradia"),
    ("Spotify Premium", "lazer"),
    ("Gasolina Posto Shell", "transporte"),
    ("Nubank fatura cartão", "outros"),         # sem regra específica
    ("Faculdade mensalidade", "educacao"),
    ("Smart Fit academia mensal", "saude"),
    ("Zara roupas shopping", "vestuario"),
    ("Tesouro Direto aplicação", "investimentos"),
    ("Dividendos PETR4", "dividendos"),
    ("Freelance desenvolvimento web", "freelance"),
    ("Conta de luz CELPE", "moradia"),
    ("Tim celular fatura", "assinaturas"),
    ("Estacionamento shoping", "transporte"),
    ("McDonald's lanche", "alimentacao"),
]

for desc, expected in FIXTURES:
    category, _ = cat.classify(desc)
    report(f"'{desc[:40]}' → {expected}", category == expected, f"got={category}")


# ── 2. TransactionService — CRUD ─────────────────────────────────────────────
print("\n=== 2. TransactionService — CRUD ===\n")

acc_svc, tx_svc, eng = make_services()
acc = acc_svc.create("Nubank", "Nubank", "checking", balance=2000.0)
acc_svc.db.commit()

today = date.today()

# Cria transações
tx1 = tx_svc.create(acc.id, -50.0, "iFood pedido pizza", today)
tx_svc.db.commit()
report("create auto-categoriza iFood → alimentacao", tx1.category == "alimentacao", f"cat={tx1.category}")

tx2 = tx_svc.create(acc.id, -120.0, "Conta de luz", today, category="moradia")
tx_svc.db.commit()
report("create com categoria explícita", tx2.category == "moradia")

tx3 = tx_svc.create(acc.id, 5000.0, "Salário mês", today)
tx_svc.db.commit()
report("create salário → salario", tx3.category == "salario", f"cat={tx3.category}")

# List filters
all_txs = tx_svc.list()
report("list retorna todas as transações", len(all_txs) == 3, f"count={len(all_txs)}")

filtered = tx_svc.list(category="alimentacao")
report("list filtro por categoria funciona", len(filtered) == 1)

filtered_acc = tx_svc.list(account_id=acc.id)
report("list filtro por account_id funciona", len(filtered_acc) == 3)

# Monthly summary
summary = tx_svc.monthly_summary(today.year, today.month)
report("monthly_summary retorna income > 0", summary["income"] > 0, f"income={summary['income']}")
report("monthly_summary retorna expenses < 0", summary["expenses"] < 0, f"expenses={summary['expenses']}")
report("by_category contém alimentacao", "alimentacao" in summary["by_category"])

# Delete
tx_svc.delete(tx1.id)
tx_svc.db.commit()
report("delete remove a transação", len(tx_svc.list()) == 2)

# Conta inexistente
try:
    tx_svc.create(9999, -10.0, "Teste", today)
    report("AccountNotFound em conta inexistente", False)
except AccountNotFound:
    report("AccountNotFound em conta inexistente", True)

tx_svc.db.close()
eng.dispose()


# ── 3. Router /transactions ───────────────────────────────────────────────────
print("\n=== 3. Router /transactions ===\n")

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
    r = tc.post("/accounts/", json={"name": "CC", "bank_name": "Nubank",
                                     "account_type": "credit_card", "balance": 0.0})
    acc_id = r.json()["id"]

    # Cria transação
    r = tc.post("/transactions/", json={
        "account_id": acc_id,
        "amount": -200.0,
        "description": "Supermercado Pão de Açúcar",
        "transaction_date": str(today),
    })
    report("POST /transactions/ retorna 201", r.status_code == 201, f"status={r.status_code}")
    report("categoria auto-detectada via API", r.json()["category"] == "alimentacao",
           f"cat={r.json().get('category')}")
    tx_id = r.json()["id"]

    # Lista
    r = tc.get("/transactions/")
    report("GET /transactions/ retorna lista", r.status_code == 200 and len(r.json()) == 1)

    # Filtro
    r = tc.get("/transactions/?category=alimentacao")
    report("GET /transactions/?category filtra corretamente", len(r.json()) == 1)

    # Summary
    r = tc.get(f"/transactions/summary/{today.year}/{today.month}")
    report("GET /transactions/summary retorna 200", r.status_code == 200)
    report("summary contém expenses", "expenses" in r.json())

    # Delete
    r = tc.delete(f"/transactions/{tx_id}")
    report("DELETE /transactions/{id} retorna 204", r.status_code == 204)

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
