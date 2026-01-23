from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QLabel


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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        # Center the image within the label's available space
        x = (size.width() - scaled_pixmap.width()) // 2
        y = (size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
