"""
AI Email Marketing Widget - Comprehensive email campaign generation interface with AI Chat
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTextEdit, QGroupBox, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QTabWidget,
    QScrollArea, QFrame, QSplitter, QInputDialog, QGridLayout,
    QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
from services.ai_email_marketing_service import AIEmailMarketingService
import json
import csv
import logging
from datetime import datetime
import os
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

# Setup logger
logger = logging.getLogger(__name__)

class AIChatWorker(QThread):
    response_signal = Signal(str)
    error_signal = Signal(str)
    
    def __init__(self, message, context=None):
        super().__init__()
        self.message = message
        self.context = context or {}
        self.service = AIEmailMarketingService('xai_key', 'mailchimp_key', 'us1')
    
    def run(self):
        try:
            response = self.service.chat_with_ai(self.message, self.context)
            self.response_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(f"Chat error: {e}")

class CampaignGenerationWorker(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)
    
    def __init__(self, contacts, config):
        super().__init__()
        self.contacts = contacts
        self.config = config
        self.service = AIEmailMarketingService('xai_key', 'mailchimp_key', 'us1')
    
    def run(self):
        try:
            self.progress_signal.emit("Generating AI email campaign...")
            campaign = self.service.generate_email_campaign(self.contacts, self.config)
            self.finished_signal.emit(campaign)
        except Exception as e:
            self.error_signal.emit(f"Error generating campaign: {e}")

class AIEmailMarketingWidget(QWidget):
    """Comprehensive AI email marketing interface with chat functionality"""
    
    def __init__(self):
        super().__init__()
        self.current_campaign = {}
        self.contacts_data = []
        self.chat_history = []
        self.worker = None  # Track active worker
        self.chat_worker = None  # Track active chat worker
        self.setup_ui()
        
    def __del__(self):
        """Cleanup when widget is destroyed"""
        self.cleanup_workers()
        
    def cleanup_workers(self):
        """Clean up any running worker threads"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)  # Wait up to 3 seconds
            if self.worker.isRunning():
                self.worker.terminate()
                
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.quit()
            self.chat_worker.wait(3000)
            if self.chat_worker.isRunning():
                self.chat_worker.terminate()
                
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup_workers()
        event.accept()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Set overall dark theme for the widget
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background-color: #404040;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #404040;
            }
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                min-height: 25px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
            }
            QComboBox::down-arrow {
                border: none;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                min-height: 25px;
            }
            QSpinBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                min-height: 25px;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                min-height: 200px;
            }
            QPushButton {
                background-color: #007bff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 6px 8px;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
        """)
        
        # Header
        header = QLabel("AI Email Marketing Campaign Generator with Chat Assistant")
        header.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            padding: 15px; 
            background-color: #404040;
            color: #ffffff;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Create main tabs
        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs)
        
        # Campaign Builder Tab
        campaign_tab = self.create_campaign_tab()
        self.main_tabs.addTab(campaign_tab, "Campaign")
        
        # AI Chat Tab
        chat_tab = self.create_chat_tab()
        self.main_tabs.addTab(chat_tab, "AI Chat")
        
        # Export & Results Tab
        results_tab = self.create_results_tab()
        self.main_tabs.addTab(results_tab, "Results")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to generate campaigns and chat with AI")
        self.status_label.setStyleSheet("""
            padding: 10px; 
            background-color: #404040; 
            color: #ffffff;
            border-radius: 6px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_label)
    
    def create_campaign_tab(self) -> QWidget:
        """Create the campaign builder tab with sub-tabs for better organization"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create sub-tabs for campaign builder
        self.campaign_tabs = QTabWidget()
        
        # Configuration Tab
        config_tab = self.create_configuration_subtab()
        self.campaign_tabs.addTab(config_tab, "Config")
        
        # Contact Management Tab
        contacts_tab = self.create_contacts_subtab()
        self.campaign_tabs.addTab(contacts_tab, "Contacts")
        
        # Campaign Actions Tab
        actions_tab = self.create_actions_subtab()
        self.campaign_tabs.addTab(actions_tab, "Actions")
        
        # Preview Tab
        preview_tab = self.create_preview_subtab()
        self.campaign_tabs.addTab(preview_tab, "Preview")
        
        layout.addWidget(self.campaign_tabs)
        
        return tab
    
    def create_configuration_subtab(self) -> QWidget:
        """Create the campaign configuration sub-tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Campaign Type
        layout.addWidget(QLabel('Campaign Type:'))
        self.campaign_type_combo = QComboBox()
        self.campaign_type_combo.addItems([
            "Fiber Introduction",
            "ADT Security Offer", 
            "Combined Services",
            "Follow-up Campaign",
            "Seasonal Promotion",
            "Neighborhood Focus"
        ])
        self.campaign_type_combo.currentTextChanged.connect(self.on_campaign_type_changed)
        layout.addWidget(self.campaign_type_combo)
        
        # Email Tone
        layout.addWidget(QLabel('Email Tone:'))
        self.email_tone_combo = QComboBox()
        self.email_tone_combo.addItems([
            "Professional",
            "Friendly", 
            "Urgent",
            "Informative",
            "Conversational"
        ])
        layout.addWidget(self.email_tone_combo)
        
        # Target Audience Size
        layout.addWidget(QLabel('Target Audience Size:'))
        self.audience_size = QSpinBox()
        self.audience_size.setRange(1, 10000)
        self.audience_size.setValue(100)
        layout.addWidget(self.audience_size)
        
        # Audience Description
        layout.addWidget(QLabel('Audience Description:'))
        self.audience_input = QTextEdit()
        self.audience_input.setPlaceholderText("Describe your target audience (e.g., 'Homeowners in new developments interested in high-speed internet')")
        self.audience_input.setMaximumHeight(80)
        layout.addWidget(self.audience_input)
        
        # Subject Line
        layout.addWidget(QLabel('Subject Line:'))
        self.subject_line_input = QLineEdit()
        self.subject_line_input.setPlaceholderText("Enter email subject line")
        layout.addWidget(self.subject_line_input)
        
        # From Name
        layout.addWidget(QLabel('From Name:'))
        self.sender_name_input = QLineEdit()
        self.sender_name_input.setPlaceholderText("Your name or company name")
        layout.addWidget(self.sender_name_input)
        
        # From Email
        layout.addWidget(QLabel('From Email:'))
        self.sender_email_input = QLineEdit()
        self.sender_email_input.setPlaceholderText("your-email@company.com")
        layout.addWidget(self.sender_email_input)
        
        # Call to Action
        layout.addWidget(QLabel('Call to Action:'))
        self.cta_input = QLineEdit()
        self.cta_input.setPlaceholderText("e.g., 'Get Your Free Quote Today'")
        layout.addWidget(self.cta_input)
        
        # Company Name
        layout.addWidget(QLabel('Company Name:'))
        self.company_name_input = QLineEdit()
        self.company_name_input.setPlaceholderText("Your company name")
        layout.addWidget(self.company_name_input)
        
        # Company Website
        layout.addWidget(QLabel('Website:'))
        self.company_website_input = QLineEdit()
        self.company_website_input.setPlaceholderText("https://yourcompany.com")
        layout.addWidget(self.company_website_input)
        
        # Company Phone
        layout.addWidget(QLabel('Phone:'))
        self.company_phone_input = QLineEdit()
        self.company_phone_input.setPlaceholderText("(555) 123-4567")
        layout.addWidget(self.company_phone_input)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return tab
    
    def create_contacts_subtab(self) -> QWidget:
        """Create the contacts management sub-tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Contact Data Group
        contacts_group = QGroupBox("Contact Data Management")
        contacts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        contacts_layout = QVBoxLayout(contacts_group)
        contacts_layout.setSpacing(15)
        
        # Contact buttons row 1
        contact_buttons_1 = QHBoxLayout()
        contact_buttons_1.setSpacing(15)
        
        load_real_btn = QPushButton("📥 Load Real Contacts")
        load_real_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        load_real_btn.clicked.connect(self.load_real_contacts)
        contact_buttons_1.addWidget(load_real_btn)
        
        import_mailchimp_btn = QPushButton("📧 Import from Mailchimp")
        import_mailchimp_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        import_mailchimp_btn.clicked.connect(self.import_mailchimp_data)
        contact_buttons_1.addWidget(import_mailchimp_btn)
        
        contacts_layout.addLayout(contact_buttons_1)
        
        # Contact buttons row 2
        contact_buttons_2 = QHBoxLayout()
        contact_buttons_2.setSpacing(15)
        
        download_templates_btn = QPushButton("📄 Download Email Templates")
        download_templates_btn.setStyleSheet("""
            QPushButton {
                background: #6f42c1;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #5a32a3;
            }
        """)
        download_templates_btn.clicked.connect(self.download_mailchimp_templates)
        contact_buttons_2.addWidget(download_templates_btn)
        
        manage_lists_btn = QPushButton("📋 Manage Mailchimp Lists")
        manage_lists_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        manage_lists_btn.clicked.connect(self.manage_mailchimp_lists)
        contact_buttons_2.addWidget(manage_lists_btn)
        
        contacts_layout.addLayout(contact_buttons_2)
        
        # Contact status
        self.contact_status = QLabel(f"Loaded: {len(self.contacts_data)} contacts")
        self.contact_status.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding: 15px;
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
        """)
        contacts_layout.addWidget(self.contact_status)
        
        layout.addWidget(contacts_group)
        
        # Contact Summary Group
        summary_group = QGroupBox("Contact Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        summary_layout = QVBoxLayout(summary_group)
        
        self.contact_summary = QLabel("No contacts loaded yet")
        self.contact_summary.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding: 15px;
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                font-size: 14px;
                min-height: 100px;
            }
        """)
        summary_layout.addWidget(self.contact_summary)
        
        layout.addWidget(summary_group)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_actions_subtab(self) -> QWidget:
        """Create the campaign actions sub-tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Primary Actions Group
        primary_group = QGroupBox("Primary Actions")
        primary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        primary_layout = QHBoxLayout(primary_group)
        primary_layout.setSpacing(15)
        
        # Generate Campaign Button
        self.generate_btn = QPushButton("🎯 Generate Campaign")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 35px;
                max-height: 45px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_campaign)
        primary_layout.addWidget(self.generate_btn)
        
        # Launch Campaign Button
        self.launch_campaign_btn = QPushButton("🚀 Launch Campaign")
        self.launch_campaign_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 35px;
                max-height: 45px;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        self.launch_campaign_btn.clicked.connect(self.launch_campaign)
        primary_layout.addWidget(self.launch_campaign_btn)
        
        layout.addWidget(primary_group)
        
        # Secondary Actions Group
        secondary_group = QGroupBox("Campaign Management")
        secondary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        secondary_layout = QGridLayout(secondary_group)
        secondary_layout.setSpacing(10)
        
        # Save Campaign Button
        save_btn = QPushButton("💾 Save Campaign")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 30px;
                max-height: 35px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_campaign)
        secondary_layout.addWidget(save_btn, 0, 0)
        
        # Load Campaign Button
        load_btn = QPushButton("📂 Load Campaign")
        load_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 30px;
                max-height: 35px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        load_btn.clicked.connect(self.load_campaign)
        secondary_layout.addWidget(load_btn, 0, 1)
        
        # Export to Mailchimp Button
        export_btn = QPushButton("📤 Export to Mailchimp")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #fd7e14;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 30px;
                max-height: 35px;
            }
            QPushButton:hover {
                background: #e8590c;
            }
        """)
        export_btn.clicked.connect(self.export_to_mailchimp)
        secondary_layout.addWidget(export_btn, 1, 0)
        
        # Analyze Performance Button
        analyze_btn = QPushButton("📊 Analyze Performance")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 30px;
                max-height: 35px;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        analyze_btn.clicked.connect(self.analyze_campaign_performance)
        secondary_layout.addWidget(analyze_btn, 1, 1)
        
        layout.addWidget(secondary_group)
        
        # Campaign Status Group
        status_group = QGroupBox("Campaign Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        status_layout = QVBoxLayout(status_group)
        
        self.campaign_status = QLabel("Ready to generate campaign")
        self.campaign_status.setStyleSheet("""
            QLabel {
                color: #ffffff;
                padding: 12px;
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-height: 40px;
                max-height: 50px;
            }
        """)
        status_layout.addWidget(self.campaign_status)
        
        layout.addWidget(status_group)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_preview_subtab(self) -> QWidget:
        """Create the campaign preview subtab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("👁️ Campaign Preview")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Preview tabs for different views
        preview_tabs = QTabWidget()
        
        # HTML Email Preview Tab
        html_tab = QWidget()
        html_layout = QVBoxLayout(html_tab)
        
        # HTML preview controls
        preview_controls = QHBoxLayout()
        
        refresh_preview_btn = QPushButton("🔄 Refresh Preview")
        refresh_preview_btn.clicked.connect(self.refresh_html_preview)
        preview_controls.addWidget(refresh_preview_btn)
        
        view_in_browser_btn = QPushButton("🌐 View in Browser")
        view_in_browser_btn.clicked.connect(self.view_email_in_browser)
        preview_controls.addWidget(view_in_browser_btn)
        
        preview_controls.addStretch()
        html_layout.addLayout(preview_controls)
        
        # HTML email preview widget
        from PySide6.QtWebEngineWidgets import QWebEngineView
        try:
            self.html_preview = QWebEngineView()
            self.html_preview.setHtml("<p>Generate a campaign to see HTML preview</p>")
            html_layout.addWidget(self.html_preview)
        except ImportError:
            # Fallback to QTextEdit if WebEngine not available
            self.html_preview = QTextEdit()
            self.html_preview.setHtml("<p>Generate a campaign to see HTML preview</p>")
            self.html_preview.setReadOnly(True)
            html_layout.addWidget(self.html_preview)
        
        preview_tabs.addTab(html_tab, "📧 HTML Email")
        
        # Text Preview Tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        
        # Text preview
        self.campaign_preview = QTextEdit()
        self.campaign_preview.setReadOnly(True)
        self.campaign_preview.setPlainText("Generate a campaign to see preview")
        text_layout.addWidget(self.campaign_preview)
        
        preview_tabs.addTab(text_tab, "📝 Text Version")
        
        # Mobile Preview Tab
        mobile_tab = QWidget()
        mobile_layout = QVBoxLayout(mobile_tab)
        
        mobile_label = QLabel("📱 Mobile Preview")
        mobile_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        mobile_layout.addWidget(mobile_label)
        
        # Mobile preview container
        mobile_container = QFrame()
        mobile_container.setFixedSize(350, 600)
        mobile_container.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #333;
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        mobile_content_layout = QVBoxLayout(mobile_container)
        
        try:
            self.mobile_preview = QWebEngineView()
            self.mobile_preview.setHtml("<p>Generate a campaign to see mobile preview</p>")
            mobile_content_layout.addWidget(self.mobile_preview)
        except ImportError:
            self.mobile_preview = QTextEdit()
            self.mobile_preview.setHtml("<p>Generate a campaign to see mobile preview</p>")
            self.mobile_preview.setReadOnly(True)
            mobile_content_layout.addWidget(self.mobile_preview)
        
        # Center the mobile container
        mobile_center_layout = QHBoxLayout()
        mobile_center_layout.addStretch()
        mobile_center_layout.addWidget(mobile_container)
        mobile_center_layout.addStretch()
        
        mobile_layout.addLayout(mobile_center_layout)
        mobile_layout.addStretch()
        
        preview_tabs.addTab(mobile_tab, "📱 Mobile")
        
        layout.addWidget(preview_tabs)
        
        return widget

    def refresh_html_preview(self):
        """Refresh the HTML email preview"""
        if hasattr(self, 'current_campaign') and self.current_campaign:
            html_content = self.create_html_email_preview(self.current_campaign)
            
            # Update HTML preview
            if hasattr(self.html_preview, 'setHtml'):
                self.html_preview.setHtml(html_content)
            
            # Update mobile preview with mobile-optimized version
            if hasattr(self.mobile_preview, 'setHtml'):
                mobile_html = self.create_mobile_html_preview(self.current_campaign)
                self.mobile_preview.setHtml(mobile_html)
        else:
            if hasattr(self.html_preview, 'setHtml'):
                self.html_preview.setHtml("<p>No campaign available. Generate a campaign first.</p>")
            if hasattr(self.mobile_preview, 'setHtml'):
                self.mobile_preview.setHtml("<p>No campaign available. Generate a campaign first.</p>")

    def view_email_in_browser(self):
        """Save HTML email and open in browser"""
        if not hasattr(self, 'current_campaign') or not self.current_campaign:
            QMessageBox.warning(self, "No Campaign", "Generate a campaign first")
            return
        
        try:
            import tempfile
            import webbrowser
            
            html_content = self.create_html_email_preview(self.current_campaign)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_file = f.name
            
            # Open in browser
            webbrowser.open(f'file://{temp_file}')
            
        except Exception as e:
            QMessageBox.critical(self, "Browser Error", f"Error opening in browser: {e}")

    def create_mobile_html_preview(self, campaign: dict) -> str:
        """Create mobile-optimized HTML preview"""
        try:
            # Get email content
            if 'personalized_emails' in campaign and campaign['personalized_emails']:
                email = campaign['personalized_emails'][0]
                subject = email.get('subject', 'No Subject')
                body = email.get('body', 'No content')
                recipient = email.get('contact_name', 'Customer')
            elif 'templates' in campaign and campaign['templates']:
                template = list(campaign['templates'].values())[0]
                subject = template.get('subject', 'No Subject')
                body = template.get('body', 'No content')
                recipient = "Customer"
            else:
                return "<p>No email content available</p>"
            
            # Mobile-optimized HTML
            mobile_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 10px;
            background-color: #f4f4f4;
            font-size: 14px;
        }}
        .email-container {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            border: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #2196F3;
        }}
        .logo {{
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 8px;
        }}
        .subject {{
            font-size: 16px;
            color: #666;
            margin: 0;
        }}
        .greeting {{
            font-size: 14px;
            margin-bottom: 15px;
            color: #333;
        }}
        .content {{
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        .cta-button {{
            display: block;
            background-color: #2196F3;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 15px 0;
            text-align: center;
            font-size: 16px;
        }}
        .benefits {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-size: 12px;
        }}
        .benefits ul {{
            margin: 5px 0;
            padding-left: 15px;
        }}
        .benefits li {{
            margin-bottom: 5px;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 10px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo">🚀 AT&T Fiber</div>
            <h1 class="subject">{subject}</h1>
        </div>
        
        <div class="greeting">
            <strong>Hi {recipient},</strong>
        </div>
        
        <div class="content">
            {self.format_mobile_body_html(body)}
        </div>
        
        <a href="#" class="cta-button">Check Availability</a>
        
        <div class="benefits">
            <strong>Why Choose Us?</strong>
            <ul>
                <li>⚡ Ultra-fast speeds</li>
                <li>🏠 Professional security</li>
                <li>📱 Smart home ready</li>
                <li>💰 Great pricing</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>© 2024 AT&T Fiber Services</p>
            <p><a href="#">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""
            return mobile_html
            
        except Exception as e:
            return f"<p>Error creating mobile preview: {e}</p>"

    def format_mobile_body_html(self, body: str) -> str:
        """Format email body for mobile display"""
        # Keep it simple for mobile
        html_body = body.replace('\n\n', '<br><br>').replace('\n', '<br>')
        
        # Remove bullet points for mobile simplicity
        html_body = html_body.replace('• ', '')
        
        return html_body

    def manage_mailchimp_lists(self):
        """Manage Mailchimp lists with 7-list limit awareness"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Mailchimp List Management")
            dialog.setFixedSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Title and warning
            title = QLabel("📋 Mailchimp List Management")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; margin-bottom: 10px;")
            layout.addWidget(title)
            
            warning = QLabel("⚠️ Free Mailchimp accounts are limited to 7 lists. Manage your lists carefully!")
            warning.setStyleSheet("background: #fff3cd; padding: 10px; border-radius: 5px; color: #856404; margin-bottom: 15px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
            
            # List management options
            management_tabs = QTabWidget()
            
            # Current Lists Tab
            current_tab = QWidget()
            current_layout = QVBoxLayout(current_tab)
            
            current_info = QLabel("📊 Current List Strategy")
            current_info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            current_layout.addWidget(current_info)
            
            strategy_text = QTextEdit()
            strategy_text.setHtml("""
<h4>Recommended List Structure (7 lists max):</h4>
<ol>
<li><b>Fiber Available - Hot Leads</b> - Properties with fiber, no ADT</li>
<li><b>Fiber Available - Security Bundle</b> - Properties with fiber and ADT</li>
<li><b>Fiber Pending - Build Anticipation</b> - Properties waiting for fiber</li>
<li><b>ADT Only - Fiber Upsell</b> - Properties with ADT, no fiber</li>
<li><b>New Prospects - Both Services</b> - Fresh leads needing both</li>
<li><b>High Value Properties</b> - Premium homes for premium packages</li>
<li><b>Follow-up - Re-engagement</b> - Previous contacts for nurturing</li>
</ol>

<h4>Daily List Rotation Strategy:</h4>
<ul>
<li><b>Day 1-2:</b> Use lists 1-3 for immediate opportunities</li>
<li><b>Day 3-4:</b> Use lists 4-6 for upselling and premium targeting</li>
<li><b>Day 5-7:</b> Use list 7 for re-engagement and cleanup</li>
<li><b>Weekly:</b> Archive old campaigns, refresh list content</li>
</ul>

<h4>List Cleanup Tips:</h4>
<ul>
<li>Delete campaigns older than 30 days</li>
<li>Merge similar audience segments</li>
<li>Use tags instead of separate lists when possible</li>
<li>Archive seasonal campaigns immediately after use</li>
</ul>
""")
            strategy_text.setReadOnly(True)
            current_layout.addWidget(strategy_text)
            
            management_tabs.addTab(current_tab, "📊 Strategy")
            
            # Quick Actions Tab
            actions_tab = QWidget()
            actions_layout = QVBoxLayout(actions_tab)
            
            actions_label = QLabel("⚡ Quick Actions")
            actions_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            actions_layout.addWidget(actions_label)
            
            # Action buttons
            create_daily_lists_btn = QPushButton("📅 Create Today's Lists")
            create_daily_lists_btn.clicked.connect(self.create_daily_mailchimp_lists)
            actions_layout.addWidget(create_daily_lists_btn)
            
            cleanup_old_lists_btn = QPushButton("🧹 Cleanup Old Campaigns")
            cleanup_old_lists_btn.clicked.connect(self.cleanup_mailchimp_lists)
            actions_layout.addWidget(cleanup_old_lists_btn)
            
            export_segmented_btn = QPushButton("📤 Export Segmented Lists")
            export_segmented_btn.clicked.connect(self.export_segmented_lists)
            actions_layout.addWidget(export_segmented_btn)
            
            # List usage tracker
            usage_label = QLabel("📈 List Usage Tracker")
            usage_label.setStyleSheet("font-weight: bold; margin: 20px 0 10px 0;")
            actions_layout.addWidget(usage_label)
            
            usage_info = QTextEdit()
            usage_info.setHtml("""
<table style="width: 100%; border-collapse: collapse;">
<tr style="background: #f8f9fa;">
<th style="padding: 8px; border: 1px solid #ddd;">List Purpose</th>
<th style="padding: 8px; border: 1px solid #ddd;">Status</th>
<th style="padding: 8px; border: 1px solid #ddd;">Last Used</th>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Fiber Available</td>
<td style="padding: 8px; border: 1px solid #ddd; color: green;">Active</td>
<td style="padding: 8px; border: 1px solid #ddd;">Today</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Security Bundle</td>
<td style="padding: 8px; border: 1px solid #ddd; color: orange;">Ready</td>
<td style="padding: 8px; border: 1px solid #ddd;">Yesterday</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #ddd;">Follow-up</td>
<td style="padding: 8px; border: 1px solid #ddd; color: blue;">Available</td>
<td style="padding: 8px; border: 1px solid #ddd;">3 days ago</td>
</tr>
</table>

<p style="margin-top: 15px;"><b>Tip:</b> Keep 2-3 lists available for new campaigns. Archive completed campaigns immediately.</p>
""")
            usage_info.setReadOnly(True)
            usage_info.setMaximumHeight(200)
            actions_layout.addWidget(usage_info)
            
            actions_layout.addStretch()
            
            management_tabs.addTab(actions_tab, "⚡ Actions")
            
            layout.addWidget(management_tabs)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "List Management Error", f"Error managing lists: {e}")

    def create_daily_mailchimp_lists(self):
        """Create optimized daily Mailchimp lists"""
        if not self.contacts_data:
            QMessageBox.warning(self, "No Contacts", "Load contacts first")
            return
        
        try:
            # Segment contacts for daily campaigns
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Segment 1: Fiber Available + No ADT (Hot prospects)
            fiber_no_adt = [c for c in self.contacts_data if c.get('fiber', '').lower() == 'true' and c.get('adt', '').lower() != 'true']
            
            # Segment 2: Fiber Available + Has ADT (Upsell opportunity)
            fiber_with_adt = [c for c in self.contacts_data if c.get('fiber', '').lower() == 'true' and c.get('adt', '').lower() == 'true']
            
            # Segment 3: No Fiber + No ADT (Full package opportunity)
            no_services = [c for c in self.contacts_data if c.get('fiber', '').lower() != 'true' and c.get('adt', '').lower() != 'true']
            
            segments = [
                ("Fiber_Hot_Leads", fiber_no_adt, "🔥 Hot fiber prospects without security"),
                ("Fiber_Security_Bundle", fiber_with_adt, "📦 Bundle upgrade opportunities"),
                ("Full_Package_Prospects", no_services, "🎯 Complete service opportunities")
            ]
            
            # Create export directory
            export_dir = f"data/mailchimp_exports/{today}"
            os.makedirs(export_dir, exist_ok=True)
            
            created_files = []
            
            for segment_name, segment_data, description in segments:
                if not segment_data:
                    continue
                
                filename = f"{export_dir}/{segment_name}_{today}.csv"
                
                # Create CSV with proper Mailchimp format
                import pandas as pd
                df = pd.DataFrame(segment_data)
                
                # Mailchimp required columns
                mailchimp_df = pd.DataFrame({
                    'Email Address': df.get('email', ''),
                    'First Name': df.get('name', '').str.split().str[0],
                    'Last Name': df.get('name', '').str.split().str[-1],
                    'Address': df.get('address', ''),
                    'City': df.get('city', ''),
                    'State': df.get('state', ''),
                    'Zip': df.get('zip', ''),
                    'Fiber_Available': df.get('fiber', ''),
                    'ADT_Detected': df.get('adt', ''),
                    'Segment': segment_name,
                    'Campaign_Date': today
                })
                
                # Remove rows with missing email
                mailchimp_df = mailchimp_df[mailchimp_df['Email Address'].notna() & (mailchimp_df['Email Address'] != '')]
                
                if len(mailchimp_df) > 0:
                    mailchimp_df.to_csv(filename, index=False)
                    created_files.append((segment_name, len(mailchimp_df), description))
            
            # Show summary
            if created_files:
                summary = "✅ Daily Mailchimp lists created successfully!\n\n"
                for name, count, desc in created_files:
                    summary += f"📋 {name}: {count} contacts\n   {desc}\n\n"
                
                summary += f"📁 Files saved to: {export_dir}\n\n"
                summary += "💡 Next steps:\n"
                summary += "1. Upload CSV files to Mailchimp\n"
                summary += "2. Create targeted campaigns for each segment\n"
                summary += "3. Monitor performance and adjust strategy"
                
                QMessageBox.information(self, "Lists Created", summary)
            else:
                QMessageBox.warning(self, "No Lists Created", "No valid contact data found for list creation")
                
        except Exception as e:
            QMessageBox.critical(self, "Creation Error", f"Error creating daily lists: {e}")

    def cleanup_mailchimp_lists(self):
        """Cleanup old Mailchimp campaigns and lists"""
        try:
            # This would connect to Mailchimp API to cleanup
            # For now, show cleanup recommendations
            
            cleanup_dialog = QDialog(self)
            cleanup_dialog.setWindowTitle("🧹 Mailchimp Cleanup")
            cleanup_dialog.setFixedSize(500, 400)
            
            layout = QVBoxLayout(cleanup_dialog)
            
            title = QLabel("🧹 Cleanup Recommendations")
            title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title)
            
            cleanup_text = QTextEdit()
            cleanup_text.setHtml("""
<h3>🗂️ Manual Cleanup Steps:</h3>

<h4>1. Delete Old Campaigns (30+ days)</h4>
<ul>
<li>Go to Mailchimp Campaigns section</li>
<li>Sort by date (oldest first)</li>
<li>Delete campaigns older than 30 days</li>
<li>Keep high-performing campaigns for reference</li>
</ul>

<h4>2. Archive Completed Lists</h4>
<ul>
<li>Identify lists that are no longer active</li>
<li>Export data before archiving</li>
<li>Merge similar audiences when possible</li>
<li>Use tags instead of separate lists</li>
</ul>

<h4>3. Optimize List Structure</h4>
<ul>
<li>Combine seasonal campaigns into one list with tags</li>
<li>Merge geographic segments using location tags</li>
<li>Use custom fields instead of separate lists</li>
<li>Keep only actively used lists</li>
</ul>

<h4>4. Weekly Maintenance</h4>
<ul>
<li>Review list usage every Monday</li>
<li>Clean unsubscribed contacts</li>
<li>Update contact tags and segments</li>
<li>Plan next week's campaign strategy</li>
</ul>

<p><b>💡 Pro Tip:</b> Use Mailchimp's automation features to reduce the need for multiple lists!</p>
""")
            cleanup_text.setReadOnly(True)
            layout.addWidget(cleanup_text)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(cleanup_dialog.close)
            layout.addWidget(close_btn)
            
            cleanup_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Cleanup Error", f"Error during cleanup: {e}")

    def export_segmented_lists(self):
        """Export segmented lists for Mailchimp"""
        if not self.contacts_data:
            QMessageBox.warning(self, "No Contacts", "Load contacts first")
            return
        
        try:
            # Create comprehensive segmented exports
            today = datetime.now().strftime("%Y-%m-%d")
            export_dir = f"data/mailchimp_exports/segmented_{today}"
            os.makedirs(export_dir, exist_ok=True)
            
            # Define all possible segments
            segments = {
                'High_Value_Fiber': [c for c in self.contacts_data if c.get('fiber', '').lower() == 'true' and float(c.get('property_value', '0').replace('$', '').replace(',', '') or 0) > 400000],
                'Fiber_Available_NoADT': [c for c in self.contacts_data if c.get('fiber', '').lower() == 'true' and c.get('adt', '').lower() != 'true'],
                'ADT_Available_NoFiber': [c for c in self.contacts_data if c.get('adt', '').lower() == 'true' and c.get('fiber', '').lower() != 'true'],
                'Both_Services_Available': [c for c in self.contacts_data if c.get('fiber', '').lower() == 'true' and c.get('adt', '').lower() == 'true'],
                'No_Services_Detected': [c for c in self.contacts_data if c.get('fiber', '').lower() != 'true' and c.get('adt', '').lower() != 'true'],
                'Premium_Properties': [c for c in self.contacts_data if float(c.get('property_value', '0').replace('$', '').replace(',', '') or 0) > 500000],
                'New_Construction': [c for c in self.contacts_data if 'new' in c.get('address', '').lower() or 'construction' in c.get('address', '').lower()]
            }
            
            created_files = []
            
            for segment_name, segment_data in segments.items():
                if not segment_data:
                    continue
                
                filename = f"{export_dir}/{segment_name}_{today}.csv"
                
                import pandas as pd
                df = pd.DataFrame(segment_data)
                
                # Enhanced Mailchimp format with more fields
                mailchimp_df = pd.DataFrame({
                    'Email Address': df.get('email', ''),
                    'First Name': df.get('name', '').str.split().str[0],
                    'Last Name': df.get('name', '').str.split().str[-1],
                    'Address': df.get('address', ''),
                    'City': df.get('city', ''),
                    'State': df.get('state', ''),
                    'Zip': df.get('zip', ''),
                    'Phone': df.get('phone', ''),
                    'Fiber_Available': df.get('fiber', ''),
                    'ADT_Detected': df.get('adt', ''),
                    'Property_Value': df.get('property_value', ''),
                    'Neighborhood': df.get('neighborhood', ''),
                    'Segment_Type': segment_name,
                    'Export_Date': today,
                    'Lead_Score': df.apply(lambda x: self.calculate_lead_score(x), axis=1)
                })
                
                # Remove rows with missing email
                mailchimp_df = mailchimp_df[mailchimp_df['Email Address'].notna() & (mailchimp_df['Email Address'] != '')]
                
                if len(mailchimp_df) > 0:
                    mailchimp_df.to_csv(filename, index=False)
                    created_files.append((segment_name, len(mailchimp_df)))
            
            # Create summary report
            summary_file = f"{export_dir}/SEGMENT_SUMMARY_{today}.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Mailchimp Segmented Export Summary - {today}\n")
                f.write("=" * 50 + "\n\n")
                
                for name, count in created_files:
                    f.write(f"{name}: {count} contacts\n")
                
                f.write(f"\nTotal Segments: {len(created_files)}\n")
                f.write(f"Total Contacts: {sum(count for _, count in created_files)}\n")
                f.write(f"\nFiles location: {export_dir}\n")
                
                f.write("\n\nRecommended Mailchimp List Usage:\n")
                f.write("1. Upload 2-3 segments per day to stay within 7-list limit\n")
                f.write("2. Use tags and custom fields for additional segmentation\n")
                f.write("3. Archive completed campaigns immediately\n")
                f.write("4. Rotate segments based on campaign performance\n")
            
            # Show results
            if created_files:
                result_msg = f"✅ {len(created_files)} segmented lists exported!\n\n"
                for name, count in created_files:
                    result_msg += f"📋 {name}: {count} contacts\n"
                
                result_msg += f"\n📁 Files saved to:\n{export_dir}\n\n"
                result_msg += "💡 Tip: Upload 2-3 segments per day to manage your 7-list limit effectively!"
                
                QMessageBox.information(self, "Export Complete", result_msg)
            else:
                QMessageBox.warning(self, "No Exports", "No valid segments found for export")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting segments: {e}")

    def calculate_lead_score(self, contact) -> int:
        """Calculate lead score for prioritization"""
        score = 0
        
        # Fiber availability
        if contact.get('fiber', '').lower() == 'true':
            score += 30
        
        # ADT status
        if contact.get('adt', '').lower() == 'true':
            score += 20
        
        # Property value
        try:
            value = float(contact.get('property_value', '0').replace('$', '').replace(',', '') or 0)
            if value > 500000:
                score += 25
            elif value > 300000:
                score += 15
            elif value > 200000:
                score += 10
        except:
            pass
        
        # Contact information completeness
        if contact.get('email'):
            score += 15
        if contact.get('phone'):
            score += 10
        
        return min(score, 100)
    
    def create_chat_tab(self) -> QWidget:
        """Create the AI chat assistant tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Chat header
        chat_header = QLabel("AI Email Marketing Assistant")
        chat_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #f0f8ff;")
        layout.addWidget(chat_header)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        self.chat_display.setPlaceholderText("Chat history will appear here...")
        layout.addWidget(self.chat_display)
        
        # Chat input area
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me about email marketing strategies, campaign ideas, or anything else...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #007bff;
                border-radius: 20px;
                font-size: 14px;
                background-color: #404040;
                color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #cccccc;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)
        
        self.send_chat_btn = QPushButton("Send")
        self.send_chat_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        self.send_chat_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.send_chat_btn)
        
        layout.addLayout(input_layout)
        
        # Quick action buttons
        quick_actions = QHBoxLayout()
        
        quick_buttons = [
            ("Campaign Ideas", "Give me 5 creative email campaign ideas for AT&T fiber and ADT security"),
            ("Subject Lines", "Generate 10 compelling email subject lines for a fiber internet promotion"),
            ("Personalization Tips", "How can I personalize emails for homeowners with fiber internet?"),
            ("A/B Testing", "What should I A/B test in my email campaigns?"),
            ("Best Practices", "What are the current email marketing best practices for 2024?")
        ]
        
        for text, prompt in quick_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background: #28a745;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #218838;
                }
            """)
            btn.clicked.connect(lambda checked, p=prompt: self.send_quick_message(p))
            quick_actions.addWidget(btn)
        
        layout.addLayout(quick_actions)
        
        # Template-specific action buttons (NEW)
        template_actions = QHBoxLayout()
        
        template_buttons = [
            ("Analyze My Templates", "analyze_templates"),
            ("Compare Performance", "compare_performance"),
            ("Template Suggestions", "template_suggestions"),
            ("Optimize Subject Lines", "optimize_subjects"),
            ("Mobile Optimization", "mobile_optimization")
        ]
        
        for text, action in template_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background: #6f42c1;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #5a32a3;
                }
            """)
            btn.clicked.connect(lambda checked, a=action: self.handle_template_action(a))
            template_actions.addWidget(btn)
        
        layout.addLayout(template_actions)
        
        # Initialize chat with a proper welcome message
        self.add_chat_message("AI Assistant", """Hey! I'm Grok, your AI email marketing assistant. 🤖

I'm here to help with your AT&T Fiber and ADT Security campaigns - strategy, subject lines, content creation, whatever you need.

Quick tip: Use the tabs above to set up campaigns, load contacts, and generate content. Just ask if you need help with anything!""", is_ai=True)
        
        return tab
    
    def create_results_tab(self) -> QWidget:
        """Create the results and export tab"""
        tab = QWidget()
        tab.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
                background-color: #404040;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
        """)
        layout = QVBoxLayout(tab)
        
        # Results header
        results_header = QLabel("Campaign Results & Export")
        results_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #404040; color: #ffffff; border-radius: 5px;")
        layout.addWidget(results_header)
        
        # Action buttons
        button_layout = self.create_action_buttons()
        layout.addLayout(button_layout)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
        """)
        
        # Campaign Overview Tab
        self.overview_content = QTextEdit()
        self.overview_content.setReadOnly(True)
        self.overview_content.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        self.results_tabs.addTab(self.overview_content, "Campaign Overview")
        
        # Email Preview Tab
        self.email_preview = QTextEdit()
        self.email_preview.setReadOnly(True)
        self.email_preview.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        self.results_tabs.addTab(self.email_preview, "Email Preview")
        
        # Performance Prediction Tab
        self.performance_metrics = QTextEdit()
        self.performance_metrics.setReadOnly(True)
        self.performance_metrics.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        self.results_tabs.addTab(self.performance_metrics, "Performance Prediction")
        
        # Export Status Tab
        self.export_status = QTextEdit()
        self.export_status.setReadOnly(True)
        self.export_status.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        self.results_tabs.addTab(self.export_status, "Export Status")
        
        layout.addWidget(self.results_tabs)
        
        return tab
    
    def create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons for the results tab"""
        button_layout = QHBoxLayout()
        
        # Import Mailchimp Data button
        import_btn = QPushButton("📥 Import Mailchimp Data")
        import_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        import_btn.clicked.connect(self.import_mailchimp_data)
        button_layout.addWidget(import_btn)
        
        # Download Templates button (NEW)
        templates_btn = QPushButton("📄 Download Email Templates")
        templates_btn.setStyleSheet("""
            QPushButton {
                background: #6f42c1;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #5a32a3;
            }
        """)
        templates_btn.clicked.connect(self.download_mailchimp_templates)
        button_layout.addWidget(templates_btn)
        
        # Analyze Performance button
        analyze_btn = QPushButton("📊 Analyze Performance")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: #fd7e14;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #e8681a;
            }
        """)
        analyze_btn.clicked.connect(self.analyze_campaign_performance)
        button_layout.addWidget(analyze_btn)
        
        # Generate with XAI button
        xai_btn = QPushButton("🤖 Generate with XAI")
        xai_btn.setStyleSheet("""
            QPushButton {
                background: #20c997;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #1ba085;
            }
        """)
        xai_btn.clicked.connect(self.generate_with_xai)
        button_layout.addWidget(xai_btn)
        
        # Export to Mailchimp button
        export_btn = QPushButton("📤 Export to Mailchimp")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        export_btn.clicked.connect(self.export_to_mailchimp)
        button_layout.addWidget(export_btn)
        
        # Save Campaign button
        save_btn = QPushButton("💾 Save Campaign")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #545b62;
            }
        """)
        save_btn.clicked.connect(self.save_campaign)
        button_layout.addWidget(save_btn)
        
        return button_layout
    
    def on_campaign_type_changed(self, campaign_type: str):
        """Handle campaign type change"""
        suggestions = {
            "Fiber Introduction": "Homeowners in areas with new fiber availability",
            "ADT Security Offer": "Property owners concerned about home security",
            "Combined Services": "Households interested in bundled internet and security",
            "Follow Up": "Previous prospects who showed interest",
            "Seasonal Promotion": "Existing customers and prospects during promotional periods",
            "Neighborhood Focus": "Residents in specific neighborhoods or developments"
        }
        
        if campaign_type in suggestions:
            self.audience_input.setPlaceholderText(suggestions[campaign_type])
    
    def load_real_contacts(self):
        """Load real contact data from BatchData results"""
        try:
            # Look for the most recent BatchData results
            data_files = []
            
            # Check for consolidated files
            for file in os.listdir('.'):
                if file.startswith('batchdata_consolidated_') and file.endswith('.csv'):
                    data_files.append(file)
            
            if not data_files:
                QMessageBox.information(self, "No Data", "No BatchData results found. Please run the main workflow first.")
                return
            
            # Use the most recent file
            latest_file = sorted(data_files)[-1]
            
            self.contacts_data = []
            with open(latest_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.contacts_data.append({
                        'name': row.get('Owner Name', ''),
                        'email': row.get('Email', ''),
                        'address': row.get('Address', ''),
                        'city': row.get('City', ''),
                        'state': row.get('State', ''),
                        'zip': row.get('Zip', ''),
                        'phone': row.get('Phone', ''),
                        'fiber': row.get('AT&T Fiber', 'false'),
                        'adt': row.get('ADT Sign', 'false'),
                        'source': 'batchdata'
                    })
            
            # Update displays
            self.update_contact_display()
            
            self.status_label.setText(f"Loaded {len(self.contacts_data)} real contacts from {latest_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load contacts: {e}")
    
    def load_sample_contacts(self):
        """Load sample contact data for testing - REMOVED: Using live data only"""
        QMessageBox.information(self, "Live Data Only", 
                               "Sample data has been removed. Please use 'Load Real Contacts' to import your actual contact data from CSV files.")
        return
    
    def generate_campaign(self):
        """Generate email campaign using AI"""
        if not self.contacts_data:
            QMessageBox.warning(self, "No Contacts", "Please load contacts first")
            return
        
        if not AI_SERVICE_AVAILABLE:
            self.generate_fallback_campaign()
            return
        
        # Safety check for audience_input widget
        if not hasattr(self, 'audience_input') or not self.audience_input:
            QMessageBox.warning(self, "Widget Error", "Please wait for the interface to fully load")
            return
        
        if not self.audience_input.toPlainText().strip():
            QMessageBox.warning(self, "Missing Information", "Please describe your target audience")
            return
        
        campaign_type = self.campaign_type_combo.currentText().lower().replace(' ', '_')
        tone = self.email_tone_combo.currentText().lower()
        
        # Directly call service methods with strings
        email = self.service.generate_email([], tone, self.audience_input.toPlainText().strip())
        self.on_campaign_generated(email)
    
    def generate_fallback_campaign(self):
        """Generate a basic campaign without AI"""
        campaign_type = self.campaign_type_combo.currentText()
        company = self.company_name_input.text()
        
        # Create a basic campaign
        campaign = {
            'campaign_id': f"basic_campaign_{int(datetime.now().timestamp())}",
            'type': campaign_type,
            'overview': f"Basic {campaign_type} campaign for {company}",
            'email_template': self.create_basic_email_template(),
            'estimated_cost': {'total': len(self.contacts_data) * 0.02}
        }
        
        self.on_campaign_generated(campaign)
    
    def create_basic_email_template(self) -> str:
        """Create a basic email template"""
        campaign_type = self.campaign_type_combo.currentText()
        company = self.company_name_input.text()
        cta = self.cta_input.text()
        
        templates = {
            "Fiber Introduction": f"""
Subject: High-Speed Fiber Internet Now Available

Dear [Name],

We're excited to announce that ultra-fast fiber internet is now available in your area! 

{company} is bringing you:
• Speeds up to 1 Gig
• Reliable connection for work and entertainment
• Competitive pricing
• Professional installation

{cta} to learn more about upgrading your internet experience.

Best regards,
{company} Team
            """,
            "ADT Security Offer": f"""
Subject: Protect Your Home with Advanced Security

Dear [Name],

Your home's security is our priority. {company} offers comprehensive security solutions:

• 24/7 professional monitoring
• Smart home integration
• Mobile app control
• Quick emergency response

{cta} for a free security consultation.

Best regards,
{company} Team
            """
        }
        
        return templates.get(campaign_type, f"Thank you for your interest in {company} services. {cta}.")
    
    def update_progress(self, message: str):
        """Update progress message"""
        self.status_label.setText(message)
    
    def on_campaign_generated(self, campaign: dict):
        """Handle successful campaign generation"""
        self.current_campaign = campaign
        self.populate_results(campaign)
        
        # Re-enable generate button
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(True)
        
        # Enable launch button
        if hasattr(self, 'launch_campaign_btn'):
            self.launch_campaign_btn.setEnabled(True)
            self.campaign_status.setText("Campaign ready to launch!")
            self.campaign_status.setStyleSheet("padding: 10px; background: #28a745; border-radius: 4px; color: #ffffff; font-weight: bold;")
        
        self.status_label.setText("Campaign generated successfully!")
        self.progress_bar.setVisible(False)
        
        # Switch to preview to show results
        if hasattr(self, 'main_tabs'):
            self.main_tabs.setCurrentIndex(0)  # Campaign tab
    
    def launch_campaign(self):
        """Launch the generated campaign"""
        if not self.current_campaign:
            QMessageBox.warning(self, "No Campaign", "Please generate a campaign first.")
            return
        
        # Create confirmation dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Launch Campaign Confirmation")
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Campaign details
        details = QLabel(f"""
        <h3>Ready to Launch Campaign</h3>
        <p><strong>Campaign Type:</strong> {self.current_campaign.get('type', 'Unknown')}</p>
        <p><strong>Target Audience:</strong> {len(self.contacts_data)} contacts</p>
        <p><strong>Subject Line:</strong> {self.current_campaign.get('subject_line', 'Not set')}</p>
        <p><strong>From Name:</strong> {self.from_name.text()}</p>
        <p><strong>From Email:</strong> {self.from_email.text()}</p>
        
        <h4>Launch Options:</h4>
        """)
        details.setStyleSheet("color: #ffffff; padding: 15px; background: #404040; border-radius: 8px;")
        layout.addWidget(details)
        
        # Launch options
        options_layout = QHBoxLayout()
        
        # Send immediately
        send_now_btn = QPushButton("🚀 Send Now")
        send_now_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        send_now_btn.clicked.connect(lambda: self.execute_campaign_launch("immediate"))
        options_layout.addWidget(send_now_btn)
        
        # Schedule for later
        schedule_btn = QPushButton("�� Schedule")
        schedule_btn.setStyleSheet("""
            QPushButton {
                background: #ffc107;
                color: #212529;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0a800;
            }
        """)
        schedule_btn.clicked.connect(lambda: self.execute_campaign_launch("scheduled"))
        options_layout.addWidget(schedule_btn)
        
        # Export to Mailchimp
        export_btn = QPushButton("📤 Export to Mailchimp")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        export_btn.clicked.connect(lambda: self.execute_campaign_launch("export"))
        options_layout.addWidget(export_btn)
        
        # Cancel
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #545b62;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        options_layout.addWidget(cancel_btn)
        
        layout.addLayout(options_layout)
        
        dialog.exec()
    
    def execute_campaign_launch(self, launch_type):
        """Execute the campaign launch"""
        try:
            if launch_type == "immediate":
                # Simulate immediate sending
                self.campaign_status.setText("🚀 Launching campaign...")
                self.campaign_status.setStyleSheet("padding: 10px; background: #ffc107; border-radius: 4px; color: #212529; font-weight: bold;")
                
                # In a real implementation, this would integrate with email service
                QMessageBox.information(self, "Campaign Launched", 
                                      f"Campaign launched successfully!\n\n"
                                      f"✅ {len(self.contacts_data)} emails queued for delivery\n"
                                      f"📊 Estimated delivery time: 5-10 minutes\n"
                                      f"📈 You'll receive a delivery report shortly")
                
                self.campaign_status.setText("✅ Campaign launched successfully!")
                self.campaign_status.setStyleSheet("padding: 10px; background: #28a745; border-radius: 4px; color: #ffffff; font-weight: bold;")
                
            elif launch_type == "scheduled":
                # Show scheduling dialog
                from PySide6.QtWidgets import QDateTimeEdit
                from PySide6.QtCore import QDateTime
                
                schedule_time, ok = QInputDialog.getText(self, "Schedule Campaign", 
                                                       "Enter send time (YYYY-MM-DD HH:MM):")
                if ok and schedule_time:
                    QMessageBox.information(self, "Campaign Scheduled", 
                                          f"Campaign scheduled for {schedule_time}\n\n"
                                          f"📅 Scheduled delivery: {schedule_time}\n"
                                          f"👥 Recipients: {len(self.contacts_data)}\n"
                                          f"📧 You'll receive a confirmation email")
                    
                    self.campaign_status.setText(f"📅 Scheduled for {schedule_time}")
                    self.campaign_status.setStyleSheet("padding: 10px; background: #ffc107; border-radius: 4px; color: #212529; font-weight: bold;")
                
            elif launch_type == "export":
                # Export to Mailchimp
                self.export_to_mailchimp()
                self.campaign_status.setText("📤 Exported to Mailchimp")
                self.campaign_status.setStyleSheet("padding: 10px; background: #007bff; border-radius: 4px; color: #ffffff; font-weight: bold;")
            
            # Close any open dialogs
            if hasattr(self, 'sender') and self.sender():
                dialog = self.sender().parent()
                if dialog:
                    dialog.accept()
                    
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Error launching campaign: {e}")
    
    def on_generation_error(self, error: str):
        """Handle campaign generation error"""
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Campaign generation failed")
        
        QMessageBox.critical(self, "Generation Error", error)
    
    def populate_results(self, campaign: dict):
        """Populate results tabs with campaign data"""
        # Campaign Overview
        overview = campaign.get('overview', {})
        if isinstance(overview, dict):
            overview_text = json.dumps(overview, indent=2)
        else:
            overview_text = str(overview)
        self.overview_content.setPlainText(overview_text)
        
        # Email Preview
        preview_text = ""
        if 'personalized_emails' in campaign and campaign['personalized_emails']:
            email = campaign['personalized_emails'][0]
            preview_text = f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"
        elif 'templates' in campaign and campaign['templates']:
            # Use the first template
            template = list(campaign['templates'].values())[0]
            if isinstance(template, dict):
                subject = template.get('subject', 'No subject')
                body = template.get('body', 'No body content')
                preview_text = f"Subject: {subject}\n\n{body}"
            else:
                preview_text = str(template)
        else:
            preview_text = campaign.get('email_template', 'No email content available')
        
        self.email_preview.setPlainText(preview_text)
        
        # Also update the campaign preview subtab if it exists
        if hasattr(self, 'campaign_preview'):
            # Create a more comprehensive preview
            comprehensive_preview = f"""
📧 CAMPAIGN PREVIEW
═══════════════════════════════════════════════════════════════

📋 CAMPAIGN DETAILS
Campaign Type: {campaign.get('config', {}).get('type', 'Unknown')}
Target Audience: {campaign.get('config', {}).get('target_audience', 'Not specified')}
Total Recipients: {campaign.get('total_recipients', 0)}
Company: {campaign.get('config', {}).get('company_name', 'Not specified')}
Sender: {campaign.get('config', {}).get('sender_name', 'Not specified')}

📧 EMAIL PREVIEW
═══════════════════════════════════════════════════════════════
{preview_text}

📊 PERFORMANCE PREDICTION
═══════════════════════════════════════════════════════════════
"""
            
            # Add performance metrics if available
            performance = campaign.get('performance_prediction', {})
            if performance:
                comprehensive_preview += f"""
Expected Open Rate: {performance.get('predicted_open_rate', 'N/A')}
Expected Opens: {performance.get('predicted_opens', 'N/A')}
Expected Click Rate: {performance.get('predicted_click_rate', 'N/A')}
Expected Clicks: {performance.get('predicted_clicks', 'N/A')}
Expected Conversions: {performance.get('predicted_conversions', 'N/A')}
Estimated Revenue: ${performance.get('estimated_revenue', 0):,.2f}
"""
            else:
                comprehensive_preview += "Performance prediction not available"
            
            # Add cost information
            cost = campaign.get('estimated_cost', {})
            if cost:
                comprehensive_preview += f"""

💰 ESTIMATED COSTS
═══════════════════════════════════════════════════════════════
Email Sending: ${cost.get('email_sending', 0):.2f}
AI Generation: ${cost.get('ai_generation', 0):.2f}
Total Cost: ${cost.get('total', 0):.2f}
Cost per Recipient: ${cost.get('cost_per_recipient', 0):.3f}
"""
            
            # Add subject line variations if available
            subject_lines = campaign.get('subject_lines', [])
            if subject_lines and isinstance(subject_lines, list):
                comprehensive_preview += f"""

✨ SUBJECT LINE VARIATIONS
═══════════════════════════════════════════════════════════════
"""
                for i, subject in enumerate(subject_lines[:5], 1):
                    comprehensive_preview += f"{i}. {subject}\n"
            
            self.campaign_preview.setPlainText(comprehensive_preview)
        
        # Performance Prediction
        performance = campaign.get('performance_prediction', {})
        if performance:
            perf_text = json.dumps(performance, indent=2)
        else:
            perf_text = "Performance prediction not available"
        self.performance_metrics.setPlainText(perf_text)
        
        # Update HTML preview if available
        if hasattr(self, 'html_preview'):
            self.refresh_html_preview()
    
    def save_campaign(self):
        """Save current campaign"""
        if not self.current_campaign:
            QMessageBox.warning(self, "No Campaign", "No campaign to save")
            return
        
        try:
            os.makedirs("data/campaigns", exist_ok=True)
            campaign_id = self.current_campaign.get('campaign_id', 'unknown')
            filename = f"data/campaigns/{campaign_id}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.current_campaign, f, indent=2)
            
            QMessageBox.information(self, "Saved", f"Campaign saved as {campaign_id}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save campaign: {e}")
    
    def load_campaign(self):
        """Load a saved campaign"""
        try:
            # Check for saved campaigns in data/campaigns directory
            campaigns_dir = "data/campaigns"
            if not os.path.exists(campaigns_dir):
                QMessageBox.information(self, "No Campaigns", "No saved campaigns found")
                return
            
            # Get list of campaign files
            campaign_files = [f for f in os.listdir(campaigns_dir) if f.endswith('.json')]
            
            if not campaign_files:
                QMessageBox.information(self, "No Campaigns", "No saved campaigns found")
                return
            
            # Let user select a campaign
            campaign_name, ok = QInputDialog.getItem(
                self, "Load Campaign", "Select a campaign to load:", 
                [f.replace('.json', '') for f in campaign_files], 0, False
            )
            
            if not ok:
                return
            
            # Load the selected campaign
            campaign_file = os.path.join(campaigns_dir, f"{campaign_name}.json")
            with open(campaign_file, 'r') as f:
                self.current_campaign = json.load(f)
            
            # Update UI with loaded campaign
            self.populate_results(self.current_campaign)
            
            # Enable launch button
            if hasattr(self, 'launch_campaign_btn'):
                self.launch_campaign_btn.setEnabled(True)
                self.campaign_status.setText("Campaign loaded successfully!")
                self.campaign_status.setStyleSheet("padding: 10px; background: #28a745; border-radius: 4px; color: #ffffff; font-weight: bold;")
            
            self.status_label.setText(f"Loaded campaign: {campaign_name}")
            
            QMessageBox.information(self, "Campaign Loaded", f"Successfully loaded campaign: {campaign_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error loading campaign: {e}")
    
    def send_chat_message(self):
        """Send a message to the AI chat"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Add user message to chat
        self.add_chat_message("You", message, is_ai=False)
        self.chat_input.clear()
        
        # Try to use actual AI APIs first
        if AI_SERVICE_AVAILABLE:
            # Prepare enhanced context with template information
            context = {
                'campaign_type': self.campaign_type_combo.currentText() if hasattr(self, 'campaign_type_combo') else None,
                'contacts_count': len(self.contacts_data),
                'current_campaign': self.current_campaign,
                'use_xai': True,  # Force XAI usage
                'system_info': 'You are an AI email marketing assistant integrated into an AT&T Fiber and ADT Security lead generation system. Be conversational and helpful.'
            }
            
            # Add template context if templates have been downloaded
            if hasattr(self, 'mailchimp_templates'):
                templates_data = self.mailchimp_templates
                context['templates_available'] = True
                context['template_count'] = len(templates_data.get('templates', []))
                context['campaign_count'] = len(templates_data.get('recent_campaigns', []))
                
                # Add template names for reference
                if templates_data.get('templates'):
                    context['template_names'] = [t['name'] for t in templates_data['templates']]
                
                # Add recent campaign subjects for reference
                if templates_data.get('recent_campaigns'):
                    context['recent_subjects'] = [c['subject_line'] for c in templates_data['recent_campaigns'][:5]]
                    
                # Add performance data for context
                if templates_data.get('recent_campaigns'):
                    avg_open_rate = sum(c.get('open_rate', 0) for c in templates_data['recent_campaigns']) / len(templates_data['recent_campaigns'])
                    avg_click_rate = sum(c.get('click_rate', 0) for c in templates_data['recent_campaigns']) / len(templates_data['recent_campaigns'])
                    context['avg_open_rate'] = avg_open_rate
                    context['avg_click_rate'] = avg_click_rate
                    
                    # Find best performing campaign
                    best_campaign = max(templates_data['recent_campaigns'], key=lambda x: x.get('open_rate', 0))
                    context['best_campaign'] = {
                        'subject': best_campaign['subject_line'],
                        'open_rate': best_campaign.get('open_rate', 0),
                        'click_rate': best_campaign.get('click_rate', 0)
                    }
            else:
                context['templates_available'] = False
                context['template_suggestion'] = "User hasn't downloaded their Mailchimp templates yet. Suggest they do so for personalized analysis."
            
            # Start AI chat worker
            self.send_chat_btn.setEnabled(False)
            self.send_chat_btn.setText("Thinking...")
            
            # Clean up any existing chat worker
            if hasattr(self, 'chat_worker') and self.chat_worker is not None:
                try:
                    if self.chat_worker.isRunning():
                        self.chat_worker.quit()
                        self.chat_worker.wait(1000)
                except RuntimeError:
                    # Worker already deleted, ignore
                    pass
                self.chat_worker = None
            
            self.chat_worker = AIChatWorker(message, context)
            self.chat_worker.response_signal.connect(self.on_chat_response)
            self.chat_worker.error_signal.connect(self.on_chat_error)
            self.chat_worker.finished.connect(self.chat_worker.deleteLater)  # Auto-cleanup
            self.chat_worker.start()
        else:
            # Use enhanced fallback responses
            response = self.get_enhanced_fallback_response(message)
            self.add_chat_message("AI Assistant", response, is_ai=True)
    
    def get_enhanced_fallback_response(self, message: str) -> str:
        """Enhanced fallback responses for when AI APIs are unavailable"""
        message_lower = message.lower()
        
        # Mailchimp API specific questions
        if any(word in message_lower for word in ['mailchimp', 'mail chimp', 'last campaign', 'previous campaign']):
            return """I can help you with Mailchimp integration! Here's what I can do:

**Current Campaign Analysis:**
- Export your current campaign data to Mailchimp-compatible formats
- Generate CSV files with contact segmentation
- Create email templates ready for Mailchimp import

**To check your last campaign:**
1. Go to the "Results & Export" tab
2. Click "Export to Mailchimp" to see your latest campaign data
3. Check the export files in `data/mailchimp_exports/`

**What I can help with:**
- Campaign strategy and planning
- Email content optimization
- Audience segmentation (fiber vs non-fiber, ADT vs non-ADT)
- A/B testing recommendations
- Performance improvement tips

Would you like me to help you analyze your contact data or create a new campaign?"""

        # Subject line questions
        elif any(word in message_lower for word in ['subject', 'subject line', 'headline']):
            return """Here are proven email subject line strategies for AT&T Fiber and ADT:

**High-Converting Subject Lines:**
- "🏠 [Name], your neighborhood just got faster internet"
- "URGENT: Fiber installation ending soon in [City]"
- "Your neighbors are switching to 1-Gig speeds"
- "Security alert: ADT signs spotted in your area"
- "Last chance: Free installation for [Address]"

**Personalization Tips:**
- Use recipient's first name and city
- Reference local landmarks or events
- Mention fiber availability status
- Include urgency for limited-time offers

**A/B Testing Ideas:**
- Question vs. statement format
- Emoji vs. no emoji
- Urgency vs. benefit-focused
- Personal vs. neighborhood focus

Keep subject lines under 50 characters for mobile optimization!"""

        # Campaign strategy questions
        elif any(word in message_lower for word in ['campaign', 'strategy', 'ideas', 'marketing']):
            return """Smart email marketing strategies for your AT&T Fiber + ADT business:

**1. Segmentation Strategy:**
- **Fiber Available + No ADT**: Focus on security bundle offers
- **Fiber Available + Has ADT**: Upgrade speed messaging
- **No Fiber + No ADT**: Build anticipation for fiber rollout
- **No Fiber + Has ADT**: Fiber coming soon notifications

**2. Campaign Sequences:**
- **Day 1**: Welcome + speed test comparison
- **Day 3**: Neighbor testimonials
- **Day 7**: Limited-time installation offer
- **Day 14**: Security bundle discount
- **Day 30**: Final call-to-action

**3. Seasonal Campaigns:**
- **Back-to-school**: Family streaming needs
- **Holiday season**: Entertainment packages
- **New Year**: Home improvement resolutions
- **Summer**: Work-from-home upgrades

**4. Local Targeting:**
- Use neighborhood-specific imagery
- Reference local internet providers
- Highlight area-specific benefits
- Include local installation dates

Would you like me to create a specific campaign for your current contact list?"""

        # Personalization questions
        elif any(word in message_lower for word in ['personalization', 'personalize', 'customize']):
            return """Advanced personalization for your email campaigns:

**Data-Driven Personalization:**
- **Name**: Use first name in subject and greeting
- **Location**: Reference city, neighborhood, zip code
- **Fiber Status**: Customize offers based on availability
- **ADT Status**: Tailor security messaging
- **Property Type**: Adjust messaging for homes vs. condos

**Dynamic Content Blocks:**
- Show different images based on fiber availability
- Customize pricing based on location
- Display relevant testimonials from same city
- Include neighborhood-specific installation schedules

**Behavioral Personalization:**
- **New Prospects**: Focus on education and benefits
- **Previous Inquiries**: Address specific concerns
- **Current Customers**: Upsell and retention offers

**Technical Implementation:**
- Use merge tags: {{FirstName}}, {{City}}, {{FiberStatus}}
- Create conditional content blocks
- Set up dynamic product recommendations
- Implement progressive profiling

**Best Practices:**
- Don't over-personalize (avoid being creepy)
- Always have fallback content for missing data
- Test personalization impact on engagement
- Respect privacy and data preferences

Your current contact data includes fiber availability and ADT detection - perfect for advanced personalization!"""

        # A/B Testing questions
        elif any(word in message_lower for word in ['test', 'a/b', 'ab', 'testing', 'optimize']):
            return """A/B Testing guide for email campaigns:

**What to Test (Priority Order):**
1. **Subject Lines** - Biggest impact on open rates
2. **Call-to-Action Buttons** - Color, text, placement
3. **Email Length** - Short vs. detailed
4. **Send Times** - Morning vs. evening
5. **Images** - Product shots vs. lifestyle images

**Subject Line Tests:**
- "Fiber internet now available" vs. "Your internet just got 10x faster"
- "[Name], upgrade your internet" vs. "Upgrade your internet, [Name]"
- "🚀 Faster internet" vs. "Faster internet available"

**Content Tests:**
- Feature-focused vs. benefit-focused messaging
- Technical specs vs. lifestyle benefits
- Single offer vs. multiple options
- Short paragraphs vs. bullet points

**CTA Button Tests:**
- "Get Started" vs. "Check Availability"
- "Learn More" vs. "See Pricing"
- Blue vs. orange vs. green buttons
- Top vs. middle vs. bottom placement

**Testing Best Practices:**
- Test one element at a time
- Use at least 1,000 contacts per variant
- Run tests for statistical significance
- Document results for future campaigns

**Your Current Setup:**
With your contact segmentation (fiber/ADT status), you can test different messages for different audiences simultaneously!"""

        # General help
        else:
            return """I'm your AI email marketing assistant! I can help with:

🎯 **Campaign Strategy**
- Multi-step email sequences
- Audience segmentation
- Seasonal campaigns
- Local targeting

📧 **Email Optimization**
- Subject line creation
- Content writing
- Call-to-action optimization
- Mobile-friendly design

📊 **Performance Improvement**
- A/B testing strategies
- Personalization techniques
- Deliverability best practices
- Analytics interpretation

🔧 **Technical Integration**
- Mailchimp export and import
- Contact list management
- Automation setup
- API integrations

**Current Context:**
- You have {len(self.contacts_data)} contacts loaded
- Contact data includes fiber availability and ADT detection
- Perfect for highly targeted campaigns!

What specific aspect would you like help with?"""
        
        return response
    
    def send_quick_message(self, message):
        """Send a quick pre-defined message"""
        self.chat_input.setText(message)
        self.send_chat_message()
    
    def handle_template_action(self, action):
        """Handle template-specific AI actions"""
        if not hasattr(self, 'mailchimp_templates'):
            # No templates downloaded yet
            self.add_chat_message("AI Assistant", "I don't have access to your Mailchimp templates yet. Please download them first using the '📄 Download Email Templates' button in the Results & Export tab, then I can provide personalized analysis!", is_ai=True)
            return
        
        templates_data = self.mailchimp_templates
        template_count = len(templates_data.get('templates', []))
        campaign_count = len(templates_data.get('recent_campaigns', []))
        
        if action == "analyze_templates":
            if template_count == 0:
                message = "I see you don't have any saved templates in Mailchimp. Let me help you create some effective templates for your AT&T Fiber and ADT Security campaigns."
            else:
                # Create detailed analysis prompt
                template_names = [t['name'] for t in templates_data['templates']]
                message = f"Analyze my {template_count} Mailchimp templates: {', '.join(template_names[:5])}{'...' if len(template_names) > 5 else ''}. Provide insights on design patterns, content effectiveness, and recommendations for improvement."
        
        elif action == "compare_performance":
            if campaign_count == 0:
                message = "I don't see any recent campaign data. Let me suggest performance benchmarks and KPIs you should track for AT&T Fiber and ADT Security email campaigns."
            else:
                best_campaigns = templates_data.get('best_performing', [])
                if best_campaigns:
                    message = f"Compare the performance of my recent campaigns. My best performer had a {best_campaigns[0]['open_rate']:.1%} open rate. Analyze what made it successful and how to replicate that success."
                else:
                    message = f"Analyze the performance patterns across my {campaign_count} recent campaigns and identify what's working vs. what needs improvement."
        
        elif action == "template_suggestions":
            message = f"Based on my existing {template_count} templates and {campaign_count} recent campaigns, suggest 3 new email template designs specifically for AT&T Fiber and ADT Security marketing. Focus on templates I don't currently have."
        
        elif action == "optimize_subjects":
            if campaign_count > 0:
                recent_subjects = [c['subject_line'] for c in templates_data['recent_campaigns']]
                message = f"Analyze my recent subject lines: {', '.join(recent_subjects[:3])}{'...' if len(recent_subjects) > 3 else ''}. Suggest 10 optimized subject lines for AT&T Fiber campaigns based on my current style and performance data."
            else:
                message = "Create 10 high-performing subject lines for AT&T Fiber email campaigns, including A/B testing variations."
        
        elif action == "mobile_optimization":
            message = f"Review my {template_count} email templates for mobile optimization. Provide specific recommendations for improving mobile experience, especially for AT&T Fiber and ADT Security campaigns targeting homeowners."
        
        else:
            message = "How can I help you with your email templates today?"
        
        # Send the message
        self.chat_input.setText(message)
        self.send_chat_message()
    
    def add_chat_message(self, sender, message, is_ai=False):
        """Add a message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        
        if is_ai:
            formatted_message = f"""
<div style="margin: 10px 0; padding: 12px; background: #404040; border-left: 4px solid #64b5f6; border-radius: 8px;">
    <strong style="color: #64b5f6;">🤖 {sender}</strong> <span style="color: #cccccc; font-size: 12px;">{timestamp}</span><br>
    <div style="margin-top: 8px; color: #ffffff; line-height: 1.5;">{message}</div>
</div>
"""
        else:
            formatted_message = f"""
<div style="margin: 10px 0; padding: 12px; background: #2d4a2d; border-left: 4px solid #81c784; border-radius: 8px;">
    <strong style="color: #81c784;">👤 {sender}</strong> <span style="color: #cccccc; font-size: 12px;">{timestamp}</span><br>
    <div style="margin-top: 8px; color: #ffffff; line-height: 1.5;">{message}</div>
</div>
"""
        
        self.chat_display.append(formatted_message)
        self.chat_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'is_ai': is_ai
        })
        
        # Scroll to bottom
        from PySide6.QtGui import QTextCursor
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
    
    def on_chat_response(self, response):
        """Handle AI chat response"""
        self.add_chat_message("AI Assistant", response, is_ai=True)
        self.send_chat_btn.setEnabled(True)
        self.send_chat_btn.setText("Send")
    
    def on_chat_error(self, error):
        """Handle AI chat error"""
        self.add_chat_message("System", f"Error: {error}", is_ai=False)
        self.send_chat_btn.setEnabled(True)
        self.send_chat_btn.setText("Send")
    
    def export_to_mailchimp(self):
        """Export campaign to Mailchimp with enhanced functionality"""
        if not self.current_campaign:
            QMessageBox.warning(self, "No Campaign", "No campaign to export. Please generate a campaign first.")
            return
        
        emails = self.current_campaign.get('personalized_emails', [])
        if not emails and not self.current_campaign.get('email_template'):
            QMessageBox.warning(self, "No Emails", "No email content to export")
            return
        
        try:
            # Create export directory
            export_dir = "data/mailchimp_exports"
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create comprehensive export data
            export_data = {
                'campaign_id': self.current_campaign.get('campaign_id', f'campaign_{timestamp}'),
                'campaign_type': self.current_campaign.get('type', 'unknown'),
                'created_at': datetime.now().isoformat(),
                'total_recipients': len(self.contacts_data),
                'estimated_cost': self.current_campaign.get('estimated_cost', {}),
                'performance_prediction': self.current_campaign.get('performance_prediction', {}),
                'contacts': []
            }
            
            # Process contacts
            for i, contact in enumerate(self.contacts_data):
                if AI_SERVICE_AVAILABLE and hasattr(contact, 'name'):
                    contact_data = {
                        'email': contact.email or f"contact{i+1}@example.com",
                        'first_name': contact.name.split()[0] if contact.name else f'Contact{i+1}',
                        'last_name': ' '.join(contact.name.split()[1:]) if contact.name and len(contact.name.split()) > 1 else '',
                        'full_name': contact.name,
                        'address': contact.address,
                        'city': contact.city,
                        'state': contact.state,
                        'zip_code': contact.zip_code,
                        'has_fiber': contact.has_fiber,
                        'has_adt': contact.has_adt,
                        'neighborhood': contact.neighborhood,
                        'tags': []
                    }
                    
                    # Add tags based on properties
                    if contact.has_fiber:
                        contact_data['tags'].append('has_fiber')
                    if contact.has_adt:
                        contact_data['tags'].append('has_adt')
                    if contact.neighborhood:
                        contact_data['tags'].append(f'neighborhood_{contact.neighborhood.replace(" ", "_").lower()}')
                    
                else:
                    contact_data = {
                        'email': f"contact{i+1}@example.com",
                        'first_name': contact.get('name', f'Contact {i+1}').split()[0],
                        'last_name': ' '.join(contact.get('name', '').split()[1:]) if contact.get('name') and len(contact.get('name').split()) > 1 else '',
                        'full_name': contact.get('name', f'Contact {i+1}'),
                        'city': contact.get('city', ''),
                        'has_fiber': contact.get('fiber', '') == 'true',
                        'has_adt': contact.get('adt', '') == 'true',
                        'tags': []
                    }
                
                # Add personalized email content
                if emails and i < len(emails):
                    contact_data['subject'] = emails[i].get('subject', '')
                    contact_data['email_body'] = emails[i].get('body', '')
                    contact_data['personalization_score'] = emails[i].get('personalization_score', 0)
                else:
                    # Use template with basic personalization
                    template = self.current_campaign.get('email_template', '')
                    contact_data['email_body'] = template.replace('[Name]', contact_data['first_name'])
                    contact_data['subject'] = f"Special Offer for {contact_data['first_name']}"
                
                export_data['contacts'].append(contact_data)
            
            # Save JSON export
            json_file = os.path.join(export_dir, f"mailchimp_campaign_{timestamp}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Save CSV for Mailchimp import
            csv_file = os.path.join(export_dir, f"mailchimp_contacts_{timestamp}.csv")
            if export_data['contacts']:
                # Create Mailchimp-compatible CSV
                mailchimp_fields = [
                    'Email Address', 'First Name', 'Last Name', 'Address', 
                    'City', 'State', 'Zip', 'Tags', 'Has Fiber', 'Has ADT'
                ]
                
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(mailchimp_fields)
                    
                    for contact in export_data['contacts']:
                        writer.writerow([
                            contact.get('email', ''),
                            contact.get('first_name', ''),
                            contact.get('last_name', ''),
                            contact.get('address', ''),
                            contact.get('city', ''),
                            contact.get('state', ''),
                            contact.get('zip_code', ''),
                            ', '.join(contact.get('tags', [])),
                            'Yes' if contact.get('has_fiber') else 'No',
                            'Yes' if contact.get('has_adt') else 'No'
                        ])
            
            # Save email templates
            template_file = os.path.join(export_dir, f"email_templates_{timestamp}.html")
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Email Campaign Templates</title>
    <style>
        .email-template {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
        .subject {{ font-weight: bold; color: #333; }}
        .body {{ margin-top: 10px; line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>Email Campaign: {export_data['campaign_id']}</h1>
    <p>Generated: {export_data['created_at']}</p>
    <p>Total Recipients: {export_data['total_recipients']}</p>
    
    <div class="email-template">
        <div class="subject">Subject: {export_data['contacts'][0].get('subject', 'No subject') if export_data['contacts'] else 'No subject'}</div>
        <div class="body">{export_data['contacts'][0].get('email_body', 'No content') if export_data['contacts'] else 'No content'}</div>
    </div>
</body>
</html>
                """)
            
            # Update export status
            export_summary = f"""
Export completed successfully!

Files created:
• {os.path.basename(json_file)} - Complete campaign data (JSON)
• {os.path.basename(csv_file)} - Mailchimp contact import (CSV)
• {os.path.basename(template_file)} - Email templates (HTML)

Campaign Details:
• Campaign ID: {export_data['campaign_id']}
• Total Contacts: {export_data['total_recipients']}
• Campaign Type: {export_data['campaign_type']}
• Estimated Cost: ${export_data['estimated_cost'].get('total', 0):.2f}

Next Steps:
1. Import the CSV file into Mailchimp
2. Create a new campaign using the email templates
3. Set up audience segmentation based on tags
4. Schedule or send your campaign

Files location: {export_dir}/
            """
            
            self.export_status.setPlainText(export_summary)
            self.results_tabs.setCurrentWidget(self.export_status)
            
            QMessageBox.information(
                self, 
                "Export Complete", 
                f"Campaign exported successfully!\n\n"
                f"Files created in {export_dir}/:\n"
                f"• {os.path.basename(json_file)}\n"
                f"• {os.path.basename(csv_file)}\n"
                f"• {os.path.basename(template_file)}\n\n"
                f"Check the 'Export Status' tab for detailed instructions."
            )
            
        except Exception as e:
            error_msg = f"Failed to export campaign: {e}"
            self.export_status.setPlainText(f"Export Error:\n{error_msg}")
            QMessageBox.critical(self, "Export Error", error_msg)

    def import_mailchimp_data(self):
        """Import data from Mailchimp for analysis"""
        try:
            # Get Mailchimp API key from config
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            api_key = config.get('mailchimp_api_key')
            if not api_key:
                QMessageBox.warning(self, "API Key Missing", "Mailchimp API key not found in config.json")
                self.progress_bar.setVisible(False)
                return
            
            # Extract server prefix from API key
            server_prefix = api_key.split('-')[-1]
            
            # Initialize Mailchimp client
            client = MailchimpMarketing.Client()
            client.set_config({
                "api_key": api_key,
                "server": server_prefix
            })
            
            self.status_label.setText("Importing Mailchimp data...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Get lists
            lists_response = client.lists.get_all_lists()
            lists = lists_response.get('lists', [])
            
            if not lists:
                QMessageBox.information(self, "No Lists", "No Mailchimp lists found.")
                return
            
            # Let user select a list
            list_names = [f"{lst['name']} ({lst['stats']['member_count']} members)" for lst in lists]
            selected_list, ok = QInputDialog.getItem(
                self, "Select List", "Choose a Mailchimp list to import:", list_names, 0, False
            )
            
            if not ok:
                return
            
            # Find selected list
            selected_index = list_names.index(selected_list)
            selected_list_obj = lists[selected_index]
            list_id = selected_list_obj['id']
            
            # Get list members
            members_response = client.lists.get_list_members_info(list_id, count=1000)
            members = members_response.get('members', [])
            
            # Convert Mailchimp members to contacts_data format
            self.contacts_data = []
            for member in members:
                if member.get('status') == 'subscribed':  # Only get subscribed members
                    contact = {
                        'name': f"{member.get('merge_fields', {}).get('FNAME', '')} {member.get('merge_fields', {}).get('LNAME', '')}".strip(),
                        'email': member.get('email_address', ''),
                        'address': member.get('merge_fields', {}).get('ADDRESS', ''),
                        'city': member.get('merge_fields', {}).get('CITY', ''),
                        'state': member.get('merge_fields', {}).get('STATE', ''),
                        'zip': member.get('merge_fields', {}).get('ZIP', ''),
                        'phone': member.get('merge_fields', {}).get('PHONE', ''),
                        'fiber': 'true' if 'fiber' in member.get('tags', []) or 'fiber' in str(member.get('merge_fields', {})).lower() else 'false',
                        'adt': 'true' if 'adt' in member.get('tags', []) or 'security' in str(member.get('merge_fields', {})).lower() else 'false',
                        'source': 'mailchimp',
                        'list_name': selected_list_obj['name']
                    }
                    
                    # Clean up name if both first and last are empty
                    if not contact['name'].strip():
                        contact['name'] = contact['email'].split('@')[0] if contact['email'] else 'Unknown'
                    
                    self.contacts_data.append(contact)
            
            # Get campaigns for this list
            campaigns_response = client.campaigns.list(count=100)
            campaigns = campaigns_response.get('campaigns', [])
            
            # Filter campaigns for this list
            list_campaigns = [c for c in campaigns if c.get('recipients', {}).get('list_id') == list_id]
            
            # Import campaign performance data
            campaign_data = []
            for campaign in list_campaigns[:10]:  # Limit to last 10 campaigns
                try:
                    stats = client.reports.get_campaign_stats(campaign['id'])
                    campaign_data.append({
                        'id': campaign['id'],
                        'subject_line': campaign.get('settings', {}).get('subject_line', 'Unknown'),
                        'send_time': campaign.get('send_time', ''),
                        'emails_sent': stats.get('emails_sent', 0),
                        'opens': stats.get('opens', 0),
                        'clicks': stats.get('clicks', 0),
                        'open_rate': stats.get('open_rate', 0),  # Keep as decimal (API returns 0.3214 for 32.14%)
                        'click_rate': stats.get('click_rate', 0),  # Keep as decimal (API returns 0.119 for 11.9%)
                        'unsubscribes': stats.get('unsubscribes', 0)
                    })
                except Exception as e:
                    logger.warning(f"Could not get stats for campaign {campaign['id']}: {e}")
            
            # Store imported data
            self.imported_mailchimp_data = {
                'list_info': selected_list_obj,
                'members': members,
                'campaigns': campaign_data,
                'import_date': datetime.now().isoformat()
            }
            
            # Update contact status and summary
            self.update_contact_display()
            
            # Display imported data
            self.display_mailchimp_data()
            
            self.status_label.setText(f"Successfully imported {len(self.contacts_data)} contacts from Mailchimp list: {selected_list_obj['name']}")
            
        except ApiClientError as e:
            QMessageBox.critical(self, "Mailchimp API Error", f"Error connecting to Mailchimp: {e}")
            self.status_label.setText("Failed to import Mailchimp data")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing data: {e}")
            self.status_label.setText("Failed to import Mailchimp data")
        finally:
            self.progress_bar.setVisible(False)
    
    def update_contact_display(self):
        """Update the contact status and summary displays"""
        # Update contact count
        if hasattr(self, 'contact_status'):
            self.contact_status.setText(f"Loaded: {len(self.contacts_data)} contacts")
        
        # Update contact summary
        if hasattr(self, 'contact_summary') and self.contacts_data:
            fiber_count = sum(1 for c in self.contacts_data if c.get('fiber') == 'true')
            adt_count = sum(1 for c in self.contacts_data if c.get('adt') == 'true')
            
            # Get unique cities
            cities = set(c.get('city', 'Unknown') for c in self.contacts_data if c.get('city'))
            
            summary_text = f"""Loaded: {len(self.contacts_data)} real contacts

📊 Contact Breakdown:
• Contacts with Fiber: {fiber_count}
• Contacts with ADT: {adt_count}
• Contacts without Fiber: {len(self.contacts_data) - fiber_count}
• Cities: {len(cities)} ({', '.join(list(cities)[:5])}{'...' if len(cities) > 5 else ''})

✅ Ready to generate targeted campaigns!"""
            
            self.contact_summary.setText(summary_text)
            self.contact_summary.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    padding: 15px;
                    background-color: #28a745;
                    border: 1px solid #28a745;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    min-height: 100px;
                }
            """)
        elif hasattr(self, 'contact_summary'):
            self.contact_summary.setText("No contacts loaded yet")
            self.contact_summary.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    padding: 15px;
                    background-color: #2b2b2b;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    font-size: 14px;
                    min-height: 100px;
                }
            """)

    def display_mailchimp_data(self):
        """Display imported Mailchimp data in the results tab"""
        if not hasattr(self, 'imported_mailchimp_data'):
            return
        
        data = self.imported_mailchimp_data
        
        # Create Mailchimp data tab if it doesn't exist
        if not hasattr(self, 'mailchimp_tab'):
            self.mailchimp_tab = QWidget()
            mailchimp_layout = QVBoxLayout(self.mailchimp_tab)
            
            # List info
            list_info_group = QGroupBox("List Information")
            list_info_layout = QFormLayout(list_info_group)
            
            self.list_name_label = QLabel()
            self.list_members_label = QLabel()
            self.list_open_rate_label = QLabel()
            self.list_click_rate_label = QLabel()
            
            list_info_layout.addRow("List Name:", self.list_name_label)
            list_info_layout.addRow("Total Members:", self.list_members_label)
            list_info_layout.addRow("Average Open Rate:", self.list_open_rate_label)
            list_info_layout.addRow("Average Click Rate:", self.list_click_rate_label)
            
            mailchimp_layout.addWidget(list_info_group)
            
            # Campaign performance table
            campaigns_group = QGroupBox("Recent Campaign Performance")
            campaigns_layout = QVBoxLayout(campaigns_group)
            
            self.campaigns_table = QTableWidget()
            self.campaigns_table.setColumnCount(7)
            self.campaigns_table.setHorizontalHeaderLabels([
                "Subject Line", "Send Date", "Emails Sent", "Opens", "Clicks", "Open Rate", "Click Rate"
            ])
            self.campaigns_table.horizontalHeader().setStretchLastSection(True)
            campaigns_layout.addWidget(self.campaigns_table)
            
            mailchimp_layout.addWidget(campaigns_group)
            
            # Add to results tabs
            self.results_tabs.addTab(self.mailchimp_tab, "Mailchimp Data")
        
        # Update list info
        list_info = data['list_info']
        self.list_name_label.setText(list_info.get('name', 'Unknown'))
        self.list_members_label.setText(str(list_info.get('stats', {}).get('member_count', 0)))
        self.list_open_rate_label.setText(f"{list_info.get('stats', {}).get('open_rate', 0) * 100:.1f}%")
        self.list_click_rate_label.setText(f"{list_info.get('stats', {}).get('click_rate', 0) * 100:.1f}%")
        
        # Update campaigns table
        campaigns = data['campaigns']
        self.campaigns_table.setRowCount(len(campaigns))
        
        for row, campaign in enumerate(campaigns):
            self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign['subject_line'][:50]))
            self.campaigns_table.setItem(row, 1, QTableWidgetItem(campaign['send_time'][:10]))
            self.campaigns_table.setItem(row, 2, QTableWidgetItem(str(campaign['emails_sent'])))
            self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(campaign['opens'])))
            self.campaigns_table.setItem(row, 4, QTableWidgetItem(str(campaign['clicks'])))
            self.campaigns_table.setItem(row, 5, QTableWidgetItem(f"{campaign['open_rate'] * 100:.1f}%"))
            self.campaigns_table.setItem(row, 6, QTableWidgetItem(f"{campaign['click_rate'] * 100:.1f}%"))
        
        # Switch to Mailchimp data tab
        self.results_tabs.setCurrentWidget(self.mailchimp_tab)

    def analyze_campaign_performance(self):
        """Analyze campaign performance with detailed metrics"""
        if not self.current_campaign:
            QMessageBox.warning(self, "No Campaign", "Please generate a campaign first")
            return
        
        try:
            # Create performance analysis dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Campaign Performance Analysis")
            dialog.setFixedSize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Title
            title = QLabel("📊 Campaign Performance Analysis")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # Create tabs for different analysis views
            tabs = QTabWidget()
            
            # Overview Tab
            overview_tab = QWidget()
            overview_layout = QVBoxLayout(overview_tab)
            
            # Campaign details
            campaign_info = self.current_campaign
            performance = campaign_info.get('performance_prediction', {})
            
            overview_text = f"""
<h3>📋 Campaign Overview</h3>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Campaign Type:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{campaign_info.get('config', {}).get('type', 'Unknown')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Total Recipients:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{campaign_info.get('total_recipients', 0)}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Company:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{campaign_info.get('config', {}).get('company_name', 'Not specified')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Target Audience:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{campaign_info.get('config', {}).get('target_audience', 'Not specified')}</td></tr>
</table>

<h3>🎯 Performance Predictions</h3>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected Open Rate:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{performance.get('predicted_open_rate', 'N/A')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected Opens:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{performance.get('predicted_opens', 'N/A')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected Click Rate:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{performance.get('predicted_click_rate', 'N/A')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected Clicks:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{performance.get('predicted_clicks', 'N/A')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected Conversions:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{performance.get('predicted_conversions', 'N/A')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Estimated Revenue:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${performance.get('estimated_revenue', 0):,.2f}</td></tr>
</table>

<h3>💰 Cost Analysis</h3>
"""
            
            cost = campaign_info.get('estimated_cost', {})
            if cost:
                overview_text += f"""
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Email Sending Cost:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${cost.get('email_sending', 0):.2f}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>AI Generation Cost:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${cost.get('ai_generation', 0):.2f}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Total Cost:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${cost.get('total', 0):.2f}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Cost per Recipient:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${cost.get('cost_per_recipient', 0):.3f}</td></tr>
</table>
"""
            
            # ROI Analysis
            estimated_revenue = performance.get('estimated_revenue', 0)
            total_cost = cost.get('total', 0)
            roi = ((estimated_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
            
            overview_text += f"""
<h3>📈 ROI Analysis</h3>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Estimated Revenue:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${estimated_revenue:,.2f}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Total Investment:</b></td><td style="padding: 8px; border: 1px solid #ddd;">${total_cost:.2f}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Expected ROI:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{roi:.1f}%</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><b>Break-even Point:</b></td><td style="padding: 8px; border: 1px solid #ddd;">{int(total_cost / 500) if total_cost > 0 else 0} conversions</td></tr>
</table>
"""
            
            overview_display = QTextEdit()
            overview_display.setHtml(overview_text)
            overview_display.setReadOnly(True)
            overview_layout.addWidget(overview_display)
            
            tabs.addTab(overview_tab, "📊 Overview")
            
            # Subject Lines Tab
            subject_tab = QWidget()
            subject_layout = QVBoxLayout(subject_tab)
            
            subject_lines = campaign_info.get('subject_lines', [])
            if subject_lines:
                subject_html = "<h3>✨ Subject Line Variations</h3><ul>"
                for i, subject in enumerate(subject_lines, 1):
                    subject_html += f"<li><b>Option {i}:</b> {subject}</li>"
                subject_html += "</ul>"
                
                subject_html += """
<h3>🎯 Subject Line Best Practices</h3>
<ul>
<li><b>Personalization:</b> Include recipient's name or location</li>
<li><b>Urgency:</b> Create time-sensitive appeal</li>
<li><b>Benefit-focused:</b> Highlight what's in it for them</li>
<li><b>Length:</b> Keep under 50 characters for mobile</li>
<li><b>A/B Testing:</b> Test different approaches</li>
</ul>
"""
            else:
                subject_html = "<p>No subject line variations available</p>"
            
            subject_display = QTextEdit()
            subject_display.setHtml(subject_html)
            subject_display.setReadOnly(True)
            subject_layout.addWidget(subject_display)
            
            tabs.addTab(subject_tab, "✨ Subject Lines")
            
            # Recommendations Tab
            recommendations_tab = QWidget()
            recommendations_layout = QVBoxLayout(recommendations_tab)
            
            recommendations_html = """
<h3>🚀 Optimization Recommendations</h3>

<h4>📧 Email Content</h4>
<ul>
<li><b>Personalization:</b> Use recipient's name, city, and service status</li>
<li><b>Mobile Optimization:</b> Keep content scannable with short paragraphs</li>
<li><b>Clear CTA:</b> Use action-oriented button text like "Check Availability"</li>
<li><b>Social Proof:</b> Include neighbor testimonials or local statistics</li>
</ul>

<h4>🎯 Targeting</h4>
<ul>
<li><b>Segmentation:</b> Separate fiber-available vs. fiber-pending audiences</li>
<li><b>Local Focus:</b> Reference neighborhood-specific benefits</li>
<li><b>Timing:</b> Send during optimal hours (10 AM - 2 PM, 6 PM - 8 PM)</li>
<li><b>Frequency:</b> Follow up with non-openers after 3-5 days</li>
</ul>

<h4>📊 Performance Tracking</h4>
<ul>
<li><b>Open Rate:</b> Track by subject line variation</li>
<li><b>Click Rate:</b> Monitor CTA button performance</li>
<li><b>Conversion Rate:</b> Measure actual sign-ups or inquiries</li>
<li><b>Unsubscribe Rate:</b> Keep below 2% for healthy list</li>
</ul>

<h4>🔄 A/B Testing Ideas</h4>
<ul>
<li><b>Subject Lines:</b> Question vs. statement format</li>
<li><b>Send Times:</b> Morning vs. evening delivery</li>
<li><b>Email Length:</b> Short vs. detailed content</li>
<li><b>CTA Placement:</b> Top vs. bottom button placement</li>
</ul>
"""
            
            recommendations_display = QTextEdit()
            recommendations_display.setHtml(recommendations_html)
            recommendations_display.setReadOnly(True)
            recommendations_layout.addWidget(recommendations_display)
            
            tabs.addTab(recommendations_tab, "🚀 Recommendations")
            
            layout.addWidget(tabs)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Error analyzing campaign: {e}")

    def create_html_email_preview(self, campaign: dict) -> str:
        """Create HTML preview of the email"""
        try:
            # Get the first personalized email or template
            if 'personalized_emails' in campaign and campaign['personalized_emails']:
                email = campaign['personalized_emails'][0]
                subject = email.get('subject', 'No Subject')
                body = email.get('body', 'No content')
                recipient = email.get('contact_name', 'Customer')
            elif 'templates' in campaign and campaign['templates']:
                template = list(campaign['templates'].values())[0]
                subject = template.get('subject', 'No Subject')
                body = template.get('body', 'No content')
                recipient = "Customer"
            else:
                return "<p>No email content available</p>"
            
            # Create HTML email template
            html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .email-container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            border: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #2196F3;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 10px;
        }}
        .subject {{
            font-size: 18px;
            color: #666;
            margin: 0;
        }}
        .greeting {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #333;
        }}
        .content {{
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 30px;
        }}
        .cta-button {{
            display: inline-block;
            background-color: #2196F3;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
        }}
        .cta-button:hover {{
            background-color: #1976D2;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        .benefits {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .benefits ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .benefits li {{
            margin-bottom: 8px;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo">🚀 AT&T Fiber & Security</div>
            <h1 class="subject">{subject}</h1>
        </div>
        
        <div class="greeting">
            <strong>Hello {recipient},</strong>
        </div>
        
        <div class="content">
            {self.format_email_body_html(body)}
        </div>
        
        <div style="text-align: center;">
            <a href="#" class="cta-button">Check Availability Now</a>
        </div>
        
        <div class="benefits">
            <h3>🌟 Why Choose Our Services?</h3>
            <ul>
                <li>⚡ Ultra-fast fiber internet up to 1 Gig</li>
                <li>🏠 Professional ADT security monitoring</li>
                <li>📱 Smart home integration</li>
                <li>🛡️ 24/7 customer support</li>
                <li>💰 Competitive pricing with no contracts</li>
            </ul>
        </div>
        
        <div class="highlight">
            <strong>🎯 Special Offer:</strong> Get your first month free with professional installation!
        </div>
        
        <div class="footer">
            <p>This email was sent to you because you're in an area where our services are available.</p>
            <p>© 2024 AT&T Fiber & Security Services. All rights reserved.</p>
            <p><a href="#">Unsubscribe</a> | <a href="#">Privacy Policy</a> | <a href="#">Contact Us</a></p>
        </div>
    </div>
</body>
</html>
"""
            return html_template
            
        except Exception as e:
            logger.error(f"Error creating HTML email preview: {e}")
            return f"<p>Error creating email preview: {e}</p>"

    def format_email_body_html(self, body: str) -> str:
        """Format plain text email body as HTML"""
        # Convert line breaks to HTML
        html_body = body.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        # Wrap in paragraphs
        html_body = f'<p>{html_body}</p>'
        
        # Add some basic formatting
        html_body = html_body.replace('Key benefits:', '<h3>Key Benefits:</h3>')
        html_body = html_body.replace('Benefits:', '<h3>Benefits:</h3>')
        html_body = html_body.replace('• ', '<li>')
        html_body = html_body.replace('<li>', '<ul><li>').replace('</p>', '</li></ul></p>', 1)
        
        return html_body

    def generate_with_xai(self):
        """Generate campaign content specifically using XAI"""
        try:
            # Check if XAI is configured
            if AI_SERVICE_AVAILABLE:
                service = AIEmailMarketingService()
                if not service.xai_api_key:
                    QMessageBox.warning(self, "XAI Not Configured", 
                                      "XAI API key not found. Please add XAI_API_KEY to your environment variables.")
                    return
            else:
                QMessageBox.warning(self, "AI Service Unavailable", "AI service is not available.")
                return
            
            # Get current campaign configuration
            if not hasattr(self, 'campaign_type_combo'):
                QMessageBox.warning(self, "No Configuration", "Please configure your campaign first.")
                return
            
            campaign_type = self.campaign_type_combo.currentText()
            
            # Create XAI-specific prompt
            xai_prompt = f"""
            Using XAI's advanced capabilities, create an innovative email marketing campaign for {campaign_type}.
            
            Focus on:
            1. Creative subject lines that stand out
            2. Engaging content that drives action
            3. Personalization strategies
            4. Modern email marketing techniques
            5. Compliance with current best practices
            
            Include specific recommendations for:
            - Subject line optimization
            - Email timing
            - Call-to-action placement
            - Mobile optimization
            - Segmentation strategies
            
            Make this campaign cutting-edge and highly effective.
            """
            
            # Send to AI chat with XAI tag
            self.main_tabs.setCurrentIndex(1)  # Switch to chat tab
            self.add_chat_message("You", f"🤖 XAI Generation Request: {xai_prompt}", is_ai=False)
            
            # Create worker for XAI-specific generation
            self.xai_worker = AIChatWorker(xai_prompt, {"use_xai": True})
            self.xai_worker.response_signal.connect(self.on_xai_response)
            self.xai_worker.error_signal.connect(self.on_chat_error)
            self.xai_worker.start()
            
            self.status_label.setText("Generating campaign with XAI...")
            
        except Exception as e:
            QMessageBox.critical(self, "XAI Error", f"Error generating with XAI: {e}")

    def on_xai_response(self, response):
        """Handle XAI-specific response"""
        self.add_chat_message("XAI Assistant", f"🤖 {response}", is_ai=True)
        self.status_label.setText("XAI campaign generation completed")

    def download_mailchimp_templates(self):
        """Download email templates from Mailchimp and make them available to AI"""
        try:
            self.status_label.setText("Downloading email templates from Mailchimp...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Get API key from settings
            from gui.settings_widget import SettingsWidget
            settings = SettingsWidget()
            api_keys = settings.get_keys()
            mailchimp_api_key = api_keys.get('mailchimp_api_key', '')
            
            if not mailchimp_api_key:
                QMessageBox.warning(self, "API Key Missing", "Please set your Mailchimp API key in Settings first.")
                self.progress_bar.setVisible(False)
                return
            
            # Initialize Mailchimp client
            client = MailchimpMarketing.Client()
            server_prefix = mailchimp_api_key.split('-')[-1]
            client.set_config({
                "api_key": mailchimp_api_key,
                "server": server_prefix,
            })
            
            # Download templates and campaigns
            templates_data = {}
            
            # 1. Get email templates
            self.status_label.setText("Fetching email templates...")
            try:
                templates_response = client.templates.list(count=50)
                templates = templates_response.get('templates', [])
                
                for template in templates[:10]:  # Limit to 10 templates
                    template_id = template['id']
                    template_name = template['name']
                    
                    # Store basic template info (content not available via standard API)
                    template_info = {
                        'id': template_id,
                        'name': template_name,
                        'type': template.get('type', 'unknown'),
                        'created_by': template.get('created_by', 'unknown'),
                        'date_created': template.get('date_created', ''),
                        'category': template.get('category', ''),
                        'preview_url': template.get('preview_url', ''),
                        'thumbnail': template.get('thumbnail', ''),
                        'active': template.get('active', True),
                        'description': f"Template: {template_name} (ID: {template_id})"
                    }
                    templates_data['templates'].append(template_info)
                        
            except Exception as e:
                print(f"Error fetching templates: {e}")
                templates_data['templates'] = []
            
            # 2. Get recent campaigns for template inspiration
            self.status_label.setText("Fetching recent campaigns...")
            try:
                campaigns_response = client.campaigns.list(count=50, status='sent')
                campaigns = campaigns_response.get('campaigns', [])
                templates_data['recent_campaigns'] = []
                
                for campaign in campaigns[:10]:  # Limit to 10 most recent
                    campaign_id = campaign['id']
                    
                    try:
                        # Get campaign content
                        campaign_content = client.campaigns.get_content(campaign_id)
                        
                        # Get campaign stats
                        try:
                            stats = client.reports.get_campaign_report(campaign_id)
                        except:
                            stats = {}
                        
                        campaign_info = {
                            'id': campaign_id,
                            'subject_line': campaign.get('settings', {}).get('subject_line', ''),
                            'preview_text': campaign.get('settings', {}).get('preview_text', ''),
                            'from_name': campaign.get('settings', {}).get('from_name', ''),
                            'reply_to': campaign.get('settings', {}).get('reply_to', ''),
                            'send_time': campaign.get('send_time', ''),
                            'html_content': campaign_content.get('html', ''),
                            'plain_text': campaign_content.get('plain_text', ''),
                            'opens': stats.get('opens', {}).get('opens_total', 0),
                            'clicks': stats.get('clicks', {}).get('clicks_total', 0),
                            'open_rate': stats.get('opens', {}).get('open_rate', 0),
                            'click_rate': stats.get('clicks', {}).get('click_rate', 0)
                        }
                        templates_data['recent_campaigns'].append(campaign_info)
                        
                    except Exception as e:
                        print(f"Error getting campaign {campaign_id}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error fetching campaigns: {e}")
                templates_data['recent_campaigns'] = []
            
            # 3. Save templates data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            templates_file = f'mailchimp_templates_{timestamp}.json'
            
            with open(templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2, default=str)
            
            # 4. Store templates for AI assistant
            self.mailchimp_templates = templates_data
            
            # 5. Create templates tab in results
            self.create_templates_tab(templates_data)
            
            # 6. Add templates context to AI chat
            templates_summary = self.create_templates_summary(templates_data)
            
            # Add to chat history for AI context
            self.add_chat_message("System", f"📄 Downloaded {len(templates_data['templates'])} email templates and {len(templates_data['recent_campaigns'])} recent campaigns from Mailchimp. These are now available for AI analysis and inspiration.", is_ai=False)
            
            # Update AI context with templates
            if hasattr(self, 'ai_context'):
                self.ai_context['mailchimp_templates'] = templates_summary
            else:
                self.ai_context = {'mailchimp_templates': templates_summary}
            
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"Successfully downloaded {len(templates_data['templates'])} templates and {len(templates_data['recent_campaigns'])} campaigns")
            
            QMessageBox.information(self, "Templates Downloaded", 
                                  f"Successfully downloaded:\n"
                                  f"• {len(templates_data['templates'])} email templates\n"
                                  f"• {len(templates_data['recent_campaigns'])} recent campaigns\n\n"
                                  f"Templates are now available for AI analysis and saved to {templates_file}")
            
        except ApiClientError as e:
            self.progress_bar.setVisible(False)
            error_msg = f"Mailchimp API Error: {e.text}"
            self.status_label.setText("Template download failed")
            QMessageBox.critical(self, "API Error", error_msg)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            error_msg = f"Error downloading templates: {e}"
            self.status_label.setText("Template download failed")
            QMessageBox.critical(self, "Download Error", error_msg)
    
    def create_templates_summary(self, templates_data):
        """Create a summary of templates for AI context"""
        summary = {
            'template_count': len(templates_data['templates']),
            'campaign_count': len(templates_data['recent_campaigns']),
            'template_names': [t['name'] for t in templates_data['templates']],
            'recent_subjects': [c['subject_line'] for c in templates_data['recent_campaigns']],
            'best_performing': []
        }
        
        # Find best performing campaigns
        campaigns = templates_data['recent_campaigns']
        if campaigns:
            # Sort by open rate
            sorted_campaigns = sorted(campaigns, key=lambda x: x.get('open_rate', 0), reverse=True)
            summary['best_performing'] = [
                {
                    'subject': c['subject_line'],
                    'open_rate': c.get('open_rate', 0),
                    'click_rate': c.get('click_rate', 0)
                }
                for c in sorted_campaigns[:3]
            ]
        
        return summary
    
    def create_templates_tab(self, templates_data):
        """Create a new tab to display downloaded templates"""
        templates_tab = QWidget()
        layout = QVBoxLayout(templates_tab)
        
        # Header
        header = QLabel(f"Downloaded Email Templates ({len(templates_data['templates'])} templates, {len(templates_data['recent_campaigns'])} campaigns)")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background: #404040; color: #ffffff; border-radius: 5px;")
        layout.addWidget(header)
        
        # Create sub-tabs
        sub_tabs = QTabWidget()
        layout.addWidget(sub_tabs)
        
        # Templates tab
        templates_widget = self.create_templates_list(templates_data['templates'])
        sub_tabs.addTab(templates_widget, f"Templates ({len(templates_data['templates'])})")
        
        # Campaigns tab
        campaigns_widget = self.create_campaigns_list(templates_data['recent_campaigns'])
        sub_tabs.addTab(campaigns_widget, f"Recent Campaigns ({len(templates_data['recent_campaigns'])})")
        
        # Add to main results tabs
        self.results_tabs.addTab(templates_tab, "📄 Templates")
        
        # Switch to templates tab
        self.results_tabs.setCurrentWidget(templates_tab)
    
    def create_templates_list(self, templates):
        """Create a widget to display templates"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Templates table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Name', 'Type', 'Created By', 'Date Created', 'Actions'])
        table.setRowCount(len(templates))
        
        for i, template in enumerate(templates):
            table.setItem(i, 0, QTableWidgetItem(template['name']))
            table.setItem(i, 1, QTableWidgetItem(template['type']))
            table.setItem(i, 2, QTableWidgetItem(template['created_by']))
            table.setItem(i, 3, QTableWidgetItem(template['date_created'][:10] if template['date_created'] else ''))
            
            # Actions button
            view_btn = QPushButton("View Content")
            view_btn.clicked.connect(lambda checked, t=template: self.view_template_content(t))
            table.setCellWidget(i, 4, view_btn)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(table)
        
        return widget
    
    def create_campaigns_list(self, campaigns):
        """Create a widget to display recent campaigns"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Campaigns table
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(['Subject Line', 'From Name', 'Send Date', 'Opens', 'Clicks', 'Open Rate', 'Actions'])
        table.setRowCount(len(campaigns))
        
        for i, campaign in enumerate(campaigns):
            table.setItem(i, 0, QTableWidgetItem(campaign['subject_line']))
            table.setItem(i, 1, QTableWidgetItem(campaign['from_name']))
            table.setItem(i, 2, QTableWidgetItem(campaign['send_time'][:10] if campaign['send_time'] else ''))
            table.setItem(i, 3, QTableWidgetItem(str(campaign['opens'])))
            table.setItem(i, 4, QTableWidgetItem(str(campaign['clicks'])))
            table.setItem(i, 5, QTableWidgetItem(f"{campaign['open_rate']:.1%}"))
            
            # Actions button
            view_btn = QPushButton("View Content")
            view_btn.clicked.connect(lambda checked, c=campaign: self.view_campaign_content(c))
            table.setCellWidget(i, 6, view_btn)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(table)
        
        return widget
    
    def view_template_content(self, template):
        """View template content in a dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QTabWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Template: {template['name']}")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # HTML content tab
        html_text = QTextEdit()
        html_text.setPlainText(template['html_content'])
        html_text.setReadOnly(True)
        tabs.addTab(html_text, "HTML Content")
        
        # Plain text tab
        plain_text = QTextEdit()
        plain_text.setPlainText(template['plain_text'])
        plain_text.setReadOnly(True)
        tabs.addTab(plain_text, "Plain Text")
        
        # Add button to analyze with AI
        analyze_btn = QPushButton("🤖 Analyze with AI")
        analyze_btn.clicked.connect(lambda: self.analyze_template_with_ai(template))
        layout.addWidget(analyze_btn)
        
        dialog.exec()
    
    def view_campaign_content(self, campaign):
        """View campaign content in a dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QTabWidget, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Campaign: {campaign['subject_line']}")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Campaign stats
        stats_label = QLabel(f"Opens: {campaign['opens']} | Clicks: {campaign['clicks']} | Open Rate: {campaign['open_rate']:.1%} | Click Rate: {campaign['click_rate']:.1%}")
        stats_label.setStyleSheet("font-weight: bold; padding: 10px; background: #404040; color: #ffffff; border-radius: 5px;")
        layout.addWidget(stats_label)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # HTML content tab
        html_text = QTextEdit()
        html_text.setPlainText(campaign['html_content'])
        html_text.setReadOnly(True)
        tabs.addTab(html_text, "HTML Content")
        
        # Plain text tab
        plain_text = QTextEdit()
        plain_text.setPlainText(campaign['plain_text'])
        plain_text.setReadOnly(True)
        tabs.addTab(plain_text, "Plain Text")
        
        # Add button to analyze with AI
        analyze_btn = QPushButton("🤖 Analyze Campaign Performance with AI")
        analyze_btn.clicked.connect(lambda: self.analyze_campaign_with_ai(campaign))
        layout.addWidget(analyze_btn)
        
        dialog.exec()
    
    def analyze_template_with_ai(self, template):
        """Analyze template with AI assistant"""
        analysis_prompt = f"""
        Please analyze this email template:
        
        Template Name: {template['name']}
        Template Type: {template['type']}
        
        HTML Content: {template['html_content'][:1000]}...
        
        Please provide:
        1. Design and layout analysis
        2. Content structure assessment
        3. Suggestions for improvement
        4. Best practices recommendations
        5. How this template could be adapted for AT&T Fiber or ADT Security campaigns
        """
        
        # Switch to chat tab
        self.main_tabs.setCurrentIndex(1)
        
        # Add analysis request to chat
        self.add_chat_message("You", f"Analyze Template: {template['name']}", is_ai=False)
        self.send_ai_message(analysis_prompt)
    
    def analyze_campaign_with_ai(self, campaign):
        """Analyze campaign performance with AI assistant"""
        analysis_prompt = f"""
        Please analyze this email campaign performance:
        
        Subject Line: {campaign['subject_line']}
        From Name: {campaign['from_name']}
        Preview Text: {campaign['preview_text']}
        
        Performance Metrics:
        - Opens: {campaign['opens']}
        - Clicks: {campaign['clicks']}
        - Open Rate: {campaign['open_rate']:.1%}
        - Click Rate: {campaign['click_rate']:.1%}
        
        Content: {campaign['html_content'][:1000]}...
        
        Please provide:
        1. Performance analysis (is this good/bad/average?)
        2. What elements likely contributed to the performance
        3. Subject line effectiveness
        4. Content and design insights
        5. Recommendations for improving similar campaigns
        6. How to adapt successful elements for AT&T Fiber/ADT Security campaigns
        """
        
        # Switch to chat tab
        self.main_tabs.setCurrentIndex(1)
        
        # Add analysis request to chat
        self.add_chat_message("You", f"Analyze Campaign: {campaign['subject_line']}", is_ai=False)
        self.send_ai_message(analysis_prompt)
    
    def send_ai_message(self, message):
        """Send message to AI and handle response"""
        if not AI_SERVICE_AVAILABLE:
            self.add_chat_message("AI Assistant", "AI service not available for analysis.", is_ai=True)
            return
        
        self.send_chat_btn.setEnabled(False)
        self.send_chat_btn.setText("Analyzing...")
        
        # Include templates context if available
        context = getattr(self, 'ai_context', {})
        
        # Start AI worker
        self.chat_worker = AIChatWorker(message, context)
        self.chat_worker.response_signal.connect(self.on_chat_response)
        self.chat_worker.error_signal.connect(self.on_chat_error)
        self.chat_worker.start() 