import sys
import os
from PySide6.QtWidgets import QApplication
from gui import MainWindow

def main():
    print("Starting App Engine...")
    
    # Try different DPI scaling settings that work better with Windows 
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    print("QApplication initialized.")
    
    window = MainWindow()
    print("Main window created. Showing...")
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
