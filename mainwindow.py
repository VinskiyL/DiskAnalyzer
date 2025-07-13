import os
import sys
import psutil
import shutil
from PySide6.QtCore import QThread, Signal, QObject, Qt, QDir, QTimer, QSortFilterProxyModel
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileSystemModel, QMessageBox,
                              QVBoxLayout, QInputDialog)
from ui_form import Ui_MainWindow
from Folder_size_calc import Folder_size_calc
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtGui import QPainter, QColor

class DiskUsageChart(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle("Использование дисков")
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        self.series = QPieSeries()
        self.chart.addSeries(self.series)
        self.chart.legend().setVisible(True)

    def update_chart(self, drives):
        self.series.clear()

        for drive in drives:
            try:
                usage = psutil.disk_usage(drive)
                slice_ = self.series.append(f"{drive} ({usage.percent}%)", usage.percent)

                red = min(255, int(255 * (usage.percent / 100)))
                green = max(0, int(255 * (1 - usage.percent / 100)))
                slice_.setColor(QColor(red, green, 0))

                slice_.setLabelVisible(True)

            except Exception as e:
                print(f"Ошибка обновления диаграммы для {drive}: {e}")

class ThreadCalculator(QThread):
    task_added = Signal(str)

    def __init__(self):
        super().__init__()
        self.worker = Folder_size_calc()
        self.worker.moveToThread(self)
        self.task_added.connect(self.worker.calculate_size)
        self.start()

    def add_task(self, path):
        self.task_added.emit(path)

    def stop(self):
        self.worker.stop()
        self.quit()
        self.wait()

class DriveInfoProxyModel(QSortFilterProxyModel):
    def __init__(self, drives=None, parent=None):
        super().__init__(parent)
        self.drives = drives or []
        self.size_cache = {}
        self.calculator = ThreadCalculator()
        self.calculator.worker.calculated.connect(self.update_size)

    def data(self, index, role=Qt.DisplayRole):
        if index.column() == 1 and role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            path = self.sourceModel().filePath(source_index)

            if path in self.drives:
                try:
                    usage = psutil.disk_usage(path)
                    used = self.format_size(usage.used)
                    total = self.format_size(usage.total)


                    return f"Используется {used}/{total}({usage.percent}%)"
                except Exception:
                    return "Ошибка"

            if os.path.isdir(path) or os.path.islink(path):
                if path in self.size_cache:
                    return self.size_cache[path]
                else:
                    QTimer.singleShot(0, lambda p=path: self.calculator.add_task(p))
                    return "Вычисление..."

        if role == Qt.BackgroundRole and index.column() == 0:
            source_index = self.mapToSource(index)
            path = self.sourceModel().filePath(source_index)

            if path in self.drives:
                try:
                    usage = psutil.disk_usage(path)

                    red = min(255, int(255 * (usage.percent / 100)))
                    green = max(0, int(255 * (1 - usage.percent / 100)))
                    return QColor(red, green, 0)
                except Exception:
                    return None

        return super().data(index, role)

    def update_size(self, path, size):
        if path not in self.size_cache or self.size_cache[path] != size:
            self.size_cache[path] = size
            root_index = self.sourceModel().index(path)
            if root_index.isValid():
                proxy_index = self.mapFromSource(root_index)
                if proxy_index.isValid():
                    self.dataChanged.emit(proxy_index, proxy_index, [Qt.DisplayRole])

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
        self.file_model.setReadOnly(False)

        self.proxy_model = DriveInfoProxyModel(self.drives)
        self.proxy_model.setSourceModel(self.file_model)

        self.ui.treeView.setModel(self.proxy_model)

        self.show_drives()

        self.ui.treeView.clicked.connect(self.on_item_clicked)
        self.ui.treeView.setColumnWidth(1, 270)

        self.setup_chart()
        self.update_chart()

        self.current_selection = None
        self.ui.treeView.selectionModel().selectionChanged.connect(self.update_delete_button_state)
        self.ui.deleteButton.clicked.connect(self.delete_selected_item)
        self.ui.deleteButton.setEnabled(False)

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

    def show_drives(self):
        root_index = self.proxy_model.mapFromSource(self.file_model.index(""))
        self.ui.treeView.setRootIndex(root_index)

    def on_item_clicked(self, index):
        path = self.file_model.filePath(self.proxy_model.mapToSource(index))
        self.statusBar().showMessage(f"Выбрано: {path}")
        self.current_selection = path

    def closeEvent(self, event):
        self.proxy_model.calculator.stop()
        super().closeEvent(event)

    def setup_chart(self):
        self.chart_view = DiskUsageChart()
        layout = self.ui.graphicsView.layout() or QVBoxLayout()
        layout.addWidget(self.chart_view)
        self.ui.graphicsView.setLayout(layout)

    def update_chart(self):
        if hasattr(self, 'chart_view'):
            self.chart_view.update_chart(self.drives)

    def update_delete_button_state(self):
        selected = self.ui.treeView.selectionModel().selectedIndexes()
        self.ui.deleteButton.setEnabled(len(selected) > 0)

    def delete_selected_item(self):
        if not self.current_selection:
            return

        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Вы уверены, что хотите удалить "{os.path.basename(self.current_selection)}"?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(self.current_selection):
                    shutil.rmtree(self.current_selection)
                else:
                    os.remove(self.current_selection)

                    parent_dir = os.path.dirname(self.current_selection)
                    parent_index = self.file_model.index(parent_dir)

                    self.file_model.setRootPath("")

                QMessageBox.information(self, "Успех", "Удаление завершено успешно")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
