#!/bin/bash

# Mobile Sales App - iOS Version
# Open in Xcode

echo "🚀 Opening Mobile Sales App in Xcode..."
echo "📱 iOS App for Door-to-Door Sales Management"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Path to the Xcode project
PROJECT_PATH="$SCRIPT_DIR/MobileSalesApp.xcodeproj"

# Check if Xcode project exists
if [ -d "$PROJECT_PATH" ]; then
    echo "✅ Found Xcode project at: $PROJECT_PATH"
    echo ""
    echo "📋 Next steps:"
    echo "1. Xcode will open with the Mobile Sales App project"
    echo "2. Select your target device (iPhone/iPad simulator or physical device)"
    echo "3. Press Cmd+R to build and run the app"
    echo "4. Test the app functionality"
    echo ""
    echo "📖 For detailed instructions, see: IOS_APP_README.md"
    echo ""
    
    # Open the project in Xcode
    open "$PROJECT_PATH"
    
else
    echo "❌ Error: Xcode project not found at: $PROJECT_PATH"
    echo ""
    echo "Please ensure the MobileSalesApp.xcodeproj file exists in the project directory."
    echo ""
    echo "📁 Current directory contents:"
    ls -la "$SCRIPT_DIR"
fi

echo ""
echo "🎉 Happy coding!"
