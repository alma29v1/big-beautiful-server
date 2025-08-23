"""Widget for XAI Email Assistant functionality."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QComboBox, QGroupBox,
                             QMessageBox, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
import json
import logging
from ..services.xai_service import XAIService

logger = logging.getLogger(__name__)

class XAIMarketingWidget(QWidget):
    """Widget for AI-powered email marketing assistance."""
    
    def __init__(self):
        super().__init__()
        self.xai_service = XAIService()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        # Campaign Settings
        settings_group = QGroupBox("Campaign Settings")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)
        
        # Audience Selection
        settings_layout.addWidget(QLabel("Target Audience:"))
        self.audience_combo = QComboBox()
        self.audience_combo.addItems([
            "Homeowners with AT&T Fiber Available",
            "New Construction Properties",
            "Neighborhoods with Recent Fiber Installation",
            "Custom Audience"
        ])
        settings_layout.addWidget(self.audience_combo)
        
        # Tone Selection
        settings_layout.addWidget(QLabel("Tone:"))
        self.tone_combo = QComboBox()
        self.tone_combo.addItems([
            "Professional",
            "Friendly",
            "Exciting",
            "Informative",
            "Persuasive"
        ])
        settings_layout.addWidget(self.tone_combo)
        
        # Key Points
        settings_layout.addWidget(QLabel("Key Points:"))
        self.key_points_list = QListWidget()
        self.key_points_list.addItems([
            "Ultra-fast internet speeds up to 5 Gbps",
            "No data caps or equipment fees",
            "Professional installation included",
            "Reliable fiber-optic technology",
            "Special promotional pricing available"
        ])
        self.key_points_list.setSelectionMode(QListWidget.MultiSelection)
        settings_layout.addWidget(self.key_points_list)
        
        # Call to Action
        settings_layout.addWidget(QLabel("Call to Action:"))
        self.cta_combo = QComboBox()
        self.cta_combo.addItems([
            "Schedule Installation",
            "Learn More",
            "Get Special Offer",
            "Sign Up Now",
            "Contact Sales"
        ])
        settings_layout.addWidget(self.cta_combo)
        
        layout.addWidget(settings_group)
        
        # Campaign Preview
        preview_group = QGroupBox("Campaign Preview")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        
        # Subject Line
        preview_layout.addWidget(QLabel("Subject Line:"))
        self.subject_edit = QTextEdit()
        self.subject_edit.setMaximumHeight(50)
        preview_layout.addWidget(self.subject_edit)
        
        # Email Body
        preview_layout.addWidget(QLabel("Email Body:"))
        self.body_edit = QTextEdit()
        preview_layout.addWidget(self.body_edit)
        
        layout.addWidget(preview_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Campaign")
        self.generate_btn.clicked.connect(self.generate_campaign)
        button_layout.addWidget(self.generate_btn)
        
        self.review_btn = QPushButton("Review & Optimize")
        self.review_btn.clicked.connect(self.review_campaign)
        button_layout.addWidget(self.review_btn)
        
        self.save_btn = QPushButton("Save Campaign")
        self.save_btn.clicked.connect(self.save_campaign)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
    def generate_campaign(self):
        """Generate a new email campaign using AI."""
        try:
            # Get selected key points
            key_points = [item.text() for item in 
                         self.key_points_list.selectedItems()]
            
            if not key_points:
                QMessageBox.warning(self, "Warning", 
                                  "Please select at least one key point.")
                return
            
            # Prepare campaign data
            campaign_data = {
                "target_audience": self.audience_combo.currentText(),
                "key_points": key_points,
                "tone": self.tone_combo.currentText(),
                "call_to_action": self.cta_combo.currentText()
            }
            
            # Generate campaign
            result = self.xai_service.generate_campaign(campaign_data)
            
            if result.get("success"):
                campaign = result["campaign"]
                self.subject_edit.setText(campaign["subject_line"])
                self.body_edit.setText(campaign["email_body"])
                QMessageBox.information(self, "Success", 
                                      "Campaign generated successfully!")
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Failed to generate campaign: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error generating campaign: {str(e)}")
            QMessageBox.critical(self, "Error", 
                               f"An error occurred: {str(e)}")
    
    def review_campaign(self):
        """Review and optimize the current campaign."""
        try:
            # Get current campaign content
            subject = self.subject_edit.toPlainText()
            body = self.body_edit.toPlainText()
            
            if not subject or not body:
                QMessageBox.warning(self, "Warning", 
                                  "Please generate or enter a campaign first.")
                return
            
            campaign_content = f"Subject: {subject}\n\nBody:\n{body}"
            
            # Get review feedback
            result = self.xai_service.review_campaign(campaign_content)
            
            if result.get("success"):
                # Show feedback
                feedback = result["feedback"]
                msg = QMessageBox(self)
                msg.setWindowTitle("Campaign Review")
                msg.setText("Review Feedback:")
                msg.setDetailedText(feedback)
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Apply)
                
                response = msg.exec_()
                
                # If user clicks Apply, optimize the campaign
                if response == QMessageBox.Apply:
                    optimize_result = self.xai_service.optimize_campaign(
                        campaign_content, feedback)
                    
                    if optimize_result.get("success"):
                        # Parse and update optimized content
                        content = optimize_result["optimized_content"]
                        parts = content.split('\n\n')
                        
                        subject = next((p.replace('Subject:', '').strip() 
                                      for p in parts if 'Subject:' in p), '')
                        body = next((p.replace('Body:', '').strip() 
                                   for p in parts if 'Body:' in p), '')
                        
                        if subject:
                            self.subject_edit.setText(subject)
                        if body:
                            self.body_edit.setText(body)
                            
                        QMessageBox.information(self, "Success", 
                                              "Campaign optimized successfully!")
                    else:
                        QMessageBox.warning(self, "Error", 
                                          f"Failed to optimize campaign: {optimize_result.get('error')}")
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Failed to review campaign: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error reviewing campaign: {str(e)}")
            QMessageBox.critical(self, "Error", 
                               f"An error occurred: {str(e)}")
    
    def save_campaign(self):
        """Save the current campaign."""
        try:
            subject = self.subject_edit.toPlainText()
            body = self.body_edit.toPlainText()
            
            if not subject or not body:
                QMessageBox.warning(self, "Warning", 
                                  "Please generate or enter a campaign first.")
                return
            
            campaign_data = {
                "subject_line": subject,
                "email_body": body,
                "settings": {
                    "target_audience": self.audience_combo.currentText(),
                    "tone": self.tone_combo.currentText(),
                    "key_points": [item.text() for item in 
                                 self.key_points_list.selectedItems()],
                    "call_to_action": self.cta_combo.currentText()
                }
            }
            
            # Save to file
            with open('saved_campaigns.json', 'w') as f:
                json.dump(campaign_data, f, indent=2)
                
            QMessageBox.information(self, "Success", 
                                  "Campaign saved successfully!")
            
        except Exception as e:
            logger.error(f"Error saving campaign: {str(e)}")
            QMessageBox.critical(self, "Error", 
                               f"An error occurred: {str(e)}") 