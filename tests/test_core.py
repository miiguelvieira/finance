"""Testes Fase 1 — core infra: DB, config, exceções, API health."""

import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.database import get_engine, init_db
from src.core.exceptions import (
    AccountNotFound, ConfigError, FinanceException, GoalNotFound,
    InstallmentNotFound, InsufficientBalance, InvestmentNotFound,
    PluggyAuthError, TaxCalculationError,
)
from src.core.models import (
    Account, BalanceHistory, ChatbotHistory, Goal, IncomeSource,
    Installment, Investment, InvestmentEvent, Transaction,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def report(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, passed))


# ── 1. Database ───────────────────────────────────────────────────────────────
print("\n=== 1. Database — criação de tabelas ===\n")

eng = get_engine("sqlite:///:memory:")
init_db(eng)
inspector = inspect(eng)
tables = set(inspector.get_table_names())

EXPECTED_TABLES = {
    "accounts", "transactions", "installments", "investments",
    "investment_events", "goals", "balance_history",
    "income_sources", "chatbot_history",
}

for tbl in EXPECTED_TABLES:
    report(f"Tabela '{tbl}' criada", tbl in tables)

# Verifica colunas críticas de accounts
cols_accounts = {c["name"] for c in inspector.get_columns("accounts")}
for col in ("id", "name", "bank_name", "account_type", "balance", "is_active"):
    report(f"accounts.{col} existe", col in cols_accounts)

# Verifica FK transactions → accounts
fks = inspector.get_foreign_keys("transactions")
fk_targets = {fk["referred_table"] for fk in fks}
report("transactions tem FK para accounts", "accounts" in fk_targets)

eng.dispose()


# ── 2. Exceções ───────────────────────────────────────────────────────────────
print("\n=== 2. Hierarquia de exceções ===\n")

report("AccountNotFound é FinanceException", issubclass(AccountNotFound, FinanceException))
report("InsufficientBalance é FinanceException", issubclass(InsufficientBalance, FinanceException))
report("PluggyAuthError é FinanceException", issubclass(PluggyAuthError, FinanceException))
report("TaxCalculationError é FinanceException", issubclass(TaxCalculationError, FinanceException))

try:
    raise AccountNotFound(42)
except FinanceException as e:
    report("AccountNotFound capturada como FinanceException", "42" in str(e))

try:
    raise InsufficientBalance(100.0, 200.0)
except InsufficientBalance as e:
    report("InsufficientBalance contém valores", "100" in str(e) and "200" in str(e))


# ── 3. Config ─────────────────────────────────────────────────────────────────
print("\n=== 3. Config — carregamento ===\n")

from src.core.config import get_settings

# Limpa cache para garantir leitura fresca
get_settings.cache_clear()
settings = get_settings(str(ROOT / "config.yaml"))

report("Settings carregado sem erro", settings is not None)
report("dash_port é inteiro", isinstance(settings.dash_port, int))
report("api_port é inteiro", isinstance(settings.api_port, int))
report("database_url contém sqlite", "sqlite" in settings.database_url)
report("config.yaml tax.renda_fixa_rate == 0.175", settings.get("tax", "renda_fixa_rate") == 0.175)
report("config.yaml tax.acoes_day_trade_rate == 0.20", settings.get("tax", "acoes_day_trade_rate") == 0.20)
report("config.yaml projection.months_forward == 12", settings.get("projection", "months_forward") == 12)


# ── 4. API /health ────────────────────────────────────────────────────────────
print("\n=== 4. FastAPI /health ===\n")

from fastapi.testclient import TestClient
from src.api.main import app
from src.core.database import make_session_factory

test_engine = get_engine("sqlite:///:memory:")
init_db(test_engine)
factory = make_session_factory(test_engine)

from src.core.database import get_db

def _override():
    db = factory()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override

with TestClient(app) as tc:
    resp = tc.get("/health")
    report("/health retorna 200", resp.status_code == 200, f"status={resp.status_code}")
    report("/health retorna status ok", resp.json().get("status") == "ok", f"body={resp.json()}")

app.dependency_overrides.clear()
test_engine.dispose()


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
