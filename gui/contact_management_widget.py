import os
import json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QProgressBar, QGroupBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from utils.contact_manager import ContactManager

class ContactManagementWidget(QWidget):
    """Widget for managing persistent contact storage"""
    
    def __init__(self):
        super().__init__()
        self.contact_manager = ContactManager()
        self.init_ui()
        self.refresh_data()
        
        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30 seconds
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📧 Contact Storage Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Statistics Group
        stats_group = QGroupBox("📊 Contact Statistics")
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0")
        self.pending_label = QLabel("Pending: 0")
        self.sent_label = QLabel("Sent: 0")
        self.percentage_label = QLabel("Sent %: 0%")
        
        for label in [self.total_label, self.pending_label, self.sent_label, self.percentage_label]:
            label.setStyleSheet("font-size: 14px; padding: 5px; background: #f0f0f0; border-radius: 5px;")
            stats_layout.addWidget(label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Progress bar for sent percentage
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        self.export_btn = QPushButton("📤 Export to CSV")
        self.export_btn.clicked.connect(self.export_contacts)
        
        self.clear_sent_btn = QPushButton("🗑️ Clear Sent Contacts")
        self.clear_sent_btn.clicked.connect(self.clear_sent_contacts)
        
        self.delete_all_btn = QPushButton("⚠️ Delete All")
        self.delete_all_btn.clicked.connect(self.delete_all_contacts)
        self.delete_all_btn.setStyleSheet("background-color: #ff4444; color: white;")
        
        for btn in [self.refresh_btn, self.export_btn, self.clear_sent_btn, self.delete_all_btn]:
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        
        # Contacts table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Email", "Phone", "Address", "Status", "Date Added"
        ])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Phone
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Address
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Date
        
        layout.addWidget(self.table)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh the contact data and update the UI"""
        try:
            # Get statistics
            stats = self.contact_manager.get_statistics()
            
            self.total_label.setText(f"Total: {stats['total_contacts']}")
            self.pending_label.setText(f"Pending: {stats['pending_contacts']}")
            self.sent_label.setText(f"Sent: {stats['sent_contacts']}")
            self.percentage_label.setText(f"Sent %: {stats['sent_percentage']:.1f}%")
            
            # Update progress bar
            self.progress_bar.setValue(int(stats['sent_percentage']))
            
            # Update table
            self.populate_table()
            
            self.log_status(f"✅ Data refreshed at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.log_status(f"❌ Error refreshing data: {str(e)}")
    
    def populate_table(self):
        """Populate the contacts table"""
        try:
            contacts = self.contact_manager.get_all_contacts()
            self.table.setRowCount(len(contacts))
            
            for row, contact in enumerate(contacts):
                # Name
                name_item = QTableWidgetItem(contact.get('owner_name', 'N/A'))
                self.table.setItem(row, 0, name_item)
                
                # Email
                email_item = QTableWidgetItem(contact.get('owner_email', 'N/A'))
                self.table.setItem(row, 1, email_item)
                
                # Phone
                phone_item = QTableWidgetItem(contact.get('owner_phone', 'N/A'))
                self.table.setItem(row, 2, phone_item)
                
                # Address
                address_item = QTableWidgetItem(contact.get('address', 'N/A'))
                self.table.setItem(row, 3, address_item)
                
                # Status
                status = "✅ Sent" if contact.get('email_sent', False) else "⏳ Pending"
                status_item = QTableWidgetItem(status)
                if contact.get('email_sent', False):
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.yellow)
                self.table.setItem(row, 4, status_item)
                
                # Date added
                date_added = contact.get('date_added', 'Unknown')
                if date_added != 'Unknown':
                    try:
                        date_obj = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                        date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = date_added
                else:
                    date_str = 'Unknown'
                
                date_item = QTableWidgetItem(date_str)
                self.table.setItem(row, 5, date_item)
                
        except Exception as e:
            self.log_status(f"❌ Error populating table: {str(e)}")
    
    def export_contacts(self):
        """Export contacts to CSV file"""
        try:
            filename = self.contact_manager.export_to_csv()
            self.log_status(f"✅ Contacts exported to {filename}")
            QMessageBox.information(self, "Export Complete", f"Contacts exported to:\n{filename}")
        except Exception as e:
            self.log_status(f"❌ Error exporting contacts: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export contacts:\n{str(e)}")
    
    def clear_sent_contacts(self):
        """Clear all sent contacts"""
        try:
            reply = QMessageBox.question(
                self, "Clear Sent Contacts",
                "This will permanently remove all contacts that have been sent emails.\n\nThis action cannot be undone. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                removed_count = self.contact_manager.clear_sent_contacts()
                self.log_status(f"✅ Removed {removed_count} sent contacts")
                self.refresh_data()
                QMessageBox.information(self, "Clear Complete", f"Removed {removed_count} sent contacts")
        except Exception as e:
            self.log_status(f"❌ Error clearing sent contacts: {str(e)}")
            QMessageBox.critical(self, "Clear Error", f"Failed to clear sent contacts:\n{str(e)}")
    
    def delete_all_contacts(self):
        """Delete all contacts"""
        try:
            reply = QMessageBox.question(
                self, "Delete All Contacts",
                "⚠️ WARNING: This will permanently delete ALL contacts from storage.\n\nThis action cannot be undone. Are you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Double confirmation
                reply2 = QMessageBox.question(
                    self, "Final Confirmation",
                    "This is your final warning. All contact data will be permanently lost.\n\nType 'DELETE' to confirm:",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply2 == QMessageBox.Yes:
                    self.contact_manager.contacts = []
                    self.contact_manager.save_contacts()
                    self.log_status("🗑️ All contacts deleted")
                    self.refresh_data()
                    QMessageBox.information(self, "Delete Complete", "All contacts have been deleted")
        except Exception as e:
            self.log_status(f"❌ Error deleting contacts: {str(e)}")
            QMessageBox.critical(self, "Delete Error", f"Failed to delete contacts:\n{str(e)}")
    
    def log_status(self, message):
        """Add a status message to the log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum()) 