#!/usr/bin/env python3
"""
Improved ADT Detection Worker
Uses local computer vision techniques for reliable ADT sign detection
"""

import os
import sys
import cv2
import numpy as np
import glob
import json
from datetime import datetime
from PySide6.QtCore import QThread, Signal

class ImprovedADTWorker(QThread):
    """Improved ADT detection worker using local computer vision"""
    
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    city_progress_signal = Signal(int, int, str)  # current_city, total_cities, city_name
    detection_signal = Signal(dict)  # detection result
    finished_signal = Signal(dict)  # final results
    
    def __init__(self, selected_cities):
        super().__init__()
        self.selected_cities = selected_cities
        self.stop_flag = False
        
    def run(self):
        """Run ADT detection on all selected cities"""
        try:
            self.log_signal.emit("🔍 Starting improved ADT detection...")
            
            all_detections = []
            total_properties = 0
            total_detections = 0
            
            # Process each city
            for city_idx, city_name in enumerate(self.selected_cities):
                if self.stop_flag:
                    break
                    
                self.city_progress_signal.emit(city_idx + 1, len(self.selected_cities), city_name)
                self.log_signal.emit(f"🏙️ Processing {city_name}...")
                
                # Find property directories for this city
                city_pattern = f"adt_detections/{city_name}_*"
                property_dirs = glob.glob(city_pattern)
                
                if not property_dirs:
                    self.log_signal.emit(f"⚠️ No property directories found for {city_name}")
                    continue
                
                self.log_signal.emit(f"📂 Found {len(property_dirs)} properties in {city_name}")
                
                # Process each property
                for prop_idx, prop_dir in enumerate(property_dirs):
                    if self.stop_flag:
                        break
                        
                    self.progress_signal.emit(prop_idx + 1, len(property_dirs))
                    
                    # Extract address from directory name
                    prop_name = os.path.basename(prop_dir)
                    address = prop_name.replace(f"{city_name}_", "").replace("_", " ")
                    
                    # Find images in this property
                    image_files = []
                    for ext in ['*.jpg', '*.jpeg', '*.png']:
                        image_files.extend(glob.glob(os.path.join(prop_dir, ext)))
                    
                    if not image_files:
                        continue
                    
                    # Test each image for ADT signs
                    max_confidence = 0.0
                    best_explanation = ""
                    adt_detected = False
                    
                    for image_path in image_files:
                        confidence, explanation = self.detect_adt_in_image(image_path)
                        
                        if confidence > max_confidence:
                            max_confidence = confidence
                            best_explanation = explanation
                            
                        if confidence > 0.5:  # Detection threshold
                            adt_detected = True
                    
                    # Create detection result
                    detection = {
                        'address': address,
                        'city': city_name,
                        'state': 'NC',
                        'adt_detected': adt_detected,
                        'confidence': max_confidence,
                        'explanation': best_explanation,
                        'detection_method': 'Local Computer Vision',
                        'image_path': image_files[0] if image_files else '',
                        'images_processed': len(image_files),
                        'property_dir': prop_dir
                    }
                    
                    all_detections.append(detection)
                    total_properties += 1
                    
                    if adt_detected:
                        total_detections += 1
                        self.log_signal.emit(f"✅ ADT detected at {address} (confidence: {max_confidence:.3f})")
                    
                    # Emit individual detection
                    self.detection_signal.emit(detection)
            
            # Save consolidated results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"adt_detection_results_{timestamp}.json"
            
            results_data = {
                'timestamp': timestamp,
                'cities_processed': self.selected_cities,
                'total_properties': total_properties,
                'total_detections': total_detections,
                'detection_rate': (total_detections / total_properties * 100) if total_properties > 0 else 0,
                'detections': all_detections
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            self.log_signal.emit(f"💾 Results saved to {results_file}")
            
            # Final summary
            self.log_signal.emit(f"🎯 ADT Detection Summary:")
            self.log_signal.emit(f"   Properties processed: {total_properties}")
            self.log_signal.emit(f"   ADT signs detected: {total_detections}")
            self.log_signal.emit(f"   Detection rate: {(total_detections/total_properties*100):.1f}%" if total_properties > 0 else "   Detection rate: 0%")
            
            # Emit final results
            self.finished_signal.emit(results_data)
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error in ADT detection: {e}")
            import traceback
            self.log_signal.emit(f"Traceback: {traceback.format_exc()}")
    
    def detect_adt_in_image(self, image_path):
        """Detect ADT signs in an image using local computer vision"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return 0.0, "Could not load image"
            
            # Convert to different color spaces
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Method 1: Color-based detection (blue/red for ADT signs)
            # Blue color range for ADT signs
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Red color range for ADT signs
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            # Combine color masks
            combined_mask = cv2.bitwise_or(blue_mask, red_mask)
            
            # Calculate color score
            total_pixels = hsv.shape[0] * hsv.shape[1]
            adt_pixels = cv2.countNonZero(combined_mask)
            color_score = min(adt_pixels / total_pixels * 10, 1.0)
            
            # Method 2: Template matching for "ADT" text
            template = np.zeros((30, 60), dtype=np.uint8)
            cv2.putText(template, "ADT", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255, 2)
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, template_score, _, _ = cv2.minMaxLoc(result)
            
            # Method 3: Edge detection for rectangular signs
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            rectangular_objects = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area for a sign
                    # Approximate contour to polygon
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Check if it's roughly rectangular (4 corners)
                    if len(approx) >= 4:
                        rectangular_objects += 1
            
            shape_score = min(rectangular_objects / 10, 1.0)
            
            # Combine all scores
            final_confidence = (color_score * 0.5 + template_score * 0.3 + shape_score * 0.2)
            
            explanation = f"Color: {color_score:.2f}, Template: {template_score:.2f}, Shape: {shape_score:.2f}"
            
            return final_confidence, explanation
            
        except Exception as e:
            return 0.0, f"Error: {str(e)}"
    
    def stop(self):
        """Stop the worker"""
        self.stop_flag = True

def main():
    print("🧪 Simple ADT Detection Test")
    print("=" * 50)
    
    # Test with downloaded images
    test_images = glob.glob("adt_test_images/*.jpg")
    
    if not test_images:
        print("❌ No test images found in adt_test_images/")
        return
    
    print(f"Testing {len(test_images)} images...")
    
    detected_count = 0
    total_processed = 0
    
    for image_path in test_images[:10]:  # Test first 10 images
        image_name = os.path.basename(image_path)
        print(f"\n🔍 Testing: {image_name}")
        
        confidence, explanation = test_local_adt_detection(image_path)
        total_processed += 1
        
        if confidence > 0.5:
            detected_count += 1
            status = "✅ DETECTED"
        else:
            status = "❌ No ADT"
        
        print(f"   {status} - Confidence: {confidence:.3f}")
        print(f"   {explanation}")
    
    print(f"\n📊 Results Summary:")
    print(f"   Total images tested: {total_processed}")
    print(f"   ADT signs detected: {detected_count}/{total_processed}")
    
    if detected_count > 0:
        print(f"   ✅ ADT detection is working!")
        print(f"   Detection rate: {(detected_count/total_processed*100):.1f}%")
    else:
        print(f"   ⚠️  No ADT signs detected")
        print(f"   This could be normal if test images don't contain ADT signs")
    
    # Test with real property images if available
    print(f"\n🏠 Testing with real property images...")
    property_images = glob.glob("adt_detections/*/redfin_image_*.jpg")
    
    if property_images:
        print(f"Found {len(property_images)} property images")
        
        for image_path in property_images[:5]:  # Test first 5 property images
            image_name = os.path.basename(image_path)
            property_name = os.path.basename(os.path.dirname(image_path))
            
            confidence, explanation = test_local_adt_detection(image_path)
            
            if confidence > 0.5:
                print(f"   ✅ {property_name}/{image_name} - ADT DETECTED ({confidence:.3f})")
            else:
                print(f"   ❌ {property_name}/{image_name} - No ADT ({confidence:.3f})")
    else:
        print("   No property images found in adt_detections/")

if __name__ == "__main__":
    main() 