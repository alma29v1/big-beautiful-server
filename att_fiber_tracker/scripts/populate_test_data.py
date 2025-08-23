import sqlite3
from datetime import datetime
import json

# Sample roads in Leland, NC with their fiber status
TEST_ROADS = [
    {"name": "Village Road", "has_fiber": True},
    {"name": "Olde Waterford Way", "has_fiber": True},
    {"name": "Grandiflora Drive", "has_fiber": True},
    {"name": "Magnolia Greens Drive", "has_fiber": True},
    {"name": "Lanvale Road", "has_fiber": False},
    {"name": "Olde Point Drive", "has_fiber": False},
    {"name": "Waterford Way", "has_fiber": True},
    {"name": "Marsh Oak Drive", "has_fiber": True},
    {"name": "Leland Road", "has_fiber": True},
    {"name": "Old Fayetteville Road", "has_fiber": False}
]

# Sample coordinates for the roads (approximate)
ROAD_COORDINATES = {
    "Village Road": [[34.2563, -78.0447], [34.2570, -78.0430], [34.2575, -78.0415]],
    "Olde Waterford Way": [[34.2550, -78.0450], [34.2540, -78.0460], [34.2530, -78.0470]],
    "Grandiflora Drive": [[34.2580, -78.0420], [34.2590, -78.0410], [34.2600, -78.0400]],
    "Magnolia Greens Drive": [[34.2570, -78.0430], [34.2580, -78.0420], [34.2590, -78.0410]],
    "Lanvale Road": [[34.2560, -78.0450], [34.2550, -78.0460], [34.2540, -78.0470]],
    "Olde Point Drive": [[34.2555, -78.0445], [34.2565, -78.0435], [34.2575, -78.0425]],
    "Waterford Way": [[34.2540, -78.0460], [34.2530, -78.0470], [34.2520, -78.0480]],
    "Marsh Oak Drive": [[34.2585, -78.0415], [34.2595, -78.0405], [34.2605, -78.0395]],
    "Leland Road": [[34.2565, -78.0445], [34.2575, -78.0435], [34.2585, -78.0425]],
    "Old Fayetteville Road": [[34.2555, -78.0455], [34.2545, -78.0465], [34.2535, -78.0475]]
}

def populate_database():
    """Populate the database with test data."""
    conn = sqlite3.connect("fiber_data.db")
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS road_fiber_status (
            road_name TEXT PRIMARY KEY,
            has_fiber BOOLEAN,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS road_coordinates (
            road_name TEXT PRIMARY KEY,
            coordinates TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert test data
    for road in TEST_ROADS:
        # Insert road fiber status
        cursor.execute(
            "INSERT OR REPLACE INTO road_fiber_status (road_name, has_fiber) VALUES (?, ?)",
            (road["name"], road["has_fiber"])
        )

        # Insert road coordinates
        if road["name"] in ROAD_COORDINATES:
            cursor.execute(
                "INSERT OR REPLACE INTO road_coordinates (road_name, coordinates) VALUES (?, ?)",
                (road["name"], json.dumps(ROAD_COORDINATES[road["name"]]))
            )

    conn.commit()
    conn.close()
    print("Test data populated successfully!")

if __name__ == "__main__":
    populate_database() 