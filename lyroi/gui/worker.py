import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal


class CommandWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None

    def run(self):
        safe_command = [str(x) for x in self.command]

        self.process = subprocess.Popen(
            safe_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in self.process.stdout:
            self.output_signal.emit(line.strip())

        self.process.wait()
        self.finished_signal.emit()

    def stop(self):
        if self.process:
            self.process.terminate()