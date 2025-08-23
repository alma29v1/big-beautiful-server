#!/usr/bin/env python3
"""
Initialize Mobile Sales App Database
"""

import sqlite3
import json

def init_database():
    """Initialize the database with tables and sample data"""
    conn = sqlite3.connect('mobile_sales.db')
    cursor = conn.cursor()
    
    # Create tables
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            salesperson_id INTEGER,
            house_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (salesperson_id) REFERENCES salespeople (id)
        )
    ''')
    
    # Add sample salespeople
    sample_salespeople = [
        ("Mike Sales", "mike@company.com", "910-555-0201"),
        ("Sarah Closer", "sarah@company.com", "910-555-0202"),
        ("Tom Door", "tom@company.com", "910-555-0203"),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO salespeople (name, email, phone)
        VALUES (?, ?, ?)
    ''', sample_salespeople)
    
    # Add sample houses
    sample_houses = [
        ("123 Main St", "Wilmington", "NC", "28401", 34.2257, -77.9447, "2024-01-15", 250000, "John Smith", "john@email.com", "910-555-0101", True, False),
        ("456 Oak Ave", "Leland", "NC", "28451", 34.2563, -78.0447, "2024-01-16", 275000, "Jane Doe", "jane@email.com", "910-555-0102", False, True),
        ("789 Pine Rd", "Southport", "NC", "28461", 33.9207, -78.0189, "2024-01-17", 300000, "Bob Johnson", "bob@email.com", "910-555-0103", True, False),
        ("321 Elm St", "Wilmington", "NC", "28403", 34.2357, -77.8547, "2024-01-18", 225000, "Alice Brown", "alice@email.com", "910-555-0104", False, True),
        ("654 Maple Dr", "Leland", "NC", "28451", 34.2463, -78.0347, "2024-01-19", 260000, "Charlie Wilson", "charlie@email.com", "910-555-0105", True, False),
        ("987 Cedar Ln", "Wilmington", "NC", "28401", 34.2157, -77.9347, "2024-01-20", 290000, "Diana Davis", "diana@email.com", "910-555-0106", True, False),
        ("147 Birch St", "Southport", "NC", "28461", 33.9307, -78.0289, "2024-01-21", 240000, "Edward Evans", "edward@email.com", "910-555-0107", False, True),
        ("258 Willow Way", "Leland", "NC", "28451", 34.2663, -78.0547, "2024-01-22", 270000, "Fiona Foster", "fiona@email.com", "910-555-0108", True, False),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO houses (address, city, state, zip_code, latitude, longitude, sold_date, price, 
                                      contact_name, contact_email, contact_phone, fiber_available, adt_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_houses)
    
    # Add sample incidents
    sample_incidents = [
        ("123 Main St", "fire", "House fire in neighborhood", 34.2257, -77.9447, 1),
        ("456 Oak Ave", "break-in", "Recent break-in reported", 34.2563, -78.0447, 2),
        ("789 Pine Rd", "flood", "Flood damage reported", 33.9207, -78.0189, 3),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO incidents (address, incident_type, description, latitude, longitude, assigned_salesperson_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_incidents)
    
    # Create sample routes
    cursor.execute("SELECT id FROM houses WHERE city = 'Wilmington'")
    wilmington_houses = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM houses WHERE city = 'Leland'")
    leland_houses = [row[0] for row in cursor.fetchall()]
    
    sample_routes = [
        ("Wilmington Route 1", 1, json.dumps(wilmington_houses[:3])),
        ("Leland Route 1", 2, json.dumps(leland_houses[:2])),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO routes (name, salesperson_id, house_ids)
        VALUES (?, ?, ?)
    ''', sample_routes)
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("📊 Sample data added:")
    print("   - 8 houses")
    print("   - 3 salespeople")
    print("   - 3 incidents")
    print("   - 2 routes")

if __name__ == "__main__":
    init_database()
