#!/usr/bin/env python3
"""
Mobile Sales App - Door-to-Door Sales Management System
Integrates with Big Beautiful Program data for interactive mapping and route planning
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import threading
import time

app = Flask(__name__)
CORS(app)

# Database setup
DB_PATH = 'mobile_sales.db'

class MobileSalesApp:
    def __init__(self):
        self.setup_database()
        self.geolocator = Nominatim(user_agent="mobile_sales_app")

    def setup_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Houses table (from Big Beautiful Program)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS houses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                latitude REAL,
                longitude REAL,
                sold_date TEXT,
                price REAL,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                fiber_available BOOLEAN DEFAULT FALSE,
                adt_detected BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Sales visits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                house_id INTEGER,
                salesperson_id INTEGER,
                visit_date TIMESTAMP,
                status TEXT,
                notes TEXT,
                follow_up_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (house_id) REFERENCES houses (id)
            )
        ''')

        # Salespeople table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salespeople (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                incident_type TEXT,
                description TEXT,
                latitude REAL,
                longitude REAL,
                assigned_salesperson_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_salesperson_id) REFERENCES salespeople (id)
            )
        ''')

        # Routes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                salesperson_id INTEGER,
                house_ids TEXT,  -- JSON array of house IDs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salesperson_id) REFERENCES salespeople (id)
            )
        ''')

        conn.commit()
        conn.close()

        # Add sample data if database is empty
        self.add_sample_data()

    def add_sample_data(self):
        """Add sample data for testing"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM houses")
        if cursor.fetchone()[0] == 0:
            # Add sample houses
            sample_houses = [
                ("123 Main St", "Wilmington", "NC", "28401", 34.2257, -77.9447, "2024-01-15", 250000, "John Smith", "john@email.com", "910-555-0101", True, False),
                ("456 Oak Ave", "Leland", "NC", "28451", 34.2563, -78.0447, "2024-01-16", 275000, "Jane Doe", "jane@email.com", "910-555-0102", False, True),
                ("789 Pine Rd", "Southport", "NC", "28461", 33.9207, -78.0189, "2024-01-17", 300000, "Bob Johnson", "bob@email.com", "910-555-0103", True, False),
                ("321 Elm St", "Wilmington", "NC", "28403", 34.2357, -77.8547, "2024-01-18", 225000, "Alice Brown", "alice@email.com", "910-555-0104", False, True),
                ("654 Maple Dr", "Leland", "NC", "28451", 34.2463, -78.0347, "2024-01-19", 260000, "Charlie Wilson", "charlie@email.com", "910-555-0105", True, False),
            ]

            cursor.executemany('''
                INSERT INTO houses (address, city, state, zip_code, latitude, longitude, sold_date, price,
                                  contact_name, contact_email, contact_phone, fiber_available, adt_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_houses)

            # Add sample salespeople
            sample_salespeople = [
                ("Mike Sales", "mike@company.com", "910-555-0201"),
                ("Sarah Closer", "sarah@company.com", "910-555-0202"),
                ("Tom Door", "tom@company.com", "910-555-0203"),
            ]

            cursor.executemany('''
                INSERT INTO salespeople (name, email, phone)
                VALUES (?, ?, ?)
            ''', sample_salespeople)

            # Add sample incidents
            sample_incidents = [
                ("123 Main St", "fire", "House fire in neighborhood", 34.2257, -77.9447, 1),
                ("456 Oak Ave", "break-in", "Recent break-in reported", 34.2563, -78.0447, 2),
            ]

            cursor.executemany('''
                INSERT INTO incidents (address, incident_type, description, latitude, longitude, assigned_salesperson_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', sample_incidents)

            conn.commit()

        conn.close()

# Initialize the app
sales_app = MobileSalesApp()

@app.route('/')
def index():
    """Main mobile interface"""
    return render_template('mobile_index.html')

@app.route('/api/houses')
def get_houses():
    """Get all houses with optional filters"""
    status = request.args.get('status', 'all')
    city = request.args.get('city', 'all')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM houses WHERE 1=1"
    params = []

    if status != 'all':
        query += " AND status = ?"
        params.append(status)

    if city != 'all':
        query += " AND city = ?"
        params.append(city)

    cursor.execute(query, params)
    houses = cursor.fetchall()

    # Convert to list of dictionaries
    columns = [description[0] for description in cursor.description]
    houses_data = []
    for house in houses:
        house_dict = dict(zip(columns, house))
        houses_data.append(house_dict)

    conn.close()
    return jsonify(houses_data)

@app.route('/api/houses/<int:house_id>', methods=['GET', 'PUT'])
def house_detail(house_id):
    """Get or update house details"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()

        if house:
            columns = [description[0] for description in cursor.description]
            house_dict = dict(zip(columns, house))
            conn.close()
            return jsonify(house_dict)
        else:
            conn.close()
            return jsonify({"error": "House not found"}), 404

    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE houses
            SET status = ?, notes = ?
            WHERE id = ?
        ''', (data.get('status'), data.get('notes'), house_id))

        conn.commit()
        conn.close()
        return jsonify({"message": "House updated successfully"})

@app.route('/api/incidents')
def get_incidents():
    """Get all active incidents"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT i.*, s.name as salesperson_name
        FROM incidents i
        LEFT JOIN salespeople s ON i.assigned_salesperson_id = s.id
        WHERE i.status = 'active'
    ''')

    incidents = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    incidents_data = []
    for incident in incidents:
        incident_dict = dict(zip(columns, incident))
        incidents_data.append(incident_dict)

    conn.close()
    return jsonify(incidents_data)

@app.route('/api/routes', methods=['GET', 'POST'])
def routes():
    """Get or create routes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('''
            SELECT r.*, s.name as salesperson_name
            FROM routes r
            LEFT JOIN salespeople s ON r.salesperson_id = s.id
        ''')

        routes = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        routes_data = []
        for route in routes:
            route_dict = dict(zip(columns, route))
            routes_data.append(route_dict)

        conn.close()
        return jsonify(routes_data)

    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO routes (name, salesperson_id, house_ids)
            VALUES (?, ?, ?)
        ''', (data['name'], data['salesperson_id'], json.dumps(data['house_ids'])))

        conn.commit()
        conn.close()
        return jsonify({"message": "Route created successfully"})

@app.route('/api/salespeople')
def get_salespeople():
    """Get all active salespeople"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM salespeople WHERE active = 1")
    salespeople = cursor.fetchall()

    columns = [description[0] for description in cursor.description]
    salespeople_data = []
    for person in salespeople:
        person_dict = dict(zip(columns, person))
        salespeople_data.append(person_dict)

    conn.close()
    return jsonify(salespeople_data)

@app.route('/api/visits', methods=['POST'])
def create_visit():
    """Create a new sales visit"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO sales_visits (house_id, salesperson_id, visit_date, status, notes, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['house_id'], data['salesperson_id'], data['visit_date'],
          data['status'], data['notes'], data.get('follow_up_date')))

    conn.commit()
    conn.close()
    return jsonify({"message": "Visit created successfully"})

@app.route('/api/map')
def get_map_data():
    """Get map data for all houses and incidents"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get houses
    cursor.execute("SELECT id, address, latitude, longitude, status, fiber_available, adt_detected FROM houses")
    houses = cursor.fetchall()

    # Get incidents
    cursor.execute("SELECT id, address, latitude, longitude, incident_type FROM incidents WHERE status = 'active'")
    incidents = cursor.fetchall()

    conn.close()

    return jsonify({
        "houses": [{"id": h[0], "address": h[1], "lat": h[2], "lng": h[3],
                   "status": h[4], "fiber": h[5], "adt": h[6]} for h in houses],
        "incidents": [{"id": i[0], "address": i[1], "lat": i[2], "lng": i[3],
                      "type": i[4]} for i in incidents]
    })

@app.route('/api/import_from_big_beautiful', methods=['POST'])
def import_from_big_beautiful():
    """Import data from Big Beautiful Program"""
    # This would integrate with your existing Big Beautiful Program
    # For now, we'll simulate importing data

    # You would typically:
    # 1. Read CSV files from your Big Beautiful Program
    # 2. Process the data
    # 3. Insert into the mobile app database

    sample_import_data = [
        ("999 New House St", "Wilmington", "NC", "28401", 34.2157, -77.9347,
         "2024-01-20", 280000, "New Customer", "new@email.com", "910-555-9999", True, False),
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for house_data in sample_import_data:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO houses (address, city, state, zip_code, latitude, longitude,
                                            sold_date, price, contact_name, contact_email,
                                            contact_phone, fiber_available, adt_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', house_data)
        except sqlite3.IntegrityError:
            pass  # Address already exists

    conn.commit()
    conn.close()

    return jsonify({"message": "Data imported successfully"})

def create_mobile_template():
    """Create the mobile HTML template"""
    template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Sales App</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }

        .header p {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .nav-tabs {
            display: flex;
            background: white;
            border-bottom: 1px solid #ddd;
        }

        .nav-tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            background: white;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
        }

        .nav-tab.active {
            background: #667eea;
            color: white;
        }

        .tab-content {
            display: none;
            padding: 20px;
        }

        .tab-content.active {
            display: block;
        }

        #map {
            height: 400px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .house-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .house-card h3 {
            color: #333;
            margin-bottom: 10px;
        }

        .house-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }

        .info-item {
            font-size: 0.9rem;
        }

        .info-label {
            color: #666;
            font-weight: 500;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .status-new { background: #e3f2fd; color: #1976d2; }
        .status-contacted { background: #fff3e0; color: #f57c00; }
        .status-interested { background: #e8f5e8; color: #388e3c; }
        .status-closed { background: #fce4ec; color: #c2185b; }

        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .btn {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-success {
            background: #28a745;
            color: white;
        }

        .btn:hover {
            opacity: 0.8;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }

        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 500px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .incident-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .incident-type {
            font-weight: bold;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚪 Mobile Sales App</h1>
        <p>Door-to-Door Sales Management</p>
    </div>

    <div class="nav-tabs">
        <button class="nav-tab active" onclick="showTab('map')">🗺️ Map</button>
        <button class="nav-tab" onclick="showTab('houses')">🏠 Houses</button>
        <button class="nav-tab" onclick="showTab('incidents')">🚨 Incidents</button>
        <button class="nav-tab" onclick="showTab('routes')">🛣️ Routes</button>
    </div>

    <!-- Map Tab -->
    <div id="map-tab" class="tab-content active">
        <div id="map"></div>
        <div class="action-buttons">
            <button class="btn btn-primary" onclick="createRoute()">Create Route</button>
            <button class="btn btn-secondary" onclick="refreshMap()">Refresh</button>
        </div>
    </div>

    <!-- Houses Tab -->
    <div id="houses-tab" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-houses">0</div>
                <div class="stat-label">Total Houses</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="new-houses">0</div>
                <div class="stat-label">New Leads</div>
            </div>
        </div>
        <div id="houses-list"></div>
    </div>

    <!-- Incidents Tab -->
    <div id="incidents-tab" class="tab-content">
        <div id="incidents-list"></div>
    </div>

    <!-- Routes Tab -->
    <div id="routes-tab" class="tab-content">
        <div class="action-buttons">
            <button class="btn btn-primary" onclick="showCreateRouteModal()">Create New Route</button>
        </div>
        <div id="routes-list"></div>
    </div>

    <!-- House Detail Modal -->
    <div id="house-modal" class="modal">
        <div class="modal-content">
            <h2>House Details</h2>
            <div id="house-detail-content"></div>
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="updateHouse()">Update</button>
                <button class="btn btn-secondary" onclick="closeModal('house-modal')">Close</button>
            </div>
        </div>
    </div>

    <!-- Visit Modal -->
    <div id="visit-modal" class="modal">
        <div class="modal-content">
            <h2>Record Visit</h2>
            <form id="visit-form">
                <div class="form-group">
                    <label>Salesperson:</label>
                    <select id="visit-salesperson" required>
                        <option value="">Select salesperson...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Status:</label>
                    <select id="visit-status" required>
                        <option value="contacted">Contacted</option>
                        <option value="interested">Interested</option>
                        <option value="not-interested">Not Interested</option>
                        <option value="follow-up">Follow Up</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Notes:</label>
                    <textarea id="visit-notes" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>Follow Up Date:</label>
                    <input type="date" id="visit-followup">
                </div>
                <div class="action-buttons">
                    <button type="submit" class="btn btn-success">Save Visit</button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('visit-modal')">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let map;
        let houses = [];
        let incidents = [];
        let currentHouseId = null;

        // Initialize the app
        document.addEventListener('DOMContentLoaded', function() {
            initMap();
            loadData();
            loadSalespeople();
        });

        function initMap() {
            // Initialize map centered on Wilmington, NC
            map = L.map('map').setView([34.2257, -77.9447], 12);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
        }

        function loadData() {
            // Load houses
            fetch('/api/houses')
                .then(response => response.json())
                .then(data => {
                    houses = data;
                    updateMap();
                    updateHousesList();
                    updateStats();
                });

            // Load incidents
            fetch('/api/incidents')
                .then(response => response.json())
                .then(data => {
                    incidents = data;
                    updateIncidentsList();
                });

            // Load routes
            fetch('/api/routes')
                .then(response => response.json())
                .then(data => {
                    updateRoutesList(data);
                });
        }

        function loadSalespeople() {
            fetch('/api/salespeople')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('visit-salesperson');
                    select.innerHTML = '<option value="">Select salesperson...</option>';
                    data.forEach(person => {
                        select.innerHTML += `<option value="${person.id}">${person.name}</option>`;
                    });
                });
        }

        function updateMap() {
            // Clear existing markers
            map.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    map.removeLayer(layer);
                }
            });

            // Add house markers
            houses.forEach(house => {
                if (house.latitude && house.longitude) {
                    const color = getStatusColor(house.status);
                    const icon = L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
                        iconSize: [20, 20]
                    });

                    const marker = L.marker([house.latitude, house.longitude], {icon: icon})
                        .addTo(map)
                        .bindPopup(`
                            <strong>${house.address}</strong><br>
                            Status: ${house.status}<br>
                            Fiber: ${house.fiber_available ? 'Yes' : 'No'}<br>
                            ADT: ${house.adt_detected ? 'Yes' : 'No'}<br>
                            <button onclick="showHouseDetail(${house.id})">View Details</button>
                        `);
                }
            });

            // Add incident markers
            incidents.forEach(incident => {
                if (incident.latitude && incident.longitude) {
                    const icon = L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background: #ff4444; width: 25px; height: 25px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">!</div>`,
                        iconSize: [25, 25]
                    });

                    const marker = L.marker([incident.latitude, incident.longitude], {icon: icon})
                        .addTo(map)
                        .bindPopup(`
                            <strong>🚨 Incident</strong><br>
                            ${incident.address}<br>
                            Type: ${incident.incident_type}<br>
                            ${incident.description}
                        `);
                }
            });
        }

        function getStatusColor(status) {
            const colors = {
                'new': '#28a745',
                'contacted': '#ffc107',
                'interested': '#17a2b8',
                'closed': '#dc3545'
            };
            return colors[status] || '#6c757d';
        }

        function updateHousesList() {
            const container = document.getElementById('houses-list');
            container.innerHTML = '';

            houses.forEach(house => {
                const card = document.createElement('div');
                card.className = 'house-card';
                card.innerHTML = `
                    <h3>${house.address}</h3>
                    <div class="house-info">
                        <div class="info-item">
                            <span class="info-label">Status:</span>
                            <span class="status-badge status-${house.status}">${house.status}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Fiber:</span>
                            <span>${house.fiber_available ? '✅' : '❌'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">ADT:</span>
                            <span>${house.adt_detected ? '✅' : '❌'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Contact:</span>
                            <span>${house.contact_name || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="action-buttons">
                        <button class="btn btn-primary" onclick="showHouseDetail(${house.id})">Details</button>
                        <button class="btn btn-success" onclick="showVisitModal(${house.id})">Record Visit</button>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateIncidentsList() {
            const container = document.getElementById('incidents-list');
            container.innerHTML = '';

            incidents.forEach(incident => {
                const card = document.createElement('div');
                card.className = 'incident-card';
                card.innerHTML = `
                    <div class="incident-type">🚨 ${incident.incident_type.toUpperCase()}</div>
                    <div><strong>${incident.address}</strong></div>
                    <div>${incident.description}</div>
                    <div style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                        Assigned: ${incident.salesperson_name || 'Unassigned'}
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateRoutesList(routes) {
            const container = document.getElementById('routes-list');
            container.innerHTML = '';

            routes.forEach(route => {
                const card = document.createElement('div');
                card.className = 'house-card';
                card.innerHTML = `
                    <h3>${route.name}</h3>
                    <div class="house-info">
                        <div class="info-item">
                            <span class="info-label">Salesperson:</span>
                            <span>${route.salesperson_name || 'Unassigned'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Houses:</span>
                            <span>${JSON.parse(route.house_ids || '[]').length}</span>
                        </div>
                    </div>
                    <div class="action-buttons">
                        <button class="btn btn-primary" onclick="viewRoute(${route.id})">View Route</button>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateStats() {
            document.getElementById('total-houses').textContent = houses.length;
            const newHouses = houses.filter(h => h.status === 'new').length;
            document.getElementById('new-houses').textContent = newHouses;
        }

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');

            // Refresh map if showing map tab
            if (tabName === 'map') {
                setTimeout(() => map.invalidateSize(), 100);
            }
        }

        function showHouseDetail(houseId) {
            const house = houses.find(h => h.id === houseId);
            if (!house) return;

            const content = document.getElementById('house-detail-content');
            content.innerHTML = `
                <div class="form-group">
                    <label>Address:</label>
                    <input type="text" id="house-address" value="${house.address}" readonly>
                </div>
                <div class="form-group">
                    <label>Status:</label>
                    <select id="house-status">
                        <option value="new" ${house.status === 'new' ? 'selected' : ''}>New</option>
                        <option value="contacted" ${house.status === 'contacted' ? 'selected' : ''}>Contacted</option>
                        <option value="interested" ${house.status === 'interested' ? 'selected' : ''}>Interested</option>
                        <option value="closed" ${house.status === 'closed' ? 'selected' : ''}>Closed</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Notes:</label>
                    <textarea id="house-notes" rows="3">${house.notes || ''}</textarea>
                </div>
            `;

            currentHouseId = houseId;
            document.getElementById('house-modal').style.display = 'block';
        }

        function showVisitModal(houseId) {
            currentHouseId = houseId;
            document.getElementById('visit-modal').style.display = 'block';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        function updateHouse() {
            const status = document.getElementById('house-status').value;
            const notes = document.getElementById('house-notes').value;

            fetch(`/api/houses/${currentHouseId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status, notes })
            })
            .then(response => response.json())
            .then(data => {
                closeModal('house-modal');
                loadData(); // Refresh data
            });
        }

        document.getElementById('visit-form').addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = {
                house_id: currentHouseId,
                salesperson_id: document.getElementById('visit-salesperson').value,
                visit_date: new Date().toISOString(),
                status: document.getElementById('visit-status').value,
                notes: document.getElementById('visit-notes').value,
                follow_up_date: document.getElementById('visit-followup').value
            };

            fetch('/api/visits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                closeModal('visit-modal');
                loadData(); // Refresh data
            });
        });

        function refreshMap() {
            loadData();
        }

        function createRoute() {
            // Simple route creation - in a real app, you'd have more sophisticated routing
            alert('Route creation feature would integrate with mapping APIs for optimal routing');
        }

        function showCreateRouteModal() {
            alert('Route creation modal would allow selecting houses and salesperson');
        }

        function viewRoute(routeId) {
            alert('Route viewer would show the route on the map with turn-by-turn directions');
        }

        // Close modals when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }
    </script>
</body>
</html>
    '''

    with open('templates/mobile_index.html', 'w') as f:
        f.write(template_content)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Create the mobile interface template
    create_mobile_template()

    print("🚀 Mobile Sales App starting...")
    print("📱 Access the app at: http://localhost:5001")
    print("🗺️  Interactive map for door-to-door sales")
    print("📊 Integrates with Big Beautiful Program data")

    app.run(debug=True, host='0.0.0.0', port=5001)
