from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGroupBox, QTextEdit, QProgressBar, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime

class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AT&T Fiber Tracker - Main Dashboard")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Status group
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout()
        
        self.status_labels = {}
        status_items = [
            ("AT&T Service", "Ready"),
            ("ADT Detection", "Ready"),
            ("Mailchimp", "Ready"),
            ("Data Processing", "Ready")
        ]
        
        for i, (name, status) in enumerate(status_items):
            status_layout.addWidget(QLabel(f"{name}:"), i, 0)
            self.status_labels[name] = QLabel(status)
            self.status_labels[name].setStyleSheet("color: green; font-weight: bold;")
            status_layout.addWidget(self.status_labels[name], i, 1)
            
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        self.check_fiber_btn = QPushButton("Check AT&T Fiber")
        self.check_fiber_btn.clicked.connect(self.check_fiber)
        actions_layout.addWidget(self.check_fiber_btn)
        
        self.process_adt_btn = QPushButton("Process ADT Data")
        self.process_adt_btn.clicked.connect(self.process_adt)
        actions_layout.addWidget(self.process_adt_btn)
        
        self.export_data_btn = QPushButton("Export Data")
        self.export_data_btn.clicked.connect(self.export_data)
        actions_layout.addWidget(self.export_data_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Progress section
        progress_group = QGroupBox("Current Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("No active operations")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log section
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Add some initial log entries
        self.append_log("System initialized successfully")
        self.append_log("Ready to process AT&T Fiber data")
        
        self.setLayout(layout)
        
        # Timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
    def check_fiber(self):
        self.append_log("Starting AT&T Fiber availability check...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Checking AT&T Fiber availability...")
        
        # Simulate progress
        self.progress_bar.setValue(50)
        self.append_log("AT&T Fiber check in progress...")
        
    def process_adt(self):
        self.append_log("Starting ADT data processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Processing ADT detection data...")
        
        # Simulate progress
        self.progress_bar.setValue(75)
        self.append_log("ADT data processing in progress...")
        
    def export_data(self):
        self.append_log("Starting data export...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Exporting data...")
        
        # Simulate progress
        self.progress_bar.setValue(100)
        self.append_log("Data export completed")
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Export completed")
        
    def update_status(self):
        # Update status indicators based on system state
        current_time = datetime.now().strftime("%H:%M:%S")
        self.append_log(f"Status check at {current_time}")
        
    def append_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        ) 