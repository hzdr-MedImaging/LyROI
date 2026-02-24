import sys
from PyQt5.QtWidgets import QApplication
from lyroi.gui.main_window import MainWindow
from lyroi.utils import setup_lyroi

def main():
    setup_lyroi()
    app = QApplication(sys.argv)
    app.setApplicationName("LyROI")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()