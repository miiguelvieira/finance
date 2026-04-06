# CONTEXT.md — Estado do Projeto Finance

## Fase Atual
**Fase 9 concluída** — Polimento (redesign visual, overview page, splash screen, CI/CD).
Próxima: **Fase 10 — Empacotamento final e distribuição**.

## Arquivos Criados
```
config.yaml                          # Configuração centralizada
.env.example                         # Template de variáveis de ambiente
requirements.txt                     # Dependências pinadas
src/core/models.py                   # 9 tabelas ORM (source of truth)
src/core/database.py                 # Engine + StaticPool, session factory, init_db()
src/core/config.py                   # Pydantic Settings (.env + config.yaml)
src/core/exceptions.py               # Hierarquia de exceções
src/api/main.py                      # FastAPI app + todos os routers registrados
src/accounts/service.py              # CRUD, update_balance(), transfer(), net_worth()
src/accounts/schemas.py              # Pydantic schemas
src/accounts/router.py               # /accounts/* (7 endpoints)
src/transactions/service.py          # CRUD, list() com filtros, monthly_summary()
src/transactions/categorizer.py      # Regras regex com normalize (sem acento/pontuação)
src/transactions/schemas.py          # Pydantic schemas
src/transactions/router.py           # /transactions/* (5 endpoints)
assets/categorization_rules.yaml    # 35 regras regex por categoria
assets/intents.yaml                  # 8 intents do chatbot com padrões keyword
src/installments/service.py          # InstallmentService + IncomeSourceService
src/installments/schemas.py          # Pydantic schemas
src/installments/router.py           # /installments/* + /income-sources/*
src/projections/engine.py            # ProjectionEngine (saldo diário, metas, tendência)
src/projections/schemas.py           # Pydantic schemas
src/projections/router.py            # /projections/*
src/investments/tax_engine.py        # Tax Engine BR 2026 (100% coverage)
src/investments/schemas.py           # Pydantic schemas
src/investments/service.py           # InvestmentService (CRUD, eventos, portfolio, tax sim)
src/investments/router.py            # /investments/* + /tax/simulate + /flashcards/*
src/investments/flashcards.py        # 8 flashcards educativos BR 2026
src/pluggy/schemas.py                # PluggyAccount, PluggyTransaction, SyncResult
src/pluggy/client.py                 # PluggyClient — HTTP wrapper com auth + paginação
src/pluggy/sync.py                   # PluggySync — upsert contas e transações
src/pluggy/router.py                 # /pluggy/sync/* (3 endpoints)
src/chatbot/intents.py               # IntentClassifier — keyword matching + normalização
src/chatbot/responses.py             # Templates de resposta formatados em BRL
src/chatbot/engine.py                # ChatbotEngine — dispatch + histórico
src/chatbot/router.py                # /chatbot/ POST + /chatbot/history GET
tests/conftest.py                    # Fixtures pytest (engine em memória)
tests/test_core.py                   # Testes Fase 1
tests/test_accounts.py               # Testes Fase 2 — accounts
tests/test_transactions.py           # Testes Fase 2 — transactions + categorizer
tests/test_installments.py           # Testes Fase 3 — installments + income sources
tests/test_projections.py            # Testes Fase 4 — projection engine
tests/test_tax_engine.py             # Testes Fase 5 — tax engine (100% coverage)
tests/test_investments.py            # Testes Fase 5 — investments service + router + flashcards
tests/test_pluggy.py                 # Testes Fase 6 — PluggyClient (mocked) + PluggySync
tests/test_chatbot.py                # Testes Fase 6 — IntentClassifier + ChatbotEngine + router
src/dashboard/theme.py               # Constantes visuais (THEME, cores, SIDEBAR_WIDTH, FONT_FAMILY)
src/dashboard/components/cards.py   # metric_card(), section_header()
src/dashboard/components/charts.py  # bar_chart(), pie_chart(), line_chart()
src/dashboard/layout.py             # create_layout() — sidebar fixa + dcc.Location + page-content
src/dashboard/app.py                # Dash app — routing callback + register_callbacks
src/dashboard/pages/accounts.py    # Página Contas (fmt_brl, layout, register_callbacks)
src/dashboard/pages/transactions.py # Página Transacoes (filtros, tabela, pie chart)
src/dashboard/pages/investments.py  # Página Investimentos (portfolio, tabela, pie chart)
src/dashboard/pages/goals.py        # Página Metas (lista, formulario, progress bars)
src/dashboard/pages/chatbot.py      # Página Chatbot (chat history, input, badges)
tests/test_dashboard.py             # Testes Fase 7 — 62/62 PASS
desktop/__init__.py                  # Torna desktop/ pacote importavel
desktop/launcher.py                  # start_servers() — FastAPI + Dash em threads daemon
desktop/main.py                      # Ponto de entrada — pywebview window 1280x800
desktop/build.spec                   # PyInstaller spec (console=False, assets bundled)
tests/test_desktop.py               # Testes Fase 8/9 — 27/27 PASS
# -- Fase 9 (Polimento) --
src/dashboard/theme.py               # Atualizado: paleta Tailwind, SECONDARY, INFO, PAGE_BG
src/dashboard/components/cards.py   # Atualizado: delta/trend (seta +/-), tipografia melhorada
src/dashboard/components/charts.py  # Atualizado: bg transparente, COLOR_SEQ 8 cores, line fill
src/dashboard/layout.py             # Atualizado: sidebar com logo area, footer, nav pills modernos
src/dashboard/pages/overview.py     # NOVO: Visao Geral com 4 KPIs, graficos, alertas dinamicos
desktop/splash.html                  # Splash screen animada (dark navy, spinner CSS)
desktop/main.py                      # Atualizado: abre splash primeiro, redireciona ao dash
.github/workflows/ci.yml             # CI/CD: test + build-exe + release no GitHub Actions
# -- Fase 10 (E2E) --
tests/test_e2e.py                    # Testes E2E Playwright (5 cenários, rodar com -m e2e)
requirements.txt                     # Modificado: adicionado playwright + pytest-playwright
# -- Fase 10 (Auto-update) --
src/core/updater.py                  # NOVO: auto-update via GitHub Releases (get_current_version, check_for_update, download_and_apply)
desktop/main.py                      # Atualizado: check_for_update em background thread + aviso 3s na splash
config.yaml                          # Atualizado: app.version "0.1.0" -> "1.0.0"
requirements.txt                     # Modificado: adicionado requests + packaging
tests/test_updater.py                # NOVO: 14/14 PASS (mock GitHub API, sem update, com update, falha de rede)
README.md                            # NOVO: documentação completa (instalação, stack, impostos BR 2026, testes)
```

## Testes
| Arquivo | Resultado |
|---------|-----------|
| tests/test_core.py | 31/31 PASS |
| tests/test_accounts.py | 28/28 PASS |
| tests/test_transactions.py | 38/38 PASS |
| tests/test_installments.py | 43/43 PASS |
| tests/test_projections.py | 68/68 PASS |
| tests/test_tax_engine.py | 49/49 PASS |
| tests/test_investments.py | 73/73 PASS |
| tests/test_pluggy.py | 41/41 PASS |
| tests/test_chatbot.py | 61/61 PASS |
| tests/test_dashboard.py | 62/62 PASS |
| tests/test_desktop.py | 27/27 PASS |
| tests/test_dashboard.py (Fase 9) | 78/78 PASS |
| tests/test_updater.py | 14/14 PASS |

## Schema do Banco
9 tabelas: accounts, transactions, installments, investments, investment_events,
goals, balance_history, income_sources, chatbot_history

## API REST — Routers Registrados
- `/accounts/*` — 7 endpoints (CRUD, saldo, transferência, net worth)
- `/transactions/*` — 5 endpoints (CRUD, filtros, resumo mensal)
- `/installments/*` — 6 endpoints + `/income-sources/*` — 4 endpoints
- `/projections/*` — projeção de saldo 12 meses
- `/investments/*` — CRUD + eventos + /tax/simulate + /flashcards/*
- `/pluggy/sync/*` — 3 endpoints (full sync, contas, transações)
- `/chatbot/` — POST mensagem + GET histórico

# -- Fase 10 (Ícone + Instalador) --
scripts/generate_icon.py             # NOVO: gera assets/icon.ico (256x256, letra F, fundo #1e293b)
installer/setup.iss                  # NOVO: script Inno Setup 6+ (lzma2/ultra64, PT-BR, atalho desktop)
desktop/build.spec                   # Atualizado: icon=None → icon='assets/icon.ico'
requirements.txt                     # Modificado: adicionado Pillow>=10.0

## Uso
```bash
# Gerar ícone:
python scripts/generate_icon.py

# Gerar instalador (após pyinstaller desktop/build.spec):
ISCC installer/setup.iss /DAppVersion=1.0.0
```

## Próximo Passo
Fase 10 — Empacotamento final (restante):
1. ~~`assets/icon.ico`~~ — **concluído**
2. ~~Instalador Inno Setup~~ — **concluído**
3. ~~Auto-update via GitHub Releases~~ — **concluído**
4. Testes E2E com Playwright ou Selenium no dashboard
5. ~~README.md completo com screenshots e instruções de instalacao~~ — **concluído**
