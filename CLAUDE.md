# CLAUDE.md — Finance Personal App

## Visão Geral
App de gestão financeira pessoal: web (Dash) + executável Windows (PyInstaller).
Gerencia contas, transações, parcelas, investimentos, metas e projeções de saldo.
Foco no mercado brasileiro — impostos 2026, Open Banking via Pluggy.

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite (migrações Alembic)
- Frontend: Dash 2.17+ + Plotly 5.22+ + Dash Bootstrap Components
- Desktop: PyInstaller + pywebview
- Open Banking: Pluggy SDK (Brasil)
- Python 3.10+

## Agents
- frontend-dev.md - Para polir a aparencia
- ux-designer.md - Para adicionar funcionalidades e beleza
- ia-engineer.md - Para fazer o chatbot 

## Estrutura de Pastas
```
finance/
├── src/
│   ├── core/           # models.py, database.py, config.py, exceptions.py
│   ├── accounts/       # service.py, schemas.py, router.py
│   ├── transactions/   # service.py, categorizer.py, schemas.py, router.py
│   ├── installments/   # service.py, schemas.py, router.py
│   ├── projections/    # engine.py, schemas.py, router.py
│   ├── investments/    # service.py, tax_engine.py, flashcards.py, schemas.py, router.py
│   ├── goals/          # service.py, schemas.py, router.py
│   ├── pluggy/         # client.py, sync.py, schemas.py
│   ├── chatbot/        # engine.py, intents.py, responses.py
│   ├── api/            # main.py (FastAPI app)
│   └── dashboard/      # app.py, layout.py, theme.py, pages/, callbacks/, components/
├── desktop/            # main.py (pywebview), build.spec
├── data/               # finance.db (gitignored)
├── assets/             # custom.css, categorization_rules.yaml, intents.yaml
├── migrations/         # Alembic
└── tests/              # 12 arquivos de teste
```

## Regras de Desenvolvimento
- NUNCA hardcodar credenciais — usar .env (ver .env.example)
- SEMPRE rodar `pytest tests/ -v` após qualquer mudança em módulo
- NUNCA editar migrations manualmente — usar `alembic revision --autogenerate`
- `data/finance.db` é gitignored — nunca commitar o banco
- Todo módulo novo precisa de teste em `tests/`
- Callbacks Dash nunca bloqueiam — operações pesadas em `dcc.Store` ou thread separada

## Variáveis de Ambiente
- PLUGGY_API_KEY — client ID da Pluggy
- PLUGGY_CLIENT_SECRET — secret da Pluggy
- PLUGGY_SANDBOX — "true" (sandbox) ou "false" (produção)
- DATABASE_URL — padrão: sqlite:///data/finance.db
- DASH_PORT — padrão: 8050
- API_PORT — padrão: 8000

## Rodando em Desenvolvimento
```bash
python src/api/main.py        # FastAPI em :8000
python src/dashboard/app.py   # Dash em :8050
```

## Build Desktop
```bash
pyinstaller desktop/build.spec
# Executável em dist/finance/finance.exe
```

## Impostos BR 2026
- Renda Fixa (CDB, Tesouro): 17.5% sobre ganho + IOF (<30 dias)
- LCI/LCA: 5% (novas emissões pós-reforma)
- Ações: 17.5% normal / 20% day trade / isento se vendas ≤ R$60k/trimestre
- FII: 5% dividendos / 17.5% ganho de capital
- Carryforward de prejuízo: 5 anos

## Categorias de Transação (14)
moradia, alimentacao, transporte, saude, educacao, lazer, vestuario,
assinaturas, investimentos, transferencia, salario, freelance, dividendos, outros

## Regras de Economia de Tokens
- NUNCA repetir código já existente — referenciar pelo caminho e linha
- SEMPRE referenciar arquivos pelo caminho (`src/core/models.py:42`)
- Comentários curtos — sem explicar o óbvio
- Sem docstrings longas — uma linha basta
- Preferir edições cirúrgicas (Edit) a reescritas completas (Write)
- NUNCA mostrar o arquivo inteiro se só uma parte mudou

## Cobertura Mínima de Testes
- `src/investments/tax_engine.py` — 100% obrigatório
- `src/projections/engine.py` — 100% obrigatório
- Projeto geral — ≥ 85%
