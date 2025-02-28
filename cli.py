import sys
import logging
import sqlalchemy
from Models import Base
from MenuClass import BankMenu

logging.basicConfig(
    filename="bank.log",
    level=logging.DEBUG,
    format="%(asctime)s|%(levelname)s|%(message)s",    # noqa
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main(bank_menu: BankMenu):
    """Runs the bank menu system."""
    bank_menu.run()

if __name__ == "__main__":
    engine = sqlalchemy.create_engine("sqlite:///bank.db")
    Base.metadata.create_all(engine)
    menu = BankMenu()
    try:
        main(menu)
    except Exception as e:
        error_message = repr(e).replace("\n", "\\n")
        logging.error(f"{type(e).__name__}: {error_message}")
        try:
            menu.session.commit()
            menu.session.close()
        except sqlalchemy.exc.SQLAlchemyError as save_error:
            logging.error(f"Failed to save to database: {repr(save_error)}")
            pass
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        sys.exit(0)