#!/usr/bin/env python3
"""
Automated Incident Response Email Worker
Monitors incidents in target cities and automatically generates targeted email campaigns
for nearby residents based on incident type (fire → smoke monitoring, break-in → alarms)
"""

import os
import sys
import json
import requests
import pandas as pd
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from PySide6.QtCore import QThread, Signal
from workers.automation_worker import AutomationWorker
from workers.batchdata_worker import BatchDataWorker

class IncidentAutomationWorker(QThread):
    """Automated incident monitoring and email campaign generation"""
    
    progress_signal = Signal(int, int, str)  # current, total, message
    log_signal = Signal(str)  # log message
    email_campaigns_signal = Signal(list)  # generated email campaigns
    finished_signal = Signal(dict)  # final results
    
    def __init__(self, target_cities=None, radius_yards=50, check_interval_hours=6):
        super().__init__()
        self.target_cities = target_cities or [
            "Wilmington, NC", "Leland, NC", "Hampstead, NC", 
            "Lumberton, NC", "Southport, NC", "Jacksonville, NC", "Fayetteville, NC"
        ]
        self.radius_yards = radius_yards
        self.check_interval_hours = check_interval_hours
        self.stop_flag = False
        
        # Initialize automation worker for email generation
        try:
            self.email_worker = AutomationWorker([])  # Empty processes list
        except:
            self.email_worker = None
            
    def run(self):
        """Main automation loop - monitor incidents and generate emails"""
        try:
            self.log_signal.emit("🚨 Starting automated incident monitoring...")
            
            # Get recent incidents from target cities
            all_incidents = self.fetch_recent_incidents()
            
            if not all_incidents:
                self.log_signal.emit("ℹ️ No new incidents found in target cities")
                self.finished_signal.emit({'success': True, 'incidents': 0, 'campaigns': 0})
                return
            
            self.log_signal.emit(f"🔍 Found {len(all_incidents)} recent incidents")
            
            # Process each incident and generate targeted email campaigns
            generated_campaigns = []
            total_incidents = len(all_incidents)
            
            for i, incident in enumerate(all_incidents):
                if self.stop_flag:
                    break
                
                self.progress_signal.emit(i + 1, total_incidents, 
                                        f"Processing {incident['type']} incident at {incident.get('location', incident.get('address', 'Unknown'))}")
                
                # Generate email campaign for this incident
                campaign = self.generate_incident_email_campaign(incident)
                if campaign:
                    generated_campaigns.append(campaign)
                    self.log_signal.emit(f"📧 Generated {campaign['campaign_type']} campaign for {len(campaign['contacts'])} nearby residents")
            
            self.email_campaigns_signal.emit(generated_campaigns)
            self.finished_signal.emit({
                'success': True,
                'incidents': len(all_incidents),
                'campaigns': len(generated_campaigns),
                'campaigns_data': generated_campaigns
            })
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error in incident automation: {e}")
            self.finished_signal.emit({'success': False, 'error': str(e)})
    
    def fetch_recent_incidents(self):
        """Fetch recent incidents from target cities"""
        all_incidents = []
        
        # In production, this would connect to police APIs, RSS feeds, or other data sources
        # For now, using enhanced sample data with realistic incident patterns
        
        for city in self.target_cities:
            city_incidents = self.get_sample_incidents_for_city(city)
            all_incidents.extend(city_incidents)
        
        # Filter to only recent incidents (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_incidents = []
        
        for incident in all_incidents:
            try:
                incident_date_str = incident.get('timestamp', incident.get('date', ''))
                try:
                    incident_date = datetime.fromisoformat(incident_date_str.replace('Z', ''))
                except:
                    incident_date = datetime.now()
                if incident_date >= recent_cutoff.replace(hour=0, minute=0, second=0):
                    recent_incidents.append(incident)
            except:
                # If date parsing fails, include it anyway
                recent_incidents.append(incident)
        
        return recent_incidents
    
    def get_sample_incidents_for_city(self, city):
        """Generate realistic sample incidents for a city"""
        city_name = city.split(',')[0]
        
        # City-specific incident data with realistic locations
        city_incidents = {
            "Wilmington": [
                {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'fire',
                    'address': '123 Market St',
                    'city': 'Wilmington',
                    'state': 'NC',
                    'latitude': 34.2352,
                    'longitude': -77.9503,
                    'priority': 'High',
                    'details': 'Structure fire, smoke damage to adjacent properties'
                },
                {
                    'date': (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d'),
                    'type': 'burglary',
                    'address': '456 Princess St',
                    'city': 'Wilmington', 
                    'state': 'NC',
                    'latitude': 34.2342,
                    'longitude': -77.9468,
                    'priority': 'High',
                    'details': 'Forced entry through rear door, electronics stolen'
                }
            ],
            "Leland": [
                {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'break-in',
                    'address': '789 Village Rd',
                    'city': 'Leland',
                    'state': 'NC', 
                    'latitude': 34.2155,
                    'longitude': -78.0160,
                    'priority': 'High',
                    'details': 'Home invasion attempt, no injuries reported'
                }
            ],
            "Fayetteville": [
                {
                    'date': (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d'),
                    'type': 'fire',
                    'address': '321 Bragg Blvd',
                    'city': 'Fayetteville',
                    'state': 'NC',
                    'latitude': 35.0527,
                    'longitude': -78.8783,
                    'priority': 'High',
                    'details': 'Kitchen fire, smoke damage throughout house'
                }
            ]
        }
        
        return city_incidents.get(city_name, [])
    
    def generate_incident_email_campaign(self, incident):
        """Generate targeted email campaign based on incident type"""
        
        # Find nearby residents within radius
        nearby_contacts = self.find_nearby_residents(incident)
        
        if not nearby_contacts:
            return None
        
        # Determine campaign type and messaging based on incident
        campaign_config = self.get_campaign_config_for_incident(incident)
        
        # Create email campaign
        campaign = {
            'campaign_id': f"incident_{incident['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'campaign_type': campaign_config['type'],
            'title': campaign_config['title'],
            'icon': campaign_config['icon'],
            'target_audience': f"Residents within {self.radius_yards} yards of {incident['type']} incident",
            'company_name': 'Seaside Security',
            'subject_lines': campaign_config['subject_lines'],
            'email_body': campaign_config['email_body'].format(
                incident_type=incident['type'],
                incident_address=incident.get('location', incident.get('address', 'Unknown')),
                incident_date=incident.get('timestamp', incident.get('date', 'Unknown'))
            ),
            'call_to_action': campaign_config['call_to_action'],
            'customer_phone': campaign_config['phone'],
            'contacts': nearby_contacts,
            'target_contacts': len(nearby_contacts),
            'incident_details': {
                'type': incident['type'],
                'address': incident.get('location', incident.get('address', 'Unknown')),
                'date': incident.get('timestamp', incident.get('date', 'Unknown')),
                'priority': incident.get('priority', 'Medium'),
                'details': incident.get('details', incident.get('description', ''))
            },
            'automation_source': 'Incident Monitor',
            'requires_approval': True,
            'priority': 'High' if incident['type'] in ['fire', 'burglary', 'break-in'] else 'Medium',
            'created_at': datetime.now().isoformat(),
            'status': 'pending_approval'
        }
        
        return campaign
    
    def generate_incident_email_campaign_with_contacts(self, incident, contacts):
        """Generate incident email campaign with provided contacts"""
        if not contacts:
            return None
        
        # Determine campaign type and messaging based on incident
        campaign_config = self.get_campaign_config_for_incident(incident)
        
        # Create email campaign
        campaign = {
            'campaign_id': f"incident_{incident['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'campaign_type': campaign_config['type'],
            'title': campaign_config['title'],
            'icon': campaign_config['icon'],
            'target_audience': f"Residents within contact radius of {incident['type']} incident",
            'company_name': 'Seaside Security',
            'subject_lines': campaign_config['subject_lines'],
            'email_body': campaign_config['email_body'].format(
                incident_type=incident['type'],
                incident_address=incident.get('location', incident.get('address', 'Unknown')),
                incident_date=incident.get('timestamp', incident.get('date', 'Unknown'))
            ),
            'call_to_action': campaign_config['call_to_action'],
            'customer_phone': campaign_config['phone'],
            'contacts': contacts,
            'target_contacts': len(contacts),
            'incident_details': {
                'type': incident['type'],
                'address': incident.get('location', incident.get('address', 'Unknown')),
                'date': incident.get('timestamp', incident.get('date', 'Unknown')),
                'priority': incident.get('priority', 'Medium'),
                'details': incident.get('details', '')
            },
            'automation_source': 'Incident Response Widget',
            'requires_approval': True,
            'priority': 'High' if incident['type'] in ['fire', 'burglary', 'break-in'] else 'Medium',
            'created_at': datetime.now().isoformat(),
            'status': 'pending_approval'
        }
        
        return campaign
    
    def get_campaign_config_for_incident(self, incident):
        """Get email campaign configuration based on incident type"""
        
        incident_type = incident['type'].lower()
        
        # Fire incidents → smoke monitoring and fire safety
        if incident_type == 'fire':
            return {
                'type': 'Fire Safety Response',
                'title': '🔥 Fire Safety Alert - Smoke Monitoring Available',
                'icon': '🔥',
                'subject_lines': [
                    f"Fire Safety Alert: Incident Near Your Address",
                    f"Protect Your Family - Fire Occurred at {incident.get('location', incident.get('address', 'Unknown'))}",
                    f"Free Fire Safety Consultation After Nearby Fire",
                    f"Smoke Detection Upgrade Available - Fire Safety Alert"
                ],
                'email_body': """
Dear {{name}},

🔥 **Fire Safety Alert for Your Neighborhood**

We wanted to reach out following the fire incident that occurred at {incident_address} on {incident_date}. As a neighbor within the immediate area, your property safety is our priority.

<img src="https://seasidesecurity.net/wp-content/uploads/2025/07/PK3_bundle_531x380.webp" alt="PK3 Security Bundle" style="max-width: 531px; margin: 20px 0;">

🚨 **Immediate Fire Safety Solutions:**
• Professional smoke detection system upgrades
• 24/7 monitored fire detection with instant response
• Heat sensor installation for early fire detection
• Carbon monoxide monitoring for complete safety
• **Emergency evacuation planning and family safety protocols**

Following a neighborhood fire, now is the critical time to evaluate your home's fire safety systems. Many insurance companies offer discounts for professionally monitored fire detection.

<!-- Clickable Fire Safety Button -->
<div style="text-align: center; margin: 30px 0;">
<a href="https://seasidesecurity.net/schedule-appointment/" style="background-color: #cc0000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">🔥 Schedule Free Fire Safety Assessment</a>
</div>

📞 **Priority Response**: Call us at (910) 597-4085 for immediate fire safety assessment
🔥 **Free Service**: Complete fire safety consultation - no obligation

Your family's safety is precious. Let us help you protect what matters most.

Best regards,
The Fire Safety Response Team
Seaside Security

<img src="https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp" alt="Seaside Security - Fire Safety Response" style="max-width: 300px; margin: 20px 0;">

*This message was sent due to proximity to a fire incident. Professional fire safety assessment can prevent tragedy.*
""",
                'call_to_action': 'Get Free Fire Safety Assessment',
                'phone': '(910) 597-4085'
            }
        
        # Burglary/break-in incidents → security systems and alarms
        elif incident_type in ['burglary', 'break-in', 'robbery']:
            return {
                'type': 'Security Alert Response', 
                'title': '🏠 Security Alert - Break-in Protection Available',
                'icon': '🔒',
                'subject_lines': [
                    f"Security Alert: Break-in Near Your Address",
                    f"Protect Your Home - Incident at {incident.get('location', incident.get('address', 'Unknown'))}",
                    f"Free Security Assessment After Nearby Break-in",
                    f"Enhanced Security Available - Neighborhood Alert"
                ],
                'email_body': """
Dear {{name}},

🚨 **Neighborhood Security Alert**

We're reaching out following the {incident_type} incident that occurred at {incident_address} on {incident_date}. As your neighbor, we want to ensure your family's safety and security.

<img src="https://seasidesecurity.net/wp-content/uploads/2025/07/PK3_bundle_531x380.webp" alt="PK3 Security Bundle" style="max-width: 531px; margin: 20px 0;">

🏠 **Immediate Security Enhancements:**
• Professional alarm system installation and monitoring
• 24/7 security monitoring with police dispatch
• Door and window sensor upgrades
• Motion detection with instant mobile alerts
• **Security camera systems for property protection**
• Smart locks and access control systems

After a neighborhood break-in, residents who upgrade their security systems within 48 hours are 89% less likely to experience similar incidents.

<!-- Clickable Security Assessment Button -->
<div style="text-align: center; margin: 30px 0;">
<a href="https://seasidesecurity.net/schedule-appointment/" style="background-color: #cc0000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">🔒 Schedule Free Security Assessment</a>
</div>

📞 **Priority Security**: Call us at (910) 597-4085 for immediate security assessment
🔒 **Free Service**: Complete home security evaluation - no obligation

Don't wait for the next incident. Protect your family now.

Best regards,
The Security Response Team  
Seaside Security

<img src="https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp" alt="Seaside Security - Security Response" style="max-width: 300px; margin: 20px 0;">

*This message was sent due to proximity to a security incident. Professional security assessment can prevent future break-ins.*
""",
                'call_to_action': 'Get Free Security Assessment',
                'phone': '(910) 597-4085'
            }
        
        # General incidents → comprehensive security consultation
        else:
            return {
                'type': 'Neighborhood Safety Response',
                'title': '🛡️ Neighborhood Safety Alert',
                'icon': '🛡️',
                'subject_lines': [
                    f"Neighborhood Safety Alert: Incident Near You",
                    f"Community Safety Update - {incident.get('location', incident.get('address', 'Unknown'))}",
                    f"Free Safety Consultation Available",
                    f"Protect Your Family - Neighborhood Alert"
                ],
                'email_body': """
Dear {{name}},

🛡️ **Neighborhood Safety Alert**

We wanted to inform you about the recent {incident_type} incident at {incident_address} on {incident_date}. Community safety is our shared responsibility.

<img src="https://seasidesecurity.net/wp-content/uploads/2025/07/PK3_bundle_531x380.webp" alt="PK3 Security Bundle" style="max-width: 531px; margin: 20px 0;">

🏡 **Comprehensive Safety Solutions:**
• Complete home security assessment
• Advanced monitoring systems 
• Emergency response planning
• Neighborhood watch coordination
• **Family safety and emergency protocols**

As your local security professionals, we're here to help keep our community safe. A professional safety assessment can identify vulnerabilities before they become problems.

<!-- Clickable Safety Consultation Button -->
<div style="text-align: center; margin: 30px 0;">
<a href="https://seasidesecurity.net/schedule-appointment/" style="background-color: #cc0000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">🛡️ Schedule Free Safety Consultation</a>
</div>

📞 **Community Support**: Call us at (910) 597-4085 for safety consultation
🏡 **Free Service**: Complete home safety evaluation

Together, we can keep our neighborhood safe and secure.

Best regards,
The Community Safety Team
Seaside Security

<img src="https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp" alt="Seaside Security - Community Safety" style="max-width: 300px; margin: 20px 0;">

*This message was sent to promote community safety awareness following a local incident.*
""",
                'call_to_action': 'Get Free Safety Consultation',
                'phone': '(910) 597-4085'
            }
    
    def find_nearby_residents(self, incident):
        """Find residents within radius of incident location and get their contact information via BatchData"""
        nearby_contacts = []
        
        self.log_signal.emit(f"🔍 Finding residents within {self.radius_yards} yards of incident...")
        
        # Get incident coordinates
        incident_lat = incident.get('latitude', 0)
        incident_lng = incident.get('longitude', 0)
        
        if not incident_lat or not incident_lng:
            self.log_signal.emit("❌ No incident coordinates available")
            return nearby_contacts
        
        # Generate nearby addresses (in production, this would query a property database)
        sample_addresses = self.generate_nearby_addresses(incident_lat, incident_lng, incident)
        
        if not sample_addresses:
            self.log_signal.emit("❌ No nearby addresses found")
            return nearby_contacts
        
        self.log_signal.emit(f"📋 Found {len(sample_addresses)} nearby properties")
        
        # Track all addresses for accountability
        all_potential_leads = []
        
        # Prepare addresses for BatchData lookup
        addresses_for_batchdata = []
        address_distance_map = {}
        
        for addr in sample_addresses:
            distance_yards = self.calculate_distance_yards(
                incident_lat, incident_lng,
                addr.get('latitude', 0), addr.get('longitude', 0)
            )
            
            full_address = f"{addr['address']}, {incident['city']}, {incident['state']} {self.get_city_zip(incident['city'])}"
            
            # Track all addresses (both included and excluded)
            lead_status = 'included' if distance_yards <= self.radius_yards else 'excluded_distance'
            all_potential_leads.append({
                'address': full_address,
                'distance_yards': distance_yards,
                'latitude': addr.get('latitude', 0),
                'longitude': addr.get('longitude', 0),
                'lead_status': lead_status,
                'exclusion_reason': '' if distance_yards <= self.radius_yards else f'Outside {self.radius_yards} yard radius',
                'incident_type': incident['type'],
                'incident_address': incident.get('location', incident.get('address', 'Unknown')),
                'processed_date': datetime.now().isoformat()
            })
            
            if distance_yards <= self.radius_yards:
                addresses_for_batchdata.append(full_address)
                address_distance_map[full_address] = {
                    'distance_yards': distance_yards,
                    'priority': 'High' if distance_yards <= 25 else 'Medium'
                }
        
        # Save all potential leads for accountability
        self.save_all_incident_leads(all_potential_leads, incident)
        
        if not addresses_for_batchdata:
            self.log_signal.emit("❌ No addresses within radius")
            return nearby_contacts
        
        self.log_signal.emit(f"🎯 {len(addresses_for_batchdata)} addresses within {self.radius_yards} yard radius")
        self.log_signal.emit(f"📊 {len(sample_addresses) - len(addresses_for_batchdata)} addresses excluded by distance filter")
        self.log_signal.emit("📞 Calling BatchData API to get owner contact information...")
        
        # Use BatchData to get actual owner contact information
        try:
            # Format addresses for BatchData worker (it expects AT&T-style results format)
            batchdata_addresses = []
            for addr in addresses_for_batchdata:
                # Create AT&T-style format that BatchDataWorker expects
                parts = addr.split(', ')
                street = parts[0] if len(parts) > 0 else addr
                
                batchdata_addresses.append({
                    'address': addr,
                    'street': street,
                    'city': incident['city'],
                    'state': incident['state'],
                    'zip': self.get_city_zip(incident['city']),
                    'fiber_available': False  # Not relevant for incident response
                })
            
            # Format for BatchDataWorker which expects city results structure
            att_results_format = {
                f"{incident['city']}_incident": {
                    'addresses': batchdata_addresses
                }
            }
            
            # Get BatchData API key
            try:
                import json
                config_path = os.path.join('config', 'config.json')
                with open(config_path, 'r') as f:
                    config = json.load(f)
                batchdata_api_key = config.get('batchdata_api_key', '')
            except:
                batchdata_api_key = "Y7k9GnFK8YLkNpzQjRhJ"  # Fallback key
            
            # Create BatchData worker with correctly formatted data
            batchdata_worker = BatchDataWorker(att_results_format, batchdata_api_key)
            
            # Connect to signals to capture results
            results_captured = {}
            
            def capture_finished_results(summary):
                nonlocal results_captured
                results_captured = summary
            
            def capture_log_message(message):
                self.log_signal.emit(f"   [BatchData] {message}")
            
            # Connect signals
            batchdata_worker.finished_signal.connect(capture_finished_results)
            batchdata_worker.log_signal.connect(capture_log_message)
            
            # Run BatchData worker synchronously
            batchdata_worker.run()
            
            # Wait for completion (since it's threaded)
            batchdata_worker.wait()
            
            # Process results
            batch_results = results_captured.get('results', [])
            self.log_signal.emit(f"📊 BatchData returned {len(batch_results)} results")
            
            # Process BatchData results and add incident context
            for result in batch_results:
                # Accept both completed and partial results to maximize lead capture
                if result.get('batchdata_status') in ['completed', 'partial'] and (result.get('owner_name') or result.get('owner_email') or result.get('owner_phone')):
                    address_key = result.get('address', '')
                    
                    # Find matching address in our distance map
                    distance_info = None
                    for addr_key, info in address_distance_map.items():
                        if result.get('address', '').lower() in addr_key.lower():
                            distance_info = info
                            break
                    
                    if not distance_info:
                        distance_info = {'distance_yards': 50, 'priority': 'Medium'}
                    
                    # Create full contact record with incident context
                    contact = {
                        'owner_name': result.get('owner_name', ''),
                        'owner_email': result.get('owner_email', ''),
                        'owner_phone': result.get('owner_phone', ''),
                        'address': result.get('address', ''),
                        'city': incident['city'],
                        'state': incident['state'],
                        'zip': self.get_city_zip(incident['city']),
                        'distance_yards': distance_info['distance_yards'],
                        'incident_type': incident['type'],
                        'incident_date': incident.get('timestamp', incident.get('date', 'Unknown')),
                        'incident_address': incident.get('location', incident.get('address', 'Unknown')),
                        'priority': distance_info['priority'],
                        'lead_source': 'Incident Response - BatchData',
                        'batchdata_status': result.get('batchdata_status', 'completed'),
                        'processed_date': datetime.now().isoformat()
                    }
                    
                    nearby_contacts.append(contact)
                    
            self.log_signal.emit(f"✅ Found {len(nearby_contacts)} residents with contact information")
            
            # Save incident response BatchData results (only real data, no samples)
            if nearby_contacts:
                self.save_incident_batchdata_results(nearby_contacts, incident)
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error getting contact information: {e}")
            # Fallback to addresses without contact info
            for addr in sample_addresses:
                distance_yards = self.calculate_distance_yards(
                    incident_lat, incident_lng,
                    addr.get('latitude', 0), addr.get('longitude', 0)
                )
                
                if distance_yards <= self.radius_yards:
                    nearby_contacts.append({
                        'owner_name': 'Address Only',
                        'owner_email': '',
                        'owner_phone': '',
                        'address': addr['address'],
                        'city': incident['city'],
                        'state': incident['state'],
                        'zip': self.get_city_zip(incident['city']),
                        'distance_yards': distance_yards,
                        'incident_type': incident['type'],
                        'incident_date': incident.get('timestamp', incident.get('date', 'Unknown')),
                        'incident_address': incident.get('location', incident.get('address', 'Unknown')),
                        'priority': 'High' if distance_yards <= 25 else 'Medium',
                        'lead_source': 'Incident Response - Address Only',
                        'batchdata_status': 'failed'
                    })
        
        return nearby_contacts
    
    def generate_nearby_addresses(self, lat, lng, incident):
        """Generate realistic nearby addresses within incident radius"""
        addresses = []
        
        # Generate more addresses in a realistic pattern around the incident
        for i in range(25):  # Increased from 8 to 25 addresses per incident for better coverage
            # Create random variations in coordinates within reasonable distance
            import random
            
            # Generate addresses in multiple rings for better coverage
            ring = i // 8  # Create rings of addresses (0, 1, 2)
            angle = (i * 360 / 8) % 360  # More varied angles for better distribution
            
            # Vary distance based on ring to create realistic neighborhood pattern
            if ring == 0:
                distance_factor = random.uniform(0.0001, 0.0003)  # 10-30 yards (closest ring)
            elif ring == 1:
                distance_factor = random.uniform(0.0003, 0.0006)  # 30-60 yards (middle ring)
            else:
                distance_factor = random.uniform(0.0006, 0.0010)  # 60-100 yards (outer ring)
            
            import math
            addr_lat = lat + distance_factor * math.cos(math.radians(angle))
            addr_lng = lng + distance_factor * math.sin(math.radians(angle))
            
            # Generate realistic street addresses based on city
            city = incident.get('city', 'Wilmington')
            street_number = random.randint(100, 999)
            
            # City-specific street names for realism
            street_names = {
                'Wilmington': ["Market St", "Princess St", "Castle St", "Grace St", "Dock St", "Front St", "Chestnut St", "Red Cross St"],
                'Leland': ["Village Rd", "Brunswick Ave", "Magnolia Dr", "Old Fayetteville Rd", "Plantation Dr"],
                'Fayetteville': ["Bragg Blvd", "Ramsey St", "Owen Dr", "Skibo Rd", "All American Fwy"],
                'Lumberton': ["Elm St", "5th St", "Pine St", "Roberts Ave", "Chestnut St"],
                'Hampstead': ["Highway 17", "Penderlea Hwy", "Folkstone Rd", "Military Cutoff"],
                'Southport': ["Howe St", "Moore St", "Atlantic Ave", "Bay St", "Nash St"]
            }
            
            available_streets = street_names.get(city, street_names['Wilmington'])
            street_name = random.choice(available_streets)
            
            address = f"{street_number} {street_name}"
            
            addresses.append({
                'address': address,
                'latitude': addr_lat,
                'longitude': addr_lng
            })
        
        return addresses
    
    def calculate_distance_yards(self, lat1, lng1, lat2, lng2):
        """Calculate distance in yards between two coordinates"""
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance_miles = R * c
        distance_yards = distance_miles * 1760  # Convert miles to yards
        
        return round(distance_yards)
    
    def get_city_zip(self, city):
        """Get default ZIP code for city"""
        zip_codes = {
            'Wilmington': '28401',
            'Leland': '28451', 
            'Hampstead': '28443',
            'Lumberton': '28358',
            'Southport': '28461',
            'Jacksonville': '28540',
            'Fayetteville': '28301'
        }
        return zip_codes.get(city, '28401')
    
    def save_all_incident_leads(self, all_leads, incident):
        """Save all incident leads (both processed and unprocessed) to CSV for accountability"""
        try:
            import pandas as pd
            from datetime import datetime
            
            if not all_leads:
                return
            
            # Create DataFrame from all leads
            df = pd.DataFrame(all_leads)
            
            # Add incident metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            incident_type = incident.get('type', 'unknown')
            incident_address = incident.get('location', incident.get('address', 'unknown'))
            
            filename = f"ALL_incident_leads_{incident_type}_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            self.log_signal.emit(f"💾 Saved {len(all_leads)} total incident leads to {filename}")
            self.log_signal.emit(f"📊 Lead Breakdown:")
            
            # Count by status for reporting
            status_counts = {}
            for lead in all_leads:
                status = lead.get('lead_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                self.log_signal.emit(f"  • {status}: {count} leads")
            
        except Exception as e:
            self.log_signal.emit(f"⚠️ Error saving all incident leads: {e}")
    
    def save_incident_batchdata_results(self, contacts, incident):
        """Save incident response BatchData results to CSV file"""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Create DataFrame from contacts
            df = pd.DataFrame(contacts)
            
            # Add incident-specific metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            incident_type = incident.get('type', 'unknown')
            
            filename = f"processed_incident_contacts_{incident_type}_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            self.log_signal.emit(f"💾 Saved {len(contacts)} processed incident contacts to {filename}")
            
        except Exception as e:
            self.log_signal.emit(f"⚠️ Error saving incident BatchData results: {e}")
    
    def stop(self):
        """Stop the automation worker"""
        self.stop_flag = True 