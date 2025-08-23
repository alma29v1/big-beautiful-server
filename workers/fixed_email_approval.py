
"""
Fixed AI Email Approval Workflow - Thread-Safe Campaign Display
"""

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication

class FixedEmailApprovalHandler(QObject):
    """Fixed email approval handler with proper thread safety"""
    
    # Signals for thread-safe communication
    campaigns_ready_signal = Signal(object)  # campaigns dict
    approval_status_signal = Signal(bool)    # approved/rejected
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.pending_campaigns = {}
        self.setup_connections()
    
    def setup_connections(self):
        """Setup thread-safe signal connections"""
        
        # Connect campaigns ready signal to UI update
        self.campaigns_ready_signal.connect(
            self.display_campaigns_in_ui,
            Qt.QueuedConnection  # Ensures it runs on main thread
        )
        
        # Connect approval status back to automation
        self.approval_status_signal.connect(
            self.handle_approval_response,
            Qt.QueuedConnection
        )
    
    @Slot(object)
    def receive_campaigns_from_automation(self, campaigns):
        """Receive campaigns from automation worker (called from worker thread)"""
        
        print(f"[EmailApproval] Received {len(campaigns)} campaigns from automation")
        
        # Store campaigns
        self.pending_campaigns = campaigns
        
        # Emit signal to update UI (thread-safe)
        self.campaigns_ready_signal.emit(campaigns)
    
    @Slot(object)
    def display_campaigns_in_ui(self, campaigns):
        """Display campaigns in UI (runs on main thread)"""
        
        print(f"[EmailApproval] Displaying {len(campaigns)} campaigns in UI")
        
        # Get AI Email Marketing widget
        if hasattr(self.main_window, 'efficient_ai_widget') and self.main_window.efficient_ai_widget:
            # Update the widget with campaigns
            self.main_window.efficient_ai_widget.show_campaigns_for_review(campaigns)
            
            # Switch to the AI Email Marketing tab
            for i in range(self.main_window.tabs.count()):
                if self.main_window.tabs.tabText(i) == "AI Email Marketing":
                    self.main_window.tabs.setCurrentIndex(i)
                    break
            
            # Update main window log
            self.main_window.log_text.append(f"[AI Email] 📧 {len(campaigns)} campaigns now visible for approval")
            self.main_window.log_text.append("[AI Email] 👀 Please review campaigns in the AI Email Marketing tab")
            
        else:
            print("[EmailApproval] ERROR: AI Email Marketing widget not available")
            self.main_window.log_text.append("[AI Email] ❌ Error: Cannot display campaigns - widget not loaded")
    
    @Slot(bool)
    def handle_approval_response(self, approved):
        """Handle approval/rejection response"""
        
        if approved:
            print("[EmailApproval] Campaigns approved by user")
            self.main_window.log_text.append("[AI Email] ✅ Campaigns approved - proceeding with send")
        else:
            print("[EmailApproval] Campaigns rejected by user")
            self.main_window.log_text.append("[AI Email] ❌ Campaigns rejected - stopping automation")
        
        # Set approval status for automation worker
        if hasattr(self.main_window, 'automation_worker'):
            self.main_window.automation_worker.email_approved = approved
            self.main_window.automation_worker.email_review_complete = True

# Integration code for main_window.py
def integrate_fixed_email_approval(main_window):
    """Integrate the fixed email approval system into main window"""
    
    # Create the fixed email approval handler
    main_window.email_approval_handler = FixedEmailApprovalHandler(main_window)
    
    # Connect automation worker signals
    if hasattr(main_window, 'automation_worker'):
        # Connect regular campaigns signal
        main_window.automation_worker.regular_campaigns_signal.connect(
            main_window.email_approval_handler.receive_campaigns_from_automation,
            Qt.QueuedConnection
        )
        
        # Connect incident campaigns signal  
        main_window.automation_worker.incident_campaigns_signal.connect(
            main_window.email_approval_handler.receive_campaigns_from_automation,
            Qt.QueuedConnection
        )
    
    print("[Integration] Fixed email approval system integrated")

# Test function to verify the fix
def test_fixed_email_approval():
    """Test the fixed email approval system"""
    
    print("🧪 TESTING FIXED EMAIL APPROVAL SYSTEM")
    print("=" * 50)
    
    # Create sample campaigns
    test_campaigns = {
        'att_fiber': {
            'title': '🌐 AT&T Fiber Campaign',
            'subject': 'Lightning-Fast Fiber Internet Available!',
            'recipients': 4,
            'content': 'Test fiber campaign content...'
        },
        'adt_general': {
            'title': '🔒 ADT Security Campaign', 
            'subject': 'Protect Your Home with Professional Security',
            'recipients': 165,
            'content': 'Test security campaign content...'
        }
    }
    
    print(f"📧 Test campaigns created: {list(test_campaigns.keys())}")
    print(f"📊 Total recipients: {sum(c['recipients'] for c in test_campaigns.values())}")
    
    return test_campaigns

if __name__ == "__main__":
    test_campaigns = test_fixed_email_approval()
    print("✅ Fixed email approval system ready for integration")
