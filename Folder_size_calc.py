import os
from PySide6.QtCore import QObject, Signal, QDir

class Folder_size_calc(QObject):
    calculated = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._active = True
        self._current_path = None

    def calculate_size(self, path):
        if not self._active or not path:
            return

        self._current_path = path
        try:
            total_size = 0

            real_path = os.path.realpath(path) if os.path.islink(path) else path

            for dirpath, _, filenames in os.walk(real_path):
                if not self._active or self._current_path != path:
                    return
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        continue

            if self._active and self._current_path == path:
                self.calculated.emit(path, self.format_size(total_size))
        except Exception as e:
            print(f"Ошибка при расчете размера для {path}: {str(e)}")
            self.calculated.emit(path, "Ошибка")

    def format_size(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} PB"

    def stop(self):
        self._active = False
        self._current_path = None
