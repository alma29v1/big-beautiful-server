#!/bin/bash

echo "🚀 Starting Big Beautiful Program API Server..."
echo ""

# Navigate to the Big Beautiful Program directory
cd /Volumes/LaCie/the_big_beautiful_program

# Check if virtual environment exists
if [ ! -d "companion_app_env" ]; then
    echo "❌ Virtual environment not found. Please run the setup first."
    echo "   Expected location: /Volumes/LaCie/the_big_beautiful_program/companion_app_env"
    exit 1
fi

# Activate virtual environment and start the API server
echo "✅ Activating virtual environment..."
source companion_app_env/bin/activate

echo "✅ Starting API server on port 5001..."
echo "📱 Your iOS app will connect to: http://localhost:5001/api"
echo "🔑 API Key: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server
python api_setup_for_companion_app.py
