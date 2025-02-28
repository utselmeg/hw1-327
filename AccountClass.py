import logging
import datetime
from typing import List, Optional
from decimal import Decimal
from AccountType import AccountType
from TransactionClass import Transaction, TransactionType
from CustomException import OverdrawError, TransactionSequenceError, TransactionLimitError
from Models import Account as AccountModel, SavingsAccount as SavingsAccountModel, \
    CheckingAccount as CheckingAccountModel, Transaction as TransactionModel

logger = logging.getLogger(__name__)

class Account:
    """Represents a bank account with transaction management."""

    INTEREST_RATES = {
        AccountType.CHECKING: Decimal(0.08),
        AccountType.SAVINGS: Decimal(0.33),
    }

    def __init__(self, account_type: AccountType, account_number: int, model: Optional[AccountModel] = None):
        """Initialize a new account with a $0.00 starting balance."""
        self._account_type: AccountType = account_type
        self._account_number: int = account_number
        self._name: str = f"{str(account_type)}#{str(account_number).zfill(9)}"
        self._balance: Decimal = Decimal(0)
        self._transactions: List[Transaction] = []

        if model:
            self._model = model
            self._account_number = model.account_number
            self._name = model.name
            self._balance = model.balance
            self._transactions = [
                Transaction(
                    t.account_number,
                    t.date,
                    t.amount,
                    TransactionType(t.transaction_type)
                ) for t in model.transactions
            ]
        else:
            self._model = None

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

    @property
    def model(self) -> AccountModel:
        """Returns the database model."""
        return self._model

    def add_transaction(self, amount: Decimal, date: datetime.date, transaction_type: TransactionType) -> None:
        """Adds a transaction to the account if it passes validation checks."""
        new_transaction = Transaction(self._account_number, date, amount, transaction_type)
        Transaction.validate_transaction(self._transactions, new_transaction)

        self._transactions.append(new_transaction)
        self._update_balance()

        transaction_model = TransactionModel(
            account_number=self._account_number,
            date=date,
            amount=amount,
            transaction_type=transaction_type.value
        )
        self._model.transactions.append(transaction_model)
        self._model.balance = self._balance

    def _update_balance(self) -> None:
        """Updates the account balance based on all transactions."""
        self._balance = sum(Decimal(t.amount) for t in self._transactions)
        if self._model:
            self._model.balance = self._balance

    def list_transactions(self) -> List[Transaction]:
        """Returns all transactions sorted by date."""
        return sorted(self._transactions, key=lambda t: t.date)

    def apply_interest_and_fees(self) -> None:
        interest_rate = self.INTEREST_RATES[self._account_type]
        last_transaction = Transaction.get_last_transaction(self._transactions)
        fee_date = Transaction.last_day_of_month(last_transaction.date) if self._transactions else datetime.date.today()

        if any(t.transaction_type in {TransactionType.INTEREST, TransactionType.FEE} for t in self._transactions if t.date.month == fee_date.month):
            raise TransactionSequenceError(fee_date, error_type="interest")

        interest = (self._balance * interest_rate) / Decimal(100)
        logger.debug(f"Created transaction: {self.account_number}, {interest}")
        if isinstance(self, SavingsAccount) or isinstance(self, CheckingAccount):
            self.add_transaction(interest, fee_date, TransactionType.INTEREST, bypass_limit=True)
        self._apply_account_fees(fee_date)
        self._update_balance()

    def _apply_account_fees(self, fee_date):
        """Applies fees for account types that require them."""
        pass


class SavingsAccount(Account):
    """Represents a savings account with transaction limits."""

    MAX_DAILY_TRANSACTIONS = 2
    MAX_MONTHLY_TRANSACTIONS = 5

    def __init__(self, account_number: int, model: Optional[SavingsAccountModel] = None):
        if not model:
            model = SavingsAccountModel(
                account_number=account_number,
                account_type="savings",
                name=f"{str(AccountType.SAVINGS)}#{str(account_number).zfill(9)}",
                balance=Decimal(0)
            )
        super().__init__(AccountType.SAVINGS, account_number, model)

    def _can_add_transaction(self, date: datetime.date) -> bool:
        """Checks if the account meets daily and monthly transaction limits."""
        daily_count = sum(1 for t in self._transactions if t.date == date)
        monthly_count = sum(1 for t in self._transactions if t.date.month == date.month and t.date.year == date.year)

        return daily_count < self.MAX_DAILY_TRANSACTIONS and monthly_count < self.MAX_MONTHLY_TRANSACTIONS

    def add_transaction(self, amount: Decimal, date: datetime.date, transaction_type: TransactionType, bypass_limit=False) -> None:
        """Overrides transaction logic to enforce savings account limits."""
        if not bypass_limit and self._balance + amount < 0 and transaction_type != TransactionType.DEPOSIT:
            raise OverdrawError()
        if not bypass_limit and not self._can_add_transaction(date):
            raise TransactionLimitError("daily" if sum(1 for t in self._transactions if t.date == date) >= self.MAX_DAILY_TRANSACTIONS else "monthly")

        super().add_transaction(amount, date, transaction_type)


class CheckingAccount(Account):
    """Represents a checking account with standard transaction rules."""

    MIN_BALANCE_FOR_FEE = Decimal(100)
    OVERDRAFT_FEE = Decimal(-5.75)

    def __init__(self, account_number: int, model: Optional[CheckingAccountModel] = None):
        if not model:
            model = CheckingAccountModel(
                account_number=account_number,
                account_type="checking",
                name=f"{str(AccountType.CHECKING)}#{str(account_number).zfill(9)}",
                balance=Decimal(0)
            )
        super().__init__(AccountType.CHECKING, account_number, model)

    def add_transaction(self, amount: Decimal, date: datetime.date, transaction_type: TransactionType, bypass_limit=False) -> None:
        """Allows overdraft for fees and interest but prevents user withdrawals from overdrawing."""
        if not bypass_limit and self._balance + amount < 0 and transaction_type != TransactionType.DEPOSIT:
            raise OverdrawError()
        super().add_transaction(amount, date, transaction_type)

    def _apply_account_fees(self, fee_date: datetime.date) -> None:
        """Applies an overdraft fee if the balance is too low."""
        if self.balance < self.MIN_BALANCE_FOR_FEE:
            logger.debug(f"Created transaction: {self.account_number}, {self.OVERDRAFT_FEE}")
            self.add_transaction(self.OVERDRAFT_FEE, fee_date, TransactionType.FEE, bypass_limit=True)
