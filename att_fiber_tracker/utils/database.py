import sqlite3
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "fiber_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create road fiber status table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS road_fiber_status (
                        road_name TEXT PRIMARY KEY,
                        has_fiber BOOLEAN,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create road coordinates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS road_coordinates (
                        road_name TEXT PRIMARY KEY,
                        coordinates TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def get_road_fiber_status(self) -> Dict[str, List[Dict]]:
        """Get all roads with their fiber status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get roads with fiber
                cursor.execute("SELECT road_name FROM road_fiber_status WHERE has_fiber = 1")
                with_fiber = [{"name": row[0]} for row in cursor.fetchall()]
                
                # Get roads without fiber
                cursor.execute("SELECT road_name FROM road_fiber_status WHERE has_fiber = 0")
                without_fiber = [{"name": row[0]} for row in cursor.fetchall()]
                
                return {
                    "with_fiber": with_fiber,
                    "without_fiber": without_fiber
                }
        except Exception as e:
            logger.error(f"Error getting road fiber status: {str(e)}")
            return {"with_fiber": [], "without_fiber": []}

    def get_road_coordinates(self, road_name: str) -> Optional[List[List[float]]]:
        """Get cached coordinates for a road."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT coordinates FROM road_coordinates WHERE road_name = ?",
                    (road_name,)
                )
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
        except Exception as e:
            logger.error(f"Error getting road coordinates: {str(e)}")
            return None

    def save_road_coordinates(self, road_name: str, coordinates: List[List[float]]):
        """Save road coordinates to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO road_coordinates (road_name, coordinates) VALUES (?, ?)",
                    (road_name, json.dumps(coordinates))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving road coordinates: {str(e)}")
            raise 