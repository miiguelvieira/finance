"""Testes Fase 6 — IntentClassifier + ChatbotEngine + router."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.database import get_db, get_engine, init_db, make_session_factory
from src.accounts.service import AccountService
from src.chatbot.intents import IntentClassifier
from src.chatbot.engine import ChatbotEngine
from src.chatbot import responses as resp
from src.investments.service import InvestmentService
from src.core.models import Goal, ChatbotHistory

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


INTENTS_PATH = str(Path(ROOT) / "assets" / "intents.yaml")


# ── 1. IntentClassifier ───────────────────────────────────────────────────────
print("\n=== 1. IntentClassifier ===\n")

clf = IntentClassifier(INTENTS_PATH)

report("saldo detectado",          clf.classify("qual e meu saldo?") == "saldo")
report("gastos detectado",         clf.classify("quanto gastei esse mes?") == "gastos")
report("transacoes detectado",     clf.classify("minhas transacoes recentes") == "transacoes")
report("investimentos detectado",  clf.classify("como esta minha carteira de investimentos?") == "investimentos")
report("metas detectado",          clf.classify("quero ver minhas metas") == "metas")
report("projecao detectado",       clf.classify("projecao de saldo futuro") == "projecao")
report("impostos detectado",       clf.classify("como calcular imposto de renda?") == "impostos")
report("ajuda detectado",          clf.classify("ajuda") == "ajuda")
report("desconhecido detectado",   clf.classify("xyzabc foobar") == "desconhecido")

report("known_intents tem 8",      len(clf.known_intents) == 8)

# Acentos normalizados
report("acento normalizado (transacoes)", clf.classify("transacoes") in ("transacoes",))


# ── 2. responses.py — formatacao ────────────────────────────────────────────
print("\n=== 2. responses — formatacao ===\n")

# fmt_brl
report("fmt_brl R$1.234,56",      resp.fmt_brl(1234.56) == "R$ 1.234,56")
report("fmt_brl R$0,00",          resp.fmt_brl(0.0) == "R$ 0,00")

# build_saldo
s = resp.build_saldo([
    {"name": "Nubank", "bank_name": "Nubank", "balance": 1000.0},
    {"name": "Itau", "bank_name": "Itau", "balance": 500.0},
])
report("build_saldo menciona patrimonio", "Patrimonio" in s)
report("build_saldo menciona R$ 1.500,00", "1.500,00" in s)

s_empty = resp.build_saldo([])
report("build_saldo vazio", "Nenhuma" in s_empty)

# build_gastos
summary = {"income": 5000.0, "expenses": -2000.0, "net": 3000.0,
           "by_category": {"alimentacao": -500.0, "transporte": -200.0},
           "month": 4, "year": 2026}
g = resp.build_gastos(summary)
report("build_gastos menciona Receitas",  "Receitas" in g)
report("build_gastos menciona categoria", "alimentacao" in g)

# build_transacoes
txs = [{"transaction_date": "2026-01-10", "description": "Netflix",
         "amount": -45.9, "category": "lazer"}]
t = resp.build_transacoes(txs)
report("build_transacoes menciona Netflix", "Netflix" in t)
report("build_transacoes vazio", "Nenhuma" in resp.build_transacoes([]))

# build_investimentos
portfolio_data = {
    "count": 1, "total_principal": 10000.0, "total_current": 10500.0,
    "total_gain": 500.0, "gain_pct": 5.0,
    "by_type": {"renda_fixa": {"current": 10500.0, "allocation_pct": 100.0}},
}
i = resp.build_investimentos(portfolio_data)
report("build_investimentos menciona Carteira", "Carteira" in i)
report("build_investimentos vazio", "Nenhum" in resp.build_investimentos({"count": 0}))

# build_metas
metas = [{"name": "Carro", "current_amount": 5000.0, "target_amount": 50000.0, "is_achieved": False}]
m = resp.build_metas(metas)
report("build_metas menciona meta",   "Carro" in m)
report("build_metas vazio",           "Nenhuma" in resp.build_metas([]))
achieved = [{"name": "Viagem", "current_amount": 3000.0, "target_amount": 3000.0, "is_achieved": True}]
report("build_metas ATINGIDA",        "ATINGIDA" in resp.build_metas(achieved))

# build_projecao
p = resp.build_projecao(12000.0, "growing", 30)
report("build_projecao menciona crescendo", "crescendo" in p)
report("build_projecao declining -> caindo", "caindo" in resp.build_projecao(0.0, "declining", 30))
report("build_projecao stable -> estavel",  "estavel" in resp.build_projecao(0.0, "stable", 30))

# build_impostos
imp = resp.build_impostos()
report("build_impostos menciona 17,5%", "17,5%" in imp)
report("build_impostos menciona FII", "FII" in imp)

# HELP e UNKNOWN
report("HELP_TEXT nao vazio",   len(resp.HELP_TEXT) > 20)
report("UNKNOWN_TEXT nao vazio", len(resp.UNKNOWN_TEXT) > 20)


# ── 3. ChatbotEngine — dispatch ─────────────────────────────────────────────
print("\n=== 3. ChatbotEngine — dispatch ===\n")

db, eng = make_db()
acc_svc = AccountService(db)
acc = acc_svc.create("Nubank", "Nubank", "checking", balance=3000.0)
db.commit()

engine = ChatbotEngine(db, INTENTS_PATH)

# saldo
r = engine.reply("qual o meu saldo?")
report("reply saldo menciona Nubank",        "Nubank" in r)
report("reply saldo menciona 3.000,00",      "3.000,00" in r)

# ajuda
r = engine.reply("ajuda", save_history=False)
report("reply ajuda retorna HELP_TEXT",      "Posso ajudar" in r)

# desconhecido
r = engine.reply("xyzabc", save_history=False)
report("reply desconhecido retorna UNKNOWN", "Nao entendi" in r)

# impostos
r = engine.reply("imposto de renda sobre investimentos", save_history=False)
report("reply impostos menciona 17,5%",      "17,5%" in r)

# investimentos (carteira vazia)
r = engine.reply("como esta minha carteira?", save_history=False)
report("reply investimentos vazio",          "Nenhum" in r)

# metas (sem metas)
r = engine.reply("quero ver minhas metas", save_history=False)
report("reply metas vazio",                  "Nenhuma" in r)

# gastos
r = engine.reply("quanto gastei esse mes?", save_history=False)
report("reply gastos menciona Receitas",     "Receitas" in r)

# transacoes (sem txs)
r = engine.reply("minhas transacoes recentes", save_history=False)
report("reply transacoes vazio",             "Nenhuma" in r)

# projecao (usa termo exclusivo para evitar empate com "saldo")
r = engine.reply("previsao daqui 30 dias", save_history=False)
report("reply projecao menciona saldo projetado", "projetado" in r.lower())

db.close()
eng.dispose()


# ── 4. ChatbotEngine — save_history ─────────────────────────────────────────
print("\n=== 4. ChatbotEngine — save_history ===\n")

db, eng = make_db()
engine = ChatbotEngine(db, INTENTS_PATH)

engine.reply("ajuda")
db.commit()
engine.reply("saldo")
db.commit()

history = db.query(ChatbotHistory).order_by(ChatbotHistory.id).all()
report("save_history salva 2 registros",   len(history) == 2)
report("intent correto no historico",      history[0].intent == "ajuda")
report("user_message salvo",               history[0].user_message == "ajuda")
report("bot_response salvo",               len(history[0].bot_response) > 10)

# save_history=False nao salva
engine.reply("impostos", save_history=False)
db.commit()
history2 = db.query(ChatbotHistory).all()
report("save_history=False nao salva",     len(history2) == 2)

db.close()
eng.dispose()


# ── 5. ChatbotEngine — com investimentos ─────────────────────────────────────
print("\n=== 5. ChatbotEngine — com investimentos ===\n")

db, eng = make_db()
inv_svc = InvestmentService(db)
inv_svc.create("CDB XP", "renda_fixa", 10000.0, 10800.0, date(2025, 1, 1))
db.commit()

engine = ChatbotEngine(db, INTENTS_PATH)
r = engine.reply("como esta minha carteira de investimentos?", save_history=False)
report("reply investimentos com dados",    "Carteira" in r)
report("menciona valor aplicado",          "10.000,00" in r)

db.close()
eng.dispose()


# ── 6. ChatbotEngine — com metas ────────────────────────────────────────────
print("\n=== 6. ChatbotEngine — com metas ===\n")

db, eng = make_db()
db.add(Goal(name="Viagem Europa", target_amount=20000.0, current_amount=5000.0))
db.commit()

engine = ChatbotEngine(db, INTENTS_PATH)
r = engine.reply("quero ver minhas metas", save_history=False)
report("reply metas com dados",            "Viagem Europa" in r)
report("menciona valor atual",             "5.000,00" in r)

db.close()
eng.dispose()


# ── 7. Router /chatbot ────────────────────────────────────────────────────────
print("\n=== 7. Router /chatbot ===\n")

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
    r = tc.post("/chatbot/", json={"message": "ajuda"})
    report("POST /chatbot/ retorna 200",   r.status_code == 200, f"status={r.status_code}")
    report("response tem intent",          "intent" in r.json())
    report("response tem response",        "response" in r.json())
    report("intent = ajuda",               r.json()["intent"] == "ajuda")

    r = tc.post("/chatbot/", json={"message": "saldo das contas"})
    report("POST saldo retorna 200",       r.status_code == 200)
    report("intent = saldo",               r.json()["intent"] == "saldo")

    # Mensagem vazia
    r = tc.post("/chatbot/", json={"message": ""})
    report("POST mensagem vazia retorna 422", r.status_code == 422)

    # Historico
    r = tc.get("/chatbot/history")
    report("GET /chatbot/history retorna 200", r.status_code == 200)
    report("historico tem >= 2 itens",     len(r.json()) >= 2)

    r = tc.get("/chatbot/history?limit=1")
    report("GET /chatbot/history?limit=1", len(r.json()) == 1)

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
