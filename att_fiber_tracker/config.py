"""Configuration settings for the AT&T Fiber Tracker application."""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load API keys from config file
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')

def load_config():
    """Load configuration from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

config = load_config()

# API Keys
BATCHDATA_API_KEY = config.get('batchdata_api_key', '')
MAILCHIMP_API_KEY = config.get('mailchimp_api_key', '')
MAILCHIMP_SERVER_PREFIX = config.get('mailchimp_server_prefix', 'us17')
ACTIVEKNOCKER_API_KEY = config.get('activeknocker_api_key', '')
OPENAI_API_KEY = config.get('openai_api_key', '')

# URLs and endpoints
REDFIN_SEARCH_URL = "https://www.redfin.com/stingray/api/gis?al=1&market=wilmington&num_homes=350&ord=redfin-recommended-asc&page_number=1&region_id=118&region_type=6&sf=1,2,3,5,6,7&status=9&uipt=1,2,3,4,5,6,7,8&v=8"

# Bach API settings
BACH_API_KEY = os.getenv('BACH_API_KEY')

# Selenium settings
CHROME_PROFILE_PATH = os.path.expanduser('~/.config/google-chrome/Default')
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver')

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'att_fiber_tracker.log') 