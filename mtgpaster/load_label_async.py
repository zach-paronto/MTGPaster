import requests
from PyQt6.QtCore import QRunnable, pyqtSlot
from PyQt6.QtGui import QPixmap

from mtgpaster.image_text_label import ImageTextLabel


class LoadLabelAsync(QRunnable):
    def __init__(self, cell_widget, image_info):
        super().__init__()
        self.cell_widget = cell_widget
        self.image_info = image_info


    @pyqtSlot()
    def run(self):
        if 'error' not in self.image_info:
            image_response = requests.get(self.image_info['normal'])

            image_response.raise_for_status()

            pixmap = QPixmap()
            pixmap.loadFromData(image_response.content)  # perform error checks here

            self.cell_widget.text_content = self.image_info["normal"]

            self.cell_widget.setPixmap(pixmap)

        else:
            self.cell_widget = ImageTextLabel(self.image_info["error"])