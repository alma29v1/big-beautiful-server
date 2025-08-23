
import atexit
import signal
import threading
import multiprocessing
import sys
from PySide6.QtCore import QThread

class ResourceManager:
    """Manages cleanup of threads and processes"""
    
    def __init__(self):
        self.workers = []
        self._shutdown = False
        
        # Register cleanup handlers
        atexit.register(self.cleanup_all)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def register_worker(self, worker):
        """Register a worker for cleanup"""
        if hasattr(worker, 'stop'):
            self.workers.append(worker)
    
    def cleanup_worker(self, worker):
        """Clean up a specific worker"""
        try:
            if hasattr(worker, 'stop'):
                worker.stop()
            elif hasattr(worker, 'quit'):
                worker.quit()
                worker.wait(1000)
        except Exception as e:
            print(f"Error cleaning up worker: {e}")
    
    def cleanup_all(self):
        """Clean up all registered workers"""
        if self._shutdown:
            return
        
        self._shutdown = True
        print("🧹 Cleaning up resources...")
        
        # Clean up registered workers
        for worker in self.workers:
            self.cleanup_worker(worker)
        
        # Clean up QThreads
        try:
            for thread in QThread.currentThread().findChildren(QThread):
                if thread != QThread.currentThread():
                    thread.quit()
                    thread.wait(1000)
        except:
            pass
        
        # Clean up multiprocessing
        try:
            for process in multiprocessing.active_children():
                process.terminate()
                process.join(timeout=1.0)
        except:
            pass
        
        # Clean up threading
        try:
            active_threads = threading.enumerate()
            main_thread = threading.main_thread()
            
            for thread in active_threads:
                if thread != main_thread and thread.is_alive():
                    try:
                        thread.join(timeout=1.0)
                    except:
                        pass
        except:
            pass
        
        print("✅ Resource cleanup complete")
    
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        print(f"Received signal {signum}, cleaning up...")
        self.cleanup_all()
        sys.exit(0)

# Global resource manager
resource_manager = ResourceManager()

def register_worker(worker):
    """Register a worker for cleanup"""
    resource_manager.register_worker(worker)

def cleanup_all():
    """Clean up all resources"""
    resource_manager.cleanup_all()

print("✅ Resource manager loaded")
