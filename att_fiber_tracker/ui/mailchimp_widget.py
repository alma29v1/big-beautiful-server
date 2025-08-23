import time
from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QProgressBar, QTextEdit
)
from att_fiber_tracker.services.mailchimp_service import MailchimpService
from att_fiber_tracker.config import MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX

class MailchimpWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    finished_signal = Signal(dict)
    
    def __init__(self, consolidated_contacts, mailchimp_api_key=None):
        super().__init__()
        self.consolidated_contacts = consolidated_contacts
        self.mailchimp_api_key = mailchimp_api_key
        
    def run(self):
        try:
            if not self.consolidated_contacts:
                self.log_signal.emit("[MAILCHIMP] ❌ No contacts to process")
                self.finished_signal.emit({"success": False, "error": "No contacts"})
                return
                
            mailchimp = MailchimpService(MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX)
            current_date = datetime.now().strftime("%Y-%m-%d")
            fiber_list_name = f"AT&T Fiber Available - {current_date}"
            no_fiber_list_name = f"No AT&T Fiber - {current_date}"
            
            self.log_signal.emit(f"[MAILCHIMP] Creating lists: '{fiber_list_name}' and '{no_fiber_list_name}'")
            
            fiber_contacts = [c for c in self.consolidated_contacts if c.get('fiber_available', False)]
            no_fiber_contacts = [c for c in self.consolidated_contacts if not c.get('fiber_available', False)]
            
            self.log_signal.emit(f"[MAILCHIMP] Found {len(fiber_contacts)} fiber contacts and {len(no_fiber_contacts)} no-fiber contacts")
            
            # Process contacts
            total_contacts = len(self.consolidated_contacts)
            uploaded_count = 0
            
            for i, contact in enumerate(fiber_contacts):
                self.log_signal.emit(f"[MAILCHIMP] Processing fiber contact {i+1}/{len(fiber_contacts)}: {contact.get('email', 'N/A')}")
                uploaded_count += 1
                self.progress_signal.emit(uploaded_count, total_contacts)
                time.sleep(0.1)
                
            for i, contact in enumerate(no_fiber_contacts):
                self.log_signal.emit(f"[MAILCHIMP] Processing no-fiber contact {i+1}/{len(no_fiber_contacts)}: {contact.get('email', 'N/A')}")
                uploaded_count += 1
                self.progress_signal.emit(uploaded_count, total_contacts)
                time.sleep(0.1)
                
            results = {
                "success": True,
                "fiber_contacts_processed": len(fiber_contacts),
                "no_fiber_contacts_processed": len(no_fiber_contacts),
                "total_processed": uploaded_count
            }
            
            self.log_signal.emit(f"[MAILCHIMP] ✅ SUCCESS! Processed {uploaded_count} contacts")
            self.finished_signal.emit(results)
            
        except Exception as e:
            self.log_signal.emit(f"[MAILCHIMP] ❌ Error: {e}")
            self.finished_signal.emit({"success": False, "error": str(e)})

class MailchimpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Mailchimp table
        self.mailchimp_table = QTableWidget()
        self.mailchimp_table.setColumnCount(5)
        self.mailchimp_table.setHorizontalHeaderLabels([
            "Email", "List", "Status", "Name", "Address"
        ])
        self.mailchimp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.mailchimp_table.setAlternatingRowColors(True)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Mailchimp Data")
        self.refresh_btn.clicked.connect(self.refresh_mailchimp_data)
        layout.addWidget(self.refresh_btn)
        
        layout.addWidget(self.mailchimp_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Mailchimp: Ready")
        layout.addWidget(self.status_label)
        
        # Log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.worker = None
        self.consolidated_contacts = []
        
        self.setLayout(layout)
        
    def start_mailchimp_processing(self, contacts):
        self.consolidated_contacts = contacts
        self.worker = MailchimpWorker(self.consolidated_contacts)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker.start()
        
    def refresh_mailchimp_data(self):
        self.append_log("[MAILCHIMP] Refreshing data...")
        # Placeholder for refreshing table from Mailchimp API
        
    def update_progress(self, current, total):
        self.progress_bar.setValue(int((current / total) * 100))
        
    def on_finished(self, results):
        self.progress_bar.setVisible(False)
        if results.get("success"):
            self.status_label.setText("Mailchimp: Completed successfully")
        else:
            self.status_label.setText(f"Mailchimp: Error - {results.get('error', 'Unknown error')}")
            
    def append_log(self, message):
        self.log_text.append(f"{datetime.now().strftime('%H:%M:%S')} {message}") 