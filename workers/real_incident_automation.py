#!/usr/bin/env python3
"""
Real Incident Automation Integration
Integrates real incident monitoring into the main automation workflow
"""

from workers.real_incident_monitor import RealIncidentMonitor
from PySide6.QtCore import QObject, Signal
import time

class RealIncidentAutomation(QObject):
    """Integration class for real incident monitoring in automation workflow"""
    
    log_signal = Signal(str)
    campaigns_signal = Signal(list)
    finished_signal = Signal(dict)
    
    def __init__(self, target_cities=None, radius_yards=25):
        super().__init__()
        self.target_cities = target_cities or [
            "Wilmington, NC", "Leland, NC", "Hampstead, NC", 
            "Lumberton, NC", "Southport, NC", "Jacksonville, NC", "Fayetteville, NC"
        ]
        self.radius_yards = radius_yards
        self.monitor = None
    
    def run_real_incident_monitoring(self):
        """Run real incident monitoring and return results"""
        
        try:
            self.log_signal.emit("🚨 Starting REAL incident monitoring system...")
            self.log_signal.emit(f"📍 Monitoring {len(self.target_cities)} cities for incidents")
            self.log_signal.emit(f"🎯 Targeting customers within {self.radius_yards} yards of incidents")
            
            # Create and configure monitor
            self.monitor = RealIncidentMonitor(self.target_cities, self.radius_yards)
            
            # Connect signals
            self.monitor.log_signal.connect(self.log_signal)
            self.monitor.campaigns_generated_signal.connect(self.campaigns_signal)
            
            # Store results
            results = {'incidents': 0, 'campaigns': 0, 'campaigns_data': []}
            
            def capture_results(final_results):
                results.update(final_results)
                self.finished_signal.emit(results)
            
            def capture_campaigns(campaigns):
                results['campaigns_data'].extend(campaigns)
                self.campaigns_signal.emit(campaigns)
            
            self.monitor.finished_signal.connect(capture_results)
            self.monitor.campaigns_generated_signal.connect(capture_campaigns)
            
            # Run monitoring
            self.monitor.run()
            
            # Wait for completion
            start_time = time.time()
            timeout = 60  # 1 minute timeout
            
            while self.monitor.isRunning() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.monitor.isRunning():
                self.monitor.stop_flag = True
                self.monitor.wait(5000)
                self.log_signal.emit("⚠️ Incident monitoring timed out")
                return "Incident monitoring timed out"
            
            # Return summary
            incidents_found = results.get('incidents', 0)
            campaigns_generated = results.get('campaigns', 0)
            
            if campaigns_generated > 0:
                return f"✅ Found {incidents_found} incidents, generated {campaigns_generated} URGENT campaigns"
            elif incidents_found > 0:
                return f"ℹ️ Found {incidents_found} incidents, but no customers within {self.radius_yards} yards"
            else:
                return f"✅ No incidents found in monitored areas (good news!)"
                
        except Exception as e:
            self.log_signal.emit(f"❌ Error in real incident monitoring: {e}")
            import traceback
            traceback.print_exc()
            return f"Real incident monitoring error: {str(e)}" 