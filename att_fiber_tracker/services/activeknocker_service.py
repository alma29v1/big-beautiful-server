import requests
import os
import time
import urllib.parse

def geocode_address(address):
    """Geocode an address using the Census Geocoder API."""
    base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        matches = data.get("result", {}).get("addressMatches", [])
        if matches:
            coords = matches[0]["coordinates"]
            return coords["y"], coords["x"]  # lat, lon
    except Exception as e:
        print(f"[GEOCODE ERROR] {address}: {e}")
    return None, None

class ActiveKnockerService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ACTIVEKNOCKER_API_KEY")
        self.api_url = "https://api.activeknocker.com/knock-pin"
        self.get_pins_url = "https://api.activeknocker.com/knock-pins"
        self.headers = {"x-api-key": self.api_key}

    def send_lead(self, address, notes="Lead from AT&T Fiber Tracker", debug_log=None):
        lat, lon = geocode_address(address)
        payload = {
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "notes": notes
        }
        try:
            if debug_log:
                debug_log.write(f"\n=== Sending to ActiveKnocker ===\nPayload: {payload}\n")
            print(f"[SEND] {payload}")
            resp = requests.post(self.api_url, json=payload, headers=self.headers)
            if debug_log:
                debug_log.write(f"Response status: {resp.status_code}\nResponse body: {resp.text}\n")
            if resp.status_code == 200:
                print(f"[SENT] {address}")
            else:
                print(f"[FAIL] {address} | Status: {resp.status_code} | Body: {resp.text}")
                if debug_log:
                    debug_log.write(f"[FAIL] {address} | Status: {resp.status_code} | Body: {resp.text}\n")
        except Exception as e:
            print(f"[ERROR] {address} | {e}")
            if debug_log:
                debug_log.write(f"[ERROR] {address} | {e}\n")
        time.sleep(1)  # avoid rate limits

    def send_leads(self, addresses, debug_log_path="activeknocker_api_debug.log"):
        with open(debug_log_path, "a") as debug_log:
            for addr in addresses:
                self.send_lead(addr, debug_log=debug_log)

    def fetch_knock_pins(self):
        try:
            resp = requests.get(self.get_pins_url, headers=self.headers, timeout=15)
            print(f"[GET /knock-pins] Status: {resp.status_code}")
            print(resp.text)
            return resp.json()
        except Exception as e:
            print(f"[ERROR] Fetching knock pins: {e}")
            return None 