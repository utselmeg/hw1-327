import calendar
from datetime import date

class OverdrawError(Exception):
    """Exception raised for overdraw errors."""

    DEFAULT_MESSAGE = "This transaction could not be completed due to an insufficient account balance."

    def __init__(self, message:str=None):
        if message is None:
            message = self.DEFAULT_MESSAGE
        super().__init__(message)

class TransactionSequenceError(Exception):
    """Exception raised for transaction sequence errors
    and duplicate interest application errors."""

    def __init__(self, latest_date: date, error_type:str="sequence"):
        """
        :param latest_date: The date related to the error (e.g., last transaction date).
        :param error_type: "sequence" for transaction order errors, "interest" for duplicate interest application.
        """
        self.latest_date: date = latest_date
        self.error_type: str = error_type

    def __str__(self):
        if self.error_type == "interest":
            month_name = calendar.month_name[self.latest_date.month]
            return f"Cannot apply interest and fees again in the month of {month_name}."
        else:
            return f"New transactions must be from {self.latest_date} onward."

class TransactionLimitError(Exception):
    """Exception raised for transaction limit errors."""

    def __init__(self, limit_type: str):
        self.limit_type = limit_type

    def __str__(self):
        if self.limit_type == "monthly":
            return f"This transaction could not be completed because this account already has 5 transactions in this month."
        else:
            return f"This transaction could not be completed because this account already has 2 transactions in this day."
