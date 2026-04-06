"""PluggySync — sincroniza dados da API Pluggy para o banco local."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.accounts.service import AccountService
from src.core.models import Account, Transaction
from src.pluggy.client import PluggyClient
from src.pluggy.schemas import SyncResult
from src.transactions.categorizer import Categorizer

_categorizer = Categorizer()

# Subtype Pluggy -> account_type local
_SUBTYPE_MAP = {
    "CHECKING_ACCOUNT": "checking",
    "SAVINGS_ACCOUNT": "savings",
    "CREDIT_CARD": "credit_card",
    "INVESTMENT": "investment",
}


def _map_subtype(subtype: str) -> str:
    return _SUBTYPE_MAP.get(subtype.upper(), "checking")


class PluggySync:
    def __init__(self, client: PluggyClient, db: Session):
        self.client = client
        self.db = db
        self._acc_svc = AccountService(db)

    # ── Sync de contas ────────────────────────────────────────────────────────

    def sync_accounts(self, item_id: str) -> SyncResult:
        result = SyncResult()
        try:
            pluggy_accounts = self.client.get_accounts(item_id)
        except Exception as e:
            result.errors.append(f"Erro ao buscar contas do item {item_id}: {e}")
            return result

        for pa in pluggy_accounts:
            existing = (
                self.db.query(Account)
                .filter(Account.pluggy_account_id == pa.id)
                .first()
            )
            if existing:
                existing.balance = pa.balance
                result.accounts_updated += 1
            else:
                self._acc_svc.create(
                    name=pa.marketingName or pa.name,
                    bank_name=pa.name,
                    account_type=_map_subtype(pa.subtype),
                    balance=pa.balance,
                    pluggy_account_id=pa.id,
                )
                result.accounts_created += 1

        self.db.flush()
        return result

    # ── Sync de transações ────────────────────────────────────────────────────

    def sync_transactions(
        self,
        pluggy_account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> SyncResult:
        result = SyncResult()

        local_account = (
            self.db.query(Account)
            .filter(Account.pluggy_account_id == pluggy_account_id)
            .first()
        )
        if local_account is None:
            result.errors.append(
                f"Conta pluggy_account_id={pluggy_account_id} nao encontrada localmente. "
                "Execute sync_accounts primeiro."
            )
            return result

        try:
            txs = self.client.get_all_transactions(pluggy_account_id, from_date, to_date)
        except Exception as e:
            result.errors.append(f"Erro ao buscar transacoes de {pluggy_account_id}: {e}")
            return result

        for pt in txs:
            existing = (
                self.db.query(Transaction)
                .filter(Transaction.pluggy_transaction_id == pt.id)
                .first()
            )
            if existing:
                result.transactions_skipped += 1
                continue

            # Pluggy: positivo para crédito, negativo para débito
            amount = pt.amount if pt.type == "CREDIT" else -abs(pt.amount)
            category, subcategory = _categorizer.classify(pt.description)
            tx_date = pt.date.date() if isinstance(pt.date, datetime) else pt.date

            self.db.add(Transaction(
                account_id=local_account.id,
                amount=amount,
                description=pt.description,
                category=category,
                subcategory=subcategory,
                transaction_date=tx_date,
                pluggy_transaction_id=pt.id,
            ))
            result.transactions_created += 1

        self.db.flush()
        return result

    # ── Sync completo ─────────────────────────────────────────────────────────

    def full_sync(
        self,
        item_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> SyncResult:
        total = SyncResult()

        acc_result = self.sync_accounts(item_id)
        total.merge(acc_result)

        if acc_result.errors:
            return total  # não tenta sync de transações se contas falharam

        try:
            pluggy_accounts = self.client.get_accounts(item_id)
        except Exception as e:
            total.errors.append(f"Erro relisting contas para sync tx: {e}")
            return total

        for pa in pluggy_accounts:
            tx_result = self.sync_transactions(pa.id, from_date, to_date)
            total.merge(tx_result)

        return total
