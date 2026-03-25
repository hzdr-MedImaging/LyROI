import pathlib

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor

from lyroi.gui.utils import set_property_and_update


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 80);")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = QtSpinner(self, radius=25, line_width=5, color=QColor.fromRgb(0, 90, 160))
        layout.addWidget(self.spinner)
        layout.addWidget(self.spinner)

        self.hide()

    def start(self):
        self.resize(self.parent().size())
        self.raise_()
        self.parent().setEnabled(False)
        self.spinner.start()
        self.show()

    def stop(self):
        self.spinner.stop()
        self.parent().setEnabled(True)
        self.hide()

    def resizeEvent(self, event):
        self.resize(self.parent().size())
        super().resizeEvent(event)


class QtSpinner(QWidget):
    def __init__(self, parent=None, radius=20, line_width=4, color = QColor(255, 255, 255)):
        super().__init__(parent)

        self._angle = 0
        self._radius = radius
        self._line_width = line_width
        self._color = color

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.rotate)
        self._timer.setInterval(16)  # ~60 FPS

        self.setFixedSize(radius * 2 + line_width,
                          radius * 2 + line_width)

    def start(self):
        self._timer.start()
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def rotate(self):
        self._angle = (self._angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self._color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        rect = self.rect().adjusted(
            self._line_width,
            self._line_width,
            -self._line_width,
            -self._line_width
        )

        # draw arc (120° segment)
        painter.drawArc(
            rect,
            int(self._angle * 16),
            int(120 * 16)
        )


class DirectoryDialog(QFileDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setFileMode(QFileDialog.Directory)
        self.setOption(QFileDialog.ShowDirsOnly, False)

    def accept(self):
        dir_path = self.selectedFiles()[0]

        files = [p for p in pathlib.Path(dir_path).iterdir() if p.is_file()]

        if len(files) > 0:
            reply = QMessageBox.question(
                self,
                "Directory Not Empty",
                "The selected directory is not empty and the files there might be overwritten.\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return  # prevent closing

        super().accept()

    @staticmethod
    def getDirectoryWithWarning(parent = None, caption = '', directory = ''):
        #self.setParent(parent)
        selector = DirectoryDialog(parent)
        if caption:
            selector.setWindowTitle(caption)
        if directory:
            selector.setDirectory(directory)
        if selector.exec():
            return selector.selectedFiles()[0]
        else:
            return ""


class FileSelector:
    def __init__(self, parent: QWidget, label: QLabel, directory: bool, output = False):
        self.label = QLabel(label)
        self.line_edit = QLineEdit()
        self.button = QPushButton("Browse")

        self.input_error = QLabel("Missing required field")
        self.input_error.setStyleSheet("color: #d32f2f; font-size: 10px")
        self.input_error.setMargin(-1)
        self.input_error.setVisible(False)
        self.input_error.setAlignment(Qt.AlignLeft)
        self.input_error.setAlignment(Qt.AlignTop)

        def browse():
            if directory:
                if output:
                    path = DirectoryDialog.getDirectoryWithWarning(parent, label)
                else:
                    path = QFileDialog.getExistingDirectory(parent, label, options = QFileDialog.DontResolveSymlinks)
            else:
                if output:
                    path, _ = QFileDialog.getSaveFileName(parent, label, filter = "NIfTI files (*.nii.gz)")
                else:
                    path, _ = QFileDialog.getOpenFileName(parent, label, filter = "NIfTI files (*.nii.gz)")
            if path:
                self.line_edit.setText(path)

        self.line_edit.textChanged.connect(self.set_invalid)
        self.button.clicked.connect(browse)

    def set_invalid(self):
        value = self.is_invalid()
        self.input_error.setVisible(value)
        set_property_and_update(self.line_edit, "invalid", value)

    def is_invalid(self):
        return self.line_edit.text().strip() == ""
