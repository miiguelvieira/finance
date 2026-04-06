"""FastAPI router para /chatbot."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.chatbot.engine import ChatbotEngine
from src.core.database import get_db
from src.core.models import ChatbotHistory

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatOut(BaseModel):
    intent: str
    response: str


def _engine(db: Session = Depends(get_db)) -> ChatbotEngine:
    return ChatbotEngine(db)


@router.post("/", response_model=ChatOut)
def chat(body: ChatIn, engine: ChatbotEngine = Depends(_engine)):
    intent = engine._classifier.classify(body.message)
    response = engine.reply(body.message)
    engine.db.commit()
    return ChatOut(intent=intent, response=response)


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatbotHistory)
        .order_by(ChatbotHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "user_message": r.user_message,
            "bot_response": r.bot_response,
            "intent": r.intent,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]
