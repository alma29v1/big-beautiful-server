from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QGroupBox, QFormLayout, QFileDialog, QCheckBox, QComboBox, QSpinBox
)
from PySide6.QtCore import Signal, Qt
import json
import os

CONFIG_FILE = 'config/config.json'

class SettingsWidget(QWidget):
    api_keys_updated = Signal(dict)
    backup_config_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_keys()

    def setup_ui(self):
        """Setup the settings UI with sections for API keys and backup"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("⚙️ Application Settings")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # API Keys Section
        api_group = QGroupBox("🔑 API Keys Configuration")
        api_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #667eea;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #667eea;
            }
        """)
        
        api_layout = QFormLayout()
        
        # Existing API key fields
        self.batchdata_input = QLineEdit()
        self.batchdata_input.setPlaceholderText("Enter BatchData API key")
        api_layout.addRow("BatchData API Key:", self.batchdata_input)
        
        self.mailchimp_input = QLineEdit()
        self.mailchimp_input.setPlaceholderText("Enter MailChimp API key")
        api_layout.addRow("MailChimp API Key:", self.mailchimp_input)
        
        self.activeknocker_input = QLineEdit()
        self.activeknocker_input.setPlaceholderText("Enter ActiveKnocker API key")
        api_layout.addRow("ActiveKnocker API Key:", self.activeknocker_input)
        
        self.xai_input = QLineEdit()
        self.xai_input.setPlaceholderText("Enter XAI API key")
        api_layout.addRow("XAI API Key:", self.xai_input)
        
        self.google_vision_input = QLineEdit()
        self.google_vision_input.setPlaceholderText("Enter Google Vision API key")
        api_layout.addRow("Google Vision API Key:", self.google_vision_input)
        
        self.google_maps_input = QLineEdit()
        self.google_maps_input.setPlaceholderText("Enter Google Maps API key")
        api_layout.addRow("Google Maps API Key:", self.google_maps_input)
        
        self.openai_input = QLineEdit()
        self.openai_input.setPlaceholderText("Enter OpenAI API key")
        api_layout.addRow("OpenAI API Key:", self.openai_input)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Google Cloud Backup Section
        backup_group = QGroupBox("☁️ Google Cloud Backup Configuration")
        backup_group.setStyleSheet("""
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
        
        backup_layout = QFormLayout()
        
        # Service Account JSON file
        self.gcloud_credentials_input = QLineEdit()
        self.gcloud_credentials_input.setPlaceholderText("Path to Google Cloud service account JSON file")
        credentials_browse_btn = QPushButton("📁 Browse")
        credentials_browse_btn.clicked.connect(self.browse_gcloud_credentials)
        
        credentials_layout = QHBoxLayout()
        credentials_layout.addWidget(self.gcloud_credentials_input)
        credentials_layout.addWidget(credentials_browse_btn)
        backup_layout.addRow("Service Account JSON:", credentials_layout)
        
        # Storage bucket name
        self.gcloud_bucket_input = QLineEdit()
        self.gcloud_bucket_input.setPlaceholderText("your-backup-bucket-name")
        backup_layout.addRow("Storage Bucket:", self.gcloud_bucket_input)
        
        # Backup schedule
        self.backup_enabled = QCheckBox("Enable automatic backups")
        backup_layout.addRow(self.backup_enabled)
        
        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["hourly", "daily", "weekly"])
        self.backup_frequency.setCurrentText("daily")
        backup_layout.addRow("Backup Frequency:", self.backup_frequency)
        
        # Retention period
        self.backup_retention = QSpinBox()
        self.backup_retention.setRange(1, 365)
        self.backup_retention.setValue(30)
        self.backup_retention.setSuffix(" days")
        backup_layout.addRow("Retention Period:", self.backup_retention)
        
        # Advanced retention settings
        retention_label = QLabel("🔧 Advanced Retention Settings")
        retention_label.setStyleSheet("font-weight: bold; color: #4285f4; margin-top: 10px;")
        backup_layout.addRow(retention_label)
        
        # Keep recent backups
        self.keep_recent_backups = QSpinBox()
        self.keep_recent_backups.setRange(1, 20)
        self.keep_recent_backups.setValue(5)
        self.keep_recent_backups.setSuffix(" backups")
        self.keep_recent_backups.setToolTip("Number of most recent backups to always keep (regardless of age)")
        backup_layout.addRow("Keep Recent:", self.keep_recent_backups)
        
        # Keep daily backups
        self.keep_daily_backups = QSpinBox()
        self.keep_daily_backups.setRange(1, 30)
        self.keep_daily_backups.setValue(7)
        self.keep_daily_backups.setSuffix(" days")
        self.keep_daily_backups.setToolTip("Keep one backup per day for this many days")
        backup_layout.addRow("Keep Daily:", self.keep_daily_backups)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Test Google Cloud connection
        test_gcloud_btn = QPushButton("🔗 Test Google Cloud")
        test_gcloud_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #138496; }
        """)
        test_gcloud_btn.clicked.connect(self.test_gcloud_connection)
        button_layout.addWidget(test_gcloud_btn)
        
        # Save all settings
        save_btn = QPushButton("💾 Save All Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        save_btn.clicked.connect(self.save_keys)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_gcloud_credentials(self):
        """Browse for Google Cloud service account JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Google Cloud Service Account JSON",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.gcloud_credentials_input.setText(file_path)
    
    def test_gcloud_connection(self):
        """Test Google Cloud connection"""
        credentials_path = self.gcloud_credentials_input.text().strip()
        bucket_name = self.gcloud_bucket_input.text().strip()
        
        if not credentials_path or not bucket_name:
            QMessageBox.warning(self, "Missing Configuration", 
                              "Please set both service account JSON file and bucket name.")
            return
        
        if not os.path.exists(credentials_path):
            QMessageBox.warning(self, "File Not Found", 
                              f"Service account file not found: {credentials_path}")
            return
        
        try:
            from google.cloud import storage
            from google.oauth2 import service_account
            
            # Test credentials and bucket access
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = storage.Client(credentials=credentials)
            bucket = client.bucket(bucket_name)
            bucket.reload()  # This will fail if bucket doesn't exist or no access
            
            # Get project ID from the client or credentials
            project_id = client.project or credentials.project_id
            
            QMessageBox.information(self, "Connection Successful", 
                                  "✅ Successfully connected to Google Cloud Storage!\n\n"
                                  f"Bucket: {bucket_name}\n"
                                  f"Project: {project_id}")
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", 
                               f"❌ Failed to connect to Google Cloud:\n\n{str(e)}")

    def load_keys(self):
        """Load API keys and backup configuration"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Load API keys
                    self.batchdata_input.setText(data.get('batchdata_api_key', ''))
                    self.mailchimp_input.setText(data.get('mailchimp_api_key', ''))
                    self.activeknocker_input.setText(data.get('activeknocker_api_key', ''))
                    self.xai_input.setText(data.get('xai_api_key', ''))
                    self.google_vision_input.setText(data.get('google_vision_api_key', ''))
                    self.google_maps_input.setText(data.get('google_maps_api_key', ''))
                    self.openai_input.setText(data.get('openai_api_key', ''))
                    
                    # Load backup configuration
                    backup_config = data.get('backup_config', {})
                    self.gcloud_credentials_input.setText(backup_config.get('credentials_path', ''))
                    self.gcloud_bucket_input.setText(backup_config.get('bucket_name', ''))
                    self.backup_enabled.setChecked(backup_config.get('enabled', False))
                    self.backup_frequency.setCurrentText(backup_config.get('frequency', 'daily'))
                    self.backup_retention.setValue(backup_config.get('retention_days', 30))
                    self.keep_recent_backups.setValue(backup_config.get('keep_recent_backups', 5))
                    self.keep_daily_backups.setValue(backup_config.get('keep_daily_backups', 7))
                    
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Error loading configuration: {e}")

    def save_keys(self):
        """Save API keys and backup configuration"""
        try:
            # Prepare API keys data
            api_data = {
                'batchdata_api_key': self.batchdata_input.text().strip(),
                'mailchimp_api_key': self.mailchimp_input.text().strip(),
                'activeknocker_api_key': self.activeknocker_input.text().strip(),
                'xai_api_key': self.xai_input.text().strip(),
                'google_vision_api_key': self.google_vision_input.text().strip(),
                'google_maps_api_key': self.google_maps_input.text().strip(),
                'openai_api_key': self.openai_input.text().strip(),
            }
            
            # Prepare backup configuration
            backup_config = {
                'credentials_path': self.gcloud_credentials_input.text().strip(),
                'bucket_name': self.gcloud_bucket_input.text().strip(),
                'enabled': self.backup_enabled.isChecked(),
                'frequency': self.backup_frequency.currentText(),
                'retention_days': self.backup_retention.value(),
                'keep_recent_backups': self.keep_recent_backups.value(),
                'keep_daily_backups': self.keep_daily_backups.value()
            }
            
            # Combine all configuration
            full_config = api_data.copy()
            full_config['backup_config'] = backup_config
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Save to file
            with open(CONFIG_FILE, 'w') as f:
                json.dump(full_config, f, indent=2)
            
            QMessageBox.information(self, 'Settings', 
                                  '✅ All settings saved successfully!\n\n'
                                  '• API keys updated\n'
                                  '• Backup configuration saved\n'
                                  '• Settings will take effect immediately')
            
            # Emit signals for other components
            self.api_keys_updated.emit(api_data)
            self.backup_config_updated.emit(backup_config)
            
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', f"❌ Error saving settings:\n\n{e}")

    def get_keys(self):
        """Get current API keys"""
        return {
            'batchdata_api_key': self.batchdata_input.text().strip(),
            'mailchimp_api_key': self.mailchimp_input.text().strip(),
            'activeknocker_api_key': self.activeknocker_input.text().strip(),
            'xai_api_key': self.xai_input.text().strip(),
            'google_vision_api_key': self.google_vision_input.text().strip(),
            'google_maps_api_key': self.google_maps_input.text().strip(),
            'openai_api_key': self.openai_input.text().strip(),
        }
    
    def get_backup_config(self):
        """Get current backup configuration"""
        return {
            'credentials_path': self.gcloud_credentials_input.text().strip(),
            'bucket_name': self.gcloud_bucket_input.text().strip(),
            'enabled': self.backup_enabled.isChecked(),
            'frequency': self.backup_frequency.currentText(),
            'retention_days': self.backup_retention.value(),
            'keep_recent_backups': self.keep_recent_backups.value(),
            'keep_daily_backups': self.keep_daily_backups.value()
        } 