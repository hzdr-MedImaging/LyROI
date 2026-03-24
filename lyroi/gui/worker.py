import os
import re
import signal
import subprocess
import sys
import time

from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot


# Only for Windows
def send_ctrl_break(pid):
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32')
    kernel32.FreeConsole()
    if kernel32.AttachConsole(pid):
        kernel32.GenerateConsoleCtrlEvent(1, pid)
        time.sleep(0.1)
        kernel32.FreeConsole()
        return True
    return False


class CommandWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)
    progress_total_signal = pyqtSignal(int)

    tqdm_re = re.compile(r"(\d+)%\|")
    cases_re = re.compile(r"There are (\d+) cases in the source folder")
    models_re = re.compile(r"Predicting with model (\d+)/(\d+)")
    download_re = re.compile("Downloading pretrained model from url:")

    def __init__(self, command, n_folds=1):
        super().__init__()
        self.command = command
        self.process = None
        self.error_status = False
        self._in_tqdm = False
        self._current_fold = 0
        self._current_case = -1
        self._current_model = -1
        self.n_cases = 1
        self.n_models = 1
        self.n_folds = n_folds

    def run(self):
        safe_command = [str(x) for x in self.command]
        self.progress_signal.emit(0)
        self.progress_total_signal.emit(0)

        try:
            kwargs = {}
            if os.name == "nt":
                # Windows flags
                kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                # kwargs['creationflags'] |= subprocess.CREATE_NO_WINDOW
                # kwargs['creationflags'] |= subprocess.DETACHED_PROCESS

                # Use STARTUPINFO to hide the window instead of CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                kwargs['startupinfo'] = startupinfo
                kwargs['close_fds'] = True
            else:
                kwargs['preexec_fn'] = os.setsid

            self.process = subprocess.Popen(
                safe_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                **kwargs
            )
        except Exception as e:
            self.output_signal.emit("Error: " + e.__str__())
            self.error_status = True
            self.finished_signal.emit()
            return

        for line in self.process.stdout:
            self.handle_output(line.strip())

        self.process.wait()
        self.finished_signal.emit()

    def handle_output(self, text: str):
        text = text.rstrip("\n")

        # matching percent indication
        match = self.tqdm_re.search(text)
        if match:
            if not self._in_tqdm:
                self.output_signal.emit("Task in progress...\n")
                self._current_case += 1  # increment case counter of tqdm loop start
                self.output_signal.emit("Current case: " + str(self._current_case) + "/" + str(self.n_cases))
            self._in_tqdm = True
            self.progress_signal.emit(self.task_progress(match.group(1)))
            self.progress_total_signal.emit(self.total_progress(match.group(1)))
            return  # DO NOT send tqdm lines to console

        # skip empty lines in tqdm loop and track the current fold
        if self._in_tqdm and text.strip() == "":
            self._current_fold += 1
            return

        # tdqm loop is over. Reset
        self._current_fold = 0
        self._in_tqdm = False

        ### prediction parsing
        # matching case count
        match = self.cases_re.search(text)
        if match:
            self.set_n_cases(match.group(1))
            self._current_case = -1  # will become 0 as soon as the first tqdm line is received

        # matching model count
        match = self.models_re.search(text)
        if match:
            self.set_current_model(match.group(1))
            self.set_n_models(match.group(2))

        ### installation parsing
        match = self.download_re.search(text)
        if match:
            self._current_model += 1
            self._current_case = -1

        # everything else goes to console
        self.output_signal.emit(text)

    def set_n_cases(self, n_cases):
        n_cases = int(n_cases)
        self.output_signal.emit("Cases:" + str(n_cases))
        self.n_cases = n_cases

    def set_n_models(self, n_models):
        n_models = int(n_models)
        self.output_signal.emit("Models:" + str(n_models))
        self.n_models = n_models

    def set_current_model(self, index):
        index = int(index)
        index = index - 1
        self.output_signal.emit("Current model:" + str(index))
        self._current_model = index

    def get_error_status(self):
        return self.error_status

    def task_progress(self, percent):
        percent = int(percent)
        percent = (100 * self._current_fold + percent) / self.n_folds
        return round(percent)

    def total_progress(self, percent):
        percent = self.task_progress(percent)  # taking care of folds
        percent = (100 * self._current_case + percent) / self.n_cases  # taking care of cases
        percent = (100 * self._current_model + percent) / self.n_models  # taking care of models
        return round(percent)

    def term_process(self):
        if os.name == "nt":
            # Windows
            if sys.executable.endswith("pythonw.exe"):
                # pythonw does not have its own console, so we need to attach to a child's console
                send_ctrl_break(self.process.pid)
            else:
                # Needed to avoid crashes with python interpreter
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            # UNIX
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def stop(self):
        self.error_status = True
        if not self.process:
            return

        if self.process.poll() is None:  # check if already terminated
            try:
                self.term_process()
                self.process.wait(2)
            except subprocess.TimeoutExpired:
                try:
                    # try again
                    self.term_process()
                    self.process.wait(2)
                except subprocess.TimeoutExpired:
                    # if nothing else helps
                    print("Force termination")
                    self.process.kill()


class PyWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

        self.muted = False

    def run(self):
        result = self.function(*self.args, **self.kwargs)
        if not self.muted:
            self.result.emit(result)
        self.finished.emit()
