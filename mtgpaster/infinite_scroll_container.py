from copy import copy

import requests
from PyQt6.QtCore import QThreadPool, pyqtSlot
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QMessageBox
from PyQt6.uic.properties import QtCore

from mtgpaster import utils
from mtgpaster.load_label_async import LoadLabelAsync
from mtgpaster.search_bar import SearchBar
from mtgpaster.image_text_label import ImageTextLabel


class InfiniteScrollContainer(QTableWidget):
    def __init__(self, search_bar: SearchBar):
        super().__init__()

        self.cellActivated.connect(self.copy_cell)

        self.threadpool = QThreadPool()

        self.search_bar = search_bar
        self.cards_remaining = 0
        self.next_page = None
        self.image_pool = []

        self.insertColumn(0)
        self.insertColumn(0)

        self.hor_header = self.horizontalHeader()
        self.hor_header.setVisible(False)
        self.hor_header.setSectionResizeMode(0, QHeaderView.ResizeMode(1))
        self.hor_header.setSectionResizeMode(1, QHeaderView.ResizeMode(1))

        self.vert_header = self.verticalHeader()
        self.vert_header.setVisible(False)
        # self.vert_header.setFixedHeight(300)

        self.setVerticalScrollMode(QAbstractItemView.ScrollMode(1))
        self.verticalScrollBar().valueChanged.connect(self.value_changed)

        self.search_bar.editingFinished.connect(self.on_search_bar_editing_finished)

        self.show()


    # TODO: pick back up here. Set this up to redraw rows/cols when window is resized
    @pyqtSlot()
    def resizeEvent(self, event):
        """
        Overrides the standard QWidget.resizeEvent handler.
        """
        new_height = event.size().height()
        # old_size = event.oldSize()
        # print(f"Widget resized. New size: {new_size.width()}x{new_size.height()}. Old size: {old_size.width()}x{old_size.height()}")

        for i in range(0, self.rowCount()):
            self.setRowHeight(i, new_height // 10 * 8)
        # Call the base class implementation to ensure proper handling
        super().resizeEvent(event)

    def copy_cell(self, row, col):
        print(f"Attempting to copy {(row, col)}")
        widget = self.cellWidget(row, col)
        if widget is None:
            print("No widget found")
            return
        print(f"Copying: {widget.text_content}")
        copy(widget.text_content)


    def value_changed(self, value):
        if self.image_pool.__len__() == 0 and self.next_page is None:
            return
        if value == self.verticalScrollBar().maximum():  # if we're at the end
            self.add_lines(8)


    def add_lines(self, n):
        curRows = self.rowCount()
        for r in range(n):
            self.insertRow(curRows + r)
            self.setRowHeight(curRows + r, 250)

            for i in range(2):
                if self.image_pool.__len__() == 0 and self.next_page is not None:
                    self.get_next_page()
                if self.image_pool.__len__() == 0:
                    break

                cell_widget = ImageTextLabel()
                # cell_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setCellWidget(curRows + r, i, cell_widget)

                image_info = self.image_pool.pop()
                self.threadpool.start(LoadLabelAsync(cell_widget, image_info))


    def get_next_page(self):
        response = requests.get(url=self.next_page)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.show_error("A network error occured. Please check your network access and try again.")
            self.next_page = None
            return

        data = response.json()
        if 'next_page' in data:
            self.next_page = data['next_page']
        else:
            self.next_page = None

        ## TODO: make this the parse_data function, make sure it works first.
        for card in data['data']:
            if 'image_uris' in card:
                self.image_pool.append({"small": card['image_uris']['small'], "normal": card['image_uris']['normal']})
            else:
                try:
                    self.image_pool.append(
                        {"small": card['image_uris']['small'], "normal": card['image_uris']['normal']})
                except Exception as e:
                    print(e)
                    self.image_pool.append({"error": "Failed to find image source"})


    def show_error(self, message):
        QMessageBox.information(self, "Search Error", message)

        self.add_lines(5)


    def on_search_bar_editing_finished(self):
        self.setRowCount(0)
        self.cards_remaining = 0
        self.next_page = None
        self.image_pool = []

        self.parse_data(utils.make_request(self.search_bar.text()))

        self.add_lines(5)


    def parse_data(self, data: dict) -> None:
        if not data['data']:
            return

        for card in data['data']:
            if 'image_uris' in card:
                self.image_pool.append({"small": card['image_uris']['small'], "normal": card['image_uris']['normal']})
            else:
                try:
                    # TODO: place a flip button within the cell OR paste copy both urls to the clipboard, new line separated (?)
                    self.image_pool.append({"small": card['card_faces'][0]['image_uris']['small'],
                                            "normal": card['card_faces'][0]['image_uris']['normal']})
                except Exception as e:
                    print(f"{card['name']} had exception: {e}")
                    self.image_pool.append({"error": "Failed to find image source"})