#!/bin/bash

# Mobile Sales System - Complete Setup
# Starts both Python backend and iOS app

echo "🚀 Mobile Sales System - Complete Setup"
echo "📱 iOS App + Python Backend Integration"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📍 Project Directory: $SCRIPT_DIR"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "🔧 Setting up Python virtual environment..."
    cd "$SCRIPT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed"
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

# Check if database exists
if [ ! -f "$SCRIPT_DIR/mobile_sales.db" ]; then
    echo "🗄️  Initializing database..."
    cd "$SCRIPT_DIR"
    python3 init_database.py
    echo "✅ Database initialized with sample data"
else
    echo "✅ Database found"
fi

echo ""
echo "🚀 Starting Python Backend Server..."
echo "📡 Backend will be available at: http://localhost:5000"
echo ""

# Start the Python backend in the background
cd "$SCRIPT_DIR"
python3 mobile_sales_app.py &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ Python backend is running successfully"
    echo "📊 API endpoints available:"
    echo "   - Houses: http://localhost:5000/api/houses"
    echo "   - Incidents: http://localhost:5000/api/incidents"
    echo "   - Routes: http://localhost:5000/api/routes"
    echo ""
else
    echo "❌ Error: Backend failed to start"
    echo "Check the console output above for errors"
    exit 1
fi

echo "📱 Opening iOS App in Xcode..."
echo ""

# Check if Xcode project exists
if [ -d "$SCRIPT_DIR/MobileSalesApp.xcodeproj" ]; then
    echo "✅ Found Xcode project"
    open "$SCRIPT_DIR/MobileSalesApp.xcodeproj"
    echo "🎉 Xcode should now open with your iOS project"
    echo ""
    echo "📋 Next steps in Xcode:"
    echo "1. Select your target device (iPhone/iPad simulator or physical device)"
    echo "2. Press Cmd+R to build and run the app"
    echo "3. Test the app functionality"
    echo "4. The app will automatically connect to the Python backend"
    echo ""
else
    echo "❌ Error: Xcode project not found"
    echo "Please ensure MobileSalesApp.xcodeproj exists in the project directory"
fi

echo "🔄 System Status:"
echo "   ✅ Python Backend: Running (PID: $BACKEND_PID)"
echo "   ✅ Database: Initialized"
echo "   ✅ iOS App: Ready to build in Xcode"
echo ""
echo "📖 For detailed instructions, see: MOBILE_SALES_README.md"
echo "📖 For iOS-specific instructions, see: IOS_APP_README.md"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Python backend..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ Backend stopped"
    echo "🎉 Mobile Sales System shutdown complete"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

echo "💡 To stop the system, press Ctrl+C"
echo ""

# Keep the script running to maintain the backend
wait $BACKEND_PID
