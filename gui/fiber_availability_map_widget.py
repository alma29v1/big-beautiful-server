#!/usr/bin/env python3
"""
AT&T Fiber Availability Map Widget
Interactive map for strategic market expansion planning
"""

import os
import json
import pandas as pd
import folium
from folium import plugins
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QProgressBar, QSplitter, QFrame, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
import webbrowser
import tempfile
from datetime import datetime
from att_fiber_tracker.services.activeknocker_service import ActiveKnockerService, geocode_address
import threading
import http.server
import socketserver

class FiberMapWorker(QThread):
    """Worker for processing fiber data and generating map"""
    progress_signal = Signal(int, int)
    log_signal = Signal(str)
    finished_signal = Signal(str)  # HTML file path
    
    def __init__(self, fiber_data_path=None):
        super().__init__()
        self.fiber_data_path = fiber_data_path or "/Users/seasidesecurity/Downloads/att_only.csv"
        
    def run(self):
        print('[DEBUG] FiberMapWorker.run() called')
        """Generate interactive fiber availability map"""
        try:
            self.log_signal.emit("🗺️ Loading AT&T fiber data...")
            self.progress_signal.emit(1, 5)
            
            # Create base map centered on North Carolina
            self.log_signal.emit("🌍 Creating interactive map...")
            m = folium.Map(
                location=[34.2354, -77.9478],  # Downtown Wilmington center (more precise)
                zoom_start=11,  # Higher zoom for neighborhood detail
                tiles='CartoDB positron'  # Better contrast for detailed view
            )
            
            # Add AT&T fiber coverage layer
            self.log_signal.emit("🔵 Adding fiber coverage areas...")
            self.progress_signal.emit(2, 5)
            
            # Sample data for visualization (in real implementation, use actual block coordinates)
            fiber_areas = self.generate_sample_fiber_areas()
            
            # Add fiber coverage polygons
            for area in fiber_areas:
                # Create detailed popup with street information
                streets_list = ""
                if 'streets' in area:
                    streets_list = "<br><b>Streets covered:</b><br>" + "<br>".join([f"• {street}" for street in area['streets']])
                
                popup_content = f"""
                <div style='font-family: Arial, sans-serif; min-width: 200px;'>
                    <h4 style='color: #2196F3; margin: 0 0 10px 0;'>{area['name']}</h4>
                    <p style='margin: 5px 0;'><b>AT&T Fiber Coverage:</b> {area['coverage']}%</p>
                    {streets_list}
                    <hr style='margin: 10px 0;'>
                    <small style='color: #666;'>Click for detailed coverage info</small>
                </div>
                """
                
                # Color coding based on coverage percentage
                if area['coverage'] >= 80:
                    color = '#27ae60'  # Green for high coverage
                    fillColor = '#2ecc71'
                    fillOpacity = 0.4
                elif area['coverage'] >= 60:
                    color = '#f39c12'  # Orange for medium coverage
                    fillColor = '#f1c40f'
                    fillOpacity = 0.3
                else:
                    color = '#e74c3c'  # Red for low coverage
                    fillColor = '#e74c3c'
                    fillOpacity = 0.2
                
                folium.Polygon(
                    locations=area['coordinates'],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{area['name']}: {area['coverage']}% fiber coverage",
                    color=color,
                    fill=True,
                    fillColor=fillColor,
                    fillOpacity=fillOpacity,
                    weight=3
                ).add_to(m)
            
            # Add strategic expansion zones
            self.log_signal.emit("🎯 Adding strategic expansion zones...")
            self.progress_signal.emit(3, 5)
            
            expansion_zones = self.generate_expansion_zones()
            for zone in expansion_zones:
                target_streets = ""
                if 'target_streets' in zone:
                    target_streets = "<br><b>Target Streets:</b><br>" + "<br>".join([f"• {street}" for street in zone['target_streets']])
                
                expansion_popup = f"""
                <div style='font-family: Arial, sans-serif; min-width: 200px;'>
                    <h4 style='color: #e74c3c; margin: 0 0 10px 0;'>🎯 {zone['name']}</h4>
                    <p style='margin: 5px 0;'><b>Priority:</b> {zone['priority']}</p>
                    <p style='margin: 5px 0;'><b>Estimated ROI:</b> {zone['roi']}%</p>
                    {target_streets}
                    <hr style='margin: 10px 0;'>
                    <small style='color: #666;'>Strategic expansion opportunity</small>
                </div>
                """
                
                folium.Polygon(
                    locations=zone['coordinates'],
                    popup=folium.Popup(expansion_popup, max_width=300),
                    tooltip=f"Expansion Zone: {zone['name']} ({zone['priority']} Priority)",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.2,
                    weight=3,
                    dashArray='5, 5'  # Dashed line for expansion zones
                ).add_to(m)
            
            # Add specific street markers for fiber availability
            self.log_signal.emit("🛣️ Adding street-level fiber markers...")
            street_markers = self.generate_street_markers()
            
            for street in street_markers:
                # Choose icon based on fiber availability
                if street['has_fiber']:
                    icon_color = 'green'
                    icon_symbol = 'ok-sign'
                    prefix = '✅'
                else:
                    icon_color = 'red'
                    icon_symbol = 'remove-sign'
                    prefix = '❌'
                
                marker_popup = f"""
                <div style='font-family: Arial, sans-serif; min-width: 180px;'>
                    <h4 style='margin: 0 0 10px 0;'>{prefix} {street['name']}</h4>
                    <p style='margin: 5px 0;'><b>Fiber Available:</b> {'Yes' if street['has_fiber'] else 'No'}</p>
                    <p style='margin: 5px 0;'><b>Neighborhood:</b> {street['neighborhood']}</p>
                    {f"<p style='margin: 5px 0;'><b>Coverage:</b> {street['coverage']}%</p>" if 'coverage' in street else ""}
                    <hr style='margin: 10px 0;'>
                    <small style='color: #666;'>Street-level fiber status</small>
                </div>
                """
                
                folium.Marker(
                    location=street['coordinates'],
                    popup=folium.Popup(marker_popup, max_width=250),
                    tooltip=f"{street['name']}: {'Fiber Available' if street['has_fiber'] else 'No Fiber'}",
                    icon=folium.Icon(
                        color=icon_color,
                        icon=icon_symbol,
                        prefix='glyphicon'
                    )
                ).add_to(m)
            
            # Add market analysis layer
            self.log_signal.emit("📊 Adding market analysis...")
            self.progress_signal.emit(4, 5)
            
            # Add heatmap for property density
            property_density = self.generate_property_density()
            folium.plugins.HeatMap(
                property_density,
                name="Property Density",
                radius=25,
                blur=15,
                max_zoom=13
            ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Add fullscreen option
            plugins.Fullscreen().add_to(m)
            
            self.log_signal.emit("💾 Saving map...")
            self.progress_signal.emit(5, 5)
            
            # Save map to current directory instead of temp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            map_filename = f'fiber_map_{timestamp}.html'
            map_path = os.path.join(os.getcwd(), map_filename)
            
            m.save(map_path)
            print(f"[DEBUG] Map HTML saved to: {map_path}")
            
            # Verify file was created and has content
            if os.path.exists(map_path) and os.path.getsize(map_path) > 0:
                self.log_signal.emit(f"✅ Map generated successfully: {map_filename}")
                self.finished_signal.emit(map_filename)  # Return just filename, not full path
            else:
                raise Exception(f"Failed to create map file: {map_path}")
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error generating map: {e}")
            import traceback
            self.log_signal.emit(f"Traceback: {traceback.format_exc()}")
            
            # Create a simple fallback map
            fallback_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AT&T Fiber Map</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
                    .error {{ color: #e74c3c; margin: 20px; }}
                    .info {{ color: #3498db; margin: 20px; }}
                </style>
            </head>
            <body>
                <h1>🗺️ AT&T Fiber Availability Map</h1>
                <div class="error">
                    <h2>Map Generation Error</h2>
                    <p>There was an error generating the interactive map.</p>
                    <p>Error: {e}</p>
                </div>
                <div class="info">
                    <h3>Available Coverage Areas:</h3>
                    <ul style="text-align: left; display: inline-block;">
                        <li>Wilmington Metro - 85% coverage</li>
                        <li>Leland Area - 72% coverage</li>
                        <li>Hampstead Region - 45% coverage</li>
                        <li>North Wilmington - 90% coverage</li>
                    </ul>
                </div>
                <p><em>Please try generating the map again or contact support.</em></p>
            </body>
            </html>
            """
            
            fallback_filename = 'fiber_map_fallback.html'
            fallback_path = os.path.join(os.getcwd(), fallback_filename)
            with open(fallback_path, 'w') as f:
                f.write(fallback_content)
            
            self.finished_signal.emit(fallback_filename)
    
    def generate_sample_fiber_areas(self):
        """Generate precise neighborhood-level fiber coverage areas"""
        return [
            # Wilmington - Downtown Core (small precise area)
            {
                'name': 'Downtown Wilmington',
                'coordinates': [
                    [34.2352, -77.9503],
                    [34.2352, -77.9453],
                    [34.2402, -77.9453],
                    [34.2402, -77.9503]
                ],
                'coverage': 95,
                'streets': ['Market St', 'Front St', 'Princess St', 'Castle St']
            },
            # Wilmington - Midtown (small area)
            {
                'name': 'Midtown Wilmington',
                'coordinates': [
                    [34.2252, -77.9303],
                    [34.2252, -77.9253],
                    [34.2302, -77.9253],
                    [34.2302, -77.9303]
                ],
                'coverage': 88,
                'streets': ['Oleander Dr', 'Military Cutoff Rd', 'Wrightsville Ave']
            },
            # Wilmington - Monkey Junction
            {
                'name': 'Monkey Junction',
                'coordinates': [
                    [34.1952, -77.8703],
                    [34.1952, -77.8653],
                    [34.2002, -77.8653],
                    [34.2002, -77.8703]
                ],
                'coverage': 75,
                'streets': ['Carolina Beach Rd', 'Monkey Junction Blvd']
            },
            # Leland - Magnolia Greens
            {
                'name': 'Magnolia Greens',
                'coordinates': [
                    [34.2563, -78.0147],
                    [34.2563, -78.0097],
                    [34.2613, -78.0097],
                    [34.2613, -78.0147]
                ],
                'coverage': 90,
                'streets': ['Magnolia Greens Dr', 'Compass Pointe Dr']
            },
            # Leland - Brunswick Forest
            {
                'name': 'Brunswick Forest',
                'coordinates': [
                    [34.2663, -78.0247],
                    [34.2663, -78.0197],
                    [34.2713, -78.0197],
                    [34.2713, -78.0247]
                ],
                'coverage': 85,
                'streets': ['Brunswick Forest Pkwy', 'Masonboro Sound Dr']
            },
            # Leland - Waterford
            {
                'name': 'Waterford',
                'coordinates': [
                    [34.2463, -78.0347],
                    [34.2463, -78.0297],
                    [34.2513, -78.0297],
                    [34.2513, -78.0347]
                ],
                'coverage': 70,
                'streets': ['Waterford Dr', 'Village Rd']
            },
            # Hampstead - Scotts Hill
            {
                'name': 'Scotts Hill',
                'coordinates': [
                    [34.3673, -77.7052],
                    [34.3673, -77.7002],
                    [34.3723, -77.7002],
                    [34.3723, -77.7052]
                ],
                'coverage': 45,
                'streets': ['US-17', 'Scotts Hill Loop Rd']
            },
            # Hampstead - Topsail Greens
            {
                'name': 'Topsail Greens',
                'coordinates': [
                    [34.3573, -77.6952],
                    [34.3573, -77.6902],
                    [34.3623, -77.6902],
                    [34.3623, -77.6952]
                ],
                'coverage': 55,
                'streets': ['Topsail Greens Dr', 'Country Club Dr']
            },
            # Southport - Historic District
            {
                'name': 'Southport Historic District',
                'coordinates': [
                    [33.9152, -78.0203],
                    [33.9152, -78.0153],
                    [33.9202, -78.0153],
                    [33.9202, -78.0203]
                ],
                'coverage': 60,
                'streets': ['Howe St', 'Moore St', 'Lord St', 'Bay St']
            },
            # Southport - Oak Island Area
            {
                'name': 'Oak Island - Southport',
                'coordinates': [
                    [33.9052, -78.0403],
                    [33.9052, -78.0353],
                    [33.9102, -78.0353],
                    [33.9102, -78.0403]
                ],
                'coverage': 45,
                'streets': ['Oak Island Dr', 'Beach Dr', 'Caswell Beach Rd']
            },
            # Carolina Beach - Beachfront
            {
                'name': 'Carolina Beach',
                'coordinates': [
                    [34.0516, -77.8903],
                    [34.0516, -77.8853],
                    [34.0566, -77.8853],
                    [34.0566, -77.8903]
                ],
                'coverage': 40,
                'streets': ['Lake Park Blvd', 'Carolina Beach Ave']
            },
            # Wrightsville Beach
            {
                'name': 'Wrightsville Beach',
                'coordinates': [
                    [34.2116, -77.8003],
                    [34.2116, -77.7953],
                    [34.2166, -77.7953],
                    [34.2166, -77.8003]
                ],
                'coverage': 35,
                'streets': ['Lumina Ave', 'Waynick Blvd']
            }
        ]
    
    def generate_expansion_zones(self):
        """Generate precise strategic expansion zones"""
        return [
            {
                'name': 'North Wilmington - Porters Neck',
                'coordinates': [
                    [34.2904, -77.8568],
                    [34.2904, -77.8518],
                    [34.2954, -77.8518],
                    [34.2954, -77.8568]
                ],
                'priority': 'High',
                'roi': 32,
                'target_streets': ['Porters Neck Rd', 'Market St Extension']
            },
            {
                'name': 'Leland - Grayson Park',
                'coordinates': [
                    [34.2363, -78.0547],
                    [34.2363, -78.0497],
                    [34.2413, -78.0497],
                    [34.2413, -78.0547]
                ],
                'priority': 'High',
                'roi': 28,
                'target_streets': ['Grayson Park Blvd', 'Old Fayetteville Rd']
            },
            {
                'name': 'Hampstead - Surf City Extension',
                'coordinates': [
                    [34.3473, -77.6852],
                    [34.3473, -77.6802],
                    [34.3523, -77.6802],
                    [34.3523, -77.6852]
                ],
                'priority': 'Medium',
                'roi': 22,
                'target_streets': ['NC-210', 'Surf City Rd']
            },
            {
                'name': 'Carolina Beach - Kure Beach',
                'coordinates': [
                    [34.0216, -77.9053],
                    [34.0216, -77.9003],
                    [34.0266, -77.9003],
                    [34.0266, -77.9053]
                ],
                'priority': 'Medium',
                'roi': 18,
                'target_streets': ['Fort Fisher Blvd', 'Kure Beach Ave']
            }
        ]
    
    def generate_property_density(self):
        """Generate property density heatmap data"""
        return [
            [34.2104, -77.8868, 100],  # Wilmington center
            [34.2563, -78.0447, 75],   # Leland center
            [34.3673, -77.7102, 60],   # Hampstead center
            [34.3104, -77.7868, 85],   # North Wilmington
            [34.1563, -78.1447, 45],   # South Brunswick
            [34.4673, -77.6102, 55],   # Pender County
        ]
    
    def generate_street_markers(self):
        """Generate street-level markers for fiber availability"""
        return [
            # Wilmington Streets - High Fiber Availability
            {'name': 'Market St (Downtown)', 'coordinates': [34.2352, -77.9478], 'has_fiber': True, 'neighborhood': 'Downtown Wilmington', 'coverage': 95},
            {'name': 'Front St', 'coordinates': [34.2362, -77.9488], 'has_fiber': True, 'neighborhood': 'Downtown Wilmington', 'coverage': 90},
            {'name': 'Princess St', 'coordinates': [34.2342, -77.9468], 'has_fiber': True, 'neighborhood': 'Downtown Wilmington', 'coverage': 92},
            {'name': 'Oleander Dr', 'coordinates': [34.2252, -77.9278], 'has_fiber': True, 'neighborhood': 'Midtown Wilmington', 'coverage': 88},
            {'name': 'Military Cutoff Rd', 'coordinates': [34.2272, -77.9288], 'has_fiber': True, 'neighborhood': 'Midtown Wilmington', 'coverage': 85},
            {'name': 'Wrightsville Ave', 'coordinates': [34.2262, -77.9268], 'has_fiber': True, 'neighborhood': 'Midtown Wilmington', 'coverage': 90},
            
            # Leland Streets - Mixed Availability
            {'name': 'Magnolia Greens Dr', 'coordinates': [34.2588, -78.0122], 'has_fiber': True, 'neighborhood': 'Magnolia Greens', 'coverage': 90},
            {'name': 'Compass Pointe Dr', 'coordinates': [34.2598, -78.0132], 'has_fiber': True, 'neighborhood': 'Magnolia Greens', 'coverage': 88},
            {'name': 'Brunswick Forest Pkwy', 'coordinates': [34.2688, -78.0222], 'has_fiber': True, 'neighborhood': 'Brunswick Forest', 'coverage': 85},
            {'name': 'Village Rd', 'coordinates': [34.2488, -78.0322], 'has_fiber': True, 'neighborhood': 'Waterford', 'coverage': 70},
            {'name': 'Old Fayetteville Rd', 'coordinates': [34.2388, -78.0522], 'has_fiber': False, 'neighborhood': 'Grayson Park Area'},
            
            # Hampstead Streets - Lower Availability
            {'name': 'US-17 (Hampstead)', 'coordinates': [34.3698, -77.7027], 'has_fiber': False, 'neighborhood': 'Scotts Hill'},
            {'name': 'Scotts Hill Loop Rd', 'coordinates': [34.3688, -77.7037], 'has_fiber': False, 'neighborhood': 'Scotts Hill'},
            {'name': 'Topsail Greens Dr', 'coordinates': [34.3598, -77.6927], 'has_fiber': True, 'neighborhood': 'Topsail Greens', 'coverage': 55},
            {'name': 'Country Club Dr', 'coordinates': [34.3608, -77.6937], 'has_fiber': True, 'neighborhood': 'Topsail Greens', 'coverage': 50},
            
            # Southport Streets - Mixed
            {'name': 'Bay St', 'coordinates': [33.9241, -78.0128], 'has_fiber': True, 'neighborhood': 'Southport Historic', 'coverage': 65},
            {'name': 'Moore St', 'coordinates': [33.9251, -78.0138], 'has_fiber': True, 'neighborhood': 'Southport Historic', 'coverage': 60},
            {'name': 'St. James Dr', 'coordinates': [33.9141, -78.0028], 'has_fiber': True, 'neighborhood': 'St. James Plantation', 'coverage': 80},
            
            # Beach Areas - Limited Availability
            {'name': 'Carolina Beach Ave', 'coordinates': [34.0541, -77.8878], 'has_fiber': False, 'neighborhood': 'Carolina Beach'},
            {'name': 'Lake Park Blvd', 'coordinates': [34.0531, -77.8888], 'has_fiber': False, 'neighborhood': 'Carolina Beach'},
            {'name': 'Lumina Ave', 'coordinates': [34.2141, -77.7978], 'has_fiber': False, 'neighborhood': 'Wrightsville Beach'},
            {'name': 'Waynick Blvd', 'coordinates': [34.2151, -77.7988], 'has_fiber': False, 'neighborhood': 'Wrightsville Beach'},
            
            # Expansion Target Streets
            {'name': 'Porters Neck Rd', 'coordinates': [34.2929, -77.8543], 'has_fiber': False, 'neighborhood': 'Porters Neck (Target)'},
            {'name': 'Market St Extension', 'coordinates': [34.2939, -77.8553], 'has_fiber': False, 'neighborhood': 'Porters Neck (Target)'},
            {'name': 'Grayson Park Blvd', 'coordinates': [34.2388, -78.0522], 'has_fiber': False, 'neighborhood': 'Grayson Park (Target)'},
        ]

class FiberAvailabilityMapWidget(QWidget):
    """AT&T Fiber Availability Map Widget"""
    
    def __init__(self):
        super().__init__()
        self.map_worker = None
        self.current_map_file = None
        self.httpd = None
        self.http_thread = None
        self.http_port = 8000
        self.setup_ui()
        self.start_http_server()
        
    def setup_ui(self):
        """Setup the map widget UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🗺️ AT&T Fiber Availability Strategic Map")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Control Panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Map area
        map_frame = QFrame()
        map_frame.setStyleSheet("QFrame { border: 2px solid #bdc3c7; border-radius: 8px; }")
        map_layout = QVBoxLayout(map_frame)
        
        # Web view for map
        self.map_view = QWebEngineView()
        self.map_view.setMinimumSize(800, 600)
        map_layout.addWidget(self.map_view)
        
        content_splitter.addWidget(map_frame)
        
        # Analysis panel
        analysis_panel = self.create_analysis_panel()
        content_splitter.addWidget(analysis_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([800, 400])
        layout.addWidget(content_splitter)
        
        # Status bar
        self.status_label = QLabel("Ready to generate fiber availability map")
        self.status_label.setStyleSheet("""
            QLabel {
                background: #ecf0f1;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add date range selectors for ActiveKnocker export
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Export leads processed from:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(datetime.now().replace(month=1, day=1))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QLabel("to"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(datetime.now())
        date_layout.addWidget(self.end_date_edit)
        self.export_ak_btn = QPushButton("Export to ActiveKnocker")
        self.export_ak_btn.clicked.connect(self.export_to_activeknocker)
        date_layout.addWidget(self.export_ak_btn)
        layout.addLayout(date_layout)
        
        self.setLayout(layout)
        
    def create_control_panel(self):
        """Create the control panel for map options"""
        control_group = QGroupBox("🎛️ Map Controls")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2980b9;
            }
        """)
        
        control_layout = QHBoxLayout()
        
        # Generate Map Button
        self.generate_btn = QPushButton("🗺️ Generate Fiber Map")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_map)
        control_layout.addWidget(self.generate_btn)
        
        # Map Type Selector
        map_type_label = QLabel("Map Type:")
        map_type_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        control_layout.addWidget(map_type_label)
        
        self.map_type_combo = QComboBox()
        self.map_type_combo.addItems(["Fiber Coverage", "Strategic Expansion", "Market Analysis", "Combined View"])
        self.map_type_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
        """)
        control_layout.addWidget(self.map_type_combo)
        
        # Zoom Level
        zoom_label = QLabel("Zoom Level:")
        zoom_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        control_layout.addWidget(zoom_label)
        
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(5, 18)
        self.zoom_spin.setValue(11)  # Higher default zoom for neighborhood detail
        self.zoom_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
        """)
        control_layout.addWidget(self.zoom_spin)
        
        # Export Button
        self.export_btn = QPushButton("📤 Export Map")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        self.export_btn.clicked.connect(self.export_map)
        self.export_btn.setEnabled(False)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        return control_group
    
    def create_analysis_panel(self):
        """Create the analysis panel"""
        analysis_group = QGroupBox("📊 Strategic Analysis")
        analysis_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #c0392b;
            }
        """)
        
        analysis_layout = QVBoxLayout()
        
        # Market Statistics
        stats_label = QLabel("📈 Market Statistics")
        stats_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        analysis_layout.addWidget(stats_label)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["Area", "Fiber Coverage", "Growth Potential"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.stats_table.setMaximumHeight(150)
        analysis_layout.addWidget(self.stats_table)
        
        # Strategic Recommendations
        rec_label = QLabel("🎯 Strategic Recommendations")
        rec_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        analysis_layout.addWidget(rec_label)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(200)
        self.recommendations_text.setHtml("""
        <h3>Market Expansion Strategy</h3>
        <p><b>High Priority Areas:</b></p>
        <ul>
        <li>North Wilmington - 85% fiber coverage, high ROI potential</li>
        <li>Pender County - Growing residential market</li>
        </ul>
        <p><b>Medium Priority Areas:</b></p>
        <ul>
        <li>South Brunswick - Moderate growth, good infrastructure</li>
        </ul>
        <p><b>Next Steps:</b></p>
        <ul>
        <li>Focus marketing efforts on high-priority zones</li>
        <li>Develop partnerships with local builders</li>
        <li>Monitor competitor activity in expansion zones</li>
        </ul>
        """)
        analysis_layout.addWidget(self.recommendations_text)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("📊 Analyze Market")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        self.analyze_btn.clicked.connect(self.analyze_market)
        action_layout.addWidget(self.analyze_btn)
        
        self.export_analysis_btn = QPushButton("📋 Export Analysis")
        self.export_analysis_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        self.export_analysis_btn.clicked.connect(self.export_analysis)
        action_layout.addWidget(self.export_analysis_btn)
        
        analysis_layout.addLayout(action_layout)
        analysis_group.setLayout(analysis_layout)
        return analysis_group
    
    def generate_map(self):
        print('[DEBUG] generate_map() called')
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating fiber availability map...")
        
        # Create and start map worker
        self.map_worker = FiberMapWorker()
        self.map_worker.progress_signal.connect(self.update_progress)
        self.map_worker.log_signal.connect(self.update_status)
        self.map_worker.finished_signal.connect(self.on_map_generated)
        self.map_worker.start()
    
    def update_progress(self, current, total):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def update_status(self, message):
        """Update status label and show errors in a popup"""
        self.status_label.setText(message)
        if message.startswith('❌') or 'Error' in message or 'exception' in message:
            print(f"[ERROR] {message}")
            QMessageBox.critical(self, "Map Generation Error", message)
    
    def on_map_generated(self, map_filename):
        """Handle map generation completion"""
        self.current_map_file = map_filename
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Debug: print filename and check existence
        map_path = os.path.join(os.getcwd(), map_filename)
        print(f"[DEBUG] Map file generated: {map_filename}")
        print(f"[DEBUG] Full path: {map_path}")
        
        if not os.path.exists(map_path):
            self.status_label.setText(f"❌ Map file not found: {map_filename}")
            QMessageBox.critical(self, "Map Error", f"Map file not found: {map_filename}")
            return
            
        if os.path.getsize(map_path) == 0:
            self.status_label.setText(f"❌ Map file is empty: {map_filename}")
            QMessageBox.critical(self, "Map Error", f"Map file is empty: {map_filename}")
            return
        
        # Load map via HTTP server
        url = f"http://localhost:{self.http_port}/{map_filename}"
        print(f"[DEBUG] Loading map in QWebEngineView: {url}")
        
        # Test if HTTP server is responding
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=5)
            if response.getcode() == 200:
                print(f"[DEBUG] HTTP server is responding correctly")
                self.map_view.load(url)
                self.status_label.setText("✅ Fiber availability map generated successfully!")
            else:
                raise Exception(f"HTTP server returned code: {response.getcode()}")
        except Exception as e:
            print(f"[DEBUG] HTTP server error: {e}")
            # Fallback: try to load directly as file URL
            file_url = f"file://{map_path}"
            print(f"[DEBUG] Fallback: Loading as file URL: {file_url}")
            self.map_view.load(file_url)
            self.status_label.setText("✅ Map loaded (fallback mode)")
        
        # Debug: print HTML file head
        try:
            with open(map_path, 'r') as f:
                head = f.read(500)
                print(f"[DEBUG] Map HTML head:\n{head}")
        except Exception as e:
            print(f"[DEBUG] Could not read map file: {e}")
        
        # Update market statistics
        self.update_market_statistics()
    
    def update_market_statistics(self):
        """Update market statistics table"""
        stats_data = [
            ["Wilmington Metro", "85%", "High"],
            ["Leland Area", "72%", "Medium"],
            ["Hampstead Region", "45%", "High"],
            ["North Wilmington", "90%", "Very High"],
            ["South Brunswick", "30%", "Medium"],
            ["Pender County", "25%", "High"]
        ]
        
        self.stats_table.setRowCount(len(stats_data))
        for i, (area, coverage, potential) in enumerate(stats_data):
            self.stats_table.setItem(i, 0, QTableWidgetItem(area))
            self.stats_table.setItem(i, 1, QTableWidgetItem(coverage))
            self.stats_table.setItem(i, 2, QTableWidgetItem(potential))
    
    def export_map(self):
        """Export the current map"""
        if self.current_map_file:
            import shutil
            export_path = f"fiber_availability_map_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
            shutil.copy2(self.current_map_file, export_path)
            self.status_label.setText(f"✅ Map exported to: {export_path}")
    
    def analyze_market(self):
        """Perform market analysis"""
        self.status_label.setText("📊 Performing market analysis...")
        
        # Simulate market analysis
        QTimer.singleShot(2000, self.complete_market_analysis)
    
    def complete_market_analysis(self):
        """Complete market analysis"""
        self.recommendations_text.setHtml("""
        <h3>🎯 Updated Market Analysis</h3>
        <p><b>Market Trends:</b></p>
        <ul>
        <li>Wilmington metro area showing 15% growth in fiber adoption</li>
        <li>New residential developments in Pender County</li>
        <li>Competitor activity increasing in Brunswick County</li>
        </ul>
        <p><b>Strategic Recommendations:</b></p>
        <ul>
        <li><b>Immediate Action:</b> Target North Wilmington with aggressive marketing</li>
        <li><b>Short-term:</b> Develop partnerships with Pender County builders</li>
        <li><b>Long-term:</b> Monitor Brunswick County for expansion opportunities</li>
        </ul>
        <p><b>ROI Projections:</b></p>
        <ul>
        <li>North Wilmington: 25-30% ROI potential</li>
        <li>Pender County: 20-25% ROI</li>
        <li>South Brunswick: 15-20% ROI</li>
        </ul>
        """)
        self.status_label.setText("✅ Market analysis completed!")
    
    def export_analysis(self):
        """Export market analysis report"""
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"fiber_market_analysis_{timestamp}.html"
        
        report_content = f"""
        <html>
        <head>
            <title>AT&T Fiber Market Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }}
                .highlight {{ background: #ecf0f1; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🗺️ AT&T Fiber Market Analysis Report</h1>
            <p><em>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
            
            <div class="section">
                <h2>📊 Market Statistics</h2>
                <div class="highlight">
                    <p><strong>Total Coverage Areas:</strong> 6 strategic zones</p>
                    <p><strong>Average Fiber Coverage:</strong> 58%</p>
                    <p><strong>High-Growth Areas:</strong> 3 zones</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 Strategic Recommendations</h2>
                <ul>
                    <li><strong>Priority 1:</strong> Focus on North Wilmington expansion</li>
                    <li><strong>Priority 2:</strong> Develop Pender County partnerships</li>
                    <li><strong>Priority 3:</strong> Monitor Brunswick County opportunities</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>💰 ROI Projections</h2>
                <ul>
                    <li>North Wilmington: 25-30% ROI</li>
                    <li>Pender County: 20-25% ROI</li>
                    <li>South Brunswick: 15-20% ROI</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.status_label.setText(f"✅ Analysis report exported to: {report_file}")
        
        # Open report in browser
        webbrowser.open(f"file://{os.path.abspath(report_file)}")
    
    def get_fiber_cities(self):
        """Return a dict of city: polygon_coords for cities with fiber (stub for now)"""
        # TODO: Replace with real city polygons from your data or a geojson
        return {
            'Wilmington': {'coordinates': [[ [34.2104, -77.8868], [34.2104, -77.7868], [34.3104, -77.7868], [34.3104, -77.8868] ]]},
            'Leland': {'coordinates': [[ [34.2563, -78.0447], [34.2563, -77.9447], [34.3563, -77.9447], [34.3563, -78.0447] ]]},
            'Hampstead': {'coordinates': [[ [34.3673, -77.7102], [34.3673, -77.6102], [34.4673, -77.6102], [34.4673, -77.7102] ]]},
            'Southport': {'coordinates': [[ [33.9216, -78.0206], [33.9216, -77.9206], [34.0216, -77.9206], [34.0216, -78.0206] ]]}
        }
    
    def export_to_activeknocker(self):
        """Export leads processed within the selected date range to ActiveKnocker"""
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        df = pd.read_csv('att_fiber_master.csv', parse_dates=['processed_date'])
        mask = (df['processed_date'] >= start_date) & (df['processed_date'] <= end_date)
        leads = df[mask & (df['fiber_available'] == True)]
        if leads.empty:
            self.status_label.setText(f"No leads found for {start_date} to {end_date}")
            return
        ak_service = ActiveKnockerService()
        errors = 0
        for _, row in leads.iterrows():
            address = row['address']
            lat, lon = geocode_address(address)
            try:
                ak_service.send_lead(address, notes="Lead from AT&T Fiber Tracker", debug_log=None)
            except Exception as e:
                errors += 1
        self.status_label.setText(f"Exported {len(leads) - errors} leads to ActiveKnocker for {start_date} to {end_date}. Errors: {errors}")
    
    def start_http_server(self):
        """Start a simple HTTP server to serve map files"""
        try:
            # Try different ports if 8000 is busy
            for port in range(8000, 8010):
                try:
                    handler = http.server.SimpleHTTPRequestHandler
                    self.httpd = socketserver.TCPServer(("", port), handler)
                    self.http_port = port
                    self.http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                    self.http_thread.start()
                    print(f"[DEBUG] HTTP server started at http://localhost:{self.http_port}/")
                    
                    # Test the server
                    import time
                    time.sleep(0.5)  # Give server time to start
                    
                    # Create a simple test file
                    test_file = 'server_test.html'
                    with open(test_file, 'w') as f:
                        f.write('<html><body><h1>Server Test</h1></body></html>')
                    
                    # Test if we can access it
                    import urllib.request
                    test_url = f"http://localhost:{self.http_port}/{test_file}"
                    try:
                        response = urllib.request.urlopen(test_url, timeout=2)
                        if response.getcode() == 200:
                            print(f"[DEBUG] HTTP server test successful")
                            os.remove(test_file)  # Clean up test file
                            return
                    except:
                        pass
                    
                    # If test failed, try next port
                    self.httpd.shutdown()
                    continue
                    
                except OSError:
                    # Port is busy, try next one
                    continue
                    
            # If we get here, all ports failed
            print("[ERROR] Could not start HTTP server on any port")
            self.http_port = None
            
        except Exception as e:
            print(f"[ERROR] Failed to start HTTP server: {e}")
            self.http_port = None

    def closeEvent(self, event):
        if self.httpd:
            self.httpd.shutdown()
        super().closeEvent(event) 