import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
BATCHDATA_API_TOKEN = "i2qyvJigHe7OpRkOBTMC29InO5YM6LSh5V9JDLEx"
MAILCHIMP_API_KEY = "f0c09c934d57b78dba2533ed252c933d-us17"
MAILCHIMP_SERVER_PREFIX = "us17"
GOOGLE_MAPS_API_KEY = "AIzaSyBpH5E2KKGo-GypuWA8Mj_RpKXUOHQuhkI"

# Mailchimp List IDs
FIBER_AVAILABLE_LIST_ID = "dee211f076"
NO_FIBER_LIST_ID = "80bf1ab411"

# Application Constants
LELAND_ZIP_CODES = ["28451", "28479", "28480", "28481"]  # All Leland ZIP codes
LELAND_REDFIN_URL = "https://www.redfin.com/city/9564/NC/Leland/filter/include=sold-1wk"
WILMINGTON_REDFIN_URL = "https://www.redfin.com/city/18894/NC/Wilmington/filter/include=sold-1wk,viewport=34.2898685:34.124065:-77.7896965:-77.957117"
LUMBERTON_REDFIN_URL = "https://www.redfin.com/city/10113/NC/Lumberton/filter/include=sold-1wk"
HAMPSTEAD_REDFIN_URL = "https://www.redfin.com/city/32836/NC/Hampstead/filter/include=sold-1wk"
SOUTHPORT_REDFIN_URL = "https://www.redfin.com/city/16254/NC/Southport/filter/include=sold-1wk"

# City URLs dictionary
CITY_REDFIN_URLS = {
    "Leland": LELAND_REDFIN_URL,
    "Wilmington": WILMINGTON_REDFIN_URL,
    "Lumberton": LUMBERTON_REDFIN_URL,
    "Hampstead": HAMPSTEAD_REDFIN_URL,
    "Southport": SOUTHPORT_REDFIN_URL
}

# User Agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
]

# API Rate Limiting
RATE_LIMIT = {
    "google_maps": 50,  # requests per minute
    "mailchimp": 10    # requests per minute
}

# Database Configuration
DB_PATH = "fiber_data.db"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = "fiber_tracker.log"

# BatchData API Costs (per request)
BATCHDATA_COSTS = {
    "property_search": 0.01,  # Basic Property Data
    "skip_trace": 0.07,      # Skip Tracing
    "geocoding": 0.0045,     # Geocoding Rooftop
    "address_verification": 0.015  # Address Verification
} 