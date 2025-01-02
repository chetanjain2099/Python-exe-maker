import os
import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from GUI.UI import MainWindow

# import importlib

# if '_PYI_SPLASH_IPC' in os.environ and importlib.util.find_spec("pyi_splash"):
#     import pyi_splash
#     pyi_splash.close()

# Set up logging: output logs to file and console
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[
    logging.FileHandler("app.log", mode='w', encoding='utf-8'),
    logging.StreamHandler(sys.stdout)])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('windowsvista')
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set icon for the software
    icon_path = os.path.join(script_dir, 'Icons', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        logging.warning(f"Icon file not found: {icon_path}")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
