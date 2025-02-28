import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import datetime
from decimal import Decimal, InvalidOperation
import sqlalchemy
from sqlalchemy.orm import Session

from Models import Base
from BankClass import Bank
from CustomException import OverdrawError, TransactionSequenceError, TransactionLimitError

logging.basicConfig(
    filename="bank.log",
    level=logging.DEBUG,
    format="%(asctime)s|%(levelname)s|%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


class BankApp:
    """GUI application for the Bank system."""

    def __init__(self, root):
        self._window = root
        self._window.title("Bank")
        self._window.geometry("800x600")
        self._window.report_callback_exception = self.handle_exception

        # db setup
        self.engine = sqlalchemy.create_engine("sqlite:///bank.db")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

        self.bank = Bank(self.session)
        self.accounts_frame = None
        self.right_panel = None
        self.transactions_frame = None
        self.actions_frame = None
        self.accounts_tree = None
        self.transactions_tree = None
        self.account_type_var = None
        self.amount_var = None
        self.amount_entry = None
        self.amount_warning = None
        self.date_var = None
        self.date_entry = None
        self.date_button = None
        self.add_transaction_btn = None
        self.interest_fees_btn = None

        self.create_main_frames()
        self.create_accounts_frame()
        self.create_transactions_frame()
        self.create_actions_frame()
        self.update_accounts_list()

    def create_main_frames(self):
        """Create the main layout frames."""
        # left panel for accounts
        self.accounts_frame = ttk.LabelFrame(self._window, text="Accounts")
        self.accounts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # right panel for transactions + actions
        self.right_panel = ttk.Frame(self._window)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # top right for transactions
        self.transactions_frame = ttk.LabelFrame(self.right_panel, text="Transactions")
        self.transactions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # bottom right for actions
        self.actions_frame = ttk.LabelFrame(self.right_panel, text="Actions")
        self.actions_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

    def create_accounts_frame(self):
        """Create and populate the accounts frame."""
        self.accounts_tree = ttk.Treeview(self.accounts_frame, columns=("number", "type", "balance"), show="headings")
        self.accounts_tree.heading("number", text="Account Number")
        self.accounts_tree.heading("type", text="Type")
        self.accounts_tree.heading("balance", text="Balance")
        self.accounts_tree.column("number", width=70)
        self.accounts_tree.column("type", width=70)
        self.accounts_tree.column("balance", width=70)
        self.accounts_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.accounts_tree.bind("<<TreeviewSelect>>", self.on_account_selected)

        add_account_frame = ttk.Frame(self.accounts_frame)
        add_account_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(add_account_frame, text="Account Type:").pack(side=tk.LEFT, padx=5)

        self.account_type_var = StringVar()
        account_type_combo = ttk.Combobox(add_account_frame, textvariable=self.account_type_var)
        account_type_combo['values'] = ('Checking', 'Savings')
        account_type_combo.current(0)
        account_type_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(add_account_frame, text="Open Account", command=self.open_account).pack(side=tk.LEFT, padx=5)

    def create_transactions_frame(self):
        """Create and populate the transactions frame."""
        self.transactions_tree = ttk.Treeview(self.transactions_frame, columns=("date", "amount"), show="headings")
        self.transactions_tree.heading("date", text="Date")
        self.transactions_tree.heading("amount", text="Amount")
        self.transactions_tree.column("date", width=150)
        self.transactions_tree.column("amount", width=150)
        self.transactions_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.transactions_tree.tag_configure("positive", foreground="green")
        self.transactions_tree.tag_configure("negative", foreground="red")

    def create_actions_frame(self):
        """Create and populate the actions frame."""

        def on_entry_click(event):
            """Force focus and select all text when entry is clicked."""
            event.widget.focus_set()
            event.widget.selection_range(0, tk.END)
            return "break"

        amount_frame = ttk.Frame(self.actions_frame)
        amount_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(amount_frame, text="Amount:").pack(side=tk.LEFT, padx=5)

        self.amount_var = StringVar()
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var)
        self.amount_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.amount_entry.bind("<Button-1>", on_entry_click)

        vcmd = (self.amount_entry.register(self.validate_amount), '%P')
        self.amount_entry.config(validate="key", validatecommand=vcmd)

        self.amount_warning = ttk.Label(amount_frame, text="", foreground="red")
        self.amount_warning.pack(side=tk.LEFT, padx=5)

        # date frame
        date_frame = ttk.Frame(self.actions_frame)
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(date_frame, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)

        self.date_var = tk.StringVar()
        self.date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))  # Default to today

        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)

        def validate_date_input(p):
            """Only allow digits and hyphens in the right places for YYYY-MM-DD format."""
            if len(p) == 0:
                return True

            if len(p) > 10:
                return False

            for i, char in enumerate(p):
                if i in (4, 7) and char == '-':
                    continue
                elif char.isdigit():
                    continue
                else:
                    return False

            return True

        vcmd = (self.date_entry.register(validate_date_input), '%P')
        self.date_entry.config(validate="key", validatecommand=vcmd)

        def on_entry_click(event):
            """Force focus and select all text when entry is clicked."""
            event.widget.focus_set()
            event.widget.selection_range(0, tk.END)
            return "break"

        self.date_entry.bind("<Button-1>", on_entry_click)

        ttk.Label(date_frame, text="Format: YYYY-MM-DD", foreground="gray").pack(side=tk.LEFT, padx=5)

        # transaction button
        self.add_transaction_btn = ttk.Button(self.actions_frame, text="Add Transaction",
                                              command=self.add_transaction)
        self.add_transaction_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.add_transaction_btn.config(state=tk.DISABLED)  # disabled until account is selected

        # apply interest & fees button
        self.interest_fees_btn = ttk.Button(self.actions_frame, text="Apply Interest & Fees",
                                            command=self.apply_interest_fees)
        self.interest_fees_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.interest_fees_btn.config(state=tk.DISABLED)  # disabled until account is selected

    @staticmethod
    def is_valid_date(date_str):
        """Check if a date string is in valid YYYY-MM-DD format and represents a real date."""
        if not len(date_str) == 10:
            return False

        if date_str[4] != '-' or date_str[7] != '-':
            return False

        for i, char in enumerate(date_str):
            if i != 4 and i != 7 and not char.isdigit():
                return False

        try:
            year = int(date_str[0:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])

            if year < 1900 or year > 2100: #some yr range
                return False

            if month < 1 or month > 12:
                return False

            days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

            # leap year
            if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                days_in_month[2] = 29

            if day < 1 or day > days_in_month[month]:
                return False

            datetime.datetime(year, month, day)

            return True
        except ValueError:
            return False
    def update_accounts_list(self):
        """Update the accounts treeview with current data."""
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)

        accounts_dict = self.bank.get_accounts()
        for account_num, account in accounts_dict.items():
            balance_str = self.bank.format_amount(account.balance)
            self.accounts_tree.insert("", "end", iid=str(account_num),
                                      values=(account_num, account.name.split('#')[0], balance_str))

        selected_account = self.bank.get_selected_account()
        if selected_account:
            self.accounts_tree.selection_set(str(selected_account.account_number))

    def update_transactions_list(self):
        """Update the transactions treeview with current data."""
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        selected_account = self.bank.get_selected_account()
        if not selected_account:
            return

        transactions = selected_account.list_transactions()

        for idx, transaction in enumerate(transactions):
            amount_str = self.bank.format_amount(transaction.amount)
            tag = "positive" if transaction.amount >= 0 else "negative"
            self.transactions_tree.insert("", "end", iid=str(idx),
                                          values=(transaction.date, amount_str),
                                          tags=(tag,))

    def on_account_selected(self, _):
        """Handle account selection in treeview."""
        selection = self.accounts_tree.selection()
        if selection:
            account_num = int(selection[0])

            try:
                self.bank.select_account(account_num)
                self.add_transaction_btn.config(state=tk.NORMAL)
                self.interest_fees_btn.config(state=tk.NORMAL)
                self.update_transactions_list()
            except AttributeError as e:
                messagebox.showwarning("Selection Error", str(e))

    def open_account(self):
        """Open a new account."""
        account_type = self.account_type_var.get()

        try:
            self.bank.open_account(account_type)
            self.bank.commit()
            self.update_accounts_list()
            messagebox.showinfo("Success", f"New {account_type} account created successfully.")
        except ValueError as e:
            messagebox.showwarning("Error", str(e))

    def validate_amount(self, value):
        """Validate the amount input."""
        if value == "" or value == "-":
            self.amount_warning.config(text="")
            return True

        try:
            Decimal(value)
            self.amount_warning.config(text="")
            return True
        except InvalidOperation:
            self.amount_warning.config(text="Invalid amount")
            return True

    def add_transaction(self):
        """Add a transaction to the selected account."""
        selected_account = self.bank.get_selected_account()
        if not selected_account:
            messagebox.showwarning("Error", "No account selected.")
            return

        try:
            amount_str = self.amount_var.get()
            try:
                amount = Decimal(amount_str)
            except InvalidOperation:
                messagebox.showwarning("Input Error", "Please enter a valid amount.")
                return

            date_str = self.date_var.get()
            if len(date_str) == 8 and date_str.isdigit():
                date_str = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                self.date_var.set(date_str)

            try:
                transaction_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Input Error", "Please enter a valid date in YYYY-MM-DD format.")
                return

            self.bank.add_transaction(amount, transaction_date)
            self.bank.commit()
            self.amount_var.set("")
            self.update_accounts_list()
            self.update_transactions_list()

            messagebox.showinfo("Success", "Transaction added successfully.")

        except (OverdrawError, TransactionSequenceError, TransactionLimitError) as e:
            messagebox.showwarning("Transaction Error", str(e))

    def apply_interest_fees(self):
        """Apply interest and fees to the selected account."""
        selected_account = self.bank.get_selected_account()
        if not selected_account:
            messagebox.showwarning("Error", "No account selected.")
            return

        try:
            self.bank.interest_and_fees()
            self.bank.commit()
            self.update_accounts_list()
            self.update_transactions_list()

            messagebox.showinfo("Success", "Interest and fees applied successfully.")

        except (ValueError, TypeError, AttributeError, TransactionSequenceError) as e:
            messagebox.showwarning("Error", str(e))

    @staticmethod
    def handle_exception(exception, value, _):
        """Handle uncaught exceptions."""
        error_message = repr(value).replace("\n", "\\n")
        logging.error(f"{exception.__name__}: {error_message}")

        messagebox.showerror(
            "Unexpected Error",
            "Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")

        sys.exit(0)


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    BankApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()