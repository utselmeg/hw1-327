from enum import Enum

class AccountType(Enum):
    """Enum representing account types with numerical values."""
    CHECKING = 1
    SAVINGS = 2

    @classmethod
    def from_string(cls, type_str: str):
        """Converts a string ('Checking' or 'Savings') to an AccountType enum."""
        if type_str.lower() == "checking":
            return cls.CHECKING
        elif type_str.lower() == "savings":
            return cls.SAVINGS
        raise ValueError(f"Invalid account type: {type_str}")

    def __str__(self):
        """Returns the readable string representation of the account type."""
        return "Checking" if self == AccountType.CHECKING else "Savings"
