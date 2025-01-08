# PythonEXE Maker

![logo](./Icons/logo.png)

**PythonEXE Maker** is an open-source and free tool designed to convert Python scripts into standalone executable files (EXE). It provides a user-friendly graphical interface to configure conversion parameters, manage multiple tasks, and customize properties like icons, version information, and more.

---

## Features

- **Drag and Drop Support**: Quickly add `.py` files to the program via drag and drop.
- **Batch Conversion**: Convert multiple Python scripts into EXE files simultaneously.
- **Custom Settings**:
  - Console window visibility.
  - Single file or directory-based output.
  - Specify output directory and EXE file name.
  - Add custom icons (`.png` or `.ico` formats supported).
  - Set EXE file version and copyright information.
  - Add hidden import modules and additional PyInstaller parameters.
- **Task Management**: Track progress and status of conversion tasks.
- **Log Viewing**: Troubleshoot with detailed logs.
- **Dependency Check**: Automatically ensure required libraries are installed at startup.

---

## Screenshots

### Main Interface
![image](./Screenshots/MainInterface.png)

### Log View
![image](./Screenshots/LogView.png)

---

## Installation

### Prerequisites
- **Operating System**: Windows
- **Python Version**: 3.6 and above
- **Dependencies**:
  - [PyQt5](https://pypi.org/project/PyQt5/)
  - [Pillow](https://pypi.org/project/Pillow/)
  - [PyInstaller](https://pypi.org/project/PyInstaller/)

### Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/chetanjain2099/Python-exe-maker.git
   cd Python-exe-maker
   ```
2. **Create a virtual environment (optional)**

    ```bash
    python -m venv venv
    source venv/bin/activate # For Windows users, use venv\Scripts\activate
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

    *If there is no `requirements.txt` file, please install the dependencies manually:*

    ```bash
    pip install pyside6-essentials Pillow PyInstaller
    ```

## Instructions

1. **Run the program**

    ```bash
    python PythonEXE_Maker.py
    ```
2. **Configure conversion parameters**

   - **Console Window**: Select whether the generated EXE is with a console (command line mode) or without a console.
   - 
   - **Single File**: Select whether the generated EXE is a single file or a single directory.

   - **Output directory**: Specify the storage location of the generated EXE file, which defaults to the directory where the source file is located.

   - **EXE information**:

     - **EXE name**: Set the name of the generated EXE file, which defaults to the same name as the source file.

     - **Icon file**: Select an icon file for EXE, supporting `.png` and `.ico` formats.

     - **File version**: Set the version number of the EXE file (format: X.X.X.X).
     - **Copyright information**: Set the copyright information of the EXE file.
   
   - **Advanced settings**:
     - **Additional modules**: Enter the module names that need to be hidden import. Multiple modules are separated by commas.
     - **Additional arguments**: Enter additional command line arguments for PyInstaller.
   
   - **Additional Directory**: Specify the source and destination location of the directory to be included in the folder.

3. **Add conversion task**

   - **Drag and drop files**: Drag the `.py` file directly into the drag and drop area of the program window.
   - **Browse files**: Click the "Browse files" button to select the Python script to be converted.

4. **Start conversion**

   - Click the "Start Convert" button and the program will start converting the selected Python script.
   - During the conversion process, you can view the progress and status of each task in the "Task Management" tab.
   - The Conversion logs can be viewed in detail in the "Log" tab.

5. **Cancel conversion**

   - During the conversion process, you can click the "Cancel Conversion" button to stop all ongoing conversion tasks.

## Contribution
Contributions are welcome! You can:

- **Submit Issues**: Report bugs or suggest new features.
- **Create Pull Requests**: Fork this repository, make changes, and submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](/LICENSE) file for more details.

## Acknowledgments
This project is based on the original repository by [yeahhe365](https://github.com/yeahhe365/PythonEXE_Maker). Additional options and improvements have been made in this fork to enhance functionality and usability.
