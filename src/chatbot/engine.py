"""ChatbotEngine — intent classification + resposta com dados do banco."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from src.chatbot import responses as resp
from src.chatbot.intents import IntentClassifier
from src.core.models import Account, ChatbotHistory, Goal
from src.investments.service import InvestmentService
from src.projections.engine import ProjectionEngine
from src.transactions.service import TransactionService


class ChatbotEngine:
    def __init__(self, db: Session, intents_path: str = "assets/intents.yaml"):
        self.db = db
        self._classifier = IntentClassifier(intents_path)
        self._tx_svc = TransactionService(db)
        self._inv_svc = InvestmentService(db)

    def reply(self, user_message: str, save_history: bool = True) -> str:
        intent = self._classifier.classify(user_message)
        response = self._dispatch(intent)

        if save_history:
            self.db.add(ChatbotHistory(
                user_message=user_message,
                bot_response=response,
                intent=intent,
            ))
            self.db.flush()

        return response

    def _dispatch(self, intent: str) -> str:
        if intent == "saldo":
            accounts = (
                self.db.query(Account)
                .filter(Account.is_active == True)
                .all()
            )
            return resp.build_saldo([
                {"name": a.name, "bank_name": a.bank_name, "balance": a.balance}
                for a in accounts
            ])

        if intent == "gastos":
            today = date.today()
            summary = self._tx_svc.monthly_summary(today.year, today.month)
            return resp.build_gastos(summary)

        if intent == "transacoes":
            txs = self._tx_svc.list(limit=10)
            return resp.build_transacoes([
                {
                    "transaction_date": str(t.transaction_date),
                    "description": t.description,
                    "amount": t.amount,
                    "category": t.category,
                }
                for t in txs
            ])

        if intent == "investimentos":
            portfolio = self._inv_svc.portfolio_summary()
            return resp.build_investimentos(portfolio)

        if intent == "metas":
            goals = self.db.query(Goal).all()
            return resp.build_metas([
                {
                    "name": g.name,
                    "current_amount": g.current_amount,
                    "target_amount": g.target_amount,
                    "is_achieved": g.is_achieved,
                }
                for g in goals
            ])

        if intent == "projecao":
            engine = ProjectionEngine(self.db)
            result = engine.project()
            last_balance = result.months[-1].base if result.months else result.current_balance
            return resp.build_projecao(
                projected_balance=last_balance,
                trend=result.trend,
                days=len(result.months) * 30,
            )

        if intent == "impostos":
            return resp.build_impostos()

        if intent == "ajuda":
            return resp.HELP_TEXT

        return resp.UNKNOWN_TEXT
