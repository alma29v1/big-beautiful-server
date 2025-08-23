from PySide6.QtCore import QThread, Signal
import time
import pandas as pd
import os
import requests
import re
import csv

class CustomATTWorker(QThread):
    """Worker for custom CSV import and AT&T fiber checking"""
    log_signal = Signal(str)
    progress_signal = Signal(str, int, int)  # city, current, total
    finished_signal = Signal(str, dict)  # city, results_data
    fiber_count_signal = Signal(str, int)  # city, fiber_count
    
    def __init__(self, csv_file_path, addresses=None):
        super().__init__()
        self.csv_file_path = csv_file_path
        self.custom_addresses = addresses
        self.stop_flag = False
    
    def run(self):
        """Process custom CSV or address list for AT&T fiber checking"""
        try:
            if self.custom_addresses:
                self.log_signal.emit("[CustomATT] Processing custom address list...")
                addresses = self.custom_addresses
            elif self.csv_file_path and os.path.exists(self.csv_file_path):
                self.log_signal.emit(f"[CustomATT] Processing CSV file: {self.csv_file_path}")
                addresses = self.load_addresses_from_csv(self.csv_file_path)
            else:
                self.log_signal.emit("[CustomATT] ❌ No valid input provided")
                self.finished_signal.emit("custom", {})
                return
            
            if not addresses:
                self.log_signal.emit("[CustomATT] ❌ No addresses to process")
                self.finished_signal.emit("custom", {})
                return
            
            self.log_signal.emit(f"[CustomATT] Starting fiber checks for {len(addresses)} addresses")
            
            # Load AT&T fiber blocks data
            att_csv = "/Users/seasidesecurity/Downloads/att_only.csv"
            if not os.path.exists(att_csv):
                self.log_signal.emit(f"[CustomATT] ❌ AT&T fiber data file not found: {att_csv}")
                self.finished_signal.emit("custom", {})
                return
            
            att_blocks = set()
            with open(att_csv, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    att_blocks.add(row["block_geoid"])
            
            self.log_signal.emit(f"[CustomATT] Loaded {len(att_blocks)} AT&T fiber blocks")
            
            # Process addresses
            fiber_count = 0
            no_fiber_count = 0
            address_results = []
            street_fiber_map = {}
            
            for i, address in enumerate(addresses):
                if self.stop_flag:
                    break
                
                self.progress_signal.emit("custom", i + 1, len(addresses))
                
                try:
                    # Clean address
                    if isinstance(address, dict):
                        # Handle dictionary format
                        clean_address = self.format_address_from_dict(address)
                    else:
                        # Handle string format
                        clean_address = re.split(r'[#Uu]nit|,\s*#', str(address))[0].strip()
                    
                    self.log_signal.emit(f"[CustomATT] Checking address {i+1}/{len(addresses)}: {clean_address}")
                    
                    # Parse address components
                    street_name = clean_address.split(',')[0].strip().lower()
                    city_val, state_val, zip_val = self.parse_address_components(clean_address)
                    
                    # Get census block GEOID
                    block_geoid = self.get_census_block_geoid(clean_address)
                    
                    if block_geoid:
                        has_fiber = block_geoid in att_blocks
                        if has_fiber:
                            fiber_count += 1
                            self.log_signal.emit(f"[CustomATT] ✅ FIBER AVAILABLE: {clean_address}")
                        else:
                            no_fiber_count += 1
                            self.log_signal.emit(f"[CustomATT] ❌ No fiber: {clean_address}")
                        
                        if street_name not in street_fiber_map:
                            street_fiber_map[street_name] = has_fiber
                        elif has_fiber:
                            street_fiber_map[street_name] = True
                    else:
                        # Try to infer from other addresses on same street
                        if street_name in street_fiber_map and street_fiber_map[street_name]:
                            has_fiber = True
                            fiber_inferred = True
                            fiber_count += 1
                            inferred_basis = f"Inferred from other address on street: {street_name}"
                            self.log_signal.emit(f"[CustomATT] ⚡️ INFERRED FIBER: {clean_address} (basis: {inferred_basis})")
                        else:
                            has_fiber = False
                            no_fiber_count += 1
                            self.log_signal.emit(f"[CustomATT] ❌ Census block lookup failed: {clean_address}")
                    
                    # Create result record
                    result = {
                        'address': clean_address,
                        'fiber_available': has_fiber,
                        'city': city_val,
                        'state': state_val,
                        'zip': zip_val,
                        'street': clean_address.split(',')[0].strip(),
                        'processed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'block_geoid': block_geoid,
                        'fiber_inferred': fiber_inferred if 'fiber_inferred' in locals() else False,
                        'source': 'custom_import'
                    }
                    
                    if 'inferred_basis' in locals():
                        result['inferred_basis'] = inferred_basis
                    
                    address_results.append(result)
                    
                except Exception as e:
                    self.log_signal.emit(f"[CustomATT] Error checking {clean_address}: {e}")
                    address_results.append({
                        'address': clean_address,
                        'fiber_available': False,
                        'city': city_val if 'city_val' in locals() else '',
                        'processed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'error': str(e),
                        'state': state_val if 'state_val' in locals() else '',
                        'zip': zip_val if 'zip_val' in locals() else '',
                        'source': 'custom_import'
                    })
                
                time.sleep(1)  # Rate limiting
            
            # Save results
            self.log_signal.emit(f"[CustomATT] ✅ COMPLETED: {fiber_count} with fiber, {no_fiber_count} without fiber")
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            out_file = f'custom_att_fiber_results_{timestamp}.csv'
            pd.DataFrame(address_results).to_csv(out_file, index=False)
            self.log_signal.emit(f"[CustomATT] Wrote fiber results to {out_file}")
            
            # Update master file
            master_file = 'att_fiber_master.csv'
            if os.path.exists(master_file):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.DataFrame()
            
            new_df = pd.DataFrame(address_results)
            all_df = pd.concat([master_df, new_df], ignore_index=True)
            all_df['processed_date'] = pd.to_datetime(all_df['processed_date'], errors='coerce')
            all_df = all_df.sort_values('processed_date').drop_duplicates('address', keep='last')
            
            # Keep only last 90 days
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
            all_df = all_df[all_df['processed_date'] >= cutoff]
            all_df.to_csv(master_file, index=False)
            
            self.log_signal.emit(f"[CustomATT] Updated master fiber file: {master_file}")
            self.fiber_count_signal.emit("custom", fiber_count)
            
            results_data = {
                'addresses': address_results,
                'fiber_count': fiber_count,
                'total_count': len(address_results),
                'output_file': out_file
            }
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Custom AT&T check failed: {e}")
            results_data = {}
        
        self.finished_signal.emit("custom", results_data)
    
    def load_addresses_from_csv(self, csv_file):
        """Load addresses from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            addresses = []
            
            # Try different column name variations
            address_columns = ['ADDRESS', 'Address', 'address', 'STREET', 'Street', 'street']
            city_columns = ['CITY', 'City', 'city']
            state_columns = ['STATE', 'State', 'state', 'STATE OR PROVINCE']
            zip_columns = ['ZIP', 'Zip', 'zip', 'ZIP OR POSTAL CODE', 'ZIPCODE']
            
            address_col = None
            city_col = None
            state_col = None
            zip_col = None
            
            for col in address_columns:
                if col in df.columns:
                    address_col = col
                    break
            
            for col in city_columns:
                if col in df.columns:
                    city_col = col
                    break
            
            for col in state_columns:
                if col in df.columns:
                    state_col = col
                    break
            
            for col in zip_columns:
                if col in df.columns:
                    zip_col = col
                    break
            
            if not address_col:
                self.log_signal.emit("[CustomATT] ❌ No address column found in CSV")
                return []
            
            for _, row in df.iterrows():
                address = str(row[address_col]).strip()
                if pd.notna(address) and address != 'nan':
                    if city_col and state_col and zip_col:
                        city = str(row[city_col]).strip()
                        state = str(row[state_col]).strip()
                        zip_code = str(row[zip_col]).strip()
                        full_address = f"{address}, {city}, {state} {zip_code}"
                    else:
                        full_address = address
                    
                    addresses.append(full_address)
            
            return addresses
            
        except Exception as e:
            self.log_signal.emit(f"[CustomATT] Error loading CSV: {e}")
            return []
    
    def format_address_from_dict(self, address_dict):
        """Format address from dictionary"""
        try:
            address = address_dict.get('address', '')
            city = address_dict.get('city', '')
            state = address_dict.get('state', '')
            zip_code = address_dict.get('zip', '')
            
            if city and state and zip_code:
                return f"{address}, {city}, {state} {zip_code}"
            else:
                return address
        except:
            return str(address_dict)
    
    def parse_address_components(self, address):
        """Parse address into components"""
        try:
            m = re.match(r'^(.*),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$', address)
            if m:
                city_val = m.group(2).strip()
                state_val = m.group(3).strip()
                zip_val = m.group(4).strip()
            else:
                parts = address.split(',')
                if len(parts) >= 3:
                    city_val = parts[1].strip()
                    state_zip = parts[2].strip().split()
                    if len(state_zip) == 2:
                        state_val, zip_val = state_zip
                    elif len(state_zip) == 1:
                        state_val = state_zip[0]
                        zip_val = ''
                    else:
                        state_val = ''
                        zip_val = ''
                else:
                    city_val = ''
                    state_val = ''
                    zip_val = ''
            
            return city_val, state_val, zip_val
        except:
            return '', '', ''
    
    def get_census_block_geoid(self, address, lat=None, lon=None):
        """Get census block GEOID for an address"""
        # Try Census Geocoder first
        census_url = f"https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?address={requests.utils.quote(address)}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
        
        try:
            resp = requests.get(census_url, timeout=10)
            data = resp.json()
            matches = data.get('result', {}).get('addressMatches', [])
            
            if matches:
                geographies = matches[0].get('geographies', {})
                blocks = geographies.get('Census Blocks', [])
                if blocks and 'GEOID' in blocks[0]:
                    return blocks[0]['GEOID']
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Census Geocoder exception: {e}")
        
        # If no lat/lon, geocode with Google
        if lat is None or lon is None:
            lat, lon = self.geocode_with_google(address)
        
        if lat is not None and lon is not None:
            # Try Census coordinate lookup
            coord_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lon}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
            
            try:
                resp = requests.get(coord_url, timeout=10)
                data = resp.json()
                blocks = data.get('result', {}).get('geographies', {}).get('Census Blocks', [])
                if blocks and 'GEOID' in blocks[0]:
                    return blocks[0]['GEOID']
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Census Coord exception: {e}")
            
            # Try FCC Block API
            fcc_url = f"https://geo.fcc.gov/api/census/block/find?latitude={lat}&longitude={lon}&format=json"
            
            try:
                resp = requests.get(fcc_url, timeout=10)
                data = resp.json()
                geoid = data.get('Block', {}).get('FIPS')
                if geoid:
                    return geoid
            except Exception as e:
                self.log_signal.emit(f"[ERROR] FCC Block API exception: {e}")
        
        return None
    
    def geocode_with_google(self, address):
        """Geocode address using Google Maps API"""
        GOOGLE_API_KEY = "AIzaSyBpH5E2KKGo-GypuWA8Mj_RpKXUOHQuhkI"
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&key={GOOGLE_API_KEY}"
        
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Google geocoding exception: {e}")
        
        return None, None
    
    def stop(self):
        """Stop the worker"""
        self.stop_flag = True 