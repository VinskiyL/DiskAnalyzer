from PySide6.QtCore import QThread, Signal
from Folder_size_calc import Folder_size_calc

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

    def stop(self, timeout=None):
        self.worker.stop()
        self.quit()
        if not self.wait(timeout if timeout is not None else 1000):
            self.terminate()

