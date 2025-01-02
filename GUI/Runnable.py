import os
import sys
import subprocess
import logging

from PySide6.QtCore import QRunnable

from GUI.Signals import WorkerSignals

# Try to import Pillow
try:
    from PIL import Image
except ImportError:
    Image = None


class ConvertRunnable(QRunnable):
    """Runnable class for conversion tasks"""

    def __init__(self, script_path, console_window, single_exe_file, output_dir, exe_name, icon_path, file_version,
                 copyright_info, extra_library, additional_options, python_path):
        super().__init__()
        self.script_path = script_path
        self.console_window = console_window
        self.single_exe_file = single_exe_file
        self.output_dir = output_dir
        self.exe_name = exe_name
        self.icon_path = icon_path
        self.file_version = file_version
        self.copyright_info = copyright_info
        self.extra_library = extra_library
        self.additional_options = additional_options
        self.python_path = python_path
        self.signals = WorkerSignals()
        self._is_running = True

    def get_dir_size(self, path='.'):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_dir_size(entry.path)
        return total

    def run(self):
        version_file_path = None
        try:
            script_dir = os.path.dirname(self.script_path)
            exe_name = self.exe_name or os.path.splitext(os.path.basename(self.script_path))[0]
            output_dir = self.output_dir or script_dir

            if not self.ensure_pyinstaller():
                return

            options = self.prepare_pyinstaller_options(exe_name, output_dir)
            if self.icon_path:
                icon_file = self.handle_icon(script_dir)
                if icon_file:
                    options.append(f'--icon={icon_file}')

            if self.file_version or self.copyright_info:
                version_file_path = self.create_version_file(exe_name, script_dir)
                if version_file_path:
                    options.append(f'--version-file={version_file_path}')

            self.update_status("Start converting...")
            success = self.run_pyinstaller(options)
            self._is_running = False
            if success:
                exe_path = [os.path.join(output_dir, exe_name + '.exe')
                            if self.single_exe_file
                            else os.path.join(output_dir, exe_name, exe_name + '.exe')][0]
                if os.path.exists(exe_path):
                    exe_size = [os.path.getsize(exe_path)
                                if self.single_exe_file
                                else self.get_dir_size(os.path.dirname(exe_path))]
                    exe_size = exe_size[0] // 1048576
                    self.signals.conversion_finished.emit(exe_path, exe_size)
                else:
                    error_message = "Conversion completed, but the resulting EXE file was not found."
                    self.update_status(error_message)
                    self.signals.conversion_failed.emit(error_message)
            else:
                error_message = "Conversion failed, please see the error message above."
                self.update_status(error_message)
                self.signals.conversion_failed.emit(error_message)
        except Exception as e:
            error_message = f"Exception occurred during conversion : {e}"
            self.update_status(error_message)
            self.signals.conversion_failed.emit(error_message)
        finally:
            self._is_running = False
            self.cleanup_files(version_file_path)

    def stop(self):
        """Stop the conversion task"""
        self._is_running = False

    def update_status(self, message: str):
        """Update conversion status"""
        logging.info(message)
        self.signals.status_updated.emit(message)

    def ensure_pyinstaller(self) -> bool:
        """Make sure PyInstaller is installed"""
        path = self.python_path
        if not path:
            path = sys.executable
        try:
            subprocess.run([path, '-m', 'PyInstaller', '--version'],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            self.update_status("PyInstaller detected.")
            return True
        except subprocess.CalledProcessError:
            self.update_status("PyInstaller not detected, trying to install...")
            try:
                subprocess.check_call([path, "-m", "pip", "install", "pyinstaller"], shell=True)
                self.update_status("PyInstaller was installed successfully.")
                return True
            except subprocess.CalledProcessError as e:
                self.update_status(f"Failed to install PyInstaller : {e}")
                return False

    def prepare_pyinstaller_options(self, exe_name: str, output_dir: str) -> list:
        """Prepare command line options for PyInstaller"""
        if self.single_exe_file:
            options = ['--onefile', '--clean']
        else:
            options = ['--onedir', '--clean']
        options += ['--console' if self.console_window else '--windowed']

        if self.extra_library:
            hidden_imports = [lib.strip() for lib in self.extra_library.split(',') if lib.strip()]
            options += [f'--hidden-import={lib}' for lib in hidden_imports]

        if self.additional_options:
            options += self.additional_options.strip().split()

        options += ['--distpath', output_dir, '-n', exe_name]
        return options

    def handle_icon(self, script_dir: str) -> str:
        """Process icon files, support converting PNG to ICO"""
        if not Image:
            self.update_status(
                "Pillow library is not installed and cannot convert PNG icons. Please install Pillow or use the ICO icon.")
            return ""

        lower_icon = self.icon_path.lower()
        if lower_icon.endswith('.png'):
            self.update_status("PNG icon detected, converting to ICO format...")
            try:
                img = Image.open(self.icon_path)
                ico_path = os.path.join(script_dir, 'icon_converted.ico')
                img.save(ico_path, format='ICO',
                         sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                self.update_status("The icon conversion was successful.")
                return ico_path
            except Exception as e:
                self.update_status(f"PNG to ICO failed: {e}")
                return ""
        elif lower_icon.endswith('.ico'):
            return self.icon_path
        else:
            self.update_status("Unsupported icon format, only .png and .ico formats are supported.")
            return ""

    def create_version_file(self, exe_name: str, script_dir: str) -> str:
        """Create version information file"""
        try:
            from PyInstaller.utils.win32.versionfile import (
                VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
            )
        except ImportError as e:
            self.update_status(f"Failed to import version information class: {e}")
            return ""

        version_numbers = self.file_version.split('.') if self.file_version else ['1', '0', '0', '0']
        if len(version_numbers) != 4 or not all(num.isdigit() for num in version_numbers):
            version_numbers = ['1', '0', '0', '0']

        version_info = VSVersionInfo(
            ffi=FixedFileInfo(
                filevers=tuple(map(int, version_numbers)),
                prodvers=tuple(map(int, version_numbers)),
                mask=0x3f,
                flags=0x0,
                OS=0x40004,
                fileType=0x1,
                subtype=0x0,
                date=(0, 0)
            ),
            kids=[
                StringFileInfo(
                    [
                        StringTable(
                            '040904E4',
                            [
                                StringStruct('CompanyName', ''),
                                StringStruct('FileDescription', exe_name),
                                StringStruct('FileVersion', '.'.join(version_numbers)),
                                StringStruct('InternalName', f'{exe_name}.exe'),
                                StringStruct('LegalCopyright', self.copyright_info),
                                StringStruct('OriginalFilename', f'{exe_name}.exe'),
                                StringStruct('ProductName', exe_name),
                                StringStruct('ProductVersion', '.'.join(version_numbers))
                            ]
                        )
                    ]
                ),
                VarFileInfo([VarStruct('Translation', [0x0409, 0x04B0])])
            ]
        )

        version_file_path = os.path.join(script_dir, 'version_info.txt')
        try:
            with open(version_file_path, 'w', encoding='utf-8') as vf:
                vf.write(version_info.__str__())
            self.update_status("Generate version information file.")
            return version_file_path
        except Exception as e:
            self.update_status(f"Failed to generate version information file: {e}")
            return ""

    def run_pyinstaller(self, options: list) -> bool:
        """Run PyInstaller to convert"""
        path = self.python_path
        if not path:
            path = sys.executable
        cmd = [path, '-m', 'PyInstaller'] + options + [self.script_path]
        self.update_status(f"Execute Command: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True
            )

            for line in process.stdout:
                if not self._is_running:
                    process.terminate()
                    self.update_status("Conversion canceled by user.")
                    return False
                line = line.strip()
                self.update_status(line)
                # Simple progress estimate
                if "Analyzing" in line:
                    self.signals.progress_updated.emit(30)
                elif "Collecting" in line:
                    self.signals.progress_updated.emit(50)
                elif "Building" in line:
                    self.signals.progress_updated.emit(70)
                elif "completed successfully" in line.lower():
                    self.signals.progress_updated.emit(100)

            process.stdout.close()
            process.wait()

            return process.returncode == 0
        except Exception as e:
            self.update_status(f"Exception occurred during conversion: {e}")
            return False

    def cleanup_files(self, version_file_path: str):
        """Clean temporary files"""
        script_dir = os.path.dirname(self.script_path)
        if version_file_path and os.path.exists(version_file_path):
            try:
                os.remove(version_file_path)
                self.update_status("Delete the version information file.")
            except Exception as e:
                self.update_status(f"Unable to delete version information file: {e}")

        if self.icon_path and self.icon_path.lower().endswith('.png'):
            ico_path = os.path.join(script_dir, 'icon_converted.ico')
            if os.path.exists(ico_path):
                try:
                    os.remove(ico_path)
                    self.update_status("Delete temporary ICO files.")
                except Exception as e:
                    self.update_status(f"Unable to delete temporary ICO file: {e}")
