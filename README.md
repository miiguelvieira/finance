# Finance — Gestão Financeira Pessoal

![CI](https://github.com/seu-usuario/finance/actions/workflows/ci.yml/badge.svg)

> 📸 Screenshot do dashboard (adicionar após build)

App de gestão financeira pessoal com interface web (Dash) e executável Windows (PyInstaller). Foco no mercado brasileiro — cálculo de impostos 2026 e integração com Open Banking via Pluggy.

---

## Funcionalidades

- **Contas** — cadastro e saldo de contas bancárias e carteiras
- **Transações** — lançamentos com categorização automática (14 categorias)
- **Parcelas** — controle de compras parceladas com projeção de vencimentos
- **Investimentos** — carteira com cálculo de impostos BR 2026 (CDB, LCI, Ações, FII)
- **Metas** — definição e acompanhamento de objetivos financeiros
- **Projeções** — simulação de saldo futuro com base em receitas e despesas recorrentes
- **Chatbot** — assistente financeiro integrado via intenções configuráveis

---

## Stack

| Componente      | Tecnologia                                   |
|-----------------|----------------------------------------------|
| Backend / API   | FastAPI + SQLAlchemy + SQLite + Alembic       |
| Frontend        | Dash 2.17+ + Plotly 5.22+ + Bootstrap (DBC)  |
| Desktop         | PyInstaller + pywebview                       |
| Open Banking    | Pluggy SDK (Brasil)                           |
| Testes          | pytest + pytest-cov + Playwright (E2E)        |
| Linguagem       | Python 3.10+                                 |

---

## Pré-requisitos

- Python 3.10 ou superior
- As variáveis de ambiente listadas na seção [Variáveis de Ambiente](#variáveis-de-ambiente)
- (Opcional) Conta na [Pluggy](https://pluggy.ai) para Open Banking

---

## Instalação (desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/finance.git
cd finance

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 4. Aplique as migrações do banco
alembic upgrade head

# 5. Inicie os servidores
python src/api/main.py        # FastAPI em :8000
python src/dashboard/app.py   # Dash em :8050
```

Acesse o dashboard em `http://localhost:8050` e a API em `http://localhost:8000/docs`.

---

## Instalação (executável Windows)

1. Baixe `finance.exe` na aba [Releases](https://github.com/seu-usuario/finance/releases) do repositório.
2. Crie um arquivo `.env` na mesma pasta do executável com as variáveis necessárias.
3. Execute `finance.exe` — nenhuma instalação do Python é necessária.

---

## Variáveis de Ambiente

| Variável              | Padrão                        | Descrição                              |
|-----------------------|-------------------------------|----------------------------------------|
| `DATABASE_URL`        | `sqlite:///data/finance.db`   | URL do banco de dados SQLite           |
| `PLUGGY_API_KEY`      | —                             | Client ID da Pluggy (Open Banking)     |
| `PLUGGY_CLIENT_SECRET`| —                             | Secret da Pluggy                       |
| `PLUGGY_SANDBOX`      | `true`                        | `true` = sandbox / `false` = produção  |
| `DASH_PORT`           | `8050`                        | Porta do servidor Dash                 |
| `API_PORT`            | `8000`                        | Porta do servidor FastAPI              |

---

## Rodando Testes

```bash
# Todos os testes com relatório de cobertura
pytest tests/ -v --cov=src --cov-report=term-missing

# Apenas testes E2E (requer Playwright instalado)
pytest -m e2e
```

Cobertura mínima exigida: **85%** geral, **100%** em `tax_engine.py` e `projections/engine.py`.

---

## Build do Executável

```bash
pyinstaller desktop/build.spec
# Executável gerado em: dist/finance/finance.exe
```

---

## Estrutura de Pastas

```
finance/
├── src/            # Código-fonte principal (API + Dashboard)
├── tests/          # 12 arquivos de teste (pytest)
├── data/           # Banco SQLite — gitignored
├── assets/         # CSS, YAML de categorização e intenções
├── desktop/        # Entrypoint pywebview + build.spec
└── migrations/     # Migrações Alembic
```

---

## Impostos BR 2026

| Ativo                  | Alíquota                                                      |
|------------------------|---------------------------------------------------------------|
| Renda Fixa (CDB, Tesouro) | 17,5% sobre o ganho + IOF se resgate < 30 dias           |
| LCI / LCA              | 5% (novas emissões pós-reforma)                               |
| Ações — normal         | 17,5%                                                         |
| Ações — day trade      | 20%                                                           |
| Ações — isenção        | Vendas ≤ R$ 60 mil/trimestre                                  |
| FII — dividendos       | 5%                                                            |
| FII — ganho de capital | 17,5%                                                         |
| Carryforward de prejuízo | Até 5 anos                                                  |

---

## Licença

Distribuído sob a licença [MIT](LICENSE).
