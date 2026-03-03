from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QComboBox, QRadioButton, QGroupBox,
    QMessageBox, QProgressBar, QFormLayout, QGridLayout, QLayout, QSpacerItem, QFrame
)
from PyQt5.QtCore import Qt

from lyroi.gui.worker import CommandWorker
from lyroi.gui.model_manager import ModelManager
from lyroi.gui.settings import Settings
from lyroi.gui.utils import visualize_grid, set_property_and_update


class FileSelector:
    def __init__(self, parent: QWidget, label, directory, output = False):
        self.label = QLabel(label)
        self.line_edit = QLineEdit()
        self.button = QPushButton("Browse")

        self.input_error = QLabel("Missing required field")
        self.input_error.setStyleSheet("color: red; font-size: 10px")
        self.input_error.setMargin(-1)
        self.input_error.setVisible(False)
        self.input_error.setAlignment(Qt.AlignLeft)
        self.input_error.setAlignment(Qt.AlignTop)

        def browse():
            if directory:
                path = QFileDialog.getExistingDirectory(parent, label)
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
        self.define_styles()

        self.color_ui_red = ""

    # ---------------- UI ---------------- #
    def add_file_selector(self, layout: QGridLayout, selector: FileSelector):
        row = layout.rowCount()
        layout.addWidget(selector.label, row, 0)
        layout.addWidget(selector.line_edit, row, 1)
        layout.addWidget(selector.button, row, 2)
        layout.addWidget(selector.input_error, row + 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        layout.setRowMinimumHeight(row + 1, selector.input_error.sizeHint().height() + 1)

    def add_note(self, layout: QGridLayout, text: str):
        row = layout.rowCount()
        columns = layout.columnCount()
        layout.addWidget(QLabel(text), row, 0, 1, columns)

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
        """)

    def init_ui(self):
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
        self.batch_output = FileSelector(self,"Output Directory", True)

        self.add_file_selector(batch_layout, self.batch_input)
        #self.add_note(batch_layout, "Note: abc")
        self.add_file_selector(batch_layout, self.batch_output)

        self.batch_group.setLayout(batch_layout)
        layout.addWidget(self.batch_group)
        #visualize_grid(batch_layout)

        # -------- Single Mode -------- #
        self.single_group = QGroupBox()
        single_layout = QGridLayout()

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

        self.model_dropdown = QComboBox()
        self.model_version_label = QLabel("Installed: unknown")

        self.btn_check_updates = QPushButton("Check Updates")
        self.btn_install = QPushButton("Install / Update")

        self.btn_check_updates.clicked.connect(self.check_updates)
        self.btn_install.clicked.connect(self.install_model)
        self.model_dropdown.currentIndexChanged.connect(self.update_installed_version)


        model_layout.addWidget(QLabel("Select Mode"))
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
        self.progress_label = QLabel("Current Task Progress")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.btn_run.clicked.connect(self.start_prediction)
        self.btn_stop.clicked.connect(self.stop_command)

        run_layout.addWidget(self.btn_run)
        run_layout.addWidget(self.btn_stop)
        run_layout.addWidget(self.progress_label)
        run_layout.addWidget(self.progress_bar)

        layout.addLayout(run_layout)

        # -------- Errors ---------#

        self.input_error = QLabel("Missing required fields")
        self.input_error.setStyleSheet("color: red; font-size: 11px;")
        self.input_error.setVisible(False)
        self.input_error.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.input_error)

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


    # ---------------- Run Logic ---------------- #

    def start_prediction(self):
        model = self.model_dropdown.currentData()
        if not self.validate_fields():
            return False

        self.console.clear()
        self.console.append("Starting prediction with model " + model)

        if self.radio_batch.isChecked():
            input_dir = self.batch_input.line_edit.text()
            output_dir = self.batch_output.line_edit.text()

            font_metrics = QFontMetrics(self.console.font())
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
                "--mode", model
            ]

        else:
            pet = self.pet_file.line_edit.text()
            ct = self.ct_file.line_edit.text()
            output_file = self.output_file.line_edit.text()

            self.console.append("Input files:\n" + "CT: " + ct + "\n" + "PET: " + pet + "\n")
            self.console.append("Output file:\n" + str(output_file) + "\n")

            cmd = [
                "lyroi",
                "-i", ct, pet,
                "-o", output_file,
                "--mode", model
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