import calendar
import datetime
from decimal import Decimal
from TransactionClass import Transaction
from enum import Enum
from typing import List

class AccountType(Enum):
    """Enum representing account types with numerical values."""
    CHECKING = 1
    SAVINGS = 2

    @classmethod
    def from_string(cls, type_str: str):
        """Converts a string ('Checking' or 'Savings') to an AccountType enum."""
        if type_str.lower() == "checking":
            return cls.CHECKING
        elif type_str.lower() == "savings":
            return cls.SAVINGS
        raise ValueError(f"Invalid account type: {type_str}")

    def __str__(self):
        """Returns the readable string representation of the account type."""
        return "Checking" if self == AccountType.CHECKING else "Savings"

class Account:
    """Represents a bank account with transaction management."""

    class InterestRateMonthly:
        CHECKING = Decimal(0.08)
        SAVINGS = Decimal(0.33)

    def __init__(self, account_type: AccountType, account_number: int):
        """Initialize a new account with a $0.00 starting balance."""
        self._account_type: AccountType = account_type
        self._account_number: int = account_number
        self._name: str = f"{str(account_type)}#{str(account_number).zfill(9)}"
        self._balance: Decimal = Decimal(0)
        self._transactions: List[Transaction] = []

    def get_balance(self) -> Decimal:
        """Returns the current balance of the account."""
        return self._balance

    def get_name(self) -> str:
        """Returns the account name."""
        return self._name

    def get_account_number(self) -> int:
        """Returns the account number."""
        return self._account_number

    def add_transaction(self, amount: Decimal, date) -> None:
        """Adds a transaction to the account if it passes validation checks."""
        if self._balance + amount < 0:
            return

        self._transactions.append(Transaction(self._account_number, date, amount))
        self._transactions.sort(key=lambda t: t.date)
        self._update_balance()

    def _update_balance(self) -> None:
        """Updates the account balance based on all transactions."""
        self._balance = sum(Decimal(t.amount) for t in self._transactions)

    def list_transactions(self) -> List[Transaction]:
        """Returns all transactions sorted by date."""
        return sorted(self._transactions, key=lambda t: t.date)

    def apply_interest_and_fees(self) -> None:
        interest_rate = (
            self.InterestRateMonthly.SAVINGS
            if self._account_type == AccountType.SAVINGS
            else self.InterestRateMonthly.CHECKING
        )

        if not self._transactions:
            last_transaction_date = datetime.date.today()
        else:
            last_transaction_date = self._transactions[-1].date

        last_day_of_month = calendar.monthrange(last_transaction_date.year, last_transaction_date.month)[1]
        fee_date = last_transaction_date.replace(day=last_day_of_month)

        interest = (self._balance * interest_rate) / Decimal(100)
        if isinstance(self, SavingsAccount):
            self.add_transaction(interest, fee_date, bypass_limit=True)
        elif isinstance(self, CheckingAccount):
            self.add_transaction(interest, fee_date, bypass_limit=True)
        else:
            self.add_transaction(interest, fee_date)

        if isinstance(self, CheckingAccount) and self._balance < 100:
            self.add_transaction(Decimal(-5.75), fee_date, bypass_limit=True)

        self._transactions.sort(key=lambda transaction: transaction.date)
        self._update_balance()

    def __str__(self) -> str:
        return f"{self._name} - Balance: ${self._balance:,.2f}"

class SavingsAccount(Account):
    """Represents a savings account with transaction limits."""

    MAX_DAILY_TRANSACTIONS = 2
    MAX_MONTHLY_TRANSACTIONS = 5

    def __init__(self, account_number: int):
        super().__init__(AccountType.SAVINGS, account_number)

    def _can_add_transaction(self, date) -> bool:
        """Checks if the account meets daily and monthly transaction limits."""
        daily_count = sum(1 for t in self._transactions if t.date == date)
        monthly_count = sum(1 for t in self._transactions if t.date.month == date.month and t.date.year == date.year)

        return daily_count < self.MAX_DAILY_TRANSACTIONS and monthly_count < self.MAX_MONTHLY_TRANSACTIONS

    def add_transaction(self, amount: Decimal, date, bypass_limit=False) -> None:
        """Overrides transaction logic to enforce savings account limits."""
        if not bypass_limit and not self._can_add_transaction(date):
            # print("savings account limit reached")
            return
        super().add_transaction(amount, date)


class CheckingAccount(Account):
    """Represents a checking account with standard transaction rules."""

    def __init__(self, account_number: int):
        super().__init__(AccountType.CHECKING, account_number)

    def add_transaction(self, amount: Decimal, date, bypass_limit=False) -> None:
        """Allows overdraft for fees and interest but prevents user withdrawals from overdrawing."""
        if not bypass_limit and self._balance + amount < 0:
            # print("Insufficient funds")
            return

        self._transactions.append(Transaction(self._account_number, date, amount))
        self._transactions.sort(key=lambda t: t.date)
        self._update_balance()
