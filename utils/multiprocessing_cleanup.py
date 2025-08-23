
import multiprocessing
import atexit

def cleanup_multiprocessing():
    """Clean up multiprocessing resources"""
    try:
        # Clean up any remaining processes
        for process in multiprocessing.active_children():
            try:
                process.terminate()
                process.join(timeout=1.0)
            except:
                pass
    except:
        pass

# Register cleanup
atexit.register(cleanup_multiprocessing)
print("✅ Multiprocessing cleanup installed")
