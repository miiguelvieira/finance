"""FastAPI application — ponto de entrada da API REST."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.accounts.router import router as accounts_router
from src.chatbot.router import router as chatbot_router
from src.core.config import get_settings
from src.core.database import setup
from src.installments.router import income_router, router as installments_router
from src.investments.router import router as investments_router
from src.pluggy.router import router as pluggy_router
from src.projections.router import router as projections_router
from src.transactions.router import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup(settings.database_url)
    yield


app = FastAPI(
    title="Finance API",
    version="0.1.0",
    lifespan=lifespan,
)

import os as _os
_cors_extra = _os.environ.get("CORS_ORIGINS", "").split(",")
_origins = ["http://localhost:8050", "http://127.0.0.1:8050"] + [o for o in _cors_extra if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(installments_router)
app.include_router(income_router)
app.include_router(projections_router)
app.include_router(investments_router)
app.include_router(pluggy_router)
app.include_router(chatbot_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "finance-api"}


if __name__ == "__main__":
    import uvicorn
    s = get_settings()
    uvicorn.run("src.api.main:app", host=s.host, port=s.api_port, reload=True)
