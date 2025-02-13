from __future__ import annotations
from enum import Enum
from decimal import Decimal
from datetime import date, timedelta
from CustomException import TransactionSequenceError


class TransactionType(Enum):
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    INTEREST = "Interest"
    FEE = "Fee"

class Transaction:
    """Represents a transaction on an account."""

    def __init__(self, account_number: int, transaction_date: date, amount: Decimal, transaction_type: TransactionType):
        """Initialize a new transaction."""
        self.account_number: int = account_number
        self.date: date = transaction_date
        self.amount: Decimal = amount
        self.transaction_type: TransactionType = transaction_type

    @classmethod
    def get_last_transaction(cls, transactions: list["Transaction"]) -> Transaction | None:
        """Returns the most recent transaction, or None if there are no transactions."""
        return max(transactions, key=lambda t: t.date, default=None)

    @staticmethod
    def last_day_of_month(transaction_date: date) -> date:
        """Returns the last day of the given month."""
        first_of_next_month = date(transaction_date.year + transaction_date.month // 12,
                                   transaction_date.month % 12 + 1, 1)
        return first_of_next_month - timedelta(days=1)

    @staticmethod
    def validate_transaction(transactions: list["Transaction"], new_transaction: "Transaction") -> None:
        """Check whether the new transaction follows sequence rules."""
        if not transactions:
            return

        last_transaction = max(transactions, key=lambda t: t.date)

        if last_transaction.date > new_transaction.date:
            raise TransactionSequenceError(last_transaction.date, error_type="sequence")
