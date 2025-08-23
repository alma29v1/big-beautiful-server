"""Main entry point for the AT&T Fiber Tracker application."""

import logging
import sys
from .app import FiberTrackerApp
from .config import LOG_LEVEL, LOG_FILE

def main():
    """Run the AT&T Fiber Tracker application."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting AT&T Fiber Tracker application...")
    
    try:
        app = FiberTrackerApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 