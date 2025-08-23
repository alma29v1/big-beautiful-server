"""Main application window for the AT&T Fiber Tracker."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
import logging
from att_fiber_tracker.services.api_service import ATTService
from att_fiber_tracker.services.bach_service import BachService
from att_fiber_tracker.services.mailchimp_service import MailchimpService
from att_fiber_tracker.services.xai_service import XAIService
from att_fiber_tracker.ui.xai_marketing_widget import XAIMarketingWidget
from att_fiber_tracker.ui.main_widget import MainWidget
from att_fiber_tracker.ui.adt_results_widget import ADTResultsWidget
from att_fiber_tracker.ui.mailchimp_widget import MailchimpWidget
# from .redfin_parser import download_redfin_data, parse_redfin_csv
from att_fiber_tracker.config import REDFIN_SEARCH_URL, MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX

logger = logging.getLogger(__name__)

class FiberTrackerApp(QMainWindow):
    """Main application window for AT&T Fiber Tracker."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        self.setWindowTitle("AT&T Fiber Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize services
        self.att_service = ATTService()
        self.bach_service = BachService()
        self.mailchimp_service = MailchimpService(MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX)
        self.xai_service = XAIService()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self._create_tabs()
        
    def _create_tabs(self):
        """Create and add tabs to the application."""
        # Main tab
        main_tab = MainWidget()
        self.tab_widget.addTab(main_tab, "Main")
        
        # ADT Detection Results tab
        adt_results_tab = ADTResultsWidget()
        self.tab_widget.addTab(adt_results_tab, "ADT Detection Results")
        
        # BatchData tab
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        batch_label = QLabel("BatchData Processing - Coming Soon")
        batch_layout.addWidget(batch_label)
        self.tab_widget.addTab(batch_tab, "BatchData")
        
        # Contacts tab
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)
        contacts_label = QLabel("Contact Management - Coming Soon")
        contacts_layout.addWidget(contacts_label)
        self.tab_widget.addTab(contacts_tab, "Contacts")
        
        # ATT Fiber Results tab
        fiber_tab = QWidget()
        fiber_layout = QVBoxLayout(fiber_tab)
        fiber_label = QLabel("AT&T Fiber Results - Coming Soon")
        fiber_layout.addWidget(fiber_label)
        self.tab_widget.addTab(fiber_tab, "ATT Fiber Results")
        
        # ActiveKnocker tab
        knocker_tab = QWidget()
        knocker_layout = QVBoxLayout(knocker_tab)
        knocker_label = QLabel("ActiveKnocker Integration - Coming Soon")
        knocker_layout.addWidget(knocker_label)
        self.tab_widget.addTab(knocker_tab, "ActiveKnocker")
        
        # AI Marketing tab with XAI Email Assistant
        marketing_tab = XAIMarketingWidget()
        self.tab_widget.addTab(marketing_tab, "AI Marketing")
        
        # Mailchimp tab
        mailchimp_tab = MailchimpWidget()
        self.tab_widget.addTab(mailchimp_tab, "Mailchimp")
        
        # ADT Verification tab
        verification_tab = QWidget()
        verification_layout = QVBoxLayout(verification_tab)
        verification_label = QLabel("ADT Verification - Coming Soon")
        verification_layout.addWidget(verification_label)
        self.tab_widget.addTab(verification_tab, "ADT Verification")
        
        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_label = QLabel("Settings - Coming Soon")
        settings_layout.addWidget(settings_label)
        self.tab_widget.addTab(settings_tab, "Settings")

def main():
    """Run the main application."""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = FiberTrackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 