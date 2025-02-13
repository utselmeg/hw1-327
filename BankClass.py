import logging
from decimal import Decimal, ROUND_HALF_UP
from TransactionClass import TransactionType
from AccountClass import Account, AccountType, SavingsAccount, CheckingAccount
from CustomException import OverdrawError, TransactionSequenceError

logger = logging.getLogger(__name__)

class Bank:
    """Represents a banking system that manages multiple accounts."""

    def __init__(self):
        """Initializes the bank with an empty dictionary of accounts."""
        self._accounts = {}  # dictionary to store accounts by account number
        self._selected: Account | None = None
        self._num_accounts: int = 0

    def open_account(self, account_type: str) -> None:
        """Opens a new account of the specified type."""
        try:
            acc_type_enum = AccountType.from_string(account_type)
        except ValueError as e:
            raise e

        if acc_type_enum == AccountType.CHECKING:
            new_account = CheckingAccount(self._num_accounts + 1)
        else:
            new_account = SavingsAccount(self._num_accounts + 1)

        self._num_accounts += 1
        self._accounts[self._num_accounts] = new_account
        logger.debug(f"Created account: {self._num_accounts}")

    @classmethod
    def format_amount(cls, amount: Decimal) -> str:
        """Formats a monetary amount to two decimal places rounded up."""
        return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"

    def summary(self) -> None:
        """Prints a summary of all accounts and their balances."""
        if not self._accounts:
            # print("No accounts in bank.")
            return

        for account in self._accounts.values():
            print(f"{account.name},\tbalance: {self.format_amount(account.balance)}")

    def get_selected_account(self) -> Account | None:
        """Returns the currently selected account."""
        return self._selected

    def select_account(self, account_number: int | None) -> None:
        """Selects an account by its account number. Allows None to deselect."""
        if account_number is None:
            self._selected = None
        elif account_number in self._accounts:
            self._selected = self._accounts[account_number]
        else:
            raise AttributeError("Invalid account number.")

    def add_transaction(self, amount: Decimal, date) -> None:
        """Adds a transaction to the selected account."""
        logger.debug(f"Created transaction: {self._selected.account_number}, {amount}")
        try:
            transaction_type = (TransactionType.WITHDRAWAL if amount < 0 else TransactionType.DEPOSIT)
            self._selected.add_transaction(amount, date, transaction_type)
        except (OverdrawError, TransactionSequenceError) as e:
            raise e

    def list_transactions(self) -> None:
        """Lists all transactions for the selected account."""
        if not self.get_selected_account():
            raise AttributeError("This command requires that you first select an account.")

        transactions = self._selected.list_transactions()
        if transactions:
            for transaction in transactions:
                print(f"{transaction.date}, {self.format_amount(transaction.amount)}")
        else:
            # print("No transactions to show on this account.")
            return

    def interest_and_fees(self) -> None:
        """When invoked, apply interests and fees to the selected account."""
        if not self.get_selected_account():
            raise AttributeError("This command requires that you first select an account.")

        try:
            self._selected.apply_interest_and_fees()
            logger.debug("Triggered interest and fees")
        except TransactionSequenceError as e:
            raise e
