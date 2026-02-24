import pathlib

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QComboBox, QRadioButton, QGroupBox,
    QMessageBox
)

from lyroi.gui.worker import CommandWorker
from lyroi.gui.model_manager import ModelManager
from lyroi.gui.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LyROI")
        self.resize(900, 650)

        self.settings = Settings()
        self.model_manager = ModelManager()

        self.worker = None

        self.init_ui()
        self.load_models()

    # ---------------- UI ---------------- #

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # -------- Mode Selection -------- #
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()

        self.radio_batch = QRadioButton("Batch (Input/Output Directories)")
        self.radio_single = QRadioButton("Single Case (PET + CT Files)")
        self.radio_batch.setChecked(True)

        self.radio_batch.toggled.connect(self.update_mode_visibility)

        mode_layout.addWidget(self.radio_batch)
        mode_layout.addWidget(self.radio_single)
        mode_group.setLayout(mode_layout)

        layout.addWidget(mode_group)

        # -------- Batch Mode -------- #
        self.batch_group = QGroupBox("Batch Processing")
        batch_layout = QVBoxLayout()

        self.batch_input = self.make_path_selector("Input Directory", True)
        self.batch_output = self.make_path_selector("Output Directory", True)

        batch_layout.addLayout(self.batch_input)
        batch_layout.addLayout(self.batch_output)

        self.batch_group.setLayout(batch_layout)
        layout.addWidget(self.batch_group)

        # -------- Single Mode -------- #
        self.single_group = QGroupBox("Single Case Processing")
        single_layout = QVBoxLayout()

        self.pet_file = self.make_path_selector("PET File", False)
        self.ct_file = self.make_path_selector("CT File", False)
        self.single_output_dir = self.make_path_selector("Output Directory", True)

        self.output_filename = QLineEdit()
        single_layout.addLayout(self.pet_file)
        single_layout.addLayout(self.ct_file)
        single_layout.addLayout(self.single_output_dir)
        single_layout.addWidget(QLabel("Output Filename"))
        single_layout.addWidget(self.output_filename)

        self.single_group.setLayout(single_layout)
        layout.addWidget(self.single_group)

        # -------- Model Section -------- #
        model_group = QGroupBox("Model")
        model_layout = QHBoxLayout()

        self.model_dropdown = QComboBox()
        self.model_version_label = QLabel("Installed: unknown")

        self.btn_check_updates = QPushButton("Check Updates")
        self.btn_install = QPushButton("Install / Update")

        self.btn_check_updates.clicked.connect(self.check_updates)
        self.btn_install.clicked.connect(self.install_model)
        self.model_dropdown.currentIndexChanged.connect(self.update_installed_version)


        model_layout.addWidget(QLabel("Select Model"))
        model_layout.addWidget(self.model_dropdown)
        model_layout.addWidget(self.model_version_label)
        model_layout.addWidget(self.btn_check_updates)
        model_layout.addWidget(self.btn_install)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # -------- Run Section -------- #
        run_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_stop = QPushButton("Stop")

        self.btn_run.clicked.connect(self.run_command)
        self.btn_stop.clicked.connect(self.stop_command)

        run_layout.addWidget(self.btn_run)
        run_layout.addWidget(self.btn_stop)

        layout.addLayout(run_layout)

        # -------- Console -------- #
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        self.update_mode_visibility()

    # ---------------- Utilities ---------------- #

    def make_path_selector(self, label, directory):
        layout = QHBoxLayout()
        line = QLineEdit()
        btn = QPushButton("Browse")

        def browse():
            if directory:
                path = QFileDialog.getExistingDirectory(self, label)
            else:
                path, _ = QFileDialog.getOpenFileName(self, label)
            if path:
                line.setText(path)

        btn.clicked.connect(browse)

        layout.addWidget(QLabel(label))
        layout.addWidget(line)
        layout.addWidget(btn)
        layout.line_edit = line
        return layout

    def update_mode_visibility(self):
        self.batch_group.setVisible(self.radio_batch.isChecked())
        self.single_group.setVisible(self.radio_single.isChecked())

    # ---------------- Model Logic ---------------- #

    def load_models(self):
        models = self.model_manager.get_available_models()
        for model in models:
            self.model_dropdown.addItem(self.model_manager.get_pretty_name(model), userData=model)
        self.update_installed_version()

    def update_installed_version(self):
        model = self.model_dropdown.currentData()
        version = self.model_manager.get_installed_version(model)
        self.model_version_label.setText(f"Installed: {version}")

    def check_updates(self):
        model = self.model_dropdown.currentData()
        msg = self.model_manager.check_for_updates(model)
        QMessageBox.information(self, "Model Update", msg)

    def install_model(self):
        model = self.model_dropdown.currentData()
        self.console.append("Installing model " + model)
        self.worker = CommandWorker(
            ["lyroi_install", "--mode", model, "-y"])
        self.connect_worker()
        self.worker.start()

    # ---------------- Run Logic ---------------- #

    def run_command(self):
        model = self.model_dropdown.currentData()

        if self.radio_batch.isChecked():
            input_dir = self.batch_input.line_edit.text()
            output_dir = self.batch_output.line_edit.text()

            cmd = [
                "lyroi",
                "-i", input_dir,
                "-o", output_dir,
                "--mode", model
            ]

        else:
            pet = self.pet_file.line_edit.text()
            ct = self.ct_file.line_edit.text()
            out_dir = self.single_output_dir.line_edit.text()
            filename = self.output_filename.text()

            cmd = [
                "lyroi",
                "-i", ct, pet,
                "-o", pathlib.Path(out_dir, filename),
                "--mode", model
            ]

        self.console.clear()
        self.worker = CommandWorker(cmd)
        self.connect_worker()
        self.worker.start()

    def stop_command(self):
        if self.worker:
            self.worker.stop()

    def connect_worker(self):
        self.worker.output_signal.connect(self.console.append)
        self.worker.finished_signal.connect(
            lambda: self.console.append("\nFinished.\n")
        )