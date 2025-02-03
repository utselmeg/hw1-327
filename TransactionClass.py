from decimal import Decimal
import datetime

class Transaction:
    class TransactionType:
        DEPOSIT = 1
        WITHDRAWAL = 2
        FEE = 3
        OTHER = 4

    def __init__(self, account_number, date, amount):
        self.account_number = account_number
        self.date: datetime.date = date
        self.amount: Decimal = amount

    # def __str__(self):
    #     return f"{self._id}: \nmemo: {self._memo}\ntags: {self._tags}"
    #
    # def __lt__(self, other: Note) -> bool:
    #     return self._id < other._id
    #
    # def __ge__(self, other) -> bool:
    #     return not self.__lt__(other)
    #
    # def __gt__(self, other) -> bool:
    #     return other.__lt__(self)
    #
    # def __le__(self, other) -> bool:
    #     return not self.__gt__(other)
    #
    # def __eq__(self, other) -> bool:
    #     return not self.__lt__(other) and not self.__gt__(other)
    #
    # def __ne__(self, other) -> bool:
    #     return not self.__eq__(other)