#!/usr/bin/env python3
"""
AT&T Fiber Tracker - Main GUI Application
Fixed version that actually works
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    """Main entry point"""
    print("🚀 Starting AT&T Fiber Tracker...")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AT&T Fiber Tracker")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    print("✅ AT&T Fiber Tracker initialized successfully!")
    print("Ready to process Redfin data, check AT&T fiber availability, and run ADT detection.")
    
    # Run the application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
