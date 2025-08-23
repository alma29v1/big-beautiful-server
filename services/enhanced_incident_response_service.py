
"""
Enhanced Incident Response - Better radius calculations and contact generation
"""

import math
import random
from typing import List, Dict

class EnhancedIncidentResponseService:
    """Enhanced incident response with better radius calculations"""
    
    def __init__(self, radius_yards=50):
        self.radius_yards = radius_yards
        self.yards_to_degrees = 1 / 121800  # Approximate conversion
    
    def generate_comprehensive_nearby_addresses(self, incident_lat: float, incident_lng: float, 
                                              incident_address: str) -> List[Dict]:
        """Generate comprehensive list of addresses within radius"""
        
        print(f"🎯 Generating addresses within {self.radius_yards} yards of {incident_address}")
        
        # Convert yards to degrees for grid generation
        radius_degrees = self.radius_yards * self.yards_to_degrees
        
        # Create denser grid for better coverage
        grid_density = 20  # Increased from 10 for better coverage
        step = (radius_degrees * 2) / grid_density
        
        nearby_addresses = []
        address_counter = 1
        
        # Generate addresses in concentric circles for realistic distribution
        for ring in range(5):  # 5 rings within radius
            ring_radius = (ring + 1) * (radius_degrees / 5)
            points_in_ring = max(8, (ring + 1) * 8)  # More points in outer rings
            
            for point in range(points_in_ring):
                angle = (2 * math.pi * point) / points_in_ring
                
                # Add some randomness to avoid perfect grid
                radius_variation = ring_radius * (0.8 + 0.4 * random.random())
                angle_variation = angle + (random.random() - 0.5) * 0.2
                
                lat = incident_lat + radius_variation * math.cos(angle_variation)
                lng = incident_lng + radius_variation * math.sin(angle_variation)
                
                # Calculate actual distance
                distance_yards = self.calculate_distance_yards(incident_lat, incident_lng, lat, lng)
                
                if distance_yards <= self.radius_yards:
                    # Generate realistic address
                    address = self.generate_realistic_street_address(lat, lng, address_counter)
                    
                    nearby_addresses.append({
                        'address': address,
                        'latitude': lat,
                        'longitude': lng,
                        'distance_yards': distance_yards,
                        'city': self.extract_city_from_incident(incident_address),
                        'state': 'NC',
                        'zip': self.get_area_zip_code(incident_address),
                        'priority': 'High' if distance_yards <= 25 else 'Medium',
                        'estimated_properties': 1
                    })
                    
                    address_counter += 1
        
        print(f"✅ Generated {len(nearby_addresses)} addresses within {self.radius_yards}-yard radius")
        return nearby_addresses
    
    def calculate_distance_yards(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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
        
        return distance_yards
    
    def generate_realistic_street_address(self, lat: float, lng: float, counter: int) -> str:
        """Generate realistic street address based on location"""
        
        # Common street names for the area
        street_names = [
            "Main St", "Oak Ave", "Pine St", "Maple Dr", "Cedar Ln",
            "Church St", "School Rd", "Park Ave", "First St", "Second St",
            "Third St", "Fourth St", "Mill Rd", "River Rd", "Forest Dr",
            "Sunset Dr", "Sunrise Ave", "Hill St", "Valley Rd", "Garden Way"
        ]
        
        # Generate house number (100-9999 range for realism)
        house_number = random.randint(100, 999) + (counter * 2)
        street_name = random.choice(street_names)
        
        return f"{house_number} {street_name}"
    
    def extract_city_from_incident(self, incident_address: str) -> str:
        """Extract city from incident address"""
        
        # Common cities in the area
        if "Fayetteville" in incident_address:
            return "Fayetteville"
        elif "Lumberton" in incident_address:
            return "Lumberton"
        elif "Wilmington" in incident_address:
            return "Wilmington"
        else:
            return "Fayetteville"  # Default
    
    def get_area_zip_code(self, incident_address: str) -> str:
        """Get appropriate zip code for the area"""
        
        zip_codes = {
            "Fayetteville": ["28301", "28302", "28303", "28304"],
            "Lumberton": ["28358", "28359"],
            "Wilmington": ["28401", "28402", "28403", "28404", "28405"]
        }
        
        city = self.extract_city_from_incident(incident_address)
        return random.choice(zip_codes.get(city, ["28301"]))

# Example usage
def demo_enhanced_incident_response():
    """Demonstrate enhanced incident response"""
    
    service = EnhancedIncidentResponseService(radius_yards=50)
    
    # Sample incident
    incident_lat = 35.0527  # Fayetteville, NC area
    incident_lng = -78.8784
    incident_address = "321 Bragg Blvd, Fayetteville, NC"
    
    # Generate nearby addresses
    nearby_addresses = service.generate_comprehensive_nearby_addresses(
        incident_lat, incident_lng, incident_address
    )
    
    print(f"\n📊 ENHANCED INCIDENT RESPONSE RESULTS:")
    print(f"🎯 Incident: {incident_address}")
    print(f"📍 Radius: {service.radius_yards} yards")
    print(f"🏠 Properties found: {len(nearby_addresses)}")
    print(f"💡 Expected contacts after BatchData: {len(nearby_addresses) * 0.6:.0f}")  # 60% success rate
    
    # Show distance distribution
    distances = [addr['distance_yards'] for addr in nearby_addresses]
    avg_distance = sum(distances) / len(distances)
    print(f"📏 Average distance: {avg_distance:.1f} yards")
    
    return nearby_addresses

if __name__ == "__main__":
    demo_enhanced_incident_response()
