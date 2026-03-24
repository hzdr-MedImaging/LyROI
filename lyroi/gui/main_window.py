from PyQt5.QtGui import QFontMetrics, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QComboBox, QRadioButton, QGroupBox,
    QMessageBox, QProgressBar, QGridLayout, QSizePolicy, QAction
)
from PyQt5.QtCore import Qt, QTimer, QThread, QEventLoop

from lyroi.devices import DeviceManager
from lyroi.gui.worker import CommandWorker, PyWorker
from lyroi.gui.model_manager import ModelManager
from lyroi.gui.settings import Settings
from lyroi.gui.utils import visualize_grid, set_property_and_update, set_ui_scale, DirectoryDialog, FileSelector
from lyroi.gui.loading_screen import LoadingOverlay

from lyroi import __legal__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LyROI")
        self.resize(700, 650)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        self.settings = Settings()
        self.model_manager = ModelManager()
        self.device_manager = DeviceManager()

        self.worker = None
        self.gui_tasks = []

        self.define_styles()
        self.init_ui()
        self.build_menubar()
        self.load_models()
        QTimer.singleShot(100, self.load_devices)

    # ---------------- UI ---------------- #
    def add_file_selector(self, layout: QGridLayout, selector: FileSelector):
        row = layout.rowCount()
        layout.addWidget(selector.label, row, 0)
        layout.addWidget(selector.line_edit, row, 1)
        layout.addWidget(selector.button, row, 2)
        layout.addWidget(selector.input_error, row + 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        layout.setRowMinimumHeight(row + 1, selector.input_error.sizeHint().height() + 1)

    def add_note(self, layout: QGridLayout, label: QLabel):
        row = layout.rowCount()
        columns = layout.columnCount()
        label.setProperty("type", "note")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, 1, columns)

    def define_styles(self):
        self.setStyleSheet("""
            QLineEdit[invalid="true"] {
                border: 1px solid #d32f2f;
                padding-bottom: 0px
            }
            QProgressBar::chunk[inactive="true"] {
                background-color: #a9a9a9;
                border: 2px
            }
            QLabel[status="bad"] {
                color: #d32f2f  
            }
            QLabel[status="good"] {
                color: #388e3c  
            }
            QLabel[status="neutral"] {
                color: #616161  
            }
            QLabel[type="note"] {
                color: #616161  
            }
        """)

    def build_menubar(self):

        def show_help():
            QMessageBox.information(self, "Help",
                                    "Welcome to LyROI – nnU-Net-based Lymphoma Total Metabolic Tumor Volume Delineation Tool\n\n"
                                    "For detailed documentation, visit our github:\n"
                                    "https://github.com/hzdr-MedImaging/LyROI")

        def show_about():
            QMessageBox.about(self, "About",
                              __legal__)

        # Help
        help_menu = self.menuBar().addMenu("&Help")

        help_contents_action = QAction("&Help", self)
        help_contents_action.setShortcut("F1")
        help_contents_action.setStatusTip("Open help documentation")
        help_contents_action.triggered.connect(show_help)
        help_menu.addAction(help_contents_action)

        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(show_about)
        help_menu.addAction(about_action)



    def init_ui(self):
        self.overlay = LoadingOverlay(self)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # -------- Mode Selection -------- #
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()

        self.radio_batch = QRadioButton("Batch Processing")
        self.radio_single = QRadioButton("Single Case Processing")
        self.radio_batch.setChecked(True)

        self.radio_batch.toggled.connect(self.update_mode_visibility)

        mode_layout.addWidget(self.radio_batch)
        mode_layout.addWidget(self.radio_single)
        mode_group.setLayout(mode_layout)

        layout.addWidget(mode_group)

        # -------- Batch Mode -------- #
        self.batch_group = QGroupBox()
        batch_layout = QGridLayout()
        batch_layout.setAlignment(Qt.AlignTop)
        batch_layout.setVerticalSpacing(0)

        self.batch_input = FileSelector(self,"Input Directory", True)
        self.batch_output = FileSelector(self,"Output Directory", True, output=True)
        self.batch_note_label = QLabel(self)

        self.add_file_selector(batch_layout, self.batch_input)
        self.add_file_selector(batch_layout, self.batch_output)

        self.add_note(batch_layout, self.batch_note_label)

        self.batch_group.setLayout(batch_layout)
        layout.addWidget(self.batch_group)
        #visualize_grid(batch_layout)

        # -------- Single Mode -------- #
        self.single_group = QGroupBox()
        single_layout = QGridLayout()
        single_layout.setAlignment(Qt.AlignTop)
        single_layout.setVerticalSpacing(0)

        self.ct_file = FileSelector(self,"CT File", False)
        self.pet_file = FileSelector(self,"PET File", False)
        self.output_file = FileSelector(self,"Output File", False, True)

        self.add_file_selector(single_layout, self.ct_file)
        self.add_file_selector(single_layout, self.pet_file)
        self.add_file_selector(single_layout, self.output_file)

        self.single_group.setLayout(single_layout)
        layout.addWidget(self.single_group)

        # -------- Model Section -------- #
        model_group = QGroupBox("Model")
        model_layout = QHBoxLayout()

        self.model_label = QLabel("Select mode")
        self.model_dropdown = QComboBox()
        self.model_version_tag_offline = QLabel("Installed: ")
        self.model_version_tag_online = QLabel("Latest: ")
        self.model_version_val_offline = QLabel("Unknown")
        self.model_version_val_online = QLabel("Unknown")
        self.btn_install = QPushButton("Install / Update")

        self.model_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.model_dropdown.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.btn_install.clicked.connect(self.model_install_dialog)
        self.model_dropdown.currentIndexChanged.connect(self.update_installed_version)
        self.model_dropdown.currentIndexChanged.connect(self.update_online_version)
        self.model_dropdown.currentIndexChanged.connect(self.update_notes)

        model_version_layout = QGridLayout()
        tag_width = self.model_version_tag_offline.sizeHint().width() + 10
        self.model_version_tag_online.setFixedWidth(tag_width)
        self.model_version_tag_offline.setFixedWidth(tag_width)
        model_version_layout.addWidget(self.model_version_tag_offline, 0, 0)
        model_version_layout.addWidget(self.model_version_tag_online, 1, 0)
        model_version_layout.addWidget(self.model_version_val_offline, 0, 1)
        model_version_layout.addWidget(self.model_version_val_online, 1, 1)
        model_version_layout.setSpacing(0)
        model_version_layout.setContentsMargins(10, 0, 0, 0)

        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_dropdown)
        model_layout.addLayout(model_version_layout)
        model_layout.addWidget(self.btn_install)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # -------- Run Section -------- #
        run_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_stop = QPushButton("Stop")
        self.device_label = QLabel("Select device")
        self.device_dropdown = QComboBox()
        self.device_status_label = QLabel("")

        self.device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.btn_run.clicked.connect(self.start_prediction)
        self.btn_stop.clicked.connect(self.stop_command)
        self.device_dropdown.currentIndexChanged.connect(self.update_device_availability)

        run_layout.addWidget(self.btn_run)
        run_layout.addWidget(self.btn_stop)
        run_layout.addWidget(QWidget())
        run_layout.addWidget(self.device_label)
        run_layout.addWidget(self.device_dropdown)
        run_layout.addWidget(self.device_status_label)

        layout.addLayout(run_layout)

        # -------- Progress bar -------- #
        progress_layout = QGridLayout()

        self.progress_label = QLabel("Current Task Progress")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.progress_label, 0, 0)
        progress_layout.addWidget(self.progress_bar, 0, 1)

        layout.addLayout(progress_layout)

        # -------- Console -------- #
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        self.update_mode_visibility()
        self.set_idle_state()

    # ---------------- Utilities ---------------- #

    def update_mode_visibility(self):
        self.batch_group.setVisible(self.radio_batch.isChecked())
        self.single_group.setVisible(self.radio_single.isChecked())

    def set_active_state(self):
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        set_property_and_update(self.progress_bar, "inactive", False)

    def set_idle_state(self):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        set_property_and_update(self.progress_bar, "inactive", True)

    # ---------------- Model Logic ---------------- #

    def load_models(self):
        models = self.model_manager.get_available_models()
        for model in models:
            self.model_dropdown.addItem(self.model_manager.get_pretty_name(model), userData=model)

        size = self.model_dropdown.sizeHint().width() + 5
        self.model_dropdown.setMaximumWidth(size)

    def update_notes(self):
        suff_string = self.model_manager.get_suffix_string(self.model_dropdown.currentData())
        self.batch_note_label.setText('Note: files in the input folder should follow the nnU-Net conventions: '
                                    'file name should start with unique patient ID and end with appropriate suffix (' + suff_string+'). Only .nii.gz files are supported.')

    def update_installed_version(self):
        model = self.model_dropdown.currentData()
        version = self.model_manager.get_installed_version(model)
        self.model_version_val_offline.setText(version)

    def update_online_version(self):
        model = self.model_dropdown.currentData()

        def get_version():
            return self.model_manager.get_online_version(model)

        def set_version(version):
            self.model_version_val_online.setText(version)
            if version != "N/A":
                set_property_and_update(self.model_version_val_online, "status", "")
            else:
                set_property_and_update(self.model_version_val_online, "status", "bad")
            #self.model_dropdown.setEnabled(True)

        self.model_version_val_online.setText("Checking...")
        set_property_and_update(self.model_version_val_online, "status", "neutral")
        #self.model_dropdown.setEnabled(False)
        self.async_call(set_version, get_version, kill_signal=self.model_dropdown.currentIndexChanged)

    def model_install_dialog(self):
        model = self.model_dropdown.currentData()

        msg = self.blocking_call(self.model_manager.check_for_updates, model = model)

        reply = QMessageBox.question(
            self,
            "Model installation",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes  # default button
        )

        if reply == QMessageBox.Yes:
            self.install_model()

    def install_model(self):
        model = self.model_dropdown.currentData()
        pretty_name = self.model_manager.get_pretty_name(model)
        self.console.clear()
        self.console.append("Installing models for " + pretty_name + " mode\n")
        self.worker = CommandWorker(
            ["lyroi_install", "--mode", model, "-y", "-f"])
        self.connect_worker()
        self.worker.start()
        self.set_active_state()

    def validate_fields(self):
        is_batch_mode = self.radio_batch.isChecked()
        fields = []
        if is_batch_mode:
            fields.append(self.batch_input)
            fields.append(self.batch_output)
        else:
            fields.append(self.ct_file)
            fields.append(self.pet_file)
            fields.append(self.output_file)

        flag = True
        for field in fields:
            flag &= not field.is_invalid()
            field.set_invalid()

        return flag

    # ---------------- Device Logic ---------------- #

    def load_devices(self):
        devices = self.device_manager.get_all()
        for device in devices:
            self.device_dropdown.addItem(self.device_manager.get_pretty_name(device), userData=device)

    def update_device_availability(self):
        device = self.device_dropdown.currentData()

        def get_availability():
            return self.device_manager.is_available(device)

        def set_device_status(is_available):
            if is_available:
                self.device_status_label.setText("Status: Available")
                set_property_and_update(self.device_status_label, "status", "good")
            else:
                set_property_and_update(self.device_status_label, "status", "bad")
                self.device_status_label.setText("Status: Not Available")
            #self.device_dropdown.setEnabled(True)

        if self.device_manager.has_availability(device):
            set_device_status(get_availability()) # no need to wait
        else:
            self.device_status_label.setText("Status: Checking...")
            set_property_and_update(self.device_status_label, "status", "neutral")
            #self.device_dropdown.setEnabled(False)
            self.async_call(set_device_status, get_availability, kill_signal=self.device_dropdown.currentIndexChanged)


    # ---------------- Run Logic ---------------- #

    def start_prediction(self):
        model = self.model_dropdown.currentData()
        device = self.device_dropdown.currentData()
        if not self.validate_fields():
            return False

        self.console.clear()
        self.console.append("Starting prediction with model " + model)

        font_metrics = QFontMetrics(self.console.font())

        if self.radio_batch.isChecked():
            input_dir = self.batch_input.line_edit.text()
            output_dir = self.batch_output.line_edit.text()

            tab_width = font_metrics.horizontalAdvance("Output directory:") + 15
            self.console.insertHtml(f"""
                <table width="100%" cellpadding="2">
                    <tr><td width="{tab_width}">Input directory:</td><td>{input_dir}</td></tr>
                    <tr><td width="{tab_width}">Output directory:</td><td>{output_dir}</td></tr>
                </table>
                <br>
            """)

            cmd = [
                "lyroi",
                "-i", input_dir,
                "-o", output_dir,
                "--mode", model,
                "--device", device
            ]

        else:
            pet = self.pet_file.line_edit.text()
            ct = self.ct_file.line_edit.text()
            output_file = self.output_file.line_edit.text()

            tab_width = font_metrics.horizontalAdvance("Output file:") + 15
            self.console.insertHtml(f"""
                <table width="100%" cellpadding="2">
                    <tr><td width="{tab_width}">CT file:</td><td>{ct}</td></tr>
                    <tr><td width="{tab_width}">PET file:</td><td>{pet}</td></tr>
                    <tr><td width="{tab_width}">Output file:</td><td>{output_file}</td></tr>
                </table>
                <br>
            """)

            cmd = [
                "lyroi",
                "-i", ct, pet,
                "-o", output_file,
                "--mode", model,
                "--device", device
            ]

        n_folds = self.model_manager.get_n_folds(model)
        self.worker = CommandWorker(cmd, n_folds = n_folds)
        self.connect_worker()
        self.worker.start()
        self.set_active_state()

        return True

    def stop_command(self):
        if self.worker:
            self.console.append("Stop requested")
            self.console.repaint()
            self.worker.progress_signal.disconnect()
            self.worker.stop()

    def finish_handler(self):
        self.worker = None
        self.console.append("\nFinished.\n")
        self.set_idle_state()

    def connect_worker(self):
        self.worker.output_signal.connect(self.console.append)
        self.worker.finished_signal.connect(self.finish_handler)
        self.worker.progress_signal.connect(self.progress_bar.setValue)

    def blocking_call(self, function, *args, **kwargs):
        loop = QEventLoop()
        thread = QThread()
        worker = PyWorker(function, *args, **kwargs)
        worker.moveToThread(thread)

        results = {}

        def store_results(value):
            results["value"] = value

        worker.result.connect(store_results)
        worker.finished.connect(loop.quit)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)

        self.overlay.start()
        thread.start()

        loop.exec()  # blocks logically but UI still alive

        thread.wait()

        self.overlay.stop()

        return results.get("value")

    def async_call(self, result_handler, function, kill_signal = None, *args, **kwargs):
        thread = QThread()
        worker = PyWorker(function, *args, **kwargs)
        task = (thread, worker)

        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.result.connect(result_handler)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(lambda: self.cleanup_task(task))

        if kill_signal:
            def ignore_result():
                worker.muted = True
                kill_signal.disconnect(ignore_result)
            kill_signal.connect(ignore_result)

        self.gui_tasks.append(task)

        thread.start()

    def cleanup_task(self, task):
        if task in self.gui_tasks:
            self.gui_tasks.remove(task)
