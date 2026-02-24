from PyQt5.QtCore import QSettings


class Settings:
    def __init__(self):
        self.settings = QSettings("HZDR", "LyROI_GUI")

    def set(self, key, value):
        self.settings.setValue(key, value)

    def get(self, key, default=None):
        return self.settings.value(key, default)