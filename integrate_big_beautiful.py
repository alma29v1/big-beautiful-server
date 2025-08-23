#!/usr/bin/env python3
"""
Data Integration Script - Big Beautiful Program to Mobile Sales App
Imports house data, contact information, and incident data from Big Beautiful Program
"""

import os
import sys
import sqlite3
import pandas as pd
import json
from datetime import datetime
import glob

class BigBeautifulIntegrator:
    def __init__(self, mobile_db_path='mobile_sales.db'):
        self.mobile_db_path = mobile_db_path
        self.big_beautiful_data_dir = '.'  # Current directory where Big Beautiful Program data is
        
    def find_big_beautiful_data(self):
        """Find CSV files and data from Big Beautiful Program"""
        data_files = []
        
        # Look for CSV files in various locations
        csv_patterns = [
            '*.csv',
            'data/*.csv',
            'downloads/*.csv',
            'consolidated/*.csv',
            'att_fiber_tracker/data/*.csv'
        ]
        
        for pattern in csv_patterns:
            files = glob.glob(pattern)
            data_files.extend(files)
        
        return data_files
    
    def import_house_data(self, csv_file):
        """Import house data from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 Processing {len(df)} records from {csv_file}")
            
            conn = sqlite3.connect(self.mobile_db_path)
            cursor = conn.cursor()
            
            # Map CSV columns to database columns
            # This will need to be adjusted based on your actual CSV structure
            column_mapping = {
                'address': ['address', 'Address', 'ADDRESS', 'property_address'],
                'city': ['city', 'City', 'CITY', 'property_city'],
                'state': ['state', 'State', 'STATE', 'property_state'],
                'zip_code': ['zip', 'zip_code', 'ZIP', 'ZIP_CODE', 'property_zip'],
                'sold_date': ['sold_date', 'SoldDate', 'SOLD_DATE', 'date_sold'],
                'price': ['price', 'Price', 'PRICE', 'sale_price'],
                'contact_name': ['contact_name', 'ContactName', 'CONTACT_NAME', 'owner_name'],
                'contact_email': ['contact_email', 'ContactEmail', 'CONTACT_EMAIL', 'email'],
                'contact_phone': ['contact_phone', 'ContactPhone', 'CONTACT_PHONE', 'phone'],
                'fiber_available': ['fiber_available', 'FiberAvailable', 'FIBER_AVAILABLE', 'att_fiber'],
                'adt_detected': ['adt_detected', 'ADTDetected', 'ADT_DETECTED', 'adt_sign']
            }
            
            # Find matching columns in the CSV
            csv_columns = df.columns.tolist()
            mapped_columns = {}
            
            for db_col, possible_csv_cols in column_mapping.items():
                for csv_col in possible_csv_cols:
                    if csv_col in csv_columns:
                        mapped_columns[db_col] = csv_col
                        break
            
            print(f"🔍 Found column mappings: {mapped_columns}")
            
            # Process each row
            imported_count = 0
            for index, row in df.iterrows():
                try:
                    # Extract data using mapped columns
                    house_data = {
                        'address': row.get(mapped_columns.get('address', ''), ''),
                        'city': row.get(mapped_columns.get('city', ''), ''),
                        'state': row.get(mapped_columns.get('state', ''), ''),
                        'zip_code': str(row.get(mapped_columns.get('zip_code', ''), '')),
                        'sold_date': str(row.get(mapped_columns.get('sold_date', ''), '')),
                        'price': float(row.get(mapped_columns.get('price', 0), 0)),
                        'contact_name': row.get(mapped_columns.get('contact_name', ''), ''),
                        'contact_email': row.get(mapped_columns.get('contact_email', ''), ''),
                        'contact_phone': str(row.get(mapped_columns.get('contact_phone', ''), '')),
                        'fiber_available': bool(row.get(mapped_columns.get('fiber_available', False), False)),
                        'adt_detected': bool(row.get(mapped_columns.get('adt_detected', False), False))
                    }
                    
                    # Skip if no address
                    if not house_data['address']:
                        continue
                    
                    # Try to get coordinates (you might need to geocode addresses)
                    # For now, we'll use placeholder coordinates
                    house_data['latitude'] = 34.2257  # Default to Wilmington
                    house_data['longitude'] = -77.9447
                    
                    # Insert into database
                    cursor.execute('''
                        INSERT OR REPLACE INTO houses 
                        (address, city, state, zip_code, latitude, longitude, sold_date, price,
                         contact_name, contact_email, contact_phone, fiber_available, adt_detected)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        house_data['address'], house_data['city'], house_data['state'],
                        house_data['zip_code'], house_data['latitude'], house_data['longitude'],
                        house_data['sold_date'], house_data['price'], house_data['contact_name'],
                        house_data['contact_email'], house_data['contact_phone'],
                        house_data['fiber_available'], house_data['adt_detected']
                    ))
                    
                    imported_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error processing row {index}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully imported {imported_count} houses from {csv_file}")
            return imported_count
            
        except Exception as e:
            print(f"❌ Error importing from {csv_file}: {e}")
            return 0
    
    def import_incident_data(self, incident_file):
        """Import incident data (fires, break-ins, etc.)"""
        try:
            # This would typically come from your incident monitoring system
            # For now, we'll create sample incident data based on house locations
            
            conn = sqlite3.connect(self.mobile_db_path)
            cursor = conn.cursor()
            
            # Get some houses to create incidents for
            cursor.execute("SELECT id, address, latitude, longitude FROM houses LIMIT 5")
            houses = cursor.fetchall()
            
            sample_incidents = [
                ("fire", "House fire reported in neighborhood"),
                ("break-in", "Recent break-in reported"),
                ("flood", "Flood damage reported"),
                ("storm", "Storm damage to property"),
                ("theft", "Package theft reported")
            ]
            
            for i, house in enumerate(houses):
                if i < len(sample_incidents):
                    incident_type, description = sample_incidents[i]
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO incidents 
                        (address, incident_type, description, latitude, longitude, assigned_salesperson_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (house[1], incident_type, description, house[2], house[3], 1))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Created sample incident data")
            
        except Exception as e:
            print(f"❌ Error importing incident data: {e}")
    
    def create_sales_routes(self):
        """Create optimized sales routes based on house locations"""
        try:
            conn = sqlite3.connect(self.mobile_db_path)
            cursor = conn.cursor()
            
            # Get houses grouped by city
            cursor.execute("SELECT city, GROUP_CONCAT(id) as house_ids FROM houses GROUP BY city")
            city_groups = cursor.fetchall()
            
            for i, (city, house_ids_str) in enumerate(city_groups):
                if house_ids_str:
                    house_ids = [int(id) for id in house_ids_str.split(',')]
                    
                    # Create a route for each city
                    route_name = f"{city} Route {i+1}"
                    salesperson_id = (i % 3) + 1  # Assign to different salespeople
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO routes (name, salesperson_id, house_ids)
                        VALUES (?, ?, ?)
                    ''', (route_name, salesperson_id, json.dumps(house_ids)))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Created sales routes for {len(city_groups)} cities")
            
        except Exception as e:
            print(f"❌ Error creating routes: {e}")
    
    def run_full_integration(self):
        """Run the complete integration process"""
        print("🚀 Starting Big Beautiful Program Integration...")
        print("=" * 50)
        
        # Find data files
        data_files = self.find_big_beautiful_data()
        print(f"📁 Found {len(data_files)} data files:")
        for file in data_files:
            print(f"   - {file}")
        
        if not data_files:
            print("⚠️  No data files found. Creating sample data...")
            self.create_sample_data()
        
        # Import house data from each file
        total_imported = 0
        for file in data_files:
            if file.endswith('.csv'):
                imported = self.import_house_data(file)
                total_imported += imported
        
        # Import incident data
        self.import_incident_data(None)
        
        # Create sales routes
        self.create_sales_routes()
        
        # Show summary
        conn = sqlite3.connect(self.mobile_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM houses")
        total_houses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE status = 'active'")
        total_incidents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM routes")
        total_routes = cursor.fetchone()[0]
        
        conn.close()
        
        print("=" * 50)
        print("📊 Integration Summary:")
        print(f"   🏠 Total Houses: {total_houses}")
        print(f"   🚨 Active Incidents: {total_incidents}")
        print(f"   🛣️  Sales Routes: {total_routes}")
        print(f"   ✅ New Houses Imported: {total_imported}")
        print("=" * 50)
        print("🎉 Integration complete! Your mobile sales app is ready to use.")
        print("📱 Access the app at: http://localhost:5000")
    
    def create_sample_data(self):
        """Create sample data if no Big Beautiful Program data is found"""
        print("📝 Creating sample data for demonstration...")
        
        conn = sqlite3.connect(self.mobile_db_path)
        cursor = conn.cursor()
        
        # Sample house data
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
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data created successfully")

def main():
    """Main function to run the integration"""
    integrator = BigBeautifulIntegrator()
    integrator.run_full_integration()

if __name__ == "__main__":
    main()
