from PySide6.QtCore import QThread, Signal

class ADTDetectionWorker(QThread):
    finished = Signal()
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        
    def run(self):
        """Placeholder implementation"""
        self.is_running = True
        try:
            # Placeholder logic
            self.progress.emit(50)
            self.progress.emit(100)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.is_running = False
            self.finished.emit()
