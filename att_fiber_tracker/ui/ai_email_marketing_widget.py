import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QGroupBox, QFormLayout, QProgressBar,
    QMessageBox, QFileDialog, QDialog, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFrame,
    QScrollArea, QGridLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QColor

# Set up logging
logger = logging.getLogger(__name__)

class EmailGenerationWorker(QThread):
    """Worker thread for generating emails"""
    finished_signal = Signal(str, str)  # response, email_type
    error_signal = Signal(str)
    
    def __init__(self, prompt, email_type):
        super().__init__()
        self.prompt = prompt
        self.email_type = email_type
    
    def run(self):
        try:
            # Import here to avoid circular imports
            from services.ai_email_marketing_service import AIEmailMarketingService
            
            service = AIEmailMarketingService()
            
            # Use the chat_with_ai method for simple email generation
            response = service.chat_with_ai(self.prompt)
            self.finished_signal.emit(response, self.email_type)
        except Exception as e:
            self.error_signal.emit(str(e))

class EmailPreviewDialog(QDialog):
    """Dialog to preview emails in a popup window"""
    
    def __init__(self, email_content, parent=None):
        super().__init__(parent)
        self.email_content = email_content
        self.setWindowTitle("Email Preview")
        self.setFixedSize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📧 Email Preview")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Subject line
        subject_label = QLabel(f"Subject: {self.email_content.get('subject', 'No Subject')}")
        subject_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(subject_label)
        
        # Preview tabs
        preview_tabs = QTabWidget()
        
        # HTML Preview
        html_preview = QTextEdit()
        html_preview.setHtml(self.email_content.get('html_content', ''))
        html_preview.setReadOnly(True)
        preview_tabs.addTab(html_preview, "📱 HTML View")
        
        # Text Preview
        text_preview = QTextEdit()
        text_preview.setPlainText(self.email_content.get('text_version', ''))
        text_preview.setReadOnly(True)
        preview_tabs.addTab(text_preview, "📝 Text View")
        
        layout.addWidget(preview_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy HTML")
        copy_btn.clicked.connect(self.copy_html)
        copy_btn.setStyleSheet("""
            QPushButton {{
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        
        save_btn = QPushButton("💾 Save Email")
        save_btn.clicked.connect(self.save_email)
        save_btn.setStyleSheet("""
            QPushButton {{
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
        """)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {{
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #545b62;
            }}
        """)
        
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def copy_html(self):
        """Copy HTML content to clipboard"""
        try:
            from PySide6.QtGui import QClipboard
            from PySide6.QtWidgets import QApplication
            
            clipboard = QApplication.clipboard()
            clipboard.setText(self.email_content.get('html_content', ''))
            QMessageBox.information(self, "Copied", "HTML content copied to clipboard!")
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Failed to copy: {e}")
    
    def save_email(self):
        """Save email to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_type = self.email_content.get('type', 'email')
            filename = f"saved_emails/{email_type}_{timestamp}.json"
            
            os.makedirs('saved_emails', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.email_content, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Email Saved", f"Email saved as: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save email: {e}")

class AIEmailMarketingWidget(QWidget):
    """Clean, simple AI email marketing widget"""
    
    def __init__(self):
        super().__init__()
        self.current_email_content = None
        self.chat_history = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("🤖 AI Email Marketing Assistant")
        header.setStyleSheet("""
            QLabel {{
                background-color: #007bff;
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
            }}
        """)
        layout.addWidget(header)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        
        # Chat Tab
        chat_tab = self.create_chat_tab()
        self.tab_widget.addTab(chat_tab, "💬 AI Chat")
        
        # Email Generator Tab
        generator_tab = self.create_generator_tab()
        self.tab_widget.addTab(generator_tab, "✍️ Email Generator")
        
        # Saved Emails Tab
        saved_tab = self.create_saved_emails_tab()
        self.tab_widget.addTab(saved_tab, "📁 Saved Emails")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }}
        """)
        layout.addWidget(self.status_label)
    
    def create_chat_tab(self):
        """Create the AI chat tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setStyleSheet("""
            QTextEdit {{
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }}
        """)
        layout.addWidget(self.chat_display)
        
        # Input section
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me to generate emails, write subject lines, or provide marketing advice...")
        self.chat_input.setStyleSheet("""
            QLineEdit {{
                padding: 12px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: #007bff;
            }}
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {{
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        send_btn.clicked.connect(self.send_chat_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        
        # Quick actions
        quick_actions = QGroupBox("Quick Actions")
        quick_layout = QGridLayout(quick_actions)
        
        quick_buttons = [
            ("📧 Generate Fiber Email", "fiber"),
            ("🔒 Generate Security Email", "security"),
            ("📦 Generate Combo Email", "combo"),
            ("✨ Write Subject Lines", "subjects")
        ]
        
        for i, (text, action) in enumerate(quick_buttons):
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {{
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #218838;
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self.quick_action(a))
            quick_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addWidget(quick_actions)
        
        # Email management buttons
        email_mgmt = QGroupBox("Email Management")
        email_layout = QHBoxLayout(email_mgmt)
        
        save_btn = QPushButton("💾 Save Current Email")
        save_btn.clicked.connect(self.save_current_email)
        save_btn.setStyleSheet("""
            QPushButton {{
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #138496;
            }}
        """)
        
        load_btn = QPushButton("📁 Load Saved Email")
        load_btn.clicked.connect(self.load_saved_email)
        load_btn.setStyleSheet("""
            QPushButton {{
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5a32a3;
            }}
        """)
        
        email_layout.addWidget(save_btn)
        email_layout.addWidget(load_btn)
        email_layout.addStretch()
        
        layout.addWidget(email_mgmt)
        
        # Add welcome message
        self.add_chat_message("AI Assistant", 
            "👋 Hello! I'm your AI email marketing assistant.\n\n"
            "I can help you:\n"
            "• Generate professional email campaigns\n"
            "• Create compelling subject lines\n"
            "• Write marketing content\n"
            "• Provide strategic advice\n\n"
            "What would you like to create today?")
        
        return tab
    
    def create_generator_tab(self):
        """Create the email generator tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Email type selection
        type_group = QGroupBox("Email Type")
        type_layout = QFormLayout(type_group)
        
        self.email_type_combo = QComboBox()
        self.email_type_combo.addItems([
            "AT&T Fiber Introduction",
            "ADT Security Offer", 
            "Combined Services Package",
            "Follow-up Campaign",
            "Seasonal Promotion"
        ])
        type_layout.addRow("Email Type:", self.email_type_combo)
        
        layout.addWidget(type_group)
        
        # Custom prompt
        prompt_group = QGroupBox("Custom Instructions")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.custom_prompt = QTextEdit()
        self.custom_prompt.setPlaceholderText("Enter specific instructions for your email (optional)...")
        self.custom_prompt.setMaximumHeight(100)
        prompt_layout.addWidget(self.custom_prompt)
        
        layout.addWidget(prompt_group)
        
        # Generate button
        generate_btn = QPushButton("🚀 Generate Email")
        generate_btn.setStyleSheet("""
            QPushButton {{
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """)
        generate_btn.clicked.connect(self.generate_email)
        layout.addWidget(generate_btn)
        
        # Preview area
        preview_group = QGroupBox("Email Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.email_preview = QTextEdit()
        self.email_preview.setReadOnly(True)
        self.email_preview.setMinimumHeight(200)
        preview_layout.addWidget(self.email_preview)
        
        # Preview buttons
        preview_btn_layout = QHBoxLayout()
        
        popup_btn = QPushButton("🔍 Open in Popup")
        popup_btn.clicked.connect(self.open_email_popup)
        popup_btn.setStyleSheet("""
            QPushButton {{
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #e0a800;
            }}
        """)
        
        copy_btn = QPushButton("📋 Copy HTML")
        copy_btn.clicked.connect(self.copy_email_html)
        copy_btn.setStyleSheet("""
            QPushButton {{
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #545b62;
            }}
        """)
        
        preview_btn_layout.addWidget(popup_btn)
        preview_btn_layout.addWidget(copy_btn)
        preview_btn_layout.addStretch()
        
        preview_layout.addLayout(preview_btn_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
        return tab
    
    def create_saved_emails_tab(self):
        """Create the saved emails tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("📁 Saved Emails")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Email list
        self.saved_emails_list = QListWidget()
        self.saved_emails_list.itemDoubleClicked.connect(self.load_selected_email)
        layout.addWidget(self.saved_emails_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.refresh_saved_emails)
        
        load_btn = QPushButton("📖 Load Selected")
        load_btn.clicked.connect(self.load_selected_email)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_email)
        delete_btn.setStyleSheet("""
            QPushButton {{
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Load saved emails on startup
        self.refresh_saved_emails()
        
        return tab
    
    def add_chat_message(self, sender, message, is_ai=True):
        """Add a message to the chat display"""
        try:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            
            # Format message
            if is_ai:
                formatted = f"""
<div style="margin: 10px 0; padding: 12px; background-color: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 5px;">
    <strong style="color: #1976d2;">🤖 {sender}:</strong><br>
    <span style="color: #333; line-height: 1.5;">{message.replace(chr(10), '<br>')}</span>
</div>
"""
            else:
                formatted = f"""
<div style="margin: 10px 0; padding: 12px; background-color: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 5px;">
    <strong style="color: #7b1fa2;">👤 {sender}:</strong><br>
    <span style="color: #333; line-height: 1.5;">{message.replace(chr(10), '<br>')}</span>
</div>
"""
            
            cursor.insertHtml(formatted)
            self.chat_display.setTextCursor(cursor)
            self.chat_display.ensureCursorVisible()
            
            # Store in history
            self.chat_history.append({
                'sender': sender,
                'message': message,
                'is_ai': is_ai,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error adding chat message: {e}")
    
    def send_chat_message(self):
        """Send a chat message"""
        try:
            message = self.chat_input.text().strip()
            if not message:
                return
            
            self.chat_input.clear()
            self.add_chat_message("You", message, is_ai=False)
            
            # Check if this is an email generation request
            if any(keyword in message.lower() for keyword in ['email', 'generate', 'create', 'write', 'campaign']):
                self.generate_email_from_chat(message)
            else:
                self.get_ai_response(message)
                
        except Exception as e:
            self.add_chat_message("AI Assistant", f"❌ Error: {e}")
    
    def quick_action(self, action):
        """Handle quick action buttons"""
        actions = {
            'fiber': "Generate a professional email about AT&T Fiber internet services",
            'security': "Generate a professional email about ADT security systems", 
            'combo': "Generate a professional email about combined AT&T Fiber and ADT services",
            'subjects': "Generate 5 compelling subject lines for AT&T Fiber marketing"
        }
        
        if action in actions:
            self.chat_input.setText(actions[action])
            self.send_chat_message()
    
    def generate_email(self):
        """Generate email from the generator tab"""
        try:
            email_type = self.email_type_combo.currentText()
            custom_instructions = self.custom_prompt.toPlainText().strip()
            
            # Create prompt
            prompt = f"Generate a professional email for: {email_type}"
            if custom_instructions:
                prompt += f"\n\nAdditional instructions: {custom_instructions}"
            
            self.status_label.setText("🔄 Generating email...")
            
            # Start worker
            self.email_worker = EmailGenerationWorker(prompt, email_type)
            self.email_worker.finished_signal.connect(self.on_email_generated)
            self.email_worker.error_signal.connect(self.on_email_error)
            self.email_worker.start()
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
    
    def generate_email_from_chat(self, message):
        """Generate email from chat message"""
        try:
            self.add_chat_message("AI Assistant", "🎯 I'll generate an email for you!")
            
            self.status_label.setText("🔄 Generating email...")
            
            # Start worker
            self.email_worker = EmailGenerationWorker(message, "chat_request")
            self.email_worker.finished_signal.connect(self.on_email_generated)
            self.email_worker.error_signal.connect(self.on_email_error)
            self.email_worker.start()
            
        except Exception as e:
            self.add_chat_message("AI Assistant", f"❌ Error generating email: {e}")
    
    def get_ai_response(self, message):
        """Get AI response using XAI for general chat"""
        try:
            from services.ai_email_marketing_service import AIEmailMarketingService
            service = AIEmailMarketingService()
            response = service.chat_with_ai(message)
            self.add_chat_message("AI Assistant (via XAI)", response)
        except Exception as e:
            self.add_chat_message("AI Assistant", f"❌ Error with XAI: {e}. Falling back...")
            # Optional simple fallback
            self.add_chat_message("AI Assistant", "Sorry, having trouble connecting to XAI. How can I help?")
    
    def on_email_generated(self, response, email_type):
        """Handle successful email generation"""
        try:
            self.status_label.setText("✅ Email generated successfully!")
            
            # Parse response into email content
            email_content = self.parse_email_response(response, email_type)
            self.current_email_content = email_content
            
            # Update preview
            self.email_preview.setHtml(email_content.get('html_content', ''))
            
            # Add to chat
            self.add_chat_message("AI Assistant", 
                f"✅ Generated {email_type} email!\n\n"
                f"📧 Subject: {email_content.get('subject', 'N/A')}\n\n"
                f"Check the Email Generator tab to see the preview!")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.add_chat_message("AI Assistant", f"❌ Error processing email: {e}")
    
    def on_email_error(self, error):
        """Handle email generation error"""
        self.status_label.setText(f"❌ Error: {error}")
        self.add_chat_message("AI Assistant", f"❌ Error generating email: {error}")
    
    def parse_email_response(self, response, email_type):
        """Parse AI response into email components"""
        try:
            # Extract subject line
            lines = response.split('\n')
            subject = ""
            
            for line in lines:
                if 'subject' in line.lower() and ':' in line:
                    subject = line.split(':', 1)[1].strip()
                    break
            
            # Default subject if none found
            if not subject:
                if 'fiber' in email_type.lower():
                    subject = "High-Speed AT&T Fiber Now Available!"
                elif 'security' in email_type.lower():
                    subject = "Protect Your Home with Professional ADT Security"
                else:
                    subject = "Special Offer from Seaside Security & Communications"
            
            # Create HTML content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
                    .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                    .content {{ padding: 20px; background: #f8f9fa; margin: 10px 0; border-radius: 5px; }}
                    .cta {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                    .footer {{ background: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Seaside Security & Communications</h1>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <div>{response.replace(chr(10), '<br>')}</div>
                    <a href="tel:(910) 555-FIBER" class="cta">Call (910) 555-FIBER</a>
                </div>
                <div class="footer">
                    <p>Seaside Security & Communications<br>
                    Email: fiber@seasidesecurity.com | Web: https://seasidesecurity.com</p>
                </div>
            </body>
            </html>
            """
            
            # Create text version
            text_content = f"""
{subject}

{response}

Call us at (910) 555-FIBER
Email: fiber@seasidesecurity.com
Web: https://seasidesecurity.com

---
Seaside Security & Communications
Your trusted partner for connectivity and security solutions.
            """
            
            return {
                'type': email_type,
                'subject': subject,
                'html_content': html_content,
                'text_version': text_content,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing email response: {e}")
            return {}

    def open_email_popup(self):
        """Open email preview in popup dialog"""
        if not self.current_email_content:
            QMessageBox.warning(self, "No Email", "No email generated yet!")
            return
        
        dialog = EmailPreviewDialog(self.current_email_content, self)
        dialog.exec()
    
    def copy_email_html(self):
        """Copy email HTML to clipboard"""
        if not self.current_email_content:
            QMessageBox.warning(self, "No Email", "No email generated yet!")
            return
        
        try:
            from PySide6.QtGui import QClipboard
            from PySide6.QtWidgets import QApplication
            
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_email_content.get('html_content', ''))
            QMessageBox.information(self, "Copied", "Email HTML copied to clipboard!")
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Failed to copy: {e}")
    
    def save_current_email(self):
        """Save the current email to file"""
        if not self.current_email_content:
            QMessageBox.warning(self, "No Email", "No email generated yet!")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_type = self.current_email_content.get('type', 'email')
            filename = f"saved_emails/{email_type}_{timestamp}.json"
            
            os.makedirs('saved_emails', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_email_content, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Saved", f"Email saved as: {filename}")
            self.refresh_saved_emails()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")
    
    def load_saved_email(self):
        """Load a saved email from file"""
        filename = QFileDialog.getOpenFileName(self, "Load Saved Email", "saved_emails", "JSON Files (*.json)" )[0]
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.current_email_content = json.load(f)
            
            self.email_preview.setHtml(self.current_email_content.get('html_content', ''))
            self.add_chat_message("AI Assistant", f"📁 Loaded saved email from {os.path.basename(filename)}")
            self.tab_widget.setCurrentIndex(1)  # Switch to generator tab
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load: {e}")
    
    def refresh_saved_emails(self):
        """Refresh the list of saved emails"""
        self.saved_emails_list.clear()
        
        try:
            os.makedirs('saved_emails', exist_ok=True)
            saved_files = sorted([f for f in os.listdir('saved_emails') if f.endswith('.json')])
            
            for file in saved_files:
                item = QListWidgetItem(file)
                item.setData(Qt.UserRole, os.path.join('saved_emails', file))
                self.saved_emails_list.addItem(item)
            
        except Exception as e:
            self.add_chat_message("AI Assistant", f"❌ Error loading saved emails: {e}")
    
    def load_selected_email(self):
        """Load the selected saved email"""
        selected = self.saved_emails_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "No email selected!")
            return
        
        filename = selected.data(Qt.UserRole)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.current_email_content = json.load(f)
            
            self.email_preview.setHtml(self.current_email_content.get('html_content', ''))
            self.add_chat_message("AI Assistant", f"📁 Loaded {os.path.basename(filename)}")
            self.tab_widget.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load: {e}")
    
    def delete_selected_email(self):
        """Delete the selected saved email"""
        selected = self.saved_emails_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "No Selection", "No email selected!")
            return
        
        filename = selected.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete {os.path.basename(filename)}?", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(filename)
                self.refresh_saved_emails()
                QMessageBox.information(self, "Deleted", "Email deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete: {e}")

    def refresh_saved_emails(self):
        """Refresh the list of saved emails"""
        self.saved_emails_list.clear()
        
        try:
            os.makedirs('saved_emails', exist_ok=True)
            saved_files = sorted([f for f in os.listdir('saved_emails') if f.endswith('.json')])
            
            for file in saved_files:
                item = QListWidgetItem(file)
                item.setData(Qt.UserRole, os.path.join('saved_emails', file))
                self.saved_emails_list.addItem(item)
            
        except Exception as e:
            self.add_chat_message("AI Assistant", f"❌ Error loading saved emails: {e}")

# For testing
if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = AIEmailMarketingWidget()
    widget.show()
    sys.exit(app.exec()) 