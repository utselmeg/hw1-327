import datetime
from typing import List
from decimal import Decimal
from sqlalchemy import ForeignKey, String, Integer, Numeric, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    account_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    # one-to-many rel
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_on": account_type,
        "polymorphic_identity": "account"
    }


class SavingsAccount(Account):
    __mapper_args__ = {
        "polymorphic_identity": "savings"
    }


class CheckingAccount(Account):
    __mapper_args__ = {
        "polymorphic_identity": "checking"
    }


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[int] = mapped_column(ForeignKey("accounts.account_number"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)
    # many-to-one rel
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")