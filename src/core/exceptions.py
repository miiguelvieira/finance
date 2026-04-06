"""Hierarquia de exceções do domínio Finance."""


class FinanceException(Exception):
    """Base exception para todos os erros do domínio."""


class AccountNotFound(FinanceException):
    def __init__(self, account_id: int):
        super().__init__(f"Conta {account_id} não encontrada")
        self.account_id = account_id


class InsufficientBalance(FinanceException):
    def __init__(self, available: float, required: float):
        super().__init__(f"Saldo insuficiente: disponível R${available:.2f}, necessário R${required:.2f}")
        self.available = available
        self.required = required


class InstallmentNotFound(FinanceException):
    def __init__(self, installment_id: int):
        super().__init__(f"Parcelamento {installment_id} não encontrado")


class InvestmentNotFound(FinanceException):
    def __init__(self, investment_id: int):
        super().__init__(f"Investimento {investment_id} não encontrado")


class GoalNotFound(FinanceException):
    def __init__(self, goal_id: int):
        super().__init__(f"Meta {goal_id} não encontrada")


class PluggyAuthError(FinanceException):
    """Falha de autenticação com a API Pluggy."""


class TaxCalculationError(FinanceException):
    """Erro no cálculo de impostos."""


class ConfigError(FinanceException):
    """Erro de configuração do sistema."""
