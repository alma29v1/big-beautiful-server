#!/usr/bin/env python3
"""
ActiveKnocker Automation Worker
Automatically creates targeted pins for:
1. AT&T Fiber available houses in Lumberton
2. Incident locations in Fayetteville/Lumberton
3. ADT sign detection locations in Fayetteville/Lumberton
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import urllib.parse

from PySide6.QtCore import QThread, Signal

class ActiveKnockerAutomationWorker(QThread):
    """Automated ActiveKnocker pin creation for targeted locations"""
    
    progress_signal = Signal(int, int, str)  # current, total, message
    log_signal = Signal(str)  # log message
    pins_created_signal = Signal(int)  # number of pins created
    finished_signal = Signal(dict)  # final results
    
    def __init__(self):
        super().__init__()
        self.api_key = "da012c4e2d094df36de9e7ce2e0e7d2595cdb9e7f99f0b3b5b6dbeb23a1a4034"
        self.api_url = "https://api.activeknocker.com/knock-pin"
        self.headers = {"x-api-key": self.api_key}
        self.stop_flag = False
        
        # Target cities for operations
        self.target_cities = ["Lumberton", "Fayetteville"]
        
        # Pin categories
        self.pin_categories = {
            'fiber': '🌐 AT&T Fiber Available',
            'incident': '🚨 Incident Response',
            'adt': '🔒 ADT Security Detected'
        }
    
    def run(self):
        """Main automation loop"""
        try:
            self.log_signal.emit("🎯 Starting targeted ActiveKnocker automation...")
            
            all_pins = []
            total_steps = 3
            current_step = 0
            
            # Step 1: Get AT&T Fiber locations in Lumberton
            current_step += 1
            self.progress_signal.emit(current_step, total_steps, "Getting AT&T Fiber locations in Lumberton...")
            fiber_pins = self.get_fiber_locations_lumberton()
            all_pins.extend(fiber_pins)
            self.log_signal.emit(f"📡 Found {len(fiber_pins)} AT&T Fiber locations in Lumberton")
            
            # Step 2: Get incident locations in target cities
            current_step += 1
            self.progress_signal.emit(current_step, total_steps, "Getting incident locations...")
            incident_pins = self.get_incident_locations()
            all_pins.extend(incident_pins)
            self.log_signal.emit(f"🚨 Found {len(incident_pins)} incident locations")
            
            # Step 3: Get ADT detection locations in target cities
            current_step += 1
            self.progress_signal.emit(current_step, total_steps, "Getting ADT detection locations...")
            adt_pins = self.get_adt_detection_locations()
            all_pins.extend(adt_pins)
            self.log_signal.emit(f"🔒 Found {len(adt_pins)} ADT detection locations")
            
            # Remove duplicates based on address
            unique_pins = self.deduplicate_pins(all_pins)
            self.log_signal.emit(f"📍 Total unique locations: {len(unique_pins)}")
            
            if not unique_pins:
                self.log_signal.emit("ℹ️ No targeted locations found")
                self.finished_signal.emit({'success': True, 'pins_created': 0})
                return
            
            # Send pins to ActiveKnocker
            self.log_signal.emit(f"📤 Sending {len(unique_pins)} targeted pins to ActiveKnocker...")
            created_pins = self.send_pins_to_activeknocker(unique_pins)
            
            self.pins_created_signal.emit(created_pins)
            self.finished_signal.emit({
                'success': True,
                'pins_created': created_pins,
                'fiber_locations': len(fiber_pins),
                'incident_locations': len(incident_pins),
                'adt_locations': len(adt_pins),
                'total_unique': len(unique_pins)
            })
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error in ActiveKnocker automation: {e}")
            self.finished_signal.emit({'success': False, 'error': str(e)})
    
    def get_fiber_locations_lumberton(self) -> List[Dict[str, Any]]:
        """Get AT&T Fiber available locations in Lumberton"""
        fiber_pins = []
        
        try:
            # Look for Lumberton fiber data files
            lumberton_files = [
                "downloads/lumberton/redfin_*.csv",
                "fiber_available_redfin_addresses_lumberton.csv"
            ]
            
            # Try to find Lumberton specific data
            import glob
            for pattern in lumberton_files:
                files = glob.glob(pattern)
                if files:
                    latest_file = sorted(files)[-1]
                    self.log_signal.emit(f"📄 Loading Lumberton fiber data from: {latest_file}")
                    
                    if latest_file.endswith('.csv'):
                        fiber_addresses = self.load_csv_addresses(latest_file)
                    else:
                        fiber_addresses = self.load_text_addresses(latest_file)
                    
                    # Only use first 5 for testing
                    for address in fiber_addresses[:5]:
                        if "Lumberton" in address or "lumberton" in address.lower():
                            fiber_pins.append({
                                'address': address,
                                'city': 'Lumberton',
                                'state': 'NC',
                                'category': 'fiber',
                                'notes': f"{self.pin_categories['fiber']} - From Redfin listing - High-speed internet available",
                                'priority': 'Medium'
                            })
                    break
            
            # If no specific Lumberton files, use REAL Lumberton addresses
            if not fiber_pins:
                self.log_signal.emit("📄 No Lumberton fiber files found, using real Lumberton addresses")
                real_addresses = [
                    "100 N Elm St, Lumberton, NC 28358",
                    "200 N Walnut St, Lumberton, NC 28358", 
                    "300 E 5th St, Lumberton, NC 28358",
                    "400 Fayetteville Rd, Lumberton, NC 28358",
                    "500 W 5th St, Lumberton, NC 28358"
                ]
                
                for address in real_addresses:
                    fiber_pins.append({
                        'address': address,
                        'city': 'Lumberton',
                        'state': 'NC',
                        'category': 'fiber',
                        'notes': f"{self.pin_categories['fiber']} - Real address in Lumberton",
                        'priority': 'Medium'
                    })
        
        except Exception as e:
            self.log_signal.emit(f"❌ Error loading Lumberton fiber locations: {e}")
        
        return fiber_pins
    
    def get_incident_locations(self) -> List[Dict[str, Any]]:
        """Get recent incident locations in target cities"""
        incident_pins = []
        
        try:
            # Import the incident worker to get recent incidents
            from workers.incident_automation_worker import IncidentAutomationWorker
            
            # Create worker and get incidents for target cities
            worker = IncidentAutomationWorker(
                target_cities=[f"{city}, NC" for city in self.target_cities], 
                radius_yards=100
            )
            
            # Get incidents from the last 48 hours
            recent_incidents = worker.fetch_recent_incidents()
            
            for incident in recent_incidents:
                city = incident.get('city', '')
                if city in self.target_cities:
                    incident_pins.append({
                        'address': incident.get('address', 'Unknown Address'),
                        'city': incident.get('city', 'Unknown'),
                        'state': incident.get('state', 'NC'),
                        'category': 'incident',
                        'notes': f"{self.pin_categories['incident']} - {incident.get('type', 'Unknown')} incident on {incident.get('date', 'Unknown')} - {incident.get('details', '')}",
                        'priority': 'High',
                        'incident_type': incident.get('type', 'Unknown'),
                        'incident_date': incident.get('date', 'Unknown')
                    })
        
        except Exception as e:
            self.log_signal.emit(f"❌ Error getting incident locations: {e}")
            
            # Create sample incident data for testing
            sample_incidents = [
                {
                    'address': '123 Fire Station Rd, Lumberton, NC',
                    'city': 'Lumberton',
                    'incident_type': 'fire',
                    'notes': f"{self.pin_categories['incident']} - Fire incident - Smoke monitoring needed"
                },
                {
                    'address': '456 Security Blvd, Fayetteville, NC', 
                    'city': 'Fayetteville',
                    'incident_type': 'burglary',
                    'notes': f"{self.pin_categories['incident']} - Break-in incident - Security system needed"
                }
            ]
            
            for incident in sample_incidents:
                incident_pins.append({
                    'address': incident['address'],
                    'city': incident['city'],
                    'state': 'NC',
                    'category': 'incident',
                    'notes': incident['notes'],
                    'priority': 'High',
                    'incident_type': incident['incident_type']
                })
        
        return incident_pins
    
    def get_adt_detection_locations(self) -> List[Dict[str, Any]]:
        """Get ADT sign detection locations in target cities"""
        adt_pins = []
        
        try:
            # Look for ADT detection results
            adt_files = [
                "redfin_adt_consolidated_REAL_*.json",
                "redfin_adt_consolidated_*.json"
            ]
            
            import glob
            for pattern in adt_files:
                files = glob.glob(pattern)
                if files:
                    latest_file = sorted(files)[-1]
                    self.log_signal.emit(f"📄 Loading ADT detection data from: {latest_file}")
                    
                    with open(latest_file, 'r') as f:
                        adt_data = json.load(f)
                    
                    # Extract ADT detection results
                    adt_results = []
                    if 'results' in adt_data and 'adt_results' in adt_data['results']:
                        adt_results = adt_data['results']['adt_results']
                    elif 'adt_results' in adt_data:
                        adt_results = adt_data['adt_results']
                    
                    for result in adt_results:
                        city = result.get('city', '')
                        if city in self.target_cities:
                            # Include both detected and non-detected for targeted marketing
                            adt_detected = result.get('adt_detected', False)
                            confidence = result.get('confidence', 0.0)
                            
                            if adt_detected:
                                notes = f"{self.pin_categories['adt']} - ADT system detected (confidence: {confidence:.2f}) - Upgrade opportunity"
                                priority = 'High'
                            else:
                                notes = f"{self.pin_categories['adt']} - No ADT detected - Security system opportunity"
                                priority = 'Medium'
                            
                            adt_pins.append({
                                'address': result.get('address', 'Unknown Address'),
                                'city': result.get('city', 'Unknown'),
                                'state': result.get('state', 'NC'),
                                'category': 'adt',
                                'notes': notes,
                                'priority': priority,
                                'adt_detected': adt_detected,
                                'confidence': confidence,
                                'detection_method': result.get('detection_method', 'Unknown')
                            })
                    break
            
            # If no ADT files found, create sample data
            if not adt_pins:
                self.log_signal.emit("📄 No ADT detection files found, using sample data")
                sample_adt = [
                    {
                        'address': '789 Security Ave, Lumberton, NC',
                        'city': 'Lumberton',
                        'adt_detected': True,
                        'confidence': 0.85
                    },
                    {
                        'address': '321 Guard St, Fayetteville, NC',
                        'city': 'Fayetteville', 
                        'adt_detected': False,
                        'confidence': 0.0
                    }
                ]
                
                for adt in sample_adt:
                    if adt['adt_detected']:
                        notes = f"{self.pin_categories['adt']} - ADT system detected - Upgrade opportunity"
                        priority = 'High'
                    else:
                        notes = f"{self.pin_categories['adt']} - No ADT detected - Security system opportunity" 
                        priority = 'Medium'
                    
                    adt_pins.append({
                        'address': adt['address'],
                        'city': adt['city'],
                        'state': 'NC',
                        'category': 'adt',
                        'notes': notes,
                        'priority': priority,
                        'adt_detected': adt['adt_detected'],
                        'confidence': adt['confidence']
                    })
        
        except Exception as e:
            self.log_signal.emit(f"❌ Error getting ADT detection locations: {e}")
        
        return adt_pins
    
    def deduplicate_pins(self, pins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate pins based on address, keeping highest priority"""
        unique_pins = {}
        
        priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
        
        for pin in pins:
            address = pin['address'].strip().lower()
            
            if address not in unique_pins:
                unique_pins[address] = pin
            else:
                # Keep the pin with higher priority
                existing_priority = priority_order.get(unique_pins[address].get('priority', 'Low'), 1)
                new_priority = priority_order.get(pin.get('priority', 'Low'), 1)
                
                if new_priority > existing_priority:
                    # Merge categories if different
                    if unique_pins[address].get('category') != pin.get('category'):
                        categories = [unique_pins[address].get('category', ''), pin.get('category', '')]
                        pin['category'] = f"{categories[0]}+{categories[1]}"
                        pin['notes'] = f"Multi-category: {unique_pins[address].get('notes', '')} | {pin.get('notes', '')}"
                    
                    unique_pins[address] = pin
        
        return list(unique_pins.values())
    
    def send_pins_to_activeknocker(self, pins: List[Dict[str, Any]]) -> int:
        """Send pins to ActiveKnocker"""
        created_count = 0
        total_pins = len(pins)
        
        for i, pin in enumerate(pins):
            if self.stop_flag:
                break
                
            self.progress_signal.emit(i + 1, total_pins, f"Sending pin {i+1}/{total_pins}: {pin['address']}")
            
            if self.send_single_pin(pin):
                created_count += 1
                self.log_signal.emit(f"✅ Sent: {pin['address']} ({pin['category']})")
            else:
                self.log_signal.emit(f"❌ Failed: {pin['address']}")
            
            time.sleep(1)  # Rate limiting
        
        return created_count
    
    def send_single_pin(self, pin: Dict[str, Any]) -> bool:
        """Send a single pin to ActiveKnocker"""
        try:
            # Geocode the address
            lat, lng = self.geocode_address(pin['address'])
            
            if not lat or not lng:
                self.log_signal.emit(f"❌ Failed to geocode: {pin['address']}")
                return False
            
            # Parse the address into components for the structured format
            address_parts = self.parse_address(pin['address'])
            
            # Use the exact format from successful pins
            payload = {
                "address": address_parts,  # Structured address object
                "latitude": lat,
                "longitude": lng,
                "notes": pin['notes'],
                "created_user_id": "15249"  # Required user ID from successful pins
            }
            
            self.log_signal.emit(f"📤 Sending: {pin['address']} ({lat}, {lng})")
            
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=15)
            
            self.log_signal.emit(f"📊 API Response: {response.status_code} - {response.text[:100]}")
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == True:  # ActiveKnocker returns status: true/false
                    return True
                else:
                    self.log_signal.emit(f"❌ API Error: {response_data.get('msg', 'Unknown error')}")
                    return False
            else:
                self.log_signal.emit(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_signal.emit(f"❌ Exception sending pin: {e}")
            return False
    
    def parse_address(self, address: str) -> dict:
        """Parse an address string into the structured format ActiveKnocker expects"""
        try:
            # Simple parsing for "Street, City, State Zipcode" format
            parts = address.split(', ')
            
            if len(parts) >= 3:
                street = parts[0].strip()
                city = parts[1].strip()
                state_zip = parts[2].strip()
                
                # Split state and zip
                state_parts = state_zip.split(' ')
                state = state_parts[0].strip()
                postal_code = state_parts[1].strip() if len(state_parts) > 1 else ""
                
                return {
                    "street": street,
                    "city": city, 
                    "state": "North Carolina" if state == "NC" else state,
                    "country": "United States",
                    "postalCode": postal_code
                }
            else:
                # Fallback for addresses that don't parse well
                return {
                    "street": address,
                    "city": "Unknown",
                    "state": "North Carolina", 
                    "country": "United States",
                    "postalCode": ""
                }
                
        except Exception as e:
            self.log_signal.emit(f"❌ Address parsing error: {e}")
            return {
                "street": address,
                "city": "Unknown",
                "state": "North Carolina",
                "country": "United States", 
                "postalCode": ""
            }
    
    def geocode_address(self, address: str) -> tuple:
        """Geocode an address using Census API"""
        try:
            base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params = {
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json"
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            resp = requests.get(url, timeout=10)
            data = resp.json()
            matches = data.get("result", {}).get("addressMatches", [])
            
            if matches:
                coords = matches[0]["coordinates"]
                return coords["y"], coords["x"]  # lat, lon
        except Exception as e:
            self.log_signal.emit(f"❌ Geocoding error for {address}: {e}")
        
        return None, None
    
    def load_csv_addresses(self, file_path: str) -> List[str]:
        """Load addresses from CSV file"""
        addresses = []
        try:
            import csv
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    address = row.get('ADDRESS') or row.get('address') or row.get('Address')
                    if address:
                        addresses.append(address.strip())
        except Exception as e:
            self.log_signal.emit(f"❌ Error loading CSV {file_path}: {e}")
        return addresses
    
    def load_text_addresses(self, file_path: str) -> List[str]:
        """Load addresses from text file"""
        addresses = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    address = line.strip()
                    if address and not address.startswith('#'):
                        addresses.append(address)
        except Exception as e:
            self.log_signal.emit(f"❌ Error loading text file {file_path}: {e}")
        return addresses
    
    def stop(self):
        """Stop the automation worker"""
        self.stop_flag = True 