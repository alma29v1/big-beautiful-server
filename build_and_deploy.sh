#!/bin/bash

echo "🚀 Mobile Sales App - Build & Deploy Script"
echo "============================================"

# Navigate to project directory
cd /Volumes/LaCie/MobileSalesProject

echo "📱 Opening Xcode project..."
open MobileSalesApp.xcodeproj

echo "🧪 Testing server connection..."
curl -H "X-API-Key: MLlhXK3cyJ8_Hnr_kKCP_-uRgv9RuZaKtZyyFl6ZCgw" https://big-beautiful-server.onrender.com/api/health | python3 -m json.tool

echo ""
echo "🎯 Next Steps:"
echo "1. Connect your iPhone via USB"
echo "2. In Xcode, select your iPhone as the destination"
echo "3. Click the Play button (▶️) to build and install"
echo "4. Trust the developer certificate on your iPhone"
echo ""
echo "✅ Your app is ready for deployment!"
