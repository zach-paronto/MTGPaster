from typing import List

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

from mtgpaster.infinite_scroll_container import InfiniteScrollContainer
from mtgpaster.search_bar import SearchBar


class Application(QApplication):
    """
    Main application class - contains all other widgets within the program.
    """

    def __init__(self):
        super().__init__([])

        self.window = QWidget()

        self.search_bar = SearchBar()
        self.infinite_scroll_container = InfiniteScrollContainer(self.search_bar)
        self.error_label = QLabel()
        self.error_label.setVisible(False)

        self._initialize_window_layout([self.search_bar, self.infinite_scroll_container])
        self.window.show()


    def _initialize_window_layout(self, widgets: List[QWidget]) -> None:
        self.window.setWindowTitle("Scryfall Searcher")
        self.window.setMinimumSize(QSize(400, 400))

        window_layout = QVBoxLayout(self.window)
        for widget in widgets:
            window_layout.addWidget(widget)
        self.window.setLayout(window_layout)


    def display_error_message(self, message: str) -> None:
        """
        Displays an error message within the main window. Note that this error message does replace the
        infinite scroll container.

        :param message: The message string to display.
        :return: None
        """
        self.infinite_scroll_container.setVisible(False)
        self.error_label.setText(message)
        self.error_label.setVisible(True)

