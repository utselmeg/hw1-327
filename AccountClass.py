import calendar
from decimal import Decimal, ROUND_HALF_UP
from TransactionClass import Transaction

class Account:
    class AccountType:
        CHECKING = 1
        SAVINGS = 2

    class InterestRateMonthly:
        CHECKING = Decimal(0.08)
        SAVINGS = Decimal(0.33)

    def __init__(self, account_type, number):
        """Initialize a new account with a $0.00 starting balance."""
        name = account_type + "#" + str(number).zfill(9)
        # Checking or Savings
        self.account_type: str = account_type   # self.account_type = AccountType.account_type
        self.account_number: int = number
        self.name: str = name
        self.balance: Decimal = Decimal(0)
        self.transactions: list[Transaction] = []
        print(
            f"Account {name} created with starting balance of {self.balance}")

    def check_transaction(self, date) -> bool:
        """Check if a savings account has less than two transactions
        in a day and less than five transactions in a month."""
        day_count = 0
        month_count = 0
        # day_set = set()
        for transaction in self.transactions:
            print(transaction.date, date)
            print(day_count, month_count)
            if transaction.date == date:
                day_count += 1
                if day_count >= 2:
                    return False
            if transaction.date.month == date.month and transaction.date.year == date.year:
                month_count += 1
                if month_count >= 5:
                    return False
        return True

    def update_balance(self):
        """Update the account balance based on the transactions."""
        self.balance: Decimal = Decimal(sum(Decimal(t.amount) for t in self.transactions))
        # self.balance: Decimal = total_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        print(f"Balance updated to {self.balance}")

    def sort_transactions(self):
        """Sort the transactions in the account."""
        self.transactions = sorted(self.transactions, key=lambda transaction: transaction.date)

    def add_transaction(self, amount, date):
        """Add a transaction to the currently selected account."""
        # trying to withdraw too much from an account
        if self.balance + amount < 0:
            print("Insufficient funds")
            return
        if self.account_type == "Savings" and self.check_transaction(date) == False:
            print("Transaction not allowed")
            return

        self.transactions.append(Transaction(self.account_number, date, amount))
        # self.transactions.sort(key=lambda x: x.date)
        self.transactions = sorted(self.transactions, key=lambda transaction: transaction.date)
        self.update_balance()
        print(f"Transaction of {amount} added to {self.name} on {date}")

    def all_transactions(self):
        sorted_transactions = sorted(self.transactions, key=lambda t: t.date)
        return sorted_transactions

    def interest_and_fees(self):
        """When invoked, apply interests and fees to the account."""
        if self.account_type == "Savings":
            interest_rate = Account.InterestRateMonthly.SAVINGS
        else:
            interest_rate = Account.InterestRateMonthly.CHECKING
        interest = (self.balance * interest_rate) / Decimal(100)
        print(f"Interest on {self.name} is {interest}")

        last_transaction_date = self.transactions[-1].date
        last_transaction_month = last_transaction_date.month
        last_day_of_month = calendar.monthrange(last_transaction_date.year, last_transaction_month)[1]
        print(f"Last transaction date is {last_transaction_date}")
        print(f"Last day of month is {last_day_of_month}")
        fee_date = last_transaction_date.replace(day=last_day_of_month)

        interest_transaction = Transaction(self.account_number, fee_date , interest)
        self.transactions.append(interest_transaction)

        if self.account_type == "Checking":
            if self.balance < 100:
                low_balance_fee_transaction = Transaction(self.account_number, fee_date, Decimal(-5.75))
                self.transactions.append(low_balance_fee_transaction)
                print("Account is low on funds")

        self.transactions = sorted(self.transactions, key=lambda transaction: transaction.date)
        self.update_balance()

        print(f"Interest and fees added to {self.name} on {fee_date}")
