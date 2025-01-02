import os
import sys
import logging

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QApplication, QPushButton, QFileDialog, QCheckBox,
                               QMessageBox, QTextEdit, QLineEdit, QHBoxLayout, QProgressBar, QGridLayout, QGroupBox,
                               QStatusBar, QListWidget, QListWidgetItem, QSplitter, QScrollArea, QTabWidget, QLabel)

from PySide6.QtGui import QFont, QColor, QAction
from PySide6.QtCore import Qt, QThreadPool

from GUI.CustomWidgets import DropArea, TaskWidget
from GUI.Runnable import ConvertRunnable


def validate_version(version):
    """Verify version number format"""
    parts = version.split('.')
    return all(part.isdigit() for part in parts)


class MainWindow(QMainWindow):
    """Main window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PythonEXE Maker")
        self.setGeometry(250, 80, 1000, 700)
        self.setFont(QFont("Arial", 10))

        self.script_paths = []
        self.additional_directories = []
        self.thread_pool = QThreadPool()
        self.tasks = []
        self.task_widgets = {}
        self.default_theme = True

        # Menu bar
        self.init_menu()

        self.init_ui()
        self.update_start_button_state()

    def init_ui(self):
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Settings and operation area on the left
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.init_settings_group())
        left_layout.addLayout(self.init_button_group())
        left_widget.setMaximumWidth(450)
        splitter.addWidget(left_widget)

        # Right tab (task management, log)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # "Task Management" tab
        task_tab = QWidget()
        task_tab_layout = QVBoxLayout(task_tab)

        # Script management area
        script_group = QGroupBox("Script management")
        script_layout = QVBoxLayout()

        # Drag area and browse button
        drop_browse_layout = QHBoxLayout()
        self.drop_area = DropArea(self)
        self.drop_area.file_dropped.connect(self.add_script_path)
        drop_browse_layout.addWidget(self.drop_area)

        browse_button = QPushButton("Browse Files")
        browse_button.setToolTip(
            "Click to select the Python file to be converted. Multiple selections are available.")
        browse_button.clicked.connect(self.browse_files)
        browse_button.setFixedHeight(80)
        browse_button.setStyleSheet("QPushButton { font-size: 13px; }")
        drop_browse_layout.addWidget(browse_button)

        script_layout.addLayout(drop_browse_layout)

        # Script list
        self.script_list = QListWidget()
        self.script_list.setStyleSheet("""QListWidget {border: 1px;}""")
        self.script_list.setToolTip("List of selected Python scripts, which can be removed by double-clicking.")
        self.script_list.itemDoubleClicked.connect(self.remove_script)
        script_layout.addWidget(self.script_list)

        script_group.setLayout(script_layout)
        task_tab_layout.addWidget(script_group)

        # Task progress area
        task_progress_group = QGroupBox("Conversion Task Progress")
        task_progress_group.setStyleSheet("""QListWidget {border: 1px;}""")
        task_progress_layout = QVBoxLayout(task_progress_group)

        self.task_area = QScrollArea()
        self.task_area.setWidgetResizable(True)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_area.setWidget(self.task_container)
        task_progress_layout.addWidget(self.task_area)

        task_progress_group.setLayout(task_progress_layout)
        task_tab_layout.addWidget(task_progress_group)

        self.tab_widget.addTab(task_tab, "Task Management")

        # "Log" tab
        log_tab = QWidget()
        log_tab_layout = QVBoxLayout(log_tab)

        # Log text
        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)
        self.status_text_edit.setFont(QFont("Courier New", 9))
        log_tab_layout.addWidget(self.status_text_edit)

        # Global progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        log_tab_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_bar = QStatusBar()
        log_tab_layout.addWidget(self.status_bar)

        self.tab_widget.addTab(log_tab, "Log")

        splitter.addWidget(self.tab_widget)
        splitter.setSizes([700, 1000])

        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

    def init_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Quit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        theme_action = QAction('Change Theme', self)
        theme_action.triggered.connect(self.change_theme)
        file_menu.addAction(theme_action)

    def change_theme(self):
        app = QApplication.instance()
        if self.default_theme:
            app.setStyle("Windows")
            self.default_theme = False
        else:
            app.setStyle('windowsvista')
            self.default_theme = True

    def init_settings_group(self):
        """Initialize the group of basic settings, EXE information and advanced settings"""
        settings_group = QGroupBox("Basic Settings")
        settings_layout = QGridLayout()

        # Console window mode
        self.console_window = QCheckBox("Add a console window to the EXE file")
        settings_layout.addWidget(self.console_window, 0, 0, 1, 2)

        # Single exe or directory
        self.single_exe_file = QCheckBox("Single EXE file")
        self.single_exe_file.setChecked(True)
        settings_layout.addWidget(self.single_exe_file, 1, 0, 1, 2)

        # Output directory
        output_label = QLabel("Output Directory:")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("By default, it is in the same directory as the source file.")
        self.output_edit.setToolTip((
            "Set the output directory for generated EXE files. If empty, it will be placed in the same directory as the source file by default."))
        output_button = QPushButton("...")
        output_button.setToolTip("Select the output directory.")
        output_button.clicked.connect(self.browse_output_dir)
        output_button.setMaximumWidth(40)
        output_button.setStyleSheet("font-weight: bold")
        output_h_layout = QHBoxLayout()
        output_h_layout.addWidget(self.output_edit)
        output_h_layout.addWidget(output_button)
        settings_layout.addWidget(output_label, 2, 0)
        settings_layout.addLayout(output_h_layout, 2, 1)

        # EXE information
        exe_info_group = QGroupBox("EXE Information")
        exe_info_layout = QGridLayout()

        name_label = QLabel("EXE Name:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Defaults to the same name as the source file")
        self.name_edit.setToolTip("Set the generated EXE file name.")
        exe_info_layout.addWidget(name_label, 0, 0)
        exe_info_layout.addWidget(self.name_edit, 0, 1)

        icon_label = QLabel("Icon File:")
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("Optional, supports .png and .ico")
        self.icon_edit.setToolTip(
            'Select an icon file to use with the EXE. If it is PNG, it will be automatically converted to ICO.')
        icon_button = QPushButton("...")
        icon_button.setToolTip("Select the icon file.")
        icon_button.clicked.connect(self.browse_icon_file)
        icon_button.setMaximumWidth(40)
        icon_button.setStyleSheet("font-weight: bold")
        icon_h_layout = QHBoxLayout()
        icon_h_layout.addWidget(self.icon_edit)
        icon_h_layout.addWidget(icon_button)
        exe_info_layout.addWidget(icon_label, 1, 0)
        exe_info_layout.addLayout(icon_h_layout, 1, 1)

        version_label = QLabel("File Version:")
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1.0.0.0")
        self.version_edit.setToolTip("Set the version number of the EXE file (X.X.X.X).")
        exe_info_layout.addWidget(version_label, 2, 0)
        exe_info_layout.addWidget(self.version_edit, 2, 1)

        copyright_label = QLabel("Copyright Information:")
        self.copyright_edit = QLineEdit()
        self.copyright_edit.setToolTip("Set the copyright information of the EXE file.")
        exe_info_layout.addWidget(copyright_label, 3, 0)
        exe_info_layout.addWidget(self.copyright_edit, 3, 1)

        exe_info_group.setLayout(exe_info_layout)
        settings_layout.addWidget(exe_info_group, 3, 0, 1, 2)

        # Advanced settings
        advanced_settings_group = QGroupBox("Advanced Settings")
        advanced_settings_layout = QGridLayout()

        # Python Path
        python_path_label = QLabel("Python Path:")
        self.python_path_edit = QLineEdit()
        self.python_path_edit.setPlaceholderText("Select the Python exe file to use.")
        self.python_path_edit.setToolTip('Select the Python path to use.')
        if "__file__" in globals() and "PythonEXE_Maker.py" in sys.argv[0]:
            self.python_path_edit.setText(sys.executable)
        elif "PYTHONPATH" in os.environ:
            paths = os.environ['PYTHONPATH'].split(os.pathsep)
            for path in paths:
                python_exe_path = os.path.join(path, 'python.exe')
                if os.path.exists(python_exe_path):
                    self.python_path_edit.setText(python_exe_path)
                    break
        python_path_button = QPushButton("...")
        python_path_button.setToolTip("Select the python exe file.")
        python_path_button.clicked.connect(self.browse_python_path_file)
        python_path_button.setMaximumWidth(40)
        python_path_button.setStyleSheet("font-weight: bold")
        python_path_h_layout = QHBoxLayout()
        python_path_h_layout.addWidget(self.python_path_edit)
        python_path_h_layout.addWidget(python_path_button)
        advanced_settings_layout.addWidget(python_path_label, 0, 0)
        advanced_settings_layout.addLayout(python_path_h_layout, 0, 1)

        # Extra modules
        library_label = QLabel("Additional Modules:")
        self.library_edit = QLineEdit()
        self.library_edit.setPlaceholderText("Hidden imported modules, separated by commas")
        self.library_edit.setToolTip(
            "Enter the name of the module that needs to be added (separate multiple with commas).")
        advanced_settings_layout.addWidget(library_label, 1, 0)
        advanced_settings_layout.addWidget(self.library_edit, 1, 1)

        # Additional arguments
        options_label = QLabel("Additional Parameters:")
        self.options_edit = QLineEdit()
        self.options_edit.setPlaceholderText("For example：--add-binary 'libfoo.so;./Lib'")
        self.options_edit.setToolTip("Enter custom PyInstaller parameters.")
        advanced_settings_layout.addWidget(options_label, 2, 0)
        advanced_settings_layout.addWidget(self.options_edit, 2, 1)

        advanced_settings_group.setLayout(advanced_settings_layout)
        settings_layout.addWidget(advanced_settings_group, 4, 0, 1, 2)

        # Additional Directory
        additional_directory_group = QGroupBox("Additional Directory")
        additional_directory_layout = QGridLayout()

        # Source and destination headers
        source_folder_h_layout = QHBoxLayout()
        source_label = QLabel("Source")
        destination_label = QLabel("Destination")
        label = QLabel("   ")
        label.setMaximumWidth(40)
        source_folder_h_layout.addWidget(label)
        source_folder_h_layout.addWidget(destination_label)
        additional_directory_layout.addWidget(source_label, 0, 0)
        additional_directory_layout.addLayout(source_folder_h_layout, 0, 1)

        # Additional directories
        for index in range(3):
            source_folder_h_layout = QHBoxLayout()
            source_folder_edit = QLineEdit()
            source_folder_edit.setPlaceholderText("./Icons")
            source_folder_edit.setToolTip('Enter the directory to be included in the installation.')
            source_folder_button = QPushButton("...")
            source_folder_button.setObjectName(str(index))
            source_folder_button.setToolTip("Select the source directory folder.")
            source_folder_button.setMaximumWidth(40)
            source_folder_button.setStyleSheet("font-weight: bold")
            destination_folder_edit = QLineEdit()
            destination_folder_edit.setPlaceholderText("./Icons")
            destination_folder_edit.setToolTip('Enter the destination path.')
            source_folder_button.clicked.connect(self.browse_directory)
            source_folder_h_layout.addWidget(source_folder_button)
            source_folder_h_layout.addWidget(destination_folder_edit)
            additional_directory_layout.addWidget(source_folder_edit, index + 1, 0)
            additional_directory_layout.addLayout(source_folder_h_layout, index + 1, 1)
            self.additional_directories.append([source_folder_edit, destination_folder_edit])

        additional_directory_group.setLayout(additional_directory_layout)
        settings_layout.addWidget(additional_directory_group, 5, 0, 1, 2)

        settings_group.setLayout(settings_layout)
        return settings_group

    def init_button_group(self):
        """Initialize start and cancel conversion buttons"""
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start conversion")
        self.start_button.setEnabled(False)
        self.start_button.setToolTip("Start conversion of the selected Python script to EXE.")
        self.start_button.setStyleSheet("QPushButton { font-size: 13px; padding: 6px; }")
        self.start_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Cancel conversion")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip("Cancel a conversion task in progress.")
        self.cancel_button.setStyleSheet("QPushButton { font-size: 13px; padding: 6px; }")
        self.cancel_button.clicked.connect(self.cancel_conversion)
        button_layout.addWidget(self.cancel_button)

        return button_layout

    def add_script_path(self, path):
        """Add script path to list"""
        if path not in self.script_paths:
            self.script_paths.append(path)
            self.script_list.addItem(QListWidgetItem(path))
            self.append_status(f"Script added: {path}")
            self.update_start_button_state()

    def browse_files(self):
        """Browse and add the Python script file"""
        script_paths, _ = QFileDialog.getOpenFileNames(self, "Select Python file", "", "Python Files (*.py)")
        if script_paths:
            added = False
            for script_path in script_paths:
                if script_path not in self.script_paths:
                    self.script_paths.append(script_path)
                    self.script_list.addItem(QListWidgetItem(script_path))
                    self.append_status(f"Script added: {script_path}")
                    added = True
            if added:
                self.update_start_button_state()

    def browse_output_dir(self):
        """Browse and set the output directory"""
        output_dir = QFileDialog.getExistingDirectory(self, "Select output directory")
        if output_dir:
            self.output_edit.setText(output_dir)

    def browse_directory(self):
        """Browse and set the output directory"""
        button = self.sender()
        output_dir = QFileDialog.getExistingDirectory(self, "Select the directory to be included:")
        if button:
            index = int(button.objectName())
            if output_dir:
                self.additional_directories[index][0].setText(output_dir)
                self.additional_directories[index][1].setText("./" + os.path.basename(output_dir))

    def browse_icon_file(self):
        """Browse and set the icon file"""
        icon_path, _ = QFileDialog.getOpenFileName(self, "Select Icon file", "", "Image Files (*.ico *.png)")
        if icon_path:
            self.icon_edit.setText(icon_path)

    def browse_python_path_file(self):
        python_path, _ = QFileDialog.getOpenFileName(self, "Select Python File", "", "Executable (*.exe)")
        if python_path:
            self.python_path_edit.setText(python_path)

    def remove_script(self, item):
        """Remove script"""
        path = item.text()
        if path in self.script_paths:
            self.script_paths.remove(path)
            self.script_list.takeItem(self.script_list.row(item))
            self.append_status(f"Script removed: {path}")
            self.update_start_button_state()

    def start_conversion(self):
        """Start converting all selected scripts"""
        if not self.script_paths:
            QMessageBox.warning(self, "Warning", "Please select at least one Python script first.",
                                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return
        single_exe_file = self.single_exe_file.isChecked()
        console_window = self.console_window.isChecked()
        output_dir = self.output_edit.text().strip() or None
        exe_name = self.name_edit.text().strip() or None
        icon_path = self.icon_edit.text().strip() or None
        file_version = self.version_edit.text().strip() or None
        copyright_info = self.copyright_edit.text().strip()
        extra_library = self.library_edit.text().strip() or None
        additional_options = self.options_edit.text().strip() or ""
        python_path = self.python_path_edit.text().strip() or None
        directory_values = []
        for directories in self.additional_directories:
            directory_values.append([directories[0].text().strip() or None, directories[1].text().strip() or None])

        for item in directory_values:
            if item[0] and os.path.exists(item[0]):
                additional_options += f" --add-data {item[0]}:{item[1]}"

        if not python_path:
            QMessageBox.warning(self, "Warning", "Please set the correct path for Python (python.exe).",
                                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return

        if not os.path.exists(python_path):
            QMessageBox.warning(self, "Warning", "Python path does not exist. Please select a correct file. ",
                                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return

        if file_version and not validate_version(file_version):
            QMessageBox.warning(self, "Warning", "Enter correct version number (Numbers, separated by dots).",
                                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return

        self.toggle_ui_elements(False)
        self.status_text_edit.clear()
        self.append_status("Start converting...")
        self.progress_bar.show()
        self.status_bar.showMessage("Converting...")

        self.tasks = []
        self.task_widgets = {}
        # Clear the task progress display area
        for i in reversed(range(self.task_layout.count())):
            w = self.task_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for script_path in self.script_paths:
            task_widget = TaskWidget(script_path)
            self.task_layout.addWidget(task_widget)
            self.task_widgets[script_path] = {'widget': task_widget, 'script_label': task_widget.script_label,
                                              'progress': task_widget.progress, 'status': task_widget.status,
                                              'path': task_widget.path}

            runnable = ConvertRunnable(script_path=script_path, console_window=console_window,
                                       single_exe_file=single_exe_file, output_dir=output_dir, exe_name=exe_name,
                                       icon_path=icon_path, file_version=file_version, copyright_info=copyright_info,
                                       extra_library=extra_library, additional_options=additional_options,
                                       python_path=python_path)

            runnable.signals.status_updated.connect(lambda msg, sp=script_path: self.update_status(msg, sp))
            runnable.signals.progress_updated.connect(lambda val, sp=script_path: self.update_progress(val, sp))
            runnable.signals.conversion_finished.connect(
                lambda exe, size, sp=script_path: self.conversion_finished(exe, size, sp))
            runnable.signals.conversion_failed.connect(lambda err, sp=script_path: self.conversion_failed(err, sp))

            self.thread_pool.start(runnable)
            self.tasks.append(runnable)

        self.cancel_button.setEnabled(True)

    def cancel_conversion(self):
        """Cancel all ongoing conversion tasks"""
        if hasattr(self, 'tasks') and self.tasks:
            for task in self.tasks:
                task.stop()
            self.append_status("Cancellation of the conversion task has been requested.")
            self.status_bar.showMessage("Cancel conversion...")
            self.cancel_button.setEnabled(False)

    def conversion_finished(self, exe_path, exe_size, script_path):
        """Handle conversion completion"""
        self.append_status("<span style='color:green;'>Conversion successful!</span>")
        self.append_status(f"EXE file is located at: {exe_path} (size: {exe_size} MB)")
        task_widget = self.task_widgets.get(script_path)
        if task_widget:
            task_widget['status'].setText("<span style='color:green;'>Conversion successful!</span>")
            task_widget['path'].show()
            task_widget['path'].setText(f"File: {exe_path} ({exe_size} MB)")
            task_widget['progress'].setValue(100)
            self.progress_bar.setValue(100)
        if not all([getattr(task, '_is_running', False) for task in self.tasks]):
            self.conversion_complete()

    def conversion_failed(self, error_message, script_path):
        """Handling conversion failure situations"""
        self.append_status(f"<span style='color:red;'>{error_message}</span>")
        task_widget = self.task_widgets.get(script_path)
        if task_widget:
            task_widget['status'].setText(f"<span style='color:red;'>{error_message}</span>")
            task_widget['progress'].setValue(0)
            self.progress_bar.setValue(0)
        if not all([getattr(task, '_is_running', False) for task in self.tasks]):
            self.conversion_complete()

    def conversion_complete(self):
        """Processing after completion of all conversion tasks"""
        self.toggle_ui_elements(True)
        self.progress_bar.hide()
        self.status_bar.showMessage("Conversion completed.")
        self.tasks = []

    def toggle_ui_elements(self, enabled):
        """Enable or disable UI elements"""
        self.start_button.setEnabled(enabled and bool(self.script_paths))
        self.console_window.setEnabled(enabled)
        self.single_exe_file.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.name_edit.setEnabled(enabled)
        self.icon_edit.setEnabled(enabled)
        self.version_edit.setEnabled(enabled)
        self.library_edit.setEnabled(enabled)
        self.options_edit.setEnabled(enabled)
        self.drop_area.setEnabled(enabled)
        self.script_list.setEnabled(enabled)
        if enabled:
            self.cancel_button.setEnabled(False)

    def append_status(self, text):
        """Append status information to the log"""
        logging.info(text)
        if "<span style='color:red;'>" in text:
            self.status_text_edit.setTextColor(QColor('red'))
        else:
            self.status_text_edit.setTextColor(QColor('black'))
        self.status_text_edit.append(text)

    def update_status(self, status, script_path):
        """Update the status of a specific script"""
        self.append_status(f"[{os.path.basename(script_path)}] {status}")

    def update_progress(self, value, script_path):
        """Update the progress bar of a specific script"""
        task_widget = self.task_widgets.get(script_path)
        if task_widget:
            task_widget['progress'].setValue(value)
            self.progress_bar.setValue(value)

    def update_start_button_state(self):
        """Update the enabled state of the start button"""
        self.start_button.setEnabled(bool(self.script_paths))

    def closeEvent(self, event):
        """Processing before closing the window"""
        if hasattr(self, 'tasks') and self.tasks:
            for task in self.tasks:
                task.stop()
            self.tasks = []
        event.accept()
