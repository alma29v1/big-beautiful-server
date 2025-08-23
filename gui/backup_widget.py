"""
Backup Status and Control Widget
Shows backup status and provides manual backup controls
Configuration is managed in the main Settings tab
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from services.google_cloud_backup_service import GoogleCloudBackupService, BackupScheduler

class BackupWidget(QWidget):
    """Widget for monitoring backup status and running manual backups"""
    
    def __init__(self):
        super().__init__()
        self.backup_service = None
        self.backup_scheduler = None
        self.setup_ui()
        self.load_status()
        
        # Start automatic backup scheduler if enabled
        self.start_backup_scheduler()
    
    def setup_ui(self):
        """Setup the backup status and control UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("☁️ Google Cloud Backup Status")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 15px;
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Configuration status
        config_group = QGroupBox("⚙️ Configuration Status")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4285f4;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4285f4;
            }
        """)
        
        config_layout = QVBoxLayout()
        
        self.config_status_label = QLabel("⏳ Checking configuration...")
        self.config_status_label.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        config_layout.addWidget(self.config_status_label)
        
        # Settings link
        settings_note = QLabel("💡 Configure backup settings in the Settings tab")
        settings_note.setStyleSheet("""
            QLabel {
                background: #e7f3ff;
                color: #0066cc;
                padding: 8px;
                border-radius: 4px;
                font-style: italic;
            }
        """)
        config_layout.addWidget(settings_note)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Backup status section
        status_group = QGroupBox("📊 Backup Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34a853;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #34a853;
            }
        """)
        
        status_layout = QVBoxLayout()
        
        # Status indicators
        status_row = QHBoxLayout()
        
        self.last_backup_label = QLabel("Last Backup: Never")
        self.last_backup_label.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        status_row.addWidget(self.last_backup_label)
        
        self.backup_size_label = QLabel("Size: Unknown")
        self.backup_size_label.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        status_row.addWidget(self.backup_size_label)
        
        self.auto_backup_status = QLabel("Auto Backup: Disabled")
        self.auto_backup_status.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        status_row.addWidget(self.auto_backup_status)
        
        status_layout.addLayout(status_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_message = QLabel("Ready to backup")
        self.status_message.setStyleSheet("""
            QLabel {
                background: #e9ecef;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        status_layout.addWidget(self.status_message)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_status_btn = QPushButton("🔄 Refresh Status")
        self.refresh_status_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.refresh_status_btn.clicked.connect(self.refresh_status)
        button_layout.addWidget(self.refresh_status_btn)
        
        self.backup_now_btn = QPushButton("💾 Backup Now")
        self.backup_now_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.backup_now_btn.clicked.connect(self.start_manual_backup)
        button_layout.addWidget(self.backup_now_btn)
        
        layout.addLayout(button_layout)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 4px;
            }
        """)
        layout.addWidget(QLabel("📋 Backup Log:"))
        layout.addWidget(self.log_text)
        
        # Initial status check
        QTimer.singleShot(1000, self.refresh_status)  # Check status after 1 second
    
    def get_backup_config(self):
        """Get backup configuration from main settings"""
        config_file = 'config/config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('backup_config', {})
            except:
                pass
        return {}
    
    def refresh_status(self):
        """Refresh backup configuration and status"""
        config = self.get_backup_config()
        
        # Check configuration status
        credentials_path = config.get('credentials_path', '')
        bucket_name = config.get('bucket_name', '')
        enabled = config.get('enabled', False)
        frequency = config.get('frequency', 'daily')
        
        if not credentials_path or not bucket_name:
            self.config_status_label.setText("❌ Backup not configured - Please set credentials and bucket in Settings")
            self.config_status_label.setStyleSheet("""
                QLabel {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.backup_now_btn.setEnabled(False)
        elif not os.path.exists(credentials_path):
            self.config_status_label.setText(f"❌ Credentials file not found: {credentials_path}")
            self.config_status_label.setStyleSheet("""
                QLabel {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.backup_now_btn.setEnabled(False)
        else:
            self.config_status_label.setText(f"✅ Configured - Bucket: {bucket_name}")
            self.config_status_label.setStyleSheet("""
                QLabel {
                    background: #d4edda;
                    color: #155724;
                    padding: 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.backup_now_btn.setEnabled(True)
        
        # Update auto backup status
        if enabled:
            self.auto_backup_status.setText(f"Auto Backup: Enabled ({frequency})")
            self.auto_backup_status.setStyleSheet("""
                QLabel {
                    background: #d4edda;
                    color: #155724;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.auto_backup_status.setText("Auto Backup: Disabled")
            self.auto_backup_status.setStyleSheet("""
                QLabel {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        
        # Update last backup status
        self.update_backup_status()
        
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Status refreshed")
    
    def load_status(self):
        """Load initial status"""
        self.refresh_status()
    
    def start_manual_backup(self):
        """Start manual backup"""
        config = self.get_backup_config()
        
        if not config.get('credentials_path') or not config.get('bucket_name'):
            QMessageBox.warning(self, "Configuration Missing", 
                              "Please configure Google Cloud backup settings in the Settings tab first.")
            return
        
        self.log_text.append("🚀 Starting manual backup...")
        self.backup_now_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_message.setText("Preparing backup...")
        
        # Create backup service
        self.backup_service = GoogleCloudBackupService(config)
        self.backup_service.progress_signal.connect(self.update_progress)
        self.backup_service.log_signal.connect(self.log_text.append)
        self.backup_service.error_signal.connect(self.on_backup_error)
        self.backup_service.finished_signal.connect(self.on_backup_finished)
        
        self.backup_service.start()
    
    def update_progress(self, current, total, message):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_message.setText(message)
    
    def on_backup_error(self, error):
        """Handle backup error"""
        self.log_text.append(f"❌ Backup error: {error}")
        self.backup_now_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_message.setText("Backup failed")
        
        QMessageBox.critical(self, "Backup Failed", f"Backup failed:\n\n{error}")
    
    def on_backup_finished(self, result):
        """Handle backup completion"""
        self.backup_now_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if result['success']:
            self.status_message.setText("Backup completed successfully")
            self.update_backup_status()
            
            file_size_mb = result['file_size'] / (1024 * 1024)
            QMessageBox.information(self, "Backup Complete", 
                                  f"✅ Backup completed successfully!\n\n"
                                  f"Size: {file_size_mb:.1f} MB\n"
                                  f"Location: {result['public_url']}")
        else:
            self.status_message.setText("Backup failed")
            QMessageBox.critical(self, "Backup Failed", f"Backup failed:\n\n{result.get('error', 'Unknown error')}")
    
    def update_backup_status(self):
        """Update backup status display"""
        # Check for last backup time
        if os.path.exists('last_backup_time.txt'):
            try:
                with open('last_backup_time.txt', 'r') as f:
                    last_backup = datetime.fromisoformat(f.read().strip())
                    self.last_backup_label.setText(f"Last Backup: {last_backup.strftime('%Y-%m-%d %H:%M')}")
                    self.last_backup_label.setStyleSheet("""
                        QLabel {
                            background: #d4edda;
                            color: #155724;
                            padding: 8px;
                            border-radius: 4px;
                            font-weight: bold;
                        }
                    """)
            except:
                pass
        
        # Try to get backup size from recent backup files
        try:
            import glob
            backup_files = glob.glob("*.zip")
            if backup_files:
                latest_backup = max(backup_files, key=os.path.getmtime)
                size_mb = os.path.getsize(latest_backup) / (1024 * 1024)
                self.backup_size_label.setText(f"Size: {size_mb:.1f} MB")
        except:
            pass
    
    def closeEvent(self, event):
        """Handle widget close"""
        if self.backup_service and self.backup_service.isRunning():
            self.backup_service.stop()
            self.backup_service.wait()
        
        event.accept() 

    def start_backup_scheduler(self):
        """Start the automatic backup scheduler if enabled"""
        config = self.get_backup_config()
        
        if config.get('enabled', False):
            try:
                # Create and start backup scheduler
                self.backup_scheduler = BackupScheduler(config)
                self.backup_scheduler.backup_triggered.connect(self.start_automatic_backup)
                self.backup_scheduler.log_signal.connect(self.log_text.append)
                self.backup_scheduler.start()
                
                self.log_text.append("⏰ Automatic backup scheduler started")
                self.log_text.append(f"📅 Frequency: {config.get('frequency', 'daily')}")
            except Exception as e:
                self.log_text.append(f"❌ Failed to start backup scheduler: {e}")
        else:
            self.log_text.append("⏸️ Automatic backups disabled")
    
    def start_automatic_backup(self):
        """Start automatic backup triggered by scheduler"""
        self.log_text.append("🔄 Automatic backup triggered by scheduler...")
        self.start_manual_backup()  # Reuse manual backup logic 