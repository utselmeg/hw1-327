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


class ValidatedEntry(ttk.Frame):
    """A megawidget to combines entry with validation and warning label."""

    def __init__(self, parent, label_text, validate_func, warning_text="", **kwargs):
        """Initialize the validated entry.

        Args:
            parent: parent widget
            label_text: text for label
            validate_func: func to validate entry input
            warning_text: default warning text
            **kwargs: additional keyword arguments for entry widget
        """
        super().__init__(parent)

        # label for entry
        self.label = ttk.Label(self, text=label_text)
        self.label.pack(side=tk.LEFT, padx=5)
        self.var = StringVar()

        # entry
        self.entry = ttk.Entry(self, textvariable=self.var, **kwargs)
        self.entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        vcmd = (self.entry.register(validate_func), '%P')
        self.entry.config(validate="key", validatecommand=vcmd)

        # warning label
        self.warning = ttk.Label(self, text=warning_text, foreground="red")
        self.warning.pack(side=tk.LEFT, padx=5)

        self.entry.bind("<Button-1>", self._on_entry_click)

    @staticmethod
    def _on_entry_click(event):
        """Force focus and select all text when entry is clicked."""
        event.widget.focus_set()
        event.widget.selection_range(0, tk.END)
        return "break"

    def get(self):
        """Get the current value of the entry."""
        return self.var.get()

    def set(self, value):
        """Set the value of the entry."""
        self.var.set(value)

    def set_warning(self, text):
        """Set the warning text."""
        self.warning.config(text=text)


class DateEntry(ttk.Frame):
    """A megawidget for entering dates (YYYY-MM-DD format)."""

    def __init__(self, parent):
        super().__init__(parent)

        # label for entry
        self.label = ttk.Label(self, text="Date (YYYY-MM-DD):")
        self.label.pack(side=tk.LEFT, padx=5)
        self.date_var = StringVar()
        self.date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))  # Default to today

        # entry
        self.entry = ttk.Entry(self, textvariable=self.date_var, width=15)
        self.entry.pack(side=tk.LEFT, padx=5)
        vcmd = (self.entry.register(self._validate_date_input), '%P')
        self.entry.config(validate="key", validatecommand=vcmd)
        self.entry.bind("<Button-1>", self._on_entry_click)
        self.reminder = ttk.Label(self, text="Format: YYYY-MM-DD", foreground="gray")
        self.reminder.pack(side=tk.LEFT, padx=5)

    @staticmethod
    def _validate_date_input(p):
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

    @staticmethod
    def _on_entry_click(event):
        """Force focus and select all text when entry is clicked."""
        event.widget.focus_set()
        event.widget.selection_range(0, tk.END)
        return "break"

    def get(self):
        """Get the current date value."""
        return self.date_var.get()

    def set(self, value):
        """Set the date value."""
        self.date_var.set(value)

    def is_valid_date(self, date_str=None):
        """Check if a date string is in valid YYYY-MM-DD format and represents a real date."""
        if date_str is None:
            date_str = self.get()
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
            if year < 1900 or year > 2100:
                return False
            if month < 1 or month > 12:
                return False
            days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                days_in_month[2] = 29
            if day < 1 or day > days_in_month[month]:
                return False
            datetime.datetime(year, month, day)
            return True
        except ValueError:
            return False

    def get_date_object(self):
        """Convert the date string to a datetime.date object."""
        date_str = self.get()
        if len(date_str) == 8 and date_str.isdigit():
            date_str = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            self.set(date_str)
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None


class AccountsFrame(ttk.LabelFrame):
    """A megawidget for displaying and managing accounts."""

    def __init__(self, parent, bank, on_account_selected):
        """Initialize the accounts frame.
        Args:
            parent: parent widget
            bank: Bank instance
            on_account_selected: callback function when an account is selected
        """
        super().__init__(parent, text="Accounts")
        self.bank = bank
        self.on_account_selected_callback = on_account_selected
        self.accounts_tree = ttk.Treeview(self, columns=("number", "type", "balance"), show="headings")
        self.accounts_tree.heading("number", text="Account Number")
        self.accounts_tree.heading("type", text="Type")
        self.accounts_tree.heading("balance", text="Balance")
        self.accounts_tree.column("number", width=70)
        self.accounts_tree.column("type", width=70)
        self.accounts_tree.column("balance", width=70)
        self.accounts_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.accounts_tree.bind("<<TreeviewSelect>>", self._on_account_selected)
        self._create_account_controls()

    def _create_account_controls(self):
        """Create controls for adding new accounts."""
        add_account_frame = ttk.Frame(self)
        add_account_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(add_account_frame, text="Account Type:").pack(side=tk.LEFT, padx=5)
        self.account_type_var = StringVar()
        account_type_combo = ttk.Combobox(add_account_frame, textvariable=self.account_type_var)
        account_type_combo['values'] = ('Checking', 'Savings')
        account_type_combo.current(0)
        account_type_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(add_account_frame, text="Open Account", command=self._open_account).pack(side=tk.LEFT, padx=5)

    def _on_account_selected(self, _):
        """Handle account selection in treeview."""
        selection = self.accounts_tree.selection()
        if selection:
            account_num = int(selection[0])
            try:
                self.bank.select_account(account_num)
                self.on_account_selected_callback()
            except AttributeError as e:
                messagebox.showwarning("Error selecting", str(e))

    def _open_account(self):
        """Open a new account."""
        account_type = self.account_type_var.get()
        try:
            self.bank.open_account(account_type)
            self.bank.commit()
            self.update_accounts_list()
            messagebox.showinfo("Success", f"New {account_type} account created successfully.")
        except ValueError as e:
            messagebox.showwarning("Error", str(e))

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


class TransactionsFrame(ttk.LabelFrame):
    """A megawidget for displaying transactions."""

    def __init__(self, parent, bank):
        """Initialize the transactions frame.

        Args:
            parent: parent widget
            bank: Bank instance
        """
        super().__init__(parent, text="Transactions")
        self.bank = bank
        self.transactions_tree = ttk.Treeview(self, columns=("date", "amount"), show="headings")
        self.transactions_tree.heading("date", text="Date")
        self.transactions_tree.heading("amount", text="Amount")
        self.transactions_tree.column("date", width=150)
        self.transactions_tree.column("amount", width=150)
        self.transactions_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.transactions_tree.tag_configure("positive", foreground="green")
        self.transactions_tree.tag_configure("negative", foreground="red")

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


class ActionsFrame(ttk.LabelFrame):
    """A megawidget for transaction actions."""

    def __init__(self, parent, bank, on_action_complete):
        """Initialize the actions frame.

        Args:
            parent: parent widget
            bank: Bank instance
            on_action_complete: callback function to run after an action is completed
        """
        super().__init__(parent, text="Actions")
        self.bank = bank
        self.on_action_complete = on_action_complete
        self.amount_entry = ValidatedEntry(
            self,
            "Amount:",
            self._validate_amount,
            warning_text=""
        )
        self.amount_entry.pack(fill=tk.X, padx=5, pady=5)
        self.date_entry = DateEntry(self)
        self.date_entry.pack(fill=tk.X, padx=5, pady=5)
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_transaction_btn = ttk.Button(
            buttons_frame,
            text="Add Transaction",
            command=self._add_transaction
        )
        self.add_transaction_btn.pack(side=tk.LEFT, padx=5)
        self.add_transaction_btn.config(state=tk.DISABLED)  # disabled until account is selected
        self.interest_fees_btn = ttk.Button(
            buttons_frame,
            text="Apply Interest & Fees",
            command=self._apply_interest_fees
        )
        self.interest_fees_btn.pack(side=tk.LEFT, padx=5)
        self.interest_fees_btn.config(state=tk.DISABLED)  # disabled until account is selected

    def _validate_amount(self, value):
        """Validate the amount input."""
        if value == "" or value == "-":
            self.amount_entry.set_warning("")
            return True

        try:
            Decimal(value)
            self.amount_entry.set_warning("")
            return True
        except InvalidOperation:
            self.amount_entry.set_warning("Invalid amount")
            return True

    def _add_transaction(self):
        """Add a transaction to the selected account."""
        selected_account = self.bank.get_selected_account()
        if not selected_account:
            messagebox.showwarning("Error", "No account selected.")
            return

        try:
            amount_str = self.amount_entry.get()
            try:
                amount = Decimal(amount_str)
            except InvalidOperation:
                messagebox.showwarning("Input Error", "Please enter a valid amount.")
                return
            transaction_date = self.date_entry.get_date_object()
            if not transaction_date:
                messagebox.showwarning("Input Error", "Please enter a valid date in YYYY-MM-DD format.")
                return
            self.bank.add_transaction(amount, transaction_date)
            self.bank.commit()
            self.amount_entry.set("")
            self.on_action_complete()
            messagebox.showinfo("Success", "Transaction added successfully.")
        except (OverdrawError, TransactionSequenceError, TransactionLimitError) as e:
            messagebox.showwarning("Transaction Error", str(e))

    def _apply_interest_fees(self):
        """Apply interest and fees to the selected account."""
        selected_account = self.bank.get_selected_account()
        if not selected_account:
            messagebox.showwarning("Error", "No account selected.")
            return

        try:
            self.bank.interest_and_fees()
            self.bank.commit()
            self.on_action_complete()
            messagebox.showinfo("Success", "Interest and fees applied successfully.")
        except (ValueError, TypeError, AttributeError, TransactionSequenceError) as e:
            messagebox.showwarning("Error", str(e))

    def enable_buttons(self):
        """Enable the action buttons."""
        self.add_transaction_btn.config(state=tk.NORMAL)
        self.interest_fees_btn.config(state=tk.NORMAL)

    def disable_buttons(self):
        """Disable the action buttons."""
        self.add_transaction_btn.config(state=tk.DISABLED)
        self.interest_fees_btn.config(state=tk.DISABLED)


class BankApp:
    """GUI application for the Bank system."""

    def __init__(self, root):
        """Initialize the GUI application."""
        self._window = root
        self._window.title("Bank")
        self._window.geometry("800x600")
        self._window.report_callback_exception = self.handle_exception
        self.engine = sqlalchemy.create_engine("sqlite:///bank.db")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.bank = Bank(self.session)
        self._create_layout()
        self.accounts_frame.update_accounts_list()

    def _create_layout(self):
        """Create the main layout with megawidgets."""
        # left panel for accounts
        self.accounts_frame = AccountsFrame(
            self._window,
            self.bank,
            self._on_account_selected
        )
        self.accounts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # right panel
        right_panel = ttk.Frame(self._window)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # transactions frame
        self.transactions_frame = TransactionsFrame(right_panel, self.bank)
        self.transactions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # actions frame
        self.actions_frame = ActionsFrame(
            right_panel,
            self.bank,
            self._on_action_complete
        )
        self.actions_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

    def _on_account_selected(self):
        """Handle when an account is selected."""
        self.actions_frame.enable_buttons()
        self.transactions_frame.update_transactions_list()

    def _on_action_complete(self):
        """Handle when an action is completed."""
        self.accounts_frame.update_accounts_list()
        self.transactions_frame.update_transactions_list()

    @staticmethod
    def handle_exception(exception, value, _):
        """Handle uncaught exceptions."""
        error_message = repr(value).replace("\n", "\\n")
        logging.error(f"{exception.__name__}: {error_message}")

        messagebox.showerror(
            "Unexpected Error",
            "Sorry! Something unexpected happened. Check the logs or contact the developer for assistance."
        )
        sys.exit(0)


def main():
    """Run GUI."""
    root = tk.Tk()
    BankApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
