#!/usr/bin/env python3
"""
Simple AT&T Fiber Tracker - Working Demo Version
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QGroupBox, QProgressBar,
    QLineEdit, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
import pandas as pd
import requests
import time
from datetime import datetime

class ATTWorker(QThread):
    """Worker thread for AT&T Fiber checking"""
    progress = Signal(int)
    result = Signal(str)
    finished = Signal()
    
    def __init__(self, addresses):
        super().__init__()
        self.addresses = addresses
        
    def run(self):
        """Simulate AT&T Fiber checking"""
        total = len(self.addresses)
        for i, address in enumerate(self.addresses):
            # Simulate checking fiber availability
            time.sleep(0.5)  # Simulate API call
            result = f"Address: {address} - Fiber: {'Available' if i % 3 == 0 else 'Not Available'}"
            self.result.emit(result)
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit()

class SimpleATTFiberTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AT&T Fiber Tracker - Simple Demo")
        self.setGeometry(100, 100, 800, 600)
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("AT&T Fiber Tracker - Simple Demo")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px; background: #ecf0f1; border-radius: 5px;")
        layout.addWidget(title)
        
        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Main Tab
        main_tab = self.create_main_tab()
        tabs.addTab(main_tab, "Fiber Checker")
        
        # About Tab
        about_tab = self.create_about_tab()
        tabs.addTab(about_tab, "About")
        
    def create_main_tab(self):
        """Create the main fiber checking tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input section
        input_group = QGroupBox("Address Input")
        input_layout = QVBoxLayout(input_group)
        
        # Address input
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter addresses (one per line):\n123 Main St, Wilmington, NC\n456 Oak Ave, Leland, NC\n789 Pine Rd, Southport, NC")
        self.address_input.setMaximumHeight(100)
        input_layout.addWidget(self.address_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Check Fiber Availability")
        self.check_button.clicked.connect(self.start_fiber_check)
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.clear_button)
        input_layout.addLayout(button_layout)
        
        layout.addWidget(input_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        return widget
    
    def create_about_tab(self):
        """Create the about tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        about_text = """
        <h2>AT&T Fiber Tracker - Simple Demo</h2>
        
        <p>This is a simplified version of the comprehensive AT&T Fiber tracking system.</p>
        
        <h3>Features:</h3>
        <ul>
            <li>Batch address processing</li>
            <li>Fiber availability checking</li>
            <li>Results display</li>
            <li>Progress tracking</li>
        </ul>
        
        <h3>How to use:</h3>
        <ol>
            <li>Enter addresses in the input field (one per line)</li>
            <li>Click "Check Fiber Availability"</li>
            <li>Watch the progress bar</li>
            <li>View results in the results section</li>
        </ol>
        
        <p><strong>Note:</strong> This demo simulates the fiber checking process. In the full version, 
        it would make actual API calls to AT&T's systems.</p>
        
        <p><em>Created as a working demo of the AT&T Fiber Tracker system.</em></p>
        """
        
        about_label = QLabel(about_text)
        about_label.setWordWrap(True)
        about_label.setStyleSheet("padding: 20px; font-size: 14px;")
        layout.addWidget(about_label)
        
        return widget
    
    def start_fiber_check(self):
        """Start the fiber availability check"""
        addresses_text = self.address_input.toPlainText().strip()
        if not addresses_text:
            QMessageBox.warning(self, "Warning", "Please enter at least one address.")
            return
        
        addresses = [addr.strip() for addr in addresses_text.split('\n') if addr.strip()]
        
        # Disable button and show progress
        self.check_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        
        # Start worker thread
        self.worker = ATTWorker(addresses)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.result.connect(self.add_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def add_result(self, result):
        """Add a result to the results display"""
        current_text = self.results_text.toPlainText()
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_result = f"[{timestamp}] {result}\n"
        self.results_text.setPlainText(current_text + new_result)
        
        # Auto-scroll to bottom
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_finished(self):
        """Called when the worker thread finishes"""
        self.check_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.add_result("=== Fiber check completed ===")
    
    def clear_results(self):
        """Clear the results display"""
        self.results_text.clear()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = SimpleATTFiberTracker()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
