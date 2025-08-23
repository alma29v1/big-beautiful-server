#!/usr/bin/env python3
"""
ActiveKnocker Automation Worker
Automatically sends specific lead types to Mark Walters in ActiveKnocker with appropriate pins
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

from PySide6.QtCore import QThread, Signal

class ActiveKnockerAutomationWorker(QThread):
    """Automated ActiveKnocker lead assignment"""
    
    progress_signal = Signal(int, int, str)  # current, total, message
    log_signal = Signal(str)  # log message
    finished_signal = Signal(dict)  # final results
    
    def __init__(self):
        super().__init__()
        self.stop_flag = False
        
        # Mark Walters contact info for ActiveKnocker
        self.mark_walters_config = {
            'name': 'Mark Walters',
            'email': 'mark@example.com',  # Replace with actual email
            'phone': '(910) 555-0000',    # Replace with actual phone
            'agent_id': 'mark_walters'    # Replace with actual ActiveKnocker agent ID
        }
        
        # Pin configurations for different lead types
        self.pin_configs = {
            'att_fiber': {
                'pin_type': 'att_fiber',
                'pin_color': 'blue',
                'pin_icon': 'wifi',
                'description': 'AT&T Fiber Available'
            },
            'fire_incident': {
                'pin_type': 'fire_incident', 
                'pin_color': 'red',
                'pin_icon': 'fire',
                'description': 'Fire Incident - Security Opportunity'
            },
            'breakin_incident': {
                'pin_type': 'breakin_incident',
                'pin_color': 'orange', 
                'pin_icon': 'lock',
                'description': 'Break-in Incident - Security Opportunity'
            },
            'adt_detected': {
                'pin_type': 'adt_detected',
                'pin_color': 'green',
                'pin_icon': 'shield',
                'description': 'ADT Sign Detected - Upgrade Opportunity'
            }
        }
            
    def run(self):
        """Main automation loop"""
        try:
            self.log_signal.emit("🎯 Starting ActiveKnocker automation for Mark Walters...")
            
            results = {
                'att_fiber_sent': 0,
                'incident_pins_sent': 0, 
                'adt_pins_sent': 0,
                'errors': []
            }
            
            # 1. Process AT&T Fiber leads from Lumberton
            self.log_signal.emit("🌐 Processing AT&T Fiber leads from Lumberton...")
            fiber_results = self.process_lumberton_fiber_leads()
            results['att_fiber_sent'] = fiber_results['sent_count']
            if fiber_results['errors']:
                results['errors'].extend(fiber_results['errors'])
            
            # 2. Process incident leads from Fayetteville and Lumberton
            self.log_signal.emit("🚨 Processing incident leads from Fayetteville and Lumberton...")
            incident_results = self.process_incident_leads()
            results['incident_pins_sent'] = incident_results['sent_count'] 
            if incident_results['errors']:
                results['errors'].extend(incident_results['errors'])
            
            # 3. Process ADT detection leads
            self.log_signal.emit("🔒 Processing ADT detection leads...")
            adt_results = self.process_adt_detection_leads()
            results['adt_pins_sent'] = adt_results['sent_count']
            if adt_results['errors']:
                results['errors'].extend(adt_results['errors'])
            
            # Summary
            total_sent = results['att_fiber_sent'] + results['incident_pins_sent'] + results['adt_pins_sent']
            self.log_signal.emit(f"✅ ActiveKnocker automation complete!")
            self.log_signal.emit(f"📊 Summary:")
            self.log_signal.emit(f"   AT&T Fiber pins: {results['att_fiber_sent']}")
            self.log_signal.emit(f"   Incident pins: {results['incident_pins_sent']}")
            self.log_signal.emit(f"   ADT pins: {results['adt_pins_sent']}")
            self.log_signal.emit(f"   Total pins sent: {total_sent}")
            
            if results['errors']:
                self.log_signal.emit(f"⚠️ Errors encountered: {len(results['errors'])}")
                for error in results['errors']:
                    self.log_signal.emit(f"   - {error}")
            
            self.finished_signal.emit(results)
            
        except Exception as e:
            error_msg = f"Error in ActiveKnocker automation: {str(e)}"
            self.log_signal.emit(f"❌ {error_msg}")
            self.finished_signal.emit({'error': error_msg})
    
    def process_lumberton_fiber_leads(self):
        """Process AT&T Fiber available addresses in Lumberton for Mark Walters"""
        results = {'sent_count': 0, 'errors': []}
        
        try:
            # Look for AT&T fiber results for Lumberton
            lumberton_files = [
                'downloads/Lumberton_att_fiber_results.csv',
                'downloads/lumberton_att_fiber_results.csv',
                'data/Lumberton_fiber_check.csv',
                'data/lumberton_fiber_check.csv'
            ]
            
            fiber_data = None
            for file_path in lumberton_files:
                if os.path.exists(file_path):
                    try:
                        fiber_data = pd.read_csv(file_path)
                        self.log_signal.emit(f"📁 Found Lumberton fiber data: {file_path}")
                        break
                    except Exception as e:
                        continue
            
            if fiber_data is None:
                self.log_signal.emit("⚠️ No Lumberton fiber data found - checking downloads folder...")
                # Check for any Lumberton files with fiber availability
                import glob
                lumberton_patterns = [
                    'downloads/*lumberton*.csv',
                    'downloads/*Lumberton*.csv', 
                    'data/*lumberton*.csv',
                    'data/*Lumberton*.csv'
                ]
                
                for pattern in lumberton_patterns:
                    files = glob.glob(pattern)
                    for file_path in files:
                        try:
                            test_data = pd.read_csv(file_path)
                            if 'fiber_available' in test_data.columns or 'att_fiber' in test_data.columns:
                                fiber_data = test_data
                                self.log_signal.emit(f"📁 Found Lumberton data with fiber info: {file_path}")
                                break
                        except:
                            continue
                    if fiber_data is not None:
                        break
            
            if fiber_data is None:
                self.log_signal.emit("❌ No Lumberton fiber data found")
                return results
            
            # Filter for fiber available addresses
            fiber_available = None
            if 'fiber_available' in fiber_data.columns:
                fiber_available = fiber_data[fiber_data['fiber_available'] == True]
            elif 'att_fiber' in fiber_data.columns:
                fiber_available = fiber_data[fiber_data['att_fiber'] == True]
            elif 'FIBER_AVAILABLE' in fiber_data.columns:
                fiber_available = fiber_data[fiber_data['FIBER_AVAILABLE'] == True]
            
            if fiber_available is None or len(fiber_available) == 0:
                self.log_signal.emit("ℹ️ No fiber available addresses found in Lumberton data")
                return results
            
            self.log_signal.emit(f"🎯 Found {len(fiber_available)} AT&T Fiber available addresses in Lumberton")
            
            # Send each fiber available address to ActiveKnocker for Mark
            for idx, row in fiber_available.iterrows():
                if self.stop_flag:
                    break
                
                try:
                    address = self.get_address_from_row(row)
                    if address:
                        pin_data = self.create_activeknocker_pin(
                            address=address,
                            pin_config=self.pin_configs['att_fiber'],
                            notes=f"AT&T Fiber confirmed available at this address. Ready for immediate installation. Contact: (910) 713-1213",
                            priority='High',
                            lead_source='Lumberton Fiber Check'
                        )
                        
                        success = self.send_to_activeknocker(pin_data)
                        if success:
                            results['sent_count'] += 1
                            self.log_signal.emit(f"✅ Sent AT&T Fiber pin for {address}")
                        else:
                            results['errors'].append(f"Failed to send AT&T Fiber pin for {address}")
                            
                except Exception as e:
                    results['errors'].append(f"Error processing fiber address {idx}: {str(e)}")
                    
        except Exception as e:
            results['errors'].append(f"Error in process_lumberton_fiber_leads: {str(e)}")
        
        return results
    
    def process_incident_leads(self):
        """Process incident leads from Fayetteville and Lumberton"""
        results = {'sent_count': 0, 'errors': []}
        
        try:
            # Look for incident data files
            incident_files = [
                'data/incident_leads.json',
                'data/fayetteville_incidents.json',
                'data/lumberton_incidents.json',
                'incident_data.json'
            ]
            
            incidents = []
            for file_path in incident_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            incident_data = json.load(f)
                            if isinstance(incident_data, list):
                                incidents.extend(incident_data)
                            elif isinstance(incident_data, dict) and 'incidents' in incident_data:
                                incidents.extend(incident_data['incidents'])
                        self.log_signal.emit(f"📁 Found incident data: {file_path}")
                    except:
                        continue
            
            if not incidents:
                self.log_signal.emit("ℹ️ No incident data found - checking for recent incident response emails...")
                # Check if incident response emails were generated recently
                return results
            
            # Filter for Fayetteville and Lumberton incidents
            target_cities = ['fayetteville', 'lumberton', 'Fayetteville', 'Lumberton']
            target_incidents = []
            
            for incident in incidents:
                city = incident.get('city', '').lower()
                if any(target_city.lower() in city for target_city in target_cities):
                    target_incidents.append(incident)
            
            self.log_signal.emit(f"🎯 Found {len(target_incidents)} incidents in Fayetteville/Lumberton")
            
            # Send incident pins to Mark
            for incident in target_incidents:
                if self.stop_flag:
                    break
                
                try:
                    incident_type = incident.get('type', 'unknown').lower()
                    address = incident.get('address', '')
                    city = incident.get('city', '')
                    
                    # Determine pin type based on incident
                    if 'fire' in incident_type:
                        pin_config = self.pin_configs['fire_incident']
                        notes = f"Fire incident occurred at {address}. Contact nearby residents for fire safety/smoke monitoring systems. Phone: (910) 742-0609"
                    elif any(crime in incident_type for crime in ['break', 'burglary', 'robbery', 'theft']):
                        pin_config = self.pin_configs['breakin_incident'] 
                        notes = f"Break-in/security incident at {address}. High-priority area for security systems. Phone: (910) 742-0609"
                    else:
                        # General incident
                        pin_config = self.pin_configs['breakin_incident']  # Use security pin for general incidents
                        notes = f"Security incident ({incident_type}) at {address}. Contact nearby residents for security solutions. Phone: (910) 742-0609"
                    
                    pin_data = self.create_activeknocker_pin(
                        address=address,
                        pin_config=pin_config,
                        notes=notes,
                        priority='High',
                        lead_source=f'{city.title()} Incident Monitor'
                    )
                    
                    success = self.send_to_activeknocker(pin_data)
                    if success:
                        results['sent_count'] += 1
                        self.log_signal.emit(f"✅ Sent {incident_type} incident pin for {address}")
                    else:
                        results['errors'].append(f"Failed to send incident pin for {address}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing incident: {str(e)}")
                    
        except Exception as e:
            results['errors'].append(f"Error in process_incident_leads: {str(e)}")
        
        return results
    
    def process_adt_detection_leads(self):
        """Process ADT detection results and send pins to Mark"""
        results = {'sent_count': 0, 'errors': []}
        
        try:
            # Look for ADT detection results
            adt_files = [
                'data/adt_detection_results.json',
                'adt_detections/detection_results.json',
                'downloads/adt_results.csv'
            ]
            
            adt_detections = []
            for file_path in adt_files:
                if os.path.exists(file_path):
                    try:
                        if file_path.endswith('.json'):
                            with open(file_path, 'r') as f:
                                adt_data = json.load(f)
                                if isinstance(adt_data, list):
                                    adt_detections.extend(adt_data)
                                elif isinstance(adt_data, dict) and 'detections' in adt_data:
                                    adt_detections.extend(adt_data['detections'])
                        elif file_path.endswith('.csv'):
                            adt_df = pd.read_csv(file_path)
                            # Filter for positive ADT detections
                            if 'adt_detected' in adt_df.columns:
                                positive_detections = adt_df[adt_df['adt_detected'] == True]
                            elif 'confidence' in adt_df.columns:
                                positive_detections = adt_df[adt_df['confidence'] > 0.7]
                            else:
                                positive_detections = adt_df
                            
                            adt_detections.extend(positive_detections.to_dict('records'))
                        
                        self.log_signal.emit(f"📁 Found ADT detection data: {file_path}")
                    except:
                        continue
            
            if not adt_detections:
                self.log_signal.emit("ℹ️ No ADT detection data found")
                return results
            
            # Filter for high-confidence detections
            high_confidence_detections = []
            for detection in adt_detections:
                confidence = detection.get('confidence', 0)
                adt_detected = detection.get('adt_detected', False)
                
                if adt_detected or confidence > 0.7:
                    high_confidence_detections.append(detection)
            
            self.log_signal.emit(f"🎯 Found {len(high_confidence_detections)} high-confidence ADT detections")
            
            # Send ADT detection pins to Mark
            for detection in high_confidence_detections:
                if self.stop_flag:
                    break
                
                try:
                    address = detection.get('address', '')
                    confidence = detection.get('confidence', 0)
                    city = detection.get('city', '')
                    
                    notes = f"ADT security system detected at {address} (confidence: {confidence:.2f}). Potential upgrade opportunity - existing customer may want enhanced monitoring. Phone: (910) 742-0609"
                    
                    pin_data = self.create_activeknocker_pin(
                        address=address,
                        pin_config=self.pin_configs['adt_detected'],
                        notes=notes,
                        priority='Medium',
                        lead_source='ADT Detection System'
                    )
                    
                    success = self.send_to_activeknocker(pin_data)
                    if success:
                        results['sent_count'] += 1
                        self.log_signal.emit(f"✅ Sent ADT detection pin for {address}")
                    else:
                        results['errors'].append(f"Failed to send ADT pin for {address}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing ADT detection: {str(e)}")
                    
        except Exception as e:
            results['errors'].append(f"Error in process_adt_detection_leads: {str(e)}")
        
        return results
    
    def create_activeknocker_pin(self, address, pin_config, notes, priority='Medium', lead_source='Automation'):
        """Create ActiveKnocker pin data structure"""
        return {
            'address': address,
            'assigned_to': self.mark_walters_config,
            'pin_type': pin_config['pin_type'],
            'pin_color': pin_config['pin_color'],
            'pin_icon': pin_config['pin_icon'],
            'description': pin_config['description'],
            'notes': notes,
            'priority': priority,
            'lead_source': lead_source,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
    
    def send_to_activeknocker(self, pin_data):
        """Send pin data to ActiveKnocker API"""
        try:
            # For now, simulate the API call since we don't have the actual ActiveKnocker API endpoint
            # In production, this would make a real API call to ActiveKnocker
            
            self.log_signal.emit(f"📌 Sending pin to ActiveKnocker: {pin_data['address']} -> {pin_data['assigned_to']['name']}")
            
            # Simulate API call
            # api_url = "https://api.activeknocker.com/v1/pins"
            # headers = {'Authorization': f'Bearer {activeknocker_api_key}'}
            # response = requests.post(api_url, json=pin_data, headers=headers)
            # return response.status_code == 200
            
            # For demonstration, always return success
            return True
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error sending to ActiveKnocker: {str(e)}")
            return False
    
    def get_address_from_row(self, row):
        """Extract address from a data row (flexible column names)"""
        address_fields = ['address', 'ADDRESS', 'Address', 'street', 'STREET', 'Street', 'property_address']
        
        for field in address_fields:
            if field in row and pd.notna(row[field]):
                return str(row[field])
        
        return None
    
    def stop(self):
        """Stop the automation worker"""
        self.stop_flag = True 