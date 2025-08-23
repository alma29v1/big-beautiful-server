from PySide6.QtCore import QThread, Signal
import os
import glob
import pandas as pd
import time
import requests
import re
import csv
import urllib.parse
from utils.api_cost_tracker import track_google_maps_usage

class ATTWorker(QThread):
    """Worker for checking AT&T fiber availability - NO BatchData collection here"""
    log_signal = Signal(str)
    progress_signal = Signal(str, int, int)  # city, current, total
    finished_signal = Signal(str, dict)  # city, results_data
    fiber_count_signal = Signal(str, int)  # city, fiber_count
    
    def __init__(self, city_name):
        super().__init__()
        self.city_name = city_name
    
    def run(self):
        """Check AT&T fiber for addresses in this city using FCC data and geocoding"""
        try:
            # Load AT&T fiber blocks data
            att_csv = "/Users/seasidesecurity/Downloads/att_only.csv"
            if not os.path.exists(att_csv):
                self.log_signal.emit(f"[AT&T] ❌ AT&T fiber data file not found: {att_csv}")
                self.finished_signal.emit(self.city_name, {})
                return
                
            att_blocks = set()
            with open(att_csv, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    att_blocks.add(row["block_geoid"])
            
            self.log_signal.emit(f"[AT&T] Loaded {len(att_blocks)} AT&T fiber blocks")
            
            # Find latest Redfin CSV for this city
            project_dir = os.path.dirname(os.path.abspath(__file__))
            csv_pattern = os.path.join(project_dir, '../downloads', self.city_name.lower(), '*.csv')
            csv_files = sorted(glob.glob(csv_pattern), key=os.path.getmtime, reverse=True)
            
            if not csv_files:
                self.log_signal.emit(f"[AT&T] No CSV files found for {self.city_name}")
                self.finished_signal.emit(self.city_name, {})
                return
                
            df = pd.read_csv(csv_files[0])
            city_df = df[df['CITY'].str.contains(self.city_name, case=False, na=False)]
            
            if city_df.empty:
                self.log_signal.emit(f"[AT&T] No addresses found for {self.city_name}")
                self.finished_signal.emit(self.city_name, {})
                return
                
            # Prepare addresses
            addresses = []
            for _, row in city_df.iterrows():
                if pd.notna(row.get('ADDRESS')) and pd.notna(row.get('ZIP OR POSTAL CODE')):
                    zip_code = str(row['ZIP OR POSTAL CODE']).replace('.0', '')
                    address = f"{row['ADDRESS']}, {row['CITY']}, {row['STATE OR PROVINCE']} {zip_code}"
                    addresses.append(address)
            
            if not addresses:
                self.log_signal.emit(f"[AT&T] No valid addresses found for {self.city_name}")
                self.finished_signal.emit(self.city_name, {})
                return
                
            # Check for already processed addresses
            master_file = 'att_fiber_master.csv'
            already_processed = set()
            if os.path.exists(master_file):
                master_df = pd.read_csv(master_file)
                already_processed = set(master_df['address'].str.lower().str.strip())
            
            orig_count = len(addresses)
            addresses = [a for a in addresses if a.lower().strip() not in already_processed]
            skipped_count = orig_count - len(addresses)
            
            if skipped_count > 0:
                self.log_signal.emit(f"[AT&T] Skipping {skipped_count} addresses already processed in last 3 months.")
            
            if not addresses:
                self.log_signal.emit(f"[AT&T] All addresses already processed for {self.city_name} (last 3 months). Nothing to do.")
                self.finished_signal.emit(self.city_name, {})
                return
                
            self.log_signal.emit(f"[AT&T] Starting FCC fiber checks for {len(addresses)} addresses in {self.city_name}")
            
            fiber_count = 0
            no_fiber_count = 0
            address_results = []
            street_fiber_map = {}
            
            for i, address in enumerate(addresses):
                clean_address = re.split(r'[#Uu]nit|,\s*#', address)[0].strip()
                self.log_signal.emit(f"[AT&T] Geocoding address {i+1}/{len(addresses)}: {clean_address}")
                self.progress_signal.emit(self.city_name, i + 1, len(addresses))
                
                street_name = clean_address.split(',')[0].strip().lower()
                block_geoid = None
                fiber_inferred = False
                inferred_basis = None
                city_val, state_val, zip_val = '', '', ''
                
                # Parse address components
                try:
                    m = re.match(r'^(.*),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$', clean_address)
                    if m:
                        city_val = m.group(2).strip()
                        state_val = m.group(3).strip()
                        zip_val = m.group(4).strip()
                    else:
                        parts = clean_address.split(',')
                        if len(parts) >= 3:
                            city_val = parts[1].strip()
                            state_zip = parts[2].strip().split()
                            if len(state_zip) == 2:
                                state_val, zip_val = state_zip
                            elif len(state_zip) == 1:
                                state_val = state_zip[0]
                except Exception:
                    pass
                
                if not city_val:
                    city_val = self.city_name
                
                # Get census block GEOID
                try:
                    block_geoid = self.get_census_block_geoid(clean_address)
                    
                    if block_geoid:
                        has_fiber = block_geoid in att_blocks
                        if has_fiber:
                            fiber_count += 1
                            self.log_signal.emit(f"[AT&T] ✅ FIBER AVAILABLE: {clean_address}")
                        else:
                            no_fiber_count += 1
                            self.log_signal.emit(f"[AT&T] ❌ No fiber: {clean_address}")
                        
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
                            self.log_signal.emit(f"[AT&T] ⚡️ INFERRED FIBER: {clean_address} (basis: {inferred_basis})")
                        else:
                            has_fiber = False
                            no_fiber_count += 1
                            self.log_signal.emit(f"[AT&T] ❌ Census block lookup failed: {clean_address}")
                    
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
                        'fiber_inferred': fiber_inferred,
                        'orig_street': row.get('ADDRESS', ''),
                        'orig_city': row.get('CITY', ''),
                        'orig_state': row.get('STATE OR PROVINCE', ''),
                        'orig_zip': str(row.get('ZIP OR POSTAL CODE', '')).replace('.0', '')
                    }
                    
                    if fiber_inferred and inferred_basis:
                        result['inferred_basis'] = inferred_basis
                    
                    address_results.append(result)
                    
                except Exception as e:
                    self.log_signal.emit(f"[AT&T] Error checking {clean_address}: {e}")
                    address_results.append({
                        'address': clean_address,
                        'fiber_available': False,
                        'city': self.city_name,
                        'processed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'error': str(e),
                        'state': state_val,
                        'zip': zip_val
                    })
                
                time.sleep(1)  # Rate limiting
            
            # Save results
            self.log_signal.emit(f"[AT&T] ✅ FCC COMPLETED {self.city_name}: {fiber_count} with fiber, {no_fiber_count} without fiber")
            
            today_str = time.strftime('%Y%m%d')
            out_file = f'att_fiber_results_{self.city_name.lower()}_{today_str}.csv'
            pd.DataFrame(address_results).to_csv(out_file, index=False)
            self.log_signal.emit(f"[AT&T] Wrote fiber results to {out_file}")
            
            # Update master file
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
            
            self.log_signal.emit(f"[AT&T] Updated master fiber file: {master_file} (last 3 months)")
            self.fiber_count_signal.emit(self.city_name, fiber_count)
            
            results_data = {
                'addresses': address_results,
                'fiber_count': fiber_count,
                'total_count': len(address_results)
            }
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] AT&T FCC check failed for {self.city_name}: {e}")
            results_data = {}
            
        self.finished_signal.emit(self.city_name, results_data)

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
        
        self.log_signal.emit(f"[FAIL] Could not get GEOID for: {address} (lat={lat}, lon={lon})")
        return None

    def geocode_with_google(self, address):
        """Geocode address using Google Maps API"""
        # Use the API key from environment or config
        GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY') or os.getenv('GOOGLE_VISION_API_KEY')
        
        if not GOOGLE_API_KEY:
            self.log_signal.emit(f"[GEOCODE] ❌ No Google API key found in environment")
            return None, None
        
        # Clean up the address for better geocoding
        clean_address = address.strip()
        
        # URL encode the address properly
        encoded_address = urllib.parse.quote(clean_address)
        
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={GOOGLE_API_KEY}"
        
        try:
            self.log_signal.emit(f"[GEOCODE] Attempting to geocode: {clean_address}")
            resp = requests.get(url, timeout=15)
            
            if resp.status_code != 200:
                self.log_signal.emit(f"[GEOCODE] HTTP Error {resp.status_code} for: {clean_address}")
                return None, None
                
            data = resp.json()
            
            if data.get("status") == "OK" and data.get("results"):
                # Track successful API usage
                track_google_maps_usage(1, "geocoding")
                
                loc = data["results"][0]["geometry"]["location"]
                lat, lng = loc["lat"], loc["lng"]
                self.log_signal.emit(f"[GEOCODE] ✅ Success: {clean_address} -> ({lat}, {lng})")
                return lat, lng
            elif data.get("status") == "ZERO_RESULTS":
                self.log_signal.emit(f"[GEOCODE] ❌ No results found for: {clean_address}")
                return None, None
            elif data.get("status") == "OVER_QUERY_LIMIT":
                self.log_signal.emit(f"[GEOCODE] ❌ Google API quota exceeded")
                return None, None
            elif data.get("status") == "REQUEST_DENIED":
                self.log_signal.emit(f"[GEOCODE] ❌ Google API request denied - check API key")
                return None, None
            else:
                self.log_signal.emit(f"[GEOCODE] ❌ API Error: {data.get('status')} for {clean_address}")
                return None, None
                
        except requests.exceptions.Timeout:
            self.log_signal.emit(f"[GEOCODE] ❌ Timeout for: {clean_address}")
            return None, None
        except requests.exceptions.RequestException as e:
            self.log_signal.emit(f"[GEOCODE] ❌ Request error for {clean_address}: {e}")
            return None, None
        except Exception as e:
            self.log_signal.emit(f"[GEOCODE] ❌ Unexpected error for {clean_address}: {e}")
            return None, None 