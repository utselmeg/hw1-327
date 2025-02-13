import os
import sys
import pickle
import datetime
from decimal import Decimal
from typing import NoReturn
from BankClass import Bank
from AccountClass import Account

class BankMenu:
    """Display the bank menu."""

    def __init__(self) -> None:
        """Initializes the bank.
        If there is a local save file named bank.pickle, it loads it.
        Otherwise, it creates a new bank."""
        self._load()

    def _display_menu(self) -> None:
        selected_account: Account = self.bank.get_selected_account()
        account_info = (f'{selected_account.get_name()},\tbalance: {self.bank.format_amount(selected_account.get_balance())}'
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
        account_type = input("Type of account? (checking/savings)\n>").strip().capitalize()
        self.bank.open_account(account_type)

    def _summary(self) -> None:
        self.bank.summary()

    def _select_account(self) -> None:
        try:
            account_number = int(input("Enter account number\n>"))
            self.bank.select_account(account_number)
        except ValueError:
            # print("invalid input")
            return

    def _add_transaction(self) -> None:
        try:
            amount = Decimal(input("Amount?\n>"))
            date_input = input("Date? (YYYY-MM-DD)\n>").strip()
            date = datetime.datetime.strptime(date_input, "%Y-%m-%d").date()
            self.bank.add_transaction(amount, date)
        except (ValueError, TypeError):
            # print("invalid input")
            return

    def _list_transactions(self) -> None:
        self.bank.list_transactions()

    def _apply_interest_and_fees(self) -> None:
        self.bank.interest_and_fees()

    def _save(self) -> None:
        with open("bank.pickle", "wb") as file:
            pickle.dump(self.bank, file)  # type: ignore

    def _load(self) -> None:
        if os.path.exists("bank.pickle"):
            with open("bank.pickle", "rb") as file:
                self.bank = pickle.load(file)
                self.bank.select_account(None)
        else:
            self.bank = Bank()

    def _quit(self) -> NoReturn:
        self._save()
        sys.exit(0)
