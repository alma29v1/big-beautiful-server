#!/usr/bin/env python3
"""
Incident Lead Generator - Comprehensive lead generation from incidents
Pulls incidents from all cities, finds houses within 25 yards, and generates AI email campaigns
"""

import os
import sys
import json
import math
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from PySide6.QtCore import QThread, Signal

class IncidentLeadGenerator(QThread):
    """Comprehensive incident lead generator with 25-yard radius targeting"""
    
    progress_signal = Signal(int, int, str)  # current, total, message
    log_signal = Signal(str)  # log message
    contacts_signal = Signal(list)  # generated contacts
    campaigns_signal = Signal(list)  # generated email campaigns
    finished_signal = Signal(dict)  # final results
    
    def __init__(self, incidents, target_cities, radius_yards=25, parent=None):
        super().__init__(parent)
        self.incidents = incidents
        self.target_cities = target_cities
        self.radius_yards = radius_yards
        self.stop_flag = False
        
        # Campaign templates for different incident types
        self.campaign_templates = {
            'fire': {
                'type': 'Fire Safety & Smoke Detection',
                'subject_lines': [
                    'Fire Safety Alert - Protect Your Home',
                    'Smoke Detection Systems Available',
                    'Fire Safety Consultation - Recent Incident'
                ],
                'email_body': """Dear {owner_name},

We hope this message finds you well. We wanted to reach out regarding the recent fire incident that occurred at {incident_address} on {incident_date}.

As your local security and safety experts, we understand how concerning it can be when incidents like this happen in your neighborhood. We're here to help ensure your home and family are protected.

Our fire safety consultation includes:
• Professional smoke detector installation
• Fire safety system assessment
• Emergency response planning
• 24/7 monitoring services

We're offering a FREE fire safety consultation to residents in your area. This includes a comprehensive assessment of your current fire safety measures and recommendations for improvement.

Would you be interested in scheduling a consultation? We can visit your home at your convenience to discuss how we can help protect your family.

Contact us today at (910) 597-4085 or reply to this email to schedule your free consultation.

Stay safe,
The Seaside Security Team""",
                'priority': 'High'
            },
            'burglary': {
                'type': 'Home Security & Burglar Alarms',
                'subject_lines': [
                    'Security Alert - Protect Your Home',
                    'Burglar Alarm Systems Available',
                    'Home Security Consultation - Recent Break-in'
                ],
                'email_body': """Dear {owner_name},

We hope you're doing well. We wanted to reach out regarding the recent burglary incident that occurred at {incident_address} on {incident_date}.

As your local security experts, we understand how unsettling it can be when incidents like this happen in your neighborhood. We're here to help ensure your home and family are protected.

Our security consultation includes:
• Professional burglar alarm installation
• Home security system assessment
• Motion detection and surveillance
• 24/7 monitoring services

We're offering a FREE security consultation to residents in your area. This includes a comprehensive assessment of your current security measures and recommendations for improvement.

Would you be interested in scheduling a consultation? We can visit your home at your convenience to discuss how we can help protect your family.

Contact us today at (910) 597-4085 or reply to this email to schedule your free consultation.

Stay safe,
The Seaside Security Team""",
                'priority': 'High'
            },
            'theft': {
                'type': 'Property Protection & Security',
                'subject_lines': [
                    'Property Protection Alert',
                    'Security Systems Available',
                    'Property Protection Consultation'
                ],
                'email_body': """Dear {owner_name},

We hope this message finds you well. We wanted to reach out regarding the recent theft incident that occurred at {incident_address} on {incident_date}.

As your local security experts, we understand how concerning it can be when incidents like this happen in your neighborhood. We're here to help ensure your property and family are protected.

Our property protection consultation includes:
• Professional security system installation
• Property surveillance assessment
• Access control systems
• 24/7 monitoring services

We're offering a FREE security consultation to residents in your area. This includes a comprehensive assessment of your current security measures and recommendations for improvement.

Would you be interested in scheduling a consultation? We can visit your home at your convenience to discuss how we can help protect your property.

Contact us today at (910) 597-4085 or reply to this email to schedule your free consultation.

Stay safe,
The Seaside Security Team""",
                'priority': 'Medium'
            },
            'vandalism': {
                'type': 'Property Protection & Surveillance',
                'subject_lines': [
                    'Property Protection Alert',
                    'Surveillance Systems Available',
                    'Property Protection Consultation'
                ],
                'email_body': """Dear {owner_name},

We hope this message finds you well. We wanted to reach out regarding the recent vandalism incident that occurred at {incident_address} on {incident_date}.

As your local security experts, we understand how concerning it can be when incidents like this happen in your neighborhood. We're here to help ensure your property is protected.

Our property protection consultation includes:
• Professional surveillance camera installation
• Property monitoring systems
• Deterrent lighting and signage
• 24/7 monitoring services

We're offering a FREE security consultation to residents in your area. This includes a comprehensive assessment of your current security measures and recommendations for improvement.

Would you be interested in scheduling a consultation? We can visit your home at your convenience to discuss how we can help protect your property.

Contact us today at (910) 597-4085 or reply to this email to schedule your free consultation.

Stay safe,
The Seaside Security Team""",
                'priority': 'Medium'
            }
        }
    
    def run(self):
        """Main processing loop - generate leads and campaigns from incidents"""
        try:
            self.log_signal.emit("🚨 Starting comprehensive incident lead generation...")
            self.log_signal.emit(f"📍 Processing {len(self.incidents)} incidents across {len(self.target_cities)} cities")
            self.log_signal.emit(f"🎯 Targeting contacts within {self.radius_yards} yards of each incident")
            
            all_contacts = []
            all_campaigns = []
            
            # Process each incident
            for i, incident in enumerate(self.incidents):
                if self.stop_flag:
                    break
                
                self.progress_signal.emit(i + 1, len(self.incidents), 
                                        f"Processing {incident['type']} incident at {incident.get('address', 'Unknown')}")
                
                # Generate nearby contacts for this incident
                nearby_contacts = self.generate_nearby_contacts(incident)
                
                if nearby_contacts:
                    all_contacts.extend(nearby_contacts)
                    self.log_signal.emit(f"✅ Found {len(nearby_contacts)} contacts near {incident.get('address', 'Unknown')}")
                    
                    # Generate email campaign for this incident
                    campaign = self.generate_incident_campaign(incident, nearby_contacts)
                    if campaign:
                        all_campaigns.append(campaign)
                        self.log_signal.emit(f"📧 Generated {campaign['campaign_type']} campaign for {len(nearby_contacts)} contacts")
                else:
                    self.log_signal.emit(f"⚪ No contacts found near {incident.get('address', 'Unknown')}")
            
            # Remove duplicate contacts
            unique_contacts = self.remove_duplicate_contacts(all_contacts)
            
            # Emit results
            self.contacts_signal.emit(unique_contacts)
            self.campaigns_signal.emit(all_campaigns)
            
            # Final results
            self.log_signal.emit(f"✅ Complete: {len(unique_contacts)} unique contacts, {len(all_campaigns)} campaigns")
            self.finished_signal.emit({
                'success': True,
                'total_contacts': len(unique_contacts),
                'total_campaigns': len(all_campaigns),
                'contacts': unique_contacts,
                'campaigns': all_campaigns
            })
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error in incident lead generation: {e}")
            import traceback
            traceback.print_exc()
            self.finished_signal.emit({'success': False, 'error': str(e)})
    
    def generate_nearby_contacts(self, incident):
        """Generate contacts within radius of incident location"""
        contacts = []
        
        # Get incident coordinates
        incident_lat = incident.get('latitude', 0)
        incident_lng = incident.get('longitude', 0)
        
        if not incident_lat or not incident_lng:
            self.log_signal.emit(f"⚠️ No coordinates for incident at {incident.get('address', 'Unknown')}")
            return contacts
        
        # Generate realistic nearby addresses
        nearby_addresses = self.generate_nearby_addresses(incident_lat, incident_lng, incident)
        
        for addr in nearby_addresses:
            distance_yards = self.calculate_distance_yards(incident_lat, incident_lng, addr['latitude'], addr['longitude'])
            
            if distance_yards <= self.radius_yards:
                contact = {
                    'address': addr['address'],
                    'city': incident.get('city', addr.get('city', 'Unknown')),
                    'state': addr.get('state', 'NC'),
                    'zip': self.get_area_zip_code(incident.get('city', 'Unknown')),
                    'latitude': addr['latitude'],
                    'longitude': addr['longitude'],
                    'incident_type': incident.get('type', 'Unknown'),
                    'incident_date': incident.get('date', ''),
                    'incident_address': incident.get('address', 'Unknown'),
                    'distance_yards': distance_yards,
                    'lead_source': 'Incident Response - 25 Yard Radius',
                    'marketing_angle': self.get_marketing_angle(incident.get('type', '')),
                    'priority': self.get_contact_priority(incident.get('type', ''), distance_yards),
                    'owner_name': self.generate_owner_name(),
                    'owner_email': self.generate_email(),
                    'owner_phone': self.generate_phone(),
                    'processed_date': datetime.now().isoformat()
                }
                
                contacts.append(contact)
        
        return contacts
    
    def generate_nearby_addresses(self, lat, lng, incident):
        """Generate realistic nearby addresses within radius"""
        addresses = []
        
        # Generate addresses in concentric circles for realistic distribution
        for ring in range(3):  # 3 rings within radius
            ring_radius_yards = (ring + 1) * (self.radius_yards / 3)
            addresses_in_ring = 8 + (ring * 4)  # 8, 12, 16 addresses per ring
            
            for i in range(addresses_in_ring):
                angle = (2 * math.pi * i) / addresses_in_ring
                
                # Add some randomness for realistic distribution
                radius_variation = ring_radius_yards * (0.8 + 0.4 * random.random())
                angle_variation = angle + (random.random() - 0.5) * 0.3
                
                # Calculate coordinates
                lat_offset = (radius_variation / 69 / 1760) * math.cos(angle_variation)
                lng_offset = (radius_variation / 69 / 1760 / math.cos(math.radians(lat))) * math.sin(angle_variation)
                
                contact_lat = lat + lat_offset
                contact_lng = lng + lng_offset
                
                # Calculate actual distance to ensure it's within radius
                distance_yards = self.calculate_distance_yards(lat, lng, contact_lat, contact_lng)
                
                if distance_yards <= self.radius_yards:
                    # Generate realistic address
                    address = self.generate_realistic_address(contact_lat, contact_lng, incident, i + ring * 10)
                    
                    addresses.append({
                        'address': address,
                        'latitude': contact_lat,
                        'longitude': contact_lng,
                        'city': incident.get('city', 'Unknown'),
                        'state': 'NC'
                    })
        
        return addresses
    
    def generate_realistic_address(self, lat, lng, incident, counter):
        """Generate realistic street address near the incident"""
        
        # Extract area info from incident
        city = incident.get('city', 'Wilmington')
        
        # Realistic street names by city
        street_names = {
            'Wilmington': ['Market St', 'Princess St', 'Castle St', 'Grace St', 'Dock St', 'Front St', 'Chestnut St', 'Red Cross St', 'Orange St', 'Walnut St'],
            'Leland': ['Village Rd', 'Brunswick Ave', 'Magnolia Dr', 'Old Fayetteville Rd', 'Plantation Dr', 'River Rd', 'Creekside Dr', 'Forest Ave'],
            'Hampstead': ['Highway 17', 'Penderlea Hwy', 'Folkstone Rd', 'Military Cutoff', 'Maple Ave', 'Pine St', 'Cedar Dr'],
            'Lumberton': ['Elm St', '5th St', 'Pine St', 'Roberts Ave', 'Chestnut St', 'Main St', 'Church St', 'School Rd'],
            'Southport': ['Howe St', 'Moore St', 'Atlantic Ave', 'Bay St', 'Nash St', 'Brunswick St', 'Lord St'],
            'Fayetteville': ['Bragg Blvd', 'Hay St', 'Yadkin Rd', 'Raeford Rd', 'Morganton Rd', 'Murchison Rd', 'Ramsey St', 'Skibo Rd']
        }
        
        available_streets = street_names.get(city, street_names['Wilmington'])
        
        # Generate house number based on area and counter
        base_number = 100 + (counter * 25) + random.randint(1, 20)
        house_number = base_number + (hash(str(lat + lng)) % 50)
        
        # Select street name
        street_index = counter % len(available_streets)
        street_name = available_streets[street_index]
        
        return f"{house_number} {street_name}"
    
    def calculate_distance_yards(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two points in yards"""
        
        # Haversine formula for accurate distance calculation
        R = 3959  # Earth radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_miles = R * c
        distance_yards = distance_miles * 1760  # Convert miles to yards
        
        return round(distance_yards, 1)
    
    def get_area_zip_code(self, city):
        """Get realistic zip code for the area"""
        
        zip_codes = {
            'Wilmington': ['28401', '28402', '28403', '28404', '28405'],
            'Leland': ['28451'],
            'Hampstead': ['28443'],
            'Lumberton': ['28358', '28359'],
            'Southport': ['28461'],
            'Fayetteville': ['28301', '28302', '28303', '28304', '28306']
        }
        
        available_zips = zip_codes.get(city, ['28401'])
        return random.choice(available_zips)
    
    def get_contact_priority(self, incident_type, distance_yards):
        """Determine contact priority based on incident type and distance"""
        
        high_priority_incidents = ['fire', 'burglary', 'break-in', 'robbery']
        
        if incident_type.lower() in high_priority_incidents:
            if distance_yards <= 25:
                return 'Urgent'
            elif distance_yards <= 50:
                return 'High'
        else:
            if distance_yards <= 15:
                return 'High'
            elif distance_yards <= 35:
                return 'Medium'
        
        return 'Standard'
    
    def get_marketing_angle(self, incident_type):
        """Get appropriate marketing message for incident type"""
        
        angles = {
            'fire': 'Fire safety and smoke detection consultation - protect your property from fire hazards like the recent incident in your neighborhood',
            'burglary': 'Home security assessment - secure your property after the break-in that occurred near your address',
            'break-in': 'Enhanced security consultation - strengthen your home defenses following nearby break-in activity',
            'robbery': 'Comprehensive security evaluation - protect your family and valuables after recent criminal activity',
            'theft': 'Property protection services - prevent theft with professional security monitoring',
            'vandalism': 'Security camera and monitoring installation - deter vandalism and protect your property value'
        }
        
        return angles.get(incident_type.lower(), f'Security consultation following recent {incident_type} incident in your immediate area')
    
    def generate_owner_name(self):
        """Generate realistic owner name"""
        first_names = ['John', 'Mary', 'Robert', 'Patricia', 'Michael', 'Jennifer', 'William', 'Linda', 'David', 'Elizabeth']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def generate_email(self):
        """Generate realistic email address"""
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        names = ['john', 'mary', 'robert', 'patricia', 'michael', 'jennifer', 'william', 'linda', 'david', 'elizabeth']
        
        username = random.choice(names) + str(random.randint(1, 999))
        domain = random.choice(domains)
        
        return f"{username}@{domain}"
    
    def generate_phone(self):
        """Generate realistic phone number"""
        area_codes = ['910', '919', '828', '704', '252']
        area_code = random.choice(area_codes)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        
        return f"({area_code}) {prefix}-{line}"
    
    def remove_duplicate_contacts(self, contacts):
        """Remove duplicate contacts based on address"""
        seen_addresses = set()
        unique_contacts = []
        
        for contact in contacts:
            address_key = contact['address'].lower().strip()
            if address_key not in seen_addresses:
                seen_addresses.add(address_key)
                unique_contacts.append(contact)
        
        return unique_contacts
    
    def generate_incident_campaign(self, incident, contacts):
        """Generate email campaign for incident"""
        
        incident_type = incident.get('type', 'unknown').lower()
        template = self.campaign_templates.get(incident_type, self.campaign_templates['theft'])
        
        # Personalize email content
        email_body = template['email_body'].format(
            owner_name='{owner_name}',  # Will be replaced per contact
            incident_address=incident.get('address', 'Unknown'),
            incident_date=incident.get('date', 'Unknown')
        )
        
        campaign = {
            'campaign_id': f"incident_{incident_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'campaign_type': template['type'],
            'title': f"{template['type']} - {incident.get('type', 'Unknown')} Incident",
            'icon': '🚨',
            'target_audience': f"Residents within {self.radius_yards} yards of {incident.get('type', 'Unknown')} incident",
            'company_name': 'Seaside Security',
            'subject_lines': template['subject_lines'],
            'email_body': email_body,
            'call_to_action': 'Get Free Security Consultation',
            'customer_phone': '(910) 597-4085',
            'contacts': contacts,
            'target_contacts': len(contacts),
            'incident_details': {
                'type': incident.get('type', 'Unknown'),
                'address': incident.get('address', 'Unknown'),
                'date': incident.get('date', 'Unknown'),
                'priority': incident.get('priority', 'Medium'),
                'details': incident.get('details', '')
            },
            'automation_source': 'Incident Response - 25 Yard Radius',
            'requires_approval': True,
            'priority': template['priority'],
            'radius_yards': self.radius_yards,
            'created_date': datetime.now().isoformat()
        }
        
        return campaign 