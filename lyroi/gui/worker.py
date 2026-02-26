import os
import re
import signal
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal


class CommandWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)

    tqdm_re = re.compile(r"(\d+)%\|")

    def __init__(self, command, n_folds = 1):
        super().__init__()
        self.command = command
        self.process = None
        self._in_tqdm = False
        self._current_fold = 0
        self.n_folds = n_folds

    def run(self):
        safe_command = [str(x) for x in self.command]
        self.progress_signal.emit(0)

        try:
            kwargs = {}
            if os.name == "nt":
                # Windows flags
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs['preexec_fn'] = os.setsid

            self.process = subprocess.Popen(
                safe_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                **kwargs
            )
        except Exception as e:
            self.output_signal.emit("Error: " + e.__str__())
            self.finished_signal.emit()
            return

        for line in self.process.stdout:
            self.handle_output(line.strip())

        self.process.wait()
        self.finished_signal.emit()

    def handle_output(self, text: str):
        text = text.rstrip("\n")

        match = self.tqdm_re.search(text)
        if match:
            percent = int(match.group(1))
            percent = (100 * self._current_fold + percent) / self.n_folds
            self.progress_signal.emit(round(percent))
            if not self._in_tqdm:
                self.output_signal.emit("Task in progress...\n")
            self._in_tqdm = True
            return  # DO NOT send tqdm lines to console

        # skip empty lines in tqdm loop and track the current fold
        if self._in_tqdm and text.strip() == "":
            self._current_fold += 1
            return

        # tdqm loop is over. Reset
        self._current_fold = 0
        self._in_tqdm = False

        # everything else goes to console
        self.output_signal.emit(text)

    def term_process(self):
        if os.name == "nt":
            # Windows
            self.process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            # UNIX
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def stop(self):
        if not self.process:
            return

        if self.process.poll() is None: #check if already terminated
            try:
                self.term_process()
                self.process.wait(1)
            except subprocess.TimeoutExpired:
                try:
                    # try again
                    self.term_process()
                    self.process.wait(1)
                except subprocess.TimeoutExpired:
                    # if nothing else helps
                    self.process.kill()
