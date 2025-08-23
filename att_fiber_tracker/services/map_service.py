from typing import Dict, List, Optional
import folium
import logging
from datetime import datetime
from ..utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class MapService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.initial_location = [34.2563, -78.0447]  # Leland, NC coordinates
        self.initial_zoom = 12

    def create_fiber_map(self) -> folium.Map:
        """Create a map showing roads with and without fiber availability."""
        # Create the base map with a better tile layer
        fiber_map = folium.Map(
            location=self.initial_location,
            zoom_start=self.initial_zoom,
            tiles='CartoDB positron'  # Better looking tile layer
        )

        # Get road fiber status from database
        road_status = self.db_manager.get_road_fiber_status()

        # Create feature groups for better layer control
        fiber_group = folium.FeatureGroup(name='Fiber Available')
        no_fiber_group = folium.FeatureGroup(name='No Fiber')

        # Add roads with fiber (green)
        if road_status['with_fiber']:
            for road in road_status['with_fiber']:
                self._add_road_to_map(fiber_group, road, 'green')

        # Add roads without fiber (red)
        if road_status['without_fiber']:
            for road in road_status['without_fiber']:
                self._add_road_to_map(no_fiber_group, road, 'red')

        # Add feature groups to map
        fiber_group.add_to(fiber_map)
        no_fiber_group.add_to(fiber_map)

        # Add layer control
        folium.LayerControl().add_to(fiber_map)

        # Add a legend with better styling
        self._add_legend(fiber_map)

        # Add a title to the map
        title_html = '''
            <div style="position: fixed; 
                        top: 10px; left: 50px; width: 300px; height: 50px; 
                        border:2px solid grey; z-index:9999; background-color:white;
                        padding: 10px;">
                <h3 style="margin: 0;">AT&T Fiber Availability in Leland, NC</h3>
            </div>
        '''
        fiber_map.get_root().html.add_child(folium.Element(title_html))

        return fiber_map

    def _add_road_to_map(self, map_obj: folium.Map, road: Dict, color: str) -> None:
        """Add a road to the map with the specified color."""
        try:
            # Get coordinates for the road
            coordinates = self.db_manager.get_road_coordinates(road['name'])
            if coordinates:
                # Create a polyline for the road with better styling
                folium.PolyLine(
                    locations=coordinates,
                    color=color,
                    weight=4,  # Thicker lines
                    opacity=0.8,
                    popup=folium.Popup(
                        f"""
                        <div style='font-family: Arial, sans-serif;'>
                            <h4>{road['name']}</h4>
                            <p><b>Fiber Available:</b> {'Yes' if color == 'green' else 'No'}</p>
                            <p><b>Last Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                        </div>
                        """,
                        max_width=300
                    )
                ).add_to(map_obj)
        except Exception as e:
            logger.error(f"Error adding road {road['name']} to map: {str(e)}")

    def _add_legend(self, map_obj: folium.Map) -> None:
        """Add a legend to the map with better styling."""
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 180px; height: 110px; 
                    border:2px solid grey; z-index:9999; background-color:white;
                    padding: 10px; font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0;">Legend</h4>
            <p style="margin: 0;"><i class="fa fa-square fa-2x" style="color:green"></i> Fiber Available</p>
            <p style="margin: 0;"><i class="fa fa-square fa-2x" style="color:red"></i> No Fiber</p>
            <p style="margin: 10px 0 0 0; font-size: 0.8em;">Click on roads for details</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def save_map(self, map_obj: folium.Map, filename: str = "fiber_map.html") -> None:
        """Save the map to an HTML file."""
        try:
            map_obj.save(filename)
            logger.info(f"Map saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving map: {str(e)}")
            raise 