import sys
import logging
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
    menu = BankMenu()
    try:
        main(menu)
    except Exception as e:
        error_message = repr(e).replace("\n", "\\n")
        logging.error(f"{type(e).__name__}: {error_message}")
        # try:
        #     menu.save()
        #     # print("Bank state saved before exiting due to an error.")
        # except (IOError, ValueError) as save_error:
        #     # print(f"Failed to save bank state: {repr(save_error)}")
        #     pass
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        sys.exit(0)
