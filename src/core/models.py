"""Definição de todas as tabelas ORM (source of truth para o schema)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Enums (strings simples — sem Enum do SQLAlchemy para portabilidade) ───────
ACCOUNT_TYPES = ("checking", "savings", "credit_card", "investment")
ASSET_TYPES = ("renda_fixa", "lci_lca", "acoes", "fii", "crypto", "other")
EVENT_TYPES = ("buy", "sell", "dividend", "income", "rebalance")
BALANCE_SOURCES = ("manual", "pluggy", "auto")
CATEGORIES = (
    "moradia", "alimentacao", "transporte", "saude", "educacao",
    "lazer", "vestuario", "assinaturas", "investimentos", "transferencia",
    "salario", "freelance", "dividendos", "outros",
)


# ── Tabelas ───────────────────────────────────────────────────────────────────

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ACCOUNT_TYPES
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    credit_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    pluggy_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    installments: Mapped[list[Installment]] = relationship("Installment", back_populates="account")
    balance_history: Mapped[list[BalanceHistory]] = relationship("BalanceHistory", back_populates="account", cascade="all, delete-orphan")
    income_sources: Mapped[list[IncomeSource]] = relationship("IncomeSource", back_populates="account")
    investments: Mapped[list[Investment]] = relationship("Investment", back_populates="account")
    goals: Mapped[list[Goal]] = relationship("Goal", back_populates="linked_account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # positivo=crédito, negativo=débito
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="outros")
    subcategory: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    competence_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    installment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("installments.id"), nullable=True)
    transfer_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)  # UUID para pares de transferência
    pluggy_transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped[Account] = relationship("Account", back_populates="transactions")
    installment: Mapped[Installment | None] = relationship("Installment", back_populates="transactions")


class Installment(Base):
    __tablename__ = "installments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    installment_value: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_count: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="outros")
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped[Account] = relationship("Account", back_populates="installments")
    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="installment")


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ASSET_TYPES
    ticker: Mapped[str | None] = mapped_column(String(10), nullable=True)
    principal: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rate_description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pluggy_investment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    account: Mapped[Account | None] = relationship("Account", back_populates="investments")
    events: Mapped[list[InvestmentEvent]] = relationship("InvestmentEvent", back_populates="investment", cascade="all, delete-orphan")


class InvestmentEvent(Base):
    __tablename__ = "investment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investment_id: Mapped[int] = mapped_column(Integer, ForeignKey("investments.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EVENT_TYPES
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    taxes_paid: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    investment: Mapped[Investment] = relationship("Investment", back_populates="events")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    linked_account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="target")
    color: Mapped[str] = mapped_column(String(7), default="#2962ff")
    is_achieved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    linked_account: Mapped[Account | None] = relationship("Account", back_populates="goals")


class BalanceHistory(Base):
    __tablename__ = "balance_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(10), default="manual")  # BALANCE_SOURCES

    account: Mapped[Account] = relationship("Account", back_populates="balance_history")


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account: Mapped[Account | None] = relationship("Account", back_populates="income_sources")


class ChatbotHistory(Base):
    __tablename__ = "chatbot_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    bot_response: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
