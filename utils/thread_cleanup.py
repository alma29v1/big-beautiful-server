
import threading
import atexit
import signal
import sys

def cleanup_threads():
    """Clean up any remaining threads on exit"""
    try:
        # Get all active threads
        active_threads = threading.enumerate()
        main_thread = threading.main_thread()
        
        # Wait for non-main threads to finish
        for thread in active_threads:
            if thread != main_thread and thread.is_alive():
                try:
                    thread.join(timeout=1.0)
                except:
                    pass
    except:
        pass

def signal_handler(signum, frame):
    """Handle system signals gracefully"""
    cleanup_threads()
    sys.exit(0)

# Register cleanup functions
atexit.register(cleanup_threads)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("✅ Thread cleanup handlers installed")
