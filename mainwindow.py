import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QMessageBox
from PySide6.QtCore import QDir
from ui_form import Ui_MainWindow
import psutil

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.ui.treeView.setModel(self.file_model)

        self.setup_ui()

        self.load_drives()

    def setup_ui(self):
        self.ui.treeView.clicked.connect(self.on_item_clicked)

    def load_drives(self):
        try:
            drives = [part.mountpoint for part in psutil.disk_partitions()
                     if part.fstype and 'snap' not in part.mountpoint]

            if not drives:
                QMessageBox.warning(self, "Ошибка", "Не удалось обнаружить диски")
                return

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить диски: {str(e)}")

    def on_item_clicked(self, index):
        path = self.file_model.filePath(index)
        self.statusBar().showMessage(f"Выбрано: {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
