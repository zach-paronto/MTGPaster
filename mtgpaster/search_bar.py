from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QLineEdit


class SearchBar(QLineEdit):
    """
    Wrapper class for the QLineEdit widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setValidator(QRegularExpressionValidator(QRegularExpression('^[a-zA-Z_ ]+$')))
