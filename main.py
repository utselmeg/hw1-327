import os
import pickle
import datetime
from decimal import Decimal, ROUND_HALF_UP

from BankClass import Bank


def display_amount(amount) -> Decimal:
    """Display the current balance of the account."""
    formatted_amount: Decimal = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return formatted_amount

def bank_menu(bank_app):
    selected_account = bank_app.selected
    account_info = (f'{selected_account.name}, balance: ${display_amount(selected_account.balance):,.2f}'
                    if selected_account else "None")
    menu = (
        "--------------------------------\n"
        f"Currently selected account: {account_info}\n"
        "Enter command:\n"
        "1: open account\n"
        "2: summary\n"
        "3: select account\n"
        "4: add transaction\n"
        "5: list transactions\n"
        "6: interest and fees\n"
        "7: quit\n> "
    )
    try:
        val = int(input(menu))
        return val
    except ValueError:
        return 0

def main():
    if os.path.exists('bank.pickle'):
        with open('bank.pickle', 'rb') as file:
            bank_app = pickle.load(file)
            bank_app.selected = None
    else:
        bank_app = Bank()
    command = 0
    while command != 7:
        command = bank_menu(bank_app)
        if command == 1:
            # open account
            account_type = (input(
                'Type of account? (checking/savings)\n')
                            .strip()
                            .capitalize())
            bank_app.open_account(account_type)
        elif command == 2:
            # summary
            bank_app.summary()
        elif command == 3:
            # select account
            account_number = int(input('Enter account number\n'))
            bank_app.select_account(account_number)
        elif command == 4:
            # add transaction
            amount = Decimal(input('Amount?\n'))
            date_input = input("Date? (YYYY-MM-DD)\n").strip()
            date = datetime.datetime.strptime(date_input, "%Y-%m-%d").date()
            bank_app.add_transaction(amount, date)
        elif command == 5:
            # list transactions
            bank_app.list_transactions()
        elif command == 6:
            #interest and fees
            bank_app.interest_and_fees()
        elif command == 7:
            # quit
            with open('bank.pickle', 'wb') as file:
                pickle.dump(bank_app, file) # type: ignore
            print("Bank app quit.")
        else:
            pass

if __name__ == '__main__':
    main()