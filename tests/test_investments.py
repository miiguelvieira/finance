"""Testes Fase 5 — InvestmentService + router + flashcards."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.database import get_db, get_engine, init_db, make_session_factory
from src.accounts.service import AccountService
from src.investments.service import InvestmentNotFound, InvestmentService
from src.investments.flashcards import get_all, get_by_id, get_by_tag

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


def make_db():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    db = factory()
    return db, eng


# ── 1. InvestmentService — CRUD ───────────────────────────────────────────────
print("\n=== 1. InvestmentService — CRUD ===\n")

db, eng = make_db()
svc = InvestmentService(db)

inv = svc.create(
    name="CDB Banco XYZ",
    asset_type="renda_fixa",
    principal=10_000.0,
    current_value=10_500.0,
    purchase_date=date(2025, 1, 15),
)
db.commit()

report("create retorna Investment",    inv.id is not None)
report("asset_type correto",           inv.asset_type == "renda_fixa")
report("principal correto",            inv.principal == 10_000.0)

fetched = svc.get(inv.id)
report("get retorna o mesmo objeto",   fetched.id == inv.id)

try:
    svc.get(9999)
    report("get inexistente lança exceção", False)
except InvestmentNotFound:
    report("get inexistente lança InvestmentNotFound", True)

updated = svc.update(inv.id, current_value=11_000.0)
db.commit()
report("update altera current_value",  updated.current_value == 11_000.0)

inv2 = svc.create("FII XPML11", "fii", 2000.0, 2200.0, date(2025, 2, 1))
db.commit()
all_inv = svc.list()
report("list retorna todos",           len(all_inv) == 2)

rf_only = svc.list(asset_type="renda_fixa")
report("list filtra por asset_type",   len(rf_only) == 1 and rf_only[0].asset_type == "renda_fixa")

svc.delete(inv2.id)
db.commit()
report("delete remove investment",     len(svc.list()) == 1)

try:
    svc.delete(9999)
    report("delete inexistente lança exceção", False)
except InvestmentNotFound:
    report("delete inexistente lança InvestmentNotFound", True)

db.close()
eng.dispose()


# ── 2. InvestmentService — Eventos ───────────────────────────────────────────
print("\n=== 2. InvestmentService — Eventos ===\n")

db, eng = make_db()
svc = InvestmentService(db)
inv = svc.create("PETR4", "acoes", 2000.0, 2300.0, date(2025, 1, 10))
db.commit()

evt = svc.add_event(inv.id, "dividend", 50.0, date(2025, 6, 1))
db.commit()
report("add_event retorna InvestmentEvent",  evt.id is not None)
report("event_type correto",                  evt.event_type == "dividend")
report("amount correto",                      evt.amount == 50.0)

evt2 = svc.add_event(inv.id, "income", 30.0, date(2025, 7, 1), taxes_paid=1.5)
db.commit()
events = svc.list_events(inv.id)
report("list_events retorna 2 eventos",       len(events) == 2)
report("taxes_paid armazenado",               evt2.taxes_paid == 1.5)

try:
    svc.add_event(9999, "buy", 100.0, date(2025, 1, 1))
    report("add_event inv inexistente lança exceção", False)
except InvestmentNotFound:
    report("add_event inv inexistente lança exceção", True)

db.close()
eng.dispose()


# ── 3. InvestmentService — Portfolio ─────────────────────────────────────────
print("\n=== 3. InvestmentService — Portfolio ===\n")

db, eng = make_db()
svc = InvestmentService(db)

summary_empty = svc.portfolio_summary()
report("portfolio vazio -> count=0",           summary_empty["count"] == 0)
report("portfolio vazio -> total_principal=0", summary_empty["total_principal"] == 0.0)

svc.create("CDB", "renda_fixa", 1000.0, 1100.0, date(2025, 1, 1))
svc.create("FII",  "fii",        2000.0, 2200.0, date(2025, 2, 1))
db.commit()

s = svc.portfolio_summary()
report("total_principal correto",         approx(s["total_principal"], 3000.0))
report("total_current correto",           approx(s["total_current"],   3300.0))
report("total_gain correto",              approx(s["total_gain"],       300.0))
report("by_type tem renda_fixa e fii",    "renda_fixa" in s["by_type"] and "fii" in s["by_type"])
report("allocation_pct soma ~100%",
       approx(sum(v["allocation_pct"] for v in s["by_type"].values()), 100.0, tol=0.1))
report("count = 2",                       s["count"] == 2)

db.close()
eng.dispose()


# ── 4. InvestmentService — Simulação de Imposto ──────────────────────────────
print("\n=== 4. InvestmentService — Simulação de Imposto ===\n")

db, eng = make_db()
svc = InvestmentService(db)

r = svc.simulate_tax(
    asset_type="renda_fixa", principal=10_000.0, gross_gain=500.0,
    purchase_date=date(2025, 1, 1), sale_date=date(2025, 6, 1),
)
report("renda_fixa: IR 17.5%",   approx(r.ir, 87.5))
report("renda_fixa: sem IOF",    r.iof == 0.0)

r2 = svc.simulate_tax("lci_lca", 5000.0, 200.0)
report("lci_lca: IR 5%",         approx(r2.ir, 10.0))

r3 = svc.simulate_tax("acoes", 1000.0, 500.0, quarterly_sales=30_000.0)
report("acoes: isento <60k",     r3.ir == 0.0)

r4 = svc.simulate_tax("fii", 0.0, 0.0, dividend=200.0, capital_gain=300.0)
report("fii: IR composto",       approx(r4.ir, 62.5))

r5 = svc.simulate_tax("crypto", 1000.0, 500.0, monthly_sales=40_000.0)
report("crypto: IR 17.5%",       approx(r5.ir, 87.5))

# sem datas -> usa today
r6 = svc.simulate_tax("renda_fixa", 1000.0, 50.0)
report("renda_fixa sem datas não lança erro", r6 is not None)

try:
    svc.simulate_tax("invalido", 1000.0, 100.0)
    report("tipo inválido lança ValueError", False)
except ValueError:
    report("tipo inválido lança ValueError", True)

db.close()
eng.dispose()


# ── 5. InvestmentService — conta associada ────────────────────────────────────
print("\n=== 5. InvestmentService — conta associada ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
svc = InvestmentService(db)

acc = acc_svc.create("Corretora XP", "XP", "investment", balance=0.0)
db.commit()

inv = svc.create("Tesouro IPCA", "renda_fixa", 5000.0, 5300.0,
                  date(2025, 3, 1), account_id=acc.id)
db.commit()
report("investment vinculado à conta",    inv.account_id == acc.id)

by_account = svc.list(account_id=acc.id)
report("list filtra por account_id",      len(by_account) == 1)

try:
    svc.create("X", "renda_fixa", 100.0, 110.0, date(2025, 1, 1), account_id=9999)
    report("conta inexistente lança exceção", False)
except Exception:
    report("conta inexistente lança exceção", True)

db.close()
eng.dispose()


# ── 6. Router /investments ────────────────────────────────────────────────────
print("\n=== 6. Router /investments ===\n")

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
    # Cria
    r = tc.post("/investments/", json={
        "name": "CDB Banco XYZ", "asset_type": "renda_fixa",
        "principal": 10000.0, "current_value": 10500.0,
        "purchase_date": "2025-01-15",
    })
    report("POST /investments/ retorna 201", r.status_code == 201, f"status={r.status_code}")
    inv_id = r.json()["id"]

    # Tipo inválido
    r = tc.post("/investments/", json={
        "name": "X", "asset_type": "invalido",
        "principal": 100.0, "current_value": 110.0, "purchase_date": "2025-01-01",
    })
    report("POST tipo inválido retorna 422", r.status_code == 422)

    # Get
    r = tc.get(f"/investments/{inv_id}")
    report("GET /investments/{id} retorna 200", r.status_code == 200)
    report("GET retorna dados corretos", r.json()["id"] == inv_id)

    r = tc.get("/investments/9999")
    report("GET inexistente retorna 404", r.status_code == 404)

    # List
    tc.post("/investments/", json={
        "name": "FII BCFF11", "asset_type": "fii",
        "principal": 3000.0, "current_value": 3200.0, "purchase_date": "2025-02-01",
    })
    r = tc.get("/investments/")
    report("GET /investments/ lista todos", r.status_code == 200 and len(r.json()) == 2)

    r = tc.get("/investments/?asset_type=fii")
    report("GET filtra por asset_type", all(i["asset_type"] == "fii" for i in r.json()))

    # Update
    r = tc.patch(f"/investments/{inv_id}", json={"current_value": 11000.0})
    report("PATCH /investments/{id} retorna 200", r.status_code == 200)
    report("current_value atualizado", r.json()["current_value"] == 11000.0)

    r = tc.patch("/investments/9999", json={"current_value": 100.0})
    report("PATCH inexistente retorna 404", r.status_code == 404)

    # Portfolio
    r = tc.get("/investments/portfolio")
    report("GET /investments/portfolio retorna 200", r.status_code == 200)
    report("portfolio count = 2", r.json()["count"] == 2)
    report("total_gain correto", approx(r.json()["total_gain"], 1200.0))

    # Eventos
    r = tc.post(f"/investments/{inv_id}/events", json={
        "event_type": "dividend", "amount": 75.0, "event_date": "2025-07-01",
    })
    report("POST /events retorna 201", r.status_code == 201)
    report("event_type correto", r.json()["event_type"] == "dividend")

    r = tc.post("/investments/9999/events", json={
        "event_type": "buy", "amount": 100.0, "event_date": "2025-01-01",
    })
    report("POST /events inexistente retorna 404", r.status_code == 404)

    r = tc.get(f"/investments/{inv_id}/events")
    report("GET /events retorna lista", r.status_code == 200 and len(r.json()) == 1)

    r = tc.get("/investments/9999/events")
    report("GET /events inexistente retorna 404", r.status_code == 404)

    # Simulação de imposto
    r = tc.post("/investments/tax/simulate", json={
        "asset_type": "renda_fixa", "principal": 10000.0, "gross_gain": 500.0,
        "purchase_date": "2025-01-01", "sale_date": "2025-07-01",
    })
    report("POST /tax/simulate retorna 200",      r.status_code == 200)
    report("simulação renda_fixa IR 17.5%",        approx(r.json()["ir"], 87.5))
    report("simulação sem IOF (>30 dias)",          r.json()["iof"] == 0.0)

    r = tc.post("/investments/tax/simulate", json={
        "asset_type": "acoes", "principal": 5000.0, "gross_gain": 300.0,
        "quarterly_sales": 15000.0,
    })
    report("simulação ações isenta <60k",  r.json()["ir"] == 0.0)
    report("details exempt=True",          r.json()["details"]["exempt"] is True)

    r = tc.post("/investments/tax/simulate", json={
        "asset_type": "fii", "principal": 5000.0, "gross_gain": 0.0,
        "dividend": 200.0, "capital_gain": 300.0,
    })
    report("simulação FII IR composto",    approx(r.json()["ir"], 62.5))

    # Delete
    r = tc.delete(f"/investments/{inv_id}")
    report("DELETE retorna 204", r.status_code == 204)
    report("GET após delete retorna 404", tc.get(f"/investments/{inv_id}").status_code == 404)

    r = tc.delete("/investments/9999")
    report("DELETE inexistente retorna 404", r.status_code == 404)

app.dependency_overrides.clear()
test_eng.dispose()


# ── 7. Flashcards ─────────────────────────────────────────────────────────────
print("\n=== 7. Flashcards ===\n")

test_eng2 = get_engine("sqlite:///:memory:")
init_db(test_eng2)
test_factory2 = make_session_factory(test_eng2)


def _override2():
    db = test_factory2()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override2

with TestClient(app) as tc:
    r = tc.get("/investments/flashcards/all")
    report("GET /flashcards/all retorna 200", r.status_code == 200)
    report("8 flashcards disponíveis", len(r.json()) == 8)

    r = tc.get("/investments/flashcards/tag/ir")
    report("GET /flashcards/tag/ir retorna cards com tag ir",
           r.status_code == 200 and all("ir" in c["tags"] for c in r.json()))

    r = tc.get("/investments/flashcards/1")
    report("GET /flashcards/1 retorna card correto", r.status_code == 200 and r.json()["id"] == 1)

    r = tc.get("/investments/flashcards/999")
    report("GET /flashcards/999 retorna 404", r.status_code == 404)

# Testes unitários diretos
cards = get_all()
report("get_all retorna 8 cards", len(cards) == 8)
report("todos os cards têm question e answer",
       all(len(c.question) > 10 and len(c.answer) > 10 for c in cards))
report("todos os cards têm tags",  all(len(c.tags) >= 1 for c in cards))

rf_cards = get_by_tag("renda_fixa")
report("get_by_tag retorna subset correto", all("renda_fixa" in c.tags for c in rf_cards))

report("get_by_id None quando não existe", get_by_id(9999) is None)
report("get_by_id retorna card correto",   get_by_id(1) is not None and get_by_id(1).id == 1)

app.dependency_overrides.clear()
test_eng2.dispose()


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
