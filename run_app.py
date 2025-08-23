#!/usr/bin/env python3
"""
AT&T Fiber Tracker - Main Application
"""

# Apply fixes for warnings and threading issues
import warnings
import os

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub.utils")
warnings.filterwarnings("ignore", category=UserWarning, module="PySide6.QtCore")
warnings.filterwarnings("ignore", message="QThread: Destroyed while thread.*is still running")

# Set environment variables
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

# Setup ffmpeg
try:
    import subprocess
    result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
    if result.returncode == 0:
        os.environ['FFMPEG_BINARY'] = result.stdout.strip()
except:
    pass

import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set environment variables for GUI
os.environ['QT_MAC_WANTS_LAYER'] = '1'

# Now import and run the main application
if __name__ == "__main__":
    try:
        # Import the main window
        from main_window import MainWindow
        from PySide6.QtWidgets import QApplication
        
        # Create the application
        app = QApplication(sys.argv)
        
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Run the application
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install PySide6 pandas requests Pillow")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

