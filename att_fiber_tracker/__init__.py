"""AT&T Fiber Tracker package."""

# from .redfin_parser import download_redfin_data, parse_redfin_csv
from .fiber_checker import process_addresses
from .services.api_service import ATTService
from .services.bach_service import BachService
from .services.mailchimp_service import MailchimpService
from .app import FiberTrackerApp, main

__version__ = "1.0.0" 