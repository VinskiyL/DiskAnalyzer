import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QMessageBox
from PySide6.QtCore import QDir, Qt, QSortFilterProxyModel
from ui_form import Ui_MainWindow
import psutil

class DriveInfoProxyModel(QSortFilterProxyModel):
    def __init__(self, drives=None, parent=None):
        super().__init__(parent)
        self.drives = drives or []

    def data(self, index, role=Qt.DisplayRole):
        if index.column() == 1 and role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            path = self.sourceModel().filePath(source_index)

            if path in self.drives:
                try:
                    usage = psutil.disk_usage(path)
                    used = self.format_size(usage.used)
                    total = self.format_size(usage.total)
                    return f"Использовано {used}/{total}({usage.percent}%)"
                except Exception:
                    return "Ошибка"

        return super().data(index, role)

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags &= ~Qt.ItemIsUserCheckable
        return flags

    def format_size(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} PB"

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.drives = self.load_drives()

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        self.proxy_model = DriveInfoProxyModel(self.drives)
        self.proxy_model.setSourceModel(self.file_model)

        self.ui.treeView.setModel(self.proxy_model)
        self.ui.treeView.clicked.connect(self.on_item_clicked)

        self.ui.treeView.setColumnWidth(1, 270)

    def load_drives(self):
        try:
            return [
                part.mountpoint for part in psutil.disk_partitions()
                if part.fstype
                and 'snap' not in part.mountpoint
                and (
                    part.mountpoint == '/' or
                    part.mountpoint.startswith('/mnt/') or
                    part.mountpoint.startswith('/media/')
                )
            ]
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить диски: {str(e)}")
            return []

    def on_item_clicked(self, index):
        path = self.file_model.filePath(index)
        self.statusBar().showMessage(f"Выбрано: {path}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
