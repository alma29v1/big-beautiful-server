"""
AT&T Fiber Tracker Version Information
"""

__version__ = "2.1.0"
__build_date__ = "2025-07-08"
__author__ = "AT&T Fiber Tracker Team"

# Version history:
# 2.1.0 - Enhanced Google Cloud backup with versioning and smart retention
# 2.0.0 - Integrated Settings tab with backup configuration
# 1.5.0 - Added Google Cloud backup functionality
# 1.0.0 - Initial release with core AT&T fiber tracking features

def get_version_info():
    """Get detailed version information"""
    return {
        'version': __version__,
        'build_date': __build_date__,
        'author': __author__
    }

if __name__ == "__main__":
    print(f"AT&T Fiber Tracker v{__version__}")
    print(f"Build Date: {__build_date__}")
    print(f"Author: {__author__}") 