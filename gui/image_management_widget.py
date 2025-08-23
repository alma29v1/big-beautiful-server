#!/usr/bin/env python3
"""
Image Management Widget
Allows users to manage campaign images - review, approve, remove, and add new images
"""

import os
import json
import requests
from urllib.parse import urlparse
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QGroupBox, QCheckBox, 
                               QFileDialog, QMessageBox, QLineEdit, QTextEdit,
                               QGridLayout, QFrame, QProgressBar, QComboBox, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# Add OIP file handler import
try:
    from oip_file_handler import OIPFileHandler
    OIP_SUPPORT = True
except ImportError:
    OIP_SUPPORT = False
    print("⚠️ OIP file support not available - install python-magic for full support")

class ImageDownloadWorker(QThread):
    """Worker thread for downloading and validating images"""
    
    image_downloaded = Signal(str, str, bool)  # url, local_path, success
    progress_update = Signal(int, int, str)  # current, total, status
    
    def __init__(self, image_urls):
        super().__init__()
        self.image_urls = image_urls
        
    def run(self):
        """Download images and validate them"""
        total = len(self.image_urls)
        
        for i, url in enumerate(self.image_urls):
            try:
                self.progress_update.emit(i + 1, total, f"Processing {url}")
                
                if url.startswith('file://'):
                    # Handle local file URLs - no download needed
                    file_path = url.replace('file://', '')
                    if os.path.exists(file_path):
                        self.image_downloaded.emit(url, file_path, True)
                    else:
                        self.image_downloaded.emit(url, "", False)
                        
                elif url.startswith(('http://', 'https://')):
                    # Handle web URLs - download them
                    os.makedirs("campaign_images", exist_ok=True)
                    
                    # Generate local filename
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path) or f"image_{i}.jpg"
                    local_path = os.path.join("campaign_images", filename)
                    
                    # Download image
                    response = requests.get(url, timeout=10, stream=True)
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    self.image_downloaded.emit(url, local_path, True)
                    
                else:
                    # Unknown URL type
                    print(f"Unknown URL type: {url}")
                    self.image_downloaded.emit(url, "", False)
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                self.image_downloaded.emit(url, "", False)

class ImageManagementWidget(QWidget):
    """Widget for managing campaign images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.images_data = {}
        self.download_worker = None
        self.setup_ui()
        self.load_current_images()

    def get_category_display_name(self, category):
        """Get user-friendly display name for category"""
        display_names = {
            'att_fiber': '🌐 AT&T Fiber',
            'adt_security': '🔒 ADT Security',
            'fire_incident': '🔥 Fire Incident',
            'burglary_incident': '🏠 Burglary/Break-in',
            'medical_emergency': '🚑 Medical Emergency',
            'assault_incident': '⚠️ Assault Incident',
            'vandalism_incident': '🔨 Vandalism',
            'theft_incident': '💎 Theft',
            'domestic_violence': '🏡 Domestic Violence',
            'drug_activity': '💊 Drug Activity',
            'general_incident': '🚨 General Incident',
            'general_outreach': '📢 General Outreach'
        }
        return display_names.get(category, f"📁 {category.replace('_', ' ').title()}")

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Set widget background
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                color: #333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #0052a3; }
            QPushButton:pressed { background-color: #004080; }
        """)
        
        # Header
        header = QLabel("🖼️ Image Management")
        header.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #0066cc;
                padding: 15px;
                background: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh Images")
        self.refresh_btn.clicked.connect(self.load_current_images)
        actions_layout.addWidget(self.refresh_btn)
        
        self.add_url_btn = QPushButton("🔗 Add Image URL")
        self.add_url_btn.clicked.connect(self.add_image_url)
        actions_layout.addWidget(self.add_url_btn)
        
        self.upload_btn = QPushButton("📁 Upload Image File")
        self.upload_btn.clicked.connect(self.upload_image_file)
        actions_layout.addWidget(self.upload_btn)
        
        self.bulk_upload_btn = QPushButton("📂 Bulk Upload Folder")
        self.bulk_upload_btn.clicked.connect(self.bulk_upload_folder)
        self.bulk_upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        actions_layout.addWidget(self.bulk_upload_btn)
        
        # OIP Convert button (NEW)
        if OIP_SUPPORT:
            self.convert_oip_btn = QPushButton("🔄 Convert OIP Files")
            self.convert_oip_btn.clicked.connect(self.convert_oip_files)
            self.convert_oip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                }
                QPushButton:hover { background-color: #8e44ad; }
            """)
            actions_layout.addWidget(self.convert_oip_btn)
        
        self.pull_website_btn = QPushButton("🌐 Pull from Seaside Security")
        self.pull_website_btn.clicked.connect(self.pull_seaside_images)
        actions_layout.addWidget(self.pull_website_btn)
        
        actions_layout.addStretch()
        
        self.save_changes_btn = QPushButton("💾 Save Changes")
        self.save_changes_btn.clicked.connect(self.save_changes)
        self.save_changes_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        actions_layout.addWidget(self.save_changes_btn)
        
        layout.addLayout(actions_layout)
        
        # Progress bar for downloads
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Scroll area for images
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.images_widget = QWidget()
        self.images_layout = QVBoxLayout(self.images_widget)
        scroll.setWidget(self.images_widget)
        
        layout.addWidget(scroll)
        
    def load_current_images(self):
        """Load current images from config file or fall back to defaults"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Clear existing widgets
        for i in reversed(range(self.images_layout.count())):
            child = self.images_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Try to load from saved config first
        config_path = "image_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    saved_images = json.load(f)
                    self.images_data = saved_images
                    print(f"Loaded image configuration from {config_path}")
            except Exception as e:
                print(f"Error loading saved config, using defaults: {e}")
                self.load_default_images()
        else:
            print("No saved config found, using default images")
            self.load_default_images()
            
        # Create category sections
        for category, urls in self.images_data.items():
            self.create_category_section(category, urls)
        
        self.progress_bar.setVisible(False)
        
        # Load local images immediately, then start downloading web images
        self.load_local_images_immediately()
        self.download_images()
        
    def load_default_images(self):
        """Load default image configuration"""
        # Default image configuration from automation_worker.py
        current_images = {
            'att_fiber': [
                # Professional fiber optic cable installations
                "https://images.unsplash.com/photo-1606868306217-dbf5046868d2?w=600",  # Fiber cables close-up - technical
                "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=600",  # Fiber optic network cables
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",    # Networking/tech installation
                
                # High-speed internet and technology setups
                "https://images.unsplash.com/photo-1582201942988-13e60e4b31cd?w=600",  # Professional tech setup
                "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=600",    # Network equipment/server room
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600",    # Modern home office (fiber benefit)
                
                # Smart homes and modern connectivity
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",    # Modern smart home exterior
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Modern interior with tech
                "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600", # Gaming setup (fiber speed benefit)
                
                # Professional installation and service
                "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=600", # Professional tech work
                "https://images.unsplash.com/photo-1573164713347-4452bf387ac4?w=600", # Professional installer
                
                # Speed and performance imagery
                "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=600", # Speed/performance concept
                "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=600",   # High-tech networking
            ],
            'adt_security': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Security keypad
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Security system
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600"    # Secure home
            ],
            'fire_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600",   # Smoke detection
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Home safety
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Fire safety equipment
            ],
            'burglary_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Security keypad
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Security system
                "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600",   # Door/window sensors
            ],
            'medical_emergency': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600",   # Emergency button
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Medical alert
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Help system
            ],
            'assault_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Panic button
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Personal security
                "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600",   # Safety monitoring
            ],
            'vandalism_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Security cameras
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Property monitoring
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Property protection
            ],
            'theft_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Theft prevention
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Anti-theft system
                "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600",   # Security monitoring
            ],
            'domestic_violence': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Safe home system
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Emergency response
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Family protection
            ],
            'drug_activity': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Neighborhood security
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Community protection
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Area monitoring
            ],
            'general_incident': [
                "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp",
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # General security
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Emergency system
                "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600",   # Safety equipment
            ],
            'general_outreach': [
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Modern home
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Modern interior
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600"    # Home office
            ]
        }
        
        self.images_data = current_images
        
    def load_local_images_immediately(self):
        """Load local file:// images immediately without waiting for worker thread"""
        print("[IMG] Loading local images immediately...")
        
        for category, urls in self.images_data.items():
            print(f"[IMG] Processing category: {category} with {len(urls)} URLs")
            for url in urls:
                if url.startswith('file://'):
                    print(f"[IMG] Loading local file: {url}")
                    try:
                        file_path = url.replace('file://', '')
                        if os.path.exists(file_path):
                            print(f"[IMG] File exists, creating QPixmap...")
                            pixmap = QPixmap(file_path)
                            if not pixmap.isNull():
                                print(f"[IMG] QPixmap created successfully ({pixmap.width()}x{pixmap.height()})")
                                scaled_pixmap = pixmap.scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                
                                # Update the image display immediately
                                updated = False
                                for i in range(self.images_layout.count()):
                                    group_widget = self.images_layout.itemAt(i).widget()
                                    if isinstance(group_widget, QGroupBox):
                                        if self.update_image_in_group(group_widget, url, scaled_pixmap):
                                            updated = True
                                            print(f"[IMG] ✅ Updated image display for {url}")
                                
                                if not updated:
                                    print(f"[IMG] ⚠️ Could not find widget to update for {url}")
                            else:
                                print(f"[IMG] ❌ QPixmap is null - invalid image file")
                                # File exists but can't load as image
                                for i in range(self.images_layout.count()):
                                    group_widget = self.images_layout.itemAt(i).widget()
                                    if isinstance(group_widget, QGroupBox):
                                        self.update_image_error_in_group(group_widget, url, "Invalid image")
                        else:
                            print(f"[IMG] ❌ File does not exist: {file_path}")
                            # File doesn't exist
                            for i in range(self.images_layout.count()):
                                group_widget = self.images_layout.itemAt(i).widget()
                                if isinstance(group_widget, QGroupBox):
                                    self.update_image_error_in_group(group_widget, url, "File not found")
                    except Exception as e:
                        print(f"[IMG] ❌ Error loading local image {url}: {e}")
                        # Show error
                        for i in range(self.images_layout.count()):
                            group_widget = self.images_layout.itemAt(i).widget()
                            if isinstance(group_widget, QGroupBox):
                                self.update_image_error_in_group(group_widget, url, "Load error")
        
        print("[IMG] Finished loading local images.")

    def download_images(self):
        """Download web images to show previews"""
        # Get all unique URLs that are NOT local files
        all_urls = []
        for urls in self.images_data.values():
            for url in urls:
                if not url.startswith('file://'):
                    all_urls.append(url)
        unique_urls = list(set(all_urls))
        
        if unique_urls:
            self.download_worker = ImageDownloadWorker(unique_urls)
            self.download_worker.image_downloaded.connect(self.on_image_downloaded)
            self.download_worker.progress_update.connect(self.on_download_progress)
            self.download_worker.finished.connect(self.on_download_finished)
            self.download_worker.start()
        
    def create_category_section(self, category, urls):
        """Create a section for each image category"""
        # Category group with user-friendly display name
        display_name = self.get_category_display_name(category)
        group = QGroupBox(display_name)
        group_layout = QVBoxLayout()
        
        # Images grid
        images_grid = QGridLayout()
        
        for i, url in enumerate(urls):
            image_frame = self.create_image_item(url, category, i)
            row = i // 3
            col = i % 3
            images_grid.addWidget(image_frame, row, col)
        
        group_layout.addLayout(images_grid)
        
        # Add image button for this category with display name
        simple_name = category.replace('_', ' ').title()
        add_btn = QPushButton(f"➕ Add Image to {simple_name}")
        add_btn.clicked.connect(lambda: self.add_image_to_category(category))
        group_layout.addWidget(add_btn)
        
        group.setLayout(group_layout)
        self.images_layout.addWidget(group)
        
    def create_image_item(self, url, category, index):
        """Create a widget for displaying an image item"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }
        """)
        frame.setFixedSize(200, 250)
        
        layout = QVBoxLayout(frame)
        
        # Image preview placeholder
        image_label = QLabel("Loading...")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedSize(180, 120)
        image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        layout.addWidget(image_label)
        
        # URL display (truncated)
        url_label = QLabel(f"...{url[-30:]}" if len(url) > 30 else url)
        url_label.setWordWrap(True)
        url_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(url_label)
        
        # Approval checkbox
        approval_checkbox = QCheckBox("✅ Approved")
        approval_checkbox.setChecked(True)  # Default approved
        approval_checkbox.setObjectName(f"{category}_{index}_approved")
        layout.addWidget(approval_checkbox)
        
        # Remove button
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                font-size: 10px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        remove_btn.clicked.connect(lambda: self.remove_image(category, index))
        layout.addWidget(remove_btn)
        
        # Store reference for later updates
        frame.image_label = image_label
        frame.url = url
        
        return frame
        
    def on_image_downloaded(self, url, local_path, success):
        """Handle completed image download"""
        try:
            pixmap = None
            
            # Handle different URL types
            if url.startswith('file://'):
                # For local file URLs, use the original path directly
                file_path = url.replace('file://', '')
                if os.path.exists(file_path):
                    pixmap = QPixmap(file_path)
            elif success and local_path and os.path.exists(local_path):
                # For downloaded web images
                pixmap = QPixmap(local_path)
            
            if pixmap and not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(180, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Find the widget with this URL
                for i in range(self.images_layout.count()):
                    group_widget = self.images_layout.itemAt(i).widget()
                    if isinstance(group_widget, QGroupBox):
                        self.update_image_in_group(group_widget, url, scaled_pixmap)
            else:
                # If image loading failed, update with error message
                for i in range(self.images_layout.count()):
                    group_widget = self.images_layout.itemAt(i).widget()
                    if isinstance(group_widget, QGroupBox):
                        self.update_image_error_in_group(group_widget, url, "Failed to load")
                        
        except Exception as e:
            print(f"Error processing image {url}: {e}")
            # Show error in UI
            for i in range(self.images_layout.count()):
                group_widget = self.images_layout.itemAt(i).widget()
                if isinstance(group_widget, QGroupBox):
                    self.update_image_error_in_group(group_widget, url, "Load error")
    
    def update_image_in_group(self, group_widget, url, pixmap):
        """Update image preview in a group widget"""
        def find_frames(widget):
            frames = []
            for child in widget.children():
                if isinstance(child, QFrame) and hasattr(child, 'url'):
                    frames.append(child)
                else:
                    frames.extend(find_frames(child))
            return frames
        
        frames = find_frames(group_widget)
        for frame in frames:
            if hasattr(frame, 'url') and frame.url == url:
                frame.image_label.setPixmap(pixmap)
                frame.image_label.setText("")  # Clear loading text
                return True  # Successfully updated
        return False  # No matching frame found

    def update_image_error_in_group(self, group_widget, url, error_msg):
        """Update image preview with error message in a group widget"""
        def find_frames(widget):
            frames = []
            for child in widget.children():
                if isinstance(child, QFrame) and hasattr(child, 'url'):
                    frames.append(child)
                else:
                    frames.extend(find_frames(child))
            return frames
        
        frames = find_frames(group_widget)
        for frame in frames:
            if hasattr(frame, 'url') and frame.url == url:
                frame.image_label.setText(f"❌ {error_msg}")
                frame.image_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #ccc;
                        background-color: #fff5f5;
                        border-radius: 4px;
                        color: #d63384;
                    }
                """)
                break
    
    def on_download_progress(self, current, total, status):
        """Handle download progress updates"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def on_download_finished(self):
        """Handle download completion"""
        self.progress_bar.setVisible(False)
        
    def add_image_url(self):
        """Add a new image URL"""
        from PySide6.QtWidgets import QInputDialog
        
        url, ok = QInputDialog.getText(self, "Add Image URL", "Enter image URL:")
        if ok and url:
            # Ask which category
            categories = list(self.images_data.keys())
            category, ok = QInputDialog.getItem(self, "Select Category", "Choose category:", categories, 0, False)
            if ok:
                self.images_data[category].append(url)
                self.load_current_images()  # Refresh display
    
    def upload_image_file(self):
        """Upload a local image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image File", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        
        if file_path:
            # Copy to campaign_images directory
            os.makedirs("campaign_images", exist_ok=True)
            filename = os.path.basename(file_path)
            local_path = os.path.join("campaign_images", filename)
            
            try:
                # Skip resource fork files
                filename = os.path.basename(file_path)
                if filename.startswith('._'):
                    QMessageBox.warning(self, "Invalid File", "Resource fork files (._*) cannot be used as images.")
                    return
                
                import shutil
                shutil.copy2(file_path, local_path)
                
                # Ask which category
                categories = list(self.images_data.keys())
                from PySide6.QtWidgets import QInputDialog
                category, ok = QInputDialog.getItem(self, "Select Category", "Choose category:", categories, 0, False)
                if ok:
                    # Convert to file:// URL for local files
                    file_url = f"file://{os.path.abspath(local_path)}"
                    self.images_data[category].append(file_url)
                    self.load_current_images()  # Refresh display
                    
            except Exception as e:
                QMessageBox.warning(self, "Upload Error", f"Error copying file: {e}")
    
    def bulk_upload_folder(self):
        """Bulk upload all images from a selected folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder with Images", 
            "", 
            QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return
        
        # Find all image files in the folder
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        image_files = []
        
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            # Skip macOS resource fork files and hidden files
            if (os.path.isfile(file_path) and 
                not file_name.startswith('._') and 
                not file_name.startswith('.')):
                _, ext = os.path.splitext(file_name.lower())
                if ext in image_extensions:
                    image_files.append(file_path)
        
        if not image_files:
            QMessageBox.information(
                self, 
                "No Images Found", 
                f"No image files found in the selected folder.\n\n"
                f"Supported formats: {', '.join(image_extensions)}"
            )
            return
        
        # Ask user to confirm and select category
        categories = list(self.images_data.keys())
        
        # Create mapping of display names to actual category keys
        category_mapping = {}
        display_categories = []
        for cat in categories:
            display_name = self.get_category_display_name(cat)
            display_categories.append(display_name)
            category_mapping[display_name] = cat
        
        # Show preview dialog
        from PySide6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Upload Images")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel(f"📂 Found {len(image_files)} images in folder:\n{folder_path}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Category selection
        category_label = QLabel("Select category for all images:")
        layout.addWidget(category_label)
        
        category_combo = QComboBox()
        category_combo.addItems(display_categories)  # Use display names
        layout.addWidget(category_combo)
        
        # File list preview
        files_label = QLabel("Images to upload:")
        layout.addWidget(files_label)
        
        files_text = QTextEdit()
        files_text.setMaximumHeight(150)
        files_text.setPlainText('\n'.join([os.path.basename(f) for f in image_files]))
        files_text.setReadOnly(True)
        layout.addWidget(files_text)
        
        # Buttons
        from PySide6.QtWidgets import QHBoxLayout
        buttons_layout = QHBoxLayout()
        
        upload_btn = QPushButton("✅ Upload All")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        upload_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(upload_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Execute dialog
        if dialog.exec() == QDialog.Accepted:
            selected_display_category = category_combo.currentText()
            selected_category = category_mapping.get(selected_display_category)
            
            if not selected_category:
                QMessageBox.warning(self, "Category Not Found", 
                    f"The selected category '{selected_display_category}' was not found in the current image configuration.")
                return
            
            # Process upload with progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(image_files))
            self.progress_bar.setValue(0)
            
            os.makedirs("campaign_images", exist_ok=True)
            uploaded_count = 0
            failed_files = []
            
            for i, file_path in enumerate(image_files):
                try:
                    filename = os.path.basename(file_path)
                    local_path = os.path.join("campaign_images", filename)
                    
                    # Handle duplicate names
                    if os.path.exists(local_path):
                        name, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(local_path):
                            new_filename = f"{name}_{counter}{ext}"
                            local_path = os.path.join("campaign_images", new_filename)
                            counter += 1
                    
                    # Copy file
                    import shutil
                    shutil.copy2(file_path, local_path)
                    
                    # Convert to file:// URL for local files
                    file_url = f"file://{os.path.abspath(local_path)}"
                    self.images_data[selected_category].append(file_url)
                    
                    uploaded_count += 1
                    
                except Exception as e:
                    failed_files.append(f"{filename}: {str(e)}")
                    print(f"Error uploading {filename}: {e}")
                
                # Update progress
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Keep UI responsive
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            
            # Save changes immediately
            self.save_changes_silently()
            
            # Refresh display
            self.refresh_display()
            
            # Show results
            if uploaded_count > 0:
                success_msg = f"✅ Successfully uploaded {uploaded_count} images to '{selected_display_category}' category."
                if failed_files:
                    success_msg += f"\n\n❌ Failed to upload {len(failed_files)} files:\n" + "\n".join(failed_files[:5])
                    if len(failed_files) > 5:
                        success_msg += f"\n... and {len(failed_files) - 5} more"
                
                QMessageBox.information(self, "Bulk Upload Complete", success_msg)
            else:
                QMessageBox.warning(self, "Upload Failed", "No images were successfully uploaded.")
    
    def pull_seaside_images(self):
        """Pull multiple images from seasidesecurity.net website to address liability by using owned content"""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            QMessageBox.information(
                self, 
                "Pull from Website", 
                "🌐 Pulling licensed images from seasidesecurity.net...\n\n"
                "This will add your owned Seaside Security images to all categories for full copyright compliance."
            )
            
            # Base URL
            base_url = "https://seasidesecurity.net"
            
            # Pages to scrape for images (focus on relevant sections)
            pages_to_scrape = [
                "/",  # Home page
                "/services/",  # Services
                "/about/",  # About
                "/fiber/",  # Fiber-related if exists
                "/security/",  # Security-related
                "/gallery/"  # Any gallery pages
            ]
            
            # Search terms for relevant images
            search_terms = ['fiber', 'att', 'security', 'adt', 'installation', 'internet', 'network', 'technology', 'home', 'safe']
            
            # Collect images
            found_images = []
            for page in pages_to_scrape:
                url = urljoin(base_url, page)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        alt = img.get('alt', '').lower()
                        title = img.get('title', '').lower()
                        if src and (any(term in alt or term in title or term in src.lower() for term in search_terms)):
                            if src.startswith('/'):
                                src = urljoin(base_url, src)
                            found_images.append(src)
            
            # Remove duplicates
            found_images = list(set(found_images))
            
            # Add to categories
            added_count = 0
            # Map images to categories based on terms
            category_mapping = {
                'att_fiber': ['fiber', 'att', 'internet', 'network', 'technology'],
                'adt_security': ['security', 'adt', 'safe'],
                'fire_incident': ['fire', 'smoke'],
                'burglary_incident': ['burglary', 'break-in', 'security'],
                'medical_emergency': ['medical', 'emergency'],
                'assault_incident': ['assault', 'personal safety'],
                'vandalism_incident': ['vandalism', 'property damage'],
                'theft_incident': ['theft', 'robbery'],
                'domestic_violence': ['domestic', 'family protection'],
                'drug_activity': ['drug', 'neighborhood security'],
                'general_incident': ['incident', 'alert'],
                'general_outreach': ['home', 'general']
            }
            
            for img_url in found_images:
                added = False
                for category, terms in category_mapping.items():
                    if category in self.images_data and any(term in img_url.lower() for term in terms):
                        if img_url not in self.images_data[category]:
                            self.images_data[category].append(img_url)
                            added_count += 1
                            added = True
                if not added:
                    # Add to general if no specific match
                    if 'general_outreach' in self.images_data and img_url not in self.images_data['general_outreach']:
                        self.images_data['general_outreach'].append(img_url)
                        added_count += 1
            
            # Save and refresh
            self.save_changes_silently()
            self.refresh_display()
            
            if added_count > 0:
                QMessageBox.information(
                    self, 
                    "Images Added", 
                    f"✅ Added {added_count} owned images from seasidesecurity.net to categories.\n\n"
                    f"This ensures full copyright compliance and uses only your licensed content."
                )
            else:
                QMessageBox.information(
                    self, 
                    "No New Images", 
                    "ℹ️ No new images found or all are already added.\n\n"
                    "Add more images to your website for automatic pulling."
                )
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error pulling images: {e}")
    
    def add_image_to_category(self, category):
        """Add an image to a specific category"""
        from PySide6.QtWidgets import QInputDialog
        
        url, ok = QInputDialog.getText(self, f"Add Image to {category}", "Enter image URL:")
        if ok and url:
            self.images_data[category].append(url)
            self.load_current_images()  # Refresh display
    
    def remove_image(self, category, index):
        """Remove an image from a category"""
        try:
            if category in self.images_data and index < len(self.images_data[category]):
                # Get the URL to be removed (but don't remove it yet)
                url_to_remove = self.images_data[category][index]
                
                # Show confirmation dialog FIRST
                reply = QMessageBox.question(
                    self, 
                    "Confirm Removal", 
                    f"Remove this image from {category.replace('_', ' ').title()}?\n\n{url_to_remove[-50:]}...",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # NOW actually remove the image from data
                    self.images_data[category].pop(index)
                    
                    # Save changes immediately to persist the removal
                    self.save_changes_silently()
                    
                    # Refresh the display
                    self.refresh_display()
                    
                    QMessageBox.information(
                        self, 
                        "Image Removed", 
                        f"✅ Removed image from {category.replace('_', ' ').title()}"
                    )
                # If user said No, do nothing - image remains in list
                    
            else:
                QMessageBox.warning(self, "Error", f"Image not found at index {index} in {category}")
                
        except (IndexError, KeyError) as e:
            QMessageBox.warning(self, "Error", f"Error removing image: {e}")
    
    def save_changes(self):
        """Save changes to the automation worker configuration"""
        try:
            # Generate Python code to update the automation worker
            config_code = self.generate_image_config()
            
            # Save to a configuration file
            config_path = "image_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.images_data, f, indent=2)
            
            QMessageBox.information(
                self, 
                "Changes Saved", 
                f"✅ Image configuration saved to {config_path}\n\n"
                "The automation worker will use the updated images in future campaigns.\n\n"
                "Restart the program to apply changes."
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Error saving changes: {e}")
    
    def save_changes_silently(self):
        """Save changes without showing confirmation dialog"""
        try:
            # Save to a configuration file
            config_path = "image_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.images_data, f, indent=2)
            print(f"Image configuration saved to {config_path}")
        except Exception as e:
            print(f"Error saving image configuration: {e}")
    
    def refresh_display(self):
        """Refresh the display without reloading from hardcoded data"""
        # Clear existing widgets
        for i in reversed(range(self.images_layout.count())):
            child = self.images_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Create image category sections using current data
        for category, urls in self.images_data.items():
            self.create_category_section(category, urls)
        
        self.progress_bar.setVisible(False)
        
        # Load local images immediately, then download any new web images
        self.load_local_images_immediately()
        self.download_images()
    
    def generate_image_config(self):
        """Generate Python code for the image configuration"""
        code = "# Updated image configuration\nAPPROVED_IMAGES = {\n"
        
        for category, urls in self.images_data.items():
            code += f"    '{category}': [\n"
            for url in urls:
                code += f"        \"{url}\",\n"
            code += f"    ],\n"
        
        code += "}\n"
        return code 

    def convert_oip_files(self):
        """Convert OIP files to standard image formats"""
        if not OIP_SUPPORT:
            QMessageBox.warning(self, "Feature Not Available", 
                "OIP file conversion requires python-magic.\n\n"
                "Install with: pip install python-magic")
            return
        
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder with OIP Files", 
            "", 
            QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return
        
        # Show progress dialog
        progress_dialog = QProgressDialog("Converting OIP files...", "Cancel", 0, 0, self)
        progress_dialog.setWindowTitle("OIP Conversion")
        progress_dialog.setModal(True)
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Convert OIP files
            handler = OIPFileHandler()
            results = handler.batch_convert_oip_files(folder_path, "campaign_images")
            
            progress_dialog.close()
            
            if results['total'] == 0:
                QMessageBox.information(self, "No OIP Files", 
                    f"No OIP files found in:\n{folder_path}\n\n"
                    f"Looking for files starting with 'OIP-' or containing valid image data.")
                return
            
            # Show results and ask which category to add them to
            message = f"🔄 OIP CONVERSION RESULTS:\n\n"
            message += f"📁 Scanned folder: {os.path.basename(folder_path)}\n"
            message += f"📊 Total OIP files found: {results['total']}\n"
            message += f"✅ Successfully converted: {len(results['converted'])}\n"
            message += f"❌ Failed conversions: {len(results['failed'])}\n\n"
            
            if results['converted']:
                message += "✅ CONVERTED FILES:\n"
                for item in results['converted'][:5]:  # Show first 5
                    orig_name = os.path.basename(item['original'])
                    conv_name = os.path.basename(item['converted'])
                    message += f"  • {orig_name} → {conv_name}\n"
                if len(results['converted']) > 5:
                    message += f"  ... and {len(results['converted']) - 5} more\n"
            
            if results['failed']:
                message += f"\n❌ FAILED FILES:\n"
                for item in results['failed'][:3]:  # Show first 3 failures
                    message += f"  • {os.path.basename(item['file'])}: {item['error']}\n"
            
            # Ask if user wants to add converted files to a category
            if results['converted']:
                reply = QMessageBox.question(self, "OIP Conversion Complete", 
                    message + f"\n🎯 Add converted images to a category?",
                    QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Category selection
                    categories = list(self.images_data.keys())
                    category, ok = QInputDialog.getItem(
                        self, "Select Category", 
                        "Choose category for converted OIP images:", 
                        categories, 0, False)
                    
                    if ok:
                        # Add converted files to selected category
                        added_count = 0
                        for item in results['converted']:
                            file_url = f"file://{os.path.abspath(item['converted'])}"
                            self.images_data[category].append(file_url)
                            added_count += 1
                        
                        # Save and refresh
                        self.save_changes_silently()
                        self.refresh_display()
                        
                        QMessageBox.information(self, "Images Added", 
                            f"✅ Added {added_count} converted OIP images to '{category}' category!")
            else:
                QMessageBox.information(self, "Conversion Results", message)
        
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(self, "Conversion Error", 
                f"Error converting OIP files:\n\n{str(e)}") 