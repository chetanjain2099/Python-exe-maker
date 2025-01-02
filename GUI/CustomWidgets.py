import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QFrame, QGridLayout, QProgressBar


class DropArea(QLabel):
    """Drag and drop area, allowing users to drag in .py files"""
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("Drag in .py file")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            """QLabel {border: 2px dashed #aaa; min-height: 80px; font-size: 13px; color: #555; padding: 10px;}
            QLabel:hover {border-color: #777;}
            """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.toLocalFile().endswith('.py') for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile().endswith(".py")]
        if paths:
            for path in paths:
                self.file_dropped.emit(path)
        else:
            QMessageBox.warning(self, "Warning", "Please drag and drop the Python file (.py) into the window.",
                                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)


class TaskWidget(QFrame):
    """Create a task display widget"""

    def __init__(self, script_path):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QGridLayout(self)
        self.script_label = QLabel(os.path.basename(script_path))
        self.script_label.setFixedWidth(200)
        layout.addWidget(self.script_label, 0, 0)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(200)
        layout.addWidget(self.progress, 0, 1)

        self.status = QLabel("Waiting...")
        layout.addWidget(self.status, 0, 2)

        self.path = QLabel("")
        self.path.setWordWrap(True)
        self.path.hide()
        layout.addWidget(self.path, 1, 0, 1, 3)
