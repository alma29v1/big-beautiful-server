#!/usr/bin/env python3
"""
Uptime Monitor for Big Beautiful Server
Keeps the server alive and monitors health
"""

import requests
import time
import datetime
import sys

# Server configuration
SERVER_URL = "https://big-beautiful-server.onrender.com"
PING_INTERVAL = 300  # 5 minutes
API_KEY = "MLlhXK3cyJ8_Hnr_kKCP_-uRgv9RuZaKtZyyFl6ZCgw"

def ping_server():
    """Ping the server to keep it alive"""
    try:
        response = requests.get(f"{SERVER_URL}/ping", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Server alive: {data.get('status')}")
            return True
        else:
            print(f"⚠️  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Server ping failed: {e}")
        return False

def check_health():
    """Check server health"""
    try:
        response = requests.get(f"{SERVER_URL}/api/health", 
                              headers={"X-API-Key": API_KEY}, 
                              timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Health check: {data.get('status')} - API Key: {data.get('api_key_configured')}")
            return True
        else:
            print(f"🚨 Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"🚨 Health check error: {e}")
        return False

def monitor_uptime():
    """Main monitoring loop"""
    print(f"🚀 Starting uptime monitor for {SERVER_URL}")
    print(f"⏰ Ping interval: {PING_INTERVAL} seconds")
    print("=" * 60)
    
    while True:
        try:
            # Ping to keep alive
            ping_success = ping_server()
            
            # Health check every few pings
            if ping_success:
                health_success = check_health()
                if not health_success:
                    print("🔄 Health check failed, but server is responding")
            
            # Wait for next ping
            time.sleep(PING_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⏹️  Monitor stopped by user")
            break
        except Exception as e:
            print(f"💥 Monitor error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    monitor_uptime()
