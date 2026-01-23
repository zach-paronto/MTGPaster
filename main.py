import sys

from mtgpaster.application import Application
from mtgpaster.data.database_client import DatabaseClient

if __name__ == "__main__":
    DatabaseClient.initialize()

    app = Application()
    sys.exit(app.exec())