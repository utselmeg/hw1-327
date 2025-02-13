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
    def last_day_of_month(cls, transaction_date: date) -> date:
        """Returns the last day of the given month."""
        first_of_next_month = date(transaction_date.year + transaction_date.month // 12,
                                   transaction_date.month % 12 + 1, 1)
        return first_of_next_month - timedelta(days=1)

    @staticmethod
    def validate_transaction(transactions: list["Transaction"], new_transaction: "Transaction") -> None:
        """Ensures the new transaction follows sequence rules."""
        if not transactions:
            return

        last_transaction = max(transactions, key=lambda t: t.date)
        last_transaction_date = Transaction.last_day_of_month(last_transaction.date)

        if last_transaction_date > new_transaction.date and last_transaction.transaction_type not in {TransactionType.FEE,
                                                                                                      TransactionType.INTEREST}:
            raise TransactionSequenceError(last_transaction_date, error_type="sequence")