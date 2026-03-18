from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor


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