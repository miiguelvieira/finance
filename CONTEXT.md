# CONTEXT.md — Estado do Projeto Finance

## Fase Atual
**Fase 1 concluída** — Core infra (DB + config + FastAPI skeleton).
Próxima: **Fase 2 — Accounts + Transactions + Categorizer**.

## Arquivos Criados
```
config.yaml                      # Configuração centralizada
.env.example                     # Template de variáveis de ambiente
requirements.txt                 # Dependências pinadas
src/core/models.py               # 9 tabelas ORM (source of truth)
src/core/database.py             # Engine, session factory, init_db()
src/core/config.py               # Pydantic Settings (.env + config.yaml)
src/core/exceptions.py           # Hierarquia de exceções
src/api/main.py                  # FastAPI skeleton + /health
tests/conftest.py                # Fixtures: engine em memória, session, client
tests/test_core.py               # Testes Fase 1
```

## Testes
| Arquivo | Resultado |
|---------|-----------|
| tests/test_core.py | — (rodar após instalar dependências) |

## Schema do Banco
9 tabelas: accounts, transactions, installments, investments, investment_events,
goals, balance_history, income_sources, chatbot_history

## Próximo Passo
Fase 2 — Accounts + Transactions:
1. `src/accounts/service.py` — CRUD, update_balance(), transfer(), net_worth()
2. `src/accounts/schemas.py` + `router.py`
3. `src/transactions/service.py` + `categorizer.py`
4. `assets/categorization_rules.yaml` — ~30 regras regex
5. `tests/test_accounts.py` + `tests/test_transactions.py`
