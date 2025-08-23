from PySide6.QtCore import QThread, Signal
import pandas as pd
import json
import os
import time
from datetime import datetime
import shutil

class ADTTrainingWorker(QThread):
    """Worker for ADT detection training and verification"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    finished_signal = Signal(dict)  # training_results
    verification_signal = Signal(dict)  # verification data for GUI
    
    def __init__(self, adt_results_file=None):
        super().__init__()
        self.adt_results_file = adt_results_file
        self.stop_flag = False
        
        # Training data directories
        self.training_dir = "adt_training_data"
        self.verified_dir = os.path.join(self.training_dir, "verified")
        self.pending_dir = os.path.join(self.training_dir, "pending")
        self.false_positives_dir = os.path.join(self.training_dir, "false_positives")
        self.false_negatives_dir = os.path.join(self.training_dir, "false_negatives")
        
        # Create directories
        for dir_path in [self.training_dir, self.verified_dir, self.pending_dir, 
                        self.false_positives_dir, self.false_negatives_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_adt_results(self):
        """Load ADT detection results from file"""
        try:
            if not self.adt_results_file or not os.path.exists(self.adt_results_file):
                # Look for the most recent ADT results file (JSON or CSV)
                adt_files = [f for f in os.listdir('.') if f.startswith('adt_detection_results_') and (f.endswith('.csv') or f.endswith('.json'))]
                if adt_files:
                    self.adt_results_file = max(adt_files, key=os.path.getmtime)
                else:
                    self.log_signal.emit("[ADT Training] No ADT results file found")
                    return []
            
            # Check file extension and load accordingly
            if self.adt_results_file.endswith('.json'):
                # Load JSON file
                with open(self.adt_results_file, 'r') as f:
                    data = json.load(f)
                
                # Extract detections from JSON structure
                if 'detections' in data:
                    adt_results = data['detections']
                else:
                    adt_results = data  # Assume it's a list of detections
                
                self.log_signal.emit(f"[ADT Training] Loaded {len(adt_results)} ADT results from {self.adt_results_file}")
                return adt_results
            else:
                # Load CSV file
                df = pd.read_csv(self.adt_results_file)
                self.log_signal.emit(f"[ADT Training] Loaded {len(df)} ADT results from {self.adt_results_file}")
                return df.to_dict('records')
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error loading ADT results: {e}")
            return []
    
    def prepare_verification_data(self, adt_results):
        """Prepare ADT results for verification"""
        try:
            verification_data = []
            
            for i, result in enumerate(adt_results):
                if self.stop_flag:
                    break
                
                address = result.get('address', '')
                image_path = result.get('image_path', '')
                confidence = result.get('confidence', 0)
                adt_detected = result.get('adt_detected', False)
                
                # Skip if no image path
                if not image_path or not os.path.exists(image_path):
                    continue
                
                # Create verification record
                verification_record = {
                    'id': i,
                    'address': address,
                    'image_path': image_path,
                    'confidence': confidence,
                    'adt_detected': adt_detected,
                    'verified': False,
                    'user_verification': None,  # True/False/None
                    'verification_notes': '',
                    'verification_date': None,
                    'training_category': None  # 'true_positive', 'false_positive', 'false_negative'
                }
                
                verification_data.append(verification_record)
                
                # Copy image to pending directory for verification
                self.copy_image_for_verification(image_path, address, i)
            
            self.log_signal.emit(f"[ADT Training] Prepared {len(verification_data)} images for verification")
            return verification_data
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error preparing verification data: {e}")
            return []
    
    def copy_image_for_verification(self, image_path, address, image_id):
        """Copy image to pending directory for verification"""
        try:
            # Create safe filename
            safe_address = address.replace('/', '_').replace(' ', '_')
            filename = f"{image_id}_{safe_address}.jpg"
            dest_path = os.path.join(self.pending_dir, filename)
            
            # Copy image
            shutil.copy2(image_path, dest_path)
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error copying image {image_path}: {e}")
    
    def save_verification_data(self, verification_data):
        """Save verification data to file"""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            verification_file = os.path.join(self.training_dir, f'verification_data_{timestamp}.json')
            
            with open(verification_file, 'w') as f:
                json.dump(verification_data, f, indent=2, default=str)
            
            self.log_signal.emit(f"[ADT Training] Saved verification data to {verification_file}")
            return verification_file
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error saving verification data: {e}")
            return None
    
    def process_verification(self, verification_data):
        """Process verification results and categorize training data"""
        try:
            true_positives = []
            false_positives = []
            false_negatives = []
            
            for record in verification_data:
                if record.get('verified', False):
                    user_verification = record.get('user_verification')
                    adt_detected = record.get('adt_detected', False)
                    
                    if user_verification is True and adt_detected is True:
                        # True positive: AI correctly detected ADT
                        record['training_category'] = 'true_positive'
                        true_positives.append(record)
                        self.move_to_category(record, 'true_positives')
                        
                    elif user_verification is True and adt_detected is False:
                        # False negative: AI missed ADT
                        record['training_category'] = 'false_negative'
                        false_negatives.append(record)
                        self.move_to_category(record, 'false_negatives')
                        
                    elif user_verification is False and adt_detected is True:
                        # False positive: AI incorrectly detected ADT
                        record['training_category'] = 'false_positive'
                        false_positives.append(record)
                        self.move_to_category(record, 'false_positives')
            
            # Create training summary
            training_summary = {
                'total_verified': len([r for r in verification_data if r.get('verified', False)]),
                'true_positives': len(true_positives),
                'false_positives': len(false_positives),
                'false_negatives': len(false_negatives),
                'accuracy': len(true_positives) / max(1, len(true_positives) + len(false_positives) + len(false_negatives)) * 100,
                'precision': len(true_positives) / max(1, len(true_positives) + len(false_positives)) * 100,
                'recall': len(true_positives) / max(1, len(true_positives) + len(false_negatives)) * 100
            }
            
            self.log_signal.emit(f"[ADT Training] Training Summary:")
            self.log_signal.emit(f"[ADT Training] - True Positives: {training_summary['true_positives']}")
            self.log_signal.emit(f"[ADT Training] - False Positives: {training_summary['false_positives']}")
            self.log_signal.emit(f"[ADT Training] - False Negatives: {training_summary['false_negatives']}")
            self.log_signal.emit(f"[ADT Training] - Accuracy: {training_summary['accuracy']:.1f}%")
            self.log_signal.emit(f"[ADT Training] - Precision: {training_summary['precision']:.1f}%")
            self.log_signal.emit(f"[ADT Training] - Recall: {training_summary['recall']:.1f}%")
            
            return training_summary
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error processing verification: {e}")
            return {}
    
    def move_to_category(self, record, category):
        """Move image to appropriate training category directory"""
        try:
            image_path = record.get('image_path', '')
            if not image_path or not os.path.exists(image_path):
                return
            
            # Get filename from pending directory
            safe_address = record.get('address', '').replace('/', '_').replace(' ', '_')
            filename = f"{record.get('id')}_{safe_address}.jpg"
            pending_path = os.path.join(self.pending_dir, filename)
            
            if os.path.exists(pending_path):
                # Move to category directory
                category_dir = os.path.join(self.training_dir, category)
                dest_path = os.path.join(category_dir, filename)
                shutil.move(pending_path, dest_path)
                
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error moving image to category: {e}")
    
    def generate_training_report(self, training_summary):
        """Generate training report for model improvement"""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(self.training_dir, f'training_report_{timestamp}.json')
            
            report = {
                'training_date': timestamp,
                'summary': training_summary,
                'recommendations': self.generate_recommendations(training_summary),
                'model_improvements': self.suggest_model_improvements(training_summary)
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_signal.emit(f"[ADT Training] Generated training report: {report_file}")
            return report_file
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error generating training report: {e}")
            return None
    
    def generate_recommendations(self, training_summary):
        """Generate recommendations based on training results"""
        recommendations = []
        
        if training_summary.get('false_positives', 0) > training_summary.get('false_negatives', 0):
            recommendations.append("High false positive rate - consider increasing confidence threshold")
            recommendations.append("Review false positive images to identify common patterns")
            recommendations.append("Add more negative training examples")
        
        if training_summary.get('false_negatives', 0) > training_summary.get('false_positives', 0):
            recommendations.append("High false negative rate - consider decreasing confidence threshold")
            recommendations.append("Review false negative images to identify missed patterns")
            recommendations.append("Add more positive training examples")
        
        if training_summary.get('accuracy', 0) < 80:
            recommendations.append("Overall accuracy below 80% - consider retraining model")
            recommendations.append("Review all misclassified images for pattern analysis")
        
        return recommendations
    
    def suggest_model_improvements(self, training_summary):
        """Suggest specific model improvements"""
        improvements = []
        
        # Based on performance, suggest improvements
        if training_summary.get('precision', 0) < 85:
            improvements.append("Improve text detection accuracy for ADT signs")
            improvements.append("Add more ADT sign templates and variations")
        
        if training_summary.get('recall', 0) < 85:
            improvements.append("Improve visual pattern detection for ADT signs")
            improvements.append("Add color-based detection for ADT brand colors")
        
        improvements.append("Implement confidence calibration based on training data")
        improvements.append("Add image preprocessing for better text extraction")
        
        return improvements
    
    def run(self):
        """Run ADT training workflow"""
        try:
            self.log_signal.emit("[ADT Training] Starting ADT training workflow...")
            
            # Load ADT results
            adt_results = self.load_adt_results()
            if not adt_results:
                self.finished_signal.emit({})
                return
            
            # Prepare verification data
            verification_data = self.prepare_verification_data(adt_results)
            if not verification_data:
                self.finished_signal.emit({})
                return
            
            # Save verification data
            verification_file = self.save_verification_data(verification_data)
            
            # Emit verification data for GUI
            self.verification_signal.emit({
                'verification_data': verification_data,
                'verification_file': verification_file,
                'pending_images': len(verification_data)
            })
            
            # Wait for user verification (this will be handled by GUI)
            self.log_signal.emit("[ADT Training] Verification data prepared. Please verify images in the GUI.")
            
            # For now, we'll simulate some verifications for testing
            # In real implementation, this would come from GUI user input
            self.simulate_verifications(verification_data)
            
            # Process verification results
            training_summary = self.process_verification(verification_data)
            
            # Generate training report
            report_file = self.generate_training_report(training_summary)
            
            # Save updated verification data
            self.save_verification_data(verification_data)
            
            # Return results
            results = {
                'verification_data': verification_data,
                'training_summary': training_summary,
                'report_file': report_file,
                'verification_file': verification_file
            }
            
            self.finished_signal.emit(results)
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error in training workflow: {e}")
            self.finished_signal.emit({})
    
    def simulate_verifications(self, verification_data):
        """Simulate user verifications for testing purposes"""
        try:
            # Simulate some verifications (remove this in production)
            for i, record in enumerate(verification_data[:5]):  # First 5 records
                record['verified'] = True
                record['user_verification'] = record.get('adt_detected', False)  # Assume AI is correct for simulation
                record['verification_notes'] = f"Simulated verification {i+1}"
                record['verification_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.log_signal.emit("[ADT Training] Simulated 5 verifications for testing")
            
        except Exception as e:
            self.log_signal.emit(f"[ADT Training] Error in simulation: {e}")
    
    def stop(self):
        """Stop the worker"""
        self.stop_flag = True 