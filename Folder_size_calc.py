from PySide6.QtCore import QObject, Signal, QDir

class Folder_size_calc(QObject):
    progress = Signal(str, int)
    finish = Signal(str, int)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False

    def calculate(self, path):
        if self._is_running:
            self.error.emit("Расчет уже выполняется")
            return

        self._is_running = True
        try:
            total = self._calculate_rec(path)
            self.finish.emit(path, total)
        except Exception as e:
            self.error.emit(f"Ошибка расчета: {str(e)}")
        finally:
            self._is_running = False

    def _calculate_rec(self, path):
        total = 0
        dir_iterator = QDir(path).entryInfoList(
            QDir.Files | QDir.Dirs | QDir.NoDotAndDotDot,
            QDir.Name | QDir.IgnoreCase
        )

        for d in dir_iterator:
            if not self._is_running:
                break

            if d.isDir():
                dir_size = self._calculate_rec(d.filePath())
                total += dir_size
            else:
                total += d.size()

            if dir_iterator.index(d) % 10 == 0:
                self.progress.emit(d.filePath(), total)

        return total

    def cancel(self):
        self._is_running = False
