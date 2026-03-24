import pathlib

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication, QFileDialog, QMessageBox, QLabel, QWidget, QLineEdit, \
    QPushButton

from PyQt5.QtCore import Qt


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


def validate_path(path):
    return path and path.strip() != ""

def visualize_grid(grid_layout):
    """Wrap each widget in a QFrame to show cell boundaries"""
    # Store items to process (can't modify while iterating)
    items_to_wrap = []
    for i in range(grid_layout.count()):
        item = grid_layout.itemAt(i)
        if item and item.widget():
            items_to_wrap.append((i, item.widget()))

    # Wrap each widget in a frame
    for i, widget in items_to_wrap:
        # Get position
        index = grid_layout.indexOf(widget)
        if index == -1:
            continue

        row, col, row_span, col_span = grid_layout.getItemPosition(index)

        # Remove widget from layout
        grid_layout.removeWidget(widget)

        # Create frame container
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        frame.setLineWidth(1)
        frame.setStyleSheet("border-color: red;")

        # Put widget inside frame
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(widget)

        # Add frame back to grid
        grid_layout.addWidget(frame, row, col, row_span, col_span)

def set_property_and_update(field, property, value):
    field.setProperty(property, value)
    field.style().unpolish(field)
    field.style().polish(field)
    field.update()

def set_ui_scale(factor: float):
    app = QApplication.instance()
    font = app.font()
    font.setPointSizeF(font.pointSizeF() * factor)
    app.setFont(font)