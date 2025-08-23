from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QMessageBox, QLineEdit, QToolButton, QGroupBox, QCheckBox, QDialog, QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt, Slot, QThread
from PySide6.QtGui import QColor
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play
import io
import time
from datetime import datetime
import os
import glob
import pandas as pd
import json
import multiprocessing
import atexit
import gc

from services.enhanced_ai_email_service import EnhancedAIEmailService

# Global cleanup function for multiprocessing resources
def cleanup_multiprocessing():
    """Clean up multiprocessing resources to prevent semaphore leaks"""
    try:
        # Force garbage collection
        gc.collect()
        
        # Clean up any remaining multiprocessing resources
        if hasattr(multiprocessing, 'current_process'):
            current = multiprocessing.current_process()
            if hasattr(current, '_cleanup'):
                current._cleanup()
    except Exception as e:
        print(f"Cleanup warning: {e}")

# Register cleanup function
atexit.register(cleanup_multiprocessing)

class EfficientAIEmailWidget(QWidget):
    campaign_generated = Signal(dict)  # campaign data
    campaign_verified = Signal(bool)

    def __init__(self, parent=None):
        print('Creating EfficientAIEmailWidget at:', datetime.now())
        super().__init__(parent)
        # Initialize the enhanced service
        self.service = None  # Will be initialized when needed
        self.conversation_active = False
        self.auto_approval_enabled = False  # Auto-approval state
        self.worker_threads = []  # Track worker threads for cleanup
        self.setup_ui()
        
        # Initialize AI Command Controller
        try:
            from utils.ai_command_controller_simple import AICommandController
            self.command_controller = AICommandController(self)
            
            print("✅ AI Command Controller initialized successfully!")
            self.chat_display.append("🤖 AI Command Controller ready! Say 'help' to see available commands.")
        except Exception as e:
            print(f"⚠️ AI Command Controller not available: {str(e)}")
            self.command_controller = None

    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        try:
            # Clean up worker threads
            for thread in self.worker_threads:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(5000)  # Wait up to 5 seconds
            
            # Force garbage collection
            gc.collect()
            
            # Call multiprocessing cleanup
            cleanup_multiprocessing()
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        super().closeEvent(event)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Set overall widget background to dark
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
            }
            QGroupBox {
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ecf0f1;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Header
        header = QLabel("🤖 AI Email Marketing & Campaign Manager")
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
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #667eea;
                border-radius: 8px;
                background: #2c3e50;
                color: #ecf0f1;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #667eea;
                color: white;
            }
            QTabBar::tab:hover {
                background: #4a6741;
            }
        """)

        # Campaign Review Tab - NEW MAIN TAB
        review_tab = QWidget()
        review_layout = QVBoxLayout(review_tab)
        
        # Campaign status with improved styling
        self.campaign_status_label = QLabel("📊 Campaign Status: Ready to select leads or run automation...")
        self.campaign_status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 15px 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #34495e, stop: 1 #2c3e50);
                border: 2px solid #5d6d7e;
                border-radius: 8px;
                margin-bottom: 15px;
            }
        """)
        review_layout.addWidget(self.campaign_status_label)
        
        # Campaign list view (new)
        self.campaign_list_widget = QWidget()
        self.campaign_list_layout = QVBoxLayout(self.campaign_list_widget)
        
        # Instructions with improved styling
        instructions_label = QLabel("📋 Generated campaigns will appear below. Click 'Preview Email' to review content before approval.")
        instructions_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-style: italic;
                font-size: 13px;
                padding: 12px 15px;
                background: #34495e;
                border-radius: 6px;
                margin-bottom: 15px;
                border-left: 4px solid #3498db;
            }
        """)
        instructions_label.setWordWrap(True)
        self.campaign_list_layout.addWidget(instructions_label)
        
        review_layout.addWidget(self.campaign_list_widget)
        
        # Campaign tabs for different types
        self.campaign_tabs = QTabWidget()
        self.campaign_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #2c3e50;
                color: #ecf0f1;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
                padding: 6px 12px;
                margin-right: 1px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background: #4a6741;
            }
        """)
        review_layout.addWidget(self.campaign_tabs)
        
        # Auto-Approval Section
        auto_approval_group = QGroupBox("🤖 Auto-Approval Settings")
        auto_approval_layout = QHBoxLayout(auto_approval_group)
        
        # Auto-approval toggle button
        self.auto_approval_btn = QPushButton("🔴 Auto-Approval: OFF")
        self.auto_approval_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        self.auto_approval_btn.setCheckable(True)
        self.auto_approval_btn.clicked.connect(self.toggle_auto_approval)
        auto_approval_layout.addWidget(self.auto_approval_btn)
        
        # Auto-approval info
        self.auto_approval_info = QLabel("⚠️ When enabled, AI emails will be automatically approved without manual review")
        self.auto_approval_info.setStyleSheet("""
            QLabel {
                color: #f39c12;
                font-style: italic;
                font-size: 12px;
                padding: 5px;
            }
        """)
        auto_approval_layout.addWidget(self.auto_approval_info)
        
        review_layout.addWidget(auto_approval_group)
        
        # Action buttons with improved layout
        action_frame = QGroupBox("📋 Campaign Actions")
        action_frame_layout = QVBoxLayout(action_frame)
        
        # Primary actions row
        primary_actions = QHBoxLayout()
        primary_actions.setSpacing(15)
        
        self.approve_all_btn = QPushButton("✅ Approve All Campaigns")
        self.approve_all_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
                min-height: 32px;
            }
            QPushButton:hover { 
                background: #218838; 
            }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.approve_all_btn.setEnabled(False)
        self.approve_all_btn.clicked.connect(self.approve_all_campaigns)
        primary_actions.addWidget(self.approve_all_btn)
        
        self.reject_all_btn = QPushButton("❌ Reject All Campaigns")
        self.reject_all_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
                min-height: 32px;
            }
            QPushButton:hover { 
                background: #c82333; 
            }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.reject_all_btn.setEnabled(False)
        self.reject_all_btn.clicked.connect(self.reject_all_campaigns)
        primary_actions.addWidget(self.reject_all_btn)
        
        action_frame_layout.addLayout(primary_actions)
        
        # Secondary actions row
        secondary_actions = QHBoxLayout()
        secondary_actions.setSpacing(15)
        
        # Select existing leads button
        self.select_leads_btn = QPushButton("📋 Select Existing Leads")
        self.select_leads_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
                min-height: 32px;
            }
            QPushButton:hover { 
                background: #138496; 
            }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.select_leads_btn.clicked.connect(self.select_existing_leads)
        secondary_actions.addWidget(self.select_leads_btn)
        
        # Generate campaigns from leads button
        self.generate_from_leads_btn = QPushButton("🚀 Generate Campaigns from Leads")
        self.generate_from_leads_btn.setStyleSheet("""
            QPushButton {
                background: #fd7e14;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 180px;
                min-height: 32px;
            }
            QPushButton:hover { 
                background: #e8690b; 
            }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.generate_from_leads_btn.setEnabled(False)  # Disabled until leads are selected
        self.generate_from_leads_btn.clicked.connect(self.generate_campaigns_from_leads)
        secondary_actions.addWidget(self.generate_from_leads_btn)
        
        # Test button for debugging
        test_btn = QPushButton("🧪 Test Campaign Display")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #6f42c1;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
                min-height: 28px;
            }
            QPushButton:hover { background: #5a2d91; }
        """)
        # DISABLED: Test campaigns override real automation data
        # test_btn.clicked.connect(self.test_campaign_display)
        # secondary_actions.addWidget(test_btn)
        
        # DISABLED: Test incident campaigns override real automation data
        # test_incident_btn = QPushButton("🚨 Test Incident Campaigns")
        # test_incident_btn.clicked.connect(self.test_incident_campaigns)
        # secondary_actions.addWidget(test_incident_btn)
        
        # DEPRECATED: Check for real incident campaigns button - Use Incident Response tab instead
        check_incidents_btn = QPushButton("⚠️ DEPRECATED - Use Incident Tab")
        check_incidents_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
                min-height: 28px;
            }
            QPushButton:hover { background: #5a6268; }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        check_incidents_btn.setEnabled(False)  # Disable the old method
        check_incidents_btn.setToolTip("This feature is deprecated. Use the 'Generate Leads from Incidents' button in the Incident Response tab instead.")
        secondary_actions.addWidget(check_incidents_btn)
        
        # Audience list management button
        self.manage_lists_btn = QPushButton("📊 Manage Audience Lists")
        self.manage_lists_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
                min-height: 32px;
            }
            QPushButton:hover { 
                background: #218838; 
            }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.manage_lists_btn.clicked.connect(self.manage_audience_lists)
        secondary_actions.addWidget(self.manage_lists_btn)
        
        # Add spacer in middle
        secondary_actions.addStretch()
        
        self.regenerate_btn = QPushButton("🔄 Regenerate Campaigns")
        self.regenerate_btn.setStyleSheet("""
            QPushButton {
                background: #ffc107;
                color: #212529;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
                min-height: 28px;
            }
            QPushButton:hover { background: #e0a800; }
            QPushButton:disabled { 
                background: #6c757d; 
                color: #bdc3c7;
            }
        """)
        self.regenerate_btn.setEnabled(False)
        self.regenerate_btn.clicked.connect(self.regenerate_campaigns)
        secondary_actions.addWidget(self.regenerate_btn)
        
        action_frame_layout.addLayout(secondary_actions)
        
        review_layout.addWidget(action_frame)
        tabs.addTab(review_tab, '📧 Campaign Review')

        # Analytics Tab - ENHANCED
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        
        # Analytics header
        analytics_header = QLabel("📈 MailChimp Analytics & Performance Data")
        analytics_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 10px;
                background: #34495e;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        """)
        analytics_layout.addWidget(analytics_header)
        
        # Analytics display
        self.analytics_display = QTextEdit()
        self.analytics_display.setReadOnly(True)
        self.analytics_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        analytics_layout.addWidget(self.analytics_display)
        
        # Analytics controls
        analytics_controls = QHBoxLayout()
        
        refresh_analytics_btn = QPushButton('🔄 Refresh Analytics')
        refresh_analytics_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0056b3; }
        """)
        refresh_analytics_btn.clicked.connect(self.load_analytics)
        analytics_controls.addWidget(refresh_analytics_btn)
        
        export_analytics_btn = QPushButton('📊 Export Analytics')
        export_analytics_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        export_analytics_btn.clicked.connect(self.export_analytics)
        analytics_controls.addWidget(export_analytics_btn)
        
        analytics_controls.addStretch()
        analytics_layout.addLayout(analytics_controls)
        tabs.addTab(analytics_tab, '📈 Analytics')

        # Campaign Builder Tab - ENHANCED
        builder_tab = QWidget()
        builder_layout = QVBoxLayout(builder_tab)
        
        # Builder header
        builder_header = QLabel("🛠️ Manual Campaign Builder")
        builder_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 10px;
                background: #34495e;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        """)
        builder_layout.addWidget(builder_header)
        
        # Campaign type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('Campaign Type:'))
        self.campaign_type = QComboBox()
        self.campaign_type.addItems(['🌐 AT&T Fiber', '🔒 ADT Security', '📢 General Outreach', '🔄 Follow-up'])
        self.campaign_type.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #34495e;
                color: #ecf0f1;
            }
            QComboBox::drop-down {
                background: #34495e;
            }
            QComboBox QAbstractItemView {
                background: #34495e;
                color: #ecf0f1;
                selection-background-color: #3498db;
            }
        """)
        type_layout.addWidget(self.campaign_type)
        builder_layout.addLayout(type_layout)
        
        # Generate button
        generate_btn = QPushButton('🚀 Generate Campaign')
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #667eea;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #5a6fd8; }
        """)
        generate_btn.clicked.connect(self.generate_campaign)
        builder_layout.addWidget(generate_btn)
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #34495e;
                color: #ecf0f1;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
            }
        """)
        builder_layout.addWidget(self.preview_text)
        
        tabs.addTab(builder_tab, '🛠️ Builder')

        # XAI Chat Tab - ENHANCED
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # Chat header
        chat_header = QLabel("💬 XAI Marketing Assistant")
        chat_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 10px;
                background: #34495e;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        """)
        chat_layout.addWidget(chat_header)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        
        # Chat input
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask about marketing strategies, campaign optimization, or analytics...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #34495e;
                color: #ecf0f1;
                font-size: 12px;
            }
            QLineEdit::placeholder {
                color: #95a5a6;
            }
        """)
        chat_input_layout.addWidget(self.chat_input)
        
        send_btn = QPushButton('Send')
        send_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0056b3; }
        """)
        send_btn.clicked.connect(self.send_chat)
        chat_input_layout.addWidget(send_btn)
        
        self.voice_btn = QToolButton()
        self.voice_btn.setText('🎤')
        self.voice_btn.setStyleSheet("""
            QToolButton {
                background: #28a745;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QToolButton:hover { background: #218838; }
        """)
        self.voice_btn.clicked.connect(self.voice_chat)
        chat_input_layout.addWidget(self.voice_btn)
        
        self.conversation_btn = QToolButton()
        self.conversation_btn.setText('💬 Start Conversation')
        self.conversation_btn.setStyleSheet("""
            QToolButton {
                background: #ffc107;
                color: #212529;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QToolButton:hover { background: #e0a800; }
        """)
        self.conversation_btn.clicked.connect(self.toggle_conversation)
        chat_input_layout.addWidget(self.conversation_btn)
        
        chat_layout.addLayout(chat_input_layout)
        tabs.addTab(chat_tab, '💬 XAI Chat')

        layout.addWidget(tabs)
        
        # Initialize with placeholder data
        self.load_analytics()

        # Add auto-approval toggle
        auto_approval_layout = QHBoxLayout()
        self.auto_approval_checkbox = QCheckBox("Enable Auto-Approval")
        self.auto_approval_checkbox.setChecked(False)
        self.auto_approval_checkbox.stateChanged.connect(self.toggle_auto_approval)
        auto_approval_layout.addWidget(self.auto_approval_checkbox)
        auto_approval_layout.addStretch()
        layout.addLayout(auto_approval_layout)

    def _ensure_service_initialized(self):
        """Initialize the service if not already done"""
        if self.service is None:
            try:
                self.service = EnhancedAIEmailService()
            except Exception as e:
                print(f"Error initializing AI service: {e}")
                self.service = None
        return self.service

    def generate_campaign(self):
        """Generate a campaign using the manual builder"""
        try:
            campaign_type_text = self.campaign_type.currentText()
            
            # Map UI text to campaign types
            type_mapping = {
                '🌐 AT&T Fiber': 'fiber_introduction',
                '🔒 ADT Security': 'adt_security_offer', 
                '📢 General Outreach': 'general_outreach',
                '🔄 Follow-up': 'general_outreach'
            }
            
            campaign_type = type_mapping.get(campaign_type_text, 'general_outreach')
            
            # Generate a simple campaign
            from datetime import datetime
            
            if campaign_type == 'fiber_introduction':
                campaign_content = """
🌐 AT&T FIBER CAMPAIGN

Subject: High-Speed Fiber Internet Now Available!

Dear Homeowner,

Great news! High-speed AT&T Fiber internet is now available in your area.

🚀 Lightning-fast speeds up to 1 Gig
💼 Perfect for work-from-home
🎮 Ultimate gaming and streaming experience
💰 Competitive pricing with no contracts

Don't miss out on this opportunity to upgrade your internet experience.

Contact us today to schedule your installation!

Best regards,
The Fiber Team
Seaside Security & Communications
"""
            elif campaign_type == 'adt_security_offer':
                campaign_content = """
🔒 ADT SECURITY CAMPAIGN

Subject: Protect Your Home with Advanced Security

Dear Homeowner,

Your family's safety is our priority. Let us help you secure your home with the latest technology.

🏠 24/7 professional monitoring
📱 Smart home integration
🚨 Instant emergency response
💡 Mobile app control

Contact us today for a free security consultation!

Best regards,
The Security Team
Seaside Security & Communications
"""
            else:
                campaign_content = """
📢 GENERAL OUTREACH CAMPAIGN

Subject: Exclusive Services Available in Your Area

Dear Homeowner,

We're excited to offer exclusive technology services to homeowners in your area.

🌐 High-speed internet solutions
🔒 Advanced security systems
📱 Smart home automation
💼 Professional installation

Contact us today to learn more about our services!

Best regards,
The Technology Team
Seaside Security & Communications
"""
            
            self.preview_text.setPlainText(campaign_content)
            
            # Create campaign data for emission
            campaign_data = {
                'type': campaign_type,
                'subject': campaign_content.split('Subject: ')[1].split('\n')[0] if 'Subject: ' in campaign_content else 'Generated Campaign',
                'body': campaign_content,
                'created_at': datetime.now().isoformat()
            }
            
            self.campaign_generated.emit(campaign_data)
            
        except Exception as e:
            error_msg = f"Error generating campaign: {str(e)}"
            self.preview_text.setPlainText(error_msg)
            print(error_msg)

    def load_analytics(self):
        """Load MailChimp analytics data"""
        try:
            self._ensure_service_initialized()
            
            # Try to get real analytics data
            analytics_text = """
📈 MAILCHIMP ANALYTICS & PERFORMANCE DATA
================================================================

🔄 Loading analytics data...
"""
            self.analytics_display.setText(analytics_text)
            
            if self.service:
                try:
                    analytics = self.service.get_campaign_analytics(limit=10)
                    mailchimp_data = self.service.get_comprehensive_mailchimp_data()
                    
                    # Format analytics display
                    analytics_text = """
📈 MAILCHIMP ANALYTICS & PERFORMANCE DATA
================================================================

🎯 RECENT CAMPAIGN PERFORMANCE:
"""
                    
                    if analytics and len(analytics) > 0:
                        for i, campaign in enumerate(analytics[:5]):
                            analytics_text += f"""
Campaign {i+1}: {campaign.get('subject_line', 'N/A')}
  📧 Sent: {campaign.get('emails_sent', 0)}
  📖 Opens: {campaign.get('opens', 0)} ({campaign.get('open_rate', 0)*100:.1f}%)
  🖱️ Clicks: {campaign.get('clicks', 0)} ({campaign.get('click_rate', 0)*100:.1f}%)
  📊 Status: {campaign.get('status', 'N/A')}
  📅 Sent: {campaign.get('send_time', 'N/A')}
"""
                    else:
                        analytics_text += "\n  ⚠️ No recent campaigns found in MailChimp"
                    
                    analytics_text += """
📊 ACCOUNT SUMMARY:
"""
                    if mailchimp_data and isinstance(mailchimp_data, dict) and mailchimp_data.get('total_contacts', 0) > 0:
                        analytics_text += f"""
  👥 Total Contacts: {mailchimp_data.get('total_contacts', 0)}
  📧 Campaigns Sent: {mailchimp_data.get('total_campaigns', 0)}
  📈 Average Open Rate: {mailchimp_data.get('avg_open_rate', 0)*100:.1f}%
  🖱️ Average Click Rate: {mailchimp_data.get('avg_click_rate', 0)*100:.1f}%
"""
                    elif mailchimp_data:
                        # Handle case where mailchimp_data is not a dict (fallback)
                        analytics_text += f"""
  📊 MailChimp data available but in unexpected format
  ℹ️  Type: {type(mailchimp_data).__name__}
"""
                    else:
                        analytics_text += "\n  ⚠️ MailChimp account data not available"
                    
                except Exception as e:
                    print(f"Error getting MailChimp data: {e}")
                    analytics_text = """
📈 MAILCHIMP ANALYTICS & PERFORMANCE DATA
================================================================

⚠️ Unable to connect to MailChimp API
Error: """ + str(e) + """

🔧 TROUBLESHOOTING:
1. Check MailChimp API key in Settings tab
2. Verify internet connection
3. Ensure MailChimp account is active

"""
            else:
                analytics_text = """
📈 MAILCHIMP ANALYTICS & PERFORMANCE DATA
================================================================

⚠️ AI service not initialized

🔧 TROUBLESHOOTING:
1. Check MailChimp API key in Settings tab
2. Verify XAI API key is configured
3. Restart the application

"""
            
            # Add sample/demo data regardless
            analytics_text += """
📊 SAMPLE ANALYTICS DATA (Demo):
================================================================

📧 Recent Campaign Performance:
  • Fiber Campaign: 1,250 sent, 32% open rate, 8% click rate
  • Security Campaign: 980 sent, 28% open rate, 12% click rate
  • General Outreach: 1,500 sent, 25% open rate, 6% click rate
  • Follow-up Campaign: 750 sent, 35% open rate, 15% click rate

📈 Account Summary:
  • Total Contacts: 15,420
  • Campaigns Sent: 47
  • Average Open Rate: 28.5%
  • Average Click Rate: 8.7%

🎯 OPTIMIZATION INSIGHTS:
  • Best performing subject lines tend to be personal and urgent
  • Tuesday-Thursday 10AM-2PM shows highest engagement
  • Fiber-related campaigns average 32% open rate
  • Security campaigns average 28% open rate
  • Follow-up campaigns show 15% higher conversion

📈 RECOMMENDATIONS:
  • A/B test subject lines with urgency vs. benefit focus
  • Segment campaigns by property type (fiber vs. non-fiber)
  • Implement drip campaigns for non-responders
  • Use personalization tokens for higher engagement
  • Focus on mobile-friendly email designs
"""
            
            self.analytics_display.setText(analytics_text)
            
        except Exception as e:
            error_text = f"""
📈 MAILCHIMP ANALYTICS - ERROR
================================================================

❌ Error loading analytics: {str(e)}

🔧 Please check:
1. MailChimp API key in Settings
2. Internet connection
3. Application logs for details

📊 SAMPLE DATA (Demo):
  • Fiber Campaigns: 32% avg open rate
  • Security Campaigns: 28% avg open rate
  • General Outreach: 25% avg open rate
"""
            self.analytics_display.setText(error_text)
            print(f"Analytics loading error: {e}")

    def send_chat(self):
        """AI chat with command control"""
        query = self.chat_input.text()
        if not query.strip():
            return
        
        self.chat_display.append(f'You: {query}')
        self.chat_input.clear()
        
        # Check if it's a command first
        if self.command_controller and self.command_controller.is_command(query):
            result = self.command_controller.execute_command(query)
            if result.success:
                self.chat_display.append(f'🤖 {result.message}')
            else:
                self.chat_display.append(f'❌ {result.message}')
        else:
            # Use regular AI chat for general questions
            try:
                self._ensure_service_initialized()
                
                if self.service:
                    response = self.service.xai_chat(query)
                    self.chat_display.append(f'AI: {response}')
                else:
                    self.chat_display.append('AI service not available')
                    
            except Exception as e:
                self.chat_display.append(f'❌ Chat error: {str(e)}')
                # Try fallback
                try:
                    from utils.ai_fallback import simple_ai_chat
                    fallback_response = simple_ai_chat(query)
                    self.chat_display.append(f'AI: {fallback_response}')
                    self.chat_display.append('ℹ️ Using fallback AI service')
                except:
                    self.chat_display.append('❌ AI service unavailable')
    
    def on_command_executed(self, action, result):
        """Handle command execution results"""
        self.chat_display.append(f'🎯 Command executed: {action}')
        self.chat_display.append(f'📋 Result: {result}')
    
    def on_status_updated(self, status):
        """Handle status updates"""
        self.chat_display.append(f'🔄 {status}')
    
    def on_error_occurred(self, error):
        """Handle error messages"""
        self.chat_display.append(f'❌ {error}')
    
    def _fallback_send_chat(self, query):
        """Fallback AI chat implementation"""
        try:
            self._ensure_service_initialized()
            if self.service:
                response = self.service.xai_chat(query)
                self.chat_display.append(f'XAI: {response}')
            else:
                self.chat_display.append('AI service not available')
        except Exception as e:
            self.chat_display.append(f'Error: {str(e)}')

    def voice_chat(self):
        """Stable voice chat with better microphone handling"""
        try:
            # Try to use the stable voice chat utility
            from utils.stable_voice_chat import stable_voice_chat
            from utils.resource_manager import register_worker
            
            self.chat_display.append("🎤 Starting stable voice chat...")
            
            # Use the stable voice chat worker
            worker = stable_voice_chat(self)
            
            if worker:
                # Register for cleanup
                register_worker(worker)
                
                # Connect signals
                def on_voice_heard(text):
                    self.chat_display.append(f"✅ Heard: {text}")
                    
                    # Check if it's a command
                    if self.command_controller and self.command_controller.is_command(text):
                        result = self.command_controller.execute_command(text)
                        if result.success:
                            self.chat_display.append(f'🤖 {result.message}')
                        else:
                            self.chat_display.append(f'❌ {result.message}')
                    else:
                        # Use regular AI chat
                        self.chat_input.setText(text)
                        self.send_chat()
                
                def on_error(error):
                    self.chat_display.append(f"❌ Voice error: {error}")
                
                def on_status(status):
                    self.chat_display.append(status)
                
                def on_finished():
                    self.chat_display.append("🎤 Voice chat finished")
                
                worker.voice_heard.connect(on_voice_heard)
                worker.error_occurred.connect(on_error)
                worker.status_update.connect(on_status)
                worker.finished_signal.connect(on_finished)
                
            else:
                self.chat_display.append("❌ Failed to start voice chat")
                
        except ImportError:
            # Fallback to original implementation if stable utilities not available
            self.chat_display.append("⚠️ Stable voice chat not available, using fallback...")
            self._fallback_voice_chat()
            
        except Exception as e:
            self.chat_display.append(f"❌ Voice chat error: {str(e)}")
            self.chat_display.append("  • Check microphone permissions")
            self.chat_display.append("  • Ensure microphone is connected")
    
    def _fallback_voice_chat(self):
        """Fallback voice chat implementation"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Adjust for ambient noise
            with sr.Microphone() as source:
                self.chat_display.append("🎤 Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
            with sr.Microphone() as source:
                self.chat_display.append("🎤 Listening... (speak now)")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                
            self.chat_display.append("🔄 Processing speech...")
            
            try:
                query = recognizer.recognize_google(audio)
                self.chat_display.append(f"✅ Heard: {query}")
                self.chat_input.setText(query)
                self.send_chat()
                
            except sr.UnknownValueError:
                self.chat_display.append("❌ Could not understand audio. Please try:")
                self.chat_display.append("  • Speaking more clearly")
                self.chat_display.append("  • Moving closer to microphone") 
                self.chat_display.append("  • Reducing background noise")
                
            except sr.RequestError as e:
                self.chat_display.append(f"❌ Speech service error: {e}")
                self.chat_display.append("  • Check internet connection")
                self.chat_display.append("  • Try again in a moment")
                
        except ImportError:
            self.chat_display.append("❌ Speech recognition not available")
            self.chat_display.append("  • Install: pip install SpeechRecognition pyaudio")
            
        except Exception as e:
            self.chat_display.append(f"❌ Voice chat error: {str(e)}")
            self.chat_display.append("  • Check microphone permissions")
            self.chat_display.append("  • Ensure microphone is connected")

    def toggle_conversation(self):
        if not self.conversation_active:
            self.conversation_active = True
            self.conversation_btn.setText('🛑 Stop Conversation')
            self.start_conversation()
        else:
            self.conversation_active = False
            self.conversation_btn.setText('💬 Start Conversation')

    def start_conversation(self):
        """Start crash-safe continuous conversation"""
        try:
            # Try to use safe conversation utilities
            from utils.safe_ai_chat import SafeVoiceChatWorker, SafeAIChatWorker
            from utils.resource_manager import register_worker
            import threading
            import time
            
            def safe_conversation_loop():
                try:
                    import pyttsx3
                    
                    engine = pyttsx3.init()
                    
                    # Add safety timeout to prevent infinite loops
                    conversation_timeout = 300  # 5 minutes maximum conversation time
                    start_time = time.time()
                    
                    # Adjust speech rate for natural conversation
                    rate = engine.getProperty('rate')
                    engine.setProperty('rate', rate - 20)  # Slightly reduce speech rate for clarity
                    
                    # Set voice properties for better quality
                    voices = engine.getProperty('voices')
                    if voices:
                        # Try to find a better quality voice (prefer female voices for clarity)
                        female_voice = None
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'samantha' in voice.name.lower() or 'victoria' in voice.name.lower():
                                female_voice = voice
                                break
                        
                        if female_voice:
                            engine.setProperty('voice', female_voice.id)
                        else:
                            engine.setProperty('voice', voices[0].id)  # Fallback to first available voice
                    
                    # Set volume for better audio quality
                    volume = engine.getProperty('volume')
                    engine.setProperty('volume', 0.9)  # Slightly reduce volume for clarity
                    
                    engine.say("Hello! I'm ready to help with your marketing strategies. What would you like to discuss?")
                    engine.runAndWait()
                    
                    while self.conversation_active:
                        # Safety timeout check
                        if time.time() - start_time > conversation_timeout:
                            self.chat_display.append("❌ Conversation timeout - ending session")
                            engine.say("Our conversation has reached the time limit. Feel free to start a new session.")
                            engine.runAndWait()
                            self.conversation_active = False
                            self.conversation_btn.setText('💬 Start Conversation')
                            break
                        
                        try:
                            # Use improved voice recognition
                            from utils.improved_voice_chat import ImprovedVoiceChatWorker
                            voice_worker = ImprovedVoiceChatWorker()
                            register_worker(voice_worker)
                            
                            # Wait for voice input
                            voice_worker.start()
                            voice_worker.wait(15000)  # Wait up to 15 seconds for voice input
                            
                            if voice_worker.isFinished():
                                # Process the voice input
                                query = voice_worker.recognized_text if hasattr(voice_worker, 'recognized_text') else None
                                
                                if query:
                                    self.chat_display.append(f"You: {query}")
                                    
                                    if "goodbye" in query.lower() or "stop" in query.lower():
                                        engine.say("Goodbye! Feel free to start another conversation anytime.")
                                        engine.runAndWait()
                                        self.conversation_active = False
                                        self.conversation_btn.setText('💬 Start Conversation')
                                        break
                                    
                                    # Use safe AI chat
                                    self._ensure_service_initialized()
                                    if self.service:
                                        ai_worker = SafeAIChatWorker(query, self.service)
                                        register_worker(ai_worker)
                                        
                                        ai_worker.start()
                                        ai_worker.wait(30000)  # Wait up to 30 seconds for AI response
                                        
                                        if ai_worker.isFinished():
                                            response = ai_worker.response if hasattr(ai_worker, 'response') else None
                                            
                                            if response:
                                                self.chat_display.append(f"AI: {response}")
                                                
                                                # Limit response length for better speech quality
                                                if len(response) > 200:
                                                    response = response[:200] + "... I can provide more details if needed."
                                                
                                                engine.say(response)
                                                engine.runAndWait()
                                            else:
                                                self.chat_display.append("AI: I'm sorry, I couldn't generate a response.")
                                                engine.say("I'm sorry, I couldn't generate a response.")
                                                engine.runAndWait()
                                    else:
                                        response = "AI service not available"
                                        self.chat_display.append(f"AI: {response}")
                                        engine.say(response)
                                        engine.runAndWait()
                            
                        except Exception as e:
                            self.chat_display.append(f"❌ Conversation error: {str(e)}")
                            engine.say("I encountered an error. Please try again.")
                            engine.runAndWait()
                            continue
                    
                    # Cleanup
                    try:
                        engine.stop()
                    except:
                        pass
                        
                except Exception as e:
                    self.chat_display.append(f"❌ Conversation setup error: {str(e)}")
                    self.conversation_active = False
                    self.conversation_btn.setText('💬 Start Conversation')
            
            # Start conversation in a separate thread
            conversation_thread = threading.Thread(target=safe_conversation_loop, daemon=True)
            conversation_thread.start()
            
        except ImportError:
            # Fallback to original implementation
            self.chat_display.append("⚠️ Safe conversation not available, using fallback...")
            self._fallback_start_conversation()
            
        except Exception as e:
            self.chat_display.append(f"❌ Failed to start conversation: {str(e)}")
            self.conversation_active = False
            self.conversation_btn.setText('💬 Start Conversation')
    
    def _fallback_start_conversation(self):
        """Fallback conversation implementation"""
        import speech_recognition as sr
        import pyttsx3
        import threading
        
        def conversation_loop():
            recognizer = sr.Recognizer()
            engine = pyttsx3.init()
            
            # Add safety timeout to prevent infinite loops
            conversation_timeout = 300  # 5 minutes maximum conversation time
            start_time = time.time()
            
            # Adjust speech rate for natural conversation
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate - 20)  # Slightly reduce speech rate for clarity
            
            # Set voice properties for better quality
            voices = engine.getProperty('voices')
            if voices:
                # Try to find a better quality voice (prefer female voices for clarity)
                female_voice = None
                for voice in voices:
                    if 'female' in voice.name.lower() or 'samantha' in voice.name.lower() or 'victoria' in voice.name.lower():
                        female_voice = voice
                        break
                
                if female_voice:
                    engine.setProperty('voice', female_voice.id)
                else:
                    engine.setProperty('voice', voices[0].id)  # Fallback to first available voice
            
            # Set volume for better audio quality
            volume = engine.getProperty('volume')
            engine.setProperty('volume', 0.9)  # Slightly reduce volume for clarity
            
            engine.say("Hello! I'm ready to help with your marketing strategies. What would you like to discuss?")
            engine.runAndWait()
            
            while self.conversation_active:
                # Safety timeout check
                if time.time() - start_time > conversation_timeout:
                    self.chat_display.append("❌ Conversation timeout - ending session")
                    engine.say("Our conversation has reached the time limit. Feel free to start a new session.")
                    engine.runAndWait()
                    self.conversation_active = False
                    self.conversation_btn.setText('💬 Start Conversation')
                    break
                try:
                    with sr.Microphone() as source:
                        self.chat_display.append("🎤 Listening...")
                        # Add noise adjustment for better recognition
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                    
                    query = recognizer.recognize_google(audio)
                    self.chat_display.append(f"You: {query}")
                    
                    if "goodbye" in query.lower() or "stop" in query.lower():
                        engine.say("Goodbye! Feel free to start another conversation anytime.")
                        engine.runAndWait()
                        self.conversation_active = False
                        self.conversation_btn.setText('💬 Start Conversation')
                        break
                    
                    self._ensure_service_initialized()
                    if self.service:
                        try:
                            response = self.service.xai_chat(query)
                            if response:
                                self.chat_display.append(f"AI: {response}")
                                
                                # Limit response length for better speech quality
                                if len(response) > 200:
                                    response = response[:200] + "... I can provide more details if needed."
                                
                                engine.say(response)
                                engine.runAndWait()
                            else:
                                self.chat_display.append("AI: I'm sorry, I couldn't generate a response.")
                                engine.say("I'm sorry, I couldn't generate a response.")
                                engine.runAndWait()
                        except Exception as ai_error:
                            self.chat_display.append(f"❌ AI Error: {str(ai_error)}")
                            engine.say("I'm having trouble processing that request. Please try again.")
                            engine.runAndWait()
                    else:
                        response = "AI service not available"
                        self.chat_display.append(f"AI: {response}")
                        engine.say(response)
                        engine.runAndWait()
                    
                except sr.UnknownValueError:
                    self.chat_display.append("❌ Could not understand audio")
                    engine.say("I didn't catch that. Could you repeat?")
                    engine.runAndWait()
                except sr.RequestError as req_error:
                    self.chat_display.append(f"❌ Speech service error: {req_error}")
                    engine.say("Speech recognition service is having issues. Please try again.")
                    engine.runAndWait()
                    break
                except sr.WaitTimeoutError:
                    self.chat_display.append("❌ Listening timeout")
                    engine.say("I didn't hear anything. Please try speaking again.")
                    engine.runAndWait()
                except Exception as e:
                    self.chat_display.append(f"❌ Error: {str(e)}")
                    engine.say("I encountered an error. Please try again.")
                    engine.runAndWait()
                    # Don't break on general errors, just continue
                    continue
        
        threading.Thread(target=conversation_loop, daemon=True).start()
        
        # Add cleanup
        import atexit
        def cleanup_engine():
            engine.stop()
            engine = None
        atexit.register(cleanup_engine)
        
        # Enhanced cleanup
        def enhanced_cleanup():
            try:
                engine.stop()
                engine.endLoop()
                import multiprocessing
                multiprocessing.active_children()  # Clean up children
                for p in multiprocessing.active_children():
                    p.terminate()
                    p.join()
            except:
                pass
        atexit.register(enhanced_cleanup)
    
    @Slot()
    def load_pending_campaigns(self):
        """Load pending campaigns from main window"""
        try:
            print(f"[AI Widget] load_pending_campaigns called")
            print(f"[AI Widget] Parent: {self.parent()}")
            print(f"[AI Widget] Parent type: {type(self.parent())}")
            
            # Get campaigns from main window
            if self.parent() and hasattr(self.parent(), 'pending_campaigns'):
                campaigns = self.parent().pending_campaigns
                print(f"[AI Widget] Found pending campaigns: {campaigns is not None}")
                if campaigns:
                    print(f"[AI Widget] Campaign count: {len(campaigns)}")
                    print(f"[AI Widget] Campaign types: {list(campaigns.keys())}")
                    
                    # FILTER OUT OLD CAMPAIGN TYPES to prevent duplicates
                    # Only allow the new single campaign types from automation worker
                    allowed_campaign_types = [
                        'att_fiber_main', 'adt_security_main',  # From automation worker
                        'incident_fire_', 'incident_burglary_', 'incident_',  # Incident campaigns
                        'att_fiber_comprehensive'  # From test methods
                    ]
                    
                    filtered_campaigns = {}
                    for campaign_id, campaign_data in campaigns.items():
                        # Check if campaign ID starts with any allowed type
                        if any(campaign_id.startswith(allowed_type) for allowed_type in allowed_campaign_types):
                            filtered_campaigns[campaign_id] = campaign_data
                        else:
                            print(f"[AI Widget] Filtering out old campaign type: {campaign_id}")
                    
                    if filtered_campaigns:
                        print(f"[AI Widget] Showing {len(filtered_campaigns)} filtered campaigns: {list(filtered_campaigns.keys())}")
                        self.show_campaigns_for_review(filtered_campaigns)
                    else:
                        print("[AI Widget] All campaigns filtered out - no valid campaigns")
                        self.campaign_status_label.setText("❌ No valid campaigns found")
                else:
                    print("[AI Widget] Pending campaigns is empty")
                    self.campaign_status_label.setText("❌ No campaigns generated")
            else:
                print("[AI Widget] No pending campaigns found in main window")
                if self.parent():
                    has_pending = hasattr(self.parent(), 'pending_campaigns')
                    print(f"[AI Widget] Parent has pending_campaigns attribute: {has_pending}")
                    if has_pending:
                        print(f"[AI Widget] pending_campaigns value: {getattr(self.parent(), 'pending_campaigns', 'None')}")
                else:
                    print("[AI Widget] No parent found")
                self.campaign_status_label.setText("❌ No campaigns available")
        except Exception as e:
            print(f"[AI Widget] Error loading pending campaigns: {e}")
            import traceback
            traceback.print_exc()
            self.campaign_status_label.setText(f"❌ Error loading campaigns: {str(e)}")

    def test_campaign_display(self):
        """Generate REAL campaigns from ALL verified fiber data sources"""
        print("[AI Widget] Generating REAL campaigns from ALL fiber data sources...")
        
        try:
            import pandas as pd
            import glob
            from datetime import datetime
            
            all_fiber_leads = []
            sources_found = []
            
            # Source 1: ActiveKnocker Fiber Leads
            activeknocker_files = glob.glob("ActiveKnocker_Fiber_Leads_*.csv")
            if activeknocker_files:
                latest_ak_file = max(activeknocker_files, key=os.path.getctime)
                print(f"[AI Widget] Loading ActiveKnocker data: {latest_ak_file}")
                try:
                    ak_df = pd.read_csv(latest_ak_file)
                    ak_df = ak_df.dropna(subset=['Full_Address', 'City'])
                    ak_fiber = ak_df[ak_df['Lead_Type'] == 'AT&T Fiber Available']
                    print(f"[AI Widget] ✅ ActiveKnocker: {len(ak_fiber)} verified fiber leads")
                    
                    for _, row in ak_fiber.iterrows():
                        all_fiber_leads.append({
                            'address': row.get('Full_Address', ''),
                            'city': row.get('City', ''),
                            'state': row.get('State', ''),
                            'zip': row.get('ZIP', ''),
                            'price': row.get('Price', ''),
                            'source': 'ActiveKnocker + AT&T Verification',
                            'verified_date': row.get('Verified_Date', ''),
                            'fiber_confirmed': True,
                            'lead_type': 'AT&T Fiber Available',
                            'mls': row.get('MLS_Number', ''),
                            'assign_to': row.get('Assign_To', 'Sales Team')
                        })
                    sources_found.append(f"ActiveKnocker: {len(ak_fiber)} leads")
                except Exception as e:
                    print(f"[AI Widget] ⚠️ Error loading ActiveKnocker: {e}")
            
            # Source 2: AT&T Fiber Master Database
            if os.path.exists("att_fiber_master.csv"):
                print(f"[AI Widget] Loading AT&T Master Database: att_fiber_master.csv")
                try:
                    master_df = pd.read_csv("att_fiber_master.csv")
                    master_fiber = master_df[master_df['fiber_available'] == True]
                    print(f"[AI Widget] ✅ AT&T Master: {len(master_fiber)} verified fiber leads")
                    
                    for _, row in master_fiber.iterrows():
                        all_fiber_leads.append({
                            'address': row.get('address', ''),
                            'city': row.get('city', ''),
                            'state': row.get('state', ''),
                            'zip': row.get('zip', ''),
                            'source': 'AT&T Master Database + FCC Verification',
                            'verified_date': row.get('processed_date', ''),
                            'fiber_confirmed': True,
                            'lead_type': 'AT&T Fiber Available',
                            'block_geoid': row.get('block_geoid', ''),
                            'assign_to': 'Sales Team'
                        })
                    sources_found.append(f"AT&T Master: {len(master_fiber)} leads")
                except Exception as e:
                    print(f"[AI Widget] ⚠️ Error loading AT&T Master: {e}")
            
            # Source 3: Comprehensive Fiber Summary
            if os.path.exists("comprehensive_fiber_summary_20250710_105432.csv"):
                print(f"[AI Widget] Loading Comprehensive Summary: comprehensive_fiber_summary_20250710_105432.csv")
                try:
                    comp_df = pd.read_csv("comprehensive_fiber_summary_20250710_105432.csv")
                    comp_fiber = comp_df[comp_df['fiber_available'] == True]
                    print(f"[AI Widget] ✅ Comprehensive: {len(comp_fiber)} verified fiber leads")
                    
                    for _, row in comp_fiber.iterrows():
                        all_fiber_leads.append({
                            'address': row.get('address', ''),
                            'city': row.get('city', ''),
                            'state': row.get('state', ''),
                            'zip': row.get('zip', ''),
                            'source': 'Comprehensive Fiber Database + FCC Verification',
                            'verified_date': row.get('processed_date', ''),
                            'fiber_confirmed': True,
                            'lead_type': 'AT&T Fiber Available',
                            'block_geoid': row.get('block_geoid', ''),
                            'assign_to': 'Sales Team'
                        })
                    sources_found.append(f"Comprehensive: {len(comp_fiber)} leads")
                except Exception as e:
                    print(f"[AI Widget] ⚠️ Error loading Comprehensive: {e}")
            
            if not all_fiber_leads:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "No Fiber Data", "No verified fiber leads found in any data source!")
                return
            
            # Remove duplicates based on address
            seen_addresses = set()
            unique_leads = []
            for lead in all_fiber_leads:
                address = lead.get('address', '')
                if isinstance(address, str):
                    addr_key = address.lower().strip()
                    if addr_key not in seen_addresses:
                        seen_addresses.add(addr_key)
                        unique_leads.append(lead)
                else:
                    print(f"[AI Widget] Skipping lead with non-string address: {address} (type: {type(address)})")
            
            total_leads = len(unique_leads)
            duplicate_count = len(all_fiber_leads) - total_leads
            
            print(f"[AI Widget] 🎯 CONSOLIDATED: {total_leads} unique verified fiber leads (removed {duplicate_count} duplicates)")
            
            # Group by city for campaign targeting
            city_breakdown = {}
            for lead in unique_leads:
                city = lead['city']
                if city not in city_breakdown:
                    city_breakdown[city] = []
                city_breakdown[city].append(lead)
            
            print(f"[AI Widget] 🌍 City breakdown: {dict((city, len(leads)) for city, leads in city_breakdown.items())}")
            
            # Create comprehensive campaign with all verified leads
            real_campaigns = {
                'att_fiber_comprehensive': {
                    'title': f'🌐 AT&T Fiber - Multi-City Campaign ({total_leads:,} Verified Leads)',
                    'icon': '🌐',
                    'target_audience': f'Verified AT&T Fiber Properties Across {len(city_breakdown)} Cities',
                    'company_name': 'Seaside Security',
                    'target_contacts': total_leads,
                    'subject_lines': [
                        'Your Property is AT&T Fiber Verified - Upgrade Today!',
                        'Confirmed: High-Speed Fiber Internet at Your Address',
                        'AT&T Fiber Service Verified for Your Home',
                        'Lightning-Fast Internet - Schedule Your Installation Now'
                    ],
                    'email_body': """
Dear {assign_to},

🌐 **AT&T Fiber Verified at Your Property**

Our comprehensive fiber verification system has confirmed that high-speed AT&T Fiber internet is available at your address: {address}

🚀 **Why AT&T Fiber?**
• Lightning-fast speeds up to 1 Gig
• Perfect for work-from-home and streaming
• No data caps or bandwidth throttling
• Professional installation included
• Competitive pricing with bundle options

📍 **Your Verified Property:**
• Address: {address}
• City: {city}, {state} {zip}
• Verification Source: {source}
• Verified Date: {verified_date}

🎯 **Ready to Upgrade?**
Contact Seaside Security today to schedule your AT&T Fiber installation!

📞 Call: (910) 597-4085
🌐 Online: seasidesecurity.net/fiber

Best regards,
The AT&T Fiber Team
Seaside Security & Communications

*This message was sent because your property has been verified as AT&T Fiber ready through multiple verification systems.*
""",
                    'call_to_action': 'Schedule AT&T Fiber Installation',
                    'predicted_open_rate': 0.35,
                    'predicted_click_rate': 0.15,
                    'contacts': unique_leads,  # ALL consolidated leads
                    'mailchimp_insights': [
                        f'Multi-source verification increases trust by 50%',
                        f'Cross-city campaigns have 35% open rates',
                        f'FCC + multiple database verification builds credibility'
                    ],
                    'optimization_tips': [
                        'Segment by city for localized messaging',
                        'Mention multiple verification sources for credibility',
                        'Use urgency without being pushy',
                        'Include verification details for trust'
                    ]
                }
            }
            
            # Display the consolidated campaigns
            self.show_campaigns_for_review(real_campaigns)
            
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "COMPREHENSIVE Fiber Campaigns", 
                                  f"✅ Generated comprehensive AT&T Fiber campaign with {total_leads:,} VERIFIED leads!\n\n"
                                  f"📊 Data Sources Consolidated:\n" + "\n".join([f"  • {source}" for source in sources_found]) + 
                                  f"\n\n🌍 Cities Covered: {', '.join(city_breakdown.keys())}\n"
                                  f"🔍 Verification: FCC census blocks + multiple databases\n"
                                  f"📧 Ready for MailChimp segmented campaigns\n\n"
                                  f"This includes ALL verified fiber leads from multiple sources!")
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error Loading Comprehensive Data", f"Error generating comprehensive campaigns: {e}")
            print(f"Error in comprehensive campaign generation: {e}")
            import traceback
            traceback.print_exc()
    
    def test_incident_campaigns(self):
        """Test incident campaign generation and display"""
        try:
            from workers.incident_automation_worker import IncidentAutomationWorker
            from PySide6.QtWidgets import QMessageBox
            
            # Create test incident data
            test_incidents = [
                {
                    'type': 'fire',
                    'address': '123 Main St, Wilmington, NC',
                    'location': '123 Main St, Wilmington, NC',
                    'date': datetime.now().isoformat(),
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'High',
                    'details': 'House fire on Main Street'
                }
            ]
            
            # Create test contacts 
            test_contacts = [
                {
                    'owner_name': 'John Smith',
                    'first_name': 'John',
                    'address': '125 Main St, Wilmington, NC',
                    'owner_email': 'john@example.com',
                    'incident_type': 'fire'
                },
                {
                    'owner_name': 'Jane Doe',
                    'first_name': 'Jane', 
                    'address': '127 Main St, Wilmington, NC',
                    'owner_email': 'jane@example.com',
                    'incident_type': 'fire'
                },
                {
                    'owner_name': 'Bob Wilson',
                    'first_name': 'Bob', 
                    'address': '121 Main St, Wilmington, NC',
                    'owner_email': 'bob@example.com',
                    'incident_type': 'fire'
                }
            ]
            
            # Generate incident campaigns
            worker = IncidentAutomationWorker([], 50)
            campaigns = []
            
            for incident in test_incidents:
                incident_contacts = [c for c in test_contacts if c['incident_type'] == incident['type']]
                
                if len(incident_contacts) >= 2:
                    campaign = worker.generate_incident_email_campaign_with_contacts(incident, incident_contacts)
                    if campaign:
                        campaigns.append(campaign)
            
            if campaigns:
                # Display incident campaigns
                self.handle_incident_campaigns(campaigns)
                
                QMessageBox.information(self, "Test Incident Campaigns Generated", 
                                      f"🚨 Generated {len(campaigns)} test incident campaigns!\n\n"
                                      f"These campaigns demonstrate:\n"
                                      f"• Fire safety response messaging\n"
                                      f"• Template variable replacement\n"
                                      f"• HTML rendering with buttons and images\n"
                                      f"• Incident-specific targeting\n\n"
                                      f"Click 'Preview Email' on any campaign to see the full formatted content.")
            else:
                QMessageBox.warning(self, "Test Failed", "Could not generate test incident campaigns.")
                
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Test Error", f"Error generating test incident campaigns: {e}")

    @Slot(object)
    def handle_regular_campaigns(self, campaigns):
        """Handle regular campaigns from automation worker with filtering"""
        try:
            print(f"[AI Widget] Received {len(campaigns)} regular campaigns from automation")
            
            if not campaigns:
                self.campaign_status_label.setText("❌ No campaigns received")
                return
            
            # FILTER OUT OLD CAMPAIGN TYPES to prevent duplicates
            # Only allow the new single campaign types from automation worker
            allowed_campaign_types = [
                'att_fiber_main', 'adt_security_main',  # Correct automation campaigns
                'att_fiber_comprehensive'  # From test methods
            ]
            
            filtered_campaigns = {}
            for campaign_id, campaign_data in campaigns.items():
                # Check if campaign ID is in allowed types
                if campaign_id in ['att_fiber_main', 'adt_security_main'] or \
                   any(campaign_id.startswith(allowed_type) for allowed_type in allowed_campaign_types):
                    filtered_campaigns[campaign_id] = campaign_data
                    print(f"[AI Widget] Accepting campaign: {campaign_id}")
                else:
                    print(f"[AI Widget] Filtering out old campaign type: {campaign_id}")
            
            if filtered_campaigns:
                print(f"[AI Widget] Displaying {len(filtered_campaigns)} filtered campaigns: {list(filtered_campaigns.keys())}")
                # Clear any existing campaigns before showing new ones
                self.current_campaigns = filtered_campaigns
                self.show_campaigns_for_review(filtered_campaigns)
            else:
                print("[AI Widget] All campaigns filtered out - no valid campaigns")
                self.campaign_status_label.setText("❌ No valid campaigns received")
                
        except Exception as e:
            print(f"[AI Widget] Error handling regular campaigns: {e}")
            import traceback
            traceback.print_exc()
            self.campaign_status_label.setText(f"❌ Error processing campaigns: {str(e)}")

    @Slot(object)
    def show_campaigns_for_review(self, campaigns):
        """Show generated campaigns for review"""
        try:
            print(f"[AI Widget] Showing campaigns for review: {campaigns}")
            
            if not campaigns:
                self.campaign_status_label.setText("❌ No campaigns generated")
                return
            
            # Ensure campaigns is a dictionary
            if not isinstance(campaigns, dict):
                print(f"[AI Widget] ERROR: Expected dict, got {type(campaigns)}")
                self.campaign_status_label.setText("❌ Invalid campaign data format")
                return
            
            # Store campaigns for modification
            self.current_campaigns = campaigns
            
            self.campaign_status_label.setText(f"📧 {len(campaigns)} campaigns ready for review")
            
            # Clear existing campaign tabs and list
            self.campaign_tabs.clear()
            self.clear_campaign_list()
            
            # Add campaign cards to list view
            for campaign_type, campaign_data in campaigns.items():
                print(f"[AI Widget] Adding campaign card for {campaign_type}: {campaign_data.get('title', 'No title')}")
                self.add_campaign_card(campaign_type, campaign_data)
            
            # Add tabs for each campaign
            for campaign_type, campaign_data in campaigns.items():
                try:
                    print(f"[AI Widget] Creating tab for {campaign_type}")
                    tab = self.create_campaign_tab(campaign_type, campaign_data)
                    
                    # Get display name and icon
                    display_name = campaign_data.get('title', campaign_type.replace('_', ' ').title())
                    icon = campaign_data.get('icon', '📧')
                    
                    self.campaign_tabs.addTab(tab, f"{icon} {display_name}")
                    print(f"[AI Widget] Added tab: {display_name}")
                    
                except Exception as e:
                    print(f"[AI Widget] Error creating tab for {campaign_type}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Enable action buttons
            self.approve_all_btn.setEnabled(True)
            self.reject_all_btn.setEnabled(True)
            self.regenerate_btn.setEnabled(True)
            
            print(f"[AI Widget] Campaign review interface updated with {self.campaign_tabs.count()} tabs")
            
        except Exception as e:
            print(f"[AI Widget] Error in show_campaigns_for_review: {e}")
            import traceback
            traceback.print_exc()
            self.campaign_status_label.setText(f"❌ Error displaying campaigns: {str(e)}")
    
    def create_campaign_tab(self, campaign_type, campaign_data):
        """Create a tab for reviewing a single campaign"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Campaign header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(campaign_data.get('title', campaign_type.replace('_', ' ').title()))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Campaign stats
        stats_label = QLabel(f"📊 {campaign_data.get('target_contacts', 0)} contacts")
        stats_label.setStyleSheet("color: #bdc3c7; font-weight: bold;")
        header_layout.addWidget(stats_label)
        
        layout.addLayout(header_layout)
        
        # Campaign overview card
        overview_group = QGroupBox("📋 Campaign Overview")
        overview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: #2c3e50;
                color: #ecf0f1;
            }
        """)
        overview_layout = QVBoxLayout(overview_group)
        
        # Target audience
        audience_label = QLabel(f"🎯 Target Audience: {campaign_data.get('target_audience', 'N/A')}")
        audience_label.setStyleSheet("color: #ecf0f1; font-size: 12px; margin: 5px;")
        overview_layout.addWidget(audience_label)
        
        # Subject lines preview
        subject_label = QLabel("📝 Subject Line Options:")
        subject_label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #ecf0f1;")
        overview_layout.addWidget(subject_label)
        
        subject_lines = campaign_data.get('subject_lines', [])
        for i, subject in enumerate(subject_lines[:2]):  # Show only first 2
            subject_item = QLabel(f"  {i+1}. {subject}")
            subject_item.setStyleSheet("margin-left: 20px; color: #bdc3c7; font-size: 11px;")
            overview_layout.addWidget(subject_item)
        
        if len(subject_lines) > 2:
            more_label = QLabel(f"  ... and {len(subject_lines) - 2} more")
            more_label.setStyleSheet("margin-left: 20px; color: #95a5a6; font-size: 10px; font-style: italic;")
            overview_layout.addWidget(more_label)
        
        # Email preview button
        preview_btn = QPushButton("👁️ Preview Email Content")
        preview_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                margin: 5px 0;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        preview_btn.clicked.connect(lambda: self.show_email_preview(campaign_type, campaign_data))
        overview_layout.addWidget(preview_btn)
        
        layout.addWidget(overview_group)
        
        # Performance predictions
        perf_group = QGroupBox("📈 Performance Predictions")
        perf_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: #2c3e50;
                color: #ecf0f1;
            }
        """)
        perf_layout = QVBoxLayout(perf_group)
        
        open_rate = campaign_data.get('predicted_open_rate', 0) * 100
        click_rate = campaign_data.get('predicted_click_rate', 0) * 100
        
        perf_label = QLabel(f"""
📖 Predicted Open Rate: {open_rate:.1f}%
🖱️ Predicted Click Rate: {click_rate:.1f}%
🎯 Call to Action: {campaign_data.get('call_to_action', 'N/A')}
""")
        perf_label.setStyleSheet("color: #ecf0f1; font-size: 12px; margin: 5px;")
        perf_layout.addWidget(perf_label)
        
        layout.addWidget(perf_group)
        
        # MailChimp insights (condensed)
        insights_group = QGroupBox("💡 Key Insights")
        insights_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: #2c3e50;
                color: #ecf0f1;
            }
        """)
        insights_layout = QVBoxLayout(insights_group)
        
        insights = campaign_data.get('mailchimp_insights', [])
        optimization_tips = campaign_data.get('optimization_tips', [])
        
        insights_content = ""
        if insights:
            insights_content += "📊 Key Insights:\n"
            for insight in insights[:2]:  # Show only first 2
                insights_content += f"  • {insight}\n"
        
        if optimization_tips:
            insights_content += "\n🎯 Optimization Tips:\n"
            for tip in optimization_tips[:2]:  # Show only first 2
                insights_content += f"  • {tip}\n"
        
        insights_label = QLabel(insights_content)
        insights_label.setStyleSheet("color: #ecf0f1; font-size: 11px; margin: 5px;")
        insights_label.setWordWrap(True)
        insights_layout.addWidget(insights_label)
        
        layout.addWidget(insights_group)
        
        # Individual campaign actions
        actions_layout = QHBoxLayout()
        
        approve_btn = QPushButton("✅ Approve")
        approve_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        approve_btn.clicked.connect(lambda: self.approve_campaign(campaign_type))
        actions_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌ Reject")
        reject_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        reject_btn.clicked.connect(lambda: self.reject_campaign(campaign_type))
        actions_layout.addWidget(reject_btn)
        
        modify_btn = QPushButton("✏️ Modify")
        modify_btn.setStyleSheet("""
            QPushButton {
                background: #ffc107;
                color: #212529;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #e0a800; }
        """)
        modify_btn.clicked.connect(lambda: self.modify_campaign(campaign_type))
        actions_layout.addWidget(modify_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return tab
    
    def show_email_preview(self, campaign_type, campaign_data):
        """Show a detailed email preview dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox, QScrollArea
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Email Preview - {campaign_data.get('title', campaign_type)}")
        dialog.setModal(True)
        dialog.resize(700, 600)
        dialog.setStyleSheet("""
            QDialog {
                background: #2c3e50;
                color: #ecf0f1;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"📧 {campaign_data.get('title', campaign_type.replace('_', ' ').title())}")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ecf0f1;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        contacts_label = QLabel(f"📊 {campaign_data.get('target_contacts', 0)} recipients")
        contacts_label.setStyleSheet("color: #bdc3c7; font-weight: bold;")
        header_layout.addWidget(contacts_label)
        
        layout.addLayout(header_layout)
        
        # Subject line selector
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("📝 Subject Line:"))
        
        subject_combo = QComboBox()
        subject_combo.setStyleSheet("""
            QComboBox {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        subject_lines = campaign_data.get('subject_lines', ['No subject available'])
        subject_combo.addItems(subject_lines)
        subject_layout.addWidget(subject_combo)
        
        layout.addLayout(subject_layout)
        
        # Email content preview with HTML rendering
        content_label = QLabel("📧 Email Content Preview:")
        content_label.setStyleSheet("font-weight: bold; margin-top: 15px; color: #ecf0f1;")
        layout.addWidget(content_label)
        
        # Create scrollable area for email content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #34495e;
                border-radius: 8px;
                background: #ffffff;
            }
        """)
        
        # Email content widget with HTML support
        email_widget = QWidget()
        email_layout = QVBoxLayout(email_widget)
        
        # Sample email with personalization
        sample_contact = campaign_data.get('contacts', [{}])[0] if campaign_data.get('contacts') else {}
        
        # Extract name from various possible fields
        sample_name = (sample_contact.get('first_name') or 
                      sample_contact.get('owner_name') or 
                      sample_contact.get('name') or 
                      'John Doe')
        
        # If owner_name contains full name, extract first name
        if sample_name and ' ' in sample_name:
            sample_name = sample_name.split(' ')[0]
        
        sample_address = (sample_contact.get('address') or 
                         sample_contact.get('street') or 
                         '123 Main St, Anytown, CA 90210')
        
        email_body = campaign_data.get('email_body', 'No content available')
        
        # Safely format the email body
        try:
            personalized_email = email_body.format(name=sample_name, address=sample_address)
        except KeyError as e:
            print(f"[AI Widget] Email formatting error: {e}")
            personalized_email = email_body.replace('{name}', sample_name).replace('{address}', sample_address)
        
        # Use QTextBrowser for HTML support (displays images and links)
        from PySide6.QtWidgets import QTextBrowser
        email_content = QTextBrowser()
        email_content.setReadOnly(True)
        
        # Convert plain text email to HTML format for better display
        html_email = self.convert_email_to_html(personalized_email)
        email_content.setHtml(html_email)
        
        email_content.setStyleSheet("""
            QTextBrowser {
                background: #ffffff;
                color: #212529;
                border: none;
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                padding: 20px;
                line-height: 1.5;
            }
        """)
        email_content.setMinimumHeight(400)
        email_content.setOpenExternalLinks(True)  # Make links clickable
        
        email_layout.addWidget(email_content)
        scroll_area.setWidget(email_widget)
        layout.addWidget(scroll_area)
        
        # Sample data note
        sample_note = QLabel("💡 Preview shows sample data. Actual emails will be personalized for each recipient.")
        sample_note.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 11px; margin-top: 10px;")
        sample_note.setWordWrap(True)
        layout.addWidget(sample_note)
        
        # Campaign details
        details_label = QLabel(f"""
🎯 Target Audience: {campaign_data.get('target_audience', 'N/A')}
🏢 Company: {campaign_data.get('company_name', 'N/A')}
📈 Predicted Open Rate: {campaign_data.get('predicted_open_rate', 0) * 100:.1f}%
🖱️ Predicted Click Rate: {campaign_data.get('predicted_click_rate', 0) * 100:.1f}%
🎯 Call to Action: {campaign_data.get('call_to_action', 'N/A')}
""")
        details_label.setStyleSheet("color: #ecf0f1; font-size: 12px; margin: 10px 0; background: #34495e; padding: 10px; border-radius: 4px;")
        layout.addWidget(details_label)
        
        # Send date scheduler
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("📅 Schedule Send Date:"))
        
        from PySide6.QtWidgets import QDateTimeEdit
        from PySide6.QtCore import QDateTime
        
        date_picker = QDateTimeEdit()
        date_picker.setDateTime(QDateTime.currentDateTime())
        date_picker.setStyleSheet("""
            QDateTimeEdit {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        date_layout.addWidget(date_picker)
        
        # Store date picker for later access
        setattr(dialog, f'date_picker_{campaign_type}', date_picker)
        
        layout.addLayout(date_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        approve_btn = QPushButton("✅ Approve This Campaign")
        approve_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #218838; }
        """)
        approve_btn.clicked.connect(lambda: [self.approve_campaign(campaign_type), dialog.accept()])
        button_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌ Reject This Campaign")
        reject_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        reject_btn.clicked.connect(lambda: [self.reject_campaign(campaign_type), dialog.accept()])
        button_layout.addWidget(reject_btn)
        
        close_btn = QPushButton("📋 Back to Review")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Update email content when subject line changes
        def update_email_content():
            selected_subject = subject_combo.currentText()
            # Could add logic here to modify email content based on subject
            pass
        
        subject_combo.currentTextChanged.connect(update_email_content)
        
        dialog.exec()
    
    def clear_campaign_list(self):
        """Clear the campaign list view"""
        # Remove all campaign cards except the instructions
        for i in reversed(range(1, self.campaign_list_layout.count())):
            child = self.campaign_list_layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
    
    def add_campaign_card(self, campaign_type, campaign_data):
        """Add a campaign card to the list view"""
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
        
        # Create campaign card with improved styling
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #34495e;
                border: 2px solid #5d6d7e;
                border-radius: 12px;
                margin: 8px;
                padding: 15px;
                min-height: 120px;
            }
            QFrame:hover {
                border-color: #3498db;
                background: #3c566e;
                border: 0 4px 8px rgba(0,0,0,0.2);
            }
        """)
        card.setFixedHeight(140)
        
        card_layout = QHBoxLayout(card)
        
        # Campaign info section
        info_layout = QVBoxLayout()
        
        # Title and icon
        title_layout = QHBoxLayout()
        icon_label = QLabel(campaign_data.get('icon', '📧'))
        icon_label.setStyleSheet("font-size: 20px;")
        title_layout.addWidget(icon_label)
        
        # Truncate long titles and add proper text wrapping
        full_title = campaign_data.get('title', campaign_type.replace('_', ' ').title())
        if len(full_title) > 50:
            display_title = full_title[:47] + "..."
        else:
            display_title = full_title
            
        title_label = QLabel(display_title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
                max-width: 400px;
            }
        """)
        title_label.setWordWrap(True)
        title_label.setToolTip(full_title)  # Show full title on hover
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        info_layout.addLayout(title_layout)
        
        # Campaign details
        details_text = f"🎯 {campaign_data.get('target_audience', 'N/A')} • 📊 {campaign_data.get('target_contacts', 0)} contacts"
        details_label = QLabel(details_text)
        details_label.setStyleSheet("color: #bdc3c7; font-size: 12px; margin-top: 5px;")
        info_layout.addWidget(details_label)
        
        # Company info
        company_text = f"🏢 {campaign_data.get('company_name', 'N/A')}"
        company_label = QLabel(company_text)
        company_label.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 2px;")
        info_layout.addWidget(company_label)
        
        # Performance prediction
        open_rate = campaign_data.get('predicted_open_rate', 0) * 100
        click_rate = campaign_data.get('predicted_click_rate', 0) * 100
        perf_text = f"📈 Open: {open_rate:.1f}% • 🖱️ Click: {click_rate:.1f}%"
        perf_label = QLabel(perf_text)
        perf_label.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 3px;")
        info_layout.addWidget(perf_label)
        
        card_layout.addLayout(info_layout)
        
        # Action buttons section
        actions_layout = QVBoxLayout()
        
        # Preview button (main action)
        preview_btn = QPushButton("👁️ Preview Email")
        preview_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        preview_btn.clicked.connect(lambda: self.show_email_preview(campaign_type, campaign_data))
        actions_layout.addWidget(preview_btn)
        
        # Quick action buttons
        quick_actions = QHBoxLayout()
        
        approve_btn = QPushButton("✅")
        approve_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        approve_btn.setToolTip("Approve this campaign")
        approve_btn.clicked.connect(lambda: self.approve_campaign(campaign_type))
        quick_actions.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌")
        reject_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        reject_btn.setToolTip("Reject this campaign")
        reject_btn.clicked.connect(lambda: self.reject_campaign(campaign_type))
        quick_actions.addWidget(reject_btn)
        
        actions_layout.addLayout(quick_actions)
        
        card_layout.addLayout(actions_layout)
        
        # Add card to list
        self.campaign_list_layout.addWidget(card)
    
    def approve_campaign(self, campaign_type):
        """Approve a single campaign"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Campaign Approved", f"✅ {campaign_type.replace('_', ' ').title()} campaign approved!")
    
    def reject_campaign(self, campaign_type):
        """Reject a single campaign"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Campaign Rejected", f"❌ {campaign_type.replace('_', ' ').title()} campaign rejected!")
    
    def load_campaign_content(self, campaign_type):
        """Load campaign content with fallback to defaults"""
        import os
        import json
        
        try:
            # Try to load from current campaigns first
            if hasattr(self, 'current_campaigns') and campaign_type in self.current_campaigns:
                campaign_data = self.current_campaigns[campaign_type]
                if campaign_data.get('email_body') and campaign_data.get('subject_lines'):
                    return campaign_data
            
            # Load from default content file
            if os.path.exists('default_campaign_content.json'):
                with open('default_campaign_content.json', 'r') as f:
                    default_content = json.load(f)
                    if campaign_type in default_content:
                        return default_content[campaign_type]
            
            # Create fallback content
            fallback_content = {
                'title': f'{campaign_type.replace("_", " ").title()} Campaign',
                'target_audience': 'Targeted homeowners',
                'subject_lines': [
                    f'Important Information About Your {campaign_type.replace("_", " ").title()}',
                    f'Exclusive Offer for Your {campaign_type.replace("_", " ").title()}',
                    f'Special {campaign_type.replace("_", " ").title()} Opportunity'
                ],
                'email_body': f"""
Dear {{name}},

We have important information about {campaign_type.replace("_", " ").title()} services available at your address: {{address}}

Contact us today to learn more!

Best regards,
The Team
Seaside Security & Communications
""",
                'call_to_action': 'Contact Us Today',
                'predicted_open_rate': 0.25,
                'predicted_click_rate': 0.05
            }
            
            return fallback_content
            
        except Exception as e:
            print(f"Error loading campaign content: {e}")
            return None

    def modify_campaign(self, campaign_type):
        """Modify a single campaign"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QComboBox, QMessageBox
        
        # Load campaign content with fallback
        campaign_data = self.load_campaign_content(campaign_type)
        
        if not campaign_data:
            QMessageBox.warning(self, "Error", f"Could not load campaign data for {campaign_type}")
            return
        
        # Create modification dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modify Campaign - {campaign_data.get('title', campaign_type)}")
        dialog.setModal(True)
        dialog.resize(800, 700)
        dialog.setStyleSheet("""
            QDialog {
                background: #2c3e50;
                color: #ecf0f1;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header_label = QLabel(f"✏️ Modify {campaign_data.get('title', campaign_type.replace('_', ' ').title())}")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ecf0f1;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(header_label)
        
        # Campaign title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Campaign Title:"))
        title_edit = QLineEdit(campaign_data.get('title', ''))
        title_edit.setStyleSheet("""
            QLineEdit {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        title_layout.addWidget(title_edit)
        layout.addLayout(title_layout)
        
        # Target audience
        audience_layout = QHBoxLayout()
        audience_layout.addWidget(QLabel("Target Audience:"))
        audience_edit = QLineEdit(campaign_data.get('target_audience', ''))
        audience_edit.setStyleSheet("""
            QLineEdit {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        audience_layout.addWidget(audience_edit)
        layout.addLayout(audience_layout)
        
        # Subject lines
        subject_label = QLabel("Subject Lines (one per line):")
        subject_label.setStyleSheet("font-weight: bold; margin-top: 15px; color: #ecf0f1;")
        layout.addWidget(subject_label)
        
        subject_edit = QTextEdit()
        subject_lines = campaign_data.get('subject_lines', [])
        subject_edit.setPlainText('\n'.join(subject_lines))
        subject_edit.setStyleSheet("""
            QTextEdit {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        subject_edit.setMaximumHeight(100)
        layout.addWidget(subject_edit)
        
        # Email body with HTML preview
        body_label = QLabel("Email Body (HTML supported):")
        body_label.setStyleSheet("font-weight: bold; margin-top: 15px; color: #ecf0f1;")
        layout.addWidget(body_label)
        
        # Create tabbed editor for HTML and Preview
        from PySide6.QtWidgets import QTabWidget
        body_tabs = QTabWidget()
        body_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #5d6d7e; background: #34495e; }
            QTabBar::tab { 
                background: #2c3e50; 
                color: #ecf0f1; 
                padding: 8px 16px; 
                margin-right: 2px; 
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected { background: #34495e; }
        """)
        
        # HTML Editor tab
        body_edit = QTextEdit()
        body_edit.setPlainText(campaign_data.get('email_body', ''))
        body_edit.setStyleSheet("""
            QTextEdit {
                background: #34495e;
                color: #ecf0f1;
                border: none;
                padding: 8px;
                font-size: 12px;
                font-family: 'Monaco', 'Consolas', monospace;
            }
        """)
        body_tabs.addTab(body_edit, "📝 Edit HTML")
        
        # Preview tab
        preview_edit = QTextEdit()
        preview_edit.setReadOnly(True)
        preview_edit.setStyleSheet("""
            QTextEdit {
                background: white;
                color: black;
                border: none;
                padding: 8px;
                font-size: 12px;
            }
        """)
        
        def update_preview():
            # Replace template variables with sample data for preview
            preview_content = body_edit.toPlainText()
            preview_content = preview_content.replace('{name}', 'John Smith')
            preview_content = preview_content.replace('{address}', '123 Main St, Wilmington, NC 28401')
            preview_edit.setHtml(preview_content)
        
        # Update preview when text changes
        body_edit.textChanged.connect(update_preview)
        update_preview()  # Initial preview
        
        body_tabs.addTab(preview_edit, "👁️ Preview")
        
        layout.addWidget(body_tabs)
        
        # Call to action
        cta_layout = QHBoxLayout()
        cta_layout.addWidget(QLabel("Call to Action:"))
        cta_edit = QLineEdit(campaign_data.get('call_to_action', ''))
        cta_edit.setStyleSheet("""
            QLineEdit {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #5d6d7e;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        cta_layout.addWidget(cta_edit)
        layout.addLayout(cta_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #218838; }
        """)
        
        def save_changes():
            # Update campaign data
            updated_campaign = {
                'title': title_edit.text(),
                'target_audience': audience_edit.text(),
                'subject_lines': [line.strip() for line in subject_edit.toPlainText().split('\n') if line.strip()],
                'email_body': body_edit.toPlainText(),
                'call_to_action': cta_edit.text()
            }
            
            # Save to current campaigns
            if not hasattr(self, 'current_campaigns'):
                self.current_campaigns = {}
            self.current_campaigns[campaign_type] = updated_campaign
            
            QMessageBox.information(self, "Changes Saved", "Campaign modifications saved successfully!")
            dialog.accept()
        
        save_btn.clicked.connect(save_changes)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def approve_all_campaigns(self):
        """Approve all campaigns and continue automation"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Approve All Campaigns", 
                                   "Are you sure you want to approve all campaigns and continue with automation?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Send approved campaigns to MailChimp
            self.send_campaigns_to_mailchimp()
            
            self.campaign_verified.emit(True)
            self.campaign_status_label.setText("✅ All campaigns approved - sent to MailChimp - automation continuing...")
            self.approve_all_btn.setEnabled(False)
            self.reject_all_btn.setEnabled(False)
            self.regenerate_btn.setEnabled(False)
    
    def send_campaigns_to_mailchimp(self):
        """Send all approved campaigns to MailChimp"""
        if not self.service:
            print("❌ Email service not available")
            return
        
        if not hasattr(self, 'current_campaigns') or not self.current_campaigns:
            print("❌ No campaigns to send")
            return
        
        print(f"📧 Sending {len(self.current_campaigns)} campaigns to MailChimp...")
        
        success_count = 0
        failed_campaigns = []
        
        for campaign_id, campaign_data in self.current_campaigns.items():
            try:
                print(f"📤 Sending campaign: {campaign_data.get('title', 'Unknown')}")
                
                # Debug: Show campaign structure
                print(f"[DEBUG] Campaign keys: {list(campaign_data.keys())}")
                print(f"[DEBUG] Campaign has 'contacts': {'contacts' in campaign_data}")
                print(f"[DEBUG] Campaign has 'recipients': {'recipients' in campaign_data}")
                
                # Check for contacts (the actual field name used in campaign generation)
                contacts = campaign_data.get('contacts', [])
                recipients = campaign_data.get('recipients', [])
                
                print(f"[DEBUG] Contacts count: {len(contacts)}")
                print(f"[DEBUG] Recipients count: {len(recipients)}")
                
                # Use contacts if recipients is empty (fix for the field name mismatch)
                if not recipients and contacts:
                    print(f"[DEBUG] Using 'contacts' field as 'recipients'")
                    campaign_data['recipients'] = contacts
                    recipients = contacts
                
                # Ensure campaign has required data
                if not recipients or len(recipients) == 0:
                    print(f"⚠️ Campaign {campaign_id} has no recipients - skipping")
                    print(f"[DEBUG] Final recipients count: {len(recipients)}")
                    failed_campaigns.append(f"{campaign_data.get('title', 'Unknown')} - No recipients")
                    continue
                
                print(f"[DEBUG] ✅ Campaign has {len(recipients)} recipients, proceeding with send")
                
                # Create MailChimp campaign
                result = self.service.create_mailchimp_campaign(campaign_data)
                
                if result.get('success'):
                    success_count += 1
                    campaign_id = result.get('campaign_id', 'Unknown ID')
                    print(f"✅ Campaign sent successfully: {campaign_id}")
                    
                    # Update campaign status
                    campaign_data['mailchimp_id'] = campaign_id
                    campaign_data['sent_date'] = datetime.now().isoformat()
                    campaign_data['status'] = 'sent'
                    
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ Failed to send campaign: {error_msg}")
                    failed_campaigns.append(f"{campaign_data.get('title', 'Unknown')} - {error_msg}")
                    
            except Exception as e:
                print(f"❌ Error sending campaign {campaign_id}: {e}")
                failed_campaigns.append(f"{campaign_data.get('title', 'Unknown')} - {str(e)}")
        
        print(f"📊 MailChimp Results: {success_count}/{len(self.current_campaigns)} campaigns sent successfully")
        
        # Update status with detailed results
        if success_count > 0:
            status_msg = f"✅ {success_count} campaigns sent to MailChimp successfully!"
            if failed_campaigns:
                status_msg += f" ({len(failed_campaigns)} failed)"
            self.campaign_status_label.setText(status_msg)
            
            # Show detailed results dialog
            self.show_send_results_dialog(success_count, len(self.current_campaigns), failed_campaigns)
        else:
            self.campaign_status_label.setText("⚠️ All campaigns failed to send - check API configuration")
            
            # Show error dialog
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Send Failed", 
                              f"All {len(self.current_campaigns)} campaigns failed to send.\n\n"
                              f"Please check your MailChimp API configuration and try again.")
    
    def show_send_results_dialog(self, success_count, total_count, failed_campaigns):
        """Show detailed results of campaign sending"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📧 Campaign Send Results")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Results summary
        summary = QTextEdit()
        summary.setReadOnly(True)
        summary.setMaximumHeight(100)
        
        summary_text = f"""
📊 CAMPAIGN SEND RESULTS

✅ Successfully Sent: {success_count}/{total_count} campaigns
❌ Failed: {len(failed_campaigns)} campaigns

"""
        
        if failed_campaigns:
            summary_text += "\n❌ FAILED CAMPAIGNS:\n"
            for failed in failed_campaigns:
                summary_text += f"• {failed}\n"
        
        summary.setPlainText(summary_text)
        layout.addWidget(summary)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("✅ OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def reject_all_campaigns(self):
        """Reject all campaigns and stop automation"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Reject All Campaigns", 
                                   "Are you sure you want to reject all campaigns and stop automation?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.campaign_verified.emit(False)
            self.campaign_status_label.setText("❌ All campaigns rejected - automation stopped")
            self.approve_all_btn.setEnabled(False)
            self.reject_all_btn.setEnabled(False)
            self.regenerate_btn.setEnabled(False)
    
    def toggle_auto_approval(self):
        """Toggle auto-approval of AI-generated emails"""
        from PySide6.QtWidgets import QMessageBox
        
        self.auto_approval_enabled = not self.auto_approval_enabled
        
        if self.auto_approval_enabled:
            # Confirm with user
            reply = QMessageBox.question(
                self, 
                "Enable Auto-Approval", 
                "⚠️ WARNING: Auto-approval will automatically approve ALL AI-generated emails without manual review.\n\n"
                "This means emails will be sent immediately without your oversight.\n\n"
                "Are you sure you want to enable this?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.auto_approval_btn.setText("🟢 Auto-Approval: ON")
                self.auto_approval_btn.setStyleSheet("""
                    QPushButton {
                        background: #28a745;
                        color: white;
                        padding: 12px 24px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 200px;
                    }
                    QPushButton:hover { background: #1e7e34; }
                """)
                self.auto_approval_info.setText("✅ Auto-approval ENABLED: AI emails will be automatically approved and sent")
                self.auto_approval_info.setStyleSheet("""
                    QLabel {
                        color: #28a745;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 5px;
                    }
                """)
                
                # Notify parent/main window about auto-approval being enabled
                if hasattr(self.parent(), 'set_auto_approval_enabled'):
                    self.parent().set_auto_approval_enabled(True)
            else:
                # User cancelled, revert the state
                self.auto_approval_enabled = False
                self.auto_approval_btn.setChecked(False)
        else:
            self.auto_approval_btn.setText("🔴 Auto-Approval: OFF")
            self.auto_approval_btn.setStyleSheet("""
                QPushButton {
                    background: #dc3545;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 200px;
                }
                QPushButton:hover { background: #c82333; }
            """)
            self.auto_approval_info.setText("⚠️ When enabled, AI emails will be automatically approved without manual review")
            self.auto_approval_info.setStyleSheet("""
                QLabel {
                    color: #f39c12;
                    font-style: italic;
                    font-size: 12px;
                    padding: 5px;
                }
            """)
            
            # Notify parent/main window about auto-approval being disabled
            if hasattr(self.parent(), 'set_auto_approval_enabled'):
                self.parent().set_auto_approval_enabled(False)

    def regenerate_campaigns(self):
        """Regenerate all campaigns"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Regenerate Campaigns", "🔄 Campaign regeneration not yet implemented!")
    
    def export_analytics(self):
        """Export analytics to file"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Analytics", "mailchimp_analytics.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.analytics_display.toPlainText())
                QMessageBox.information(self, "Export Complete", f"Analytics exported to {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Error exporting analytics: {e}") 

    def check_for_real_incidents(self):
        """DEPRECATED: This method is deprecated. Use the Incident Response tab instead."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Deprecated Feature", 
                              "⚠️ This feature is deprecated!\n\n"
                              "Please use the 'Generate Leads from Incidents' button in the Incident Response tab instead.\n\n"
                              "The new system provides:\n"
                              "• 25-yard radius targeting\n"
                              "• Realistic contact generation\n"
                              "• AI-powered email campaigns\n"
                              "• Better incident response automation")
        print("[AI Widget] DEPRECATED: check_for_real_incidents called - use Incident Response tab instead")

    @Slot(object)
    def handle_incident_campaigns(self, incident_campaigns):
        """Handle incident campaigns from automation widget"""
        try:
            print(f"[AI Widget] Received {len(incident_campaigns)} incident campaigns")
            
            if not incident_campaigns:
                return
            
            # Convert incident campaigns to the standard campaign format
            converted_campaigns = {}
            
            for i, incident_campaign in enumerate(incident_campaigns):
                campaign_id = incident_campaign.get('campaign_id', f'incident_{i}')
                
                # Convert incident campaign to standard format
                converted_campaign = {
                    'campaign_type': incident_campaign.get('campaign_type', 'Incident Response'),
                    'title': incident_campaign.get('title', 'Incident Response Campaign'),
                    'icon': incident_campaign.get('icon', '🚨'),
                    'target_audience': incident_campaign.get('target_audience', 'Nearby residents'),
                    'company_name': incident_campaign.get('company_name', 'Seaside Security'),
                    'subject_lines': incident_campaign.get('subject_lines', []),
                    'email_body': incident_campaign.get('email_body', ''),
                    'call_to_action': incident_campaign.get('call_to_action', 'Contact Us'),
                    'customer_phone': incident_campaign.get('customer_phone', '(910) 597-4085'),
                    'contacts': incident_campaign.get('contacts', []),
                    'target_contacts': incident_campaign.get('target_contacts', 0),
                    'incident_details': incident_campaign.get('incident_details', {}),
                    'automation_source': 'Incident Monitor',
                    'priority': incident_campaign.get('priority', 'High'),
                    'created_at': incident_campaign.get('created_at', datetime.now().isoformat()),
                    'status': 'pending_approval',
                    'predicted_open_rate': 0.35,  # Higher for incident-based emails
                    'predicted_click_rate': 0.15,  # Higher urgency
                    'mailchimp_insights': [
                        f"Incident-based emails have 35% higher open rates",
                        f"Proximity targeting increases conversion by 40%",
                        f"Security incidents create immediate demand"
                    ],
                    'optimization_tips': [
                        "Send within 24 hours of incident for maximum impact",
                        "Use urgent but helpful messaging",
                        "Include specific incident details for credibility"
                    ]
                }
                
                converted_campaigns[campaign_id] = converted_campaign
            
            # Only use incident campaigns - don't mix with old cached campaigns
            self.current_campaigns = converted_campaigns
            
            # Update the display
            self.show_campaigns_for_review(self.current_campaigns)
            
            # Show notification
            QMessageBox.information(self, "Incident Campaigns Generated", 
                                  f"🚨 Generated {len(incident_campaigns)} urgent incident-based email campaigns.\n\n"
                                  f"These high-priority campaigns are waiting for your approval in the Campaign Review tab.\n"
                                  f"Incident-based campaigns typically have 35% higher open rates due to urgency and relevance.")
            
        except Exception as e:
            print(f"[AI Widget] Error handling incident campaigns: {e}")
            import traceback
            traceback.print_exc() 

    def convert_email_to_html(self, email_text):
        """Convert plain text email to HTML with proper formatting and working images"""
        import re
        
        # Start with basic HTML structure
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 600px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .button {
            display: inline-block;
            background-color: #0066cc;
            color: white !important;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        .button:hover {
            background-color: #0052a3;
        }
        a[href*="seasidesecurity.net"] {
            background-color: #cc0000 !important;
        }
        a[href*="seasidesecurity.net"]:hover {
            background-color: #a60000 !important;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 8px;
        }
        .logo {
            max-width: 300px;
            height: auto;
            display: block;
            margin: 20px auto;
        }
        .emoji {
            font-size: 1.2em;
        }
        .highlight {
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #0066cc;
            margin: 15px 0;
        }
    </style>
</head>
<body>
"""
        
        # Convert the email text
        email_html = email_text
        
        # If email already contains HTML, preserve it; otherwise convert line breaks
        if '<img' not in email_html and '<div' not in email_html:
            # Convert line breaks to HTML for plain text emails
            email_html = email_html.replace('\n\n', '</p><p>')
            email_html = email_html.replace('\n', '<br>')
            # Wrap in paragraphs
            email_html = f'<p>{email_html}</p>'
        
        # Convert bullet points for both HTML and text
        email_html = re.sub(r'•\s*([^<\n]*)', r'<li>\1</li>', email_html)
        
        # Wrap consecutive li elements in ul tags
        email_html = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul>\1</ul>', email_html, flags=re.DOTALL)
        
        # Make **bold** text actually bold
        email_html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', email_html)
        
        # Ensure Seaside Security logo images have proper class
        email_html = re.sub(
            r'<img([^>]*?)alt="([^"]*Seaside[^"]*)"([^>]*?)>',
            r'<img\1alt="\2"\3 class="logo">',
            email_html,
            flags=re.IGNORECASE
        )
        
        # Ensure all other images have proper styling if they don't already
        email_html = re.sub(
            r'<img(?![^>]*(?:class=|style=))([^>]*?)>',
            r'<img\1 style="max-width: 500px; height: auto; display: block; margin: 20px auto; border-radius: 8px;">',
            email_html
        )
        
        # Convert button HTML to be properly clickable with better styling
        email_html = re.sub(
            r'<a\s+href="([^"]*)"[^>]*style="[^"]*"[^>]*>([^<]*)</a>',
            r'<a href="\1" class="button" target="_blank">\2</a>',
            email_html
        )
        
        # Handle button divs and preserve center alignment
        button_pattern = r'<div[^>]*center[^>]*>\s*<a\s+href="([^"]*)"[^>]*>([^<]*)</a>\s*</div>'
        email_html = re.sub(button_pattern, r'<div style="text-align: center; margin: 30px 0;"><a href="\1" class="button" target="_blank">\2</a></div>', email_html)
        
        # Make phone numbers clickable
        email_html = re.sub(r'\((\d{3})\)\s*(\d{3})-(\d{4})', r'<a href="tel:\1\2\3">(\1) \2-\3</a>', email_html)
        
        # Close HTML
        html += email_html + """
</body>
</html>
"""
        
        return html 
    
    def generate_incident_campaigns_from_contacts(self, df):
        """Generate realistic incident campaigns using real contact data"""
        try:
            from datetime import datetime
            import random
            
            # Sample realistic incidents for the area
            sample_incidents = [
                {
                    'type': 'fire',
                    'address': '123 Market St, Wilmington, NC',
                    'city': 'Wilmington',
                    'details': 'Kitchen fire with smoke damage to adjacent properties'
                },
                {
                    'type': 'burglary',
                    'address': '456 Princess St, Wilmington, NC', 
                    'city': 'Wilmington',
                    'details': 'Break-in through rear door, electronics stolen'
                },
                {
                    'type': 'fire',
                    'address': '789 Village Rd, Leland, NC',
                    'city': 'Leland',
                    'details': 'Electrical fire in garage, smoke damage'
                }
            ]
            
            campaigns = []
            
            for incident in sample_incidents:
                # Get contacts from the same city as the incident
                # Check if 'city' column exists in the DataFrame
                if 'city' not in df.columns:
                    print(f"[AI Widget] Warning: DataFrame does not have 'city' column. Available columns: {list(df.columns)}")
                    continue
                
                city_contacts = df[df['city'].str.contains(incident['city'], case=False, na=False)]
                
                if len(city_contacts) == 0:
                    continue
                
                # Use a subset of contacts as "nearby residents"
                # In reality, this would be based on geographic proximity
                nearby_count = min(len(city_contacts), random.randint(15, 35))
                nearby_contacts = city_contacts.sample(n=nearby_count).to_dict('records')
                
                # Generate campaign based on incident type
                if incident['type'] == 'fire':
                    campaign = {
                        'campaign_id': f"incident_fire_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'campaign_type': 'Fire Safety Response',
                        'title': '🔥 Fire Safety Alert - Smoke Monitoring Available',
                        'icon': '🔥',
                        'target_audience': f"Residents near {incident['address']}",
                        'company_name': 'Seaside Security',
                        'subject_lines': [
                            f"Fire Safety Alert: Incident Near Your Address",
                            f"Protect Your Family - Fire Occurred at {incident['address']}",
                            f"Free Fire Safety Consultation After Nearby Fire"
                        ],
                        'email_body': f"""
Dear {{name}},

🚨 **FIRE SAFETY ALERT FOR YOUR NEIGHBORHOOD**

We want to inform you about a recent fire incident that occurred at {incident['address']} on {datetime.now().strftime('%B %d, %Y')}.

**Incident Details:**
📍 Location: {incident['address']}
🔥 Type: {incident['details']}
⚠️ Impact: Smoke damage to surrounding area

**FREE FIRE SAFETY CONSULTATION**
Given this recent incident in your neighborhood, we're offering FREE fire safety consultations to ensure your family is protected.

🔔 **Our Fire Safety Services:**
• Advanced smoke detection systems
• 24/7 fire monitoring
• Emergency response coordination
• Carbon monoxide detection

📞 **Emergency Contact**: (910) 742-0609
👉 **Free Consultation**: https://seasidesecurity.net/fire-safety

Stay safe,
Seaside Security Team
""",
                        'call_to_action': 'Get Free Fire Safety Consultation',
                        'customer_phone': '(910) 742-0609',
                        'contacts': nearby_contacts,
                        'target_contacts': len(nearby_contacts),
                        'incident_details': incident,
                        'created_at': datetime.now().isoformat(),
                        'status': 'pending_review',
                        'priority': 'High'
                    }
                
                elif incident['type'] == 'burglary':
                    campaign = {
                        'campaign_id': f"incident_burglary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'campaign_type': 'Security Alert Response',
                        'title': '🏠 Security Alert - Break-in Protection Available',
                        'icon': '🏠',
                        'target_audience': f"Residents near {incident['address']}",
                        'company_name': 'Seaside Security',
                        'subject_lines': [
                            f"Security Alert: Break-in Near Your Address",
                            f"Protect Your Home - Incident at {incident['address']}",
                            f"Free Security Assessment After Nearby Break-in"
                        ],
                        'email_body': f"""
Dear {{name}},

🚨 **SECURITY ALERT FOR YOUR NEIGHBORHOOD**

We want to inform you about a recent break-in that occurred at {incident['address']} on {datetime.now().strftime('%B %d, %Y')}.

**Incident Details:**
📍 Location: {incident['address']}
🏠 Type: {incident['details']}
⚠️ Impact: Security concern for neighborhood

**FREE SECURITY ASSESSMENT**
Given this recent incident in your neighborhood, we're offering FREE security assessments to help protect your home and family.

🔒 **Our Security Services:**
• Advanced alarm systems
• 24/7 security monitoring
• Door/window sensors
• Motion detection cameras

📞 **Emergency Contact**: (910) 742-0609
👉 **Free Assessment**: https://seasidesecurity.net/security-assessment

Stay secure,
Seaside Security Team
""",
                        'call_to_action': 'Get Free Security Assessment',
                        'customer_phone': '(910) 742-0609',
                        'contacts': nearby_contacts,
                        'target_contacts': len(nearby_contacts),
                        'incident_details': incident,
                        'created_at': datetime.now().isoformat(),
                        'status': 'pending_review',
                        'priority': 'High'
                    }
                
                if 'campaign' in locals():
                    campaigns.append(campaign)
                    print(f"[AI Widget] Generated {incident['type']} campaign with {len(nearby_contacts)} contacts")
                    del campaign  # Clear for next iteration
            
            return campaigns
            
        except Exception as e:
            print(f"[AI Widget] Error generating incident campaigns: {e}")
            import traceback
            traceback.print_exc()
            return []

    def is_auto_approval_enabled(self):
        return self.auto_approval_enabled
    
    def select_existing_leads(self):
        """Select existing leads with optimized memory usage"""
        try:
            print("[AI Widget] Selecting existing leads...")
            self.campaign_status_label.setText("🔍 Loading existing leads...")
            
            # Use threading to prevent UI freeze
            from PySide6.QtCore import QThread, Signal
            
            class LeadSelectorThread(QThread):
                leads_ready = Signal(list)
                error_occurred = Signal(str)
                
                def __init__(self, parent_widget):
                    super().__init__()
                    self.parent_widget = parent_widget
                
                def run(self):
                    try:
                        import gc  # Garbage collector for memory management
                        
                        # Get pending contacts from ContactManager
                        from utils.contact_manager import ContactManager
                        contact_manager = ContactManager()
                        pending_contacts = contact_manager.get_pending_contacts()
                        print(f"[AI Widget] Found {len(pending_contacts)} pending contacts from ContactManager")
                        
                        # Process contacts in chunks to reduce memory usage
                        chunk_size = 50
                        all_contacts = []
                        
                        for i in range(0, len(pending_contacts), chunk_size):
                            chunk = pending_contacts[i:i + chunk_size]
                            processed_chunk = self.process_contact_chunk(chunk)
                            all_contacts.extend(processed_chunk)
                            
                            # Force garbage collection after each chunk
                            gc.collect()
                        
                        # Load AT&T fiber data efficiently
                        att_fiber_data = self.load_att_fiber_data()
                        
                        # Update fiber availability
                        updated_contacts = self.update_fiber_availability(all_contacts, att_fiber_data)
                        
                        # Deduplicate contacts efficiently
                        unique_contacts = self.deduplicate_contacts(updated_contacts)
                        
                        # Final garbage collection
                        gc.collect()
                        
                        self.leads_ready.emit(unique_contacts)
                        
                    except Exception as e:
                        print(f"[AI Widget] Error in lead selector thread: {e}")
                        import traceback
                        traceback.print_exc()
                        self.error_occurred.emit(str(e))
                    finally:
                        # Clean up resources
                        cleanup_multiprocessing()
                
                def process_contact_chunk(self, contacts):
                    """Process a chunk of contacts efficiently"""
                    processed = []
                    for contact in contacts:
                        # Basic validation
                        if contact.get('owner_name') and contact.get('batchdata_status') in ['completed', 'success']:
                            processed.append(contact)
                    return processed
                
                def load_att_fiber_data(self):
                    """Load AT&T fiber data efficiently"""
                    att_fiber_data = {}
                    att_fiber_patterns = ['att_fiber_results_*.csv', 'att_fiber_master.csv']
                    
                    for pattern in att_fiber_patterns:
                        import glob
                        csv_files = glob.glob(pattern)
                        for csv_file in csv_files:
                            try:
                                import pandas as pd
                                df = pd.read_csv(csv_file)
                                for _, row in df.iterrows():
                                    address = row.get('address', '')
                                    fiber_available = row.get('fiber_available', False)
                                    if address:
                                        att_fiber_data[address] = fiber_available
                            except Exception as e:
                                print(f"[AI Widget] Error reading AT&T fiber file {csv_file}: {e}")
                    
                    return att_fiber_data
                
                def update_fiber_availability(self, contacts, att_fiber_data):
                    """Update fiber availability for contacts"""
                    updated = []
                    for contact in contacts:
                        address = contact.get('address', '')
                        if address in att_fiber_data and contact.get('fiber_available') is None:
                            contact['fiber_available'] = att_fiber_data[address]
                        updated.append(contact)
                    return updated
                
                def deduplicate_contacts(self, contacts):
                    """Deduplicate contacts efficiently"""
                    unique_contacts = []
                    seen_emails = {}
                    seen_addresses = {}
                    
                    for contact in contacts:
                        email = contact.get('owner_email', '')
                        address = contact.get('address', '')
                        owner_name = contact.get('owner_name', '')
                        
                        # Convert email to string and handle NaN values
                        if email is None or (hasattr(email, 'isna') and email.isna()) or str(email).lower() == 'nan':
                            email = ''
                        else:
                            email = str(email).strip()
                        
                        # Convert owner_name to string and handle NaN values
                        if owner_name is None or (hasattr(owner_name, 'isna') and owner_name.isna()) or str(owner_name).lower() == 'nan':
                            owner_name = ''
                        else:
                            owner_name = str(owner_name).strip()
                        
                        # Defensive type check and debug print
                        if not isinstance(email, str):
                            print(f"[AI Widget] Defensive: email is not str, got {type(email)}: {email}")
                            email = '' if email is None else str(email)
                        if not isinstance(owner_name, str):
                            print(f"[AI Widget] Defensive: owner_name is not str, got {type(owner_name)}: {owner_name}")
                            owner_name = '' if owner_name is None else str(owner_name)
                        
                        # Skip test contacts
                        skip_test_contact = False
                        try:
                            if email == 'test@example.com' or 'test@' in email.lower():
                                skip_test_contact = True
                        except Exception as e:
                            print(f"[AI Widget] Exception in email test: {e} (email: {email}, type: {type(email)})")
                        try:
                            if 'Test' in owner_name or 'test' in owner_name.lower():
                                skip_test_contact = True
                        except Exception as e:
                            print(f"[AI Widget] Exception in owner_name test: {e} (owner_name: {owner_name}, type: {type(owner_name)})")
                        
                        if skip_test_contact:
                            continue
                        
                        # Deduplicate by email
                        if email:
                            if email not in seen_emails:
                                unique_contacts.append(contact)
                                seen_emails[email] = contact
                            else:
                                # Prefer contact with fiber_available not None
                                existing = seen_emails[email]
                                existing_fiber = existing.get('fiber_available')
                                new_fiber = contact.get('fiber_available')
                                
                                if existing_fiber is None and new_fiber is not None:
                                    idx = unique_contacts.index(existing)
                                    unique_contacts[idx] = contact
                                    seen_emails[email] = contact
                        # Deduplicate by address for contacts without emails
                        elif address and owner_name:
                            if address not in seen_addresses:
                                unique_contacts.append(contact)
                                seen_addresses[address] = contact
                            else:
                                existing = seen_addresses[address]
                                existing_fiber = existing.get('fiber_available')
                                new_fiber = contact.get('fiber_available')
                                
                                if existing_fiber is None and new_fiber is not None:
                                    idx = unique_contacts.index(existing)
                                    unique_contacts[idx] = contact
                                    seen_addresses[address] = contact
                    
                    return unique_contacts
            
            # Create and start the thread
            self.lead_selector_thread = LeadSelectorThread(self)
            self.lead_selector_thread.leads_ready.connect(self.handle_leads_loaded)
            self.lead_selector_thread.error_occurred.connect(self.handle_lead_error)
            self.worker_threads.append(self.lead_selector_thread)  # Track for cleanup
            self.lead_selector_thread.start()
            
        except Exception as e:
            print(f"[AI Widget] Error setting up lead selection: {e}")
            import traceback
            traceback.print_exc()
            self.campaign_status_label.setText(f"❌ Error setting up lead selection: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error setting up lead selection: {str(e)}")
    
    def handle_leads_loaded(self, contacts):
        """Handle leads loaded in background thread"""
        try:
            self.selected_contacts = contacts
            
            # Count contacts by type
            fiber_contacts = [c for c in contacts if c.get('fiber_available') == True]
            non_fiber_contacts = [c for c in contacts if c.get('fiber_available') == False]
            unknown_contacts = [c for c in contacts if c.get('fiber_available') is None]
            
            print(f"[AI Widget] ✅ Loaded {len(contacts)} contacts")
            print(f"[AI Widget] Fiber breakdown: {len(fiber_contacts)} fiber, {len(non_fiber_contacts)} non-fiber, {len(unknown_contacts)} unknown")
            
            # Update UI
            self.campaign_status_label.setText(f"✅ Loaded {len(contacts)} contacts ({len(fiber_contacts)} fiber, {len(non_fiber_contacts)} non-fiber)")
            
            # Enable the generate campaigns button
            self.generate_from_leads_btn.setEnabled(True)
            
            # Show success message
            QMessageBox.information(self, "Leads Loaded", 
                f"Successfully loaded {len(contacts)} contacts:\n"
                f"• {len(fiber_contacts)} AT&T Fiber leads\n"
                f"• {len(non_fiber_contacts)} non-fiber leads\n"
                f"• {len(unknown_contacts)} unknown status\n\n"
                f"You can now generate campaigns from these leads.")
            
        except Exception as e:
            print(f"[AI Widget] Error handling loaded leads: {e}")
            self.campaign_status_label.setText(f"❌ Error handling leads: {str(e)}")
    
    def handle_lead_error(self, error_message):
        """Handle lead loading error"""
        self.campaign_status_label.setText("❌ Error loading leads")
        QMessageBox.warning(self, "Error Loading Leads", 
            f"Failed to load leads:\n{error_message}")
        print(f"[AI Widget] ❌ Lead loading error: {error_message}")
    
    def manage_audience_lists(self):
        """Manage MailChimp audience lists - delete old ones to stay under limit"""
        try:
            # Initialize the service
            service = self._ensure_service_initialized()
            
            # Get current list statistics
            stats = service.get_list_statistics()
            
            if "error" in stats:
                QMessageBox.warning(self, "Error", f"Failed to get list statistics:\n{stats['error']}")
                return
            
            # Show current status
            current_count = stats.get('total_lists', 0)
            total_subscribers = stats.get('total_subscribers', 0)
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 Manage Audience Lists")
            dialog.setModal(True)
            dialog.setMinimumWidth(600)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QPushButton {
                    background: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
                QPushButton.danger {
                    background: #e74c3c;
                }
                QPushButton.danger:hover {
                    background: #c0392b;
                }
                QTextEdit {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #5d6d7e;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            
            # Status info
            status_label = QLabel(f"📊 Current Status:\n• {current_count} audience lists\n• {total_subscribers:,} total subscribers\n• MailChimp limit: 6 active lists")
            status_label.setStyleSheet("font-size: 14px; padding: 10px; background: #34495e; border-radius: 4px;")
            layout.addWidget(status_label)
            
            # List details with deletion eligibility
            if stats.get('lists'):
                lists_text = QTextEdit()
                lists_text.setMaximumHeight(300)  # Increased height for more info
                lists_text.setReadOnly(True)
                
                lists_content = "📋 Current Lists:\n\n"
                for list_info in stats['lists']:
                    name = list_info.get('name', 'Unknown')
                    count = list_info.get('member_count', 0)
                    created = list_info.get('created_date', 'Unknown')
                    last_campaign = list_info.get('last_campaign_date', 'No campaigns')
                    deletion_eligible = list_info.get('deletion_eligible', True)
                    days_until_deletable = list_info.get('days_until_deletable', 0)
                    deletion_date = list_info.get('deletion_date')
                    
                    # Format creation date
                    try:
                        from datetime import datetime
                        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        created_formatted = created_dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        created_formatted = created
                    
                    # Deletion status indicator
                    if deletion_eligible:
                        deletion_status = "✅ Deletable"
                        deletion_color = "#27ae60"
                    else:
                        if days_until_deletable == 1:
                            deletion_status = f"⏰ Deletable in 1 day"
                        else:
                            deletion_status = f"⏰ Deletable in {days_until_deletable} days"
                        deletion_color = "#f39c12"
                    
                    lists_content += f"• {name}\n"
                    lists_content += f"  - {count:,} subscribers\n"
                    lists_content += f"  - Created: {created_formatted}\n"
                    lists_content += f"  - Last Campaign: {last_campaign}\n"
                    lists_content += f"  - Status: {deletion_status}\n"
                    
                    if not deletion_eligible and deletion_date:
                        lists_content += f"  - Deletion Date: {deletion_date}\n"
                    
                    # Add individual delete button for each list
                    if deletion_eligible:
                        lists_content += f"  - [DELETE] Click 'Delete Individual List' below\n"
                    else:
                        lists_content += f"  - [LOCKED] Cannot delete due to recent campaigns\n"
                    
                    lists_content += "\n"
                
                lists_text.setText(lists_content)
                layout.addWidget(lists_text)
            
            # Action buttons
            button_layout = QHBoxLayout()
            
            # Count deletable lists
            deletable_lists = [lst for lst in stats.get('lists', []) if lst.get('deletion_eligible', True)]
            non_deletable_lists = [lst for lst in stats.get('lists', []) if not lst.get('deletion_eligible', True)]
            
            if current_count > 6:
                if len(deletable_lists) > 0:
                    # Need to delete some lists and have deletable ones
                    delete_btn = QPushButton(f"🗑️ Delete Old Lists (Keep 6) - {len(deletable_lists)} deletable")
                    delete_btn.setProperty("class", "danger")
                    delete_btn.clicked.connect(lambda: self.delete_old_lists(dialog))
                    button_layout.addWidget(delete_btn)
                    
                    info_text = f"⚠️ You have {current_count} lists (over the 6 limit). {len(deletable_lists)} can be deleted now."
                    if len(non_deletable_lists) > 0:
                        info_text += f" {len(non_deletable_lists)} are locked due to recent campaigns."
                    info_label = QLabel(info_text)
                    info_label.setStyleSheet("color: #f39c12; font-style: italic;")
                    layout.addWidget(info_label)
                else:
                    # Over limit but no deletable lists
                    info_label = QLabel(f"⚠️ You have {current_count} lists (over the 6 limit) but none can be deleted yet due to recent campaigns.")
                    info_label.setStyleSheet("color: #e74c3c; font-style: italic;")
                    layout.addWidget(info_label)
            else:
                # Under limit
                info_label = QLabel(f"✅ You're under the limit ({current_count}/6 lists). No action needed.")
                info_label.setStyleSheet("color: #27ae60; font-style: italic;")
                layout.addWidget(info_label)
            
            # Add individual list deletion button - show for all lists, but indicate which are deletable
            if len(stats.get('lists', [])) > 0:
                delete_individual_btn = QPushButton("🗑️ Delete Individual List")
                delete_individual_btn.setProperty("class", "danger")
                delete_individual_btn.clicked.connect(lambda: self.delete_individual_list(dialog, stats.get('lists', [])))
                button_layout.addWidget(delete_individual_btn)
            
            # Add clean unsubscribed contacts button
            clean_btn = QPushButton("🧹 Clean Unsubscribed Contacts")
            clean_btn.setProperty("class", "danger")
            clean_btn.clicked.connect(lambda: self.clean_unsubscribed_contacts(dialog))
            button_layout.addWidget(clean_btn)
            
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self.refresh_list_stats(dialog))
            button_layout.addWidget(refresh_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error managing audience lists:\n{str(e)}")
            print(f"[AI Widget] Error managing audience lists: {e}")
    
    def delete_old_lists(self, dialog):
        """Delete old audience lists"""
        try:
            # Get current lists to show what will be deleted
            service = self._ensure_service_initialized()
            stats = service.get_list_statistics()
            
            if not stats.get('lists'):
                QMessageBox.warning(self, "No Lists", "No lists found to delete.")
                return
            
            # Filter only deletable lists
            deletable_lists = [lst for lst in stats.get('lists', []) if lst.get('deletion_eligible', True)]
            
            if not deletable_lists:
                QMessageBox.warning(self, "No Deletable Lists", "No lists can be deleted at this time due to recent campaigns.")
                return
            
            # Sort by creation date (oldest first)
            deletable_lists.sort(key=lambda x: x.get('created_date', ''))
            
            # Show what will be deleted
            lists_to_delete = deletable_lists[:len(deletable_lists) - 6] if len(deletable_lists) > 6 else []
            
            if not lists_to_delete:
                QMessageBox.information(self, "No Action Needed", "No lists need to be deleted to stay under the limit.")
                return
            
            deletion_text = "The following lists will be deleted:\n\n"
            for lst in lists_to_delete:
                deletion_text += f"• {lst.get('name', 'Unknown')} ({lst.get('member_count', 0)} subscribers)\n"
            
            deletion_text += f"\nThis will keep you under the 6-list limit.\n\nThis action cannot be undone. Continue?"
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 
                "Confirm Deletion", 
                deletion_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Show progress
            self.campaign_status_label.setText("🗑️ Deleting old audience lists...")
            
            # Delete old lists
            result = service.delete_old_audience_lists(keep_count=6)
            
            if result.get("success"):
                deleted_count = result.get("deleted_count", 0)
                remaining = result.get("remaining_lists", 0)
                
                # Show success message
                message = f"✅ Successfully deleted {deleted_count} old lists.\n\nRemaining lists: {remaining}/6"
                
                if result.get("deleted_lists"):
                    message += "\n\nDeleted lists:\n"
                    for list_info in result["deleted_lists"]:
                        message += f"• {list_info['name']}\n"
                
                QMessageBox.information(self, "Success", message)
                self.campaign_status_label.setText(f"✅ Deleted {deleted_count} old audience lists")
                
                # Close and reopen dialog to refresh
                dialog.accept()
                self.manage_audience_lists()
            else:
                error_msg = result.get("error", "Unknown error")
                QMessageBox.warning(self, "Error", f"Failed to delete lists:\n{error_msg}")
                self.campaign_status_label.setText("❌ Error deleting audience lists")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting old lists:\n{str(e)}")
            self.campaign_status_label.setText("❌ Error deleting audience lists")
    
    def refresh_list_stats(self, dialog):
        """Refresh list statistics in the dialog"""
        try:
            service = self._ensure_service_initialized()
            stats = service.get_list_statistics()
            if "error" not in stats:
                # Close and reopen dialog to refresh
                dialog.accept()
                self.manage_audience_lists()
            else:
                QMessageBox.warning(self, "Error", f"Failed to refresh statistics:\n{stats['error']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error refreshing statistics:\n{str(e)}")
    
    def delete_individual_list(self, dialog, lists):
        """Delete a specific audience list"""
        try:
            # Show all lists, but indicate which are deletable
            if not lists:
                QMessageBox.warning(self, "No Lists", "No lists found to manage.")
                return
            
            # Create list selection dialog
            selection_dialog = QDialog(self)
            selection_dialog.setWindowTitle("🗑️ Select List to Delete")
            selection_dialog.setModal(True)
            selection_dialog.setMinimumWidth(500)
            selection_dialog.setStyleSheet("""
                QDialog {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QPushButton {
                    background: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
                QPushButton.danger {
                    background: #e74c3c;
                }
                QPushButton.danger:hover {
                    background: #c0392b;
                }
                QListWidget {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #5d6d7e;
                    border-radius: 4px;
                    padding: 8px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #5d6d7e;
                }
                QListWidget::item:selected {
                    background-color: #3498db;
                }
            """)
            
            layout = QVBoxLayout(selection_dialog)
            
            # Instructions
            instructions = QLabel("Select a list to delete:")
            instructions.setStyleSheet("font-size: 14px; padding: 10px;")
            layout.addWidget(instructions)
            
            # Color coding explanation
            color_info = QLabel("💡 Color coding: Blue = Deletable, Gray = Locked (7-day rule)")
            color_info.setStyleSheet("font-size: 12px; padding: 5px; color: #95a5a6; font-style: italic;")
            layout.addWidget(color_info)
            
            # List widget
            list_widget = QListWidget()
            for lst in lists:
                name = lst.get('name', 'Unknown')
                count = lst.get('member_count', 0)
                created = lst.get('created_date', 'Unknown')
                deletion_eligible = lst.get('deletion_eligible', True)
                days_until_deletable = lst.get('days_until_deletable', 0)
                
                # Format creation date
                try:
                    from datetime import datetime
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created_formatted = created_dt.strftime('%Y-%m-%d')
                except:
                    created_formatted = created
                
                # Add deletion status to item text
                if deletion_eligible:
                    status_text = "✅ DELETABLE"
                    item_text = f"{name} ({count:,} subscribers, created {created_formatted}) - {status_text}"
                else:
                    if days_until_deletable == 1:
                        status_text = f"⏰ LOCKED - Deletable in 1 day"
                    else:
                        status_text = f"⏰ LOCKED - Deletable in {days_until_deletable} days"
                    item_text = f"{name} ({count:,} subscribers, created {created_formatted}) - {status_text}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, lst)  # Store the list data
                
                # Set item color based on deletion eligibility
                if deletion_eligible:
                    item.setBackground(QColor(52, 152, 219))  # Blue for deletable
                    item.setForeground(QColor(255, 255, 255))  # White text
                else:
                    item.setBackground(QColor(155, 155, 155))  # Gray for locked
                    item.setForeground(QColor(255, 255, 255))  # White text
                
                list_widget.addItem(item)
            
            layout.addWidget(list_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            delete_btn = QPushButton("🗑️ Delete Selected")
            delete_btn.setProperty("class", "danger")
            delete_btn.clicked.connect(lambda: self.confirm_delete_individual_list(selection_dialog, list_widget))
            button_layout.addWidget(delete_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(selection_dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            if selection_dialog.exec_() == QDialog.Accepted:
                # Refresh the main dialog
                dialog.accept()
                self.manage_audience_lists()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting up list deletion:\n{str(e)}")
    
    def confirm_delete_individual_list(self, selection_dialog, list_widget):
        """Confirm deletion of selected list"""
        try:
            current_item = list_widget.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a list to delete.")
                return
            
            list_data = current_item.data(Qt.UserRole)
            list_name = list_data.get('name', 'Unknown')
            list_count = list_data.get('member_count', 0)
            list_id = list_data.get('id')
            deletion_eligible = list_data.get('deletion_eligible', True)
            days_until_deletable = list_data.get('days_until_deletable', 0)
            
            if not list_id:
                QMessageBox.warning(self, "Error", "Could not get list ID for deletion.")
                return
            
            # Check if list can be deleted
            if not deletion_eligible:
                if days_until_deletable == 1:
                    QMessageBox.warning(
                        self, 
                        "List Locked", 
                        f"This list cannot be deleted yet.\n\n"
                        f"• {list_name}\n"
                        f"• {list_count:,} subscribers\n\n"
                        f"⏰ This list will be deletable in 1 day due to recent campaigns.\n\n"
                        f"MailChimp requires a 7-day waiting period after sending campaigns."
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "List Locked", 
                        f"This list cannot be deleted yet.\n\n"
                        f"• {list_name}\n"
                        f"• {list_count:,} subscribers\n\n"
                        f"⏰ This list will be deletable in {days_until_deletable} days due to recent campaigns.\n\n"
                        f"MailChimp requires a 7-day waiting period after sending campaigns."
                    )
                return
            
            # Show confirmation for deletable lists
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the list:\n\n"
                f"• {list_name}\n"
                f"• {list_count:,} subscribers\n\n"
                f"This action cannot be undone. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Delete the list
            service = self._ensure_service_initialized()
            result = service.delete_audience_list(list_id)
            
            if result.get('success'):
                QMessageBox.information(
                    self,
                    "Success",
                    f"✅ Successfully deleted list: {list_name}\n\n"
                    f"📊 Deleted {list_count:,} subscribers"
                )
                selection_dialog.accept()
            else:
                error_msg = result.get('error', 'Unknown error')
                QMessageBox.warning(self, "Error", f"Failed to delete list:\n{error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting list:\n{str(e)}")
    
    def clean_unsubscribed_contacts(self, dialog):
        """Clean unsubscribed contacts to prevent bounce issues"""
        try:
            service = self._ensure_service_initialized()
            if not service:
                return
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                dialog, 
                "Clean Unsubscribed Contacts", 
                "This will remove unsubscribed and cleaned contacts from your lists to prevent bounce issues.\n\nThis action cannot be undone. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Clean the contacts
            result = service.clean_unsubscribed_contacts()
            
            if result.get('success'):
                QMessageBox.information(
                    dialog,
                    "Success",
                    f"✅ {result['message']}\n\n"
                    f"📊 Results:\n"
                    f"• Unsubscribed found: {result.get('unsubscribed_found', 0)}\n"
                    f"• Cleaned found: {result.get('cleaned_found', 0)}\n"
                    f"• Archived: {result.get('archived_count', 0)}"
                )
                
                # Refresh the stats
                self.refresh_list_stats(dialog)
            else:
                QMessageBox.warning(dialog, "Warning", f"Could not clean contacts: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error cleaning contacts:\n{str(e)}")
            print(f"[AI Widget] Error cleaning contacts: {e}")
    
    def generate_campaigns_from_leads(self):
        """Generate campaigns using the selected leads with threading to prevent UI freezes"""
        try:
            if not hasattr(self, 'selected_contacts') or not self.selected_contacts:
                QMessageBox.warning(self, "No Leads Selected", 
                    "Please select existing leads first using the 'Select Existing Leads' button.")
                return
            
            print(f"[AI Widget] Generating campaigns from {len(self.selected_contacts)} selected leads...")
            print(f"[DEBUG] Selected contacts sample: {self.selected_contacts[0] if self.selected_contacts else 'None'}")
            self.campaign_status_label.setText("🤖 Generating AI campaigns from selected leads...")
            
            # Check if these are incident leads (have incident_type field)
            first_contact = self.selected_contacts[0] if self.selected_contacts else {}
            is_incident_leads = 'incident_type' in first_contact and first_contact.get('incident_type')
            
            # Use threading to prevent UI freeze
            from PySide6.QtCore import QThread, Signal
            
            class CampaignGeneratorThread(QThread):
                campaigns_ready = Signal(dict)
                error_occurred = Signal(str)
                
                def __init__(self, contacts, is_incident_leads, parent_widget):
                    super().__init__()
                    self.contacts = contacts
                    self.is_incident_leads = is_incident_leads
                    self.parent_widget = parent_widget
                
                def run(self):
                    try:
                        import gc  # Garbage collector for memory management
                        
                        if self.is_incident_leads:
                            print(f"[AI Widget] Detected incident leads, generating incident-specific campaigns...")
                            campaigns = self.generate_incident_campaigns_from_leads(self.contacts)
                        else:
                            print(f"[AI Widget] Generating standard AT&T/ADT campaigns...")
                            # Use optimized campaign generation
                            campaigns = self.generate_optimized_campaigns(self.contacts)
                        
                        # Force garbage collection to free memory
                        gc.collect()
                        
                        if campaigns:
                            self.campaigns_ready.emit(campaigns)
                        else:
                            self.error_occurred.emit("No campaigns were generated")
                            
                    except Exception as e:
                        print(f"[AI Widget] Error in campaign generation thread: {e}")
                        import traceback
                        traceback.print_exc()
                        self.error_occurred.emit(str(e))
                    finally:
                        # Clean up resources
                        cleanup_multiprocessing()
                
                def generate_incident_campaigns_from_leads(self, incident_contacts):
                    """Generate incident-specific campaigns from incident leads"""
                    try:
                        print(f"[AI Widget] Generating incident campaigns from {len(incident_contacts)} incident leads...")
                        
                        # Group contacts by incident type and location
                        incidents_with_contacts = {}
                        
                        for contact in incident_contacts:
                            incident_type = contact.get('incident_type', 'unknown')
                            incident_address = contact.get('incident_address', 'Unknown Location')
                            incident_date = contact.get('incident_date', '')
                            incident_key = f"{incident_type}_{incident_address}"
                            
                            if incident_key not in incidents_with_contacts:
                                incidents_with_contacts[incident_key] = {
                                    'incident_type': incident_type,
                                    'incident_address': incident_address,
                                    'incident_date': incident_date,
                                    'contacts': []
                                }
                            
                            # Only include contacts with email addresses
                            if contact.get('owner_email'):
                                incidents_with_contacts[incident_key]['contacts'].append(contact)
                        
                        # Generate campaigns for each incident
                        campaigns = {}
                        
                        for incident_key, incident_data in incidents_with_contacts.items():
                            if len(incident_data['contacts']) > 0:
                                campaign_id = f"incident_{incident_key}"
                                campaigns[campaign_id] = {
                                    'title': f"{incident_data['incident_type'].title()} Alert - {incident_data['incident_address']}",
                                    'contacts': incident_data['contacts'],
                                    'recipients': incident_data['contacts'],
                                    'incident_type': incident_data['incident_type'],
                                    'incident_address': incident_data['incident_address'],
                                    'incident_date': incident_data['incident_date']
                                }
                        
                        return campaigns
                        
                    except Exception as e:
                        print(f"[AI Widget] Error generating incident campaigns: {e}")
                        return {}
                
                def generate_optimized_campaigns(self, contacts):
                    """Generate optimized campaigns without heavy automation worker"""
                    try:
                        # Simple campaign generation without heavy processing
                        campaigns = {}
                        
                        # Separate contacts by type
                        fiber_contacts = [c for c in contacts if c.get('fiber_available') == True]
                        non_fiber_contacts = [c for c in contacts if c.get('fiber_available') == False]
                        unknown_contacts = [c for c in contacts if c.get('fiber_available') is None]
                        
                        # Generate AT&T Fiber campaign
                        if fiber_contacts:
                            campaigns['att_fiber'] = {
                                'title': 'AT&T Fiber Availability',
                                'contacts': fiber_contacts,
                                'recipients': fiber_contacts,
                                'campaign_type': 'AT&T Fiber'
                            }
                        
                        # Generate ADT Security campaign
                        if non_fiber_contacts or unknown_contacts:
                            security_contacts = non_fiber_contacts + unknown_contacts
                            campaigns['adt_security'] = {
                                'title': 'Home Security Solutions',
                                'contacts': security_contacts,
                                'recipients': security_contacts,
                                'campaign_type': 'ADT Security'
                            }
                        
                        return campaigns
                        
                    except Exception as e:
                        print(f"[AI Widget] Error generating optimized campaigns: {e}")
                        return {}
            
            # Create and start the thread
            self.campaign_thread = CampaignGeneratorThread(self.selected_contacts, is_incident_leads, self)
            self.campaign_thread.campaigns_ready.connect(self.handle_campaigns_generated)
            self.campaign_thread.error_occurred.connect(self.handle_campaign_error)
            self.worker_threads.append(self.campaign_thread)  # Track for cleanup
            self.campaign_thread.start()
            
        except Exception as e:
            print(f"[AI Widget] Error setting up campaign generation: {e}")
            import traceback
            traceback.print_exc()
            self.campaign_status_label.setText(f"❌ Error setting up campaign generation: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error setting up campaign generation: {str(e)}")
    
    def handle_campaigns_generated(self, campaigns):
        """Handle campaigns generated in background thread"""
        try:
            print(f"[AI Widget] ✅ Generated {len(campaigns)} campaigns")
            
            # Debug: Show campaign structure
            for campaign_id, campaign_data in campaigns.items():
                print(f"[DEBUG] Campaign {campaign_id}:")
                print(f"[DEBUG]   - Title: {campaign_data.get('title', 'Unknown')}")
                print(f"[DEBUG]   - Has contacts: {'contacts' in campaign_data}")
                print(f"[DEBUG]   - Has recipients: {'recipients' in campaign_data}")
                print(f"[DEBUG]   - Contacts count: {len(campaign_data.get('contacts', []))}")
                print(f"[DEBUG]   - Recipients count: {len(campaign_data.get('recipients', []))}")
            
            # Display the campaigns for review
            self.show_campaigns_for_review(campaigns)
            
            # Update status
            self.campaign_status_label.setText(f"✅ Generated {len(campaigns)} campaigns from {len(self.selected_contacts)} leads")
            
            # Show success message
            QMessageBox.information(self, "Campaigns Generated", 
                f"Successfully generated {len(campaigns)} campaigns:\n"
                f"• {len(self.selected_contacts)} leads used\n"
                f"• Campaigns are now available for review\n\n"
                f"Please review and approve the campaigns before sending.")
            
        except Exception as e:
            print(f"[AI Widget] Error handling generated campaigns: {e}")
            self.campaign_status_label.setText(f"❌ Error handling campaigns: {str(e)}")
    
    def handle_campaign_error(self, error_message):
        """Handle campaign generation error"""
        self.campaign_status_label.setText("❌ No campaigns generated")
        QMessageBox.warning(self, "No Campaigns Generated", 
            f"No campaigns were generated from the selected leads.\n"
            f"Error: {error_message}")
        print(f"[AI Widget] ❌ Campaign generation error: {error_message}")
    
    def generate_incident_campaigns_from_leads(self, incident_contacts):
        """Generate incident-specific campaigns from incident leads"""
        try:
            print(f"[AI Widget] Generating incident campaigns from {len(incident_contacts)} incident leads...")
            
            # Group contacts by incident type and location
            incidents_with_contacts = {}
            
            for contact in incident_contacts:
                incident_type = contact.get('incident_type', 'unknown')
                incident_address = contact.get('incident_address', 'Unknown Location')
                incident_date = contact.get('incident_date', '')
                incident_key = f"{incident_type}_{incident_address}"
                
                # Debug: Log incident information
                if len(incidents_with_contacts) < 5:  # Only log first 5 for debugging
                    print(f"[AI Widget] Processing incident: {incident_type} at {incident_address} (date: {incident_date})")
                
                if incident_key not in incidents_with_contacts:
                    incidents_with_contacts[incident_key] = {
                        'incident_type': incident_type,
                        'incident_address': incident_address,
                        'incident_date': incident_date,
                        'contacts': []
                    }
                
                # Only include contacts with email addresses
                if contact.get('owner_email'):
                    incidents_with_contacts[incident_key]['contacts'].append(contact)
            
            # Generate campaigns for each incident
            campaigns = {}
            
            for incident_key, incident_data in incidents_with_contacts.items():
                if len(incident_data['contacts']) < 3:  # Skip incidents with too few contacts
                    continue
                
                # Create incident object for campaign generation
                incident = {
                    'type': incident_data['incident_type'],
                    'address': incident_data['incident_address'],
                    'date': incident_data['incident_date'],
                    'priority': 'High' if incident_data['incident_type'] in ['fire', 'burglary', 'break-in'] else 'Medium',
                    'details': f"{incident_data['incident_type'].title()} incident at {incident_data['incident_address']}"
                }
                
                # Generate campaign using incident automation worker logic
                from workers.incident_automation_worker import IncidentAutomationWorker
                worker = IncidentAutomationWorker([], 50)  # Dummy parameters
                
                campaign = worker.generate_incident_email_campaign_with_contacts(incident, incident_data['contacts'])
                if campaign:
                    campaign_key = f"incident_{incident_key}"
                    campaigns[campaign_key] = campaign
                    print(f"[AI Widget] Generated campaign for {incident_type} incident: {campaign.get('title', 'Unknown')}")
                else:
                    print(f"[AI Widget] Failed to generate campaign for {incident_type} incident")
            
            print(f"[AI Widget] Generated {len(campaigns)} incident campaigns")
            return campaigns
            
        except Exception as e:
            print(f"[AI Widget] Error generating incident campaigns: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @Slot(object)
    def load_incident_leads_for_campaigns(self, incident_contacts):
        """Load incident leads for campaign generation"""
        try:
            print(f"[AI Widget] Received {len(incident_contacts)} incident leads for campaign generation")
            
            if not incident_contacts:
                QMessageBox.warning(self, "No Leads", "No incident leads received for campaign generation.")
                return
            
            # Store the incident leads
            self.selected_contacts = incident_contacts
            
            # Show breakdown of leads
            fiber_contacts = [c for c in incident_contacts if c.get('fiber_available') == True]
            non_fiber_contacts = [c for c in incident_contacts if c.get('fiber_available') == False]
            unknown_contacts = [c for c in incident_contacts if c.get('fiber_available') is None]
            
            # Update status
            status_msg = f"📧 Loaded {len(incident_contacts)} incident leads ({len(fiber_contacts)} fiber, {len(non_fiber_contacts)} non-fiber, {len(unknown_contacts)} unknown)"
            self.campaign_status_label.setText(status_msg)
            
            # Enable campaign generation button
            self.generate_from_leads_btn.setEnabled(True)
            
            # Show success message
            QMessageBox.information(self, "Incident Leads Loaded", 
                                  f"✅ Successfully loaded {len(incident_contacts)} incident leads:\n"
                                  f"• {len(fiber_contacts)} AT&T Fiber customers\n"
                                  f"• {len(non_fiber_contacts)} non-fiber customers\n"
                                  f"• {len(unknown_contacts)} unknown fiber status\n\n"
                                  f"You can now generate targeted AI email campaigns for these leads.")
            
            print(f"[AI Widget] ✅ Loaded {len(incident_contacts)} incident leads for campaign generation")
            
        except Exception as e:
            print(f"[AI Widget] Error loading incident leads: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error loading incident leads: {str(e)}")