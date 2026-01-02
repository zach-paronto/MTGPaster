from PyQt6 import QtCore
from PyQt6.QtCore import QRunnable, QThreadPool, QSize, Qt, pyqtSlot
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QTableWidget, QLabel, QAbstractItemView
from pyperclip import copy
import sys
import requests

#https://www.pythonguis.com/tutorials/pyqt6-signals-slots-events/
#https://www.riverbankcomputing.com/static/Docs/PyQt6/

SCRYFALL_URL = "https://api.scryfall.com/cards/search"

class ImageTextLabel(QLabel):
    def __init__(self, text=None):
        super().__init__()
        self.text_content = text


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
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode(1))
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)

        self.cellActivated.connect(self.copy_cell)

        self.threadpool = QThreadPool()
        
        self.search_box = search_box
        self.cards_remaining = 0
        self.next_page = None
        self.image_pool = []

        self.insertColumn(0)
        self.insertColumn(0)

        self.setColumnWidth(0, 175)
        self.setColumnWidth(1, 175)

        self.verticalScrollBar().valueChanged.connect(self.value_changed)

        self.show()
    
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

            for i in range(2):
                if self.image_pool.__len__() == 0 and self.next_page is not None:
                    self.get_next_page()
                if self.image_pool.__len__() == 0:
                    break

                cell_widget = ImageTextLabel()
                cell_widget.setFixedSize(QSize(175,250))
                cell_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.setCellWidget(curRows + r, i, cell_widget)

                image_info = self.image_pool.pop()
                self.threadpool.start(LoadLabelAsync(cell_widget, image_info))



    def get_next_page(self):
        response = requests.get(url=self.next_page)
        response.raise_for_status()

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

    def makeRequest(self):
        print("Resetting info...")
        self.setRowCount(0)
        self.cards_remaining = 0
        self.next_page = None
        self.image_pool = []

        text = search_bar.text()
        # with open("./response.json", "w") as json_file:
        response = requests.get(url=SCRYFALL_URL, params={"q":text})
        response.raise_for_status()

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
    window.setFixedSize(QSize(400,400))
    window.setAttribute(Qt.WidgetAttribute(120))

    search_bar = QLineEdit()
    infinite_scroll = InfiniteCardScroll(search_bar)

    search_bar.editingFinished.connect(infinite_scroll.makeRequest)
    
    window_layout = QVBoxLayout(window)
    window_layout.addWidget(search_bar)
    window_layout.addWidget(infinite_scroll)
    window.setLayout(window_layout)

    window.show()

    sys.exit(app.exec())
