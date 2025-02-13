import sys
import logging
from MenuClass import BankMenu

logging.basicConfig(
    filename="bank.log",
    level=logging.DEBUG,
    format="%(asctime)s|%(levelname)s|%(message)s",    # noqa
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    """Runs the bank menu system."""
    menu = BankMenu()
    menu.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_message = repr(e).replace("\n", "\\n")
        logging.error(f"{type(e).__name__}: {error_message}")
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        sys.exit(1)
