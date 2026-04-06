"""FastAPI router para /pluggy (sync Open Banking)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
from src.core.exceptions import PluggyAuthError
from src.pluggy.client import PluggyClient
from src.pluggy.schemas import SyncResult
from src.pluggy.sync import PluggySync

router = APIRouter(prefix="/pluggy", tags=["pluggy"])


def _client() -> PluggyClient:
    s = get_settings()
    if not s.pluggy_api_key or not s.pluggy_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Pluggy nao configurado. Defina PLUGGY_API_KEY e PLUGGY_CLIENT_SECRET.",
        )
    return PluggyClient(client_id=s.pluggy_api_key, client_secret=s.pluggy_client_secret)


@router.post("/sync/{item_id}", response_model=SyncResult)
def full_sync(
    item_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    db: Session = Depends(get_db),
):
    """Sync completo de contas + transacoes de um item Pluggy."""
    client = _client()
    try:
        client.authenticate()
    except PluggyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sync = PluggySync(client, db)
    result = sync.full_sync(item_id, from_date, to_date)
    db.commit()
    return result


@router.post("/sync/{item_id}/accounts", response_model=SyncResult)
def sync_accounts(item_id: str, db: Session = Depends(get_db)):
    """Sync apenas de contas de um item Pluggy."""
    client = _client()
    try:
        client.authenticate()
    except PluggyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sync = PluggySync(client, db)
    result = sync.sync_accounts(item_id)
    db.commit()
    return result


@router.post("/sync/transactions/{pluggy_account_id}", response_model=SyncResult)
def sync_transactions(
    pluggy_account_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    db: Session = Depends(get_db),
):
    """Sync de transacoes de uma conta especifica."""
    client = _client()
    try:
        client.authenticate()
    except PluggyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sync = PluggySync(client, db)
    result = sync.sync_transactions(pluggy_account_id, from_date, to_date)
    db.commit()
    return result
