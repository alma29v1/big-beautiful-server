from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QTextEdit,
                               QProgressBar, QSplitter, QGroupBox, QGridLayout,
                               QMessageBox, QFileDialog, QComboBox, QGraphicsView, 
                               QGraphicsScene, QGraphicsPixmapItem)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QRectF
from PySide6.QtGui import QPixmap, QImage, QFont, QPainter, QCursor
import os
import json
from datetime import datetime

class ZoomableGraphicsView(QGraphicsView):
    """A QGraphicsView that supports zooming and panning."""
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._zoom = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        factor = 1.25
        self._zoom += 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0
    
    def zoom_out(self):
        factor = 0.8
        self._zoom -= 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0

    def fitInView(self, scale=True):
        rect = self.scene().sceneRect()
        if not rect.isNull():
            self.setSceneRect(rect)
            unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(), 
                         viewrect.height() / scenerect.height())
            self.scale(factor, factor)
            self._zoom = 0

class ADTVerificationWidget(QWidget):
    """Widget for verifying ADT detection results with image zoom/pan."""
    
    verification_complete = Signal(dict)

    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.verification_data = []
        self.current_index = 0

        splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(splitter)

        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        
        zoom_layout = QHBoxLayout()
        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.view.zoom_in)
        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.view.zoom_out)
        zoom_fit_button = QPushButton("Fit Image")
        zoom_fit_button.clicked.connect(self.view.fitInView)
        zoom_layout.addStretch()
        zoom_layout.addWidget(zoom_in_button)
        zoom_layout.addWidget(zoom_out_button)
        zoom_layout.addWidget(zoom_fit_button)
        
        image_layout.addLayout(zoom_layout)
        image_layout.addWidget(self.view)
        image_container.setLayout(image_layout)
        splitter.addWidget(image_container)

        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_container.setFixedWidth(450)
        self.setup_controls(controls_layout)
        controls_container.setLayout(controls_layout)
        splitter.addWidget(controls_container)
        splitter.setSizes([self.width() - 450, 450])
        
        self.update_navigation_controls()

    def setup_controls(self, layout):
        """Create and add all control widgets to the provided layout."""
        # Property info group
        info_group = QGroupBox("Property Information")
        info_layout = QGridLayout()
        info_group.setLayout(info_layout)
        
        self.address_label = QLabel("N/A")
        self.city_label = QLabel("N/A")
        self.confidence_label = QLabel("N/A")
        self.method_label = QLabel("N/A")
        self.explanation_label = QLabel("N/A")
        self.timestamp_label = QLabel("N/A")
        self.status_label = QLabel("N/A")

        info_layout.addWidget(QLabel("Address:"), 0, 0)
        info_layout.addWidget(self.address_label, 0, 1)
        info_layout.addWidget(QLabel("City:"), 1, 0)
        info_layout.addWidget(self.city_label, 1, 1)
        info_layout.addWidget(QLabel("Confidence:"), 2, 0)
        info_layout.addWidget(self.confidence_label, 2, 1)
        info_layout.addWidget(QLabel("Method:"), 3, 0)
        info_layout.addWidget(self.method_label, 3, 1)
        info_layout.addWidget(QLabel("Details:"), 4, 0)
        info_layout.addWidget(self.explanation_label, 4, 1)
        info_layout.addWidget(QLabel("Detected:"), 5, 0)
        info_layout.addWidget(self.timestamp_label, 5, 1)
        info_layout.addWidget(QLabel("Status:"), 6, 0)
        info_layout.addWidget(self.status_label, 6, 1)
        layout.addWidget(info_group)
        
        # Notes
        notes_group = QGroupBox("Verification Notes")
        notes_layout = QVBoxLayout()
        notes_group.setLayout(notes_layout)
        self.notes_text = QTextEdit()
        notes_layout.addWidget(self.notes_text)
        layout.addWidget(notes_group)
        
        # Verification Actions
        verify_group = QGroupBox("Verification Actions")
        verify_layout = QHBoxLayout()
        verify_group.setLayout(verify_layout)
        self.yes_button = QPushButton("✅ ADT Present")
        self.yes_button.clicked.connect(self.mark_adt_present)
        self.no_button = QPushButton("❌ No ADT")
        self.no_button.clicked.connect(self.mark_no_adt)
        self.unsure_button = QPushButton("❓ Unsure")
        self.unsure_button.clicked.connect(self.mark_unsure)
        verify_layout.addWidget(self.yes_button)
        verify_layout.addWidget(self.no_button)
        verify_layout.addWidget(self.unsure_button)
        layout.addWidget(verify_group)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.previous_image)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_image)
        self.jump_combo = QComboBox()
        self.jump_combo.currentIndexChanged.connect(self.jump_to_image)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.jump_combo)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)
        
        # Progress
        self.progress_label = QLabel("0/0 images verified")
        layout.addWidget(self.progress_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Detection Results")
        self.load_button.clicked.connect(self.load_verification_data)
        self.save_button = QPushButton("Save Progress")
        self.save_button.clicked.connect(self.save_verifications)
        self.export_button = QPushButton("Export Training Data")
        self.export_button.clicked.connect(self.export_training_data)
        action_layout.addWidget(self.load_button)
        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.export_button)
        layout.addLayout(action_layout)

    def load_verification_data(self):
        try:
            # Look for consolidated JSON files (prioritize REAL results)
            detection_files = [f for f in os.listdir('.') if f.startswith('redfin_adt_consolidated_') and f.endswith('.json')]
            if not detection_files:
                QMessageBox.warning(self, "No Data", "No consolidated ADT detection files found.")
                return
            
            # Prioritize REAL results over simulated ones
            real_files = [f for f in detection_files if 'REAL' in f]
            if real_files:
                latest_file = max(real_files, key=lambda f: os.path.getmtime(f))
            else:
                latest_file = max(detection_files, key=lambda f: os.path.getmtime(f))
            
            print(f"[DEBUG] Loading verification data from: {latest_file}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            verification_data = []
            
            # Handle different JSON structures
            if 'results' in data and 'adt_results' in data['results']:
                # New structure
                results = data['results']['adt_results']
            elif 'adt_results' in data:
                # Direct structure
                results = data['adt_results']
            else:
                # Try to find results in any city data
                results = []
                for key, value in data.items():
                    if isinstance(value, dict) and 'adt_results' in value:
                        results.extend(value['adt_results'])
            
            print(f"[DEBUG] Found {len(results)} ADT results")
            
            # Check if this is real Google Vision API data
            is_real_data = 'REAL' in latest_file or any(r.get('detection_method') == 'Google Vision API' for r in results)
            
            # For real data, show info about the results
            if is_real_data:
                detected_count = len([r for r in results if r.get('adt_detected', False)])
                total_count = len(results)
                
                if detected_count == 0:
                    QMessageBox.information(self, "Real ADT Detection Results", 
                        f"Google Vision API processed {total_count} properties and found 0 ADT signs.\n\n"
                        f"This is normal if the properties don't have visible ADT security signs.\n\n"
                        f"The system is working correctly with real computer vision analysis.\n\n"
                        f"You can still browse all {total_count} analyzed properties to verify the results.")
                else:
                    QMessageBox.information(self, "Real ADT Detection Results", 
                        f"Google Vision API processed {total_count} properties and found {detected_count} ADT signs.\n\n"
                        f"Detection rate: {(detected_count/total_count*100):.1f}%\n\n"
                        f"These are real detections from analyzing actual property images.")
            
            for result in results:
                # Ensure all required fields exist
                verification_record = {
                    'address': result.get('address', 'Unknown Address'),
                    'city': result.get('city', 'Unknown City'),
                    'state': result.get('state', 'NC'),
                    'image_path': result.get('image_path', ''),
                    'confidence': result.get('confidence', 0.0),
                    'adt_detected': result.get('adt_detected', False),
                    'detection_method': result.get('detection_method', 'Local CV'),
                    'explanation': result.get('explanation', 'No explanation'),
                    'timestamp': result.get('timestamp', ''),
                    'verification_status': result.get('verification_status', 'pending'),
                    'user_notes': result.get('user_notes', '')
                }
                
                # Only add if image exists
                if verification_record['image_path'] and os.path.exists(verification_record['image_path']):
                    verification_data.append(verification_record)
                else:
                    print(f"[DEBUG] Skipping record - image not found: {verification_record['image_path']}")
            
            if not verification_data:
                QMessageBox.warning(self, "No Images", "No verification records with accessible images found.")
                return
            
            self.verification_data = verification_data
            self.current_index = 0
            self.update_navigation_controls()
            self.load_current_image()
            
            detected_in_loaded = len([r for r in verification_data if r.get('adt_detected', False)])
            QMessageBox.information(self, "Data Loaded", 
                f"Loaded {len(self.verification_data)} properties for verification.\n"
                f"ADT detections: {detected_in_loaded}\n"
                f"Detection method: {verification_data[0].get('detection_method', 'Unknown') if verification_data else 'Unknown'}")
            print(f"[DEBUG] Successfully loaded {len(self.verification_data)} verification records")

        except Exception as e:
            error_msg = f"Failed to load verification data: {e}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

    def load_current_image(self):
        self.scene.clear()
        if not self.verification_data:
            return

        record = self.verification_data[self.current_index]
        image_path = record.get('image_path')
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.scene.addPixmap(pixmap)
                self.view.fitInView()
            else:
                self.scene.addText("Failed to load image.")
        else:
            self.scene.addText("Image not found.")
            
        self.address_label.setText(record.get('address', 'N/A'))
        self.city_label.setText(record.get('city', 'N/A'))
        self.confidence_label.setText(f"{record.get('confidence', 0):.2f}")
        self.method_label.setText(record.get('detection_method', 'N/A'))
        self.explanation_label.setText(record.get('explanation', 'N/A'))
        self.timestamp_label.setText(record.get('timestamp', 'N/A'))
        self.notes_text.setPlainText(record.get('user_notes', ''))
        self.update_status_label()

    def update_navigation_controls(self):
        if not self.verification_data:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.jump_combo.clear()
            return
            
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.verification_data) - 1)
        
        self.jump_combo.blockSignals(True)
        self.jump_combo.clear()
        for i, record in enumerate(self.verification_data):
            status_map = {'pending': '○', 'adt_present': '✅', 'no_adt': '❌', 'unsure': '❓'}
            status = status_map.get(record.get('verification_status', 'pending'))
            self.jump_combo.addItem(f"{status} {record.get('address', f'Image {i+1}')}")
        self.jump_combo.setCurrentIndex(self.current_index)
        self.jump_combo.blockSignals(False)
        
        verified_count = len([r for r in self.verification_data if r['verification_status'] != 'pending'])
        self.progress_label.setText(f"{verified_count}/{len(self.verification_data)} images verified")

    def verify_detection(self, user_verification):
        if not self.verification_data: return
        record = self.verification_data[self.current_index]
        record['verification_status'] = user_verification
        record['user_notes'] = self.notes_text.toPlainText()
        self.update_status_label()
        self.update_navigation_controls()
        QTimer.singleShot(200, self.next_image)

    def mark_adt_present(self): self.verify_detection('adt_present')
    def mark_no_adt(self): self.verify_detection('no_adt')
    def mark_unsure(self): self.verify_detection('unsure')

    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            self.update_navigation_controls()

    def next_image(self):
        if self.current_index < len(self.verification_data) - 1:
            self.current_index += 1
            self.load_current_image()
            self.update_navigation_controls()
        else:
            QMessageBox.information(self, "Done", "All images have been reviewed.")

    def jump_to_image(self, index):
        if 0 <= index < len(self.verification_data):
            self.current_index = index
            self.load_current_image()

    def save_verifications(self):
        if not self.verification_data:
            QMessageBox.warning(self, "No Data", "No data to save.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save Verifications", f"verifications_{datetime.now():%Y%m%d_%H%M%S}.json", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.verification_data, f, indent=2)
                QMessageBox.information(self, "Success", "Verifications saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def export_training_data(self):
        training_data = [r for r in self.verification_data if r['verification_status'] != 'pending']
        if not training_data:
            QMessageBox.warning(self, "No Data", "No verified images to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export Training Data", f"adt_training_data_{datetime.now():%Y%m%d_%H%M%S}.json", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(training_data, f, indent=2)
                QMessageBox.information(self, "Success", "Training data exported.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not export data: {e}")

    def update_status_label(self):
        if not self.verification_data: return
        record = self.verification_data[self.current_index]
        status = record.get('verification_status', 'pending')
        status_styles = {
            'pending': ("⏳ Pending", "gray"),
            'adt_present': ("✅ ADT Present", "green"),
            'no_adt': ("❌ No ADT", "red"),
            'unsure': ("❓ Unsure", "orange")
        }
        text, color = status_styles.get(status, ("Unknown", "black"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.load_current_image()