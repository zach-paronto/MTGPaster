from PyQt6.QtWidgets import QLineEdit


class SearchBar(QLineEdit):
    """
    Wrapper class for the QLineEdit widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
