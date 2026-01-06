from PyQt6 import QtCore
from PyQt6.QtCore import QRunnable, QThreadPool, QSize, Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QTableWidget, QLabel, QAbstractItemView, QMessageBox, QHeaderView
from pyperclip import copy
import sys
import requests

#https://www.pythonguis.com/tutorials/pyqt6-signals-slots-events/
#https://www.riverbankcomputing.com/static/Docs/PyQt6/

SCRYFALL_URL = "https://api.scryfall.com/cards/search"

class ImageTextLabel(QLabel):
    def __init__(self, text=None):
        super().__init__()
        self.setScaledContents(True)
        self.text_content = text

    def paintEvent(self, event):
        if not self.pixmap():
            return

        size = self.size()
        scaled_pixmap = self.pixmap().scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation # Provides better image quality
        )

        painter = QPainter(self)
        # Center the image within the label's available space
        x = (size.width() - scaled_pixmap.width()) // 2
        y = (size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)


class LoadLabelAsync(QRunnable):
    def __init__(self, cell_widget, image_info):
        super().__init__()
        self.cell_widget = cell_widget
        self.image_info = image_info

    @pyqtSlot()
    def run(self):
        if 'error' not in self.image_info:
            image_response = requests.get(self.image_info['small'])
        
            image_response.raise_for_status()

            pixmap = QPixmap()
            pixmap.loadFromData(image_response.content) #perform error checks here

            self.cell_widget.text_content = self.image_info["normal"]

            self.cell_widget.setPixmap(pixmap)

        else:
            self.cell_widget = ImageTextLabel(self.image_info["error"])



class InfiniteCardScroll(QTableWidget):
    def __init__(self, search_box):
        super().__init__()

        self.cellActivated.connect(self.copy_cell)

        self.threadpool = QThreadPool()
        
        self.search_box = search_box
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

        self.show()

    #TODO: pick back up here. Set this up to redraw rows/cols when window is resized
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
        print(f"Attempting to copy {(row,col)}")
        widget = self.cellWidget(row, col)
        if widget is None: 
            print("No widget found")
            return
        print(f"Copying: {widget.text_content}")
        copy(widget.text_content)
        
    def value_changed(self, value):
        if self.image_pool.__len__() == 0 and self.next_page is None:
            return
        if value == self.verticalScrollBar().maximum(): #if we're at the end
            self.add_lines(8)

    def add_lines(self, n):
        curRows = self.rowCount()
        for r in range(n):
            self.insertRow(curRows+r)
            self.setRowHeight(curRows + r, 250)
            # self.resizeRowsToContents()

            for i in range(2):
                if self.image_pool.__len__() == 0 and self.next_page is not None:
                    self.get_next_page()
                if self.image_pool.__len__() == 0:
                    break

                cell_widget = ImageTextLabel()
                # cell_widget.setFixedSize(QSize(175,250))
                cell_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
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

        for card in data['data']:
            if 'image_uris' in card:
                self.image_pool.append({"small":card['image_uris']['small'],"normal":card['image_uris']['normal']})
            else:
                try:
                    self.image_pool.append({"small":card['image_uris']['small'],"normal":card['image_uris']['normal']})
                except Exception as e:
                    print(e)
                    self.image_pool.append({"error":"Failed to find image source"})

    def show_error(self, message):
        QMessageBox.information(self, "Search Error", message)

    def makeRequest(self):
        self.setRowCount(0)
        self.cards_remaining = 0
        self.next_page = None
        self.image_pool = []

        text = search_bar.text()
        # with open("./response.json", "w") as json_file:
        response = requests.get(url=SCRYFALL_URL, params={"q":text})
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code == 404:
                self.show_error("No cards matched the criteria.")
            else:
                self.show_error("A network error occured. Please check your network access and try again.")
            return

        data = response.json()

            # json.dump(data, json_file, indent=4)

        for card in data['data']:
            if 'image_uris' in card:
                self.image_pool.append({"small":card['image_uris']['small'],"normal":card['image_uris']['normal']})
            else:
                try:
                    #TODO: place a flip button within the cell OR paste copy both urls to the clipboard, new line separated (?)
                    self.image_pool.append({"small":card['card_faces'][0]['image_uris']['small'],"normal":card['card_faces'][0]['image_uris']['normal']})
                except Exception as e:
                    print(f"{card['name']} had exception: {e}")
                    self.image_pool.append({"error":"Failed to find image source"})
        
        self.add_lines(5)
    

if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    window.setWindowTitle("Scryfall Searcher")
    window.setMinimumSize(QSize(400,400))

    search_bar = QLineEdit()
    infinite_scroll = InfiniteCardScroll(search_bar)
    search_bar.editingFinished.connect(infinite_scroll.makeRequest)
    
    window_layout = QVBoxLayout(window)
    window_layout.addWidget(search_bar)
    window_layout.addWidget(infinite_scroll)
    window.setLayout(window_layout)

    window.show()

    sys.exit(app.exec())
