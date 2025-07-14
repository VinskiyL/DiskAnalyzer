import os
import shutil
from PySide6.QtWidgets import QDialog, QMessageBox, QFileSystemModel, QTreeView
from PySide6.QtCore import Qt, Signal, QTimer, QSortFilterProxyModel
from ui_dialog import Ui_Dialog
from ThreadCalculator import ThreadCalculator

class ProxyModel(QSortFilterProxyModel):
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

            if os.path.isdir(path) or os.path.islink(path):
                if path in self.size_cache:
                    return self.size_cache[path]
                else:
                    QTimer.singleShot(0, lambda p=path: self.calculator.add_task(p))
                    return "Вычисление..."

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

class DiskCleanupDialog(QDialog):
    dialog_finished = Signal()

    def __init__(self, drive_path, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.drive_path = drive_path
        self.setWindowTitle(f"Очистите диск {drive_path}")
        self.setModal(True)
        self.ui.pushButton.setEnabled(False)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.drive_path)
        self.file_model.setReadOnly(False)

        self.proxy_model = ProxyModel()
        self.proxy_model.setSourceModel(self.file_model)

        self.ui.treeView.setModel(self.proxy_model)
        self.ui.treeView.setRootIndex(
            self.proxy_model.mapFromSource(
                self.file_model.index(self.drive_path)
            )
        )
        self.ui.treeView.setColumnWidth(0, 300)
        self.ui.treeView.setSelectionMode(QTreeView.ExtendedSelection)

        self.ui.pushButton.clicked.connect(self.delete_selected)
        self.ui.treeView.selectionModel().selectionChanged.connect(
            self.update_selection_count)
        self.update_selection_count()

    def update_selection_count(self):
        selected = self.get_unique_selected_files()
        self.ui.label.setText(f"Выбрано элементов: {len(selected)}")
        self.ui.pushButton.setEnabled(bool(selected))

    def get_unique_selected_files(self):
        selected = self.ui.treeView.selectionModel().selectedIndexes()
        return {
            self.proxy_model.mapToSource(index).data(QFileSystemModel.FilePathRole)
            for index in selected
            if index.column() == 0
        }

    def delete_selected(self):
        selected_files = self.get_unique_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "Ошибка", "Ничего не выбрано для удаления")
            return

        total_size = self.calculate_total_size(selected_files)

        if not self.confirm_deletion(len(selected_files), total_size):
            return

        deleted_count, errors = self.perform_deletion(selected_files)
        self.handle_deletion_result(deleted_count, errors)

    def calculate_total_size(self, files):
        return sum(
            os.path.getsize(f) if os.path.isfile(f) else
            self.proxy_model.size_cache.get(f, 0)
            for f in files
        )

    def confirm_deletion(self, count, total_size):
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить {count} элементов?\n"
            f"Общий размер: {self.proxy_model.format_size(total_size)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def perform_deletion(self, files):
        errors = []
        deleted_count = 0

        for file_path in files:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        return deleted_count, errors

    def handle_deletion_result(self, deleted_count, errors):
        if errors:
            self.show_errors(errors)

        if deleted_count > 0:
            self.file_model.setRootPath(self.drive_path)
            QMessageBox.information(
                self, "Готово",
                f"Успешно удалено {deleted_count} элементов")
            self.update_selection_count()

    def show_errors(self, errors):
        error_msg = "\n".join(errors[:10])
        if len(errors) > 10:
            error_msg += f"\n\n...и ещё {len(errors)-10} ошибок"
        QMessageBox.critical(self, "Ошибки", f"Не удалось удалить:\n{error_msg}")

    def safe_stop_calculator(self):
        if hasattr(self.proxy_model, 'calculator'):
            self.proxy_model.calculator.stop(500)

    def closeEvent(self, event):
        self.safe_stop_calculator()
        self.dialog_finished.emit()
        super().closeEvent(event)
