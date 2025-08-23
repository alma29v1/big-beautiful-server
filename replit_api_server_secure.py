#!/usr/bin/env python3
"""
Big Beautiful Program API Server for Replit.com - SECURE VERSION
This provides a cloud-hosted version of the API for the iPhone app
NO HARDCODED API KEYS - All keys must be set in environment variables
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import sqlite3
from datetime import datetime
import requests
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration - ALL KEYS MUST BE SET IN ENVIRONMENT VARIABLES
API_KEY = os.getenv('MOBILE_APP_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Validate required environment variables
if not API_KEY:
    print("❌ ERROR: MOBILE_APP_API_KEY environment variable is required!")
    print("💡 Set it in Replit Secrets tab")
    exit(1)

print(f"✅ API Key loaded: {API_KEY[:8]}...")
if GOOGLE_API_KEY:
    print(f"✅ Google API Key loaded: {GOOGLE_API_KEY[:8]}...")
else:
    print("⚠️  Google API Key not set - geocoding will be disabled")

# Database setup (using SQLite for Replit)
DATABASE_PATH = '/tmp/big_beautiful_api.db'

def init_database():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            owner_email TEXT,
            owner_phone TEXT,
            fiber_available BOOLEAN DEFAULT FALSE,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'mobile_app'
        )
    ''')

    # Create analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_contacts INTEGER DEFAULT 0,
            fiber_contacts INTEGER DEFAULT 0,
            recent_contacts INTEGER DEFAULT 0,
            conversion_rate REAL DEFAULT 0.0,
            weekly_growth REAL DEFAULT 0.0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Authentication decorator
def require_api_key(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'server': 'replit-cloud-secure',
        'api_key_configured': bool(API_KEY),
        'google_api_configured': bool(GOOGLE_API_KEY)
    })

@app.route('/api/contacts', methods=['GET'])
@require_api_key
def get_contacts():
    """Get all contacts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contacts ORDER BY created_date DESC')
        contacts = cursor.fetchall()

        contacts_list = []
        for contact in contacts:
            contacts_list.append({
                'id': contact['id'],
                'address': contact['address'],
                'city': contact['city'],
                'state': contact['state'],
                'zip_code': contact['zip_code'],
                'owner_name': contact['owner_name'],
                'owner_email': contact['owner_email'],
                'owner_phone': contact['owner_phone'],
                'fiber_available': bool(contact['fiber_available']),
                'created_date': contact['created_date'],
                'source': contact['source']
            })

        conn.close()
        return jsonify({
            'contacts': contacts_list,
            'total': len(contacts_list),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['GET'])
@require_api_key
def get_contact(contact_id):
    """Get specific contact"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
        contact = cursor.fetchone()

        if not contact:
            return jsonify({'error': 'Contact not found'}), 404

        contact_data = {
            'id': contact['id'],
            'address': contact['address'],
            'city': contact['city'],
            'state': contact['state'],
            'zip_code': contact['zip_code'],
            'owner_name': contact['owner_name'],
            'owner_email': contact['owner_email'],
            'owner_phone': contact['owner_phone'],
            'fiber_available': bool(contact['fiber_available']),
            'created_date': contact['created_date'],
            'source': contact['source']
        }

        conn.close()
        return jsonify(contact_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
@require_api_key
def create_contact():
    """Create new contact"""
    try:
        data = request.get_json()

        required_fields = ['address', 'city', 'state', 'zip_code', 'owner_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO contacts (address, city, state, zip_code, owner_name, owner_email, owner_phone, fiber_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['address'],
            data['city'],
            data['state'],
            data['zip_code'],
            data['owner_name'],
            data.get('owner_email', ''),
            data.get('owner_phone', ''),
            data.get('fiber_available', False)
        ))

        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'id': contact_id,
            'address': data['address'],
            'city': data['city'],
            'state': data['state'],
            'zip_code': data['zip_code'],
            'owner_name': data['owner_name'],
            'owner_email': data.get('owner_email', ''),
            'owner_phone': data.get('owner_phone', ''),
            'fiber_available': data.get('fiber_available', False),
            'created_date': datetime.now().isoformat(),
            'source': 'mobile_app'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/geocode', methods=['POST'])
@require_api_key
def geocode_address():
    """Geocode an address using Google Maps API"""
    if not GOOGLE_API_KEY:
        return jsonify({
            'error': 'Google API key not configured',
            'success': False
        }), 503

    try:
        data = request.get_json()
        address = data.get('address')

        if not address:
            return jsonify({'error': 'Address is required'}), 400

        # Use Google Maps Geocoding API
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': GOOGLE_API_KEY
        }

        response = requests.get(url, params=params)
        result = response.json()

        if result['status'] == 'OK' and result['results']:
            location = result['results'][0]['geometry']['location']
            return jsonify({
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': result['results'][0]['formatted_address'],
                'success': True
            })
        else:
            return jsonify({
                'error': f"Geocoding failed: {result.get('status', 'Unknown error')}",
                'success': False
            }), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/att-fiber-check', methods=['POST'])
@require_api_key
def check_att_fiber():
    """Check AT&T Fiber availability for an address"""
    try:
        data = request.get_json()
        address = data.get('address')

        if not address:
            return jsonify({'error': 'Address is required'}), 400

        # Simulate AT&T Fiber check (replace with actual API call)
        # For now, return mock data
        import random
        fiber_available = random.choice([True, False])

        return jsonify({
            'address': address,
            'fiber_available': fiber_available,
            'speed_tiers': ['100 Mbps', '300 Mbps', '1 Gbps'] if fiber_available else [],
            'installation_date': None,
            'status': 'available' if fiber_available else 'unavailable',
            'estimated_installation_time': '2-4 weeks' if fiber_available else None,
            'promotional_offers': [
                {
                    'speed': '1 Gbps',
                    'price': '$80/month',
                    'term': '12 months'
                }
            ] if fiber_available else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
@require_api_key
def get_analytics():
    """Get analytics data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total contacts
        cursor.execute('SELECT COUNT(*) as total FROM contacts')
        total_contacts = cursor.fetchone()['total']

        # Get fiber contacts
        cursor.execute('SELECT COUNT(*) as fiber_count FROM contacts WHERE fiber_available = 1')
        fiber_contacts = cursor.fetchone()['fiber_count']

        # Get recent contacts (last 7 days)
        cursor.execute('''
            SELECT COUNT(*) as recent_count FROM contacts
            WHERE created_date >= datetime('now', '-7 days')
        ''')
        recent_contacts = cursor.fetchone()['recent_count']

        # Calculate conversion rate (mock data for now)
        conversion_rate = 15.5  # 15.5%
        weekly_growth = 8.2     # 8.2%

        # Get top cities
        cursor.execute('''
            SELECT city, COUNT(*) as count
            FROM contacts
            GROUP BY city
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_cities = [{'city': row['city'], 'count': row['count']} for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'total_contacts': total_contacts,
            'fiber_contacts': fiber_contacts,
            'recent_contacts': recent_contacts,
            'conversion_rate': conversion_rate,
            'weekly_growth': weekly_growth,
            'top_cities': top_cities,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
@require_api_key
def sync_data():
    """Sync data endpoint"""
    try:
        # This would sync with your main Big Beautiful Program
        # For now, return success status
        return jsonify({
            'status': 'synced',
            'timestamp': datetime.now().isoformat(),
            'message': 'Data synchronized successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rolling-sales', methods=['GET'])
@require_api_key
def get_rolling_sales():
    """Get rolling weekly sales data"""
    try:
        # Mock rolling sales data
        return jsonify({
            'weekly_sales': [
                {'week': '2024-01-01', 'sales': 12, 'revenue': 24000},
                {'week': '2024-01-08', 'sales': 15, 'revenue': 30000},
                {'week': '2024-01-15', 'sales': 18, 'revenue': 36000},
                {'week': '2024-01-22', 'sales': 14, 'revenue': 28000}
            ],
            'total_sales': 59,
            'total_revenue': 118000,
            'average_per_week': 14.75
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rolling-sales/export', methods=['GET'])
@require_api_key
def export_rolling_sales():
    """Export rolling sales for AI email"""
    try:
        # Mock export data
        return jsonify({
            'export_data': {
                'format': 'csv',
                'data': [
                    'Week,Sales,Revenue',
                    '2024-01-01,12,24000',
                    '2024-01-08,15,30000',
                    '2024-01-15,18,36000',
                    '2024-01-22,14,28000'
                ],
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Handle HTTP exceptions"""
    return jsonify({
        'error': e.description,
        'code': e.code
    }), e.code

@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handle general exceptions"""
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

if __name__ == '__main__':
    # Initialize database
    init_database()

    print("🚀 Big Beautiful Program API Server for Replit - SECURE VERSION")
    print("🔒 NO HARDCODED API KEYS - All keys must be set in environment variables")
    print("📱 Available endpoints:")
    print("   GET  /api/health - Health check")
    print("   GET  /api/contacts - Get contacts")
    print("   GET  /api/contacts/<id> - Get specific contact")
    print("   POST /api/contacts - Create new contact")
    print("   POST /api/geocode - Geocode address")
    print("   POST /api/att-fiber-check - Check AT&T Fiber")
    print("   GET  /api/analytics - Get analytics")
    print("   POST /api/sync - Sync data")
    print("   GET  /api/rolling-sales - Get rolling weekly sales")
    print("   GET  /api/rolling-sales/export - Export for AI email")
    print("🔑 API Key Required: X-API-Key header")
    print("🌐 Server will be available at your Replit URL")
    print("⚠️  IMPORTANT: Set MOBILE_APP_API_KEY in Replit Secrets!")

    # Run the app (Replit will handle the port)
    app.run(host='0.0.0.0', port=8080, debug=False)
