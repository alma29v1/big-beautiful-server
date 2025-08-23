"""
Cost Tracking Widget - Real-time API cost monitoring for AT&T Fiber Tracker
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QGroupBox, QProgressBar,
    QTextEdit, QComboBox, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from utils.api_cost_tracker import cost_tracker, get_cost_summary
import json
from datetime import datetime

class CostTrackingWidget(QWidget):
    """Widget for tracking and displaying API costs"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_timer()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("API Cost Tracking & Usage Monitor")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        layout.addWidget(header)
        
        # Cost Summary Section
        cost_summary_group = QGroupBox("Current Month Cost Summary")
        cost_summary_layout = QVBoxLayout(cost_summary_group)
        
        # Total cost display
        self.total_cost_label = QLabel("Total Monthly Cost: $0.00")
        self.total_cost_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        cost_summary_layout.addWidget(self.total_cost_label)
        
        # Projected cost display
        self.projected_cost_label = QLabel("Projected Monthly Cost: $0.00")
        self.projected_cost_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        cost_summary_layout.addWidget(self.projected_cost_label)
        
        layout.addWidget(cost_summary_group)
        
        # API Usage Table
        usage_group = QGroupBox("API Usage Details")
        usage_layout = QVBoxLayout(usage_group)
        
        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(7)
        self.usage_table.setHorizontalHeaderLabels([
            "API Service", "Usage", "Free Tier", "Free Remaining", "Paid Usage", "Cost", "Status"
        ])
        self.usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.usage_table.setAlternatingRowColors(True)
        usage_layout.addWidget(self.usage_table)
        
        layout.addWidget(usage_group)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self.export_report)
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addStretch()
        
        # Auto-refresh toggle
        self.auto_refresh_combo = QComboBox()
        self.auto_refresh_combo.addItems(["Manual", "Every 30s", "Every 1min", "Every 5min"])
        self.auto_refresh_combo.currentTextChanged.connect(self.on_auto_refresh_changed)
        controls_layout.addWidget(QLabel("Auto Refresh:"))
        controls_layout.addWidget(self.auto_refresh_combo)
        
        layout.addLayout(controls_layout)
        
        # Usage Summary
        summary_group = QGroupBox("Usage Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.usage_summary_text = QTextEdit()
        self.usage_summary_text.setReadOnly(True)
        self.usage_summary_text.setMaximumHeight(200)
        self.usage_summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
        """)
        summary_layout.addWidget(self.usage_summary_text)
        
        layout.addWidget(summary_group)
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
    
    def on_auto_refresh_changed(self, text):
        """Handle auto-refresh setting change"""
        self.refresh_timer.stop()
        
        if text == "Every 30s":
            self.refresh_timer.start(30000)
        elif text == "Every 1min":
            self.refresh_timer.start(60000)
        elif text == "Every 5min":
            self.refresh_timer.start(300000)
    
    def refresh_data(self):
        """Refresh cost tracking data"""
        try:
            # Get current costs
            costs = cost_tracker.calculate_costs()
            projections = cost_tracker.get_cost_projection()
            
            # Update total cost labels
            if costs:
                self.total_cost_label.setText(f"Total Monthly Cost: ${costs['total_monthly_cost']:.2f}")
                
                if projections:
                    self.projected_cost_label.setText(
                        f"Projected Monthly Cost: ${projections['total_projected_monthly_cost']:.2f}"
                    )
                else:
                    self.projected_cost_label.setText("Projected Monthly Cost: Calculating...")
            else:
                self.total_cost_label.setText("Total Monthly Cost: $0.00")
                self.projected_cost_label.setText("Projected Monthly Cost: $0.00")
            
            # Update usage table
            self.update_usage_table(costs)
            
            # Update usage summary
            summary = get_cost_summary()
            self.usage_summary_text.setPlainText(summary)
            
        except Exception as e:
            self.usage_summary_text.setPlainText(f"Error refreshing data: {e}")
    
    def update_usage_table(self, costs):
        """Update the usage table with current data"""
        if not costs or 'costs' not in costs:
            self.usage_table.setRowCount(0)
            return
        
        api_costs = costs['costs']
        self.usage_table.setRowCount(len(api_costs))
        
        for row, (api_name, data) in enumerate(api_costs.items()):
            # API Service
            self.usage_table.setItem(row, 0, QTableWidgetItem(data['name']))
            
            # Usage
            usage_text = f"{data['usage']} {data['billing_unit']}s"
            self.usage_table.setItem(row, 1, QTableWidgetItem(usage_text))
            
            # Free Tier
            self.usage_table.setItem(row, 2, QTableWidgetItem(str(data['free_tier'])))
            
            # Free Remaining
            remaining_item = QTableWidgetItem(str(data['free_remaining']))
            if data['free_remaining'] == 0:
                remaining_item.setBackground(Qt.red)
            elif data['free_remaining'] < data['free_tier'] * 0.1:  # Less than 10% remaining
                remaining_item.setBackground(Qt.yellow)
            self.usage_table.setItem(row, 3, remaining_item)
            
            # Paid Usage
            self.usage_table.setItem(row, 4, QTableWidgetItem(str(data['paid_usage'])))
            
            # Cost
            cost_item = QTableWidgetItem(f"${data['cost']:.2f}")
            if data['cost'] > 0:
                cost_item.setBackground(Qt.lightGray)
            self.usage_table.setItem(row, 5, cost_item)
            
            # Status
            if data['free_remaining'] > 0:
                status = "Free Tier"
                status_color = Qt.green
            elif data['cost'] > 0:
                status = "Paid Usage"
                status_color = Qt.red
            else:
                status = "No Usage"
                status_color = Qt.gray
            
            status_item = QTableWidgetItem(status)
            status_item.setBackground(status_color)
            self.usage_table.setItem(row, 6, status_item)
    
    def export_report(self):
        """Export detailed cost report"""
        try:
            output_file = cost_tracker.export_cost_report()
            QMessageBox.information(
                self, 
                "Report Exported", 
                f"Cost report exported to: {output_file}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Error", 
                f"Failed to export report: {e}"
            )
    
    def get_cost_alerts(self):
        """Get cost alerts for high usage"""
        costs = cost_tracker.calculate_costs()
        projections = cost_tracker.get_cost_projection()
        
        alerts = []
        
        if costs and 'costs' in costs:
            for api_name, data in costs['costs'].items():
                # Alert if free tier is almost exhausted
                if data['free_tier'] > 0 and data['free_remaining'] < data['free_tier'] * 0.1:
                    alerts.append(f"⚠️ {data['name']}: Only {data['free_remaining']} free requests remaining!")
                
                # Alert if paid usage is high
                if data['cost'] > 10:  # More than $10
                    alerts.append(f"💰 {data['name']}: ${data['cost']:.2f} in charges this month")
        
        if projections and projections.get('total_projected_monthly_cost', 0) > 50:
            alerts.append(f"📈 Projected monthly cost: ${projections['total_projected_monthly_cost']:.2f}")
        
        return alerts 