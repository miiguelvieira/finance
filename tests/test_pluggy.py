"""Testes Fase 6 — PluggyClient (mocked) + PluggySync + schemas."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.database import get_engine, init_db, make_session_factory
from src.core.exceptions import PluggyAuthError
from src.pluggy.client import PluggyClient
from src.pluggy.schemas import (
    PluggyAccount, PluggyAuthResponse, PluggyTransaction,
    PluggyTransactionPage, SyncResult,
)
from src.pluggy.sync import PluggySync, _map_subtype

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((name, passed))


def approx(a, b, tol=0.01):
    return abs(a - b) <= tol


def make_db():
    eng = get_engine("sqlite:///:memory:")
    init_db(eng)
    factory = make_session_factory(eng)
    return factory(), eng


# ── 1. PluggyClient — autenticacao ────────────────────────────────────────────
print("\n=== 1. PluggyClient — autenticacao ===\n")

# Sucesso
with patch("httpx.post") as mock_post:
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"apiKey": "tok123"})
    client = PluggyClient("id1", "secret1")
    key = client.authenticate()
    report("authenticate retorna apiKey",   key == "tok123")
    report("is_authenticated = True",       client.is_authenticated)
    report("_api_key armazenado",           client._api_key == "tok123")

# Falha de autenticacao
with patch("httpx.post") as mock_post:
    mock_post.return_value = MagicMock(status_code=401, text="Unauthorized")
    client2 = PluggyClient("bad", "bad")
    try:
        client2.authenticate()
        report("auth falha lanca PluggyAuthError", False)
    except PluggyAuthError:
        report("auth falha lanca PluggyAuthError", True)

# Sem autenticar
client3 = PluggyClient("x", "y")
try:
    client3._headers()
    report("_headers sem auth lanca PluggyAuthError", False)
except PluggyAuthError:
    report("_headers sem auth lanca PluggyAuthError", True)


# ── 2. PluggyClient — get_accounts ───────────────────────────────────────────
print("\n=== 2. PluggyClient — get_accounts ===\n")

_fake_accounts = {
    "results": [
        {
            "id": "acc-001", "itemId": "item-1", "name": "Nubank",
            "balance": 1500.0, "currencyCode": "BRL",
            "type": "BANK", "subtype": "CHECKING_ACCOUNT",
        }
    ]
}

with patch("httpx.post") as mock_post, patch("httpx.get") as mock_get:
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"apiKey": "tok"})
    mock_get.return_value = MagicMock(status_code=200, json=lambda: _fake_accounts)
    mock_get.return_value.raise_for_status = lambda: None

    client = PluggyClient("id", "secret")
    client.authenticate()
    accounts = client.get_accounts("item-1")

    report("get_accounts retorna lista",       len(accounts) == 1)
    report("PluggyAccount.id correto",         accounts[0].id == "acc-001")
    report("PluggyAccount.balance correto",    accounts[0].balance == 1500.0)
    report("PluggyAccount.subtype correto",    accounts[0].subtype == "CHECKING_ACCOUNT")


# ── 3. PluggyClient — get_transactions ──────────────────────────────────────
print("\n=== 3. PluggyClient — get_transactions ===\n")

_fake_txs = {
    "total": 2, "totalPages": 1, "page": 1,
    "results": [
        {
            "id": "tx-001", "accountId": "acc-001",
            "date": "2026-01-15T10:00:00Z",
            "description": "Netflix", "amount": 45.90,
            "currencyCode": "BRL", "type": "DEBIT",
        },
        {
            "id": "tx-002", "accountId": "acc-001",
            "date": "2026-01-20T12:00:00Z",
            "description": "Salario", "amount": 5000.0,
            "currencyCode": "BRL", "type": "CREDIT",
        },
    ],
}

with patch("httpx.post") as mock_post, patch("httpx.get") as mock_get:
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"apiKey": "tok"})
    resp_mock = MagicMock(status_code=200, json=lambda: _fake_txs)
    resp_mock.raise_for_status = lambda: None
    mock_get.return_value = resp_mock

    client = PluggyClient("id", "secret")
    client.authenticate()
    page = client.get_transactions("acc-001")

    report("get_transactions retorna PluggyTransactionPage", isinstance(page, PluggyTransactionPage))
    report("total = 2",           page.total == 2)
    report("totalPages = 1",      page.totalPages == 1)
    report("results com 2 txs",   len(page.results) == 2)
    report("tx DEBIT amount 45.90", approx(page.results[0].amount, 45.90))
    report("tx CREDIT amount 5000", approx(page.results[1].amount, 5000.0))


# ── 4. PluggyClient — get_all_transactions (paginacao) ─────────────────────
print("\n=== 4. PluggyClient — get_all_transactions (paginacao) ===\n")

_page1 = {"total": 3, "totalPages": 2, "page": 1, "results": [
    {"id": "tx-p1", "accountId": "acc-001", "date": "2026-01-01T00:00:00Z",
     "description": "A", "amount": 10.0, "currencyCode": "BRL", "type": "DEBIT"},
]}
_page2 = {"total": 3, "totalPages": 2, "page": 2, "results": [
    {"id": "tx-p2", "accountId": "acc-001", "date": "2026-01-02T00:00:00Z",
     "description": "B", "amount": 20.0, "currencyCode": "BRL", "type": "CREDIT"},
    {"id": "tx-p3", "accountId": "acc-001", "date": "2026-01-03T00:00:00Z",
     "description": "C", "amount": 30.0, "currencyCode": "BRL", "type": "DEBIT"},
]}

_pages = [_page1, _page2]
_page_call_count = [0]

def _mock_get_paginated(*args, **kwargs):
    idx = _page_call_count[0]
    _page_call_count[0] += 1
    m = MagicMock(status_code=200)
    m.json = lambda i=idx: _pages[i]
    m.raise_for_status = lambda: None
    return m

with patch("httpx.post") as mock_post, patch("httpx.get", side_effect=_mock_get_paginated):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"apiKey": "tok"})
    client = PluggyClient("id", "secret")
    client.authenticate()
    all_txs = client.get_all_transactions("acc-001")

    report("get_all_transactions une paginas",  len(all_txs) == 3)
    report("ids corretos",
           {t.id for t in all_txs} == {"tx-p1", "tx-p2", "tx-p3"})


# ── 5. PluggySync — sync_accounts ────────────────────────────────────────────
print("\n=== 5. PluggySync — sync_accounts ===\n")

db, eng = make_db()

fake_pluggy_acc = PluggyAccount(
    id="pluggy-acc-1", itemId="item-1", name="Nubank",
    balance=2500.0, currencyCode="BRL", type="BANK", subtype="CHECKING_ACCOUNT",
)

mock_client = MagicMock()
mock_client.get_accounts.return_value = [fake_pluggy_acc]

sync = PluggySync(mock_client, db)
result = sync.sync_accounts("item-1")
db.commit()

report("sync_accounts cria conta nova",        result.accounts_created == 1)
report("accounts_updated = 0",                 result.accounts_updated == 0)
report("sem erros",                            len(result.errors) == 0)

# Segunda sync: deve atualizar
result2 = sync.sync_accounts("item-1")
db.commit()
report("segunda sync atualiza (nao cria)",     result2.accounts_updated == 1 and result2.accounts_created == 0)

db.close()
eng.dispose()


# ── 6. PluggySync — sync_transactions ────────────────────────────────────────
print("\n=== 6. PluggySync — sync_transactions ===\n")

db, eng = make_db()
from src.accounts.service import AccountService
acc_svc = AccountService(db)
acc = acc_svc.create("Nubank", "Nubank", "checking", balance=1000.0, pluggy_account_id="pluggy-acc-2")
db.commit()

fake_tx = PluggyTransaction(
    id="pluggy-tx-1", accountId="pluggy-acc-2",
    date=datetime(2026, 1, 15, 10, 0),
    description="iFood pedido", amount=35.90,
    currencyCode="BRL", type="DEBIT",
)
fake_tx2 = PluggyTransaction(
    id="pluggy-tx-2", accountId="pluggy-acc-2",
    date=datetime(2026, 1, 20, 12, 0),
    description="Salario empresa", amount=5000.0,
    currencyCode="BRL", type="CREDIT",
)

mock_client2 = MagicMock()
mock_client2.get_all_transactions.return_value = [fake_tx, fake_tx2]

sync2 = PluggySync(mock_client2, db)
result = sync2.sync_transactions("pluggy-acc-2")
db.commit()

report("sync_transactions cria 2 txs",         result.transactions_created == 2)
report("transactions_skipped = 0",             result.transactions_skipped == 0)
report("sem erros",                            len(result.errors) == 0)

# Re-sync deve pular (duplicatas)
result2 = sync2.sync_transactions("pluggy-acc-2")
db.commit()
report("re-sync pula duplicatas",              result2.transactions_skipped == 2)
report("created = 0 no re-sync",              result2.transactions_created == 0)

db.close()
eng.dispose()


# ── 7. PluggySync — conta inexistente ────────────────────────────────────────
print("\n=== 7. PluggySync — conta inexistente ===\n")

db, eng = make_db()
mock_client3 = MagicMock()
sync3 = PluggySync(mock_client3, db)
result = sync3.sync_transactions("nao-existe-id")
report("conta inexistente gera erro",          len(result.errors) == 1)
report("erro menciona nao encontrada",         "nao encontrada" in result.errors[0].lower())
db.close()
eng.dispose()


# ── 8. PluggySync — full_sync ─────────────────────────────────────────────────
print("\n=== 8. PluggySync — full_sync ===\n")

db, eng = make_db()

fake_acc = PluggyAccount(
    id="pluggy-acc-full", itemId="item-full", name="Itau",
    balance=3000.0, currencyCode="BRL", type="BANK", subtype="SAVINGS_ACCOUNT",
)
fake_tx_full = PluggyTransaction(
    id="pluggy-tx-full", accountId="pluggy-acc-full",
    date=datetime(2026, 2, 1, 9, 0),
    description="Mercado livre", amount=120.0,
    currencyCode="BRL", type="DEBIT",
)

mock_client4 = MagicMock()
mock_client4.get_accounts.return_value = [fake_acc]
mock_client4.get_all_transactions.return_value = [fake_tx_full]

sync4 = PluggySync(mock_client4, db)
result = sync4.full_sync("item-full")
db.commit()

report("full_sync cria conta",           result.accounts_created == 1)
report("full_sync cria transacao",       result.transactions_created == 1)
report("full_sync sem erros",            len(result.errors) == 0)

db.close()
eng.dispose()


# ── 9. _map_subtype ────────────────────────────────────────────────────────────
print("\n=== 9. _map_subtype ===\n")

report("CHECKING_ACCOUNT -> checking",   _map_subtype("CHECKING_ACCOUNT") == "checking")
report("SAVINGS_ACCOUNT -> savings",     _map_subtype("SAVINGS_ACCOUNT") == "savings")
report("CREDIT_CARD -> credit_card",     _map_subtype("CREDIT_CARD") == "credit_card")
report("INVESTMENT -> investment",       _map_subtype("INVESTMENT") == "investment")
report("desconhecido -> checking",       _map_subtype("OUTRO") == "checking")


# ── 10. SyncResult.merge ──────────────────────────────────────────────────────
print("\n=== 10. SyncResult.merge ===\n")

a = SyncResult(accounts_created=1, transactions_created=5, errors=["err1"])
b = SyncResult(accounts_updated=2, transactions_skipped=3, errors=["err2"])
a.merge(b)

report("merge soma accounts_created",     a.accounts_created == 1)
report("merge soma accounts_updated",     a.accounts_updated == 2)
report("merge soma transactions_created", a.transactions_created == 5)
report("merge soma transactions_skipped", a.transactions_skipped == 3)
report("merge concatena errors",          a.errors == ["err1", "err2"])


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
