import sys
import logging
import datetime
from decimal import Decimal, InvalidOperation
from typing import NoReturn
from BankClass import Bank
from AccountClass import Account
from CustomException import OverdrawError, TransactionSequenceError, TransactionLimitError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from Models import Base


logger = logging.getLogger(__name__)


class BankMenu:
    """Display the bank menu."""

    def __init__(self) -> None:
        """Initializes the bank and database connection."""
        self.engine = create_engine("sqlite:///bank.db")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.bank = Bank(self.session)

    def _display_menu(self) -> None:
        selected_account: Account = self.bank.get_selected_account()
        account_info = (f'{selected_account.name},\tbalance: {self.bank.format_amount(selected_account.balance)}'
                        if selected_account else "None")
        print(
"--------------------------------\n"
f"Currently selected account: {account_info}\n"
"Enter command\n"
"1: open account\n"
"2: summary\n"
"3: select account\n"
"4: add transaction\n"
"5: list transactions\n"
"6: interest and fees\n"
"7: quit"
)

    def run(self) -> NoReturn:
        """Display the menu and respond to choices until the user quits."""
        while True:
            self._display_menu()
            choice = input(">")
            if choice == "1":
                self._open_account()
            elif choice == "2":
                self._summary()
            elif choice == "3":
                self._select_account()
            elif choice == "4":
                self._add_transaction()
            elif choice == "5":
                self._list_transactions()
            elif choice == "6":
                self._apply_interest_and_fees()
            elif choice == "7":
                self._quit()

    def _open_account(self) -> None:
        while True:
            try:
                account_type = input("Type of account? (checking/savings)\n>").strip().capitalize()
                self.bank.open_account(account_type)
                self.bank.commit()
                break
            except ValueError as e:
                print(e)

    def _summary(self) -> None:
        self.bank.summary()

    @staticmethod
    def _get_valid_input(prompt: str, input_validation, error_message: str, exceptions=(ValueError,)):
        """Helper to repeatedly prompt for valid input."""
        while True:
            try:
                return input_validation(input(prompt).strip())
            except exceptions:
                print(error_message)

    def _select_account(self) -> None:
        while True:
            account_number = BankMenu._get_valid_input(
                "Enter account number\n>",
                lambda x: int(x),
                "Please enter a valid account number."
            )
            try:
                self.bank.select_account(account_number)
                break
            except AttributeError as e:
                print(e)

    def _add_transaction(self) -> None:
        selected_account: Account = self.bank.get_selected_account()
        if selected_account is None:
            print("This command requires that you first select an account.")
            return

        try:
            amount = BankMenu._get_valid_input(
                "Amount?\n>",
                lambda x: Decimal(x),
                "Please try again with a valid dollar amount.",
                (ValueError, InvalidOperation)
            )

            date = BankMenu._get_valid_input(
                "Date? (YYYY-MM-DD)\n>",
                lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date(),
                "Please try again with a valid date in the format YYYY-MM-DD."
            )

            self.bank.add_transaction(amount, date)
            self.bank.commit()

        except (OverdrawError, TransactionLimitError, TransactionSequenceError) as e:
            print(e)
            return

    def _list_transactions(self) -> None:
        try:
            self.bank.list_transactions()
        except AttributeError as e:
            print(e)
            return

    def _apply_interest_and_fees(self) -> None:
        try:
            self.bank.interest_and_fees()
            self.bank.commit()
        except (ValueError, TypeError, AttributeError, TransactionSequenceError) as e:
            print(e)
            return

    def _quit(self) -> NoReturn:
        self.session.commit()
        self.session.close()
        sys.exit(0)
