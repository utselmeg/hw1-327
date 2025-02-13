from decimal import Decimal
import datetime

class Transaction:
    """Represents a transaction on an account."""

    def __init__(self, account_number: int, date: datetime.date, amount: Decimal):
        """Initialize a new transaction."""
        self.account_number: int = account_number
        self.date: datetime.date = date
        self.amount: Decimal = amount
