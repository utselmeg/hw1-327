from decimal import Decimal, ROUND_HALF_UP
from AccountClass import Account

class Bank:
    num_accounts: int = 0
    def __init__(self):
        # dictionary of accounts
        self.accounts = {}
        self.selected: Account | None = None

    def open_account(self, account_type: str):
        if account_type not in ['Checking', 'Savings']:
            print('Invalid account type')
            return
        self.num_accounts += 1
        self.accounts[self.num_accounts] = Account(account_type, self.num_accounts)

    @staticmethod
    def display_amount(amount) -> Decimal:
        """Display the current balance of the account."""
        formatted_amount: Decimal = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return formatted_amount

    def summary(self):
        for account in self.accounts:
            total_balance: Decimal = Decimal(sum(Decimal(t.amount) for t in self.accounts[account].transactions))
            # formatted_balance: Decimal = total_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            print(f"{self.accounts[account].name},\t\tbalance: ${self.display_amount(total_balance):,.2f}")

    def select_account(self, account_number):
        if account_number not in self.accounts:
            return
        self.selected = self.accounts[account_number]
        print(f"Selected account: {self.selected.name}")

    def add_transaction(self, amount, date):
        if self.selected is None:
            return
        self.accounts[self.selected.account_number].add_transaction(amount, date)

    def list_transactions(self) -> None:
        if self.selected is None:
            return
        transactions = self.selected.all_transactions()
        # selected_transactions = self.accounts[self.selected.account_number].transactions
        # sorted_transactions = sorted(selected_transactions, key=lambda t: t.date)
        # for transaction in sorted_transactions:
        #     formatted_amount: Decimal = transaction.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        #     print(f"{str(transaction.date)}, ${formatted_amount:,.2f}")
        for transaction in transactions:
            formatted_amount: Decimal = transaction.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            # formatted_amount: Decimal = transaction.amount
            print(f"{str(transaction.date)}, ${formatted_amount:,.2f}")

    def interest_and_fees(self) -> None:
        """When invoked, apply interests and fees to the selected account."""
        if self.selected is None:
            return
        self.accounts[self.selected.account_number].interest_and_fees()