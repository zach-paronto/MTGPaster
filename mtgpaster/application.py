from typing import List

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout

from mtgpaster.infinite_scroll_container import InfiniteScrollContainer
from mtgpaster.search_bar import SearchBar


class Application(QApplication):
    def __init__(self):
        super().__init__([])

        self.window = QWidget()

        self.search_bar = SearchBar()
        self.infinite_scroll_container = InfiniteScrollContainer(self.search_bar)

        self._initialize_window_layout([self.search_bar, self.infinite_scroll_container])
        self.window.show()


    def _initialize_window_layout(self, widgets: List[QWidget]) -> None:
        self.window.setWindowTitle("Scryfall Searcher")
        self.window.setMinimumSize(QSize(400, 400))

        window_layout = QVBoxLayout(self.window)
        for widget in widgets:
            window_layout.addWidget(widget)
        self.window.setLayout(window_layout)