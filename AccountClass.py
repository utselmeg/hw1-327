import datetime
from typing import List
from decimal import Decimal
from AccountType import AccountType
from TransactionClass import Transaction, TransactionType
from CustomException import OverdrawError, TransactionSequenceError, TransactionLimitError


class Account:
    """Represents a bank account with transaction management."""

    INTEREST_RATES = {
        AccountType.CHECKING: Decimal(0.08),
        AccountType.SAVINGS: Decimal(0.33),
    }

    def __init__(self, account_type: AccountType, account_number: int):
        """Initialize a new account with a $0.00 starting balance."""
        self._account_type: AccountType = account_type
        self._account_number: int = account_number
        self._name: str = f"{str(account_type)}#{str(account_number).zfill(9)}"
        self._balance: Decimal = Decimal(0)
        self._transactions: List[Transaction] = []

    def __str__(self) -> str:
        return f"{self._name} - Balance: ${self._balance:,.2f}"

    @property
    def balance(self) -> Decimal:
        """Returns the current balance of the account."""
        return self._balance

    @property
    def name(self) -> str:
        """Returns the account name."""
        return self._name

    @property
    def account_number(self) -> int:
        """Returns the account number."""
        return self._account_number

    def get_last_transaction(self) -> Transaction | None:
        """Returns the most recent transaction, or None if there are no transactions."""
        return max(self._transactions, key=lambda t: t.date, default=None)

    def add_transaction(self, amount: Decimal, date, transaction_type: TransactionType) -> None:
        """Adds a transaction to the account if it passes validation checks."""
        if self._balance + amount < 0:
            raise OverdrawError()

        Transaction.validate_transaction(self._transactions,
                                         Transaction(self._account_number, date, amount, transaction_type))
        # if len(self._transactions) > 0:
        #     last_transaction = self.get_last_transaction()
        #     last_transaction_date = Transaction.last_day_of_month(last_transaction.date)
        #     print(last_transaction_date, date)
        #     if last_transaction_date > date and last_transaction.transaction_type not in {TransactionType.FEE, TransactionType.INTEREST}:
        #         print("sequence error")
        #         raise TransactionSequenceError(last_transaction_date, error_type="sequence")

        self._transactions.append(Transaction(self._account_number, date, amount, transaction_type))
        self._update_balance()

    def _update_balance(self) -> None:
        """Updates the account balance based on all transactions."""
        self._balance = sum(Decimal(t.amount) for t in self._transactions)

    def list_transactions(self) -> List[Transaction]:
        """Returns all transactions sorted by date."""
        return sorted(self._transactions, key=lambda t: t.date)

    def apply_interest_and_fees(self) -> None:
        interest_rate = self.INTEREST_RATES[self._account_type]
        last_transaction = self.get_last_transaction()
        fee_date = Transaction.last_day_of_month(last_transaction.date) if self._transactions else datetime.date.today()

        # for transaction in reversed(self._transactions):
        #     if transaction.date.month != fee_date.month:
        #         break
        #     if transaction.transaction_type in {TransactionType.INTEREST, TransactionType.FEE}:
        #         raise TransactionSequenceError(fee_date, error_type="interest")
        if any(t.transaction_type in {TransactionType.INTEREST, TransactionType.FEE} for t in self._transactions if t.date.month == fee_date.month):
            raise TransactionSequenceError(fee_date, error_type="interest")

        interest = (self._balance * interest_rate) / Decimal(100)
        self.add_transaction(interest, fee_date, TransactionType.INTEREST)
        self._apply_account_fees(fee_date)
        self._update_balance()

        # if isinstance(self, SavingsAccount):
        #     self.add_transaction(interest, fee_date, TransactionType.INTEREST, bypass_limit=True)
        # elif isinstance(self, CheckingAccount):
        #     self.add_transaction(interest, fee_date, TransactionType.INTEREST, bypass_limit=True)
        # else:
        #     self.add_transaction(interest, fee_date, TransactionType.INTEREST)
        #
        # if isinstance(self, CheckingAccount) and self._balance < 100:
        #     self.add_transaction(Decimal(-5.75), fee_date,TransactionType.FEE,  bypass_limit=True)

        # self._transactions.sort(key=lambda transaction: transaction.date)
        # self._update_balance()

    def _apply_account_fees(self, fee_date):
        """Applies fees for account types that require them."""
        pass

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

    def add_transaction(self, amount: Decimal, date, transaction_type: TransactionType, bypass_limit=False) -> None:
        """Overrides transaction logic to enforce savings account limits."""
        if not bypass_limit and not self._can_add_transaction(date):
            raise TransactionLimitError("daily" if sum(1 for t in self._transactions if t.date == date) >= self.MAX_DAILY_TRANSACTIONS else "monthly")

        super().add_transaction(amount, date, transaction_type)


class CheckingAccount(Account):
    """Represents a checking account with standard transaction rules."""

    MIN_BALANCE_FOR_FEE = 100
    OVERDRAFT_FEE = Decimal(-5.75)

    def __init__(self, account_number: int):
        super().__init__(AccountType.CHECKING, account_number)

    def add_transaction(self, amount: Decimal, date, transaction_type: TransactionType, bypass_limit=False) -> None:
        """Allows overdraft for fees and interest but prevents user withdrawals from overdrawing."""
        if not bypass_limit and self._balance + amount < 0:
            raise OverdrawError()

        last_transaction = self.get_last_transaction()
        last_transaction_date = last_transaction.date if self._transactions else None

        if last_transaction_date and last_transaction_date > date:
            raise TransactionSequenceError(last_transaction_date, error_type="sequence")

        super().add_transaction(amount, date, transaction_type)

    def _apply_account_fees(self, fee_date):
        """Applies an overdraft fee if the balance is too low."""
        if self.balance < self.MIN_BALANCE_FOR_FEE:
            self.add_transaction(self.OVERDRAFT_FEE, fee_date, TransactionType.FEE, bypass_limit=True)
